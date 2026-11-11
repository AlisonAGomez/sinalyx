"""Retenção restrita aos arquivos de apoio auxiliares de execuções live concluídas."""

import os
from contextlib import contextmanager
from datetime import datetime, timedelta, timezone
from pathlib import Path
from types import SimpleNamespace
from uuid import UUID

import pytest

from src.core.config import get_settings
from src.services import live_run_retention as retention


REFERENCE = datetime(2026, 1, 1, 12, tzinfo=timezone.utc)


def _run(root: Path, number: int, *, age_hours: float, summary: bool = True) -> Path:
    directory = root / str(UUID(int=number))
    directory.mkdir(parents=True)
    (directory / "parsed_events.csv").write_text("evento sintético", encoding="utf-8")
    if summary:
        marker = directory / retention.SUMMARY_NAME
        marker.write_text('{"status":"error"}', encoding="utf-8")
        modified = (REFERENCE - timedelta(hours=age_hours)).timestamp()
        os.utime(marker, (modified, modified))
    return directory


def _retain(root: Path, **kwargs):
    return retention.retain_live_runs(root, reference_time=REFERENCE, **kwargs)


def test_desabilitada_e_abaixo_dos_limites_nao_remove(tmp_path):
    root = tmp_path / "runs"
    older = _run(root, 1, age_hours=30)
    assert _retain(root, enabled=False, max_count=1, max_age_hours=24)["removed"] == 0
    assert older.exists()
    result = _retain(root, max_count=2, max_age_hours=48)
    assert result["eligible"] == result["removed"] == 0
    assert older.exists()


@pytest.mark.parametrize("age_hours,removed", [(23, False), (24, True), (25, True)])
def test_idade_inclui_limite_exato(tmp_path, age_hours, removed):
    root = tmp_path / "runs"
    directory = _run(root, 1, age_hours=age_hours)
    result = _retain(root, max_count=0, max_age_hours=24)
    assert (not directory.exists()) == removed
    assert result["removed_by_age"] == int(removed)


def test_count_mantem_tres_mais_recentes(tmp_path):
    root = tmp_path / "runs"
    directories = [_run(root, index, age_hours=6 - index) for index in range(1, 6)]
    result = _retain(root, max_count=3, max_age_hours=0)
    assert result["removed"] == result["removed_by_count"] == 2
    assert [path.exists() for path in directories] == [False, False, True, True, True]


def test_idade_ou_count_tornam_elegivel(tmp_path):
    root = tmp_path / "runs"
    older = _run(root, 1, age_hours=25)
    middle = _run(root, 2, age_hours=2)
    recent = _run(root, 3, age_hours=1)
    result = _retain(root, max_count=1, max_age_hours=24)
    assert not older.exists() and not middle.exists() and recent.exists()
    assert result["removed"] == 2
    assert result["removed_by_age"] == 1
    assert result["removed_by_count"] == 2


def test_criterios_zero_nao_apagam(tmp_path):
    root = tmp_path / "runs"
    directory = _run(root, 1, age_hours=100)
    assert _retain(root, max_count=0, max_age_hours=0)["removed"] == 0
    assert directory.exists()


def test_incompleto_protegido_arquivo_solto_e_nome_inesperado(tmp_path):
    root = tmp_path / "runs"
    incomplete = _run(root, 1, age_hours=100, summary=False)
    protected = _run(root, 2, age_hours=100)
    strange = root / "nome-inesperado"
    strange.mkdir()
    (strange / retention.SUMMARY_NAME).write_text("{}", encoding="utf-8")
    loose = root / "solto.txt"
    loose.write_text("preservar", encoding="utf-8")
    result = _retain(root, max_count=0, max_age_hours=1, protected_execution_ids={protected.name})
    assert incomplete.exists() and protected.exists() and strange.exists() and loose.exists()
    assert result["skipped_incomplete"] == 1
    assert result["skipped_unsafe"] == 1
    assert result["removed"] == 0


def test_artefato_desconhecido_preserva_diretorio_concluido(tmp_path):
    root = tmp_path / "runs"
    directory = _run(root, 1, age_hours=30)
    (directory / "desconhecido.txt").write_text("preservar", encoding="utf-8")
    result = _retain(root, max_count=0, max_age_hours=24)
    assert directory.exists()
    assert result["skipped_unsafe"] == 1
    assert result["removed"] == 0


def test_ordenacao_deterministica_em_empate_de_mtime(tmp_path):
    root = tmp_path / "runs"
    first = _run(root, 1, age_hours=1)
    second = _run(root, 2, age_hours=1)
    third = _run(root, 3, age_hours=1)
    result = _retain(root, max_count=1, max_age_hours=0)
    assert result["removed"] == 2
    assert first.exists() and not second.exists() and not third.exists()


