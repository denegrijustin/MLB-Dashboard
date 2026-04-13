from __future__ import annotations

import numpy as np
import pandas as pd

from models.constants import PITCH_TYPE_MAP
from utils.formatting import stoplight


def _numeric(df: pd.DataFrame, cols: list[str]) -> pd.DataFrame:
    for col in cols:
        if col in df.columns:
            df[col] = pd.to_numeric(df[col], errors="coerce")
    return df


def summarize_hitter_statcast(events: pd.DataFrame, player_lookup: dict[int, str], team_abbrev: str) -> pd.DataFrame:
    if events.empty:
        return pd.DataFrame(columns=["player_id", "player", "avg_exit_velocity", "hard_hit_pct", "avg_hr_distance", "home_hr_dist", "away_hr_dist", "trend"])
    df = events.copy()
    df = _numeric(df, ["launch_speed", "hit_distance_sc"])
    if "batter" not in df.columns:
        return pd.DataFrame()
    rows = []
    for pid, group in df.groupby("batter"):
        player = player_lookup.get(int(pid), str(pid))
        batted = group.dropna(subset=["launch_speed"])
        hr = group[group.get("events", "").eq("home_run") if "events" in group.columns else False]
        home_hr = hr[hr.get("home_team") == team_abbrev] if "home_team" in hr.columns else pd.DataFrame()
        away_hr = hr[hr.get("away_team") == team_abbrev] if "away_team" in hr.columns else pd.DataFrame()
        recent = batted.tail(max(1, len(batted) // 3))["launch_speed"].mean() if not batted.empty else np.nan
        earlier = batted.head(max(1, len(batted) - max(1, len(batted) // 3)))["launch_speed"].mean() if not batted.empty else np.nan
        rows.append(
            {
                "player_id": int(pid),
                "player": player,
                "avg_exit_velocity": round(float(batted["launch_speed"].mean()), 1) if not batted.empty else None,
                "hard_hit_pct": round(float((batted["launch_speed"] >= 95).mean() * 100), 1) if not batted.empty else None,
                "avg_hr_distance": round(float(hr["hit_distance_sc"].mean()), 1) if not hr.empty and "hit_distance_sc" in hr.columns else None,
                "home_hr_dist": round(float(home_hr["hit_distance_sc"].mean()), 1) if not home_hr.empty and "hit_distance_sc" in home_hr.columns else None,
                "away_hr_dist": round(float(away_hr["hit_distance_sc"].mean()), 1) if not away_hr.empty and "hit_distance_sc" in away_hr.columns else None,
                "trend": stoplight((recent or 0) - (earlier or 0)),
            }
        )
    return pd.DataFrame(rows).sort_values("avg_exit_velocity", ascending=False, na_position="last")


def summarize_pitcher_statcast(events: pd.DataFrame, player_lookup: dict[int, str]) -> tuple[pd.DataFrame, pd.DataFrame, dict]:
    if events.empty:
        return pd.DataFrame(), pd.DataFrame(), {}
    df = events.copy()
    df = _numeric(df, ["release_spin_rate", "release_speed", "launch_speed"])
    player_col = "pitcher" if "pitcher" in df.columns else None
    if player_col is None:
        return pd.DataFrame(), pd.DataFrame(), {}
    pitcher_rows = []
    pitch_mix_rows = []
    for pid, group in df.groupby(player_col):
        player = player_lookup.get(int(pid), str(pid))
        recent = group.tail(max(1, len(group) // 3))["release_spin_rate"].mean()
        earlier = group.head(max(1, len(group) - max(1, len(group) // 3)))["release_spin_rate"].mean()
        pitcher_rows.append(
            {
                "player_id": int(pid),
                "pitcher": player,
                "avg_exit_velocity_allowed": round(float(group["launch_speed"].mean()), 1) if "launch_speed" in group else None,
                "avg_spin_rate": round(float(group["release_spin_rate"].mean()), 1) if "release_spin_rate" in group else None,
                "avg_velocity": round(float(group["release_speed"].mean()), 1) if "release_speed" in group else None,
                "trend": stoplight((recent or 0) - (earlier or 0)),
            }
        )
        if "pitch_type" in group.columns:
            counts = group["pitch_type"].fillna("UNK").value_counts(normalize=True)
            for pitch_type, pct in counts.items():
                sub = group[group["pitch_type"] == pitch_type]
                pitch_mix_rows.append(
                    {
                        "player_id": int(pid),
                        "pitcher": player,
                        "pitch_type": PITCH_TYPE_MAP.get(pitch_type, pitch_type),
                        "usage_pct": round(pct * 100, 1),
                        "avg_spin_rate": round(float(sub["release_spin_rate"].mean()), 1) if "release_spin_rate" in sub else None,
                        "avg_velocity": round(float(sub["release_speed"].mean()), 1) if "release_speed" in sub else None,
                    }
                )
    team_summary = {
        "team_avg_exit_velocity": round(float(df["launch_speed"].mean()), 1) if "launch_speed" in df.columns else None,
        "team_avg_spin_rate": round(float(df["release_spin_rate"].mean()), 1) if "release_spin_rate" in df.columns else None,
    }
    return pd.DataFrame(pitcher_rows).sort_values("avg_spin_rate", ascending=False, na_position="last"), pd.DataFrame(pitch_mix_rows), team_summary
