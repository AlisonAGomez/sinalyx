"""Contexto auxiliar de seguranca por janela.

Este módulo e experimental, lateral e desligavel. Ele não altera as 13
características oficiais do Sinalyx e não deve ser usado para treinar Autoencoder ou
Isolation Forest. O objetivo e preservar sinais interpretaveis que podem
apoiar heurísticas, ensemble contextual e Motor de decisão em etapas futuras.
"""

from __future__ import annotations

import hashlib
import re
from collections import Counter
from typing import Any, Iterable


TOP_DESTINATION_IP_LIMIT = 10
DESTINATION_IP_LIST_LIMIT = 25
TOP_DESTINATION_PORT_LIMIT = 20
DESTINATION_PORT_LIST_LIMIT = 50
TOP_SOURCE_DESTINATION_PAIR_LIMIT = 20
TOP_SOURCE_DESTINATION_PORT_PAIR_LIMIT = 30

IP_PATTERN = re.compile(r"\b(?:\d{1,3}\.){3}\d{1,3}\b")

SOURCE_IP_FIELDS = ("source_ip", "src_ip", "Source IP", "src")
DESTINATION_IP_FIELDS = (
    "destination_ip",
    "destination_ip_sample",
    "dst_ip",
    "dest_ip",
    "Destination IP",
    "dst",
)
DESTINATION_PORT_FIELDS = (
    "destination_port",
    "dst_port",
    "dest_port",
    "Destination Port",
    "common_destination_ports",
    "safe_port_text",
)
SOURCE_PORT_FIELDS = ("source_port", "src_port", "Source Port")

NOISE_PORTS = {
    1900: "SSDP",
    3702: "WS-Discovery",
    5353: "mDNS",
    5355: "LLMNR",
    547: "DHCPv6",
}
SENSITIVE_SERVICE_PORTS = {
    21: "FTP",
    22: "SSH",
    23: "Telnet",
    25: "SMTP",
    53: "DNS",
    80: "HTTP",
    110: "POP3",
    143: "IMAP",
    389: "LDAP",
    443: "HTTPS",
    445: "SMB",
    1433: "MSSQL",
    1521: "Oracle",
    3306: "MySQL",
    3389: "RDP",
    5432: "PostgreSQL",
    5900: "VNC",
    6379: "Redis",
    9200: "Elasticsearch",
}


def _as_records(events: Iterable[dict[str, Any]] | None) -> list[dict[str, Any]]:
    """Copia somente os eventos que são dicionários para uma lista uniforme."""
    return [dict(event) for event in (events or []) if isinstance(event, dict)]


def _first_value(records: Iterable[dict[str, Any]], names: Iterable[str]) -> Any:
    """Procura o primeiro campo preenchido entre os registros e nomes informados."""
    for record in records:
        for name in names:
            value = record.get(name)
            if value not in (None, ""):
                return value
    return None


def _safe_int(value: Any, default: int = 0) -> int:
    """Converte para inteiro; valores vazios ou inválidos usam o padrão informado."""
    try:
        if value in (None, ""):
            return default
        return int(float(value))
    except (TypeError, ValueError):
        return default


def _safe_float(value: Any, default: float = 0.0) -> float:
    """Converte para decimal; valores vazios ou inválidos usam o padrão informado."""
    try:
        if value in (None, ""):
            return default
        return float(value)
    except (TypeError, ValueError):
        return default


def _split_tokens(value: Any) -> list[str]:
    """Separa os itens de texto ou de listas sem perder os itens das estruturas aninhadas."""
    if isinstance(value, (list, tuple, set)):
        tokens: list[str] = []
        for item in value:
            tokens.extend(_split_tokens(item))
        return tokens
    text = str(value or "").strip()
    if not text:
        return []
    return [
        token.strip()
        for token in re.split(r"[,;|\s]+", text)
        if token.strip()
    ]


def _extract_ips(value: Any) -> list[str]:
    """Extrai os endereços IP presentes no texto de contexto."""
    text = str(value or "")
    matches = IP_PATTERN.findall(text)
    if matches:
        return matches
    return [
        token
        for token in _split_tokens(value)
        if IP_PATTERN.fullmatch(token)
    ]


def _extract_ports(value: Any) -> list[int]:
    """Lê portas numéricas e mantém somente valores na faixa permitida."""
    ports: list[int] = []
    for token in _split_tokens(value):
        try:
            port = int(float(token))
        except ValueError:
            continue
        if 0 < port <= 65535:
            ports.append(port)
    return ports


