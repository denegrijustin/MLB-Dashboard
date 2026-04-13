from __future__ import annotations

import pandas as pd

from utils.formatting import confidence_label


def recommend_lineup(player_summary: pd.DataFrame) -> pd.DataFrame:
    if player_summary.empty:
        return pd.DataFrame()
    df = player_summary.copy()
    df["lineup_score"] = (
        df["ob_events"] * 2.0
        + df["impact"] * 0.8
        + df["xbh"] * 3.0
        - df["so"] * 0.6
        + df["clutch_score"] * 0.2
    )
    df = df.sort_values("lineup_score", ascending=False).reset_index(drop=True)
    df["slot"] = range(1, len(df) + 1)
    max_score = max(df["lineup_score"].max(), 1)
    df["confidence"] = df["lineup_score"].map(lambda x: confidence_label(x / max_score))
    return df[["slot", "player", "confidence"]]
