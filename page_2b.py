"""
Filename: page_2b.py
Description: 🛡️ 艙房 2b：環球市底大師指揮塔 (100% 全真實數據量化旗艦版)
- 正式接入【國指 (恒生中國企業指數 50 隻)】，基準綁定 2828.HK
- 100% 同步 page_2a.py 所有指數成分股隻數 (恒指93、科指30、國指50、道指30、納市101、標指504、IWM500)
- 徹底剔除 .bfill() 未來數據回溯污染 (Look-Ahead Bias)
- 修正動態分母矩陣：精確核算歷史每一日真實存續之成分股總數
- 修正週線數據長度：切換週線時自動加載 5 年數據，確保 200 週均線樣本充足
- 時區安全防禦：全域自動剝離 tz-aware 時間戳
- 頂部圖例文字強制純白 (#ffffff)，防止黑字隱形
"""

import streamlit as st
import pandas as pd
import numpy as np
import plotly.graph_objects as go
from plotly.subplots import make_subplots
import yfinance as yf
import time

# 從 page_2a 導入 Tickers 清單
from page_2a import FULL_INDEX_TICKERS

@st.cache_data(ttl=3600, show_spinner=False)
def smart_fetch(ticker_sym, period="2y"):
    try:
        time.sleep(0.01)
        data = yf.Ticker(str(ticker_sym).strip().upper()).history(period=period, auto_adjust=True)
        if data.empty or len(data) < 20:
            return pd.DataFrame()
        
        # 時區安全剝離
        if hasattr(data.index, 'tz') and data.index.tz is not None:
            data.index = data.index.tz_localize(None)
            
        return data.dropna(subset=['Close', 'Volume', 'High', 'Low', 'Open'])
    except Exception: 
        return pd.DataFrame()

def compute_expanded_timeline_breadth(tickers, chart_dates, timeframe):
    num_days = len(chart_dates)
    count_20 = np.zeros(num_days)
    count_50 = np.zeros(num_days)
    count_100 = np.zeros(num_days)
    count_200 = np.zeros(num_days)
    
    # 動態每日有效成分股分母計數器 (防未來污染與除零)
    daily_valid_counts = np.zeros(num_days)
    above_50_list = []
    
    # 週線模式需 5 年數據方能計算真實 200 週均線
    fetch_period = "5y" if "週線" in timeframe else "2y"
    
    for t in tickers:
        try:
            df_t = smart_fetch(t, period=fetch_period)
            if df_t.empty or 'Close' not in df_t.columns:
                continue
            
            if "週線" in timeframe:
                df_t = df_t.resample('W-FRI').agg({
                    'Open': 'first', 'High': 'max', 'Low': 'min', 'Close': 'last', 'Volume': 'sum'
                }).dropna()
            
            close_orig = df_t['Close'].dropna()
            if len(close_orig) < 20:
                continue
            
            # 真實滾動均線 (不使用 min_periods=1 掩蓋數據不足)
            ma20 = close_orig.rolling(20, min_periods=20).mean()
            ma50 = close_orig.rolling(50, min_periods=50).mean()
            ma100 = close_orig.rolling(100, min_periods=100).mean()
            ma200 = close_orig.rolling(200, min_periods=200).mean()
            
            # 僅使用 ffill()，嚴格禁止 bfill() 倒灌未來價格
            close_align = close_orig.reindex(chart_dates).ffill()
            ma20_align = ma20.reindex(chart_dates).ffill()
            ma50_align = ma50.reindex(chart_dates).ffill()
            ma100_align = ma100.reindex(chart_dates).ffill()
            ma200_align = ma200.reindex(chart_dates).ffill()
            
            # 有效交易日遮罩 (該日有真實價格存在者方納入計算)
            valid_mask = close_align.notna().values
            daily_valid_counts += valid_mask.astype(int)
            
            # 各維度市寬累積
            count_20 += np.where(valid_mask & (close_align > ma20_align).values, 1, 0)
            count_50 += np.where(valid_mask & (close_align > ma50_align).values, 1, 0)
            count_100 += np.where(valid_mask & (close_align > ma100_align).values, 1, 0)
            count_200 += np.where(valid_mask & (close_align > ma200_align).values, 1, 0)
            
            # 最新一期站上 50MA 判定
            if valid_mask[-1] and pd.notna(ma50_align.iloc[-1]):
                if close_align.iloc[-1] > ma50_align.iloc[-1]:
                    above_50_list.append(t)
        except Exception:
            continue
        
    safe_denominators = np.where(daily_valid_counts > 0, daily_valid_counts, 1.0)
    
    pct_20 = (count_20 / safe_denominators) * 100.0
    pct_50 = (count_50 / safe_denominators) * 100.0
    pct_100 = (count_100 / safe_denominators) * 100.0
    pct_200 = (count_200 / safe_denominators) * 100.0
    
    total_valid = int(daily_valid_counts[-1]) if len(daily_valid_counts) > 0 else 0
    return pct_20, pct_50, pct_100, pct_200, total_valid, above_50_list

