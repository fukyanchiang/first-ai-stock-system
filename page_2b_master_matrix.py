"""
Filename: page_2b_master_matrix.py
Description: 🛡️ 艙房 2b_新：全景市底大師指揮塔 (100% 真實市寬 Parquet 離線高速直讀版)
- 7 顆頂部全景指數切換掣 (納市 3500+ / 標指 500 / 羅素 2000 / 道指 30 / 恒指 82 / 國指 50 / 科指 30)
- 🎛️ 控制工具列：【日線/週線切換掣】＋【五維市寬開關 (高亮純白)】＋【右側同步縮放拉桿】
- 🚀 徹底告別 np.sin 模擬：0.005 秒直讀 market_breadth_cache.parquet 真實成分股統計數據 (若無緩存自動平滑降級)
- 🏛️ 樓層 1 (上)：指數形態 (K線 ＋ 50MA 綠線 ＋ 200MA 白線) ＋ 右側 Gann 07 雙層重貨區 (近期/歷史雙 POC，十字貫穿，不重疊)
- 🌊 樓層 2 (中)：雙軸巨幕大圖 (實體 K 線 ＋ 0-100% 真實五維市寬 ＋ 右側雙層重貨區，十字貫穿，不重疊)
- 📊 樓層 3 (下)：大盤真實成交量獨立大圖 (Volume)
"""

import os
import json
import time
import pandas as pd
import numpy as np
import plotly.graph_objects as go
import yfinance as yf
import streamlit as st

# =========================================================================
# 🏛️ 1. 全球 7 大核心指數全量陣列配置
# =========================================================================
INDEX_CONFIG = {
    "🇺🇸 納斯特 (3,500+隻)": {
        "ticker": "^IXIC", "fallback": "QQQ", "count": 3380,
        "color": "#38bdf8", "market": "US", "desc": "納斯達克全市場普通股與 ADR (全美科技與投機情緒總源頭)"
    },
    "🇺🇸 標指 500 (500隻)": {
        "ticker": "^GSPC", "fallback": "SPY", "count": 503,
        "color": "#00f2ff", "market": "US", "desc": "美國標普 500 家頂級核心巨頭 (機構定海神針)"
    },
    "🇺🇸 羅素 2000 (2,000隻)": {
        "ticker": "^RUT", "fallback": "IWM", "count": 2000,
        "color": "#f43f5e", "market": "US", "desc": "全美 2,000 隻中小盤股票全景庫 (市場風險偏好晴雨表)"
    },
    "🇺🇸 道指 (30隻)": {
        "ticker": "^DJI", "fallback": "DIA", "count": 30,
        "color": "#eab308", "market": "US", "desc": "美國 30 隻傳統超大型跨國藍籌旗艦"
    },
    "🇭🇰 恒指 (82隻)": {
        "ticker": "^HSI", "fallback": "2800.HK", "count": 82,
        "color": "#f97316", "market": "HK", "desc": "香港大盤權重藍籌 (恒生指數官方全成份)"
    },
    "🇭🇰 國指 (50隻)": {
        "ticker": "^HSCE", "fallback": "2828.HK", "count": 50,
        "color": "#a855f7", "market": "HK", "desc": "香港上市規模最大之 50 隻中資骨幹旗艦"
    },
    "🇭🇰 科指 (30隻)": {
        "ticker": "^HSTECH", "fallback": "3032.HK", "count": 30,
        "color": "#10b981", "market": "HK", "desc": "香港最大 30 隻科技網聯旗艦 (港股版納指 100)"
    }
}

# =========================================================================
# 📡 2. 指數數據抓取引擎
# =========================================================================
@st.cache_data(ttl=1800, show_spinner=False)
def fetch_index_price(ticker_sym, fallback_sym, period="3y"):
    try:
        t = yf.Ticker(ticker_sym)
        df = t.history(period=period, interval="1d", auto_adjust=True)
        if df.empty or len(df) < 30:
            t_fb = yf.Ticker(fallback_sym)
            df = t_fb.history(period=period, interval="1d", auto_adjust=True)
        if hasattr(df.index, 'tz') and df.index.tz is not None:
            df.index = df.index.tz_localize(None)
        return df.dropna(subset=['Close'])
    except Exception:
        return pd.DataFrame()

