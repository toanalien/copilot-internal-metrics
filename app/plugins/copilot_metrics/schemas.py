from datetime import datetime
from typing import Optional

from pydantic import BaseModel


class ImportAccountRequest(BaseModel):
    token: str
    proxy: Optional[str] = None


class GithubAccountRead(BaseModel):
    id: int
    login: str
    github_user_id: int
    node_id: Optional[str] = None
    avatar_url: Optional[str] = None
    created_at: datetime
    updated_at: datetime

    class Config:
        from_attributes = True


class CopilotMetricsRead(BaseModel):
    id: int
    account_id: int
    fetched_at: datetime
    payload: dict

    class Config:
        from_attributes = True