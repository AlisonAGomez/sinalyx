"""Explicabilidade aditiva no fluxo de processamento, HTTP e gravação JSON."""

import asyncio
import copy
import json
from unittest.mock import Mock

import pandas as pd
import pytest
from pydantic import ValidationError

from tests.support.api import multipart, preparar_fluxo, requisicao
from src.services.component_contributions import (
    ComponentContributionsPayload, calcular_contribuicoes_seguras, projetar_contribuicoes,
)


@pytest.fixture
def sinais(entrada):
    from src.models.decision_engine import decide_attack
    from src.models.ensemble import _build_support_snapshot
    ensemble = _build_support_snapshot(if_output=entrada["if_output"], ae_output=entrada["ae_output"],
        config=entrada["ensemble_config"], ae_reference_threshold_raw=entrada["ae_reference_threshold"])
    decisao = decide_attack(if_output=entrada["if_output"], ae_output=entrada["ae_output"],
        heuristic_output=entrada["heuristic_output"], ensemble_output=ensemble,
        config=entrada["decision_config"], runtime_profile=entrada["runtime_profile"])
    return dict(entrada, decisao_oficial=decisao, ensemble_oficial=ensemble)


def test_contrato_e_serializacao(sinais):
    resultado = calcular_contribuicoes_seguras(**sinais)
    assert resultado is not None
    assert resultado["methodology"] == "exact_shapley_v1"
    assert resultado["baseline_type"] == "zero_signal_reference"
    assert set(resultado["components"]) == {"autoencoder", "isolation_forest", "security_rules"}
    assert "coalitions" not in resultado
    assert sum(c["relative_share_percent"] for c in resultado["components"].values()) == pytest.approx(100)
    assert projetar_contribuicoes(json.dumps(resultado)) == resultado
    assert ComponentContributionsPayload.model_validate(resultado).model_dump() == resultado
    invalido = copy.deepcopy(resultado)
    invalido["components"]["autoencoder"]["direction"] = "probability"
    with pytest.raises(ValidationError):
        ComponentContributionsPayload.model_validate(invalido)


@pytest.mark.parametrize("falha", ["sinal", "paridade", "serializacao"])
def test_falha_nao_muda_decisao_nem_expoe_erro(sinais, monkeypatch, caplog, falha):
    from src.models import component_contribution
    original = copy.deepcopy(sinais)
    if falha == "sinal":
        sinais["if_output"] = {}
    elif falha == "paridade":
        sinais["decisao_oficial"]["confidence"] = 0.01
    else:
        monkeypatch.setattr(component_contribution, "calculate_component_contribution",
            Mock(side_effect=TypeError("CAMINHO_SECRETO_SINTETICO")))
    antes = copy.deepcopy(sinais)
    assert calcular_contribuicoes_seguras(**sinais) is None
    assert sinais == antes
    assert "metadado indisponivel" in caplog.text
    assert "CAMINHO_SECRETO_SINTETICO" not in caplog.text
    assert original["ensemble_oficial"] == sinais["ensemble_oficial"]


def test_json_invalido_nao_vira_percentual_zero(caplog):
    assert projetar_contribuicoes('{"secreto": "NAO_EXIBIR"}') is None
    assert "serializacao" in caplog.text and "NAO_EXIBIR" not in caplog.text


def test_ground_truth_filtrado_antes_do_calculo(sinais, monkeypatch):
    from src.models import component_contribution as modulo
    espiao = Mock(wraps=modulo.calculate_component_contribution)
    monkeypatch.setattr(modulo, "calculate_component_contribution", espiao)
    sinais["features"] = dict(label="ataque", scenario="syn_flood", target=1, src_ip="SINTETICO")
    sinais["metadata"] = dict(filename="sintetico", diagnostic_category="erro", error_type="FN")
    assert calcular_contribuicoes_seguras(**sinais) is not None
    assert espiao.call_args.kwargs["features"] == {}
    assert espiao.call_args.kwargs["metadata"] == {}


