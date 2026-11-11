"""Worker sequencial: uma chamada do fluxo de processamento existente por ciclo."""

import logging
import os
import signal
import threading
import time
from contextlib import contextmanager, redirect_stdout, redirect_stderr

from src.core.config import get_settings
from src.db.init_db import create_tables
from src.services import pfsense_worker_service as controle
from src.services.pfsense_incremental_service import process_live_pfsense


logger = logging.getLogger("sinalyx.worker")


@contextmanager
def saida_pipeline_privada():
    """O processo dedicado publica só diagnósticos operacionais sanitizados."""
    nivel_anterior = logging.root.manager.disable
    try:
        logging.disable(logging.CRITICAL)
        with open(os.devnull, "w") as destino, redirect_stdout(destino), redirect_stderr(destino):
            yield
    finally:
        logging.disable(nivel_anterior)


def intervalo_backoff(intervalo, falhas):
    """Aumenta a espera após falhas consecutivas, respeitando o limite de sessenta segundos."""
    return intervalo if not falhas else min(60, intervalo * 2 ** min(falhas, 6))


def instalar_sinais(parada):
    """Registra os pedidos de encerramento e guarda os tratamentos anteriores."""
    anteriores = {}
    def encerrar(signum, frame):
        """Sinaliza a parada para que o ciclo atual termine de forma controlada."""
        parada.set()
    for sinal in (signal.SIGTERM, signal.SIGINT):
        anteriores[sinal] = signal.signal(sinal, encerrar)
    return anteriores


def aguardar(parada, segundos, desejado):
    """Espera entre ciclos, interrompendo a espera quando houver pedido de parada ou mudança de controle."""
    limite = time.monotonic() + segundos
    while not parada.is_set():
        if controle.ler_controle() != desejado:
            return
        restante = limite - time.monotonic()
        if restante <= 0:
            return
        parada.wait(min(0.5, restante))


def executar_worker(parada=None):
    """Repete as rodadas autorizadas, prepara o banco e aplica espera progressiva após falhas."""
    parada = parada if parada is not None else threading.Event()
    intervalo = get_settings().pfsense_worker_interval_seconds
    estado = {"state": "starting", "interval_seconds": intervalo, "consecutive_failures": 0}
    inicializado = False
    schema_ready = False
    try:
        while not parada.is_set():
            try:
                if not inicializado:
                    controle.iniciar_controle()
                    controle.salvar_status(estado)
                    inicializado = True
                desejado = controle.ler_controle()
                if desejado != "running":
                    estado["state"] = "stopped"
                    controle.salvar_status(estado)
                    aguardar(parada, intervalo, "stopped")
                    continue
                # Reler antes de iniciar; stop durante a rodada vale para a próxima.
                if parada.is_set() or controle.ler_controle() != "running":
                    continue
                estado.update(state="running", last_cycle_started_at=controle.agora())
                controle.salvar_status(estado)
                try:
                    with saida_pipeline_privada():
                        if not schema_ready:
                            create_tables()
                            schema_ready = True
                        resultado = process_live_pfsense(collect=True, persist=True, finite_file=False, window="5s")
                    situacao = resultado.get("status")
                    if situacao not in {"success", "busy"}:
                        situacao = "error"
                    estado["last_execution_id"] = resultado.get("execution_id")
                except Exception:
                    situacao = "error"
                    estado["last_execution_id"] = None
                estado.update(last_cycle_status=situacao, last_cycle_finished_at=controle.agora())
                if situacao == "error":
                    estado["consecutive_failures"] += 1
                    estado.update(state="error", last_error=controle.SAFE_ERROR)
                    logger.warning(controle.SAFE_ERROR)
                else:
                    if situacao == "success":
                        estado["consecutive_failures"] = 0
                    estado.update(state="busy" if situacao == "busy" else "waiting", last_error=None)
                controle.salvar_status(estado)
                aguardar(parada, intervalo_backoff(intervalo, estado["consecutive_failures"]), "running")
            except Exception:
                # Inclui falha transitória de I/O do controle/status, sem traceback.
                logger.warning(controle.SAFE_ERROR)
                estado["consecutive_failures"] += 1
                aguardar(parada, intervalo_backoff(intervalo, estado["consecutive_failures"]), controle.ler_controle())
    finally:
        try:
            controle.salvar_status({**estado, "state": "shutting_down"})
        except Exception:
            logger.warning(controle.SAFE_ERROR)


def main():
    """Prepara os avisos e sinais de parada antes de iniciar os ciclos do processo."""
    logging.basicConfig(level=logging.INFO, format="%(levelname)s %(name)s %(message)s")
    parada = threading.Event()
    anteriores = instalar_sinais(parada)
    try:
        executar_worker(parada)
    finally:
        for sinal, anterior in anteriores.items():
            signal.signal(sinal, anterior)


if __name__ == "__main__":
    main()