def _unique_ordered(values: Iterable[Any], limit: int | None = None) -> list[Any]:
    """Remove repetições preservando a ordem em que os valores apareceram."""
    result: list[Any] = []
    seen: set[Any] = set()
    for value in values:
        if value in seen:
            continue
        seen.add(value)
        result.append(value)
        if limit is not None and len(result) >= limit:
            break
    return result


def _top(counter: Counter[Any], limit: int) -> list[dict[str, Any]]:
    """Retorna os valores mais frequentes com suas contagens."""
    return [
        {"value": value, "count": count}
        for value, count in counter.most_common(limit)
    ]


def _metadata_records(
    events: Iterable[dict[str, Any]] | None,
    window_metadata: dict[str, Any] | None,
) -> list[dict[str, Any]]:
    """Junta os dados complementares da janela aos registros disponíveis."""
    records = _as_records(events)
    if window_metadata:
        return [dict(window_metadata), *records]
    return records


def _hash_ip(value: Any) -> str:
    """Gera um identificador curto e estável para o IP sem reproduzir o endereço no relatório."""
    text = str(value or "").strip()
    if not text:
        return ""
    digest = hashlib.sha256(f"sinalyx:{text}".encode("utf-8")).hexdigest()
    return digest[:12]


def summarize_destination_ips(
    events: Iterable[dict[str, Any]] | None,
    window_metadata: dict[str, Any] | None = None,
) -> dict[str, Any]:
    """Resume destinos da janela com os campos disponiveis."""

    raw_records = _as_records(events)
    metadata_records = [dict(window_metadata)] if window_metadata else []
    records = raw_records or metadata_records
    ips: list[str] = []
    for record in records:
        for field in DESTINATION_IP_FIELDS:
            if field in record:
                ips.extend(_extract_ips(record.get(field)))

    counter = Counter(ips)
    reported_count = _safe_int(_first_value(metadata_records, ("destination_ip_count",)), 0)
    distinct_count = len(counter)
    destination_ip_count = max(reported_count, distinct_count)
    limitations: list[str] = []
    if reported_count > distinct_count:
        limitations.append("destination_ip_list_partial")

    return {
        "destination_ip_count": destination_ip_count,
        "destination_ip_sample": _unique_ordered(ips, TOP_DESTINATION_IP_LIMIT),
        "top_destination_ips": _top(counter, TOP_DESTINATION_IP_LIMIT),
        "destination_ip_list_limited": _unique_ordered(ips, DESTINATION_IP_LIST_LIMIT),
        "limitations": limitations,
    }


def summarize_destination_ports(
    events: Iterable[dict[str, Any]] | None,
    window_metadata: dict[str, Any] | None = None,
) -> dict[str, Any]:
    """Resume portas de destino preservando limites seguros."""

    raw_records = _as_records(events)
    metadata_records = [dict(window_metadata)] if window_metadata else []
    records = raw_records or metadata_records
    ports: list[int] = []
    for record in records:
        for field in DESTINATION_PORT_FIELDS:
            if field in record:
                ports.extend(_extract_ports(record.get(field)))
        min_port = _safe_int(record.get("destination_port_min"), 0)
        max_port = _safe_int(record.get("destination_port_max"), 0)
        if 0 < min_port <= 65535:
            ports.append(min_port)
        if 0 < max_port <= 65535:
            ports.append(max_port)

    counter = Counter(ports)
    reported_count = _safe_int(
        _first_value(metadata_records, ("destination_port_count", "ports")),
        0,
    )
    distinct_count = len(counter)
    destination_port_count = max(reported_count, distinct_count)
    limited_ports = _unique_ordered(sorted(counter), DESTINATION_PORT_LIST_LIMIT)
    limitations: list[str] = []
    if reported_count > distinct_count:
        limitations.append("destination_port_list_partial")

    return {
        "destination_port_count": destination_port_count,
        "destination_port_min": min(limited_ports) if limited_ports else None,
        "destination_port_max": max(limited_ports) if limited_ports else None,
        "common_destination_ports": limited_ports[:TOP_DESTINATION_PORT_LIMIT],
        "top_destination_ports": _top(counter, TOP_DESTINATION_PORT_LIMIT),
        "destination_port_list_limited": limited_ports,
        "limitations": limitations,
    }


