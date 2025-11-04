# FastAPI + PostgreSQL (Docker)

A template project using FastAPI, SQLAlchemy, and PostgreSQL, running inside Docker. It includes a pluggable module system, sample plugins, and a small CRUD domain to demonstrate integration.

## Requirements
- Docker and Docker Compose
- Host port `8001` free for the API (`uvicorn` listens on container port `8000`, mapped to host `8001`)
- PostgreSQL runs inside Docker; database connectivity is via the internal Docker network

## Configuration
1. Copy or edit `.env`:
   ```env
   DATABASE_URL=postgresql://user:password@postgres:5432/dbname
   POSTGRES_USER=user
   POSTGRES_PASSWORD=password
   POSTGRES_DB=dbname
   APP_NAME=FastAPI Docker App
   DEBUG=true
   ```
   Note: `postgres` is the service name in `docker-compose.yml`. The API connects to the DB through the internal Docker network.

## Run with Docker
```bash
docker compose up --build
```
- API: `http://localhost:8001`
- Docs: `http://localhost:8001/docs`
- Healthcheck: `http://localhost:8001/health`

Run in background:
```bash
docker compose up -d
```

## Testing
Ensure the `postgres` service is healthy, then run:
```bash
docker compose run --rm api pytest -q
```
Tests include:
- Validate `DATABASE_URL` environment variable format
- Ping DB connection and ensure tables are created

## Project Structure
```
app/
  ├── core/               # Plugin system core
  │   ├── interfaces.py   # ModuleInterface and ServiceRegistry
  │   └── manager.py      # PluginManager: load/start/stop/unload, states
  ├── plugins/            # Plugin packages
  │   ├── hello/          # Demo plugin: greeting
  │   │   └── plugin.py
  │   ├── analytics/      # Demo plugin: items count from DB
  │   │   └── plugin.py
  │   └── items/          # Full plugin example (CRUD, services, middleware)
  ├── config.py       # Read env via python-dotenv
  ├── db.py           # Engine, Session, connectivity checks, table creation
  ├── models.py       # Core Item model (SQLAlchemy)
  ├── schemas.py      # Pydantic schemas for request/response
  ├── crud.py         # Core Item CRUD operations
  └── main.py         # FastAPI app, CRUD endpoints, healthcheck
tests/
  ├── test_env_config.py
  ├── test_db_connection.py
  └── test_plugins.py   # Plugin, performance, and memory tests
Dockerfile
docker-compose.yml
.env
requirements.txt
README.md
```

## Primary Endpoints
- `POST /items` create Item
- `GET /items` list Items
- `GET /items/{id}` get Item by ID
- `PUT /items/{id}` update Item
- `DELETE /items/{id}` delete Item
- `GET /health` check DB connectivity
- `GET /plugins` list plugin states
- `POST /plugins/load/{name}` load plugin by name
- `POST /plugins/start/{name}` start plugin
- `POST /plugins/stop/{name}` stop plugin
- `GET /plugins/hello/` endpoint from `hello` plugin
- `GET /plugins/analytics/count` count Items from DB via `analytics` plugin

## Quality & Notes
- Basic PEP 8 compliance.
- DB error handling: ping on startup and `/health`, log failures.
- No migrations included; tables are auto-created at first run.
- Modular: add new plugins by creating `app/plugins/<name>/plugin.py` implementing `ModuleInterface`.
- Backward-compatible: existing endpoints remain unchanged.
- Fail-safe: plugin errors are captured and do not break the system.

## Develop a New Plugin (Quickstart)
1. Create `app/plugins/myplugin/plugin.py`:
   ```python
   from fastapi import APIRouter
   from app.core.interfaces import ModuleInterface, ServiceRegistry

   class Plugin(ModuleInterface):
       name = "myplugin"
       version = "0.1.0"

       def __init__(self):
           self.router = APIRouter()

           @self.router.get("/info")
           def info():
               return {"plugin": self.name}

       def init(self, app, registry: ServiceRegistry):
           pass

       def start(self):
           pass

       def stop(self):
           pass

       def get_router(self):
           return self.router
   ```
2. Enable plugin in `.env`:
   ```env
   PLUGINS_ENABLED=hello,analytics,myplugin
   ```
3. Restart services: `docker compose up --build`

## Detailed Guide: Writing a New Plugin

Goal: Standardize how to build independent plugin modules with clear separation of concerns (Middleware, Schemas, Models, CRUD, Services, Utils, Routes) and integrate cleanly via `ModuleInterface` and `PluginManager`.

### Standard Directory Layout

```
app/
  plugins/
    myplugin/
      __init__.py
      models.py        # SQLAlchemy models (if DB is used)
      schemas.py       # Pydantic schemas (request/response)
      crud.py          # DB operations (create/read/update/delete)
      services.py      # Business logic / orchestration
      utils.py         # Utilities and helpers
      middleware.py    # Optional middleware
      routes.py        # FastAPI router for the plugin
      plugin.py        # Plugin class implementing ModuleInterface
```

