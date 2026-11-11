"""Regressões A02/A03 com ASGI local e arquivos sintéticos, sem servidor ou modelos."""

import asyncio
import io
import json
import threading
from types import SimpleNamespace

import pytest
from starlette.datastructures import UploadFile


from tests.support.api import multipart, preparar_fluxo, requisicao


def assert_sem_temporarios(raiz, *, resultados=False):
    assert not list((raiz / "uploads").glob("*"))
    if resultados:
        assert not list((raiz / "resultados").glob("*"))


def test_fluxo_http_preserva_contrato_e_executa_fora_do_event_loop(ambiente, monkeypatch):
    main, services, raiz = ambiente
    chamadas = preparar_fluxo(monkeypatch, services)
    corpo, headers = multipart(b"log sintetico")
    status, payload, _ = asyncio.run(requisicao(main.app, corpo, headers=headers))
    assert status == 200
    assert payload["status"] == "success"
    assert payload["total_windows"] == 1
    assert payload["persistence"] == {"database_saved": True, "error": None}
    assert set(payload) == {"status", "analysis_id", "filename", "created_at", "total_windows",
                            "summary", "classification", "counts", "parse_stats", "artifacts",
                            "results", "persistence"}
    assert [nome for nome, _ in chamadas] == ["parser", "inferencia", "persistencia"]
    assert all(ident != threading.get_ident() for _, ident in chamadas)
    assert_sem_temporarios(raiz)
    assert (raiz / "resultados" / payload["analysis_id"] / services.ANALYSIS_SUMMARY_FILE).exists()


@pytest.mark.parametrize("conteudo,nome,status,codigo", [
    (b"", "teste.log", 400, "empty_file"),
    (b" \n\t", "teste.log", 400, "empty_file"),
    (b"x", "teste.csv", 415, "invalid_extension"),
    (b"x" * 1025, "teste.log", 413, "upload_too_large"),
])
def test_rejeicao_fecha_upload_e_limpa(ambiente, monkeypatch, conteudo, nome, status, codigo):
    _, services, raiz = ambiente
    monkeypatch.setattr(services, "run_pipeline", lambda **kw: pytest.fail("Não deve processar"))
    upload = UploadFile(filename=nome, file=io.BytesIO(conteudo))
    with pytest.raises(services.ApiServiceError) as erro:
        asyncio.run(services.analyze_pfsense_upload(upload))
    assert erro.value.status_code == status
    assert erro.value.error_code == codigo
    assert upload.file.closed
    assert_sem_temporarios(raiz, resultados=True)


@pytest.mark.parametrize("content_length", [None, b"1", b"5000"])
def test_limite_http_independe_content_length_e_fecha_spool(ambiente, monkeypatch, content_length):
    main, services, raiz = ambiente
    from starlette import formparsers
    original = formparsers.SpooledTemporaryFile
    arquivos = []

    def criar(*args, **kwargs):
        arquivo = original(*args, **kwargs)
        arquivos.append(arquivo)
        return arquivo

    monkeypatch.setattr(formparsers, "SpooledTemporaryFile", criar)
    monkeypatch.setattr(services, "run_pipeline", lambda **kw: pytest.fail("Não deve processar"))
    corpo, headers = multipart(b"x" * 4000)
    if content_length:
        headers.append((b"content-length", content_length))
    status, payload, lidos = asyncio.run(requisicao(main.app, corpo, headers=headers))
    assert status == 413
    assert payload["error_code"] == "upload_too_large"
    assert lidos < len(corpo)
    assert arquivos and all(a.closed for a in arquivos)
    assert_sem_temporarios(raiz, resultados=True)


