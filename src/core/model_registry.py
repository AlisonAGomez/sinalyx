"""Cadastro de perfis local de perfis de modelo e alternativa segura do Sinalyx.

O cadastro de perfis e uma camada de controle operacional. Ele não promove modelos e não
copia arquivos de apoio; apenas resolve qual pasta deve ser tentada em ambiente de execução quando
as variaveis de ambiente pedem um perfil específico.
"""

from __future__ import annotations

import json
import os
import sys
from dataclasses import dataclass
from pathlib import Path
from typing import Any

from src.core.paths import MODELS_DIR


MODEL_REGISTRY_FILE = MODELS_DIR / "model_registry.json"
RUNTIME_REQUIRED_FILES = (
    "scaler.joblib",
    "isolation.pkl",
    "autoencoder/model.keras",
    "threshold.pkl",
    "manifest.json",
)
RUNTIME_OPTIONAL_FILES = ("ensemble.json",)


@dataclass(frozen=True)
class ModelProfileResolution:
    """Resultado do resolvedor de perfil de modelo."""

    profile_name: str
    profile_path: Path
    source: str
    warnings: tuple[str, ...]


def _read_json(path: Path) -> dict[str, Any]:
    """Lê um objeto JSON; arquivo ausente ou conteúdo de outro tipo resulta em objeto vazio."""
    if not path.exists():
        return {}
    with path.open("r", encoding="utf-8") as file:
        payload = json.load(file)
    return payload if isinstance(payload, dict) else {}


def load_model_registry(path: Path = MODEL_REGISTRY_FILE) -> dict[str, Any]:
    """Carrega o cadastro de perfis de perfis; ausente significa modo legado seguro."""
    return _read_json(path)


def profile_path(profile_name: str, registry: dict[str, Any] | None = None) -> Path:
    """Resolve a pasta de arquivos de apoio de um perfil sem validar existencia."""
    registry = registry or load_model_registry()
    profiles = registry.get("profiles", {}) if isinstance(registry, dict) else {}
    profile = profiles.get(profile_name, {}) if isinstance(profiles, dict) else {}
    artifact_path = profile.get("artifact_path")
    if artifact_path:
        caminho = Path(str(artifact_path)).expanduser()
        if caminho.is_absolute():
            return caminho
        # O cadastro atual usa o prefixo antigo data/models para localizar a pasta oficial de modelos.
        prefixo_legado = Path("data") / "models"
        try:
            relativo_ao_store = caminho.relative_to(prefixo_legado)
        except ValueError:
            relativo_ao_store = caminho
        return (MODELS_DIR / relativo_ao_store).resolve()
    if profile_name == "current":
        return MODELS_DIR
    return MODELS_DIR / profile_name


def profile_runtime_artifacts(path: Path) -> dict[str, Path]:
    """Monta os caminhos esperados para análise em uma pasta de perfil."""
    return {
        "scaler": path / "scaler.joblib",
        "isolation": path / "isolation.pkl",
        "autoencoder_model": path / "autoencoder" / "model.keras",
        "threshold": path / "threshold.pkl",
        "legacy_threshold": path / "autoencoder" / "threshold.pkl",
        "manifest": path / "manifest.json",
        "ensemble": path / "ensemble.json",
    }


def profile_has_runtime_artifacts(path: Path) -> bool:
    """Confirma se uma pasta tem o mínimo para carregar análise."""
    artifacts = profile_runtime_artifacts(path)
    return (
        artifacts["scaler"].exists()
        and artifacts["isolation"].exists()
        and artifacts["autoencoder_model"].exists()
        and (artifacts["threshold"].exists() or artifacts["legacy_threshold"].exists())
        and artifacts["manifest"].exists()
    )


def validate_model_registry(registry: dict[str, Any] | None = None) -> dict[str, Any]:
    """Valida estrutura, referencias e uso operacional dos perfis."""
    registry = registry if registry is not None else load_model_registry()
    errors: list[str] = []
    warnings: list[str] = []
    profiles = registry.get("profiles", {}) if isinstance(registry, dict) else {}
    if not isinstance(profiles, dict) or not profiles:
        errors.append("Registry sem bloco profiles.")
        profiles = {}

    active = str(registry.get("active_profile", "") or "")
    fallback = str(registry.get("fallback_profile", "") or "")
    candidate = str(registry.get("candidate_profile", "") or "")
    for field_name, profile_name in (
        ("active_profile", active),
        ("fallback_profile", fallback),
    ):
        if not profile_name:
            errors.append(f"{field_name} nao preenchido.")
        elif profile_name not in profiles:
            errors.append(f"{field_name} aponta para perfil inexistente: {profile_name}.")
    if candidate and candidate not in profiles:
        warnings.append(f"candidate_profile aponta para perfil inexistente: {candidate}.")

    profile_results: dict[str, Any] = {}
    for name, profile in profiles.items():
        if not isinstance(profile, dict):
            errors.append(f"Perfil {name} deve ser objeto JSON.")
            continue
        for required in ("display_name", "description", "status"):
            if not str(profile.get(required, "") or "").strip():
                errors.append(f"Perfil {name} sem campo obrigatorio {required}.")
        path = profile_path(str(name), registry)
        production_usable = bool(profile.get("production_usable", False))
        runtime_ready = profile_has_runtime_artifacts(path)
        if production_usable and not runtime_ready:
            errors.append(
                f"Perfil {name} marcado como production_usable, mas sem artefatos completos."
            )
        if profile.get("artifact_path") and not path.exists():
            warnings.append(f"Perfil {name} aponta para caminho ausente: {path}.")
        profile_results[str(name)] = {
            "artifact_path": str(path),
            "path_exists": path.exists(),
            "runtime_ready": runtime_ready,
            "production_usable": production_usable,
            "diagnostic_only": bool(profile.get("diagnostic_only", False)),
        }

    return {
        "valid": not errors,
        "errors": errors,
        "warnings": warnings,
        "active_profile": active,
        "candidate_profile": candidate,
        "fallback_profile": fallback,
        "profiles": profile_results,
    }


