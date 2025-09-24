
import pandas as pd
from langdetect import detect

def _unify_text(row):
    parts = []
    bodies = row.get("ad_creative_bodies", [])
    titles = row.get("ad_creative_link_titles", [])
    descs  = row.get("ad_creative_link_descriptions", [])
    for arr in (bodies, titles, descs):
        if isinstance(arr, list):
            parts += [t for t in arr if isinstance(t, str)]
    return " | ".join(parts)[:5000]

def _safe_lang(text):
    try:
        return detect(text) if text and text.strip() else ""
    except Exception:
        return ""

def normalize_ads(df: pd.DataFrame) -> pd.DataFrame:
    if df is None or df.empty:
        return pd.DataFrame()
    out = df.copy()
    out["ad_text"] = out.apply(_unify_text, axis=1)
    out["lang"] = out["ad_text"].apply(_safe_lang)
    out["start_time"] = pd.to_datetime(out.get("ad_delivery_start_time"), errors="coerce", utc=True)
    out["stop_time"]  = pd.to_datetime(out.get("ad_delivery_stop_time"),  errors="coerce", utc=True)
    out["is_active"]  = out["stop_time"].isna()
    now = pd.Timestamp.utcnow()
    out["age_hours"]  = ((now - out["start_time"]).dt.total_seconds()/3600).clip(lower=0)

    out["impressions_mid"] = 0
    out["velocity"] = (out["impressions_mid"] / out["age_hours"].replace(0,1)).fillna(0)

    out["ad_key"] = out["page_id"].astype(str) + "::" + out["ad_text"].str[:120].fillna("")
    counts = out["ad_key"].value_counts().to_dict()
    out["sustained_spend"] = out["ad_key"].map(counts) + (out["age_hours"]/24.0)

    cols = ["_keyword","id","page_id","page_name","ad_snapshot_url","ad_text","lang",
            "start_time","stop_time","is_active","age_hours","velocity","sustained_spend"]
    return out[cols]
