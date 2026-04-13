import streamlit as st

st.set_page_config(
    page_title="MLB Dashboard ⚾",
    page_icon="⚾",
    layout="wide",
    initial_sidebar_state="expanded",
)

import sys
import os
sys.path.insert(0, os.path.dirname(__file__))

from config import TEAM_ID_DEFAULT, TEAM_METADATA, SEASON_DEFAULT, LEAGUE_AL_ID, LEAGUE_NL_ID
from sources.mlb_api import MLBApi
from sources.statcast_api import StatcastApi
from utils.logos import logo_url
from services.live_game import get_today_games, get_team_current_game
from services.standings import get_division_standings, get_team_standing
from services.roster import get_roster_with_roles
from views.landing import render_landing
from views.live_game import render_live_game
from views import standings as standings_view
from views.player_impact import render_player_impact
from views.spray_charts import render_spray_charts
from views.hr_tracker import render_hr_tracker


# Cached clients
@st.cache_resource
def get_mlb_client():
    return MLBApi()


@st.cache_resource
def get_statcast_client():
    return StatcastApi()


@st.cache_data(ttl=3600)
def load_all_teams():
    client = get_mlb_client()
    try:
        teams = client.get_teams()
        return {t["id"]: t for t in teams if t.get("id")}
    except Exception:
        return {}


@st.cache_data(ttl=300)
def load_today_games():
    client = get_mlb_client()
    try:
        return get_today_games(client)
    except Exception:
        return []


@st.cache_data(ttl=900)
def load_standings(league_id: int, season: int):
    client = get_mlb_client()
    try:
        return get_division_standings(client, league_id, season)
    except Exception:
        return {}


@st.cache_data(ttl=3600)
def load_roster(team_id: int, season: int):
    client = get_mlb_client()
    try:
        return get_roster_with_roles(client, team_id, season)
    except Exception:
        return []


# Sidebar
team_ids = sorted(TEAM_METADATA.keys())
default_idx = team_ids.index(TEAM_ID_DEFAULT) if TEAM_ID_DEFAULT in team_ids else 0

with st.sidebar:
    st.title("⚾ MLB Dashboard")

    selected_team_id = st.selectbox(
        "Select Team",
        options=team_ids,
        format_func=lambda tid: TEAM_METADATA.get(tid, {}).get("name", str(tid)),
        index=default_idx,
        key="selected_team",
    )

    team_meta = TEAM_METADATA.get(selected_team_id, {})
    team_name = team_meta.get("name", "Unknown Team")
    team_abbrev = team_meta.get("abbrev", "")
    team_league = team_meta.get("league", "AL")
    team_division = team_meta.get("division", "")

    st.image(logo_url(selected_team_id), width=100)
    st.write(f"**{team_name}**")
    st.caption(f"{team_division} | Season {SEASON_DEFAULT}")

    st.divider()
    with st.expander("🔧 Admin / Debug"):
        if st.button("Check MLB API"):
            mlb = get_mlb_client()
            ok = mlb.health_check()
            st.write("✅ MLB API OK" if ok else "❌ MLB API Error")
        if st.button("Check Statcast API"):
            sc = get_statcast_client()
            ok = sc.health_check()
            st.write("✅ Statcast OK" if ok else "⚠️ Statcast may be unavailable")


# Load fast data
today_games = load_today_games()
current_game = get_team_current_game(today_games, selected_team_id)

# Standings (needed for landing)
league_id = LEAGUE_AL_ID if team_league == "AL" else LEAGUE_NL_ID
all_division_standings = load_standings(league_id, SEASON_DEFAULT)

# Find team standing
standings_row = None
for div_name, teams in all_division_standings.items():
    for t in teams:
        if t.get("team_id") == selected_team_id:
            standings_row = {**t, "division": div_name}
            break

record = None
if standings_row:
    record = {
        "wins": standings_row.get("wins", 0),
        "losses": standings_row.get("losses", 0),
        "pct": standings_row.get("pct", ".000"),
    }

# Main tabs
tab_overview, tab_live, tab_standings, tab_impact, tab_spray, tab_hr = st.tabs([
    "🏠 Overview",
    "⚡ Live Game",
    "📊 Standings & Playoffs",
    "👥 Player Impact",
    "🎯 Spray Charts",
    "💣 Home Runs",
])

with tab_overview:
    render_landing(
        team_id=selected_team_id,
        team_name=team_name,
        team_abbrev=team_abbrev,
        record=record,
        current_game=current_game,
        next_game=None,
        standings_row=standings_row,
    )

with tab_live:
    if current_game:
        render_live_game(current_game, selected_team_id, mlb_client=get_mlb_client())
    else:
        st.info(f"No game today for {team_name}.")
        st.write("**Today's Schedule:**")
        if today_games:
            for g in today_games:
                home = g.get("home_team_name", "?")
                away = g.get("away_team_name", "?")
                status = g.get("status", "")
                hs = g.get("home_score", 0)
                aws = g.get("away_score", 0)
                if g.get("abstract_state") in ("Live", "Final"):
                    st.write(f"• {away} {aws} @ {home} {hs} — {status}")
                else:
                    st.write(f"• {away} @ {home} — {status}")
        else:
            st.write("No games scheduled today.")

with tab_standings:
    # Load both leagues for full standings
    al_standings = load_standings(LEAGUE_AL_ID, SEASON_DEFAULT)
    nl_standings = load_standings(LEAGUE_NL_ID, SEASON_DEFAULT)
    combined = {**al_standings, **nl_standings}

    standings_view.render_standings(
        combined,
        selected_team_id=selected_team_id,
        standings_row=standings_row,
        season=SEASON_DEFAULT,
    )

with tab_impact:
    roster = load_roster(selected_team_id, SEASON_DEFAULT)
    render_player_impact(roster=roster)

with tab_spray:
    sc_client = get_statcast_client()
    roster_for_spray = load_roster(selected_team_id, SEASON_DEFAULT)
    player_names = [r["player_name"] for r in roster_for_spray]
    render_spray_charts(sc_client, selected_team_id, team_abbrev, player_names)

with tab_hr:
    sc_client = get_statcast_client()
    render_hr_tracker(sc_client, team_abbrev, selected_team_id)