def summarize_pairs(
    events: Iterable[dict[str, Any]] | None,
    window_metadata: dict[str, Any] | None = None,
) -> dict[str, Any]:
    """Resume pares origem/destino e origem/destino/porta."""

    raw_records = _as_records(events)
    metadata_records = [dict(window_metadata)] if window_metadata else []
    records = raw_records or metadata_records
    source_destination = Counter()
    source_destination_port = Counter()

    for record in records:
        source = str(_first_value([record], SOURCE_IP_FIELDS) or "").strip()
        destinations = []
        ports = []
        for field in DESTINATION_IP_FIELDS:
            destinations.extend(_extract_ips(record.get(field)))
        for field in DESTINATION_PORT_FIELDS:
            ports.extend(_extract_ports(record.get(field)))
        if not source:
            continue
        for destination in _unique_ordered(destinations):
            source_destination[f"{source}->{destination}"] += 1
            for port in _unique_ordered(ports):
                source_destination_port[f"{source}->{destination}:{port}"] += 1

    return {
        "source_destination_pair_count": len(source_destination),
        "top_source_destination_pairs": _top(
            source_destination,
            TOP_SOURCE_DESTINATION_PAIR_LIMIT,
        ),
        "source_destination_port_pair_count": len(source_destination_port),
        "top_source_destination_port_pairs": _top(
            source_destination_port,
            TOP_SOURCE_DESTINATION_PORT_PAIR_LIMIT,
        ),
        "limitations": ["pair_lists_partial"] if not source_destination_port else [],
    }


def summarize_tcp_flags(
    events: Iterable[dict[str, Any]] | None,
    window_metadata: dict[str, Any] | None = None,
) -> dict[str, Any]:
    """Resume flags TCP quando a janela fornece contadores ou texto."""

    raw_records = _as_records(events)
    metadata_records = [dict(window_metadata)] if window_metadata else []
    records = raw_records or metadata_records
    syn = _safe_int(_first_value(metadata_records, ("tcp_syn_count",)), 0)
    ack = _safe_int(_first_value(metadata_records, ("tcp_ack_count",)), 0)
    rst = _safe_int(_first_value(metadata_records, ("tcp_rst_count",)), 0)
    fin = _safe_int(_first_value(metadata_records, ("tcp_fin_count",)), 0)
    pa = _safe_int(_first_value(metadata_records, ("tcp_pa_count",)), 0)
    summary_text = str(
        _first_value(metadata_records, ("tcp_flags_summary", "flags", "tcp_flags")) or ""
    )

    flag_counter: Counter[str] = Counter()
    for record in records:
        for field in ("tcp_flags", "flags", "tcp_flags_summary"):
            value = record.get(field)
            if value in (None, ""):
                continue
            for token in re.split(r"[,;|\s:/]+", str(value).upper()):
                token = token.strip()
                if token:
                    flag_counter[token] += 1

    if syn == 0:
        syn = int(flag_counter.get("S", 0) + flag_counter.get("SYN", 0))
    if ack == 0:
        ack = int(flag_counter.get("A", 0) + flag_counter.get("ACK", 0))
    if rst == 0:
        rst = int(flag_counter.get("R", 0) + flag_counter.get("RST", 0))
    if fin == 0:
        fin = int(flag_counter.get("F", 0) + flag_counter.get("FIN", 0))
    if pa == 0:
        pa = int(flag_counter.get("PA", 0))

    total_known = syn + ack + rst + fin + pa
    syn_ratio = (syn / total_known) if total_known else None
    limitations: list[str] = []
    if not summary_text and not total_known:
        limitations.append("tcp_flags_not_available")
    if ack == 0:
        limitations.append("tcp_ack_count_not_available")
    if rst == 0:
        limitations.append("tcp_rst_count_not_available")
    if fin == 0:
        limitations.append("tcp_fin_count_not_available")

    return {
        "tcp_syn_count": syn,
        "tcp_ack_count": ack if ack else None,
        "tcp_rst_count": rst if rst else None,
        "tcp_fin_count": fin if fin else None,
        "tcp_pa_count": pa,
        "tcp_flags_summary": summary_text,
        "tcp_syn_ratio": syn_ratio,
        "limitations": limitations,
    }


