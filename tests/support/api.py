"""Helpers ASGI e fluxo sintético compartilhados pela suíte."""

import json
import threading


async def requisicao(app, corpo, *, caminho="/analyze/pfsense", headers=None, blocos=64, metodo="POST"):
    """Executa o app ASGI real sem httpx, rede ou lifespan de produção."""
    mensagens = []
    posicao = 0

    async def receber():
        nonlocal posicao
        trecho = corpo[posicao:posicao + blocos]
        posicao += len(trecho)
        return {"type": "http.request", "body": trecho, "more_body": posicao < len(corpo)}

    async def enviar(mensagem):
        mensagens.append(mensagem)

    scope = {
        "type": "http", "asgi": {"version": "3.0"}, "http_version": "1.1",
        "method": metodo, "scheme": "http", "path": caminho, "root_path": "",
        "query_string": b"", "headers": headers or [],
        "server": ("testserver", 80), "client": ("testclient", 1234),
    }
    await app(scope, receber, enviar)
    status = next(m["status"] for m in mensagens if m["type"] == "http.response.start")
    body = b"".join(m.get("body", b"") for m in mensagens if m["type"] == "http.response.body")
    return status, json.loads(body), posicao


def multipart(conteudo, nome="teste.log"):
    corpo = (
        f'--teste\r\nContent-Disposition: form-data; name="file"; filename="{nome}"\r\n'
        'Content-Type: text/plain\r\n\r\n'
    ).encode() + conteudo + b"\r\n--teste--\r\n"
    return corpo, [(b"content-type", b"multipart/form-data; boundary=teste")]


def preparar_fluxo(monkeypatch, services):
    import pandas as pd

    chamadas = []

    def pipeline(**kwargs):
        chamadas.append(("parser", threading.get_ident()))
        assert kwargs["input_path"].read_bytes() == b"log sintetico"
        kwargs["events_output"].write_text("sintetico", encoding="utf-8")
        kwargs["features_output"].write_text("sintetico", encoding="utf-8")
        return pd.DataFrame({"parse_status": ["success"], "parsed_successfully": [True]}), pd.DataFrame({"connections": [1]})

    def inferencia(**kwargs):
        chamadas.append(("inferencia", threading.get_ident()))
        kwargs["output_csv"].write_text("sintetico", encoding="utf-8")
        kwargs["output_json"].write_text("{}", encoding="utf-8")
        return pd.DataFrame([{"final_label": "normal", "attack_type": "normal",
                              "risk_level": "low", "confidence": 0.9}]), {}

    def persistir(*args):
        chamadas.append(("persistencia", threading.get_ident()))

    monkeypatch.setattr(services, "run_pipeline", pipeline)
    monkeypatch.setattr(services, "run_inference", inferencia)
    monkeypatch.setattr(services, "save_analysis_to_database", persistir)
    return chamadas
