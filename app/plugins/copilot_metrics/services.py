import json
import os
from typing import Optional

import httpx
from sqlalchemy.orm import Session

from .crud import create_or_update_account, save_metrics
from .utils import encrypt_token, decrypt_token
from app.db import SessionLocal


GITHUB_USER_URL = "https://api.github.com/user"
COPILOT_USER_URL = "https://api.github.com/copilot_internal/user"


class CopilotMetricsService:
    def __init__(self, db_factory) -> None:
        self._db_factory = db_factory

    def _client(self, proxy: Optional[str] = None) -> httpx.Client:
        proxies = {"all": proxy} if proxy else None
        return httpx.Client(timeout=20.0, proxies=proxies, headers={"Accept": "*/*"})

    def import_account(self, token: str, proxy: Optional[str] = None) -> int:
        secret_hex = os.getenv("COPILOT_METRICS__TOKEN_SECRET")
        if not secret_hex:
            raise RuntimeError("COPILOT_METRICS__TOKEN_SECRET not configured")

        ct_b64, nonce_b64, salt_b64 = encrypt_token(secret_hex, token)

        db = SessionLocal()
        try:
            with self._client(proxy) as client:
                # Fetch user info
                resp = client.get(
                    GITHUB_USER_URL,
                    headers={"authorization": f"token {token}", "user-agent": "Visual Studio Code (desktop)"},
                )
                resp.raise_for_status()
                user = resp.json()

            acc = create_or_update_account(
                db,
                login=user.get("login"),
                github_user_id=int(user.get("id")),
                node_id=user.get("node_id"),
                avatar_url=user.get("avatar_url"),
                token_ciphertext=ct_b64,
                token_nonce=nonce_b64,
                token_salt=salt_b64,
            )
            return acc.id
        finally:
            db.close()

    def fetch_metrics(self, account_id: int, proxy: Optional[str] = None) -> int:
        secret_hex = os.getenv("COPILOT_METRICS__TOKEN_SECRET")
        if not secret_hex:
            raise RuntimeError("COPILOT_METRICS__TOKEN_SECRET not configured")

        db = SessionLocal()
        try:
            from .crud import get_account

            acc = get_account(db, account_id)
            if not acc:
                raise RuntimeError("Account not found")

            token = decrypt_token(secret_hex, acc.token_ciphertext, acc.token_nonce, acc.token_salt)

            with self._client(proxy) as client:
                resp = client.get(
                    COPILOT_USER_URL,
                    headers={"authorization": f"Bearer {token}", "user-agent": "Mozilla/5.0 (Macintosh; Intel Mac OS X)"},
                )
                resp.raise_for_status()
                data = resp.json()

            m = save_metrics(db, account_id=acc.id, payload_json=json.dumps(data))
            return m.id
        finally:
            db.close()