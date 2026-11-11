"""Entradas legadas compartilham estado e CLI com os módulos canônicos."""

import importlib
import subprocess
import sys
from pathlib import Path

import pytest


@pytest.mark.parametrize("old_name,new_name", [
    ("src.models.classifier", "src.models.heuristics"),
    ("src.models.detection", "src.models.isolation_forest"),
    ("src.services.pfsense_live_service", "src.services.pfsense_incremental_service"),
    ("src.pipelines.process_live_pfsense", "src.pipelines.process_pfsense_incremental"),
])
def test_legacy_import_shares_module_state(monkeypatch, old_name, new_name):
    current = importlib.import_module(new_name)
    legacy = importlib.import_module(old_name)
    marker = object()
    monkeypatch.setattr(current, "_compatibility_probe", marker, raising=False)
    assert legacy._compatibility_probe is marker
    assert legacy is current


def test_legacy_cli_preserves_options():
    outputs = []
    for name in ("process_live_pfsense", "process_pfsense_incremental"):
        result = subprocess.run(
            [sys.executable, "-m", f"src.pipelines.{name}", "--help"],
            cwd=Path(__file__).resolve().parents[1],
            capture_output=True, text=True, check=True,
        )
        outputs.append(result.stdout.replace(name, "pipeline"))
    # O argparse alinha o help conforme o comprimento do nome executado.
    assert outputs[0].split() == outputs[1].split()
    assert "--skip-collect" in outputs[0]
    assert "--finite-file" in outputs[0]
