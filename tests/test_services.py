import pandas as pd
import pytest
from services.spray_chart import filter_hit_events, make_spray_chart
from services.hr_tracker import filter_home_runs, build_hr_table
from services.projections import project_record


def test_filter_hit_events_empty():
    df = pd.DataFrame()
    result = filter_hit_events(df)
    assert result.empty


def test_filter_hit_events_filters_correctly():
    df = pd.DataFrame({'events': ['single', 'strikeout', 'home_run', 'field_out', 'double']})
    result = filter_hit_events(df)
    assert len(result) == 3
    assert set(result['events'].tolist()) == {'single', 'home_run', 'double'}


def test_make_spray_chart_empty_returns_none():
    df = pd.DataFrame()
    result = make_spray_chart(df, "Test")
    assert result is None


def test_make_spray_chart_missing_coords_returns_none():
    df = pd.DataFrame({'events': ['single', 'home_run']})
    result = make_spray_chart(df, "Test")
    assert result is None


def test_make_spray_chart_with_data():
    df = pd.DataFrame({
        'hc_x': [100.0, 150.0, 125.0],
        'hc_y': [100.0, 50.0, 75.0],
        'events': ['single', 'home_run', 'double'],
        'bb_type': ['line_drive', 'fly_ball', 'line_drive'],
    })
    result = make_spray_chart(df, "Test Chart")
    assert result is not None


def test_filter_home_runs():
    df = pd.DataFrame({'events': ['home_run', 'single', 'home_run', 'strikeout']})
    result = filter_home_runs(df)
    assert len(result) == 2


def test_filter_home_runs_empty():
    df = pd.DataFrame()
    result = filter_home_runs(df)
    assert result.empty


def test_build_hr_table_empty():
    df = pd.DataFrame()
    result = build_hr_table(df)
    assert result.empty


def test_build_hr_table_with_data():
    df = pd.DataFrame({
        'events': ['home_run', 'single'],
        'player_name': ['Player A', 'Player B'],
        'hit_distance_sc': [420.0, None],
        'launch_speed': [105.2, 85.0],
        'launch_angle': [28.5, 10.0],
        'game_date': ['2026-04-15', '2026-04-15'],
        'inning': [3, 5],
        'home_team': ['KC', 'KC'],
        'away_team': ['NYY', 'NYY'],
    })
    result = build_hr_table(df)
    assert len(result) == 1
    assert 'Player' in result.columns


def test_project_record_basic():
    team_summary = {'wins': 50, 'losses': 40}
    result = project_record(team_summary, games_played=90)
    assert 'projected_wins' in result
    assert result['projected_wins'] + result['projected_losses'] == 162


def test_project_record_zero_games():
    result = project_record({'wins': 0, 'losses': 0}, games_played=0)
    assert 'projected_wins' in result


def test_logo_html_contains_img():
    from utils.logos import logo_img
    html = logo_img(118, 'KC')
    assert '<img' in html
    assert '118' in html


def test_logo_url_royals():
    from utils.logos import logo_url
    url = logo_url(118)
    assert url.startswith('https://www.mlbstatic.com/team-logos/')
    assert url.endswith('118.svg')
