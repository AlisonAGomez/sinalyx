"""Contratos operacionais com SQLite descartável e dependências simuladas."""

import asyncio
from datetime import datetime
from types import SimpleNamespace

import pytest
from sqlalchemy import create_engine, select
from sqlalchemy.orm import sessionmaker

from tests.support.api import requisicao


@pytest.mark.parametrize("papel,ativo", [("admin", True), ("user", True), ("admin", False), ("user", False)])
@pytest.mark.parametrize("senha_presente", [True, False])
def test_seed_nao_promove_reativa_ou_troca_senha(banco, papel, ativo, senha_presente):
    repo, models, fabrica, config = banco
    if not senha_presente:
        config.admin_password = ""
    with fabrica.begin() as sessao:
        sessao.add(models.User(name="Existente", email=config.admin_email, password_hash="hash-sintetico",
                               role=papel, is_active=ativo, created_at=datetime(2026, 1, 1), updated_at=datetime(2026, 1, 1)))
    assert repo.seed_initial_admin()["created"] is False
    with fabrica() as sessao:
        usuario = sessao.execute(select(models.User)).scalar_one()
        assert (usuario.role, usuario.is_active, usuario.password_hash) == (papel, ativo, "hash-sintetico")


def test_seed_cria_admin_e_e_idempotente(banco):
    repo, _, _, _ = banco
    resultado = repo.seed_initial_admin()
    assert resultado["created"] and resultado["user"]["role"] == "admin"
    assert "password_hash" not in resultado["user"]
    assert repo.seed_initial_admin()["created"] is False


def test_seed_sem_senha_nao_cria(banco):
    repo, models, fabrica, config = banco
    config.admin_password = ""
    assert repo.seed_initial_admin()["created"] is False
    with fabrica() as sessao:
        assert sessao.execute(select(models.User)).scalars().all() == []


@pytest.mark.parametrize("email", ["", "invalido", "a b@example.test"])
def test_seed_configuracao_invalida(banco, email):
    repo, _, _, config = banco
    config.admin_email = email
    with pytest.raises(ValueError, match="configuracao"):
        repo.seed_initial_admin()


@pytest.mark.parametrize("acao", ["desativar", "rebaixar", "excluir"])
def test_nao_remove_ultimo_admin_ativo(banco, acao):
    repo, _, _, _ = banco
    usuario = repo.seed_initial_admin()["user"]
    with pytest.raises(ValueError):
        if acao == "desativar":
            repo.update_user_status(usuario["id"], False)
        elif acao == "rebaixar":
            repo.update_user(usuario["id"], role="user")
        else:
            repo.delete_user(usuario["id"])


@pytest.mark.parametrize("banco_ok,runtime_ok", [(True, True), (False, True), (True, False), (False, False)])
def test_readiness_http_sem_detalhes(monkeypatch, banco_ok, runtime_ok):
    from src.api import main, health_checks
    monkeypatch.setattr(health_checks, "banco_pronto", lambda: banco_ok)
    monkeypatch.setattr(health_checks, "runtime_pronto", lambda: runtime_ok)
    status, corpo, _ = asyncio.run(requisicao(main.app, b"", caminho="/ready", metodo="GET"))
    assert status == (200 if banco_ok and runtime_ok else 503)
    assert corpo == {"status": "ready" if status == 200 else "not_ready"}


def test_liveness_independe_de_banco_e_runtime(monkeypatch):
    from src.api import main
    monkeypatch.setattr(main, "is_database_available", lambda: (_ for _ in ()).throw(AssertionError("nao consultar")))
    status, corpo, _ = asyncio.run(requisicao(main.app, b"", caminho="/live", metodo="GET"))
    assert (status, corpo) == (200, {"status": "ok"})


def test_health_preserva_contrato_anterior(monkeypatch):
    from src.api import main
    monkeypatch.setattr(main, "DATABASE_ENABLED", True)
    monkeypatch.setattr(main, "is_database_available", lambda: False)
    status, corpo, _ = asyncio.run(requisicao(main.app, b"", caminho="/health", metodo="GET"))
    assert status == 200
    assert corpo == {"status": "ok", "database": {"enabled": True, "available": False}}


@pytest.mark.parametrize("falha", [True, False])
def test_preload_define_prontidao_sem_inferencia(monkeypatch, falha):
    from src.api import main, health_checks
    monkeypatch.setattr(health_checks, "runtime_preparado", True)
    monkeypatch.setattr(main, "get_auth_secret", lambda: "sintetico")
    monkeypatch.setattr(main, "ensure_api_runtime_dirs", lambda: None)
    monkeypatch.setattr(main, "create_tables", lambda: None)
    monkeypatch.setattr(main, "seed_initial_admin", lambda: {})

    def carregar():
        if falha:
            raise RuntimeError("FALHA_SINTETICA_DE_PRELOAD")

    monkeypatch.setattr(main, "load_all_models", carregar)
    main.startup()
    assert health_checks.runtime_preparado is (not falha)


