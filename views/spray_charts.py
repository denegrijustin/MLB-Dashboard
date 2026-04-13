import streamlit as st
from services.spray_chart import filter_hit_events, filter_batted_balls, make_spray_chart


def render_spray_charts(statcast_client, team_id: int, team_abbrev: str, player_list: list = None):
    st.subheader("🎯 Spray Charts")

    tab_7d, tab_season, tab_game = st.tabs(["📅 Last 7 Days", "📆 Season", "🔴 Current Game"])

    with tab_7d:
        _render_spray_tab(statcast_client, team_abbrev, scope="7d", player_list=player_list)

    with tab_season:
        _render_spray_tab(statcast_client, team_abbrev, scope="season", player_list=player_list)

    with tab_game:
        st.info("🎮 Current Game spray chart: Select an active game on the Live Game tab, then return here.")


def _render_spray_tab(statcast_client, team_abbrev: str, scope: str, player_list: list = None):
    from config import SEASON_DEFAULT

    load_key = f"spray_loaded_{team_abbrev}_{scope}"

    if st.button(f"Load {scope.replace('7d', 'Last 7 Days').replace('season', 'Season')} Data", key=f"load_{scope}"):
        with st.spinner("Fetching Statcast data..."):
            try:
                if scope == "7d":
                    df = statcast_client.team_events_recent(team_abbrev, days=7)
                else:
                    df = statcast_client.team_events(SEASON_DEFAULT, team_abbrev)

                if df is None or df.empty:
                    st.warning("No Statcast data available. Statcast may be rate-limited or data not yet available for this date range.")
                    return

                st.session_state[load_key] = df
            except Exception as e:
                st.error(f"Could not load Statcast data: {e}")
                return

    df = st.session_state.get(load_key)
    if df is None or (hasattr(df, 'empty') and df.empty):
        st.info("Click the button above to load spray chart data.")
        return

    # Filters
    col1, col2 = st.columns(2)

    with col1:
        outcome_filter = st.selectbox(
            "Outcome Filter",
            ["All Batted Balls", "Hits Only", "Home Runs Only"],
            key=f"outcome_{scope}"
        )

    with col2:
        if player_list and "player_name" in df.columns:
            players = sorted(df["player_name"].dropna().unique().tolist())
            all_opt = ["All Players"] + players
            selected_player = st.selectbox("Player Filter", all_opt, key=f"player_{scope}")
        else:
            selected_player = "All Players"

    # Apply filters
    filtered = df.copy()
    if selected_player != "All Players" and "player_name" in filtered.columns:
        filtered = filtered[filtered["player_name"] == selected_player]

    if outcome_filter == "Hits Only":
        filtered = filter_hit_events(filtered)
    elif outcome_filter == "Home Runs Only":
        if "events" in filtered.columns:
            filtered = filtered[filtered["events"] == "home_run"]

    filtered = filter_batted_balls(filtered)

    if filtered.empty:
        st.info("No batted ball data matches the current filters.")
        return

    title = f"{team_abbrev} - {outcome_filter}"
    if selected_player != "All Players":
        title += f" - {selected_player}"

    fig = make_spray_chart(filtered, title)
    if fig:
        st.plotly_chart(fig, use_container_width=True)
        st.caption(f"Showing {len(filtered)} batted ball events.")
    else:
        st.info("Could not render spray chart. Missing coordinate data.")
