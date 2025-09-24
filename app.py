# ===== Robust path + dynamic import =====
import sys
from pathlib import Path
import importlib.util
import streamlit as st
import pandas as pd

APP_DIR = Path(__file__).resolve().parent

# جرّب مسارات شائعة لإضافة src إلى sys.path
CANDIDATE_PATHS = [
    APP_DIR,                  # …/ads
    APP_DIR / "src",         # …/ads/src
    APP_DIR.parent,          # …
    APP_DIR.parent / "src",  # …/src
]
for p in CANDIDATE_PATHS:
    if p.exists():
        sp = str(p)
        if sp not in sys.path:
            sys.path.insert(0, sp)

def import_or_load(module_name: str, file_rel: str):
    """
    جرّب import بالحِزمة؛ ولو فشل، حمّل الملف مباشرة من المسار النسبي.
    """
    try:
        return __import__(module_name, fromlist=['*'])
    except Exception:
        f = APP_DIR / file_rel
        if not f.exists():
            st.error(f"❌ لم أجد الملف: {f}")
            st.write("تحقّق من الأسماء بالضبط (case-sensitive) ومن وجود __init__.py")
            st.stop()
        spec = importlib.util.spec_from_file_location(module_name.split(".")[-1], f)
        mod = importlib.util.module_from_spec(spec)
        spec.loader.exec_module(mod)
        return mod

# === استيراد الوحدات (مع fallback مباشر من الملفات) ===
meta_ads     = import_or_load("src.collectors.meta_ads",     "src/collectors/meta_ads.py")
trends_mod   = import_or_load("src.collectors.trends",       "src/collectors/trends.py")
tiktok_mod   = import_or_load("src.collectors.tiktok_ads",   "src/collectors/tiktok_ads.py")
normalize_mod= import_or_load("src.processing.normalize",    "src/processing/normalize.py")
scoring_mod  = import_or_load("src.processing.scoring",      "src/processing/scoring.py")
ai_mod       = import_or_load("src.ai.llm_analyzer",         "src/ai/llm_analyzer.py")

fetch_ads_by_keywords = meta_ads.fetch_ads_by_keywords
fetch_trends_scores   = trends_mod.fetch_trends_scores
fetch_tiktok_ads      = tiktok_mod.fetch_tiktok_ads
normalize_ads         = normalize_mod.normalize_ads
score_gap             = scoring_mod.score_gap
analyze_batches       = ai_mod.analyze_batches

# ===== UI =====
st.set_page_config(page_title="Gap Analysis MVP", page_icon="📊", layout="wide")
st.title("📊 Gap Analysis – MVP (Meta + Google Trends + TikTok)")

with st.sidebar:
    country = st.selectbox("Country", ["JO", "SA", "AE", "EG"], index=0)
    sector  = st.selectbox("Sector",  ["Furniture","Electronics","Fashion","Food"])
    seeds   = st.text_area("Seed keywords (one per line)",
                           value="كنب\nسرير مع تخزين\nمراتب طبية\nطاولة قابلة للطي")
    max_ads = st.slider("Max ads per keyword", 50, 500, 200, 50)
    run     = st.button("Run Analysis")

if run:
    kw_list = [s.strip() for s in seeds.splitlines() if s.strip()]

    with st.spinner("Collecting Meta ads..."):
        meta_df = fetch_ads_by_keywords(kw_list, country, limit=max_ads)
    st.success(f"Meta Ads: {len(meta_df)} rows")

    with st.spinner("Collecting Google Trends..."):
        trends_df = fetch_trends_scores(kw_list, country)
    st.success("Trends collected")

    with st.spinner("Collecting TikTok ads (CSV/Apify)..."):
        tiktok_df = fetch_tiktok_ads(kw_list, country)
    st.success(f"TikTok Ads: {len(tiktok_df)} rows")

    with st.spinner("Normalizing..."):
        meta_clean = normalize_ads(meta_df)

    with st.spinner("AI analysis (products/angles/objections)..."):
        llm_df = analyze_batches(meta_clean, country)

    with st.spinner("Scoring gaps..."):
        result = score_gap(meta_clean, llm_df, trends_df, tiktok_df)

    st.subheader("Top Gap Opportunities")
    if result is not None and not result.empty:
        st.dataframe(result.sort_values("gap_score", ascending=False).head(25))
        st.download_button("Download CSV",
                           result.to_csv(index=False),
                           "gap_opportunities.csv", "text/csv")
    else:
        st.info("No results to show yet. Try increasing keywords or ads limit.")
