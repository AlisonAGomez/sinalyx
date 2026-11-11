"""Protecoes do fluxo de processamento historico contra alteracao acidental do current."""

from __future__ import annotations

import sys
from pathlib import Path

import pandas as pd
import pytest

from src.core import artifacts
from src.models.autoencoder import AutoencoderConfig
from src.models.isolation_forest import IsolationForestConfig
from src.pipelines import infer_pfsense_batch, train


@pytest.fixture
def artefatos_temporarios(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> dict[str, Path]:
    diretorio = tmp_path / "models"
    autoencoder = diretorio / "autoencoder"
    caminhos = {
        "SCALER_FILE": diretorio / "scaler.joblib",
        "ISOLATION_MODEL_FILE": diretorio / "isolation.pkl",
        "MANIFEST_FILE": diretorio / "manifest.json",
        "ENSEMBLE_CONFIG_FILE": diretorio / "ensemble.json",
        "ISOLATION_STATS_FILE": diretorio / "isolation_stats.json",
        "AUTOENCODER_STATS_FILE": diretorio / "autoencoder_stats.json",
        "AUTOENCODER_THRESHOLD_FILE": diretorio / "threshold.pkl",
        "LEGACY_AUTOENCODER_THRESHOLD_FILE": autoencoder / "threshold.pkl",
        "AUTOENCODER_MODEL_FILE": autoencoder / "model.keras",
    }
    monkeypatch.setattr(artifacts, "MODELS_DIR", diretorio)
    monkeypatch.setattr(artifacts, "AUTOENCODER_DIR", autoencoder)
    for nome, caminho in caminhos.items():
        monkeypatch.setattr(artifacts, nome, caminho)
        caminho.parent.mkdir(parents=True, exist_ok=True)
        caminho.write_text("temporario", encoding="utf-8")
    (diretorio / "nao_relacionado.txt").write_text("preservar", encoding="utf-8")
    return caminhos


def test_limpeza_sem_autorizacao_nao_altera_arquivos_ou_diretorios(
    artefatos_temporarios: dict[str, Path], tmp_path: Path
) -> None:
    with pytest.raises(PermissionError, match="runtime current"):
        artifacts.clear_model_artifacts()

    assert all(caminho.exists() for caminho in artefatos_temporarios.values())
    assert (tmp_path / "models" / "autoencoder").is_dir()
    assert (tmp_path / "models" / "nao_relacionado.txt").exists()


def test_limpeza_autorizada_preserva_comportamento_legado(
    artefatos_temporarios: dict[str, Path], tmp_path: Path
) -> None:
    artifacts.clear_model_artifacts(allow_current_overwrite=True)

    assert all(not caminho.exists() for caminho in artefatos_temporarios.values())
    assert (tmp_path / "models" / "autoencoder").is_dir()
    assert list((tmp_path / "models" / "autoencoder").iterdir()) == []
    assert (tmp_path / "models" / "nao_relacionado.txt").read_text(encoding="utf-8") == "preservar"


@pytest.mark.parametrize("funcao", ["final", "tuned"])
def test_treino_programatico_sem_autorizacao_falha_antes_de_treinar(
    funcao: str,
    artefatos_temporarios: dict[str, Path],
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    def treino_indevido(*args: object, **kwargs: object) -> None:
        pytest.fail("O treino nao deveria iniciar sem autorizacao.")

    monkeypatch.setattr(train, "train_model", treino_indevido)
    monkeypatch.setattr(train, "train_autoencoder", treino_indevido)

    with pytest.raises(PermissionError, match="runtime current"):
        if funcao == "final":
            train.fit_final_models(
                pd.DataFrame(),
                detection_config=IsolationForestConfig(),
                autoencoder_config=AutoencoderConfig(),
            )
        else:
            train.fit_tuned_models(
                X_train_final_df=pd.DataFrame(),
                detection_best_result={},
                autoencoder_best_result={},
                ensemble_best_result={},
            )

    assert all(caminho.exists() for caminho in artefatos_temporarios.values())


@pytest.mark.parametrize("tune", [False, True])
def test_cli_sem_flag_bloqueia_antes_de_carregar_dataset(
    tune: bool, monkeypatch: pytest.MonkeyPatch, capsys: pytest.CaptureFixture[str]
) -> None:
    def leitura_indevida(*args: object, **kwargs: object) -> None:
        pytest.fail("O dataset nao deveria ser carregado sem autorizacao.")

    argumentos = ["train", "--input", "arquivo_inexistente.csv"]
    if tune:
        argumentos.append("--tune")
    monkeypatch.setattr(sys, "argv", argumentos)
    monkeypatch.setattr(train, "load_training_dataframe", leitura_indevida)

    with pytest.raises(SystemExit) as erro:
        train.main()

    assert erro.value.code == 2
    mensagem = capsys.readouterr().err
    assert "historico/legado" in mensagem
    assert "runtime current" in mensagem
    assert "Nenhuma alteracao foi feita" in mensagem


def test_mensagens_orientam_restauracao_sem_sugerir_treino(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    monkeypatch.setattr(artifacts, "MANIFEST_FILE", tmp_path / "manifest.json")
    with pytest.raises(FileNotFoundError) as erro_manifesto:
        artifacts.load_manifest()
    monkeypatch.setattr(artifacts, "models_available", lambda: False)
    with pytest.raises(FileNotFoundError) as erro_bundle:
        artifacts.load_artifact_bundle()

    for erro in (erro_manifesto, erro_bundle):
        mensagem = str(erro.value)
        assert "runtime current" in mensagem
        assert "model registry" in mensagem
        assert "restaure" in mensagem
        assert "src.pipelines.train" not in mensagem


def test_auditoria_mantem_contrato_sem_comando_destrutivo(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    monkeypatch.setattr(infer_pfsense_batch, "MANIFEST_FILE", tmp_path / "manifest.json")
    monkeypatch.setattr(infer_pfsense_batch, "ENSEMBLE_CONFIG_FILE", tmp_path / "ensemble.json")
    monkeypatch.setattr(infer_pfsense_batch, "ISOLATION_MODEL_FILE", tmp_path / "isolation.pkl")
    monkeypatch.setattr(
        infer_pfsense_batch,
        "resolve_autoencoder_threshold_file",
        lambda: tmp_path / "threshold.pkl",
    )

    auditoria = infer_pfsense_batch.audit_model_artifacts(["connections"])

    assert auditoria["recommended_regeneration_command"] is None
    assert "model_registry.json" in auditoria["recommended_action"]
    assert "current" in auditoria["recommended_action"]
    assert {"status", "needs_regeneration", "warnings", "manifest", "ensemble", "score_stats"} <= auditoria.keys()
    assert auditoria["needs_regeneration"] is True


def test_bundle_valido_preserva_carregamento_normal(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    scaler = object()
    isolamento = object()
    autoencoder = object()
    caminho_limiar = tmp_path / "threshold.pkl"
    monkeypatch.setattr(artifacts, "models_available", lambda: True)
    monkeypatch.setattr(artifacts, "load_manifest", lambda: {"n_features": 13})
    monkeypatch.setattr(artifacts, "SCALER_FILE", tmp_path / "scaler.joblib")
    monkeypatch.setattr(artifacts, "ISOLATION_MODEL_FILE", tmp_path / "isolation.pkl")
    monkeypatch.setattr(artifacts, "AUTOENCODER_MODEL_FILE", tmp_path / "model.keras")
    monkeypatch.setattr(
        artifacts.joblib,
        "load",
        lambda caminho: scaler if caminho == artifacts.SCALER_FILE else {
            "model": isolamento,
            "config": {"tipo": "teste"},
            "score_stats": {"mean": 0.1},
        },
    )
    monkeypatch.setattr(artifacts.tf.keras.models, "load_model", lambda *args, **kwargs: autoencoder)
    monkeypatch.setattr(
        artifacts,
        "load_autoencoder_threshold_payload",
        lambda: (caminho_limiar, {"threshold": 0.5, "config": {}, "score_stats": {"mean": 0.2}}),
    )

    bundle = artifacts.load_artifact_bundle()

    assert bundle["manifest"] == {"n_features": 13}
    assert bundle["scaler"] is scaler
    assert bundle["isolation_model"] is isolamento
    assert bundle["autoencoder_model"] is autoencoder
    assert bundle["autoencoder_threshold"] == 0.5
    assert bundle["autoencoder_threshold_path"] == str(caminho_limiar)
