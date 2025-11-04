from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session

from app.core.interfaces import ModuleInterface, ServiceRegistry
from app import models


class Plugin(ModuleInterface):
    name = "analytics"
    version = "1.0.0"

    def __init__(self) -> None:
        self._db_dep = None
        self.router = APIRouter()

    def init(self, app, registry: ServiceRegistry) -> None:
        self._db_dep = registry.get_service("db_session_dep")

        @self.router.get("/count")
        def count_items(db: Session = Depends(self._db_dep)):
            # Count items from the items table
            return {"items_count": db.query(models.Item).count()}

    def start(self) -> None:
        pass

    def stop(self) -> None:
        pass

    def get_router(self) -> APIRouter:
        return self.router