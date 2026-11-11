"""Projeção aditiva de saídas existentes, sem análise ou recálculo.

Ausências são null (signals: {}). ai_support é somente metadado auxiliar.
Somente os campos explícitos são expostos, sem caminhos internos adicionais.
"""
import json
from datetime import datetime
from pathlib import Path
from typing import Any

import pandas as pd


def _to_builtin(value: Any) -> Any:
    """
    Converte valores pandas/numpy/timestamp para JSON/SQLAlchemy.
    """
    if hasattr(value, "item"):
        value = value.item()
    if isinstance(value, pd.Timestamp):
        return value.isoformat()
    if isinstance(value, datetime):
        return value.isoformat()
    if isinstance(value, Path):
        return str(value)
    if isinstance(value, dict):
        return {str(key): _to_builtin(item) for key, item in value.items()}
    if isinstance(value, (list, tuple)):
        return [_to_builtin(item) for item in value]
    if isinstance(value, float) and (pd.isna(value) or value in {float("inf"), float("-inf")}):
        return None
    if pd.isna(value) if not isinstance(value, (dict, list, tuple, str, bytes)) else False:
        return None
    return value


def _json_object_or_empty(value: Any) -> dict[str, Any]:
    """Converte JSON textual em dicionário quando possível."""
    if isinstance(value, dict):
        return value
    if value is None:
        return {}
    if isinstance(value, str) and value.strip():
        try:
            payload = json.loads(value)
        except json.JSONDecodeError:
            return {}
        return payload if isinstance(payload, dict) else {}
    return {}


def montar_model_outputs(record: dict[str, Any]) -> dict[str, Any]:
    """Extrai pontuações e saídas relevantes dos modelos para gravação."""
    return {
        "isolation_forest": {
            "pred": _to_builtin(record.get("pred_if")),
            "label": _to_builtin(record.get("label_if")),
            "raw_score": _to_builtin(record.get("score_if")),
            "normalized_score": _to_builtin(record.get("score_if_normalized")),
            "confidence": _to_builtin(record.get("if_confidence")),
        },
        "autoencoder": {
            "pred": _to_builtin(record.get("pred_ae")),
            "label": _to_builtin(record.get("label_ae")),
            "raw_score": _to_builtin(record.get("score_ae")),
            "log_score": _to_builtin(record.get("score_ae_log")),
            "normalized_score": _to_builtin(record.get("score_ae_normalized")),
            "confidence": _to_builtin(record.get("ae_confidence")),
            "threshold_raw": _to_builtin(record.get("ae_threshold_raw")),
            "threshold_log": _to_builtin(record.get("ae_threshold_log")),
        },
        "heuristic": {
            "pred": _to_builtin(record.get("pred_heuristic")),
            "attack_type": _to_builtin(record.get("heuristic_attack_type")),
            "confidence": _to_builtin(record.get("heuristic_confidence")),
            "reason": _to_builtin(record.get("heuristic_reason")),
        },
        "ensemble": {
            "pred": _to_builtin(record.get("pred_ensemble")),
            "score": _to_builtin(record.get("score_ensemble")),
            "threshold": _to_builtin(record.get("ensemble_threshold")),
            "runtime_profile": _to_builtin(record.get("runtime_profile")),
            "if_weight": _to_builtin(record.get("ensemble_if_weight")),
            "ae_weight": _to_builtin(record.get("ensemble_ae_weight")),
            "if_pred": _to_builtin(record.get("ensemble_if_pred")),
            "ae_pred": _to_builtin(record.get("ensemble_ae_pred")),
            "if_alert_score": _to_builtin(record.get("ensemble_if_alert_score")),
            "agreement_score": _to_builtin(record.get("ensemble_agreement_score")),
            "conflict_penalty": _to_builtin(record.get("ensemble_conflict_penalty")),
            "ae_risk_score": _to_builtin(record.get("ensemble_ae_risk_score")),
            "ae_risk_band": _to_builtin(record.get("ensemble_ae_risk_band")),
        },
        "ai_support": {
            "enabled": _to_builtin(record.get("ai_support")),
            "conservative": _to_builtin(record.get("ai_support_conservative")),
            "type": _to_builtin(record.get("ai_support_type")),
            "level": _to_builtin(record.get("ai_support_level")),
            "reason": _to_builtin(record.get("ai_support_reason")),
            "signals": _json_object_or_empty(record.get("ai_support_signals")),
        },
        "decision_engine": {
            "pred": _to_builtin(record.get("pred_decision_engine")),
            "is_anomaly": _to_builtin(record.get("is_anomaly")),
            "final_label": _to_builtin(record.get("final_label")),
            "attack_type": _to_builtin(record.get("attack_type")),
            "risk_level": _to_builtin(record.get("risk_level")),
            "confidence": _to_builtin(record.get("confidence")),
            "decision_source": _to_builtin(record.get("decision_source")),
            "decision_reason": _to_builtin(record.get("decision_reason")),
            "explanation": _to_builtin(record.get("explanation")),
            "agreement_level": _to_builtin(record.get("agreement_level")),
            "conflict_winner": _to_builtin(record.get("conflict_winner")),
            "base_attack_support": _to_builtin(record.get("base_attack_support")),
            "base_negative_support": _to_builtin(record.get("base_negative_support")),
        },
    }
