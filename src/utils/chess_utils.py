import re
from datetime import datetime, timezone
from pathlib import Path
from typing import List, Optional, Tuple

import pandas as pd
from pyspark.sql import DataFrame, SparkSession, Window
from pyspark.sql import functions as F

from utils.file_utils import *
from utils.opening_tree import OpeningTree

"""
Extract ECO code from PGN
"""
def extract_eco_code_from_pgn(pgn: str) -> str:
    if not pgn:
        return None
    match = re.search(r'\[ECO\s+"([A-E][0-9]{2})"\]', pgn)
    return match.group(1) if match else None

"""
Extract moves list from PGN
"""
def extract_moves_list_from_pgn(pgn: str, moves_list_max_size: int) -> list:
    if not pgn:
        return None
    pgn_moves_section = re.sub(r'\[.*?\]', '', pgn, flags=re.DOTALL)
    pgn_moves_section = re.sub(r'\{.*?\}', '', pgn_moves_section)
    pgn_moves_section = pgn_moves_section.replace('\n', ' ').strip()
    pgn_moves_section = re.sub(r'(1-0|0-1|1/2-1/2|\*)$', '', pgn_moves_section).strip()
    pgn_moves_section = re.sub(r'\d+\.(\.\.)?', '', pgn_moves_section).strip()
    moves = pgn_moves_section.split()
    return moves[:moves_list_max_size]

"""
Returns opening name based on game
"""
def find_opening_name(openings_tree: OpeningTree, row: pd.Series)-> str:
        return openings_tree.search(row["eco"], row["moves_list"])

"""
Returns game datetime based on game
"""
def extract_pgn_datetime(pgn: str, date_tag: str = "Date", time_tag: str = "StartTime") -> datetime:
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
def ts_to_dt(ts: pd.Timestamp) -> datetime:
            try:
                return datetime.fromtimestamp(ts, tz=timezone.utc)
            except Exception:
                return None
            
"""
Create Pandas DataFrame based on games JSON list
"""
def create_games_dataframe(username: str, games: List[Dict], openings_tree: OpeningTree) -> pd.DataFrame:
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
            "year": start.year if start else None,
            "duration": duration,
            "time_class": g.get("time_class"),
            "rules": g.get("rules"),
            "moves": extract_moves_list_from_pgn(pgn, moves_list_max_size),
        })

    return pd.DataFrame(rows)

"""
Creates aggregate win/loss summary data 
by time class
"""
def create_games_summary_dataframe(spark: SparkSession, username: str, clean_dir: str, time_classes: Optional[List[str]] = None) -> DataFrame:
    ensure_dir(clean_dir)

    path = str(Path(clean_dir) / f"{username}_games")

    sdf = spark.read.parquet(path)

    if time_classes:
        sdf = sdf.filter(F.col("time_class").isin(time_classes))

    summary_sdf = (
        sdf.groupBy("win_loss", "eco", "family", "opening", "time_class")
           .agg(F.count(F.lit(1)).alias("game_count"))
           .orderBy(
               F.col("time_class").desc(),
               F.col("win_loss").desc(),
               F.col("game_count").desc()
           )
    )
    return summary_sdf

"""
Creates tree of chess openings
"""
def create_openings_tree(openings_df: pd.DataFrame):
    openings_tree = OpeningTree()
    for _, row in openings_df.iterrows():
        moves = row["moves_list"]
        eco = row["eco"]
        family = row["family"]
        name = row["name"]
        openings_tree.insert(eco, family, moves, name)

    return openings_tree

"""
Calculates ECO, opening, opening family
"""
def calculate_eco_opening(games_df: pd.DataFrame, openings_tree: OpeningTree) -> pd.DataFrame:
    games_df[["eco", "family", "opening"]] = games_df.apply(
            lambda row: pd.Series(openings_tree.search(row["moves"])), axis=1
        )
    games_df = games_df.drop("moves", axis=1)
    return games_df

