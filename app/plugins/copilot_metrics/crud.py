from typing import List, Optional

from sqlalchemy.orm import Session

from .models import GithubAccount, CopilotMetrics


def create_or_update_account(
    db: Session,
    *,
    login: str,
    github_user_id: int,
    node_id: str | None,
    avatar_url: str | None,
    token_ciphertext: str,
    token_nonce: str,
    token_salt: str,
) -> GithubAccount:
    acc = db.query(GithubAccount).filter(GithubAccount.github_user_id == github_user_id).first()
    if acc:
        acc.login = login
        acc.node_id = node_id
        acc.avatar_url = avatar_url
        acc.token_ciphertext = token_ciphertext
        acc.token_nonce = token_nonce
        acc.token_salt = token_salt
    else:
        acc = GithubAccount(
            login=login,
            github_user_id=github_user_id,
            node_id=node_id,
            avatar_url=avatar_url,
            token_ciphertext=token_ciphertext,
            token_nonce=token_nonce,
            token_salt=token_salt,
        )
        db.add(acc)
    db.commit()
    db.refresh(acc)
    return acc


def list_accounts(db: Session) -> List[GithubAccount]:
    return db.query(GithubAccount).order_by(GithubAccount.id.desc()).all()


def get_account(db: Session, account_id: int) -> Optional[GithubAccount]:
    return db.query(GithubAccount).filter(GithubAccount.id == account_id).first()


def save_metrics(db: Session, account_id: int, payload_json: str) -> CopilotMetrics:
    m = CopilotMetrics(account_id=account_id, payload=payload_json)
    db.add(m)
    db.commit()
    db.refresh(m)
    return m


def latest_metrics_for_account(db: Session, account_id: int) -> Optional[CopilotMetrics]:
    return (
        db.query(CopilotMetrics)
        .filter(CopilotMetrics.account_id == account_id)
        .order_by(CopilotMetrics.id.desc())
        .first()
    )


def latest_metrics_all(db: Session) -> List[CopilotMetrics]:
    # Simple approach: latest per account by max(id)
    # Depending on DB, we could do window func; here fetch latest by grouping in Python
    all_metrics = db.query(CopilotMetrics).order_by(CopilotMetrics.account_id, CopilotMetrics.id.desc()).all()
    latest_by_account = {}
    for m in all_metrics:
        if m.account_id not in latest_by_account:
            latest_by_account[m.account_id] = m
    return list(latest_by_account.values())