def test_create_all_preserva_tabelas_existentes(banco, monkeypatch):
    from src.db import init_db
    repo, models, fabrica, _ = banco
    repo.seed_initial_admin()
    monkeypatch.setattr(init_db, "engine", fabrica.kw["bind"])
    monkeypatch.setattr(init_db, "SessionLocal", fabrica)
    init_db.create_tables()
    init_db.create_tables()
    with fabrica() as sessao:
        assert len(sessao.execute(select(models.User)).scalars().all()) == 1


def test_create_all_sem_engine_falha(monkeypatch):
    from src.db import init_db
    monkeypatch.setattr(init_db, "engine", None)
    with pytest.raises(RuntimeError):
        init_db.create_tables()


def test_create_all_nao_migra_tabela_existente(monkeypatch):
    from sqlalchemy import inspect, text
    from src.db import init_db
    motor = create_engine("sqlite://")
    try:
        with motor.begin() as conexao:
            conexao.execute(text("CREATE TABLE users (id INTEGER PRIMARY KEY)"))
        monkeypatch.setattr(init_db, "engine", motor)
        monkeypatch.setattr(init_db, "SessionLocal", sessionmaker(bind=motor))
        init_db.create_tables()
        assert [coluna["name"] for coluna in inspect(motor).get_columns("users")] == ["id"]
    finally:
        motor.dispose()


@pytest.mark.parametrize("etapa", ["conexao", "consulta", "sucesso", "desabilitado"])
def test_sonda_banco_sem_dados_e_sem_excecao_publica(monkeypatch, etapa):
    from src.api import health_checks
    chamadas = []

    class Conexao:
        def connect(self):
            if etapa == "conexao":
                raise RuntimeError("DETALHE_INTERNO_SINTETICO")
            return self

        def __enter__(self): return self
        def __exit__(self, *args): pass

        def execute(self, comando):
            chamadas.append(str(comando))
            if etapa == "consulta":
                raise RuntimeError("DETALHE_INTERNO_SINTETICO")

    monkeypatch.setattr(health_checks, "get_settings", lambda: SimpleNamespace(database_enabled=etapa != "desabilitado"))
    monkeypatch.setattr(health_checks, "_motor_sonda", lambda: Conexao())
    assert health_checks.banco_pronto() == (etapa == "sucesso")
    assert all("LIMIT 0" in sql for sql in chamadas)


def test_sonda_tem_timeout_e_pool_separado(monkeypatch):
    from src.api import health_checks
    chamadas = []
    monkeypatch.setattr(health_checks, "get_settings", lambda: SimpleNamespace(database_url="postgresql://exemplo"))
    monkeypatch.setattr(health_checks, "create_engine", lambda *a, **k: chamadas.append(k))
    health_checks._motor_sonda.cache_clear()
    try:
        health_checks._motor_sonda()
        assert chamadas[0]["connect_args"] == {"connect_timeout": 2, "options": "-c statement_timeout=2000"}
        assert chamadas[0]["poolclass"].__name__ == "NullPool"
    finally:
        health_checks._motor_sonda.cache_clear()


@pytest.mark.parametrize("falha", [None, "autoencoder", "detector", "preparo"])
def test_sonda_runtime_nao_carrega_modelos(monkeypatch, falha):
    from src.api import health_checks
    monkeypatch.setattr(health_checks, "runtime_preparado", falha != "preparo")

    def obter(nome):
        if falha == nome:
            raise RuntimeError("ARTEFATO_INTERNO_SINTETICO")
        return {"model": object(), "scaler": object()}

    monkeypatch.setattr(health_checks, "obter_autoencoder", lambda: obter("autoencoder"))
    monkeypatch.setattr(health_checks, "obter_detector", lambda: obter("detector"))
    assert health_checks.runtime_pronto() == (falha is None)


def test_migration_inicial_cobre_colunas_orm_sem_executar_sql(monkeypatch):
    import importlib.util
    import re
    from pathlib import Path
    from src.db.models import Base
    caminho = Path(__file__).resolve().parents[1] / "migrations/versions/20260505_0001_initial_schema.py"
    spec = importlib.util.spec_from_file_location("migration_testada", caminho)
    migration = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(migration)
    comandos = []
    monkeypatch.setattr(migration, "op", SimpleNamespace(execute=comandos.append))
    migration.upgrade()
    for nome, tabela in Base.metadata.tables.items():
        ddl = next(sql for sql in comandos if f"CREATE TABLE IF NOT EXISTS {nome} (" in sql)
        colunas = set(re.findall(r"^\s+(\w+) (?:VARCHAR|TIMESTAMP|INTEGER|SERIAL|BOOLEAN|DOUBLE|JSON|TEXT)", ddl, re.M))
        assert colunas == set(tabela.columns.keys())
    antes = list(comandos)
    migration.downgrade()
    assert comandos == antes  # downgrade histórico deliberadamente não destrutivo
