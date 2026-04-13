import pandas as pd
from typing import List


def build_hitter_impact(game_log_rows: list) -> pd.DataFrame:
    if not game_log_rows:
        return pd.DataFrame(columns=["player", "games", "avg_impact", "ob_events", "xbh", "rbi", "runs", "so", "trend", "grade"])
    df = pd.DataFrame(game_log_rows)
    return df


def build_starter_impact(pitch_rows: list) -> pd.DataFrame:
    if not pitch_rows:
        return pd.DataFrame(columns=["pitcher", "games_started", "ip", "era", "k_per_9", "bb_per_9", "hr_per_9", "impact", "trend"])
    df = pd.DataFrame(pitch_rows)
    return df


def build_reliever_impact(pitch_rows: list, is_closer_ids: list = None) -> pd.DataFrame:
    if not pitch_rows:
        return pd.DataFrame(columns=["pitcher", "appearances", "ip", "era", "k_per_9", "saves", "holds", "impact"])
    closer_ids = set(is_closer_ids or [])
    rows = [r for r in pitch_rows if r.get("player_id") not in closer_ids]
    if not rows:
        return pd.DataFrame(columns=["pitcher", "appearances", "ip", "era", "k_per_9", "saves", "holds", "impact"])
    return pd.DataFrame(rows)


def build_closer_impact(pitch_rows: list, closer_ids: list = None) -> pd.DataFrame:
    if not pitch_rows:
        return pd.DataFrame(columns=["pitcher", "appearances", "ip", "era", "saves", "blown_saves", "impact"])
    ids = set(closer_ids or [])
    rows = [r for r in pitch_rows if r.get("player_id") in ids]
    if not rows:
        return pd.DataFrame(columns=["pitcher", "appearances", "ip", "era", "saves", "blown_saves", "impact"])
    return pd.DataFrame(rows)