def classify_service_categories(
    ports: Iterable[int],
    protocol: str | None = None,
) -> dict[str, Any]:
    """Classifica portas em categorias simples e explicáveis."""

    port_set = {int(port) for port in ports if 0 < int(port) <= 65535}
    protocol_text = str(protocol or "").strip().lower()
    sensitive = sorted(
        {
            f"{port}/{SENSITIVE_SERVICE_PORTS[port]}"
            for port in port_set
            if port in SENSITIVE_SERVICE_PORTS
        }
    )
    noise = sorted(
        {
            f"{port}/{NOISE_PORTS[port]}"
            for port in port_set
            if port in NOISE_PORTS
        }
    )
    categories: set[str] = set()
    if sensitive:
        categories.add("servico_sensivel")
    if noise:
        categories.add("ruido_operacional")
    if protocol_text == "icmpv6":
        categories.add("icmpv6")
        noise.append("icmpv6")
    if protocol_text == "udp" and noise:
        categories.add("udp_multicast_broadcast_possivel")

    return {
        "sensitive_services_seen": sensitive,
        "sensitive_service_count": len(sensitive),
        "noise_services_seen": sorted(set(noise)),
        "noise_service_count": len(set(noise)),
        "service_categories": sorted(categories),
    }


def detect_context_hints(context: dict[str, Any]) -> dict[str, bool]:
    """Gera hints conservadores sem confirmar ataque sozinho."""

    protocol = str(context.get("protocol") or "").strip().lower()
    action = str(context.get("action") or "").strip().lower()
    destination_ip_count = _safe_int(context.get("destination_ip_count"), 0)
    destination_port_count = _safe_int(context.get("destination_port_count"), 0)
    connections = _safe_float(context.get("connections"), 0.0)
    bytes_per_connection = _safe_float(context.get("bytes_per_connection"), 0.0)
    tcp_syn_count = _safe_float(context.get("tcp_syn_count"), 0.0)
    tcp_syn_ratio = context.get("tcp_syn_ratio")
    syn_ratio_value = _safe_float(tcp_syn_ratio, 0.0) if tcp_syn_ratio is not None else 0.0
    rolling_distinct_ports = _safe_int(context.get("rolling_distinct_ports"), 0)
    rolling_windows = _safe_int(context.get("rolling_windows"), 0)
    rolling_connections = _safe_float(context.get("rolling_connections"), 0.0)
    noise_service_count = _safe_int(context.get("noise_service_count"), 0)
    sensitive_service_count = _safe_int(context.get("sensitive_service_count"), 0)

    operational_noise = noise_service_count > 0 or protocol == "icmpv6"
    horizontal_scan = (
        destination_ip_count >= 7
        and 1 <= destination_port_count <= 3
        and not operational_noise
    )
    vertical_scan = (
        destination_port_count >= 7
        and destination_ip_count <= 3
        and not operational_noise
    )
    slow_scan = (
        rolling_windows >= 2
        and rolling_distinct_ports >= 10
        and rolling_connections >= 20
        and not operational_noise
    )
    brute_force = (
        sensitive_service_count > 0
        and destination_port_count <= 3
        and (connections >= 6 or rolling_connections >= 12)
        and not operational_noise
    )
    syn_flood = (
        tcp_syn_count >= 30
        and (syn_ratio_value >= 0.70 or bytes_per_connection <= 120)
        and connections >= 10
    )

    return {
        "horizontal_scan_hint": horizontal_scan,
        "vertical_scan_hint": vertical_scan,
        "slow_scan_hint": slow_scan,
        "brute_force_hint": brute_force,
        "syn_flood_hint": syn_flood,
        "operational_noise_hint": operational_noise,
    }


