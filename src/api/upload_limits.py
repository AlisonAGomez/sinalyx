"""Limite do corpo recebido antes do spool multipart do FastAPI."""

from fastapi import HTTPException
from starlette.types import ASGIApp, Receive, Scope, Send

from src.core.config import get_settings


def detalhe_limite_upload(limite: int) -> dict:
    """Monta a mensagem de arquivo grande demais, incluindo o limite em bytes."""
    return {
        "status": "error", "error_code": "upload_too_large",
        "message": "O arquivo ou a requisicao excede o limite de upload permitido.",
        "details": {"limit_bytes": limite},
    }


class ErroLimiteUpload(HTTPException):
    """Erro de arquivo ou requisição maior que o limite permitido."""
    def __init__(self, limite: int) -> None:
        """Cria o erro HTTP 413 com o limite de tamanho permitido."""
        super().__init__(status_code=413, detail=detalhe_limite_upload(limite))


class LimiteUploadMiddleware:
    """Controle do tamanho recebido antes de processar o arquivo de log."""
    def __init__(self, app: ASGIApp) -> None:
        """Guarda a aplicação para limitar a leitura dos arquivos enviados."""
        self.app = app

    async def __call__(self, scope: Scope, receive: Receive, send: Send) -> None:
        """Limita os bytes recebidos no envio de logs antes de encaminhar à análise."""
        caminho = scope.get("path", "")
        raiz = scope.get("root_path", "").rstrip("/")
        if raiz and caminho.startswith(raiz + "/"):
            caminho = caminho[len(raiz):]
        if scope["type"] != "http" or scope.get("method") != "POST" or caminho.rstrip("/") != "/analyze/pfsense":
            await self.app(scope, receive, send)
            return

        limite = get_settings().limite_upload_bytes
        recebidos = 0

        async def receber_limitado():
            """Conta os bytes recebidos e interrompe a leitura quando o corpo ultrapassa o limite."""
            nonlocal recebidos
            mensagem = await receive()
            if mensagem["type"] == "http.request":
                recebidos += len(mensagem.get("body", b""))
                if recebidos > limite:
                    # Starlette fecha o arquivo temporário quando a leitura do corpo da requisição falha.
                    raise ErroLimiteUpload(limite)
            return mensagem

        await self.app(scope, receber_limitado, send)
