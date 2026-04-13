from __future__ import annotations

from collections import defaultdict
from dataclasses import dataclass
from datetime import datetime
from typing import Any

import numpy as np
import pandas as pd

from utils.formatting import safe_div

FINAL_STATES = {"Final", "Game Over", "Completed Early"}


@dataclass
class TeamContext:
    team_id: int
    team_name: str
    team_abbrev: str
    league_id: int


def extract_team_context(team: dict[str, Any]) -> TeamContext:
    return TeamContext(
        team_id=team["id"],
        team_name=team["name"],
        team_abbrev=team.get("abbreviation", team.get("fileCode", "").upper()),
        league_id=team.get("league", {}).get("id", 103),
    )


def is_completed_game(game: dict[str, Any]) -> bool:
    return game.get("status", {}).get("detailedState") in FINAL_STATES


def normalize_schedule_row(game: dict[str, Any], team_id: int) -> dict[str, Any]:
    teams = game["teams"]
    is_home = teams["home"]["team"]["id"] == team_id
    team_side = "home" if is_home else "away"
    opp_side = "away" if is_home else "home"
    team_score = teams[team_side].get("score")
    opp_score = teams[opp_side].get("score")
    return {
        "gamePk": game["gamePk"],
        "date": game["gameDate"],
        "status": game.get("status", {}).get("detailedState"),
        "is_home": is_home,
        "opponent": teams[opp_side]["team"]["name"],
        "opponent_id": teams[opp_side]["team"]["id"],
        "team_score": team_score,
        "opp_score": opp_score,
        "won": None if team_score is None or opp_score is None else team_score > opp_score,
    }


def build_game_log(schedule: list[dict[str, Any]], team_id: int) -> pd.DataFrame:
    rows = [normalize_schedule_row(game, team_id) for game in schedule]
    df = pd.DataFrame(rows)
    if not df.empty:
        df["date"] = pd.to_datetime(df["date"])
        df = df.sort_values("date").reset_index(drop=True)
    return df


def parse_game_offense(feed: dict[str, Any], team_id: int) -> dict[str, Any]:
    box = feed.get("liveData", {}).get("boxscore", {}).get("teams", {})
    side = "home" if feed["gameData"]["teams"]["home"]["id"] == team_id else "away"
    team_box = box.get(side, {})
    batting_order = team_box.get("batters", [])
    players = team_box.get("players", {})
    rows: list[dict[str, Any]] = []
    totals = defaultdict(float)
    for pid in batting_order:
        player = players.get(f"ID{pid}", {})
        stats = player.get("stats", {}).get("batting", {})
        name = player.get("person", {}).get("fullName")
        if not name:
            continue
        row = {
            "player_id": pid,
            "player": name,
            "ab": stats.get("atBats", 0),
            "h": stats.get("hits", 0),
            "bb": stats.get("baseOnBalls", 0),
            "hbp": stats.get("hitByPitch", 0),
            "2b": stats.get("doubles", 0),
            "3b": stats.get("triples", 0),
            "hr": stats.get("homeRuns", 0),
            "rbi": stats.get("rbi", 0),
            "runs": stats.get("runs", 0),
            "so": stats.get("strikeOuts", 0),
            "tb": stats.get("totalBases", 0),
            "sb": stats.get("stolenBases", 0),
            "lob": stats.get("leftOnBase", 0),
            "game_pk": feed["gamePk"],
            "date": feed["gameData"]["datetime"]["officialDate"],
        }
        row["ob_events"] = row["h"] + row["bb"] + row["hbp"]
        row["xbh"] = row["2b"] + row["3b"] + row["hr"]
        row["productive_outs"] = 0
        rows.append(row)
        for k, v in row.items():
            if isinstance(v, (int, float)):
                totals[k] += v
    return {"player_rows": rows, "team_totals": dict(totals)}


def parse_game_pitching(feed: dict[str, Any], team_id: int) -> list[dict[str, Any]]:
    box = feed.get("liveData", {}).get("boxscore", {}).get("teams", {})
    side = "home" if feed["gameData"]["teams"]["home"]["id"] == team_id else "away"
    team_box = box.get(side, {})
    pitchers = team_box.get("pitchers", [])
    players = team_box.get("players", {})
    rows: list[dict[str, Any]] = []
    for pid in pitchers:
        player = players.get(f"ID{pid}", {})
        stats = player.get("stats", {}).get("pitching", {})
        name = player.get("person", {}).get("fullName")
        if not name:
            continue
        rows.append(
            {
                "player_id": pid,
                "pitcher": name,
                "ip": stats.get("inningsPitched", "0.0"),
                "er": stats.get("earnedRuns", 0),
                "so": stats.get("strikeOuts", 0),
                "bb": stats.get("baseOnBalls", 0),
                "hr": stats.get("homeRuns", 0),
                "hits": stats.get("hits", 0),
                "pitches": stats.get("numberOfPitches", 0),
                "strikes": stats.get("strikes", 0),
                "date": feed["gameData"]["datetime"]["officialDate"],
                "game_pk": feed["gamePk"],
            }
        )
    return rows


