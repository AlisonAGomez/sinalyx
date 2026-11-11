"""Camada experimental de análise com memória do Sinalyx.

Está camada não substitui parser, características, modelos, ensemble ou motor de
decisão. Ela observa historico recente por IP de origem durante reprocessamento causal e
devolve sinais auxiliares para experimentos offline.
"""

from __future__ import annotations

from collections import Counter, deque
from dataclasses import dataclass, field
from datetime import datetime
from math import exp
from typing import Any, Deque


NOISE_PORTS = {1900, 3702, 5353, 5355, 547}
SENSITIVE_SERVICE_PORTS = {21, 22, 23, 445, 3389, 5900}
NOISE_PROTOCOLS = {"icmpv6"}


@dataclass(frozen=True)
class MemoryContextConfig:
    """Configuração de seguranca para o historico recente."""

    retention_seconds: int = 600
    max_tracked_sources: int = 10000
    min_history_windows: int = 2
    min_history_seconds: int = 120
    moderate_score_threshold: float = 0.04
    detailed_port_trigger: int = 4
    detailed_connection_trigger: int = 12
    vertical_port_threshold: int = 10
    horizontal_destination_threshold: int = 8
    brute_force_sensitive_hits: int = 4
    syn_flood_syn_threshold: int = 30


@dataclass
class MemoryEvent:
    """Resumo leve de uma janela agregada."""

    timestamp: datetime
    source_ip: str
    destination_ips: set[str]
    destination_ports: set[int]
    protocol: str
    action: str
    connections: float
    bytes_per_connection: float
    packet_size: float
    packets: float
    tcp_syn_count: float
    ensemble_score: float
    base_prediction: int
    base_attack_type: str
    is_noise: bool
    has_sensitive_port: bool
    detailed: bool


@dataclass
class SourceMemoryState:
    """Estado recente de uma origem."""

    source_ip: str
    events: Deque[MemoryEvent] = field(default_factory=deque)
    first_seen: datetime | None = None
    last_seen: datetime | None = None
    detailed_tracking: bool = False

    def append(self, event: MemoryEvent) -> None:
        """Acrescenta o evento ao histórico e atualiza as datas do primeiro e do último registro."""
        if self.first_seen is None:
            self.first_seen = event.timestamp
        self.last_seen = event.timestamp
        self.detailed_tracking = self.detailed_tracking or event.detailed
        self.events.append(event)


def _float_value(value: Any, default: float = 0.0) -> float:
    """Lê um número decimal e usa o padrão para valores vazios ou inválidos."""
    try:
        if value in (None, ""):
            return default
        return float(value)
    except (TypeError, ValueError):
        return default


def _int_value(value: Any, default: int = 0) -> int:
    """Lê o valor numérico como inteiro usando o padrão em caso de ausência."""
    return int(_float_value(value, float(default)))


def _parse_timestamp(value: Any) -> datetime | None:
    """Interpreta a data e hora textual para comparar eventos na mesma base temporal."""
    text = str(value or "").strip()
    if not text:
        return None
    normalized = text.replace("Z", "+00:00")
    for candidate in (normalized, normalized.replace(" ", "T")):
        try:
            return datetime.fromisoformat(candidate).replace(tzinfo=None)
        except ValueError:
            pass
    return None


def _parse_ports(*values: Any) -> set[int]:
    """Reúne as portas presentes nos campos de texto, sem repetições."""
    ports: set[int] = set()
    for value in values:
        text = str(value or "").strip()
        if not text:
            continue
        for token in text.replace(";", ",").replace("|", ",").split(","):
            token = token.strip()
            if not token:
                continue
            try:
                port = int(float(token))
            except ValueError:
                continue
            if 0 < port <= 65535:
                ports.add(port)
    return ports


def _parse_ip_sample(value: Any) -> set[str]:
    """Separa os endereços presentes na amostra de texto, sem repetições."""
    text = str(value or "").strip()
    if not text:
        return set()
    return {
        token.strip()
        for token in text.replace(";", ",").replace("|", ",").split(",")
        if token.strip()
    }


def _row_value(row: dict[str, Any], *names: str) -> Any:
    """Retorna o primeiro campo preenchido entre os nomes equivalentes de um registro."""
    for name in names:
        if name in row and row[name] not in (None, ""):
            return row[name]
    return None


