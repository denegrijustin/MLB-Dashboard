import pandas as pd
from typing import Optional


def filter_home_runs(df: pd.DataFrame) -> pd.DataFrame:
    if df is None or df.empty:
        return pd.DataFrame()
    if "events" not in df.columns:
        return pd.DataFrame()
    return df[df["events"] == "home_run"].copy()


def build_hr_table(df: pd.DataFrame) -> pd.DataFrame:
    if df is None or df.empty:
        return pd.DataFrame()
    hr_df = filter_home_runs(df)
    if hr_df.empty:
        return pd.DataFrame()

    cols_map = {
        "player_name": "Player",
        "hit_distance_sc": "Distance (ft)",
        "launch_speed": "Exit Velo (mph)",
        "launch_angle": "Launch Angle (°)",
        "game_date": "Date",
        "inning": "Inning",
        "home_team": "Home Team",
        "away_team": "Away Team",
    }
    available = {k: v for k, v in cols_map.items() if k in hr_df.columns}
    if not available:
        return pd.DataFrame()

    result = hr_df[list(available.keys())].copy()
    result = result.rename(columns=available)

    if "Distance (ft)" in result.columns:
        result["Distance (ft)"] = pd.to_numeric(result["Distance (ft)"], errors="coerce").round(0)
    if "Exit Velo (mph)" in result.columns:
        result["Exit Velo (mph)"] = pd.to_numeric(result["Exit Velo (mph)"], errors="coerce").round(1)
    if "Launch Angle (°)" in result.columns:
        result["Launch Angle (°)"] = pd.to_numeric(result["Launch Angle (°)"], errors="coerce").round(1)
    if "Date" in result.columns:
        result = result.sort_values("Date", ascending=False)

    return result.reset_index(drop=True)


def team_hr_summary(df: pd.DataFrame, team_abbrev: str) -> dict:
    hr_df = filter_home_runs(df)
    if hr_df.empty:
        return {
            "total_hrs": 0,
            "avg_distance": None,
            "avg_exit_velo": None,
            "avg_launch_angle": None,
            "longest_hr": None,
        }

    total = len(hr_df)
    avg_dist = None
    avg_velo = None
    avg_angle = None
    longest = None

    if "hit_distance_sc" in hr_df.columns:
        dist_series = pd.to_numeric(hr_df["hit_distance_sc"], errors="coerce").dropna()
        if not dist_series.empty:
            avg_dist = round(dist_series.mean(), 1)
            longest = round(dist_series.max(), 0)

    if "launch_speed" in hr_df.columns:
        velo_series = pd.to_numeric(hr_df["launch_speed"], errors="coerce").dropna()
        if not velo_series.empty:
            avg_velo = round(velo_series.mean(), 1)

    if "launch_angle" in hr_df.columns:
        angle_series = pd.to_numeric(hr_df["launch_angle"], errors="coerce").dropna()
        if not angle_series.empty:
            avg_angle = round(angle_series.mean(), 1)

    return {
        "total_hrs": total,
        "avg_distance": avg_dist,
        "avg_exit_velo": avg_velo,
        "avg_launch_angle": avg_angle,
        "longest_hr": longest,
    }
