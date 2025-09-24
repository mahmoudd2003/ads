
import pandas as pd

def _z(s):
    s = pd.to_numeric(s, errors="coerce").fillna(0.0)
    mu, sd = s.mean(), s.std(ddof=0)
    return (s - mu)/sd if sd != 0 else s*0

def score_gap(meta_clean: pd.DataFrame,
              llm_df: pd.DataFrame,
              trends_df: pd.DataFrame,
              tiktok_df: pd.DataFrame) -> pd.DataFrame:
    if llm_df is None or llm_df.empty:
        return pd.DataFrame()

    agg = llm_df.groupby("product", as_index=False).agg({
        "synonyms":"first",
        "angles":"first",
        "objections":"first",
        "purchase_intent_pct":"mean"
    })

    if meta_clean is not None and not meta_clean.empty:
        meta_clean = meta_clean.copy()
        meta_clean["text_lc"] = meta_clean["ad_text"].str.lower()
        hits = []
        for p in agg["product"]:
            hits.append(meta_clean["text_lc"].str.contains(p, na=False).mean())
        agg["mention_rate"] = hits
        agg["velocity"] = meta_clean["velocity"].mean()
        agg["sustained_spend"] = meta_clean["sustained_spend"].mean()
    else:
        agg["mention_rate"] = 0.0
        agg["velocity"] = 0.0
        agg["sustained_spend"] = 0.0

    if trends_df is not None and not trends_df.empty:
        trend_map = trends_df.groupby("keyword")["trend_score"].mean().to_dict()
        agg["trend_score"] = agg["product"].map(trend_map).fillna(0.0)
    else:
        agg["trend_score"] = 0.0

    if tiktok_df is not None and not tiktok_df.empty:
        cols = [c for c in tiktok_df.columns if any(k in c.lower() for k in ["view","like","comment"])]
        tiktok_signal = tiktok_df[cols].sum().sum() if cols else 0.0
        agg["tiktok_velocity"] = float(tiktok_signal) / max(len(tiktok_df),1)
    else:
        agg["tiktok_velocity"] = 0.0

    agg["demand_score"] = (_z(agg["mention_rate"]) + _z(agg["trend_score"]) +
                           _z(agg["tiktok_velocity"]) + _z(agg["purchase_intent_pct"]))

    agg["competition_score"] = (_z(agg["sustained_spend"]) + _z(agg["velocity"]))

    agg["gap_score"] = agg["demand_score"] - agg["competition_score"]
    agg = agg.sort_values("gap_score", ascending=False)

    return agg[["product","synonyms","angles","objections","demand_score","competition_score","gap_score"]]
