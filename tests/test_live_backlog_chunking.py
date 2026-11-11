"""Leitura limitada do backlog live sem alterar o reprocessamento finito."""

from contextlib import contextmanager
from types import SimpleNamespace

import pandas as pd
import pytest

from src.services import pfsense_incremental_service as live


def _estado_seguinte(leitura):
    return {
        "offset": leitura["offset_after"],
        "file_size": leitura["file_size_after"],
        "total_lines_processed": leitura["total_lines_after"],
        "generation_signature": leitura["generation_signature"],
    }


def test_arquivo_menor_que_limite_chega_ao_eof(tmp_path):
    caminho = tmp_path / "filter.log"
    caminho.write_bytes(b"uma\nduas\n")
    linhas, leitura = live._read_new_lines(caminho, {}, max_read_bytes=100)
    assert linhas == ["uma", "duas"]
    assert leitura["offset_after"] == leitura["file_size_after"] == 9
    assert leitura["bytes_read"] == 9
    assert leitura["remaining_bytes"] == 0
    assert not leitura["read_limited"]


def test_backlog_grande_consumido_em_multiplas_rodadas(tmp_path):
    caminho = tmp_path / "filter.log"
    originais = [f"linha-{indice:03d}" for indice in range(100)]
    caminho.write_bytes(("\n".join(originais) + "\n").encode())
    estado = {}
    reunidas = []
    for rodada in range(100):
        linhas, leitura = live._read_new_lines(caminho, estado, max_read_bytes=32)
        reunidas.extend(linhas)
        assert leitura["bytes_read"] == leitura["offset_after"] - leitura["offset_before"]
        assert leitura["remaining_bytes"] == caminho.stat().st_size - leitura["offset_after"]
        if rodada == 0:
            assert leitura["read_limited"]
            assert leitura["offset_after"] < leitura["file_size_after"]
            assert leitura["bytes_read"] <= 32 + len(originais[0]) + 1
        estado = _estado_seguinte(leitura)
        if not leitura["read_limited"]:
            break
    assert reunidas == originais
    assert estado["offset"] == caminho.stat().st_size


def test_limite_no_meio_da_linha_completa_somente_ela(tmp_path):
    caminho = tmp_path / "filter.log"
    caminho.write_bytes(b"linha1\nlinha2-muito-grande\nlinha3\n")
    primeiras, leitura = live._read_new_lines(caminho, {}, max_read_bytes=10)
    proximas, seguinte = live._read_new_lines(caminho, _estado_seguinte(leitura), max_read_bytes=10)
    assert primeiras == ["linha1", "linha2-muito-grande"]
    assert proximas == ["linha3"]
    assert leitura["offset_after"] == len(b"linha1\nlinha2-muito-grande\n")
    assert seguinte["offset_before"] == leitura["offset_after"]


def test_limite_exatamente_no_newline_nao_le_linha_extra(tmp_path):
    caminho = tmp_path / "filter.log"
    caminho.write_bytes(b"uma\nduas\n")
    linhas, leitura = live._read_new_lines(caminho, {}, max_read_bytes=4)
    assert linhas == ["uma"]
    assert leitura["offset_after"] == 4
    assert leitura["read_limited"]


def test_utf8_mantem_offset_em_bytes_e_texto_inteiro(tmp_path):
    caminho = tmp_path / "filter.log"
    caminho.write_bytes("ação\npróxima\n".encode("utf-8"))
    primeiras, leitura = live._read_new_lines(caminho, {}, max_read_bytes=2)
    proximas, seguinte = live._read_new_lines(caminho, _estado_seguinte(leitura), max_read_bytes=2)
    assert primeiras == ["ação"]
    assert proximas == ["próxima"]
    assert leitura["offset_after"] == len("ação\n".encode("utf-8"))
    assert seguinte["offset_after"] == caminho.stat().st_size


def test_eof_sem_newline_mantem_semantica_atual(tmp_path):
    caminho = tmp_path / "filter.log"
    caminho.write_bytes(b"ultima")
    linhas, leitura = live._read_new_lines(caminho, {}, max_read_bytes=10)
    assert linhas == ["ultima"]
    assert leitura["offset_after"] == 6


def test_rotacao_recomeca_do_byte_zero_com_limite(tmp_path):
    caminho = tmp_path / "filter.log"
    caminho.write_bytes(b"anterior\n")
    _, anterior = live._read_new_lines(caminho, {})
    caminho.write_bytes(b"nova-1\nnova-2\nnova-3\n")
    linhas, leitura = live._read_new_lines(caminho, _estado_seguinte(anterior), max_read_bytes=7)
    assert leitura["rotation_detected"]
    assert leitura["offset_before"] == 0
    assert linhas == ["nova-1"]
    assert leitura["offset_after"] == 7
    assert leitura["read_limited"]


@pytest.fixture
def fluxo_local(tmp_path, monkeypatch):
    from src.services import live_execution_lock

    @contextmanager
    def bloqueio():
        yield True

    monkeypatch.setattr(live_execution_lock, "live_execution_lock", bloqueio)
    caminho = tmp_path / "filter.log"
    monkeypatch.setattr(live, "_parser_state_path", lambda local_log_path=None: tmp_path / "parser_state.json")
    monkeypatch.setattr(live.PfSenseCollectorConfig, "from_env", lambda: SimpleNamespace(local_path=caminho, remote_path="sintetico"))
    monkeypatch.setattr(live, "LIVE_RUNTIME_DIR", tmp_path)
    monkeypatch.setattr(live, "LIVE_RUNS_DIR", tmp_path / "runs")
    monkeypatch.setattr(live, "DEFAULT_LIVE_MAX_READ_BYTES", 2)
    return caminho


