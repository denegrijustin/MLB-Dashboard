from typing import Optional
import pandas as pd
import plotly.graph_objects as go
import numpy as np

HIT_EVENTS = {"single", "double", "triple", "home_run"}
REQUIRED_COLS = {"hc_x", "hc_y"}
BB_TYPE_COLORS = {
    "fly_ball": "#e74c3c",
    "line_drive": "#2ecc71",
    "ground_ball": "#3498db",
    "popup": "#f39c12",
}
EVENT_COLORS = {
    "single": "#2ecc71",
    "double": "#f39c12",
    "triple": "#9b59b6",
    "home_run": "#e74c3c",
}


def filter_hit_events(df: pd.DataFrame) -> pd.DataFrame:
    if df is None or df.empty:
        return pd.DataFrame()
    if "events" not in df.columns:
        return pd.DataFrame()
    return df[df["events"].isin(HIT_EVENTS)].copy()


def filter_batted_balls(df: pd.DataFrame) -> pd.DataFrame:
    if df is None or df.empty:
        return pd.DataFrame()
    if not REQUIRED_COLS.issubset(df.columns):
        return pd.DataFrame()
    result = df.dropna(subset=["hc_x", "hc_y"]).copy()
    return result


def _arc_path(cx, cy, r, start_deg, end_deg, steps=60):
    import math
    points = []
    for i in range(steps + 1):
        angle = math.radians(start_deg + (end_deg - start_deg) * i / steps)
        x = cx + r * math.cos(angle)
        y = cy + r * math.sin(angle)
        points.append(f"{'M' if i == 0 else 'L'} {x:.2f} {y:.2f}")
    return " ".join(points)


def make_spray_chart(df: pd.DataFrame, title: str = "Spray Chart") -> Optional[go.Figure]:
    if df is None or df.empty:
        return None
    if not REQUIRED_COLS.issubset(df.columns):
        return None

    plot_df = df.dropna(subset=["hc_x", "hc_y"]).copy()
    if plot_df.empty:
        return None

    # Transform coordinates: center at home plate
    plot_df["plot_x"] = plot_df["hc_x"] - 125
    plot_df["plot_y"] = 200 - plot_df["hc_y"]

    # Color by event type if available, else by bb_type
    if "events" in plot_df.columns:
        plot_df["color_key"] = plot_df["events"].fillna("other")
        color_map = EVENT_COLORS
    elif "bb_type" in plot_df.columns:
        plot_df["color_key"] = plot_df["bb_type"].fillna("other")
        color_map = BB_TYPE_COLORS
    else:
        plot_df["color_key"] = "batted_ball"
        color_map = {"batted_ball": "#3498db"}

    fig = go.Figure()

    # Plot points by category
    for key, color in color_map.items():
        subset = plot_df[plot_df["color_key"] == key]
        if subset.empty:
            continue

        extra_hover = []
        for _, row in subset.iterrows():
            parts = [f"Type: {key}"]
            if "launch_speed" in subset.columns and pd.notna(row.get("launch_speed")):
                parts.append(f"Exit Velo: {row['launch_speed']:.1f} mph")
            if "launch_angle" in subset.columns and pd.notna(row.get("launch_angle")):
                parts.append(f"Launch Angle: {row['launch_angle']:.1f}°")
            if "hit_distance_sc" in subset.columns and pd.notna(row.get("hit_distance_sc")):
                parts.append(f"Distance: {row['hit_distance_sc']:.0f} ft")
            extra_hover.append("<br>".join(parts))

        fig.add_trace(go.Scatter(
            x=subset["plot_x"],
            y=subset["plot_y"],
            mode="markers",
            marker=dict(color=color, size=8, opacity=0.75, line=dict(width=0.5, color="white")),
            name=key.replace("_", " ").title(),
            text=extra_hover,
            hovertemplate="%{text}<extra></extra>",
        ))

    # Add "other" category points
    other = plot_df[~plot_df["color_key"].isin(color_map.keys())]
    if not other.empty:
        fig.add_trace(go.Scatter(
            x=other["plot_x"], y=other["plot_y"],
            mode="markers",
            marker=dict(color="#95a5a6", size=6, opacity=0.5),
            name="Other",
            hovertemplate="Other<extra></extra>",
        ))

    # Draw foul lines
    scale = 2.5
    fig.add_shape(type="line", x0=0, y0=-2, x1=-330 / scale, y1=330 / scale,
                  line=dict(color="rgba(255,255,255,0.5)", width=1.5, dash="dot"))
    fig.add_shape(type="line", x0=0, y0=-2, x1=330 / scale, y1=330 / scale,
                  line=dict(color="rgba(255,255,255,0.5)", width=1.5, dash="dot"))

    # Outfield arc
    import math
    arc_r = 400 / scale
    arc_points_x = [arc_r * math.cos(math.radians(a)) for a in range(-135, -44)]
    arc_points_y = [-2 + arc_r * math.sin(math.radians(a)) for a in range(-135, -44)]
    fig.add_trace(go.Scatter(
        x=arc_points_x, y=arc_points_y,
        mode="lines", line=dict(color="rgba(255,255,255,0.5)", width=1.5, dash="dot"),
        showlegend=False, hoverinfo="skip"
    ))

    # Infield circle
    infield_r = 95 / scale
    infield_x = [infield_r * math.cos(math.radians(a)) for a in range(0, 361)]
    infield_y = [-2 + infield_r * math.sin(math.radians(a)) for a in range(0, 361)]
    fig.add_trace(go.Scatter(
        x=infield_x, y=infield_y,
        mode="lines", line=dict(color="rgba(255,255,255,0.2)", width=1),
        showlegend=False, hoverinfo="skip"
    ))

    fig.update_layout(
        title=dict(text=title, font=dict(color="white", size=16)),
        paper_bgcolor="#1a1a2e",
        plot_bgcolor="#2d5a27",
        xaxis=dict(
            range=[-200, 200],
            showgrid=False, zeroline=False, showticklabels=False,
            title=""
        ),
        yaxis=dict(
            range=[-30, 200],
            showgrid=False, zeroline=False, showticklabels=False,
            title="", scaleanchor="x", scaleratio=1
        ),
        legend=dict(
            bgcolor="rgba(0,0,0,0.5)", font=dict(color="white"),
            orientation="h", yanchor="bottom", y=1.02, xanchor="right", x=1
        ),
        height=500,
        margin=dict(l=20, r=20, t=60, b=20),
    )

    return fig
