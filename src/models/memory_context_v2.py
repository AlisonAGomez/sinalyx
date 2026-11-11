"""Análise com memória aprimorada para validação offline do Sinalyx.

Está versao e experimental, lateral e desligavel. Ela não retreina modelos,
não altera as 13 características oficiais e não substitui o ensemble ou o Motor de
decisão atuais. O objetivo e produzir sinais causais por tipo de ameaca para
avaliação offline.
"""

from __future__ import annotations

from bisect import bisect_left, insort
from collections import Counter, deque
from dataclasses import dataclass, field
from datetime import datetime, timedelta
from math import exp, isfinite
from statistics import fmean, pstdev
from typing import Any, Deque


NOISE_PORTS = {1900, 3702, 5353, 5355, 547}
NOISE_PROTOCOLS = {"icmpv6"}
SENSITIVE_SERVICE_PORTS = {21, 22, 23, 445, 3389, 5900}
FLOW_TEMPORAL_HORIZONS = (30, 60, 120, 300, 600)
FLOW_TEMPORAL_CONTEXT_VERSION = "experimental_flow_temporal_context_v1"
FLOW_TEMPORAL_CONTEXT_COLUMNS = [
    "ctx_flow_context_available",
    "ctx_flow_context_version",
    "ctx_flow_selected_port",
    *[f"ctx_flow_count_{horizon}s" for horizon in FLOW_TEMPORAL_HORIZONS],
    "ctx_flow_span_300s",
    "ctx_flow_span_600s",
    "ctx_flow_interval_mean_300s",
    "ctx_flow_interval_mean_600s",
    "ctx_flow_interval_cv_300s",
    "ctx_flow_interval_cv_600s",
    "ctx_flow_active_windows_300s",
    "ctx_flow_active_windows_600s",
    "ctx_flow_consecutive_active_windows",
    "ctx_flow_share_src_300s",
    "ctx_flow_share_src_600s",
]

STATUS_LABELS = {
    "normal": "Normal",
    "operational_noise": "Ruido operacional",
    "suspicious_low": "Suspeito baixo",
    "suspicious_medium": "Suspeito medio",
    "attack_probable": "Ataque provavel",
    "attack_confirmed": "Ataque confirmado",
}

THREAT_LABELS = {
    "normal": "Normal",
    "operational_noise": "Ruido operacional",
    "port_scan": "Varredura de Portas",
    "brute_force_suspected": "Tentativa provavel de forca bruta",
    "syn_flood": "DDoS / SYN Flood",
    "unknown_anomaly": "Anomalia nao classificada",
}


@dataclass(frozen=True)
class MemoryContextV2Config:
    """Parâmetros do experimento de memória v2."""

    retention_seconds: int = 600
    max_tracked_sources: int = 10000
    min_history_windows: int = 2
    min_history_seconds: int = 120
    final_attack_threshold: float = 0.82
    suppression_noise_threshold: float = 0.88
    suppression_max_threat_score: float = 0.48
    portscan_vertical_ports: int = 7
    portscan_horizontal_destinations: int = 7
    portscan_rolling_ports: int = 10
    portscan_min_windows: int = 2
    bruteforce_sensitive_hits: float = 6.0
    synflood_syn_threshold: float = 30.0
    model_signal_weight: float = 0.20
    current_ensemble_weight: float = 0.25
    portscan_memory_weight: float = 0.55
    bruteforce_memory_weight: float = 0.55
    experimental_temporal_bruteforce_enabled: bool = False
    temporal_bruteforce_count_600_min: int = 3
    temporal_bruteforce_span_600_min: float = 60.0
    temporal_bruteforce_interval_mean_600_min: float = 10.0
    temporal_bruteforce_interval_cv_600_max: float = 0.50
    temporal_bruteforce_consecutive_windows_min: int = 2
    temporal_bruteforce_direct_score: float = 0.90
    synflood_model_signal_weight: float = 0.15
    synflood_current_ensemble_weight: float = 0.20
    synflood_memory_weight: float = 0.65


@dataclass
class MemoryV2Event:
    """Resumo causal de uma janela."""

    timestamp: datetime
    source_ip: str
    destination_samples: set[str]
    destination_ip_count: int
    destination_ports: set[int]
    destination_port_count: int
    protocol: str
    action: str
    connections: float
    bytes_per_connection: float
    packets_per_connection: float
    packets: float
    tcp_syn_count: float
    blocked_count: float
    passed_count: float
    ae_normalized: float
    if_normalized: float
    ensemble_score: float
    heuristic_attack_type: str
    heuristic_confidence: float
    rolling_distinct_ports: int
    rolling_connections: float
    is_noise: bool
    has_sensitive_port: bool
    temporal_context_available: bool
    ctx_flow_selected_port: int
    ctx_flow_count_600s: int
    ctx_flow_span_600s: float
    ctx_flow_interval_mean_600s: float
    ctx_flow_interval_cv_600s: float
    ctx_flow_consecutive_active_windows: int


def _datetime_value(value: Any) -> datetime | None:
    """Converte datas e horas de eventos finos sem depender do pandas."""
    if isinstance(value, datetime):
        return value.replace(tzinfo=None)
    if hasattr(value, "to_pydatetime"):
        converted = value.to_pydatetime()
        if isinstance(converted, datetime):
            return converted.replace(tzinfo=None)
    return _parse_timestamp(value)


def _bool_value(value: Any) -> bool:
    """Interpreta flags booleanas vindas de CSV sem tratar texto falso como verdadeiro."""
    if isinstance(value, bool):
        return value
    return str(value or "").strip().lower() in {"1", "true", "yes", "sim", "on"}


