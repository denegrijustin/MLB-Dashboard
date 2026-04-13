from __future__ import annotations

from datetime import date
from pathlib import Path
import sys

import pandas as pd
import streamlit as st

ROOT = Path(__file__).parent
if str(ROOT) not in sys.path:
    sys.path.append(str(ROOT))

from api.mlb_client import MLBClient
from api.statcast_client import StatcastClient
from components.charts import (
    exit_velocity_chart,
    pitch_mix_chart,
    playoff_chart,
    rolling_runs_chart,
    win_probability_chart,
)
from components.heatmaps import inning_heatmap
from components.tables import show_table
from models.constants import SEASON_DEFAULT, SECTION_HELP, TEAM_ID_DEFAULT
from services.advanced_metrics import summarize_hitter_statcast, summarize_pitcher_statcast
from services.game_forecast import forecast_next_five
from services.inning_analysis import build_heatmap_table
from services.lineup_model import recommend_lineup
from services.momentum import summarize_momentum
from services.pitching_metrics import summarize_pitchers
from services.player_metrics import build_player_game_log, summarize_players
from services.playoff_model import estimate_playoff_probability, extract_standings_rows
from services.team_stats import (
    aggregate_innings,
    build_game_log,
    extract_team_context,
    is_completed_game,
    parse_game_offense,
    parse_game_pitching,
    parse_linescore,
    parse_momentum,
    summarize_team,
)
from utils.formatting import stoplight

st.set_page_config(page_title="MLB Dashboard", page_icon="⚾", layout="wide")


CSS = """
<style>
    .stApp {
        background: linear-gradient(180deg, #f7f9fc 0%, #eef3f9 100%);
    }
    .block-container {
        padding-top: 1.25rem;
        padding-bottom: 2rem;
        max-width: 1450px;
    }
    .hero {
        background: linear-gradient(135deg, #ffffff 0%, #f4f8ff 100%);
        border: 1px solid rgba(15, 23, 42, 0.08);
        border-radius: 20px;
        padding: 20px 24px;
        margin-bottom: 1rem;
        box-shadow: 0 10px 30px rgba(15, 23, 42, 0.06);
    }
    .hero h1 {
        margin: 0;
        font-size: 2rem;
    }
    .hero p {
        margin: 0.35rem 0 0 0;
        color: #475569;
    }
    .section-card {
        background: rgba(255,255,255,0.92);
        border: 1px solid rgba(15, 23, 42, 0.08);
        border-radius: 18px;
        padding: 14px 16px 16px 16px;
        box-shadow: 0 6px 22px rgba(15, 23, 42, 0.05);
        margin-bottom: 1rem;
    }
    .section-title {
        font-size: 1.08rem;
        font-weight: 700;
        margin-bottom: 0.15rem;
        color: #0f172a;
    }
    .section-subtitle {
        color: #475569;
        font-size: 0.94rem;
        margin-bottom: 0.75rem;
    }
    div[data-testid="stMetric"] {
        background: rgba(255,255,255,0.96);
        border: 1px solid rgba(15, 23, 42, 0.08);
        border-radius: 18px;
        padding: 0.65rem 0.85rem;
        box-shadow: 0 6px 18px rgba(15, 23, 42, 0.04);
    }
    div[data-testid="stMetricLabel"] {
        color: #64748b;
        font-weight: 600;
    }
    div[data-testid="stMetricValue"] {
        color: #0f172a;
    }
    .sidebar-note {
        background: rgba(255,255,255,0.9);
        border: 1px solid rgba(15, 23, 42, 0.08);
        border-radius: 14px;
        padding: 12px;
        font-size: 0.92rem;
        color: #475569;
        margin-top: 0.75rem;
    }
</style>
"""

st.markdown(CSS, unsafe_allow_html=True)

st.markdown(
    """
    <div class="hero">
        <h1>Live MLB Analytics Dashboard</h1>
        <p>Streamlit app powered by MLB StatsAPI and Baseball Savant Statcast data with a cleaner executive-style UI.</p>
    </div>
    """,
    unsafe_allow_html=True,
)

mlb = MLBClient()
statcast = StatcastClient()


@st.cache_data(ttl=3600, show_spinner=False)
def load_teams():
    teams = mlb.get_teams()
    df = pd.DataFrame(
        [
            {
                "id": t["id"],
                "name": t["name"],
                "abbrev": t.get("abbreviation", t.get("fileCode", "").upper()),
                "league_id": t.get("league", {}).get("id", 103),
            }
            for t in teams
        ]
    ).sort_values("name")
    return df


