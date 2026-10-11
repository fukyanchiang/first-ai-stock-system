import streamlit as st
import yfinance as yf
import pandas as pd
import numpy as np
import plotly.graph_objects as go
from plotly.subplots import make_subplots
from datetime import datetime

# =========================================================
# 🗄️ 港股成分股名單 (來自 2bb-HK)
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
    "0175.HK", "2238.HK", "2333.HK", "0669.HK", "0371.HK", "1070.HK", "3800.HK", 
    "0968.HK", "0836.HK", "2380.HK", "1898.HK", "1171.HK", "1818.HK", "0358.HK", 
    "1378.HK", "3993.HK", "1308.HK", "3311.HK", "1209.HK", "2669.HK", "3319.HK", 
    "3759.HK", "2359.HK"
]

# =========================================================
# ⚙️ 數據抓取引擎
# =========================================================
@st.cache_data(ttl=3600, show_spinner=False)
def fetch_us_ratio_data():
    try:
        tickers_to_fetch = ["SPHB", "SPLV", "XLY", "XLP", "RSPT", "XLK", "INFL", "TLT", "SPY", "QQQ"]
        raw_us = yf.download(tickers_to_fetch, period="2y", auto_adjust=True, group_by="ticker", progress=False)
        
        def extract_pair_ratio(raw, num_ticker, den_ticker, bench_ticker):
            df_ratio = pd.DataFrame()
            try:
                if num_ticker in getattr(raw.columns, "levels", [[]])[0]:
                    df_ratio['Open'] = raw[num_ticker]['Open'] / raw[den_ticker]['Open']
                    df_ratio['High'] = raw[num_ticker]['High'] / raw[den_ticker]['Low']
                    df_ratio['Low'] = raw[num_ticker]['Low'] / raw[den_ticker]['High']
                    df_ratio['Close'] = raw[num_ticker]['Close'] / raw[den_ticker]['Close']
                    df_ratio['SPY_Close'] = raw[bench_ticker]['Close']
                else:
                    df_ratio['Open'] = raw['Open'][num_ticker] / raw['Open'][den_ticker]
                    df_ratio['High'] = raw['High'][num_ticker] / raw['Low'][den_ticker]
                    df_ratio['Low'] = raw['Low'][num_ticker] / raw['High'][den_ticker]
                    df_ratio['Close'] = raw['Close'][num_ticker] / raw['Close'][den_ticker]
                    df_ratio['SPY_Close'] = raw['Close'][bench_ticker]
                    
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
    except Exception as e:
        return pd.DataFrame(), pd.DataFrame(), pd.DataFrame(), pd.DataFrame()

@st.cache_data(ttl=3600, show_spinner=False)
def fetch_hk_custom_ratio_data():
    all_hk_tickers = list(set(HK_SHIELD_TICKERS + HK_SHRIMP_TICKERS + ["2800.HK"]))
    try:
        raw_hk = yf.download(all_hk_tickers, period="2y", auto_adjust=True, group_by="ticker", progress=False)
        
        def calculate_custom_index(tickers, raw_data):
            returns = []
            for t in tickers:
                try:
                    if t in getattr(raw_data.columns, "levels", [[]])[0]:
                        s = raw_data[t]['Close'].pct_change()
                        returns.append(s)
                    elif 'Close' in raw_data.columns and t in raw_data['Close'].columns:
                        s = raw_data['Close'][t].pct_change()
                        returns.append(s)
                except: pass
            if returns:
                avg_ret = pd.concat(returns, axis=1).mean(axis=1).fillna(0)
                idx_price = (1 + avg_ret).cumprod() * 100
                return idx_price
            return pd.Series(dtype=float)
            
        shield_idx = calculate_custom_index(HK_SHIELD_TICKERS, raw_hk)
        shrimp_idx = calculate_custom_index(HK_SHRIMP_TICKERS, raw_hk)
        
        df_hk = pd.DataFrame({'Shield': shield_idx, 'Shrimp': shrimp_idx}).dropna()
        df_hk['Ratio'] = df_hk['Shrimp'] / df_hk['Shield']
        df_hk['Close'] = df_hk['Ratio']
        
        df_hk['Open'] = df_hk['Close'].shift(1).fillna(df_hk['Close'])
        df_hk['High'] = df_hk[['Open', 'Close']].max(axis=1) * 1.001
        df_hk['Low'] = df_hk[['Open', 'Close']].min(axis=1) * 0.999
        
        try:
            if "2800.HK" in getattr(raw_hk.columns, "levels", [[]])[0]:
                df_hk['SPY_Close'] = raw_hk["2800.HK"]['Close']
            else:
                df_hk['SPY_Close'] = raw_hk['Close']["2800.HK"]
        except:
            df_hk['SPY_Close'] = df_hk['Ratio']
        
        df_hk.index = pd.to_datetime(df_hk.index).tz_localize(None)
        return df_hk.dropna()
    except Exception as e:
        return pd.DataFrame()

