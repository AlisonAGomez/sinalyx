"""Defaults internos independem do diretório de trabalho do processo."""

import os
import shutil
import subprocess
import sys
from pathlib import Path

import pytest
from alembic.config import Config
from alembic.script import ScriptDirectory


RAIZ_PROJETO = Path(__file__).resolve().parents[1]


def _executar(script: str, *, cwd: Path, variaveis: dict[str, str] | None = None) -> None:
    ambiente = os.environ.copy()
    ambiente["PYTHONPATH"] = str(RAIZ_PROJETO)
    ambiente["PYTHON_DOTENV_DISABLED"] = "1"
    ambiente["SINALYX_TEST_BASE_DIR"] = str(RAIZ_PROJETO)
    for nome in ("SINALYX_DATA_DIR", "SINALYX_MODELS_DIR"):
        ambiente.pop(nome, None)
    ambiente.update(variaveis or {})
    subprocess.run(
        [sys.executable, "-B", "-c", script],
        cwd=cwd,
        env=ambiente,
        capture_output=True,
        text=True,
        check=True,
    )


def test_imports_e_defaults_batch_fora_do_projeto(tmp_path):
    dados = tmp_path / "dados-operacionais"
    modelos = tmp_path / "modelos-oficiais"
    script = """
import os
import sys
from pathlib import Path
from src.core import paths
from src.pipelines import parse_pfsense_logs as parser
from src.pipelines import infer_pfsense_batch as batch
from src.pipelines import process_pfsense_incremental as incremental

assert paths.BASE_DIR == Path(os.environ['SINALYX_TEST_BASE_DIR'])
assert paths.DATA_DIR == Path(os.environ['SINALYX_DATA_DIR'])
assert paths.MODELS_DIR == Path(os.environ['SINALYX_MODELS_DIR'])
assert parser.DEFAULT_EVENTS_OUTPUT == paths.PROCESSED_DIR / 'pfsense' / 'parsed_events.csv'
assert parser.DEFAULT_FEATURES_OUTPUT == paths.PROCESSED_DIR / 'pfsense' / 'sinalyx_features.csv'
assert batch.DEFAULT_INPUT_FILE == paths.PROCESSED_DIR / 'pfsense' / 'sinalyx_features.csv'
assert batch.DEFAULT_OUTPUT_CSV == paths.PROCESSED_DIR / 'pfsense' / 'inference_results.csv'
assert batch.DEFAULT_OUTPUT_JSON == paths.PROCESSED_DIR / 'pfsense' / 'inference_report.json'
sys.argv = ['parser', '--input', 'meu-log.log']
argumentos = parser.parse_args()
assert argumentos.input == 'meu-log.log'
assert Path(argumentos.events_output) == parser.DEFAULT_EVENTS_OUTPUT
sys.argv = ['parser', '--input', 'meu-log.log', '--events-output', 'saida.csv']
assert parser.parse_args().events_output == 'saida.csv'
sys.argv = ['batch', '--input', 'entrada.csv', '--output-csv', 'saida.csv']
argumentos = batch.parse_args()
assert argumentos.input == 'entrada.csv' and argumentos.output_csv == 'saida.csv'
sys.argv = ['incremental', '--skip-collect', '--no-persist']
assert incremental.parse_args().window == '5s'
"""
    _executar(script, cwd=tmp_path, variaveis={
        "SINALYX_DATA_DIR": str(dados),
        "SINALYX_MODELS_DIR": str(modelos),
    })
    assert not dados.exists() and not modelos.exists()


def test_fallback_de_paths_independe_do_cwd(tmp_path):
    _executar("""
from src.core.paths import BASE_DIR, DATA_DIR, MODELS_DIR
assert DATA_DIR == BASE_DIR / 'data'
assert MODELS_DIR == BASE_DIR / 'data' / 'models'
""", cwd=tmp_path)


