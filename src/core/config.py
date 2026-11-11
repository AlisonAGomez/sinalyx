"""Configuração central do Sinalyx.

Este módulo concentra leitura de variaveis de ambiente e defaults locais.
Ele mantém a configuração simples para o TCC e evita espalhar senhas,
URLs e flags operacionais por varios arquivos.
"""

from __future__ import annotations

import os
from dataclasses import dataclass
from functools import lru_cache
from pathlib import Path
from urllib.parse import unquote, urlsplit


try:
    from dotenv import load_dotenv
except Exception:
    load_dotenv = None

if load_dotenv is not None:
    load_dotenv(dotenv_path=Path(__file__).resolve().parents[2] / ".env", override=False)


TRUE_VALUES = {"1", "true", "yes", "on", "sim"}
PRODUCTION_ENVIRONMENTS = {"demo", "production", "producao", "prod", "shared", "compartilhado", "staging"}
LOCAL_ENVIRONMENTS = {"local", "dev", "development", "test"}
DEFAULT_DATABASE_URL = "postgresql://sinalyx:sinalyx@localhost:5432/sinalyx"
DEFAULT_CORS_ORIGINS = [
    "http://localhost:5173",
    "http://127.0.0.1:5173",
    "http://localhost:3000",
    "http://127.0.0.1:3000",
]


def _env_bool(name: str, default: bool) -> bool:
    """Lê uma opção de ambiente como sim ou não, usando o padrão quando ela não existe."""
    raw = os.getenv(name)
    if raw is None:
        return default
    return raw.strip().lower() in TRUE_VALUES


def _env_int(name: str, default: int, *, minimum: int | None = None) -> int:
    """Lê um número inteiro do ambiente e usa o padrão quando o valor não é válido."""
    raw = os.getenv(name, "").strip()
    if not raw:
        return default
    try:
        value = int(raw)
    except ValueError:
        return default
    if minimum is not None:
        return max(minimum, value)
    return value


def _env_list(name: str, default: list[str]) -> list[str]:
    """Lê itens separados por vírgula do ambiente, sem compartilhar a lista padrão."""
    raw = os.getenv(name, "").strip()
    if not raw:
        return default.copy()
    values = [item.strip() for item in raw.split(",") if item.strip()]
    return values or default.copy()


@dataclass(frozen=True)
class Settings:
    """Configurações lidas do ambiente; valores explícitos têm precedência sobre o arquivo local."""
    environment: str
    cors_origins: list[str]
    database_enabled: bool
    database_url: str
    auth_secret_key: str
    access_token_expire_minutes: int
    runtime_profile: str
    version: str
    admin_name: str
    admin_email: str
    admin_password: str
    super_admin_email: str
    pfsense_host: str
    pfsense_ssh_port: int
    pfsense_user: str
    pfsense_password: str
    pfsense_key_path: str
    pfsense_remote_log_path: str
    pfsense_local_log_path: str
    pfsense_collector_state_path: str
    pfsense_parser_state_path: str
    pfsense_connect_timeout: int
    pfsense_allow_unknown_host: bool
    limite_upload_bytes: int = 50 * 1024 * 1024
    pfsense_known_hosts_path: str = ""
    login_max_tentativas: int = 10
    login_janela_segundos: int = 60
    login_max_clientes: int = 4096
    pfsense_worker_interval_seconds: int = 5
    pfsense_worker_autostart: bool = False
    live_run_retention_enabled: bool = True
    live_run_retention_max_count: int = 2000
    live_run_retention_max_age_hours: int = 24

    @property
    def is_production_like(self) -> bool:
        """Indica se o ambiente exige os cuidados aplicados à instalação de produção."""
        return self.environment.strip().lower() in PRODUCTION_ENVIRONMENTS