def test_falha_ao_remover_nao_impede_outra_execucao(tmp_path, monkeypatch):
    root = tmp_path / "runs"
    first = _run(root, 1, age_hours=30)
    second = _run(root, 2, age_hours=29)
    original = retention.shutil.rmtree

    def remove(directory):
        if directory == first:
            raise PermissionError("detalhe sensível do filesystem")
        return original(directory)

    monkeypatch.setattr(retention.shutil, "rmtree", remove)
    result = _retain(root, max_count=0, max_age_hours=24)
    assert first.exists() and not second.exists()
    assert result["removed"] == 1
    assert len(result["errors"]) == 1
    assert "detalhe sensível" not in str(result)
    assert str(root) not in str(result)


def test_symlink_externo_e_aninhado_nao_sao_seguidos(tmp_path):
    root = tmp_path / "runs"
    root.mkdir()
    external = tmp_path / "externo"
    external.mkdir()
    sentinel = external / "sentinela.txt"
    sentinel.write_text("preservar", encoding="utf-8")
    link = root / str(UUID(int=1))
    try:
        link.symlink_to(external, target_is_directory=True)
        nested = _run(root, 2, age_hours=30)
        (nested / "atalho").symlink_to(external, target_is_directory=True)
    except (OSError, NotImplementedError) as exc:
        pytest.skip(f"Symlink indisponível neste ambiente: {type(exc).__name__}")
    result = _retain(root, max_count=0, max_age_hours=24)
    assert sentinel.exists() and link.exists() and nested.exists()
    assert result["removed"] == 0
    assert result["skipped_unsafe"] >= 2


def test_configuracao_defaults_desativacao_e_zero(monkeypatch):
    for name in (
        "SINALYX_LIVE_RUN_RETENTION_ENABLED", "SINALYX_LIVE_RUN_RETENTION_MAX_COUNT",
        "SINALYX_LIVE_RUN_RETENTION_MAX_AGE_HOURS",
    ):
        monkeypatch.delenv(name, raising=False)
    get_settings.cache_clear()
    try:
        settings = get_settings()
        assert (settings.live_run_retention_enabled, settings.live_run_retention_max_count,
                settings.live_run_retention_max_age_hours) == (True, 2000, 24)
        monkeypatch.setenv("SINALYX_LIVE_RUN_RETENTION_ENABLED", "false")
        monkeypatch.setenv("SINALYX_LIVE_RUN_RETENTION_MAX_COUNT", "0")
        monkeypatch.setenv("SINALYX_LIVE_RUN_RETENTION_MAX_AGE_HOURS", "-1")
        get_settings.cache_clear()
        settings = get_settings()
        assert not settings.live_run_retention_enabled
        assert settings.live_run_retention_max_count == 0
        assert settings.live_run_retention_max_age_hours == 0
        monkeypatch.setenv("SINALYX_LIVE_RUN_RETENTION_MAX_COUNT", "7")
        monkeypatch.setenv("SINALYX_LIVE_RUN_RETENTION_MAX_AGE_HOURS", "12")
        get_settings.cache_clear()
        settings = get_settings()
        assert (settings.live_run_retention_max_count, settings.live_run_retention_max_age_hours) == (7, 12)
    finally:
        get_settings.cache_clear()


def test_falha_de_retencao_nao_interrompe_live_ou_acessa_postgresql(tmp_path, monkeypatch):
    from src.services import live_execution_lock, pfsense_incremental_service as live
    from src.db import repository

    @contextmanager
    def lock():
        yield True

    monkeypatch.setattr(live_execution_lock, "live_execution_lock", lock)
    monkeypatch.setattr(live, "LIVE_RUNTIME_DIR", tmp_path)
    monkeypatch.setattr(live, "LIVE_RUNS_DIR", tmp_path / "runs")
    log = tmp_path / "filter.log"
    log.write_bytes(b"")
    monkeypatch.setattr(live.PfSenseCollectorConfig, "from_env", lambda: SimpleNamespace(local_path=log, remote_path="sintetico"))
    monkeypatch.setattr(live, "_parser_state_path", lambda local_log_path=None: tmp_path / "parser_state.json")
    monkeypatch.setattr(live, "retain_live_runs", lambda *args, **kwargs: (_ for _ in ()).throw(OSError("falha simulada")))
    monkeypatch.setattr(repository, "save_live_windows", lambda *args, **kwargs: pytest.fail("retenção não deve tocar no banco"))
    response = live.process_live_pfsense(collect=False, persist=False)
    assert response["status"] == "success"
    assert live._load_parser_state(log)["offset"] == 0
