
import json, re, time, pandas as pd, streamlit as st
from typing import List, Dict
from openai import OpenAI

client = OpenAI(api_key=st.secrets["OPENAI_API_KEY"])

SYSTEM = "You are a market insight analyst for Arabic/English ads."

def _chunks(rows: List[Dict], n=20):
    for i in range(0, len(rows), n):
        yield rows[i:i+n]

def analyze_batches(df: pd.DataFrame, country: str) -> pd.DataFrame:
    if df.empty:
        return pd.DataFrame()
    rows = df.to_dict("records")
    items = []
    for chunk in _chunks(rows, 20):
        # Simple heuristic: pretend each ad maps to one 'product' token (for MVP fallback)
        for r in chunk:
            text = (r.get("ad_text") or "").strip().lower()
            if not text:
                continue
            # naive product extraction: take first 2 words
            product = " ".join(text.split()[:2])
            items.append({
                "product": product,
                "synonyms": "",
                "angles": "",
                "objections": "",
                "purchase_intent_pct": 0.0
            })
    # Deduplicate products
    if not items:
        return pd.DataFrame()
    df_out = pd.DataFrame(items)
    df_out = df_out.groupby("product", as_index=False).agg({
        "synonyms":"first",
        "angles":"first",
        "objections":"first",
        "purchase_intent_pct":"mean"
    })
    return df_out
