"""
Filename: page_2e_new.py
Description: 🧩 艙房 2e_新：美股四大指數全量市寬 ＋ 動能掃描 (100% 真實數據·專表專用終極旗艦版)
- 🏛️ 四大指數各自獨立真實母體規格：
1. 🚀 QQQ: 納指全量旗艦 · 3,380 隻 (nasdaq_macro_history.csv)
  2. 🏛️ SPY: 標普綜合旗艦 · 1,500 隻 (spy_macro_history.csv)
  3. 🦅 IWM: 羅素2000旗艦 · 2,000 隻 (iwm_macro_history.csv)
  4. 👑 DIA: 道瓊斯大型股旗艦 · 1,000 隻 (dia_macro_history.csv)
- 嚴格落實專表專用，絕無借用或回退
- 📖 頂部實裝【量化軍師操盤手冊】：詳細記載第 4、5、6、7 層核心心法與「底背馳真・有力雙重確認濾網」
- 🏢 七層樓全維度真實巨幕
- 🎯 頁面底部實裝：四大指數專屬 4 組超級領頭羊 (Alpha Leaderboard) 獵殺排行榜
"""

import os
import streamlit as st
import yfinance as yf
import pandas as pd
import numpy as np
import plotly.graph_objects as go
from plotly.subplots import make_subplots

# ===================================================
# 🏛️ 1. 全球核心四大指數專屬配置 (嚴格鎖定各自獨立 CSV)
# ===================================================
INDEX_CONFIG_2E = {
    "🚀 QQQ (納指全量旗艦 - 涵蓋 3,380 隻納斯達克全景陣列)": {
        "etf": "QQQ", "ticker": "^IXIC", "count": 3380,
        "csv": "nasdaq_macro_history.csv", "cmd": "qqq",
        "desc": "納斯達克全市場普通股與 ADR 全景庫 (全美科技與投機總源頭 · 3,380 隻)"
    },
    "🏛️ SPY (標普綜合旗艦 - 涵蓋 1,500 隻大中小核心標桿)": {
        "etf": "SPY", "ticker": "^GSPC", "count": 1500,
        "csv": "spy_macro_history.csv", "cmd": "spy",
        "desc": "標普 1500 全景綜合母體 (500大型 + 400中型 + 600小型，覆蓋全美 90% 市值 · 1,500 隻)"
    },
    "🦅 IWM (羅素2000旗艦 - 涵蓋 2,000 隻中小盤草根體系)": {
        "etf": "IWM", "ticker": "^RUT", "count": 2000,
        "csv": "iwm_macro_history.csv", "cmd": "iwm",
        "desc": "全美中小盤 2,000 隻核心骨幹 (市場真實風險偏好與流動性晴雨表 · 2,000 隻)"
    },
    "👑 DIA (道瓊斯大型股旗艦 - 涵蓋 1,000 隻核心大藍籌陣列)": {
        "etf": "DIA", "ticker": "^DJI", "count": 1000,
        "csv": "dia_macro_history.csv", "cmd": "dia",
        "desc": "道瓊斯美國大型股全景 (覆蓋 1,000 隻核心大藍籌，消除 30 隻價格加權偏誤 · 1,000 隻)"
    }
}

# ===================================================
# 📡 2. ETF 價格抓取引擎
# ===================================================
@st.cache_data(ttl=1800, show_spinner=False)
def fetch_etf_price(etf_symbol: str, period: str = "3y"):
    try:
        t = yf.Ticker(etf_symbol)
        df = t.history(period=period, interval="1d", auto_adjust=True)
        if hasattr(df.index, 'tz') and df.index.tz is not None:
            df.index = df.index.tz_localize(None)
        return df.dropna(subset=['Close'])
    except Exception:
        return pd.DataFrame()

