"""Contrato aditivo com análise sintética e gravação real de JSON."""

import asyncio
import copy
import os

import pandas as pd
import pytest
from sqlalchemy import create_engine, select
from sqlalchemy.orm import sessionmaker
from sqlalchemy.pool import StaticPool

from tests.support.api import multipart, preparar_fluxo, requisicao


@pytest.fixture
def registro():
    return {
        "window_id": "1", "final_label": "normal", "is_anomaly": False,
        "attack_type": "normal", "risk_level": "low", "confidence": 0.81,
        "pred_decision_engine": False, "explanation": "decisão original",
        "decision_source": "base", "decision_reason": "motivo original",
        "agreement_level": "partial", "conflict_winner": "normal",
        "base_attack_support": 0.13, "base_negative_support": 0.87,
        "pred_if": -1, "label_if": "anomaly", "score_if": -0.123,
        "score_if_normalized": 0.72, "if_confidence": 0.73,
        "pred_ae": 1, "label_ae": "normal", "score_ae": 0.123,
        "score_ae_log": -2.095, "score_ae_normalized": 0.21,
        "ae_confidence": 0.79, "ae_threshold_raw": 0.456, "ae_threshold_log": -0.785,
        "pred_heuristic": 0, "heuristic_attack_type": "normal",
        "heuristic_confidence": 0.88, "heuristic_reason": "heurística original",
        "pred_ensemble": 0, "score_ensemble": 0.321, "ensemble_threshold": 0.654,
        "runtime_profile": "current", "ensemble_if_weight": 0.6, "ensemble_ae_weight": 0.4,
        "ensemble_if_pred": -1, "ensemble_ae_pred": 1, "ensemble_if_alert_score": 0.77,
        "ensemble_agreement_score": 0.1, "ensemble_conflict_penalty": 0.12,
        "ensemble_ae_risk_score": 0.23, "ensemble_ae_risk_band": "low",
        "ai_support": True, "ai_support_conservative": True,
        "ai_support_type": "auxiliar", "ai_support_level": "low",
        "ai_support_reason": "apoio somente", "ai_support_signals": '{"signal": true}',
        "ensemble_score": 0.321, "autoencoder_score": 0.123, "isolation_score": -0.123,
    }


def test_contrato_completo_sem_recalculo_ou_mutacao(registro):
    from src.api.services import _build_results_payload
    from src.api.schemas import ModelOutputsPayload
    from src.services.pfsense_incremental_service import _extract_model_outputs
    original = copy.deepcopy(registro)
    item = _build_results_payload(pd.DataFrame([registro]))[0]
    saidas = item["model_outputs"]
    assert saidas == _extract_model_outputs(registro)
    assert ModelOutputsPayload(**saidas).model_dump() == saidas
    assert [len(saidas[k]) for k in ("isolation_forest", "autoencoder", "heuristic", "ensemble", "ai_support", "decision_engine")] == [5, 8, 4, 13, 6, 13]
    assert saidas["isolation_forest"]["raw_score"] == registro["score_if"]
    assert saidas["autoencoder"]["threshold_log"] == registro["ae_threshold_log"]
    for bloco, mapa in {
        "isolation_forest": {"pred": "pred_if", "label": "label_if", "raw_score": "score_if", "normalized_score": "score_if_normalized", "confidence": "if_confidence"},
        "autoencoder": {"pred": "pred_ae", "label": "label_ae", "raw_score": "score_ae", "log_score": "score_ae_log", "normalized_score": "score_ae_normalized", "confidence": "ae_confidence", "threshold_raw": "ae_threshold_raw", "threshold_log": "ae_threshold_log"},
        "heuristic": {"pred": "pred_heuristic", "attack_type": "heuristic_attack_type", "confidence": "heuristic_confidence", "reason": "heuristic_reason"},
        "ensemble": {"pred": "pred_ensemble", "score": "score_ensemble", "threshold": "ensemble_threshold", "runtime_profile": "runtime_profile", "if_weight": "ensemble_if_weight", "ae_weight": "ensemble_ae_weight"},
        "ai_support": {"enabled": "ai_support", "conservative": "ai_support_conservative", "type": "ai_support_type", "level": "ai_support_level", "reason": "ai_support_reason"},
    }.items():
        for destino, origem in mapa.items():
            assert saidas[bloco][destino] == registro[origem]
    for campo in ("if_pred", "ae_pred", "if_alert_score", "agreement_score", "conflict_penalty", "ae_risk_score", "ae_risk_band"):
        assert saidas["ensemble"][campo] == registro["ensemble_" + campo]
    for campo, valor in saidas["decision_engine"].items():
        assert valor == registro["pred_decision_engine" if campo == "pred" else campo]
    registro["ai_support"] = False
    assert _extract_model_outputs(registro)["decision_engine"] == saidas["decision_engine"]
    registro["ai_support"] = True
    assert registro == original
    for chave, valor in item.items():
        if chave not in {"model_outputs", "ai_support_signals"}:
            assert valor == registro[chave]


