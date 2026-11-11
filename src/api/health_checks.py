"""Sondas leves, sem análise, escrita no banco ou detalhes públicos internos."""

from functools import lru_cache

from sqlalchemy import create_engine, text
from sqlalchemy.pool import NullPool

from src.core.config import get_settings
from src.models.autoencoder import get_loaded_bundle as obter_autoencoder
from src.models.isolation_forest import get_loaded_bundle as obter_detector

runtime_preparado = False


@lru_cache(maxsize=1)
def _motor_sonda():
    # Pool separado: a sonda não aguarda vagas do pool de requisições da API.
    """Cria uma conexão curta para verificar o banco, sem manter conexões abertas."""
    return create_engine(
        get_settings().database_url, poolclass=NullPool,
        connect_args={"connect_timeout": 2, "options": "-c statement_timeout=2000"},
    )


def banco_pronto() -> bool:
    """Confere conexão PostgreSQL e presença das quatro tabelas, sem ler dados."""
    try:
        if not get_settings().database_enabled:
            return False
        with _motor_sonda().connect() as conexao:
            conexao.execute(text(
                "SELECT users.id, analyses.id, analysis_results.id, live_pfsense_windows.id "
                "FROM users, analyses, analysis_results, live_pfsense_windows LIMIT 0"
            ))
        return True
    except Exception:
        return False


def runtime_pronto() -> bool:
    """Usa os arquivos de apoio já carregados do perfil ativo; nunca carrega ou infere."""
    try:
        if not runtime_preparado:
            return False
        obter_autoencoder()
        obter_detector()
        return True
    except Exception:
        return False


def esta_pronto() -> bool:
    """Exige banco disponível e modelos carregados para considerar a aplicação pronta."""
    return banco_pronto() and runtime_pronto()