@st.cache_data(ttl=900, show_spinner=True)
def load_dashboard(team_id: int, season: int, start_date: str | None, end_date: str | None):
    schedule = mlb.get_schedule(team_id, season, start_date, end_date)
    team = mlb.get_team(team_id)
    if team is None:
        raise ValueError("Team not found")
    context = extract_team_context(team)
    game_log = build_game_log(schedule, team_id)
    completed_games = [g for g in schedule if is_completed_game(g)]

    player_rows = []
    pitch_rows = []
    inning_rows = []
    momentum_rows = []
    player_lookup = {}
    for game in completed_games:
        feed = mlb.get_game_feed(game["gamePk"])
        offense = parse_game_offense(feed, team_id)
        player_rows.extend(offense["player_rows"])
        for row in offense["player_rows"]:
            player_lookup[row["player_id"]] = row["player"]
        pitch_rows.extend(parse_game_pitching(feed, team_id))
        inning_rows.extend(parse_linescore(feed, team_id))
        momentum_rows.extend(parse_momentum(feed, team_id))

    player_game_log = build_player_game_log(player_rows)
    player_summary, clutch_df, consistency_df = summarize_players(player_game_log)
    pitching_df = summarize_pitchers(pitch_rows)
    inning_df = aggregate_innings(inning_rows)
    team_summary = summarize_team(game_log)

    standings = mlb.get_standings(context.league_id, season)
    wild = mlb.get_wild_card(context.league_id, season)
    standings_row = extract_standings_rows(standings, team_id)
    wild_row = extract_standings_rows(wild, team_id)
    playoff_probs = estimate_playoff_probability(team_summary, standings_row, wild_row)

    upcoming = game_log[game_log["team_score"].isna()].copy()
    next_five = forecast_next_five(game_log, upcoming, team_summary)

    hitter_statcast = pd.DataFrame()
    pitcher_statcast = pd.DataFrame()
    pitch_mix = pd.DataFrame()
    team_statcast_summary = {}
    try:
        team_events = statcast.team_events(season, context.team_abbrev)
        hitter_statcast = summarize_hitter_statcast(team_events, player_lookup, context.team_abbrev)
        pitcher_statcast, pitch_mix, team_statcast_summary = summarize_pitcher_statcast(team_events, player_lookup)
    except Exception:
        pass

    return {
        "context": context,
        "game_log": game_log,
        "team_summary": team_summary,
        "player_summary": player_summary,
        "clutch_df": clutch_df,
        "consistency_df": consistency_df,
        "pitching_df": pitching_df,
        "inning_df": inning_df,
        "momentum_df": summarize_momentum(momentum_rows),
        "playoff_probs": playoff_probs,
        "next_five": next_five,
        "lineup_df": recommend_lineup(player_summary),
        "hitter_statcast": hitter_statcast,
        "pitcher_statcast": pitcher_statcast,
        "pitch_mix": pitch_mix,
        "team_statcast_summary": team_statcast_summary,
    }


def card_header(title: str, subtitle: str):
    st.markdown(
        f"<div class='section-card'><div class='section-title'>{title}</div><div class='section-subtitle'>{subtitle}</div>",
        unsafe_allow_html=True,
    )


def card_close():
    st.markdown("</div>", unsafe_allow_html=True)


teams_df = load_teams()
team_options = teams_df.set_index("name")["id"].to_dict()
default_team_name = teams_df.loc[teams_df["id"] == TEAM_ID_DEFAULT, "name"].iloc[0]

with st.sidebar:
    st.header("Dashboard Controls")
    team_name = st.selectbox("Team", list(team_options.keys()), index=list(team_options.keys()).index(default_team_name))
    season = st.number_input("Season", min_value=2015, max_value=2100, value=SEASON_DEFAULT, step=1)
    start_date = st.date_input("Start date", value=date(int(season), 1, 1))
    end_date = st.date_input("End date", value=date.today())
    if st.button("Refresh data", use_container_width=True):
        st.cache_data.clear()
    st.markdown(
        "<div class='sidebar-note'><strong>Trend colors</strong><br>🟢 improving<br>🟡 stable<br>🔴 declining</div>",
        unsafe_allow_html=True,
    )
    st.markdown(
        "<div class='sidebar-note'><strong>Data note</strong><br>Statcast-driven sections gracefully show unavailable data when source coverage is incomplete.</div>",
        unsafe_allow_html=True,
    )