def test_ausencias_e_valores_nao_finitos():
    from src.services.model_outputs import montar_model_outputs
    saidas = montar_model_outputs({"score_if": float("nan"), "score_ae": float("inf")})
    assert saidas["isolation_forest"]["raw_score"] is None
    assert saidas["autoencoder"]["raw_score"] is None
    assert saidas["ai_support"]["signals"] == {}
    assert saidas["decision_engine"]["pred"] is None


@pytest.mark.parametrize("backend", ["sqlite", "postgresql"])
def test_post_raw_json_get_e_live(ambiente, monkeypatch, registro, backend):
    from src.db import repository, models
    from src.services.pfsense_incremental_service import _extract_model_outputs
    main, services, _ = ambiente
    url = os.environ.get("SINALYX_TEST_POSTGRES_URL")
    if backend == "postgresql" and not url:
        pytest.skip("PostgreSQL descartável: definir SINALYX_TEST_POSTGRES_URL")
    motor = create_engine(url) if backend == "postgresql" else create_engine(
        "sqlite://", connect_args={"check_same_thread": False}, poolclass=StaticPool)
    # A URL de QA deve apontar exclusivamente para banco descartável vazio.
    models.Base.metadata.create_all(motor)
    fabrica = sessionmaker(bind=motor)
    monkeypatch.setattr(repository, "SessionLocal", fabrica)
    monkeypatch.setattr(repository, "_require_database", lambda: None)
    preparar_fluxo(monkeypatch, services)
    monkeypatch.setattr(services, "run_inference", lambda **kw: (pd.DataFrame([registro]), {}))
    monkeypatch.setattr(services, "save_analysis_to_database", repository.save_analysis)
    monkeypatch.setattr(services, "is_database_available", lambda: True)
    try:
        corpo, headers = multipart(b"log sintetico")
        status, resposta, _ = asyncio.run(requisicao(main.app, corpo, headers=headers))
        assert status == 200
        item = resposta["results"][0]
        assert {"final_label", "confidence", "ensemble_score", "ai_support", "ai_support_signals"} <= item.keys()
        assert resposta["persistence"]["database_saved"] is True
        with fabrica() as sessao:
            salvo = sessao.execute(select(models.AnalysisResult).where(models.AnalysisResult.analysis_id == resposta["analysis_id"])).scalar_one()
            assert salvo.raw_json == item
        status, historico, _ = asyncio.run(requisicao(main.app, b"", caminho=f'/analyses/{resposta["analysis_id"]}/results', metodo="GET"))
        assert status == 200
        assert historico["results"][0]["model_outputs"] == item["model_outputs"]
        assert historico["data"]["results"] == historico["results"]
        repository.save_live_windows([{
            "window_uid": resposta["analysis_id"], "execution_id": "qa-contrato",
            "local_log_path": "sintetico.log", "model_outputs": _extract_model_outputs(registro),
        }])
        with fabrica() as sessao:
            janela = sessao.execute(select(models.LivePfSenseWindow).where(models.LivePfSenseWindow.window_uid == resposta["analysis_id"])).scalar_one()
            assert janela.model_outputs_json == item["model_outputs"]
        legado = {k: v for k, v in item.items() if k != "model_outputs"}
        legado["campo_legado_adicional"] = {"preservar": True}
        repository.save_analysis(resposta, [legado])
        status, antigo, _ = asyncio.run(requisicao(main.app, b"", caminho=f'/analyses/{resposta["analysis_id"]}/results', metodo="GET"))
        assert status == 200
        assert "model_outputs" not in antigo["results"][0]
        assert antigo["results"][0]["campo_legado_adicional"] == {"preservar": True}
    finally:
        motor.dispose()
