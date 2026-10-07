"""طبقة الوصول للبيانات. أسماء الجداول/الأعمدة هنا أمثلة - عدّلها حسب الـ schema الحقيقي."""
from . import db


class OracleRepo:
    def search_customers(self, q: str, limit: int):
        sql = ("SELECT * FROM (SELECT cust_id, cust_name, phone, balance FROM customers "
               "WHERE UPPER(cust_name) LIKE UPPER(:q) ORDER BY cust_name) WHERE ROWNUM <= :lim")
        return db.query(sql, {"q": f"%{q}%", "lim": limit + 1}, limit)

    def list_invoices(self, date_from, date_to, cust_id, limit: int):
        where, binds = ["1=1"], {"lim": limit + 1}
        if date_from:
            where.append("inv_date >= TO_DATE(:d1, 'YYYY-MM-DD')"); binds["d1"] = date_from
        if date_to:
            where.append("inv_date < TO_DATE(:d2, 'YYYY-MM-DD') + 1"); binds["d2"] = date_to
        if cust_id:
            where.append("cust_id = :cid"); binds["cid"] = cust_id
        sql = ("SELECT * FROM (SELECT inv_no, inv_date, cust_id, total_amount, status FROM sales_invoices "
               f"WHERE {' AND '.join(where)} ORDER BY inv_date DESC) WHERE ROWNUM <= :lim")
        return db.query(sql, binds, limit)

    def stock(self, item_id, limit: int):
        where, binds = "1=1", {"lim": limit + 1}
        if item_id:
            where, binds["iid"] = "item_id = :iid", item_id
        sql = (f"SELECT * FROM (SELECT item_id, item_name, qty_on_hand FROM stock_view WHERE {where} "
               "ORDER BY item_id) WHERE ROWNUM <= :lim")
        return db.query(sql, binds, limit)

    def monthly_sales(self, item_id: int, months: int) -> list[tuple[str, float]]:
        sql = ("SELECT TO_CHAR(inv_date, 'YYYY-MM') AS period, SUM(qty) AS qty FROM sales_invoice_lines "
               "WHERE item_id = :iid AND inv_date >= ADD_MONTHS(TRUNC(SYSDATE, 'MM'), -:m) "
               "AND inv_date < TRUNC(SYSDATE, 'MM') GROUP BY TO_CHAR(inv_date, 'YYYY-MM') ORDER BY 1")
        rows, _ = db.query(sql, {"iid": item_id, "m": months}, 1000)
        return [(r["period"], float(r["qty"])) for r in rows]

    def on_hand(self, item_id: int) -> float:
        rows, _ = db.query("SELECT qty_on_hand FROM stock_view WHERE item_id = :iid", {"iid": item_id}, 1)
        return float(rows[0]["qty_on_hand"]) if rows else 0.0

    def create_request(self, req_type: str, payload: dict, created_by: str) -> int:
        return db.insert_request(req_type, payload, created_by)


def get_repo() -> OracleRepo:
    return OracleRepo()
