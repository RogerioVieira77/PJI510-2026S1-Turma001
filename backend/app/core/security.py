"""Utilitários de segurança — hashing de senhas e JWT."""
from __future__ import annotations

from datetime import datetime, timedelta, timezone

import bcrypt
from jose import JWTError, jwt

from app.config import get_settings

settings = get_settings()

# ── Bcrypt ──────────────────────────────────────────────────────────────────

def hash_password(plain: str) -> str:
    """Retorna hash bcrypt (rounds=12)."""
    return bcrypt.hashpw(plain.encode(), bcrypt.gensalt(rounds=12)).decode()


def verify_password(plain: str, hashed: str) -> bool:
    return bcrypt.checkpw(plain.encode(), hashed.encode())


# ── JWT ─────────────────────────────────────────────────────────────────────

_ACCESS_TYPE = "access"
_REFRESH_TYPE = "refresh"


def _create_token(subject: str, token_type: str, expires_delta: timedelta) -> str:
    now = datetime.now(tz=timezone.utc)
    payload = {
        "sub": subject,
        "type": token_type,
        "iat": now,
        "exp": now + expires_delta,
    }
    return jwt.encode(payload, settings.SECRET_KEY, algorithm=settings.ALGORITHM)


def create_access_token(subject: str) -> str:
    return _create_token(
        subject,
        _ACCESS_TYPE,
        timedelta(minutes=settings.ACCESS_TOKEN_EXPIRE_MINUTES),
    )


def create_refresh_token(subject: str) -> str:
    return _create_token(
        subject,
        _REFRESH_TYPE,
        timedelta(days=settings.REFRESH_TOKEN_EXPIRE_DAYS),
    )


def decode_token(token: str, expected_type: str = _ACCESS_TYPE) -> str:
    """Decodifica e valida JWT. Retorna `sub`. Lança ValueError se inválido."""
    try:
        payload = jwt.decode(token, settings.SECRET_KEY, algorithms=[settings.ALGORITHM])
    except JWTError as exc:
        raise ValueError("Token inválido ou expirado") from exc

    if payload.get("type") != expected_type:
        raise ValueError(f"Tipo de token incorreto: esperado '{expected_type}'")

    sub: str | None = payload.get("sub")
    if not sub:
        raise ValueError("Token sem subject")
    return sub
