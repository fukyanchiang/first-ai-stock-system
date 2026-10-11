import streamlit as st
import yfinance as yf
import pandas as pd
import numpy as np
import plotly.graph_objects as go
from plotly.subplots import make_subplots
import time
from datetime import datetime

# =========================================================
# 🛡️ 戰略盾牌：多層級字典安全防爆取值函數
# =========================================================
def get_safe_dict_val(d, k1, k2):
    try:
        val = d.get(k1, {}).get(k2, 0.0)
        return float(val)
    except Exception:
        return 0.0

def _extract_close_series_single(raw_df, ticker):
    try:
        if raw_df is None or raw_df.empty: return pd.Series(dtype=float)
        if isinstance(raw_df.columns, pd.MultiIndex):
            if ticker in raw_df.columns.get_level_values(0):
                if "Close" in raw_df[ticker].columns: return raw_df[ticker]["Close"].dropna()
        elif "Close" in raw_df.columns: return raw_df["Close"].dropna()
    except: pass
    return pd.Series(dtype=float)

# ===================================================
# 🗄️ 戰略核心：港股大板塊精銳部隊 (HK Stock Map)
# ===================================================
TOP_N_LEADERS = 30

HK_STOCK_MAP = {
    "1. ATMXJ 互聯網巨頭": ["0700.HK", "9988.HK", "3690.HK", "9999.HK", "1024.HK", "09888.HK", "01810.HK"],
    "2. AI 大模型與 SaaS 雲端": ["0020.HK", "1357.HK", "3896.HK", "6682.HK", "2158.HK", "2013.HK", "9698.HK"],
    "3. 半導體與 AI 算力硬體": ["0981.HK", "1347.HK", "1385.HK", "2878.HK"],
    "4. 智能駕駛與汽車晶片": ["9660.HK", "2498.HK", "1274.HK", "9863.HK", "9868.HK", "9866.HK", "2015.HK"],
    "5. 創新藥與生物科技 (High Beta)": ["9926.HK", "1801.HK", "6160.HK", "2268.HK", "2367.HK", "1093.HK", "2269.HK"],
    "6. IP 潮玩與數字娛樂新消費": ["9992.HK", "2400.HK", "1896.HK", "6181.HK", "9899.HK"],
    "7. 新能源汽車與產業鏈": ["1211.HK", "2238.HK", "0175.HK", "2333.HK", "1114.HK"],
    "8. 國企三大石油石化": ["0883.HK", "0857.HK", "0386.HK"],
    "9. 國企三大電訊營運商": ["0941.HK", "0728.HK", "0762.HK"],
    "10. 國企四大商業銀行": ["0939.HK", "1398.HK", "3988.HK", "1288.HK", "3328.HK", "1658.HK"],
    "11. 招商系與綜合金融": ["3968.HK", "2318.HK", "2601.HK", "1339.HK", "2328.HK"],
    "12. 國際金融與保險巨頭": ["0005.HK", "1299.HK", "0011.HK", "2888.HK"],
    "13. 港股交易所與證券": ["0388.HK", "6030.HK", "3908.HK", "6837.HK"],
    "14. 澳門博彩娛樂": ["0027.HK", "1928.HK", "0200.HK", "2282.HK", "0880.HK", "1128.HK"],
    "15. 體育用品與服飾龍頭": ["2331.HK", "2020.HK", "1368.HK", "6110.HK"],
    "16. 核心餐飲與食品飲料": ["9633.HK", "0291.HK", "6862.HK", "9922.HK", "0322.HK", "0220.HK"],
    "17. 家電與消費電子": ["0669.HK", "0371.HK", "0285.HK", "1070.HK"],
    "18. 光伏與清潔能源": ["3800.HK", "0968.HK", "1772.HK", "0686.HK"],
    "19. 火力與風光電力": ["0836.HK", "0902.HK", "2380.HK", "0916.HK", "1816.HK"],
    "20. 煤炭與傳統能源": ["1088.HK", "1898.HK", "1171.HK"],
    "21. 紫金與貴金屬礦業": ["2899.HK", "1818.HK", "0358.HK", "1787.HK"],
    "22. 有色金屬與鋁業": ["2600.HK", "1378.HK", "3993.HK"],
    "23. 航運物流與港口": ["1919.HK", "0144.HK", "1199.HK", "1308.HK", "0525.HK", "0576.HK", "0107.HK"],
    "24. 央企基建與工程裝備": ["0390.HK", "1186.HK", "1800.HK", "1766.HK", "3311.HK", "0914.HK"],
    "25. 香港本地地產巨頭": ["0016.HK", "0012.HK", "0101.HK", "0017.HK", "1972.HK", "0019.HK"],
    "26. 中資頭部房企": ["1109.HK", "0688.HK", "0960.HK", "1270.HK"],
    "27. 物業管理金牛": ["6098.HK", "1209.HK", "2669.HK", "3319.HK"],
    "28. 香港本地公用事業與粵海": ["0002.HK", "0003.HK", "0006.HK", "1038.HK", "0270.HK", "1193.HK"],
    "29. 房託基金 REITs": ["0823.HK", "0405.HK", "0778.HK"],
    "30. 醫療器械與 CXO": ["2269.HK", "3759.HK", "2359.HK", "1813.HK"]
}

