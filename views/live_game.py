import streamlit as st
import pandas as pd
from utils.logos import logo_url
from services.live_game import get_live_game_detail


def render_live_game(game: dict, team_id: int, mlb_client=None):
    if not game:
        st.info("No live game data available.")
        return

    abstract = game.get("abstract_state", "")
    status = game.get("status", "Scheduled")
    home_id = game.get("home_team_id")
    away_id = game.get("away_team_id")
    home_name = game.get("home_team_name", "Home")
    away_name = game.get("away_team_name", "Away")

    # Score card
    col1, col_mid, col2 = st.columns([3, 2, 3])
    with col1:
        if away_id:
            st.image(logo_url(away_id), width=70)
        st.subheader(away_name)
        st.metric("Runs", game.get("away_score", 0))

    with col_mid:
        st.write("")
        st.write("")
        inning = game.get("inning", 0)
        if abstract == "Live" and inning:
            half = "▲" if game.get("is_top_inning") else "▼"
            st.markdown(f"### {half}{inning}")
        elif abstract == "Final":
            st.markdown("### **Final**")
        else:
            st.write(f"**{status}**")

    with col2:
        if home_id:
            st.image(logo_url(home_id), width=70)
        st.subheader(home_name)
        st.metric("Runs", game.get("home_score", 0))

    st.divider()

    # Pitchers
    col_p1, col_p2 = st.columns(2)
    with col_p1:
        st.write(f"**{away_name} SP:** {game.get('away_probable_pitcher', 'TBD')}")
    with col_p2:
        st.write(f"**{home_name} SP:** {game.get('home_probable_pitcher', 'TBD')}")

    # Live linescore
    if mlb_client and abstract in ("Live", "Final"):
        game_pk = game.get("game_pk")
        if game_pk:
            with st.spinner("Loading linescore..."):
                try:
                    detail = get_live_game_detail(mlb_client, game_pk)
                    _render_linescore(detail, away_name, home_name)
                except Exception as e:
                    st.warning(f"Could not load linescore: {e}")


def _render_linescore(detail: dict, away_name: str, home_name: str):
    innings = detail.get("innings", [])
    if not innings:
        st.info("Linescore not available yet.")
        return

    st.subheader("Line Score")
    inning_nums = [str(i["num"]) for i in innings]
    away_runs = [str(i.get("away_runs", "")) for i in innings]
    home_runs = [str(i.get("home_runs", "")) for i in innings]

    data = {
        "Team": [away_name, home_name],
        **{f"{n}": [a, h] for n, a, h in zip(inning_nums, away_runs, home_runs)},
        "R": [str(detail.get("away_runs_total", 0)), str(detail.get("home_runs_total", 0))],
        "H": [str(detail.get("away_hits", 0)), str(detail.get("home_hits", 0))],
        "E": [str(detail.get("away_errors", 0)), str(detail.get("home_errors", 0))],
    }
    df = pd.DataFrame(data)
    st.dataframe(df, use_container_width=True, hide_index=True)