def _flow_key(record: dict[str, Any]) -> tuple[str, str, int, str] | None:
    """Extrai a chave causal de fluxo apenas para eventos TCP SYN utilizaveis."""
    protocol = str(record.get("protocol") or "").strip().lower()
    flags = str(record.get("tcp_flags") or "").strip().upper()
    source = str(record.get("source_ip") or record.get("src_ip") or "").strip()
    destination = str(record.get("destination_ip") or "").strip()
    port = _int_value(record.get("destination_port"))
    if (
        protocol != "tcp"
        or flags not in {"S", "SYN"}
        or not source
        or not destination
        or not 0 < port <= 65535
    ):
        return None
    return source, destination, port, protocol


class CausalFlowTemporalContext:
    """Acumula datas e horas finos de SYN para enriquecer janelas experimentais.

    Está e a camada de eventos finos do ``MemoryContextV2``, não uma nova
    decisão de memória. As consultas usam intervalo superior exclusivo, logo
    um resumo em ``t`` nunca observa eventos posteriores a ``t``. Os sinais
    ``ctx_flow_*`` são dados complementares e não integram as 13 características de
    AE/IF.
    """

    def __init__(self, *, retention_seconds: int = 600, max_tracked_flows: int = 10000) -> None:
        """Prepara os históricos por fluxo e os contadores do contexto experimental."""
        self.retention_seconds = max(600, int(retention_seconds))
        self.max_tracked_flows = max(1, int(max_tracked_flows))
        self._flow_events: dict[tuple[str, str, int, str], list[datetime]] = {}
        self._source_events: dict[str, list[tuple[datetime, tuple[str, str, int, str]]]] = {}
        self._last_seen: dict[tuple[str, str, int, str], datetime] = {}
        self._latest_timestamp: datetime | None = None

    @staticmethod
    def _empty_signals() -> dict[str, Any]:
        """Monta os sinais vazios usados quando ainda não há histórico suficiente."""
        output: dict[str, Any] = {
            "ctx_flow_context_available": False,
            "ctx_flow_context_version": FLOW_TEMPORAL_CONTEXT_VERSION,
            "ctx_flow_selected_port": None,
            "ctx_flow_span_300s": 0.0,
            "ctx_flow_span_600s": 0.0,
            "ctx_flow_interval_mean_300s": 0.0,
            "ctx_flow_interval_mean_600s": 0.0,
            "ctx_flow_interval_cv_300s": 0.0,
            "ctx_flow_interval_cv_600s": 0.0,
            "ctx_flow_active_windows_300s": 0,
            "ctx_flow_active_windows_600s": 0,
            "ctx_flow_consecutive_active_windows": 0,
            "ctx_flow_share_src_300s": 0.0,
            "ctx_flow_share_src_600s": 0.0,
        }
        for horizon in FLOW_TEMPORAL_HORIZONS:
            output[f"ctx_flow_count_{horizon}s"] = 0
        return output

    def _prune_touched(
        self,
        key: tuple[str, str, int, str],
        now: datetime,
    ) -> None:
        """Poda somente o fluxo/origem tocados; consultas ainda recortam por horizonte."""
        cutoff = now - timedelta(seconds=self.retention_seconds)
        timestamps = self._flow_events.get(key)
        if timestamps is not None:
            position = bisect_left(timestamps, cutoff)
            if position:
                del timestamps[:position]
            if not timestamps:
                self._flow_events.pop(key, None)
                self._last_seen.pop(key, None)

        source = key[0]
        entries = self._source_events.get(source)
        if entries is not None:
            position = bisect_left(entries, (cutoff, ("", "", 0, "")))
            if position:
                del entries[:position]
            if not entries:
                self._source_events.pop(source, None)

    def _enforce_hardcap(self) -> None:
        """Limita a quantidade de fluxos guardados e descarta os mais antigos quando necessário."""
        excess = len(self._flow_events) - self.max_tracked_flows
        if excess <= 0:
            return
        oldest = sorted(self._last_seen.items(), key=lambda item: item[1])[:excess]
        removed = {key for key, _ in oldest}
        for key in removed:
            self._flow_events.pop(key, None)
            self._last_seen.pop(key, None)
        for source, entries in list(self._source_events.items()):
            filtered = [entry for entry in entries if entry[1] not in removed]
            if filtered:
                self._source_events[source] = filtered
            else:
                self._source_events.pop(source, None)

    def observe(self, record: dict[str, Any]) -> bool:
        """Registra um SYN individual; eventos sem chave completa usam alternativa silencioso."""
        key = _flow_key(record)
        timestamp = _datetime_value(record.get("timestamp"))
        if key is None or timestamp is None:
            return False
        timestamps = self._flow_events.setdefault(key, [])
        insort(timestamps, timestamp)
        source_entries = self._source_events.setdefault(key[0], [])
        insort(source_entries, (timestamp, key))
        self._last_seen[key] = max(timestamp, self._last_seen.get(key, timestamp))
        self._latest_timestamp = max(timestamp, self._latest_timestamp or timestamp)
        self._prune_touched(key, self._latest_timestamp)
        self._enforce_hardcap()
        return True

    @staticmethod
    def _slice(timestamps: list[datetime], *, start: datetime, end: datetime) -> list[datetime]:
        """Seleciona os eventos do intervalo solicitado sem incluir eventos posteriores ao limite."""
        return timestamps[bisect_left(timestamps, start) : bisect_left(timestamps, end)]

    @staticmethod
    def _interval_metrics(timestamps: list[datetime]) -> tuple[float, float]:
        """Calcula medidas dos intervalos de tempo entre eventos."""
        intervals = [
            (current - previous).total_seconds()
            for previous, current in zip(timestamps, timestamps[1:])
        ]
        if not intervals:
            return 0.0, 0.0
        mean = float(fmean(intervals))
        cv = float(pstdev(intervals) / mean) if mean > 0 else 0.0
        return mean, cv

    @staticmethod
    def _active_window_metrics(timestamps: list[datetime]) -> tuple[int, int]:
        """Conta os segundos com atividade e a sequência de segundos consecutivos."""
        buckets = sorted({timestamp.replace(second=0, microsecond=0) for timestamp in timestamps})
        if not buckets:
            return 0, 0
        consecutive = 1
        for previous, current in zip(reversed(buckets[:-1]), reversed(buckets[1:])):
            if (current - previous).total_seconds() != 60:
                break
            consecutive += 1
        return len(buckets), consecutive

    def summarize_window(
        self,
        *,
        source_ip: str,
        window_end: datetime,
        window_events: list[dict[str, Any]],
    ) -> dict[str, Any]:
        """Seleciona o fluxo SYN mais relevante da janela e resume apenas seu passado causal."""
        end = _datetime_value(window_end)
        if end is None:
            return self._empty_signals()
        candidates = {
            key
            for record in window_events
            if (key := _flow_key(record)) is not None and key[0] == source_ip
        }
        if not candidates:
            return self._empty_signals()

        def candidate_rank(key: tuple[str, str, int, str]) -> tuple[int, int, float]:
            """Ordena os fluxos candidatos pela continuidade e pelo histórico disponível."""
            history = self._slice(
                self._flow_events.get(key, []),
                start=end.replace(microsecond=0) - timedelta(seconds=600),
                end=end,
            )
            span = (history[-1] - history[0]).total_seconds() if len(history) >= 2 else 0.0
            return int(key[2] in SENSITIVE_SERVICE_PORTS), len(history), span

        selected = max(candidates, key=candidate_rank)
        all_timestamps = self._flow_events.get(selected, [])
        output = self._empty_signals()
        output["ctx_flow_context_available"] = True
        output["ctx_flow_selected_port"] = selected[2]

        histories: dict[int, list[datetime]] = {}
        for horizon in FLOW_TEMPORAL_HORIZONS:
            history = self._slice(
                all_timestamps,
                start=end - timedelta(seconds=horizon),
                end=end,
            )
            histories[horizon] = history
            output[f"ctx_flow_count_{horizon}s"] = len(history)

        for horizon in (300, 600):
            history = histories[horizon]
            span = (history[-1] - history[0]).total_seconds() if len(history) >= 2 else 0.0
            mean, cv = self._interval_metrics(history)
            active_windows, consecutive = self._active_window_metrics(history)
            source_history = self._source_events.get(source_ip, [])
            source_count = len(
                source_history[
                    bisect_left(source_history, (end - timedelta(seconds=horizon), ("", "", 0, ""))) :
                    bisect_left(source_history, (end, ("", "", 0, "")))
                ]
            )
            output[f"ctx_flow_span_{horizon}s"] = float(span)
            output[f"ctx_flow_interval_mean_{horizon}s"] = float(mean)
            output[f"ctx_flow_interval_cv_{horizon}s"] = float(cv)
            output[f"ctx_flow_active_windows_{horizon}s"] = int(active_windows)
            output[f"ctx_flow_share_src_{horizon}s"] = (
                float(len(history) / source_count) if source_count else 0.0
            )
            if horizon == 600:
                output["ctx_flow_consecutive_active_windows"] = int(consecutive)
        return output


