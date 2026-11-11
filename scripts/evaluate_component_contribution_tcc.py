"""Avaliação offline das 355 janelas; nunca carrega modelos ou acessa dotenv."""

from __future__ import annotations

import argparse
import hashlib
import json
import os
import sys
from dataclasses import asdict
from pathlib import Path
from statistics import mean, median

# Precisa preceder os imports do projeto, que carregam src.core.config.
os.environ["PYTHON_DOTENV_DISABLED"] = "1"

RAIZ = Path(__file__).resolve().parents[1]
if str(RAIZ) not in sys.path:
    sys.path.insert(0, str(RAIZ))

import pandas as pd

from src.core.model_registry import profile_runtime_artifacts, resolve_model_profile
from src.models.component_contribution import (
    CAMPOS_CONTEXTO, CAMPOS_DECISAO, PARTICIPANTES, TOLERANCIA,
    calculate_component_contribution, verificar_paridade,
)
from src.models.decision_engine import resolve_config
from src.models.ensemble import (
    EnsembleConfig, _resolve_ae_reference_threshold, resolve_ensemble_config,
)

CENARIOS = {"normal_firewall": "normal", "port_scan": "port_scan",
            "syn_flood": "syn_flood", "brute_force": "brute_force"}
COLUNAS_SINAIS = {
    "pred_if", "score_if", "score_if_normalized", "if_confidence",
    "pred_ae", "score_ae", "score_ae_normalized", "ae_confidence", "ae_threshold_raw",
    "pred_heuristic", "heuristic_confidence", "heuristic_attack_type", "heuristic_reason",
    "runtime_profile", "decision_runtime_profile", "ensemble_score", "pred_ensemble",
    "ensemble_threshold", "ensemble_if_weight", "ensemble_ae_weight",
}
COLUNAS = COLUNAS_SINAIS | set(CAMPOS_DECISAO) | CAMPOS_CONTEXTO


def resolver_current(perfil_operacional: str):
    """Mesmo cadastro de perfis e resolvedores do fluxo de processamento, sem carregar bundles/pickles."""
    if perfil_operacional not in {"balanced", "conservative"}:
        raise ValueError("Perfil operacional histórico desconhecido.")
    resolucao = resolve_model_profile(requested_profile="current", fallback_profile="current")
    if resolucao.profile_name != "current" or resolucao.source != "requested":
        raise ValueError("Artefatos current não resolvidos; fallback não permitido.")
    arquivo = profile_runtime_artifacts(resolucao.profile_path)["ensemble"]
    conteudo = arquivo.read_bytes()
    base = EnsembleConfig(**json.loads(conteudo))
    ensemble = resolve_ensemble_config(base, runtime_profile=perfil_operacional)
    # infer_pfsense_batch chama decide_attack_batch sem config customizada.
    decisao = resolve_config(profile=perfil_operacional)
    evidencia = {
        "model_profile": "current", "resolution_source": resolucao.source,
        "ensemble_config_sha256": hashlib.sha256(conteudo).hexdigest(),
        "ensemble_config_persisted": asdict(base),
        "ensemble_config_resolved": asdict(ensemble),
        "decision_config_resolved": asdict(decisao),
        "runtime_profile": perfil_operacional,
    }
    return ensemble, decisao, evidencia


def preparar_entrada(linha, ensemble, decisao):
    def detector(sufixo):
        return dict(pred=int(linha[f"pred_{sufixo}"]), raw_score=float(linha[f"score_{sufixo}"]),
                    normalized_score=float(linha[f"score_{sufixo}_normalized"]),
                    confidence=float(linha[f"{sufixo}_confidence"]))

    # O resolvedor oficial prioriza o limite de classificação salvo no Ensemble;
    # se ausente, usa o limite de classificação do bundle já registrado pela análise AE.
    referencia = _resolve_ae_reference_threshold(
        ensemble, autoencoder_bundle={"threshold": float(linha["ae_threshold_raw"])},
    )
    return dict(
        if_output=detector("if"), ae_output=detector("ae"),
        heuristic_output=dict(
            heuristic_detected_attack=bool(int(linha["pred_heuristic"])),
            heuristic_confidence=float(linha["heuristic_confidence"]),
            attack_type=str(linha["heuristic_attack_type"]),
            heuristic_reason=str(linha["heuristic_reason"] or ""),
        ),
        features={k: linha[k] for k in CAMPOS_CONTEXTO if k in linha}, metadata={},
        runtime_profile=ensemble.profile_name, ensemble_config=ensemble,
        decision_config=decisao, ae_reference_threshold=referencia,
    )