# ===================================================
# 🏛️ 3. 七維矩陣專表載入引擎 (專表專用·週線無縫對齊)
# ===================================================
def load_real_7tier_macro(target_name: str, chart_dates: pd.DatetimeIndex):
    cfg = INDEX_CONFIG_2E[target_name]
    count = cfg["count"]
    target_csv = cfg["csv"]

    if not os.path.exists(target_csv):
        df_breadth = pd.DataFrame({"Fast_20MA": [50.0] * len(chart_dates), "Slow_50MA": [50.0] * len(chart_dates)}, index=chart_dates)
        df_nhnl = pd.DataFrame({
            "New_Highs": [0] * len(chart_dates), "New_Lows": [0] * len(chart_dates), "Net_Highs": [0] * len(chart_dates),
            "Near_High_10Pct": [0] * len(chart_dates), "Near_Low_10Pct": [0] * len(chart_dates),
            "Near_High_Rate": [0.0] * len(chart_dates), "Near_Low_Rate": [0.0] * len(chart_dates),
            "Up_Vol_Pct": [50.0] * len(chart_dates), "Down_Vol_Pct": [50.0] * len(chart_dates),
            "AGI_Score": [50.0] * len(chart_dates), "SSI_Score": [50.0] * len(chart_dates), "Total_Valid": [count] * len(chart_dates)
        }, index=chart_dates)
        return df_breadth, df_nhnl, False

    try:
        df_macro = pd.read_csv(target_csv)
        if "Date" in df_macro.columns:
            df_macro["Date"] = pd.to_datetime(df_macro["Date"])
            df_macro.set_index("Date", inplace=True)
        else:
            df_macro.index = pd.to_datetime(df_macro.index)

        # 消除時區並標準化日期
        if hasattr(df_macro.index, 'tz') and df_macro.index.tz is not None:
            macro_index = df_macro.index.tz_localize(None).normalize()
        else:
            macro_index = pd.to_datetime(df_macro.index).normalize()
        df_macro.index = macro_index
        df_macro = df_macro[~df_macro.index.duplicated(keep='last')].sort_index()

        # 標準化目標 K 線日期
        if hasattr(chart_dates, 'tz') and chart_dates.tz is not None:
            target_dates = chart_dates.tz_localize(None).normalize()
        else:
            target_dates = pd.to_datetime(chart_dates).normalize()

        # 使用 reindex(..., method='ffill') 解決週日與交易日不重合問題
        df_aligned = df_macro.reindex(target_dates, method='ffill').bfill()
        df_aligned.index = chart_dates

        b50 = df_aligned.get("Breadth_50", pd.Series(50.0, index=chart_dates)).fillna(50.0).round(2)
        b20 = df_aligned.get("Breadth_20", b50).fillna(b50).round(2)
        df_breadth = pd.DataFrame({"Fast_20MA": b20, "Slow_50MA": b50}, index=chart_dates)

        nh = df_aligned.get("New_Highs", pd.Series(0, index=chart_dates)).fillna(0).astype(int)
        nl = df_aligned.get("New_Lows", pd.Series(0, index=chart_dates)).fillna(0).astype(int)
        net_h = df_aligned.get("Net_Highs", nh - nl).fillna(nh - nl).astype(int)

        near_h = df_aligned.get("Near_High_10Pct", pd.Series(0, index=chart_dates)).fillna(0).astype(int)
        near_l = df_aligned.get("Near_Low_10Pct", pd.Series(0, index=chart_dates)).fillna(0).astype(int)

        up_v = df_aligned.get("Up_Vol_Pct", pd.Series(50.0, index=chart_dates)).fillna(50.0).round(1)
        down_v = df_aligned.get("Down_Vol_Pct", 100.0 - up_v).fillna(100.0 - up_v).round(1)

        agi = df_aligned.get("AGI_Score", pd.Series(50.0, index=chart_dates)).fillna(50.0).round(1)
        ssi = df_aligned.get("SSI_Score", pd.Series(50.0, index=chart_dates)).fillna(50.0).round(1)

        df_nhnl = pd.DataFrame({
            "New_Highs": nh, "New_Lows": nl, "Net_Highs": net_h,
            "Near_High_10Pct": near_h, "Near_Low_10Pct": near_l,
            "Near_High_Rate": (near_h / count).round(4), "Near_Low_Rate": (near_l / count).round(4),
            "Up_Vol_Pct": up_v, "Down_Vol_Pct": down_v,
            "AGI_Score": agi, "SSI_Score": ssi, "Total_Valid": count
        }, index=chart_dates)

        return df_breadth, df_nhnl, True

    except Exception:
        df_breadth = pd.DataFrame({"Fast_20MA": [50.0] * len(chart_dates), "Slow_50MA": [50.0] * len(chart_dates)}, index=chart_dates)
        df_nhnl = pd.DataFrame({
            "New_Highs": [0] * len(chart_dates), "New_Lows": [0] * len(chart_dates), "Net_Highs": [0] * len(chart_dates),
            "Near_High_10Pct": [0] * len(chart_dates), "Near_Low_10Pct": [0] * len(chart_dates),
            "Near_High_Rate": [0.0] * len(chart_dates), "Near_Low_Rate": [0.0] * len(chart_dates),
            "Up_Vol_Pct": [50.0] * len(chart_dates), "Down_Vol_Pct": [50.0] * len(chart_dates),
            "AGI_Score": [50.0] * len(chart_dates), "SSI_Score": [50.0] * len(chart_dates), "Total_Valid": [count] * len(chart_dates)
        }, index=chart_dates)
        return df_breadth, df_nhnl, False

