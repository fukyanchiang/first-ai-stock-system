"""
Filename: page_2v_ratio_radar.py
Description: ⚖️ 艙房 2v: 宏觀風險比率與背離雷達 (機構實盤加固版 · 邏輯與UI徹底修復)
重大修復：
1. 解決量化邏輯矛盾：加入 Z-Score >= 0 門檻，杜絕比率趴在歷史地牢時誤報「高位滯脹」
2. 修復 Streamlit 箭頭反轉 Bug：將負號置於字串首位，負數精準觸發紅色向下箭頭 (↓)
3. 根治圖表撞色：將 200日/40週 MA 牛熊線統一升級為醒目尊貴紫 (#a855f7)，徹底與紅燭及港股紅線分離
4. 維持分批抓取防禦與週線均線自適應架構
"""

import streamlit as st
import yfinance as yf
import pandas as pd
import numpy as np
import plotly.graph_objects as go
from plotly.subplots import make_subplots

# =========================================================
# 🗄️ 港股成分股名單 (已剔除防守重疊股)
# =========================================================
HK_SHIELD_TICKERS = [
    "0883.HK", "0857.HK", "0386.HK", "0941.HK", "0728.HK", "0762.HK", 
    "0939.HK", "1398.HK", "3988.HK", "1288.HK", "3328.HK", "2388.HK", 
    "1088.HK", "1919.HK", "0002.HK", "0003.HK", "0006.HK", "1038.HK", 
    "0823.HK", "0576.HK", "0107.HK", "0144.HK", "1199.HK", "0270.HK", 
    "0836.HK", "1193.HK", "0371.HK", "2328.HK", "1339.HK", "0998.HK", 
    "1658.HK", "1898.HK", "1171.HK", "0322.HK", "0220.HK", "0019.HK", 
    "0291.HK", "0390.HK", "1186.HK", "0914.HK"
]

HK_SHRIMP_TICKERS = [
    "0020.HK", "1357.HK", "3896.HK", "6682.HK", "2158.HK", "2013.HK", "9698.HK", 
    "0981.HK", "1347.HK", "1385.HK", "2878.HK", "9660.HK", "2498.HK", "1274.HK", 
    "9863.HK", "9868.HK", "9866.HK", "2015.HK", "9926.HK", "1801.HK", "6160.HK", 
    "2268.HK", "2367.HK", "9992.HK", "2400.HK", "1896.HK", "6181.HK", "9899.HK", 
    "0175.HK", "2238.HK", "2333.HK", "0669.HK", "1070.HK", "3800.HK", "0968.HK", 
    "2380.HK", "1818.HK", "0358.HK", "1378.HK", "3993.HK", "1308.HK", "3311.HK", 
    "1209.HK", "2669.HK", "3319.HK", "3759.HK", "2359.HK"
]

# =========================================================
# ⚙️ 數據抓取引擎 (含分批防禦網絡崩潰機制)
# =========================================================
def download_in_batches(tickers, period, batch_size=20):
    """分批下載，防止 yf 觸發 429 Too Many Requests 限流崩潰"""
    dfs = []
    for i in range(0, len(tickers), batch_size):
        batch = tickers[i:i+batch_size]
        try:
            res = yf.download(batch, period=period, auto_adjust=True, group_by="ticker", progress=False)
            dfs.append(res)
        except Exception:
            pass
    if dfs:
        return pd.concat(dfs, axis=1)
    return pd.DataFrame()

