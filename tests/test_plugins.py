import tracemalloc
from fastapi.testclient import TestClient

from app.main import app
from app.core.manager import PluginManager
from app.core.interfaces import ModuleInterface, ServiceRegistry


def test_plugins_endpoints():
    # Explicitly trigger startup to initialize PluginManager
    from app.main import on_startup
    on_startup()

    client = TestClient(app)
    # List plugins
    resp = client.get("/plugins")
    assert resp.status_code == 200
    names = {p["name"] for p in resp.json()}
    assert {"hello", "analytics"}.issubset(names)

    # Check hello plugin endpoint
    hello = client.get("/plugins/hello/")
    assert hello.status_code == 200
    assert hello.json()["message"].startswith("Hello")

    # Check analytics plugin endpoint
    analytics = client.get("/plugins/analytics/count")
    assert analytics.status_code == 200
    assert isinstance(analytics.json().get("items_count"), int)


class DummyModule(ModuleInterface):
    name = "dummy"
    version = "0.1"

    def __init__(self):
        self.started = False

    def init(self, app, registry: ServiceRegistry) -> None:
        pass

    def start(self) -> None:
        self.started = True

    def stop(self) -> None:
        self.started = False

    def get_router(self):
        return None


def test_performance_many_modules():
    # Create many lightweight modules and ensure they start quickly
    pm = PluginManager(app)
    pm.register_core_services()
    for i in range(50):
        m = DummyModule()
        m.name = f"dummy{i}"
        pm.register_module(m)
        pm.start(m.name)
    # Ensure 50 modules are in 'started' state
    assert sum(1 for s in pm.list_states() if s.status == "started") >= 50


def test_memory_no_leak_on_load_unload():
    tracemalloc.start()
    pm = PluginManager(app)
    pm.register_core_services()
    for _ in range(100):
        m = DummyModule()
        m.name = "dummy_mem"
        pm.register_module(m)
        pm.start(m.name)
        pm.stop(m.name)
        pm.unload(m.name)
    current, peak = tracemalloc.get_traced_memory()
    tracemalloc.stop()
    # Small margin is acceptable; ensure no abnormal growth
    assert peak - current < 5_000_000  # < ~5MB