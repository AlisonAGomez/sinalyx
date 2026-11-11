"""Contrato offline, álgebra exata e integração com os combinadores reais."""

from copy import deepcopy
from itertools import permutations
from math import fsum
from unittest.mock import Mock

import pytest

from src.models import component_contribution as modulo
from src.models.decision_engine import decide_attack, resolve_config
from src.models.ensemble import EnsembleConfig, _build_support_snapshot, resolve_ensemble_config


def test_oito_determinismo_eficiencia_paridade_e_preservacao(entrada):
    original = deepcopy(entrada)
    resultado = modulo.calculate_component_contribution(**entrada)
    assert entrada == original
    assert resultado == modulo.calculate_component_contribution(**entrada)
    assert len(resultado["coalitions"]) == 8
    assert {frozenset(c["members"]) for c in resultado["coalitions"].values()} == {
        frozenset(c) for c in modulo.gerar_coalizoes()
    }
    assert abs(resultado["efficiency_residual"]) <= modulo.TOLERANCIA
    assert fsum(c["relative_share_percent"] for c in resultado["components"].values()) == pytest.approx(100)
    assert resultado["components"]["autoencoder"]["shapley_value"] > 0
    assert resultado["baseline_value"] == -1
    assert resultado["baseline_type"] == "zero_signal_reference"
    vazia = resultado["coalitions"]["empty"]["decision"]
    assert vazia["base_attack_support"] == 0
    assert vazia["base_negative_support"] == vazia["confidence"] == 1
    ensemble = _build_support_snapshot(if_output=entrada["if_output"], ae_output=entrada["ae_output"],
                                      config=entrada["ensemble_config"], ae_reference_threshold_raw=9.0)
    oficial = decide_attack(if_output=entrada["if_output"], ae_output=entrada["ae_output"],
                            heuristic_output=entrada["heuristic_output"], ensemble_output=ensemble,
                            features={}, runtime_profile="balanced")
    completa = resultado["coalitions"]["+".join(modulo.PARTICIPANTES)]
    assert max(modulo.verificar_paridade(completa["decision"], oficial).values()) == 0
    assert completa["ensemble"]["if_weight"] == ensemble["if_weight"]
    assert completa["ensemble"]["score"] == ensemble["score"]


def test_zeramento_sem_reinferencia_ou_treino(entrada, monkeypatch):
    from src.models import ensemble, autoencoder, isolation_forest

    proibida = Mock(side_effect=AssertionError("Inferência/treino/carregamento proibido"))
    for alvo, nomes in (
        (ensemble, ("predict_ensemble_details", "predict_with_details", "predict_autoencoder_with_details", "train_all", "load_all_models")),
        (autoencoder, ("train_autoencoder", "predict_autoencoder", "predict_autoencoder_with_details", "load_autoencoder")),
        (isolation_forest, ("train_model", "predict", "predict_with_details", "load_model")),
    ):
        for nome in nomes:
            monkeypatch.setattr(alvo, nome, proibida)
    combinar = Mock(wraps=modulo._build_support_snapshot)
    decidir = Mock(wraps=modulo.decide_attack)
    monkeypatch.setattr(modulo, "_build_support_snapshot", combinar)
    monkeypatch.setattr(modulo, "decide_attack", decidir)
    modulo.calculate_component_contribution(**entrada)
    assert combinar.call_count == decidir.call_count == 8
    zero = dict(pred=0, raw_score=0.0, normalized_score=0.0, confidence=0.0)
    for coalizao, chamada in zip(modulo.gerar_coalizoes(), decidir.call_args_list):
        args = chamada.kwargs
        for participante, campo in (("autoencoder", "ae_output"), ("isolation_forest", "if_output")):
            assert args[campo] == (entrada[campo] if participante in coalizao else zero)
        if "security_rules" not in coalizao:
            assert args["heuristic_output"] == dict(heuristic_detected_attack=False,
                heuristic_confidence=0.0, attack_type="normal", heuristic_reason="")
        assert args["config"] == entrada["decision_config"]
    proibida.assert_not_called()


