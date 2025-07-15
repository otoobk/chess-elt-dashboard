import pandas as pd
import numpy as np
import re
from datetime import datetime, timezone
from utils.opening_tree import OpeningTree

"""
Extract ECO code from PGN
"""
def extract_eco_code_from_pgn(pgn):
    if not pgn:
        return None
    match = re.search(r'\[ECO\s+"([A-E][0-9]{2})"\]', pgn)
    return match.group(1) if match else None

"""
Extract moves list from PGN
"""
def extract_moves_list_from_pgn(pgn, moves_list_max_size):
    if not pgn:
        return None
    pgn_moves_section = re.sub(r'\[.*?\]', '', pgn, flags=re.DOTALL)
    pgn_moves_section = re.sub(r'\{.*?\}', '', pgn_moves_section)
    pgn_moves_section = pgn_moves_section.replace('\n', ' ').strip()
    pgn_moves_section = re.sub(r'(1-0|0-1|1/2-1/2|\*)$', '', pgn_moves_section).strip()
    pgn_moves_section = re.sub(r'\d+\.(\.\.)?', '', pgn_moves_section).strip()
    moves = pgn_moves_section.split()
    return moves[:moves_list_max_size]

def find_opening_name(openings_tree, row):
        return openings_tree.search(row["eco"], row["moves_list"])

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
def create_games_dataframe(username, games, openings_tree):
    rows = []
    moves_list_max_size = openings_tree.get_max_depth()
    for g in games:
        white = g.get("white", {})
        black = g.get("black", {})
        pgn = g.get("pgn", "")

        start = extract_pgn_datetime(pgn, "Date", "StartTime")
        end = extract_pgn_datetime(pgn, "EndDate", "EndTime")
        duration = (end - start).total_seconds() if start and end else None

        game_url = g.get("url")

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
            "game_id": g.get("uuid"),
            "color_played": color_played,
            "user_rating": white.get("rating") if color_played == "white" else black.get("rating"),
            "opponent_rating": white.get("rating") if color_played == "black" else black.get("rating"),
            "win_loss": win_loss,
            "victory_method": result_raw,
            "date": start if start else None,
            "duration": duration,
            "time_class": g.get("time_class"),
            "rules": g.get("rules"),
            "moves": extract_moves_list_from_pgn(pgn, moves_list_max_size),
        })

    return pd.DataFrame(rows)

"""
Creates aggregate win/loss summary data based on games Dataframe
"""
def create_games_summary_dataframe(games_df):
    summary_df = (
        games_df.groupby(["win_loss", "eco", "family", "opening", "time_class"])
        .agg(game_count=("win_loss", "count"))
        .reset_index()
    )
    summary_df = summary_df.sort_values(by=["time_class", "win_loss", "game_count"], ascending=[False, False, False])
    return summary_df

def create_openings_tree(openings_df):
    openings_tree = OpeningTree()
    for _, row in openings_df.iterrows():
        moves = row["moves_list"]
        eco = row["eco"]
        family = row["family"]
        name = row["name"]
        openings_tree.insert(eco, family, moves, name)

    #openings_tree.print_tree()
    return openings_tree

def calculate_eco_opening(games_df, openings_tree):
    games_df[["eco", "family", "opening"]] = games_df.apply(
            lambda row: pd.Series(openings_tree.search(row["moves"])), axis=1
        )
    games_df = games_df.drop("moves", axis=1)
    return games_df

def create_games_metadata(games_df, last_n, kpi_results, top_openings_results):
    for time_class, group in games_df.groupby("time_class"):
        group = group.sort_values("date")

        if group.empty:
            continue    

        current_elo = group.iloc[-1]["user_rating"]

        if len(group) >= last_n:
            prev_elo = group.iloc[-last_n]["user_rating"]
            elo_change = current_elo - prev_elo
            last_n_games = group.iloc[-last_n:]
        else:
            prev_elo = group.iloc[0]["user_rating"]
            elo_change = current_elo - prev_elo
            last_n_games = group

        win_count = (group["win_loss"] == "win").sum()
        loss_count = (group["win_loss"] == "loss").sum()
        draw_count = (group["win_loss"] == "draw").sum()
        total_games = len(group)

        win_pct = (win_count / total_games) * 100 if total_games else None

        win_count_last_n = (last_n_games["win_loss"] == "win").sum()
        loss_count_last_n = (last_n_games["win_loss"] == "loss").sum()
        draw_count_last_n = (last_n_games["win_loss"] == "draw").sum()
        total_games_last_n = len(last_n_games)

        win_pct_last_n = (win_count_last_n / total_games_last_n) * 100 if total_games_last_n else None

        filtered = group[group["win_loss"].isin(["win", "loss"])]

        top_openings = (
            filtered.groupby(["opening", "win_loss"])
            .size()
            .reset_index(name="count")
            .pivot_table(index="opening", columns="win_loss", values="count", fill_value=0)
            .reset_index()
        )

        top_openings.columns.name = None
        top_openings = top_openings.rename(columns={"win": "win_count", "loss": "loss_count"})

        for col in ["win_count", "loss_count"]:
            if col not in top_openings.columns:
                top_openings[col] = 0

        top_openings["total_games"] = top_openings["win_count"] + top_openings["loss_count"]
        top_openings = top_openings.sort_values("total_games", ascending=False).head(5)

        # Add time_class column to top openings for exporting
        top_openings["time_class"] = time_class
        top_openings_results.append(top_openings)

        kpi_results.append({
            "time_class": time_class,
            "current_rating": current_elo,
            "rating_change_last_n": elo_change,
            "win_count": win_count,
            "loss_count": loss_count,
            "draw_count": draw_count,
            "win_pct": np.round(win_pct, 2),
            "win_count_10": win_count_last_n,
            "loss_count_10": loss_count_last_n,
            "draw_count_10": draw_count_last_n,
            "win_pct_10": np.round(win_pct_last_n, 2)
        })

    return kpi_results, top_openings_results