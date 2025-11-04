from __future__ import annotations

import importlib
import logging
import pkgutil
from dataclasses import dataclass
from typing import Dict, List, Optional

from fastapi import APIRouter, FastAPI, HTTPException

from .interfaces import ModuleInterface, ServiceRegistry, MiddlewareDef


logger = logging.getLogger("plugins")


@dataclass
class ModuleState:
    name: str
    version: str
    status: str  # loaded|started|stopped|failed
    error: Optional[str] = None


class PluginManager:
    def __init__(self, app: FastAPI, base_package: str = "app.plugins") -> None:
        self.app = app
        self.base_package = base_package
        self.registry = ServiceRegistry()
        self.modules: Dict[str, ModuleInterface] = {}
        self.states: Dict[str, ModuleState] = {}

    def register_core_services(self) -> None:
        # Example: register core services available to plugins
        # DB session dependency
        try:
            from app.db import get_db

            self.registry.register_service("db_session_dep", get_db)
        except Exception:
            logger.warning("Could not register db_session_dep service")

    def discover_available(self) -> List[str]:
        """List plugin packages available under base_package."""
        try:
            pkg = importlib.import_module(self.base_package)
        except ModuleNotFoundError:
            return []
        return [m.name for m in pkgutil.iter_modules(pkg.__path__)]

    def load(self, name: str) -> ModuleState:
        if name in self.modules:
            return self.states[name]
        try:
            mod = importlib.import_module(f"{self.base_package}.{name}.plugin")
            plugin: ModuleInterface
            if hasattr(mod, "get_plugin"):
                plugin = mod.get_plugin()
            elif hasattr(mod, "Plugin"):
                plugin = getattr(mod, "Plugin")()
            else:
                raise RuntimeError("Plugin module must define get_plugin() or Plugin class")

            plugin.init(self.app, self.registry)
            # Add middlewares (if any)
            for md in plugin.middlewares():
                if isinstance(md, MiddlewareDef):
                    self.app.add_middleware(md.cls, **(md.kwargs or {}))
            router = plugin.get_router()
            if isinstance(router, APIRouter):
                # Mount router under /plugins/<name>
                self.app.include_router(router, prefix=f"/plugins/{name}")

            # Register provided services
            for svc_name, svc in plugin.provides().items():
                self.registry.register_service(svc_name, svc)

            self.modules[name] = plugin
            state = ModuleState(name=name, version=getattr(plugin, "version", "0.0.0"), status="loaded")
            self.states[name] = state
            logger.info("Loaded plugin: %s", name)
            return state
        except Exception as exc:
            state = ModuleState(name=name, version="unknown", status="failed", error=str(exc))
            self.states[name] = state
            logger.exception("Failed to load plugin %s: %s", name, exc)
            return state

    def start(self, name: str) -> ModuleState:
        plugin = self.modules.get(name)
        if not plugin:
            raise HTTPException(status_code=404, detail=f"Plugin {name} not loaded")
        try:
            plugin.start()
            st = self.states[name]
            st.status = "started"
            logger.info("Started plugin: %s", name)
            return st
        except Exception as exc:
            st = self.states[name]
            st.status = "failed"
            st.error = str(exc)
            logger.exception("Failed to start plugin %s: %s", name, exc)
            return st

    def stop(self, name: str) -> ModuleState:
        plugin = self.modules.get(name)
        if not plugin:
            raise HTTPException(status_code=404, detail=f"Plugin {name} not loaded")
        try:
            plugin.stop()
            st = self.states[name]
            st.status = "stopped"
            logger.info("Stopped plugin: %s", name)
            return st
        except Exception as exc:
            st = self.states[name]
            st.status = "failed"
            st.error = str(exc)
            logger.exception("Failed to stop plugin %s: %s", name, exc)
            return st

    def unload(self, name: str) -> None:
        # FastAPI does not support safe dynamic router removal; instead, stop and remove from registry.
        if name in self.modules:
            try:
                self.modules[name].stop()
            except Exception:
                pass
            del self.modules[name]
            del self.states[name]

    def list_states(self) -> List[ModuleState]:
        return list(self.states.values())

    def register_module(self, module: ModuleInterface) -> ModuleState:
        """Manually register a module (useful for testing/dynamic embedding)."""
        name = getattr(module, "name", module.__class__.__name__.lower())
        version = getattr(module, "version", "0.0.0")
        self.modules[name] = module
        st = ModuleState(name=name, version=version, status="loaded")
        self.states[name] = st
        return st