# 5 大特權標竿成份股 MAP
HK_ETF_COMPONENTS_MAP = {
    "🔵 [藍籌] 盈富基金 (2800.HK)": ["0700.HK", "9988.HK", "3690.HK", "0005.HK", "1299.HK", "0939.HK", "1398.HK", "3988.HK", "0388.HK", "1211.HK", "0941.HK", "2318.HK", "1810.HK", "6690.HK", "0291.HK", "2020.HK", "2331.HK", "0016.HK", "0002.HK", "0883.HK", "0857.HK", "0386.HK", "1088.HK", "1928.HK", "0027.HK", "1093.HK", "2269.HK", "9633.HK", "0288.HK", "1109.HK"],
    "🇨🇳 [國企] 恒生國企 (2828.HK)": ["0700.HK", "9988.HK", "3690.HK", "0939.HK", "1398.HK", "3988.HK", "0941.HK", "1211.HK", "2318.HK", "0883.HK", "0857.HK", "0386.HK", "1088.HK", "1810.HK", "9999.HK", "1024.HK", "09888.HK", "3968.HK", "1288.HK", "3328.HK", "1109.HK", "0688.HK", "2020.HK", "2331.HK", "1093.HK", "0291.HK", "1919.HK", "2600.HK", "2899.HK"],
    "🚀 [科技] 恒生科技 (3033.HK)": ["0700.HK", "9988.HK", "3690.HK", "1810.HK", "9999.HK", "1024.HK", "09888.HK", "0981.HK", "2015.HK", "9868.HK", "9866.HK", "0241.HK", "0268.HK", "0788.HK", "1347.HK", "0285.HK", "0522.HK", "3888.HK", "2382.HK", "0020.HK", "1357.HK", "6690.HK", "1833.HK", "6060.HK", "0992.HK", "1772.HK", "3896.HK", "0772.HK", "9618.HK"],
    "🛡️ [低波高息] 央企與公用金牛 (3437.HK/3110.HK)": [
        "0883.HK", "0857.HK", "0386.HK", "0941.HK", "0728.HK", "0762.HK", 
        "0939.HK", "1398.HK", "3988.HK", "1288.HK", "3328.HK", "2388.HK", 
        "1088.HK", "1919.HK", "0002.HK", "0003.HK", "0006.HK", "1038.HK", 
        "0823.HK", "0576.HK", "0107.HK", "0144.HK", "1199.HK", "0270.HK", 
        "0836.HK", "1193.HK", "0371.HK", "2328.HK", "1339.HK", "0998.HK", 
        "1658.HK", "1898.HK", "1171.HK", "0322.HK", "0220.HK", "0019.HK", 
        "0291.HK", "0390.HK", "1186.HK", "0914.HK"
    ],
    "🦐 [新銳] 中小型股與 AI 科技": ["0020.HK", "1357.HK", "3896.HK", "6682.HK", "2158.HK", "2013.HK", "9698.HK", "0981.HK", "1347.HK", "1385.HK", "2878.HK", "9660.HK", "2498.HK", "1274.HK", "9863.HK", "9868.HK", "9866.HK", "2015.HK", "9926.HK", "1801.HK", "6160.HK", "2268.HK", "2367.HK", "9992.HK", "2400.HK", "1896.HK", "6181.HK", "9899.HK", "0175.HK", "2238.HK", "2333.HK", "0669.HK", "0371.HK", "1070.HK", "3800.HK", "0968.HK", "0836.HK", "2380.HK", "1898.HK", "1171.HK", "1818.HK", "0358.HK", "1378.HK", "3993.HK", "1308.HK", "3311.HK", "1209.HK", "2669.HK", "3319.HK", "3759.HK", "2359.HK"]
}

FULL_HK_STOCK_MAP = {**HK_ETF_COMPONENTS_MAP, **HK_STOCK_MAP}