def test_pending_events_sobrevive_a_divisao_do_backlog(fluxo_local, monkeypatch):
    caminho = fluxo_local
    caminho.write_bytes(b"a\nb\n")
    monkeypatch.setattr(live, "_now_iso", lambda: "2026-01-01T00:00:01")
    eventos_fechados = []
    timestamps = {"a": "2026-01-01T00:00:00", "b": "2026-01-01T00:00:05"}
    monkeypatch.setattr(live, "_parse_new_lines", lambda linhas, **kw: (
        pd.DataFrame([{"timestamp": timestamps[linha], "source_ip": linha} for linha in linhas]), {},
    ))
    monkeypatch.setattr(live, "prepare_events_dataframe", lambda df: df)

    def construir_features(df, **kw):
        eventos_fechados.extend(df["source_ip"].tolist())
        return pd.DataFrame()

    monkeypatch.setattr(live, "build_windowed_feature_frame", construir_features)
    primeira = live.process_live_pfsense(collect=False, persist=False)
    estado = live._load_parser_state(caminho)
    assert primeira["status"] == "success"
    assert primeira["parser"]["read_limited"]
    assert [evento["source_ip"] for evento in estado["pending_events"]] == ["a"]
    segunda = live.process_live_pfsense(collect=False, persist=False)
    estado = live._load_parser_state(caminho)
    assert segunda["status"] == "success"
    assert not segunda["parser"]["read_limited"]
    assert eventos_fechados == ["a"]
    assert [evento["source_ip"] for evento in estado["pending_events"]] == ["b"]
    assert estado["offset"] == caminho.stat().st_size


@pytest.mark.parametrize("etapa", ["inferencia", "persistencia", "schema", "banco_indisponivel"])
def test_retry_apos_falha_rele_mesmo_lote(fluxo_local, monkeypatch, etapa):
    from src.pipelines import infer_pfsense_batch as inferencia
    from src.db import init_db

    caminho = fluxo_local
    caminho.write_bytes(b"a\nb\n")
    leituras = []
    janela = pd.DataFrame([{
        "window_id": "janela", "window_start": "2026-01-01T00:00:00",
        "window_end": "2026-01-01T00:00:05", "final_label": "normal",
    }])

    def analisar(linhas, **kw):
        leituras.append(linhas)
        return janela.copy(), {}

    monkeypatch.setattr(live, "_parse_new_lines", analisar)
    monkeypatch.setattr(live, "prepare_events_dataframe", lambda df: df)
    monkeypatch.setattr(live, "_split_closed_and_pending_events", lambda df, **kw: (df, []))
    monkeypatch.setattr(live, "build_windowed_feature_frame", lambda df, **kw: janela.copy())
    persistir = etapa != "inferencia"
    if etapa == "inferencia":
        monkeypatch.setattr(inferencia, "run_inference_from_frame", lambda **kw: (_ for _ in ()).throw(RuntimeError("falha simulada")))
    else:
        monkeypatch.setattr(inferencia, "run_inference_from_frame", lambda **kw: (janela.copy(), {}))
        monkeypatch.setattr(live, "is_database_available", lambda: etapa != "banco_indisponivel")
        monkeypatch.setattr(init_db, "create_tables", lambda: pytest.fail("bootstrap não pertence à rodada live"))
        if etapa == "schema":
            monkeypatch.setattr(live, "save_live_windows_to_database", lambda itens: (_ for _ in ()).throw(RuntimeError("schema ausente")))
        else:
            monkeypatch.setattr(live, "save_live_windows_to_database", lambda itens: {"database_saved": False, "errors": ["falha simulada"]})
    falha = live.process_live_pfsense(collect=False, persist=persistir)
    assert falha["status"] == "error"
    assert live._load_parser_state(caminho)["offset"] == 0
    monkeypatch.setattr(inferencia, "run_inference_from_frame", lambda **kw: (janela.copy(), {}))
    monkeypatch.setattr(live, "is_database_available", lambda: True)
    monkeypatch.setattr(live, "save_live_windows_to_database", lambda itens: {"database_saved": True, "saved": 1, "errors": []})
    sucesso = live.process_live_pfsense(collect=False, persist=persistir)
    assert sucesso["status"] == "success"
    assert leituras == [["a"], ["a"]]
    assert live._load_parser_state(caminho)["offset"] == 2
    assert sucesso["parser"]["read_limited"]


def test_finite_file_consume_arquivo_maior_que_limite_padrao(fluxo_local, monkeypatch):
    caminho = fluxo_local
    monkeypatch.setattr(live, "DEFAULT_LIVE_MAX_READ_BYTES", 4 * 1024 * 1024)
    linha = b"x" * 1023 + b"\n"
    caminho.write_bytes(linha * 4097)
    observado = []
    monkeypatch.setattr(live, "_parse_new_lines", lambda linhas, **kw: (
        observado.append(len(linhas)) or pd.DataFrame(), {},
    ))
    monkeypatch.setattr(live, "prepare_events_dataframe", lambda df: df)
    resultado = live.process_live_pfsense(collect=False, persist=False, finite_file=True)
    assert resultado["status"] == "success"
    assert observado == [4097]
    assert resultado["parser"]["offset_after"] == caminho.stat().st_size
    assert not resultado["parser"]["read_limited"]
