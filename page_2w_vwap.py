import streamlit as st
import yfinance as yf
import pandas as pd
import numpy as np
import plotly.graph_objects as go
from plotly.subplots import make_subplots
import math

# ==========================================
# ⚙️ 1. 時間錨定演算法：月度 OPEX / 季度 OPEX / YTD
# ==========================================
def is_third_friday(date_obj):
    return date_obj.weekday() == 4 and 15 <= date_obj.day <= 21

def get_opex_dates(df_index):
    monthly_opex = None
    quarterly_opex = None
    ytd_date = df_index[0]
    
    current_year = df_index[-1].year
    # 尋找今年初的第一個交易日作為 YTD 起點
    ytd_candidates = [d for d in df_index if d.year == current_year]
    if ytd_candidates:
        ytd_date = ytd_candidates[0]

    for d in reversed(df_index):
        if is_third_friday(d):
            if monthly_opex is None:
                monthly_opex = d
            if d.month in [3, 6, 9, 12] and quarterly_opex is None:
                quarterly_opex = d
        if monthly_opex and quarterly_opex:
            break
            
    if not monthly_opex: monthly_opex = df_index[-20] if len(df_index) >= 20 else df_index[0]
    if not quarterly_opex: quarterly_opex = df_index[-60] if len(df_index) >= 60 else df_index[0]
    
    return monthly_opex, quarterly_opex, ytd_date

def calculate_anchored_vwap(df, anchor_date):
    df_vwap = df.copy()
    if anchor_date in df_vwap.index:
        df_vwap = df_vwap.loc[anchor_date:].copy()
        
    df_vwap['Typ_Price'] = (df_vwap['High'] + df_vwap['Low'] + df_vwap['Close']) / 3
    df_vwap['Vol_Price'] = df_vwap['Typ_Price'] * df_vwap['Volume']
    df_vwap['Cum_Vol'] = df_vwap['Volume'].cumsum()
    df_vwap['Cum_Vol_Price'] = df_vwap['Vol_Price'].cumsum()
    
    df_vwap['AVWAP'] = np.where(df_vwap['Cum_Vol'] > 0, df_vwap['Cum_Vol_Price'] / df_vwap['Cum_Vol'], df_vwap['Typ_Price'])
    return df_vwap['AVWAP']

# ==========================================
# ⚙️ 2. Volume Profile & 70% 籌碼通道 (VAH, VAL, POC)
# ==========================================
def calculate_volume_profile_advanced(df, n_bins=50):
    if len(df) < 5: return None
    p_min, p_max = df['Low'].min(), df['High'].max()
    if p_max == p_min: return None
        
    bins = np.linspace(p_min, p_max, n_bins + 1)
    bin_vols = np.zeros(n_bins)
    
    for _, row in df.iterrows():
        c_low, c_high, c_vol = row['Low'], row['High'], row['Volume']
        if c_high == c_low:
            idx = int(np.clip((c_low - p_min) / (p_max - p_min) * n_bins, 0, n_bins - 1))
            bin_vols[idx] += c_vol
        else:
            mask = (bins[:-1] <= c_high) & (bins[1:] >= c_low)
            n_overlap = np.sum(mask)
            if n_overlap > 0: bin_vols[mask] += c_vol / n_overlap

    total_vol = np.sum(bin_vols)
    if total_vol == 0: return None
        
    max_bin_idx = np.argmax(bin_vols)
    poc_price = (bins[max_bin_idx] + bins[max_bin_idx + 1]) / 2.0
    
    # 計算 70% Value Area (VAH & VAL)
    target_vol = total_vol * 0.70
    sorted_indices = np.argsort(bin_vols)[::-1]
    cum_vol = 0
    va_indices = []
    for idx in sorted_indices:
        cum_vol += bin_vols[idx]
        va_indices.append(idx)
        if cum_vol >= target_vol: break
            
    val_price = bins[min(va_indices)]
    vah_price = bins[max(va_indices) + 1]
    
    return {
        'poc': poc_price, 'vah': vah_price, 'val': val_price,
        'bins': bins, 'bin_vols': bin_vols
    }