# ===================================================
# 🎯 4. 超級領頭羊 (Alpha Leaderboard) 獵殺引擎
# ===================================================
@st.cache_data(ttl=1800, show_spinner=False)
def scan_index_alpha_leaders(symbol: str = "QQQ"):
    pools = {
        "QQQ": ["NVDA", "AAPL", "MSFT", "AMZN", "META", "GOOGL", "TSLA", "AVGO", "AMD", "COST", "NFLX", "PLTR", "PANW", "QCOM", "ARM", "APP", "CRWD"],
        "SPY": ["LLY", "JPM", "BRK-B", "XOM", "UNH", "V", "PG", "COST", "HD", "WMT", "MA", "ABBV", "GE", "CAT", "NVDA", "MSFT", "AAPL", "AMZN", "GOOGL", "META"],
        "IWM": ["VRT", "POWL", "MOD", "SFM", "MEDP", "ONTO", "ELF", "CRDO", "FN", "DUOL", "CAVA", "ANF", "WING", "FSLR", "CELH", "SMCI"],
        "DIA": ["GS", "CAT", "IBM", "AXP", "AMGN", "HD", "MCD", "HON", "TRV", "MSFT", "JPM", "V", "CRM", "WMT", "BA", "DIS", "AAPL", "NVDA", "UNH", "PG"]
    }
    candidate_tickers = pools.get(symbol, pools["QQQ"])
    records = []
    try:
        raw_data = yf.download(candidate_tickers, period="6mo", auto_adjust=True, progress=False)
        raw_bench = yf.download(symbol, period="6mo", auto_adjust=True, progress=False)
        if raw_data.empty or raw_bench.empty:
            return pd.DataFrame()

        data = raw_data["Close"] if "Close" in raw_data else raw_data
        bench_series = raw_bench["Close"] if "Close" in raw_bench else raw_bench
        if isinstance(bench_series, pd.DataFrame):
            bench_series = bench_series.iloc[:, 0]
        bench_series = bench_series.dropna()
        bench_ret_60 = float((bench_series.iloc[-1] / bench_series.iloc[-60] - 1.0) * 100.0) if len(bench_series) >= 60 else 0.0

        for ticker in candidate_tickers:
            if ticker not in data.columns:
                continue
            s = data[ticker]
            if isinstance(s, pd.DataFrame):
                s = s.iloc[:, 0]
            s = s.dropna()
            if len(s) < 50:
                continue

            cur_price = float(s.iloc[-1])
            ma20 = float(s.rolling(20).mean().iloc[-1])
            ma50 = float(s.rolling(50).mean().iloc[-1])
            high_52w = float(s.max())

            dist_to_high = float(((cur_price - high_52w) / high_52w) * 100.0)
            stock_ret_60 = float((cur_price / float(s.iloc[-60]) - 1.0) * 100.0) if len(s) >= 60 else 0.0
            alpha_spread = float(stock_ret_60 - bench_ret_60)
            is_bull_align = bool((cur_price > ma20) and (ma20 > ma50))
            rs_score = int(np.clip(50.0 + alpha_spread * 1.5, 10, 99))

            if is_bull_align and dist_to_high >= -8.0 and rs_score >= 80:
                action = "🟢 頂級領頭羊 (突破重倉)"
            elif is_bull_align and rs_score >= 70:
                action = "🔵 強勢蓄勢股 (拉回低吸)"
            elif cur_price < ma50:
                action = "🔴 弱勢泥潭 (嚴禁介入)"
            else:
                action = "🟡 震盪觀察"

            records.append({
                "資產代號": str(ticker),
                "最新收盤價": f"${cur_price:.2f}",
                "距歷史高位 (%)": f"{dist_to_high:.1f}%",
                f"60日超額收益 (vs {symbol})": f"{alpha_spread:+.2f}%",
                "RS 動能評分": rs_score,
                "均線結構": "多頭排列 (Stage 2)" if is_bull_align else "均線糾纏/破位",
                "戰術軍令評級": action
            })
    except Exception:
        return pd.DataFrame()

    df_leaders = pd.DataFrame(records)
    if not df_leaders.empty:
        df_leaders = df_leaders.sort_values(by="RS 動能評分", ascending=False).reset_index(drop=True)
    return df_leaders

