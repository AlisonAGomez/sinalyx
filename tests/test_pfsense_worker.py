"""Worker controlável sem rede pfSense; lock PostgreSQL testado em QA isolado."""

import asyncio
import json
import os
import signal
import threading
from contextlib import contextmanager
from dataclasses import replace
from types import SimpleNamespace

import pytest
from sqlalchemy import create_engine

from tests.support.api import requisicao


@pytest.fixture
def controle(tmp_path, monkeypatch):
    from src.services import pfsense_worker_service as servico
    from src.workers import pfsense_live_worker as worker
    from src.core.config import get_settings
    monkeypatch.setattr(servico, "WORKER_DIR", tmp_path)
    monkeypatch.setattr(servico, "get_settings", lambda: replace(get_settings(), pfsense_worker_autostart=False))
    monkeypatch.setattr(worker, "create_tables", lambda: None)
    return servico


def test_config_defaults_e_minimo(monkeypatch):
    from src.core.config import get_settings
    monkeypatch.delenv("SINALYX_PFSENSE_WORKER_INTERVAL_SECONDS", raising=False)
    monkeypatch.delenv("SINALYX_PFSENSE_WORKER_AUTOSTART", raising=False)
    try:
        get_settings.cache_clear()
        assert get_settings().pfsense_worker_interval_seconds == 5
        assert get_settings().pfsense_worker_autostart is False
        monkeypatch.setenv("SINALYX_PFSENSE_WORKER_INTERVAL_SECONDS", "0")
        get_settings.cache_clear()
        assert get_settings().pfsense_worker_interval_seconds == 1
    finally:
        get_settings.cache_clear()


@pytest.mark.parametrize("autostart", [False, True])
def test_boot_e_controle_persistido(controle, monkeypatch, autostart):
    configuracao = controle.get_settings()
    monkeypatch.setattr(controle, "get_settings", lambda: replace(configuracao, pfsense_worker_autostart=autostart))
    assert controle.iniciar_controle() == ("running" if autostart else "stopped")
    controle.alterar_controle("stopped")
    monkeypatch.setattr(controle, "get_settings", lambda: replace(configuracao, pfsense_worker_autostart=True))
    assert controle.iniciar_controle() == "stopped"


@pytest.mark.parametrize("rota", ["start", "stop", "status"])
@pytest.mark.parametrize("papel", [None, "user", "admin"])
def test_api_permissoes_e_controle(ambiente, controle, rota, papel):
    main, _, _ = ambiente
    main.app.dependency_overrides.clear()
    if papel:
        main.app.dependency_overrides[main.get_current_user] = lambda: {"id": 1, "role": papel}
    status, corpo, _ = asyncio.run(requisicao(main.app, b"", caminho=f"/live/pfsense/worker/{rota}", metodo="GET" if rota == "status" else "POST"))
    esperado = 401 if papel is None else 403 if papel == "user" and rota != "status" else 200
    assert status == esperado
    if esperado == 200 and rota != "status":
        assert controle.ler_controle() == ("running" if rota == "start" else "stopped")
        assert corpo["desired_state"] == controle.ler_controle()
        assert "lógico" in corpo["message"]
        dados = json.loads((controle.WORKER_DIR / "worker_control.json").read_text(encoding="utf-8"))
        assert set(dados) == {"desired_state", "updated_at", "updated_by"}
        assert not (controle.WORKER_DIR / "worker_status.json").exists()
    elif esperado != 200:
        assert not (controle.WORKER_DIR / "worker_control.json").exists()


def test_status_sanitizado_e_escrita_atomica(ambiente, controle, monkeypatch):
    main, _, _ = ambiente
    substituicoes = []
    original = os.replace
    def substituir(origem, destino):
        assert origem != str(destino)
        assert json.loads(open(origem, encoding="utf-8").read())
        substituicoes.append(destino.name)
        original(origem, destino)
    monkeypatch.setattr(controle.os, "replace", substituir)
    controle.alterar_controle("running")
    controle.salvar_status({"state": "error", "last_error": "SEGREDO host.interno 10.0.0.1", "generation_signature": "HASH", "token": "TOKEN", "last_execution_id": "SEGREDO", "updated_at": "SEGREDO"})
    assert substituicoes == ["worker_control.json", "worker_status.json"]
    assert not list(controle.WORKER_DIR.glob(".*.json.*"))
    status, corpo, _ = asyncio.run(requisicao(main.app, b"", caminho="/live/pfsense/worker/status", metodo="GET"))
    assert status == 200
    texto = json.dumps(corpo)
    for segredo in ("SEGREDO", "host.interno", "10.0.0.1", "HASH", "TOKEN", "generation_signature"):
        assert segredo not in texto
    assert corpo["last_error"] == controle.SAFE_ERROR


