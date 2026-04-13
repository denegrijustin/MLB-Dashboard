from __future__ import annotations

import pandas as pd
import plotly.express as px
import plotly.graph_objects as go


PLOT_TEMPLATE = "plotly_white"


def _base_layout(fig: go.Figure, height: int = 330) -> go.Figure:
    fig.update_layout(
        template=PLOT_TEMPLATE,
        height=height,
        margin=dict(l=12, r=12, t=52, b=12),
        paper_bgcolor="rgba(0,0,0,0)",
        plot_bgcolor="rgba(255,255,255,0.98)",
        font=dict(size=13),
        title=dict(x=0.02, xanchor="left"),
    )
    return fig


def playoff_chart(probabilities: dict):
    df = pd.DataFrame(
        {
            "Category": ["Playoff", "Division", "Wild Card"],
            "Probability": [
                probabilities.get("playoff_probability", 0),
                probabilities.get("division_probability", 0),
                probabilities.get("wild_card_probability", 0),
            ],
        }
    )
    fig = px.bar(df, x="Category", y="Probability", text="Probability", title="Estimated Postseason Outlook")
    fig.update_yaxes(range=[0, 100], title="Probability %")
    fig.update_traces(texttemplate="%{text:.1f}%", textposition="outside")
    return _base_layout(fig)


def exit_velocity_chart(df: pd.DataFrame):
    if df.empty or "avg_exit_velocity" not in df.columns:
        return None
    plot_df = (
        df.dropna(subset=["avg_exit_velocity"])
        .sort_values("avg_exit_velocity", ascending=False)
        .head(12)
    )
    if plot_df.empty:
        return None
    fig = px.bar(
        plot_df,
        x="avg_exit_velocity",
        y="player",
        orientation="h",
        title="Average Exit Velocity Leaders",
        text="avg_exit_velocity",
    )
    fig.update_traces(texttemplate="%{text:.1f} mph", textposition="outside")
    fig.update_yaxes(categoryorder="total ascending")
    fig.update_xaxes(title="Average Exit Velocity")
    return _base_layout(fig, height=420)


def pitch_mix_chart(df: pd.DataFrame, pitcher: str):
    plot_df = df[df["pitcher"] == pitcher].copy()
    if plot_df.empty:
        return None
    fig = px.pie(plot_df, names="pitch_type", values="usage_pct", hole=0.5, title=f"Pitch Mix: {pitcher}")
    fig.update_traces(texttemplate="%{label}<br>%{value:.1f}%")
    return _base_layout(fig, height=380)


def win_probability_chart(df: pd.DataFrame):
    if df.empty or "win_probability" not in df.columns:
        return None
    plot_df = df.copy()
    label_col = "opponent" if "opponent" in plot_df.columns else plot_df.columns[0]
    fig = px.bar(
        plot_df,
        x=label_col,
        y="win_probability",
        title="Next 5 Games Win Likelihood",
        text="win_probability",
    )
    fig.update_yaxes(title="Win Probability %", range=[0, 100])
    fig.update_traces(texttemplate="%{text:.1f}%", textposition="outside")
    return _base_layout(fig)


def rolling_runs_chart(game_log: pd.DataFrame):
    if game_log.empty or "team_score" not in game_log.columns:
        return None
    plot_df = game_log.dropna(subset=["team_score", "opp_score"]).copy().tail(15)
    if plot_df.empty:
        return None
    if "game_date" in plot_df.columns:
        plot_df["label"] = pd.to_datetime(plot_df["game_date"]).dt.strftime("%m/%d")
    else:
        plot_df["label"] = range(1, len(plot_df) + 1)
    fig = go.Figure()
    fig.add_trace(go.Scatter(x=plot_df["label"], y=plot_df["team_score"], mode="lines+markers", name="Runs For"))
    fig.add_trace(go.Scatter(x=plot_df["label"], y=plot_df["opp_score"], mode="lines+markers", name="Runs Against"))
    fig.update_yaxes(title="Runs")
    fig.update_xaxes(title="Game")
    fig.update_layout(title="Recent Game Trend")
    return _base_layout(fig, height=360)
