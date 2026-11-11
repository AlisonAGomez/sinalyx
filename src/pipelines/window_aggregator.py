"""Agregação oficial de janelas para análise quase em tempo real do Sinalyx.

Regras centrais deste módulo:
- grupo de registros temporal fixo de 5 segundos por padrão
- chave de agregação principal = (src_ip, bucket_start)
- cada janela fechada gera 1 linha com dados complementares + 13 características do projeto

O módulo foi desenhado para ser reutilizado tanto pelo parse lote atual
quanto pelo processador de fluxo tail-like.
"""

from __future__ import annotations

import json
import os
from collections import Counter
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any

import pandas as pd

from src.features.constants import FEATURE_COLUMNS
from src.features.engineering import select_active_feature_frame
from src.features.security_window_context import build_security_window_context
from src.models.memory_context_v2 import (
    CausalFlowTemporalContext,
    FLOW_TEMPORAL_CONTEXT_COLUMNS,
)


DEFAULT_WINDOW_SECONDS = 5
DEFAULT_WINDOW_FREQUENCY = f"{DEFAULT_WINDOW_SECONDS}s"
WINDOW_METADATA_COLUMNS = [
    "window_id",
    "window_start",
    "window_end",
    "time_window",
    "src_ip",
    "source_ip",
    "event_count",
    "protocol",
    "action",
    "interface",
    "destination_ip_count",
    "destination_ip_sample",
    "destination_port_min",
    "destination_port_max",
    "destination_port_count",
    "common_destination_ports",
    "tcp_syn_count",
    "tcp_pa_count",
    "tcp_flags_summary",
    "blocked_count",
    "passed_count",
]
WINDOW_OUTPUT_COLUMNS = [*WINDOW_METADATA_COLUMNS, *FEATURE_COLUMNS]
SECURITY_CONTEXT_ENV_FLAG = "SINALYX_ENABLE_SECURITY_WINDOW_CONTEXT"
EXPERIMENTAL_TEMPORAL_CONTEXT_ENV_FLAG = (
    "SINALYX_ENABLE_EXPERIMENTAL_TEMPORAL_CONTEXT"
)
SECURITY_CONTEXT_COLUMNS = [
    "ctx_destination_ips_top",
    "ctx_destination_ports_top",
    "ctx_source_destination_pairs_top",
    "ctx_source_destination_port_pairs_top",
    "ctx_destination_ip_list_limited",
    "ctx_destination_port_list_limited",
    "ctx_destination_ip_count",
    "ctx_destination_port_count",
    "ctx_source_destination_pair_count",
    "ctx_source_destination_port_pair_count",
    "ctx_tcp_syn_count",
    "ctx_tcp_ack_count",
    "ctx_tcp_rst_count",
    "ctx_tcp_fin_count",
    "ctx_tcp_pa_count",
    "ctx_tcp_syn_ratio",
    "ctx_protocol_counts",
    "ctx_action_counts",
    "ctx_interface_counts",
    "ctx_sensitive_services_seen",
    "ctx_noise_services_seen",
    "ctx_service_categories",
    "ctx_horizontal_scan_hint",
    "ctx_vertical_scan_hint",
    "ctx_slow_scan_hint",
    "ctx_brute_force_hint",
    "ctx_syn_flood_hint",
    "ctx_operational_noise_hint",
    "ctx_context_limitations",
    "ctx_security_window_context_version",
]


def _security_context_enabled_from_env() -> bool:
    """
    Resolve a flag experimental de contexto auxiliar.
    """
    value = str(os.getenv(SECURITY_CONTEXT_ENV_FLAG, "")).strip().lower()
    return value in {"1", "true", "yes", "sim", "on", "enabled"}


def _experimental_temporal_context_enabled_from_env() -> bool:
    """Resolve a flag explicitamente experimental do contexto fino por fluxo."""
    value = str(os.getenv(EXPERIMENTAL_TEMPORAL_CONTEXT_ENV_FLAG, "")).strip().lower()
    return value in {"1", "true", "yes", "sim", "on", "enabled"}


