"""Resolucao isolada do store de modelos sem carregar arquivos de apoio binarios."""

import json
import os
import subprocess
import sys
from pathlib import Path

import pytest

from src.core.model_registry import profile_has_runtime_artifacts


RAIZ_PROJETO = Path(__file__).resolve().parents[1]
ARQUIVOS_OBRIGATORIOS = (
    "scaler.joblib",
    "isolation.pkl",
    "autoencoder/model.keras",
    "threshold.pkl",
    "manifest.json",
)
SCRIPT_INSPECAO = """
import json
import os
from pathlib import Path
from src.core import paths
from src.core import model_registry as registro

if os.getenv("SINALYX_TEST_READONLY") == "1":
    abrir_original = Path.open
    def abrir_sem_escrita(self, mode="r", *args, **kwargs):
        if any(marcador in mode for marcador in "wax+"):
            raise AssertionError("A resolucao nao deve escrever modelos.")
        return abrir_original(self, mode, *args, **kwargs)
    Path.open = abrir_sem_escrita
    def bloquear_mkdir(self, *args, **kwargs):
        raise AssertionError("A resolucao nao deve criar diretorios.")
    Path.mkdir = bloquear_mkdir

legado = {"profiles": {
    "current": {"artifact_path": "data/models"},
    "hybrid_v2_3": {"artifact_path": "data/models/hybrid_v2_3"},
}}
resultado = {
    "base": str(paths.BASE_DIR),
    "dados": str(paths.DATA_DIR),
    "padrao": str(paths.DEFAULT_MODELS_DIR),
    "modelos": str(paths.MODELS_DIR),
    "registry": str(registro.MODEL_REGISTRY_FILE),
    "current_legado": str(registro.profile_path("current", legado)),
    "historico_legado": str(registro.profile_path("hybrid_v2_3", legado)),
}
if os.getenv("SINALYX_TEST_RESOLVE") == "1":
    cadastro = registro.load_model_registry()
    resolucao = registro.resolve_model_profile(registry=cadastro)
    resultado.update({
        "ativo": cadastro.get("active_profile"),
        "fallback": cadastro.get("fallback_profile"),
        "resolvido": resolucao.profile_name,
        "origem": resolucao.source,
        "caminho_resolvido": str(resolucao.profile_path),
        "pronto": registro.profile_has_runtime_artifacts(resolucao.profile_path),
        "valido": registro.validate_model_registry(cadastro)["valid"],
        "avisos": list(resolucao.warnings),
    })
if os.getenv("SINALYX_TEST_ARTIFACT_SAFETY") == "1":
    from src.core import artifacts
    resultado["artefatos_disponiveis"] = artifacts.models_available()
    try:
        artifacts.clear_model_artifacts()
    except PermissionError:
        resultado["limpeza_bloqueada"] = True
    else:
        resultado["limpeza_bloqueada"] = False
print("MODELS_TEST_RESULT=" + json.dumps(resultado))
"""


def _inspecionar(*, variaveis=None, cwd=None):
    ambiente = os.environ.copy()
    ambiente["PYTHON_DOTENV_DISABLED"] = "1"
    ambiente["PYTHONPATH"] = str(RAIZ_PROJETO)
    for nome in ("SINALYX_MODELS_DIR", "SINALYX_DATA_DIR", "SINALYX_MODEL_PROFILE"):
        ambiente.pop(nome, None)
    ambiente.update(variaveis or {})
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
        if linha.startswith("MODELS_TEST_RESULT=")
    )
    return json.loads(linha.removeprefix("MODELS_TEST_RESULT="))


def _criar_store(tmp_path, *, threshold_legado=False):
    store = tmp_path / "app" / "models"
    obrigatorios = list(ARQUIVOS_OBRIGATORIOS)
    if threshold_legado:
        obrigatorios[3] = "autoencoder/threshold.pkl"
    for nome in obrigatorios:
        destino = store / nome
        destino.parent.mkdir(parents=True, exist_ok=True)
        destino.write_bytes(b"artefato-sintetico")
    (store / "ensemble.json").write_text("{}", encoding="utf-8")
    (store / "model_registry.json").write_text(json.dumps({
        "active_profile": "current",
        "fallback_profile": "current",
        "profiles": {
            "current": {
                "display_name": "Current", "description": "Oficial",
                "status": "active", "production_usable": True,
                "artifact_path": "data/models",
            },
            "hybrid_v2_3": {
                "display_name": "Historico", "description": "Validacao",
                "status": "candidate", "production_usable": False,
                "artifact_path": "data/models/hybrid_v2_3",
            },
        },
    }), encoding="utf-8")
    return store