def test_boot_nao_sobrescreve_stop_concorrente(controle, monkeypatch):
    original = os.link
    def publicar(origem, destino):
        controle.alterar_controle("stopped")
        original(origem, destino)
    monkeypatch.setattr(controle.os, "link", publicar)
    assert controle.iniciar_controle() == "stopped"
    assert json.loads((controle.WORKER_DIR / "worker_control.json").read_text())["updated_by"] == "api"


def test_worker_parado_nao_processa(controle, monkeypatch):
    from src.workers import pfsense_live_worker as worker
    evento = threading.Event()
    monkeypatch.setattr(worker, "process_live_pfsense", lambda **kw: pytest.fail("não executar parado"))
    monkeypatch.setattr(worker, "aguardar", lambda *args: evento.set())
    worker.executar_worker(evento)
    assert controle.obter_status()["state"] == "shutting_down"
    assert controle.ler_controle() == "stopped"


def test_stop_antes_inicio_nao_registra_ciclo(controle, monkeypatch):
    from src.workers import pfsense_live_worker as worker
    controle.alterar_controle("running")
    evento = threading.Event()
    original = controle.ler_controle
    leituras = 0
    def ler():
        nonlocal leituras
        leituras += 1
        # Preparação inicial lê controle e salvar_status também; depois vem o loop.
        if leituras == 4:
            controle.alterar_controle("stopped")
        return original()
    monkeypatch.setattr(controle, "ler_controle", ler)
    monkeypatch.setattr(worker, "process_live_pfsense", lambda **kw: pytest.fail("stop antes do início"))
    monkeypatch.setattr(worker, "aguardar", lambda *args: evento.set())
    worker.executar_worker(evento)
    estado = controle.obter_status()
    assert estado["last_cycle_started_at"] is None
    assert estado["desired_state"] == "stopped"


def test_erro_lock_nao_inicia_pipeline(bloqueio, monkeypatch):
    from src.services import pfsense_incremental_service as live
    monkeypatch.setattr(bloqueio.database, "DATABASE_ENABLED", False)
    monkeypatch.setattr(live, "ensure_live_runtime_dirs", lambda: pytest.fail("não tocar runtime"))
    resultado = live.process_live_pfsense()
    assert resultado["status"] == "error"
    assert "PostgreSQL" in resultado["message"]


def test_worker_retry_backoff_sucesso_stop(controle, monkeypatch, caplog):
    from src.workers import pfsense_live_worker as worker
    controle.alterar_controle("running")
    evento = threading.Event()
    chamadas = []
    esperas = []
    estados = []
    original = controle.salvar_status
    monkeypatch.setattr(controle, "salvar_status", lambda dados: estados.append(original(dados)) or estados[-1])
    def ciclo(**kwargs):
        chamadas.append(kwargs)
        if len(chamadas) == 1:
            raise RuntimeError("SEGREDO 10.0.0.1 senha")
        if len(chamadas) == 2:
            return {"status": "error", "message": "TOKEN"}
        controle.alterar_controle("stopped")
        return {"status": "success"}
    def esperar(parada, segundos, desejado):
        esperas.append(segundos)
        if desejado == "stopped":
            parada.set()
    monkeypatch.setattr(worker, "process_live_pfsense", ciclo)
    monkeypatch.setattr(worker, "aguardar", esperar)
    monkeypatch.setattr(worker, "get_settings", lambda: SimpleNamespace(pfsense_worker_interval_seconds=5))
    worker.executar_worker(evento)
    assert chamadas == [dict(collect=True, persist=True, finite_file=False, window="5s")] * 3
    assert esperas[:3] == [10, 20, 5]
    assert any(e["consecutive_failures"] == 2 for e in estados)
    assert estados[-1]["consecutive_failures"] == 0
    assert "SEGREDO" not in caplog.text + json.dumps(estados)
    assert "TOKEN" not in caplog.text + json.dumps(estados)
    assert worker.intervalo_backoff(5, 1000) == 60


