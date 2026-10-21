import streamlit as st
import pandas as pd
import numpy as np
import yfinance as yf
import plotly.graph_objects as go

# =========================================================================
# 🏛️ 1. 完整板塊資料庫定義 (11 大傳統宏觀 + 23 大前沿硬科技 = 34 大板塊)
# =========================================================================

MACRO_SECTORS = {
    'XLK': '科技 (XLK)', 'XLF': '金融 (XLF)', 'XLV': '醫療保健 (XLV)',
    'XLE': '能源 (XLE)', 'XLY': '非必需消費 (XLY)', 'XLP': '必需消費 (XLP)',
    'XLI': '工業 (XLI)', 'XLU': '公用事業 (XLU)', 'XLB': '原材料 (XLB)',
    'XLRE': '房地產 (XLRE)', 'XLC': '通訊服務 (XLC)'
}

# 🏛️ 11 大傳統宏觀板塊之核心成分股與代表 ETF 資料庫
MACRO_SECTOR_HOLDINGS = {
    '科技 (XLK)': {
        'etfs': ['XLK', 'VGT', 'IYW', 'QQQ'],
        'tickers': ['AAPL', 'MSFT', 'NVDA', 'AVGO', 'ORCL', 'CRM', 'ADBE', 'CSCO', 'AMD', 'QCOM']
    },
    '金融 (XLF)': {
        'etfs': ['XLF', 'VFH', 'KBE', 'KRE'],
        'tickers': ['JPM', 'BAC', 'WFC', 'GS', 'MS', 'BLK', 'C', 'AXP', 'V', 'MA']
    },
    '醫療保健 (XLV)': {
        'etfs': ['XLV', 'VHT', 'IBB', 'XBI'],
        'tickers': ['LLY', 'UNH', 'JNJ', 'ABBV', 'MRK', 'TMO', 'ABT', 'PFE', 'AMGN', 'ISRG']
    },
    '能源 (XLE)': {
        'etfs': ['XLE', 'VDE', 'OIH', 'XOP'],
        'tickers': ['XOM', 'CVX', 'COP', 'EOG', 'SLB', 'MPC', 'PSX', 'VLO', 'OXY', 'HAL']
    },
    '非必需消費 (XLY)': {
        'etfs': ['XLY', 'VCR', 'XRT'],
        'tickers': ['AMZN', 'TSLA', 'HD', 'MCD', 'NKE', 'LOW', 'BKNG', 'SBUX', 'TJX', 'TGT']
    },
    '必需消費 (XLP)': {
        'etfs': ['XLP', 'VDC', 'KXI'],
        'tickers': ['PG', 'COST', 'WMT', 'KO', 'PEP', 'PM', 'MDLZ', 'CL', 'MO', 'KMB']
    },
    '工業 (XLI)': {
        'etfs': ['XLI', 'VIS', 'ITA'],
        'tickers': ['GE', 'CAT', 'UNP', 'HON', 'RTX', 'BA', 'LMT', 'DE', 'UPS', 'FDX']
    },
    '公用事業 (XLU)': {
        'etfs': ['XLU', 'VPU', 'GRID'],
        'tickers': ['NEE', 'SO', 'DUK', 'CEG', 'VST', 'SRE', 'AEP', 'PEG', 'EXC', 'ED']
    },
    '原材料 (XLB)': {
        'etfs': ['XLB', 'VAW', 'LIT'],
        'tickers': ['LIN', 'SHW', 'FCX', 'APD', 'ECL', 'NEM', 'CTVA', 'DOW', 'DD', 'ALB']
    },
    '房地產 (XLRE)': {
        'etfs': ['XLRE', 'VNQ', 'IYR'],
        'tickers': ['PLD', 'AMT', 'EQIX', 'WELL', 'SPG', 'PSA', 'O', 'DLR', 'CCI', 'VICI']
    },
    '通訊服務 (XLC)': {
        'etfs': ['XLC', 'VOX', 'FCOM'],
        'tickers': ['META', 'GOOGL', 'GOOG', 'NFLX', 'DIS', 'CMCSA', 'TMUS', 'VZ', 'T', 'EA']
    }
}

