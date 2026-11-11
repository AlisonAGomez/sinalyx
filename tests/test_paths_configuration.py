"""Contratos de paths sem contaminar imports globais dos demais testes."""

import json
import os
import subprocess
import sys
from pathlib import Path

import pytest


RAIZ_PROJETO = Path(__file__).resolve().parents[1]
SCRIPT_INSPECAO = """
import json
from src.core import paths
from src.core.config import get_settings
from src.api import services as api
from src.collectors import pfsense_collector as coletor
from src.services import pfsense_incremental_service as live
from src.services import pfsense_worker_service as worker

configuracao = coletor.PfSenseCollectorConfig.from_env()
resultado = {
    "base": str(paths.BASE_DIR),
    "padrao": str(paths.DEFAULT_DATA_DIR),
    "dados": str(paths.DATA_DIR),
    "raw": str(paths.RAW_DIR),
    "processed": str(paths.PROCESSED_DIR),
    "modelos": str(paths.MODELS_DIR),
    "uploads": str(api.API_UPLOADS_DIR),
    "resultados": str(api.API_RESULTS_DIR),
    "live": str(live.LIVE_RUNTIME_DIR),
    "runs": str(live.LIVE_RUNS_DIR),
    "worker": str(worker.WORKER_DIR),
    "log": str(configuracao.local_path),
    "collector_state": str(configuracao.state_path),
    "parser_state": str(live._parser_state_path()),
    "config_log": get_settings().pfsense_local_log_path,
}
print("PATHS_TEST_RESULT=" + json.dumps(resultado))
"""


def _inspecionar_paths(*, variaveis=None, cwd=None):
    ambiente = os.environ.copy()
    ambiente["PYTHON_DOTENV_DISABLED"] = "1"
    ambiente["SINALYX_ENV"] = "local"
    ambiente["DATABASE_ENABLED"] = "false"
    for nome in (
        "SINALYX_DATA_DIR",
        "SINALYX_PFSENSE_LOCAL_LOG_PATH",
        "SINALYX_PFSENSE_COLLECTOR_STATE_PATH",
        "SINALYX_PFSENSE_PARSER_STATE_PATH",
    ):
        ambiente.pop(nome, None)
    ambiente.update(variaveis or {})
    ambiente["PYTHONPATH"] = str(RAIZ_PROJETO)
    processo = subprocess.run(
        [sys.executable, "-B", "-c", SCRIPT_INSPECAO],
        cwd=cwd or RAIZ_PROJETO,
        env=ambiente,
        capture_output=True,
        text=True,
        check=True,
    )
    linha = next(
        linha for linha in processo.stdout.splitlines()
        if linha.startswith("PATHS_TEST_RESULT=")
    )
    return json.loads(linha.removeprefix("PATHS_TEST_RESULT="))


def _validar_runtime(resultado, raiz):
    raiz = Path(raiz)
    assert Path(resultado["dados"]) == raiz
    assert Path(resultado["uploads"]) == raiz / "runtime" / "api_uploads"
    assert Path(resultado["resultados"]) == raiz / "runtime" / "api_results"
    live = raiz / "runtime" / "pfsense" / "live"
    assert Path(resultado["live"]) == live
    assert Path(resultado["runs"]) == live / "runs"
    assert Path(resultado["worker"]) == live
    assert Path(resultado["log"]) == live / "filter.log"
    assert Path(resultado["collector_state"]) == live / "collector_state.json"
    assert Path(resultado["parser_state"]) == live / "parser_state.json"
    assert resultado["config_log"] == ""


def test_sem_configuracao_preserva_paths_atuais():
    resultado = _inspecionar_paths()
    padrao = Path(resultado["base"]) / "data"
    assert Path(resultado["padrao"]) == padrao
    _validar_runtime(resultado, padrao)
    assert Path(resultado["modelos"]) == padrao / "models"


def test_dados_fora_do_aplicativo_preservam_modelos(tmp_path):
    dados = tmp_path / "programdata" / "Sinalyx"
    resultado = _inspecionar_paths(variaveis={"SINALYX_DATA_DIR": str(dados)})
    _validar_runtime(resultado, dados)
    assert Path(resultado["modelos"]) == Path(resultado["padrao"]) / "models"
    assert Path(resultado["modelos"]) != dados / "models"
    assert Path(resultado["raw"]) == dados / "raw"
    assert Path(resultado["processed"]) == dados / "processed"
    assert not dados.exists()  # Importar os módulos não cria diretórios.


def test_path_relativo_independe_do_diretorio_de_execucao(tmp_path):
    variaveis = {"SINALYX_DATA_DIR": "dados-operacionais"}
    primeiro = _inspecionar_paths(variaveis=variaveis)
    segundo = _inspecionar_paths(variaveis=variaveis, cwd=tmp_path)
    esperado = Path(primeiro["base"]) / "dados-operacionais"
    _validar_runtime(primeiro, esperado)
    assert segundo == primeiro


@pytest.mark.parametrize("nome", [
    "SINALYX_PFSENSE_LOCAL_LOG_PATH",
    "SINALYX_PFSENSE_COLLECTOR_STATE_PATH",
    "SINALYX_PFSENSE_PARSER_STATE_PATH",
])
def test_override_especifico_vence_raiz_de_dados(tmp_path, nome):
    destino = tmp_path / "especifico" / f"{nome}.json"
    resultado = _inspecionar_paths(variaveis={
        "SINALYX_DATA_DIR": str(tmp_path / "dados"),
        nome: str(destino),
    })
    campo = {
        "SINALYX_PFSENSE_LOCAL_LOG_PATH": "log",
        "SINALYX_PFSENSE_COLLECTOR_STATE_PATH": "collector_state",
        "SINALYX_PFSENSE_PARSER_STATE_PATH": "parser_state",
    }[nome]
    assert Path(resultado[campo]) == destino
    assert Path(resultado["modelos"]) == Path(resultado["padrao"]) / "models"