# =========================================================
# 🧮 歷史背離量化掃描與去重引擎
# =========================================================
def compute_quant_and_signals(df, ratio_col="Ratio", benchmark_col="SPY_Close"):
    if df.empty or len(df) < 50:
        return df, {}, pd.DataFrame()
        
    df['MA20'] = df[ratio_col].rolling(20).mean()
    df['MA50'] = df[ratio_col].rolling(50).mean()
    df['MA200'] = df[ratio_col].rolling(200).mean() if len(df) >= 200 else df[ratio_col].rolling(len(df)).mean()
    
    rolling_mean = df[ratio_col].rolling(200, min_periods=30).mean()
    rolling_std = df[ratio_col].rolling(200, min_periods=30).std()
    df['Z_Score'] = (df[ratio_col] - rolling_mean) / rolling_std

    latest_val = df[ratio_col].iloc[-1]
    hist_vals = df[ratio_col].dropna()
    percentile = (hist_vals < latest_val).mean() * 100
    
    roc_5d = ((latest_val / df[ratio_col].iloc[-6]) - 1) * 100 if len(df) >= 6 else 0.0
    roc_20d = ((latest_val / df[ratio_col].iloc[-21]) - 1) * 100 if len(df) >= 21 else 0.0
    
    latest_z = df['Z_Score'].iloc[-1] if not pd.isna(df['Z_Score'].iloc[-1]) else 0.0
    latest_ma200 = df['MA200'].iloc[-1] if not pd.isna(df['MA200'].iloc[-1]) else latest_val

    df['Bench_30Max'] = df[benchmark_col].rolling(30, min_periods=10).max()
    df['Bench_30Min'] = df[benchmark_col].rolling(30, min_periods=10).min()
    df['Ratio_30Max'] = df[ratio_col].rolling(30, min_periods=10).max()
    df['Ratio_30Min'] = df[ratio_col].rolling(30, min_periods=10).min()

    df['Bearish_Div_Raw'] = (df[benchmark_col] >= df['Bench_30Max'] * 0.99) & (df[ratio_col] < df['Ratio_30Max'] * 0.97)
    df['Bullish_Div_Raw'] = (df[benchmark_col] <= df['Bench_30Min'] * 1.01) & (df[ratio_col] > df['Ratio_30Min'] * 1.03)

    def filter_signals(flag_col, gap_days=10):
        sig_indices = []
        last_d = None
        for idx in df[df[flag_col]].index:
            if last_d is None or (idx - last_d).days >= gap_days:
                sig_indices.append(idx)
                last_d = idx
        return sig_indices

    bear_dates = filter_signals('Bearish_Div_Raw', 10)
    bull_dates = filter_signals('Bullish_Div_Raw', 10)

    df['Signal'] = "NORMAL"
    df.loc[bear_dates, 'Signal'] = "BEARISH_DIVERGENCE"
    df.loc[bull_dates, 'Signal'] = "BULLISH_DIVERGENCE"

    df_signals = df[df['Signal'] != "NORMAL"][['Ratio', benchmark_col, 'Z_Score', 'Signal']].copy()
    df_signals['訊號類型'] = df_signals['Signal'].map({
        "BEARISH_DIVERGENCE": "🔻 頂背離 (大市見頂風險)",
        "BULLISH_DIVERGENCE": "🟢 底背離 (聰明錢抄底訊號)"
    })

    curr_div = df['Signal'].iloc[-1]
    if curr_div == "NORMAL" and len(df) >= 5:
        recent_sigs = df['Signal'].iloc[-5:]
        if "BEARISH_DIVERGENCE" in recent_sigs.values: curr_div = "BEARISH_DIVERGENCE"
        elif "BULLISH_DIVERGENCE" in recent_sigs.values: curr_div = "BULLISH_DIVERGENCE"

    metrics = {
        "latest": latest_val,
        "ma200": latest_ma200,
        "z_score": latest_z,
        "percentile": percentile,
        "roc_5d": roc_5d,
        "roc_20d": roc_20d,
        "is_bull_regime": latest_val > latest_ma200,
        "divergence": curr_div
    }
    return df, metrics, df_signals

