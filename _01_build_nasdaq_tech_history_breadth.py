"""
Filename: _01_build_nasdaq_tech_history_breadth.py
Description: 🏛️ 1,310 隻純血科技股底層市寬矩陣精確構建引擎
- 🎯 回測精確週期: 2004-01-01 至 2026-11-06
- 🎯 三大機構級提純標準: 股價 >= $5.0, 日均成交額 >= $300萬, 滾動成交量過濾
- 🎯 完整計算逐日 Pct_Above_50MA, Pct_Above_200MA, Median_Dist_52W, Down_4Pct, Up_4Pct
- 💾 輸出檔案: _01_nasdaq_tech_breadth_2004_2026.csv
"""

import os
import time
import urllib.request
import pandas as pd
import numpy as np
import yfinance as yf

OUTPUT_CSV = "_01_nasdaq_tech_breadth_2004_2026.csv"
CORE_INDICES = ["QQQ", "SMH"]
START_DATE = "2004-01-01"
END_DATE = "2026-11-07"  # yfinance end 為開區間，設為 11-07 確保完整取到 2026-11-06

# NYSE 上市關鍵 AI 物理基建與科技龍頭
NYSE_TECH_LEADERS = [
    "ORCL", "CRM", "NOW", "SNOW", "IBM", "DELL", "ANET", "APH", "GLW",
    "VRT", "ETN", "NVT", "HUBB", "VST", "GEV", "NRG", "TSM", "ROK", "PATH", "PL"
]

def clean_ticker(s):
    if not isinstance(s, str): return ""
    s = s.strip().upper().replace('.', '-')
    if not s or s == '-' or s.isdigit(): return ""
    if len(s) > 5: return ""
    if len(s) == 5 and s[-1] in ['W', 'R', 'U', 'P', 'Z']: return ""
    parts = s.split('-')
    if len(parts) <= 2 and all(p.isalpha() for p in parts if p):
        return s
    return ""

def get_nasdaq_all_traded():
    """安全獲取 Nasdaq 全市場官方名錄"""
    url = "https://www.nasdaqtrader.com/dynamic/SymDir/nasdaqtraded.txt"
    try:
        req = urllib.request.Request(url, headers={'User-Agent': 'Mozilla/5.0'})
        with urllib.request.urlopen(req, timeout=15) as resp:
            df_sym = pd.read_csv(resp, sep="|")
        df_clean = df_sym[(df_sym['Test Issue'] == 'N') & (df_sym['ETF'] == 'N') & (df_sym['Listing Exchange'] == 'Q')].copy()
        return df_clean
    except Exception as e:
        print(f"⚠️ 無法直接拉取官方名錄: {e}")
        return pd.DataFrame()

def collect_tech_universe():
    print("📡 [1310 科技母池] 正在收集納斯達克與紐交所科技龍頭名冊...")
    tickers = set(NYSE_TECH_LEADERS)
    for idx_t in CORE_INDICES:
        tickers.add(idx_t)

    df_nasdaq = get_nasdaq_all_traded()
    if not df_nasdaq.empty:
        raw_syms = [clean_ticker(s) for s in df_nasdaq['Symbol'].dropna().tolist()]
        for s in [x for x in raw_syms if x]:
            tickers.add(s)

    clean_list = sorted(list(tickers))
    print(f"🏛️ 科技候選母池鎖定：共 {len(clean_list)} 隻標的")
    return clean_list

def extract_close_and_volume(raw, chunk_tickers):
    if raw is None or raw.empty: return None, None
    try:
        if isinstance(raw.columns, pd.MultiIndex):
            lvl0 = [str(c).lower() for c in raw.columns.get_level_values(0)]
            lvl1 = [str(c).lower() for c in raw.columns.get_level_values(1)]
            if 'close' in lvl0:
                return raw['Close'].copy(), (raw['Volume'].copy() if 'Volume' in raw else pd.DataFrame(index=raw.index))
            elif 'close' in lvl1:
                return raw.xs('Close', level=1, axis=1).copy(), (raw.xs('Volume', level=1, axis=1).copy() if 'Volume' in lvl1 else pd.DataFrame(index=raw.index))
        else:
            t = chunk_tickers[0] if len(chunk_tickers) == 1 else 'TICKER'
            if 'Close' in raw.columns:
                return pd.DataFrame({t: raw['Close']}), (pd.DataFrame({t: raw['Volume']}) if 'Volume' in raw.columns else pd.DataFrame(index=raw.index))
        return None, None
    except Exception: return None, None