team_id = int(team_options[team_name])
data = load_dashboard(team_id, int(season), start_date.isoformat(), end_date.isoformat())
ts = data["team_summary"]
completed_games = data["game_log"].dropna(subset=["team_score", "opp_score"])
prev_avg_runs = completed_games.head(max(1, len(completed_games) - 1))["team_score"].mean() if not completed_games.empty else 0
prev_avg_allowed = completed_games.head(max(1, len(completed_games) - 1))["opp_score"].mean() if not completed_games.empty else 0

metric_cols = st.columns(6)
metric_cols[0].metric("Record", ts.get("record", "0-0"))
metric_cols[1].metric("Runs Scored", ts.get("runs_scored", 0))
metric_cols[2].metric("Runs Allowed", ts.get("runs_allowed", 0))
metric_cols[3].metric("Run Diff", ts.get("run_differential", 0))
metric_cols[4].metric("Expected Runs", ts.get("expected_runs", 0))
metric_cols[5].metric("Consistency", ts.get("consistency_rating", 0))

team_tab, trend_tab, player_tab, pitch_tab, inning_tab, momentum_tab, lineup_tab, advanced_tab, forecast_tab = st.tabs(
    [
        "Team Summary",
        "Trends",
        "Player Performance",
        "Pitching",
        "Inning Analysis",
        "Momentum",
        "Lineup",
        "Advanced Metrics",
        "Forecast",
    ]
)

with team_tab:
    card_header("Team Performance Summary", SECTION_HELP["team_summary"])
    summary_df = pd.DataFrame(
        [
            {"Metric": "Record", "Value": ts["record"], "Trend": "🟢" if ts["run_differential"] >= 0 else "🟡"},
            {"Metric": "Runs scored", "Value": ts["runs_scored"], "Trend": stoplight(ts["avg_runs"] - prev_avg_runs)},
            {"Metric": "Runs allowed", "Value": ts["runs_allowed"], "Trend": stoplight(ts["avg_runs_allowed"] - prev_avg_allowed, better_high=False)},
            {"Metric": "Run differential", "Value": ts["run_differential"], "Trend": stoplight(ts["run_differential"])},
            {"Metric": "Avg runs per game", "Value": ts["avg_runs"], "Trend": stoplight(ts["avg_runs"] - prev_avg_runs)},
            {"Metric": "Avg runs allowed", "Value": ts["avg_runs_allowed"], "Trend": stoplight(ts["avg_runs_allowed"] - prev_avg_allowed, better_high=False)},
            {"Metric": "Expected runs next game", "Value": ts["expected_runs"], "Trend": stoplight(ts["expected_runs"] - ts["avg_runs"])},
            {"Metric": "Consistency rating", "Value": ts["consistency_rating"], "Trend": stoplight(ts["consistency_rating"] - 50)},
            {"Metric": "Clutch index", "Value": ts["clutch_index"], "Trend": stoplight(ts["clutch_index"] - 45)},
        ]
    )
    show_table(summary_df, height=390)
    card_close()

with trend_tab:
    c1, c2 = st.columns([1.1, 1.4])
    with c1:
        card_header("Rolling 3 Game Average", SECTION_HELP["rolling"])
        completed = completed_games.tail(3)
        rolling_df = pd.DataFrame(
            [
                {"Metric": "Runs", "Value": round(completed["team_score"].mean(), 2) if not completed.empty else 0, "Trend": stoplight((completed["team_score"].mean() if not completed.empty else 0) - ts["avg_runs"])},
                {"Metric": "Runs allowed", "Value": round(completed["opp_score"].mean(), 2) if not completed.empty else 0, "Trend": stoplight((completed["opp_score"].mean() if not completed.empty else 0) - ts["avg_runs_allowed"], better_high=False)},
            ]
        )
        show_table(rolling_df, height=180)
        card_close()
    with c2:
        card_header("Recent Game Trend", "Last completed games with runs for and against.")
        fig = rolling_runs_chart(data["game_log"])
        if fig:
            st.plotly_chart(fig, use_container_width=True)
        else:
            st.info("Not enough completed games to render trend chart.")
        card_close()

with player_tab:
    card_header("Player Performance Index", SECTION_HELP["players"])
    st.markdown("**Impact formula:** 35% on-base events, 25% extra-base hits, 20% run creation, 10% strikeout avoidance, 10% clutch contribution.")
    show_table(data["player_summary"][["player", "grade", "impact", "trend", "ob_events", "xbh", "so", "consistency_score"]], height=460)
    card_close()

    c1, c2 = st.columns(2)
    with c1:
        card_header("Clutch Index", "Performance in high-leverage situations.")
        show_table(data["clutch_df"][["player", "clutch_score", "clutch_trend"]], height=360)
        card_close()
    with c2:
        card_header("Consistency Rating", "Inverse volatility score using OB variation, strikeout variation, zero-production frequency, and impact fluctuation.")
        show_table(data["consistency_df"][["player", "consistency_score", "consistency_trend"]], height=360)
        card_close()

