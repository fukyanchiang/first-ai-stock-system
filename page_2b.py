import streamlit as st
import pandas as pd
import numpy as np
import plotly.graph_objects as go
from plotly.subplots import make_subplots
import yfinance as yf
import time

# 從 page_2a 導入 Tickers 清單
from page_2a import FULL_INDEX_TICKERS

@st.cache_data(ttl=3600)
def smart_fetch(ticker_sym, period="2y"):
    try:
        time.sleep(0.005)
        data = yf.Ticker(ticker_sym).history(period=period, auto_adjust=True)
        return data.dropna(subset=['Close', 'Volume', 'High', 'Low', 'Open'])
    except: 
        return pd.DataFrame()

def compute_expanded_timeline_breadth(tickers, chart_dates, timeframe):
    num_days = len(chart_dates)
    count_20 = np.zeros(num_days)
    count_50 = np.zeros(num_days)
    count_100 = np.zeros(num_days)
    count_200 = np.zeros(num_days)
    valid_stocks = 0
    above_50_list = []
    
    for t in tickers:
        try:
            df_t = smart_fetch(t, period="2y")
            if df_t.empty or 'Close' not in df_t.columns: continue
            
            if "週線" in timeframe:
                df_t = df_t.resample('W').agg({'Open':'first', 'High':'max', 'Low':'min', 'Close':'last', 'Volume':'sum'}).dropna()
            
            close_orig = df_t['Close'].dropna()
            if len(close_orig) < 50: continue
            
            ma20 = close_orig.rolling(20, min_periods=1).mean()
            ma50 = close_orig.rolling(50, min_periods=1).mean()
            ma100 = close_orig.rolling(100, min_periods=1).mean()
            ma200 = close_orig.rolling(200, min_periods=1).mean()
            
            close_align = close_orig.reindex(chart_dates).ffill().bfill()
            ma20_align = ma20.reindex(chart_dates).ffill().bfill()
            ma50_align = ma50.reindex(chart_dates).ffill().bfill()
            ma100_align = ma100.reindex(chart_dates).ffill().bfill()
            ma200_align = ma200.reindex(chart_dates).ffill().bfill()
            
            count_20 += (close_align > ma20_align).astype(int).values
            count_50 += (close_align > ma50_align).astype(int).values
            count_100 += (close_align > ma100_align).astype(int).values
            count_200 += (close_align > ma200_align).astype(int).values
            
            valid_stocks += 1
            if close_align.iloc[-1] > ma50_align.iloc[-1]:
                above_50_list.append(t)
        except: pass
        
    valid_stocks = max(1, valid_stocks)
    return (count_20/valid_stocks)*100, (count_50/valid_stocks)*100, (count_100/valid_stocks)*100, (count_200/valid_stocks)*100, valid_stocks, above_50_list

# --- 核心繪圖函數：由備份數據驅動 ---
def draw_tower_chart(idx_choice, clean_recent, dates_str, pct_20, pct_50, pct_100, pct_200, above_50_list):
    st.markdown(f"### 🌊 {idx_choice} —— 當前最新實時市寬 (100% 真相)")
    st.markdown(f"<div style='display: flex; justify-content: space-between; text-align: center; background-color: #111; padding: 20px; border-radius: 15px; border: 1px solid #FFD700;'><div><span style='color: #8892b0; font-size: 1.2rem;'>20市寬之上</span><br><span style='color: white; font-size: 3rem; font-weight: 900;'>{pct_20[-1]:.1f}%</span></div><div><span style='color: #FFD700; font-size: 1.3rem; font-weight: bold;'>50市寬之上 (真・市底)</span><br><span style='color: #00ff88; font-size: 3.5rem; font-weight: 900;'>{pct_50[-1]:.1f}%</span></div><div><span style='color: #8892b0; font-size: 1.2rem;'>100市寬之上</span><br><span style='color: white; font-size: 3rem; font-weight: 900;'>{pct_100[-1]:.1f}%</span></div><div><span style='color: #8892b0; font-size: 1.2rem;'>200市寬之上</span><br><span style='color: white; font-size: 3rem; font-weight: 900;'>{pct_200[-1]:.1f}%</span></div></div>", unsafe_allow_html=True)
    
    fig = make_subplots(rows=2, cols=1, shared_xaxes=True, row_heights=[0.75, 0.25], vertical_spacing=0.04, specs=[[{"secondary_y": True}], [{"secondary_y": False}]])
    fig.add_trace(go.Candlestick(x=dates_str, open=clean_recent['Open'], high=clean_recent['High'], low=clean_recent['Low'], close=clean_recent['Close'], name=f'{idx_choice} 指數價格'), row=1, col=1, secondary_y=False)
    
    fig.add_trace(go.Scatter(x=dates_str, y=pct_20, mode='lines', name='20市寬線 (%)', line=dict(color='#ffffff', width=1.5, dash='dot')), row=1, col=1, secondary_y=True)
    fig.add_trace(go.Scatter(x=dates_str, y=pct_50, mode='lines', name='50市寬線 (%)', line=dict(color='#FFD700', width=2.5)), row=1, col=1, secondary_y=True)
    fig.add_trace(go.Scatter(x=dates_str, y=pct_100, mode='lines', name='100市寬線 (%)', line=dict(color='#00FFFF', width=2)), row=1, col=1, secondary_y=True)
    fig.add_trace(go.Scatter(x=dates_str, y=pct_200, mode='lines', name='200市寬線 (%)', line=dict(color='#FF00FF', width=2)), row=1, col=1, secondary_y=True)
    
    v_colors = ['#00FF00' if clean_recent['Close'].iloc[i] >= clean_recent['Open'].iloc[i] else '#FF0000' for i in range(len(clean_recent))]
    fig.add_trace(go.Bar(x=dates_str, y=clean_recent['Volume'], marker_color=v_colors, name='大盤成交量'), row=2, col=1)
    
    fig.update_layout(template="plotly_dark", paper_bgcolor='#0e1117', plot_bgcolor='#0e1117', height=800, xaxis_rangeslider_visible=False, xaxis=dict(type='category', showgrid=False), legend=dict(orientation="h", yanchor="bottom", y=1.02, xanchor="right", x=1))
    fig.update_yaxes(title_text="📈 價格刻度", row=1, col=1, secondary_y=False)
    fig.update_yaxes(title_text="🌊 四維市寬 %", row=1, col=1, secondary_y=True, range=[-5, 105])
    st.plotly_chart(fig, use_container_width=True, config={'displayModeBar': False}, key=f"tower_ultimate_{idx_choice}")
    
    if above_50_list:
        st.markdown(f"<h3 style='color: white;'>🏆 逆市真龍名單 ({idx_choice})</h3>", unsafe_allow_html=True)
        cols = st.columns(6)
        for i, t in enumerate(above_50_list[:24]): cols[i % 6].info(f"🔥 {t}")

