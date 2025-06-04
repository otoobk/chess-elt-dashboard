from pathlib import Path
from utils.api_utils import fetch_all_games
from utils.chess_utils import create_games_dataframe, create_games_summary_dataframe
from utils.file_utils import ensure_dir, save_csv
from utils.config_utils import config, PROJ_PATH

def main():
    username = config["username"]
    raw_dir = (Path(PROJ_PATH) / config["raw_dir"]).resolve()
    clean_dir = (Path(PROJ_PATH) / config["clean_dir"]).resolve()
    all_archives = True if config["all_archives"]=="True" else False
    headers = config["headers"]

    ensure_dir(raw_dir)
    ensure_dir(clean_dir)

    games = fetch_all_games(username, raw_dir, headers, all_archives)
    df = create_games_dataframe(username, games)
    summary_df = create_games_summary_dataframe(df)

    save_csv(df, clean_dir / f"{username}_games.csv")
    save_csv(summary_df, clean_dir / f"{username}_summary.csv")

if __name__ == "__main__":
    main()