def _resolve_window_seconds(window: str | int | float | None) -> int:
    """Resolve a duração da janela em segundos inteiros."""
    if window is None:
        return DEFAULT_WINDOW_SECONDS

    if isinstance(window, (int, float)):
        seconds = float(window)
    else:
        seconds = float(pd.to_timedelta(str(window)).total_seconds())

    if seconds <= 0:
        raise ValueError("A janela precisa ser positiva.")

    rounded_seconds = int(round(seconds))
    if abs(seconds - rounded_seconds) > 1e-9:
        raise ValueError(
            "A janela precisa ser expressa em segundos inteiros para o agregador atual."
        )
    return rounded_seconds


def _normalize_text(value: Any, default: str) -> str:
    """Padroniza textos livres com alternativa segura."""
    if value is None:
        return default

    text = str(value).strip()
    return text if text else default


def _normalize_flag(value: Any) -> str:
    """
    Padroniza flags TCP em caixa alta.
    """
    if value is None:
        return ""
    return str(value).strip().upper()


def _safe_float(value: Any, default: float = 0.0) -> float:
    """
    Converte qualquer valor para float resiliente.
    """
    try:
        return float(value)
    except (TypeError, ValueError):
        return float(default)


def _safe_timestamp(value: Any) -> pd.Timestamp | None:
    """Converte datas e horas para pandas.Timestamp quando possível."""
    timestamp = pd.to_datetime(value, errors="coerce")
    if pd.isna(timestamp):
        return None
    return timestamp


def _safe_port(value: Any) -> int | None:
    """
    Normaliza uma porta quando ela estiver em faixa valida.
    """
    try:
        candidate = int(float(value))
    except (TypeError, ValueError):
        return None

    if 0 <= candidate <= 65535:
        return candidate
    return None


def _top_counter_key(counter: Counter[str], default: str) -> str:
    """
    Retorna a chave mais comum de um Counter textual.
    """
    if not counter:
        return default
    return str(counter.most_common(1)[0][0])


def _summarize_int_counter(counter: Counter[int], *, limit: int = 10) -> str:
    """
    Resume um Counter de portas em formato estavel para CSV/JSON.
    """
    if not counter:
        return ""
    return ",".join(str(value) for value, _ in counter.most_common(limit))


def _summarize_text_counter(counter: Counter[str], *, limit: int = 5) -> str:
    """
    Resume um Counter textual em formato chave:contagem.
    """
    if not counter:
        return ""
    return ",".join(
        f"{key}:{int(count)}"
        for key, count in counter.most_common(limit)
    )


def _json_for_csv(value: Any) -> str:
    """
    Serializa valores compostos de contexto em uma celula CSV estavel.
    """
    if value in (None, ""):
        return ""
    if isinstance(value, (list, dict, tuple)):
        return json.dumps(value, ensure_ascii=False, sort_keys=True, default=str)
    return str(value)


def _bool_for_csv(value: Any) -> bool:
    """
    Normaliza booleanos de contexto para CSV.
    """
    return bool(value)