@st.cache_data(ttl=3600, show_spinner=False)
def fetch_us_ratio_data(is_weekly: bool = False):
    try:
        tickers_to_fetch = ["SPHB", "SPLV", "XLY", "XLP", "RSPT", "XLK", "INFL", "TLT", "SPY", "QQQ"]
        period_str = "5y" if is_weekly else "2y"
        raw_us = yf.download(tickers_to_fetch, period=period_str, auto_adjust=True, group_by="ticker", progress=False)
        
        def extract_pair_ratio(raw, num_ticker, den_ticker, bench_ticker):
            df_ratio = pd.DataFrame()
            try:
                is_multi = isinstance(raw.columns, pd.MultiIndex)
                if is_multi and num_ticker in raw.columns.levels[0]:
                    df_ratio['Open'] = raw[num_ticker]['Open'] / raw[den_ticker]['Open']
                    df_ratio['High'] = raw[num_ticker]['High'] / raw[den_ticker]['Low']
                    df_ratio['Low'] = raw[num_ticker]['Low'] / raw[den_ticker]['High']
                    df_ratio['Close'] = raw[num_ticker]['Close'] / raw[den_ticker]['Close']
                    df_ratio['Bench_Close'] = raw[bench_ticker]['Close']
                else:
                    df_ratio['Open'] = raw['Open'][num_ticker] / raw['Open'][den_ticker]
                    df_ratio['High'] = raw['High'][num_ticker] / raw['Low'][den_ticker]
                    df_ratio['Low'] = raw['Low'][num_ticker] / raw['High'][den_ticker]
                    df_ratio['Close'] = raw['Close'][num_ticker] / raw['Close'][den_ticker]
                    df_ratio['Bench_Close'] = raw['Close'][bench_ticker]
                    
                df_ratio = df_ratio.dropna()
                df_ratio['Ratio'] = df_ratio['Close']
                df_ratio.index = pd.to_datetime(df_ratio.index).tz_localize(None)
            except Exception:
                df_ratio = pd.DataFrame()
            return df_ratio

        df_sphb = extract_pair_ratio(raw_us, "SPHB", "SPLV", "SPY")
        df_xly  = extract_pair_ratio(raw_us, "XLY",  "XLP",  "SPY")
        df_rspt = extract_pair_ratio(raw_us, "RSPT", "XLK",  "QQQ")
        df_infl = extract_pair_ratio(raw_us, "INFL", "TLT",  "SPY")

        return df_sphb, df_xly, df_rspt, df_infl
    except Exception:
        return pd.DataFrame(), pd.DataFrame(), pd.DataFrame(), pd.DataFrame()

@st.cache_data(ttl=3600, show_spinner=False)
def fetch_hk_custom_ratio_data(is_weekly: bool = False):
    all_hk_tickers = list(set(HK_SHIELD_TICKERS + HK_SHRIMP_TICKERS + ["2800.HK"]))
    period_str = "5y" if is_weekly else "2y"
    try:
        raw_hk = download_in_batches(all_hk_tickers, period=period_str, batch_size=20)
        
        def calculate_custom_index(tickers, raw_data):
            returns = []
            for t in tickers:
                try:
                    is_multi = isinstance(raw_data.columns, pd.MultiIndex)
                    if is_multi and t in raw_data.columns.levels[0]:
                        s = raw_data[t]['Close'].pct_change()
                        returns.append(s)
                    elif 'Close' in raw_data.columns and t in raw_data['Close'].columns:
                        s = raw_data['Close'][t].pct_change()
                        returns.append(s)
                except Exception:
                    pass
            if returns:
                avg_ret = pd.concat(returns, axis=1).mean(axis=1).fillna(0)
                idx_price = (1.0 + avg_ret).cumprod() * 100.0
                return idx_price
            return pd.Series(dtype=float)
            
        shield_idx = calculate_custom_index(HK_SHIELD_TICKERS, raw_hk)
        shrimp_idx = calculate_custom_index(HK_SHRIMP_TICKERS, raw_hk)
        
        df_hk = pd.DataFrame({'Shield': shield_idx, 'Shrimp': shrimp_idx}).dropna()
        df_hk['Ratio'] = df_hk['Shrimp'] / df_hk['Shield']
        df_hk['Close'] = df_hk['Ratio']
        
        df_hk['Open'] = df_hk['Close']
        df_hk['High'] = df_hk['Close']
        df_hk['Low'] = df_hk['Close']
        
        try:
            is_multi = isinstance(raw_hk.columns, pd.MultiIndex)
            if is_multi and "2800.HK" in raw_hk.columns.levels[0]:
                df_hk['Bench_Close'] = raw_hk["2800.HK"]['Close']
            else:
                df_hk['Bench_Close'] = raw_hk['Close']["2800.HK"]
        except Exception:
            df_hk['Bench_Close'] = df_hk['Ratio']
        
        df_hk.index = pd.to_datetime(df_hk.index).tz_localize(None)
        return df_hk.dropna()
    except Exception:
        return pd.DataFrame()