# 🚀 23 大前沿硬科技、主題與資源霸權
FRONTIER_SECTORS = {
    '🧠 GPU / AI 核心算力 (SMH)': {'etfs': ['SMH', 'SOXX', 'USD'], 'tickers': ['NVDA', 'TSM', 'AVGO', 'AMD', 'ASML', 'ARM', 'MU', 'QCOM']},
    '💻 CPU / 處理器 (SOXX)': {'etfs': ['SOXX', 'XSD'], 'tickers': ['AMD', 'INTC', 'ARM', 'QCOM', 'AAPL', 'NVDA', 'TXN']},
    '💾 DRAM / 存儲與記憶體': {'etfs': ['DRAM', 'CHPX'], 'tickers': ['MU', '000660.KS', '005930.KS', 'WDC', 'STX']},
    '⚡ 光通訊 / 矽光子': {'etfs': ['FOTO'], 'tickers': ['LITE', 'COHR', 'FN', 'CIEN', 'IPGP', 'AAOI', 'CRDO', 'MRVL']},
    '🔋 MLCC / 被動元件': {'etfs': [], 'tickers': ['6981.T', '6762.T', '6976.T', '009150.KS', '2327.TW', '2492.TW']},
    '🏭 AI 伺服器與組裝': {'etfs': [], 'tickers': ['SMCI', 'DELL', 'HPE', '2317.TW', '2382.TW', '2356.TW', '3231.TW']},
    '❄ 發電、液冷與散熱板': {'etfs': ['GRID', 'XLU'], 'tickers': ['GEV', 'CAT', 'CMI', 'CEG', 'VST', 'VRT', 'MOD', '3324.TW', '3017.TW', '3653.TW']},
    '⚡ 變壓器與電網升級': {'etfs': ['GRID', 'PAVE'], 'tickers': ['PWR', 'ETN', 'HUBB', 'ABB', 'EME', 'MYRG']},
    '📱 Edge AI / 端側晶片': {'etfs': [], 'tickers': ['QCOM', 'AAPL', 'AVGO', 'SWKS', 'QRVO', 'LOGI', 'NXPI']},
    '🛡️ 網絡安全': {'etfs': ['CIBR', 'HACK', 'BUG'], 'tickers': ['CRWD', 'PANW', 'ZS', 'FTNT', 'NET', 'CYBR', 'OKTA', 'CHKP']},
    '🧠 LLM 大模型巨頭': {'etfs': ['AIQ', 'BOTZ', 'THNQ'], 'tickers': ['MSFT', 'GOOGL', 'AMZN', 'META', 'ORCL', 'AAPL']},
    '🚗 自動駕駛與 Robotaxi': {'etfs': ['IDRV', 'DRIV', 'HAIL'], 'tickers': ['TSLA', 'GOOGL', 'MBLY', 'UBER', 'HSAI', 'AUR']},
    '🦾 機械人與自動化': {'etfs': ['BOTZ', 'ROBO', 'IRBO'], 'tickers': ['TSLA', 'ISRG', '6954.T', 'PATH', 'SYM', 'TER']},
    '🌌 量子電腦': {'etfs': ['QTUM', 'DEFI'], 'tickers': ['IONQ', 'RGTI', 'QBTS', 'QUBT', 'IBM']},
    '🚀 太空與衛星通訊': {'etfs': ['UFO', 'ROKT', 'ARKX', 'NASA'], 'tickers': ['RKLB', 'ASTS', 'LUNR', 'VSAT', 'IRDM', 'PL']},
    '🪙 加密貨幣與狂熱': {'etfs': ['IBIT', 'BITO', 'WGMI'], 'tickers': ['COIN', 'MSTR', 'MARA', 'RIOT', 'CLSK', 'HOOD']},
    '⚛ 核能、SMR 與鈾礦': {'etfs': ['URA', 'URNM', 'NLR'], 'tickers': ['CCJ', 'OKLO', 'SMR', 'LEU', 'UUUU', 'CEG', 'VST']},
    '🥇 金礦股': {'etfs': ['GDX', 'GDXJ', 'RING'], 'tickers': ['NEM', 'GOLD', 'AEM', 'KGC', 'AUY']},
    '🥈 銀礦股': {'etfs': ['SIL', 'SILJ'], 'tickers': ['AG', 'PAAS', 'HL', 'CDE', 'FSM']},
    '🥉 銅礦股': {'etfs': ['COPX', 'CPER'], 'tickers': ['FCX', 'SCCO', 'ERO', 'TECK', 'HBM']},
    '🧬 前沿生物科技': {'etfs': ['XBI', 'IBB', 'ARKG'], 'tickers': ['MRNA', 'BNTX', 'CRSP', 'VRTX', 'REGN', 'ILMN']},
    '⚔️ 國防與軍工': {'etfs': ['ITA', 'PPA', 'XAR'], 'tickers': ['LMT', 'RTX', 'NOC', 'GD', 'BA', 'LHX', 'HII']},
    '🚀 顛覆性創新 (木頭姐)': {'etfs': ['ARKK', 'ARKW', 'ARKG', 'ARKF', 'ARKX'], 'tickers': ['TSLA', 'ROKU', 'COIN', 'PLTR', 'U']}
}

