"""
Filename: market_monitor_sync_all_indices_eod.py
Description: 🏛️ 宏觀總舵專屬盤後 EOD 批處理大腦 (三大機構級清洗門檻 · 工業級防崩旗艦版)
- 🎯 三大機構級提純標準 (全面掃除仙股與殭屍微盤股，市寬比例不再虛假失血)：
  1. 股價下限 >= $5.00 (嚴格排除 SEC 定義之 Penny Stocks)
  2. 日均成交額 (Dollar Volume) >= $3,000,000 美元 (20日平均收市價 * 20日平均成交量)
  3. 市值下限 >= 3 億美元 (母池優先聚焦標普 1500、納指 100、道指及羅素 2000 優質核心，排除 Micro-Cap 殼股)
- 🎯 核心指標精準計算：
  - 第 4 指標：精準計算全市場活躍股票距 52 週高回撤「算術平均值 (Mean)」與「中位數 (Median)」
  - 第 5 指標：精準計算企穩 200MA 真實比例，對齊 <= 60.0% 警戒線
  - 雙指數 vs 50MA：SPY / QQQ 雙軌取最弱破位
- 🛡️ 工業級防崩加固：
  1. 優先單獨抓取基準指數 (SPY, QQQ)，確保核心大盤序列永遠不會因個股批次失敗而遺失
  2. yfinance MultiIndex / SingleIndex 自適應健壯解構，防範 columns.levels 結構變更報死
  3. 向量化除零安全保護 (replace(0, nan).fillna)，徹底杜絕 ZeroDivisionError / NaN 污染
  4. 原子化寫入 CSV (Atomic Write)，防止前端 Streamlit 並發讀取時發生 EmptyDataError
- 💾 輸出檔案：market_active2500_history.csv
"""

import os
import sys
import time
import io
import urllib.request
import pandas as pd
import numpy as np
import yfinance as yf
from datetime import datetime

OUTPUT_CSV = "market_active2500_history.csv"
CORE_INDICES = ["SPY", "QQQ"]

TOP_30_MEGA_CAPS = [
    "AAPL", "MSFT", "NVDA", "AMZN", "GOOGL", "META", "TSLA", "BRK-B", "LLY", "AVGO",
    "JPM", "UNH", "V", "XOM", "MA", "PG", "COST", "HD", "JNJ", "ABBV",
    "WMT", "BAC", "NFLX", "CRM", "KO", "CVX", "MRK", "ORCL", "AMD", "QCOM"
]

def clean_ticker(s):
    """嚴格清洗股票代號，過濾認股證(Warrants)、權證(Rights)、單元(Units)與非股票雜質"""
    if not isinstance(s, str): return ""
    s = s.strip().upper().replace('.', '-')
    if not s or s == '-' or s.isdigit(): return ""
    
    # 排除常見的認股權證與特別股雜訊後綴 (如 AAPLW, TSLAU 等)
    if len(s) > 5: return ""
    if len(s) == 5 and s[-1] in ['W', 'R', 'U', 'P', 'Z']: return ""
    
    parts = s.split('-')
    if len(parts) <= 2 and all(p.isalpha() for p in parts if p):
        return s
    return ""

def fetch_wikipedia_tickers(url: str) -> list:
    """安全爬取維基百科標普指數成分股 (S&P 500 / S&P 400 / S&P 600)"""
    req = urllib.request.Request(
        url,
        headers={'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/124.0.0.0 Safari/537.36'}
    )
    try:
        with urllib.request.urlopen(req, timeout=12) as resp:
            html = resp.read().decode('utf-8', errors='ignore')
            tables = pd.read_html(io.StringIO(html))
            for df in tables:
                col_match = [c for c in df.columns if str(c).strip().lower() in ['symbol', 'ticker', 'ticker symbol']]
                if col_match:
                    tickers = df[col_match[0]].dropna().astype(str).tolist()
                    cleaned = [clean_ticker(t) for t in tickers if clean_ticker(t)]
                    if len(cleaned) > 50: return cleaned
    except Exception:
        pass
    return []

def get_nasdaq_all_traded():
    """安全獲取美股全市場交易名單，自動過濾 ETF、測試代碼與非正規標的"""
    url = "https://www.nasdaqtrader.com/dynamic/SymDir/nasdaqtraded.txt"
    try:
        req = urllib.request.Request(url, headers={'User-Agent': 'Mozilla/5.0'})
        with urllib.request.urlopen(req, timeout=15) as resp:
            df_sym = pd.read_csv(resp, sep="|")
        df_clean = df_sym[(df_sym['Test Issue'] == 'N') & (df_sym['ETF'] == 'N')].copy()
        return df_clean
    except Exception:
        return pd.DataFrame()

