"""Fixtures compartilhadas; cada teste mantém escopo e isolamento originais."""

from types import SimpleNamespace

import pytest
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker


@pytest.fixture
def ambiente(monkeypatch, tmp_path):
    monkeypatch.setenv("PYTHON_DOTENV_DISABLED", "1")
    monkeypatch.setenv("DATABASE_ENABLED", "false")
    from src.api import main, services

    monkeypatch.setattr(services, "API_UPLOADS_DIR", tmp_path / "uploads")
    monkeypatch.setattr(services, "API_RESULTS_DIR", tmp_path / "resultados")
    monkeypatch.setattr(services, "get_settings", lambda: SimpleNamespace(limite_upload_bytes=1024))
    from src.api import upload_limits

    monkeypatch.setattr(upload_limits, "get_settings", lambda: SimpleNamespace(limite_upload_bytes=1024))
    main.app.dependency_overrides[main.get_current_user] = lambda: {"id": 1, "role": "user"}
    yield main, services, tmp_path
    main.app.dependency_overrides.clear()


@pytest.fixture
def banco(monkeypatch):
    monkeypatch.setenv("PYTHON_DOTENV_DISABLED", "1")
    from src.db import repository, models

    motor = create_engine("sqlite://")
    models.Base.metadata.create_all(motor)
    fabrica = sessionmaker(bind=motor)
    monkeypatch.setattr(repository, "SessionLocal", fabrica)
    monkeypatch.setattr(repository, "_require_database", lambda: None)
    configuracao = SimpleNamespace(admin_email="inicial@example.test", admin_name="Inicial",
                                   admin_password="SENHA_SINTETICA", super_admin_email="protegido@example.test")
    monkeypatch.setattr(repository, "get_settings", lambda: configuracao)
    yield repository, models, fabrica, configuracao
    motor.dispose()


@pytest.fixture
def coletor(monkeypatch, tmp_path):
    monkeypatch.setenv("PYTHON_DOTENV_DISABLED", "1")
    from src.collectors import pfsense_collector as modulo

    config = modulo.PfSenseCollectorConfig(
        host="ssh.example.test", port=22, username="usuario_sintetico",
        password="SENHA_SINTETICA_NAO_REAL", key_path=None,
        remote_path="/var/log/filter.log", local_path=tmp_path / "filter.log",
        state_path=tmp_path / "state.json", connect_timeout=1,
        known_hosts_path=tmp_path / "known_hosts",
    )
    return modulo, config


@pytest.fixture
def entrada():
    from src.models.decision_engine import resolve_config
    from src.models.ensemble import EnsembleConfig, resolve_ensemble_config

    return dict(
        if_output=dict(pred=1, raw_score=-0.3, normalized_score=0.8, confidence=0.8),
        ae_output=dict(pred=1, raw_score=20.0, normalized_score=0.9, confidence=0.9),
        heuristic_output=dict(heuristic_detected_attack=True, heuristic_confidence=0.85,
                              attack_type="syn_flood", heuristic_reason="Sinal sintético"),
        features={}, metadata={}, runtime_profile="balanced",
        ensemble_config=resolve_ensemble_config(EnsembleConfig(if_weight=0.19, ae_weight=0.91), runtime_profile="balanced"),
        decision_config=resolve_config(profile="balanced"), ae_reference_threshold=9.0,
    )