def _security_context_to_columns(context: dict[str, Any]) -> dict[str, Any]:
    """Converte o contexto auxiliar para colunas `ctx_*` sem tocar nas características."""
    return {
        "ctx_destination_ips_top": _json_for_csv(context.get("top_destination_ips")),
        "ctx_destination_ports_top": _json_for_csv(context.get("top_destination_ports")),
        "ctx_source_destination_pairs_top": _json_for_csv(
            context.get("top_source_destination_pairs")
        ),
        "ctx_source_destination_port_pairs_top": _json_for_csv(
            context.get("top_source_destination_port_pairs")
        ),
        "ctx_destination_ip_list_limited": _json_for_csv(
            context.get("destination_ip_list_limited")
        ),
        "ctx_destination_port_list_limited": _json_for_csv(
            context.get("destination_port_list_limited")
        ),
        "ctx_destination_ip_count": int(context.get("destination_ip_count") or 0),
        "ctx_destination_port_count": int(context.get("destination_port_count") or 0),
        "ctx_source_destination_pair_count": int(
            context.get("source_destination_pair_count") or 0
        ),
        "ctx_source_destination_port_pair_count": int(
            context.get("source_destination_port_pair_count") or 0
        ),
        "ctx_tcp_syn_count": int(context.get("tcp_syn_count") or 0),
        "ctx_tcp_ack_count": context.get("tcp_ack_count"),
        "ctx_tcp_rst_count": context.get("tcp_rst_count"),
        "ctx_tcp_fin_count": context.get("tcp_fin_count"),
        "ctx_tcp_pa_count": int(context.get("tcp_pa_count") or 0),
        "ctx_tcp_syn_ratio": context.get("tcp_syn_ratio"),
        "ctx_protocol_counts": _json_for_csv(context.get("protocol_counts")),
        "ctx_action_counts": _json_for_csv(context.get("action_counts")),
        "ctx_interface_counts": _json_for_csv(context.get("interface_counts")),
        "ctx_sensitive_services_seen": _json_for_csv(
            context.get("sensitive_services_seen")
        ),
        "ctx_noise_services_seen": _json_for_csv(context.get("noise_services_seen")),
        "ctx_service_categories": _json_for_csv(context.get("service_categories")),
        "ctx_horizontal_scan_hint": _bool_for_csv(context.get("horizontal_scan_hint")),
        "ctx_vertical_scan_hint": _bool_for_csv(context.get("vertical_scan_hint")),
        "ctx_slow_scan_hint": _bool_for_csv(context.get("slow_scan_hint")),
        "ctx_brute_force_hint": _bool_for_csv(context.get("brute_force_hint")),
        "ctx_syn_flood_hint": _bool_for_csv(context.get("syn_flood_hint")),
        "ctx_operational_noise_hint": _bool_for_csv(
            context.get("operational_noise_hint")
        ),
        "ctx_context_limitations": _json_for_csv(context.get("context_limitations")),
        "ctx_security_window_context_version": str(
            context.get("security_window_context_version") or ""
        ),
    }


def _record_is_eligible(record: dict[str, Any]) -> bool:
    """Decide se o evento pode entrar na agregação."""
    if "parse_status" in record and str(record.get("parse_status") or "") != "full":
        return False
    if "parse_status" not in record and "parsed_successfully" in record:
        if not bool(record.get("parsed_successfully", False)):
            return False
    if "log_type" in record and str(record.get("log_type") or "") != "firewall":
        return False
    return True


def normalize_event_record(record: Any) -> dict[str, Any] | None:
    """Normaliza um evento interpretado em um registro pronto para agregação."""
    if hasattr(record, "to_dict"):
        raw = record.to_dict()
    elif isinstance(record, dict):
        raw = dict(record)
    else:
        raw = dict(record)

    if not _record_is_eligible(raw):
        return None

    timestamp = _safe_timestamp(raw.get("timestamp"))
    if timestamp is None:
        return None

    return {
        "timestamp": timestamp,
        "source_ip": _normalize_text(raw.get("source_ip"), "unknown_source"),
        "protocol": _normalize_text(raw.get("protocol"), "unknown_protocol").lower(),
        "action": _normalize_text(raw.get("action"), "unknown_action").lower(),
        "interface": _normalize_text(raw.get("interface"), "unknown_interface"),
        "destination_ip": _normalize_text(
            raw.get("destination_ip"),
            "unknown_destination",
        ),
        "destination_port": _safe_port(raw.get("destination_port")),
        "tcp_flags": _normalize_flag(raw.get("tcp_flags")),
        "bytes": max(_safe_float(raw.get("bytes"), 0.0), 0.0),
        "packets": max(_safe_float(raw.get("packets"), 1.0), 0.0),
    }


def prepare_events_dataframe(events_df: pd.DataFrame) -> pd.DataFrame:
    """Filtra e normaliza um Tabela de dados de eventos para a camada de janelas."""
    if events_df.empty:
        return pd.DataFrame(
            columns=[
                "timestamp",
                "source_ip",
                "protocol",
                "action",
                "interface",
                "destination_ip",
                "destination_port",
                "tcp_flags",
                "bytes",
                "packets",
            ]
        )

    normalized_records: list[dict[str, Any]] = []
    for record in events_df.to_dict(orient="records"):
        normalized = normalize_event_record(record)
        if normalized is not None:
            normalized_records.append(normalized)

    if not normalized_records:
        return pd.DataFrame(
            columns=[
                "timestamp",
                "source_ip",
                "protocol",
                "action",
                "interface",
                "destination_ip",
                "destination_port",
                "tcp_flags",
                "bytes",
                "packets",
            ]
        )

    prepared_df = pd.DataFrame(normalized_records)
    prepared_df = prepared_df.sort_values(
        by=["timestamp", "source_ip", "destination_ip"],
        kind="stable",
    ).reset_index(drop=True)
    return prepared_df