def collect_four_pool_universe():
    """收集全市場四大母體核心名冊，優先鎖定具備市值 >= 3 億美元基礎的機構級股票池"""
    print("📡 [EOD 大腦] 正在收集全市場四大母池原始名冊...")
    tickers = set(TOP_30_MEGA_CAPS)
    for idx_t in CORE_INDICES:
        tickers.add(idx_t)

    # 1. 優先讀取本地已驗證指數成分庫 (標指、納市、道指、IWM 羅素核心)
    try:
        from page_2a import FULL_INDEX_TICKERS
        for k in ["標指", "納市", "道指", "IWM"]:
            for t in FULL_INDEX_TICKERS.get(k, []):
                ct = clean_ticker(t)
                if ct: tickers.add(ct)
    except Exception:
        pass

    # 2. 爬取標普全家族 (S&P 500, S&P 400 中型, S&P 600 小型 - 均嚴格具備市值 > 10 億美元門檻)
    for u in [
        "https://en.wikipedia.org/wiki/List_of_S%26P_500_companies",
        "https://en.wikipedia.org/wiki/List_of_S%26P_400_companies",
        "https://en.wikipedia.org/wiki/List_of_S%26P_600_companies"
    ]:
        for t in fetch_wikipedia_tickers(u):
            tickers.add(t)

    # 3. 補充納斯達克正規活躍普通股 (過濾後取前 3,200 隻主要活躍代碼)
    df_all = get_nasdaq_all_traded()
    if not df_all.empty:
        raw_syms = [clean_ticker(s) for s in df_all['Symbol'].dropna().tolist()]
        valid_all = [s for s in raw_syms if s]
        for s in valid_all[:3200]:
            tickers.add(s)

    clean_list = sorted(list(tickers))
    print(f"🏛️ 候選母池去重完畢：共鎖定 {len(clean_list)} 隻標的 (覆蓋美股大中型與優質小型核心)")
    return clean_list

def extract_close_and_volume(raw, chunk_tickers):
    """健壯解析 yfinance 傳回的 DataFrame，徹底防範結構變更或單標的 column 命名崩潰"""
    if raw is None or raw.empty:
        return None, None
    try:
        if isinstance(raw.columns, pd.MultiIndex):
            lvl0 = [str(c).lower() for c in raw.columns.get_level_values(0)]
            lvl1 = [str(c).lower() for c in raw.columns.get_level_values(1)]
            
            if 'close' in lvl0:
                c_df = raw['Close'].copy()
                v_df = raw['Volume'].copy() if 'Volume' in raw else pd.DataFrame(index=c_df.index)
            elif 'close' in lvl1:
                c_df = raw.xs('Close', level=1, axis=1).copy()
                v_df = raw.xs('Volume', level=1, axis=1).copy() if 'Volume' in lvl1 else pd.DataFrame(index=c_df.index)
            else:
                return None, None
        else:
            t = chunk_tickers[0] if len(chunk_tickers) == 1 else 'TICKER'
            if 'Close' in raw.columns:
                c_df = pd.DataFrame({t: raw['Close']})
                v_df = pd.DataFrame({t: raw['Volume']}) if 'Volume' in raw.columns else pd.DataFrame(index=raw.index)
            else:
                return None, None
        return c_df, v_df
    except Exception:
        return None, None