# =========================================================
# ⚙️ 高階矩陣運算引擎 (港股專用，防爆運算)
# =========================================================
@st.cache_data(ttl=43200, show_spinner=False)
def fetch_full_dashboard_data_hk():
    special_etfs = {
        "🔵 港股藍籌核心 (2800.HK)": HK_ETF_COMPONENTS_MAP["🔵 [藍籌] 盈富基金 (2800.HK)"],
        "🇨🇳 中資國企骨幹 (2828.HK)": HK_ETF_COMPONENTS_MAP["🇨🇳 [國企] 恒生國企 (2828.HK)"],
        "🚀 科技狂牛巨頭 (3033.HK)": HK_ETF_COMPONENTS_MAP["🚀 [科技] 恒生科技 (3033.HK)"],
        "🛡️ 港股高息低波盾牌 (3437.HK)": HK_ETF_COMPONENTS_MAP["🛡️ [低波高息] 央企與公用金牛 (3437.HK/3110.HK)"],
        "🦐 中小型股與 AI 科技新銳": HK_ETF_COMPONENTS_MAP["🦐 [新銳] 中小型股與 AI 科技"]
    }
    
    breadth_results = {}
    current_day_data = {}
    price_results = {}

    etf_tickers = ["2800.HK", "2828.HK", "3033.HK", "3437.HK", "3110.HK"]
    try:
        raw_etf = yf.download(etf_tickers, period="1y", auto_adjust=True, progress=False, group_by="ticker")
    except Exception:
        raw_etf = pd.DataFrame()

    for name, tickers in special_etfs.items():
        try:
            raw_comp = yf.download(tickers, period="1y", auto_adjust=True, progress=False)
            if raw_comp is None or raw_comp.empty:
                raise ValueError(f"{name} 下載的資料為空")

            if "Close" in raw_comp: close_prices = raw_comp["Close"]
            else: close_prices = raw_comp
            
            if not close_prices.empty and isinstance(close_prices.index, pd.DatetimeIndex):
                str_idx = pd.Series(close_prices.index.astype(str))
                valid_mask = str_idx.str.startswith('20').values
                close_prices = close_prices.iloc[valid_mask]
                close_prices.index = pd.to_datetime(close_prices.index).tz_localize(None).normalize()
            
            total_b5 = pd.Series(0, index=close_prices.index)
            total_b20 = pd.Series(0, index=close_prices.index)
            total_b50 = pd.Series(0, index=close_prices.index)
            total_b100 = pd.Series(0, index=close_prices.index)
            total_b200 = pd.Series(0, index=close_prices.index)
            valid_counts = pd.Series(0, index=close_prices.index)

            for ticker in close_prices.columns:
                series = close_prices[ticker].dropna()
                if len(series) >= 120:
                    ma5 = series.rolling(5).mean()
                    ma20 = series.rolling(20).mean()
                    ma50 = series.rolling(50).mean()
                    ma100 = series.rolling(100).mean()
                    ma200 = series.rolling(200).mean()

                    total_b5 = total_b5.add((series > ma5).astype(int), fill_value=0)
                    total_b20 = total_b20.add((series > ma20).astype(int), fill_value=0)
                    total_b50 = total_b50.add((series > ma50).astype(int), fill_value=0)
                    total_b100 = total_b100.add((series > ma100).astype(int), fill_value=0)
                    total_b200 = total_b200.add((series > ma200).astype(int), fill_value=0)
                    valid_counts = valid_counts.add(pd.Series(1, index=series.index), fill_value=0)
            
            df_b = pd.DataFrame({
                "Breadth_MA5": (total_b5 / valid_counts * 100).fillna(0),
                "Breadth_MA20": (total_b20 / valid_counts * 100).fillna(0),
                "Breadth_MA50": (total_b50 / valid_counts * 100).fillna(0),
                "Breadth_MA100": (total_b100 / valid_counts * 100).fillna(0),
                "Breadth_MA200": (total_b200 / valid_counts * 100).fillna(0)
            })

            try: b5_val = float(df_b["Breadth_MA5"].iloc[-1])
            except: b5_val = 0.0
            try: b20_val = float(df_b["Breadth_MA20"].iloc[-1])
            except: b20_val = 0.0
            try: b50_val = float(df_b["Breadth_MA50"].iloc[-1])
            except: b50_val = 0.0
            try: b200_val = float(df_b["Breadth_MA200"].iloc[-1])
            except: b200_val = 0.0

            current_day_data[name] = {
                "MA5_Pct": b5_val, "MA20_Pct": b20_val,
                "MA50_Pct": b50_val, "MA200_Pct": b200_val
            }
            breadth_results[name] = df_b.tail(60)

        except Exception as e:
            breadth_results[name] = pd.DataFrame()
            current_day_data[name] = {"MA5_Pct":0.0, "MA20_Pct":0.0, "MA50_Pct":0.0, "MA200_Pct":0.0}

        # 抓取單一 ETF
        ticker_symbol = "3437.HK" if "3437" in name or "低波" in name else (
            "2800.HK" if "2800" in name else (
                "2828.HK" if "2828" in name else (
                    "3033.HK" if "3033" in name else "3033.HK"
                )
            )
        )
        df_p = pd.DataFrame()
        if not raw_etf.empty and ticker_symbol in raw_etf.columns.get_level_values(0):
            df_p = raw_etf[ticker_symbol].copy().dropna(subset=["Close"])
            if not df_p.empty and isinstance(df_p.index, pd.DatetimeIndex):
                str_idx = pd.Series(df_p.index.astype(str))
                valid_mask = str_idx.str.startswith('20').values
                df_p = df_p.iloc[valid_mask]
                df_p.index = pd.to_datetime(df_p.index).tz_localize(None).normalize()
            
        if not breadth_results.get(name, pd.DataFrame()).empty and not df_p.empty:
            df_b = breadth_results[name]
            union_dates = df_p.index.intersection(df_b.index).sort_values()
            
            if not union_dates.empty:
                df_p_aligned = df_p.reindex(union_dates).ffill().fillna(0)
                df_b_aligned = df_b.reindex(union_dates).ffill().fillna(0)
                
                if len(df_p_aligned) == len(df_b_aligned) and len(df_p_aligned) > 0:
                    price_results[name] = df_p_aligned.tail(60)
                    breadth_results[name] = df_b_aligned.tail(60)
                else:
                    price_results[name] = pd.DataFrame()
                    breadth_results[name] = pd.DataFrame()
            else:
                price_results[name] = pd.DataFrame()
                breadth_results[name] = pd.DataFrame()
        else:
            price_results[name] = pd.DataFrame()
            breadth_results[name] = pd.DataFrame()

    return breadth_results, current_day_data, price_results