# =========================================================
# 🔴 圖表引擎 1：雙 Y 軸折線對照圖
# =========================================================
def plot_dual_axis_chart_with_signals(df, title, ratio_line_color, benchmark_label):
    if df.empty: return None
    
    fig = make_subplots(specs=[[{"secondary_y": True}]])
    
    fig.add_trace(go.Scatter(x=df.index, y=df['Ratio'], mode='lines', name='Ratio (比率)', line=dict(color=ratio_line_color, width=3)), secondary_y=False)
    fig.add_trace(go.Scatter(x=df.index, y=df['MA20'], mode='lines', name='20日 MA', line=dict(color='#ffbb00', width=1.5, dash='dash')), secondary_y=False)
    fig.add_trace(go.Scatter(x=df.index, y=df['MA50'], mode='lines', name='50日 MA', line=dict(color='#00ff88', width=1.5, dash='dot')), secondary_y=False)
    fig.add_trace(go.Scatter(x=df.index, y=df['MA200'], mode='lines', name='200日 MA 牛熊線', line=dict(color='#ff3333', width=2.5)), secondary_y=False)

    bear_df = df[df['Signal'] == 'BEARISH_DIVERGENCE']
    if not bear_df.empty:
        fig.add_trace(go.Scatter(
            x=bear_df.index, y=bear_df['Ratio'] * 1.02,
            mode='markers+text', name='🔻 頂背離訊號',
            marker=dict(symbol='triangle-down', size=14, color='#ff2222'),
            text=['🔻頂背離'] * len(bear_df), textposition='top center',
            textfont=dict(color='#ff2222', size=12, family='Arial Black')
        ), secondary_y=False)

    bull_df = df[df['Signal'] == 'BULLISH_DIVERGENCE']
    if not bull_df.empty:
        fig.add_trace(go.Scatter(
            x=bull_df.index, y=bull_df['Ratio'] * 0.98,
            mode='markers+text', name='🟢 底背離訊號',
            marker=dict(symbol='triangle-up', size=14, color='#00ff88'),
            text=['🟢底背離'] * len(bull_df), textposition='bottom center',
            textfont=dict(color='#00ff88', size=12, family='Arial Black')
        ), secondary_y=False)

    if 'SPY_Close' in df.columns:
        fig.add_trace(go.Scatter(x=df.index, y=df['SPY_Close'], mode='lines', name=f'基準指數 ({benchmark_label})', line=dict(color='#ffd700', width=1.8, dash='longdash')), secondary_y=True)

    fig.update_layout(
        title=dict(text=title, font=dict(color='white', size=20, family='Arial Black')),
        template="plotly_dark", height=550, margin=dict(l=40, r=40, t=50, b=20),
        legend=dict(orientation="h", yanchor="bottom", y=1.02, xanchor="right", x=1, font=dict(color="white")),
        paper_bgcolor="#1e212b", plot_bgcolor="#1e212b", hovermode="x unified"
    )
    fig.update_yaxes(title_text="Ratio 比率 (倍數)", secondary_y=False, gridcolor="#333")
    fig.update_yaxes(title_text=f"指數價格 ({benchmark_label})", secondary_y=True, gridcolor="#222", showgrid=False)
    fig.update_xaxes(gridcolor="#333")
    return fig

# =========================================================
# 🔴 圖表引擎 2：戰術陰陽燭 K 線大圖
# =========================================================
def plot_candlestick_chart_with_signals(df, title, ma_colors):
    if df.empty or 'Open' not in df.columns: return None
    
    fig = go.Figure()
    
    fig.add_trace(go.Candlestick(
        x=df.index, open=df['Open'], high=df['High'], low=df['Low'], close=df['Close'],
        name='陰陽燭 Ratio',
        increasing_line_color='#00ff88', decreasing_line_color='#ff3333'
    ))
    
    if 'MA20' in df.columns:
        fig.add_trace(go.Scatter(x=df.index, y=df['MA20'], mode='lines', name='20日 MA', line=dict(color=ma_colors[0], width=1.5, dash='dash')))
    if 'MA50' in df.columns:
        fig.add_trace(go.Scatter(x=df.index, y=df['MA50'], mode='lines', name='50日 MA', line=dict(color=ma_colors[1], width=1.5, dash='dot')))
    if 'MA200' in df.columns:
        fig.add_trace(go.Scatter(x=df.index, y=df['MA200'], mode='lines', name='200日 MA 牛熊線', line=dict(color='#ff3333', width=2.5)))

    bear_df = df[df['Signal'] == 'BEARISH_DIVERGENCE']
    if not bear_df.empty:
        fig.add_trace(go.Scatter(
            x=bear_df.index, y=bear_df['High'] * 1.01,
            mode='markers+text', name='🔻 頂背離訊號',
            marker=dict(symbol='triangle-down', size=14, color='#ff2222'),
            text=['🔻頂背離'] * len(bear_df), textposition='top center',
            textfont=dict(color='#ff2222', size=12, family='Arial Black')
        ))

    bull_df = df[df['Signal'] == 'BULLISH_DIVERGENCE']
    if not bull_df.empty:
        fig.add_trace(go.Scatter(
            x=bull_df.index, y=bull_df['Low'] * 0.99,
            mode='markers+text', name='🟢 底背離訊號',
            marker=dict(symbol='triangle-up', size=14, color='#00ff88'),
            text=['🟢底背離'] * len(bull_df), textposition='bottom center',
            textfont=dict(color='#00ff88', size=12, family='Arial Black')
        ))

    fig.update_layout(
        title=dict(text=title, font=dict(color='white', size=20, family='Arial Black')),
        template="plotly_dark", height=580, margin=dict(l=40, r=40, t=50, b=20),
        legend=dict(orientation="h", yanchor="bottom", y=1.02, xanchor="right", x=1, font=dict(color="white")),
        paper_bgcolor="#1e212b", plot_bgcolor="#1e212b", hovermode="x unified",
        xaxis_rangeslider_visible=False
    )
    fig.update_yaxes(title_text="Ratio 比率 (倍數)", gridcolor="#333")
    fig.update_xaxes(gridcolor="#333")
    return fig

