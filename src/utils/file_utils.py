import json
import os
from pathlib import Path
from pyspark.sql import DataFrame, SparkSession
from typing import Dict, List, Optional
from uuid import uuid4

import pandas as pd


"""
Ensures specified path is an existing directory, creates one if not currently is
"""
def ensure_dir(path: str):
    os.makedirs(path, exist_ok=True)

"""
Saves JSON to specified path
"""
def save_json(data, path: str):
    path = Path(path)
    with open(path, "w", encoding="utf-8") as f:
        json.dump(data, f, ensure_ascii=False, indent=2)

"""
Loads JSON from specified path
"""
def load_json(path: str):
    path = Path(path)
    with open(path, "r", encoding="utf-8") as f:
        return json.load(f)

"""
Saves Pandas DataFrame as CSV to specified path
OPTIONAL: 
    save_index to save with index
"""
def save_csv_pdf(df: pd.DataFrame, path: str, save_index: bool = False):
    path = Path(path)
    df.to_csv(path, index=save_index)

"""
Loads Pandas DataFrame from CSV at specified path
"""
def load_csv_pdf(path: str) -> pd.DataFrame:
    path = Path(path)
    return pd.read_csv(path) if os.path.exists(path) else pd.DataFrame()

"""
Saves PySpark DataFrame as CSV to specified path
OPTIONAL: 
    coalesce to save CSV as one partition
    header to save CSV including header line
"""
def save_csv_sdf(sdf: DataFrame, path: str, coalesce: bool = True, header: bool = True):
    if coalesce:
        sdf = sdf.coalesce(1) 
    
    (
        sdf.write
        .option("header", header)
        .mode("overwrite")
        .csv(path)
    )

"""
Saves PySpark DataFrame as Parquet to specified path
OPTIONAL: 
    coalesce to save Parquet as one partition
    overwrite to save Parquet over any existing
    partition_by to save Parquet partitioned by list of cols
"""
def save_parquet_sdf(sdf: DataFrame, path: str, coalesce: bool = True, overwrite: bool = True, partition_by: Optional[List[str]] = None):
    out_path = str(path)

    if coalesce:
        sdf = sdf.coalesce(1)

    writer = (
                sdf.write
                    .mode("overwrite" if overwrite else "errorifexists")
                    .option("compression", "snappy")
            )

    if partition_by:
        writer = writer.partitionBy(partition_by)

    writer.parquet(out_path)

"""
Loads JSON list from games.JSON files at specified path
"""
def get_games_list(username: str, raw_dir: str) -> List[Dict]:
    raw_dir_path = Path(raw_dir) / username

    games_list: List[Dict] = []

    for file in sorted(raw_dir_path.rglob("games.json")):
        with open(file, "r") as f:
            games_list.extend(json.load(f)) 

    return games_list

"""
Saves all final Parquet files as CSV to specified export path
"""
def export_final_to_csv(spark: SparkSession, username: str, final_dir: str, export_dir: str):
    final_dir  = Path(final_dir)
    export_dir = Path(export_dir)

    for ds_dir in final_dir.iterdir():
        if not ds_dir.is_dir():
            continue
        if not ds_dir.name.startswith(username):
            continue
        if not any(ds_dir.rglob("*.parquet")):
            continue

        sdf = spark.read.parquet(str(ds_dir))

        tmp = export_dir / f"__tmp_{uuid4().hex}"
        tmp.mkdir(exist_ok=True)
        (sdf.coalesce(1)
            .write.mode("overwrite")
            .option("header", True)
            .csv(str(tmp)))

        part = next(tmp.glob("*.csv"))
        out_file = export_dir / f"{ds_dir.name}.csv"
        part.replace(out_file)  

        for p in tmp.glob("*"): p.unlink()
        tmp.rmdir()