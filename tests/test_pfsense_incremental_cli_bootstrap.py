"""Preparação inicial da CLI incremental fora da rodada de processamento."""

import json
from types import SimpleNamespace

import pytest


def _args(*, no_persist=False):
    return SimpleNamespace(
        skip_collect=True, no_persist=no_persist, window="5s",
        finite_file=False, flush_pending=False, runtime_profile=None,
    )


@pytest.mark.parametrize("no_persist", [False, True])
def test_cli_bootstrap_somente_quando_persiste(monkeypatch, capsys, no_persist):
    from src.db import init_db
    from src.pipelines import process_pfsense_incremental as cli
    from src.services import pfsense_incremental_service as live

    chamadas = []
    monkeypatch.setattr(cli, "parse_args", lambda: _args(no_persist=no_persist))
    monkeypatch.setattr(init_db, "create_tables", lambda: chamadas.append("bootstrap"))
    monkeypatch.setattr(live, "process_live_pfsense", lambda **kwargs: chamadas.append("rodada") or {"status": "success"})
    cli.main()
    assert chamadas == (["rodada"] if no_persist else ["bootstrap", "rodada"])
    assert json.loads(capsys.readouterr().out)["status"] == "success"


def test_cli_falha_de_bootstrap_nao_inicia_rodada(monkeypatch, capsys):
    from src.db import init_db
    from src.pipelines import process_pfsense_incremental as cli
    from src.services import pfsense_incremental_service as live

    monkeypatch.setattr(cli, "parse_args", lambda: _args())
    monkeypatch.setattr(init_db, "create_tables", lambda: (_ for _ in ()).throw(OSError("detalhe interno")))
    monkeypatch.setattr(live, "process_live_pfsense", lambda **kwargs: pytest.fail("rodada não deve começar"))
    cli.main()
    response = json.loads(capsys.readouterr().out)
    assert response["status"] == "error"
    assert "detalhe interno" not in json.dumps(response)
