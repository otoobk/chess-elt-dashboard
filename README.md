# Chess API Ingestion & Analytics Dashboaring Pipeline
This project is a Python based batch data pipeline ingests and processes player chess game data from the [Chess.com Public API](https://www.chess.com/news/view/published-data-api). Data is ingested and cached from the game archive API endpoint, retrieving all or only recent-year game data for a supplied user, and is then processed and aggregated to provide insightful analytics on ranking, game type win-loss ratios, best and worst openings, and more. 

## Setup
### Requirements
- Docker
- Optional: BI Tools (Power BI, Tableau, etc.)

### Installation
1. Clone repo
2. Pull latest from develop
3. cd chess
4. docker-compuse build
5. docker-compose run --rm spark-app <optional --username username --allarchives>