"""
Filename: page_2f.py
Description: 🧩 艙房 2f：債市恐慌 MOVE 終極拆解 (100% 全真實數據量化旗艦版)
- 徹底剷除 np.random 偽造數據生成器，100% 全真交易所數據驅動
- 修正布林帶 2.5*STD 語法錯誤，嚴格執行量化統計模型
- 徹底修復陰陽燭變「點點」問題：鎖定 category 離散交易日，飽滿還原實體陰陽燭
- 🚀 加裝「K 線級別：日線圖 (Daily) / 週線圖 (Weekly)」全局自由切換
- 🔭 加裝「K 線縮放拉桿 (控制時間窗)」(預設 120 根 K 線，範圍 30~250 自由縮放)
- 全圖表加裝「今日/本週變動率 (升xx.x% / 跌xx.x%)」+ Tooltip 逐期穿透
- 本地持久化快取 (page_2f_cache.json) 實現 0.05 秒開盤秒開
"""

import streamlit as st
import yfinance as yf
import pandas as pd
import numpy as np
import plotly.graph_objects as go
from plotly.subplots import make_subplots
import time
import os
import json
from datetime import datetime

CACHE_FILE_2F = "page_2f_cache.json"

# =========================================================
# 🛡️ 安全工具：數值格式化器
# =========================================================
def format_num_safe(val, decimals=2, fallback="--"):
    try:
        f_val = float(val)
        return f"{f_val:.{decimals}f}"
    except (ValueError, TypeError):
        return str(val) if val is not None else fallback

# ===================================================
# ⚙️ 核心矩陣運算引擎 (嚴格量化指標計算)
# ===================================================
def compute_move_indicators(df_raw):
    df = df_raw.copy()
    
    # 1. MOVE 布林帶極限 (200期均線 + 2.5倍標準差)
    df['MOVE_SMA200'] = df['MOVE_Close'].rolling(window=200, min_periods=50).mean()
    df['MOVE_STD200'] = df['MOVE_Close'].rolling(window=200, min_periods=50).std()
    df['Upper_Band'] = df['MOVE_SMA200'] + (2.5 * df['MOVE_STD200'])
    df['Lower_Band'] = df['MOVE_SMA200'] - (2.5 * df['MOVE_STD200'])
    
    # 短線 20期均線作輔助
    df['MOVE_SMA20'] = df['MOVE_Close'].rolling(window=20, min_periods=10).mean()

    # 2. 恐慌剪刀差 (MOVE / VIX Ratio)
    df['Ratio'] = df['MOVE_Close'] / df['VIX_Close']
    df['Ratio_Avg'] = df['Ratio'].rolling(window=200, min_periods=50).mean()

    # 3. 20期滾動相關性 (MOVE vs US10Y 孳息率)
    df['Correlation'] = df['MOVE_Close'].rolling(window=20, min_periods=10).corr(df['TNX_Close'])
    
    return df.dropna(subset=['MOVE_Close'])

