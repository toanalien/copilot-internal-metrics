from sqlalchemy import Column, Integer, String, Text, DateTime, ForeignKey, func
from sqlalchemy.orm import relationship

from app.models import Base


class GithubAccount(Base):
    __tablename__ = "copilot_github_accounts"

    id = Column(Integer, primary_key=True, index=True)
    login = Column(String(255), nullable=False, index=True)
    github_user_id = Column(Integer, nullable=False, index=True)
    node_id = Column(String(255), nullable=True)
    avatar_url = Column(Text, nullable=True)

    # Encrypted token storage (AES-GCM)
    token_ciphertext = Column(Text, nullable=False)
    token_nonce = Column(String(255), nullable=False)
    token_salt = Column(String(255), nullable=False)

    created_at = Column(DateTime(timezone=True), server_default=func.now(), nullable=False)
    updated_at = Column(DateTime(timezone=True), server_default=func.now(), onupdate=func.now(), nullable=False)

    metrics = relationship("CopilotMetrics", back_populates="account", cascade="all, delete-orphan")


class CopilotMetrics(Base):
    __tablename__ = "copilot_metrics"

    id = Column(Integer, primary_key=True, index=True)
    account_id = Column(Integer, ForeignKey("copilot_github_accounts.id", ondelete="CASCADE"), nullable=False, index=True)
    fetched_at = Column(DateTime(timezone=True), server_default=func.now(), nullable=False)

    # Raw metrics payload as JSON string (for flexibility)
    payload = Column(Text, nullable=False)

    account = relationship("GithubAccount", back_populates="metrics")