# 🌐 全球 34 大完整板塊成分資料庫 (11 宏觀 + 23 前沿)
ALL_34_SECTOR_HOLDINGS = {**MACRO_SECTOR_HOLDINGS, **FRONTIER_SECTORS}

ULTIMATE_SECTORS = {
    '📈 股市總體風險 (SPY)': 'SPY',
    '🗑️ 聰明錢信用風險 (HYG)': 'HYG',
    '🪙 極限流動性 (BTC-USD)': 'BTC-USD',
    '👑 黃金終極避險 (GLD)': 'GLD',
    '🏭 實體基建與通脹 (COPX)': 'COPX',
    '🛍️ 美國消費信心 (XLY)': 'XLY',
    '🧠 AI 算力命脈 (SMH)': 'SMH',
    '⚛️ 核能與終極能源 (URA)': 'URA',
    '⚔️ 地緣政治與軍工 (ITA)': 'ITA'
}

# =========================================================================
# ⚙️ 2. 全量數據抓取與合成引擎
# =========================================================================
@st.cache_data(ttl=900, show_spinner=False)
def load_all_market_data():
    all_tickers = set(['SPY', 'TLT'])
    all_tickers.update(MACRO_SECTORS.keys())
    all_tickers.update(ULTIMATE_SECTORS.values())
    
    # 提取所有前沿 ETF 和個股
    for sec, info in FRONTIER_SECTORS.items():
        if 'etfs' in info:
            for etf in info['etfs']:
                if etf: all_tickers.add(etf)
        all_tickers.update(info['tickers'])
        
    try:
        data = yf.download(list(all_tickers), period='1y', progress=False)['Close']
        data = data.ffill().bfill()
        return data
    except Exception as e:
        return pd.DataFrame()

def calculate_momentum_table(series_dict):
    data = []
    for name, series in series_dict.items():
        s = series.dropna()
        if len(s) >= 22:
            chg_1d = (s.iloc[-1] / s.iloc[-2] - 1) * 100
            chg_1w = (s.iloc[-1] / s.iloc[-6] - 1) * 100
            chg_1m = (s.iloc[-1] / s.iloc[-22] - 1) * 100
            data.append({
                '板塊': name, '1日變化 (%)': chg_1d, '1週變化 (%)': chg_1w, '1個月變化 (%)': chg_1m
            })
    df = pd.DataFrame(data)
    if not df.empty:
        df = df.sort_values(by='1週變化 (%)', ascending=False)
    return df

def calculate_rrg_metrics(price_df, sector_series_dict, window=14, benchmark='SPY'):
    if price_df.empty or benchmark not in price_df.columns:
        return pd.DataFrame(), pd.DataFrame()
        
    bench_price = price_df[benchmark]
    rs_df = pd.DataFrame(index=price_df.index)
    for name, series in sector_series_dict.items():
        rs_df[name] = series / bench_price
        
    rs_mean = rs_df.rolling(window).mean()
    rs_std = rs_df.rolling(window).std().replace(0, np.nan)
    rs_ratio = 100 + ((rs_df - rs_mean) / rs_std) * 2
    
    ratio_mean = rs_ratio.rolling(window).mean()
    ratio_std = rs_ratio.rolling(window).std().replace(0, np.nan)
    rs_mom = 100 + ((rs_ratio - ratio_mean) / ratio_std) * 2
    return rs_ratio.dropna(), rs_mom.dropna()


