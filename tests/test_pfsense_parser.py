"""Testes da leitura dos campos de logs pfSense, incluindo linhas inválidas e protocolos diferentes."""

from src.parsers.pfsense_parser import PfSenseLogParser

PAYLOAD = (
    "66,,,12004,em0,match,block,in,4,0x0,,128,32770,0,none,17,udp,78,"
    "192.0.2.10,198.51.100.20,137,137,58"
)


def test_rfc3164_filterlog_with_hostname_preserves_existing_behavior():
    parser = PfSenseLogParser(default_year=2026)
    event = parser.parse_line(
        f"Aug 28 13:22:49 pfSense filterlog[20915]: {PAYLOAD}"
    )

    assert event.parsed_successfully is True
    assert event.timestamp == "2026-08-28T13:22:49"
    assert event.hostname == "pfSense"
    assert event.process == "filterlog[20915]"
    assert event.is_syslog is True
    assert event.is_filterlog is True


def test_local_filterlog_without_hostname_keeps_timestamp():
    parser = PfSenseLogParser(default_year=2026)
    event = parser.parse_line(
        f"Aug 28 13:22:49  filterlog[20915]: {PAYLOAD}"
    )

    assert event.parsed_successfully is True
    assert event.timestamp == "2026-08-28T13:22:49"
    assert event.hostname is None
    assert event.process == "filterlog[20915]"
    assert event.is_syslog is True
    assert event.is_filterlog is True