@st.cache_data(ttl=43200, show_spinner=False)
def fetch_traditional_breadth_hk():
    all_sectors = list(HK_STOCK_MAP.keys())
    results_dict_list = []
    total_ma5, total_ma20, total_ma50, total_ma200, total_valid = 0, 0, 0, 0, 0

    for sector_name in all_sectors:
        constituents = HK_STOCK_MAP.get(sector_name, [])[:TOP_N_LEADERS]
        sec_ma5, sec_ma20, sec_ma50, sec_ma200, sec_valid = 0, 0, 0, 0, 0
        try:
            if constituents:
                raw = yf.download(constituents, period="250d", auto_adjust=True, progress=False, threads=False, group_by="ticker")
                for sym in constituents:
                    close_series = _extract_close_series_single(raw, sym)
                    if not close_series.empty and len(close_series) >= 120:
                        curr_p = float(close_series.iloc[-1])
                        if curr_p > float(close_series.rolling(5).mean().iloc[-1]): sec_ma5 += 1
                        if curr_p > float(close_series.rolling(20).mean().iloc[-1]): sec_ma20 += 1
                        if len(close_series) >= 50 and curr_p > float(close_series.rolling(50).mean().iloc[-1]): sec_ma50 += 1
                        if len(close_series) >= 200 and curr_p > float(close_series.rolling(200).mean().iloc[-1]): sec_ma200 += 1
                        sec_valid += 1
        except: pass

        if sec_valid > 0:
            results_dict_list.append({
                "板塊": sector_name, "MA5_Pct": (sec_ma5 / sec_valid * 100.0), "MA20_Pct": (sec_ma20 / sec_valid * 100.0),
                "MA50_Pct": (sec_ma50 / sec_valid * 100.0), "MA200_Pct": (sec_ma200 / sec_valid * 100.0), "sort_order": 999
            })
            total_ma5 += sec_ma5; total_ma20 += sec_ma20; total_ma50 += sec_ma50; total_ma200 += sec_ma200; total_valid += sec_valid
        time.sleep(0.01)

    top_banners = {
        "MA5": (total_ma5 / total_valid * 100.0) if total_valid > 0 else 0.0,
        "MA20": (total_ma20 / total_valid * 100.0) if total_valid > 0 else 0.0,
        "MA50": (total_ma50 / total_valid * 100.0) if total_valid > 0 else 0.0,
        "MA200": (total_ma200 / total_valid * 100.0) if total_valid > 0 else 0.0
    }
    return pd.DataFrame(results_dict_list), top_banners