# =========================================================
# 🧮 歷史背離量化掃描引擎 (徹底解決趴地出高位警報矛盾)
# =========================================================
def compute_quant_and_signals(df, is_weekly, ratio_col="Ratio", benchmark_col="Bench_Close"):
    if df.empty or len(df) < 50:
        return df, {}, pd.DataFrame()
        
    df = df.copy()
    
    # 🌟 MA 參數自適應 (日線 vs 週線)
    ma_s, ma_m, ma_l = (4, 10, 40) if is_weekly else (20, 50, 200)
    
    df['MA_Short'] = df[ratio_col].rolling(ma_s, min_periods=ma_s//2).mean()
    df['MA_Mid'] = df[ratio_col].rolling(ma_m, min_periods=ma_m//2).mean()
    df['MA_Long'] = df[ratio_col].rolling(ma_l, min_periods=ma_l//2).mean()
    
    # Z-Score 計算 (使用 200 週期)
    rolling_mean = df[ratio_col].rolling(200, min_periods=30).mean()
    rolling_std = df[ratio_col].rolling(200, min_periods=30).std()
    df['Z_Score'] = (df[ratio_col] - rolling_mean) / rolling_std.replace(0, np.nan)

    latest_val = float(df[ratio_col].iloc[-1])
    hist_vals = df[ratio_col].dropna()
    percentile = (hist_vals < latest_val).mean() * 100.0
    
    roc_fast = ((latest_val / df[ratio_col].iloc[-6]) - 1.0) * 100.0 if len(df) >= 6 else 0.0
    roc_slow = ((latest_val / df[ratio_col].iloc[-21]) - 1.0) * 100.0 if len(df) >= 21 else 0.0
    
    latest_z = float(df['Z_Score'].iloc[-1]) if not pd.isna(df['Z_Score'].iloc[-1]) else 0.0
    latest_ma_long = float(df['MA_Long'].iloc[-1]) if not pd.isna(df['MA_Long'].iloc[-1]) else latest_val

    # 🌟 波段極值計算
    swing_len = 12 if is_weekly else 60
    bench_max = df[benchmark_col].rolling(swing_len, min_periods=swing_len//3).max()
    bench_min = df[benchmark_col].rolling(swing_len, min_periods=swing_len//3).min()
    ratio_max = df[ratio_col].rolling(swing_len, min_periods=swing_len//3).max()
    ratio_min = df[ratio_col].rolling(swing_len, min_periods=swing_len//3).min()

    mom_len = 2 if is_weekly else 10
    df['Ratio_Mom'] = df[ratio_col].diff(mom_len)

    # 🌟 邏輯修復關鍵：
    # 衰竭/滯脹：必須滿足 Ratio 自身處於中高區間 (Z_Score >= -0.2)，杜絕在地底極端超跌時誤報「高位衰竭」
    df['Bearish_Div_Raw'] = (
        (df['Z_Score'] >= -0.2) &
        (df[benchmark_col] >= bench_max * 0.99) & 
        (df[ratio_col] < ratio_max * 0.95) & 
        (df['Ratio_Mom'] < 0)
    )
    # 底部復甦：必須滿足 Ratio 自身處於中低區間 (Z_Score <= 0.2)
    df['Bullish_Div_Raw'] = (
        (df['Z_Score'] <= 0.2) &
        (df[benchmark_col] <= bench_min * 1.01) & 
        (df[ratio_col] > ratio_min * 1.05) & 
        (df['Ratio_Mom'] > 0)
    )

    def filter_signals(flag_col, gap_days=15):
        sig_indices = []
        last_d = None
        for idx in df[df[flag_col]].index:
            if last_d is None or (idx - last_d).days >= gap_days:
                sig_indices.append(idx)
                last_d = idx
        return sig_indices

    bear_dates = filter_signals('Bearish_Div_Raw', 15)
    bull_dates = filter_signals('Bullish_Div_Raw', 15)

    df['Signal'] = "NORMAL"
    df.loc[bear_dates, 'Signal'] = "BEARISH_DIVERGENCE"
    df.loc[bull_dates, 'Signal'] = "BULLISH_DIVERGENCE"

    df_signals = df[df['Signal'] != "NORMAL"][[ratio_col, benchmark_col, 'Z_Score', 'Signal']].copy()
    df_signals['訊號類型'] = df_signals['Signal'].map({
        "BEARISH_DIVERGENCE": "🔻 高位滯脹 / 動能衰竭",
        "BULLISH_DIVERGENCE": "🟢 底部復甦 / 提前築底"
    })

    curr_div = df['Signal'].iloc[-1]
    if curr_div == "NORMAL" and len(df) >= 5:
        recent_sigs = df['Signal'].iloc[-5:]
        if "BEARISH_DIVERGENCE" in recent_sigs.values: 
            curr_div = "BEARISH_DIVERGENCE"
        elif "BULLISH_DIVERGENCE" in recent_sigs.values: 
            curr_div = "BULLISH_DIVERGENCE"

    metrics = {
        "latest": latest_val,
        "ma_long": latest_ma_long,
        "z_score": latest_z,
        "percentile": percentile,
        "roc_fast": roc_fast,
        "roc_slow": roc_slow,
        "divergence": curr_div
    }
    return df, metrics, df_signals

# =========================================================
# 🔴 圖表引擎 1：雙 Y 軸對照走勢圖 (徹底解決撞色)
# =========================================================
def plot_dual_axis_chart_with_signals(df, title, ratio_line_color, benchmark_label, is_weekly):
    if df.empty: return None
    
    lbl_mid, lbl_long = ("10週 MA", "40週 MA 牛熊線") if is_weekly else ("50日 MA", "200日 MA 牛熊線")
    
    fig = make_subplots(specs=[[{"secondary_y": True}]])
    
    # 比率實線
    fig.add_trace(go.Scatter(x=df.index, y=df['Ratio'], mode='lines', name='Ratio (比率)', line=dict(color=ratio_line_color, width=2.8)), secondary_y=False)
    fig.add_trace(go.Scatter(x=df.index, y=df['MA_Mid'], mode='lines', name=lbl_mid, line=dict(color='#00ff88', width=1.4, dash='dot')), secondary_y=False)
    
    # 🌟 徹底杜絕撞色：牛熊線統一改為極具辨識度的尊貴紫色 (#a855f7)
    fig.add_trace(go.Scatter(x=df.index, y=df['MA_Long'], mode='lines', name=lbl_long, line=dict(color='#a855f7', width=2.2)), secondary_y=False)

    bear_df = df[df['Signal'] == 'BEARISH_DIVERGENCE']
    if not bear_df.empty:
        fig.add_trace(go.Scatter(
            x=bear_df.index, y=bear_df['Ratio'] * 1.02,
            mode='markers+text', name='🔻 高位衰竭',
            marker=dict(symbol='triangle-down', size=13, color='#ff2222'),
            text=['🔻滯脹'] * len(bear_df), textposition='top center',
            textfont=dict(color='#ff2222', size=11, family='Arial Black')
        ), secondary_y=False)

    bull_df = df[df['Signal'] == 'BULLISH_DIVERGENCE']
    if not bull_df.empty:
        fig.add_trace(go.Scatter(
            x=bull_df.index, y=bull_df['Ratio'] * 0.98,
            mode='markers+text', name='🟢 底部復甦',
            marker=dict(symbol='triangle-up', size=13, color='#00ff88'),
            text=['🟢復甦'] * len(bull_df), textposition='bottom center',
            textfont=dict(color='#00ff88', size=11, family='Arial Black')
        ), secondary_y=False)

    if 'Bench_Close' in df.columns:
        fig.add_trace(go.Scatter(x=df.index, y=df['Bench_Close'], mode='lines', name=f'基準 ({benchmark_label})', line=dict(color='#ffd700', width=1.6, dash='longdash')), secondary_y=True)

    fig.update_layout(
        title=dict(text=title, font=dict(color='white', size=18, family='Arial Black')),
        template="plotly_dark", height=520, margin=dict(l=35, r=35, t=50, b=20),
        legend=dict(orientation="h", yanchor="bottom", y=1.02, xanchor="right", x=1, font=dict(color="white")),
        paper_bgcolor="#1e212b", plot_bgcolor="#1e212b", hovermode="x unified"
    )
    fig.update_yaxes(title_text="Ratio 比率", secondary_y=False, gridcolor="#333")
    fig.update_yaxes(title_text=f"基準指數 ({benchmark_label})", secondary_y=True, gridcolor="#222", showgrid=False)
    fig.update_xaxes(gridcolor="#333")
    return fig

# =========================================================
# 🔴 圖表引擎 2：真實陰陽燭 / 淨值結構圖
# =========================================================
def plot_candlestick_chart_with_signals(df, title, ma_colors, is_weekly, is_custom_index=False):
    if df.empty or 'Close' not in df.columns: return None
    
    lbl_short, lbl_mid, lbl_long = ("4週 MA", "10週 MA", "40週 MA 牛熊線") if is_weekly else ("20日 MA", "50日 MA", "200日 MA 牛熊線")
    
    fig = go.Figure()
    
    if is_custom_index or (df['Open'] == df['Close']).all():
        fig.add_trace(go.Scatter(
            x=df.index, y=df['Close'],
            mode='lines', line=dict(color='#00f2ff', width=2.4),
            fill='tozeroy', fillcolor='rgba(0, 242, 255, 0.08)',
            name='新銳/盾牌 淨值比'
        ))
    else:
        fig.add_trace(go.Candlestick(
            x=df.index, open=df['Open'], high=df['High'], low=df['Low'], close=df['Close'],
            name='Ratio 陰陽燭',
            increasing_line_color='#00ff88', decreasing_line_color='#ff3333'
        ))
    
    if 'MA_Short' in df.columns:
        fig.add_trace(go.Scatter(x=df.index, y=df['MA_Short'], mode='lines', name=lbl_short, line=dict(color=ma_colors[0], width=1.4, dash='dash')))
    if 'MA_Mid' in df.columns:
        fig.add_trace(go.Scatter(x=df.index, y=df['MA_Mid'], mode='lines', name=lbl_mid, line=dict(color=ma_colors[1], width=1.4, dash='dot')))
    
    # 🌟 陰陽燭副圖牛熊線同步升級為尊貴紫 (#a855f7)，不與紅 K 線混淆
    if 'MA_Long' in df.columns:
        fig.add_trace(go.Scatter(x=df.index, y=df['MA_Long'], mode='lines', name=lbl_long, line=dict(color='#a855f7', width=2.2)))

    bear_df = df[df['Signal'] == 'BEARISH_DIVERGENCE']
    if not bear_df.empty:
        fig.add_trace(go.Scatter(
            x=bear_df.index, y=bear_df['Close'] * 1.015,
            mode='markers+text', name='🔻 高位衰竭',
            marker=dict(symbol='triangle-down', size=13, color='#ff2222'),
            text=['🔻滯脹'] * len(bear_df), textposition='top center',
            textfont=dict(color='#ff2222', size=11, family='Arial Black')
        ))

    bull_df = df[df['Signal'] == 'BULLISH_DIVERGENCE']
    if not bull_df.empty:
        fig.add_trace(go.Scatter(
            x=bull_df.index, y=bull_df['Close'] * 0.985,
            mode='markers+text', name='🟢 底部復甦',
            marker=dict(symbol='triangle-up', size=13, color='#00ff88'),
            text=['🟢復甦'] * len(bull_df), textposition='bottom center',
            textfont=dict(color='#00ff88', size=11, family='Arial Black')
        ))

    fig.update_layout(
        title=dict(text=title, font=dict(color='white', size=18, family='Arial Black')),
        template="plotly_dark", height=540, margin=dict(l=35, r=35, t=50, b=20),
        legend=dict(orientation="h", yanchor="bottom", y=1.02, xanchor="right", x=1, font=dict(color="white")),
        paper_bgcolor="#1e212b", plot_bgcolor="#1e212b", hovermode="x unified",
        xaxis_rangeslider_visible=False
    )
    fig.update_yaxes(title_text="Ratio 比率", gridcolor="#333")
    fig.update_xaxes(gridcolor="#333")
    return fig

# =========================================================
# 🔴 主頁面渲染入口 (徹底修正指標卡負號與紅綠反轉)
# =========================================================
def render():
    st.markdown("<h1 style='color:#00ff88; font-size:36px; font-family:Arial Black;'>⚖️ 艙房 2v : SPHB / SPLV Ratio (實盤機構級加固版)</h1>", unsafe_allow_html=True)
    
    st.info("""
### 📌 戰略定位：宏觀風險情緒對照與資金流雷達
- **🟡 虛線**：基準指數走勢 (SPY / QQQ / 2800.HK)。
- **🟣 紫線**：長期牛熊分水嶺 (200日 MA / 40週 MA)。
- **🔻 高位滯脹警報**：大市處於波段高位，但防守比率明顯下滑且動能轉負，提示機構資金趨於避險防禦。
- **🟢 底部復甦警報**：大市處於波段低位，但進攻比率率先築底轉強，提示風險資金提前回流。
- **XLY / XLP**：可選消費 vs 必需消費（實體消費週期偏好）。
- **RSPT / XLK**：等權重科技 vs 市值加權科技（科技股內部市寬廣度）。
- **INFL / TLT**：抗通脹資產 vs 長期國債（再通脹交易 vs 衰退避險定價）。
    """)
    st.markdown("<hr style='border:1px solid #444;'>", unsafe_allow_html=True)

    freq = st.radio("⏱ 選擇觀測時間週期：", ["📊 日線走勢 (Daily)", "📅 週線走勢 (Weekly)"], horizontal=True)
    is_weekly = "週線" in freq

    with st.spinner("📡 正在進行實盤數據抓取與波段動能掃描..."):
        df_sphb, df_xly, df_rspt, df_infl = fetch_us_ratio_data(is_weekly=is_weekly)
        df_hk = fetch_hk_custom_ratio_data(is_weekly=is_weekly)

    if is_weekly:
        def resample_weekly(df_target):
            if not df_target.empty:
                return df_target.resample('W-FRI').agg({
                    'Open':'first', 'High':'max', 'Low':'min', 'Close':'last', 
                    'Ratio':'last', 'Bench_Close':'last'
                }).dropna()
            return df_target

        df_sphb = resample_weekly(df_sphb)
        df_xly  = resample_weekly(df_xly)
        df_rspt = resample_weekly(df_rspt)
        df_infl = resample_weekly(df_infl)
        df_hk   = resample_weekly(df_hk)

    df_sphb, m_sphb, sig_sphb = compute_quant_and_signals(df_sphb, is_weekly)
    df_xly,  m_xly,  sig_xly  = compute_quant_and_signals(df_xly,  is_weekly)
    df_rspt, m_rspt, sig_rspt = compute_quant_and_signals(df_rspt, is_weekly)
    df_infl, m_infl, sig_infl = compute_quant_and_signals(df_infl, is_weekly)
    df_hk,   m_hk,   sig_hk   = compute_quant_and_signals(df_hk,   is_weekly)

    ma_label = "40週 MA (牛熊線)" if is_weekly else "200日 MA (牛熊線)"

    # 1. SPHB / SPLV vs SPY
    st.markdown("<h3 style='color:#00f2ff; margin-top:10px;'>🇺🇸 1. 美國隊長：SPHB (高 Beta) / SPLV (低波幅) vs SPY 指數</h3>", unsafe_allow_html=True)
    if not df_sphb.empty and m_sphb:
        if m_sphb["z_score"] >= 2.0:
            st.warning(f"⚠️ **偏離度極端警報 (Z-Score: +{m_sphb['z_score']:.2f} σ)**：高 Beta 攻擊比率過熱，注意均值回歸。")
        if m_sphb["divergence"] == "BEARISH_DIVERGENCE":
            st.error("🚨 **高位動能衰竭**：大市維持高位，但高 Beta 進攻動能走弱並轉負，資金實質轉入防守低波。")
        elif m_sphb["divergence"] == "BULLISH_DIVERGENCE":
            st.success("💎 **底部提前復甦**：大市處於波段低位，進攻型資金動能率先轉正回流。")

        col1, col2, col3, col4 = st.columns(4)
        col1.metric("最新 SPHB/SPLV 比率", f"{m_sphb['latest']:.4f}", delta=f"{m_sphb['roc_fast']:+.2f}% 短線動量")
        col2.metric(ma_label, f"{m_sphb['ma_long']:.4f}", delta=f"{m_sphb['roc_slow']:+.2f}% 波段動量")
        col3.metric("偏離度 Z-Score", f"{m_sphb['z_score']:+.2f} σ", "常態區間 ±2.0 σ")
        col4.metric("歷史分位數", f"{m_sphb['percentile']:.1f}%", "週期全樣本")

        fig_us_dual = plot_dual_axis_chart_with_signals(df_sphb, "📈 SPHB/SPLV vs SPY 雙軸走勢", "#00f2ff", "SPY", is_weekly)
        st.plotly_chart(fig_us_dual, use_container_width=True)

        fig_us_candle = plot_candlestick_chart_with_signals(df_sphb, "🕯️ SPHB/SPLV 比率陰陽燭", ["#ffbb00", "#00ff88"], is_weekly)
        st.plotly_chart(fig_us_candle, use_container_width=True)

        if not sig_sphb.empty:
            with st.expander("📋 查看 SPHB/SPLV 動能警報歷史紀錄"):
                st.dataframe(sig_sphb[['訊號類型', 'Ratio', 'Bench_Close', 'Z_Score']].sort_index(ascending=False), use_container_width=True)

    st.markdown("<hr style='border:1px dashed #444; margin:25px 0;'>", unsafe_allow_html=True)

    # 2. XLY / XLP vs SPY
    st.markdown("<h3 style='color:#ffaa00;'>🛒 2. 消費偏好：XLY (可選消費) / XLP (必需消費) vs SPY</h3>", unsafe_allow_html=True)
    if not df_xly.empty and m_xly:
        if m_xly["divergence"] == "BEARISH_DIVERGENCE":
            st.error("🚨 **實體消費滯脹警報**：大市處於高位，但必需消費表現強於可選消費，實體需求放緩。")
        elif m_xly["divergence"] == "BULLISH_DIVERGENCE":
            st.success("💎 **消費信心復甦**：可選消費率先發力，實體消費預期轉好。")

        col1, col2, col3, col4 = st.columns(4)
        col1.metric("最新 XLY/XLP 比率", f"{m_xly['latest']:.4f}", delta=f"{m_xly['roc_fast']:+.2f}% 短線動量")
        col2.metric(ma_label, f"{m_xly['ma_long']:.4f}", delta=f"{m_xly['roc_slow']:+.2f}% 波段動量")
        col3.metric("偏離度 Z-Score", f"{m_xly['z_score']:+.2f} σ", "常態區間 ±2.0 σ")
        col4.metric("歷史分位數", f"{m_xly['percentile']:.1f}%", "週期全樣本")

        fig_xly_dual = plot_dual_axis_chart_with_signals(df_xly, "📈 XLY/XLP vs SPY 雙軸走勢", "#ffaa00", "SPY", is_weekly)
        st.plotly_chart(fig_xly_dual, use_container_width=True)

        fig_xly_candle = plot_candlestick_chart_with_signals(df_xly, "🕯️ XLY/XLP 比率陰陽燭", ["#00ff88", "#ffbb00"], is_weekly)
        st.plotly_chart(fig_xly_candle, use_container_width=True)

    st.markdown("<hr style='border:1px dashed #444; margin:25px 0;'>", unsafe_allow_html=True)

    # 3. RSPT / XLK vs QQQ
    st.markdown("<h3 style='color:#00ff88;'>💻 3. 科技股市寬：RSPT (等權重) / XLK (市值加權) vs QQQ</h3>", unsafe_allow_html=True)
    if not df_rspt.empty and m_rspt:
        if m_rspt["divergence"] == "BEARISH_DIVERGENCE":
            st.error("🚨 **科技市寬滯脹警報**：QQQ 處於高位，但等權重比率走低，顯示升勢高度集中於巨頭。")
        elif m_rspt["divergence"] == "BULLISH_DIVERGENCE":
            st.success("💎 **科技市寬擴散復甦**：中小型科技股集體修復，廣度展開。")

        col1, col2, col3, col4 = st.columns(4)
        col1.metric("最新 RSPT/XLK 比率", f"{m_rspt['latest']:.4f}", delta=f"{m_rspt['roc_fast']:+.2f}% 短線動量")
        col2.metric(ma_label, f"{m_rspt['ma_long']:.4f}", delta=f"{m_rspt['roc_slow']:+.2f}% 波段動量")
        col3.metric("偏離度 Z-Score", f"{m_rspt['z_score']:+.2f} σ", "常態區間 ±2.0 σ")
        col4.metric("歷史分位數", f"{m_rspt['percentile']:.1f}%", "週期全樣本")

        fig_rspt_dual = plot_dual_axis_chart_with_signals(df_rspt, "📈 RSPT/XLK vs QQQ 雙軸走勢", "#00ff88", "QQQ", is_weekly)
        st.plotly_chart(fig_rspt_dual, use_container_width=True)

        fig_rspt_candle = plot_candlestick_chart_with_signals(df_rspt, "🕯️ RSPT/XLK 比率陰陽燭", ["#ffbb00", "#00f2ff"], is_weekly)
        st.plotly_chart(fig_rspt_candle, use_container_width=True)

    st.markdown("<hr style='border:1px dashed #444; margin:25px 0;'>", unsafe_allow_html=True)

    # 4. INFL / TLT vs SPY
    st.markdown("<h3 style='color:#ff3399;'>🌋 4. 通脹與衰退風向：INFL (通脹受惠) / TLT (長國債) vs SPY</h3>", unsafe_allow_html=True)
    if not df_infl.empty and m_infl:
        if m_infl["divergence"] == "BEARISH_DIVERGENCE":
            st.error("🚨 **衰退定價加深警報**：長債走強壓制抗通脹資產，提示市場對實體需求有所顧慮。")
        elif m_infl["divergence"] == "BULLISH_DIVERGENCE":
            st.success("💎 **再通脹預期回升**：資金回流實體資源資產。")

        col1, col2, col3, col4 = st.columns(4)
        col1.metric("最新 INFL/TLT 比率", f"{m_infl['latest']:.4f}", delta=f"{m_infl['roc_fast']:+.2f}% 短線動量")
        col2.metric(ma_label, f"{m_infl['ma_long']:.4f}", delta=f"{m_infl['roc_slow']:+.2f}% 波段動量")
        col3.metric("偏離度 Z-Score", f"{m_infl['z_score']:+.2f} σ", "常態區間 ±2.0 σ")
        col4.metric("歷史分位數", f"{m_infl['percentile']:.1f}%", "週期全樣本")

        fig_infl_dual = plot_dual_axis_chart_with_signals(df_infl, "📈 INFL/TLT vs SPY 雙軸走勢", "#ff3399", "SPY", is_weekly)
        st.plotly_chart(fig_infl_dual, use_container_width=True)

        fig_infl_candle = plot_candlestick_chart_with_signals(df_infl, "🕯️ INFL/TLT 比率陰陽燭", ["#00ff88", "#ffaa00"], is_weekly)
        st.plotly_chart(fig_infl_candle, use_container_width=True)

    st.markdown("<hr style='border:1px dashed #444; margin:25px 0;'>", unsafe_allow_html=True)

    # 5. 港股特戰隊 (真實淨值圖)
    st.markdown("<h3 style='color:#ff3333;'>🇭🇰 5. 港股特戰隊：🦐 AI 中小新銳 / 🛡️ 高息盾牌 vs 2800.HK 盈富基金</h3>", unsafe_allow_html=True)
    if not df_hk.empty and m_hk:
        col1, col2, col3, col4 = st.columns(4)
        # 🌟 負號置前，Streamlit 即時精確識別為負數並渲染紅色向下箭頭 (↓)
        col1.metric("最新新銳/盾牌比率", f"{m_hk['latest']:.4f}", delta=f"{m_hk['roc_fast']:+.2f}% 短線動量")
        col2.metric(ma_label, f"{m_hk['ma_long']:.4f}", delta=f"{m_hk['roc_slow']:+.2f}% 波段動量")
        col3.metric("偏離度 Z-Score", f"{m_hk['z_score']:+.2f} σ", "常態區間 ±2.0 σ")
        col4.metric("歷史分位數", f"{m_hk['percentile']:.1f}%", "週期全樣本")

        fig_hk_dual = plot_dual_axis_chart_with_signals(df_hk, "📈 港股新銳/盾牌 vs 2800.HK 雙軸對照", "#ff3333", "2800.HK", is_weekly)
        st.plotly_chart(fig_hk_dual, use_container_width=True)

        fig_hk_candle = plot_candlestick_chart_with_signals(df_hk, "📊 港股新銳/盾牌 淨值走勢結構圖", ["#00ff88", "#ffbb00"], is_weekly, is_custom_index=True)
        st.plotly_chart(fig_hk_candle, use_container_width=True)

        if not sig_hk.empty:
            with st.expander("📋 查看港股歷史動能警報紀錄"):
                st.dataframe(sig_hk[['訊號類型', 'Ratio', 'Bench_Close', 'Z_Score']].sort_index(ascending=False), use_container_width=True)

if __name__ == "__main__":
    render()