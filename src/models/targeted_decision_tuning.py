"""Ajuste experimental e direcionado de decisão.

Está camada é lateral e não substitui o Decision Engine oficial. Ela serve para
validação offline de regras conservadoras sobre janelas já avaliadas, com foco
em recuperar apenas falsos negativos avaliáveis/reais sem baixar limites de classificação
globais nem promover janelas fracas.
"""

from __future__ import annotations

import math
from dataclasses import asdict, dataclass
from typing import Any


SENSITIVE_SERVICE_PORTS = {21, 22, 23, 445, 3389, 5900}
PORTSCAN_ALLOWED_CATEGORIES = {
    "real_decision_error",
    "requires_temporal_history",
    "lost_context_in_aggregation",
}
BLOCKED_CATEGORIES = {"label_too_broad", "weak_window_low_evidence"}


@dataclass(frozen=True)
class TargetedDecisionResult:
    """Resultado da camada experimental."""

    prediction_targeted: int
    targeted_attack_type: str
    targeted_reason: str
    targeted_rule: str
    targeted_confidence: float
    targeted_changed: bool

    def as_dict(self) -> dict[str, Any]:
        """Converte os campos do resultado em dicionário, mantendo os valores calculados."""
        return asdict(self)


def _present(value: Any) -> bool:
    """Indica se o valor está preenchido e não representa um número ausente."""
    if value is None:
        return False
    try:
        if math.isnan(value):
            return False
    except (TypeError, ValueError):
        pass
    return str(value).strip() != ""


def _float(row: dict[str, Any], name: str, default: float = 0.0) -> float:
    """Lê um campo numérico do registro e usa o padrão para valor ausente ou inválido."""
    value = row.get(name, default)
    if not _present(value):
        return default
    try:
        number = float(value)
        return default if math.isnan(number) else number
    except (TypeError, ValueError):
        return default


def _int(row: dict[str, Any], name: str, default: int = 0) -> int:
    """Lê o campo numérico, arredonda e converte para inteiro."""
    return int(round(_float(row, name, float(default))))


def _str(row: dict[str, Any], name: str, default: str = "") -> str:
    """Lê um campo como texto, retirando espaços externos."""
    value = row.get(name, default)
    return str(value).strip() if _present(value) else default


def _bool(row: dict[str, Any], name: str) -> bool:
    """Reconhece valores booleanos e as formas textuais de verdadeiro aceitas pelo módulo."""
    value = row.get(name)
    if isinstance(value, bool):
        return value
    return str(value).strip().lower() in {"true", "1", "yes", "sim"}


def _safe_ports(row: dict[str, Any]) -> set[int]:
    """Recupera o conjunto de portas dos campos textuais permitidos."""
    ports: set[int] = set()
    for name in ("safe_port_text", "common_destination_ports"):
        text = _str(row, name)
        for token in text.replace(";", ",").replace("|", ",").split(","):
            token = token.strip()
            if not token:
                continue
            try:
                port = int(float(token))
            except ValueError:
                continue
            if 0 < port <= 65535:
                ports.add(port)
    return ports


def _base_prediction(row: dict[str, Any]) -> int:
    """Obtém a classificação de base respeitando a ordem de preferência dos campos existentes."""
    if "prediction_v2_3" in row:
        return _int(row, "prediction_v2_3")
    return _int(row, "prediction")


def _normal_result(row: dict[str, Any], reason: str = "sem ajuste direcionado") -> TargetedDecisionResult:
    """Monta o resultado sem ajuste, preservando a classificação de base."""
    base = _base_prediction(row)
    return TargetedDecisionResult(
        prediction_targeted=base,
        targeted_attack_type=_str(row, "heuristic_attack_type", "normal"),
        targeted_reason=reason,
        targeted_rule="none",
        targeted_confidence=0.0,
        targeted_changed=False,
    )


