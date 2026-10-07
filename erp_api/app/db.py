import datetime as dt
import decimal
import json
import logging
from typing import Any

log = logging.getLogger("erp_api")
_pool = None


def init_pool(settings) -> None:
    global _pool
    import oracledb

    if settings.oracle_client_lib_dir:
        # أوراكل 11g بيحتاج thick mode (thin بيدعم 12.1+ بس)
        oracledb.init_oracle_client(lib_dir=settings.oracle_client_lib_dir)
    _pool = oracledb.create_pool(
        user=settings.oracle_user, password=settings.oracle_password, dsn=settings.oracle_dsn,
        min=1, max=5, increment=1,
    )


def _val(v: Any) -> Any:
    if isinstance(v, (dt.datetime, dt.date)):
        return v.strftime("%Y-%m-%d %H:%M:%S") if isinstance(v, dt.datetime) else v.isoformat()
    if isinstance(v, decimal.Decimal):
        return float(v)
    if hasattr(v, "read"):  # CLOB
        return v.read()
    return v


def query(sql: str, binds: dict | None = None, limit: int = 100) -> tuple[list[dict], bool]:
    """بيرجع (rows, truncated). القيم دايمًا bind variables."""
    with _pool.acquire() as conn:
        with conn.cursor() as cur:
            cur.execute(sql, binds or {})
            cols = [c[0].lower() for c in cur.description]
            rows = cur.fetchmany(limit + 1)
    truncated = len(rows) > limit
    return [dict(zip(cols, map(_val, r))) for r in rows[:limit]], truncated


def insert_request(req_type: str, payload: dict, created_by: str) -> int:
    import oracledb

    with _pool.acquire() as conn:
        with conn.cursor() as cur:
            new_id = cur.var(oracledb.NUMBER)
            cur.execute(
                "INSERT INTO api_requests (id, req_type, payload, status, created_by, created_at) "
                "VALUES (api_requests_seq.NEXTVAL, :t, :p, 'PENDING', :u, SYSDATE) RETURNING id INTO :id",
                {"t": req_type, "p": json.dumps(payload, ensure_ascii=False), "u": created_by, "id": new_id},
            )
            conn.commit()
            return int(new_id.getvalue()[0])