def test_fallback_de_modelos_permanece_no_projeto():
    resultado = _inspecionar()
    esperado = Path(resultado["base"]) / "data" / "models"
    assert Path(resultado["modelos"]) == Path(resultado["padrao"]) == esperado
    assert Path(resultado["registry"]) == esperado / "model_registry.json"
    assert Path(resultado["current_legado"]) == esperado


def test_store_externo_separa_modelos_dos_dados_e_preserva_current(tmp_path):
    store = _criar_store(tmp_path)
    dados = tmp_path / "programdata"
    resultado = _inspecionar(variaveis={
        "SINALYX_MODELS_DIR": str(store),
        "SINALYX_DATA_DIR": str(dados),
        "SINALYX_TEST_RESOLVE": "1",
        "SINALYX_TEST_READONLY": "1",
    })
    assert Path(resultado["modelos"]) == store
    assert Path(resultado["dados"]) == dados
    assert Path(resultado["registry"]) == store / "model_registry.json"
    assert Path(resultado["current_legado"]) == store
    assert Path(resultado["historico_legado"]) == store / "hybrid_v2_3"
    assert resultado["ativo"] == resultado["fallback"] == resultado["resolvido"] == "current"
    assert Path(resultado["caminho_resolvido"]) == store
    assert resultado["pronto"] and resultado["valido"]
    assert not dados.exists()


def test_store_relativo_e_registry_independem_do_cwd(tmp_path):
    variaveis = {"SINALYX_MODELS_DIR": "modelos-configurados"}
    primeiro = _inspecionar(variaveis=variaveis)
    segundo = _inspecionar(variaveis=variaveis, cwd=tmp_path)
    assert segundo == primeiro
    assert Path(primeiro["modelos"]) == Path(primeiro["base"]) / "modelos-configurados"
    assert Path(primeiro["current_legado"]) == Path(primeiro["modelos"])


def test_uma_variavel_nao_altera_a_outra(tmp_path):
    dados = tmp_path / "dados"
    apenas_dados = _inspecionar(variaveis={"SINALYX_DATA_DIR": str(dados)})
    assert Path(apenas_dados["dados"]) == dados
    assert Path(apenas_dados["modelos"]) == Path(apenas_dados["padrao"])
    store = tmp_path / "models"
    apenas_modelos = _inspecionar(variaveis={"SINALYX_MODELS_DIR": str(store)})
    assert Path(apenas_modelos["dados"]) == Path(apenas_modelos["base"]) / "data"
    assert Path(apenas_modelos["modelos"]) == store
    assert not store.exists()


def test_store_invalido_nao_recua_para_modelos_antigos(tmp_path):
    store = tmp_path / "ausente" / "models"
    resultado = _inspecionar(variaveis={
        "SINALYX_MODELS_DIR": str(store),
        "SINALYX_TEST_RESOLVE": "1",
    })
    assert Path(resultado["registry"]) == store / "model_registry.json"
    assert Path(resultado["caminho_resolvido"]) == store
    assert resultado["origem"] == "legacy_default_missing_validation"
    assert not resultado["pronto"] and not resultado["valido"]
    assert resultado["avisos"]
    assert not store.exists()


def test_current_externo_mantem_bloqueio_de_limpeza(tmp_path):
    store = _criar_store(tmp_path)
    resultado = _inspecionar(variaveis={
        "SINALYX_MODELS_DIR": str(store),
        "SINALYX_TEST_ARTIFACT_SAFETY": "1",
    })
    assert resultado["artefatos_disponiveis"]
    assert resultado["limpeza_bloqueada"]
    assert profile_has_runtime_artifacts(store)


@pytest.mark.parametrize("ausente", ARQUIVOS_OBRIGATORIOS)
def test_checker_exige_artefatos_minimos(tmp_path, ausente):
    store = _criar_store(tmp_path)
    assert profile_has_runtime_artifacts(store)
    (store / ausente).unlink()
    assert not profile_has_runtime_artifacts(store)


def test_checker_aceita_threshold_legado_e_ensemble_opcional(tmp_path):
    store = _criar_store(tmp_path, threshold_legado=True)
    (store / "ensemble.json").unlink()
    assert profile_has_runtime_artifacts(store)
