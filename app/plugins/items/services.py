from sqlalchemy.orm import Session

from .models import PluginItem


def count_items(db: Session) -> int:
    return db.query(PluginItem).count()


class ItemsService:
    def __init__(self, db_factory):
        self._db_factory = db_factory

    def create_default(self, name: str) -> int:
        """Example service: create a default item and return its id."""
        from .crud import create_item
        from .schemas import PluginItemCreate

        with self._db_factory() as db:
            obj = create_item(db, PluginItemCreate(name=name))
            return obj.id