def resumir(resultados):
    total = sum(r["components"][p]["absolute_contribution"] for r in resultados for p in PARTICIPANTES)
    componentes = {}
    for p in PARTICIPANTES:
        valores = [r["components"][p]["shapley_value"] for r in resultados]
        absolutos = [abs(v) for v in valores]
        soma = sum(absolutos)
        componentes[p] = {
            "sum_absolute_shapley": soma,
            "relative_share_percent": 100 * soma / total if total > TOLERANCIA else 0.0,
            "mean_shapley": mean(valores), "mean_absolute_shapley": mean(absolutos),
            "median_shapley": median(valores),
            **{d: sum(r["components"][p]["direction"] == d for r in resultados)
               for d in ("toward_anomaly", "toward_normal", "neutral")},
        }
    return {"windows": len(resultados), "components": componentes}


def avaliar(entrada: Path):
    resultados, fontes, configuracoes = [], {}, {}
    max_paridade = {k: 0.0 for k in ("base_attack_support", "base_negative_support", "confidence", "ensemble_score")}
    for pasta, cenario in CENARIOS.items():
        # Projeção explícita: não materializa IPs, nomes de janela ou referência de avaliação.
        frame = pd.read_csv(entrada / pasta / "inference_results.csv", usecols=lambda c: c in COLUNAS,
                            float_precision="round_trip")
        faltantes = (COLUNAS_SINAIS | set(CAMPOS_DECISAO)) - set(frame.columns)
        if faltantes:
            raise ValueError(f"Colunas obrigatórias ausentes: {sorted(faltantes)}")
        projecao = frame.to_json(orient="split", double_precision=15)
        fontes[cenario] = {"windows": len(frame), "selected_columns_sha256": hashlib.sha256(projecao.encode()).hexdigest()}
        frame = frame.astype(object).where(pd.notna(frame), None)
        for posicao, linha in enumerate(frame.to_dict(orient="records"), 1):
            perfil = linha["runtime_profile"]
            if perfil != linha["decision_runtime_profile"]:
                raise ValueError("Perfis de Ensemble e Decision Engine divergentes na origem.")
            if perfil not in configuracoes:
                configuracoes[perfil] = resolver_current(perfil)
            ensemble, decisao, _ = configuracoes[perfil]
            resultado = calculate_component_contribution(**preparar_entrada(linha, ensemble, decisao))
            completa = resultado["coalitions"]["+".join(PARTICIPANTES)]
            try:
                erros = verificar_paridade(completa["decision"], linha)
                for campo, coluna in (("score", "ensemble_score"), ("pred", "pred_ensemble"),
                                      ("threshold", "ensemble_threshold"), ("if_weight", "ensemble_if_weight"),
                                      ("ae_weight", "ensemble_ae_weight")):
                    erro = abs(float(completa["ensemble"][campo]) - float(linha[coluna]))
                    if not erro <= TOLERANCIA:
                        raise ValueError(f"Paridade divergente: {coluna}")
                    if campo == "score":
                        erros["ensemble_score"] = erro
            except ValueError as erro:
                raise ValueError(f"Avaliação interrompida na linha sequencial {len(resultados) + 1}: {erro}") from erro
            for campo, erro in erros.items():
                max_paridade[campo] = max(max_paridade[campo], erro)
            # Agrupamento e referência só são anexados APÓS Shapley e paridade.
            resultados.append({"window_ref": f"{cenario}-{posicao:04d}", "scenario": cenario, **resultado})
    if len(resultados) != 355:
        raise ValueError(f"Esperadas 355 janelas; encontradas {len(resultados)}. Agregação interrompida.")
    resumo = {
        "methodology": "exact_shapley_v1", "baseline_type": "zero_signal_reference",
        "tolerance": TOLERANCIA, "parity_passed": True, "parity_windows": len(resultados),
        "maximum_parity_errors": max_paridade,
        "maximum_absolute_efficiency_residual": max(abs(r["efficiency_residual"]) for r in resultados),
        "baseline_values": sorted(set(r["baseline_value"] for r in resultados)),
        "configurations": {k: v[2] for k, v in configuracoes.items()}, "sources": fontes,
        "global": resumir(resultados),
        "by_scenario": {c: resumir([r for r in resultados if r["scenario"] == c]) for c in CENARIOS.values()},
        "implementation_sha256": {p: hashlib.sha256((RAIZ / p).read_bytes()).hexdigest() for p in (
            "src/models/component_contribution.py", "src/models/ensemble.py", "src/models/decision_engine.py",
            "src/pipelines/infer_pfsense_batch.py", "scripts/evaluate_component_contribution_tcc.py",
        )},
    }
    return resultados, resumo


