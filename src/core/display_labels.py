"""Rótulos amigaveis para interface, documentos e apresentacao do Sinalyx."""

from __future__ import annotations

from typing import Any


PROFILE_LABELS: dict[str, dict[str, str]] = {
    "legacy_validation": {
        "display_name": "Validacao inicial",
        "description": "Primeira validacao controlada usada como referencia historica.",
    },
    "pre_retrain": {
        "display_name": "Antes do retreino",
        "description": "Estado anterior ao ciclo de retreino hibrido.",
    },
    "hybrid_v2": {
        "display_name": "Retreino inicial",
        "description": "Primeira rodada do retreino hibrido; perfil conservador.",
    },
    "hybrid_v2_1": {
        "display_name": "Perfil sensivel",
        "description": "Rodada com maior sensibilidade, mas mais falsos alarmes.",
    },
    "hybrid_v2_2": {
        "display_name": "Perfil equilibrado",
        "description": "Rodada intermediaria entre deteccao e falsos alarmes.",
    },
    "hybrid_v2_2_operational": {
        "display_name": "Perfil equilibrado ajustado",
        "description": "Perfil equilibrado com reducao de ruido operacional.",
    },
    "hybrid_v2_3": {
        "display_name": "Candidato para rede real",
        "description": "Melhor candidato experimental atual.",
    },
    "hybrid_v2_4": {
        "display_name": "Teste com historico temporal",
        "description": "Experimento diagnostico com analise temporal; nao trouxe ganho operacional.",
    },
    "pre_memory_analysis": {
        "display_name": "Antes da analise com memoria",
        "description": "Ponto de seguranca antes da nova camada de historico.",
    },
    "memory_analysis_candidate": {
        "display_name": "Analise com memoria experimental",
        "description": "Camada experimental que usa historico recente para apoiar a decisao.",
    },
    "memory_analysis_v2": {
        "display_name": "Analise com memoria aprimorada",
        "description": "Experimento com estado multinivel e ensemble por tipo de ameaca.",
    },
    "current": {
        "display_name": "Modelo atual estavel",
        "description": "Modelo atualmente usado pelo sistema.",
    },
}


METRIC_LABELS = {
    "precision": "Acerto dos alertas",
    "recall": "Ataques identificados",
    "f1": "Equilibrio geral",
    "f1_score": "Equilibrio geral",
    "false_positive_rate": "Falsos alarmes",
    "fpr": "Falsos alarmes",
    "false_negative": "Ataques que passaram",
    "false_negative_rate": "Taxa de ataques que passaram",
    "accuracy": "Acerto geral",
}


TERM_LABELS = {
    "Decision Engine": "Motor de decisao",
    "Stateful Decision Engine": "Motor de decisao com historico",
    "Stateful Context": "Analise com memoria",
    "memory_context": "Analise com memoria",
    "historical_context": "Historico recente de comportamento",
    "Ensemble": "Combinacao de sinais",
    "Autoencoder": "Modelo de comportamento normal",
    "Isolation Forest": "Modelo estatistico de anomalias",
    "Anomaly": "Comportamento suspeito",
    "score": "Confianca",
    "threshold": "limite de alerta",
    "block-heavy": "ruido operacional",
    "normal": "trafego normal",
    "suspicious": "comportamento suspeito",
}


CLASS_LABELS = {
    "normal": "Trafego normal",
    "port_scan": "Varredura de Portas",
    "brute_force": "Forca Bruta SSH",
    "syn_flood": "DDoS / SYN Flood",
    "ssh_suspicious": "SSH suspeito",
    "unknown_anomaly": "Anomalia nao classificada",
    "suspicious": "Comportamento suspeito",
}


METRIC_EXPLANATIONS = {
    "precision": "Mostra quantos alertas gerados realmente eram ataques no conjunto validado.",
    "recall": "Mostra quantos ataques do conjunto validado foram identificados.",
    "f1_score": "Resume o equilibrio entre detectar ataques e evitar falsos alarmes.",
    "false_positive_rate": "Mostra a proporcao de trafego normal marcado como alerta.",
    "accuracy": "Mostra o acerto geral, mas pode esconder desequilibrio entre classes.",
}


def get_metric_label(metric_name: str) -> str:
    """Retorna o nome amigavel de uma metrica."""
    key = str(metric_name).strip()
    return METRIC_LABELS.get(key, METRIC_LABELS.get(key.lower(), key))


def explain_metric(metric_name: str) -> str:
    """Explica uma metrica em linguagem curta e apresentavel."""
    key = str(metric_name).strip()
    return METRIC_EXPLANATIONS.get(key, METRIC_EXPLANATIONS.get(key.lower(), "Metrica tecnica do Sinalyx."))


def get_profile_display_name(profile_name: str) -> str:
    """Converte nome interno de perfil para nome amigavel."""
    key = str(profile_name).strip()
    return PROFILE_LABELS.get(key, {}).get("display_name", key)


def get_profile_description(profile_name: str) -> str:
    """Retorna descricao amigavel de um perfil quando conhecida."""
    key = str(profile_name).strip()
    return PROFILE_LABELS.get(key, {}).get("description", "")


def get_friendly_class_name(class_name: str | None) -> str:
    """Converte labels/classes internas em nomes claros para usuário final."""
    key = str(class_name or "").strip().lower()
    return CLASS_LABELS.get(key, str(class_name or "Desconhecido"))


def format_metric_percent(value: Any, *, digits: int = 1) -> str:
    """Formata metricas 0-1 como percentual em portugues."""
    try:
        numeric = float(value)
    except (TypeError, ValueError):
        return "Nao disponivel"
    percent = numeric * 100.0
    formatted = f"{percent:.{digits}f}".replace(".", ",")
    return f"{formatted}%"


def friendly_term(term: str) -> str:
    """Traduz termos tecnicos recorrentes sem alterar nomes internos."""
    return TERM_LABELS.get(term, TERM_LABELS.get(str(term).strip(), str(term)))
