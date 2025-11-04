from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session

from .schemas import ImportAccountRequest, GithubAccountRead, CopilotMetricsRead
from .crud import list_accounts, get_account, latest_metrics_for_account, latest_metrics_all
from .services import CopilotMetricsService


def build_router(db_dep) -> APIRouter:
    router = APIRouter()

    @router.post("/accounts/import")
    def import_account(req: ImportAccountRequest, db: Session = Depends(db_dep)):
        svc = CopilotMetricsService(db_dep)
        try:
            account_id = svc.import_account(req.token, proxy=req.proxy)
        except Exception as exc:
            raise HTTPException(status_code=400, detail=str(exc))
        return {"account_id": account_id}

    @router.get("/accounts", response_model=list[GithubAccountRead])
    def get_accounts(db: Session = Depends(db_dep)):
        return list_accounts(db)

    @router.get("/accounts/{account_id}", response_model=GithubAccountRead)
    def get_account_one(account_id: int, db: Session = Depends(db_dep)):
        acc = get_account(db, account_id)
        if not acc:
            raise HTTPException(status_code=404, detail="Account not found")
        return acc

    @router.post("/metrics/fetch/{account_id}")
    def fetch_metrics(account_id: int, db: Session = Depends(db_dep)):
        svc = CopilotMetricsService(db_dep)
        try:
            metrics_id = svc.fetch_metrics(account_id)
        except Exception as exc:
            raise HTTPException(status_code=400, detail=str(exc))
        return {"metrics_id": metrics_id}

    @router.get("/metrics/{account_id}", response_model=CopilotMetricsRead)
    def get_metrics_one(account_id: int, db: Session = Depends(db_dep)):
        m = latest_metrics_for_account(db, account_id)
        if not m:
            raise HTTPException(status_code=404, detail="Metrics not found")
        # Convert payload JSON string to dict for response model
        from pydantic import TypeAdapter
        adapter = TypeAdapter(dict)
        payload = adapter.validate_json(m.payload)
        return {"id": m.id, "account_id": m.account_id, "fetched_at": m.fetched_at, "payload": payload}

    @router.get("/metrics", response_model=list[CopilotMetricsRead])
    def get_metrics_all(db: Session = Depends(db_dep)):
        metrics = latest_metrics_all(db)
        from pydantic import TypeAdapter
        adapter = TypeAdapter(dict)
        out = []
        for m in metrics:
            payload = adapter.validate_json(m.payload)
            out.append({"id": m.id, "account_id": m.account_id, "fetched_at": m.fetched_at, "payload": payload})
        return out

    return router