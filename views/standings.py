import streamlit as st
import pandas as pd
from utils.logos import logo_url, logo_img
from services.projections import project_record, estimate_playoff_odds


def render_standings(division_standings: dict, selected_team_id: int, standings_row: dict = None, season: int = 2026):
    if not division_standings:
        st.warning("Standings data unavailable.")
        return

    for div_name, teams in division_standings.items():
        st.subheader(div_name)
        rows = []
        for t in teams:
            tid = t.get("team_id")
            is_selected = "→ " if tid == selected_team_id else "   "
            rows.append({
                "": is_selected,
                "Team": t.get("team_name", ""),
                "W": t.get("wins", 0),
                "L": t.get("losses", 0),
                "PCT": t.get("pct", ".000"),
                "GB": t.get("gb", "-"),
                "Streak": t.get("streak", ""),
            })
        df = pd.DataFrame(rows)
        st.dataframe(df, use_container_width=True, hide_index=True)
        st.write("")

    # Playoff projection panel
    if standings_row:
        st.divider()
        st.subheader("📊 Model Output: Playoff Projections")
        st.caption("⚠️ These projections are estimated by a simple statistical model and are not official MLB projections.")

        wins = standings_row.get("wins", 0)
        losses = standings_row.get("losses", 0)
        gp = wins + losses

        # Find division and wild card standings for the team
        team_division = None
        all_teams_flat = []
        for div_name, teams in division_standings.items():
            all_teams_flat.extend(teams)
            for t in teams:
                if t.get("team_id") == selected_team_id:
                    team_division = div_name

        div_teams = []
        if team_division:
            div_teams = division_standings.get(team_division, [])

        if gp > 0:
            proj = project_record({"wins": wins, "losses": losses}, gp)
            odds = estimate_playoff_odds(standings_row, div_teams, all_teams_flat)

            col1, col2, col3, col4 = st.columns(4)
            col1.metric("Proj. W-L", f"{proj['projected_wins']}-{proj['projected_losses']}")
            col2.metric("Proj. Win%", f"{proj['projected_pct']:.3f}")
            col3.metric("Div. Prob", f"{odds['division_prob']*100:.1f}%")
            col4.metric("Playoff Prob", f"{odds['playoff_prob']*100:.1f}%")
        else:
            st.info("Not enough games played for projections.")
