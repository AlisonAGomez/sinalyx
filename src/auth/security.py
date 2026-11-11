"""Funções de seguranca para senhas e tokens de acesso do Sinalyx.

O módulo evita dependencias externas para manter compatibilidade com o
ambiente atual: senhas usam PBKDF2-HMAC-SHA256 e os tokens seguem o formato
JWT HS256 assinado com segredo configuravel por ambiente.
"""

from __future__ import annotations

import base64
import hashlib
import hmac
import json
import secrets
from datetime import datetime, timedelta, timezone
from typing import Any

from src.core.config import get_settings


PASSWORD_ITERATIONS = 260_000
TOKEN_ALGORITHM = "HS256"
TOKEN_TYPE = "JWT"
DEFAULT_ACCESS_TOKEN_MINUTES = 12 * 60
LOCAL_AUTH_SECRET = "sinalyx-local-dev-secret-change-me"
INSECURE_AUTH_SECRETS = {
    "",
    "sinalyx-dev-secret-change-me",
    LOCAL_AUTH_SECRET,
    "troque-este-segredo-em-producao",
}


def _b64url_encode(data: bytes) -> str:
    """Converte bytes para o formato de texto usado nas partes do token JWT."""
    return base64.urlsafe_b64encode(data).rstrip(b"=").decode("ascii")


def _b64url_decode(value: str) -> bytes:
    """Recupera os bytes de uma parte do token, completando o preenchimento Base64."""
    padding = "=" * (-len(value) % 4)
    return base64.urlsafe_b64decode(f"{value}{padding}".encode("ascii"))


def get_auth_secret() -> str:
    """Retorna o segredo usado para assinar tokens.

    Em local, ha um alternativa apenas para facilitar desenvolvimento controlado.
    Em demo/producao, SINALYX_AUTH_SECRET_KEY deve ser unico e forte.
    """
    settings = get_settings()
    secret = settings.auth_secret_key or LOCAL_AUTH_SECRET
    if settings.is_production_like:
        if (
            secret in INSECURE_AUTH_SECRETS
            or len(secret) < 32
            or len(set(secret)) < 12
            # Uma sequência repetida aparece dentro da própria duplicação sem as pontas.
            or secret in (secret + secret)[1:-1]
            or any(marcador in secret.lower() for marcador in ("change-me", "changeme", "troque-", "password"))
        ):
            raise RuntimeError(
                "Defina SINALYX_AUTH_SECRET_KEY com um valor forte "
                "para ambientes demo/producao."
            )
    return secret


def get_access_token_expire_minutes() -> int:
    """Lê a duração do token em minutos."""
    return get_settings().access_token_expire_minutes or DEFAULT_ACCESS_TOKEN_MINUTES


def hash_password(password: str) -> str:
    """
    Gera hash seguro de senha usando PBKDF2-HMAC-SHA256.
    """
    if not password:
        raise ValueError("A senha nao pode estar vazia.")

    salt = secrets.token_bytes(16)
    digest = hashlib.pbkdf2_hmac(
        "sha256",
        password.encode("utf-8"),
        salt,
        PASSWORD_ITERATIONS,
    )
    return "pbkdf2_sha256${iterations}${salt}${digest}".format(
        iterations=PASSWORD_ITERATIONS,
        salt=_b64url_encode(salt),
        digest=_b64url_encode(digest),
    )


def verify_password(password: str, password_hash: str | None) -> bool:
    """Verifica senha em tempo constante quando o hash está no formato esperado."""
    if not password or not password_hash:
        return False

    try:
        algorithm, iterations_raw, salt_raw, digest_raw = password_hash.split("$", 3)
    except ValueError:
        return False

    if algorithm != "pbkdf2_sha256":
        return False

    try:
        iterations = int(iterations_raw)
        salt = _b64url_decode(salt_raw)
        expected_digest = _b64url_decode(digest_raw)
    except Exception:
        return False

    candidate_digest = hashlib.pbkdf2_hmac(
        "sha256",
        password.encode("utf-8"),
        salt,
        iterations,
    )
    return hmac.compare_digest(candidate_digest, expected_digest)


def create_access_token(
    *,
    subject: str,
    email: str,
    role: str,
    expires_delta: timedelta | None = None,
) -> str:
    """
    Cria um token assinado no formato JWT HS256.
    """
    now = datetime.now(timezone.utc)
    expires_at = now + (
        expires_delta
        if expires_delta is not None
        else timedelta(minutes=get_access_token_expire_minutes())
    )
    header = {"alg": TOKEN_ALGORITHM, "typ": TOKEN_TYPE}
    payload = {
        "sub": str(subject),
        "email": email,
        "role": role,
        "iat": int(now.timestamp()),
        "exp": int(expires_at.timestamp()),
    }
    encoded_header = _b64url_encode(
        json.dumps(header, separators=(",", ":"), sort_keys=True).encode("utf-8")
    )
    encoded_payload = _b64url_encode(
        json.dumps(payload, separators=(",", ":"), sort_keys=True).encode("utf-8")
    )
    signing_input = f"{encoded_header}.{encoded_payload}".encode("ascii")
    signature = hmac.new(
        get_auth_secret().encode("utf-8"),
        signing_input,
        hashlib.sha256,
    ).digest()
    return f"{encoded_header}.{encoded_payload}.{_b64url_encode(signature)}"


def decode_access_token(token: str) -> dict[str, Any]:
    """
    Valida assinatura e expiracao de um token de acesso.
    """
    try:
        encoded_header, encoded_payload, encoded_signature = token.split(".", 2)
    except ValueError as exc:
        raise ValueError("Token malformado.") from exc

    signing_input = f"{encoded_header}.{encoded_payload}".encode("ascii")
    expected_signature = hmac.new(
        get_auth_secret().encode("utf-8"),
        signing_input,
        hashlib.sha256,
    ).digest()

    try:
        received_signature = _b64url_decode(encoded_signature)
    except Exception as exc:
        raise ValueError("Assinatura invalida.") from exc

    if not hmac.compare_digest(received_signature, expected_signature):
        raise ValueError("Assinatura invalida.")

    try:
        payload = json.loads(_b64url_decode(encoded_payload).decode("utf-8"))
    except Exception as exc:
        raise ValueError("Payload invalido.") from exc

    exp = payload.get("exp")
    if not isinstance(exp, int):
        raise ValueError("Token sem expiracao valida.")
    if datetime.now(timezone.utc).timestamp() >= exp:
        raise ValueError("Token expirado.")

    return payload
