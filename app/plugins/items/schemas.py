from datetime import datetime
from typing import Optional

from pydantic import BaseModel


class PluginItemBase(BaseModel):
    name: str
    description: Optional[str] = None


class PluginItemCreate(PluginItemBase):
    pass


class PluginItemUpdate(BaseModel):
    name: Optional[str] = None
    description: Optional[str] = None


class PluginItemRead(PluginItemBase):
    id: int
    created_at: datetime

    class Config:
        from_attributes = True