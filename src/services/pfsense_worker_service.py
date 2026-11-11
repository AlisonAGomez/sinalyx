"""Controle lógico compartilhado; API escreve controle, worker escreve status."""

import json
import os
import tempfile
from datetime import datetime, timezone
from uuid import UUID

from src.core.config import get_settings
from src.core.paths import DATA_DIR


WORKER_DIR = DATA_DIR / "runtime" / "pfsense" / "live"
STATES = {"starting", "running", "stopped", "waiting", "busy", "error", "shutting_down"}
SAFE_ERROR = "Falha operacional no worker; verifique a configuração e a disponibilidade dos serviços."


def agora():
    """Retorna a data e hora atual em UTC no formato ISO."""
    return datetime.now(timezone.utc).isoformat()


def escrever_atomico(nome, dados, *, somente_criar=False):
    """Grava o estado em arquivo vizinho temporário antes de substituir o arquivo anterior."""
    WORKER_DIR.mkdir(parents=True, exist_ok=True)
    destino = WORKER_DIR / nome
    descritor, temporario = tempfile.mkstemp(prefix=f".{nome}.", dir=WORKER_DIR)
    try:
        with os.fdopen(descritor, "w", encoding="utf-8") as arquivo:
            json.dump(dados, arquivo, ensure_ascii=False)
            arquivo.flush()
            os.fsync(arquivo.fileno())
        if somente_criar:
            try:
                # Publicação exclusiva impede preparação inicial de sobrescrever um stop da API.
                os.link(temporario, destino)
            except FileExistsError:
                pass
        else:
            os.replace(temporario, destino)
    finally:
        if os.path.exists(temporario):
            os.unlink(temporario)


def _ler(nome):
    """Lê o estado JSON do processo e retorna objeto vazio se o arquivo não puder ser usado."""
    try:
        with (WORKER_DIR / nome).open(encoding="utf-8") as arquivo:
            dados = json.load(arquivo)
        return dados if isinstance(dados, dict) else {}
    except (OSError, ValueError):
        return {}


def iniciar_controle():
    """Cria o controle inicial se necessário, respeitando a opção de início automático."""
    desejado = "running" if get_settings().pfsense_worker_autostart else "stopped"
    escrever_atomico("worker_control.json", {"desired_state": desejado,
                      "updated_at": agora(), "updated_by": "bootstrap"}, somente_criar=True)
    return ler_controle()


def ler_controle():
    """Autoriza execução apenas quando o controle contém explicitamente o estado running."""
    dados = _ler("worker_control.json")
    # Controle inválido ou ausente impede o início de novas rodadas.
    return "running" if dados.get("desired_state") == "running" else "stopped"


def alterar_controle(desejado):
    """Grava o pedido de iniciar ou parar e devolve o estado público do processo."""
    if desejado not in {"running", "stopped"}:
        raise ValueError("Estado de controle inválido.")
    escrever_atomico("worker_control.json", {"desired_state": desejado,
                      "updated_at": agora(), "updated_by": "api"})
    return {"status": "success", "desired_state": desejado,
            "message": ("Processamento lógico solicitado. O worker aplicará o estado; o ciclo atual pode terminar. O container não é iniciado ou encerrado por este comando.")}


def _timestamp(valor):
    """Valida a data e hora do estado antes de incluí-la na resposta pública."""
    try:
        return datetime.fromisoformat(valor).isoformat()
    except (TypeError, ValueError):
        return None


def _numero(valor, minimo=0):
    """Converte um contador e garante que ele não fique abaixo do mínimo permitido."""
    try:
        return max(minimo, int(valor))
    except (ValueError, TypeError, OverflowError):
        return minimo


def status_seguro(dados):
    """Seleciona e valida os campos que podem ser apresentados sobre o processo."""
    try:
        execution_id = str(UUID(str(dados.get("last_execution_id"))))
    except ValueError:
        execution_id = None
    return {
        "state": dados.get("state") if dados.get("state") in STATES else "waiting",
        "desired_state": ler_controle(),
        "interval_seconds": _numero(dados.get("interval_seconds", get_settings().pfsense_worker_interval_seconds), 1),
        "last_cycle_started_at": _timestamp(dados.get("last_cycle_started_at")),
        "last_cycle_finished_at": _timestamp(dados.get("last_cycle_finished_at")),
        "last_cycle_status": dados.get("last_cycle_status") if dados.get("last_cycle_status") in {"success", "error", "busy"} else None,
        "last_execution_id": execution_id,
        "consecutive_failures": _numero(dados.get("consecutive_failures")),
        "last_error": SAFE_ERROR if dados.get("last_error") else None,
        "updated_at": _timestamp(dados.get("updated_at")),
    }


def salvar_status(dados):
    """Atualiza o horário do estado, filtra seus campos e grava o resultado."""
    seguro = status_seguro({**dados, "updated_at": agora()})
    escrever_atomico("worker_status.json", seguro)
    return seguro


def obter_status():
    """Lê o último estado salvo e devolve somente os campos públicos permitidos."""
    return status_seguro(_ler("worker_status.json"))
