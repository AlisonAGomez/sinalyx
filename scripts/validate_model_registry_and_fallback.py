"""Valida o cadastro de perfis de modelos e a alternativa segura do Sinalyx.

Este script não carrega TensorFlow, Autoencoder nem Isolation Forest. Ele
confere apenas dados complementares, caminhos e a decisão de alternativa para evitar que um
perfil experimental incompleto quebre a análise em ambiente de execução.
"""

from __future__ import annotations

import json
import sys
from pathlib import Path

PROJECT_ROOT = Path(__file__).resolve().parents[1]
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))

from src.core.model_registry import (  # noqa: E402
    load_model_registry,
    resolve_model_profile,
    validate_model_registry,
)


def main() -> int:
    registry = load_model_registry()
    validation = validate_model_registry(registry)
    checks: list[dict[str, object]] = []

    if not validation["valid"]:
        print(json.dumps(validation, indent=2, ensure_ascii=False))
        return 1

    fallback_name = str(registry.get("fallback_profile", "current") or "current")
    missing_resolution = resolve_model_profile(
        requested_profile="perfil_inexistente_para_teste",
        fallback_profile=fallback_name,
        registry=registry,
    )
    checks.append(
        {
            "case": "perfil inexistente usa fallback",
            "expected": fallback_name,
            "actual": missing_resolution.profile_name,
            "source": missing_resolution.source,
            "ok": missing_resolution.profile_name == fallback_name
            and missing_resolution.source == "fallback",
        }
    )

    candidate_name = str(registry.get("candidate_profile", "") or "")
    if candidate_name:
        candidate_resolution = resolve_model_profile(
            requested_profile=candidate_name,
            fallback_profile=fallback_name,
            registry=registry,
        )
        candidate_profile = registry.get("profiles", {}).get(candidate_name, {})
        candidate_runtime = bool(candidate_profile.get("production_usable", False))
        expected = candidate_name if candidate_runtime else fallback_name
        checks.append(
            {
                "case": "perfil candidato respeita artefatos de runtime",
                "candidate": candidate_name,
                "expected": expected,
                "actual": candidate_resolution.profile_name,
                "source": candidate_resolution.source,
                "warnings": list(candidate_resolution.warnings),
                "ok": candidate_resolution.profile_name == expected,
            }
        )

    output = {
        "valid_registry": True,
        "registry_summary": validation,
        "fallback_checks": checks,
    }
    print(json.dumps(output, indent=2, ensure_ascii=False))
    return 0 if all(bool(item["ok"]) for item in checks) else 1


if __name__ == "__main__":
    raise SystemExit(main())
