# Phase 5 - Deployment & Rollout

## Local Run
1. `python -m venv .venv && source .venv/bin/activate`
2. `pip install flask`
3. `python run.py`

Default login:
- username: `owner`
- password: `owner123`

## Operational Notes
- Database file: `data/pharmacy.db`
- Daily close verification via dashboard totals.
- Backups: archive `data/pharmacy.db` periodically.
