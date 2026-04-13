from __future__ import annotations

from dataclasses import dataclass
from datetime import date
from typing import Any

import requests

BASE_URL = "https://statsapi.mlb.com/api/v1"
TIMEOUT = 30


class MLBApiError(RuntimeError):
    pass


@dataclass
class MLBClient:
    session: requests.Session | None = None

    def __post_init__(self):
        if self.session is None:
            self.session = requests.Session()

    def _get(self, path: str, params: dict[str, Any] | None = None) -> dict[str, Any]:
        url = f"{BASE_URL}{path}"
        response = self.session.get(url, params=params, timeout=TIMEOUT)
        response.raise_for_status()
        return response.json()

    def get_teams(self) -> list[dict[str, Any]]:
        data = self._get("/teams", {"sportId": 1})
        return data.get("teams", [])

    def get_team(self, team_id: int) -> dict[str, Any] | None:
        teams = self.get_teams()
        return next((team for team in teams if team["id"] == team_id), None)

    def get_schedule(
        self,
        team_id: int,
        season: int,
        start_date: str | None = None,
        end_date: str | None = None,
    ) -> list[dict[str, Any]]:
        params: dict[str, Any] = {"sportId": 1, "teamId": team_id, "season": season}
        if start_date:
            params["startDate"] = start_date
        if end_date:
            params["endDate"] = end_date
        data = self._get("/schedule", params)
        games: list[dict[str, Any]] = []
        for day in data.get("dates", []):
            games.extend(day.get("games", []))
        return games

    def get_standings(self, league_id: int, season: int) -> dict[str, Any]:
        return self._get("/standings", {"leagueId": league_id, "season": season})

    def get_wild_card(self, league_id: int, season: int) -> dict[str, Any]:
        return self._get(f"/standings/wildCard", {"leagueId": league_id, "season": season})

    def get_game_feed(self, game_pk: int) -> dict[str, Any]:
        return self._get(f"/game/{game_pk}/feed/live")

    def get_boxscore(self, game_pk: int) -> dict[str, Any]:
        return self._get(f"/game/{game_pk}/boxscore")

    def get_linescore(self, game_pk: int) -> dict[str, Any]:
        return self._get(f"/game/{game_pk}/linescore")

    def get_play_by_play(self, game_pk: int) -> dict[str, Any]:
        return self._get(f"/game/{game_pk}/playByPlay")
