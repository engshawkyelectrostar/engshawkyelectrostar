"""طبقة الوصول للبيانات (PostgreSQL). أسماء الجداول/الأعمدة هنا أمثلة - هتتعدل حسب الـ DDL الحقيقي."""
from . import db


class PgRepo:
    def search_customers(self, q: str, limit: int):
        sql = ("SELECT cust_id, cust_name, phone, balance FROM customers "
               "WHERE cust_name ILIKE %(q)s ORDER BY cust_name LIMIT %(lim)s")
        return db.query(sql, {"q": f"%{q}%", "lim": limit + 1}, limit)

    def list_invoices(self, date_from, date_to, cust_id, limit: int):
        where, binds = ["TRUE"], {"lim": limit + 1}
        if date_from:
            where.append("inv_date >= %(d1)s::date"); binds["d1"] = date_from
        if date_to:
            where.append("inv_date < %(d2)s::date + 1"); binds["d2"] = date_to
        if cust_id:
            where.append("cust_id = %(cid)s"); binds["cid"] = cust_id
        sql = ("SELECT inv_no, inv_date, cust_id, total_amount, status FROM sales_invoices "
               f"WHERE {' AND '.join(where)} ORDER BY inv_date DESC LIMIT %(lim)s")
        return db.query(sql, binds, limit)

    def stock(self, item_id, limit: int):
        where, binds = "TRUE", {"lim": limit + 1}
        if item_id:
            where, binds["iid"] = "item_id = %(iid)s", item_id
        sql = f"SELECT item_id, item_name, qty_on_hand FROM stock_view WHERE {where} ORDER BY item_id LIMIT %(lim)s"
        return db.query(sql, binds, limit)

    def monthly_sales(self, item_id: int, months: int) -> list[tuple[str, float]]:
        sql = ("SELECT to_char(inv_date, 'YYYY-MM') AS period, SUM(qty) AS qty FROM sales_invoice_lines "
               "WHERE item_id = %(iid)s "
               "AND inv_date >= date_trunc('month', now()) - make_interval(months => %(m)s) "
               "AND inv_date < date_trunc('month', now()) "
               "GROUP BY 1 ORDER BY 1 LIMIT %(lim)s")
        rows, _ = db.query(sql, {"iid": item_id, "m": months, "lim": 1001}, 1000)
        return [(r["period"], float(r["qty"])) for r in rows]

    def on_hand(self, item_id: int) -> float:
        rows, _ = db.query("SELECT qty_on_hand FROM stock_view WHERE item_id = %(iid)s LIMIT %(lim)s",
                           {"iid": item_id, "lim": 2}, 1)
        return float(rows[0]["qty_on_hand"]) if rows else 0.0

    def create_request(self, req_type: str, payload: dict, created_by: str) -> int:
        return db.insert_request(req_type, payload, created_by)


def get_repo() -> PgRepo:
    return PgRepo()
