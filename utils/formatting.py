from typing import Optional


def format_pct(value: float) -> str:
    return f"{value:.3f}"


def format_era(era: float) -> str:
    return f"{era:.2f}"


def format_record(wins: int, losses: int) -> str:
    return f"{wins}-{losses}"


def format_gb(gb) -> str:
    if gb == 0 or gb == "0" or gb == "-":
        return "-"
    return str(gb)


def format_streak(streak_code: str) -> str:
    if not streak_code:
        return ""
    return streak_code


def safe_float(val, default=0.0) -> float:
    try:
        return float(val)
    except (TypeError, ValueError):
        return default


def safe_int(val, default=0) -> int:
    try:
        return int(val)
    except (TypeError, ValueError):
        return default
