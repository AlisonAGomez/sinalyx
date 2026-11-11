"""Explica a influência dos componentes pelo método Shapley.

Reutiliza os sinais já calculados dos modelos e das regras. A comparação das
combinações serve para explicar o resultado; não executa novamente os modelos
nem substitui a decisão oficial.
"""

from __future__ import annotations

from copy import deepcopy
from itertools import combinations
from math import factorial, fsum, isfinite
from typing import Any, Mapping

from src.models.decision_engine import DecisionConfig, decide_attack
from src.models.ensemble import EnsembleConfig, _build_support_snapshot

PARTICIPANTES = ("autoencoder", "isolation_forest", "security_rules")
TOLERANCIA = 1e-12
# Somente campos usados na decisão; endereços IP e rótulos de avaliação ficam de fora.
CAMPOS_CONTEXTO = frozenset({
    "protocol", "proto", "action", "pf_action", "blocked_count", "block_count",
    "passed_count", "pass_count", "destination_ip_count", "dst_ip_count",
    "common_destination_ports", "destination_ports", "destination_port", "dst_port",
    "destination_port_min", "destination_port_max", "destination_port_count",
    "ports", "connections", "packets", "event_count", "tcp_syn_count", "tcp_pa_count",
})
CAMPOS_DECISAO = (
    "is_anomaly", "final_label", "attack_type", "decision_source",
    "base_attack_support", "base_negative_support", "confidence", "agreement_level",
)
CAMPOS_NUMERICOS = ("base_attack_support", "base_negative_support", "confidence")


def gerar_coalizoes() -> tuple[tuple[str, ...], ...]:
    """Lista todas as combinações dos três componentes usadas no cálculo Shapley."""
    return tuple(c for n in range(4) for c in combinations(PARTICIPANTES, n))


def _chave(coalizao: tuple[str, ...]) -> str:
    """Cria o nome estável de uma combinação de componentes, incluindo a combinação vazia."""
    return "+".join(coalizao) or "empty"


def _contexto_seguro(contexto: Mapping[str, Any] | None) -> dict[str, Any]:
    """Copia somente os campos de contexto permitidos para a explicação."""
    return {k: deepcopy(v) for k, v in (contexto or {}).items() if k in CAMPOS_CONTEXTO}


def _detector(output: Mapping[str, Any], presente: bool) -> dict[str, Any]:
    """Confere os sinais já calculados de um modelo antes de usá-los na explicação."""
    sinal = {k: output[k] for k in ("pred", "raw_score", "normalized_score", "confidence")}
    for k, v in sinal.items():
        if not isfinite(float(v)):
            raise ValueError(f"Sinal não finito: {k}")
    if sinal["pred"] not in (0, 1):
        raise ValueError("Predição deve ser 0 ou 1.")
    if any(not 0 <= float(sinal[k]) <= 1 for k in ("normalized_score", "confidence")):
        raise ValueError("Score normalizado e confiança devem estar entre 0 e 1.")
    return deepcopy(sinal) if presente else dict(
        pred=0, raw_score=0.0, normalized_score=0.0, confidence=0.0,
    )


def _regras(output: Mapping[str, Any], presente: bool) -> dict[str, Any]:
    """Confere os campos já calculados pela heurística antes de usá-los na explicação."""
    campos = ("heuristic_detected_attack", "heuristic_confidence", "attack_type", "heuristic_reason")
    sinal = {k: deepcopy(output[k]) for k in campos}
    if not isfinite(float(sinal["heuristic_confidence"])) or not 0 <= float(sinal["heuristic_confidence"]) <= 1:
        raise ValueError("Confiança heurística inválida.")
    return sinal if presente else dict(
        heuristic_detected_attack=False, heuristic_confidence=0.0,
        attack_type="normal", heuristic_reason="",
    )