def test_normal_sem_evidencia_tem_shares_zero(entrada):
    from src.models.ensemble import _build_support_snapshot
    from src.models.decision_engine import decide_attack
    for campo in ("if_output", "ae_output"):
        entrada[campo] = dict(pred=0, raw_score=0.0, normalized_score=0.0, confidence=0.0)
    entrada["heuristic_output"] = dict(heuristic_detected_attack=False,
        heuristic_confidence=0.0, attack_type="normal", heuristic_reason="")
    ensemble = _build_support_snapshot(if_output=entrada["if_output"], ae_output=entrada["ae_output"],
        config=entrada["ensemble_config"], ae_reference_threshold_raw=entrada["ae_reference_threshold"])
    decisao = decide_attack(if_output=entrada["if_output"], ae_output=entrada["ae_output"],
        heuristic_output=entrada["heuristic_output"], ensemble_output=ensemble, runtime_profile="balanced")
    resultado = calcular_contribuicoes_seguras(**entrada, decisao_oficial=decisao, ensemble_oficial=ensemble)
    assert resultado is not None
    assert all(c["shapley_value"] == c["relative_share_percent"] == 0 for c in resultado["components"].values())


def test_regressao_355_janelas_no_pipeline_sem_nova_inferencia(monkeypatch):
    from pathlib import Path
    from src.pipelines import infer_pfsense_batch as pipeline
    from src.models import ensemble as combinador
    from src.features.constants import FEATURE_COLUMNS
    from scripts.evaluate_component_contribution_tcc import COLUNAS, CENARIOS, preparar_entrada, resolver_current

    raiz = Path(__file__).resolve().parents[1] / "data/processed/pfsense/validation_runs/20260911_current_tcc"
    if not raiz.exists():
        pytest.skip("Conjunto histórico local indisponível")
    campos_oficiais = ["pred_decision_engine", "is_anomaly", "final_label", "attack_type", "risk_level",
                       "confidence", "decision_source", "base_attack_support", "base_negative_support"]
    colunas = COLUNAS | set(FEATURE_COLUMNS) | set(campos_oficiais)
    oficial = pd.concat([pd.read_csv(raiz / c / "inference_results.csv",
        usecols=lambda coluna: coluna in colunas, float_precision="round_trip") for c in CENARIOS], ignore_index=True)
    oficial = oficial.astype(object).where(pd.notna(oficial), None)
    config_ensemble, config_decisao, _ = resolver_current("balanced")
    entradas = [preparar_entrada(linha, config_ensemble, config_decisao) for linha in oficial.to_dict("records")]
    saidas_if = [{**e["if_output"], "label": "anomaly" if e["if_output"]["pred"] else "normal"} for e in entradas]
    saidas_ae = [{**e["ae_output"], "label": "anomaly" if e["ae_output"]["pred"] else "normal",
                 "log_score": 0.0, "threshold_raw": 9.158707301456236, "threshold_log": 0.0} for e in entradas]
    # Reprocessamento de saídas já calculadas. A chamada oficial do Ensemble permanece real.
    pred_if, pred_ae = Mock(return_value=saidas_if), Mock(return_value=saidas_ae)
    for alvo in (pipeline, combinador):
        monkeypatch.setattr(alvo, "predict_with_details", pred_if)
        monkeypatch.setattr(alvo, "predict_autoencoder_with_details", pred_ae)
    monkeypatch.setattr(combinador, "_ensemble_config", config_ensemble)
    monkeypatch.setattr(pipeline, "get_loaded_detection_bundle", lambda: {"replay": True})
    monkeypatch.setattr(pipeline, "get_loaded_autoencoder_bundle", lambda: {"threshold": 9.158707301456236})
    regras = Mock(side_effect=[e["heuristic_output"] for e in entradas])
    monkeypatch.setattr(pipeline, "analyze_behavior", regras)
    monkeypatch.setattr(pipeline, "refine_heuristic_outputs_with_window_context", lambda registros, outputs: outputs)
    monkeypatch.setattr(pipeline, "audit_model_artifacts", lambda *_: {"warnings": []})
    raw = pd.DataFrame([{**e["features"], **{c: oficial.iloc[i][c] for c in FEATURE_COLUMNS}}
                        for i, e in enumerate(entradas)])
    depois, _ = pipeline.run_inference_from_frame(raw_df=raw, runtime_profile="balanced", load_models=False)
    assert len(depois) == 355
    for campo in campos_oficiais:
        assert depois[campo].tolist() == oficial[campo].tolist(), campo
    # O fluxo de processamento anterior já consulta os saídas diretamente e dentro do Ensemble.
    # Shapley não acrescenta nenhuma chamada às duas leituras preexistentes.
    assert pred_if.call_count == pred_ae.call_count == 2
    assert regras.call_count == 355
    assert all(isinstance(v, dict) for v in depois["component_contributions"])
    negativos = [v["components"]["isolation_forest"] for v in depois["component_contributions"]
                 if v["components"]["isolation_forest"]["direction"] == "toward_normal"]
    assert len(negativos) == 3 and all(v["shapley_value"] < 0 for v in negativos)


