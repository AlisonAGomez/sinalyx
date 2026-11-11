"""Swagger precisa funcionar na API direta e sob o prefixo removido pelo Nginx."""

import asyncio
import json
import re
from urllib.parse import urljoin

import pytest


async def obter(caminho):
    from src.api.main import app
    mensagens = []

    async def receber():
        return {"type": "http.request", "body": b"", "more_body": False}

    async def enviar(mensagem):
        mensagens.append(mensagem)

    await app({"type": "http", "asgi": {"version": "3.0"}, "http_version": "1.1",
               "method": "GET", "scheme": "http", "path": caminho, "root_path": "",
               "query_string": b"", "headers": [], "server": ("testserver", 80),
               "client": ("testclient", 1234)}, receber, enviar)
    status = next(m["status"] for m in mensagens if m["type"] == "http.response.start")
    corpo = b"".join(m.get("body", b"") for m in mensagens if m["type"] == "http.response.body")
    return status, corpo.decode()


@pytest.mark.parametrize("prefixo", ["", "/api"])
def test_schema_e_operacoes_preservam_prefixo_externo(prefixo):
    status, html = asyncio.run(obter('/docs'))
    assert status == 200
    url_schema = re.search(r"url:\s*'([^']+)'", html).group(1)
    externo = 'http://testserver' + prefixo
    assert urljoin(externo + '/docs', url_schema) == externo + '/openapi.json'
    status, corpo = asyncio.run(obter('/openapi.json'))
    assert status == 200
    schema = json.loads(corpo)
    assert schema['servers'] == [{'url': '.'}]
    assert urljoin(externo + '/openapi.json', schema['servers'][0]['url']) == externo + '/'
    assert '/analyze/pfsense' in schema['paths']
