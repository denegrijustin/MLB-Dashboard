from __future__ import annotations

from typing import Iterable


def stoplight(delta: float, better_high: bool = True, tol: float = 1e-9) -> str:
    if abs(delta) <= tol:
        return "🟡"
    improving = delta > 0 if better_high else delta < 0
    return "🟢" if improving else "🔴"


def safe_div(numerator: float, denominator: float) -> float:
    return numerator / denominator if denominator else 0.0


def pct(value: float, digits: int = 1) -> str:
    return f"{value * 100:.{digits}f}%"


def round_or_none(value, digits: int = 2):
    if value is None:
        return None
    try:
        return round(float(value), digits)
    except Exception:
        return None


def trend_vs_previous(current: float, previous: float, better_high: bool = True) -> str:
    return stoplight(current - previous, better_high=better_high)


def confidence_label(score: float) -> str:
    if score >= 0.75:
        return "High"
    if score >= 0.55:
        return "Medium"
    return "Low"


def first_valid(values: Iterable):
    for value in values:
        if value not in (None, "", float("nan")):
            return value
    return None
