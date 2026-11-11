"""Proteção local por processo, antes de ler JSON ou consultar credenciais."""

import math
import time
from collections import OrderedDict
from threading import Lock
from typing import Callable

from fastapi import HTTPException
from starlette.responses import JSONResponse
from starlette.types import ASGIApp, Receive, Scope, Send

from src.core.config import get_settings


LIMITE_CORPO_IDENTIDADE_BYTES = 32 * 1024


def caminho_requisicao(scope: Scope) -> str:
    """Obtém o caminho da rota, retirando o prefixo usado pelo servidor intermediário."""
    caminho = scope.get("path", "")
    raiz = scope.get("root_path", "").rstrip("/")
    if raiz and caminho.startswith(raiz + "/"):
        caminho = caminho[len(raiz):]
    return caminho.rstrip("/")


def entrada_identidade(scope: Scope) -> bool:
    """Identifica as requisições que podem receber dados de login ou de contas."""
    caminho = caminho_requisicao(scope)
    return scope.get("method") in {"POST", "PATCH"} and (
        caminho == "/auth/login" or caminho == "/admin/users" or caminho.startswith("/admin/users/")
    )


class LimitadorLogin:
    """Janela fixa; expira entradas sem expulsar clientes ativos quando lotado."""

    def __init__(
        self, *, tentativas: int, janela_segundos: int, max_clientes: int,
        relogio: Callable[[], float] = time.monotonic,
    ) -> None:
        """Valida os limites e prepara os contadores de tentativas por cliente."""
        if min(tentativas, janela_segundos, max_clientes) < 1:
            raise ValueError("Os limites de login devem ser positivos.")
        self.tentativas = tentativas
        self.janela_segundos = janela_segundos
        self.max_clientes = max_clientes
        self.relogio = relogio
        self.clientes: OrderedDict[str, tuple[float, int]] = OrderedDict()
        self.trava = Lock()

    def verificar(self, cliente: str) -> int:
        """Retorna segundos de espera, ou zero quando a tentativa é permitida."""
        with self.trava:
            agora = self.relogio()
            while self.clientes and next(iter(self.clientes.values()))[0] <= agora:
                self.clientes.popitem(last=False)
            entrada = self.clientes.get(cliente)
            if entrada is None:
                if len(self.clientes) >= self.max_clientes:
                    return max(1, math.ceil(next(iter(self.clientes.values()))[0] - agora))
                entrada = (agora + self.janela_segundos, 0)
            expira, usadas = entrada
            if usadas >= self.tentativas:
                return max(1, math.ceil(expira - agora))
            self.clientes[cliente] = (expira, usadas + 1)
            return 0


class LimitesAcessoMiddleware:
    """Limites de tamanho e tentativas aplicados antes das rotas de contas."""
    def __init__(self, app: ASGIApp) -> None:
        """Conecta a aplicação aos limites de tentativas e tamanho das requisições de contas."""
        self.app = app
        config = get_settings()
        self.limitador = LimitadorLogin(
            tentativas=config.login_max_tentativas,
            janela_segundos=config.login_janela_segundos,
            max_clientes=config.login_max_clientes,
        )

    async def __call__(self, scope: Scope, receive: Receive, send: Send) -> None:
        """Controla tentativas de login e tamanho dos dados enviados às rotas de contas."""
        if scope["type"] != "http" or not entrada_identidade(scope):
            await self.app(scope, receive, send)
            return
        if caminho_requisicao(scope) == "/auth/login":
            # Cabeçalhos de proxy só têm efeito se o servidor ASGI confiar no proxy.
            cliente = scope.get("client")
            espera = self.limitador.verificar(str(cliente[0]) if cliente else "desconhecido")
            if espera:
                resposta = JSONResponse(status_code=429, headers={"Retry-After": str(espera)}, content={
                    "detail": {"status": "error", "error_code": "login_rate_limited",
                               "message": "Muitas tentativas de login. Aguarde e tente novamente.", "details": {}},
                })
                await resposta(scope, receive, send)
                return
        recebidos = 0

        async def receber_limitado():
            """Conta os bytes recebidos e interrompe a leitura quando o corpo ultrapassa o limite."""
            nonlocal recebidos
            mensagem = await receive()
            if mensagem["type"] == "http.request":
                recebidos += len(mensagem.get("body", b""))
                if recebidos > LIMITE_CORPO_IDENTIDADE_BYTES:
                    raise HTTPException(status_code=413, detail={
                        "status": "error", "error_code": "request_too_large",
                        "message": "A requisicao excede o limite permitido.", "details": {},
                    })
            return mensagem

        await self.app(scope, receber_limitado, send)
