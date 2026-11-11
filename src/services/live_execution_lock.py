"""Exclusão mútua entre worker, CLI e API usando uma sessão PostgreSQL."""

import hashlib
from contextlib import contextmanager
from functools import wraps
from uuid import uuid4

from sqlalchemy import text
from src.db import database


LOCK_KEY = int.from_bytes(hashlib.sha256(b"sinalyx:pfsense:live-execution").digest()[:8], "big", signed=True)


class LockUnavailable(RuntimeError):
    """Indica que não foi possível garantir uma única rodada persistente."""
    pass


@contextmanager
def live_execution_lock():
    """Reserva a execução no PostgreSQL para impedir duas rodadas persistentes simultâneas."""
    conexao = None
    adquirido = False
    try:
        try:
            if not database.DATABASE_ENABLED or database.engine is None:
                raise LockUnavailable()
            conexao = database.engine.connect()
            adquirido = bool(conexao.execute(text("SELECT pg_try_advisory_lock(:key)"), {"key": LOCK_KEY}).scalar())
        except Exception:
            if conexao is not None:
                conexao.invalidate()
            raise LockUnavailable("Bloqueio PostgreSQL indisponível.") from None
        yield adquirido
    finally:
        if conexao is not None:
            try:
                if adquirido:
                    try:
                        conexao.execute(text("SELECT pg_advisory_unlock(:key)"), {"key": LOCK_KEY})
                    except Exception:
                        # Não reutilizar uma conexão que possa continuar reservando a execução no banco.
                        conexao.invalidate()
            finally:
                conexao.close()


def serialized_live_execution(funcao):
    """Aplica a reserva de execução somente às rodadas que gravam resultados."""
    @wraps(funcao)
    def executar(*args, **kwargs):
        """Executa a rodada com a reserva necessária e trata indisponibilidade ou concorrência."""
        if not kwargs.get("persist", True):
            return funcao(*args, **kwargs)
        try:
            with live_execution_lock() as adquirido:
                if adquirido:
                    return funcao(*args, **kwargs)
                return {"status": "busy", "execution_id": str(uuid4()),
                        "message": "Fluxo live ocupado; nenhuma coleta ou leitura foi iniciada."}
        except LockUnavailable:
            return {"status": "error", "execution_id": str(uuid4()),
                    "message": "Bloqueio PostgreSQL indisponível; fluxo live não iniciado."}
    return executar
