import streamlit as st
import pandas as pd


def render_player_impact(
    hitters_df: pd.DataFrame = None,
    starters_df: pd.DataFrame = None,
    relievers_df: pd.DataFrame = None,
    closers_df: pd.DataFrame = None,
    roster: list = None,
):
    st.subheader("👥 Player Impact")

    tab_h, tab_sp, tab_rp, tab_cl = st.tabs(["🏏 Hitters", "⚾ Starting Pitchers", "🔁 Relievers", "🔒 Closers"])

    with tab_h:
        _render_role_section(hitters_df, "Hitters", roster, "hitter")

    with tab_sp:
        _render_role_section(starters_df, "Starting Pitchers", roster, "starter")

    with tab_rp:
        _render_role_section(relievers_df, "Relievers", roster, "reliever")

    with tab_cl:
        _render_role_section(closers_df, "Closers", roster, "closer")


def _render_role_section(df: pd.DataFrame, label: str, roster: list, role: str):
    if df is not None and not df.empty:
        st.dataframe(df, use_container_width=True, hide_index=True)
    else:
        # Show roster for this role if available
        if roster:
            role_players = [r for r in roster if r.get("role") == role]
            if role_players:
                st.write(f"**{label} on Active Roster:**")
                rows = [{"Player": p["player_name"], "Position": p["position"]} for p in role_players]
                st.dataframe(pd.DataFrame(rows), use_container_width=True, hide_index=True)
            else:
                st.info(f"No {label.lower()} found on active roster.")
        else:
            st.info(f"No {label.lower()} impact data available. Load season data to view statistics.")