@dataclass
class WindowAggregateState:
    """
    Estado acumulado de uma janela fixa por `src_ip`.
    """

    source_ip: str
    window_start: pd.Timestamp
    window_seconds: int
    event_count: int = 0
    total_bytes: float = 0.0
    total_packets: float = 0.0
    protocol_counts: Counter[str] = field(default_factory=Counter)
    action_counts: Counter[str] = field(default_factory=Counter)
    interface_counts: Counter[str] = field(default_factory=Counter)
    destination_ip_counts: Counter[str] = field(default_factory=Counter)
    destination_port_counts: Counter[int] = field(default_factory=Counter)
    tcp_flag_counts: Counter[str] = field(default_factory=Counter)
    source_destination_pair_counts: Counter[str] = field(default_factory=Counter)
    source_destination_port_pair_counts: Counter[str] = field(default_factory=Counter)
    blocked_count: int = 0
    passed_count: int = 0
    context_events: list[dict[str, Any]] = field(default_factory=list)

    @property
    def window_end(self) -> pd.Timestamp:
        """
        Limite superior exclusivo da janela.
        """
        return self.window_start + pd.Timedelta(seconds=self.window_seconds)

    def add_record(self, record: dict[str, Any]) -> None:
        """
        Incorpora um evento normalizado ao acumulador atual.
        """
        self.event_count += 1
        self.total_bytes += max(_safe_float(record.get("bytes"), 0.0), 0.0)
        self.total_packets += max(_safe_float(record.get("packets"), 0.0), 0.0)

        protocol = _normalize_text(record.get("protocol"), "unknown_protocol").lower()
        action = _normalize_text(record.get("action"), "unknown_action").lower()
        interface = _normalize_text(record.get("interface"), "unknown_interface")
        destination_ip = _normalize_text(
            record.get("destination_ip"),
            "unknown_destination",
        )
        tcp_flag = _normalize_flag(record.get("tcp_flags"))
        destination_port = _safe_port(record.get("destination_port"))

        self.protocol_counts[protocol] += 1
        self.action_counts[action] += 1
        self.interface_counts[interface] += 1
        self.destination_ip_counts[destination_ip] += 1
        if destination_port is not None:
            self.destination_port_counts[destination_port] += 1
            self.source_destination_port_pair_counts[
                f"{self.source_ip}->{destination_ip}:{destination_port}"
            ] += 1
        if tcp_flag:
            self.tcp_flag_counts[tcp_flag] += 1
        self.source_destination_pair_counts[f"{self.source_ip}->{destination_ip}"] += 1

        if action == "block":
            self.blocked_count += 1
        elif action == "pass":
            self.passed_count += 1

        self.context_events.append(
            {
                **record,
                "source_ip": self.source_ip,
                "destination_ip": destination_ip,
                "destination_port": destination_port,
                "tcp_flags": tcp_flag,
            }
        )

    def to_output_record(self, *, include_security_context: bool = False) -> dict[str, Any]:
        """Converte o estado acumulado em 1 linha pronta para análise."""
        destination_ports = sorted(self.destination_port_counts.keys())
        destination_port_count = len(destination_ports)
        packet_size = (
            self.total_bytes / self.total_packets
            if self.total_packets > 0
            else 0.0
        )

        base_feature_row = {
            "connections": float(self.event_count),
            "bytes": float(self.total_bytes),
            "packets": float(self.total_packets),
            "packet_size": float(packet_size),
            "ports": float(destination_port_count),
        }
        feature_frame = select_active_feature_frame(pd.DataFrame([base_feature_row]))
        feature_values = feature_frame.iloc[0].to_dict()

        protocol = _top_counter_key(self.protocol_counts, "unknown_protocol")
        action = _top_counter_key(self.action_counts, "unknown_action")
        interface = _top_counter_key(self.interface_counts, "unknown_interface")
        destination_ip_sample = _top_counter_key(
            self.destination_ip_counts,
            "unknown_destination",
        )
        window_id = f"{self.source_ip}|{self.window_start.isoformat()}|{self.window_seconds}s"

        output = {
            "window_id": window_id,
            "window_start": self.window_start,
            "window_end": self.window_end,
            "time_window": self.window_start,
            "src_ip": self.source_ip,
            "source_ip": self.source_ip,
            "event_count": int(self.event_count),
            "protocol": protocol,
            "action": action,
            "interface": interface,
            "destination_ip_count": int(len(self.destination_ip_counts)),
            "destination_ip_sample": destination_ip_sample,
            "destination_port_min": (
                int(destination_ports[0]) if destination_ports else None
            ),
            "destination_port_max": (
                int(destination_ports[-1]) if destination_ports else None
            ),
            "destination_port_count": int(destination_port_count),
            "common_destination_ports": _summarize_int_counter(
                self.destination_port_counts,
                limit=10,
            ),
            "tcp_syn_count": int(
                self.tcp_flag_counts.get("S", 0) + self.tcp_flag_counts.get("SYN", 0)
            ),
            "tcp_pa_count": int(self.tcp_flag_counts.get("PA", 0)),
            "tcp_flags_summary": _summarize_text_counter(self.tcp_flag_counts, limit=5),
            "blocked_count": int(self.blocked_count),
            "passed_count": int(self.passed_count),
        }
        output.update(feature_values)
        if include_security_context:
            context = build_security_window_context(
                self.context_events,
                window_metadata={
                    **output,
                    "protocol_counts": dict(self.protocol_counts),
                    "action_counts": dict(self.action_counts),
                    "interface_counts": dict(self.interface_counts),
                    "top_source_destination_pairs": [
                        {"value": value, "count": int(count)}
                        for value, count in self.source_destination_pair_counts.most_common(20)
                    ],
                    "top_source_destination_port_pairs": [
                        {"value": value, "count": int(count)}
                        for value, count in self.source_destination_port_pair_counts.most_common(30)
                    ],
                },
            )
            context["protocol_counts"] = dict(self.protocol_counts)
            context["action_counts"] = dict(self.action_counts)
            context["interface_counts"] = dict(self.interface_counts)
            output.update(_security_context_to_columns(context))
        return output


