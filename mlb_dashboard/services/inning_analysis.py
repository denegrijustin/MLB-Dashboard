from __future__ import annotations

import pandas as pd


def heatmap_labels(values: pd.Series, against: bool = False) -> list[str]:
    labels = []
    for val in values:
        if val == 0:
            labels.append("⬜")
        elif val == 1:
            labels.append("🟦")
        elif val == 2:
            labels.append("🟩")
        else:
            labels.append("🟥")
    return labels


def build_heatmap_table(inning_df: pd.DataFrame, col: str) -> pd.DataFrame:
    if inning_df.empty:
        return pd.DataFrame()
    row = inning_df.set_index("inning")[col]
    intensity = heatmap_labels(row)
    return pd.DataFrame([row.tolist(), intensity], index=["Runs", "Intensity"], columns=row.index.tolist())
