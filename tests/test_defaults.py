from config import TEAM_ID_DEFAULT, TEAM_METADATA


def test_default_is_royals():
    assert TEAM_ID_DEFAULT == 118


def test_royals_metadata():
    assert 118 in TEAM_METADATA
    assert TEAM_METADATA[118]['abbrev'] == 'KC'


def test_all_30_teams_in_metadata():
    assert len(TEAM_METADATA) >= 30


def test_logo_url_format():
    from utils.logos import logo_url
    url = logo_url(118)
    assert '118' in url
    assert url.startswith('https://')
