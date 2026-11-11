"""Funções de engenharia de características do Sinalyx.

Este módulo garante que as transformacoes numéricas sejam identicas entre
preparo de dados, treino, validação e análise.
"""

from __future__ import annotations

import numpy as np
import pandas as pd

from src.features.constants import (
    BASE_FEATURE_COLUMNS,
    DERIVED_FEATURE_COLUMNS,
    FEATURE_COLUMNS,
    LOG_FEATURE_COLUMNS,
    get_feature_columns,
)


def sanitize_numeric_frame(df: pd.DataFrame) -> pd.DataFrame:
    """Converte um Tabela de dados para numérico e elimina NaN/infinitos.

    Parâmetros:
        df: Tabela de dados com colunas que devem ser tratadas como numéricas.

    Retorno:
        Tabela de dados numérico, com valores finitos e dtype float.
    """
    output = df.copy()
    for column in output.columns:
        output[column] = pd.to_numeric(output[column], errors="coerce")

    output = output.replace([np.inf, -np.inf], np.nan)
    output = output.fillna(0.0)
    return output.astype(float)


def safe_ratio(numerator: pd.Series, denominator: pd.Series) -> pd.Series:
    """
    Calcula uma razão robusta, protegendo contra divisão por zero e infinitos.
    """
    safe_denominator = pd.to_numeric(denominator, errors="coerce").replace(0, np.nan)
    result = pd.to_numeric(numerator, errors="coerce") / safe_denominator
    return result.replace([np.inf, -np.inf], np.nan).fillna(0.0)


def build_base_feature_frame(df: pd.DataFrame) -> pd.DataFrame:
    """Normaliza e seleciona apenas as 5 características canônicas do projeto."""
    missing = [column for column in BASE_FEATURE_COLUMNS if column not in df.columns]
    if missing:
        raise ValueError(f"Features base ausentes: {missing}")

    return sanitize_numeric_frame(df[BASE_FEATURE_COLUMNS].copy())


def add_engineered_features(df: pd.DataFrame) -> pd.DataFrame:
    """Gera características derivadas e log-transformadas a partir das características base.

    Parâmetros:
        df: Tabela de dados contendo as características canônicas.

    Retorno:
        Tabela de dados com características base + derivadas + log1p.
    """
    working = build_base_feature_frame(df)

    working["bytes_per_packet"] = safe_ratio(
        working["bytes"],
        working["packets"],
    )
    working["bytes_per_connection"] = safe_ratio(
        working["bytes"],
        working["connections"],
    )
    working["packets_per_connection"] = safe_ratio(
        working["packets"],
        working["connections"],
    )

    for column in BASE_FEATURE_COLUMNS:
        working[f"log1p_{column}"] = np.log1p(working[column].clip(lower=0))

    ordered_columns = [
        *BASE_FEATURE_COLUMNS,
        *DERIVED_FEATURE_COLUMNS,
        *LOG_FEATURE_COLUMNS,
    ]
    return sanitize_numeric_frame(working[ordered_columns])


def select_active_feature_frame(
    df: pd.DataFrame,
    use_extended: bool | None = None,
) -> pd.DataFrame:
    """Constrói a matriz final de características usada por treino e análise.

    Parâmetros:
        df: Tabela de dados contendo ao menos as características base.
        use_extended: Quando None, usa a configuração global do projeto.

    Retorno:
        Tabela de dados com as características ativas, na ordem correta.
    """
    selected_columns = get_feature_columns(use_extended)

    if selected_columns == BASE_FEATURE_COLUMNS:
        return build_base_feature_frame(df)

    extended_df = add_engineered_features(df)
    missing = [column for column in selected_columns if column not in extended_df.columns]
    if missing:
        raise ValueError(f"Features estendidas ausentes: {missing}")

    return sanitize_numeric_frame(extended_df[selected_columns])


def to_feature_matrix(df: pd.DataFrame) -> np.ndarray:
    """Converte um Tabela de dados de características em matriz numpy finita."""
    return np.nan_to_num(
        df[FEATURE_COLUMNS].to_numpy(dtype=float),
        nan=0.0,
        posinf=0.0,
        neginf=0.0,
    )