@lru_cache(maxsize=1)
def get_settings() -> Settings:
    """Retorna as configurações efetivas do processo."""
    environment = os.getenv("SINALYX_ENV", "local").strip().lower() or "local"
    if environment not in PRODUCTION_ENVIRONMENTS | LOCAL_ENVIRONMENTS:
        raise ValueError("SINALYX_ENV invalido. Use local, demo ou production.")
    database_enabled = _env_bool("DATABASE_ENABLED", True)
    database_url_configurada = os.getenv("DATABASE_URL", "").strip()
    database_url = database_url_configurada or DEFAULT_DATABASE_URL
    if environment in PRODUCTION_ENVIRONMENTS and database_enabled:
        try:
            partes_url = urlsplit(database_url)
            senha_banco = unquote(partes_url.password or "")
        except ValueError as exc:
            raise ValueError("DATABASE_URL invalida para ambiente compartilhado.") from exc
        if (
            not database_url_configurada
            or not partes_url.scheme.startswith("postgresql")
            or senha_banco in {"", "sinalyx"}
        ):
            raise ValueError("Configure DATABASE_URL PostgreSQL com credenciais proprias em demo/producao.")
        if os.getenv("POSTGRES_PASSWORD", "").strip() == "sinalyx":
            raise ValueError("Configure POSTGRES_PASSWORD proprio em demo/producao.")
    admin_email = os.getenv("SINALYX_ADMIN_EMAIL", "admin@sinalyx.local").strip()
    return Settings(
        pfsense_worker_interval_seconds=_env_int("SINALYX_PFSENSE_WORKER_INTERVAL_SECONDS", 5, minimum=1),
        pfsense_worker_autostart=_env_bool("SINALYX_PFSENSE_WORKER_AUTOSTART", False),
        live_run_retention_enabled=_env_bool("SINALYX_LIVE_RUN_RETENTION_ENABLED", True),
        live_run_retention_max_count=_env_int("SINALYX_LIVE_RUN_RETENTION_MAX_COUNT", 2000, minimum=0),
        live_run_retention_max_age_hours=_env_int("SINALYX_LIVE_RUN_RETENTION_MAX_AGE_HOURS", 24, minimum=0),
        environment=environment,
        limite_upload_bytes=_env_int("SINALYX_LIMITE_UPLOAD_BYTES", 50 * 1024 * 1024, minimum=1),
        login_max_tentativas=_env_int("SINALYX_LOGIN_MAX_TENTATIVAS", 10, minimum=1),
        login_janela_segundos=_env_int("SINALYX_LOGIN_JANELA_SEGUNDOS", 60, minimum=1),
        login_max_clientes=_env_int("SINALYX_LOGIN_MAX_CLIENTES", 4096, minimum=1),
        pfsense_known_hosts_path=os.getenv("SINALYX_PFSENSE_KNOWN_HOSTS_PATH", "").strip(),
        cors_origins=_env_list("SINALYX_CORS_ORIGINS", DEFAULT_CORS_ORIGINS),
        database_enabled=database_enabled,
        database_url=database_url,
        auth_secret_key=os.getenv("SINALYX_AUTH_SECRET_KEY", "").strip(),
        access_token_expire_minutes=_env_int(
            "SINALYX_ACCESS_TOKEN_EXPIRE_MINUTES",
            12 * 60,
            minimum=5,
        ),
        runtime_profile=os.getenv("SINALYX_RUNTIME_PROFILE", "").strip(),
        version=os.getenv("SINALYX_VERSION", "v0.1.1-tcc").strip() or "v0.1.1-tcc",
        admin_name=os.getenv("SINALYX_ADMIN_NAME", "Administrador Sinalyx").strip(),
        admin_email=admin_email,
        admin_password=os.getenv("SINALYX_ADMIN_PASSWORD", ""),
        super_admin_email=(
            os.getenv("SINALYX_SUPER_ADMIN_EMAIL", "").strip()
            or admin_email
            or "admin@sinalyx.local"
        ),
        pfsense_host=os.getenv("SINALYX_PFSENSE_HOST", "").strip(),
        pfsense_ssh_port=_env_int("SINALYX_PFSENSE_SSH_PORT", 22, minimum=1),
        pfsense_user=os.getenv("SINALYX_PFSENSE_USER", "").strip(),
        pfsense_password=os.getenv("SINALYX_PFSENSE_PASSWORD", ""),
        pfsense_key_path=os.getenv("SINALYX_PFSENSE_KEY_PATH", "").strip(),
        pfsense_remote_log_path=os.getenv(
            "SINALYX_PFSENSE_REMOTE_LOG_PATH",
            "/var/log/filter.log",
        ).strip(),
        pfsense_local_log_path=os.getenv(
            "SINALYX_PFSENSE_LOCAL_LOG_PATH",
            "",
        ).strip(),
        pfsense_collector_state_path=os.getenv(
            "SINALYX_PFSENSE_COLLECTOR_STATE_PATH",
            "",
        ).strip(),
        pfsense_parser_state_path=os.getenv(
            "SINALYX_PFSENSE_PARSER_STATE_PATH",
            "",
        ).strip(),
        pfsense_connect_timeout=_env_int(
            "SINALYX_PFSENSE_CONNECT_TIMEOUT",
            15,
            minimum=1,
        ),
        pfsense_allow_unknown_host=_env_bool(
            "SINALYX_PFSENSE_ALLOW_UNKNOWN_HOST",
            False,
        ),
    )