def _operational_noise(row: dict[str, Any]) -> bool:
    """Verifica os indicadores já existentes de tráfego operacional recorrente."""
    return (
        _bool(row, "operational_noise_suppressed")
        or _bool(row, "v2_3_operational_noise_context")
        or _bool(row, "ctx_operational_noise_hint")
    )


def _portscan_signal(row: dict[str, Any]) -> bool:
    """Verifica indícios de varredura usando volumes, portas e contexto disponíveis."""
    return (
        _float(row, "ports") >= 5
        or _float(row, "destination_port_count") >= 5
        or _float(row, "rolling_distinct_ports") >= 5
        or _float(row, "rolling_connections") >= 5
        or _bool(row, "ctx_vertical_scan_hint")
        or _bool(row, "ctx_horizontal_scan_hint")
    )


def _sensitive_service(row: dict[str, Any]) -> bool:
    """Indica se a janela inclui porta de serviço considerada sensível pelas regras."""
    return _bool(row, "has_sensitive_service_port") or bool(
        _safe_ports(row) & SENSITIVE_SERVICE_PORTS
    )


def tune_window_decision(row: dict[str, Any]) -> TargetedDecisionResult:
    """Aplica regras conservadoras sobre uma janela já avaliada.

    A função nunca rebaixa predições positivas e nunca promove janelas marcadas
    como não avaliáveis, `label_too_broad` ou `weak_window_low_evidence`.
    """

    base = _base_prediction(row)
    if base == 1:
        return _normal_result(row, "predição original já positiva")

    if not _bool(row, "attack_window_evaluable"):
        return _normal_result(row, "janela não avaliável para ajuste")

    category = _str(row, "diagnostic_category")
    if category in BLOCKED_CATEGORIES:
        return _normal_result(row, f"categoria bloqueada: {category}")

    if _operational_noise(row):
        return _normal_result(row, "ruído operacional bloqueia promoção")

    scenario = _str(row, "scenario").lower()
    heuristic_type = _str(row, "heuristic_attack_type").lower()

    if scenario == "port_scan" or heuristic_type == "port_scan":
        if category in PORTSCAN_ALLOWED_CATEGORIES and _portscan_signal(row):
            confidence = 0.88 if category == "real_decision_error" else 0.76
            return TargetedDecisionResult(
                prediction_targeted=1,
                targeted_attack_type="port_scan",
                targeted_reason="port_scan avaliável com evidência contextual mínima",
                targeted_rule="port_scan_evaluable_context",
                targeted_confidence=confidence,
                targeted_changed=True,
            )
        return _normal_result(row, "port_scan sem categoria/sinal suficiente")

    if scenario == "brute_force" or heuristic_type in {"brute_force", "ssh_suspicious"}:
        if (
            _sensitive_service(row)
            and (_float(row, "connections") >= 6 or _float(row, "rolling_connections") >= 20)
            and _float(row, "bytes_per_connection") <= 90
        ):
            return TargetedDecisionResult(
                prediction_targeted=1,
                targeted_attack_type="brute_force",
                targeted_reason="força bruta avaliável em serviço sensível com baixo volume por conexão",
                targeted_rule="brute_force_sensitive_service",
                targeted_confidence=0.74,
                targeted_changed=True,
            )
        return _normal_result(row, "brute_force sem serviço sensível forte")

    if scenario == "syn_flood" or heuristic_type in {"syn_flood", "ddos"}:
        syn_ratio = _float(row, "tcp_syn_ratio", 1.0)
        if (
            _float(row, "tcp_syn_count") >= 30
            and _float(row, "connections") >= 30
            and _float(row, "bytes_per_connection") <= 90
            and syn_ratio >= 0.60
        ):
            return TargetedDecisionResult(
                prediction_targeted=1,
                targeted_attack_type="syn_flood",
                targeted_reason="SYN flood avaliável com alto volume de SYN e baixo volume por conexão",
                targeted_rule="syn_flood_high_syn_ratio",
                targeted_confidence=0.78,
                targeted_changed=True,
            )
        return _normal_result(row, "syn_flood sem volume SYN suficiente")

    return _normal_result(row)
