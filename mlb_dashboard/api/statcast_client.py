from __future__ import annotations

from io import StringIO
from typing import Any

import pandas as pd
import requests

BASE_URL = "https://baseballsavant.mlb.com/statcast_search/csv"
TIMEOUT = 60


class StatcastClient:
    def __init__(self, session: requests.Session | None = None):
        self.session = session or requests.Session()

    def fetch_csv(self, params: dict[str, Any]) -> pd.DataFrame:
        response = self.session.get(BASE_URL, params=params, timeout=TIMEOUT)
        response.raise_for_status()
        text = response.text.strip()
        if not text:
            return pd.DataFrame()
        return pd.read_csv(StringIO(text))

    def team_events(self, season: int, team_abbrev: str) -> pd.DataFrame:
        return self.fetch_csv(
            {
                "year": season,
                "type": "details",
                "team": team_abbrev,
            }
        )

    def hitter_events(self, season: int, player_id: int) -> pd.DataFrame:
        return self.fetch_csv(
            {
                "year": season,
                "player_type": "batter",
                "player_id": player_id,
                "type": "details",
            }
        )

    def pitcher_events(self, season: int, player_id: int) -> pd.DataFrame:
        return self.fetch_csv(
            {
                "year": season,
                "player_type": "pitcher",
                "player_id": player_id,
                "type": "details",
            }
        )
