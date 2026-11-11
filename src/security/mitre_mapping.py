"""Mapeamento MITRE ATT&CK usado apenas como enriquecimento explicativo.

O mapeamento não participa da classificação, do ensemble ou do motor de
decisão. Ele traduz classes já validadas para referencias reconheciveis em
relatorios e apresentacoes.
"""

from __future__ import annotations

from typing import Any


MITRE_MAPPING: dict[str, dict[str, Any] | None] = {
    "normal": None,
    "port_scan": {
        "tactic": "Reconhecimento",
        "technique_id": "T1595",
        "technique": "Active Scanning",
        "friendly_description": "Varredura ativa de portas ou servicos.",
    },
    "brute_force": {
        "tactic": "Acesso a credenciais",
        "technique_id": "T1110",
        "technique": "Brute Force",
        "friendly_description": "Multiplas tentativas de acesso contra servico sensivel.",
    },
    "syn_flood": {
        "tactic": "Impacto",
        "technique_id": "T1498",
        "technique": "Network Denial of Service",
        "subtechnique_id": "T1498.001",
        "subtechnique": "Direct Network Flood",
        "friendly_description": (
            "Tentativa de indisponibilizar servico por grande volume de conexoes."
        ),
    },
    "suspicious": {
        "tactic": None,
        "technique_id": None,
        "technique": "MITRE indefinido",
        "friendly_description": "Comportamento suspeito sem tecnica validada no projeto.",
    },
    "unknown_anomaly": {
        "tactic": None,
        "technique_id": None,
        "technique": "MITRE indefinido",
        "friendly_description": "Anomalia nao classificada sem tecnica MITRE atribuida.",
    },
}


ALIASES = {
    "ddos": "syn_flood",
    "ddos / syn flood": "syn_flood",
    "syn flood": "syn_flood",
    "forca_bruta": "brute_force",
    "forca bruta ssh": "brute_force",
    "brute force": "brute_force",
    "brute_force_suspected": "brute_force",
    "tentativa provavel de forca bruta": "brute_force",
    "varredura de portas": "port_scan",
    "unknown anomaly": "unknown_anomaly",
    "anomalia nao classificada": "unknown_anomaly",
}


def normalize_attack_type(attack_type: str | None) -> str:
    """Normaliza nomes internos e alguns nomes amigaveis."""
    value = str(attack_type or "unknown_anomaly").strip().lower()
    value = value.replace("-", "_")
    return ALIASES.get(value, value)


def get_mitre_mapping(attack_type: str | None) -> dict[str, Any] | None:
    """Retorna o mapeamento MITRE para uma classe validada, quando existir."""
    normalized = normalize_attack_type(attack_type)
    mapping = MITRE_MAPPING.get(normalized)
    if mapping is None:
        return None
    return {"attack_type": normalized, **mapping}


def has_mitre_mapping(attack_type: str | None) -> bool:
    """Indica se a classe possui tecnica MITRE validada no projeto."""
    mapping = get_mitre_mapping(attack_type)
    return bool(mapping and mapping.get("technique_id"))


def enrich_with_mitre(payload: dict[str, Any] | str | None) -> dict[str, Any] | None:
    """Adiciona campo mitre opcional a um conteúdo sem alterar campos existentes."""
    if isinstance(payload, dict):
        attack_type = payload.get("attack_type") or payload.get("heuristic_attack_type")
        enriched = dict(payload)
        enriched["mitre"] = get_mitre_mapping(str(attack_type or ""))
        return enriched
    return get_mitre_mapping(str(payload or ""))