def test_worker_bootstrap_uma_vez_em_tres_ciclos(controle, monkeypatch):
    from src.workers import pfsense_live_worker as worker
    controle.alterar_controle("running")
    parada = threading.Event()
    bootstrap = []
    ciclos = []
    monkeypatch.setattr(worker, "create_tables", lambda: bootstrap.append("schema"))

    def processar(**kwargs):
        ciclos.append(kwargs)
        if len(ciclos) == 3:
            controle.alterar_controle("stopped")
        return {"status": "success"}

    monkeypatch.setattr(worker, "process_live_pfsense", processar)
    monkeypatch.setattr(worker, "aguardar", lambda *args: parada.set() if args[2] == "stopped" else None)
    worker.executar_worker(parada)
    assert bootstrap == ["schema"]
    assert len(ciclos) == 3


def test_worker_retry_bootstrap_falha_antes_do_pipeline(controle, monkeypatch):
    from src.workers import pfsense_live_worker as worker
    controle.alterar_controle("running")
    parada = threading.Event()
    tentativas = []
    ciclos = []
    esperas = []

    def bootstrap():
        tentativas.append(1)
        if len(tentativas) == 1:
            raise OSError("falha sintética de banco")

    def processar(**kwargs):
        ciclos.append(kwargs)
        controle.alterar_controle("stopped")
        return {"status": "success"}

    monkeypatch.setattr(worker, "create_tables", bootstrap)
    monkeypatch.setattr(worker, "process_live_pfsense", processar)
    monkeypatch.setattr(worker, "aguardar", lambda parada, segundos, desejado: esperas.append(segundos) or (parada.set() if desejado == "stopped" else None))
    worker.executar_worker(parada)
    assert len(tentativas) == 2
    assert len(ciclos) == 1
    assert esperas[0] == 10


@pytest.mark.parametrize("sinal", [signal.SIGTERM, signal.SIGINT])
def test_sinais_terminam_loop(controle, monkeypatch, sinal):
    from src.workers import pfsense_live_worker as worker
    evento = threading.Event()
    handlers = {}
    monkeypatch.setattr(worker.signal, "signal", lambda numero, handler: handlers.setdefault(numero, handler))
    worker.instalar_sinais(evento)
    monkeypatch.setattr(worker, "aguardar", lambda *args: handlers[sinal](sinal, None))
    worker.executar_worker(evento)
    assert evento.is_set()
    assert controle.obter_status()["state"] == "shutting_down"


def test_stop_interrompe_espera(controle):
    from src.workers import pfsense_live_worker as worker
    controle.alterar_controle("stopped")
    evento = SimpleNamespace(is_set=lambda: False, wait=lambda segundos: pytest.fail("stop deve interromper"))
    worker.aguardar(evento, 60, "running")


def test_worker_busy_nao_entra_no_pipeline(controle, bloqueio, monkeypatch):
    from src.workers import pfsense_live_worker as worker
    from src.services import pfsense_incremental_service as live
    controle.alterar_controle("running")
    @contextmanager
    def ocupado(): yield False
    monkeypatch.setattr(bloqueio, "live_execution_lock", ocupado)
    monkeypatch.setattr(live, "ensure_live_runtime_dirs", lambda: pytest.fail("pipeline ocupado"))
    evento = threading.Event()
    observados = []
    def aguardar(*args):
        observados.append(controle.obter_status())
        evento.set()
    monkeypatch.setattr(worker, "aguardar", aguardar)
    worker.executar_worker(evento)
    assert observados[0]["state"] == "busy"
    assert observados[0]["consecutive_failures"] == 0


def test_saida_bruta_nao_vaza(capsys, caplog):
    import logging
    import sys
    from src.workers.pfsense_live_worker import saida_pipeline_privada
    with pytest.raises(RuntimeError):
        with saida_pipeline_privada():
            print("SEGREDO")
            print("HOST_INTERNO", file=sys.stderr)
            logging.warning("TOKEN")
            raise RuntimeError("sintetica")
    captura = capsys.readouterr()
    assert not captura.out and not captura.err
    assert "TOKEN" not in caplog.text


def test_falha_replace_preserva_controle(controle, monkeypatch):
    controle.alterar_controle("stopped")
    def falhar(*args): raise OSError("sintetico")
    monkeypatch.setattr(controle.os, "replace", falhar)
    with pytest.raises(OSError): controle.alterar_controle("running")
    assert controle.ler_controle() == "stopped"
    assert not list(controle.WORKER_DIR.glob(".*.json.*"))


