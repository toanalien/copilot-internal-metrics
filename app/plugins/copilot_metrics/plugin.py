from fastapi import APIRouter

from app.core.interfaces import ModuleInterface, ServiceRegistry
from app.db import engine
from app.models import Base

from .routes import build_router


class Plugin(ModuleInterface):
    name = "copilot_metrics"
    version = "1.0.0"

    def __init__(self) -> None:
        self.router: APIRouter | None = None
        self._db_dep = None
        self._services = {}

    def init(self, app, registry: ServiceRegistry) -> None:
        # Ensure models are imported into metadata
        from . import models  # noqa: F401

        self._db_dep = registry.get_service("db_session_dep")
        self.router = build_router(self._db_dep)

    def start(self) -> None:
        Base.metadata.create_all(bind=engine)

    def stop(self) -> None:
        pass

    def get_router(self) -> APIRouter:
        return self.router  # type: ignore[return-value]

    def provides(self):
        return self._services