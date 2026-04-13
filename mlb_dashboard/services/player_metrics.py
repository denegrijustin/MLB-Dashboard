from __future__ import annotations

import numpy as np
import pandas as pd

from utils.formatting import stoplight


def build_player_game_log(player_rows: list[dict]) -> pd.DataFrame:
    df = pd.DataFrame(player_rows)
    if not df.empty:
        df["date"] = pd.to_datetime(df["date"])
    return df


def _impact_score(df: pd.DataFrame) -> pd.Series:
    # Weighted 0-100 score
    ob_component = df["ob_events"] * 8
    xbh_component = df["xbh"] * 12
    run_component = (df["rbi"] + df["runs"]) * 5
    so_component = np.maximum(0, 12 - df["so"] * 3)
    clutch_component = (df["rbi"] * 6) + (df["productive_outs"] * 4)
    raw = 0.35 * ob_component + 0.25 * xbh_component + 0.20 * run_component + 0.10 * so_component + 0.10 * clutch_component
    return raw.clip(0, 100)


def _consistency(group: pd.DataFrame) -> float:
    if len(group) == 1:
        return 55.0
    ob_var = group["ob_events"].std(ddof=0)
    so_var = group["so"].std(ddof=0)
    impact_var = group["impact_score"].std(ddof=0)
    zero_games = (group["impact_score"] <= 20).mean()
    score = 100 - (ob_var * 18 + so_var * 10 + impact_var * 0.45 + zero_games * 25)
    return max(0.0, min(100.0, score))


def _clutch(group: pd.DataFrame) -> float:
    rbi = group["rbi"].sum() * 8
    prod = group["productive_outs"].sum() * 7
    xbh = group["xbh"].sum() * 9
    late = group.loc[group["date"] >= group["date"].max() - pd.Timedelta(days=7), "rbi"].sum() * 4
    contact = max(0, group["h"].sum() * 3 - group["so"].sum())
    return min(100.0, 0.30 * rbi + 0.20 * prod + 0.20 * xbh + 0.15 * late + 0.15 * contact)


def summarize_players(player_game_log: pd.DataFrame) -> tuple[pd.DataFrame, pd.DataFrame, pd.DataFrame]:
    if player_game_log.empty:
        empty = pd.DataFrame()
        return empty, empty, empty
    df = player_game_log.copy()
    df["impact_score"] = _impact_score(df)
    agg = df.groupby(["player_id", "player"], as_index=False).agg(
        ob_events=("ob_events", "sum"),
        xbh=("xbh", "sum"),
        so=("so", "sum"),
        rbi=("rbi", "sum"),
        runs=("runs", "sum"),
        impact=("impact_score", "mean"),
    )
    consistency_rows = []
    clutch_rows = []
    trend_rows = []
    for (player_id, player), group in df.groupby(["player_id", "player"]):
        consistency = _consistency(group)
        clutch = _clutch(group)
        last_two = group.sort_values("date").tail(2)["impact_score"].mean()
        prev = group.sort_values("date").head(max(1, len(group) - 2))["impact_score"].mean() if len(group) > 2 else group["impact_score"].iloc[0]
        trend = stoplight(last_two - prev)
        consistency_rows.append({"player_id": player_id, "player": player, "consistency_score": round(consistency, 1), "consistency_trend": trend})
        clutch_rows.append({"player_id": player_id, "player": player, "clutch_score": round(clutch, 1), "clutch_trend": trend})
        trend_rows.append({"player_id": player_id, "player": player, "trend": trend})
    out = agg.merge(pd.DataFrame(consistency_rows), on=["player_id", "player"]).merge(pd.DataFrame(clutch_rows), on=["player_id", "player"]).merge(pd.DataFrame(trend_rows), on=["player_id", "player"])
    out["impact"] = out["impact"].round(1)
    out["grade"] = pd.cut(out["impact"], bins=[-1, 29.99, 49.99, 64.99, 79.99, 100], labels=["F", "D", "C", "B", "A"])
    out = out.sort_values(["impact", "consistency_score"], ascending=False).reset_index(drop=True)
    return out, pd.DataFrame(clutch_rows).sort_values("clutch_score", ascending=False), pd.DataFrame(consistency_rows).sort_values("consistency_score", ascending=False)
