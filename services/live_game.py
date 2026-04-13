from typing import Optional
from sources.mlb_api import MLBApi


def get_today_games(mlb_client: MLBApi) -> list:
    raw_games = mlb_client.get_today_games()
    result = []
    for g in raw_games:
        try:
            teams = g.get("teams", {})
            home = teams.get("home", {})
            away = teams.get("away", {})
            status = g.get("status", {})
            linescore = g.get("linescore", {})

            home_team_id = home.get("team", {}).get("id")
            away_team_id = away.get("team", {}).get("id")

            home_score = home.get("score", 0) or 0
            away_score = away.get("score", 0) or 0

            inning = linescore.get("currentInning", 0)
            is_top = linescore.get("isTopInning", True)

            abstract_state = status.get("abstractGameState", "")
            coded_state = status.get("codedGameState", "")
            detail = status.get("detailedState", "")

            home_pitcher = home.get("probablePitcher", {}).get("fullName", "TBD")
            away_pitcher = away.get("probablePitcher", {}).get("fullName", "TBD")

            result.append({
                "game_pk": g.get("gamePk"),
                "home_team_id": home_team_id,
                "away_team_id": away_team_id,
                "home_team_name": home.get("team", {}).get("name", ""),
                "away_team_name": away.get("team", {}).get("name", ""),
                "home_score": home_score,
                "away_score": away_score,
                "status": detail,
                "abstract_state": abstract_state,
                "coded_state": coded_state,
                "inning": inning,
                "is_top_inning": is_top,
                "home_probable_pitcher": home_pitcher,
                "away_probable_pitcher": away_pitcher,
                "game_time": g.get("gameDate", ""),
            })
        except Exception:
            continue
    return result


def get_team_current_game(today_games: list, team_id: int) -> Optional[dict]:
    for g in today_games:
        if g.get("home_team_id") == team_id or g.get("away_team_id") == team_id:
            return g
    return None


def get_live_game_detail(mlb_client: MLBApi, game_pk: int) -> dict:
    feed = mlb_client.get_game_feed(game_pk)
    live_data = feed.get("liveData", {})
    linescore = live_data.get("linescore", {})
    game_data = feed.get("gameData", {})

    innings_raw = linescore.get("innings", [])
    innings = []
    for inn in innings_raw:
        innings.append({
            "num": inn.get("num", ""),
            "home_runs": inn.get("home", {}).get("runs", ""),
            "home_hits": inn.get("home", {}).get("hits", ""),
            "home_errors": inn.get("home", {}).get("errors", ""),
            "away_runs": inn.get("away", {}).get("runs", ""),
            "away_hits": inn.get("away", {}).get("hits", ""),
            "away_errors": inn.get("away", {}).get("errors", ""),
        })

    teams = game_data.get("teams", {})
    home_team = teams.get("home", {})
    away_team = teams.get("away", {})

    return {
        "innings": innings,
        "home_team_id": home_team.get("id"),
        "home_team_name": home_team.get("name", ""),
        "away_team_id": away_team.get("id"),
        "away_team_name": away_team.get("name", ""),
        "home_runs_total": linescore.get("teams", {}).get("home", {}).get("runs", 0),
        "away_runs_total": linescore.get("teams", {}).get("away", {}).get("runs", 0),
        "home_hits": linescore.get("teams", {}).get("home", {}).get("hits", 0),
        "away_hits": linescore.get("teams", {}).get("away", {}).get("hits", 0),
        "home_errors": linescore.get("teams", {}).get("home", {}).get("errors", 0),
        "away_errors": linescore.get("teams", {}).get("away", {}).get("errors", 0),
        "current_inning": linescore.get("currentInning", 0),
        "inning_half": linescore.get("inningHalf", ""),
    }
