import streamlit as st
from utils.logos import logo_url, logo_img
from utils.formatting import format_record


def render_landing(
    team_id: int,
    team_name: str,
    team_abbrev: str,
    record: dict = None,
    current_game: dict = None,
    next_game: dict = None,
    standings_row: dict = None,
):
    col_logo, col_info = st.columns([1, 4])
    with col_logo:
        st.image(logo_url(team_id), width=100)
    with col_info:
        st.title(team_name)
        if record:
            wins = record.get("wins", 0)
            losses = record.get("losses", 0)
            pct = record.get("pct", ".000")
            st.subheader(f"Record: {wins}-{losses} ({pct})")
        if standings_row:
            div = standings_row.get("division", "")
            gb = standings_row.get("gb", "-")
            streak = standings_row.get("streak", "")
            parts = []
            if div:
                parts.append(f"**{div}**")
            if gb and gb != "-":
                parts.append(f"GB: {gb}")
            if streak:
                parts.append(f"Streak: {streak}")
            if parts:
                st.write(" | ".join(parts))

    st.divider()

    if current_game:
        _render_game_card(current_game, team_id, team_abbrev, is_live=True)
    elif next_game:
        _render_game_card(next_game, team_id, team_abbrev, is_live=False)
    else:
        st.info("No game scheduled for today.")


def _render_game_card(game: dict, team_id: int, team_abbrev: str, is_live: bool):
    home_id = game.get("home_team_id")
    away_id = game.get("away_team_id")
    home_name = game.get("home_team_name", "Home")
    away_name = game.get("away_team_name", "Away")
    status = game.get("status", "")
    inning = game.get("inning", 0)
    home_score = game.get("home_score", 0)
    away_score = game.get("away_score", 0)
    abstract = game.get("abstract_state", "")

    if is_live:
        st.subheader("🔴 Live Game")
    else:
        st.subheader("📅 Today's Game")

    col1, col_vs, col2 = st.columns([2, 1, 2])

    with col1:
        if away_id:
            st.image(logo_url(away_id), width=60)
        st.write(f"**{away_name}**")
        if is_live and abstract == "Live":
            st.metric("Score", away_score)

    with col_vs:
        st.write("")
        st.write("")
        if abstract == "Live" and inning:
            half = "▲" if game.get("is_top_inning") else "▼"
            st.write(f"**{half}{inning}**")
        elif abstract == "Final":
            st.write("**Final**")
        else:
            st.write("**vs**")
            game_time = game.get("game_time", "")
            if game_time:
                from dateutil import parser as dtparser
                try:
                    dt = dtparser.parse(game_time)
                    st.caption(dt.strftime("%I:%M %p ET"))
                except Exception:
                    pass

    with col2:
        if home_id:
            st.image(logo_url(home_id), width=60)
        st.write(f"**{home_name}**")
        if is_live and abstract == "Live":
            st.metric("Score", home_score)

    # Probable pitchers
    home_pitcher = game.get("home_probable_pitcher", "TBD")
    away_pitcher = game.get("away_probable_pitcher", "TBD")
    if home_pitcher or away_pitcher:
        st.caption(f"Probable: {away_name}: {away_pitcher} vs {home_name}: {home_pitcher}")
