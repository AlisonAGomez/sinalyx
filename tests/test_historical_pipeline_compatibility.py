"""Compatibilidade dos caminhos históricos sem acessar arquivos de apoio reais."""

from __future__ import annotations

import importlib
import os
import subprocess
import sys
from pathlib import Path

import pytest


MODULOS = ("prepare", "train", "validate", "reporting", "stream_processor")
RAIZ = Path(__file__).resolve().parents[1]


@pytest.mark.parametrize("nome", MODULOS)
def test_import_legado_reutiliza_modulo_historico(nome: str) -> None:
    historico = importlib.import_module(f"scripts.historical.pipelines.{nome}")
    legado = importlib.import_module(f"src.pipelines.{nome}")

    assert legado is historico


def _executar(modulo: str, *argumentos: str) -> subprocess.CompletedProcess[str]:
    ambiente = os.environ.copy()
    ambiente["PYTHONDONTWRITEBYTECODE"] = "1"
    return subprocess.run(
        [sys.executable, "-B", "-m", modulo, *argumentos],
        cwd=RAIZ,
        env=ambiente,
        capture_output=True,
        text=True,
        check=False,
        timeout=60,
    )


@pytest.mark.parametrize(
    "modulo",
    ("src.pipelines.train", "scripts.historical.pipelines.train"),
)
def test_cli_treino_bloqueia_antes_de_ler_dataset(
    modulo: str, tmp_path: Path
) -> None:
    entrada_inexistente = tmp_path / "dataset-inexistente.csv"

    resultado = _executar(modulo, "--input", str(entrada_inexistente))

    assert resultado.returncode == 2
    assert "runtime current esta protegido" in resultado.stderr
    assert "Carregando dataset" not in resultado.stdout
    assert not entrada_inexistente.exists()


@pytest.mark.parametrize("nome", ("train", "validate", "stream_processor"))
def test_ajuda_cli_antiga_continua_disponivel(nome: str) -> None:
    resultado = _executar(f"src.pipelines.{nome}", "--help")

    assert resultado.returncode == 0
    assert "usage:" in resultado.stdout
