"""Integridade dos estados JSON do parser e coletor live."""

import json
import os
from datetime import datetime
from pathlib import Path

import numpy as np
import pandas as pd
import pytest

from src.core import atomic_json


def _legacy_bytes(payload):
    return json.dumps(payload, ensure_ascii=False, indent=2).replace(
        "\n", os.linesep,
    ).encode("utf-8")


def test_criacao_utf8_e_substituicao_sem_temporarios(tmp_path):
    destino = tmp_path / "nova" / "estado.json"
    primeiro = {"mensagem": "ação", "offset": 1}
    segundo = {"mensagem": "próxima", "offset": 2}

    atomic_json.write_json_atomic(destino, primeiro)
    assert destino.read_bytes() == _legacy_bytes(primeiro)
    assert list(destino.parent.iterdir()) == [destino]

    atomic_json.write_json_atomic(destino, segundo)
    assert json.loads(destino.read_text(encoding="utf-8")) == segundo
    assert list(destino.parent.iterdir()) == [destino]


@pytest.mark.parametrize("etapa", ["write", "fsync", "replace"])
def test_falha_preserva_estado_anterior_e_remove_temporario(tmp_path, monkeypatch, etapa):
    destino = tmp_path / "estado.json"
    anterior = b'{"offset": 10, "valido": true}'
    destino.write_bytes(anterior)

    def falha_escrita(payload, file, **kwargs):
        file.write('{"parcial":')
        raise RuntimeError("falha simulada")

    def falha_sistema(*args, **kwargs):
        raise RuntimeError("falha simulada")

    if etapa == "write":
        monkeypatch.setattr(atomic_json.json, "dump", falha_escrita)
    elif etapa == "fsync":
        monkeypatch.setattr(atomic_json.os, "fsync", falha_sistema)
    else:
        monkeypatch.setattr(atomic_json.os, "replace", falha_sistema)

    with pytest.raises(RuntimeError, match="falha simulada"):
        atomic_json.write_json_atomic(destino, {"offset": 20})
    assert destino.read_bytes() == anterior
    assert list(tmp_path.iterdir()) == [destino]


def test_parser_state_preserva_conversao_e_conteudo_logico(tmp_path, monkeypatch):
    from src.services import pfsense_incremental_service as parser

    destino = tmp_path / "parser_state.json"
    log = tmp_path / "filter.log"
    monkeypatch.setattr(parser, "_parser_state_path", lambda local_log_path=None: destino)
    estado = {
        "offset": 5,
        "file_size": 10,
        "total_lines_processed": 2,
        "generation_signature": "sha256:1:abc",
        "last_run_at": datetime(2026, 1, 1, 12, 0),
        "pending_events": [{
            "timestamp": pd.Timestamp("2026-01-01T12:00:00"),
            "source": Path("origem.log"),
            "score": np.float64(float("nan")),
        }],
    }

    parser._save_parser_state(log, estado)
    esperado = parser._to_builtin(estado)
    assert destino.read_bytes() == _legacy_bytes(esperado)
    assert parser._read_json(destino) == esperado
    assert esperado["pending_events_count"] == 1
    assert esperado["pending_events"][0]["score"] is None
    assert list(tmp_path.iterdir()) == [destino]


def test_collector_state_mantem_payload_e_leitura(coletor):
    modulo, config = coletor
    payload = {
        "last_fetch_status": "success",
        "generation_signature": "sha256:1:abc",
        "last_fetch_at": "2026-01-01T12:00:00",
        "file_size": 17,
    }

    modulo._write_json(config.state_path, payload)
    assert config.state_path.read_bytes() == _legacy_bytes(payload)
    assert modulo._read_json(config.state_path) == payload
    assert modulo.read_collector_state(config)["generation_signature"] == payload["generation_signature"]
    assert list(config.state_path.parent.iterdir()) == [config.state_path]
