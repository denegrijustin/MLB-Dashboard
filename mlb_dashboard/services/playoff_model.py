from __future__ import annotations

import pandas as pd


def estimate_playoff_probability(team_summary: dict, standings_row: dict | None, wild_row: dict | None) -> dict:
    wins, losses = [int(x) for x in team_summary["record"].split("-")]
    games = max(1, wins + losses)
    win_pct = wins / games
    run_diff = team_summary["run_differential"]
    score = 0.45 * win_pct + 0.20 * max(-0.2, min(0.2, run_diff / 100)) + 0.20 * min(1.0, team_summary["consistency_rating"] / 100) + 0.15 * min(1.0, team_summary["clutch_index"] / 100)
    division_rank = standings_row.get("divisionRank") if standings_row else None
    wc_rank = wild_row.get("wildCardRank") if wild_row else None
    if division_rank:
        score += max(0, (6 - int(division_rank))) * 0.02
    if wc_rank:
        score += max(0, (6 - int(wc_rank))) * 0.015
    playoff = max(0, min(100, round(score * 100, 1)))
    division = max(0, min(100, round(playoff * 0.45, 1)))
    wild = max(0, min(100, round(playoff * 0.75, 1)))
    return {
        "playoff_probability": playoff,
        "division_probability": division,
        "wild_card_probability": wild,
    }


def extract_standings_rows(standings: dict, team_id: int) -> dict | None:
    for record_set in standings.get("records", []):
        for row in record_set.get("teamRecords", []):
            if row.get("team", {}).get("id") == team_id:
                return row
    return None