def build_tech_breadth_exact_dates():
    start_time = time.time()
    print("=" * 80)
    print(f"🚀 啟動 1,310 隻科技股市寬構建：精確區間 2004-01-01 至 2026-11-06")
    print("=" * 80)

    # 1. 基準指數
    print("📡 正在加載基準指數 QQQ / SMH (2004-01-01 至 2026-11-06)...")
    idx_raw = yf.download(CORE_INDICES, start=START_DATE, end=END_DATE, auto_adjust=True, progress=False, threads=True, timeout=25)
    idx_c_df, _ = extract_close_and_volume(idx_raw, CORE_INDICES)
    if idx_c_df is None or idx_c_df.empty:
        print("❌ QQQ/SMH 基準指數下載失敗，終止運行。")
        return

    universe = collect_tech_universe()
    chunk_size = 80
    chunks = [universe[i:i + chunk_size] for i in range(0, len(universe), chunk_size)]

    all_closes = [idx_c_df]
    all_volumes = []

    print(f"\n📦 啟動 17 批次並行下載 (每批 80 隻，預計耗時 2～3 分鐘)...")
    for idx, chunk in enumerate(chunks):
        pct_done = int((idx + 1) / len(chunks) * 100)
        print(f"   [{idx+1}/{len(chunks)}] ({pct_done}%) 下載第 {idx+1} 批次 ({len(chunk)} 隻)...", end="\r")
        try:
            raw = yf.download(chunk, start=START_DATE, end=END_DATE, auto_adjust=True, progress=False, threads=True, timeout=30)
            c_chunk, v_chunk = extract_close_and_volume(raw, chunk)
            if c_chunk is not None and not c_chunk.empty: all_closes.append(c_chunk)
            if v_chunk is not None and not v_chunk.empty: all_volumes.append(v_chunk)
        except Exception as e:
            print(f"\n⚠️ 批次 [{idx+1}] 異常，跳過繼續: {e}")
        time.sleep(0.15)

    print("\n\n⚙️ 正在清洗並對齊數據矩陣...")
    df_c_raw = pd.concat(all_closes, axis=1)
    df_c = df_c_raw.loc[:, ~df_c_raw.columns.duplicated()].dropna(how='all')
    df_v_raw = pd.concat(all_volumes, axis=1)
    df_v = df_v_raw.loc[:, ~df_v_raw.columns.duplicated()].dropna(how='all')

    common_cols = [col for col in df_c.columns if col in df_v.columns]
    df_c = df_c[common_cols]
    df_v = df_v[common_cols]

    if hasattr(df_c.index, 'tz') and df_c.index.tz is not None:
        df_c.index = df_c.index.tz_localize(None).normalize()
        df_v.index = df_v.index.tz_localize(None).normalize()

    # 確保結算邊界精確落在 2026-11-06
    df_c = df_c.loc[(df_c.index >= START_DATE) & (df_c.index <= "2026-11-06")]
    df_v = df_v.loc[(df_v.index >= START_DATE) & (df_v.index <= "2026-11-06")]

    qqq_c = df_c['QQQ'] if 'QQQ' in df_c.columns else None
    stock_cols = [c for c in df_c.columns if c not in CORE_INDICES]
    df_stock_c = df_c[stock_cols]
    df_stock_v = df_v[stock_cols]

    print("🔬 正在執行逐日【三大機構級提純】(成交額>=300萬、股價>=5)...")
    vol_20ma = df_stock_v.rolling(window=20, min_periods=10).mean()
    dollar_vol_20ma = (df_stock_c * df_stock_v).rolling(window=20, min_periods=10).mean()

    valid_mask = (df_stock_c >= 5.0) & (dollar_vol_20ma >= 3000000.0) & (vol_20ma >= 100000.0)
    valid_cnt = valid_mask.sum(axis=1)

    print("📊 正在計算逐日真實市寬指標...")
    daily_ret = ((df_stock_c - df_stock_c.shift(1)) / df_stock_c.shift(1).replace(0, np.nan)) * 100.0
    up_4pct = ((daily_ret >= 4.0) & valid_mask).sum(axis=1)
    down_4pct = ((daily_ret <= -4.0) & valid_mask).sum(axis=1)

    ma50 = df_stock_c.rolling(window=50, min_periods=25).mean()
    ma200 = df_stock_c.rolling(window=200, min_periods=100).mean()

    is_above_50 = (df_stock_c > ma50) & valid_mask
    is_above_200 = (df_stock_c > ma200) & valid_mask

    pct_50ma = ((is_above_50.sum(axis=1) / valid_cnt.replace(0, np.nan)) * 100.0).round(1).fillna(50.0)
    pct_200ma = ((is_above_200.sum(axis=1) / valid_cnt.replace(0, np.nan)) * 100.0).round(1).fillna(50.0)

    high_252 = df_stock_c.rolling(window=252, min_periods=30).max()
    drawdown_all = ((df_stock_c - high_252) / high_252.replace(0, np.nan)) * 100.0
    median_dist_52w = drawdown_all.where(valid_mask).median(axis=1).round(2).fillna(-18.0)

    qqq_ma50 = qqq_c.rolling(window=50, min_periods=25).mean() if qqq_c is not None else None
    qqq_vs_50 = (((qqq_c - qqq_ma50) / qqq_ma50) * 100.0).round(2) if qqq_ma50 is not None else pd.Series(0.0, index=df_c.index)

    df_output = pd.DataFrame({
        "Date": [d.strftime("%Y-%m-%d") for d in df_stock_c.index],
        "QQQ_Close": qqq_c.values if qqq_c is not None else np.nan,
        "Pct_Above_50MA": pct_50ma.values,
        "Pct_Above_200MA": pct_200ma.values,
        "Median_Dist_52W": median_dist_52w.values,
        "Down_4Pct": down_4pct.values.astype(int),
        "Up_4Pct": up_4pct.values.astype(int),
        "Min_Idx_vs_50MA": qqq_vs_50.values,
        "Valid_Count": valid_cnt.values.astype(int)
    }).dropna(subset=["Date"]).set_index("Date")

    df_output.to_csv(OUTPUT_CSV)
    elapsed = round((time.time() - start_time) / 60, 2)
    print("=" * 80)
    print(f"🎉 歷史市寬矩陣構建完成！已寫入：{OUTPUT_CSV}")
    print(f"📈 精確覆蓋區間：{df_output.index.min()} 至 {df_output.index.max()} (共 {len(df_output)} 個交易日)")
    print(f"🔬 總耗時：{elapsed} 分鐘")
    print("=" * 80)

if __name__ == "__main__":
    build_tech_breadth_exact_dates()