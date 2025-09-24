
import requests, time, pandas as pd, streamlit as st

BASE = "https://graph.facebook.com/{ver}/ads_archive"
FIELDS = ",".join([
  "id","page_name","page_id","ad_creation_time",
  "ad_delivery_start_time","ad_delivery_stop_time",
  "ad_snapshot_url","ad_creative_bodies",
  "ad_creative_link_titles","ad_creative_link_descriptions",
  "publisher_platforms","languages","impressions"
])

def fetch_ads_for_keyword(keyword, country, limit=200):
    url = BASE.format(ver=st.secrets.get("META_API_VERSION","v19.0"))
    params = {
        "search_terms": keyword,
        "ad_reached_countries": country,
        "ad_active_status": "ALL",
        "fields": FIELDS,
        "access_token": st.secrets["META_ACCESS_TOKEN"],
        "limit": min(limit,200)
    }
    rows = []
    while True:
        r = requests.get(url, params=params, timeout=60)
        if r.status_code != 200:
            st.warning(f"Meta error for '{keyword}': {r.text[:250]}")
            break
        data = r.json()
        rows += data.get("data",[])
        if len(rows) >= limit or "next" not in data.get("paging",{}):
            break
        url, params = data["paging"]["next"], {}
        time.sleep(0.4)
    for d in rows: d["_keyword"] = keyword
    return rows

def fetch_ads_by_keywords(keywords, country, limit=200):
    all_rows = []
    for kw in keywords:
        all_rows += fetch_ads_for_keyword(kw, country, limit)
    return pd.json_normalize(all_rows) if all_rows else pd.DataFrame()
