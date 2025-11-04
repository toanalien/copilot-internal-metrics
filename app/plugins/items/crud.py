from typing import List, Optional

from sqlalchemy.orm import Session

from .models import PluginItem
from .schemas import PluginItemCreate, PluginItemUpdate


def create_item(db: Session, item: PluginItemCreate) -> PluginItem:
    obj = PluginItem(name=item.name, description=item.description)
    db.add(obj)
    db.commit()
    db.refresh(obj)
    return obj


def get_items(db: Session, skip: int = 0, limit: int = 100) -> List[PluginItem]:
    return db.query(PluginItem).offset(skip).limit(limit).all()


def get_item(db: Session, item_id: int) -> Optional[PluginItem]:
    return db.query(PluginItem).filter(PluginItem.id == item_id).first()


def update_item(db: Session, item_id: int, item: PluginItemUpdate) -> Optional[PluginItem]:
    obj = db.query(PluginItem).filter(PluginItem.id == item_id).first()
    if not obj:
        return None
    if item.name is not None:
        obj.name = item.name
    if item.description is not None:
        obj.description = item.description
    db.commit()
    db.refresh(obj)
    return obj


def delete_item(db: Session, item_id: int) -> bool:
    obj = db.query(PluginItem).filter(PluginItem.id == item_id).first()
    if not obj:
        return False
    db.delete(obj)
    db.commit()
    return True