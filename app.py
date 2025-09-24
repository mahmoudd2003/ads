# ---------------- PATH FIX (robust) ----------------
import sys
from pathlib import Path

APP_DIR = Path(__file__).resolve().parent
CANDIDATE_PATHS = [
    APP_DIR,                      # …/ads/
    APP_DIR / "src",             # …/ads/src
    APP_DIR.parent,              # …/
    APP_DIR.parent / "src",      # …/src
]

for p in CANDIDATE_PATHS:
    if p.exists():
        sp = str(p)
        if sp not in sys.path:
            sys.path.insert(0, sp)

# ------------- Imports (after fixing path) -------------
import streamlit as st
import pandas as pd

# محاولة أولى للاستيراد مع تشخيص إذا فشل
try:
    from src.collectors.meta_ads import fetch_ads_by_keywords
    from src.collectors.trends import fetch_trends_scores
    from src.collectors.tiktok_ads import fetch_tiktok_ads
    from src.processing.normalize import normalize_ads
    from src.ai.llm_analyzer import analyze_batches
    from src.processing.scoring import score_gap
except ModuleNotFoundError as e:
    st.error(
        "❌ لم أستطع العثور على حزمة `src`. تأكد من أن مجلد `src/` موجود "
        "إمّا بجانب `app.py` أو في جذر المستودع. أيضًا تأكد من وجود ملفات "
        "`__init__.py` داخل `src/` وداخل مجلداته الفرعية (`collectors/`, `processing/`, `ai/`)."
    )
    # تشخيص سريع: عرض بنية المجلدات القريبة
    st.write("🔎 مسار التطبيق:", str(APP_DIR))
    st.write("📁 موجود؟ ads/src:", (APP_DIR / "src").exists())
    st.write("📁 موجود؟ ../src :", (APP_DIR.parent / "src").exists())
    st.stop()

# ---------------- Streamlit UI ----------------
st.set_page_config(page_title="Gap Analysis MVP", page_icon="📊", layout="wide")
st.title("📊 Gap Analysis – MVP (Meta + Google Trends + TikTok)")

with st.sidebar:
    country = st.selectbox("Country", ["JO", "SA", "AE", "EG"], index=0)
    sector = st.selectbox("Sector", ["Furniture", "Electronics", "Fashion", "Food"])
    seeds = st.text_area(
        "Seed keywords (one per line)",
        value="كنب\nسرير مع تخزين\nمراتب طبية\nطاولة قابلة للطي"
    )
    max_ads = st.slider("Max ads per keyword", 50, 500, 200, 50)
    run = st.button("Run Analysis")

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
        st.download_button(
            "Download CSV",
            result.to_csv(index=False),
            "gap_opportunities.csv",
            "text/csv"
        )
    else:
        st.info("No results to show yet. Try increasing keywords or ads limit.")
