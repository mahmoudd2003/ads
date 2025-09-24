
import pandas as pd
import os

def fetch_tiktok_ads(keywords, country, csv_path="tiktok_ads.csv"):
    if not os.path.exists(csv_path):
        return pd.DataFrame()
    try:
        df = pd.read_csv(csv_path)
    except Exception:
        df = pd.read_csv(csv_path, encoding="utf-8", errors="ignore")
    df["_source"] = "TikTok"
    if "country" not in df.columns:
        df["country"] = country
    return df
