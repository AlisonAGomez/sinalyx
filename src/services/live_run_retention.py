"""Retenção segura dos arquivos de apoio locais auxiliares de execuções live."""

from __future__ import annotations

import os
import shutil
import stat
from datetime import datetime
from pathlib import Path
from uuid import UUID


SUMMARY_NAME = "sinalyx_live_summary.json"
KNOWN_ARTIFACTS = {
    "parsed_events.csv",
    "sinalyx_live_features.csv",
    "sinalyx_live_inference_results.csv",
    "sinalyx_live_inference_report.json",
    SUMMARY_NAME,
}


def _is_reparse_point(path: Path) -> bool:
    """Rejeita links simbólicos e junctions antes de uma remoção recursiva."""
    metadata = path.lstat()
    return stat.S_ISLNK(metadata.st_mode) or bool(
        getattr(metadata, "st_file_attributes", 0)
        & getattr(stat, "FILE_ATTRIBUTE_REPARSE_POINT", 0)
    )


def _has_unrecognized_artifacts(directory: Path) -> bool:
    """Preserva pastas com arquivos desconhecidos, links ou itens que não sejam arquivos comuns."""
    with os.scandir(directory) as entries:
        for entry in entries:
            if (
                entry.name not in KNOWN_ARTIFACTS
                or _is_reparse_point(Path(entry.path))
                or not entry.is_file(follow_symlinks=False)
            ):
                return True
    return False


def _is_execution_name(name: str) -> bool:
    """Aceita somente nomes de execução no formato UUID esperado."""
    try:
        return str(UUID(name)) == name.lower()
    except ValueError:
        return False


def retain_live_runs(
    runs_dir: Path,
    *,
    enabled: bool = True,
    max_count: int = 2000,
    max_age_hours: int = 24,
    protected_execution_ids: set[str] | None = None,
    reference_time: datetime | None = None,
) -> dict[str, object]:
    """Remove somente execuções concluídas; idade usa o mtime do summary.

    Idade igual ao limite já é elegível. Valores não positivos desativam o critério.
    """
    result: dict[str, object] = {
        "enabled": enabled,
        "scanned": 0,
        "eligible": 0,
        "removed": 0,
        "removed_by_age": 0,
        "removed_by_count": 0,
        "skipped_incomplete": 0,
        "skipped_unsafe": 0,
        "errors": [],
    }
    if not enabled or (max_count <= 0 and max_age_hours <= 0) or not runs_dir.exists():
        return result
    if _is_reparse_point(runs_dir) or not runs_dir.is_dir():
        result["errors"].append("Diretório de execuções inválido.")
        return result

    root = runs_dir.resolve(strict=True)
    protected = protected_execution_ids or set()
    now = reference_time.timestamp() if reference_time is not None else datetime.now().timestamp()
    completed: list[tuple[float, Path]] = []
    for candidate in runs_dir.iterdir():
        result["scanned"] += 1
        try:
            if _is_reparse_point(candidate):
                result["skipped_unsafe"] += 1
                continue
            if not candidate.is_dir():
                continue
            if not _is_execution_name(candidate.name):
                result["skipped_unsafe"] += 1
                continue
            if candidate.parent.resolve(strict=True) != root or candidate.resolve(strict=True).parent != root:
                result["skipped_unsafe"] += 1
                continue
            summary = candidate / SUMMARY_NAME
            if not summary.exists() or _is_reparse_point(summary) or not summary.is_file():
                result["skipped_incomplete"] += 1
                continue
            if _has_unrecognized_artifacts(candidate):
                result["skipped_unsafe"] += 1
                continue
            completed.append((summary.stat().st_mtime, candidate))
        except OSError:
            result["errors"].append("Falha ao inspecionar uma execução local.")

    completed.sort(key=lambda item: (-item[0], item[1].name))
    for rank, (modified, candidate) in enumerate(completed):
        if candidate.name in protected:
            continue
        by_age = max_age_hours > 0 and now - modified >= max_age_hours * 3600
        by_count = max_count > 0 and rank >= max_count
        if not (by_age or by_count):
            continue
        result["eligible"] += 1
        try:
            # Revalidar imediatamente antes da remoção, sem atravessar links locais.
            if candidate.parent.resolve(strict=True) != root or _is_reparse_point(candidate) or _has_unrecognized_artifacts(candidate):
                result["skipped_unsafe"] += 1
                continue
            shutil.rmtree(candidate)
            result["removed"] += 1
            if by_age:
                result["removed_by_age"] += 1
            if by_count:
                result["removed_by_count"] += 1
        except OSError:
            result["errors"].append("Falha ao remover uma execução local.")
    return result
