from __future__ import annotations

from abc import ABC, abstractmethod
from dataclasses import dataclass
from typing import Any, Dict, Iterable, Optional, Type

from fastapi import APIRouter, FastAPI


class ModuleInterface(ABC):
    """Standard interface for modules/plugins.

    Each plugin should implement the following lifecycle methods.
    """

    name: str
    version: str

    @abstractmethod
    def init(self, app: FastAPI, registry: "ServiceRegistry") -> None:
        """Initialize the plugin with references to the app and service registry."""

    @abstractmethod
    def start(self) -> None:
        """Start the plugin (register events, initialize resources)."""

    @abstractmethod
    def stop(self) -> None:
        """Stop the plugin and release resources."""

    @abstractmethod
    def get_router(self) -> Optional[APIRouter]:
        """Return a FastAPI router if the plugin exposes endpoints. Can be None."""

    def provides(self) -> Dict[str, Any]:
        """Register services provided by the plugin (optional)."""
        return {}

    def depends_on(self) -> Iterable[str]:
        """List names of services this plugin depends on (optional)."""
        return []

    def middlewares(self) -> Iterable["MiddlewareDef"]:
        """Return a list of middlewares to add to the app (optional)."""
        return []


@dataclass
class MiddlewareDef:
    cls: Type[Any]
    kwargs: Dict[str, Any] | None = None


class ServiceRegistry:
    """Simple registry for services and an event bus."""

    def __init__(self) -> None:
        self._services: Dict[str, Any] = {}
        self._subscribers: Dict[str, list] = {}

    # Services
    def register_service(self, name: str, service: Any) -> None:
        self._services[name] = service

    def get_service(self, name: str) -> Any:
        return self._services.get(name)

    def has_service(self, name: str) -> bool:
        return name in self._services

    # Event bus
    def subscribe(self, topic: str, handler) -> None:
        self._subscribers.setdefault(topic, []).append(handler)

    def publish(self, topic: str, payload: Any) -> None:
        for handler in self._subscribers.get(topic, []):
            try:
                handler(payload)
            except Exception:
                # Fail-safe: prevent a faulty handler from breaking the system
                continue