@dataclass
class StateBucket:
    """Grupo de registros de eventos recentes para uma chave de estado."""

    key: tuple[Any, ...]
    events: Deque[MemoryV2Event] = field(default_factory=deque)
    first_seen: datetime | None = None
    last_seen: datetime | None = None

    def append(self, event: MemoryV2Event) -> None:
        """Acrescenta o evento ao histórico e atualiza as datas do primeiro e do último registro."""
        if self.first_seen is None:
            self.first_seen = event.timestamp
        self.last_seen = event.timestamp
        self.events.append(event)


def _float_value(value: Any, default: float = 0.0) -> float:
    """Converte valores numéricos preservanda alternativa para ausentes/nao finitos."""
    try:
        if value in (None, ""):
            return default
        numeric_value = float(value)
        if not isfinite(numeric_value):
            return default
        return numeric_value
    except (TypeError, ValueError):
        return default


def _int_value(value: Any, default: int = 0) -> int:
    """Lê o valor numérico como inteiro usando o padrão em caso de ausência."""
    return int(_float_value(value, float(default)))


def _row_value(row: dict[str, Any], *names: str) -> Any:
    """Retorna o primeiro campo preenchido entre os nomes equivalentes de um registro."""
    for name in names:
        if name in row and row[name] not in (None, ""):
            return row[name]
    return None


def _parse_timestamp(value: Any) -> datetime | None:
    """Interpreta a data e hora textual para comparar eventos na mesma base temporal."""
    text = str(value or "").strip()
    if not text:
        return None
    for candidate in (text, text.replace(" ", "T")):
        try:
            return datetime.fromisoformat(candidate.replace("Z", "+00:00")).replace(tzinfo=None)
        except ValueError:
            continue
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


def _clamp(value: float) -> float:
    """Restringe o número ao intervalo de zero a um."""
    return max(0.0, min(1.0, float(value)))


def _temporal_weight(age_seconds: float, retention_seconds: int) -> float:
    """Dá mais importância aos eventos recentes conforme as faixas de idade configuradas."""
    if age_seconds <= 60:
        return 1.0
    if age_seconds <= 180:
        return 0.70
    if age_seconds <= 300:
        return 0.45
    return max(0.08, exp(-age_seconds / max(1.0, retention_seconds)))