def resolve_model_profile(
    requested_profile: str | None = None,
    fallback_profile: str | None = None,
    registry: dict[str, Any] | None = None,
) -> ModelProfileResolution:
    """Resolve qual perfil sera usado para carregar modelos em ambiente de execução."""
    registry = registry if registry is not None else load_model_registry()
    active = str(registry.get("active_profile", "current") or "current")
    fallback = (
        fallback_profile
        or os.getenv("SINALYX_MODEL_FALLBACK_PROFILE", "").strip()
        or str(registry.get("fallback_profile", "current") or "current")
    )
    requested = (
        requested_profile
        or os.getenv("SINALYX_MODEL_PROFILE", "").strip()
        or active
    )

    warnings: list[str] = []
    candidates: list[tuple[str, str]] = [
        (requested, "requested"),
        (fallback, "fallback"),
        ("current", "legacy_default"),
    ]
    seen: set[str] = set()
    for profile_name, source in candidates:
        if not profile_name or profile_name in seen:
            continue
        seen.add(profile_name)
        path = profile_path(profile_name, registry)
        if profile_has_runtime_artifacts(path):
            return ModelProfileResolution(
                profile_name=profile_name,
                profile_path=path,
                source=source,
                warnings=tuple(warnings),
            )
        warnings.append(
            f"Perfil {profile_name} nao possui artefatos completos em {path}."
        )

    return ModelProfileResolution(
        profile_name="current",
        profile_path=MODELS_DIR,
        source="legacy_default_missing_validation",
        warnings=tuple(warnings),
    )


def apply_runtime_profile_paths(profile_path_value: Path) -> dict[str, str]:
    """Atualiza constantes já importadas para a pasta de perfil resolvida."""
    path = Path(profile_path_value)
    artifacts = profile_runtime_artifacts(path)
    updates: dict[str, dict[str, Path]] = {
        "src.core.paths": {
            "SCALER_FILE": artifacts["scaler"],
            "ISOLATION_MODEL_FILE": artifacts["isolation"],
            "AUTOENCODER_MODEL_FILE": artifacts["autoencoder_model"],
            "AUTOENCODER_THRESHOLD_FILE": artifacts["threshold"],
            "LEGACY_AUTOENCODER_THRESHOLD_FILE": artifacts["legacy_threshold"],
            "ENSEMBLE_CONFIG_FILE": artifacts["ensemble"],
            "AUTOENCODER_DIR": path / "autoencoder",
        },
        "src.core.artifacts": {
            "MANIFEST_FILE": artifacts["manifest"],
            "SCALER_FILE": artifacts["scaler"],
            "ISOLATION_MODEL_FILE": artifacts["isolation"],
            "AUTOENCODER_MODEL_FILE": artifacts["autoencoder_model"],
            "AUTOENCODER_THRESHOLD_FILE": artifacts["threshold"],
            "LEGACY_AUTOENCODER_THRESHOLD_FILE": artifacts["legacy_threshold"],
            "ENSEMBLE_CONFIG_FILE": artifacts["ensemble"],
            "AUTOENCODER_DIR": path / "autoencoder",
        },
        "src.models.isolation_forest": {
            "SCALER_FILE": artifacts["scaler"],
            "ISOLATION_MODEL_FILE": artifacts["isolation"],
        },
        "src.models.autoencoder": {
            "SCALER_FILE": artifacts["scaler"],
            "AUTOENCODER_MODEL_FILE": artifacts["autoencoder_model"],
            "AUTOENCODER_THRESHOLD_FILE": artifacts["threshold"],
            "AUTOENCODER_DIR": path / "autoencoder",
        },
        "src.models.ensemble": {
            "ENSEMBLE_CONFIG_FILE": artifacts["ensemble"],
        },
        "src.pipelines.infer_pfsense_batch": {
            "MANIFEST_FILE": artifacts["manifest"],
            "ENSEMBLE_CONFIG_FILE": artifacts["ensemble"],
            "ISOLATION_MODEL_FILE": artifacts["isolation"],
        },
    }
    applied: dict[str, str] = {}
    for module_name, module_updates in updates.items():
        module = sys.modules.get(module_name)
        if module is None:
            continue
        for attribute, value in module_updates.items():
            setattr(module, attribute, value)
            applied[f"{module_name}.{attribute}"] = str(value)
    return applied
