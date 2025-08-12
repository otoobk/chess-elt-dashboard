import os
import requests
import time
from datetime import datetime
from dateutil.relativedelta import relativedelta
from utils.file_utils import load_json, save_json
from utils.file_utils import ensure_dir

"""
Returns list of monthly archive URLs
"""
def get_archives(username, headers):
    url = f"https://api.chess.com/pub/player/{username}/games/archives"
    response = requests.get(url, headers=headers)
    response.raise_for_status()
    return response.json()["archives"]

"""
Returns JSON games data based on archive URL
"""
def fetch_archive_games(archive_url, headers):
    response = requests.get(archive_url, headers=headers)
    response.raise_for_status()
    return response.json().get("games", [])

"""
Returns JSON file name based on archive URL
"""
def archive_to_filename(archive_url, username, raw_dir):
    parts = archive_url.strip("/").split("/")[-2:]

    dir_path = os.path.join(raw_dir, username, parts[0], parts[1])
    
    os.makedirs(dir_path, exist_ok=True)
    
    return os.path.join(dir_path, "games.json")

"""
Returns all JSON games data
"""
def fetch_all_games(username, raw_dir, headers, all_archives):
    ensure_dir(raw_dir)

    archives = get_archives(username, headers)
    all_games = []

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

        all_games.extend(games)

    return all_games

def get_archive_url_datetime(url):
    return datetime(int(url.split("/")[-2]), int(url.split("/")[-1]), 1)
