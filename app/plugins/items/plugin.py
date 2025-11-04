from fastapi import APIRouter

from app.core.interfaces import ModuleInterface, ServiceRegistry, MiddlewareDef
from app.db import engine
from app.models import Base

from .middleware import ItemsMiddleware
from .routes import build_router
from .services import count_items, ItemsService


class Plugin(ModuleInterface):
    name = "items"
    version = "1.0.0"

    def __init__(self) -> None:
        self.router: APIRouter | None = None
        self._db_dep = None
        self._services = {}

    def init(self, app, registry: ServiceRegistry) -> None:
        # Ensure plugin models are imported so SQLAlchemy metadata is aware
        from . import models  # noqa: F401

        # Get DB dependency from registry
        self._db_dep = registry.get_service("db_session_dep")
        self.router = build_router(self._db_dep)

        # Initialize services provided to the registry
        self._services = {
            "plugin_items.count": count_items,
            "plugin_items.service": ItemsService(registry.get_service("db_session_dep")),
        }

    def start(self) -> None:
        # Create tables once the application has started and DB is ready
        Base.metadata.create_all(bind=engine)

    def stop(self) -> None:
        pass

    def get_router(self) -> APIRouter:
        return self.router  # type: ignore[return-value]

    def provides(self):
        return self._services

    def middlewares(self):
        return [MiddlewareDef(cls=ItemsMiddleware)]