@pytest.mark.parametrize("etapa,excecao,status,codigo", [
    ("run_pipeline", ValueError, 500, "parser_error"),
    ("run_inference", FileNotFoundError, 503, "model_not_found"),
    ("run_inference", ValueError, 422, "inference_error"),
    ("run_inference", RuntimeError, 503, "inference_error"),
    ("run_inference", Exception, 500, "internal_error"),
    ("_save_json", OSError, 500, "internal_error"),
])
def test_falha_http_sanitizada_com_cleanup_e_diagnostico(ambiente, monkeypatch, caplog, etapa, excecao, status, codigo):
    main, services, raiz = ambiente
    preparar_fluxo(monkeypatch, services)

    def falhar(*args, **kwargs):
        raise excecao("SEGREDO_SINTETICO /privado/modelo SELECT senha")

    monkeypatch.setattr(services, etapa, falhar)
    corpo, headers = multipart(b"log sintetico")
    obtido, payload, _ = asyncio.run(requisicao(main.app, corpo, headers=headers))
    assert obtido == status
    assert payload["error_code"] == codigo
    assert "SEGREDO_SINTETICO" not in json.dumps(payload) + caplog.text
    assert payload["message"]
    assert excecao.__name__ in caplog.text
    assert "falhar" in caplog.text
    assert_sem_temporarios(raiz, resultados=True)


def test_falha_banco_preserva_fallback_local_sem_expor_excecao(ambiente, monkeypatch, caplog):
    main, services, raiz = ambiente
    preparar_fluxo(monkeypatch, services)

    def falhar(*args):
        raise RuntimeError("SEGREDO_SINTETICO SQL")

    monkeypatch.setattr(services, "save_analysis_to_database", falhar)
    corpo, headers = multipart(b"log sintetico")
    status, payload, _ = asyncio.run(requisicao(main.app, corpo, headers=headers))
    assert status == 200
    assert payload["persistence"] == {"database_saved": False, "error": "Nao foi possivel salvar a analise no banco de dados."}
    assert "SEGREDO_SINTETICO" not in json.dumps(payload) + caplog.text
    assert "RuntimeError" in caplog.text
    assert_sem_temporarios(raiz)
    assert (raiz / "resultados" / payload["analysis_id"] / services.ANALYSIS_RESULTS_FILE).exists()


def test_upload_sem_autenticacao_permanece_negado(ambiente):
    main, _, _ = ambiente
    main.app.dependency_overrides.clear()
    corpo, headers = multipart(b"log sintetico")
    status, _, _ = asyncio.run(requisicao(main.app, corpo, headers=headers))
    assert status == 401


def test_copia_limitada_aceita_limite_exato_e_preserva_arquivos_antigos(ambiente, monkeypatch):
    _, services, raiz = ambiente
    preparar_fluxo(monkeypatch, services)
    monkeypatch.setattr(services, "get_settings", lambda: SimpleNamespace(limite_upload_bytes=13))
    services.ensure_api_runtime_dirs()
    anterior = raiz / "uploads" / "anterior.log"
    anterior.write_bytes(b"preservar")

    class LeituraControlada(io.BytesIO):
        def read(self, tamanho=-1):
            assert 0 < tamanho <= 64 * 1024
            return super().read(tamanho)

    upload = UploadFile(filename="teste.log", file=LeituraControlada(b"log sintetico"))
    resposta = asyncio.run(services.analyze_pfsense_upload(upload))
    assert resposta["status"] == "success"
    assert upload.file.closed
    assert anterior.read_bytes() == b"preservar"
    assert list((raiz / "uploads").iterdir()) == [anterior]


def test_erro_durante_leitura_remove_arquivo_incompleto(ambiente, caplog):
    _, services, raiz = ambiente

    class LeituraComFalha(io.BytesIO):
        def read(self, tamanho=-1):
            if self.tell():
                raise OSError("SEGREDO_SINTETICO")
            return super().read(1)

    upload = UploadFile(filename="teste.log", file=LeituraComFalha(b"abc"))
    with pytest.raises(services.ApiServiceError) as erro:
        asyncio.run(services.analyze_pfsense_upload(upload))
    assert erro.value.status_code == 500
    assert upload.file.closed
    assert "SEGREDO_SINTETICO" not in caplog.text
    assert_sem_temporarios(raiz, resultados=True)