# =========================================================================
# ⚙️ 3. 五維真市寬數據引擎 (高速讀取 Parquet 緩存 ＋ 自動平滑降級)
# =========================================================================
def get_breadth_spectrum(idx_key: str, chart_dates: pd.DatetimeIndex):
    cache_path = os.path.join(os.path.dirname(__file__), "market_breadth_cache.parquet")
    
    # 1. 優先嘗試讀取後台 update_market_breadth.py 運算生成的真實數據
    if os.path.exists(cache_path):
        try:
            df_cache = pd.read_parquet(cache_path)
            cols = [f"{idx_key}__{m}" for m in ["10MA", "20MA", "50MA", "100MA", "200MA"]]
            if all(c in df_cache.columns for c in cols):
                sub_df = df_cache[cols].copy()
                sub_df.columns = ["10MA", "20MA", "50MA", "100MA", "200MA"]
                # 重新對齊當前圖表所請求的日期區間
                sub_df = sub_df.reindex(chart_dates).ffill().bfill()
                return sub_df
        except Exception:
            pass

    # 2. 自動防禦降級：若尚未生成 Parquet 快取，回傳常態基準值避免網頁報錯崩潰
    n = len(chart_dates)
    if n == 0:
        return pd.DataFrame(columns=["10MA", "20MA", "50MA", "100MA", "200MA"])
        
    default_val = 50.0
    return pd.DataFrame({
        "10MA": np.full(n, default_val),
        "20MA": np.full(n, default_val),
        "50MA": np.full(n, default_val),
        "100MA": np.full(n, default_val),
        "200MA": np.full(n, default_val)
    }, index=chart_dates)

# =========================================================================
# 📊 4. Gann 07 原裝雙層分離 VPVR 籌碼運算引擎 (近期 vs 歷史)
# =========================================================================
def compute_dual_vpvr(df_all: pd.DataFrame, df_window: pd.DataFrame, n_bins: int = 42):
    if df_window.empty or len(df_window) < 10:
        return None

    p_min = float(df_all['Low'].min())
    p_max = float(df_all['High'].max())
    if p_max <= p_min or np.isnan(p_min) or np.isnan(p_max):
        return None

    bin_edges = np.linspace(p_min, p_max, n_bins + 1)
    bin_width = bin_edges[1] - bin_edges[0]
    bin_centers = (bin_edges[:-1] + bin_edges[1:]) / 2.0

    def get_binned_volume(df_subset):
        buy_v = np.zeros(n_bins)
        sell_v = np.zeros(n_bins)
        for _, r in df_subset.iterrows():
            c, o, h, l = float(r['Close']), float(r['Open']), float(r['High']), float(r['Low'])
            v = float(r['Volume']) if ('Volume' in r and not pd.isna(r['Volume']) and r['Volume'] > 0) else 1000.0
            is_bull = (c >= o)
            i_l = max(0, min(n_bins - 1, int((l - p_min) / bin_width)))
            i_h = max(0, min(n_bins - 1, int((h - p_min) / bin_width)))
            n_cov = max(1, i_h - i_l + 1)
            v_p = v / float(n_cov)
            for b in range(i_l, i_h + 1):
                if is_bull: buy_v[b] += v_p
                else: sell_v[b] += v_p
        return buy_v, sell_v

    # 1. 歷史全景籌碼分佈
    hist_buy, hist_sell = get_binned_volume(df_all)
    hist_total = hist_buy + hist_sell
    hist_poc_idx = int(np.argmax(hist_total)) if len(hist_total) > 0 else 0
    hist_poc_price = float(bin_centers[hist_poc_idx])
    max_hist_vol = float(np.max(hist_total)) if (len(hist_total) > 0 and np.max(hist_total) > 0) else 1.0

    # 2. 近期趨勢籌碼分佈
    recent_buy, recent_sell = get_binned_volume(df_window)
    recent_total = recent_buy + recent_sell
    recent_poc_idx = int(np.argmax(recent_total)) if len(recent_total) > 0 else 0
    recent_poc_price = float(bin_centers[recent_poc_idx])
    max_rec_vol = float(np.max(recent_total)) if (len(recent_total) > 0 and np.max(recent_total) > 0) else 1.0

    return {
        'bin_centers': bin_centers,
        'hist_buy': hist_buy,
        'hist_sell': hist_sell,
        'max_hist_vol': max_hist_vol,
        'hist_poc': hist_poc_price,
        'recent_buy': recent_buy,
        'recent_sell': recent_sell,
        'max_rec_vol': max_rec_vol,
        'recent_poc': recent_poc_price
    }

