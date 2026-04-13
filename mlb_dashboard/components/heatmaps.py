from __future__ import annotations

import pandas as pd
import plotly.graph_objects as go



def inning_heatmap(inning_df: pd.DataFrame, value_col: str, title: str):
    if inning_df.empty or value_col not in inning_df.columns:
        return None
    z = [inning_df[value_col].tolist()]
    x = inning_df["inning"].tolist()
    custom = [[f"Inning {i}: {v}" for i, v in zip(x, inning_df[value_col].tolist())]]
    fig = go.Figure(
        data=go.Heatmap(
            z=z,
            x=x,
            y=[title],
            text=custom,
            texttemplate="%{z}",
            textfont={"size": 14},
            hovertemplate="%{text}<extra></extra>",
            colorscale="Blues",
            showscale=False,
            xgap=4,
            ygap=4,
        )
    )
    fig.update_layout(
        title=title,
        height=220,
        margin=dict(l=10, r=10, t=48, b=10),
        paper_bgcolor="rgba(0,0,0,0)",
        plot_bgcolor="rgba(255,255,255,0.98)",
    )
    fig.update_xaxes(title=None, side="top")
    fig.update_yaxes(title=None)
    return fig