def _status_for_score(
    *,
    base_prediction: int,
    score: float,
    threat_type: str,
    operational_noise: float,
) -> str:
    """Escolhe a categoria experimental pela pontuação e pela classificação de base."""
    if base_prediction == 1 and score >= 0.80:
        return "attack_confirmed"
    if score >= 0.78:
        return "attack_probable"
    if score >= 0.55:
        return "suspicious_medium"
    if score >= 0.35:
        return "suspicious_low"
    if operational_noise >= 0.70 and threat_type == "normal":
        return "operational_noise"
    return "normal"


class MemoryContextV2Analyzer:
    """Calcula riscos por ameaca usando estado recente multinivel."""

    def __init__(self, config: MemoryContextV2Config | None = None) -> None:
        """Prepara os históricos por origem, destino e porta da comparação experimental."""
        self.config = config or MemoryContextV2Config()
        self.source_states: dict[str, StateBucket] = {}
        self.source_dest_states: dict[tuple[str, str], StateBucket] = {}
        self.source_port_states: dict[tuple[str, int], StateBucket] = {}
        self.source_dest_port_states: dict[tuple[str, str, int], StateBucket] = {}
        self.dest_port_states: dict[tuple[str, int], StateBucket] = {}
        self.stats: Counter[str] = Counter()
        self.state_samples: list[int] = []
        self.peak_active_states = 0
        self._processed_since_full_prune = 0

    def _all_state_maps(self) -> list[dict[Any, StateBucket]]:
        """Reúne os históricos mantidos por origem, destino e porta."""
        return [
            self.source_states,
            self.source_dest_states,
            self.source_port_states,
            self.source_dest_port_states,
            self.dest_port_states,
        ]

    def _active_state_count(self) -> int:
        """Conta quantos grupos de histórico estão sendo acompanhados."""
        return sum(len(state_map) for state_map in self._all_state_maps())

    def _build_event(self, row: dict[str, Any]) -> MemoryV2Event | None:
        """Monta o evento temporal usando os campos disponíveis da janela analisada."""
        timestamp = _parse_timestamp(
            _row_value(row, "window_start", "time_window", "timestamp", "window_end")
        )
        source_ip = str(_row_value(row, "source_ip", "src_ip") or "").strip()
        if timestamp is None or not source_ip:
            self.stats["fallback_missing_temporal_or_source"] += 1
            return None

        destination_samples = _parse_ip_sample(_row_value(row, "destination_ip_sample"))
        destination_ip_count = _int_value(_row_value(row, "destination_ip_count"))
        if destination_ip_count and not destination_samples:
            destination_samples = {f"destino_{index}" for index in range(destination_ip_count)}

        ports = _parse_ports(
            _row_value(row, "common_destination_ports", "safe_port_text"),
            _row_value(row, "destination_port_min"),
            _row_value(row, "destination_port_max"),
        )
        destination_port_count = max(
            _int_value(_row_value(row, "destination_port_count")),
            len(ports),
        )
        temporal_selected_port = _int_value(_row_value(row, "ctx_flow_selected_port"))
        protocol = str(_row_value(row, "protocol") or "").strip().lower()
        action = str(_row_value(row, "action") or "").strip().lower()
        noise_category = str(_row_value(row, "operational_noise_category") or "").strip()
        operational_noise_reason = str(_row_value(row, "operational_noise_reason") or "").strip()
        only_noise_ports = bool(ports) and ports.issubset(NOISE_PORTS)
        is_noise = (
            protocol in NOISE_PROTOCOLS
            or only_noise_ports
            or (protocol == "udp" and bool(ports & NOISE_PORTS))
            or bool(noise_category)
            or bool(operational_noise_reason)
        )

        return MemoryV2Event(
            timestamp=timestamp,
            source_ip=source_ip,
            destination_samples=destination_samples,
            destination_ip_count=destination_ip_count,
            destination_ports=ports,
            destination_port_count=destination_port_count,
            protocol=protocol,
            action=action,
            connections=_float_value(_row_value(row, "connections")),
            bytes_per_connection=_float_value(_row_value(row, "bytes_per_connection")),
            packets_per_connection=_float_value(_row_value(row, "packets_per_connection")),
            packets=_float_value(_row_value(row, "packets")),
            tcp_syn_count=_float_value(_row_value(row, "tcp_syn_count")),
            blocked_count=_float_value(_row_value(row, "blocked_count")),
            passed_count=_float_value(_row_value(row, "passed_count")),
            ae_normalized=_float_value(
                _row_value(row, "ae_normalized", "score_ae_normalized")
            ),
            if_normalized=_float_value(
                _row_value(row, "if_normalized", "score_if_normalized")
            ),
            ensemble_score=_float_value(
                _row_value(row, "ensemble_score", "score_ensemble")
            ),
            heuristic_attack_type=str(_row_value(row, "heuristic_attack_type") or "normal"),
            heuristic_confidence=_float_value(_row_value(row, "heuristic_confidence")),
            rolling_distinct_ports=_int_value(_row_value(row, "rolling_distinct_ports")),
            rolling_connections=_float_value(_row_value(row, "rolling_connections")),
            is_noise=is_noise,
            has_sensitive_port=(
                any(port in SENSITIVE_SERVICE_PORTS for port in ports)
                or temporal_selected_port in SENSITIVE_SERVICE_PORTS
            ),
            temporal_context_available=_bool_value(
                _row_value(row, "ctx_flow_context_available")
            ),
            ctx_flow_selected_port=temporal_selected_port,
            ctx_flow_count_600s=_int_value(_row_value(row, "ctx_flow_count_600s")),
            ctx_flow_span_600s=_float_value(_row_value(row, "ctx_flow_span_600s")),
            ctx_flow_interval_mean_600s=_float_value(
                _row_value(row, "ctx_flow_interval_mean_600s")
            ),
            ctx_flow_interval_cv_600s=_float_value(
                _row_value(row, "ctx_flow_interval_cv_600s")
            ),
            ctx_flow_consecutive_active_windows=_int_value(
                _row_value(row, "ctx_flow_consecutive_active_windows")
            ),
        )

    def _bucket(self, mapping: dict[Any, StateBucket], key: Any) -> StateBucket:
        """Obtém o grupo de histórico de uma chave ou cria um grupo vazio."""
        bucket = mapping.get(key)
        if bucket is None:
            bucket = StateBucket(key=key if isinstance(key, tuple) else (key,))
            mapping[key] = bucket
            self.stats["states_created"] += 1
        return bucket

    def _append_event(self, event: MemoryV2Event) -> None:
        """Acrescenta o mesmo evento aos agrupamentos de origem, destino e porta pertinentes."""
        self._bucket(self.source_states, event.source_ip).append(event)
        for destination in event.destination_samples or {"destino_desconhecido"}:
            self._bucket(self.source_dest_states, (event.source_ip, destination)).append(event)
            for port in event.destination_ports or {0}:
                self._bucket(self.source_dest_port_states, (event.source_ip, destination, port)).append(event)
                if port:
                    self._bucket(self.dest_port_states, (destination, port)).append(event)
        for port in event.destination_ports or {0}:
            if port:
                self._bucket(self.source_port_states, (event.source_ip, port)).append(event)

    def _prune_bucket(self, bucket: StateBucket, now: datetime) -> bool:
        """Descarta eventos vencidos de um grupo e informa se ainda restou histórico."""
        retention = max(1, int(self.config.retention_seconds))
        while bucket.events:
            age = (now - bucket.events[0].timestamp).total_seconds()
            if age <= retention:
                break
            bucket.events.popleft()
            self.stats["states_removed_by_time"] += 1
        return bool(bucket.events)

    def _prune_touched(self, event: MemoryV2Event) -> None:
        """Limpa somente os grupos afetados pelo evento recém-recebido."""
        now = event.timestamp
        keys: list[tuple[dict[Any, StateBucket], Any]] = [(self.source_states, event.source_ip)]
        for destination in event.destination_samples or {"destino_desconhecido"}:
            keys.append((self.source_dest_states, (event.source_ip, destination)))
            for port in event.destination_ports or {0}:
                keys.append((self.source_dest_port_states, (event.source_ip, destination, port)))
                if port:
                    keys.append((self.dest_port_states, (destination, port)))
        for port in event.destination_ports or {0}:
            if port:
                keys.append((self.source_port_states, (event.source_ip, port)))

        for mapping, key in keys:
            bucket = mapping.get(key)
            if bucket is not None and not self._prune_bucket(bucket, now):
                mapping.pop(key, None)

    def _full_prune(self, now: datetime) -> None:
        """Limpa eventos vencidos de todos os grupos e remove grupos vazios."""
        for mapping in self._all_state_maps():
            empty_keys: list[Any] = []
            for key, bucket in mapping.items():
                if not self._prune_bucket(bucket, now):
                    empty_keys.append(key)
            for key in empty_keys:
                mapping.pop(key, None)

    def _prune_hardcap(self) -> None:
        """Remove os grupos mais antigos quando a quantidade acompanhada excede o limite."""
        limit = max(1, int(self.config.max_tracked_sources))
        total = self._active_state_count()
        if total <= limit:
            return
        buckets: list[tuple[datetime, dict[Any, StateBucket], Any, int]] = []
        for mapping in self._all_state_maps():
            for key, bucket in mapping.items():
                buckets.append((bucket.last_seen or datetime.min, mapping, key, len(bucket.events)))
        buckets.sort(key=lambda item: item[0])
        for _, mapping, key, event_count in buckets[: total - limit]:
            mapping.pop(key, None)
            self.stats["states_removed_by_hardcap"] += event_count

    def _summarize(self, events: Deque[MemoryV2Event], now: datetime) -> dict[str, Any]:
        """Resume volumes, portas e destinos do histórico, com maior peso para eventos recentes."""
        destinations: set[str] = set()
        ports: set[int] = set()
        sources: set[str] = set()
        weighted_connections = 0.0
        weighted_syn = 0.0
        weighted_sensitive = 0.0
        weighted_score = 0.0
        noise_windows = 0
        small_windows = 0
        weak_scan_windows = 0
        protocols: Counter[str] = Counter()
        actions: Counter[str] = Counter()

        for event in events:
            age = max(0.0, (now - event.timestamp).total_seconds())
            weight = _temporal_weight(age, self.config.retention_seconds)
            destinations.update(event.destination_samples)
            ports.update(port for port in event.destination_ports if port)
            sources.add(event.source_ip)
            weighted_connections += event.connections * weight
            weighted_syn += event.tcp_syn_count * weight
            weighted_score += event.ensemble_score * weight
            if event.has_sensitive_port:
                weighted_sensitive += max(1.0, event.connections) * weight
            if event.is_noise:
                noise_windows += 1
            if (
                event.connections <= 5
                and event.bytes_per_connection <= 2500
                and event.packets_per_connection <= 5
            ):
                small_windows += 1
            if (
                not event.is_noise
                and event.connections <= 5
                and event.destination_port_count <= 3
                and event.ensemble_score >= 0.005
            ):
                weak_scan_windows += 1
            protocols[event.protocol or "unknown"] += 1
            actions[event.action or "unknown"] += 1

        total = max(1, len(events))
        return {
            "window_count": len(events),
            "distinct_destinations": len(destinations),
            "distinct_ports": len(ports),
            "distinct_sources": len(sources),
            "weighted_connections": weighted_connections,
            "weighted_syn": weighted_syn,
            "weighted_sensitive": weighted_sensitive,
            "weighted_score": weighted_score,
            "noise_ratio": noise_windows / total,
            "small_window_ratio": small_windows / total,
            "weak_scan_windows": weak_scan_windows,
            "dominant_protocol": protocols.most_common(1)[0][0] if protocols else "",
            "dominant_action": actions.most_common(1)[0][0] if actions else "",
        }

    def _history_ready(self, bucket: StateBucket, now: datetime) -> bool:
        """Confere se há quantidade ou duração de histórico suficiente para avaliar o contexto."""
        if len(bucket.events) >= int(self.config.min_history_windows) + 1:
            return True
        if bucket.first_seen is None:
            return False
        elapsed = (now - bucket.first_seen).total_seconds()
        return elapsed >= float(self.config.min_history_seconds)

    def _risk_operational_noise(self, event: MemoryV2Event, source_summary: dict[str, Any]) -> tuple[float, list[str]]:
        """Avalia sinais de tráfego operacional recorrente para a comparação experimental."""
        reasons: list[str] = []
        risk = 0.0
        if event.is_noise:
            risk = max(risk, 0.65)
            reasons.append("Padrao de ruido operacional conhecido na janela atual.")
        if source_summary["noise_ratio"] >= 0.75:
            risk = max(risk, 0.80)
            reasons.append("Historico recente dominado por ruido operacional.")
        if event.action == "block" and event.blocked_count > event.passed_count and source_summary["distinct_ports"] <= 3:
            risk = max(risk, 0.70)
            reasons.append("Bloqueios repetidos sem diversidade ofensiva forte.")
        return _clamp(risk), reasons

    def _risk_portscan(
        self,
        event: MemoryV2Event,
        source_summary: dict[str, Any],
        source_dest_summaries: list[dict[str, Any]],
        history_ready: bool,
    ) -> tuple[float, list[str]]:
        """Avalia indícios temporais de varredura de portas na comparação experimental."""
        reasons: list[str] = []
        if not history_ready or source_summary["noise_ratio"] >= 0.80:
            return 0.0, reasons

        vertical_max_ports = max(
            [summary["distinct_ports"] for summary in source_dest_summaries] or [0]
        )
        rolling_ports = max(event.rolling_distinct_ports, source_summary["distinct_ports"])
        horizontal_destinations = max(
            source_summary["distinct_destinations"],
            event.destination_ip_count,
        )
        weak_windows = int(source_summary["weak_scan_windows"])
        small_ratio = float(source_summary["small_window_ratio"])
        connections = float(source_summary["weighted_connections"])

        vertical_score = 0.0
        if vertical_max_ports >= int(self.config.portscan_vertical_ports) and small_ratio >= 0.45:
            vertical_score = min(1.0, vertical_max_ports / 12.0)
            reasons.append("Origem acumulou muitas portas contra o mesmo destino.")

        horizontal_score = 0.0
        if (
            horizontal_destinations >= int(self.config.portscan_horizontal_destinations)
            and source_summary["distinct_ports"] <= 5
            and small_ratio >= 0.45
        ):
            horizontal_score = min(1.0, horizontal_destinations / 12.0)
            reasons.append("Origem acumulou varios destinos com poucas portas.")

        rolling_score = 0.0
        if (
            rolling_ports >= int(self.config.portscan_rolling_ports)
            and event.rolling_connections >= 12
            and not event.is_noise
        ):
            rolling_score = min(1.0, rolling_ports / 16.0)
            reasons.append("Campos rolling indicam crescimento de portas distintas.")

        slow_score = 0.0
        if (
            weak_windows >= int(self.config.portscan_min_windows)
            and connections >= 8
            and small_ratio >= 0.60
            and source_summary["distinct_ports"] >= 3
        ):
            slow_score = min(0.72, 0.30 + (weak_windows * 0.12))
            reasons.append("Janelas fracas e pequenas se repetiram no historico recente.")

        return _clamp(max(vertical_score, horizontal_score, rolling_score, slow_score)), reasons

    def _risk_bruteforce(
        self,
        event: MemoryV2Event,
        source_dest_port_summaries: list[dict[str, Any]],
        history_ready: bool,
    ) -> tuple[float, list[str], bool]:
        """Avalia repetição em serviços sensíveis; logs de firewall não comprovam falhas de senha."""
        reasons: list[str] = []
        temporal_rule_matched = False
        if (
            self.config.experimental_temporal_bruteforce_enabled
            and event.temporal_context_available
            and event.has_sensitive_port
            and event.ctx_flow_count_600s
            >= int(self.config.temporal_bruteforce_count_600_min)
            and event.ctx_flow_span_600s
            >= float(self.config.temporal_bruteforce_span_600_min)
            and event.ctx_flow_interval_mean_600s
            >= float(self.config.temporal_bruteforce_interval_mean_600_min)
            and event.ctx_flow_interval_cv_600s
            <= float(self.config.temporal_bruteforce_interval_cv_600_max)
            and event.ctx_flow_consecutive_active_windows
            >= int(self.config.temporal_bruteforce_consecutive_windows_min)
        ):
            temporal_rule_matched = True
            reasons.append(
                "Padrao temporal composto persistente e regular contra servico sensivel."
            )

        if not event.has_sensitive_port:
            return 0.0, reasons, temporal_rule_matched

        historical_risk = 0.0
        if not history_ready:
            return (1.0 if temporal_rule_matched else 0.0), reasons, temporal_rule_matched
        max_sensitive = max(
            [summary["weighted_sensitive"] for summary in source_dest_port_summaries] or [0.0]
        )
        max_windows = max(
            [summary["window_count"] for summary in source_dest_port_summaries] or [0]
        )
        if max_sensitive >= float(self.config.bruteforce_sensitive_hits) and max_windows >= 2:
            reasons.append("Repeticao contra servico sensivel em janelas recentes.")
            historical_risk = _clamp(max_sensitive / 14.0)
        return (
            max(historical_risk, 1.0 if temporal_rule_matched else 0.0),
            reasons,
            temporal_rule_matched,
        )

    def _risk_synflood(
        self,
        event: MemoryV2Event,
        dest_port_summaries: list[dict[str, Any]],
        history_ready: bool,
    ) -> tuple[float, list[str]]:
        """Avalia concentração de pacotes SYN na comparação experimental."""
        reasons: list[str] = []
        max_syn = max([summary["weighted_syn"] for summary in dest_port_summaries] or [0.0])
        max_sources = max([summary["distinct_sources"] for summary in dest_port_summaries] or [0])
        current_syn = event.tcp_syn_count
        if current_syn >= float(self.config.synflood_syn_threshold):
            reasons.append("Volume SYN alto na janela atual.")
            return 0.88, reasons
        if history_ready and max_syn >= float(self.config.synflood_syn_threshold):
            reasons.append("Destino/porta acumulou volume SYN alto no historico.")
            return _clamp(max_syn / 60.0), reasons
        if history_ready and max_sources >= 6 and max_syn >= 15:
            reasons.append("Multiplas origens convergiram para o mesmo destino/porta.")
            return 0.72, reasons
        return 0.0, reasons

    def analyze(self, row: dict[str, Any], *, base_prediction: int) -> dict[str, Any]:
        """Processa uma janela e retorna sinais explicáveis da memória v2."""
        event = self._build_event(row)
        if event is None:
            return {
                "memory_active": False,
                "memory_fallback_used": True,
                "temporal_context_fallback_used": bool(
                    self.config.experimental_temporal_bruteforce_enabled
                ),
                "prediction_memory_v2": int(base_prediction),
                "final_status_level": "normal" if int(base_prediction) == 0 else "attack_probable",
                "final_status_label": STATUS_LABELS["normal" if int(base_prediction) == 0 else "attack_probable"],
                "threat_type": "unknown_anomaly",
                "threat_label": THREAT_LABELS["unknown_anomaly"],
                "risk_portscan": 0.0,
                "risk_bruteforce": 0.0,
                "risk_synflood": 0.0,
                "risk_operational_noise": 0.0,
                "risk_overall_context": 0.0,
                "final_memory_v2_score": 0.0,
                "friendly_reasons": ["Memoria indisponivel; fallback para o baseline."],
                "technical_reasons": ["missing_temporal_or_source_key"],
                "memory_history_ready": False,
                "memory_cold_start": True,
                "memory_reason": "Fallback para prediction_v2_3.",
                "memory_signals": {},
            }

        self._processed_since_full_prune += 1
        self._prune_touched(event)
        if self._processed_since_full_prune >= 250:
            self._full_prune(event.timestamp)
            self._processed_since_full_prune = 0
        self._append_event(event)
        self._prune_hardcap()

        source_bucket = self.source_states[event.source_ip]
        history_ready = self._history_ready(source_bucket, event.timestamp)
        if not history_ready:
            self.stats["cold_start_windows"] += 1
        self.stats["processed_windows"] += 1

        source_summary = self._summarize(source_bucket.events, event.timestamp)
        destinations = event.destination_samples or {"destino_desconhecido"}
        ports = event.destination_ports or {0}
        source_dest_summaries = [
            self._summarize(bucket.events, event.timestamp)
            for destination in destinations
            if (
                bucket := self.source_dest_states.get(
                    (event.source_ip, destination)
                )
            )
        ]
        source_dest_port_summaries = [
            self._summarize(bucket.events, event.timestamp)
            for destination in destinations
            for port in ports
            if (
                bucket := self.source_dest_port_states.get(
                    (event.source_ip, destination, port)
                )
            )
        ]
        dest_port_summaries = [
            self._summarize(bucket.events, event.timestamp)
            for destination in destinations
            for port in ports
            if (bucket := self.dest_port_states.get((destination, port)))
        ]

        risk_noise, noise_reasons = self._risk_operational_noise(event, source_summary)
        risk_portscan, portscan_reasons = self._risk_portscan(
            event,
            source_summary,
            source_dest_summaries,
            history_ready,
        )
        risk_bruteforce, bruteforce_reasons, temporal_bruteforce_matched = self._risk_bruteforce(
            event,
            source_dest_port_summaries,
            history_ready,
        )
        risk_synflood, synflood_reasons = self._risk_synflood(
            event,
            dest_port_summaries,
            history_ready,
        )

        if risk_noise >= 0.75:
            if risk_portscan < 0.86:
                risk_portscan *= 0.45
            if risk_bruteforce < 0.86:
                risk_bruteforce *= 0.55
            if risk_synflood < 0.86:
                risk_synflood *= 0.75

        model_signal = _clamp(max(event.ae_normalized, event.if_normalized))
        current_ensemble_signal = _clamp(event.ensemble_score)
        threat_score_portscan = _clamp(
            (self.config.model_signal_weight * model_signal)
            + (self.config.current_ensemble_weight * current_ensemble_signal)
            + (self.config.portscan_memory_weight * risk_portscan)
        )
        threat_score_bruteforce = _clamp(
            (self.config.model_signal_weight * model_signal)
            + (self.config.current_ensemble_weight * current_ensemble_signal)
            + (self.config.bruteforce_memory_weight * risk_bruteforce)
        )
        if temporal_bruteforce_matched:
            threat_score_bruteforce = max(
                threat_score_bruteforce,
                _clamp(self.config.temporal_bruteforce_direct_score),
            )
        threat_score_synflood = _clamp(
            (self.config.synflood_model_signal_weight * model_signal)
            + (self.config.synflood_current_ensemble_weight * current_ensemble_signal)
            + (self.config.synflood_memory_weight * risk_synflood)
        )

        threat_scores = {
            "port_scan": threat_score_portscan,
            "brute_force_suspected": threat_score_bruteforce,
            "syn_flood": threat_score_synflood,
        }
        threat_type, final_score = max(threat_scores.items(), key=lambda item: item[1])
        if final_score < 0.25:
            threat_type = "normal"
        if risk_noise >= 0.70 and final_score < 0.35:
            threat_type = "operational_noise"

        prediction = int(base_prediction)
        if (
            (history_ready or temporal_bruteforce_matched)
            and final_score >= float(self.config.final_attack_threshold)
            and threat_type not in {"normal", "operational_noise"}
        ):
            prediction = 1
        elif (
            prediction == 1
            and risk_noise >= float(self.config.suppression_noise_threshold)
            and final_score <= float(self.config.suppression_max_threat_score)
        ):
            prediction = 0
            self.stats["suppressed_by_noise"] += 1

        if prediction == 1 and int(base_prediction) == 0:
            self.stats["promoted_by_memory_v2"] += 1
        elif prediction == 0 and int(base_prediction) == 1:
            self.stats["regressed_by_memory_v2"] += 1

        status_level = _status_for_score(
            base_prediction=prediction,
            score=final_score,
            threat_type=threat_type,
            operational_noise=risk_noise,
        )
        friendly_reasons = (
            portscan_reasons
            + bruteforce_reasons
            + synflood_reasons
            + noise_reasons
        )
        if not friendly_reasons:
            friendly_reasons = ["Sem coerencia historica suficiente para elevar a decisao."]

        self.peak_active_states = max(self.peak_active_states, self._active_state_count())
        self.state_samples.append(self._active_state_count())

        memory_signals = {
            "source_summary": source_summary,
            "model_signal": model_signal,
            "current_ensemble_signal": current_ensemble_signal,
            "threat_score_portscan": threat_score_portscan,
            "threat_score_bruteforce": threat_score_bruteforce,
            "threat_score_synflood": threat_score_synflood,
            "temporal_bruteforce": {
                "enabled": bool(
                    self.config.experimental_temporal_bruteforce_enabled
                ),
                "context_available": event.temporal_context_available,
                "rule_matched": temporal_bruteforce_matched,
                "selected_port": event.ctx_flow_selected_port or None,
                "count_600s": event.ctx_flow_count_600s,
                "span_600s": event.ctx_flow_span_600s,
                "interval_mean_600s": event.ctx_flow_interval_mean_600s,
                "interval_cv_600s": event.ctx_flow_interval_cv_600s,
                "consecutive_active_windows": (
                    event.ctx_flow_consecutive_active_windows
                ),
                "thresholds_are_development_only": True,
            },
            "destination_sample_is_partial": (
                event.destination_ip_count > len(event.destination_samples)
            ),
            "port_list_is_partial": event.destination_port_count > len(event.destination_ports),
        }

        return {
            "memory_active": True,
            "memory_fallback_used": False,
            "temporal_context_fallback_used": bool(
                self.config.experimental_temporal_bruteforce_enabled
                and not event.temporal_context_available
            ),
            "prediction_memory_v2": prediction,
            "final_status_level": status_level,
            "final_status_label": STATUS_LABELS[status_level],
            "threat_type": threat_type,
            "threat_label": THREAT_LABELS.get(threat_type, THREAT_LABELS["unknown_anomaly"]),
            "risk_portscan": _clamp(risk_portscan),
            "risk_bruteforce": _clamp(risk_bruteforce),
            "risk_synflood": _clamp(risk_synflood),
            "risk_operational_noise": _clamp(risk_noise),
            "risk_overall_context": _clamp(final_score),
            "final_memory_v2_score": _clamp(final_score),
            "memory_history_ready": history_ready,
            "memory_cold_start": not history_ready,
            "memory_reason": "; ".join(friendly_reasons),
            "memory_signals": memory_signals,
            "friendly_reasons": friendly_reasons,
            "technical_reasons": [
                f"history_ready={history_ready}",
                f"risk_portscan={risk_portscan:.4f}",
                f"risk_bruteforce={risk_bruteforce:.4f}",
                f"risk_synflood={risk_synflood:.4f}",
                f"risk_noise={risk_noise:.4f}",
                f"temporal_bruteforce_matched={temporal_bruteforce_matched}",
                f"final_score={final_score:.4f}",
            ],
        }

    def get_stats(self) -> dict[str, Any]:
        """Retorna estatísticas agregadas do estado."""
        active_states = self._active_state_count()
        active_events = 0
        for mapping in self._all_state_maps():
            active_events += sum(len(bucket.events) for bucket in mapping.values())
        average_states = (
            sum(self.state_samples) / len(self.state_samples)
            if self.state_samples
            else 0.0
        )
        return {
            "active_states": active_states,
            "active_events": active_events,
            "peak_active_states": self.peak_active_states,
            "average_active_states": average_states,
            "states_created": int(self.stats["states_created"]),
            "states_removed_by_time": int(self.stats["states_removed_by_time"]),
            "states_removed_by_hardcap": int(self.stats["states_removed_by_hardcap"]),
            "processed_windows": int(self.stats["processed_windows"]),
            "cold_start_windows": int(self.stats["cold_start_windows"]),
            "fallback_missing_temporal_or_source": int(
                self.stats["fallback_missing_temporal_or_source"]
            ),
            "promoted_by_memory_v2": int(self.stats["promoted_by_memory_v2"]),
            "regressed_by_memory_v2": int(self.stats["regressed_by_memory_v2"]),
            "suppressed_by_noise": int(self.stats["suppressed_by_noise"]),
        }
