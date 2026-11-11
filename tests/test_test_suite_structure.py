"""Impede que módulos de teste sejam bibliotecas de outros testes."""

import ast
from pathlib import Path


def test_modulos_de_teste_nao_importam_outros_modulos_de_teste():
    raiz = Path(__file__).resolve().parent
    relacoes = []
    for arquivo in raiz.rglob("test_*.py"):
        arvore = ast.parse(arquivo.read_text(encoding="utf-8"), filename=str(arquivo))
        for no in ast.walk(arvore):
            if isinstance(no, ast.Import):
                modulos = [alias.name for alias in no.names]
            elif isinstance(no, ast.ImportFrom):
                modulos = [no.module or ""]
                if no.level or (no.module or "") in {"tests", "tests.experiments"}:
                    modulos.extend(alias.name for alias in no.names)
            else:
                continue
            for modulo in modulos:
                if any(parte.startswith("test_") for parte in modulo.split(".")):
                    relacoes.append(f"{arquivo.relative_to(raiz)}:{no.lineno} -> {modulo}")
    assert relacoes == []
