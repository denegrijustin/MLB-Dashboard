import io
from datetime import date, timedelta
from typing import Optional
import requests
import pandas as pd

STATCAST_CSV_URL = "https://baseballsavant.mlb.com/statcast_search/csv"
TIMEOUT = 30
REQUIRED_COLUMNS = [
    'pitch_type', 'events', 'description', 'hc_x', 'hc_y',
    'hit_distance_sc', 'launch_speed', 'launch_angle', 'bb_type',
    'home_team', 'away_team'
]


class StatcastApi:
    def __init__(self):
        self.session = requests.Session()
        self.session.headers.update({
            "User-Agent": "Mozilla/5.0 (compatible; MLB-Dashboard/1.0)"
        })

    def fetch_csv(self, params: dict) -> pd.DataFrame:
        params = {**params, "type": "details", "player_type": "batter"}
        resp = self.session.get(STATCAST_CSV_URL, params=params, timeout=TIMEOUT)
        resp.raise_for_status()
        content = resp.text.strip()
        if not content or content.startswith("Error") or "no results" in content.lower():
            return pd.DataFrame()
        df = pd.read_csv(io.StringIO(content), low_memory=False)
        return df

    def team_events(self, season: int, team_abbrev: str) -> pd.DataFrame:
        params = {
            "all": "true",
            "hfSea": f"{season}|",
            "team": team_abbrev,
            "game_date_gt": f"{season}-03-01",
            "game_date_lt": f"{season}-11-01",
        }
        return self.fetch_csv(params)

    def team_events_recent(self, team_abbrev: str, days: int = 7) -> pd.DataFrame:
        end = date.today()
        start = end - timedelta(days=days)
        params = {
            "all": "true",
            "team": team_abbrev,
            "game_date_gt": start.isoformat(),
            "game_date_lt": end.isoformat(),
        }
        return self.fetch_csv(params)

    def game_events(self, game_pk: int) -> pd.DataFrame:
        params = {
            "all": "true",
            "game_pk": str(game_pk),
        }
        return self.fetch_csv(params)

    def health_check(self) -> bool:
        try:
            end = date.today()
            start = end - timedelta(days=3)
            params = {
                "all": "true",
                "team": "KC",
                "game_date_gt": start.isoformat(),
                "game_date_lt": end.isoformat(),
            }
            resp = self.session.get(STATCAST_CSV_URL, params=params, timeout=TIMEOUT)
            return resp.status_code == 200
        except Exception:
            return False
