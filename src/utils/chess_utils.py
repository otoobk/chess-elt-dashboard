import pandas as pd
from datetime import datetime, timezone
from urllib.parse import unquote, urlparse
import re
from utils.file_utils import load_csv, save_csv

"""
Extract ECO code from PGN
"""
def extract_eco_code_from_pgn(pgn):
    if not pgn:
        return None
    match = re.search(r'\[ECO\s+"([A-E][0-9]{2})"\]', pgn)
    return match.group(1) if match else None

def get_opening_name_from_url(url):
    if not url:
        return None
    if isinstance(url, bytes):
        url = url.decode("utf-8") 
    path = urlparse(url).path
    last_part = path.split("/")[-1]
    return unquote(last_part.strip().replace("-", " ")).title()

def extract_pgn_datetime(pgn, date_tag="Date", time_tag="StartTime"):
    date_match = re.search(rf'\[{date_tag} "(\d{{4}}\.\d{{2}}\.\d{{2}})"\]', pgn)
    time_match = re.search(rf'\[{time_tag} "(\d{{2}}:\d{{2}}:\d{{2}})"\]', pgn)
    if date_match and time_match:
        date_str = date_match.group(1).replace('.', '-')
        time_str = time_match.group(1)
        try:
            return datetime.strptime(f"{date_str} {time_str}", "%Y-%m-%d %H:%M:%S")
        except ValueError:
            return None
    return None

"""
Convert Timestamp to Datetime
"""
def ts_to_dt(ts):
            try:
                return datetime.fromtimestamp(ts, tz=timezone.utc)
            except Exception:
                return None
            
"""
Create Pandas DataFrame based on games JSON list
"""
def create_games_dataframe(username, games):
    rows = []
    for g in games:
        white = g.get("white", {})
        black = g.get("black", {})
        pgn = g.get("pgn", "")

        start = extract_pgn_datetime(pgn, "Date", "StartTime")
        end = extract_pgn_datetime(pgn, "EndDate", "EndTime")
        duration = (end - start).total_seconds() if start and end else None

        game_url = g.get("url")
        game_id = game_url.rstrip("/").split("/")[-1] if game_url else None

        color_played = "white" if white.get("username") == username else "black"
        result_raw = white.get("result") if color_played == "white" else black.get("result")

        if result_raw == "win":
            win_loss = "win"
        elif result_raw in {"checkmated", "timeout", "resigned"}:
            win_loss = "loss"
        elif result_raw in {"agreed", "repetition", "stalemate", "insufficient", "50move"}:
            win_loss = "draw"
        else:
            win_loss = "other"

        rows.append({
            "game_id": game_id,
            "color_played": color_played,
            "user_rating": white.get("rating") if color_played == "white" else black.get("rating"),
            "opponent_rating": white.get("rating") if color_played == "black" else black.get("rating"),
            "win_loss": win_loss,
            "victory_method": result_raw,
            "eco": extract_eco_code_from_pgn(pgn),
            "date": start.date() if start else None,
            "duration": duration,
            "time_class": g.get("time_class"),
            "rules": g.get("rules"),
            "opening": get_opening_name_from_url(g.get("eco"))
        })

    return pd.DataFrame(rows)

"""
Parse proper Opening name from ECO URL
"""
def parse_opening_name(raw_eco):
    if raw_eco.startswith("http"):
        return unquote(raw_eco.split("/")[-1]).replace("-", " ").strip().lower()
    return raw_eco.strip().lower()

"""
Creates aggregate win/loss summary data based on games Dataframe
"""
def create_games_summary_dataframe(games_df):
    summary_df = (
        games_df.groupby(["win_loss", "eco", "opening", "time_class"])
        .agg(game_count=("win_loss", "count"))
        .reset_index()
    )
    summary_df = summary_df.sort_values(by=["time_class", "win_loss", "game_count"], ascending=[False, False, False])
    return summary_df