"""
Inicializacao das tabelas do PostgreSQL da API.
"""

from __future__ import annotations

from src.db.database import Base, DATABASE_INIT_ERROR, SessionLocal, engine


def create_tables() -> None:
    """Preparação inicial compatível: cria somente tabelas ausentes, sem evoluir estrutura dos dados.

    Alembic é a autoridade em bancos persistentes. Este preparação inicial permanece
    para compatibilidade com startup/seed, preparação inicial do worker/CLI e testes descartáveis;
    não substitui `alembic upgrade head` nem corrige colunas de tabelas existentes.
    """
    if Base is None or engine is None or SessionLocal is None:
        raise RuntimeError(
            DATABASE_INIT_ERROR
            or "A camada de banco nao esta pronta para criar as tabelas."
        )

    from src.db import models  # noqa: F401

    Base.metadata.create_all(bind=engine)
