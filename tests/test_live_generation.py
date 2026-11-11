"""Leitura incremental, geração de arquivo e retry com logs sintéticos."""

import inspect
import json
import os
from types import SimpleNamespace
from uuid import uuid4

import pandas as pd
import pytest
from sqlalchemy import create_engine, select, func
from sqlalchemy.orm import sessionmaker



def estado_lido(caminho):
    from src.services.pfsense_incremental_service import _read_new_lines
    _, leitura = _read_new_lines(caminho, {})
    return {"offset": leitura["offset_after"], "file_size": leitura["file_size_after"],
            "total_lines_processed": leitura["total_lines_after"],
            "generation_signature": leitura["generation_signature"]}


def test_defaults_5s(monkeypatch):
    from src.services import pfsense_incremental_service as live
    from src.pipelines import process_pfsense_incremental as cli
    from src.api.main import live_pfsense_run_endpoint
    assert live.DEFAULT_LIVE_WINDOW == cli.DEFAULT_LIVE_WINDOW == "5s"
    assert inspect.signature(live.process_live_pfsense).parameters["window"].default == "5s"
    assert inspect.signature(live_pfsense_run_endpoint).parameters["window"].default == "5s"
    monkeypatch.setattr("sys.argv", ["live"])
    assert cli.parse_args().window == "5s"


def test_identidade_logica_independe_offsets(tmp_path):
    from src.services.pfsense_incremental_service import _window_uid
    janela = {"window_id": "janela", "window_start": "2026-01-01T00:00:00", "window_end": "2026-01-01T00:00:05"}
    def uid(inicio, fim, caminho=tmp_path / "filter.log"):
        return _window_uid(local_log_path=caminho, parser_read={"offset_before": inicio, "offset_after": fim}, record=janela)
    assert uid(0, 50) == uid(0, 50) == uid(500, 550)
    assert len(uid(0, 50)) == 64
    assert uid(0, 50) != uid(0, 50, tmp_path / "outra.log")
    anterior = uid(0, 50)
    janela["window_end"] = "2026-01-01T00:00:10"
    assert uid(0, 50) != anterior


@pytest.mark.parametrize("inicial", [b"", b"a", b"antigo\n", b"a" * 5000 + b"\n"])
def test_crescimento_nao_rotaciona(tmp_path, inicial):
    from src.services.pfsense_incremental_service import _read_new_lines
    from src.collectors.file_generation import tamanho_assinatura
    caminho = tmp_path / "filter.log"
    caminho.write_bytes(inicial)
    estado = estado_lido(caminho)
    caminho.write_bytes(inicial + b"novo\n")
    linhas, leitura = _read_new_lines(caminho, estado)
    assert not leitura["rotation_detected"]
    assert leitura["offset_before"] == len(inicial)
    assert linhas == ["novo"]
    assert tamanho_assinatura(leitura["generation_signature"]) == min(len(inicial) + 5, 4096)


@pytest.mark.parametrize("novo", [b"", b"ant", b"x\n", b"novo12\n", b"novo maior\ninicio preservado\n"])
def test_rotacao_rele_inicio(tmp_path, novo):
    from src.services.pfsense_incremental_service import _read_new_lines
    caminho = tmp_path / "filter.log"
    caminho.write_bytes(b"antigo\n")
    estado = estado_lido(caminho)
    caminho.write_bytes(novo)
    linhas, leitura = _read_new_lines(caminho, estado)
    assert leitura["rotation_detected"]
    assert leitura["offset_before"] == leitura["total_lines_before"] == 0
    assert linhas == novo.decode().splitlines()
    # Estado ainda não confirmado: retry lê novamente desde zero.
    assert _read_new_lines(caminho, estado) == (linhas, leitura)


def test_estado_legado_rele_conservadoramente(tmp_path):
    from src.services.pfsense_incremental_service import _read_new_lines
    caminho = tmp_path / "filter.log"
    caminho.write_bytes(b"novo maior\n")
    linhas, leitura = _read_new_lines(caminho, {"offset": 5, "file_size": 5})
    assert leitura["rotation_detected"] and leitura["offset_before"] == 0
    assert linhas == ["novo maior"]


