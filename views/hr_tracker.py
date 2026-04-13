import streamlit as st
from services.hr_tracker import filter_home_runs, build_hr_table, team_hr_summary


def render_hr_tracker(statcast_client, team_abbrev: str, team_id: int):
    st.subheader("💣 Home Run Tracker")

    tab_7d, tab_season, tab_game = st.tabs(["📅 Last 7 Days", "📆 Season", "🔴 Current Game"])

    with tab_7d:
        _render_hr_tab(statcast_client, team_abbrev, scope="7d")

    with tab_season:
        _render_hr_tab(statcast_client, team_abbrev, scope="season")

    with tab_game:
        st.info("🎮 Current Game HR tracker: Select an active game on the Live Game tab, then return here.")


def _render_hr_tab(statcast_client, team_abbrev: str, scope: str):
    from config import SEASON_DEFAULT

    load_key = f"hr_loaded_{team_abbrev}_{scope}"

    label = "Last 7 Days" if scope == "7d" else "Season"
    if st.button(f"Load {label} HR Data", key=f"hr_btn_{scope}"):
        with st.spinner("Fetching HR data from Statcast..."):
            try:
                if scope == "7d":
                    df = statcast_client.team_events_recent(team_abbrev, days=7)
                else:
                    df = statcast_client.team_events(SEASON_DEFAULT, team_abbrev)

                if df is None or df.empty:
                    st.warning("No Statcast data available for this period.")
                    st.session_state[load_key] = None
                    return

                st.session_state[load_key] = df
            except Exception as e:
                st.error(f"Could not load HR data: {e}")
                return

    df = st.session_state.get(load_key)
    if df is None:
        st.info(f"Click the button above to load {label.lower()} home run data.")
        return

    summary = team_hr_summary(df, team_abbrev)
    hr_table = build_hr_table(df)

    # Summary metrics
    col1, col2, col3, col4 = st.columns(4)
    col1.metric("Total HRs", summary["total_hrs"])
    col2.metric("Avg Distance", f"{summary['avg_distance']} ft" if summary["avg_distance"] else "N/A")
    col3.metric("Avg Exit Velo", f"{summary['avg_exit_velo']} mph" if summary["avg_exit_velo"] else "N/A")
    col4.metric("Longest HR", f"{summary['longest_hr']} ft" if summary["longest_hr"] else "N/A")

    if hr_table.empty:
        st.info("No home runs found in this dataset.")
    else:
        st.dataframe(hr_table, use_container_width=True, hide_index=True)