with pitch_tab:
    card_header("Pitching Performance", SECTION_HELP["pitching"])
    show_table(data["pitching_df"][["pitcher", "ip", "er", "so", "bb", "hr", "impact", "trend"]], height=420)
    card_close()

with inning_tab:
    card_header("Inning Performance Matrix", SECTION_HELP["inning"])
    show_table(data["inning_df"], height=320)
    card_close()
    c1, c2 = st.columns(2)
    with c1:
        card_header("Inning Heat Map: Runs For", "Visual intensity of scoring by inning.")
        fig = inning_heatmap(data["inning_df"], "runs_scored", "Runs For")
        if fig:
            st.plotly_chart(fig, use_container_width=True)
        show_table(build_heatmap_table(data["inning_df"], "runs_scored"), height=180)
        card_close()
    with c2:
        card_header("Inning Heat Map: Runs Against", "Visual intensity of opponent scoring by inning.")
        fig = inning_heatmap(data["inning_df"], "runs_allowed", "Runs Against")
        if fig:
            st.plotly_chart(fig, use_container_width=True)
        show_table(build_heatmap_table(data["inning_df"], "runs_allowed"), height=180)
        card_close()

with momentum_tab:
    card_header("Momentum Events", "Highest leverage moments impacting game outcome.")
    show_table(data["momentum_df"], height=420)
    card_close()

with lineup_tab:
    card_header("Lineup Optimization Model", "Ideal batting order based on on-base frequency, impact, strikeout avoidance, and extra-base production.")
    show_table(data["lineup_df"], height=420)
    card_close()

with advanced_tab:
    c1, c2 = st.columns([1.2, 1])
    with c1:
        card_header("Hitter Advanced Metrics", SECTION_HELP["advanced"])
        if data["hitter_statcast"].empty:
            st.info("Hitter Statcast data unavailable for current filters.")
        else:
            show_table(data["hitter_statcast"], height=420)
            ev_fig = exit_velocity_chart(data["hitter_statcast"])
            if ev_fig:
                st.plotly_chart(ev_fig, use_container_width=True)
        card_close()
    with c2:
        card_header("Pitcher Statcast", "Exit velocity allowed, spin, velocity, and pitch mix where available.")
        if data["pitcher_statcast"].empty:
            st.info("Pitcher Statcast data unavailable for current filters.")
        else:
            show_table(data["pitcher_statcast"], height=250)
            if not data["pitch_mix"].empty:
                pitcher_name = st.selectbox(
                    "Pitch mix chart pitcher",
                    data["pitch_mix"]["pitcher"].drop_duplicates().tolist(),
                    key="pitch_mix_pitcher",
                )
                fig = pitch_mix_chart(data["pitch_mix"], pitcher_name)
                if fig:
                    st.plotly_chart(fig, use_container_width=True)
                show_table(data["pitch_mix"][data["pitch_mix"]["pitcher"] == pitcher_name], height=220)
        if data["team_statcast_summary"]:
            team_stat_df = pd.DataFrame(
                [
                    {"Metric": "Team Avg EV Allowed", "Value": data["team_statcast_summary"].get("team_avg_exit_velocity")},
                    {"Metric": "Team Avg Spin Rate", "Value": data["team_statcast_summary"].get("team_avg_spin_rate")},
                ]
            )
            show_table(team_stat_df, height=120)
        card_close()

with forecast_tab:
    c1, c2 = st.columns([1, 1.2])
    with c1:
        card_header("Forecasting / Playoff Outlook", SECTION_HELP["forecast"])
        pcols = st.columns(3)
        pcols[0].metric("Playoff %", data["playoff_probs"]["playoff_probability"])
        pcols[1].metric("Division %", data["playoff_probs"]["division_probability"])
        pcols[2].metric("Wild Card %", data["playoff_probs"]["wild_card_probability"])
        st.plotly_chart(playoff_chart(data["playoff_probs"]), use_container_width=True)
        card_close()
    with c2:
        card_header("Next 5 Games Likelihood to Win", "Projected win probability for each upcoming game.")
        if data["next_five"].empty:
            st.info("No upcoming scheduled games found in current date window.")
        else:
            show_table(data["next_five"], height=280)
            win_fig = win_probability_chart(data["next_five"])
            if win_fig:
                st.plotly_chart(win_fig, use_container_width=True)
        card_close()
