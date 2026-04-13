# MLB Streamlit Dashboard

## Run locally
```bash
pip install -r requirements.txt
streamlit run app.py
```

## Notes
- Core game data comes from MLB StatsAPI.
- Advanced metrics come from Baseball Savant Statcast CSV queries.
- If advanced metrics are missing, the app continues rendering core sections.
- Update formulas in `services/player_metrics.py`, `services/pitching_metrics.py`, `services/playoff_model.py`, and `services/game_forecast.py`.
