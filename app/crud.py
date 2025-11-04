from typing import List, Optional

from sqlalchemy.orm import Session

from . import models, schemas


def create_item(db: Session, item: schemas.ItemCreate) -> models.Item:
    db_item = models.Item(name=item.name, description=item.description)
    db.add(db_item)
    db.commit()
    db.refresh(db_item)
    return db_item


def get_item(db: Session, item_id: int) -> Optional[models.Item]:
    return db.query(models.Item).filter(models.Item.id == item_id).first()


def get_items(db: Session, skip: int = 0, limit: int = 100) -> List[models.Item]:
    return db.query(models.Item).offset(skip).limit(limit).all()


def update_item(db: Session, item_id: int, item: schemas.ItemUpdate) -> Optional[models.Item]:
    db_item = get_item(db, item_id)
    if not db_item:
        return None
    if item.name is not None:
        db_item.name = item.name
    if item.description is not None:
        db_item.description = item.description
    db.commit()
    db.refresh(db_item)
    return db_item


def delete_item(db: Session, item_id: int) -> bool:
    db_item = get_item(db, item_id)
    if not db_item:
        return False
    db.delete(db_item)
    db.commit()
    return True