"""توقع بسيط وشفاف: Holt (exponential smoothing بـ trend). بدون مكتبات ثقيلة.
لو البيانات قليلة بنرجع المتوسط. ممكن نستبدله لاحقًا بـ statsmodels/Prophet بنفس الواجهة."""
from datetime import date


def _next_periods(last_period: str, n: int) -> list[str]:
    y, m = int(last_period[:4]), int(last_period[5:7])
    out = []
    for _ in range(n):
        m += 1
        if m > 12:
            y, m = y + 1, 1
        out.append(f"{y:04d}-{m:02d}")
    return out


def holt_forecast(values: list[float], horizon: int, alpha: float = 0.4, beta: float = 0.2) -> tuple[list[float], str]:
    if not values:
        return [0.0] * horizon, "no_data"
    if len(values) < 3:
        avg = sum(values) / len(values)
        return [round(avg, 2)] * horizon, "average"
    level, trend = values[0], values[1] - values[0]
    for v in values[1:]:
        prev = level
        level = alpha * v + (1 - alpha) * (level + trend)
        trend = beta * (level - prev) + (1 - beta) * trend
    return [round(max(0.0, level + trend * (h + 1)), 2) for h in range(horizon)], "holt"


def forecast_sales(history: list[tuple[str, float]], horizon: int) -> dict:
    """history = [("2026-01", 120.0), ...] مرتبة زمنيًا؛ الشهور الناقصة بتتحسب صفر."""
    if history:
        filled = _fill_gaps(history)
        periods = [p for p, _ in filled]
        values = [v for _, v in filled]
        last = periods[-1]
    else:
        values, last = [], date.today().strftime("%Y-%m")
    preds, method = holt_forecast(values, horizon)
    return {
        "method": method,
        "history_months": len(values),
        "forecast": [{"period": p, "qty": q} for p, q in zip(_next_periods(last, horizon), preds)],
    }


def _fill_gaps(history: list[tuple[str, float]]) -> list[tuple[str, float]]:
    d = dict(history)
    first, last = min(d), max(d)
    out, cur = [], first
    while True:
        out.append((cur, float(d.get(cur, 0.0))))
        if cur == last:
            return out
        cur = _next_periods(cur, 1)[0]