def build_security_window_context(
    events: Iterable[dict[str, Any]] | None,
    window_metadata: dict[str, Any] | None = None,
) -> dict[str, Any]:
    """Cria o contexto auxiliar de seguranca da janela."""

    records = _metadata_records(events, window_metadata)
    metadata = dict(window_metadata or {})
    source_ip = str(_first_value(records, SOURCE_IP_FIELDS) or "").strip()
    src_ip = str(_first_value(records, ("src_ip", "source_ip")) or "").strip()

    destination_ips = summarize_destination_ips(events, metadata)
    destination_ports = summarize_destination_ports(events, metadata)
    pairs = summarize_pairs(events, metadata)
    tcp_flags = summarize_tcp_flags(events, metadata)

    protocol = str(_first_value(records, ("protocol",)) or "").strip().lower()
    action = str(_first_value(records, ("action",)) or "").strip().lower()
    interface = str(_first_value(records, ("interface",)) or "").strip()
    port_list = destination_ports["destination_port_list_limited"]
    services = classify_service_categories(port_list, protocol)

    source_ports: list[int] = []
    for record in records:
        for field in SOURCE_PORT_FIELDS:
            source_ports.extend(_extract_ports(record.get(field)))

    context: dict[str, Any] = {
        "window_id": metadata.get("window_id"),
        "window_start": metadata.get("window_start"),
        "window_end": metadata.get("window_end"),
        "time_window": metadata.get("time_window"),
        "source_file": metadata.get("source_file"),
        "scenario": metadata.get("scenario"),
        "target": metadata.get("target"),
        "source_ip": source_ip,
        "src_ip": src_ip,
        "source_ip_hash": _hash_ip(source_ip or src_ip),
        "protocol": protocol,
        "action": action,
        "interface": interface,
        "passed_count": _safe_int(_first_value(records, ("passed_count",)), 0),
        "blocked_count": _safe_int(_first_value(records, ("blocked_count",)), 0),
        "source_port_count": len(set(source_ports)) if source_ports else None,
        "connections": _safe_float(_first_value(records, ("connections",)), 0.0),
        "bytes": _safe_float(_first_value(records, ("bytes",)), 0.0),
        "packets": _safe_float(_first_value(records, ("packets",)), 0.0),
        "bytes_per_connection": _safe_float(
            _first_value(records, ("bytes_per_connection",)),
            0.0,
        ),
        "packets_per_connection": _safe_float(
            _first_value(records, ("packets_per_connection",)),
            0.0,
        ),
        "rolling_distinct_ports": _safe_int(
            _first_value(records, ("rolling_distinct_ports",)),
            0,
        ),
        "rolling_connections": _safe_float(
            _first_value(records, ("rolling_connections",)),
            0.0,
        ),
        "rolling_windows": _safe_int(_first_value(records, ("rolling_windows",)), 0),
    }
    context.update(destination_ips)
    context.update(destination_ports)
    context.update(pairs)
    context.update(tcp_flags)
    context.update(services)
    context.update(detect_context_hints(context))
    context.pop("limitations", None)

    limitations = []
    for block in (destination_ips, destination_ports, pairs, tcp_flags):
        limitations.extend(block.get("limitations", []))
    if context["source_port_count"] is None:
        limitations.append("source_port_count_not_available")
    if not context.get("top_source_destination_port_pairs"):
        limitations.append("top_source_destination_port_pairs_requires_raw_events")
    if context.get("rolling_windows", 0) <= 0:
        limitations.append("slow_scan_hint_requires_temporal_context")
    context["context_limitations"] = sorted(set(limitations))
    context["security_window_context_version"] = "experimental_v1"
    return context


class SecurityContextAnonymizer:
    """Aplica aliases estaveis em IPs para arquivos de apoio de auditoria."""

    def __init__(self) -> None:
        """Inicia o mapa de nomes que substituirão os endereços IP no relatório."""
        self._aliases: dict[str, str] = {}

    def alias(self, value: Any) -> str:
        """Troca o endereço por um nome sequencial e reutiliza esse nome nas próximas ocorrências."""
        text = str(value or "").strip()
        if not text:
            return ""
        if text not in self._aliases:
            self._aliases[text] = f"ip_{len(self._aliases) + 1:04d}"
        return self._aliases[text]

    def text(self, value: Any) -> str:
        """Substitui os endereços IP de um texto pelos nomes anônimos já conhecidos."""
        return IP_PATTERN.sub(lambda match: self.alias(match.group(0)), str(value or ""))

    def context(self, context: dict[str, Any]) -> dict[str, Any]:
        """Aplica a troca de endereços aos campos do contexto usado no relatório."""
        return anonymize_context_for_report(context, self)


def anonymize_context_for_report(
    context: dict[str, Any],
    anonymizer: SecurityContextAnonymizer | None = None,
) -> dict[str, Any]:
    """Remove IPs reais de uma copia do contexto para relatorios."""

    anonymizer = anonymizer or SecurityContextAnonymizer()

    def anonymize_value(value: Any) -> Any:
        """Percorre textos e estruturas aninhadas substituindo os endereços encontrados."""
        if isinstance(value, str):
            return anonymizer.text(value)
        if isinstance(value, list):
            return [anonymize_value(item) for item in value]
        if isinstance(value, tuple):
            return [anonymize_value(item) for item in value]
        if isinstance(value, dict):
            return {key: anonymize_value(item) for key, item in value.items()}
        return value

    anonymized = {key: anonymize_value(value) for key, value in context.items()}
    for key in ("source_ip", "src_ip"):
        if anonymized.get(key):
            anonymized[key] = anonymizer.alias(context.get(key))
    return anonymized


__all__ = [
    "SecurityContextAnonymizer",
    "anonymize_context_for_report",
    "build_security_window_context",
    "classify_service_categories",
    "detect_context_hints",
    "summarize_destination_ips",
    "summarize_destination_ports",
    "summarize_pairs",
    "summarize_tcp_flags",
]