def test_coletor_assina_tmp_sem_conteudo_no_estado(coletor, monkeypatch):
    import paramiko
    from src.collectors.file_generation import identificar_geracao
    modulo, config = coletor
    monkeypatch.setattr(type(config), "missing_settings", lambda self: [])
    conteudo = [b"cabecalho sintetico\n"]
    class Cliente:
        def load_host_keys(self, *args): pass
        def get_host_keys(self): return {"host": True}
        def set_missing_host_key_policy(self, *args): pass
        def connect(self, **kwargs): pass
        def open_sftp(self): return self
        def stat(self, *args): return SimpleNamespace(st_size=len(conteudo[0]))
        def get(self, remoto, local):
            from pathlib import Path
            Path(local).write_bytes(conteudo[0])
        def close(self): pass
    monkeypatch.setattr(paramiko, "SSHClient", Cliente)
    primeiro = modulo.collect_filter_log(config)
    assinatura = primeiro["generation_signature"]
    assert assinatura == identificar_geracao(config.local_path)
    conteudo[0] += b"cresceu\n"
    fortalecida = modulo.collect_filter_log(config)["generation_signature"]
    assert fortalecida != assinatura
    assert fortalecida == identificar_geracao(config.local_path)
    conteudo[0] = b"substituido completamente\n"
    assert modulo.collect_filter_log(config)["generation_signature"] != assinatura
    estado = config.state_path.read_text(encoding="utf-8")
    assert "substituido completamente" not in estado
    assert config.password not in estado


@pytest.mark.parametrize("falha", ["inferencia", "persistencia", "persistencia_sem_erros"])
@pytest.mark.parametrize("crescimento", [False, True])
def test_falha_e_retry_preservam_geracao_e_offset(tmp_path, monkeypatch, falha, crescimento):
    from contextlib import contextmanager
    from src.services import live_execution_lock as bloqueio
    @contextmanager
    def lock_sintetico():
        yield True
    monkeypatch.setattr(bloqueio, "live_execution_lock", lock_sintetico)
    from src.services import pfsense_incremental_service as live
    from src.pipelines import infer_pfsense_batch as inferencia
    from src.db import init_db
    # O caminho padrão continua sendo o ambiente real, mesmo quando o log de teste é temporário.
    monkeypatch.setattr(live, "_parser_state_path", lambda local_log_path=None: tmp_path / "parser_state.json")
    caminho = tmp_path / "filter.log"
    caminho.write_bytes(b"n" if crescimento else b"antigo\n")
    anterior = estado_lido(caminho)
    live._save_parser_state(caminho, dict(anterior))
    caminho.write_bytes(b"novo maior\n")
    config = SimpleNamespace(local_path=caminho, remote_path="sintetico")
    monkeypatch.setattr(live.PfSenseCollectorConfig, "from_env", lambda: config)
    monkeypatch.setattr(live, "LIVE_RUNTIME_DIR", tmp_path)
    monkeypatch.setattr(live, "LIVE_RUNS_DIR", tmp_path / "runs")
    leituras = []
    frame = pd.DataFrame([{"window_id": "janela", "window_start": "2026-01-01T00:00:00", "window_end": "2026-01-01T00:00:05", "final_label": "normal"}])
    def parse(linhas, **kwargs):
        leituras.append(linhas)
        return frame.copy(), {}
    monkeypatch.setattr(live, "_parse_new_lines", parse)
    monkeypatch.setattr(live, "prepare_events_dataframe", lambda df: df)
    monkeypatch.setattr(live, "_split_closed_and_pending_events", lambda df, **kw: (df, []))
    monkeypatch.setattr(live, "build_windowed_feature_frame", lambda df, **kw: frame.copy())
    monkeypatch.setattr(live, "is_database_available", lambda: True)
    monkeypatch.setattr(init_db, "create_tables", lambda: None)
    def falhar(**kwargs): raise RuntimeError("falha sintetica")
    monkeypatch.setattr(inferencia, "run_inference_from_frame", falhar if falha == "inferencia" else lambda **kw: (frame.copy(), {}))
    registros = []
    def persistir(itens):
        registros.extend(itens)
        return {"database_saved": False, "errors": [] if falha == "persistencia_sem_erros" else ["falha sintetica"]}
    monkeypatch.setattr(live, "save_live_windows_to_database", persistir)
    resposta = live.process_live_pfsense(collect=False)
    assert resposta["status"] == "error"
    estado = live._load_parser_state(caminho)
    assert all(estado[k] == v for k, v in anterior.items())
    monkeypatch.setattr(inferencia, "run_inference_from_frame", lambda **kw: (frame.copy(), {}))
    monkeypatch.setattr(live, "save_live_windows_to_database", lambda itens: registros.extend(itens) or {"database_saved": True, "errors": []})
    resposta = live.process_live_pfsense(collect=False)
    assert resposta["status"] == "success"
    assert leituras == ([["ovo maior"], ["ovo maior"]] if crescimento else [["novo maior"], ["novo maior"]])
    estado = live._load_parser_state(caminho)
    assert estado["offset"] == caminho.stat().st_size
    assert estado["generation_signature"] != anterior["generation_signature"]
    from src.collectors.file_generation import tamanho_assinatura
    assert tamanho_assinatura(estado["generation_signature"]) == caminho.stat().st_size
    assert len({r["window_uid"] for r in registros}) == 1
    assert "generation_signature" not in json.dumps(resposta)
    assert "generation_signature" not in json.dumps(registros)
    assert "generation_signature" not in live.get_parser_status()
    assert estado["generation_signature"] not in json.dumps(resposta)
    assert estado["generation_signature"].split(":")[-1] not in json.dumps(registros)


