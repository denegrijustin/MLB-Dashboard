from typing import Optional


def project_record(team_summary: dict, games_played: int, total_games: int = 162) -> dict:
    wins = team_summary.get("wins", 0)
    losses = team_summary.get("losses", 0)

    if games_played <= 0:
        return {
            "projected_wins": wins,
            "projected_losses": losses,
            "projected_pct": 0.0,
        }

    current_pct = wins / games_played
    remaining = total_games - games_played
    proj_wins = round(wins + current_pct * remaining)
    proj_losses = total_games - proj_wins
    proj_pct = proj_wins / total_games

    return {
        "projected_wins": proj_wins,
        "projected_losses": proj_losses,
        "projected_pct": round(proj_pct, 3),
    }


def estimate_playoff_odds(
    standings_row: dict,
    division_standings: list,
    wild_card_standings: list,
) -> dict:
    if not standings_row:
        return {
            "division_prob": 0.0,
            "wildcard_prob": 0.0,
            "playoff_prob": 0.0,
            "projected_seed": None,
        }

    wins = standings_row.get("wins", 0)
    losses = standings_row.get("losses", 0)
    games_played = wins + losses
    if games_played == 0:
        return {
            "division_prob": 0.0,
            "wildcard_prob": 0.0,
            "playoff_prob": 0.0,
            "projected_seed": None,
        }

    pct = wins / games_played

    # Division leader
    div_leader_pct = 0.5
    if division_standings:
        leader = division_standings[0]
        l_wins = leader.get("wins", 1)
        l_losses = leader.get("losses", 1)
        l_gp = l_wins + l_losses
        if l_gp > 0:
            div_leader_pct = l_wins / l_gp

    # Simple log5-inspired estimate
    division_prob = min(max(pct / (pct + div_leader_pct) if div_leader_pct > 0 else 0.5, 0.0), 1.0)

    # Wild card: check position among wild card teams
    wc_probs = []
    for wc_team in wild_card_standings[:3]:
        wc_wins = wc_team.get("wins", 1)
        wc_losses = wc_team.get("losses", 1)
        wc_gp = wc_wins + wc_losses
        if wc_gp > 0:
            wc_pct = wc_wins / wc_gp
            wc_probs.append(pct / (pct + wc_pct) if (pct + wc_pct) > 0 else 0.5)

    wildcard_prob = min(sum(wc_probs) / len(wc_probs) if wc_probs else 0.3, 1.0)

    playoff_prob = min(division_prob * 0.6 + wildcard_prob * 0.4, 1.0)

    return {
        "division_prob": round(division_prob, 3),
        "wildcard_prob": round(wildcard_prob, 3),
        "playoff_prob": round(playoff_prob, 3),
        "projected_seed": 1 if division_prob > 0.5 else (4 if wildcard_prob > 0.5 else None),
    }
