"""Ajustes experimentais de classificação do Sinalyx.

Este módulo compara regras separadamente, sem substituir a decisão oficial.
Ele usa somente sinais disponíveis durante a análise: rótulos de avaliação,
cenários e campos de diagnóstico não podem orientar as regras. O objetivo é
verificar se ajustes estudados fora da operação podem ser reproduzidos com
esses sinais permitidos.
"""

from __future__ import annotations

import math
from dataclasses import asdict, dataclass
from typing import Any


OFFICIAL_FEATURE_COLUMNS = {
    "connections",
    "bytes",
    "packets",
    "packet_size",
    "ports",
    "bytes_per_packet",
    "bytes_per_connection",
    "packets_per_connection",
    "log1p_connections",
    "log1p_bytes",
    "log1p_packets",
    "log1p_packet_size",
    "log1p_ports",
}

FORBIDDEN_VALIDATION_FIELDS = {
    "scenario",
    "target",
    "label",
    "Label",
    "is_attack",
    "is_port_scan",
    "is_false_negative",
    "is_true_positive",
    "is_false_positive",
    "error_type",
    "diagnostic_category",
    "attack_window_evaluable",
    "evaluability_reason",
}

ALLOWED_RUNTIME_FIELDS = {
    *OFFICIAL_FEATURE_COLUMNS,
    "ae_score",
    "if_score",
    "ae_normalized",
    "if_normalized",
    "ensemble_score",
    "heuristic_attack_type",
    "heuristic_confidence",
    "heuristic_reason",
    "destination_port_count",
    "destination_ip_count",
    "rolling_distinct_ports",
    "rolling_connections",
    "rolling_windows",
    "tcp_syn_count",
    "tcp_syn_ratio",
    "has_sensitive_service_port",
    "safe_port_text",
    "common_destination_ports",
    "operational_noise_hint",
    "operational_noise_suppressed",
    "operational_noise_category",
    "operational_noise_reason",
    "v2_3_operational_noise_context",
    "ctx_vertical_scan_hint",
    "ctx_horizontal_scan_hint",
    "ctx_operational_noise_hint",
    "ctx_sensitive_service_hint",
    "ctx_repeated_destination_hint",
    "ctx_scan_like_hint",
    # Estado da decisão durante a análise; não é rótulo nem campo de avaliação.
    "prediction",
    "prediction_before",
    "prediction_after",
    "prediction_v2_2_adjusted",
    "prediction_v2_3",
    "prediction_base",
}

NOISE_SERVICE_PORTS = {53, 67, 68, 123, 137, 138, 139, 1900, 3702, 5353, 5355, 546, 547}
LOW_RISK_SERVICE_PORTS = {53, 80, 123, 443}
SUSPICIOUS_HEURISTIC_TYPES = {
    "port_scan",
    "scan",
    "ssh_suspicious",
    "unknown_anomaly",
    "anomalia_nao_classificada",
}


class ForbiddenFieldAccessError(RuntimeError):
    """Erro de regra experimental que tentou consultar campos exclusivos da avaliação."""


@dataclass(frozen=True)
class OperationalTuningResult:
    """Resultado de comparação experimental; não substitui a classificação oficial."""
    prediction_operational_targeted: int
    operational_attack_type: str
    operational_rule: str
    operational_reason: str
    operational_confidence: float
    operational_changed: bool
    operational_runtime_fields_used: list[str]

    def as_dict(self) -> dict[str, Any]:
        """Converte os campos do resultado em dicionário, mantendo os valores calculados."""
        return asdict(self)


class RuntimeRow:
    """Acesso controlado somente aos campos permitidos durante a análise."""

    def __init__(self, row: dict[str, Any]) -> None:
        """Copia somente campos permitidos e inicia o registro dos campos consultados."""
        self._row = {
            field: row.get(field)
            for field in ALLOWED_RUNTIME_FIELDS
            if field in row
        }
        self.used_fields: set[str] = set()

    def get(self, field: str, default: Any = None) -> Any:
        """Lê um campo permitido e registra seu uso; campos de avaliação são recusados."""
        if field in FORBIDDEN_VALIDATION_FIELDS:
            raise ForbiddenFieldAccessError(
                f"Operational tuning attempted to access forbidden field: {field}"
            )
        if field not in ALLOWED_RUNTIME_FIELDS:
            return default
        self.used_fields.add(field)
        return self._row.get(field, default)


def extract_runtime_fields(row: dict[str, Any]) -> dict[str, Any]:
    """Retorna somente os campos permitidos para avaliar as regras experimentais."""

    return {
        field: row.get(field)
        for field in ALLOWED_RUNTIME_FIELDS
        if field in row
    }


