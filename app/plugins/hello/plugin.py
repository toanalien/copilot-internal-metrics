from fastapi import APIRouter

from app.core.interfaces import ModuleInterface, ServiceRegistry


class Plugin(ModuleInterface):
    name = "hello"
    version = "1.0.0"

    def __init__(self) -> None:
        self.router = APIRouter()

        @self.router.get("/")
        def hello():
            return {"message": "Hello from plugin"}

    def init(self, app, registry: ServiceRegistry) -> None:
        # Register a demo service
        registry.register_service("hello.message", "Hello Service Ready")

    def start(self) -> None:
        pass

    def stop(self) -> None:
        pass

    def get_router(self) -> APIRouter:
        return self.router

    def provides(self):
        return {}