# =========================================================================
# 🎨 3. 繪圖核心：柱狀圖 + 數據表 + RRG星盤
# =========================================================================
def render_momentum_section(mom_df, section_title):
    if mom_df.empty: return
    st.markdown(f"### 📊 最新板塊動能雷達 (近期資金湧入邊度？)")
    fig_bar = go.Figure()
    fig_bar.add_trace(go.Bar(
        x=mom_df['板塊'], y=mom_df['1個月變化 (%)'],
        name='1個月趨勢 (中線資金)', marker_color='rgba(0, 229, 255, 0.4)',
        hovertemplate='%{y:.2f}%<extra></extra>'
    ))
    colors_1w = ['#00ff88' if val > 0 else '#ff3333' for val in mom_df['1週變化 (%)']]
    fig_bar.add_trace(go.Bar(
        x=mom_df['板塊'], y=mom_df['1週變化 (%)'],
        name='1週爆發力 (短線資金)', marker_color=colors_1w,
        hovertemplate='%{y:.2f}%<extra></extra>'
    ))
    fig_bar.update_layout(
        barmode='group', title=dict(text=f"🎯 {section_title}板塊資金動能對比", font=dict(color="white", size=20)),
        font=dict(color="white"), template="plotly_dark", height=500, margin=dict(l=20, r=20, t=50, b=20),
        legend=dict(orientation="h", yanchor="bottom", y=1.02, xanchor="right", x=1), paper_bgcolor="#1e212b", plot_bgcolor="#1e212b", hovermode="x unified"
    )
    st.plotly_chart(fig_bar, use_container_width=True)

    st.markdown(f"### 📋 詳細資金流向數據表")
    def color_pct(val):
        color = '#00ff88' if val > 0 else '#ff3333' if val < 0 else 'white'
        return f'color: {color}; font-weight: bold;'
    
    dynamic_height = int((len(mom_df) * 36) + 43)
    st.dataframe(
        mom_df.style.map(color_pct, subset=['1日變化 (%)', '1週變化 (%)', '1個月變化 (%)']).format({
            '1日變化 (%)': '{:.2f}%', '1週變化 (%)': '{:.2f}%', '1個月變化 (%)': '{:.2f}%'
        }), 
        use_container_width=True, height=dynamic_height, hide_index=True
    )

def plot_rrg_chart(rs_ratio, rs_mom, tail_length, chart_title):
    if rs_ratio.empty or rs_mom.empty: return

    fig = go.Figure()

    colors = ['#00ff88', '#ff3333', '#00bfff', '#ffaa00', '#ab47bc', '#ffeb3b', '#76ff03', '#f06292', '#ff9800', '#00bcd4', '#e91e63', '#00e676', '#9c27b0', '#673ab7', '#3f51b5', '#2196f3', '#03a9f4', '#00bac7', '#009688', '#4caf50', '#8bc34a', '#cddc39', '#ffc107', '#ff5722', '#e040fb', '#ff1744', '#18ffff', '#ffd600', '#ff80ab', '#82b1ff']
    text_positions = ['top center', 'bottom center', 'top right', 'bottom left', 'middle right', 'middle left', 'top left', 'bottom right']

    fig.add_shape(type="rect", x0=100, y0=100, x1=200, y1=200, fillcolor="rgba(0, 255, 136, 0.04)", layer="below", line_width=0)
    fig.add_shape(type="rect", x0=100, y0=0, x1=200, y1=100, fillcolor="rgba(255, 235, 59, 0.04)", layer="below", line_width=0)
    fig.add_shape(type="rect", x0=0, y0=0, x1=100, y1=100, fillcolor="rgba(255, 51, 51, 0.04)", layer="below", line_width=0)
    fig.add_shape(type="rect", x0=0, y0=100, x1=100, y1=200, fillcolor="rgba(0, 191, 255, 0.04)", layer="below", line_width=0)
    fig.add_vline(x=100, line_width=1.5, line_color="#777777", line_dash="dash")
    fig.add_hline(y=100, line_width=1.5, line_color="#777777", line_dash="dash")
    
    fig.add_annotation(x=0.98, y=0.98, text="領先 (Leading)", showarrow=False, xref="paper", yref="paper", font=dict(color="#00ff88", size=24, family="Arial Black"), opacity=0.25)
    fig.add_annotation(x=0.98, y=0.02, text="轉弱 (Weakening)", showarrow=False, xref="paper", yref="paper", font=dict(color="#ffeb3b", size=24, family="Arial Black"), opacity=0.25)
    fig.add_annotation(x=0.02, y=0.02, text="落後 (Lagging)", showarrow=False, xref="paper", yref="paper", font=dict(color="#ff3333", size=24, family="Arial Black"), opacity=0.25)
    fig.add_annotation(x=0.02, y=0.98, text="改善 (Improving)", showarrow=False, xref="paper", yref="paper", font=dict(color="#00bfff", size=24, family="Arial Black"), opacity=0.25)

    for i, col in enumerate(rs_ratio.columns):
        x_data = rs_ratio[col].tail(tail_length).values
        y_data = rs_mom[col].tail(tail_length).values
        if tail_length > 1:
            fig.add_trace(go.Scatter(x=x_data, y=y_data, mode='lines', line=dict(color=colors[i % len(colors)], width=1.0), showlegend=False, hoverinfo='skip'))

    for i, col in enumerate(rs_ratio.columns):
        x_data = rs_ratio[col].tail(tail_length).values
        y_data = rs_mom[col].tail(tail_length).values
        fig.add_trace(go.Scatter(
            x=[x_data[-1]], y=[y_data[-1]], mode='markers+text',
            marker=dict(color=colors[i % len(colors)], size=11, line=dict(color='#FFFFFF', width=1.2)),
            text=[f" <b>{col}</b> "], textposition=text_positions[i % len(text_positions)], textfont=dict(color="#FFFFFF", size=12, family="Arial Black"),
            name=col, hovertemplate=f"<b>{col}</b><br>RS-Ratio: %{{x:.2f}}<br>RS-Mom: %{{y:.2f}}<extra></extra>"
        ))

    min_x, max_x = rs_ratio.tail(tail_length).min().min(), rs_ratio.tail(tail_length).max().max()
    min_y, max_y = rs_mom.tail(tail_length).min().min(), rs_mom.tail(tail_length).max().max()
    padding = 2.5
    fig.update_layout(
        title=dict(text=f"🎡 {chart_title}", font=dict(color="#00ff88", size=22, family="Arial Black")),
        font=dict(color="#FFFFFF"), template="plotly_dark", height=1000, margin=dict(l=50, r=50, t=70, b=60),
        paper_bgcolor="#11141a", plot_bgcolor="#11141a", hovermode="closest", showlegend=True,
        legend=dict(orientation="h", yanchor="bottom", y=-0.12, xanchor="center", x=0.5, font=dict(size=12, color="#FFFFFF"), bgcolor="rgba(0,0,0,0.5)")
    )
    fig.update_xaxes(title_text="RS-Ratio (相對強度 →)", range=[min(min_x - padding, 95), max(max_x + padding, 105)], showgrid=True, gridcolor='#222834', zeroline=False)
    fig.update_yaxes(title_text="RS-Momentum (相對動能 ↑)", range=[min(min_y - padding, 95), max(max_y + padding, 105)], showgrid=True, gridcolor='#222834', zeroline=False)
    st.plotly_chart(fig, use_container_width=True)