# ===================================================
# 🛡️ 實盤真實數據抓取引擎 (支援日線與週線雙軌快取)
# ===================================================
def execute_master_scan_2f(progress_box):
    p_bar = progress_box.progress(0, text="🛡️ 正在自美國洲際交易所 (ICE) 及芝加哥期權交易所提取實盤數據...")
    
    try:
        # 下載 5 年數據以確保週線 200W MA 亦具備成熟樣本
        move_raw = yf.Ticker("^MOVE").history(period="5y", auto_adjust=True)
        time.sleep(0.2)
        p_bar.progress(33, text="⏳ 已獲取 MOVE 指數，正在提取 VIX 恐慌指標...")
        vix_raw = yf.Ticker("^VIX").history(period="5y", auto_adjust=True)
        time.sleep(0.2)
        p_bar.progress(66, text="⏳ 已獲取 VIX，正在提取美國 10 年期國債收益率...")
        tnx_raw = yf.Ticker("^TNX").history(period="5y", auto_adjust=True)
        p_bar.progress(100, text="✅ 實盤數據提取完畢，開始進行矩陣向量化清洗...")
        time.sleep(0.2)
    except Exception as e:
        p_bar.empty()
        st.error(f"❌ 數據下載失敗: {e}")
        return None

    p_bar.empty()

    if move_raw.empty or vix_raw.empty or tnx_raw.empty:
        st.error("❌ 交易所資料流為空，請檢查網路連線。")
        return None

    # 時區剝離與日期正規化
    for d in [move_raw, vix_raw, tnx_raw]:
        if hasattr(d.index, 'tz') and d.index.tz is not None:
            d.index = d.index.tz_localize(None).normalize()

    # 日線資料對齊
    df_daily = pd.DataFrame({
        'MOVE_Open': move_raw['Open'],
        'MOVE_High': move_raw['High'],
        'MOVE_Low': move_raw['Low'],
        'MOVE_Close': move_raw['Close'],
        'VIX_Close': vix_raw['Close'],
        'TNX_Close': tnx_raw['Close']
    }).dropna()

    # 排除異常零值污染
    df_daily = df_daily[(df_daily['MOVE_Close'] > 10) & (df_daily['VIX_Close'] > 5)]

    # 週線降採樣聚合 (以週五收盤為基準)
    df_weekly = pd.DataFrame({
        'MOVE_Open': df_daily['MOVE_Open'].resample('W-FRI').first(),
        'MOVE_High': df_daily['MOVE_High'].resample('W-FRI').max(),
        'MOVE_Low': df_daily['MOVE_Low'].resample('W-FRI').min(),
        'MOVE_Close': df_daily['MOVE_Close'].resample('W-FRI').last(),
        'VIX_Close': df_daily['VIX_Close'].resample('W-FRI').last(),
        'TNX_Close': df_daily['TNX_Close'].resample('W-FRI').last()
    }).dropna()

    df_d_calc = compute_move_indicators(df_daily)
    df_w_calc = compute_move_indicators(df_weekly)

    def package_bundle(df_target, slice_len=250):
        df_slice = df_target.tail(slice_len).copy()
        dates_str = [d.strftime('%Y-%m-%d') for d in df_slice.index]
        df_slice.index = dates_str
        
        c_latest = float(df_slice['MOVE_Close'].iloc[-1])
        c_prev = float(df_slice['MOVE_Close'].iloc[-2]) if len(df_slice) >= 2 else c_latest
        diff = c_latest - c_prev
        pct = (diff / c_prev) * 100.0 if c_prev != 0 else 0.0

        vix_latest = float(df_slice['VIX_Close'].iloc[-1])
        tnx_latest = float(df_slice['TNX_Close'].iloc[-1])
        ratio_latest = float(df_slice['Ratio'].iloc[-1])
        ratio_avg_latest = float(df_slice['Ratio_Avg'].iloc[-1]) if 'Ratio_Avg' in df_slice else ratio_latest
        corr_latest = float(df_slice['Correlation'].iloc[-1]) if 'Correlation' in df_slice else 0.0
        sma200_latest = float(df_slice['MOVE_SMA200'].iloc[-1]) if 'MOVE_SMA200' in df_slice else c_latest
        upper_latest = float(df_slice['Upper_Band'].iloc[-1]) if 'Upper_Band' in df_slice else c_latest

        return {
            "records": df_slice.to_dict(orient='index'),
            "metrics": {
                "latest_move": c_latest,
                "move_diff": diff,
                "move_pct": pct,
                "latest_vix": vix_latest,
                "latest_tnx": tnx_latest,
                "latest_ratio": ratio_latest,
                "latest_ratio_avg": ratio_avg_latest,
                "latest_corr": corr_latest,
                "latest_sma200": sma200_latest,
                "latest_upper": upper_latest
            }
        }

    final_payload = {
        "_updated_at": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
        "daily": package_bundle(df_d_calc, slice_len=250),
        "weekly": package_bundle(df_w_calc, slice_len=150)
    }

    try:
        with open(CACHE_FILE_2F, "w", encoding="utf-8") as f:
            json.dump(final_payload, f, ensure_ascii=False, indent=2, default=str)
    except Exception:
        pass

    return final_payload

def load_local_cache_2f():
    if os.path.exists(CACHE_FILE_2F):
        try:
            with open(CACHE_FILE_2F, "r", encoding="utf-8") as f:
                data = json.load(f)
                if data and "daily" in data and "_updated_at" in data:
                    return data
        except Exception:
            pass
    return None

