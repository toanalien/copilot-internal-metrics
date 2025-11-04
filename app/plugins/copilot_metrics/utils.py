import base64
import os
from typing import Optional

from argon2.low_level import Type, hash_secret_raw
from cryptography.hazmat.primitives.ciphers.aead import AESGCM


def _get_secret_bytes(secret_hex: Optional[str]) -> bytes:
    if not secret_hex:
        raise RuntimeError("COPILOT_METRICS__TOKEN_SECRET not set in environment")
    try:
        return bytes.fromhex(secret_hex)
    except ValueError as exc:
        raise RuntimeError("COPILOT_METRICS__TOKEN_SECRET must be hex string (openssl rand -hex 32)") from exc


def derive_key(secret_hex: str, salt: bytes) -> bytes:
    secret = _get_secret_bytes(secret_hex)
    # Derive 32-byte key using Argon2id
    key = hash_secret_raw(
        secret=secret,
        salt=salt,
        time_cost=2,
        memory_cost=102400,
        parallelism=8,
        hash_len=32,
        type=Type.ID,
    )
    return key


def encrypt_token(secret_hex: str, token: str) -> tuple[str, str, str]:
    """Encrypt token using AES-GCM with key derived by Argon2id.

    Returns (ciphertext_b64, nonce_b64, salt_b64)
    """
    salt = os.urandom(16)
    key = derive_key(secret_hex, salt)
    nonce = os.urandom(12)
    aesgcm = AESGCM(key)
    ct = aesgcm.encrypt(nonce, token.encode("utf-8"), None)
    return base64.b64encode(ct).decode(), base64.b64encode(nonce).decode(), base64.b64encode(salt).decode()


def decrypt_token(secret_hex: str, ciphertext_b64: str, nonce_b64: str, salt_b64: str) -> str:
    salt = base64.b64decode(salt_b64)
    key = derive_key(secret_hex, salt)
    nonce = base64.b64decode(nonce_b64)
    ct = base64.b64decode(ciphertext_b64)
    token = AESGCM(key).decrypt(nonce, ct, None)
    return token.decode("utf-8")