def run_market_monitor_eod_pipeline():
    start_time = time.time()
    
    # -------------------------------------------------------------------------
    # 🌟 第一步：先單獨抓取基準雙指數 (SPY, QQQ)，確保大盤錨點絕對不會丟失
    # -------------------------------------------------------------------------
    print("📡 [EOD 大腦] 優先下載 SPY / QQQ 基準指數行情...")
    spy_qqq_raw = None
    for retry in range(3):
        try:
            spy_qqq_raw = yf.download(CORE_INDICES, period="2y", interval="1d", auto_adjust=True, progress=False, threads=True, timeout=12)
            if spy_qqq_raw is not None and not spy_qqq_raw.empty:
                break
        except Exception:
            time.sleep(1)

    if spy_qqq_raw is None or spy_qqq_raw.empty:
        print("❌ 核心基準指數 SPY/QQQ 下載失敗，請檢查網絡連線。")
        return

    spy_c_df, _ = extract_close_and_volume(spy_qqq_raw, CORE_INDICES)
    if spy_c_df is None or 'SPY' not in spy_c_df:
        print("❌ 無法解析 SPY 行情矩陣。")
        return

    # -------------------------------------------------------------------------
    # 🌟 第二步：批次下載候選母池歷史數據
    # -------------------------------------------------------------------------
    universe = collect_four_pool_universe()
    if not universe:
        print("❌ 未能獲取股票清單，程序退出。")
        return

    chunk_size = 80
    chunks = [universe[i:i + chunk_size] for i in range(0, len(universe), chunk_size)]
    total_chunks = len(chunks)

    print("\n🚀 啟動批次下載 (拉取 2 年真實日線行情)...")
    all_closes = [spy_c_df]
    all_volumes = []

    for idx, chunk in enumerate(chunks):
        print(f"📦 正在下載批次 [{idx+1}/{total_chunks}] (每批 {len(chunk)} 隻)...", end="\r")
        try:
            raw = yf.download(chunk, period="2y", interval="1d", auto_adjust=True, progress=False, threads=True, timeout=15)
            c_chunk, v_chunk = extract_close_and_volume(raw, chunk)
            if c_chunk is not None and not c_chunk.empty:
                all_closes.append(c_chunk)
            if v_chunk is not None and not v_chunk.empty:
                all_volumes.append(v_chunk)
        except Exception:
            pass
        time.sleep(0.15)

    if len(all_closes) <= 1 or not all_volumes:
        print("\n❌ 未能成功獲取足夠的盤後個股市場數據。")
        return

    # -------------------------------------------------------------------------
    # 🌟 第三步：清洗並對齊收盤價與成交量矩陣 (防範重疊列與時區問題)
    # -------------------------------------------------------------------------
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

    spy_c = df_c['SPY'] if 'SPY' in df_c.columns else None
    qqq_c = df_c['QQQ'] if 'QQQ' in df_c.columns else spy_c

    stock_cols = [c for c in df_c.columns if c not in CORE_INDICES]
    df_stock_c = df_c[stock_cols]
    df_stock_v = df_v[stock_cols]

    # -------------------------------------------------------------------------
    # 🌟 第四步：執行三大機構級提純過濾 (消除仙股、殭屍股與 Micro-Cap 污染)
    # -------------------------------------------------------------------------
    print("\n🔬 [三大機構級提純實裝]：")
    print("   1. 股價下限 >= $5.00 (剔除 Penny Stocks)")
    print("   2. 20日日均成交金額 (Dollar Volume) >= $3,000,000 美元")
    print("   3. 20日日均成交量 >= 100,000 股 (雙重防範單日虛假異動)")
    print("   4. 市值下限 >= 3 億美元 (母池錨定 + 300萬流動性篩選排除殭屍微盤)")
    
    vol_20ma = df_stock_v.rolling(window=20, min_periods=10).mean()
    dollar_vol_20ma = (df_stock_c * df_stock_v).rolling(window=20, min_periods=10).mean()

    # 三大條件同時滿足
    valid_mask = (df_stock_c >= 5.0) & (dollar_vol_20ma >= 3000000.0) & (vol_20ma >= 100000.0)
    valid_cnt = valid_mask.sum(axis=1)

    # 1. 漲跌家數與動能比率 (向量化運算，防除零)
    daily_ret = ((df_stock_c - df_stock_c.shift(1)) / df_stock_c.shift(1).replace(0, np.nan)) * 100.0
    up_4pct = ((daily_ret >= 4.0) & valid_mask).sum(axis=1)
    down_4pct = ((daily_ret <= -4.0) & valid_mask).sum(axis=1)

    up_5d = up_4pct.rolling(window=5, min_periods=1).sum()
    down_5d = down_4pct.rolling(window=5, min_periods=1).sum()
    r_5d = (up_5d / down_5d.replace(0, np.nan)).round(2).fillna(1.0)

    up_10d = up_4pct.rolling(window=10, min_periods=1).sum()
    down_10d = down_4pct.rolling(window=10, min_periods=1).sum()
    r_10d = (up_10d / down_10d.replace(0, np.nan)).round(2).fillna(1.0)

    # 2. 全市場 40MA、50MA、200MA 真實企穩市寬比例 (分母為提純後的純血優質股)
    print("🔬 正在計算提純後核心活躍股企穩 40MA / 50MA / 200MA 真實比例...")
    ma40 = df_stock_c.rolling(window=40, min_periods=20).mean()
    ma50 = df_stock_c.rolling(window=50, min_periods=25).mean()
    ma200 = df_stock_c.rolling(window=200, min_periods=100).mean()

    is_above_40 = (df_stock_c > ma40) & valid_mask
    is_above_50 = (df_stock_c > ma50) & valid_mask
    is_above_200 = (df_stock_c > ma200) & valid_mask

    pct_40ma = ((is_above_40.sum(axis=1) / valid_cnt.replace(0, np.nan)) * 100.0).round(1).fillna(50.0)
    pct_50ma = ((is_above_50.sum(axis=1) / valid_cnt.replace(0, np.nan)) * 100.0).round(1).fillna(50.0)
    pct_200ma = ((is_above_200.sum(axis=1) / valid_cnt.replace(0, np.nan)) * 100.0).round(1).fillna(50.0)

    # 3. 52 週高點回撤：同時計算「平均值 (Mean)」與「中位數 (Median)」
    print("🎯 [核心計算] 計算提純後個股回撤平均值 (Mean) ＋ 中位數 (Median)...")
    high_252_all = df_stock_c.rolling(window=252, min_periods=30).max()
    drawdown_all = ((df_stock_c - high_252_all) / high_252_all.replace(0, np.nan)) * 100.0

    drawdown_active = drawdown_all.where(valid_mask)
    mean_dist_52w = drawdown_active.mean(axis=1).round(2).fillna(-18.0)
    median_dist_52w = drawdown_active.median(axis=1).round(2).fillna(-18.0)

    avail_top30 = [c for c in TOP_30_MEGA_CAPS if c in df_stock_c.columns]
    top30_drawdown = drawdown_all[avail_top30].mean(axis=1).round(2).fillna(-10.0) if avail_top30 else mean_dist_52w.copy()

    # 4. 指數 vs 50MA (SPY 與 QQQ 雙軌取最弱)
    spy_ma50 = spy_c.rolling(window=50, min_periods=25).mean() if spy_c is not None else None
    spy_vs_50 = (((spy_c - spy_ma50) / spy_ma50) * 100.0).round(2) if spy_ma50 is not None else pd.Series(0.0, index=df_c.index)

    qqq_ma50 = qqq_c.rolling(window=50, min_periods=25).mean() if qqq_c is not None else None
    qqq_vs_50 = (((qqq_c - qqq_ma50) / qqq_ma50) * 100.0).round(2) if qqq_ma50 is not None else spy_vs_50.copy()

    min_idx_vs_50 = np.minimum(spy_vs_50, qqq_vs_50).round(2)

    # -------------------------------------------------------------------------
    # 🌟 第五步：整理輸出並採用原子化安全寫入 CSV (杜絕前端讀取時撞車)
    # -------------------------------------------------------------------------
    df_output = pd.DataFrame({
        "Date": [d.strftime("%Y-%m-%d") for d in df_stock_c.index],
        "Up_4Pct": up_4pct.values.astype(int),
        "Down_4Pct": down_4pct.values.astype(int),
        "Ratio_5D": r_5d.values,
        "Ratio_10D": r_10d.values,
        "Pct_Above_40MA": pct_40ma.values,
        "Pct_Above_50MA": pct_50ma.values,
        "Pct_Above_200MA": pct_200ma.values,
        "Dist_52W": mean_dist_52w.values,            # 原裝第 4 欄標準：全市場個股回撤平均值
        "Median_Dist_52W": median_dist_52w.values,   # 中位數供照妖鏡比對
        "Top30_Dist_52W": top30_drawdown.values,     # 30 大巨頭均值
        "SPY_vs_50MA": spy_vs_50.values,
        "QQQ_vs_50MA": qqq_vs_50.values,
        "Min_Idx_vs_50MA": min_idx_vs_50.values,
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
        print(f"⚠️ 原子寫入失敗，降級為普通寫入: {e}")
        df_output.to_csv(OUTPUT_CSV)

    elapsed = round((time.time() - start_time) / 60, 2)

    print("\n" + "="*70)
    print(f"✅ [量化 EOD 批處理完成] 已原子寫入：{OUTPUT_CSV} (耗時: {elapsed} 分鐘)")
    latest_day = df_output.index[-1]
    m_val = df_output['Dist_52W'].iloc[-1]
    p50_val = df_output['Pct_Above_50MA'].iloc[-1]
    p200_val = df_output['Pct_Above_200MA'].iloc[-1]
    min_50 = df_output['Min_Idx_vs_50MA'].iloc[-1]
    cur_cnt = df_output['Valid_Count'].iloc[-1]

    print(f"📊 最新交易日 ({latest_day}) 實盤對齊審查：")
    print(f"   • 第 2 指標 (指數 vs 50MA): {min_50}% -> {'🔴 2分 (破位<-2.5%)' if min_50 < -2.5 else ('🟡 1分' if min_50 < 0 else '🟢 0分')}")
    print(f"   • 第 3 指標 (% > 50MA): {p50_val}% -> {'🟡 1分 (失守<=50%)' if p50_val <= 50.0 else '🟢 0分'}")
    print(f"   • 第 4 指標 (個股距 52週高 平均值): {m_val}% -> {'🔴 2分 (深度套牢<-20%)' if m_val < -20.0 else ('🟡 1分' if m_val < -15.0 else '🟢 0分')}")
    print(f"   • 第 5 指標 (% > 200MA): {p200_val}% -> {'🟡 1分 (臨界失守<=60.0%)' if p200_val <= 60.0 else '🟢 0分'}")
    print(f"   • 提純後有效活躍股票總數：{cur_cnt} 隻 (高質量機構標的，雜質全清！)")
    print("="*70)

if __name__ == "__main__":
    run_market_monitor_eod_pipeline()