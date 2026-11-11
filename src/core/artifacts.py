"""Utilitarios para lidar com arquivos de apoio salvos do Sinalyx.

Este módulo centraliza funções para limpar, salvar e carregar os arquivos
gerados no treino, como ajuste de escala, Isolation Forest, Autoencoder e manifesto.
"""

from __future__ import annotations

import json
import shutil
from pathlib import Path
from typing import Any

import joblib
import tensorflow as tf

from src.core.paths import (
    AUTOENCODER_DIR,
    AUTOENCODER_MODEL_FILE,
    AUTOENCODER_STATS_FILE,
    AUTOENCODER_THRESHOLD_FILE,
    ENSEMBLE_CONFIG_FILE,
    ISOLATION_MODEL_FILE,
    ISOLATION_STATS_FILE,
    LEGACY_AUTOENCODER_THRESHOLD_FILE,
    MODELS_DIR,
    SCALER_FILE,
)


# O manifesto resume quais arquivos de apoio foram gerados no último treino.
MANIFEST_FILE = MODELS_DIR / "manifest.json"


def ensure_project_dirs() -> None:
    """Garante que as pastas de arquivos de apoio existam antes de salvar arquivos."""
    MODELS_DIR.mkdir(parents=True, exist_ok=True)
    AUTOENCODER_DIR.mkdir(parents=True, exist_ok=True)


def clear_model_artifacts(*, allow_current_overwrite: bool = False) -> None:
    """Remove arquivos de apoio do current apenas no fluxo legado autorizado."""
    if allow_current_overwrite is not True:
        raise PermissionError(
            "Operacao destrutiva bloqueada: os artefatos do runtime current "
            "nao podem ser removidos sem autorizacao explicita. Nenhuma alteracao foi feita."
        )

    ensure_project_dirs()

    # Esses arquivos são recriados quando o fluxo de processamento de treino roda novamente.
    for path in [
        SCALER_FILE,
        ISOLATION_MODEL_FILE,
        MANIFEST_FILE,
        ENSEMBLE_CONFIG_FILE,
        ISOLATION_STATS_FILE,
        AUTOENCODER_STATS_FILE,
        AUTOENCODER_THRESHOLD_FILE,
        LEGACY_AUTOENCODER_THRESHOLD_FILE,
    ]:
        if path.exists():
            path.unlink()

    # O diretório do autoencoder e recriado por completo para evitar sobras.
    if AUTOENCODER_DIR.exists():
        shutil.rmtree(AUTOENCODER_DIR)
    AUTOENCODER_DIR.mkdir(parents=True, exist_ok=True)


def save_manifest(payload: dict[str, Any]) -> None:
    """Salva o manifesto com dados complementares da versao treinada do projeto."""
    ensure_project_dirs()
    with MANIFEST_FILE.open("w", encoding="utf-8") as file:
        json.dump(payload, file, indent=2, ensure_ascii=False)


def load_manifest() -> dict[str, Any]:
    """Carrega o manifesto salvo do treino."""
    if not MANIFEST_FILE.exists():
        raise FileNotFoundError(
            "Manifesto do runtime current ausente. Verifique o perfil current "
            "e o model registry; restaure os artefatos conhecidos antes da inferencia."
        )

    with MANIFEST_FILE.open("r", encoding="utf-8") as file:
        return json.load(file)


def models_available() -> bool:
    """Verifica se os arquivos de apoio essenciais do sistema estao disponiveis."""
    return (
        SCALER_FILE.exists()
        and ISOLATION_MODEL_FILE.exists()
        and AUTOENCODER_MODEL_FILE.exists()
        and resolve_autoencoder_threshold_file().exists()
        and MANIFEST_FILE.exists()
    )


def resolve_autoencoder_threshold_file() -> Path:
    """Resolve o caminho efetivo do limite de classificação do Autoencoder.

    Prioriza o novo caminho em data/models/threshold.pkl, mas aceita o
    arquivo de apoio legado em data/models/autoencoder/threshold.pkl para não quebrar
    inferencias enquanto o treino ainda não for rerodado.
    """
    if AUTOENCODER_THRESHOLD_FILE.exists():
        return AUTOENCODER_THRESHOLD_FILE
    if LEGACY_AUTOENCODER_THRESHOLD_FILE.exists():
        return LEGACY_AUTOENCODER_THRESHOLD_FILE
    return AUTOENCODER_THRESHOLD_FILE


def load_autoencoder_threshold_payload() -> tuple[Path, Any]:
    """Carrega o conteúdo do limite de classificação do Autoencoder com alternativa legado."""
    threshold_path = resolve_autoencoder_threshold_file()
    return threshold_path, joblib.load(threshold_path)


def load_artifact_bundle() -> dict[str, Any]:
    """Carrega todos os arquivos de apoio principais em um unico dicionário."""
    if not models_available():
        raise FileNotFoundError(
            "Artefatos essenciais do runtime current ausentes ou inconsistentes. "
            "Verifique o perfil current e o model registry; restaure os artefatos conhecidos."
        )

    # O bundle unifica tudo o que a análise precisa para funcionar.
    manifest = load_manifest()
    scaler = joblib.load(SCALER_FILE)
    isolation_payload = joblib.load(ISOLATION_MODEL_FILE)
    autoencoder_model = tf.keras.models.load_model(AUTOENCODER_MODEL_FILE, compile=False)
    threshold_path, autoencoder_threshold_payload = load_autoencoder_threshold_payload()

    if isinstance(autoencoder_threshold_payload, dict):
        autoencoder_threshold = float(autoencoder_threshold_payload["threshold"])
    else:
        autoencoder_threshold = float(autoencoder_threshold_payload)

    return {
        "manifest": manifest,
        "scaler": scaler,
        "isolation_model": isolation_payload["model"],
        "isolation_config": isolation_payload.get("config"),
        "isolation_score_stats": isolation_payload.get("score_stats"),
        "autoencoder_model": autoencoder_model,
        "autoencoder_threshold": autoencoder_threshold,
        "autoencoder_threshold_path": str(threshold_path),
        "autoencoder_config": (
            autoencoder_threshold_payload.get("config")
            if isinstance(autoencoder_threshold_payload, dict)
            else None
        ),
        "autoencoder_score_stats": (
            autoencoder_threshold_payload.get("score_stats")
            if isinstance(autoencoder_threshold_payload, dict)
            else None
        ),
    }