def test_cancelamento_aguarda_worker_antes_do_cleanup(ambiente, monkeypatch):
    import anyio
    _, services, raiz = ambiente
    preparar_fluxo(monkeypatch, services)
    pipeline = services.run_pipeline
    liberar = threading.Event()
    upload = UploadFile(filename="teste.log", file=io.BytesIO(b"log sintetico"))

    async def executar():
        iniciou = asyncio.Event()
        loop = asyncio.get_running_loop()

        def processar(**kwargs):
            loop.call_soon_threadsafe(iniciou.set)
            assert liberar.wait(timeout=5), "Event loop não liberou o worker"
            assert not upload.file.closed
            return pipeline(**kwargs)

        monkeypatch.setattr(services, "run_pipeline", processar)
        async with anyio.create_task_group() as grupo:
            grupo.start_soon(services.analyze_pfsense_upload, upload)
            with anyio.fail_after(5):
                await iniciou.wait()
            grupo.cancel_scope.cancel()
            liberar.set()

    anyio.run(executar)
    assert upload.file.closed
    assert_sem_temporarios(raiz)


def test_parser_real_com_fixture_sintetica(ambiente, monkeypatch):
    main, services, raiz = ambiente
    pipeline = services.run_pipeline
    preparar_fluxo(monkeypatch, services)
    monkeypatch.setattr(services, "run_pipeline", pipeline)
    linha = (
        b"Aug 28 13:22:49 pfSense filterlog[20915]: "
        b"66,,,12004,em0,match,block,in,4,0x0,,128,32770,0,none,17,udp,78,"
        b"192.0.2.10,198.51.100.20,137,137,58\n"
    )
    corpo, headers = multipart(linha)
    status, payload, _ = asyncio.run(requisicao(main.app, corpo, headers=headers))
    assert status == 200
    assert payload["parse_stats"]["parsed_successfully"] == 1
    assert_sem_temporarios(raiz)


def test_erros_de_linhas_nao_expoem_conteudo(ambiente, monkeypatch):
    import pandas as pd
    main, services, raiz = ambiente
    monkeypatch.setattr(services, "run_pipeline", lambda **kwargs: (
        pd.DataFrame({"parsed_successfully": [False], "parse_status": ["failed"],
                      "error": ["SEGREDO_SINTETICO"]}), pd.DataFrame(),
    ))
    corpo, headers = multipart(b"x")
    status, payload, _ = asyncio.run(requisicao(main.app, corpo, headers=headers))
    assert status == 422
    assert payload["details"] == {"parse_status_counts": {"failed": 1}}
    assert "SEGREDO_SINTETICO" not in json.dumps(payload)
    assert_sem_temporarios(raiz, resultados=True)


@pytest.mark.parametrize("funcao,caminho,status", [
    ("summarize_history_from_database", "/history/summary", 200),
    ("list_history_windows_from_database", "/history/windows", 200),
    ("get_history_window_by_id_from_database", "/history/windows/1", 500),
    ("list_history_alerts_from_database", "/history/alerts", 200),
    ("list_history_executions_from_database", "/history/executions", 200),
])
def test_historico_preserva_envelope_sem_excecao(ambiente, monkeypatch, caplog, funcao, caminho, status):
    main, services, _ = ambiente
    monkeypatch.setattr(services, "is_database_available", lambda: True)

    def falhar(*args, **kwargs):
        raise RuntimeError("SEGREDO_SINTETICO SQL")

    monkeypatch.setattr(services, funcao, falhar)
    obtido, payload, _ = asyncio.run(requisicao(main.app, b"", caminho=caminho, metodo="GET"))
    assert obtido == status
    assert payload["status"] == "error"
    assert "SEGREDO_SINTETICO" not in json.dumps(payload) + caplog.text
    assert "RuntimeError" in caplog.text


def test_login_sanitiza_erro_banco_sem_alterar_status(ambiente, monkeypatch, caplog):
    main, _, _ = ambiente

    def falhar(*args):
        raise RuntimeError("SEGREDO_SINTETICO SQL")

    monkeypatch.setattr(main, "authenticate_user", falhar)
    status, payload, _ = asyncio.run(requisicao(
        main.app, b'{"email":"teste@example.test","password":"sintetica"}',
        caminho="/auth/login", headers=[(b"content-type", b"application/json")],
    ))
    assert status == 503
    assert payload["detail"]["error_code"] == "auth_database_unavailable"
    assert "SEGREDO_SINTETICO" not in json.dumps(payload) + caplog.text
    assert "RuntimeError" in caplog.text


