import logging
from datetime import date
from contextlib import asynccontextmanager
from typing import Literal

from fastapi import Depends, FastAPI, HTTPException, Query, Request
from fastapi.responses import JSONResponse
from pydantic import BaseModel

from . import db
from .config import load_settings
from .forecast import forecast_sales
from .repo import get_repo
from .security import require_auth

log = logging.getLogger("erp_api")


@asynccontextmanager
async def lifespan(_: FastAPI):
    s = load_settings()
    if s.database_url:
        db.init_pool(s)
    yield
    db.close_pool()


app = FastAPI(title="ERP API", version="1.0", description="REST API فوق ERP (PostgreSQL)", lifespan=lifespan)
auth = [Depends(require_auth)]


@app.exception_handler(Exception)
async def _unhandled(request: Request, exc: Exception):
    log.exception("unhandled error on %s", request.url.path)  # التفاصيل في اللوج بس
    return JSONResponse({"ok": False, "error": "internal error"}, status_code=500)


@app.exception_handler(HTTPException)
async def _http(request: Request, exc: HTTPException):
    return JSONResponse({"ok": False, "error": exc.detail}, status_code=exc.status_code)


def _list(rows_truncated):
    rows, truncated = rows_truncated
    return {"ok": True, "count": len(rows), "truncated": truncated, "data": rows}


def _date(v: str | None) -> str | None:
    if v is None:
        return None
    try:
        date.fromisoformat(v)
    except ValueError:
        raise HTTPException(400, "date must be YYYY-MM-DD")
    return v


@app.get("/api/v1/health", dependencies=auth)
def health():
    return {"ok": True}


@app.get("/api/v1/customers", dependencies=auth, summary="بحث عن عملاء بالاسم")
def customers(q: str = Query("", max_length=60), limit: int = Query(20, ge=1, le=100), repo=Depends(get_repo)):
    return _list(repo.search_customers(q, limit))


@app.get("/api/v1/invoices", dependencies=auth, summary="فواتير المبيعات")
def invoices(date_from: str | None = Query(None, alias="from"), date_to: str | None = Query(None, alias="to"),
             cust_id: int | None = None, limit: int = Query(50, ge=1, le=200), repo=Depends(get_repo)):
    return _list(repo.list_invoices(_date(date_from), _date(date_to), cust_id, limit))


@app.get("/api/v1/stock", dependencies=auth, summary="أرصدة المخزون")
def stock(item_id: int | None = None, limit: int = Query(50, ge=1, le=200), repo=Depends(get_repo)):
    return _list(repo.stock(item_id, limit))


@app.get("/api/v1/forecast/sales", dependencies=auth, summary="توقع مبيعات صنف + اقتراح إعادة طلب")
def forecast(item_id: int, horizon_months: int = Query(3, ge=1, le=12), history_months: int = Query(24, ge=3, le=60),
             lead_time_months: float = Query(1.0, ge=0, le=12), repo=Depends(get_repo)):
    result = forecast_sales(repo.monthly_sales(item_id, history_months), horizon_months)
    on_hand = repo.on_hand(item_id)
    need, remaining = 0.0, lead_time_months
    for f in result["forecast"]:
        take = min(1.0, remaining)
        need += f["qty"] * take
        remaining -= take
        if remaining <= 0:
            break
    return {"ok": True, "item_id": item_id, "on_hand": on_hand, **result,
            "reorder_suggestion": round(max(0.0, need - on_hand), 2)}


class WriteRequest(BaseModel):
    type: Literal["create_sales_order", "stock_adjustment"]
    payload: dict


@app.post("/api/v1/requests", dependencies=auth, status_code=202, summary="طلب كتابة (بيتحط PENDING لحد الموافقة)")
def create_request(body: WriteRequest, repo=Depends(get_repo)):
    """الكتابة مش مباشرة في جداول الـ ERP: بتتسجل PENDING وبعد موافقة بشرية بتتنفذ عن طريق Stored Procedure."""
    new_id = repo.create_request(body.type, body.payload, "n8n")
    return {"ok": True, "request_id": new_id, "status": "PENDING"}