# =========================================================================
# 🚀 4. 主頁面渲染函數 (render_page_2m)
# =========================================================================
def render_page_2m():
    st.markdown("## 🎡 艙房 2m：華爾街板塊輪動星盤 (Sector Rotation)")
    st.markdown("大鱷專用：資金從來唔會休息，只會由一個板塊流去另一個板塊。捉住「聰明錢」嘅尾巴，比人早一步埋伏下一個爆升點！")
    st.markdown("---")

    col_a, col_b = st.columns([8, 2])
    with col_b:
        if st.button("🔄 強制刷新所有資金流向數據", use_container_width=True):
            load_all_market_data.clear()
            st.rerun()
            
    with st.spinner("📡 正在掃描並合成全球板塊大數據 (包含所有細分 ETF 與核心股)..."):
        price_data = load_all_market_data()

    if price_data.empty:
        st.error("❌ 無法取得價格數據，請稍後重試。")
        return

    # --- 數據預處理 ---
    macro_series = {name: price_data[symbol] for symbol, name in MACRO_SECTORS.items() if symbol in price_data.columns}
    macro_mom_df = calculate_momentum_table(macro_series)
    
    frontier_series = {}
    for name, info in FRONTIER_SECTORS.items():
        valid_cols = [c for c in info['tickers'] if c in price_data.columns]
        
        # 🛡 確保將 ETF 也加入合成運算，令指標更平滑穩定
        if 'etfs' in info:
            for etf in info['etfs']:
                if etf in price_data.columns and etf not in valid_cols:
                    valid_cols.append(etf)
                    
        if valid_cols:
            pct_change = price_data[valid_cols].pct_change().mean(axis=1)
            frontier_series[name] = (1 + pct_change.fillna(0)).cumprod() * 100
            
    frontier_mom_df = calculate_momentum_table(frontier_series)

    combined_series = {**macro_series, **frontier_series}
    combined_mom_df = calculate_momentum_table(combined_series)
    
    ultimate_series = {name: price_data[symbol] for name, symbol in ULTIMATE_SECTORS.items() if symbol in price_data.columns}
    ultimate_mom_df = calculate_momentum_table(ultimate_series)

    # =================================================================
    # 🎯 展區 1：傳統宏觀 11 大板塊
    # =================================================================
    st.markdown("### 🏛️ 展區一：傳統宏觀 11 大板塊 (GICS)")
    render_momentum_section(macro_mom_df, "傳統宏觀 11 大")
    st.markdown("**⚙️ 調整 [展區一] 星盤參數：**")
    col1_1, col1_2 = st.columns(2)
    with col1_1: tail_1 = st.selectbox("🐍 選擇動態軌跡時間窗", [1, 5, 10, 20, 40], index=2, key="tail_1")
    with col1_2: smooth_1 = st.selectbox("⚙️ RRG 計算靈敏度", [10, 14, 20], index=1, key="smooth_1")
    macro_ratio, macro_mom = calculate_rrg_metrics(price_data, macro_series, window=smooth_1, benchmark='SPY')
    plot_rrg_chart(macro_ratio, macro_mom, tail_1, f"傳統宏觀 11 大板塊 RRG 星盤 (尾巴: {tail_1}天, 平滑: {smooth_1}天)")
    st.markdown("---")

    # =================================================================
    # 🎯 展區 2：前沿 23 大硬科技與主題
    # =================================================================
    st.markdown("### ⚡ 展區二：前沿 23 大硬科技、主題與資源霸權")
    render_momentum_section(frontier_mom_df, "前沿 23 大硬科技")
    st.markdown("**⚙️ 調整 [展區二] 星盤參數：**")
    col2_1, col2_2 = st.columns(2)
    with col2_1: tail_2 = st.selectbox("🐍 選擇動態軌跡時間窗", [1, 5, 10, 20, 40], index=2, key="tail_2")
    with col2_2: smooth_2 = st.selectbox("⚙️ RRG 計算靈敏度", [10, 14, 20], index=1, key="smooth_2")
    frontier_ratio, frontier_mom = calculate_rrg_metrics(price_data, frontier_series, window=smooth_2, benchmark='SPY')
    plot_rrg_chart(frontier_ratio, frontier_mom, tail_2, f"前沿 23 大硬科技與主題 RRG 星盤 (尾巴: {tail_2}天, 平滑: {smooth_2}天)")
    st.markdown("---")

    # =================================================================
    # 🎯 展區 3：全球 34 大板塊同台大混戰
    # =================================================================
    st.markdown("### 🌐 展區三：全球 34 大板塊同台大混戰 (全景對比)")
    render_momentum_section(combined_mom_df, "全球 34 大混戰")
    st.markdown("**⚙ 調整 [展區三] 星盤參數：**")
    col3_1, col3_2 = st.columns(2)
    with col3_1: tail_3 = st.selectbox("🐍 選擇動態軌跡時間窗", [1, 5, 10, 20, 40], index=2, key="tail_3")
    with col3_2: smooth_3 = st.selectbox("⚙️ RRG 計算靈敏度", [10, 14, 20], index=1, key="smooth_3")
    combined_ratio, combined_mom = calculate_rrg_metrics(price_data, combined_series, window=smooth_3, benchmark='SPY')
    plot_rrg_chart(combined_ratio, combined_mom, tail_3, f"全球 34 大板塊大混戰 RRG 星盤 (尾巴: {tail_3}天, 平滑: {smooth_3}天)")
    st.markdown("---")

    # =================================================================
    # 🦅 展區 4：大鱷跨資產預警星盤 (以 TLT 為基準)
    # =================================================================
    st.markdown("### 🦅 展區四：大鱷跨資產預警星盤 (2026 年終極生死共振)")
    render_momentum_section(ultimate_mom_df, "九大跨資產預警")
    st.markdown("**⚙️ 調整 [跨資產預警] 參數：**")
    col4_1, col4_2 = st.columns(2)
    with col4_1: tail_4 = st.selectbox("🐍 選擇動態軌跡時間窗", [1, 5, 10, 20, 40], index=2, key="tail_4_1")
    with col4_2: smooth_4 = st.selectbox("⚙️ RRG 計算靈敏度", [10, 14, 20], index=1, key="smooth_4_1")
    ulti_ratio, ulti_mom = calculate_rrg_metrics(price_data, ultimate_series, window=smooth_4, benchmark='TLT')
    plot_rrg_chart(ulti_ratio, ulti_mom, tail_4, f"🔥 跨資產宏觀生死共振 (基準: TLT 美債) (尾巴: {tail_4}天)")

    st.markdown("---")

    # =========================================================================
    # 📚 大指揮官獨家秘技 (純文字 Markdown 格式)
    # =========================================================================
    st.markdown("## 🦅 爺爺壓箱底傳授：2026 九維跨資產共振 (The Macro End-Game)")
    st.markdown("展區四係華爾街頂級大鱷嘅**「抄底與逃頂核按鈕」**。呢個圖**唔係同 SPY 比較，而係同 TLT (20年期國債/終極避險資產) 比較！**\n\n2026 年宏觀已由 **AI 算力 (SMH)、核能/鈾礦 (URA) 與 地緣軍工 (ITA)** 主導，佢哋已經加入生死共振監測網！")
    
    st.markdown("### 🔥 【核按鈕用法】：")
    st.markdown("* **終極逃頂信號 (Crash Warning)**：當你見到 SPY, HYG, COPX, BTC-USD 呢幾條蛇，集體由右邊急轉彎，插水進入「落後區 (紅)」（即係跑輸 TLT），代表全球大資金正在瘋狂拋售高風險資產，湧入美債避險。**大崩盤即將來臨，清倉保命！**")
    st.markdown("* **終極抄底信號 (Generational Buy)**：當大市一片恐慌，但你見到 HYG (垃圾債) 同 BTC 率先由「落後區」抬頭，衝入「改善區 (藍)」甚至「領先區 (綠)」，代表大鱷已經開始暗中吸籌Risk-On。**呢個就係十年一遇嘅重倉抄底時機！**")
    
    st.markdown("### ⚙️ 雙控制鈕「黃金組合」實戰用法：")
    st.markdown("* **1️⃣ 玩法一：極簡速覽今日大局** ➔ 左手選【1】 ＋ 右手選【14】\n👉 畫面無雜亂線條，只睇今日蛇頭落喺邊個象限，3秒掃完所有大板塊形勢。")
    st.markdown("* **2️⃣ 玩法二：短線狙擊剛起爆妖股** ➔ 左手選【5】 ＋ 右手選【10】\n👉 5天軌跡搭配高靈敏度，第一時間捕抓由「落後區 💀」大角度抬頭衝入「改善區 🚀」嘅板塊。")
    st.markdown("* **3️⃣ 玩法三：跟隨大鱷季度大調倉** ➔ 左手選【20】 ＋ 右手選【20】\n👉 拉長 1 個月軌跡並極致平滑，確認主力資金係咪跨板塊長期轉移。")

    st.markdown("---")

    st.markdown("## ☢️ URA (核能) 與 🧠 SMH (算力) 終極背馳共振戰法")
    st.markdown("在 2026 年的宏觀格局下，**URA（核能與鈾礦）是衡量「全球 AI 物理極限」與「能源通脹」的超級溫度計。**")

    st.markdown("### 🟢 當 URA 處於「領先區 (Leading - 右上角)」")
    st.markdown("**【數學狀態】**：RS-Ratio (相對強度) > 100，RS-Momentum (相對動能) > 100。跑贏大市，而且升勢仲喺度加速！")
    st.markdown("**【宏觀與大鱷解讀：AI 缺電恐慌 ＆ 能源超級週期】**")
    st.markdown("* **「算力盡頭係電力」嘅恐慌發酵**：代表華爾街完全確認咗 AI 數據中心面臨極度嚴重嘅「電力瓶頸」。大資金正在瘋狂押注核電廠、SMR (小型核反應堆) 同鈾礦，認為只有核能先可以滿足 AI 嘅無底洞。")
    st.markdown("* **實體通脹重臨 (Hard Asset Bull Market)**：如果 URA 聯同 COPX (銅礦) 同埋 XLE (傳統能源) 一齊喺領先區，代表全球進入「實體基建通脹」。資金嫌棄虛擬軟件，全面湧入「有實質物理支撐」嘅硬資產。")
    st.markdown("* **戰術行動**：「順勢加倉，咬實唔放！」 呢個時候絕對唔好估頂，核能股嘅爆發力喺牛市中可以非常驚人。同時可以順藤摸瓜，留意「變壓器與電網 (GRID)」係咪都一齊領先。")

    st.markdown("### 🔴 當 URA 處於「落後區 (Lagging - 左下角)」")
    st.markdown("**【數學狀態】**：RS-Ratio (相對強度) < 100，RS-Momentum (相對動能) < 100。跑輸大市，而且跌勢仲未見底！")
    st.markdown("**【宏觀與大鱷解讀：基建冷卻 ＆ 衰退預期】**")
    st.markdown("* **AI 資本支出 (CapEx) 見頂或過度炒作回吐**：如果 SMH (AI 算力) 依然強勢，但 URA 率先跌入落後區，代表市場認為「AI 依然好賺，但短期內核電基建跟唔上/遠水不能救近火」，或者之前鈾礦價格炒得太高，大鱷正在瘋狂獲利回吐 (Take Profit)。")
    st.markdown("* **宏觀經濟衰退陰霾 (Recession Fear)**：核能同鈾礦本質上都係大宗商品 (Commodities)。如果 URA 同埋 COPX (銅礦) 雙雙插水進入落後區，呢個係一個極度危險嘅信號！代表全球製造業同實體需求正在急劇萎縮，大鱷預期經濟即將衰退。")
    st.markdown("* **戰術行動**：「切忌接飛刀！」 千祈唔好見佢平就走去撈底。喺 RRG 裡面，落後區嘅資產可以「落後完再落後」。你要耐心等待佢條貪食蛇尾巴轉向，向上勾起進入「改善區 (Improving - 藍色)」嗰一刻，先至係你出擊抄底嘅最佳時機！")

    st.markdown("---")

    st.markdown("### 🦅 爺爺嘅高階跨資產秘技：看透 URA 與 SMH 嘅「背馳共振」")
    st.markdown("大指揮官，用你啱啱升級嘅 「展區四：跨資產血壓計 (以 TLT 國債為基準)」，你要重點觀察 URA (核能) 同 SMH (AI 算力) 兩條蛇嘅互動：")
    st.markdown("* 🔥 **完美雙核引擎 (Risk-On 極致)**：SMH 同 URA 雙雙手拖手喺領先區 (綠) 齊飛 ➔ AI 軟硬件與物理基建同步大爆發，滿倉進攻！")
    st.markdown("* ⚠️ **算力透支危機 (瓶頸炒作)**：SMH 轉弱跌入黃色區，但 URA 繼續孤軍突入綠色領先區 ➔ 大鱷認為 GPU 已經買得太多，但發現「冇電開機」，於是掟貨 Nvidia，瘋狂炒作核能發電！呢個時候你要減倉晶片，重倉電力與散熱！")
    st.markdown("* 💀 **終極泡沫爆破 (End-Game)**：SMH 同 URA 一齊由右邊急轉彎，向左下角紅色落後區直插 ➔ AI 敘事全面破滅，資金湧入美債 (TLT) 避險。呢個就係爺爺講嘅「清屏核按鈕」！")
    
    # =========================================================================
    # 🗄️ 5. 全球 34 大完整板塊成分股資料庫 (Holdings Database)
    # =========================================================================
    st.markdown("---")
    
    with st.expander("🗄️ 點擊展開：全球 34 大完整板塊成分股資料庫 (Holdings Database)", expanded=False):
        st.markdown("### 🔍 查詢板塊核心成分股與代表 ETF")
        st.markdown("想知道邊隻 ETF 或者邊個板塊包含咩股票？喺度一撳就知！ *(已全面涵蓋 11 大傳統宏觀 GICS 板塊 ＋ 23 大前沿硬科技與主題霸權，共 34 大板塊)*")
        
        sector_names = list(ALL_34_SECTOR_HOLDINGS.keys())
        selected_sector = st.selectbox("👇 選擇要查詢的板塊 (共 34 個)：", sector_names)
        
        sector_info = ALL_34_SECTOR_HOLDINGS[selected_sector]
        etfs_list = sector_info.get('etfs', [])
        tickers_list = sector_info.get('tickers', [])
        
        # 顯示板塊類型標籤 (宏觀板塊 vs 前沿板塊)
        if selected_sector in MACRO_SECTOR_HOLDINGS:
            st.markdown("<span style='background-color:#7c4dff; color:white; padding:3px 10px; border-radius:8px; font-size:12px; font-weight:bold;'>🏛️ 傳統宏觀板塊 (GICS)</span>", unsafe_allow_html=True)
        else:
            st.markdown("<span style='background-color:#00b4d8; color:white; padding:3px 10px; border-radius:8px; font-size:12px; font-weight:bold;'>⚡ 前沿硬科技與主題霸權</span>", unsafe_allow_html=True)
        
        st.markdown("<br>", unsafe_allow_html=True)
        
        # 顯示多個 ETF
        if etfs_list:
            etfs_html = " ".join([f"<span style='background-color:#ffaa00; color:black; padding:4px 10px; border-radius:12px; margin-right:6px; margin-bottom:6px; display:inline-block; font-weight:bold;'>{e}</span>" for e in etfs_list])
            st.markdown(f"**代表 ETF / 基準：**<br><div>{etfs_html}</div>", unsafe_allow_html=True)
        else:
            st.info("**代表 ETF / 基準：** 無專屬純種 ETF (由以下核心個股完全合成)")
        
        st.markdown("<br>", unsafe_allow_html=True)
        
        # 顯示成分股
        tickers_html = " ".join([f"<span style='background-color:#1e88e5; color:white; padding:5px 12px; border-radius:15px; margin-right:8px; margin-bottom:8px; display:inline-block; font-weight:bold; font-family:Arial Black;'>{t}</span>" for t in tickers_list])
        st.markdown(f"**核心成分股 (Tickers)：**")
        st.markdown(f"<div>{tickers_html}</div>", unsafe_allow_html=True)
        st.markdown("<br>", unsafe_allow_html=True)

if __name__ == "__main__":
    render_page_2m()