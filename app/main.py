import logging
from typing import List

from fastapi import Depends, FastAPI, HTTPException
from sqlalchemy.orm import Session

from . import crud, schemas
from .db import check_db_connection, get_db, init_db
from .core.manager import PluginManager
from .config import PLUGINS_ENABLED
from fastapi import APIRouter


app = FastAPI(title="FastAPI + PostgreSQL (Docker)")
logger = logging.getLogger("uvicorn")
# Initialize plugin manager early so middleware can be registered before app startup.
plugin_manager: PluginManager = PluginManager(app)
plugin_manager.register_core_services()
for name in PLUGINS_ENABLED:
    # Pre-load plugins so that any declared middlewares are added before startup.
    # Plugin start is deferred to the startup event below.
    plugin_manager.load(name)


@app.on_event("startup")
def on_startup():
    try:
        init_db()
        check_db_connection()
        logger.info("Database connection established.")
        # Start already loaded plugins (deferred until DB is ready)
        for name in PLUGINS_ENABLED:
            st = plugin_manager.states.get(name)
            if st and st.status == "loaded":
                plugin_manager.start(name)
        logger.info("Plugins initialized: %s", PLUGINS_ENABLED)
    except Exception:
        logger.exception("Database initialization or connection failed during startup.")
        # Let FastAPI raise on startup to avoid serving a broken app
        raise


@app.get("/health")
def health():
    try:
        ok = check_db_connection()
        return {"status": "ok", "database": "ok" if ok else "error"}
    except Exception:
        raise HTTPException(status_code=500, detail="Database connection failed")


# Plugin management endpoints
plugins_router = APIRouter(prefix="/plugins", tags=["plugins"])


@plugins_router.get("")
def list_plugins():
    if not plugin_manager:
        raise HTTPException(status_code=503, detail="Plugin manager not initialized")
    return [s.__dict__ for s in plugin_manager.list_states()]


@plugins_router.post("/load/{name}")
def load_plugin(name: str):
    if not plugin_manager:
        raise HTTPException(status_code=503, detail="Plugin manager not initialized")
    state = plugin_manager.load(name)
    return state.__dict__


@plugins_router.post("/start/{name}")
def start_plugin(name: str):
    if not plugin_manager:
        raise HTTPException(status_code=503, detail="Plugin manager not initialized")
    state = plugin_manager.start(name)
    return state.__dict__


@plugins_router.post("/stop/{name}")
def stop_plugin(name: str):
    if not plugin_manager:
        raise HTTPException(status_code=503, detail="Plugin manager not initialized")
    state = plugin_manager.stop(name)
    return state.__dict__


app.include_router(plugins_router)


@app.post("/items", response_model=schemas.ItemRead)
def create_item(item: schemas.ItemCreate, db: Session = Depends(get_db)):
    return crud.create_item(db, item)


@app.get("/items", response_model=List[schemas.ItemRead])
def read_items(skip: int = 0, limit: int = 100, db: Session = Depends(get_db)):
    return crud.get_items(db, skip, limit)


@app.get("/items/{item_id}", response_model=schemas.ItemRead)
def read_item(item_id: int, db: Session = Depends(get_db)):
    db_item = crud.get_item(db, item_id)
    if not db_item:
        raise HTTPException(status_code=404, detail="Item not found")
    return db_item


@app.put("/items/{item_id}", response_model=schemas.ItemRead)
def update_item(item_id: int, item: schemas.ItemUpdate, db: Session = Depends(get_db)):
    db_item = crud.update_item(db, item_id, item)
    if not db_item:
        raise HTTPException(status_code=404, detail="Item not found")
    return db_item


@app.delete("/items/{item_id}")
def delete_item(item_id: int, db: Session = Depends(get_db)):
    ok = crud.delete_item(db, item_id)
    if not ok:
        raise HTTPException(status_code=404, detail="Item not found")
    return {"status": "deleted"}