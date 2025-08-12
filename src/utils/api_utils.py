import os
import time
from datetime import datetime

import requests
from dateutil.relativedelta import relativedelta

from utils.file_utils import ensure_dir, load_json, save_json

"""
Returns list of monthly archive URLs
"""
def get_archives(username: str, headers) -> list:
    url = f"https://api.chess.com/pub/player/{username}/games/archives"
    response = requests.get(url, headers=headers)
    response.raise_for_status()
    return response.json()["archives"]

"""
Returns JSON game data based on archive URL
"""
def fetch_archive_games(archive_url: str, headers):
    response = requests.get(archive_url, headers=headers)
    response.raise_for_status()
    return response.json().get("games", [])

"""
Returns JSON file name based on archive URL
"""
def archive_to_filename(archive_url: str, username: str, raw_dir: str):
    parts = archive_url.strip("/").split("/")[-2:]

    dir_path = os.path.join(raw_dir, username, parts[0])
    
    os.makedirs(dir_path, exist_ok=True)
    
    return os.path.join(dir_path, "games.json")

"""
Saves all JSON game data to raw data dir
"""
def fetch_all_games(username: str, raw_dir: str, headers, all_archives: bool):
    ensure_dir(raw_dir)

    archives = get_archives(username, headers)

    if not all_archives:
        year_ago_date = datetime.now() - relativedelta(years=1)
        archives = [
            url for url in archives
            if get_archive_url_datetime(url) >= year_ago_date
        ]

    for archive_url in archives:
        filename = archive_to_filename(archive_url, username, raw_dir)

        if os.path.exists(filename):
            games = load_json(filename)
        else:
            print(f"Fetching: {archive_url}")
            games = fetch_archive_games(archive_url, headers)
            save_json(games, filename)
            time.sleep(0.5)

"""
Returns archive datetime based on archive URL
"""
def get_archive_url_datetime(url: str) -> datetime:
    return datetime(int(url.split("/")[-2]), int(url.split("/")[-1]), 1)
