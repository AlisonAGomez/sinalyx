"""Controles de acesso com dados sintéticos e ASGI local, sem credenciais reais."""

import asyncio
import json
from dataclasses import replace
from types import SimpleNamespace

import pytest

from tests.support.api import requisicao


@pytest.fixture(autouse=True)
def isolar_limitador(ambiente):
    main, _, _ = ambiente
    anterior = main.app.middleware_stack
    main.app.middleware_stack = None
    yield
    main.app.middleware_stack = anterior


def test_senha_grande_nao_e_refletida_na_resposta(ambiente, caplog):
    main, _, _ = ambiente
    senha = "SEGREDO_SINTETICO" * 100
    status, payload, _ = asyncio.run(requisicao(
        main.app, json.dumps({"email": "teste@example.test", "password": senha}).encode(),
        caminho="/auth/login", headers=[(b"content-type", b"application/json")],
    ))
    assert status == 422
    assert "SEGREDO_SINTETICO" not in json.dumps(payload) + caplog.text


@pytest.mark.parametrize("campo,tamanho", [("email", 256), ("password", 1025)])
def test_limites_login(ambiente, campo, tamanho):
    from pydantic import ValidationError
    from src.api.schemas import AuthLoginRequest
    dados = {"email": "teste@example.test", "password": "frase senha sintetica"}
    dados[campo] = "x" * tamanho
    with pytest.raises(ValidationError):
        AuthLoginRequest(**dados)


def test_frase_senha_longa_permitida(ambiente):
    from src.api.schemas import AuthLoginRequest
    assert len(AuthLoginRequest(email="teste@example.test", password="x" * 1024).password) == 1024


def test_limitador_expira_separa_clientes_e_limita_memoria(ambiente):
    from src.api.auth_request_limits import LimitadorLogin
    agora = [0.0]
    controle = LimitadorLogin(tentativas=2, janela_segundos=60, max_clientes=2, relogio=lambda: agora[0])
    assert controle.verificar("a") == 0
    assert controle.verificar("a") == 0
    assert controle.verificar("a") == 60
    assert controle.verificar("b") == 0
    assert controle.verificar("c") == 60
    assert len(controle.clientes) == 2
    agora[0] = 60
    assert controle.verificar("c") == 0
    assert len(controle.clientes) == 1


@pytest.mark.parametrize("segredo", ["", "sinalyx-local-dev-secret-change-me", "a" * 64, "abc123" * 10, "0123456789abcdef" * 4], ids=["ausente", "padrao", "repetido", "previsivel", "sequencia"])
def test_perfil_compartilhado_rejeita_segredo_fraco(ambiente, monkeypatch, segredo):
    from src.auth import security
    from src.core.config import get_settings
    configuracao = replace(get_settings(), environment="demo", auth_secret_key=segredo)
    monkeypatch.setattr(security, "get_settings", lambda: configuracao)
    with pytest.raises(RuntimeError, match="SINALYX_AUTH_SECRET_KEY"):
        security.get_auth_secret()


def test_segredo_forte_e_local_preservados(ambiente, monkeypatch):
    import secrets
    from src.auth import security
    from src.core.config import get_settings
    configuracao = replace(get_settings(), environment="local", auth_secret_key="")
    monkeypatch.setattr(security, "get_settings", lambda: configuracao)
    assert security.get_auth_secret() == security.LOCAL_AUTH_SECRET
    segredo = secrets.token_urlsafe(48)
    configuracao = replace(configuracao, environment="production", auth_secret_key=segredo)
    assert security.get_auth_secret() == segredo


def test_segredo_invalido_interrompe_startup_antes_do_banco(ambiente, monkeypatch):
    main, _, _ = ambiente
    from src.auth import security
    from src.core.config import get_settings
    configuracao = replace(get_settings(), environment="demo", auth_secret_key="")
    monkeypatch.setattr(security, "get_settings", lambda: configuracao)
    monkeypatch.setattr(main, "create_tables", lambda: pytest.fail("Não deve inicializar banco"))
    with pytest.raises(RuntimeError):
        main.startup()