@pytest.mark.parametrize("valor_ambiente,esperado", [
    (None, "do-arquivo-conhecido"),
    ("do-ambiente", "do-ambiente"),
])
def test_dotenv_conhecido_independe_do_cwd_e_respeita_ambiente(
    tmp_path, valor_ambiente, esperado
):
    raiz_temporaria = tmp_path / "aplicativo"
    modulo = raiz_temporaria / "src" / "core" / "config.py"
    modulo.parent.mkdir(parents=True)
    shutil.copyfile(RAIZ_PROJETO / "src" / "core" / "config.py", modulo)
    (raiz_temporaria / ".env").write_text(
        "SINALYX_DATA_DIR=do-arquivo-conhecido\n", encoding="utf-8"
    )
    outro_cwd = tmp_path / "outro-cwd"
    outro_cwd.mkdir()
    (outro_cwd / ".env").write_text("SINALYX_DATA_DIR=do-cwd\n", encoding="utf-8")
    ambiente = os.environ.copy()
    ambiente.pop("PYTHON_DOTENV_DISABLED", None)
    ambiente.pop("SINALYX_DATA_DIR", None)
    if valor_ambiente is not None:
        ambiente["SINALYX_DATA_DIR"] = valor_ambiente
    script = """
import importlib.util
import os
import sys
from pathlib import Path
modulo = Path(sys.argv[1])
spec = importlib.util.spec_from_file_location('config_teste', modulo)
config = importlib.util.module_from_spec(spec)
sys.modules[spec.name] = config
spec.loader.exec_module(config)
assert os.environ['SINALYX_DATA_DIR'] == sys.argv[2]
"""
    subprocess.run(
        [sys.executable, "-B", "-c", script, str(modulo), esperado],
        cwd=outro_cwd, env=ambiente, capture_output=True, text=True, check=True,
    )


def test_sem_dotenv_conhecido_usa_ambiente(tmp_path):
    modulo = tmp_path / "aplicativo" / "src" / "core" / "config.py"
    modulo.parent.mkdir(parents=True)
    shutil.copyfile(RAIZ_PROJETO / "src" / "core" / "config.py", modulo)
    ambiente = os.environ.copy()
    ambiente.pop("PYTHON_DOTENV_DISABLED", None)
    ambiente["SINALYX_DATA_DIR"] = "somente-ambiente"
    subprocess.run(
        [sys.executable, "-B", "-c", """
import importlib.util, os, sys
spec = importlib.util.spec_from_file_location('config_teste', sys.argv[1])
modulo = importlib.util.module_from_spec(spec)
sys.modules[spec.name] = modulo
spec.loader.exec_module(modulo)
assert os.environ['SINALYX_DATA_DIR'] == 'somente-ambiente'
""", str(modulo)],
        cwd=tmp_path, env=ambiente, capture_output=True, text=True, check=True,
    )


def test_alembic_localiza_migrations_fora_do_projeto(tmp_path, monkeypatch):
    monkeypatch.chdir(tmp_path)
    configuracao = Config(str(RAIZ_PROJETO / "alembic.ini"))
    assert Path(configuracao.get_main_option("script_location")) == RAIZ_PROJETO / "migrations"
    assert Path(configuracao.get_main_option("prepend_sys_path")) == RAIZ_PROJETO
    assert ScriptDirectory.from_config(configuracao).get_heads()


def test_alembic_preserva_path_de_instalacao_com_espacos(tmp_path, monkeypatch):
    aplicativo = tmp_path / "Program Files" / "Sinalyx"
    (aplicativo / "migrations" / "versions").mkdir(parents=True)
    shutil.copyfile(RAIZ_PROJETO / "alembic.ini", aplicativo / "alembic.ini")
    monkeypatch.chdir(tmp_path)
    configuracao = Config(str(aplicativo / "alembic.ini"))
    assert [Path(caminho) for caminho in configuracao.get_prepend_sys_paths_list()] == [aplicativo]
    assert Path(ScriptDirectory.from_config(configuracao).dir) == aplicativo / "migrations"