@pytest.fixture
def pipeline_sintetico(sinais, monkeypatch):
    from src.pipelines import infer_pfsense_batch as pipeline
    from src.models.ensemble import _build_support_snapshot
    from src.features.constants import FEATURE_COLUMNS
    raw = pd.DataFrame([{c: 1.0 for c in FEATURE_COLUMNS}])
    saida_if = {**sinais["if_output"], "label": "anomaly"}
    saida_ae = {**sinais["ae_output"], "label": "anomaly", "log_score": 1.0,
                "threshold_raw": 9.0, "threshold_log": 1.0}
    monkeypatch.setattr(pipeline, "get_loaded_detection_bundle", lambda: {})
    monkeypatch.setattr(pipeline, "get_loaded_autoencoder_bundle", lambda: {"threshold": 9.0})
    pred_if, pred_ae = Mock(return_value=[saida_if]), Mock(return_value=[saida_ae])
    regras = Mock(return_value=sinais["heuristic_output"])
    monkeypatch.setattr(pipeline, "predict_with_details", pred_if)
    monkeypatch.setattr(pipeline, "predict_autoencoder_with_details", pred_ae)
    monkeypatch.setattr(pipeline, "analyze_behavior", regras)
    monkeypatch.setattr(pipeline, "refine_heuristic_outputs_with_window_context", lambda registros, outputs: outputs)
    monkeypatch.setattr(pipeline, "resolve_ensemble_config", lambda **kw: sinais["ensemble_config"])
    def combinar(X, **kw):
        assert kw["config"] is sinais["ensemble_config"]
        return [_build_support_snapshot(if_output=saida_if, ae_output=saida_ae,
            config=kw["config"], ae_reference_threshold_raw=9.0)]
    monkeypatch.setattr(pipeline, "predict_ensemble_details", combinar)
    monkeypatch.setattr(pipeline, "audit_model_artifacts", lambda *_: {"warnings": []})
    return pipeline, raw, (pred_if, pred_ae, regras)


def test_pipeline_aditivo_sem_reinferencia_e_csv(pipeline_sintetico, tmp_path, monkeypatch):
    pipeline, raw, detectores = pipeline_sintetico
    with monkeypatch.context() as m:
        m.setattr(pipeline, "calcular_contribuicoes_seguras", lambda **kw: None)
        antes, _ = pipeline.run_inference_from_frame(raw_df=raw, load_models=False)
    for mock in detectores:
        mock.reset_mock()
    depois, relatorio = pipeline.run_inference_from_frame(raw_df=raw, load_models=False, output_csv=tmp_path / "saida.csv")
    pd.testing.assert_frame_equal(antes.drop(columns="component_contributions"), depois.drop(columns="component_contributions"))
    for mock in detectores:
        assert mock.call_count == 1
    bloco = depois.iloc[0]["component_contributions"]
    assert bloco is not None
    assert relatorio["rows"][0]["component_contributions"] == bloco
    recarregado = pd.read_csv(tmp_path / "saida.csv")
    from src.api.services import _build_results_payload
    assert _build_results_payload(recarregado)[0]["component_contributions"] == bloco