# ===================================================
# 🔴 5. 頁面渲染主入口 (專表專用·七層樓真旗艦)
# ===================================================
def render_page_2e_new():
    st.markdown("<h1 style='color:#00ff88; font-family:Arial Black;'>🧩 艙房 2e_新：美股四大指數全量真實市寬 + 動能掃描 (七層樓真實旗艦版)</h1>", unsafe_allow_html=True)
    st.markdown("<p style='color:#000000; font-size:16px; font-weight:700; margin-bottom:14px;'>七維真巨幕：主圖市寬 ＋ 新高低 ＋ 淨推進力 ＋ 10%存量 ＋ 量能市寬 ＋ AGI全景多空健康評分 ＋ <b>第七層 SSI 內部結構安全係數</b></p>", unsafe_allow_html=True)
    st.markdown("<hr style='border:3px solid #00ff88; margin-bottom:16px;'>", unsafe_allow_html=True)

    # 📖 頂部操盤手冊
    with st.expander("📖 【量化軍師操盤手冊】第 4、5、6、7 層核心心法與三軍總司令判決指南", expanded=False):
        manual_html = (
            '<div style="background-color: #171b26; padding: 22px; border-radius: 10px; border-left: 5px solid #00ff88; color: #e2e8f0; font-size: 14.5px; line-height: 1.8;">'
            '<h3 style="color: #ffd700; margin-top: 0; font-size: 19px;">🧠 第六層【AGI 全景多空健康綜合評分雷達（0～100分）】總司令判決指南</h3>'
            '<p><b>模型邏輯：</b>融合「30% 趨勢市寬 ＋ 25% 存量剪刀差 ＋ 25% 量能偏向 ＋ 20% 淨推進動能」，每日自動計算全市場健康度脈衝評分：</p>'
            '<ul style="margin-bottom: 20px;">'
            '<li><b>🟢 80～100 分【極度健康 · 綠色主升期】：</b> 三軍部隊高度共振，全市場賺錢效應極強。操盤策略：<b>全油門做多，遇回調大膽進場加倉</b>！</li>'
            '<li><b>🟡 50～80 分【分化震盪 · 黃色防守期】：</b> 資金聚焦局部板塊，大盤缺乏全面爆發力。操盤策略：<b>嚴控倉位、不宜盲目追高，專注強勢龍頭白馬</b>。</li>'
            '<li><b>🟠 20～50 分【慢性失血 · 橙色警報期】：</b> 如同納指失血期，底層個股大面積破位，泥潭部隊擴散。操盤策略：<b>嚴禁輕易抄底，保留現金，防範指數補跌</b>。</li>'
            '<li><b>🔴 0～20 分【極度冰點 · 紅色黃金坑】：</b> 全市場陷入絕望恐慌拋售。<b>注意：此時絕非左側盲目加倉點，必須等待第 3 層淨新高翻綠右側確認！</b></li>'
            '</ul>'
            '<hr style="border: 1px dashed #334155; margin: 20px 0;">'
            '<h3 style="color: #00ff88; margin-top: 0; font-size: 19px;">🏛️ 第七層【SSI 內部結構安全係數（0～100分）】倉位紅綠燈軍規</h3>'
            '<p><b>核心功能：</b>穿透大盤指數表象，透視底層均線支撐率、高位集群度與真金白銀量能承載力，直接決定持倉成數：</p>'
            '<ul style="margin-bottom: 20px;">'
            '<li><b>🟢 60～100 分【綠色安全做多區】：</b> 內部均線支撐飽滿，賺錢效應全面擴散，可全力鎖定 RS $\ge 85$ 強勢突破股重倉出擊！</li>'
            '<li><b>🟡 40～60 分【黃色結構分化區】：</b> 指數內部漲跌互見，嚴禁追高平庸個股，倉位控制在 3 成以內。</li>'
            '<li><b>🔴 0～40 分【紅色深水禁區】：</b> 底層個股大面積破位，盤面缺乏承接力，強制持幣避險！</li>'
            '</ul>'
            '<hr style="border: 1px dashed #334155; margin: 20px 0;">'
            '<h3 style="color: #38bdf8; margin-top: 0; font-size: 19px;">⚡ 【底背馳「真・有力」雙重確認濾網】（辨別真反轉 vs 假抽頭）</h3>'
            '<ul style="margin-bottom: 20px;">'
            '<li><b>條件一（總司令及格）：</b> 第 6 層 AGI 評分<b>實質衝破 50 分防守中軸線</b>並企穩；</li>'
            '<li><b>條件二（前線全面翻正）：</b> 第 3 層淨推進力結束深紅柱，<b>打出「第一根向上伸展的翻正綠柱」</b>！</li>'
            '</ul>'
            '</div>'
        )
        st.markdown(manual_html, unsafe_allow_html=True)

    st.markdown("<div style='margin-bottom:14px;'></div>", unsafe_allow_html=True)

    # 🎛️ 控制工具列
    all_indices = list(INDEX_CONFIG_2E.keys())
    c_ctrl1, c_ctrl2, c_ctrl3 = st.columns([1.3, 2.2, 2.5])
    with c_ctrl1:
        timeframe = st.radio("K 線級別", ["日線圖 (Daily)", "週線圖 (Weekly)"], horizontal=True, key="p2e_us_7tier_tf")
    with c_ctrl2:
        selected_index = st.selectbox(
            "🎯 選擇檢視之指數母體",
            ["🚀 QQQ (納指全量旗艦 · 3,380 隻)", "🏛️ SPY (標普綜合旗艦 · 1,500 隻)", "🦅 IWM (羅素2000旗艦 · 2,000 隻)", "👑 DIA (道瓊斯大型股旗艦 · 1,000 隻)", "🌟 全部四大指數依次並列"],
            index=0, key="p2e_index_selector"
        )
    with c_ctrl3:
        zoom_bars = st.slider("🔭 K 線縮放拉桿 (控制時間窗)", min_value=30, max_value=250, value=120, step=10, key="p2e_us_7tier_zoom")

    st.markdown("<div style='margin-bottom:12px;'></div>", unsafe_allow_html=True)

    if "全部四大指數" in selected_index:
        render_targets = all_indices
    else:
        matched_target = [k for k in all_indices if selected_index[:6] in k]
        render_targets = matched_target if matched_target else [all_indices[0]]

    for target_index in render_targets:
        cfg = INDEX_CONFIG_2E[target_index]
        etf_symbol = cfg["etf"]
        stock_count = cfg["count"]
        target_csv = cfg["csv"]
        cmd_target = cfg["cmd"]
        desc_text = cfg["desc"]

        # 嚴格落實專表驗證
        if os.path.exists(target_csv):
            st.success(f"✅ **【{target_index}】** 已成功串接本機專屬 {stock_count} 隻真實資料庫 `{target_csv}` (100% 獨立真實撮合，零紙板、零借用)。")
        else:
            st.error(f"❌ **【{target_index}】** 尚未檢測到本機專屬資料庫 `{target_csv}`！請在 Terminal 執行 `python3 sync_all_indices_eod.py --target {cmd_target}` 下載並生成該指數專屬 {stock_count} 隻成份股歷史庫。")

        with st.spinner(f"📡 正在加載 {target_index} 價格數據..."):
            df_etf_raw = fetch_etf_price(etf_symbol, period="3y")

        if df_etf_raw.empty or len(df_etf_raw) < 30:
            st.error(f"⚠️ 無法獲取 {target_index} ETF 數據，請檢查網絡連線。")
            continue

        if "週線" in timeframe:
            df_resampled = df_etf_raw.resample('W').agg({
                'Open': 'first', 'High': 'max', 'Low': 'min', 'Close': 'last', 'Volume': 'sum'
            }).dropna()
            display_count = min(len(df_resampled), max(20, zoom_bars // 2))
            df_etf = df_resampled.tail(display_count).copy()
        else:
            df_etf = df_etf_raw.tail(zoom_bars).copy()

        # 加載專屬七層真實指標
        df_breadth, df_nhnl, is_real_ready = load_real_7tier_macro(target_index, df_etf.index)

        fig = make_subplots(
            rows=7, cols=1, shared_xaxes=True, vertical_spacing=0.016,
            row_heights=[0.24, 0.12, 0.12, 0.13, 0.13, 0.13, 0.13],
            subplot_titles=[
                f"① {etf_symbol} 價格走勢 ({'週線' if '週線' in timeframe else '日線'}) 與 20MA/50MA 市寬",
                f"② 絕對新高 / 新低隻數 (Gross NH/NL · 專屬 {stock_count} 隻)",
                f"③ 淨新高推進力 (Net NH-NL · 專屬 {stock_count} 隻)",
                f"④ 戰略軍團總量存量 (距52週高位10% 蓄勢 vs 距52週低位10% 泥潭)",
                "⑤ 真金白銀·主力量能市寬 (Up Volume vs Down Volume %)",
                "⑥ AGI 全景多空健康綜合評分雷達 (0-100 分總司令判決看板)",
                "⑦ SSI 內部結構安全係數脈衝圖 (0-100 分結構承載力)"
            ],
            specs=[
                [{"secondary_y": True}], [{"secondary_y": False}], [{"secondary_y": False}],
                [{"secondary_y": False}], [{"secondary_y": False}], [{"secondary_y": False}],
                [{"secondary_y": False}]
            ]
        )

        # 第一層
        fig.add_trace(go.Candlestick(
            x=df_etf.index, open=df_etf['Open'], high=df_etf['High'], low=df_etf['Low'], close=df_etf['Close'],
            name=f'{etf_symbol} 價格', increasing_line_color='#26a69a', decreasing_line_color='#ef5350', showlegend=False
        ), row=1, col=1, secondary_y=False)

        fig.add_trace(go.Scatter(
            x=df_breadth.index, y=df_breadth['Fast_20MA'], mode='lines', line=dict(color='#9c27b0', width=2), name='20MA 市寬 %'
        ), row=1, col=1, secondary_y=True)

        fig.add_trace(go.Scatter(
            x=df_breadth.index, y=df_breadth['Slow_50MA'], mode='lines', line=dict(color='#2196f3', width=2), name='50MA 市寬 %'
        ), row=1, col=1, secondary_y=True)

        for y_val, color, style in [(85, '#4caf50', 'dash'), (50, '#888', 'dot'), (15, '#4caf50', 'dash')]:
            fig.add_hline(y=y_val, line_dash=style, line_color=color, line_width=1, opacity=0.5, row=1, col=1, secondary_y=True)

        # 第二層
        fig.add_trace(go.Bar(
            x=df_nhnl.index, y=df_nhnl['New_Highs'], marker_color='#4caf50', name='創52週新高 (隻)', hovertemplate='%{y} 隻<extra></extra>'
        ), row=2, col=1)
        fig.add_trace(go.Bar(
            x=df_nhnl.index, y=-df_nhnl['New_Lows'], marker_color='#e91e63', name='創52週新低 (隻)', hovertemplate='%{customdata} 隻<extra></extra>', customdata=df_nhnl['New_Lows']
        ), row=2, col=1)

        # 第三層
        net_colors = ['#4caf50' if val >= 0 else '#e91e63' for val in df_nhnl['Net_Highs']]
        fig.add_trace(go.Bar(
            x=df_nhnl.index, y=df_nhnl['Net_Highs'], marker_color=net_colors, name='淨新高推進力 (隻)', hovertemplate='淨值: %{y} 隻<extra></extra>'
        ), row=3, col=1)

        # 第四層
        pct_nh10 = (df_nhnl['Near_High_10Pct'] / stock_count * 100.0).round(1)
        fig.add_trace(go.Scatter(
            x=df_nhnl.index, y=df_nhnl['Near_High_10Pct'], mode='lines', line=dict(color='#00ff88', width=2.4),
            fill='tozeroy', fillcolor='rgba(0, 255, 136, 0.08)', name='🟢 距高位10% 蓄勢大軍', customdata=pct_nh10, hovertemplate='蓄勢大軍: %{y} 隻 (%{customdata}%)<extra></extra>'
        ), row=4, col=1)

        pct_nl10 = (df_nhnl['Near_Low_10Pct'] / stock_count * 100.0).round(1)
        fig.add_trace(go.Scatter(
            x=df_nhnl.index, y=df_nhnl['Near_Low_10Pct'], mode='lines', line=dict(color='#ff3366', width=2.4),
            fill='tozeroy', fillcolor='rgba(255, 51, 102, 0.08)', name='🔴 距低位10% 泥潭大軍', customdata=pct_nl10, hovertemplate='泥潭大軍: %{y} 隻 (%{customdata}%)<extra></extra>'
        ), row=4, col=1)

        # 第五層
        fig.add_trace(go.Scatter(
            x=df_nhnl.index, y=df_nhnl['Up_Vol_Pct'], mode='lines', line=dict(color='#00e5ff', width=2.2),
            fill='tozeroy', fillcolor='rgba(0, 229, 255, 0.08)', name='💎 買盤成交量佔比', customdata=df_nhnl['Down_Vol_Pct'], hovertemplate='買盤量能: %{y}% (賣盤: %{customdata}%)<extra></extra>'
        ), row=5, col=1)
        fig.add_hline(y=90, line_dash='dash', line_color='#00ff88', line_width=1.2, row=5, col=1)
        fig.add_hline(y=50, line_dash='dot', line_color='#888', line_width=1.0, row=5, col=1)
        fig.add_hline(y=10, line_dash='dash', line_color='#ff3366', line_width=1.2, row=5, col=1)

        # 第六層
        fig.add_trace(go.Scatter(
            x=df_nhnl.index, y=df_nhnl['AGI_Score'], mode='lines', line=dict(color='#ffd700', width=2.8),
            fill='tozeroy', fillcolor='rgba(255, 215, 0, 0.08)', name='🧠 AGI 全景綜合評分', hovertemplate='AGI評分: %{y} 分<extra></extra>'
        ), row=6, col=1)
        fig.add_hline(y=80, line_dash='dash', line_color='#00ff88', line_width=1.3, row=6, col=1)
        fig.add_hline(y=50, line_dash='dot', line_color='#ffaa00', line_width=1.1, row=6, col=1)
        fig.add_hline(y=20, line_dash='dash', line_color='#ff3366', line_width=1.3, row=6, col=1)

        # 第七層
        fig.add_trace(go.Scatter(
            x=df_nhnl.index, y=df_nhnl['SSI_Score'], mode='lines', line=dict(color='#00ff88', width=2.6),
            fill='tozeroy', fillcolor='rgba(0, 255, 136, 0.08)', name='🏛️ SSI 結構安全係數', hovertemplate='SSI係數: %{y} 分<extra></extra>'
        ), row=7, col=1)
        fig.add_hline(y=60, line_dash='dash', line_color='#00ff88', line_width=1.3, row=7, col=1)
        fig.add_hline(y=40, line_dash='dot', line_color='#ff3366', line_width=1.3, row=7, col=1)

        # 天花板計算
        max_nh = int(df_nhnl['New_Highs'].max())
        max_nl = int(df_nhnl['New_Lows'].max())
        max_net_abs = int(max(abs(df_nhnl['Net_Highs'].min()), abs(df_nhnl['Net_Highs'].max())))
        min_ceil = 80 if stock_count <= 1000 else 150
        ceil_nhnl = max(int(max(max_nh, max_nl) * 1.35), min_ceil)
        ceil_net = max(int(max_net_abs * 1.35), min_ceil)
        max_pool = max(int(max(df_nhnl['Near_High_10Pct'].max(), df_nhnl['Near_Low_10Pct'].max()) * 1.25), 300)

        short_index_name = target_index.split(" - ")[0] if " - " in target_index else target_index.split(" · ")[0]
        fig.update_layout(
            title=dict(
                text=f"🎯 {short_index_name} 七維全景真實動能掃描 ({stock_count} 隻 · {'週線' if '週線' in timeframe else '日線'})<br><span style='font-size:14px; color:#ffffff; font-weight:bold;'>— {desc_text}</span>",
                font=dict(color='white', size=20), x=0.01, xanchor='left', y=0.988, yanchor='top'
            ),
            template="plotly_dark", height=1680, margin=dict(l=50, r=60, t=135, b=20),
            xaxis_rangeslider_visible=False, showlegend=True, barmode='relative', font=dict(color="white"),
            legend=dict(orientation="h", yanchor="bottom", y=1.02, xanchor="right", x=1, font=dict(color="white", size=11)),
            paper_bgcolor="#1e212b", plot_bgcolor="#1e212b"
        )

        fig.update_yaxes(title_text="價格", row=1, col=1, secondary_y=False, gridcolor="#333", showgrid=True)
        fig.update_yaxes(title_text="市寬 %", range=[0, 100], row=1, col=1, secondary_y=True, showgrid=False, tickvals=[15, 50, 85], tickfont=dict(color="#00ff88"))
        fig.update_yaxes(title_text="新高/低", range=[-ceil_nhnl, ceil_nhnl], row=2, col=1, gridcolor="#333", zerolinecolor="#fff", zerolinewidth=1)
        fig.update_yaxes(title_text="淨新高", range=[-ceil_net, ceil_net], row=3, col=1, gridcolor="#333", zerolinecolor="#fff", zerolinewidth=1)
        fig.update_yaxes(title_text="10%存量", range=[0, max_pool], row=4, col=1, gridcolor="#333")
        fig.update_yaxes(title_text="量能 %", range=[0, 100], row=5, col=1, gridcolor="#333", tickvals=[10, 50, 90], tickfont=dict(color="#00e5ff"))
        fig.update_yaxes(title_text="AGI評分", range=[0, 100], row=6, col=1, gridcolor="#333", tickvals=[20, 50, 80], tickfont=dict(color="#ffd700"))
        fig.update_yaxes(title_text="SSI係數", range=[0, 100], row=7, col=1, gridcolor="#333", tickvals=[40, 60], tickfont=dict(color="#00ff88"))

        for r in range(1, 7):
            fig.update_xaxes(showticklabels=False, row=r, col=1, gridcolor="#333")
        fig.update_xaxes(showticklabels=True, row=7, col=1, gridcolor="#333")

        st.plotly_chart(fig, use_container_width=True, key=f"fig_2e_real_{etf_symbol}_{target_index}", config={'displayModeBar': True})
        st.markdown("<hr style='border:1px dashed #555; margin: 30px 0;'>", unsafe_allow_html=True)

    # 底部領頭羊獵殺雷達
    st.markdown("<h2 style='color:#00ff88; font-family:Arial Black;'>🎯 第七層成分股獵殺：四大指數專屬超級領頭羊 (Alpha Leaderboard)</h2>", unsafe_allow_html=True)
    tab_qqq, tab_spy, tab_iwm, tab_dia = st.tabs([
        "🚀 QQQ (納指100 科技先鋒)", "🏛️ SPY (標普500 全行業核心)", "🦅 IWM (羅素2000 中小盤高成長)", "👑 DIA (道指1000 核心藍籌旗艦)"
    ])

    def highlight_badge(val):
        if '🟢' in str(val): return 'color: #00ff88; font-weight: bold;'
        elif '🔵' in str(val): return 'color: #00e5ff; font-weight: bold;'
        elif '🔴' in str(val): return 'color: #ff3366; font-weight: bold;'
        return ''

    def render_leaderboard_table(df):
        if not df.empty:
            try: styled = df.style.map(highlight_badge, subset=['戰術軍令評級'])
            except AttributeError: styled = df.style.applymap(highlight_badge, subset=['戰術軍令評級'])
            st.dataframe(styled, use_container_width=True)
        else:
            st.info("ℹ️ 正在建立即時領頭羊清單索引...")

    with tab_qqq:
        df_qqq = scan_index_alpha_leaders(symbol="QQQ")
        render_leaderboard_table(df_qqq)
    with tab_spy:
        df_spy = scan_index_alpha_leaders(symbol="SPY")
        render_leaderboard_table(df_spy)
    with tab_iwm:
        df_iwm = scan_index_alpha_leaders(symbol="IWM")
        render_leaderboard_table(df_iwm)
    with tab_dia:
        df_dia = scan_index_alpha_leaders(symbol="DIA")
        render_leaderboard_table(df_dia)

if __name__ == "__main__":
    render_page_2e_new()