@pytest.mark.parametrize("excecao,status", [(FileNotFoundError, 503), (RuntimeError, 503), (ValueError, 422), (Exception, 500)])
def test_predict_sanitiza_erro_e_preserva_tipo_details(ambiente, monkeypatch, caplog, excecao, status):
    main, _, _ = ambiente

    def falhar(*args):
        raise excecao("SEGREDO_SINTETICO modelo")

    monkeypatch.setattr(main, "prepare_inference_records", falhar)
    dados = {"connections": 1, "bytes": 1, "packets": 1, "packet_size": 1, "ports": 1}
    obtido, payload, _ = asyncio.run(requisicao(
        main.app, json.dumps(dados).encode(), caminho="/predict",
        headers=[(b"content-type", b"application/json")],
    ))
    assert obtido == status
    assert payload["detail"]["details"] == ""
    assert "SEGREDO_SINTETICO" not in json.dumps(payload) + caplog.text
    assert excecao.__name__ in caplog.text


def test_falha_inesperada_nao_propaga_excecao_bruta(ambiente, monkeypatch, caplog):
    main, _, _ = ambiente
    monkeypatch.setattr(main, "authenticate_user", lambda *args: {"id": 1, "email": "teste@example.test", "role": "user"})

    def falhar(**kwargs):
        raise OSError("SEGREDO_SINTETICO")

    monkeypatch.setattr(main, "create_access_token", falhar)
    status, payload, _ = asyncio.run(requisicao(
        main.app, b'{"email":"teste@example.test","password":"sintetica"}',
        caminho="/auth/login", headers=[(b"content-type", b"application/json")],
    ))
    assert status == 500
    assert payload["message"] == "Nao foi possivel concluir a solicitacao."
    assert "SEGREDO_SINTETICO" not in json.dumps(payload) + caplog.text
    assert "OSError" in caplog.text


def test_estado_live_sanitizado_sem_modificar_estado_original(ambiente, monkeypatch):
    main, _, _ = ambiente
    estado = {"last_error": "SEGREDO_SINTETICO", "offset": 42, "error": None}
    monkeypatch.setattr(main, "get_parser_status", lambda: estado)
    status, payload, _ = asyncio.run(requisicao(main.app, b"", caminho="/live/pfsense/parser/status", metodo="GET"))
    assert status == 200
    assert payload["state"]["offset"] == 42
    assert payload["state"]["error"] is None
    assert payload["state"]["last_error"] == "Nao foi possivel concluir a operacao."
    assert estado["last_error"] == "SEGREDO_SINTETICO"


def test_validacao_usuario_permite_somente_mensagens_conhecidas(ambiente, caplog):
    from src.api.error_sanitization import mensagem_validacao_usuario
    assert mensagem_validacao_usuario(ValueError("Email obrigatorio.")) == "Email obrigatorio."
    assert mensagem_validacao_usuario(ValueError("SEGREDO_SINTETICO")) == "Nao foi possivel validar a alteracao do usuario."
    assert "SEGREDO_SINTETICO" not in caplog.text


@pytest.mark.parametrize("valor,esperado", [(None, 52428800), ("4096", 4096), ("0", 1), ("invalido", 52428800)])
def test_configuracao_limite_em_bytes(ambiente, monkeypatch, valor, esperado):
    from src.core.config import get_settings
    if valor is None:
        monkeypatch.delenv("SINALYX_LIMITE_UPLOAD_BYTES", raising=False)
    else:
        monkeypatch.setenv("SINALYX_LIMITE_UPLOAD_BYTES", valor)
    get_settings.cache_clear()
    try:
        assert get_settings().limite_upload_bytes == esperado
    finally:
        get_settings.cache_clear()


