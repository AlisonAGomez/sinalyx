"""Fechamento causal de janelas pendentes no fluxo live."""

from contextlib import contextmanager
from types import SimpleNamespace

import pandas as pd
import pytest

from src.services import pfsense_incremental_service as live


def _separar(horarios, referencia, *, flush_pending=False):
    eventos = pd.DataFrame({"timestamp": horarios, "source_ip": [f"evento-{i}" for i in range(len(horarios))]})
    fechados, pendentes = live._split_closed_and_pending_events(
        eventos, window="5s", flush_pending=flush_pending, reference_time=referencia,
    )
    return fechados["source_ip"].tolist(), [evento["source_ip"] for evento in pendentes]


def test_bucket_posterior_fecha_anterior_sem_esperar_grace():
    fechados, pendentes = _separar(
        ["2026-01-01T10:00:01", "2026-01-01T10:00:06"],
        "2026-01-01T10:00:07",
    )
    assert fechados == ["evento-0"]
    assert pendentes == ["evento-1"]


@pytest.mark.parametrize("referencia, fechado", [
    ("2026-01-01T10:00:09.999999", False),
    ("2026-01-01T10:00:10", True),
    ("2026-01-01T10:00:11", True),
])
def test_grace_antes_no_cutoff_e_depois(referencia, fechado):
    fechados, pendentes = _separar(["2026-01-01T10:00:01"], referencia)
    assert fechados == (["evento-0"] if fechado else [])
    assert pendentes == ([] if fechado else ["evento-0"])


def test_flush_fecha_tudo_imediatamente():
    fechados, pendentes = _separar(
        ["2026-01-01T10:00:01", "2026-01-01T10:00:06"],
        "2026-01-01T09:00:00", flush_pending=True,
    )
    assert fechados == ["evento-0", "evento-1"]
    assert pendentes == []


@pytest.mark.parametrize("modo", ["finite_file", "flush_pending"])
def test_modos_de_replay_fecham_ultima_janela_sem_esperar_relogio(tmp_path, monkeypatch, modo):
    from src.services import live_execution_lock

    @contextmanager
    def bloqueio():
        yield True

    monkeypatch.setattr(live_execution_lock, "live_execution_lock", bloqueio)
    caminho = tmp_path / "filter.log"
    caminho.write_bytes(b"a\n")
    monkeypatch.setattr(live, "_parser_state_path", lambda local_log_path=None: tmp_path / "parser_state.json")
    monkeypatch.setattr(live.PfSenseCollectorConfig, "from_env", lambda: SimpleNamespace(local_path=caminho, remote_path="sintetico"))
    monkeypatch.setattr(live, "LIVE_RUNTIME_DIR", tmp_path)
    monkeypatch.setattr(live, "LIVE_RUNS_DIR", tmp_path / "runs")
    monkeypatch.setattr(live, "_now_iso", lambda: "2026-01-01T09:00:00")
    monkeypatch.setattr(live, "_parse_new_lines", lambda linhas, **kw: (
        pd.DataFrame([{"timestamp": "2026-01-01T10:00:01", "source_ip": linha} for linha in linhas]), {},
    ))
    monkeypatch.setattr(live, "prepare_events_dataframe", lambda df: df)
    fechados = []

    def construir_features(df, **kw):
        fechados.extend(df["source_ip"].tolist())
        return pd.DataFrame()

    monkeypatch.setattr(live, "build_windowed_feature_frame", construir_features)
    resultado = live.process_live_pfsense(collect=False, persist=False, **{modo: True})
    assert resultado["status"] == "success"
    assert fechados == ["a"]
    assert live._load_parser_state(caminho)["pending_events"] == []


def test_eventos_naive_aceitam_referencia_aware_sem_type_error():
    assert _separar(
        ["2026-01-01T10:00:01"], pd.Timestamp("2026-01-01T10:00:10+00:00"),
    ) == (["evento-0"], [])


def test_eventos_aware_alinham_referencia_ao_fuso_dos_eventos():
    assert _separar(
        [pd.Timestamp("2026-01-01T10:00:01-03:00")],
        pd.Timestamp("2026-01-01T13:00:10+00:00"),
    ) == (["evento-0"], [])
    assert _separar(
        [pd.Timestamp("2026-01-01T10:00:01-03:00")],
        pd.Timestamp("2026-01-01T10:00:08"),
    ) == ([], ["evento-0"])


def test_evento_futuro_nao_fecha_pelo_relogio():
    assert _separar(["2026-01-01T10:00:11"], "2026-01-01T10:00:10") == (
        [], ["evento-0"],
    )