def chamar_login(main, *, dados=None, cliente="192.0.2.10", cabecalhos=None, corpo=None):
    headers_resposta = {}

    async def app(scope, receive, send):
        scope["client"] = (cliente, 1234)
        async def enviar(mensagem):
            if mensagem["type"] == "http.response.start":
                headers_resposta.update(dict(mensagem["headers"]))
            await send(mensagem)
        await main.app(scope, receive, enviar)

    dados = dados or {"email": "teste@example.test", "password": "SENHA_SINTETICA"}
    resposta = asyncio.run(requisicao(
        app, corpo if corpo is not None else json.dumps(dados).encode(), caminho="/auth/login",
        headers=[(b"content-type", b"application/json")] + (cabecalhos or []),
    ))
    return (*resposta, headers_resposta)


@pytest.mark.parametrize("cenario", ["valido", "senha_invalida", "inexistente", "inativo"])
def test_login_com_autenticacao_real_e_banco_simulado(ambiente, monkeypatch, caplog, cenario):
    from datetime import datetime
    from src.db import repository
    from src.auth import security
    main, _, _ = ambiente
    usuario = SimpleNamespace(
        id=1, name="Pessoa sintetica", email="teste@example.test", role="user",
        is_active=cenario != "inativo", created_at=datetime(2026, 1, 1), updated_at=datetime(2026, 1, 1),
        password_hash=security.hash_password("SENHA_SINTETICA"),
    )

    class Sessao:
        fechada = False
        def execute(self, consulta): return self
        def scalar_one_or_none(self): return None if cenario == "inexistente" else usuario
        def close(self): self.fechada = True

    sessao = Sessao()
    monkeypatch.setattr(repository, "_require_database", lambda: None)
    monkeypatch.setattr(repository, "SessionLocal", lambda: sessao)
    status, payload, _, _ = chamar_login(main, dados={
        "email": "teste@example.test",
        "password": "INCORRETA" if cenario == "senha_invalida" else "SENHA_SINTETICA",
    })
    assert sessao.fechada
    if cenario == "valido":
        assert status == 200
        assert payload["data"]["token_type"] == "bearer"
        assert security.decode_access_token(payload["data"]["access_token"])["sub"] == "1"
        assert payload["data"]["user"]["email"] == usuario.email
    else:
        assert status == 401
        assert payload["detail"]["message"] == "Email ou senha invalidos."
    assert "SENHA_SINTETICA" not in json.dumps(payload) + caplog.text
    assert "password_hash" not in json.dumps(payload)


def test_rate_limit_http_retry_after_e_header_falso(ambiente, monkeypatch):
    from src.api import auth_request_limits
    from src.core.config import get_settings
    main, _, _ = ambiente
    config = replace(get_settings(), login_max_tentativas=2)
    monkeypatch.setattr(auth_request_limits, "get_settings", lambda: config)
    consultas = []
    monkeypatch.setattr(main, "authenticate_user", lambda *args: consultas.append(True))
    assert chamar_login(main)[0] == 401
    assert chamar_login(main)[0] == 401
    status, payload, _, headers = chamar_login(main, cabecalhos=[(b"x-forwarded-for", b"198.51.100.99")])
    assert status == 429
    assert 1 <= int(headers[b"retry-after"]) <= 60
    assert payload["detail"]["error_code"] == "login_rate_limited"
    assert len(consultas) == 2
    assert chamar_login(main, cliente="192.0.2.11")[0] == 401


def test_corpo_login_sem_content_length_e_limitado(ambiente, monkeypatch, caplog):
    main, _, _ = ambiente
    monkeypatch.setattr(main, "authenticate_user", lambda *args: pytest.fail("Não deve consultar"))
    corpo = b'{"password":"' + b"SENHA_SINTETICA" * 4000 + b'"}'
    status, payload, lidos, _ = chamar_login(main, corpo=corpo)
    assert status == 413
    assert lidos < len(corpo)
    assert "SENHA_SINTETICA" not in json.dumps(payload) + caplog.text