def test_falha_real_do_calculador_preserva_pipeline(pipeline_sintetico, monkeypatch, caplog):
    from src.models import component_contribution
    pipeline, raw, _ = pipeline_sintetico
    antes, _ = pipeline.run_inference_from_frame(raw_df=raw, load_models=False)
    monkeypatch.setattr(component_contribution, "calculate_component_contribution",
        Mock(side_effect=ValueError("ERRO_SENSIVEL_SINTETICO")))
    depois, _ = pipeline.run_inference_from_frame(raw_df=raw, load_models=False)
    pd.testing.assert_frame_equal(antes.drop(columns="component_contributions"), depois.drop(columns="component_contributions"))
    assert depois["component_contributions"].tolist() == [None]
    assert "falha de calculo" in caplog.text and "ERRO_SENSIVEL_SINTETICO" not in caplog.text


@pytest.mark.parametrize("backend", ["sqlite", "postgresql"])
def test_post_get_persistencia_live_e_legado(ambiente, pipeline_sintetico, monkeypatch, backend):
    import os
    from sqlalchemy import create_engine, select
    from sqlalchemy.orm import sessionmaker
    from sqlalchemy.pool import StaticPool
    from src.db import repository, models
    from src.services.pfsense_incremental_service import _compact_live_window
    from src.api.services import _build_results_payload, _compact_history_window

    url = os.environ.get("SINALYX_TEST_POSTGRES_URL")
    if backend == "postgresql" and not url:
        pytest.skip("PostgreSQL descartável opt-in não configurado")
    motor = create_engine(url) if backend == "postgresql" else create_engine(
        "sqlite://", connect_args={"check_same_thread": False}, poolclass=StaticPool)
    models.Base.metadata.create_all(motor)
    fabrica = sessionmaker(bind=motor)
    monkeypatch.setattr(repository, "SessionLocal", fabrica)
    monkeypatch.setattr(repository, "_require_database", lambda: None)
    main, services, _ = ambiente
    pipeline, raw, _ = pipeline_sintetico
    frame, _ = pipeline.run_inference_from_frame(raw_df=raw, load_models=False)
    preparar_fluxo(monkeypatch, services)
    monkeypatch.setattr(services, "run_inference", lambda **kw: (frame, {}))
    monkeypatch.setattr(services, "save_analysis_to_database", repository.save_analysis)
    monkeypatch.setattr(services, "is_database_available", lambda: True)
    try:
        corpo, headers = multipart(b"log sintetico")
        status, resposta, _ = asyncio.run(requisicao(main.app, corpo, headers=headers))
        assert status == 200 and resposta["persistence"]["database_saved"]
        item = resposta["results"][0]
        assert item["component_contributions"] is not None
        with fabrica() as sessao:
            salvo = sessao.execute(select(models.AnalysisResult).where(models.AnalysisResult.analysis_id == resposta["analysis_id"])).scalar_one()
            assert salvo.raw_json == item
        # GET deve apenas ler, mesmo que o calculador fique indisponível.
        monkeypatch.setattr(pipeline, "calcular_contribuicoes_seguras", Mock(side_effect=AssertionError("não recalcular")))
        status, historico, _ = asyncio.run(requisicao(main.app, b"", caminho=f'/analyses/{resposta["analysis_id"]}/results', metodo="GET"))
        assert status == 200
        for campo in ("component_contributions", "model_outputs", "ai_support", "ai_support_signals"):
            assert historico["results"][0][campo] == item[campo]
        repository.save_live_windows([dict(window_uid=resposta["analysis_id"], execution_id="qa-shapley",
            local_log_path="sintetico.log", raw=item, model_outputs=item["model_outputs"])])
        with fabrica() as sessao:
            janela = sessao.execute(select(models.LivePfSenseWindow).where(models.LivePfSenseWindow.window_uid == resposta["analysis_id"])).scalar_one()
            persistida = repository._live_window_to_dict(janela)
            assert _compact_live_window(persistida)["component_contributions"] == item["component_contributions"]
            assert _compact_history_window(persistida)["component_contributions"] == item["component_contributions"]
        legado = {k: v for k, v in item.items() if k != "component_contributions"}
        repository.save_analysis(resposta, [legado])
        status, antigo, _ = asyncio.run(requisicao(main.app, b"", caminho=f'/analyses/{resposta["analysis_id"]}/results', metodo="GET"))
        assert status == 200 and "component_contributions" not in antigo["results"][0]
    finally:
        motor.dispose()