def parse_linescore(feed: dict[str, Any], team_id: int) -> list[dict[str, Any]]:
    innings = feed.get("liveData", {}).get("linescore", {}).get("innings", [])
    is_home = feed["gameData"]["teams"]["home"]["id"] == team_id
    rows = []
    for idx, inning in enumerate(innings, start=1):
        team_runs = inning.get("home" if is_home else "away", {}).get("runs", 0)
        opp_runs = inning.get("away" if is_home else "home", {}).get("runs", 0)
        rows.append({"inning": idx, "runs_for": team_runs, "runs_against": opp_runs, "game_pk": feed["gamePk"]})
    return rows


def parse_momentum(feed: dict[str, Any], team_id: int) -> list[dict[str, Any]]:
    plays = feed.get("liveData", {}).get("plays", {}).get("allPlays", [])
    rows = []
    home_id = feed["gameData"]["teams"]["home"]["id"]
    for play in plays:
        result = play.get("result", {})
        about = play.get("about", {})
        matchup = play.get("matchup", {})
        scoring = result.get("isScoringPlay")
        if not scoring and result.get("eventType") not in {"home_run", "triple", "double", "walk", "strikeout"}:
            continue
        batter_team_home = matchup.get("batSide") is not None and about.get("isTopInning", False) != (home_id == team_id)
        impact_level = "medium"
        if scoring:
            runs_scored = len(play.get("runners", []))
            impact_level = "very high" if runs_scored >= 2 else "high"
        rows.append(
            {
                "game_pk": feed["gamePk"],
                "inning": about.get("inning"),
                "half": "Top" if about.get("isTopInning") else "Bottom",
                "event": result.get("description", result.get("event", "")),
                "event_type": result.get("eventType"),
                "impact": impact_level,
                "team_offense": batter_team_home,
            }
        )
    return rows


def aggregate_innings(linescore_rows: list[dict[str, Any]]) -> pd.DataFrame:
    df = pd.DataFrame(linescore_rows)
    if df.empty:
        return pd.DataFrame(columns=["inning", "runs_scored", "runs_allowed", "net_impact"])
    grouped = df.groupby("inning", as_index=False).agg(runs_scored=("runs_for", "sum"), runs_allowed=("runs_against", "sum"))
    grouped["net_impact"] = grouped["runs_scored"] - grouped["runs_allowed"]
    return grouped


def summarize_team(game_log: pd.DataFrame) -> dict[str, Any]:
    completed = game_log.dropna(subset=["team_score", "opp_score"]).copy()
    wins = int(completed["won"].sum()) if not completed.empty else 0
    losses = int((~completed["won"]).sum()) if not completed.empty else 0
    runs_scored = float(completed["team_score"].sum()) if not completed.empty else 0.0
    runs_allowed = float(completed["opp_score"].sum()) if not completed.empty else 0.0
    consistency = 100 - min(100, np.std(completed["team_score"]) * 18) if len(completed) > 1 else 50
    clutch = min(100, safe_div(runs_scored, max(1.0, len(completed))) * 20)
    expected_runs = safe_div(completed["team_score"].tail(3).sum(), min(3, len(completed))) + 0.8 if not completed.empty else 0.0
    return {
        "record": f"{wins}-{losses}",
        "runs_scored": int(runs_scored),
        "runs_allowed": int(runs_allowed),
        "run_differential": int(runs_scored - runs_allowed),
        "avg_runs": round(safe_div(runs_scored, len(completed)), 2),
        "avg_runs_allowed": round(safe_div(runs_allowed, len(completed)), 2),
        "expected_runs": round(expected_runs, 2),
        "consistency_rating": round(consistency, 1),
        "clutch_index": round(clutch, 1),
    }


def rolling_3(game_log: pd.DataFrame) -> dict[str, Any]:
    completed = game_log.dropna(subset=["team_score", "opp_score"]).tail(3)
    if completed.empty:
        return {}
    return {
        "Runs": round(completed["team_score"].mean(), 2),
        "Runs allowed": round(completed["opp_score"].mean(), 2),
    }