@pytest.mark.parametrize("schema", ["UserCreateRequest", "UserUpdateRequest"])
@pytest.mark.parametrize("campo,tamanho", [("email", 256), ("name", 256), ("role", 33), ("password", 1025)])
def test_limites_administrativos(ambiente, schema, campo, tamanho):
    from src.api import schemas
    from pydantic import ValidationError
    dados = {"name": "Teste", "email": "teste@example.test", "password": "sintetica", "role": "user"}
    dados[campo] = "x" * tamanho
    with pytest.raises(ValidationError):
        getattr(schemas, schema)(**dados)


def test_perfil_desconhecido_nao_cai_em_local(ambiente, monkeypatch):
    from src.core.config import get_settings
    monkeypatch.setenv("SINALYX_ENV", "produciton")
    get_settings.cache_clear()
    try:
        with pytest.raises(ValueError, match="SINALYX_ENV invalido"):
            get_settings()
    finally:
        get_settings.cache_clear()


@pytest.mark.parametrize(
    ("url_banco", "senha_postgres", "erro_esperado"),
    [
        ("", "", "DATABASE_URL"),
        ("postgresql://sinalyx:sinalyx@localhost:5432/sinalyx", "", "DATABASE_URL"),
        ("postgresql://sinalyx:senha-sintetica@localhost:5432/sinalyx", "sinalyx", "POSTGRES_PASSWORD"),
    ],
)
def test_perfil_compartilhado_rejeita_banco_de_desenvolvimento(
    ambiente, monkeypatch, url_banco, senha_postgres, erro_esperado,
):
    from src.core.config import get_settings

    monkeypatch.setenv("SINALYX_ENV", "demo")
    monkeypatch.setenv("DATABASE_ENABLED", "true")
    monkeypatch.setenv("DATABASE_URL", url_banco)
    monkeypatch.setenv("POSTGRES_PASSWORD", senha_postgres)
    get_settings.cache_clear()
    try:
        with pytest.raises(ValueError, match=erro_esperado):
            get_settings()
    finally:
        get_settings.cache_clear()


def test_banco_proprio_em_demo_e_default_local_preservado(ambiente, monkeypatch):
    from src.core.config import DEFAULT_DATABASE_URL, get_settings

    monkeypatch.setenv("SINALYX_ENV", "demo")
    monkeypatch.setenv("DATABASE_ENABLED", "true")
    monkeypatch.setenv("DATABASE_URL", "postgresql://sinalyx:senha-sintetica@localhost:5432/sinalyx")
    monkeypatch.setenv("POSTGRES_PASSWORD", "senha-sintetica")
    get_settings.cache_clear()
    try:
        assert get_settings().is_production_like
        monkeypatch.setenv("SINALYX_ENV", "local")
        monkeypatch.setenv("DATABASE_URL", "")
        monkeypatch.setenv("POSTGRES_PASSWORD", "sinalyx")
        get_settings.cache_clear()
        assert get_settings().database_url == DEFAULT_DATABASE_URL
    finally:
        get_settings.cache_clear()


def test_limitador_concorrente_respeita_teto(ambiente):
    from concurrent.futures import ThreadPoolExecutor
    from src.api.auth_request_limits import LimitadorLogin
    controle = LimitadorLogin(tentativas=3, janela_segundos=60, max_clientes=10)
    with ThreadPoolExecutor(max_workers=4) as executor:
        resultados = list(executor.map(controle.verificar, ["cliente"] * 12))
    assert resultados.count(0) == 3


def test_json_invalido_nao_reflete_senha(ambiente, caplog):
    main, _, _ = ambiente
    status, payload, _, _ = chamar_login(main, corpo=b'{"password":"SENHA_SINTETICA",')
    assert status == 422
    assert "SENHA_SINTETICA" not in json.dumps(payload) + caplog.text


def test_reinicio_limitador_reinicia_janela(ambiente):
    from src.api.auth_request_limits import LimitadorLogin
    config = dict(tentativas=1, janela_segundos=60, max_clientes=1)
    anterior = LimitadorLogin(**config)
    assert anterior.verificar("a") == 0
    assert anterior.verificar("a") > 0
    assert LimitadorLogin(**config).verificar("a") == 0
