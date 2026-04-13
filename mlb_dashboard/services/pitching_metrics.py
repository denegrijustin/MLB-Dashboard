from __future__ import annotations

import pandas as pd

from utils.formatting import stoplight


def innings_to_float(ip: str | float | int) -> float:
    if isinstance(ip, (float, int)):
        return float(ip)
    whole, _, frac = str(ip).partition(".")
    outs = int(whole) * 3 + int(frac or 0)
    return outs / 3


def summarize_pitchers(pitch_rows: list[dict]) -> pd.DataFrame:
    df = pd.DataFrame(pitch_rows)
    if df.empty:
        return df
    df["ip_float"] = df["ip"].map(innings_to_float)
    grouped = df.groupby(["player_id", "pitcher"], as_index=False).agg(
        ip=("ip_float", "sum"),
        er=("er", "sum"),
        so=("so", "sum"),
        bb=("bb", "sum"),
        hr=("hr", "sum"),
        hits=("hits", "sum"),
    )
    grouped["impact"] = (
        100
        - grouped["er"] * 12
        - grouped["bb"] * 4
        - grouped["hr"] * 8
        + grouped["so"] * 3
        + grouped["ip"] * 2
    ).clip(0, 100)
    trend_rows = []
    for (player_id, pitcher), group in df.groupby(["player_id", "pitcher"]):
        recent = group.tail(1)
        earlier = group.head(max(1, len(group) - 1))
        recent_score = (100 - recent["er"].sum() * 12 - recent["bb"].sum() * 4 - recent["hr"].sum() * 8 + recent["so"].sum() * 3)
        earlier_score = (100 - earlier["er"].sum() * 12 - earlier["bb"].sum() * 4 - earlier["hr"].sum() * 8 + earlier["so"].sum() * 3)
        trend_rows.append({"player_id": player_id, "pitcher": pitcher, "trend": stoplight(recent_score - earlier_score)})
    grouped = grouped.merge(pd.DataFrame(trend_rows), on=["player_id", "pitcher"], how="left")
    grouped["ip"] = grouped["ip"].round(1)
    grouped["impact"] = grouped["impact"].round(1)
    return grouped.sort_values("impact", ascending=False).reset_index(drop=True)