def forbidden_fields_present(row: dict[str, Any]) -> list[str]:
    """Lista os campos de avaliação presentes que não podem orientar a análise."""
    return sorted(field for field in row if field in FORBIDDEN_VALIDATION_FIELDS)


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


def _float(row: RuntimeRow, field: str, default: float = 0.0) -> float:
    """Lê um campo numérico do registro e usa o padrão para valor ausente ou inválido."""
    value = row.get(field, default)
    if not _present(value):
        return default
    try:
        number = float(value)
        return default if math.isnan(number) else number
    except (TypeError, ValueError):
        return default


def _int(row: RuntimeRow, field: str, default: int = 0) -> int:
    """Lê o campo numérico, arredonda e converte para inteiro."""
    return int(round(_float(row, field, float(default))))


def _str(row: RuntimeRow, field: str, default: str = "") -> str:
    """Lê um campo como texto, retirando espaços externos."""
    value = row.get(field, default)
    return str(value).strip() if _present(value) else default


def _bool(row: RuntimeRow, field: str) -> bool:
    """Reconhece valores booleanos e as formas textuais de verdadeiro aceitas pelo módulo."""
    value = row.get(field)
    if isinstance(value, bool):
        return value
    return str(value).strip().lower() in {"true", "1", "yes", "sim"}


def _base_prediction(row: RuntimeRow) -> int:
    """Obtém a classificação de base respeitando a ordem de preferência dos campos existentes."""
    for field in (
        "prediction_v2_3",
        "prediction_base",
        "prediction_after",
        "prediction",
        "prediction_v2_2_adjusted",
        "prediction_before",
    ):
        if _present(row.get(field)):
            return _int(row, field)
    return 0


def _ports_from_text(row: RuntimeRow) -> set[int]:
    """Recupera as portas dos campos textuais permitidos, sem consultar dados de avaliação."""
    ports: set[int] = set()
    for field in ("safe_port_text", "common_destination_ports"):
        text = _str(row, field)
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


def _has_strong_noise(row: RuntimeRow) -> bool:
    """Verifica os indicadores de tráfego operacional recorrente usados pela regra experimental."""
    if (
        _bool(row, "operational_noise_hint")
        or _bool(row, "operational_noise_suppressed")
        or _bool(row, "v2_3_operational_noise_context")
        or _bool(row, "ctx_operational_noise_hint")
    ):
        return True

    reason_text = " ".join(
        [
            _str(row, "heuristic_reason"),
            _str(row, "operational_noise_category"),
            _str(row, "operational_noise_reason"),
        ]
    ).lower()
    if any(token in reason_text for token in ("dns", "mdns", "llmnr", "ssdp", "dhcpv6", "icmpv6")):
        return True

    observed_ports = _ports_from_text(row)
    if not observed_ports:
        return False

    heuristic_type = _str(row, "heuristic_attack_type").lower()
    if (
        observed_ports.issubset(LOW_RISK_SERVICE_PORTS)
        and _float(row, "connections") > 10
        and _float(row, "ports") <= 3
        and _float(row, "destination_port_count") <= 3
        and heuristic_type not in {"port_scan", "scan"}
    ):
        return True

    low_diversity = _float(row, "ports") <= 3 and _float(row, "destination_port_count") <= 3
    return low_diversity and bool(observed_ports) and observed_ports.issubset(NOISE_SERVICE_PORTS)


def _strong_port_scan_signal(row: RuntimeRow) -> bool:
    """Verifica se há sinais suficientes de diversidade de portas para a regra experimental."""
    return (
        _float(row, "ports") >= 5
        or _float(row, "destination_port_count") >= 5
        or _float(row, "rolling_distinct_ports") >= 6
        or _bool(row, "ctx_vertical_scan_hint")
        or _bool(row, "ctx_horizontal_scan_hint")
    )


def _supporting_signal_count(row: RuntimeRow) -> int:
    """Conta quantos sinais independentes apoiam a regra experimental."""
    heuristic_type = _str(row, "heuristic_attack_type").lower()
    signals = [
        _float(row, "ensemble_score") >= 0.07,
        _float(row, "heuristic_confidence") >= 0.75,
        heuristic_type in SUSPICIOUS_HEURISTIC_TYPES,
        _float(row, "tcp_syn_count") >= 6,
        _bool(row, "ctx_vertical_scan_hint"),
        _bool(row, "ctx_horizontal_scan_hint"),
    ]
    return sum(1 for signal in signals if signal)


