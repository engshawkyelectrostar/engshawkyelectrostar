import os

os.environ["ERP_API_KEY"] = "k" * 32

from fastapi.testclient import TestClient  # noqa: E402

from app.forecast import forecast_sales, holt_forecast  # noqa: E402
from app.main import app  # noqa: E402
from app.repo import get_repo  # noqa: E402

H = {"X-API-Key": "k" * 32}


class FakeRepo:
    def search_customers(self, q, limit):
        return [{"cust_id": 1, "cust_name": "عميل " + q}], False

    def list_invoices(self, *a):
        return [], False

    def stock(self, item_id, limit):
        return [{"item_id": 5, "qty_on_hand": 10}], False

    def monthly_sales(self, item_id, months):
        return [("2026-01", 100.0), ("2026-02", 110.0), ("2026-03", 120.0), ("2026-04", 130.0)]

    def on_hand(self, item_id):
        return 50.0

    def create_request(self, t, p, u):
        return 7


app.dependency_overrides[get_repo] = lambda: FakeRepo()
c = TestClient(app)


def test_auth():
    assert c.get("/api/v1/customers").status_code == 401
    assert c.get("/api/v1/customers", headers={"X-API-Key": "x"}).status_code == 401
    assert c.get("/api/v1/customers", headers=H).status_code == 200


def test_envelope_and_arabic():
    j = c.get("/api/v1/customers?q=أحمد", headers=H).json()
    assert j["ok"] and j["count"] == 1 and j["truncated"] is False
    assert j["data"][0]["cust_name"] == "عميل أحمد"


def test_validation():
    assert c.get("/api/v1/invoices?from=bad", headers=H).status_code == 400
    assert c.get("/api/v1/customers?limit=9999", headers=H).status_code == 422


def test_forecast_trending_up():
    j = c.get("/api/v1/forecast/sales?item_id=5&horizon_months=3&lead_time_months=1", headers=H).json()
    qty = [f["qty"] for f in j["forecast"]]
    assert j["method"] == "holt" and qty == sorted(qty) and qty[0] > 130
    assert j["forecast"][0]["period"] == "2026-05"
    assert j["reorder_suggestion"] == round(max(0, qty[0] - 50.0), 2)


def test_forecast_edge_cases():
    assert holt_forecast([], 2) == ([0.0, 0.0], "no_data")
    assert holt_forecast([10, 20], 1)[1] == "average"
    gap = forecast_sales([("2026-01", 10.0), ("2026-04", 40.0)], 1)  # شهور ناقصة = صفر
    assert gap["history_months"] == 4


def test_write_goes_pending():
    r = c.post("/api/v1/requests", headers=H, json={"type": "stock_adjustment", "payload": {"item_id": 5, "qty": 3}})
    assert r.status_code == 202 and r.json() == {"ok": True, "request_id": 7, "status": "PENDING"}
    assert c.post("/api/v1/requests", headers=H, json={"type": "drop_table", "payload": {}}).status_code == 422
