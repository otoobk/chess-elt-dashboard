from pathlib import Path
import pandas as pd
from utils.api_utils import fetch_all_games
from utils.chess_utils import *
from utils.config_utils import config, PROJ_PATH
from utils.file_utils import *
from utils.spark_utils import get_spark_session, stop_spark_session


def main():
    username = config["username"]
    raw_dir = (Path(PROJ_PATH) / config["raw_dir"]).resolve()
    clean_dir = (Path(PROJ_PATH) / config["clean_dir"]).resolve()
    final_dir = (Path(PROJ_PATH) / config["final_dir"]).resolve()
    ref_dir = (Path(PROJ_PATH) / config["ref_dir"]).resolve()
    openings_file = config["openings_file"]
    all_archives = True if config["all_archives"] == "True" else False
    headers = config["headers"]

    ensure_dir(raw_dir)
    ensure_dir(clean_dir)
    ensure_dir(final_dir)
    ensure_dir(ref_dir)

    spark = get_spark_session("chess-aggregates")

    game_lst = fetch_all_games(username, raw_dir, headers, all_archives)

    openings_pdf = load_csv((ref_dir / openings_file).resolve())
    openings_pdf = clean_openings_pdf(openings_pdf)

    openings_tree = create_openings_tree(openings_pdf)
    
    games_pdf = create_games_dataframe(username, game_lst, openings_tree)
    games_pdf = calculate_eco_opening(games_pdf, openings_tree)
    games_pdf.index.name = "game_rank"
    
    games_sdf = spark.createDataFrame(games_pdf)

    summary_sdf = create_games_summary_dataframe(spark, games_sdf)

    last_n = 20
    kpi_sdf, top_openings_spd = create_games_metadata(spark, games_sdf, last_n)

    save_csv_with_index(games_pdf, clean_dir / f"{username}_games.csv")
    save_parquet_sdf(games_sdf, clean_dir / f"{username}_games", False, True, "time_class")

    save_csv_sdf(summary_sdf, final_dir / f"{username}_summary", True)
    save_csv_sdf(kpi_sdf, final_dir / f"{username}_kpis", True)
    save_csv_sdf(top_openings_spd, final_dir / f"{username}_top_openings", True)

    stop_spark_session(spark)

if __name__ == "__main__":
    main()
