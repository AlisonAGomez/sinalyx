"""Constantes centrais da camada de características do Sinalyx.

Este módulo define as colunas base, as características derivadas, as versoes
logaritmicas e o modo ativo usado pelo projeto.
"""

from __future__ import annotations

BASE_FEATURE_COLUMNS = [
    "connections",
    "bytes",
    "packets",
    "packet_size",
    "ports",
]

DERIVED_FEATURE_COLUMNS = [
    "bytes_per_packet",
    "bytes_per_connection",
    "packets_per_connection",
]

LOG_FEATURE_COLUMNS = [
    f"log1p_{column}"
    for column in BASE_FEATURE_COLUMNS
]

EXTENDED_FEATURE_COLUMNS = [
    *BASE_FEATURE_COLUMNS,
    *DERIVED_FEATURE_COLUMNS,
    *LOG_FEATURE_COLUMNS,
]

# Alternativa simples para voltar ao conjunto canônico de 5 características.
# Se alterar está flag, re-treine os modelos antes de inferir.
USE_EXTENDED_FEATURES = True


def get_feature_columns(use_extended: bool | None = None) -> list[str]:
    """Retorna a lista de características ativas conforme o modo configurado.

    Parâmetros:
        use_extended: Quando None, usa a configuração global do projeto.

    Retorno:
        Lista ordenada de características utilizadas por treino, validação e análise.
    """
    if use_extended is None:
        use_extended = USE_EXTENDED_FEATURES

    if use_extended:
        return EXTENDED_FEATURE_COLUMNS.copy()

    return BASE_FEATURE_COLUMNS.copy()


FEATURE_COLUMNS = get_feature_columns()

RAW_TO_FEATURE_MAPPING = {
    "Flow Duration": "connections",
    "Total Length of Fwd Packets": "bytes",
    "Total Fwd Packets": "packets",
    "Average Packet Size": "packet_size",
    "Destination Port": "ports",
}

KNOWN_LABEL_COLUMNS = [
    "label",
    "Label",
    "final_anomaly",
    "anomaly",
    "is_anomaly",
    "target",
]

BENIGN_TEXT_LABELS = {
    "BENIGN",
    "NORMAL",
    "NORMAL_TRAFFIC",
    "NORMAL TRAFFIC",
    "0",
}


def feature_mode_name(use_extended: bool | None = None) -> str:
    """Retorna um nome curto para o modo de características em uso."""
    if use_extended is None:
        use_extended = USE_EXTENDED_FEATURES
    return "extended" if use_extended else "base"


def describe_active_features(use_extended: bool | None = None) -> str:
    """Gera uma descrição pronta para log das características ativas."""
    columns = get_feature_columns(use_extended)
    return (
        f"mode={feature_mode_name(use_extended)} "
        f"count={len(columns)} "
        f"features={columns}"
    )