def test_ground_truth_e_identificadores_nao_chegam_ao_motor(entrada, monkeypatch):
    base = modulo.calculate_component_contribution(**entrada)
    espiao = Mock(wraps=modulo.decide_attack)
    monkeypatch.setattr(modulo, "decide_attack", espiao)
    proibidos = dict(label="ataque", target=1, scenario="syn_flood", diagnostic_category="FN",
                     error_type="FN", filename="captura", src_ip="IP-SINTETICO", source_ip="IP-SINTETICO")
    for campo in ("features", "metadata", "if_output", "ae_output", "heuristic_output"):
        entrada[campo].update(proibidos)
    assert modulo.calculate_component_contribution(**entrada) == base
    for chamada in espiao.call_args_list:
        for campo in ("features", "metadata", "if_output", "ae_output", "heuristic_output"):
            assert not set(proibidos).intersection(chamada.kwargs[campo])


def test_shapley_oraculo_por_permutacoes_e_contribuicao_negativa():
    # Caso com interação entre componentes e um componente que reduz o resultado; comparação independente por ordem de inclusão.
    valores = {"empty": -0.4, "autoencoder": 0.3, "isolation_forest": -0.5,
               "security_rules": -0.4, "autoencoder+isolation_forest": 0.1,
               "autoencoder+security_rules": 0.7, "isolation_forest+security_rules": -0.5,
               "autoencoder+isolation_forest+security_rules": 0.4}
    resultado = modulo.atribuir_valores(valores)
    oraculo = {p: 0.0 for p in modulo.PARTICIPANTES}
    for ordem in permutations(modulo.PARTICIPANTES):
        presentes = set()
        anterior = valores["empty"]
        for p in ordem:
            presentes.add(p)
            atual = valores["+".join(x for x in modulo.PARTICIPANTES if x in presentes)]
            oraculo[p] += (atual - anterior) / 6
            anterior = atual
    for p, valor in oraculo.items():
        assert resultado["components"][p]["shapley_value"] == pytest.approx(valor)
    assert resultado["components"]["isolation_forest"]["direction"] == "toward_normal"
    assert resultado["components"]["autoencoder"]["direction"] == "toward_anomaly"


@pytest.mark.parametrize("delta", [0, 1e-14])
def test_shares_zero_sem_contribuicao_relevante(delta):
    valores = {"+".join(c) or "empty": -1 + delta * len(c) for c in modulo.gerar_coalizoes()}
    resultado = modulo.atribuir_valores(valores)
    assert not resultado["relevant_contribution"]
    assert all(c["relative_share_percent"] == 0 and c["direction"] == "neutral" for c in resultado["components"].values())


@pytest.mark.parametrize("campo", modulo.CAMPOS_DECISAO)
def test_paridade_falha_em_cada_campo(entrada, campo):
    resultado = modulo.calculate_component_contribution(**entrada)
    original = resultado["coalitions"]["+".join(modulo.PARTICIPANTES)]["decision"]
    alterado = dict(original)
    alterado[campo] = original[campo] + 0.001 if campo in modulo.CAMPOS_NUMERICOS else "divergente"
    with pytest.raises(ValueError, match="Paridade divergente"):
        modulo.verificar_paridade(alterado, original)


@pytest.mark.parametrize("campo", ["raw_score", "normalized_score", "confidence"])
def test_rejeita_sinais_nao_finitos(entrada, campo):
    entrada["ae_output"][campo] = float("nan")
    with pytest.raises(ValueError, match="não finito"):
        modulo.calculate_component_contribution(**entrada)


def test_politica_operacional_fixa_nao_e_participante(entrada, monkeypatch):
    entrada["features"] = dict(protocol="icmpv6", action="block", connections=2, packets=2,
                               passed_count=0, destination_port_count=0)
    espiao = Mock(wraps=modulo.decide_attack)
    monkeypatch.setattr(modulo, "decide_attack", espiao)
    resultado = modulo.calculate_component_contribution(**entrada)
    assert all(c.kwargs["features"] == entrada["features"] for c in espiao.call_args_list)
    sem_regras = resultado["coalitions"]["autoencoder+isolation_forest"]["decision"]
    assert sem_regras["is_anomaly"] is False
    assert resultado["coalitions"]["+".join(modulo.PARTICIPANTES)]["decision"]["is_anomaly"] is True


