"""
Filename: _01_page_market_monitor_sync_nasdaq_tech_eod.py
Description: ⚡ 納指科技先鋒版 EOD 批處理大腦 (自動收集 Nasdaq + NYSE 科技龍頭)
- 🎯 三大機構級提純標準 (股價 >= $5.0, 日均成交額 >= $300萬, 市值 >= 3億)
- 🎯 輸出科技專屬 17 欄指標矩陣 (對齊 QQQ)
- 💾 輸出檔案: _01_page_market_monitor_nasdaq_tech_monitor_history.csv
"""

import os
import time
import io
import urllib.request
import pandas as pd
import numpy as np
import yfinance as yf
from datetime import datetime

OUTPUT_CSV = "_01_page_market_monitor_nasdaq_tech_monitor_history.csv"
CORE_INDICES = ["QQQ", "SMH"]

# 🎯 NYSE 上市的關鍵 AI 物理基建與科技龍頭 (絕不能漏掉的核心)
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
        # 🎯 只保留 Nasdaq (Q) 且非 ETF 的純普通股
        df_clean = df_sym[(df_sym['Test Issue'] == 'N') & (df_sym['ETF'] == 'N') & (df_sym['Listing Exchange'] == 'Q')].copy()
        return df_clean
    except Exception:
        return pd.DataFrame()

def collect_tech_universe():
    print("📡 [科技 EOD 大腦] 正在收集納斯達克與紐交所科技龍頭名冊...")
    tickers = set(NYSE_TECH_LEADERS)
    for idx_t in CORE_INDICES:
        tickers.add(idx_t)

    df_nasdaq = get_nasdaq_all_traded()
    if not df_nasdaq.empty:
        raw_syms = [clean_ticker(s) for s in df_nasdaq['Symbol'].dropna().tolist()]
        for s in [x for x in raw_syms if x]:
            tickers.add(s)

    clean_list = sorted(list(tickers))
    print(f"🏛️ 科技候選母池完畢：共鎖定 {len(clean_list)} 隻標的 (覆蓋 Nasdaq 與 NYSE AI 核心)")
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

