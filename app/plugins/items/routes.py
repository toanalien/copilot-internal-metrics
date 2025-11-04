from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session

from .schemas import PluginItemCreate, PluginItemUpdate, PluginItemRead
from .crud import create_item, get_items, get_item, update_item, delete_item


def build_router(db_dep) -> APIRouter:
    router = APIRouter()

    @router.post("/", response_model=PluginItemRead)
    def create(item: PluginItemCreate, db: Session = Depends(db_dep)):
        return create_item(db, item)

    @router.get("/", response_model=list[PluginItemRead])
    def read(skip: int = 0, limit: int = 100, db: Session = Depends(db_dep)):
        return get_items(db, skip, limit)

    @router.get("/{item_id}", response_model=PluginItemRead)
    def read_one(item_id: int, db: Session = Depends(db_dep)):
        obj = get_item(db, item_id)
        if not obj:
            raise HTTPException(status_code=404, detail="Item not found")
        return obj

    @router.put("/{item_id}", response_model=PluginItemRead)
    def update(item_id: int, item: PluginItemUpdate, db: Session = Depends(db_dep)):
        obj = update_item(db, item_id, item)
        if not obj:
            raise HTTPException(status_code=404, detail="Item not found")
        return obj

    @router.delete("/{item_id}")
    def delete(item_id: int, db: Session = Depends(db_dep)):
        ok = delete_item(db, item_id)
        if not ok:
            raise HTTPException(status_code=404, detail="Item not found")
        return {"status": "deleted"}

    return router