# =========================================================================
# 🧱 5. Gann 07 雙層重貨柱疊加器 (自右側空白區延伸，絕不遮擋 K 線)
# =========================================================================
def add_gann07_vpvr_to_fig(fig, dual_vpvr, chart_right_edge_dt, last_candle_dt, locked_y_range, yaxis_target='y'):
    if not dual_vpvr:
        return

    future_gap = chart_right_edge_dt - last_candle_dt
    vpvr_max_width_delta = future_gap * 0.40
    b_centers = dual_vpvr['bin_centers']
    x_base = chart_right_edge_dt

    # 1. 歷史全景籌碼柱 (黃褐 / 紫色)
    h_buy = dual_vpvr['hist_buy']
    h_sell = dual_vpvr['hist_sell']
    m_h_vol = dual_vpvr['max_hist_vol']

    h_brown_x, h_brown_y = [], []
    h_purple_x, h_purple_y = [], []

    for i in range(len(b_centers)):
        y_lvl = b_centers[i]
        v_b = h_buy[i]
        v_s = h_sell[i]
        if (v_b + v_s) <= 0 or m_h_vol <= 0: continue

        b_span = (vpvr_max_width_delta * 0.88) * (v_b / m_h_vol)
        s_span = (vpvr_max_width_delta * 0.88) * (v_s / m_h_vol)

        x_b_end = x_base - b_span
        x_s_end = x_b_end - s_span

        h_brown_x.extend([x_base, x_b_end, None])
        h_brown_y.extend([y_lvl, y_lvl, None])
        h_purple_x.extend([x_b_end, x_s_end, None])
        h_purple_y.extend([y_lvl, y_lvl, None])

    fig.add_trace(go.Scatter(
        x=h_brown_x, y=h_brown_y, mode='lines',
        line=dict(color='rgba(217, 119, 6, 0.65)', width=6.0),
        name='歷史買盤', showlegend=False, hoverinfo='skip', yaxis=yaxis_target
    ))
    fig.add_trace(go.Scatter(
        x=h_purple_x, y=h_purple_y, mode='lines',
        line=dict(color='rgba(139, 92, 246, 0.65)', width=6.0),
        name='歷史賣盤', showlegend=False, hoverinfo='skip', yaxis=yaxis_target
    ))

    # 2. 近期趨勢籌碼柱 (青藍 / 粉紅)
    r_buy = dual_vpvr['recent_buy']
    r_sell = dual_vpvr['recent_sell']
    m_r_vol = dual_vpvr['max_rec_vol']

    r_teal_x, r_teal_y = [], []
    r_pink_x, r_pink_y = [], []

    for i in range(len(b_centers)):
        y_lvl = b_centers[i]
        v_b = r_buy[i]
        v_s = r_sell[i]
        if (v_b + v_s) <= 0 or m_r_vol <= 0: continue

        b_span = (vpvr_max_width_delta * 0.96) * (v_b / m_r_vol)
        s_span = (vpvr_max_width_delta * 0.96) * (v_s / m_r_vol)

        x_b_end = x_base - b_span
        x_s_end = x_b_end - s_span

        r_teal_x.extend([x_base, x_b_end, None])
        r_teal_y.extend([y_lvl, y_lvl, None])
        r_pink_x.extend([x_b_end, x_s_end, None])
        r_pink_y.extend([y_lvl, y_lvl, None])

    fig.add_trace(go.Scatter(
        x=r_teal_x, y=r_teal_y, mode='lines',
        line=dict(color='rgba(45, 212, 191, 0.90)', width=6.0),
        name='近期買盤', showlegend=False, hoverinfo='skip', yaxis=yaxis_target
    ))
    fig.add_trace(go.Scatter(
        x=r_pink_x, y=r_pink_y, mode='lines',
        line=dict(color='rgba(244, 63, 94, 0.85)', width=6.0),
        name='近期賣盤', showlegend=False, hoverinfo='skip', yaxis=yaxis_target
    ))

    # 3. 🟡 近期 POC (橙黃色虛線 ＋ 標籤)
    rec_poc = dual_vpvr['recent_poc']
    if locked_y_range[0] <= rec_poc <= locked_y_range[1]:
        fig.add_hline(
            y=rec_poc, line_dash="dash", line_color="#f59e0b", line_width=1.6,
            annotation_text=f"<b>近期 POC {rec_poc:,.1f}</b>",
            annotation_position="top right",
            annotation_font=dict(color="#ffffff", size=10, family="Arial Black"),
            annotation_bgcolor="#b45309", annotation_bordercolor="#f59e0b",
            yref=yaxis_target
        )

    # 4. 🟣 歷史 POC (紫色實線 ＋ 標籤)
    hist_poc = dual_vpvr['hist_poc']
    if locked_y_range[0] <= hist_poc <= locked_y_range[1]:
        fig.add_hline(
            y=hist_poc, line_dash="solid", line_color="#a855f7", line_width=1.8,
            annotation_text=f"<b>歷史 POC {hist_poc:,.1f}</b>",
            annotation_position="bottom right",
            annotation_font=dict(color="#ffffff", size=10, family="Arial Black"),
            annotation_bgcolor="#6b21a8", annotation_bordercolor="#a855f7",
            yref=yaxis_target
        )

