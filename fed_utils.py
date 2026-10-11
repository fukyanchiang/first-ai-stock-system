import streamlit as st
import pandas as pd
import requests

API_KEY = "9c4a2d02b7abc7f4a36d54ee39a8c716"

@st.cache_data(ttl=3600)
def fetch_fred_series(series_ids, scale=0.01) -> pd.DataFrame:
    """從 FRED API 抓取數據
    scale=0.01：將百萬美元轉換為億美元
    scale=1.0：保持原本數值（例如利率 %）
    """
    if isinstance(series_ids, str):
        series_ids = [series_ids]
        
    for sid in series_ids:
        url = f"https://api.stlouisfed.org/fred/series/observations?series_id={sid}&api_key={API_KEY}&file_type=json"
        try:
            res = requests.get(url, timeout=10).json()
            if "observations" in res and len(res["observations"]) > 0:
                df = pd.DataFrame(res["observations"])[["date", "value"]]
                df["value"] = pd.to_numeric(df["value"], errors="coerce")
                df["value"] = df["value"] * scale
                df["date"] = pd.to_datetime(df["date"])
                df = df.dropna(subset=["value"]).sort_values("date").reset_index(drop=True)
                if not df.empty:
                    return df
        except Exception:
            continue
            
    return pd.DataFrame(columns=["date", "value"])

def get_latest_metrics(df: pd.DataFrame):
    if df.empty or len(df) < 2:
        return 0.0, 0.0
    latest = df["value"].iloc[-1]
    prev = df["value"].iloc[-2]
    wow = latest - prev
    return latest, wow