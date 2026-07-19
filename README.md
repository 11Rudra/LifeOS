# LifeOS

LifeOS is a personal command center for health, family, learning, and growth. It combines planning, journaling, and weekly time allocation into one simple interactive web app.

## Features
- Command center dashboard with core LifeOS principles
- Learning roadmap for technical growth
- Daily planner template for your routine
- Sunday review template for reflection
- Interactive journal entries
- Weekly planner for assigning time to health, family, career, learning, and rest

## Tech Stack
- Python
- Flask
- SQLite

## Run Locally
1. Change into the project directory:
   ```bash
   cd LifeOS
   ```
2. Install dependencies:
   ```bash
   pip install -r requirements.txt
   ```
3. Start the app:
   ```bash
   python3 main.py
   ```
4. Open http://127.0.0.1:8080

## Project Structure
- `00-Dashboard.md` – main command center
- `01-Learning-Roadmap.md` – learning roadmap
- `templates/` – planner and review templates
- `trackers/` – habit and metrics tracker
- `web/templates/` – Flask UI templates

## Notes
The app stores entries and planner data locally in `lifeos.db`.
