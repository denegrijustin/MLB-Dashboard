import requests
from datetime import date
from typing import Optional

MLB_BASE = "https://statsapi.mlb.com/api/v1"
TIMEOUT = 15


class MLBApi:
    def __init__(self):
        self.session = requests.Session()
        self.session.headers.update({"Accept": "application/json"})

    def _get(self, path: str, params: dict = None) -> dict:
        url = f"{MLB_BASE}{path}"
        resp = self.session.get(url, params=params, timeout=TIMEOUT)
        resp.raise_for_status()
        return resp.json()

    def get_teams(self) -> list:
        data = self._get("/teams", {"sportId": 1})
        return data.get("teams", [])

    def get_team(self, team_id: int) -> dict:
        data = self._get(f"/teams/{team_id}")
        teams = data.get("teams", [])
        return teams[0] if teams else {}

    def get_schedule(self, team_id: int, season: int, start_date: str = None, end_date: str = None) -> list:
        params = {"teamId": team_id, "season": season, "sportId": 1, "gameType": "R"}
        if start_date:
            params["startDate"] = start_date
        if end_date:
            params["endDate"] = end_date
        data = self._get("/schedule", params)
        games = []
        for date_entry in data.get("dates", []):
            games.extend(date_entry.get("games", []))
        return games

    def get_standings(self, league_id: int, season: int) -> dict:
        params = {"leagueId": league_id, "season": season, "standingsType": "regularSeason"}
        return self._get("/standings", params)

    def get_game_feed(self, game_pk: int) -> dict:
        return self._get(f"/game/{game_pk}/feed/live")

    def get_today_games(self) -> list:
        today = date.today().isoformat()
        params = {"date": today, "sportId": 1}
        data = self._get("/schedule", params)
        games = []
        for date_entry in data.get("dates", []):
            games.extend(date_entry.get("games", []))
        return games

    def get_roster(self, team_id: int, season: int) -> list:
        params = {"season": season, "rosterType": "active"}
        data = self._get(f"/teams/{team_id}/roster", params)
        return data.get("roster", [])

    def get_probable_pitchers(self, team_id: int, season: int) -> list:
        today = date.today().isoformat()
        params = {"teamId": team_id, "season": season, "sportId": 1, "startDate": today}
        data = self._get("/schedule", params)
        games = []
        for date_entry in data.get("dates", []):
            games.extend(date_entry.get("games", []))
        return games

    def health_check(self) -> bool:
        try:
            teams = self.get_teams()
            return len(teams) > 0
        except Exception:
            return False