### Plugin Architecture (Mermaid)

```mermaid
flowchart LR
    subgraph Client
        U[User / Client]
    end

    U --> M[Middleware]
    M --> R[APIRouter]
    R --> S[Service Layer]
    S --> C[CRUD]
    C --> D[(Database)]

    subgraph Cross-Cutting
        SC[Schemas]
        UT[Utils]
    end

    R --- SC
    C --- SC
    S --- UT

    subgraph Module
        P[plugin.py]
    end

    P ==> M
    P ==> R
    P ==> S
    P ==> C
    P ==> SC
    P ==> UT

    subgraph Core
        PM[PluginManager]
        APP[FastAPI App]
    end

    P --> PM
    PM --> APP
    R --> APP
```

### Plugin Lifecycle (Mermaid)

```mermaid
stateDiagram-v2
    [*] --> Registered
    Registered --> Initialized: Plugin.init(app, registry)
    Initialized --> Mounted: Router mounted + Middlewares added
    Mounted --> Started: Plugin.start()
    Started --> Running
    Running --> Stopped: Plugin.stop()
    Stopped --> [*]
```

### Request Flow (Mermaid)

```mermaid
sequenceDiagram
    participant Client
    participant App as FastAPI App
    participant MW as Middleware
    participant Router
    participant Service
    participant CRUD
    participant DB as Database

    Client->>App: HTTP request
    App->>MW: process(request)
    MW->>Router: forward(request)
    Router->>Service: call(params)
    Service->>CRUD: execute(query)
    CRUD->>DB: SELECT/INSERT/UPDATE/DELETE
    DB-->>CRUD: rows/result
    CRUD-->>Service: data
    Service-->>Router: response payload
    Router-->>App: JSON response
    App-->>Client: 200 OK
```

### Implementation Steps

- Create `app/plugins/<plugin-name>/` using the standard layout.
- Write `models.py` (if using DB) and create tables inside `init()` or via migrations.
- Write `schemas.py` per Pydantic conventions (match project version).
- Write `crud.py` for DB operations only; keep business logic out.
- Write `services.py` to orchestrate business logic using CRUD/Utils.
- Write `middleware.py` (optional) for cross‑cutting concerns.
- Write `routes.py` to define endpoints and inject DB/session/registry.
- Write `plugin.py` to assemble router, middleware, services, and implement `ModuleInterface`.
- Enable in `.env` (`PLUGINS_ENABLED`), rebuild, and test.

### Minimal Code Examples

`plugin.py`
```python
from fastapi import APIRouter
from app.core.interfaces import ModuleInterface, ServiceRegistry

class Plugin(ModuleInterface):
    name = "myplugin"
    version = "0.1.0"

    def __init__(self):
        self.router = APIRouter(prefix=f"/{self.name}", tags=[self.name])

    def init(self, app, registry: ServiceRegistry):
        # Initialize resources, create tables, register services
        registry.register("myplugin:service", object())

    def middlewares(self):
        # Return a list of (callable, kwargs) for app.add_middleware
        return []

    def get_router(self):
        from .routes import build_router
        return build_router(self.router)

    def start(self):
        # Start background tasks if needed
        pass

    def stop(self):
        # Cleanup resources
        pass
```

`routes.py`
```python
from fastapi import APIRouter

def build_router(router: APIRouter) -> APIRouter:
    @router.get("/info")
    def info():
        return {"plugin": "myplugin"}
    return router
```

`services.py`
```python
class MyService:
    def do_work(self, name: str) -> str:
        return name.upper()
```

`crud.py`
```python
from sqlalchemy.orm import Session

def create(db: Session, name: str):
    # Insert into DB
    ...
```

`schemas.py`
```python
from pydantic import BaseModel

class MyBase(BaseModel):
    name: str

class MyCreate(MyBase):
    pass

class MyRead(MyBase):
    id: int
```

`middleware.py`
```python
class MyMiddleware:
    def __init__(self, app):
        self.app = app
    async def __call__(self, scope, receive, send):
        # Example: add header or logging
        await self.app(scope, receive, send)
```

### Integrate and Enable Plugin

- `.env`: `PLUGINS_ENABLED=hello,analytics,myplugin`
- Rebuild: `docker compose up --build`
- Test: `docker compose run --rm api pytest -q`
- Docs: open `http://localhost:8001/docs` to verify endpoints.

### Quality Checklist

- Endpoints appear in API Docs and respond correctly.
- Disabling the plugin (remove from `PLUGINS_ENABLED`) does not break the system.
- Clear separation: Routes ↔ Service ↔ CRUD ↔ Models/Schemas.
- Middleware does not mix business logic; keep it cross‑cutting only.
- DB resources are created in `init()` or via migrations.

### Advanced (Recommendations)

- Use FastAPI Lifespan API instead of `@app.on_event("startup")` for newer versions.
- Migrate to Pydantic v2 (`model_config`) to remove class‑based `Config` deprecation.
- Support async CRUD/Service when performance is critical.
- Automatic plugin discovery via entry points or folder scanning.