def atribuir_valores(valores: Mapping[str, float], *, tolerancia: float = TOLERANCIA) -> dict[str, Any]:
    """Shapley combinatório exato para as oito avaliações de um jogo fixo."""
    if not isfinite(tolerancia) or tolerancia <= 0:
        raise ValueError("Tolerância deve ser positiva e finita.")
    coalizoes = gerar_coalizoes()
    if set(valores) != {_chave(c) for c in coalizoes}:
        raise ValueError("São necessárias exatamente as oito coalizões.")
    if any(not isfinite(v) or not -1 <= v <= 1 for v in valores.values()):
        raise ValueError("Valores devem ser finitos no eixo [-1, 1].")
    contribuicoes = {}
    for participante in PARTICIPANTES:
        marginais = []
        for coalizao in coalizoes:
            if participante in coalizao:
                continue
            uniao = tuple(p for p in PARTICIPANTES if p in coalizao or p == participante)
            peso = factorial(len(coalizao)) * factorial(2 - len(coalizao)) / factorial(3)
            marginais.append(peso * (valores[_chave(uniao)] - valores[_chave(coalizao)]))
        contribuicoes[participante] = fsum(marginais)
    total = fsum(abs(v) for v in contribuicoes.values())
    relevante = total > tolerancia
    span = valores[_chave(PARTICIPANTES)] - valores["empty"]
    residual = fsum(contribuicoes.values()) - span
    if abs(residual) > tolerancia:
        raise ArithmeticError("Eficiência Shapley fora da tolerância.")
    return {
        "methodology": "exact_shapley_v1",
        "baseline_type": "zero_signal_reference",
        "baseline_value": valores["empty"], "full_value": valores[_chave(PARTICIPANTES)],
        "decision_span": span, "efficiency_residual": residual,
        "tolerance": tolerancia, "relevant_contribution": relevante,
        "components": {p: {
            "shapley_value": v, "absolute_contribution": abs(v),
            "relative_share_percent": 100 * abs(v) / total if relevante else 0.0,
            "direction": "neutral" if abs(v) <= tolerancia else (
                "toward_anomaly" if v > 0 else "toward_normal"
            ),
        } for p, v in contribuicoes.items()},
    }


def verificar_paridade(decisao: Mapping[str, Any], oficial: Mapping[str, Any], *, tolerancia: float = TOLERANCIA) -> dict[str, Any]:
    """Falha explícita em qualquer campo ausente/divergente; não agrega resultados."""
    erros = {}
    for campo in CAMPOS_DECISAO:
        if campo not in decisao or campo not in oficial:
            raise ValueError(f"Campo obrigatório para paridade ausente: {campo}")
        if campo in CAMPOS_NUMERICOS:
            erro = abs(float(decisao[campo]) - float(oficial[campo]))
            if not isfinite(erro) or erro > tolerancia:
                raise ValueError(f"Paridade divergente: {campo}")
            erros[campo] = erro
        elif decisao[campo] != oficial[campo]:
            raise ValueError(f"Paridade divergente: {campo}")
    return erros


def calculate_component_contribution(
    *, if_output: Mapping[str, Any], ae_output: Mapping[str, Any],
    heuristic_output: Mapping[str, Any], features: Mapping[str, Any] | None = None,
    metadata: Mapping[str, Any] | None = None, runtime_profile: str,
    ensemble_config: EnsembleConfig, decision_config: DecisionConfig,
    ae_reference_threshold: float, tolerance: float = TOLERANCIA,
) -> dict[str, Any]:
    """Recombina saídas prontos com configs efetivas explícitas, sem I/O/inferência.

    O contexto operacional fica fixo nas coalizões. security_rules representa
    somente o output heurístico, não as políticas internas do Decision Engine.
    """
    if runtime_profile != ensemble_config.profile_name or runtime_profile != decision_config.profile_name:
        raise ValueError("Perfis das configurações efetivas devem coincidir.")
    if not isfinite(ae_reference_threshold) or ae_reference_threshold <= 0:
        raise ValueError("Limiar de referência AE inválido.")
    coalizoes = {}
    valores = {}
    for coalizao in gerar_coalizoes():
        sinal_if = _detector(if_output, "isolation_forest" in coalizao)
        sinal_ae = _detector(ae_output, "autoencoder" in coalizao)
        regras = _regras(heuristic_output, "security_rules" in coalizao)
        ensemble = _build_support_snapshot(
            if_output=sinal_if, ae_output=sinal_ae, config=ensemble_config,
            ae_reference_threshold_raw=ae_reference_threshold,
        )
        decisao = decide_attack(
            if_output=sinal_if, ae_output=sinal_ae, heuristic_output=regras,
            ensemble_output=ensemble, features=_contexto_seguro(features),
            metadata=_contexto_seguro(metadata), config=decision_config,
            runtime_profile=runtime_profile,
            prioritize_recall=decision_config.prioritize_recall,
            prioritize_precision=decision_config.prioritize_precision,
        )
        chave = _chave(coalizao)
        valores[chave] = float(decisao["confidence"]) * (1 if decisao["is_anomaly"] else -1)
        coalizoes[chave] = {
            "members": list(coalizao), "value": valores[chave],
            "decision": {k: decisao[k] for k in CAMPOS_DECISAO},
            "ensemble": {k: ensemble[k] for k in (
                "pred", "score", "threshold", "runtime_profile", "if_weight", "ae_weight",
                "ae_reference_threshold_raw", "ae_risk_band", "if_stability_score",
            )},
        }
    return {**atribuir_valores(valores, tolerancia=tolerance), "coalitions": coalizoes}
