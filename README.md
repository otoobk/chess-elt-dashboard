# Chess API Ingestion & Analytics Dashboaring Pipeline
This project is a Python based batch data pipeline ingests and processes player chess game data from the [Chess.com Public API](https://www.chess.com/news/view/published-data-api). Data is ingested and cached from the game archive API endpoint, retrieving all or only recent-year game data for a supplied user, and is then processed and aggregated to provide insightful analytics on ranking, game type win-loss ratios, best and worst openings, and more. 

## Setup
### Requirements
- Python 3.8+
- pip and virtualenv
- Optional: BI Tools (Power BI, Tableau, etc.)

### Installation
- Clone repo
- Pull latest from develop
- cd chess
- python3 -m venv .venv
- source .venv\Scripts\activate (on Windows)
- python -m pip install --upgrade pip
- pip install -r requirements.txt

### Usage
python ./src/main.py <optional --username username --allarchives>