@pytest.mark.parametrize("tamanho", [10, 4096, 6000])
def test_fortalecimento_detecta_substituicao_com_mesmo_primeiro_byte(tmp_path, tamanho):
    from src.services.pfsense_incremental_service import _read_new_lines
    from src.collectors.file_generation import tamanho_assinatura, corresponde_assinatura
    caminho = tmp_path / "filter.log"
    caminho.write_bytes(b"a")
    anterior = estado_lido(caminho)
    caminho.write_bytes(b"a" * tamanho)
    assert corresponde_assinatura(caminho, anterior["generation_signature"])
    _, leitura = _read_new_lines(caminho, anterior)
    assert not leitura["rotation_detected"]
    assert leitura["offset_before"] == 1
    assert tamanho_assinatura(leitura["generation_signature"]) == min(tamanho, 4096)
    fortalecido = {"offset": tamanho, "file_size": tamanho,
                   "generation_signature": leitura["generation_signature"]}
    caminho.write_bytes(b"a" + b"b" * (tamanho - 1))
    linhas, leitura = _read_new_lines(caminho, fortalecido)
    assert leitura["rotation_detected"] and leitura["offset_before"] == 0
    assert linhas == ["a" + "b" * (tamanho - 1)]


def test_assinatura_coletada_primeira_leitura_e_status(tmp_path, monkeypatch):
    from src.services import pfsense_incremental_service as live
    from src.collectors.file_generation import identificar_geracao
    caminho = tmp_path / "filter.log"
    caminho.write_bytes(b"primeira\n")
    assinatura = identificar_geracao(caminho)
    linhas, leitura = live._read_new_lines(caminho, {}, assinatura)
    assert linhas == ["primeira"] and not leitura["rotation_detected"]
    assert leitura["generation_signature"] == assinatura
    monkeypatch.setattr(live.PfSenseCollectorConfig, "from_env", lambda: object())
    monkeypatch.setattr(live, "read_collector_state", lambda config: {"generation_signature": assinatura, "last_fetch_status": "success"})
    assert live.get_collector_status() == {"last_fetch_status": "success"}


def test_postgresql_idempotencia_offsets(tmp_path, monkeypatch):
    from src.db import models, repository
    from src.services.pfsense_incremental_service import _window_uid
    url = os.environ.get("SINALYX_TEST_POSTGRES_URL")
    if not url:
        pytest.skip("Definir PostgreSQL descartável em SINALYX_TEST_POSTGRES_URL")
    motor = create_engine(url)
    models.Base.metadata.create_all(motor)
    fabrica = sessionmaker(bind=motor)
    monkeypatch.setattr(repository, "SessionLocal", fabrica)
    monkeypatch.setattr(repository, "_require_database", lambda: None)
    janela = {"window_id": str(uuid4()), "window_start": "2026-01-01T00:00:00", "window_end": "2026-01-01T00:00:05"}
    try:
        for indice, offset in enumerate([0, 100]):
            uid = _window_uid(local_log_path=tmp_path / "filter.log", parser_read={"offset_before": offset, "offset_after": offset + 100}, record=janela)
            resultado = repository.save_live_windows([{"window_uid": uid, "parser_start_offset": offset}])
            assert resultado["database_saved"]
            assert resultado["saved"] == (1 if indice == 0 else 0)
            assert resultado["skipped_duplicates"] == indice
        with fabrica() as sessao:
            assert sessao.scalar(select(func.count()).select_from(models.LivePfSenseWindow).where(models.LivePfSenseWindow.window_uid == uid)) == 1
    finally:
        motor.dispose()
