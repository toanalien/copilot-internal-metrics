from sqlalchemy import Column, Integer, String, Text, DateTime, func

from app.models import Base


class PluginItem(Base):
    __tablename__ = "plugin_items"

    id = Column(Integer, primary_key=True, index=True)
    name = Column(String(255), nullable=False)
    description = Column(Text, nullable=True)
    created_at = Column(DateTime(timezone=True), server_default=func.now(), nullable=False)