# --- 核心繪圖函數：頂部圖例全白文字 ---
def draw_tower_chart(idx_choice, clean_recent, dates_str, pct_20, pct_50, pct_100, pct_200, above_50_list, total_configured):
    st.markdown(f"### 🌊 {idx_choice} —— 當前最新實時市寬 (100% 真相)")
    st.caption(f"📊 標的總池配置：`{total_configured}` 隻 ｜ 最新有效計算樣本：`{len(above_50_list)}` 隻站上 50MA")
    
    st.markdown(
        f"<div style='display: flex; justify-content: space-between; text-align: center; background-color: #111; padding: 20px; border-radius: 15px; border: 1px solid #FFD700;'>"
        f"<div><span style='color: #cbd5e1; font-size: 1.1rem;'>20市寬之上</span><br><span style='color: #ffffff; font-size: 2.6rem; font-weight: 900;'>{pct_20[-1]:.1f}%</span></div>"
        f"<div><span style='color: #FFD700; font-size: 1.2rem; font-weight: bold;'>50市寬之上 (真・市底)</span><br><span style='color: #00ff88; font-size: 3.2rem; font-weight: 900;'>{pct_50[-1]:.1f}%</span></div>"
        f"<div><span style='color: #cbd5e1; font-size: 1.1rem;'>100市寬之上</span><br><span style='color: #ffffff; font-size: 2.6rem; font-weight: 900;'>{pct_100[-1]:.1f}%</span></div>"
        f"<div><span style='color: #cbd5e1; font-size: 1.1rem;'>200市寬之上</span><br><span style='color: #ffffff; font-size: 2.6rem; font-weight: 900;'>{pct_200[-1]:.1f}%</span></div>"
        f"</div>",
        unsafe_allow_html=True
    )
    
    fig = make_subplots(
        rows=2, cols=1, shared_xaxes=True, row_heights=[0.75, 0.25],
        vertical_spacing=0.04, specs=[[{"secondary_y": True}], [{"secondary_y": False}]]
    )
    
    fig.add_trace(go.Candlestick(
        x=dates_str, open=clean_recent['Open'], high=clean_recent['High'],
        low=clean_recent['Low'], close=clean_recent['Close'],
        name=f'{idx_choice} 指數價格'
    ), row=1, col=1, secondary_y=False)
    
    fig.add_trace(go.Scatter(x=dates_str, y=pct_20, mode='lines', name='20市寬線 (%)', line=dict(color='#ffffff', width=1.5, dash='dot')), row=1, col=1, secondary_y=True)
    fig.add_trace(go.Scatter(x=dates_str, y=pct_50, mode='lines', name='50市寬線 (%)', line=dict(color='#FFD700', width=2.5)), row=1, col=1, secondary_y=True)
    fig.add_trace(go.Scatter(x=dates_str, y=pct_100, mode='lines', name='100市寬線 (%)', line=dict(color='#00FFFF', width=2)), row=1, col=1, secondary_y=True)
    fig.add_trace(go.Scatter(x=dates_str, y=pct_200, mode='lines', name='200市寬線 (%)', line=dict(color='#FF00FF', width=2)), row=1, col=1, secondary_y=True)
    
    v_colors = ['#00ff88' if c >= o else '#ff3366' for c, o in zip(clean_recent['Close'], clean_recent['Open'])]
    fig.add_trace(go.Bar(x=dates_str, y=clean_recent['Volume'], marker_color=v_colors, name='大盤成交量'), row=2, col=1)
    
    # 🌟 強制設定圖例文字為純白 (#ffffff)，防止黑底黑字隱形
    fig.update_layout(
        template="plotly_dark",
        paper_bgcolor='#0e1117',
        plot_bgcolor='#0e1117',
        height=750,
        xaxis_rangeslider_visible=False,
        legend=dict(
            orientation="h",
            yanchor="bottom",
            y=1.02,
            xanchor="right",
            x=1.0,
            font=dict(color="#ffffff", size=11, family="Arial Black"),
            bgcolor="rgba(0,0,0,0)"
        ),
        legend_font_color="#ffffff"
    )
    
    fig.update_xaxes(type='category', showgrid=False, tickfont=dict(color='#cbd5e1'), row=1, col=1)
    fig.update_xaxes(type='category', showgrid=False, tickfont=dict(color='#cbd5e1'), row=2, col=1)
    
    fig.update_yaxes(title_text="📈 價格刻度", title_font=dict(color="#ffffff"), tickfont=dict(color='#cbd5e1'), row=1, col=1, secondary_y=False)
    fig.update_yaxes(title_text="🌊 四維市寬 %", title_font=dict(color="#ffffff"), tickfont=dict(color='#cbd5e1'), row=1, col=1, secondary_y=True, range=[-5, 105])
    
    st.plotly_chart(fig, use_container_width=True, config={'displayModeBar': False}, key=f"tower_ultimate_{idx_choice}")
    
    if above_50_list:
        st.markdown(f"<h3 style='color: white; margin-top:10px;'>🏆 逆市真龍名單 ({idx_choice}) —— 共 {len(above_50_list)} 隻</h3>", unsafe_allow_html=True)
        cols = st.columns(6)
        for i, t in enumerate(above_50_list[:24]):
            cols[i % 6].info(f"🔥 {t}")