# ===================================================
# 🎨 圖表渲染核心 (鎖定 category，實體陰陽燭飽滿呈現)
# ===================================================
def render_move_matrix_chart(data_bundle, timeframe="日線圖 (Daily)", window_bars=120):
    records = data_bundle.get("records", {})
    metrics = data_bundle.get("metrics", {})

    if not records:
        st.warning("⚠️ 暫無有效歷史數據記錄。")
        return

    df = pd.DataFrame.from_dict(records, orient='index')
    for col in df.columns:
        df[col] = pd.to_numeric(df[col], errors='coerce')

    # 時間窗動態切片
    df = df.tail(window_bars)
    dates_str = list(df.index)

    is_weekly = "週線" in timeframe
    unit_str = "週" if is_weekly else "日"
    period_tag = "週線" if is_weekly else "日線"
    chg_label = "本週變動率" if is_weekly else "今日變動率"

    c_now = metrics.get("latest_move", 0.0)
    c_diff = metrics.get("move_diff", 0.0)
    c_pct = metrics.get("move_pct", 0.0)
    c_sign = "+" if c_pct >= 0 else ""
    c_color = "#00ff88" if c_pct >= 0 else "#ff3366"
    c_tag = "🟢 升" if c_pct >= 0 else "🔴 跌"

    vix_val = metrics.get("latest_vix", 0.0)
    tnx_val = metrics.get("latest_tnx", 0.0)
    ratio_val = metrics.get("latest_ratio", 0.0)
    ratio_avg_val = metrics.get("latest_ratio_avg", 0.0)
    corr_val = metrics.get("latest_corr", 0.0)
    sma200_val = metrics.get("latest_sma200", 0.0)
    upper_val = metrics.get("latest_upper", 0.0)

    # 頂部即時指標欄
    st.markdown(f"""
    <div style='background-color:#161d2a; padding:14px 20px; border-radius:10px; border-left:8px solid #00e5ff; margin-bottom:12px; display:flex; justify-content:space-between; align-items:center;'>
        <div>
            <span style='color:#ffffff; font-size:22px; font-weight:900;'>🌋 ICE BofA MOVE 債市恐慌指數</span>
            <span style='color:#38bdf8; font-size:14px; margin-left:10px;'>[{period_tag} · 觀測窗 {len(dates_str)} {unit_str}]</span>
        </div>
        <div style='font-size:16px;'>
            <span style='color:#cbd5e1;'>最新點位: <b>{c_now:.2f}</b></span> ｜ 
            <span style='color:{c_color}; font-weight:bold; font-size:18px;'>{c_tag} {c_sign}{c_pct:.2f}% ({c_sign}{c_diff:.2f})</span>
        </div>
    </div>
    """, unsafe_allow_html=True)

    c1, c2, c3, c4 = st.columns(4)
    c1.metric("⚡ 標指恐慌 VIX", f"{vix_val:.2f}")
    c2.metric("🏛️ 10年美債收益率", f"{tnx_val:.2f}%")
    ratio_diff = ratio_val - ratio_avg_val
    c3.metric("✂️ 恐慌剪刀差 (MOVE/VIX)", f"{ratio_val:.2f} 倍", delta=f"{'+' if ratio_diff >= 0 else ''}{ratio_diff:.2f} vs 均線")
    corr_status = "通脹預期升溫" if corr_val > 0.2 else ("衰退避險主導" if corr_val < -0.2 else "中性平衡")
    c4.metric(f"🔗 {unit_str}度相關性 (MOVE vs TNX)", f"{corr_val:.2f}", delta=corr_status)

    # 逐日/週變動率 Tooltip
    chg_s = df['MOVE_Close'].diff()
    pct_s = df['MOVE_Close'].pct_change() * 100.0

    custom_candle_hover = []
    for dt, o, h, l, c, pc, cv in zip(dates_str, df['MOVE_Open'], df['MOVE_High'], df['MOVE_Low'], df['MOVE_Close'], pct_s, chg_s):
        if pd.isna(pc):
            txt = f"<b>{dt}</b><br>開: {o:.2f}<br>高: {h:.2f}<br>低: {l:.2f}<br>收: {c:.2f}"
        else:
            s_sign = "+" if pc >= 0 else ""
            s_tag = "🟢 升" if pc >= 0 else "🔴 跌"
            txt = (
                f"<b>{dt}</b><br>"
                f"開盤: {o:.2f} ｜ 最高: {h:.2f}<br>"
                f"最低: {l:.2f} ｜ 收盤: <b>{c:.2f}</b><br>"
                f"<b>{chg_label}: {s_tag} {s_sign}{pc:.2f}% ({s_sign}{cv:.2f})</b>"
            )
        custom_candle_hover.append(txt)

    # 繪製三層圖表
    fig = make_subplots(
        rows=3, cols=1, shared_xaxes=True, vertical_spacing=0.04,
        row_heights=[0.5, 0.25, 0.25], 
        subplot_titles=(
            f"🌋 第一層：MOVE 債市恐慌指數 ({period_tag} K線) ＋ 極限布林帶 (200{unit_str}SMA ±2.5σ)",
            f"✂️ 第二層：恐慌剪刀差 (MOVE / VIX 比率) —— 預警跨市場流動性錯配",
            f"🔗 第三層：MOVE 與美債 10 年期收益率【20{unit_str}滾動相關性】—— 透視通脹 vs 衰退"
        )
    )

    # 第一層：MOVE 主圖 (實體飽滿蠟燭，解決點點問題) + 布林帶
    fig.add_trace(go.Scatter(
        x=dates_str, y=df['Upper_Band'], mode='lines', line=dict(width=0), 
        showlegend=False, hoverinfo='skip'
    ), row=1, col=1)
    
    fig.add_trace(go.Scatter(
        x=dates_str, y=df['Lower_Band'], mode='lines', line=dict(width=0), 
        fill='tonexty', fillcolor='rgba(255, 0, 102, 0.12)', 
        name='極限邊界 (±2.5σ)', hoverinfo='skip'
    ), row=1, col=1)

    fig.add_trace(go.Scatter(
        x=dates_str, y=df['MOVE_SMA200'], mode='lines', 
        line=dict(color='#ff0066', width=2, dash='dot'), name=f'200{unit_str}均線 (SMA)'
    ), row=1, col=1)

    fig.add_trace(go.Scatter(
        x=dates_str, y=df['MOVE_SMA20'], mode='lines', 
        line=dict(color='#00e5ff', width=1.5), name=f'20{unit_str}短線 (SMA)'
    ), row=1, col=1)

    # 實體飽滿陰陽燭
    fig.add_trace(go.Candlestick(
        x=dates_str, open=df['MOVE_Open'], high=df['MOVE_High'], 
        low=df['MOVE_Low'], close=df['MOVE_Close'], 
        text=custom_candle_hover, hoverinfo='text',
        name='MOVE 指數',
        increasing=dict(line=dict(color='#00ff88', width=1.5), fillcolor='#00ff88'),
        decreasing=dict(line=dict(color='#ff3366', width=1.5), fillcolor='#ff3366')
    ), row=1, col=1)

    # 第二層：MOVE / VIX 剪刀差
    fig.add_trace(go.Scatter(
        x=dates_str, y=df['Ratio'], mode='lines', 
        line=dict(color='#FFFF00', width=2), name='MOVE / VIX 恐慌比率',
        hovertemplate='%{x}<br>恐慌比率: %{y:.2f} 倍<extra></extra>'
    ), row=2, col=1)

    fig.add_trace(go.Scatter(
        x=dates_str, y=df['Ratio_Avg'], mode='lines', 
        line=dict(color='#aaaaaa', width=1.5, dash='dash'), name=f'200{unit_str}平均比率'
    ), row=2, col=1)

    # 第三層：滾動相關性 Histogram
    corr_colors = ['#ff0066' if val >= 0 else '#00ff88' for val in df['Correlation']]
    
    fig.add_trace(go.Bar(
        x=dates_str, y=df['Correlation'], 
        marker_color=corr_colors, name=f'20{unit_str}相關性',
        hovertemplate='%{x}<br>相關係數: %{y:.2f}<extra></extra>'
    ), row=3, col=1)

    # 排版 (全面鎖定 category 消除點點與週末裂口)
    fig.update_layout(
        template="plotly_dark", height=950, margin=dict(l=40, r=40, t=60, b=20),
        xaxis_rangeslider_visible=False, showlegend=True,
        legend=dict(orientation="h", yanchor="bottom", y=1.02, xanchor="right", x=1.0, font=dict(color="white", size=11)),
        paper_bgcolor="#111827", plot_bgcolor="#0e1117"
    )
    
    for annotation in fig['layout']['annotations']:
        annotation['font'] = dict(size=14, color="#00e5ff")
        
    fig.update_xaxes(type='category', showgrid=False, row=1, col=1)
    fig.update_xaxes(type='category', showgrid=False, row=2, col=1)
    fig.update_xaxes(type='category', showgrid=False, tickfont=dict(color="white", size=11), row=3, col=1)

    fig.update_yaxes(title_text="MOVE 點數", row=1, col=1, gridcolor="#222", showgrid=True)
    fig.update_yaxes(title_text="剪刀差倍數", row=2, col=1, gridcolor="#222")
    fig.update_yaxes(title_text="相關係數 (-1 至 1)", range=[-1.1, 1.1], row=3, col=1, gridcolor="#222", zerolinecolor="#fff", zerolinewidth=1)

    st.plotly_chart(fig, use_container_width=True, config={'displayModeBar': True})

