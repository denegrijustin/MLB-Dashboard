import pytest
import socket
from sources.mlb_api import MLBApi


def _network_available() -> bool:
    try:
        socket.setdefaulttimeout(3)
        socket.getaddrinfo("statsapi.mlb.com", 443)
        return True
    except Exception:
        return False


requires_network = pytest.mark.skipif(
    not _network_available(),
    reason="No network access to statsapi.mlb.com"
)


@requires_network
def test_mlb_api_health():
    api = MLBApi()
    assert api.health_check(), "MLB API health check failed"


@requires_network
def test_get_teams_returns_30():
    api = MLBApi()
    teams = api.get_teams()
    assert len(teams) >= 30


@requires_network
def test_royals_in_teams():
    api = MLBApi()
    teams = api.get_teams()
    ids = [t['id'] for t in teams]
    assert 118 in ids, "KC Royals (118) not found in teams"


@requires_network
def test_get_today_schedule():
    api = MLBApi()
    games = api.get_today_games()
    assert isinstance(games, list)


@requires_network
def test_standings_schema():
    api = MLBApi()
    from config import LEAGUE_AL_ID
    standings = api.get_standings(LEAGUE_AL_ID, 2026)
    assert 'records' in standings


@pytest.mark.integration
def test_statcast_health():
    from sources.statcast_api import StatcastApi
    api = StatcastApi()
    result = api.health_check()
    if not result:
        pytest.skip("Statcast health check unavailable (may be rate limited)")
