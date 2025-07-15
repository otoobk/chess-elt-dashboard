import os
import json
import pandas as pd

def ensure_dir(path):
    os.makedirs(path, exist_ok=True)

def save_json(data, path):
    with open(path, "w", encoding="utf-8") as f:
        json.dump(data, f, ensure_ascii=False, indent=2)

def load_json(path):
    with open(path, "r", encoding="utf-8") as f:
        return json.load(f)

def save_csv(df, path):
    df.to_csv(path, index=False)

def save_csv_with_index(df, path):
    df.to_csv(path, index=True)

def load_csv(path):
    return pd.read_csv(path) if os.path.exists(path) else pd.DataFrame()