class PfSenseWindowAggregator:
    """
    Agregador incremental de janelas fixas por `src_ip`.
    """

    def __init__(
        self,
        window_seconds: int = DEFAULT_WINDOW_SECONDS,
        *,
        enable_security_context: bool | None = None,
        enable_experimental_temporal_context: bool | None = None,
    ) -> None:
        """Define a duração das janelas e prepara os acumuladores e contextos opcionais."""
        self.window_seconds = _resolve_window_seconds(window_seconds)
        self.window_frequency = f"{self.window_seconds}s"
        if enable_security_context is None:
            enable_security_context = _security_context_enabled_from_env()
        self.enable_security_context = bool(enable_security_context)
        if enable_experimental_temporal_context is None:
            enable_experimental_temporal_context = (
                _experimental_temporal_context_enabled_from_env()
            )
        self.enable_experimental_temporal_context = bool(
            enable_experimental_temporal_context
        )
        self._flow_temporal_context = (
            CausalFlowTemporalContext()
            if self.enable_experimental_temporal_context
            else None
        )
        self._states: dict[tuple[str, pd.Timestamp], WindowAggregateState] = {}

    def _render_state(self, state: WindowAggregateState) -> dict[str, Any]:
        """Fecha uma janela e anexa contexto fino apenas quando a flag foi ativada."""
        output = state.to_output_record(
            include_security_context=self.enable_security_context,
        )
        if self._flow_temporal_context is not None:
            output.update(
                self._flow_temporal_context.summarize_window(
                    source_ip=state.source_ip,
                    window_end=state.window_end,
                    window_events=state.context_events,
                )
            )
        return output

    def _bucket_start(self, timestamp: pd.Timestamp) -> pd.Timestamp:
        """Resolve o inicio do grupo de registros fixo para o data e hora informado."""
        return timestamp.floor(self.window_frequency)

    def _close_ready_states(
        self,
        *,
        reference_window_start: pd.Timestamp,
    ) -> list[dict[str, Any]]:
        """Fecha janelas cujo limite superior já ficou para tras."""
        ready_keys = [
            key
            for key, state in self._states.items()
            if state.window_end <= reference_window_start
        ]
        ready_keys = sorted(ready_keys, key=lambda item: (item[1], item[0]))

        closed_records: list[dict[str, Any]] = []
        for key in ready_keys:
            state = self._states.pop(key)
            closed_records.append(self._render_state(state))
        return closed_records

    def add_event(self, event: Any) -> list[dict[str, Any]]:
        """
        Recebe um evento bruto/parseado e devolve janelas fechadas, se houver.
        """
        normalized = normalize_event_record(event)
        if normalized is None:
            return []

        return self.add_prepared_record(normalized)

    def add_prepared_record(self, record: dict[str, Any]) -> list[dict[str, Any]]:
        """Recebe um registro já normalizado e atualiza a janela correspondente."""
        timestamp = _safe_timestamp(record.get("timestamp"))
        if timestamp is None:
            return []

        bucket_start = self._bucket_start(timestamp)
        source_ip = _normalize_text(record.get("source_ip"), "unknown_source")
        key = (source_ip, bucket_start)
        closed_records = self._close_ready_states(
            reference_window_start=bucket_start
        )

        state = self._states.get(key)
        if state is None:
            state = WindowAggregateState(
                source_ip=source_ip,
                window_start=bucket_start,
                window_seconds=self.window_seconds,
            )
            self._states[key] = state

        state.add_record(record)
        if self._flow_temporal_context is not None:
            self._flow_temporal_context.observe(record)
        return closed_records

    def flush_all(self) -> list[dict[str, Any]]:
        """Fecha e devolve todas as janelas restantes em ordem determinística."""
        pending_keys = sorted(self._states.keys(), key=lambda item: (item[1], item[0]))
        flushed_records: list[dict[str, Any]] = []
        for key in pending_keys:
            state = self._states.pop(key)
            flushed_records.append(self._render_state(state))
        return flushed_records

    def build_dataframe(self, records: list[dict[str, Any]]) -> pd.DataFrame:
        """Converte linhas agregadas em Tabela de dados com colunas ordenadas."""
        return build_window_dataframe(records)