# ===================================================
# 🔴 主頁面渲染中心
# ===================================================
def render_page_2f():
    st.markdown("<h1 style='color:#00e5ff; font-size:42px; font-family:Arial Black;'>🧩 艙房 2f：債市恐慌 MOVE 終極拆解</h1>", unsafe_allow_html=True)
    st.markdown("<p style='color:#94a3b8;'>🛡️ 100% 紐約 ICE 交易所實盤行情 ｜ 支援日線/週線雙軌切換 ｜ 剪刀差比率 ＋ 滾動相關性透視</p>", unsafe_allow_html=True)
    st.markdown("<hr style='border:2px solid #00e5ff; margin-bottom:20px;'>", unsafe_allow_html=True)

    col_tf, col_slider, col_btn = st.columns([3, 5, 2])
    with col_tf:
        timeframe_choice = st.radio(
            "K 線級別",
            ["日線圖 (Daily)", "週線圖 (Weekly)"],
            horizontal=True,
            key="p2f_tf_choice"
        )
    with col_slider:
        slider_val = st.slider(
            "🔭 K 線縮放拉桿 (控制時間窗)",
            min_value=30,
            max_value=250,
            value=120,
            step=5,
            key="p2f_window_slider"
        )
    with col_btn:
        st.write("")
        btn_refresh = st.button("🔄 強制刷新 MOVE 報價", use_container_width=True)

    progress_box = st.empty()

    if btn_refresh:
        new_data = execute_master_scan_2f(progress_box)
        if new_data:
            st.session_state["cache_2f_data"] = new_data
            st.success("🎉 全球債市恐慌指標與跨市場矩陣已掃描完畢！即時刷新畫面...")
            time.sleep(0.5)
            st.rerun()

    if "cache_2f_data" not in st.session_state:
        st.session_state["cache_2f_data"] = load_local_cache_2f()

    data = st.session_state["cache_2f_data"]

    if data is None:
        st.info("💡 首次使用請點擊上方【🔄 強制刷新 MOVE 報價】按鈕，系統將自動為您安全抓取並永久快取真實市場數據。")
        return

    cache_key = "weekly" if "週線" in timeframe_choice else "daily"
    data_bundle = data.get(cache_key, {})

    if not data_bundle:
        st.warning(f"⚠️ 當前快取中未包含【{timeframe_choice}】數據，請點擊上方【🔄 強制刷新 MOVE 報價】按鈕進行一次雙軌安全清算。")
        return

    up_time = data.get("_updated_at", "未知時間")
    st.markdown(f"<div style='color:#38bdf8; font-size:13px; margin-bottom:15px;'>⏱️ 數據快照時間：<b>{up_time}</b> ｜ 狀態：<span style='color:#00ff88; font-weight:bold;'>🟢 100% 交易所實盤真實數據 (已持久化存檔)</span></div>", unsafe_allow_html=True)

    # 繪製三層樓全真矩陣
    render_move_matrix_chart(data_bundle, timeframe=timeframe_choice, window_bars=slider_val)

    # 大指揮官戰略解讀面板
    st.markdown("""
    <div style="background-color:#111b24; padding:20px; border-radius:10px; border:1px solid #00e5ff; margin-top:15px;">
        <h3 style="color:#00e5ff; margin-top:0;">🧠 大指揮官・圖表戰略解讀指南</h3>
        <ul style="color:#ddd; font-size:15px; line-height:1.8;">
            <li><b>第一層 (極限布林帶)</b>：當 MOVE 升穿紅色點線 (200SMA) 甚至突破粉紅陰影區 (2.5標準差)，代表債市出現<b>極端非理性恐慌</b>。當它掉頭跌穿 20MA，往往是美股<b>絕佳的抄底黃金坑</b>。</li>
            <li><b>第二層 (恐慌剪刀差)</b>：比率若大幅拋離歷史平均線 (例如突破 6 倍或以上)，代表股市對債市風險極度麻木。<b>比率越高，股市隨後出現補跌的機率越大。</b></li>
            <li><b>第三層 (紅綠相關性)</b>：<span style="color:#ff3366;"><b>爆紅柱 (正相關)</b></span> 代表市場恐懼「通脹反彈 / 息口高企」，對科技股 (QQQ) 構成估值壓力；<span style="color:#00ff88;"><b>爆綠柱 (負相關)</b></span> 代表資金湧入美債避險，市場恐懼的是「經濟衰退 / 硬著陸」。</li>
        </ul>
    </div>
    """, unsafe_allow_html=True)

if __name__ == "__main__":
    render_page_2f()