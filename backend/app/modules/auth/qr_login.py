"""ログインQRペイロードの生成・解析。パスワードはQRに含めない。"""
from __future__ import annotations

import json
import secrets

LOGIN_QR_PREFIX = "SEMAP-LOGIN:v1:"
QR_TOKEN_HEX_BYTES = 24


def new_qr_login_token() -> str:
    return secrets.token_hex(QR_TOKEN_HEX_BYTES)


def encode_login_qr_payload(username: str, token: str) -> str:
    return f"{LOGIN_QR_PREFIX}{username}:{token}"


def parse_login_qr_code(code: str) -> tuple[str, str] | None:
    """QR文字列から (username, token) を取り出す。無効なら None。"""
    raw = (code or "").strip()
    if not raw:
        return None
    if raw.startswith(LOGIN_QR_PREFIX):
        rest = raw[len(LOGIN_QR_PREFIX) :]
        sep = rest.rfind(":")
        if sep <= 0 or sep >= len(rest) - 1:
            return None
        username = rest[:sep].strip()
        token = rest[sep + 1 :].strip()
        if username and token:
            return username, token
        return None
    if raw.startswith("{"):
        try:
            data = json.loads(raw)
        except json.JSONDecodeError:
            return None
        if not isinstance(data, dict):
            return None
        username = str(data.get("u") or data.get("username") or "").strip()
        token = str(data.get("t") or data.get("token") or "").strip()
        if username and token:
            return username, token
    return None
