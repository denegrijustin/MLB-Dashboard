LOGO_BASE = "https://www.mlbstatic.com/team-logos/{team_id}.svg"


def logo_url(team_id: int) -> str:
    return LOGO_BASE.format(team_id=team_id)


def logo_img(team_id: int, abbrev: str = "", size: int = 40) -> str:
    url = logo_url(team_id)
    return f'<img src="{url}" width="{size}" height="{size}" alt="{abbrev}" onerror="this.style.display=\'none\'" />'
