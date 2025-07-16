# 🧠 chess-elt-dashboard  
### Scalable Chess Analytics Pipeline using Spark, Docker, and the Chess.com API

![Python](https://img.shields.io/badge/Python-3.10-blue?logo=python)
![Spark](https://img.shields.io/badge/Spark-PySpark-orange?logo=apache-spark)
![Docker](https://img.shields.io/badge/Docker-Containerized-blue?logo=docker)

---

## 📌 Overview

`chess-elt-dashboard` is a modular and scalable **ELT** pipeline that ingests public game data from the Chess.com API, stages raw data to disk, and processes it using PySpark into optimized datasets for analytics and dashboarding. It simulates a production-grade, cloud-scalable architecture to showcase data engineering best practices like modularity, scalability, and reproducibility — making it perfect for portfolio use when applying to data roles.

---

## ⚙️ Tech Stack

- **Language**: Python 3.10  
- **Processing Engine**: Apache Spark (PySpark)  
- **Containerization**: Docker & Docker Compose  
- **Data Source**: [Chess.com Public API](https://www.chess.com/news/view/published-data-api)  
- **Output**: Structured data files (Parquet/CSV) on mounted volumes  
- **Dashboarding**: Tableau / Power BI (via exported files)  
- **Architecture**: ELT (Extract, Load, Transform)

---

## 🧱 Architecture & Design Strategy

```plaintext
                  +---------------------+
                  |   Chess.com API     |
                  +----------+----------+
                             |
                         [Extract]
                             |
                             v
                  +---------------------+
                  | Raw JSON Game Files |
                  +----------+----------+
                             |
                         [Load]
                             |
                             v
                   +------------------+
                   |  PySpark ETL Job |
                   |  (transform step)|
                   +--------+---------+
                            |
                         [Transform]
                            |
                   +----------------------+
                   | Aggregated Datasets  |
                   |   & Chess KPIs       |
                   +----------+-----------+
                              |
                (Tableau / Power BI dashboards)
```

### Key Design Highlights

- 🧩 **Modular Components**: `api/`, `processing/`, `utils/`
- 🧠 **Optimized Opening Classification**: Uses a **Trie Tree** structure for fast fuzzy matching
- ⚙️ **Scalable**: Designed to batch ingest thousands of games per user
- 🐳 **Fully Dockerized**: Zero local setup required
- 🔜 **Planned**: Airflow integration and data warehouse staging (e.g., Snowflake or Delta Lake)

---

## 🚀 Getting Started

### 🧰 Prerequisites

- Docker + Docker Compose
- (Optional) Tableau or Power BI for dashboarding

### 🔧 Build the Project
```bash
docker-compose build
```

## ▶️ Run the Pipeline
```bash
docker-compose run --rm spark-app <optional --username username --allarchives>
```

## 📊 Output Structure

After running, you'll find data in `/data/processed/`:
- `kpis.csv`: Game results, rating change, and win rates by time class
- `top_openings.csv`: Most played openings (wins/losses)
- `games_clean.csv`: Structured move-level data
- Output is dashboard-ready (load into Power BI / Tableau)

---

## 📈 Sample Dashboards

---

## 🧠 Design Highlights

- ✅ **ELT Architecture**: Raw data is staged before transformation
- ✅ **PySpark Transformations**: Efficient and scalable for large user histories
- ✅ **Trie Tree for Opening Detection**: Fast, flexible classification of chess openings
- ✅ **Dockerized & Modular**: No external dependencies, code split into logical units
- ✅ **Easily Extendable**: Future support for streaming, orchestration (Airflow), and warehouse loads

---

## 🔮 Future Enhancements

- ☁️ Load processed data into a cloud data lake (e.g., S3 + Snowflake/Delta Lake)
- 🪂 Airflow DAGs for production scheduling
- 🧪 Unit tests and CI/CD via GitHub Actions
- 📊 Public dashboard on Tableau Public or Power BI Service

---

## 👤 Author

**Brendan O'Toole**  
_Data Engineer passionate about building scalable data pipelines and analytics platforms — and a chess nerd on the side ♟️_  
[GitHub](https://github.com/otoobk) • [LinkedIn](https://www.linkedin.com/in/brendan-k-otoole/