def _runtime_port_scan_hint(row: RuntimeRow) -> bool:
    """Consulta os indícios de varredura disponíveis durante a análise."""
    heuristic_type = _str(row, "heuristic_attack_type").lower()
    return (
        heuristic_type in {"port_scan", "scan"}
        or _bool(row, "ctx_vertical_scan_hint")
        or _bool(row, "ctx_horizontal_scan_hint")
    )


def _balanced_weak_signal_count(row: RuntimeRow) -> int:
    """Conta sinais fracos complementares sem consultar rótulos de avaliação."""
    signals = [
        _float(row, "ports") >= 3,
        _float(row, "destination_port_count") >= 3,
        _float(row, "rolling_distinct_ports") >= 4,
        _float(row, "rolling_connections") >= 5,
        _float(row, "ensemble_score") >= 0.03,
        _float(row, "heuristic_confidence") >= 0.45,
        _bool(row, "ctx_vertical_scan_hint"),
        _bool(row, "ctx_horizontal_scan_hint"),
    ]
    return sum(1 for signal in signals if signal)


def _balanced_micro_scan_pattern(row: RuntimeRow) -> bool:
    """Reconhece o padrão específico observado em janelas curtas de varredura.

    Usa somente contagens e pontuações disponíveis na análise. Evita aplicar a
    regra a tráfego comum quando o histórico é volumoso, mas a janela atual não
    apresenta os sinais exigidos.
    """

    return (
        _float(row, "connections") == 4
        and _float(row, "ports") == 3
        and _float(row, "destination_port_count") == 3
        and _float(row, "destination_ip_count") == 3
        and _float(row, "rolling_distinct_ports") == 3
        and 5 <= _float(row, "rolling_connections") <= 10
        and _float(row, "ensemble_score") >= 0.035
        and _float(row, "heuristic_confidence") >= 0.75
    )


def _result(
    row: RuntimeRow,
    prediction: int,
    attack_type: str,
    rule: str,
    reason: str,
    confidence: float,
    changed: bool,
) -> dict[str, Any]:
    """Monta o resultado experimental e registra a regra e os campos utilizados."""
    return OperationalTuningResult(
        prediction_operational_targeted=prediction,
        operational_attack_type=attack_type,
        operational_rule=rule,
        operational_reason=reason,
        operational_confidence=confidence,
        operational_changed=changed,
        operational_runtime_fields_used=sorted(row.used_fields),
    ).as_dict()


def _unchanged(row: RuntimeRow, reason: str = "sem ajuste operacional") -> dict[str, Any]:
    """Mantém a classificação de base quando nenhuma regra experimental se aplica."""
    base = _base_prediction(row)
    return _result(
        row=row,
        prediction=base,
        attack_type=_str(row, "heuristic_attack_type", "normal"),
        rule="none",
        reason=reason,
        confidence=0.0,
        changed=False,
    )


def apply_operational_targeted_tuning(row: dict[str, Any]) -> dict[str, Any]:
    """Aplica ajustes experimentais usando somente sinais disponíveis na análise.

    Filtra a entrada pela lista ALLOWED_RUNTIME_FIELDS antes de avaliar regras.
    Mesmo que o chamador forneça rótulos ou cenários de avaliação, esses campos
    não ficam disponíveis para as regras.
    """

    runtime = RuntimeRow(row)
    base = _base_prediction(runtime)
    if base == 1:
        return _unchanged(runtime, "predicao operacional original ja positiva")

    connections = _float(runtime, "connections")
    ports = _float(runtime, "ports")
    ensemble_score = _float(runtime, "ensemble_score")
    if connections <= 2 or ports <= 2 or ensemble_score < 0.03:
        return _unchanged(runtime, "volume ou score insuficiente para ajuste operacional")

    if _has_strong_noise(runtime):
        return _unchanged(runtime, "ruido operacional bloqueia promocao")

    if (
        connections >= 3
        and _strong_port_scan_signal(runtime)
        and _supporting_signal_count(runtime) >= 2
        and _runtime_port_scan_hint(runtime)
    ):
        return _result(
            row=runtime,
            prediction=1,
            attack_type="port_scan",
            rule="operational_port_scan_context_strict",
            reason="sinais operacionais fortes de varredura sem depender de rotulo de validacao",
            confidence=0.74,
            changed=True,
        )

    weak_count = _balanced_weak_signal_count(runtime)
    if weak_count >= 5 and _balanced_micro_scan_pattern(runtime):
        return _result(
            row=runtime,
            prediction=1,
            attack_type="port_scan",
            rule="operational_port_scan_context_balanced",
            reason="combinacao conservadora de sinais operacionais fracos de varredura",
            confidence=0.62,
            changed=True,
        )

    return _unchanged(runtime)