"""
Calculates game metadata and KPIs
"""
def create_games_metadata(spark: SparkSession, username: str, last_n: int, clean_dir: str, time_classes: Optional[List[str]] = None) -> Tuple[DataFrame, DataFrame]:
    path = str(Path(clean_dir) / f"{username}_games")
    games_sdf = spark.read.parquet(path)
    
    if time_classes:
        games_sdf = games_sdf.filter(F.col("time_class").isin(time_classes))

    games_sdf = (
        games_sdf
        .withColumn("date", F.to_timestamp("date"))
        .withColumn("user_rating", F.col("user_rating").cast("int"))
    )

    w_part = Window.partitionBy("time_class")
    w_asc  = Window.partitionBy("time_class").orderBy(F.col("date").asc())
    w_desc = Window.partitionBy("time_class").orderBy(F.col("date").desc())

    df = (
        games_sdf
        .withColumn("rn_asc",  F.row_number().over(w_asc))
        .withColumn("rn_desc", F.row_number().over(w_desc))
        .withColumn("n_rows",  F.count(F.lit(1)).over(w_part))
    )

    df = df.withColumn(
        "target_prev_rn",
        F.when(F.col("n_rows") >= F.lit(last_n),
               F.col("n_rows") - F.lit(last_n) + F.lit(1)
        ).otherwise(F.lit(1))
    )

    df = (
        df
        .withColumn("current_elo_cand", F.when(F.col("rn_desc") == 1, F.col("user_rating")))
        .withColumn("prev_elo_cand",    F.when(F.col("rn_asc")  == F.col("target_prev_rn"), F.col("user_rating")))
        .withColumn("is_last_n",        F.col("rn_desc") <= F.lit(last_n))
    )

    kpis_sdf = (
        df.groupBy("time_class").agg(
            F.max("current_elo_cand").alias("current_rating"),
            F.max("prev_elo_cand").alias("prev_rating"),
            F.sum(F.when(F.col("win_loss")=="win",  1).otherwise(0)).alias("win_count"),
            F.sum(F.when(F.col("win_loss")=="loss", 1).otherwise(0)).alias("loss_count"),
            F.sum(F.when(F.col("win_loss")=="draw", 1).otherwise(0)).alias("draw_count"),
            F.count(F.lit(1)).alias("total_games"),
            F.sum(F.when((F.col("win_loss")=="win")  & F.col("is_last_n"), 1).otherwise(0)).alias("win_count_last_n"),
            F.sum(F.when((F.col("win_loss")=="loss") & F.col("is_last_n"), 1).otherwise(0)).alias("loss_count_last_n"),
            F.sum(F.when((F.col("win_loss")=="draw") & F.col("is_last_n"), 1).otherwise(0)).alias("draw_count_last_n"),
            F.sum(F.when(F.col("is_last_n"), 1).otherwise(0)).alias("total_games_last_n"),
        )
        .withColumn("rating_change_last_n", F.col("current_rating") - F.col("prev_rating"))
        .withColumn("win_pct", F.round(F.col("win_count")/F.col("total_games")*100, 2))
        .withColumn("win_pct_last_n", F.round(F.col("win_count_last_n")/F.col("total_games_last_n")*100, 2))
        .select(
            "time_class","current_rating","rating_change_last_n",
            "win_count","loss_count","draw_count","win_pct",
            "win_count_last_n","loss_count_last_n","draw_count_last_n","win_pct_last_n"
        )
    )

    wl = df.filter(F.col("win_loss").isin("win","loss"))
    top_openings_sdf = (
        wl.groupBy("time_class","color_played","opening")
          .pivot("win_loss", ["win","loss"])
          .agg(F.count(F.lit(1)))
          .na.fill(0, subset=["win","loss"])
          .withColumnRenamed("win","win_count")
          .withColumnRenamed("loss","loss_count")
          .withColumn("total_games", F.col("win_count") + F.col("loss_count"))
    )

    rank_w = Window.partitionBy(["time_class","color_played"]).orderBy(F.col("total_games").desc(), F.col("opening").asc())
    top_openings_sdf = (
        top_openings_sdf
        .withColumn("rank", F.row_number().over(rank_w))
        .filter(F.col("rank") <= 5)
        .drop("rank")
    )

    return kpis_sdf, top_openings_sdf

"""
Cleans PGN moves list
"""
def clean_openings_pdf(openings_pdf: pd.DataFrame) -> pd.DataFrame:
    openings_pdf["moves_list"] = openings_pdf["pgn"].str.replace(r"\d+\.", "", regex=True).str.strip().str.split()
    return openings_pdf