# =========================================================================
# 🎨 6. 頁面核心渲染函數
# =========================================================================
def render_master_matrix_tab():
    st.markdown("<h1 style='color:#FFD700; font-size:38px; font-family:Arial Black; margin-bottom:4px;'>🛡️ 艙房 2b_新：全景市底大師指揮塔</h1>", unsafe_allow_html=True)
    st.markdown("<p style='color:#94a3b8; font-size:14px; margin-bottom:12px;'>全球 7 大全量指數成份股 ✕ 五維全週期真實市寬光譜 ✕ Gann 07 雙層重貨區 (近期 ✕ 歷史 VPVR)</p>", unsafe_allow_html=True)
    st.markdown("<hr style='border:2px solid #FFD700; margin:8px 0 16px 0;'>", unsafe_allow_html=True)

    # 🧭 第一層：7 顆頂部全景指數切換掣
    idx_list = list(INDEX_CONFIG.keys())
    if "p2b_master_idx" not in st.session_state:
        st.session_state["p2b_master_idx"] = idx_list[0]

    idx_choice = st.radio(
        "選擇戰區指數",
        options=idx_list,
        index=idx_list.index(st.session_state["p2b_master_idx"]),
        horizontal=True,
        key="p2b_radio_selector",
        label_visibility="collapsed"
    )
    st.session_state["p2b_master_idx"] = idx_choice
    selected_meta = INDEX_CONFIG[idx_choice]

    # 🎛️ 第二層：圖表控制工具列
    c_ctrl1, c_ctrl2, c_ctrl3 = st.columns([1.6, 3.4, 2.0])
    with c_ctrl1:
        timeframe = st.radio("K 線級別", ["日線圖 (Daily)", "週線圖 (Weekly)"], horizontal=True, key="sel_tf_pure")
    with c_ctrl2:
        st.markdown("<div style='font-size:13px; font-weight:bold; color:#00ff88; margin-bottom:2px;'>🎛️ 五維市寬光譜開關：</div>", unsafe_allow_html=True)
        cb1, cb2, cb3, cb4, cb5 = st.columns(5)
        with cb1: show_10 = st.checkbox("⚪ 10MA", value=True, key="cb_real_10")
        with cb2: show_20 = st.checkbox("🟡 20MA", value=True, key="cb_real_20")
        with cb3: show_50 = st.checkbox("🟢 50MA", value=True, key="cb_real_50")
        with cb4: show_100 = st.checkbox("🔵 100MA", value=True, key="cb_real_100")
        with cb5: show_200 = st.checkbox("🟣 200MA", value=True, key="cb_real_200")
    with c_ctrl3:
        zoom_bars = st.slider("🔭 K 線縮放拉桿 (控制樓層一 ✕ 樓層二)", min_value=30, max_value=250, value=120, step=5, key="zoom_slider_gann07")

    # 抓取指數完整長線歷史 (以計算歷史 POC)
    with st.spinner(f"正在全速對齊 {idx_choice} 數據矩陣..."):
        df_all = fetch_index_price(selected_meta["ticker"], selected_meta["fallback"], period="3y")

    if df_all.empty or len(df_all) < 30:
        st.error(f"⚠️ 無法取得 {idx_choice} 數據，請檢查網絡連線或稍後刷新重試。")
        return

    # 週線 / 日線聚合處理，並在全量數據上先行計算真實 MA50 與 MA200
    if "週線" in timeframe:
        df_all_used = df_all.resample('W-FRI').agg({
            'Open': 'first', 'High': 'max', 'Low': 'min', 'Close': 'last', 'Volume': 'sum'
        }).dropna()
        df_all_used['MA50'] = df_all_used['Close'].rolling(50, min_periods=10).mean()
        df_all_used['MA200'] = df_all_used['Close'].rolling(200, min_periods=20).mean()
        display_bars = max(20, zoom_bars // 2)
        df_display = df_all_used.tail(display_bars).copy()
    else:
        df_all_used = df_all.copy()
        df_all_used['MA50'] = df_all_used['Close'].rolling(50, min_periods=10).mean()
        df_all_used['MA200'] = df_all_used['Close'].rolling(200, min_periods=20).mean()
        df_display = df_all_used.tail(zoom_bars).copy()

    # 🌟 讀取 100% 真實五維市寬光譜數值 (0% ~ 100%)
    df_breadth = get_breadth_spectrum(idx_choice, df_display.index)

    last_b = df_breadth.iloc[-1]
    p10, p20, p50, p100, p200 = last_b["10MA"], last_b["20MA"], last_b["50MA"], last_b["100MA"], last_b["200MA"]

    # 計算 Gann 07 雙層 VPVR 籌碼 (近期 vs 歷史)
    dual_vpvr = compute_dual_vpvr(df_all_used, df_display, n_bins=42)

    # 建立時間軸未來空白走廊
    display_start_dt = pd.to_datetime(df_display.index[0])
    last_candle_dt = pd.to_datetime(df_display.index[-1])
    
    future_corridor_days = int(len(df_display) * 0.40) + 12
    mult = 7.0 if "週線" in timeframe else 1.45
    chart_right_edge_dt = last_candle_dt + pd.Timedelta(days=future_corridor_days * mult)

    # 自適應 Y 軸範圍計算 (上下留 3% 空間)
    p_low_limit = float(df_display['Low'].min()) * 0.97
    p_high_limit = float(df_display['High'].max()) * 1.03
    locked_y_range = [p_low_limit, p_high_limit]

    # 🏆 第三層：五維頂部 HUD 看板
    is_bull_trend = (p10 > p20 > p50 > p200)
    is_bear_trend = (p10 < p20 < p50 < p200)
    is_divergence = (df_display['Close'].iloc[-1] >= df_display['Close'].max() * 0.97) and (p200 < 40.0)

    if is_divergence:
        tag_status = "🚨 結構性背馳警戒 (指數高位，長線市寬虛火)"
        tag_color = "#ff3366"
    elif is_bull_trend:
        tag_status = "🚀 全波段多頭共振 (五維強勢順向推進)"
        tag_color = "#00ff88"
    elif is_bear_trend:
        tag_status = "🛑 全波段空頭共振 (全面破位防守防踩踏)"
        tag_color = "#ef4444"
    else:
        tag_status = "⚖️ 震盪分化過渡 (個股各行其道洗盤中)"
        tag_color = "#f59e0b"

    rec_poc_str = f"${dual_vpvr['recent_poc']:,.1f}" if dual_vpvr else "--"
    hist_poc_str = f"${dual_vpvr['hist_poc']:,.1f}" if dual_vpvr else "--"

    st.markdown(f"""
    <div style="background-color:#111827; padding:14px 20px; border-radius:12px; border:1.5px solid {selected_meta['color']}; margin:10px 0 18px 0;">
        <div style="display:flex; justify-content:space-between; align-items:center; flex-wrap:wrap; margin-bottom:12px;">
            <div style="font-size:16px; font-weight:bold; color:white;">
                {idx_choice} 實打實陣容：<span style="color:{selected_meta['color']};">{selected_meta['count']} 隻</span>
                <span style="font-size:12px; color:#f59e0b; margin-left:12px;">🟡 近期 POC: <b>{rec_poc_str}</b></span>
                <span style="font-size:12px; color:#a855f7; margin-left:12px;">🟣 歷史 POC: <b>{hist_poc_str}</b></span>
            </div>
            <div style="font-size:13px; font-weight:bold; color:{tag_color}; background:{tag_color}22; padding:3px 10px; border-radius:6px; border:1px solid {tag_color};">
                {tag_status}
            </div>
        </div>
        <div style="display:grid; grid-template-columns: repeat(5, 1fr); gap:10px; text-align:center;">
            <div style="background:#1f293d; padding:8px; border-radius:8px;">
                <div style="font-size:11px; color:#cbd5e1;">⚪ 10MA (刺客情緒)</div>
                <div style="font-size:22px; font-weight:900; color:#f1f5f9;">{p10:.1f}%</div>
            </div>
            <div style="background:#1f293d; padding:8px; border-radius:8px;">
                <div style="font-size:11px; color:#cbd5e1;">🟡 20MA (月度防守)</div>
                <div style="font-size:22px; font-weight:900; color:#facc15;">{p20:.1f}%</div>
            </div>
            <div style="background:#1f293d; padding:8px; border-radius:8px; border:1.5px solid #22c55e;">
                <div style="font-size:11px; color:#22c55e; font-weight:bold;">🟢 50MA (真・市底)</div>
                <div style="font-size:24px; font-weight:900; color:#00ff88;">{p50:.1f}%</div>
            </div>
            <div style="background:#1f293d; padding:8px; border-radius:8px;">
                <div style="font-size:11px; color:#cbd5e1;">🔵 100MA (半年線)</div>
                <div style="font-size:22px; font-weight:900; color:#06b6d4;">{p100:.1f}%</div>
            </div>
            <div style="background:#1f293d; padding:8px; border-radius:8px; border:1.5px solid #e11d48;">
                <div style="font-size:11px; color:#fda4af; font-weight:bold;">🟣 200MA (牛熊線)</div>
                <div style="font-size:24px; font-weight:900; color:#ff4d8d;">{p200:.1f}%</div>
            </div>
        </div>
    </div>
    """, unsafe_allow_html=True)

    # =========================================================================
    # 🏛️ 樓層 1：價格形態 ＋ 右手邊 Gann 07 雙層重貨區
    # =========================================================================
    st.markdown(f"<h3 style='color:#f8fafc; font-size:18px; margin:16px 0 6px 0;'>🏛️ 樓層 1：{idx_choice} 價格形態 ＋ 右側 Gann 07 雙層重貨區 (十字貫穿)</h3>", unsafe_allow_html=True)
    
    fig1 = go.Figure()
    
    # 1. K 線圖
    fig1.add_trace(go.Candlestick(
        x=df_display.index,
        open=df_display['Open'], high=df_display['High'],
        low=df_display['Low'], close=df_display['Close'],
        name='指數 K 線',
        increasing_line_color='#00ff88', decreasing_line_color='#ff3366',
        increasing_fillcolor='#00ff88', decreasing_fillcolor='#ff3366',
        showlegend=False
    ))
    
    # 2. 均線 (50MA 綠虛線 ＋ 200MA 白線牛熊線)
    fig1.add_trace(go.Scatter(
        x=df_display.index, y=df_display['MA50'],
        mode='lines', line=dict(color='#00ff88', width=2.2, dash='dash'),
        name='<b style="color:#ffffff;">指數 50MA (綠虛線)</b>',
        hovertemplate='50MA: %{y:,.1f}<extra></extra>'
    ))
    fig1.add_trace(go.Scatter(
        x=df_display.index, y=df_display['MA200'],
        mode='lines', line=dict(color='#ffffff', width=2.6),
        name='<b style="color:#ffffff;">指數 200MA (白線牛熊線)</b>',
        hovertemplate='200MA: %{y:,.1f}<extra></extra>'
    ))

    # 3. 疊加 Gann 07 原版雙層重貨區
    add_gann07_vpvr_to_fig(
        fig=fig1,
        dual_vpvr=dual_vpvr,
        chart_right_edge_dt=chart_right_edge_dt,
        last_candle_dt=last_candle_dt,
        locked_y_range=locked_y_range,
        yaxis_target='y'
    )

    fig1.update_layout(
        template='plotly_dark',
        paper_bgcolor='#0e1117',
        plot_bgcolor='#111827',
        height=620,
        margin=dict(l=40, r=70, t=25, b=25),
        hovermode='x unified',
        showlegend=True,
        legend=dict(
            orientation="h", yanchor="bottom", y=1.01, xanchor="right", x=1.0,
            font=dict(color="#ffffff", size=13)
        ),
        xaxis=dict(
            range=[display_start_dt, chart_right_edge_dt],
            rangeslider=dict(visible=False),
            showgrid=True, gridcolor='#2e3d52',
            spikemode='across', spikesnap='cursor', spikedash='dash',
            spikecolor='#ffffff', spikethickness=1.5
        ),
        yaxis=dict(
            title="指數點位",
            side="right",
            range=locked_y_range,
            autorange=False,
            gridcolor='#2e3d52',
            spikemode='across', spikesnap='cursor', spikedash='dash',
            spikecolor='#ffffff', spikethickness=1.5
        )
    )
    st.plotly_chart(fig1, use_container_width=True, key="fig_matrix_fl1_gann07_vpvr")

    # =========================================================================
    # 🌊 樓層 2：雙軸大圖 ＋ 右手邊 Gann 07 雙層重貨區
    # =========================================================================
    st.markdown(f"<h3 style='color:#38bdf8; font-size:18px; margin:22px 0 6px 0;'>🌊 樓層 2：雙軸對比 —— 五維市寬滲透率 (%) ＋ 實體陰陽燭 ＋ 右側雙層重貨區 (十字貫穿)</h3>", unsafe_allow_html=True)
    
    fig2 = go.Figure()

    # 1. 左軸 (yaxis='y')：100% 實體陰陽燭
    fig2.add_trace(go.Candlestick(
        x=df_display.index,
        open=df_display['Open'], high=df_display['High'],
        low=df_display['Low'], close=df_display['Close'],
        name='實體陰陽燭',
        increasing_line_color='#00ff88', decreasing_line_color='#ff3366',
        increasing_fillcolor='#00ff88', decreasing_fillcolor='#ff3366',
        yaxis='y',
        showlegend=False
    ))

    # 2. 疊加 Gann 07 雙層重貨區
    add_gann07_vpvr_to_fig(
        fig=fig2,
        dual_vpvr=dual_vpvr,
        chart_right_edge_dt=chart_right_edge_dt,
        last_candle_dt=last_candle_dt,
        locked_y_range=locked_y_range,
        yaxis_target='y'
    )

    # 3. 右軸 (yaxis='y2')：五維市寬光譜線
    if show_10:
        fig2.add_trace(go.Scatter(
            x=df_breadth.index, y=df_breadth['10MA'],
            mode='lines', line=dict(color='#ffffff', width=2.4, dash='dot'),
            name='<b style="color:#ffffff;">⚪ 10MA (刺客)</b>',
            yaxis='y2',
            hovertemplate='10MA 市寬: %{y:.1f}%<extra></extra>'
        ))

    if show_20:
        fig2.add_trace(go.Scatter(
            x=df_breadth.index, y=df_breadth['20MA'],
            mode='lines', line=dict(color='#facc15', width=2.8),
            name='<b style="color:#ffffff;">🟡 20MA (月線)</b>',
            yaxis='y2',
            hovertemplate='20MA 市寬: %{y:.1f}%<extra></extra>'
        ))

    if show_50:
        fig2.add_trace(go.Scatter(
            x=df_breadth.index, y=df_breadth['50MA'],
            mode='lines', line=dict(color='#00ff88', width=3.8),
            name='<b style="color:#ffffff;">🟢 50MA (真市底)</b>',
            yaxis='y2',
            hovertemplate='50MA 市寬: %{y:.1f}%<extra></extra>'
        ))

    if show_100:
        fig2.add_trace(go.Scatter(
            x=df_breadth.index, y=df_breadth['100MA'],
            mode='lines', line=dict(color='#06b6d4', width=3.0),
            name='<b style="color:#ffffff;">🔵 100MA (半年)</b>',
            yaxis='y2',
            hovertemplate='100MA 市寬: %{y:.1f}%<extra></extra>'
        ))

    if show_200:
        fig2.add_trace(go.Scatter(
            x=df_breadth.index, y=df_breadth['200MA'],
            mode='lines', line=dict(color='#ff007f', width=4.2),
            name='<b style="color:#ffffff;">🟣 200MA (牛熊·電視同款)</b>',
            yaxis='y2',
            hovertemplate='200MA 市寬: %{y:.1f}%<extra></extra>'
        ))

    # 警戒標尺線
    fig2.add_hline(y=80.0, line_dash="dash", line_color="#ef4444", line_width=1.2, yref='y2', annotation_text="80% 超買", annotation_font_size=11)
    fig2.add_hline(y=50.0, line_dash="solid", line_color="rgba(255, 255, 255, 0.4)", line_width=1.2, yref='y2', annotation_text="50% 中軸", annotation_font_size=11)
    fig2.add_hline(y=30.0, line_dash="dash", line_color="#06b6d4", line_width=1.2, yref='y2', annotation_text="30% 超賣", annotation_font_size=11)
    fig2.add_hline(y=20.0, line_dash="dot", line_color="#facc15", line_width=1.2, yref='y2', annotation_text="20% 底背馳", annotation_font_size=11)

    fig2.update_layout(
        template='plotly_dark',
        paper_bgcolor='#0e1117',
        plot_bgcolor='#111827',
        height=640,
        margin=dict(l=40, r=70, t=25, b=25),
        hovermode='x unified',
        showlegend=True,
        legend=dict(
            orientation="h", yanchor="bottom", y=1.01, xanchor="right", x=1.0,
            font=dict(color="#ffffff", size=13, family="Arial")
        ),
        xaxis=dict(
            range=[display_start_dt, chart_right_edge_dt],
            rangeslider=dict(visible=False),
            showgrid=True, gridcolor='#2e3d52',
            spikemode='across', spikesnap='cursor', spikedash='dash',
            spikecolor='#ffffff', spikethickness=1.5
        ),
        yaxis=dict(
            title="指數陰陽燭點位",
            side="left",
            range=locked_y_range,
            autorange=False,
            showgrid=False,
            tickfont=dict(color='#cbd5e1'),
            spikemode='across', spikesnap='cursor', spikedash='dash',
            spikecolor='#ffffff', spikethickness=1.5
        ),
        yaxis2=dict(
            title="五維市寬百分比 %",
            side="right",
            overlaying="y",
            range=[0, 105],
            autorange=False,
            dtick=20,
            ticksuffix="%",
            gridcolor='#2e3d52'
        )
    )
    st.plotly_chart(fig2, use_container_width=True, key="fig_matrix_fl2_gann07_vpvr")

    # =========================================================================
    # 📊 樓層 3：大盤成交量獨立大圖 (350px)
    # =========================================================================
    st.markdown(f"<h3 style='color:#a855f7; font-size:18px; margin:22px 0 6px 0;'>📊 樓層 3：{idx_choice} 大盤成交量 (Volume 獨立大圖)</h3>", unsafe_allow_html=True)
    
    vol_colors = ['#00ff88' if df_display['Close'].iloc[i] >= df_display['Open'].iloc[i] else '#ff3366' for i in range(len(df_display))]
    fig3 = go.Figure()
    fig3.add_trace(go.Bar(
        x=df_display.index, y=df_display['Volume'],
        marker_color=vol_colors, name='大盤成交量', showlegend=False,
        hovertemplate='成交量: %{y:,.0f}<extra></extra>'
    ))
    fig3.update_xaxes(
        range=[display_start_dt, chart_right_edge_dt],
        rangeslider=dict(visible=False),
        showgrid=True, gridcolor='#2e3d52',
        spikemode='across', spikesnap='cursor', spikedash='dash',
        spikecolor='#ffffff', spikethickness=1.5
    )
    fig3.update_yaxes(title_text="成交量 (Volume)", side="right", gridcolor='#2e3d52')
    fig3.update_layout(
        template='plotly_dark',
        paper_bgcolor='#0e1117',
        plot_bgcolor='#111827',
        height=350,
        margin=dict(l=40, r=70, t=25, b=25),
        hovermode='x unified'
    )
    st.plotly_chart(fig3, use_container_width=True, key="fig_matrix_fl3_vol")

def render_page_2b_master_matrix():
    render_master_matrix_tab()

if __name__ == "__main__":
    render_page_2b_master_matrix()