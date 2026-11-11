"""Coletor SSH/SFTP do filter.log do pfSense para o fluxo live do Sinalyx.

Entrada:
- Credenciais e caminhos via variaveis de ambiente.

Saída:
- Arquivo local em data/runtime/pfsense/live/filter.log.
- Estado da última coleta em collector_state.json.

Observacao:
- O coletor usa SFTP por Paramiko para evitar comandos externos de SCP.
"""

from __future__ import annotations

import json
import logging
from dataclasses import dataclass
from datetime import datetime
from pathlib import Path
from typing import Any

from src.collectors.file_generation import identificar_geracao
from src.core.config import get_settings
from src.core.atomic_json import write_json_atomic
from src.core.paths import BASE_DIR, DATA_DIR

DEFAULT_REMOTE_LOG_PATH = "/var/log/filter.log"
DEFAULT_LIVE_DIR = DATA_DIR / "runtime" / "pfsense" / "live"
DEFAULT_LOCAL_LOG_PATH = DEFAULT_LIVE_DIR / "filter.log"
DEFAULT_COLLECTOR_STATE_PATH = DEFAULT_LIVE_DIR / "collector_state.json"
logger = logging.getLogger("sinalyx.coletor")


def _now_iso() -> str:
    """Retorna data e hora local com timezone para auditoria de estado."""
    return datetime.now().astimezone().isoformat(timespec="seconds")


def _resolve_project_path(value: str | None, default: Path) -> Path:
    """
    Resolve caminhos relativos a partir da raiz do projeto.
    """
    if value is None or not str(value).strip():
        return default

    path = Path(value).expanduser()
    if path.is_absolute():
        return path
    return BASE_DIR / path


def _read_json(path: Path) -> dict[str, Any]:
    """Lê um JSON quando existir; caso contrario, devolve dicionário vazio."""
    if not path.exists():
        return {}
    try:
        with path.open("r", encoding="utf-8") as file:
            payload = json.load(file)
        return payload if isinstance(payload, dict) else {}
    except Exception:
        return {}


def _write_json(path: Path, payload: dict[str, Any]) -> None:
    """Salva estado JSON com indentacao estavel."""
    write_json_atomic(path, payload)


@dataclass(frozen=True)
class PfSenseCollectorConfig:
    """Configuração do coletor de logs pfSense.

    Parâmetros:
        host: Hostname ou IP do pfSense.
        port: Porta SSH.
        username: Usuário SSH.
        password: Senha SSH, quando usada.
        key_path: Caminho da chave privada, quando usada.
        remote_path: Caminho remoto do filter.log.
        local_path: Caminho local de destino.
        state_path: Caminho do estado JSON da coleta.
        connect_timeout: Timeout em segundos para conexao/autenticacao.
        allow_unknown_host: Opção legada; true é rejeitado por segurança.
        known_hosts_path: Arquivo de chaves de host verificadas pelo operador.
    """

    host: str | None
    port: int
    username: str | None
    password: str | None
    key_path: Path | None
    remote_path: str
    local_path: Path
    state_path: Path
    connect_timeout: int
    allow_unknown_host: bool = False
    known_hosts_path: Path | None = None

    @classmethod
    def from_env(cls) -> "PfSenseCollectorConfig":
        """Monta a configuração do coletor a partir de variaveis de ambiente."""
        settings = get_settings()
        key_value = settings.pfsense_key_path
        key_path = _resolve_project_path(key_value, BASE_DIR / key_value) if key_value else None

        local_path = _resolve_project_path(
            settings.pfsense_local_log_path,
            DEFAULT_LOCAL_LOG_PATH,
        )
        state_path = _resolve_project_path(
            settings.pfsense_collector_state_path,
            local_path.parent / "collector_state.json",
        )

        return cls(
            host=settings.pfsense_host or None,
            port=settings.pfsense_ssh_port,
            username=settings.pfsense_user or None,
            password=settings.pfsense_password or None,
            key_path=key_path,
            remote_path=settings.pfsense_remote_log_path or DEFAULT_REMOTE_LOG_PATH,
            local_path=local_path,
            state_path=state_path,
            connect_timeout=settings.pfsense_connect_timeout,
            allow_unknown_host=settings.pfsense_allow_unknown_host,
            known_hosts_path=(
                _resolve_project_path(settings.pfsense_known_hosts_path, Path.home() / ".ssh" / "known_hosts")
                if settings.pfsense_known_hosts_path else None
            ),
        )

    def missing_settings(self) -> list[str]:
        """Lista configurações obrigatorias ausentes."""
        missing: list[str] = []
        if not self.host:
            missing.append("SINALYX_PFSENSE_HOST")
        if not self.username:
            missing.append("SINALYX_PFSENSE_USER")
        if not self.password and self.key_path is None:
            missing.append("SINALYX_PFSENSE_PASSWORD ou SINALYX_PFSENSE_KEY_PATH")
        if self.key_path is not None and not self.key_path.exists():
            missing.append("SINALYX_PFSENSE_KEY_PATH existente")
        if self.allow_unknown_host:
            missing.append("SINALYX_PFSENSE_ALLOW_UNKNOWN_HOST deve ser false")
        if self.known_hosts_path is not None and not self.known_hosts_path.is_file():
            missing.append("SINALYX_PFSENSE_KNOWN_HOSTS_PATH deve apontar para arquivo existente")
        return missing