def test_backlog_limitado_nao_fecha_bucket_antes_de_ler_todos_os_eventos(tmp_path, monkeypatch):
    from src.services import live_execution_lock

    @contextmanager
    def bloqueio():
        yield True

    monkeypatch.setattr(live_execution_lock, "live_execution_lock", bloqueio)
    caminho = tmp_path / "filter.log"
    caminho.write_bytes(b"a\nb\n")
    monkeypatch.setattr(live, "_parser_state_path", lambda local_log_path=None: tmp_path / "parser_state.json")
    monkeypatch.setattr(live.PfSenseCollectorConfig, "from_env", lambda: SimpleNamespace(local_path=caminho, remote_path="sintetico"))
    monkeypatch.setattr(live, "LIVE_RUNTIME_DIR", tmp_path)
    monkeypatch.setattr(live, "LIVE_RUNS_DIR", tmp_path / "runs")
    monkeypatch.setattr(live, "DEFAULT_LIVE_MAX_READ_BYTES", 2)
    monkeypatch.setattr(live, "_now_iso", lambda: "2026-01-01T10:00:10")
    monkeypatch.setattr(live, "_parse_new_lines", lambda linhas, **kw: (
        pd.DataFrame([{"timestamp": "2026-01-01T10:00:01", "source_ip": linha} for linha in linhas]), {},
    ))
    monkeypatch.setattr(live, "prepare_events_dataframe", lambda df: df)
    fechados = []

    def construir_features(df, **kw):
        fechados.append(df["source_ip"].tolist())
        return pd.DataFrame()

    monkeypatch.setattr(live, "build_windowed_feature_frame", construir_features)
    primeira = live.process_live_pfsense(collect=False, persist=False)
    estado = live._load_parser_state(caminho)
    assert primeira["parser"]["read_limited"]
    assert fechados == [[]]
    assert [evento["source_ip"] for evento in estado["pending_events"]] == ["a"]

    segunda = live.process_live_pfsense(collect=False, persist=False)
    estado = live._load_parser_state(caminho)
    assert not segunda["parser"]["read_limited"]
    assert fechados == [[], ["a", "b"]]
    assert estado["pending_events"] == []


@pytest.mark.parametrize("falha", [None, "inferencia", "persistencia"])
def test_rodada_sem_linhas_fecha_pending_e_retry_preserva_evento(tmp_path, monkeypatch, falha):
    from src.db import init_db
    from src.pipelines import infer_pfsense_batch as inferencia
    from src.services import live_execution_lock

    @contextmanager
    def bloqueio():
        yield True

    monkeypatch.setattr(live_execution_lock, "live_execution_lock", bloqueio)
    caminho = tmp_path / "filter.log"
    caminho.write_bytes(b"a\n")
    monkeypatch.setattr(live, "_parser_state_path", lambda local_log_path=None: tmp_path / "parser_state.json")
    monkeypatch.setattr(live.PfSenseCollectorConfig, "from_env", lambda: SimpleNamespace(local_path=caminho, remote_path="sintetico"))
    monkeypatch.setattr(live, "LIVE_RUNTIME_DIR", tmp_path)
    monkeypatch.setattr(live, "LIVE_RUNS_DIR", tmp_path / "runs")
    monkeypatch.setattr(live, "DEFAULT_LIVE_MAX_READ_BYTES", 2)
    horario = ["2026-01-01T10:00:08"]
    monkeypatch.setattr(live, "_now_iso", lambda: horario[0])
    monkeypatch.setattr(live, "_parse_new_lines", lambda linhas, **kw: (
        pd.DataFrame([{"timestamp": "2026-01-01T10:00:01", "source_ip": linha} for linha in linhas]), {},
    ))
    monkeypatch.setattr(live, "prepare_events_dataframe", lambda df: df)
    janela = pd.DataFrame([{
        "window_id": "janela", "window_start": "2026-01-01T10:00:00",
        "window_end": "2026-01-01T10:00:05", "final_label": "normal",
    }])
    vistos = []

    def construir_features(df, **kw):
        if df.empty:
            return pd.DataFrame()
        vistos.extend(df["source_ip"].tolist())
        return janela.copy()

    monkeypatch.setattr(live, "build_windowed_feature_frame", construir_features)
    monkeypatch.setattr(live, "is_database_available", lambda: True)
    monkeypatch.setattr(init_db, "create_tables", lambda: pytest.fail("bootstrap não pertence à rodada live"))
    salvos = []
    monkeypatch.setattr(live, "save_live_windows_to_database", lambda itens: (
        salvos.extend(itens) or {"database_saved": True, "saved": len(itens), "errors": []}
    ))
    monkeypatch.setattr(inferencia, "run_inference_from_frame", lambda **kw: (janela.copy(), {}))

    primeira = live.process_live_pfsense(collect=False, persist=True)
    estado_antes = live._load_parser_state(caminho)
    assert primeira["status"] == "success"
    assert estado_antes["offset"] == 2
    assert [evento["source_ip"] for evento in estado_antes["pending_events"]] == ["a"]
    assert not salvos

    horario[0] = "2026-01-01T10:00:10"
    if falha == "inferencia":
        monkeypatch.setattr(inferencia, "run_inference_from_frame", lambda **kw: (_ for _ in ()).throw(RuntimeError("falha simulada")))
    elif falha == "persistencia":
        monkeypatch.setattr(live, "save_live_windows_to_database", lambda itens: {"database_saved": False, "errors": ["falha simulada"]})
    if falha:
        tentativa = live.process_live_pfsense(collect=False, persist=True)
        estado_falha = live._load_parser_state(caminho)
        assert tentativa["status"] == "error"
        assert estado_falha["offset"] == estado_antes["offset"]
        assert estado_falha["pending_events"] == estado_antes["pending_events"]
        monkeypatch.setattr(inferencia, "run_inference_from_frame", lambda **kw: (janela.copy(), {}))
        monkeypatch.setattr(live, "save_live_windows_to_database", lambda itens: (
            salvos.extend(itens) or {"database_saved": True, "saved": len(itens), "errors": []}
        ))

    segunda = live.process_live_pfsense(collect=False, persist=True)
    estado_depois = live._load_parser_state(caminho)
    assert segunda["status"] == "success"
    assert segunda["parser"]["lines_new"] == 0
    assert estado_depois["pending_events"] == []
    assert len(salvos) == 1
    assert vistos == (["a", "a"] if falha else ["a"])
    terceira = live.process_live_pfsense(collect=False, persist=True)
    assert terceira["status"] == "success"
    assert len(salvos) == 1
