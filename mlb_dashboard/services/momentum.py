from __future__ import annotations

import pandas as pd


def summarize_momentum(rows: list[dict]) -> pd.DataFrame:
    df = pd.DataFrame(rows)
    if df.empty:
        return df
    return df[["game_pk", "inning", "event", "impact"]].rename(columns={"game_pk": "game"}).head(20)