def render_master_tower_tab():
    st.markdown("<h1 style='color:#FFD700; font-size:42px; font-family:Arial Black;'>🛡️ 艙房 2b：環球市底大師指揮塔</h1>", unsafe_allow_html=True)
    st.markdown("<hr style='border:3px solid #FFD700;'>", unsafe_allow_html=True)
    
    market_choice = st.radio("陣營選擇", ["🇭🇰 港股市寬系統", "🇺🇸 美股市寬系統"], horizontal=True, key="b_mkt_choice")
    if "港股" in market_choice:
        idx_choice = st.radio("港股指數", ["恒指", "科指"], horizontal=True, key="b_idx_choice_hk")
    else:
        idx_choice = st.radio("美股指數", ["道指", "標指", "納市", "IWM"], horizontal=True, key="b_idx_choice_us")
        
    timeframe = st.radio("K線級別", ["日線圖 (Daily)", "週線圖 (Weekly)"], horizontal=True, key=f"b_tf_{idx_choice}")

    # --- 戰術儲存庫 Key ---
    storage_key = f"store_2b_{idx_choice}_{timeframe}"

    # 1. 如果中央大腦有舊數據，直接顯示
    if storage_key in st.session_state:
        st.success(f"📡 已載入 {idx_choice} 存檔數據（免掃描）")
        data = st.session_state[storage_key]
        draw_tower_chart(
            idx_choice, data['clean_recent'], data['dates_str'], 
            data['pct_20'], data['pct_50'], data['pct_100'], data['pct_200'], 
            data['above_50_list']
        )
        
        # 🛡️ 爺爺極致加固：確保即使是讀取存檔，戰報依然會被強制刷新到中央大腦！
        summary = f"{idx_choice} 實時市底報告：50日線市寬為 {data['pct_50'][-1]:.1f}%，200日線市寬為 {data['pct_200'][-1]:.1f}%。共 {len(data['above_50_list'])} 隻逆市真龍企穩 50線。"
        st.session_state["data_page_2b"] = summary
        
        if st.button("🔄 重新清算最新數據"):
            del st.session_state[storage_key]
            st.rerun()
    else:
        # 2. 如果沒有數據，顯示掃描掣
        if st.button(f"🚀 啟動真全量四維市寬合流清算"):
            if idx_choice == "恒指": ticker_sym = "2800.HK"
            elif idx_choice == "科指": ticker_sym = "3032.HK"
            elif idx_choice == "道指": ticker_sym = "DIA"
            elif idx_choice == "標指": ticker_sym = "SPY"
            elif idx_choice == "納市": ticker_sym = "QQQ"
            else: ticker_sym = "IWM"
            
            b_tickers = FULL_INDEX_TICKERS.get(idx_choice, [])
            total_setup_count = len(b_tickers)

            with st.spinner(f"⏳ 正在清算 {idx_choice} ..."):
                idx_df = smart_fetch(ticker_sym, period="2y")
                if not idx_df.empty:
                    if "週線圖" in timeframe:
                        idx_df = idx_df.resample('W').agg({'Open':'first', 'High':'max', 'Low':'min', 'Close':'last', 'Volume':'sum'}).dropna()
                    
                    clean_recent = idx_df.tail(90).copy()
                    chart_dates = clean_recent.index
                    dates_str = chart_dates.strftime('%Y-%m-%d')
                    
                    pct_20, pct_50, pct_100, pct_200, v_count, above_50_list = compute_expanded_timeline_breadth(b_tickers, chart_dates, timeframe)
                    
                    # --- 數據冷藏存放 ---
                    st.session_state[storage_key] = {
                        'clean_recent': clean_recent, 'dates_str': dates_str,
                        'pct_20': pct_20, 'pct_50': pct_50, 'pct_100': pct_100, 'pct_200': pct_200,
                        'above_50_list': above_50_list
                    }

                    # --- 🧠 大腦同步戰報 ---
                    summary = f"{idx_choice} 實時市底報告：50日線市寬為 {pct_50[-1]:.1f}%，200日線市寬為 {pct_200[-1]:.1f}%。共 {len(above_50_list)} 隻逆市真龍企穩 50線。"
                    st.session_state["data_page_2b"] = summary

                    st.rerun()

if __name__ == "__main__":
    render_master_tower_tab()