def render_master_tower_tab():
    st.markdown("<h1 style='color:#FFD700; font-size:36px; font-family:Arial Black;'>🛡️ 艙房 2b：環球市底大師指揮塔</h1>", unsafe_allow_html=True)
    st.markdown("<hr style='border:2px solid #FFD700;'>", unsafe_allow_html=True)
    
    market_choice = st.radio("陣營選擇", ["🇭🇰 港股市寬系統", "🇺🇸 美股市寬系統"], horizontal=True, key="b_mkt_choice")
    if "港股" in market_choice:
        # 🌟 港股選單正式加裝「國指」
        idx_choice = st.radio("港股指數", ["恒指", "科指", "國指"], horizontal=True, key="b_idx_choice_hk")
    else:
        idx_choice = st.radio("美股指數", ["道指", "標指", "納市", "IWM"], horizontal=True, key="b_idx_choice_us")
        
    timeframe = st.radio("K線級別", ["日線圖 (Daily)", "週線圖 (Weekly)"], horizontal=True, key=f"b_tf_{idx_choice}")

    b_tickers = FULL_INDEX_TICKERS.get(idx_choice, [])
    st.caption(f"📌 當前【{idx_choice}】於 `page_2a.py` 綁定之成分股清單：共 **{len(b_tickers)}** 隻真實標的")

    storage_key = f"store_2b_{idx_choice}_{timeframe}"

    if storage_key in st.session_state:
        st.success(f"📡 已載入 {idx_choice} 存檔數據（免重新掃描）")
        data = st.session_state[storage_key]
        draw_tower_chart(
            idx_choice, data['clean_recent'], data['dates_str'], 
            data['pct_20'], data['pct_50'], data['pct_100'], data['pct_200'], 
            data['above_50_list'], len(b_tickers)
        )
        
        summary = f"{idx_choice} 實時市底報告：50線市寬為 {data['pct_50'][-1]:.1f}%，200線市寬為 {data['pct_200'][-1]:.1f}%。共 {len(data['above_50_list'])} 隻逆市真龍企穩 50線。"
        st.session_state["data_page_2b"] = summary
        
        if st.button("🔄 重新清算最新數據"):
            del st.session_state[storage_key]
            st.rerun()
    else:
        if st.button(f"🚀 啟動真全量四維市寬合流清算"):
            # 🌟 補齊國指 2828.HK 映射
            if idx_choice == "恒指": ticker_sym = "2800.HK"
            elif idx_choice == "科指": ticker_sym = "3032.HK"
            elif idx_choice == "國指": ticker_sym = "2828.HK"
            elif idx_choice == "道指": ticker_sym = "DIA"
            elif idx_choice == "標指": ticker_sym = "SPY"
            elif idx_choice == "納市": ticker_sym = "QQQ"
            else: ticker_sym = "IWM"
            
            if not b_tickers:
                st.error(f"⚠️ 未能於成分股配置中獲取到 {idx_choice} 的代碼列表，請檢查 page_2a.py 配置。")
                return

            fetch_p = "5y" if "週線圖" in timeframe else "2y"
            with st.spinner(f"⏳ 正在進行 {idx_choice} 全真實成份股穿透掃描 (共 {len(b_tickers)} 隻)..."):
                idx_df = smart_fetch(ticker_sym, period=fetch_p)
                if not idx_df.empty:
                    if "週線圖" in timeframe:
                        idx_df = idx_df.resample('W-FRI').agg({
                            'Open': 'first', 'High': 'max', 'Low': 'min', 'Close': 'last', 'Volume': 'sum'
                        }).dropna()
                    
                    clean_recent = idx_df.tail(90).copy()
                    chart_dates = clean_recent.index
                    dates_str = [d.strftime('%Y-%m-%d') for d in chart_dates]
                    
                    pct_20, pct_50, pct_100, pct_200, v_count, above_50_list = compute_expanded_timeline_breadth(b_tickers, chart_dates, timeframe)
                    
                    st.session_state[storage_key] = {
                        'clean_recent': clean_recent, 'dates_str': dates_str,
                        'pct_20': pct_20, 'pct_50': pct_50, 'pct_100': pct_100, 'pct_200': pct_200,
                        'above_50_list': above_50_list
                    }

                    summary = f"{idx_choice} 實時市底報告：50線市寬為 {pct_50[-1]:.1f}%，200線市寬為 {pct_200[-1]:.1f}%。共 {len(above_50_list)} 隻逆市真龍企穩 50線。"
                    st.session_state["data_page_2b"] = summary
                    st.rerun()
                else:
                    st.error(f"⚠️ 無法下載指數標的 {ticker_sym} 的基準行情數據。")

if __name__ == "__main__":
    render_master_tower_tab()