@pytest.fixture
def bloqueio():
    from src.services import live_execution_lock
    return live_execution_lock


@pytest.mark.parametrize("adquirido", [True, False])
def test_lock_mesma_conexao_finally(bloqueio, monkeypatch, adquirido):
    chamadas = []
    class Conexao:
        def execute(self, sql, parametros):
            chamadas.append(str(sql))
            assert parametros == {"key": bloqueio.LOCK_KEY}
            return SimpleNamespace(scalar=lambda: adquirido)
        def close(self): chamadas.append("close")
    monkeypatch.setattr(bloqueio.database, "DATABASE_ENABLED", True)
    monkeypatch.setattr(bloqueio.database, "engine", SimpleNamespace(connect=lambda: Conexao()))
    with pytest.raises(RuntimeError, match="sintetica"):
        with bloqueio.live_execution_lock() as resultado:
            assert resultado == adquirido
            raise RuntimeError("sintetica")
    assert chamadas[-1] == "close"
    assert sum("pg_advisory_unlock" in c for c in chamadas) == int(adquirido)


def test_busy_manual_e_nao_persistente(ambiente, bloqueio, monkeypatch):
    from src.services import pfsense_incremental_service as live
    main, _, _ = ambiente
    main.app.dependency_overrides[main.get_current_user] = lambda: {"id": 1, "role": "admin"}
    @contextmanager
    def ocupado(): yield False
    monkeypatch.setattr(bloqueio, "live_execution_lock", ocupado)
    monkeypatch.setattr(live, "ensure_live_runtime_dirs", lambda: pytest.fail("busy não toca pipeline"))
    status, corpo, _ = asyncio.run(requisicao(main.app, b"", caminho="/live/pfsense/run"))
    assert status == 200 and corpo["status"] == "busy"
    assert live.process_live_pfsense()["status"] == "busy"
    def proibido(): pytest.fail("replay não usa lock")
    monkeypatch.setattr(bloqueio, "live_execution_lock", proibido)
    class EntrouNoPipeline(Exception): pass
    def entrou(): raise EntrouNoPipeline()
    monkeypatch.setattr(live, "ensure_live_runtime_dirs", entrou)
    with pytest.raises(EntrouNoPipeline):
        live.process_live_pfsense(persist=False)
    @bloqueio.serialized_live_execution
    def replay(*, persist=True): return "executado"
    assert replay(persist=False) == "executado"


def test_unlock_com_falha_invalida_conexao(bloqueio, monkeypatch):
    chamadas = []
    class Conexao:
        def execute(self, sql, parametros):
            if "unlock" in str(sql): raise RuntimeError("sintetica")
            return SimpleNamespace(scalar=lambda: True)
        def invalidate(self): chamadas.append("invalidate")
        def close(self): chamadas.append("close")
    monkeypatch.setattr(bloqueio.database, "DATABASE_ENABLED", True)
    monkeypatch.setattr(bloqueio.database, "engine", SimpleNamespace(connect=lambda: Conexao()))
    with bloqueio.live_execution_lock() as adquirido:
        assert adquirido
    assert chamadas == ["invalidate", "close"]


def test_postgres_concorrencia_e_liberacao(bloqueio, monkeypatch):
    url = os.environ.get("SINALYX_TEST_POSTGRES_URL")
    if not url:
        pytest.skip("PostgreSQL descartável não configurado")
    motor = create_engine(url)
    monkeypatch.setattr(bloqueio.database, "engine", motor)
    monkeypatch.setattr(bloqueio.database, "DATABASE_ENABLED", True)
    dentro = threading.Event()
    liberar = threading.Event()
    chamadas = []
    @bloqueio.serialized_live_execution
    def ciclo(*, persist=True):
        chamadas.append(True)
        dentro.set()
        assert liberar.wait(10)
        raise RuntimeError("sintetica")
    def primeira():
        with pytest.raises(RuntimeError): ciclo()
    thread = threading.Thread(target=primeira)
    try:
        thread.start()
        assert dentro.wait(10)
        assert ciclo()["status"] == "busy"
        assert chamadas == [True]
        liberar.set()
        thread.join(10)
        assert not thread.is_alive()
        with bloqueio.live_execution_lock() as adquirido:
            assert adquirido
    finally:
        liberar.set()
        thread.join(10)
        motor.dispose()