# =========================================================
# 🔴 主頁面渲染
# =========================================================
def render():
    st.markdown("<h1 style='color:#00ff88; font-size:40px; font-family:Arial Black;'>⚖️ 艙房 2v : SPHB / SPLV Ratio (實時背離打卡與戰術雷達)</h1>", unsafe_allow_html=True)
    
    st.info("""
### 📌 戰略定位：華爾街頂底背離雷達與宏觀照妖鏡陣列
* **🟡 金色虛線**：大市或板塊指數基準 (美股 SPY / QQQ / 港股 2800.HK)。
* **🔻 頂背離訊號**：指數創新高，但 Ratio 未創新高，代表機構正暗中轉向防守，大市隨時見頂！
* **🟢 底背離訊號**：指數處於低位，但 Ratio 率先見底回升，代表聰明錢已暗中抄底！
* **🛒 爺爺壓箱底絕技**：XLY / XLP (可選消費/必需消費)。大市升但比率跌 = 實體經濟衰退，股災前兆！
* **💻 科技股市寬雷達**：RSPT / XLK (等權重科技/市值加權科技)。睇科技股係「百花齊放」定「巨頭死撐虛火」。
* **🌋 通脹 vs 衰退風向標**：INFL / TLT (通脹受惠/長國債避險)。解答靈魂拷問，睇「真通脹」定「通縮/真衰退逼近」。
    """)
    st.markdown("<hr style='border:2px solid #444;'>", unsafe_allow_html=True)

    freq = st.radio("⏱ 選擇觀測時間週期：", ["📊 日線走勢 (Daily)", "📅 週線走勢 (Weekly)"], horizontal=True)
    is_weekly = "週線" in freq

    with st.spinner("📡 正在掃描全量歷史數據與陰陽燭，定位 5 大核心背離訊號打點..."):
        df_sphb, df_xly, df_rspt, df_infl = fetch_us_ratio_data()
        df_hk = fetch_hk_custom_ratio_data()

    if is_weekly:
        def resample_weekly(df_target):
            if not df_target.empty:
                return df_target.resample('W-FRI').agg({
                    'Open':'first', 'High':'max', 'Low':'min', 'Close':'last', 
                    'Ratio':'last', 'SPY_Close':'last'
                }).dropna()
            return df_target

        df_sphb = resample_weekly(df_sphb)
        df_xly  = resample_weekly(df_xly)
        df_rspt = resample_weekly(df_rspt)
        df_infl = resample_weekly(df_infl)
        df_hk   = resample_weekly(df_hk)

    df_sphb, m_sphb, sig_sphb = compute_quant_and_signals(df_sphb, ratio_col="Ratio", benchmark_col="SPY_Close")
    df_xly,  m_xly,  sig_xly  = compute_quant_and_signals(df_xly,  ratio_col="Ratio", benchmark_col="SPY_Close")
    df_rspt, m_rspt, sig_rspt = compute_quant_and_signals(df_rspt, ratio_col="Ratio", benchmark_col="SPY_Close")
    df_infl, m_infl, sig_infl = compute_quant_and_signals(df_infl, ratio_col="Ratio", benchmark_col="SPY_Close")
    df_hk,   m_hk,   sig_hk   = compute_quant_and_signals(df_hk,   ratio_col="Ratio", benchmark_col="SPY_Close")

    # ==========================================
    # 1. 🇺🇸 美國隊長 (SPHB / SPLV vs SPY)
    # ==========================================
    st.markdown("<h3 style='color:#00f2ff; margin-top:10px;'>🇺🇸 1. 美國隊長：SPHB (高 Beta) / SPLV (低波幅) vs SPY 指數</h3>", unsafe_allow_html=True)
    
    st.info("""
### 💡 爺爺的極簡解讀：SPHB / SPLV (風險情緒溫度計)
* **SPHB (High Beta)**：進攻型、大起大落的高風險股。
* **SPLV (Low Volatility)**：防守型、沉悶收息的低波幅股。
* **解讀**：當大市升，但 SPHB/SPLV 比率跌，代表機構大戶表面上托住大市，但暗中已經將資金由「進攻」轉為「防守」，這是最強的**頂背離逃頂訊號**！
    """)

    if not df_sphb.empty and m_sphb:
        if m_sphb["z_score"] >= 2.0:
            st.warning(f"⚠️ **偏離度極端警報 (Z-Score: +{m_sphb['z_score']:.2f} σ)**：當前 Ratio 高出 200 日均線 2 個標準差以上（2年分位: {m_sphb['percentile']:.1f}%）。市場對高 Beta 股過熱，請嚴防獲利回吐！")
            
        if m_sphb["divergence"] == "BEARISH_DIVERGENCE":
            st.error("🚨 **頂背離雷達發動 (Bearish Divergence)**：標普500 (SPY) 處於高位，但 SPHB/SPLV 比率出現滯升或回落！機構正將資金轉向防守，大市有見頂風險！")
        elif m_sphb["divergence"] == "BULLISH_DIVERGENCE":
            st.success("💎 **底背離雷達發動 (Bullish Divergence)**：大市處於低位，但 SPHB/SPLV 比率率先見底回升！聰明錢已開始暗中抄底高 Beta 攻擊股！")
        else:
            st.info("🟢 **趨勢同步**：標普 500 指數與風險情緒走勢保持一致，未見明顯背離跡象。")

        col1, col2, col3, col4 = st.columns(4)
        col1.metric("最新 SPHB/SPLV 比率", f"{m_sphb['latest']:.4f}", f"5日動量: {m_sphb['roc_5d']:+.2f}%")
        col2.metric("200日 MA 牛熊分界線", f"{m_sphb['ma200']:.4f}", f"20日動量: {m_sphb['roc_20d']:+.2f}%")
        col3.metric("偏離度 Z-Score", f"{m_sphb['z_score']:+.2f} σ", "極端值: ±2.0 σ")
        col4.metric("歷史百分位數 (Percentile)", f"{m_sphb['percentile']:.1f}%", "近 2 年分位")

        fig_us_dual = plot_dual_axis_chart_with_signals(df_sphb, "📈 美股 Ratio (雙 Y 軸 vs SPY 標普500 + 背離打點)", "#00f2ff", "SPY")
        st.plotly_chart(fig_us_dual, use_container_width=True)

        fig_us_candle = plot_candlestick_chart_with_signals(df_sphb, "🕯️ 美股 Ratio 戰術陰陽燭 K 線圖 (含 20/50/200MA + 背離打點)", ["#ffbb00", "#00ff88"])
        st.plotly_chart(fig_us_candle, use_container_width=True)

        if not sig_sphb.empty:
            with st.expander("📋 查看美股 SPHB/SPLV 歷史背離訊號詳細紀錄清單"):
                st.dataframe(sig_sphb[['訊號類型', 'Ratio', 'SPY_Close', 'Z_Score']].sort_index(ascending=False), use_container_width=True)

    st.markdown("<hr style='border:1px dashed #444; margin:30px 0;'>", unsafe_allow_html=True)

    # ==========================================
    # 2. 🛒 爺爺壓箱底絕技：XLY / XLP vs SPY
    # ==========================================
    st.markdown("<h3 style='color:#ffaa00; margin-top:10px;'>🛒 2. 爺爺壓箱底絕技：XLY (買名牌) / XLP (買廁紙) vs SPY (實體經濟照妖鏡)</h3>", unsafe_allow_html=True)
    
    st.info("""
### 💡 爺爺的極簡解讀：XLY / XLP (實體經濟照妖鏡)
* **XLY (可選消費)**：例如 Amazon、Tesla、Starbucks。大家手頭有閒錢，先會買靚車、飲貴咖啡、網購。**(代表繁榮與貪婪)**
* **XLP (必需消費)**：例如 Walmart、P&G (寶潔)。經濟幾差都好，你都要買廁紙、買牙膏、食飯。**(代表衰退與恐慌)**
* **終極解讀**：如果大市 SPY 一直創新高，但 **XLY / XLP 比率卻一直跌**（大家唔敢買名牌，淨係瘋狂囤積廁紙），代表華爾街春江水暖鴨先知，美國實體經濟底座正在變弱，大市嘅繁榮全靠少數幾隻巨頭死撐。這是一個極危險的**實體經濟頂背離**！
    """)

    if not df_xly.empty and m_xly:
        if m_xly["z_score"] >= 2.0:
            st.warning(f"⚠️ **偏離度極端警報 (Z-Score: +{m_xly['z_score']:.2f} σ)**：XLY/XLP 比率過熱，市場過度樂觀，請留意獲利回吐。")

        if m_xly["divergence"] == "BEARISH_DIVERGENCE":
            st.error("🚨 **頂背離雷達發動 (Bearish Divergence)**：標普500創新高，但大家只敢買廁紙(XLP)唔敢買名牌(XLY)！實體經濟衰退警告，嚴防股災！")
        elif m_xly["divergence"] == "BULLISH_DIVERGENCE":
            st.success("💎 **底背離雷達發動 (Bullish Divergence)**：大市處於低位，但聰明錢已經開始暗中搶購可選消費(XLY)！經濟復甦信號確立！")
        else:
            st.info("🟢 **趨勢同步**：實體消費信心與大市走勢保持一致。")

        col1, col2, col3, col4 = st.columns(4)
        col1.metric("最新 XLY/XLP 比率", f"{m_xly['latest']:.4f}", f"5日動量: {m_xly['roc_5d']:+.2f}%")
        col2.metric("200日 MA 牛熊分界線", f"{m_xly['ma200']:.4f}", f"20日動量: {m_xly['roc_20d']:+.2f}%")
        col3.metric("偏離度 Z-Score", f"{m_xly['z_score']:+.2f} σ", "極端值: ±2.0 σ")
        col4.metric("歷史百分位數 (Percentile)", f"{m_xly['percentile']:.1f}%", "近 2 年分位")

        fig_xly_dual = plot_dual_axis_chart_with_signals(df_xly, "📈 XLY/XLP 消費照妖鏡 (雙 Y 軸 vs SPY 標普500 + 背離打點)", "#ffaa00", "SPY")
        st.plotly_chart(fig_xly_dual, use_container_width=True)

        fig_xly_candle = plot_candlestick_chart_with_signals(df_xly, "🕯️ XLY/XLP 戰術陰陽燭 K 線圖 (含 20/50/200MA + 背離打點)", ["#00ff88", "#ffbb00"])
        st.plotly_chart(fig_xly_candle, use_container_width=True)

        if not sig_xly.empty:
            with st.expander("📋 查看 XLY/XLP 歷史背離訊號詳細紀錄清單"):
                st.dataframe(sig_xly[['訊號類型', 'Ratio', 'SPY_Close', 'Z_Score']].sort_index(ascending=False), use_container_width=True)

    st.markdown("<hr style='border:1px dashed #444; margin:30px 0;'>", unsafe_allow_html=True)

    # ==========================================
    # 3. 💻 科技股市寬雷達：RSPT / XLK vs QQQ
    # ==========================================
    st.markdown("<h3 style='color:#00ff88; margin-top:10px;'>💻 3. 科技股市寬雷達：RSPT (等權重科技) / XLK (市值加權科技) vs QQQ 指數</h3>", unsafe_allow_html=True)
    
    st.info("""
### 💡 爺爺的極簡解讀：RSPT / XLK (科技股市寬照妖鏡)
這招係華爾街用嚟判斷「AI 牛市係真繁榮定係假抱團」嘅終極照妖鏡：
* 📈 **當 RSPT / XLK 比率向上升（RSPT 強過 XLK）**：
  * **意思**：不單止 NVIDIA、Microsoft 喺度升，連中型網絡安全（CRWD、PANW）、晶片（AMD、ON）、軟件股（DDOG、SNPS）都集體爆升、百花齊放！
  * **解讀**：牛市底座極度健康，資金廣泛流入整個科技生態圈，可以放心大膽進攻！
* 📉 **當 RSPT / XLK 比率向下跌（RSPT 弱過 XLK）**：
  * **意思**：市值加權嘅 XLK 靠幾隻巨頭獨撐不斷創新高，但等權重嘅 RSPT 卻滯升甚至走弱。代表二三線科技股、軟件股正在被資金拋棄。
  * **解讀**：抱團虛火！ 聰明錢正在縮窄戰線，只敢縮喺幾隻幾萬億市值嘅巨頭度護盤。科技股市寬嚴重惡化，大市隨時面臨「巨頭補跌」嘅危機！
    """)

    if not df_rspt.empty and m_rspt:
        if m_rspt["z_score"] >= 2.0:
            st.warning(f"⚠️ **科技股市寬極端過熱 (Z-Score: +{m_rspt['z_score']:.2f} σ)**：中小型科技股全面狂歡，請留意短線獲利回吐壓力。")

        if m_rspt["divergence"] == "BEARISH_DIVERGENCE":
            st.error("🚨 **科技股市寬頂背離 (Bearish Divergence)**：納斯達克/科技股指數 (QQQ) 創新高，但等權重/市值加權比率 (RSPT/XLK) 出現下滑！代表資金高度集中喺少數幾隻科技巨頭，中小型科技股散水，大市呈抱團虛火！")
        elif m_rspt["divergence"] == "BULLISH_DIVERGENCE":
            st.success("💎 **科技股市寬底背離 (Bullish Divergence)**：科技股指數處於低位，但 RSPT/XLK 比率率先回升！代表資金正全面擴散至中小型科技股，科技股迎來百花齊放嘅真牛市！")
        else:
            st.info("🟢 **趨勢同步**：科技股內部市寬與大市走勢保持一致。")

        col1, col2, col3, col4 = st.columns(4)
        col1.metric("最新 RSPT/XLK 比率", f"{m_rspt['latest']:.4f}", f"5日動量: {m_rspt['roc_5d']:+.2f}%")
        col2.metric("200日 MA 牛熊分界線", f"{m_rspt['ma200']:.4f}", f"20日動量: {m_rspt['roc_20d']:+.2f}%")
        col3.metric("偏離度 Z-Score", f"{m_rspt['z_score']:+.2f} σ", "極端值: ±2.0 σ")
        col4.metric("歷史百分位數 (Percentile)", f"{m_rspt['percentile']:.1f}%", "近 2 年分位")

        fig_rspt_dual = plot_dual_axis_chart_with_signals(df_rspt, "📈 RSPT/XLK 科技股市寬雷達 (雙 Y 軸 vs QQQ 納斯達克100 + 背離打點)", "#00ff88", "QQQ")
        st.plotly_chart(fig_rspt_dual, use_container_width=True)

        fig_rspt_candle = plot_candlestick_chart_with_signals(df_rspt, "🕯️ RSPT/XLK 戰術陰陽燭 K 線圖 (含 20/50/200MA + 背離打點)", ["#ffbb00", "#00f2ff"])
        st.plotly_chart(fig_rspt_candle, use_container_width=True)

        if not sig_rspt.empty:
            with st.expander("📋 查看 RSPT/XLK 歷史背離訊號詳細紀錄清單"):
                st.dataframe(sig_rspt[['訊號類型', 'Ratio', 'SPY_Close', 'Z_Score']].sort_index(ascending=False), use_container_width=True)

    st.markdown("<hr style='border:1px dashed #444; margin:30px 0;'>", unsafe_allow_html=True)

    # ==========================================
    # 4. 🌋 通脹 vs 衰退風向標：INFL / TLT vs SPY
    # ==========================================
    st.markdown("<h3 style='color:#ff3399; margin-top:10px;'>🌋 4. 通脹 vs 衰退照妖鏡：INFL (通脹受惠) / TLT (長國債避險) vs SPY 指數</h3>", unsafe_allow_html=True)
    
    st.info("""
### 💡 爺爺的極簡解讀：INFL / TLT (通脹 vs 衰退嘅「蹺蹺板」)
這個 Ratio 係反映宏觀大氣候嘅「終極風向標」：
* 📈 **當 INFL / TLT 比率向上升（INFL 強，TLT 弱）**
  * **宏觀環境**：「通脹失控 / 經濟過熱」。
  * **解讀**：大戶瘋狂買入實體資產抗通脹，同時拋售國債（因為通脹會侵蝕債券利息）。這代表市場真係信通脹好勁。
* 📉 **當 INFL / TLT 比率向下跌（INFL 跌，TLT 升）👈 你朋友見到嘅現象！**
  * **宏觀環境**：「通縮逼近 / 經濟衰退 (Recession)」。
  * **解讀**：這就是解答你朋友「靈魂拷問」的終極答案！當這個比率暴跌（日日陰燭），代表聰明錢正在「血洗通脹交易，瘋狂買入美債避險」！
  * **真相**：大戶話畀你聽，唔好信新聞講咩「通脹仲好高」，實體經濟其實已經頂唔住高息，即將面臨**需求毀滅 (Demand Destruction)**。大市（SPY）如果仲喺高位，通常好快就會被這個宏觀地心吸力扯落嚟！
    """)

    if not df_infl.empty and m_infl:
        if m_infl["z_score"] >= 2.0:
            st.warning(f"⚠️ **通脹交易極度過熱 (Z-Score: +{m_infl['z_score']:.2f} σ)**：市場對二次通脹預期過高，請留意商品及抗通脹資產回吐風險。")

        if m_infl["divergence"] == "BEARISH_DIVERGENCE":
            st.error("🚨 **通縮與衰退警報 (Bearish Divergence)**：標普500指數高企，但 INFL/TLT 比率大幅瀉落！聰明錢正大舉血洗通脹交易、轉向國債避險，預示實體經濟正面臨需求毀滅與衰退風險！")
        elif m_infl["divergence"] == "BULLISH_DIVERGENCE":
            st.success("💎 **通脹再起/再通脹訊號 (Bullish Divergence)**：大市低迷，但 INFL/TLT 比率率先反彈！代表資金重新流入實體資源與抗通脹資產，經濟再通脹 (Reflation) 訊號確立！")
        else:
            st.info("🟢 **趨勢同步**：通脹/衰退避險情緒與大市走勢保持一致。")

        col1, col2, col3, col4 = st.columns(4)
        col1.metric("最新 INFL/TLT 比率", f"{m_infl['latest']:.4f}", f"5日動量: {m_infl['roc_5d']:+.2f}%")
        col2.metric("200日 MA 牛熊分界線", f"{m_infl['ma200']:.4f}", f"20日動量: {m_infl['roc_20d']:+.2f}%")
        col3.metric("偏離度 Z-Score", f"{m_infl['z_score']:+.2f} σ", "極端值: ±2.0 σ")
        col4.metric("歷史百分位數 (Percentile)", f"{m_infl['percentile']:.1f}%", "近 2 年分位")

        fig_infl_dual = plot_dual_axis_chart_with_signals(df_infl, "📈 INFL/TLT 通脹風向標 (雙 Y 軸 vs SPY 標普500 + 背離打點)", "#ff3399", "SPY")
        st.plotly_chart(fig_infl_dual, use_container_width=True)

        fig_infl_candle = plot_candlestick_chart_with_signals(df_infl, "🕯️ INFL/TLT 戰術陰陽燭 K 線圖 (含 20/50/200MA + 背離打點)", ["#00ff88", "#ffaa00"])
        st.plotly_chart(fig_infl_candle, use_container_width=True)

        if not sig_infl.empty:
            with st.expander("📋 查看 INFL/TLT 歷史背離訊號詳細紀錄清單"):
                st.dataframe(sig_infl[['訊號類型', 'Ratio', 'SPY_Close', 'Z_Score']].sort_index(ascending=False), use_container_width=True)

    st.markdown("<hr style='border:1px dashed #444; margin:30px 0;'>", unsafe_allow_html=True)

    # ==========================================
    # 5. 🇭🇰 港股板塊 (新銳 / 盾牌 vs 2800.HK)
    # ==========================================
    st.markdown("<h3 style='color:#ff3333;'>🇭🇰 5. 港股特戰隊：🦐 AI 中小新銳 / 🛡️ 高息盾牌 vs 2800.HK 盈富基金</h3>", unsafe_allow_html=True)
    
    st.info("""
### 💡 爺爺的極簡解讀：港股特戰隊 (聰明錢抄底逃頂雷達)
* **🦐 AI 中小新銳**：進攻型高彈性港股 (如半導體、AI 應用)。
* **🛡️ 高息盾牌**：防守型收息港股 (如電訊、能源)。
* **解讀**：如果大市 2800.HK 仲喺度跌，但「新銳/盾牌」比率先一步向上翹，代表春江水暖鴨先知，聰明錢已經喺度暗中建倉進攻板塊，這就是**港股見底嘅黃金訊號**！
    """)

    if not df_hk.empty and m_hk:
        if m_hk["z_score"] >= 2.0:
            st.warning(f"⚠️ **港股偏離度極端警報 (Z-Score: +{m_hk['z_score']:.2f} σ)**：港股 Ratio 處於極度過熱區間，請提防獲利回吐。")

        if m_hk["divergence"] == "BEARISH_DIVERGENCE":
            st.error("🚨 **港股頂背離雷達發動 (Bearish Divergence)**：盈富基金 (2800.HK) 處於高位，但新銳/盾牌比率出現走弱！警惕港股大市見頂風險。")
        elif m_hk["divergence"] == "BULLISH_DIVERGENCE":
            st.success("💎 **港股底背離雷達發動 (Bullish Divergence)**：盈富基金處於低位，但新銳/盾牌比率率先回升！港股底背離反彈訊號確立。")
        else:
            st.info("🟢 **趨勢同步**：港股大市與風險情緒走勢保持一致。")

        col1, col2, col3, col4 = st.columns(4)
        col1.metric("最新港股 Ratio", f"{m_hk['latest']:.4f}", f"5日動量: {m_hk['roc_5d']:+.2f}%")
        col2.metric("200日 MA 牛熊分界線", f"{m_hk['ma200']:.4f}", f"20日動量: {m_hk['roc_20d']:+.2f}%")
        col3.metric("偏離度 Z-Score", f"{m_hk['z_score']:+.2f} σ", "極端值: ±2.0 σ")
        col4.metric("歷史百分位數 (Percentile)", f"{m_hk['percentile']:.1f}%", "近 2 年分位")

        fig_hk_dual = plot_dual_axis_chart_with_signals(df_hk, "📈 港股 Ratio (雙 Y 軸 vs 2800.HK 盈富基金 + 背離打點)", "#ff3333", "2800.HK")
        st.plotly_chart(fig_hk_dual, use_container_width=True)

        fig_hk_candle = plot_candlestick_chart_with_signals(df_hk, "🕯️ 港股 Ratio 戰術陰陽燭 K 線圖 (含 20/50/200MA + 背離打點)", ["#00ff88", "#ffbb00"])
        st.plotly_chart(fig_hk_candle, use_container_width=True)

        if not sig_hk.empty:
            with st.expander("📋 查看港股歷史背離訊號詳細紀錄清單"):
                st.dataframe(sig_hk[['訊號類型', 'Ratio', 'SPY_Close', 'Z_Score']].sort_index(ascending=False), use_container_width=True)

if __name__ == "__main__":
    render()