def test_configuracao_current_usa_arquivo_persistido_e_resolvedores(tmp_path, monkeypatch):
    import json
    from types import SimpleNamespace
    from scripts import evaluate_component_contribution_tcc as avaliador

    arquivo = tmp_path / "ensemble.json"
    arquivo.write_text(json.dumps(dict(if_weight=0.2, ae_weight=0.97, ae_reference_threshold_raw=7.5)))
    monkeypatch.setattr(avaliador, "resolve_model_profile", lambda **kw: SimpleNamespace(
        profile_name="current", profile_path=tmp_path, source="requested"))
    ensemble, decisao, evidencia = avaliador.resolver_current("conservative")
    assert ensemble.ae_weight == 0.97 and ensemble.ae_reference_threshold_raw == 7.5
    assert ensemble.profile_name == decisao.profile_name == "conservative"
    assert evidencia["ensemble_config_persisted"]["if_weight"] == 0.2
    linha = dict(pred_if=0, score_if=0, score_if_normalized=0, if_confidence=0,
                 pred_ae=0, score_ae=0, score_ae_normalized=0, ae_confidence=0,
                 ae_threshold_raw=999, pred_heuristic=0, heuristic_confidence=0,
                 heuristic_attack_type="normal", heuristic_reason="")
    assert avaliador.preparar_entrada(linha, ensemble, decisao)["ae_reference_threshold"] == 7.5


def test_falha_de_paridade_impede_agregacao_e_exportacao(tmp_path, monkeypatch):
    import json
    import pandas as pd
    from scripts import evaluate_component_contribution_tcc as avaliador

    # Mesmo adaptador e cálculo reais, com origem sintética cuja confiança foi adulterada.
    ensemble = resolve_ensemble_config(EnsembleConfig(), runtime_profile="balanced")
    decisao = resolve_config(profile="balanced")
    linha = dict(pred_if=0, score_if=0, score_if_normalized=0, if_confidence=0,
                 pred_ae=0, score_ae=0, score_ae_normalized=0, ae_confidence=0,
                 ae_threshold_raw=1, pred_heuristic=0, heuristic_confidence=0,
                 heuristic_attack_type="normal", heuristic_reason="",
                 runtime_profile="balanced", decision_runtime_profile="balanced",
                 ensemble_score=0, pred_ensemble=0, ensemble_threshold=0.32,
                 ensemble_if_weight=0.18, ensemble_ae_weight=0.88,
                 is_anomaly=False, final_label="normal", attack_type="normal",
                 decision_source="safe_negative", base_attack_support=0,
                 base_negative_support=1, confidence=0.3, agreement_level="full_agreement_negative")
    monkeypatch.setattr(avaliador.pd, "read_csv", lambda *a, **kw: pd.DataFrame([linha]))
    monkeypatch.setattr(avaliador, "resolver_current", lambda perfil: (ensemble, decisao, {}))
    agregar = Mock(side_effect=AssertionError("Agregação proibida após divergência"))
    monkeypatch.setattr(avaliador, "resumir", agregar)
    saida = tmp_path / "evidencia"
    with pytest.raises(ValueError, match="confidence"):
        avaliador.executar(tmp_path, saida)
    agregar.assert_not_called()
    assert [p.name for p in saida.iterdir()] == ["falha_validacao.json"]
    assert json.loads((saida / "falha_validacao.json").read_text())["aggregated"] is False
    with pytest.raises(FileExistsError):
        avaliador.executar(tmp_path, saida)


def test_evidencia_historica_sem_identificadores_e_paridade():
    import json
    from pathlib import Path

    pasta = Path(__file__).resolve().parents[1] / "data/processed/pfsense/component_contribution_v1"
    if not pasta.exists():
        pytest.skip("Evidência offline ainda não gerada neste checkout.")
    resumo = json.loads((pasta / "resumo.json").read_text(encoding="utf-8"))
    assert resumo["parity_windows"] == 355 and resumo["parity_passed"]
    assert max(resumo["maximum_parity_errors"].values()) <= modulo.TOLERANCIA
    resultados = json.loads((pasta / "resultados_detalhados.json").read_text(encoding="utf-8"))
    assert len(resultados) == 355
    assert all(len(r["coalitions"]) == 8 for r in resultados)
    texto = json.dumps(resultados)
    for proibido in ('"src_ip"', '"source_ip"', '"features"', '"metadata"', '"heuristic_reason"', '"label"', '"target"'):
        assert proibido not in texto
    assert any(r["components"]["isolation_forest"]["direction"] == "toward_normal" for r in resultados)
