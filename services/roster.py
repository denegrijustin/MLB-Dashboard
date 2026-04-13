from sources.mlb_api import MLBApi

CLOSER_KEYWORDS = ["CL", "closer"]
STARTER_KEYWORDS = ["SP", "starter"]


def get_roster_with_roles(mlb_client: MLBApi, team_id: int, season: int) -> list:
    roster = mlb_client.get_roster(team_id, season)
    result = []
    for player in roster:
        person = player.get("person", {})
        position = player.get("position", {})
        pos_code = position.get("code", "")
        pos_type = position.get("type", "")
        pos_abbrev = position.get("abbreviation", "")

        player_id = person.get("id")
        player_name = person.get("fullName", "Unknown")

        if pos_code == "P" or pos_type == "Pitcher":
            status = player.get("status", {}).get("description", "")
            title = player.get("title", "")
            if pos_abbrev in ("CL",) or "closer" in title.lower():
                role = "closer"
            elif pos_abbrev in ("SP",) or "starter" in title.lower():
                role = "starter"
            else:
                role = "reliever"
        else:
            role = "hitter"

        result.append({
            "player_id": player_id,
            "player_name": player_name,
            "position": pos_abbrev or pos_code,
            "role": role,
        })
    return result