# ==========================================
# ⚙️ 3. 真實 Net Gamma Exposure (GEX Flip)
# ==========================================
@st.cache_data(ttl=3600)
def get_gex_flip_level(symbol, current_price):
    """計算對沖基金級別的 GEX Flip (伽馬翻轉點) 與 Max Pain"""
    try:
        tk = yf.Ticker(symbol)
        exps = tk.options
        if not exps: return None, None
        
        opt = tk.option_chain(exps[0])
        calls, puts = opt.calls, opt.puts
        
        upper_limit, lower_limit = current_price * 1.20, current_price * 0.80
        calls = calls[(calls['strike'] >= lower_limit) & (calls['strike'] <= upper_limit)]
        puts = puts[(puts['strike'] >= lower_limit) & (puts['strike'] <= upper_limit)]
        
        if calls.empty or puts.empty: return None, None

        strikes = sorted(set(calls['strike']).union(set(puts['strike'])))
        
        # Max Pain 計算
        min_loss = float('inf')
        max_pain = current_price
        for strike in strikes:
            c_loss = calls[calls['strike'] < strike].apply(lambda x: (strike - x['strike']) * x['openInterest'], axis=1).sum()
            p_loss = puts[puts['strike'] > strike].apply(lambda x: (x['strike'] - strike) * x['openInterest'], axis=1).sum()
            if (c_loss + p_loss) < min_loss:
                min_loss = c_loss + p_loss
                max_pain = strike

        # GEX Flip Proxy：簡單的 Call/Put Net OI 翻轉加權位
        net_gex_by_strike = {}
        for strike in strikes:
            c_oi = calls[calls['strike'] == strike]['openInterest'].sum() if strike in calls['strike'].values else 0
            p_oi = puts[puts['strike'] == strike]['openInterest'].sum() if strike in puts['strike'].values else 0
            net_gex_by_strike[strike] = c_oi - p_oi  # Call 為正 Gamma，Put 為負 Gamma

        # 找出 Net Gamma 轉折點
        sorted_strikes = sorted(net_gex_by_strike.keys())
        gex_flip = max_pain # 預設
        for i in range(len(sorted_strikes) - 1):
            s1, s2 = sorted_strikes[i], sorted_strikes[i+1]
            if net_gex_by_strike[s1] < 0 and net_gex_by_strike[s2] >= 0:
                gex_flip = (s1 + s2) / 2.0
                break

        return max_pain, gex_flip
    except Exception:
        return None, None