def gerar_relatorio(resumo):
    texto = ["# Avaliação offline de contribuição marginal", "",
             f"Paridade: {resumo['parity_windows']}/355 janelas. Tolerância absoluta: {TOLERANCIA}.",
             f"Maior residual absoluto de eficiência: {resumo['maximum_absolute_efficiency_residual']:.17g}.", "",
             "Baseline: estado de referência sem evidência de ataque. Confidence é força relativa da decisão, não probabilidade.", "",
             "| Recorte | N | Componente | Soma absoluta | Participação % | Média assinada | Média absoluta | Mediana assinada | Anomalia / normal / neutra |",
             "|---|---:|---|---:|---:|---:|---:|---:|---|" ]
    for nome, recorte in {"global": resumo["global"], **resumo["by_scenario"]}.items():
        for p, c in recorte["components"].items():
            texto.append(f"| {nome} | {recorte['windows']} | {p} | {c['sum_absolute_shapley']:.9f} | {c['relative_share_percent']:.6f} | {c['mean_shapley']:.9f} | {c['mean_absolute_shapley']:.9f} | {c['median_shapley']:.9f} | {c['toward_anomaly']} / {c['toward_normal']} / {c['neutral']} |")
    texto += ["", "Brute force: limitação de observabilidade do pfSense. Não comprova observação de tentativas de senha ou de autenticação.",
              "", "Maior participação mede influência interna, não qualidade isolada. A análise histórica por remoção usa confiança 1 para detectores removidos e não é diretamente equivalente."]
    return "\n".join(texto) + "\n"


def executar(entrada: Path, saida: Path):
    # Nunca sobrescreve evidências, mesmo de uma execução anterior deste script.
    saida.mkdir(parents=True, exist_ok=False)
    try:
        resultados, resumo = avaliar(entrada)
    except (ValueError, FileNotFoundError) as erro:
        (saida / "falha_validacao.json").write_text(json.dumps(
            {"status": "interrupted", "aggregated": False, "reason": str(erro)},
            ensure_ascii=False, indent=2), encoding="utf-8")
        raise
    for nome, conteudo in (("resultados_detalhados.json", resultados), ("resumo.json", resumo)):
        (saida / nome).write_text(json.dumps(conteudo, ensure_ascii=False, indent=2, allow_nan=False), encoding="utf-8")
    linhas = []
    for r in resultados:
        linha = {k: r[k] for k in ("window_ref", "scenario", "baseline_value", "full_value", "decision_span", "efficiency_residual")}
        for p, contribuicao in r["components"].items():
            linha.update({f"{p}_{k}": v for k, v in contribuicao.items()})
        linhas.append(linha)
    pd.DataFrame(linhas).to_csv(saida / "contribuicoes_por_janela.csv", index=False)
    (saida / "relatorio.md").write_text(gerar_relatorio(resumo), encoding="utf-8")
    return resumo


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--input-root", type=Path, default=RAIZ / "data/processed/pfsense/validation_runs/20260911_current_tcc")
    parser.add_argument("--output-root", type=Path, default=RAIZ / "data/processed/pfsense/component_contribution_v1")
    args = parser.parse_args()
    resumo = executar(args.input_root, args.output_root)
    print(json.dumps({k: resumo[k] for k in ("parity_windows", "maximum_parity_errors", "maximum_absolute_efficiency_residual", "global", "by_scenario")}, indent=2))