@pytest.mark.parametrize("etapa", ["sem_linhas", "sem_janelas", "sem_resultados"])
def test_saidas_vazias_removem_temporarios(ambiente, monkeypatch, etapa):
    import pandas as pd
    main, services, raiz = ambiente
    preparar_fluxo(monkeypatch, services)
    if etapa == "sem_linhas":
        monkeypatch.setattr(services, "run_pipeline", lambda **kw: (pd.DataFrame(), pd.DataFrame()))
    elif etapa == "sem_janelas":
        monkeypatch.setattr(services, "run_pipeline", lambda **kw: (pd.DataFrame({"parsed_successfully": [True]}), pd.DataFrame()))
    else:
        monkeypatch.setattr(services, "run_inference", lambda **kw: (pd.DataFrame(), {}))
    corpo, headers = multipart(b"log sintetico")
    status, _, _ = asyncio.run(requisicao(main.app, corpo, headers=headers))
    assert status == (400 if etapa == "sem_linhas" else 422)
    assert_sem_temporarios(raiz, resultados=True)


def test_colisao_de_nome_nao_remove_upload_preexistente(ambiente, monkeypatch):
    _, services, raiz = ambiente
    services.ensure_api_runtime_dirs()
    paths = services._build_analysis_paths("teste.log")
    paths["upload_path"].write_bytes(b"preservar")
    monkeypatch.setattr(services, "_build_analysis_paths", lambda nome: paths)
    upload = UploadFile(filename="teste.log", file=io.BytesIO(b"log sintetico"))
    with pytest.raises(services.ApiServiceError):
        asyncio.run(services.analyze_pfsense_upload(upload))
    assert paths["upload_path"].read_bytes() == b"preservar"
    assert not paths["result_dir"].exists()


def test_falha_de_cleanup_e_registrada_sem_falso_sucesso(ambiente, monkeypatch, caplog):
    from pathlib import Path
    main, services, raiz = ambiente
    preparar_fluxo(monkeypatch, services)
    unlink = Path.unlink

    def negar(caminho, *args, **kwargs):
        if caminho.parent == raiz / "uploads":
            raise PermissionError("SEGREDO_SINTETICO")
        return unlink(caminho, *args, **kwargs)

    monkeypatch.setattr(Path, "unlink", negar)
    corpo, headers = multipart(b"log sintetico")
    status, payload, _ = asyncio.run(requisicao(main.app, corpo, headers=headers))
    assert status == 500
    assert payload["message"] == "Nao foi possivel finalizar a analise com seguranca."
    assert "limpeza_temporario" in caplog.text
    assert "SEGREDO_SINTETICO" not in caplog.text + json.dumps(payload)


def test_identificadores_de_diagnostico_sao_distintos(ambiente, caplog):
    import re
    from src.api.error_sanitization import registrar_falha
    for _ in range(2):
        try:
            raise ValueError("SEGREDO_SINTETICO")
        except ValueError as erro:
            registrar_falha("teste_diagnostico", erro)
    identificadores = re.findall(r"erro_id=([0-9a-f]{32})", caplog.text)
    assert len(set(identificadores)) == 2
    assert "SEGREDO_SINTETICO" not in caplog.text


def test_sanitizacao_live_preserva_estrutura_de_erros(ambiente):
    from src.api.error_sanitization import sanitizar_erros_operacionais
    original = {"error": {"code": "query_failed", "message": "Consulta indisponivel.",
                           "details": {"exception": "SEGREDO_SINTETICO"}},
                "persistence": {"errors": ["SEGREDO_SINTETICO"]},
                "parser": {"inference_error": "SEGREDO_SINTETICO"}}
    copia = sanitizar_erros_operacionais(original)
    assert "SEGREDO_SINTETICO" not in json.dumps(copia)
    assert copia["error"]["code"] == "query_failed"
    assert len(copia["persistence"]["errors"]) == 1
    assert original["parser"]["inference_error"] == "SEGREDO_SINTETICO"


def test_admin_continua_negado_a_usuario_comum(ambiente):
    main, _, _ = ambiente
    status, _, _ = asyncio.run(requisicao(main.app, b"", caminho="/admin/users", metodo="GET"))
    assert status == 403
