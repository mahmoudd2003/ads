
from pytrends.request import TrendReq
import pandas as pd

def fetch_trends_scores(keywords, country):
    if not keywords:
        return pd.DataFrame()
    pytrends = TrendReq(hl="ar", tz=180)
    pytrends.build_payload(keywords, timeframe="today 3-m", geo=country)
    df = pytrends.interest_over_time()
    if df.empty:
        return pd.DataFrame()
    df = df.drop(columns=["isPartial"])
    return df.reset_index().melt(id_vars=["date"], var_name="keyword", value_name="trend_score")
