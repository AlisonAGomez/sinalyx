"""Diagnóstico de falhas sem mensagens, variáveis locais ou conteúdos sensíveis."""

import logging
import traceback
from uuid import uuid4

from starlette.responses import JSONResponse
from starlette.types import ASGIApp, Receive, Scope, Send


logger = logging.getLogger("sinalyx.api")


def registrar_falha(operacao: str, erro: BaseException) -> None:
    """Registra tipo e pontos de código; exc_info poderia expor SQL ou credenciais."""
    origem = [
        f"{quadro.f_globals.get('__name__', '')}.{quadro.f_code.co_name}:{linha}"
        for quadro, linha in traceback.walk_tb(erro.__traceback__)
    ]
    logger.error(
        "Falha operacao=%s erro_id=%s tipo=%s origem=%s",
        operacao, uuid4().hex, type(erro).__name__, " -> ".join(origem),
    )


MENSAGENS_VALIDACAO_USUARIO = frozenset({
    "Papel de usuario invalido. Use admin ou user.",
    "Email obrigatorio.", "Nome obrigatorio.", "Senha obrigatoria.",
    "Ja existe um usuario com este email.",
    "Ja existe outro usuario com este email.",
    "O administrador supremo nao pode ter o email alterado.",
    "O administrador supremo nao pode ser rebaixado.",
    "O administrador supremo nao pode ser desativado.",
    "O administrador supremo nao pode ser removido.",
    "Nao e permitido deixar o sistema sem administrador ativo.",
    "Nao e permitido remover o proprio usuario autenticado.",
    "Nao e permitido remover o ultimo administrador ativo.",
})


def mensagem_validacao_usuario(erro: ValueError) -> str:
    """Preserva apenas mensagens de negócio conhecidas, sem interpolação externa."""
    mensagem = str(erro)
    if mensagem in MENSAGENS_VALIDACAO_USUARIO:
        return mensagem
    registrar_falha("validacao_usuario", erro)
    return "Nao foi possivel validar a alteracao do usuario."


def sanitizar_erros_operacionais(valor):
    """Copia a resposta live sem expor textos técnicos do estado persistente."""
    if isinstance(valor, list):
        return [sanitizar_erros_operacionais(item) for item in valor]
    if not isinstance(valor, dict):
        return valor
    resposta = {}
    for chave, item in valor.items():
        if chave in {"error", "last_error", "inference_error", "exception"} and isinstance(item, str) and item:
            resposta[chave] = "Nao foi possivel concluir a operacao."
        elif chave == "errors" and isinstance(item, list):
            resposta[chave] = ["Nao foi possivel concluir a operacao." for _ in item]
        else:
            resposta[chave] = sanitizar_erros_operacionais(item)
    return resposta


class ErrosPublicosMiddleware:
    """Converte falhas não tratadas antes da resposta, sem propagar texto ao servidor."""

    def __init__(self, app: ASGIApp) -> None:
        """Guarda a aplicação que receberá as requisições protegidas pelo tratamento de erros."""
        self.app = app

    async def __call__(self, scope: Scope, receive: Receive, send: Send) -> None:
        """Trata falhas não previstas antes do início da resposta sem expor detalhes internos."""
        if scope["type"] != "http":
            await self.app(scope, receive, send)
            return
        iniciada = False

        async def enviar(mensagem):
            """Registra se os cabeçalhos da resposta já foram enviados antes de tratar um erro."""
            nonlocal iniciada
            if mensagem["type"] == "http.response.start":
                iniciada = True
            await send(mensagem)

        try:
            await self.app(scope, receive, enviar)
        except Exception as exc:
            registrar_falha("requisicao_api", exc)
            if iniciada:
                # Não é possível trocar status/corpo após o início de uma resposta.
                raise RuntimeError("Falha apos inicio da resposta HTTP.") from None
            resposta = JSONResponse(status_code=500, content={
                "status": "error", "error_code": "internal_error",
                "message": "Nao foi possivel concluir a solicitacao.", "details": {},
            })
            await resposta(scope, receive, send)
