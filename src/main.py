from pathlib import Path
import pandas as pd
from utils.api_utils import fetch_all_games
from utils.chess_utils import create_games_dataframe, create_games_summary_dataframe, create_openings_tree, calculate_eco_opening
from utils.file_utils import ensure_dir, load_csv, save_csv
from utils.config_utils import config, PROJ_PATH

def main():
    username = config["username"]
    raw_dir = (Path(PROJ_PATH) / config["raw_dir"]).resolve()
    clean_dir = (Path(PROJ_PATH) / config["clean_dir"]).resolve()
    ref_dir = (Path(PROJ_PATH) / config["ref_dir"]).resolve()
    openings_file = config["openings_file"]
    all_archives = True if config["all_archives"]=="True" else False
    headers = config["headers"]

    ensure_dir(raw_dir)
    ensure_dir(clean_dir)

    games = fetch_all_games(username, raw_dir, headers, all_archives)
    openings_df = load_csv((ref_dir / openings_file).resolve())
    
    openings_df["moves_list"] = openings_df["pgn"].str.replace(r"\d+\.", "", regex=True).str.strip().str.split()
    openings_tree = create_openings_tree(openings_df)
    
    games_df = create_games_dataframe(username, games, openings_tree)
    games_df = calculate_eco_opening(games_df, openings_tree)
    summary_df = create_games_summary_dataframe(games_df)

    save_csv(games_df, clean_dir / f"{username}_games.csv")
    save_csv(summary_df, clean_dir / f"{username}_summary.csv")

if __name__ == "__main__":
    main()

