from __future__ import annotations

TEAM_ID_DEFAULT = 118  # Royals
SEASON_DEFAULT = 2026
LEAGUE_MAP = {
    "AL": 103,
    "NL": 104,
}
PITCH_TYPE_MAP = {
    "FF": "4-Seam",
    "SI": "Sinker",
    "FC": "Cutter",
    "SL": "Slider",
    "ST": "Sweeper",
    "CU": "Curve",
    "KC": "Knuckle Curve",
    "CH": "Changeup",
    "FS": "Splitter",
    "SV": "Slurve",
    "CS": "Slow Curve",
    "FA": "Fastball",
}
SECTION_HELP = {
    "team_summary": "Overall team effectiveness and scoring balance across the season.",
    "rolling": "Short-term trend indicator using the last three completed games.",
    "inning": "Run production and prevention by inning across completed games.",
    "players": "Weighted offensive contribution ranking with trend and consistency overlays.",
    "pitching": "Run prevention effectiveness for starters and bullpen.",
    "advanced": "Statcast-style contact quality, spin, and pitch mix metrics where available.",
    "forecast": "Estimated playoff outlook and next-five-games win probabilities.",
}
