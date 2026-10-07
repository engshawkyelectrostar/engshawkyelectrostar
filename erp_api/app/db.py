import datetime as dt
import decimal
import json
import logging
from typing import Any

log = logging.getLogger("erp_api")
_pool = None


def init_pool(settings) -> None:
    global _pool
    from psycopg_pool import ConnectionPool

    _pool = ConnectionPool(settings.database_url, min_size=1, max_size=5, open=True,
                           kwargs={"options": "-c statement_timeout=30000"})


def close_pool() -> None:
    if _pool is not None:
        _pool.close()


def _val(v: Any) -> Any:
    if isinstance(v, dt.datetime):
        return v.strftime("%Y-%m-%d %H:%M:%S")
    if isinstance(v, dt.date):
        return v.isoformat()
    if isinstance(v, decimal.Decimal):
        return float(v)
    return v


def query(sql: str, binds: dict | None = None, limit: int = 100) -> tuple[list[dict], bool]:
    """بيرجع (rows, truncated). القيم دايمًا bind parameters (%(name)s) - مفيش string formatting للقيم.
    الـ SQL لازم يحتوي LIMIT %(lim)s بقيمة limit+1."""
    with _pool.connection() as conn:
        with conn.cursor() as cur:
            cur.execute(sql, binds or {})
            cols = [c.name for c in cur.description]
            rows = cur.fetchmany(limit + 1)
    truncated = len(rows) > limit
    return [dict(zip(cols, map(_val, r))) for r in rows[:limit]], truncated


def insert_request(req_type: str, payload: dict, created_by: str) -> int:
    with _pool.connection() as conn:
        with conn.cursor() as cur:
            cur.execute(
                "INSERT INTO api_requests (req_type, payload, created_by) "
                "VALUES (%(t)s, %(p)s::jsonb, %(u)s) RETURNING id",
                {"t": req_type, "p": json.dumps(payload, ensure_ascii=False), "u": created_by},
            )
            return int(cur.fetchone()[0])