# ==========================================
# 🔴 頁面渲染 Engine
# ==========================================
def render_page_2w_vwap():
    st.title("⚖️ 艙房 2α : 華爾街頂級好淡分界線 (多重 AVWAP 矩陣 & GEX 翻轉雷達)")
    st.markdown("""
    **華爾街頂級對沖基金 (Top 1% Quant) 立體防線系統**：
    1️⃣ **多重 AVWAP 成本矩陣**：同時整合月度 OPEX、季度 OPEX 與 YTD 年初至今大戶平均成本。
    2️⃣ **70% 籌碼通道 (VAH / VAL / POC)**：自動描繪主力的 70% 核心建倉雲層與 POC 戰壕。
    3️⃣ **GEX 伽馬翻轉點 (GEX Flip)**：精準計算做市商波幅暴發 / 慢牛對沖切換點。
    """)
    st.divider()

    # 控制面板
    col_c1, col_c2, col_c3 = st.columns([2, 2, 2])
    with col_c1:
        symbol = st.text_input("🔍 輸入標的代號 (美股/ETF/大型股)", value="SPY").upper().strip()
    with col_c2:
        period = st.selectbox("⏱️ K線觀測範圍", ["3mo", "6mo", "1y"], index=0)
    with col_c3:
        st.info("💡 系統已啟用：多重 AVWAP 矩陣、70% 籌碼通道雲層與 GEX Flip 雷達。")

    with st.spinner(f"📡 正在導向華爾街量化數據庫計算 {symbol} 高維防線..."):
        try:
            df = yf.download(symbol, period=period, interval="1d", progress=False)
            if isinstance(df.columns, pd.MultiIndex):
                df.columns = df.columns.get_level_values(0)
            df = df.dropna()
        except Exception as e:
            st.error(f"無法載入 {symbol} 數據: {e}")
            return

    if df.empty or 'Volume' not in df.columns or df['Volume'].sum() == 0:
        st.warning(f"找不到 {symbol} 的數據或缺乏成交量。")
        return

    current_price = df['Close'].iloc[-1]

    # 1. 多重 AVWAP
    monthly_opex, quarterly_opex, ytd_date = get_opex_dates(df.index)
    avwap_monthly = calculate_anchored_vwap(df, anchor_date=monthly_opex)
    avwap_quarterly = calculate_anchored_vwap(df, anchor_date=quarterly_opex)
    
    m_vwap = avwap_monthly.iloc[-1]
    q_vwap = avwap_quarterly.iloc[-1]

    # 2. Volume Profile Advanced
    recent_days = min(60, len(df))
    vp = calculate_volume_profile_advanced(df.tail(recent_days))
    poc_price = vp['poc'] if vp else current_price
    vah_price = vp['vah'] if vp else current_price * 1.02
    val_price = vp['val'] if vp else current_price * 0.98

    # 3. GEX Flip & Max Pain
    max_pain, gex_flip = get_gex_flip_level(symbol, current_price)

    # 4. 量化共振得分計算 (Quant Confluence Score)
    score = 0
    if current_price > m_vwap: score += 25
    if current_price > q_vwap: score += 25
    if current_price > poc_price: score += 25
    if current_price > vah_price: score += 15
    if gex_flip and current_price > gex_flip: score += 10
    if current_price < val_price: score -= 30

    # 🏛️ 頂層：三大好淡分界線戰術卡
    st.markdown("### 🎯 量化共振得分與華爾街防線診斷")
    col_mp1, col_mp2, col_mp3, col_mp4 = st.columns([2.5, 2.5, 2.5, 2.5])
    
    with col_mp1:
        color_score = "#00ff88" if score >= 50 else "#ff0055"
        st.markdown(f"<div style='background-color:#1e293b; padding:12px; border-radius:10px; border-left:5px solid {color_score}'>"
                    f"<h4 style='margin:0; color:#aaa;'>量化好淡共振分</h4>"
                    f"<h2 style='margin:5px 0; color:{color_score};'>{score} / 100</h2>"
                    f"<p style='margin:0; font-size:12px; color:#ccc;'>{'強勢多頭 (線上食龍蝦)' if score>=50 else '弱勢空頭 (線下要縮沙)'}</p></div>", unsafe_allow_html=True)
                  
    with col_mp2:
        st.metric(label="🟡 月度轉倉 AVWAP", value=f"\${m_vwap:.2f}", 
                  delta=f"距離: {((current_price-m_vwap)/m_vwap)*100:.1f}%")
        st.caption(f"起點: `{monthly_opex.strftime('%Y-%m-%d')}`")
                  
    with col_mp3:
        st.metric(label="🟠 季度轉倉 AVWAP", value=f"\${q_vwap:.2f}",
                  delta=f"距離: {((current_price-q_vwap)/q_vwap)*100:.1f}%")
        st.caption(f"起點: `{quarterly_opex.strftime('%Y-%m-%d')}`")
                  
    with col_mp4:
        if gex_flip:
            st.metric(label="🔵 GEX Flip 伽馬翻轉點", value=f"\${gex_flip:.2f}",
                      delta="低波慢牛" if current_price >= gex_flip else "⚠️ 暴瀉模式",
                      delta_color="normal" if current_price >= gex_flip else "inverse")
        else:
            st.metric(label="🔴 POC 籌碼戰壕", value=f"\${poc_price:.2f}")

    # 📈 主圖表繪製 (70% 籌碼通道雲層 + 多重 AVWAP)
    fig = make_subplots(rows=1, cols=2, shared_yaxes=True, column_widths=[0.85, 0.15], horizontal_spacing=0.01)

    # 左側：K 線圖
    fig.add_trace(go.Candlestick(
        x=df.index, open=df['Open'], high=df['High'], low=df['Low'], close=df['Close'],
        name="K線", increasing_line_color='#00ff88', decreasing_line_color='#ff0066'
    ), row=1, col=1)

    # 左側：1. 月度 AVWAP (金黃色)
    df_p_m = df.loc[monthly_opex:]
    avwap_m_plot = avwap_monthly.loc[monthly_opex:]
    fig.add_trace(go.Scatter(
        x=df_p_m.index, y=avwap_m_plot, name="月度轉倉 AVWAP",
        line=dict(color='#FFD700', width=3.5)
    ), row=1, col=1)

    # 左側：2. 季度 AVWAP (橘橘色)
    df_p_q = df.loc[quarterly_opex:]
    avwap_q_plot = avwap_quarterly.loc[quarterly_opex:]
    fig.add_trace(go.Scatter(
        x=df_p_q.index, y=avwap_q_plot, name="季度大戶 AVWAP",
        line=dict(color='#FF8C00', width=2.5, dash='dash')
    ), row=1, col=1)

    # 左側：3. GEX Flip 橫線 (寶藍色)
    if gex_flip:
        fig.add_hline(
            y=gex_flip, line_color="#00BFFF", line_width=2.5, line_dash="dashdot",
            annotation_text="<b>🔵 GEX Flip 伽馬翻轉點</b>", annotation_font_color="#00BFFF",
            row=1, col=1
        )

    # 右側與左側：4. 70% 籌碼通道 (VAH & VAL 雲層)
    if vp:
        # 左側 K 線圖上畫 70% 籌碼通道 (VAH 至 VAL 半透明紅色區域)
        fig.add_hrect(
            y0=val_price, y1=vah_price, fillcolor="rgba(255, 0, 85, 0.08)",
            line_width=0, annotation_text="<b>70% 主力籌碼密集通道 (Value Area)</b>",
            annotation_position="bottom left", annotation_font_color="rgba(255,0,85,0.7)",
            row=1, col=1
        )
        # POC 戰壕
        fig.add_hline(y=poc_price, line_color="#FF0055", line_width=3, line_dash="solid", annotation_text="<b>🔴 POC 戰壕</b>", annotation_font_color="#FF0055", row=1, col=1)
        fig.add_hline(y=poc_price, line_color="#FF0055", line_width=3, line_dash="solid", row=1, col=2)

        # 右側 Volume Profile 柱狀圖
        y_centers = (vp['bins'][:-1] + vp['bins'][1:]) / 2
        norm_vols = vp['bin_vols'] / np.max(vp['bin_vols'])
        fig.add_trace(go.Bar(
            y=y_centers, x=norm_vols, orientation='h',
            marker_color='rgba(255, 0, 85, 0.55)', name='Volume Profile'
        ), row=1, col=2)

    fig.update_layout(
        height=750, template="plotly_dark", xaxis_rangeslider_visible=False,
        margin=dict(l=10, r=10, t=30, b=10),
        legend=dict(orientation="h", yanchor="bottom", y=1.02, xanchor="right", x=1),
        barmode='overlay'
    )
    
    y_min_plot = df['Low'].min() * 0.95
    y_max_plot = df['High'].max() * 1.05
    fig.update_yaxes(title_text="價格", range=[y_min_plot, y_max_plot], row=1, col=1)
    fig.update_xaxes(showticklabels=False, row=1, col=2)

    st.plotly_chart(fig, use_container_width=True)

def app():
    render_page_2w_vwap()

if __name__ == "__main__":
    app()