def _temporal_weight(age_seconds: float) -> float:
    """Dá mais importância aos eventos recentes conforme as faixas de idade configuradas."""
    if age_seconds <= 60:
        return 1.0
    if age_seconds <= 180:
        return 0.65
    if age_seconds <= 300:
        return 0.35
    return max(0.10, exp(-age_seconds / 600.0))


class MemoryContextAnalyzer:
    """Analisa historico recente por origem com limites de memória."""

    def __init__(self, config: MemoryContextConfig | None = None) -> None:
        """Prepara a configuração e o histórico temporal da comparação experimental."""
        self.config = config or MemoryContextConfig()
        self.states: dict[str, SourceMemoryState] = {}
        self.stats: Counter[str] = Counter()
        self.peak_tracked_sources = 0
        self.state_samples: list[int] = []

    def _prune_by_time(self, now: datetime) -> None:
        """Descarta eventos mais antigos que o período de histórico mantido em memória."""
        retention = max(1, int(self.config.retention_seconds))
        empty_sources: list[str] = []
        for source_ip, state in self.states.items():
            while state.events:
                age = (now - state.events[0].timestamp).total_seconds()
                if age <= retention:
                    break
                state.events.popleft()
                self.stats["removed_by_time"] += 1
            if not state.events:
                empty_sources.append(source_ip)
        for source_ip in empty_sources:
            self.states.pop(source_ip, None)

    def _prune_by_hardcap(self) -> None:
        """Limita o histórico em memória mesmo quando muitos eventos chegam no mesmo período."""
        limit = max(1, int(self.config.max_tracked_sources))
        if len(self.states) <= limit:
            return
        ordered = sorted(
            self.states.items(),
            key=lambda item: item[1].last_seen or datetime.min,
        )
        for source_ip, state in ordered[: len(self.states) - limit]:
            self.stats["removed_by_hardcap"] += len(state.events)
            self.states.pop(source_ip, None)

    def _build_event(
        self,
        row: dict[str, Any],
        *,
        base_prediction: int,
        base_attack_type: str,
        ensemble_score: float,
    ) -> MemoryEvent | None:
        """Monta o evento temporal usando os campos disponíveis da janela analisada."""
        timestamp = _parse_timestamp(
            _row_value(row, "window_start", "time_window", "timestamp", "window_end")
        )
        source_ip = str(_row_value(row, "source_ip", "src_ip", "origem") or "").strip()
        if timestamp is None or not source_ip:
            self.stats["missing_temporal_or_source_key"] += 1
            return None

        ports = _parse_ports(
            _row_value(row, "common_destination_ports", "safe_port_text"),
            _row_value(row, "destination_port_min"),
            _row_value(row, "destination_port_max"),
        )
        destination_ips = _parse_ip_sample(_row_value(row, "destination_ip_sample"))
        destination_ip_count = _int_value(_row_value(row, "destination_ip_count"))
        if destination_ip_count and not destination_ips:
            destination_ips = {f"destino_{index}" for index in range(destination_ip_count)}

        protocol = str(_row_value(row, "protocol") or "").strip().lower()
        action = str(_row_value(row, "action") or "").strip().lower()
        connections = _float_value(_row_value(row, "connections"))
        bytes_per_connection = _float_value(_row_value(row, "bytes_per_connection"))
        packet_size = _float_value(_row_value(row, "packet_size"))
        packets = _float_value(_row_value(row, "packets"))
        tcp_syn_count = _float_value(_row_value(row, "tcp_syn_count"))
        has_sensitive_port = any(port in SENSITIVE_SERVICE_PORTS for port in ports)
        only_noise_ports = bool(ports) and ports.issubset(NOISE_PORTS)
        is_noise = (
            protocol in NOISE_PROTOCOLS
            or only_noise_ports
            or (protocol == "udp" and bool(ports & NOISE_PORTS))
        )
        detailed = (
            float(ensemble_score) >= float(self.config.moderate_score_threshold)
            or len(ports) >= int(self.config.detailed_port_trigger)
            or connections >= float(self.config.detailed_connection_trigger)
            or has_sensitive_port
            or int(base_prediction) == 1
        )
        return MemoryEvent(
            timestamp=timestamp,
            source_ip=source_ip,
            destination_ips=destination_ips,
            destination_ports=ports,
            protocol=protocol,
            action=action,
            connections=connections,
            bytes_per_connection=bytes_per_connection,
            packet_size=packet_size,
            packets=packets,
            tcp_syn_count=tcp_syn_count,
            ensemble_score=float(ensemble_score),
            base_prediction=1 if int(base_prediction) == 1 else 0,
            base_attack_type=str(base_attack_type or "unknown_anomaly"),
            is_noise=is_noise,
            has_sensitive_port=has_sensitive_port,
            detailed=detailed,
        )

    def _summarize_source(self, state: SourceMemoryState, now: datetime) -> dict[str, Any]:
        """Resume contagens e padrões dos eventos guardados para uma origem."""
        weighted_connections = 0.0
        weighted_syn = 0.0
        weighted_sensitive_hits = 0.0
        moderate_windows = 0
        noise_windows = 0
        destinations: set[str] = set()
        ports: set[int] = set()
        protocols: Counter[str] = Counter()
        actions: Counter[str] = Counter()
        small_connection_windows = 0

        for event in state.events:
            age = max(0.0, (now - event.timestamp).total_seconds())
            weight = _temporal_weight(age)
            destinations.update(event.destination_ips)
            ports.update(event.destination_ports)
            protocols[event.protocol or "unknown"] += 1
            actions[event.action or "unknown"] += 1
            weighted_connections += event.connections * weight
            weighted_syn += event.tcp_syn_count * weight
            if event.has_sensitive_port:
                weighted_sensitive_hits += max(1.0, event.connections) * weight
            if event.ensemble_score >= float(self.config.moderate_score_threshold):
                moderate_windows += 1
            if event.is_noise:
                noise_windows += 1
            if (
                event.bytes_per_connection <= 2500
                or event.packet_size <= 250
                or event.packets <= 5
            ):
                small_connection_windows += 1

        total_windows = max(1, len(state.events))
        return {
            "window_count": len(state.events),
            "distinct_destinations": len(destinations),
            "distinct_ports": len(ports),
            "weighted_connections": weighted_connections,
            "weighted_syn": weighted_syn,
            "weighted_sensitive_hits": weighted_sensitive_hits,
            "moderate_windows": moderate_windows,
            "noise_ratio": noise_windows / total_windows,
            "small_connection_ratio": small_connection_windows / total_windows,
            "dominant_protocol": protocols.most_common(1)[0][0] if protocols else "",
            "dominant_action": actions.most_common(1)[0][0] if actions else "",
            "ports": sorted(ports),
        }

    def analyze(
        self,
        row: dict[str, Any],
        *,
        base_prediction: int,
        base_attack_type: str = "unknown_anomaly",
        ensemble_score: float = 0.0,
    ) -> dict[str, Any]:
        """Processa uma janela em ordem causal e retorna contexto auxiliar."""
        event = self._build_event(
            row,
            base_prediction=base_prediction,
            base_attack_type=base_attack_type,
            ensemble_score=ensemble_score,
        )
        if event is None:
            return {
                "enabled": False,
                "reason": "Sem timestamp ou IP de origem confiavel.",
                "should_promote": False,
                "should_suppress": False,
                "support_score": 0.0,
                "signals": {},
            }

        self._prune_by_time(event.timestamp)
        state = self.states.setdefault(event.source_ip, SourceMemoryState(event.source_ip))
        previous_count = len(state.events)
        previous_first_seen = state.first_seen
        state.append(event)
        self._prune_by_hardcap()

        self.peak_tracked_sources = max(self.peak_tracked_sources, len(self.states))
        self.state_samples.append(len(self.states))
        self.stats["processed_windows"] += 1
        if event.detailed:
            self.stats["detailed_windows"] += 1

        history_seconds = 0.0
        if previous_first_seen is not None:
            history_seconds = max(0.0, (event.timestamp - previous_first_seen).total_seconds())
        history_ready = (
            previous_count >= int(self.config.min_history_windows)
            or history_seconds >= float(self.config.min_history_seconds)
        )
        if not history_ready:
            self.stats["cold_start_windows"] += 1

        summary = self._summarize_source(state, event.timestamp)
        noise_ratio = float(summary["noise_ratio"])
        distinct_ports = int(summary["distinct_ports"])
        distinct_destinations = int(summary["distinct_destinations"])
        weighted_connections = float(summary["weighted_connections"])
        weighted_syn = float(summary["weighted_syn"])
        weighted_sensitive_hits = float(summary["weighted_sensitive_hits"])
        small_connection_ratio = float(summary["small_connection_ratio"])
        moderate_windows = int(summary["moderate_windows"])

        vertical_scan = (
            history_ready
            and distinct_ports >= int(self.config.vertical_port_threshold)
            and distinct_destinations <= 4
            and weighted_connections >= 12
            and small_connection_ratio >= 0.45
            and noise_ratio < 0.75
        )
        horizontal_scan = (
            history_ready
            and distinct_destinations >= int(self.config.horizontal_destination_threshold)
            and distinct_ports <= 6
            and weighted_connections >= 12
            and noise_ratio < 0.75
        )
        persistent_moderate_scan = (
            history_ready
            and moderate_windows >= 3
            and distinct_ports >= 5
            and weighted_connections >= 10
            and noise_ratio < 0.70
        )
        brute_force = (
            history_ready
            and weighted_sensitive_hits >= float(self.config.brute_force_sensitive_hits)
            and distinct_ports <= 3
            and weighted_connections >= 6
            and noise_ratio < 0.75
        )
        syn_flood = (
            history_ready
            and weighted_syn >= float(self.config.syn_flood_syn_threshold)
            and weighted_connections >= 20
            and noise_ratio < 0.75
        )

        suggested_attack_type = "unknown_anomaly"
        support_score = 0.0
        if syn_flood:
            suggested_attack_type = "syn_flood"
            support_score = 0.90
        elif brute_force:
            suggested_attack_type = "brute_force"
            support_score = 0.82
        elif vertical_scan or horizontal_scan or persistent_moderate_scan:
            suggested_attack_type = "port_scan"
            support_score = 0.78 if (vertical_scan or horizontal_scan) else 0.62

        offensive_signal = support_score > 0.0
        should_promote = int(base_prediction) == 0 and offensive_signal
        should_suppress = (
            int(base_prediction) == 1
            and history_ready
            and not offensive_signal
            and noise_ratio >= 0.85
            and distinct_ports <= 3
            and weighted_sensitive_hits == 0
        )

        if should_promote:
            self.stats["promoted_windows"] += 1
        if should_suppress:
            self.stats["suppressed_windows"] += 1

        return {
            "enabled": True,
            "source_ip": event.source_ip,
            "history_ready": history_ready,
            "cold_start": not history_ready,
            "reason": (
                "Historico recente sustentou comportamento ofensivo."
                if offensive_signal
                else "Historico recente sem sinal ofensivo forte."
            ),
            "suggested_attack_type": suggested_attack_type,
            "support_score": support_score,
            "should_promote": should_promote,
            "should_suppress": should_suppress,
            "signals": {
                "vertical_port_scan": vertical_scan,
                "horizontal_port_scan": horizontal_scan,
                "persistent_moderate_scan": persistent_moderate_scan,
                "brute_force_pattern": brute_force,
                "syn_flood_pattern": syn_flood,
                "noise_ratio": noise_ratio,
                "distinct_ports": distinct_ports,
                "distinct_destinations": distinct_destinations,
                "weighted_connections": weighted_connections,
                "weighted_syn": weighted_syn,
                "weighted_sensitive_hits": weighted_sensitive_hits,
                "moderate_windows": moderate_windows,
                "dominant_protocol": summary["dominant_protocol"],
                "dominant_action": summary["dominant_action"],
            },
        }

    def get_stats(self) -> dict[str, Any]:
        """Retorna metricas de uso de memória do experimento."""
        avg_states = (
            sum(self.state_samples) / len(self.state_samples)
            if self.state_samples
            else 0.0
        )
        active_events = sum(len(state.events) for state in self.states.values())
        return {
            "active_sources": len(self.states),
            "active_events": active_events,
            "peak_tracked_sources": self.peak_tracked_sources,
            "average_tracked_sources": avg_states,
            "removed_by_time": int(self.stats["removed_by_time"]),
            "removed_by_hardcap": int(self.stats["removed_by_hardcap"]),
            "processed_windows": int(self.stats["processed_windows"]),
            "detailed_windows": int(self.stats["detailed_windows"]),
            "cold_start_windows": int(self.stats["cold_start_windows"]),
            "promoted_windows": int(self.stats["promoted_windows"]),
            "suppressed_windows": int(self.stats["suppressed_windows"]),
            "missing_temporal_or_source_key": int(
                self.stats["missing_temporal_or_source_key"]
            ),
        }