def read_collector_state(
    config: PfSenseCollectorConfig | None = None,
) -> dict[str, Any]:
    """
    Carrega o estado atual do coletor.
    """
    config = config or PfSenseCollectorConfig.from_env()
    state = _read_json(config.state_path)
    state.setdefault("remote_path", config.remote_path)
    state.setdefault("local_path", str(config.local_path))
    state.setdefault("state_path", str(config.state_path))
    return state


def collect_filter_log(
    config: PfSenseCollectorConfig | None = None,
) -> dict[str, Any]:
    """Copia o filter.log remoto do pfSense para o ambiente de execução local do Sinalyx.

    Retorno:
        Dicionário com status, caminhos, tamanho coletado e possível erro.
    """
    config = config or PfSenseCollectorConfig.from_env()
    assinatura_anterior = _read_json(config.state_path).get("generation_signature")
    now = _now_iso()
    base_state: dict[str, Any] = {
        "generation_signature": assinatura_anterior,
        "last_fetch_at": now,
        "remote_path": config.remote_path,
        "local_path": str(config.local_path),
        "state_path": str(config.state_path),
        "host": config.host,
        "port": int(config.port),
        "last_fetch_status": "error",
        "file_size": None,
        "remote_file_size": None,
        "error": None,
        "error_type": None,
    }

    missing = config.missing_settings()
    if missing:
        base_state.update(
            {
                "error_type": "configuration_error",
                "error": "Configuracao incompleta do coletor pfSense.",
                "missing_settings": missing,
            }
        )
        _write_json(config.state_path, base_state)
        return base_state

    try:
        import paramiko
    except Exception as exc:
        logger.error("Falha ao carregar dependencia SSH; tipo=%s", type(exc).__name__)
        base_state.update(
            {
                "error_type": "dependency_missing",
                "error": (
                    "A dependencia paramiko nao esta disponivel. "
                    "Instale requirements.txt."
                ),
            }
        )
        _write_json(config.state_path, base_state)
        return base_state

    ssh_client = None
    sftp_client = None
    temp_path = config.local_path.with_name(f"{config.local_path.name}.tmp")

    try:
        config.local_path.parent.mkdir(parents=True, exist_ok=True)

        ssh_client = paramiko.SSHClient()
        if config.known_hosts_path is not None:
            ssh_client.load_host_keys(str(config.known_hosts_path))
            if not ssh_client.get_host_keys():
                raise ValueError("O arquivo known_hosts nao contem chaves validas.")
        else:
            ssh_client.load_system_host_keys()
        ssh_client.set_missing_host_key_policy(paramiko.RejectPolicy())

        ssh_client.connect(
            hostname=str(config.host),
            port=int(config.port),
            username=str(config.username),
            password=config.password,
            key_filename=str(config.key_path) if config.key_path is not None else None,
            timeout=int(config.connect_timeout),
            banner_timeout=int(config.connect_timeout),
            auth_timeout=int(config.connect_timeout),
        )

        sftp_client = ssh_client.open_sftp()
        remote_attrs = sftp_client.stat(config.remote_path)
        remote_size = int(getattr(remote_attrs, "st_size", 0) or 0)
        sftp_client.get(config.remote_path, str(temp_path))
        assinatura = identificar_geracao(temp_path)
        temp_path.replace(config.local_path)

        local_size = int(config.local_path.stat().st_size)
        base_state.update(
            {
                "generation_signature": assinatura,
                "last_fetch_status": "success",
                "file_size": local_size,
                "remote_file_size": remote_size,
                "error": None,
                "error_type": None,
            }
        )
    except FileNotFoundError as exc:
        logger.error("Falha em arquivo da coleta SSH; tipo=%s", type(exc).__name__)
        base_state.update(
            {
                "error_type": "file_not_found",
                "error": "Nao foi possivel acessar um arquivo necessario para a coleta.",
            }
        )
    except Exception as exc:  # pragma: no cover - depende de rede externa
        logger.error("Falha na coleta SSH; tipo=%s", type(exc).__name__)
        base_state.update(
            {
                "error_type": exc.__class__.__name__,
                "error": "Nao foi possivel concluir a coleta SSH. Verifique a configuracao e a identidade do servidor.",
            }
        )
    finally:
        try:
            if sftp_client is not None:
                sftp_client.close()
        finally:
            if ssh_client is not None:
                ssh_client.close()
        if temp_path.exists() and base_state["last_fetch_status"] != "success":
            try:
                temp_path.unlink()
            except OSError:
                pass

    _write_json(config.state_path, base_state)
    return base_state