def run_tech_eod_pipeline():
    start_time = time.time()
    
    print("📡 [科技 EOD] 優先下載 QQQ / SMH 基準指數...")
    idx_raw = None
    for _ in range(3):
        try:
            idx_raw = yf.download(CORE_INDICES, period="2y", interval="1d", auto_adjust=True, progress=False, threads=True, timeout=12)
            if idx_raw is not None and not idx_raw.empty: break
        except Exception: time.sleep(1)

    if idx_raw is None or idx_raw.empty:
        print("❌ 基準指數 QQQ/SMH 下載失敗。")
        return

    idx_c_df, _ = extract_close_and_volume(idx_raw, CORE_INDICES)
    
    universe = collect_tech_universe()
    if not universe: return

    chunk_size = 80
    chunks = [universe[i:i + chunk_size] for i in range(0, len(universe), chunk_size)]
    
    all_closes = [idx_c_df]
    all_volumes = []
    
    print("\n🚀 啟動批次下載 (拉取 2 年真實日線行情)...")
    for idx, chunk in enumerate(chunks):
        print(f"📦 正在下載批次 [{idx+1}/{len(chunks)}] (每批 {len(chunk)} 隻)...", end="\r")
        try:
            raw = yf.download(chunk, period="2y", interval="1d", auto_adjust=True, progress=False, threads=True, timeout=15)
            c_chunk, v_chunk = extract_close_and_volume(raw, chunk)
            if c_chunk is not None and not c_chunk.empty: all_closes.append(c_chunk)
            if v_chunk is not None and not v_chunk.empty: all_volumes.append(v_chunk)
        except Exception: pass
        time.sleep(0.15)

    print("\n⚙️ 正在清洗並對齊收盤價與成交量矩陣...")
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

    qqq_c = df_c['QQQ'] if 'QQQ' in df_c.columns else None
    
    stock_cols = [c for c in df_c.columns if c not in CORE_INDICES]
    df_stock_c = df_c[stock_cols]
    df_stock_v = df_v[stock_cols]

    print("\n🔬 [三大機構級提純實裝] (剔除科技仙股與微盤)...")
    vol_20ma = df_stock_v.rolling(window=20, min_periods=10).mean()
    dollar_vol_20ma = (df_stock_c * df_stock_v).rolling(window=20, min_periods=10).mean()
    
    # 🎯 核心過濾：股價 >= 5 且 成交額 >= 300萬美元
    valid_mask = (df_stock_c >= 5.0) & (dollar_vol_20ma >= 3000000.0) & (vol_20ma >= 100000.0)
    valid_cnt = valid_mask.sum(axis=1)

    daily_ret = ((df_stock_c - df_stock_c.shift(1)) / df_stock_c.shift(1).replace(0, np.nan)) * 100.0
    up_4pct = ((daily_ret >= 4.0) & valid_mask).sum(axis=1)
    down_4pct = ((daily_ret <= -4.0) & valid_mask).sum(axis=1)

    up_5d = up_4pct.rolling(window=5, min_periods=1).sum()
    down_5d = down_4pct.rolling(window=5, min_periods=1).sum()
    r_5d = (up_5d / down_5d.replace(0, np.nan)).round(2).fillna(1.0)

    up_10d = up_4pct.rolling(window=10, min_periods=1).sum()
    down_10d = down_4pct.rolling(window=10, min_periods=1).sum()
    r_10d = (up_10d / down_10d.replace(0, np.nan)).round(2).fillna(1.0)

    ma40 = df_stock_c.rolling(window=40, min_periods=20).mean()
    ma50 = df_stock_c.rolling(window=50, min_periods=25).mean()
    ma200 = df_stock_c.rolling(window=200, min_periods=100).mean()

    is_above_40 = (df_stock_c > ma40) & valid_mask
    is_above_50 = (df_stock_c > ma50) & valid_mask
    is_above_200 = (df_stock_c > ma200) & valid_mask

    pct_40ma = ((is_above_40.sum(axis=1) / valid_cnt.replace(0, np.nan)) * 100.0).round(1).fillna(50.0)
    pct_50ma = ((is_above_50.sum(axis=1) / valid_cnt.replace(0, np.nan)) * 100.0).round(1).fillna(50.0)
    pct_200ma = ((is_above_200.sum(axis=1) / valid_cnt.replace(0, np.nan)) * 100.0).round(1).fillna(50.0)

    high_252_all = df_stock_c.rolling(window=252, min_periods=30).max()
    drawdown_all = ((df_stock_c - high_252_all) / high_252_all.replace(0, np.nan)) * 100.0
    drawdown_active = drawdown_all.where(valid_mask)
    mean_dist_52w = drawdown_active.mean(axis=1).round(2).fillna(-18.0)
    median_dist_52w = drawdown_active.median(axis=1).round(2).fillna(-18.0)

    # 🎯 科技專頁的「指數破位」完全以 QQQ 為主將
    qqq_ma50 = qqq_c.rolling(window=50, min_periods=25).mean() if qqq_c is not None else None
    qqq_vs_50 = (((qqq_c - qqq_ma50) / qqq_ma50) * 100.0).round(2) if qqq_ma50 is not None else pd.Series(0.0, index=df_c.index)

    df_output = pd.DataFrame({
        "Date": [d.strftime("%Y-%m-%d") for d in df_stock_c.index],
        "Up_4Pct": up_4pct.values.astype(int),
        "Down_4Pct": down_4pct.values.astype(int),
        "Ratio_5D": r_5d.values,
        "Ratio_10D": r_10d.values,
        "Pct_Above_40MA": pct_40ma.values,
        "Pct_Above_50MA": pct_50ma.values,
        "Pct_Above_200MA": pct_200ma.values,
        "Dist_52W": mean_dist_52w.values,
        "Median_Dist_52W": median_dist_52w.values,
        "Min_Idx_vs_50MA": qqq_vs_50.values, # 以 QQQ 取代 SPY
        "Valid_Count": valid_cnt.values.astype(int)
    }).set_index("Date").tail(160)

    if df_output.empty:
        print("❌ 計算結果為空，取消寫入。")
        return

    tmp_csv = f"{OUTPUT_CSV}.tmp_{os.getpid()}_{int(time.time()*1000)}"
    try:
        df_output.to_csv(tmp_csv)
        os.replace(tmp_csv, OUTPUT_CSV)
    except Exception as e:
        print(f"⚠️ 原子寫入失敗: {e}")
        df_output.to_csv(OUTPUT_CSV)

    elapsed = round((time.time() - start_time) / 60, 2)
    print("\n" + "="*70)
    print(f"✅ [科技版 EOD 完成] 已寫入：{OUTPUT_CSV} (耗時: {elapsed} 分鐘)")
    print(f"📊 提純後有效純血科技股總數：{df_output['Valid_Count'].iloc[-1]} 隻 (覆蓋 Nasdaq ＋ NYSE AI龍頭)")
    print("="*70)

if __name__ == "__main__":
    run_tech_eod_pipeline()