# =========================================================
# 🔴 主頁面渲染中心 (港股版)
# =========================================================
def render_page_2bb_hk():
    st.markdown("<h1 style='color:#00ff88; font-size:46px; font-family:Arial Black;'>🇭🇰 艙房 2bb-HK：個股版塊拔河熱力圖 (港股總攻版)</h1>", unsafe_allow_html=True)
    st.markdown("<hr style='border:3px solid #00ff88; margin-bottom:20px;'>", unsafe_allow_html=True)

    st.markdown("### ⏱️ 選擇港股短期市寬觀測雷達範圍")
    short_term_mode = st.radio(
        "切換短線範圍（圖表將連動切換 5天 或 20天 短期市寬線）：",
        ["🟢 顯示 5天短期線 + (50/100/200)", "🟢 顯示 20天短期線 + (50/100/200)"],
        horizontal=True
    )
    use_ma5 = "5天" in short_term_mode

    if st.button("🔄 火力全開：啟動港股矩陣運算清算 (約需十幾秒)"):
        st.cache_data.clear()
        st.success("💥 快取已強制融冰！正在重新清算港股大市...")

    df_rs = pd.DataFrame()
    top_banners = {}

    with st.spinner("📡 正在執行港股高階矩陣歷史運算 (範圍: 60日)..."):
        try:
            breadth_results, current_day_data, price_results = fetch_full_dashboard_data_hk()
            df_rs, top_banners = fetch_traditional_breadth_hk()
        except Exception as e:
            st.error(f"數據讀取異常，請點擊上方「火力全開」。錯誤訊息: {e}")
            return
            
    short_col_name = "MA5_Pct" if use_ma5 else "MA20_Pct"
    short_col_hist = "Breadth_MA5" if use_ma5 else "Breadth_MA20"
    short_banner_val = top_banners.get("MA5", 0.0) if use_ma5 else top_banners.get("MA20", 0.0)
    short_legend_label = "🟢 MA5 短期爆發" if use_ma5 else "🟢 MA20 短期健康"

    # =========================================================
    # 🎯 置頂 6 行港股戰略儀表板
    # =========================================================
    st.markdown("<h3 style='color:#ffaa00; margin-top:10px; margin-bottom:15px;'>📊 戰略靈魂：港股 6 大維度市寬全景雷達</h3>", unsafe_allow_html=True)
    
    st.markdown(f'''
    <div style="background-color:rgba(0,0,0,0.05); padding:12px 15px; border-radius:8px; margin-bottom:12px; border-left:8px solid #000000; display:flex; justify-content:space-between; align-items:center;">
        <div style="color:#ffffff; font-size:19px; font-weight:900; width:30%;">🎯 港股傳統板塊均值 (扣除特權標竿)</div>
        <div style="color:#008844; font-size:18px; font-weight:bold; width:23%; text-align:center;">{short_legend_label}: {short_banner_val:.1f}%</div>
        <div style="color:#cc9900; font-size:18px; font-weight:bold; width:23%; text-align:center;">🟡 MA50: {top_banners.get("MA50", 0.0):.1f}%</div>
        <div style="color:#cc1111; font-size:18px; font-weight:bold; width:23%; text-align:center;">🔴 MA200: {top_banners.get("MA200", 0.0):.1f}%</div>
    </div>
    ''', unsafe_allow_html=True)

    rows_config = [
        ("🔵 港股藍籌核心 (2800.HK)", "#ffffff", "🔵 港股藍籌核心 (2800.HK)"),
        ("🇨🇳 中資國企骨幹 (2828.HK)", "#ffffff", "🇨🇳 中資國企骨幹 (2828.HK)"),
        ("🚀 科技狂牛巨頭 (3033.HK)", "#ffffff", "🚀 科技狂牛巨頭 (3033.HK)"),
        ("🛡️️ 港股高息低波盾牌 (3437.HK)", "#ffffff", "🛡️ 港股高息低波盾牌 (3437.HK)"),
        ("🦐 中小型股與 AI 科技新銳", "#ffffff", "🦐 中小型股與 AI 科技新銳")
    ]

    for label, color, key in rows_config:
        try:
            v_short = float(current_day_data.get(key, {}).get(short_col_name, 0.0))
            v_50 = float(current_day_data.get(key, {}).get("MA50_Pct", 0.0))
            v_200 = float(current_day_data.get(key, {}).get("MA200_Pct", 0.0))
        except:
            v_short, v_50, v_200 = 0.0, 0.0, 0.0
            
        border_colors = {
            "🔵 港股藍籌核心 (2800.HK)": "#00f2ff", 
            "🇨🇳 中資國企骨幹 (2828.HK)": "#a200ff", 
            "🚀 科技狂牛巨頭 (3033.HK)": "#ff00ff", 
            "🛡️ 港股高息低波盾牌 (3437.HK)": "#00ff88", 
            "🦐 中小型股與 AI 科技新銳": "#ff3333"
        }
        b_color = border_colors.get(label, "#ffffff")

        st.markdown(f'''
        <div style="background-color:#1e212b; padding:10px 15px; border-radius:8px; margin-bottom:8px; border-left:6px solid {b_color}; display:flex; justify-content:space-between; align-items:center;">
            <div style="color:{color}; font-size:18px; font-weight:bold; width:30%;">{label}</div>
            <div style="color:#00ff88; font-size:18px; font-weight:bold; width:23%; text-align:center;">{short_legend_label}: {v_short:.1f}%</div>
            <div style="color:#ffbb00; font-size:18px; font-weight:bold; width:23%; text-align:center;">🟡 MA50: {v_50:.1f}%</div>
            <div style="color:#ff3333; font-size:18px; font-weight:bold; width:23%; text-align:center;">🔴 MA200: {v_200:.1f}%</div>
        </div>
        ''', unsafe_allow_html=True)

    st.markdown("<hr style='border:2px solid #444; margin:30px 0;'>", unsafe_allow_html=True)

    # =========================================================
    # 📈 5 大港股核心圖表：K線與真實市寬雙 Y 軸融合大圖
    # =========================================================
    st.markdown("<h3 style='color:#00ff88;'>📈 5 大港股核心標竿：真實技術K線與內部市寬融合大圖</h3>", unsafe_allow_html=True)
    st.markdown("<p style='color:#aaa;'>（展示近 60 日走勢，主圖：陰陽燭 K 線與真實市寬重疊疊加；副圖：成交量）</p>", unsafe_allow_html=True)
    
    def render_ultimate_chart_hk(df_p, df_b, title_text):
        if df_p.empty or df_b.empty:
            return None

        fig = make_subplots(rows=2, cols=1, shared_xaxes=True, 
                            vertical_spacing=0.04, 
                            row_heights=[0.7, 0.3],
                            specs=[[{"secondary_y": True}], [{"secondary_y": False}]])

        if not df_p.empty and 'Close' in df_p.columns:
            fig.add_trace(go.Candlestick(x=df_p.index, open=df_p['Open'], high=df_p['High'], low=df_p['Low'], close=df_p['Close'], name='港股價格陰陽燭'), row=1, col=1, secondary_y=False)
        
        if not df_b.empty:
            if short_col_hist in df_b.columns:
                fig.add_trace(go.Scatter(x=df_b.index, y=df_b[short_col_hist], mode='lines', line=dict(color='#00ff88', width=3), name=f"市寬 {short_legend_label}"), row=1, col=1, secondary_y=True)
            if "Breadth_MA50" in df_b.columns:
                fig.add_trace(go.Scatter(x=df_b.index, y=df_b["Breadth_MA50"], mode='lines', line=dict(color='#ffbb00', width=2), name="市寬 🟡 MA50 中期"), row=1, col=1, secondary_y=True)
            if "Breadth_MA100" in df_b.columns:
                fig.add_trace(go.Scatter(x=df_b.index, y=df_b["Breadth_MA100"], mode='lines', line=dict(color='#00f2ff', width=2, dash='dot'), name="市寬 🔵 MA100 長期"), row=1, col=1, secondary_y=True)
            if "Breadth_MA200" in df_b.columns:
                fig.add_trace(go.Scatter(x=df_b.index, y=df_b["Breadth_MA200"], mode='lines', line=dict(color='#ff3333', width=3), name="市寬 🔴 MA200 牛熊"), row=1, col=1, secondary_y=True)

        if not df_p.empty and 'Volume' in df_p.columns:
            fig.add_trace(go.Bar(x=df_p.index, y=df_p['Volume'], marker_color='#4a5568', opacity=0.8, name='成交量'), row=2, col=1)

        fig.update_layout(
            title=dict(text=title_text, font=dict(color='white', size=24, family='Arial Black')),
            template="plotly_dark", height=750, margin=dict(l=50, r=60, t=60, b=20),
            xaxis_rangeslider_visible=False, showlegend=True,
            legend=dict(orientation="h", yanchor="bottom", y=1.02, xanchor="right", x=1, font=dict(color="white", size=14)),
            paper_bgcolor="#1e212b", plot_bgcolor="#1e212b"
        )
        
        fig.update_yaxes(title_text="價格 (HKD)", row=1, col=1, secondary_y=False, gridcolor="#333", tickfont=dict(size=14))
        fig.update_yaxes(title_text="真實市寬擴散 %", range=[-5, 105], row=1, col=1, secondary_y=True, gridcolor="#444", side="right", showgrid=False, tickfont=dict(color="#00ff88", size=14))
        fig.update_yaxes(title_text="Volume", row=2, col=1, gridcolor="#333", showticklabels=False)
        fig.update_xaxes(gridcolor="#333", tickfont=dict(size=14))

        return fig

    chart_order = [
        ("🔵 港股藍籌核心 (2800.HK)", "🔵 港股藍籌核心 (2800.HK) 戰略背離全景圖"),
        ("🇨🇳 中資國企骨幹 (2828.HK)", "🇨🇳 中資國企骨幹 (2828.HK) 戰略背離全景圖"),
        ("🚀 科技狂牛巨頭 (3033.HK)", "🚀 科技狂牛巨頭 (3033.HK) 戰略背離全景圖"),
        ("🛡️ 港股高息低波盾牌 (3437.HK)", "🛡️ 港股高息低波盾牌 (3437.HK) 戰略背離全景圖"),
        ("🦐 中小型股與 AI 科技新銳", "🦐 中小型股與 AI 科技新銳 戰略背離全景圖")
    ]
    
    for key, title in chart_order:
        df_p = price_results.get(key, pd.DataFrame())
        df_b = breadth_results.get(key, pd.DataFrame())
        
        if not df_p.empty and not df_b.empty and len(df_p) == len(df_b) and len(df_p) > 0:
            fig = render_ultimate_chart_hk(df_p, df_b, title)
            if fig:
                st.plotly_chart(fig, use_container_width=True, config={'displayModeBar': True})
                st.markdown("<br>", unsafe_allow_html=True)
        else:
            st.warning(f"⚠️ {title} 數據獲取中或未產生交易數據，請稍後重試。")

    st.markdown("<hr style='border:2px solid #444; margin:30px 0;'>", unsafe_allow_html=True)

    # =========================================================
    # 📊 港股 30 大板塊 3D 長條圖繪製
    # =========================================================
    st.markdown("<h3 style='color:#00ff88;'>📊 港股全量板塊大陣：今日真實市寬總動員切片</h3>", unsafe_allow_html=True)
    
    def get_val_for_bar(d, k1, k2):
        try: return float(d.get(k1, {}).get(k2, 0.0))
        except: return 0.0
    
    agg_rows = [
        {"板塊": "🎯 港股傳統板塊均值 (扣除特權標竿)", "MA5_Pct": top_banners.get("MA5",0), "MA20_Pct": top_banners.get("MA20",0), "MA50_Pct": top_banners.get("MA50",0), "MA200_Pct": top_banners.get("MA200",0), "sort_order": 1},
        {"板塊": "🔵 港股藍籌核心 (2800.HK)", "MA5_Pct": get_val_for_bar(current_day_data, "🔵 港股藍籌核心 (2800.HK)", "MA5_Pct"), "MA20_Pct": get_val_for_bar(current_day_data, "🔵 港股藍籌核心 (2800.HK)", "MA20_Pct"), "MA50_Pct": get_val_for_bar(current_day_data, "🔵 港股藍籌核心 (2800.HK)", "MA50_Pct"), "MA200_Pct": get_val_for_bar(current_day_data, "🔵 港股藍籌核心 (2800.HK)", "MA200_Pct"), "sort_order": 2},
        {"板塊": "🇨🇳 中資國企骨幹 (2828.HK)", "MA5_Pct": get_val_for_bar(current_day_data, "🇨🇳 中資國企骨幹 (2828.HK)", "MA5_Pct"), "MA20_Pct": get_val_for_bar(current_day_data, "🇨🇳 中資國企骨幹 (2828.HK)", "MA20_Pct"), "MA50_Pct": get_val_for_bar(current_day_data, "🇨🇳 中資國企骨幹 (2828.HK)", "MA50_Pct"), "MA200_Pct": get_val_for_bar(current_day_data, "🇨🇳 中資國企骨幹 (2828.HK)", "MA200_Pct"), "sort_order": 3},
        {"板塊": "🚀 科技狂牛巨頭 (3033.HK)", "MA5_Pct": get_val_for_bar(current_day_data, "🚀 科技狂牛巨頭 (3033.HK)", "MA5_Pct"), "MA20_Pct": get_val_for_bar(current_day_data, "🚀 科技狂牛巨頭 (3033.HK)", "MA20_Pct"), "MA50_Pct": get_val_for_bar(current_day_data, "🚀 科技狂牛巨頭 (3033.HK)", "MA50_Pct"), "MA200_Pct": get_val_for_bar(current_day_data, "🚀 科技狂牛巨頭 (3033.HK)", "MA200_Pct"), "sort_order": 4},
        {"板塊": "🛡️ 港股高息低波盾牌 (3437.HK)", "MA5_Pct": get_val_for_bar(current_day_data, "🛡️ 港股高息低波盾牌 (3437.HK)", "MA5_Pct"), "MA20_Pct": get_val_for_bar(current_day_data, "🛡️ 港股高息低波盾牌 (3437.HK)", "MA20_Pct"), "MA50_Pct": get_val_for_bar(current_day_data, "🛡️ 港股高息低波盾牌 (3437.HK)", "MA50_Pct"), "MA200_Pct": get_val_for_bar(current_day_data, "🛡️ 港股高息低波盾牌 (3437.HK)", "MA200_Pct"), "sort_order": 5},
        {"板塊": "🦐 中小型股與 AI 科技新銳", "MA5_Pct": get_val_for_bar(current_day_data, "🦐 中小型股與 AI 科技新銳", "MA5_Pct"), "MA20_Pct": get_val_for_bar(current_day_data, "🦐 中小型股與 AI 科技新銳", "MA20_Pct"), "MA50_Pct": get_val_for_bar(current_day_data, "🦐 中小型股與 AI 科技新銳", "MA50_Pct"), "MA200_Pct": get_val_for_bar(current_day_data, "🦐 中小型股與 AI 科技新銳", "MA200_Pct"), "sort_order": 6},
    ]
    df_agg = pd.DataFrame(agg_rows)
    
    if not df_rs.empty:
        df_rs["sort_order"] = 999
        df_final_plot = pd.concat([df_agg, df_rs], ignore_index=True)
    else:
        df_final_plot = df_agg
    
    for col in ["MA200_Pct", "MA50_Pct", short_col_name]:
        if col not in df_final_plot.columns: df_final_plot[col] = 0.0

    df_final_plot = df_final_plot.sort_values(by=["sort_order", "MA200_Pct", "MA50_Pct", short_col_name], ascending=[False, True, True, True])

    chart_height = 2000
    y_data = df_final_plot["板塊"].tolist()

    fig2 = go.Figure()
    fig2.add_trace(go.Bar(
        x=df_final_plot["MA200_Pct"].tolist(), y=y_data, name="🔴 MA200 長期牛熊", orientation='h', marker_color='#ff3333',
        text=[f"{v:.1f}%" for v in df_final_plot["MA200_Pct"].tolist()], textposition='outside', textfont=dict(color='#ffffff', size=18, family='Arial Black')
    ))
    fig2.add_trace(go.Bar(
        x=df_final_plot["MA50_Pct"].tolist(), y=y_data, name="🟡 MA50 中期穩定", orientation='h', marker_color='#ffbb00',
        text=[f"{v:.1f}%" for v in df_final_plot["MA50_Pct"].tolist()], textposition='outside', textfont=dict(color='#ffffff', size=18, family='Arial Black')
    ))
    fig2.add_trace(go.Bar(
        x=df_final_plot[short_col_name].tolist(), y=y_data, name=short_legend_label, orientation='h', marker_color='#00ff88',
        text=[f"{v:.1f}%" for v in df_final_plot[short_col_name].tolist()], textposition='outside', textfont=dict(color='#ffffff', size=18, family='Arial Black')
    ))

    fig2.update_layout(
        barmode='group', template="plotly_dark", height=chart_height, bargap=0.06, barcornerradius=8,
        xaxis=dict(title="各均線之上股票佔比 (%)", tickfont=dict(size=18, color="white"), gridcolor="#222222", range=[0, 130]),
        yaxis=dict(tickfont=dict(size=20, color="white", family='Arial Black'), gridcolor="#222222", automargin=True),
        legend=dict(orientation="h", yanchor="bottom", y=1.01, xanchor="right", x=1, font=dict(size=18, color="white")),
        margin=dict(l=320, r=100, t=100, b=40), paper_bgcolor="#0e1117", plot_bgcolor="#0e1117"
    )

    st.plotly_chart(fig2, use_container_width=True, config={'displayModeBar': True})

if __name__ == "__main__":
    render_page_2bb_hk()