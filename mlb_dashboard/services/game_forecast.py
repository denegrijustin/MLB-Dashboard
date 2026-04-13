from __future__ import annotations

from datetime import datetime

import pandas as pd

from utils.formatting import confidence_label


def forecast_next_five(game_log: pd.DataFrame, upcoming: pd.DataFrame, team_summary: dict) -> pd.DataFrame:
    if upcoming.empty:
        return pd.DataFrame()
    recent = game_log.dropna(subset=["team_score", "opp_score"]).tail(10)
    avg_scored = recent["team_score"].mean() if not recent.empty else team_summary["avg_runs"]
    avg_allowed = recent["opp_score"].mean() if not recent.empty else team_summary["avg_runs_allowed"]
    home_boost = 0.04
    rows = []
    for _, row in upcoming.head(5).iterrows():
        base = 0.50
        base += (avg_scored - avg_allowed) * 0.03
        base += 0.02 if row["is_home"] else -home_boost
        win_prob = max(0.15, min(0.85, base))
        rows.append(
            {
                "date": row["date"].date().isoformat(),
                "opponent": row["opponent"],
                "home_away": "Home" if row["is_home"] else "Away",
                "win_probability": round(win_prob * 100, 1),
                "confidence": confidence_label(abs(win_prob - 0.5) * 2),
                "key_factors": "recent scoring trend, run prevention, home/away split",
            }
        )
    return pd.DataFrame(rows)