def build_window_dataframe(records: list[dict[str, Any]]) -> pd.DataFrame:
    """Converte registros agregados em Tabela de dados padronizado."""
    if not records:
        return pd.DataFrame(columns=WINDOW_OUTPUT_COLUMNS)

    output = pd.DataFrame(records)
    output_columns = [*WINDOW_OUTPUT_COLUMNS]
    if any(column in output.columns for column in SECURITY_CONTEXT_COLUMNS):
        output_columns.extend(SECURITY_CONTEXT_COLUMNS)
    if any(column in output.columns for column in FLOW_TEMPORAL_CONTEXT_COLUMNS):
        output_columns.extend(FLOW_TEMPORAL_CONTEXT_COLUMNS)
    for column in output_columns:
        if column not in output.columns:
            output[column] = pd.NA if column not in FEATURE_COLUMNS else 0.0
    return output[output_columns].copy()


def build_windowed_feature_frame(
    events_df: pd.DataFrame,
    *,
    window: str | int | float | None = DEFAULT_WINDOW_FREQUENCY,
    enable_security_context: bool | None = None,
    enable_experimental_temporal_context: bool | None = None,
) -> pd.DataFrame:
    """Executa a agregação oficial por janela fixa sobre um Tabela de dados de eventos."""
    prepared_df = prepare_events_dataframe(events_df)
    if prepared_df.empty:
        return pd.DataFrame(columns=WINDOW_OUTPUT_COLUMNS)

    aggregator = PfSenseWindowAggregator(
        _resolve_window_seconds(window),
        enable_security_context=enable_security_context,
        enable_experimental_temporal_context=enable_experimental_temporal_context,
    )
    closed_records: list[dict[str, Any]] = []

    for record in prepared_df.to_dict(orient="records"):
        closed_records.extend(aggregator.add_prepared_record(record))

    closed_records.extend(aggregator.flush_all())
    return build_window_dataframe(closed_records)


def ensure_parent_dir(path: str | Path) -> None:
    """Garante que o diretório pai exista antes de salvar saídas."""
    Path(path).expanduser().resolve().parent.mkdir(parents=True, exist_ok=True)
