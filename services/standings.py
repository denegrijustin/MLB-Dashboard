from typing import Optional
from sources.mlb_api import MLBApi
from config import TEAM_METADATA


def get_division_standings(mlb_client: MLBApi, league_id: int, season: int) -> dict:
    data = mlb_client.get_standings(league_id, season)
    records = data.get("records", [])

    divisions = {}
    for record in records:
        div_name = record.get("division", {}).get("nameShort", "Unknown")
        full_div = record.get("division", {}).get("name", div_name)
        teams = []
        for tr in record.get("teamRecords", []):
            team_id = tr.get("team", {}).get("id")
            team_name = tr.get("team", {}).get("name", "")
            meta = TEAM_METADATA.get(team_id, {})
            abbrev = meta.get("abbrev", "")
            wins = tr.get("wins", 0)
            losses = tr.get("losses", 0)
            pct = tr.get("winningPercentage", "0.000")
            gb = tr.get("gamesBack", "-")
            streak_obj = tr.get("streak", {})
            streak = streak_obj.get("streakCode", "") if streak_obj else ""
            teams.append({
                "team_id": team_id,
                "team_name": team_name,
                "team_abbrev": abbrev,
                "wins": wins,
                "losses": losses,
                "pct": pct,
                "gb": gb,
                "streak": streak,
            })
        if teams:
            divisions[full_div] = teams
    return divisions


def get_team_standing(mlb_client: MLBApi, team_id: int, season: int) -> Optional[dict]:
    from config import TEAM_METADATA, LEAGUE_AL_ID, LEAGUE_NL_ID
    meta = TEAM_METADATA.get(team_id, {})
    league = meta.get("league", "AL")
    league_id = LEAGUE_AL_ID if league == "AL" else LEAGUE_NL_ID
    try:
        divisions = get_division_standings(mlb_client, league_id, season)
        for div_name, teams in divisions.items():
            for t in teams:
                if t["team_id"] == team_id:
                    t["division"] = div_name
                    return t
    except Exception:
        pass
    return None
