import streamlit as st
import yfinance as yf
import pandas as pd
import plotly.graph_objects as go
from plotly.subplots import make_subplots

# ===================================================
# 🗄️ 港股核心成份股字典 (100% 官方全量覆蓋)
# ===================================================
# 恒生指數 (HSI) - 81 隻全量藍籌覆蓋
HSI_TICKERS = "0001.HK,0002.HK,0003.HK,0005.HK,0006.HK,0011.HK,0012.HK,0016.HK,0017.HK,0027.HK,0066.HK,0101.HK,0175.HK,0241.HK,0267.HK,0288.HK,0291.HK,0293.HK,0316.HK,0322.HK,0386.HK,0388.HK,0669.HK,0688.HK,0700.HK,0762.HK,0823.HK,0857.HK,0868.HK,0883.HK,0914.HK,0939.HK,0941.HK,0960.HK,0968.HK,0981.HK,0992.HK,1024.HK,1038.HK,1044.HK,1088.HK,1093.HK,1109.HK,1113.HK,1177.HK,1209.HK,1211.HK,1299.HK,1378.HK,1398.HK,1810.HK,1876.HK,1888.HK,1928.HK,1929.HK,1997.HK,2015.HK,2020.HK,2269.HK,2313.HK,2318.HK,2319.HK,2331.HK,2359.HK,2382.HK,2388.HK,2628.HK,2899.HK,3690.HK,3968.HK,3988.HK,6098.HK,6690.HK,6862.HK,9618.HK,9633.HK,9868.HK,9888.HK,9961.HK,9988.HK,9999.HK"

# 恒生科技指數 (HSTECH) - 30 隻全量覆蓋
HSTECH_TICKERS = "0020.HK,0136.HK,0241.HK,0268.HK,0285.HK,0316.HK,0522.HK,0700.HK,0772.HK,0780.HK,0909.HK,0981.HK,0992.HK,1024.HK,1347.HK,1797.HK,1810.HK,1833.HK,2015.HK,2382.HK,3690.HK,3888.HK,6618.HK,6690.HK,9618.HK,9626.HK,9866.HK,9868.HK,9888.HK,9988.HK"

# 國企指數 (HSCEI) - 51 隻全量覆蓋
HSCEI_TICKERS = "0175.HK,0268.HK,0291.HK,0386.HK,0700.HK,0762.HK,0857.HK,0868.HK,0883.HK,0909.HK,0914.HK,0939.HK,0941.HK,0968.HK,0981.HK,0992.HK,1024.HK,1044.HK,1088.HK,1093.HK,1109.HK,1177.HK,1211.HK,1398.HK,1772.HK,1810.HK,1876.HK,1898.HK,1997.HK,2015.HK,2020.HK,2202.HK,2269.HK,2318.HK,2319.HK,2333.HK,2359.HK,2601.HK,2628.HK,2727.HK,2899.HK,3328.HK,3690.HK,3968.HK,6690.HK,6837.HK,6862.HK,9618.HK,9888.HK,9988.HK,9999.HK"

INDEX_COMPONENTS = {
    "恒生指數 (HSI)": HSI_TICKERS.split(","),
    "恒生科技指數 (HSTECH)": HSTECH_TICKERS.split(","),
    "國企指數 (HSCEI)": HSCEI_TICKERS.split(",")
}

# 港股對應 ETF (用作主圖 K 線顯示)
ETF_MAPPING = {
    "恒生指數 (HSI)": "2833.HK",      # 恒指 ETF (盈富基金)
    "恒生科技指數 (HSTECH)": "3032.HK", # 恒生科技 ETF
    "國企指數 (HSCEI)": "2828.HK"       # 國企 ETF (恒生中國企業)
}

# ===================================================
# ⚙️ 核心運算引擎 (加入 250日新高/新低計算)
# ===================================================
@st.cache_data(ttl=1800, show_spinner=False)
def fetch_and_calculate_hk_breadth(index_name):
    tickers = INDEX_COMPONENTS[index_name]
    etf_ticker = ETF_MAPPING[index_name]
    
    # 下載最少 250 日（1年）資料以計算 52 週新高新低
    try:
        raw_data = yf.download(tickers + [etf_ticker], period="250d", auto_adjust=True, progress=False, group_by="ticker")
    except Exception as e:
        return pd.DataFrame(), pd.DataFrame(), pd.DataFrame()

    if raw_data.empty:
        return pd.DataFrame(), pd.DataFrame(), pd.DataFrame()

    # 提取 ETF 主圖價格
    try:
        if isinstance(raw_data.columns, pd.MultiIndex):
            df_etf = raw_data[etf_ticker][['Open', 'High', 'Low', 'Close']].copy().dropna()
        else:
            df_etf = pd.DataFrame()
    except Exception:
        df_etf = pd.DataFrame()

    # 提取所有成份股 Close 與 High/Low 以計算新高新低
    close_prices, high_prices, low_prices = {}, {}, {}
    if isinstance(raw_data.columns, pd.MultiIndex):
        for tick in tickers:
            if tick in raw_data.columns.get_level_values(0):
                if 'Close' in raw_data[tick] and 'High' in raw_data[tick] and 'Low' in raw_data[tick]:
                    close_prices[tick] = raw_data[tick]['Close']
                    high_prices[tick] = raw_data[tick]['High']
                    low_prices[tick] = raw_data[tick]['Low']
    
    if not close_prices:
        return pd.DataFrame(), pd.DataFrame(), pd.DataFrame()
        
    comp_close = pd.DataFrame(close_prices).dropna(how='all', axis=1).ffill()
    comp_high = pd.DataFrame(high_prices).dropna(how='all', axis=1).ffill()
    comp_low = pd.DataFrame(low_prices).dropna(how='all', axis=1).ffill()
    
    total_valid = comp_close.notna().sum(axis=1)
    
    # 1. 矩陣化極速計算 20MA 同 50MA 市寬
    ma20 = comp_close.rolling(window=20).mean()
    ma50 = comp_close.rolling(window=50).mean()
    above_ma20 = (comp_close > ma20).sum(axis=1)
    above_ma50 = (comp_close > ma50).sum(axis=1)
    
    breadth_fast = (above_ma20 / total_valid * 100).fillna(0)
    breadth_slow = (above_ma50 / total_valid * 100).fillna(0)
    
    df_breadth = pd.DataFrame({
        "Fast_20MA": breadth_fast,
        "Slow_50MA": breadth_slow
    })

    # 2. 計算 52 週 (250日) 新高新低 (NH/NL)
    rolling_250_high = comp_high.rolling(window=250, min_periods=60).max()
    rolling_250_low = comp_low.rolling(window=250, min_periods=60).min()
    
    new_highs_count = (comp_high >= rolling_250_high).sum(axis=1)
    new_lows_count = (comp_low <= rolling_250_low).sum(axis=1)
    net_new_highs = new_highs_count - new_lows_count

    df_nhnl = pd.DataFrame({
        "New_Highs": new_highs_count,
        "New_Lows": new_lows_count,       # 稍後繪圖時會乘 -1
        "Net_Highs": net_new_highs,
        "Total_Valid": total_valid
    })
    
    return df_etf, df_breadth, df_nhnl

# ===================================================
# 🔴 頁面渲染 (三層樓終極版)
# ===================================================
def render_page_2e_hk():
    st.markdown("<h1 style='color:#ff0055; font-family:Arial Black;'>🇭🇰 艙房 2e-HK：港股原版真實市寬 + 動能掃描</h1>", unsafe_allow_html=True)
    st.markdown("<p style='color:#aaa;'>三維矩陣：價量背離 (主圖) ＋ 52週新高新低 (副圖1) ＋ 淨推進力 (副圖2)</p>", unsafe_allow_html=True)
    st.markdown("<hr style='border:3px solid #ff0055; margin-bottom:20px;'>", unsafe_allow_html=True)
    
    all_indices = ["恒生指數 (HSI)", "恒生科技指數 (HSTECH)", "國企指數 (HSCEI)"]
    count_map = {"恒生指數 (HSI)": len(INDEX_COMPONENTS["恒生指數 (HSI)"]), 
                 "恒生科技指數 (HSTECH)": len(INDEX_COMPONENTS["恒生科技指數 (HSTECH)"]), 
                 "國企指數 (HSCEI)": len(INDEX_COMPONENTS["國企指數 (HSCEI)"])}
    
    for target_index in all_indices:
        with st.spinner(f"📡 正在自動全量加載 {target_index} (共 {count_map[target_index]} 隻成份股)..."):
            df_etf, df_breadth, df_nhnl = fetch_and_calculate_hk_breadth(target_index)

        if df_etf.empty or df_breadth.empty or df_nhnl.empty:
            st.error(f"⚠️ 無法獲取 {target_index} 數據，請稍後重試。")
            continue

        # 對齊日期 (取最近 180 天讓圖表清晰展示)
        df_etf = df_etf.tail(180)
        df_breadth = df_breadth.reindex(df_etf.index).fillna(method='ffill')
        df_nhnl = df_nhnl.reindex(df_etf.index).fillna(0)

        # ==========================================
        # 📈 繪製三層圖表 (3 Subplots)
        # ==========================================
        fig = make_subplots(
            rows=3, cols=1, shared_xaxes=True, vertical_spacing=0.03,
            row_heights=[0.5, 0.25, 0.25], # 50%, 25%, 25% 比例分配
            specs=[[{"secondary_y": True}], [{"secondary_y": False}], [{"secondary_y": False}]]
        )

        # ------------------------------------
        # 🏢 第一層：主圖 K線 + 快慢市寬
        # ------------------------------------
        fig.add_trace(go.Candlestick(
            x=df_etf.index, open=df_etf['Open'], high=df_etf['High'], low=df_etf['Low'], close=df_etf['Close'], 
            name=f'{ETF_MAPPING[target_index]} 價格',
            increasing_line_color='#26a69a', decreasing_line_color='#ef5350', showlegend=False
        ), row=1, col=1, secondary_y=False)

        fig.add_trace(go.Scatter(
            x=df_breadth.index, y=df_breadth['Fast_20MA'], mode='lines', line=dict(color='#9c27b0', width=2), name='20MA %'
        ), row=1, col=1, secondary_y=True)

        fig.add_trace(go.Scatter(
            x=df_breadth.index, y=df_breadth['Slow_50MA'], mode='lines', line=dict(color='#2196f3', width=2), name='50MA %'
        ), row=1, col=1, secondary_y=True)

        # 畫警戒橫線 (掛在第一層的右 Y 軸)
        hline_configs = [(85, '#4caf50', 'dash'), (75, '#4caf50', 'dash'), (25, '#4caf50', 'dash'), (15, '#4caf50', 'dash'),
                         (90, '#e91e63', 'solid'), (70, '#e91e63', 'solid'), (30, '#00bcd4', 'solid'), (17.5, '#00bcd4', 'solid'), (5, '#00bcd4', 'solid')]
        for y_val, color, style in hline_configs:
            fig.add_hline(y=y_val, line_dash=style, line_color=color, line_width=1, opacity=0.5, row=1, col=1, secondary_y=True)

        # ------------------------------------
        # 🏢 第二層：絕對新高 / 新低 (Gross NH/NL)
        # ------------------------------------
        # 綠柱向上 (新高)
        fig.add_trace(go.Bar(
            x=df_nhnl.index, y=df_nhnl['New_Highs'], 
            marker_color='#4caf50', name='創52週新高 (隻)',
            hovertemplate='%{y} 隻<extra></extra>'
        ), row=2, col=1)
        
        # 紅柱向下 (新低，數值乘 -1)
        fig.add_trace(go.Bar(
            x=df_nhnl.index, y=-df_nhnl['New_Lows'], 
            marker_color='#e91e63', name='創52週新低 (隻)',
            hovertemplate='%{customdata} 隻<extra></extra>',
            customdata=df_nhnl['New_Lows'] # Hover 時顯示正數
        ), row=2, col=1)

        # ------------------------------------
        # 🏢 第三層：淨新高推進力 (Net NH-NL)
        # ------------------------------------
        # 根據正負數給予綠紅顏色
        net_colors = ['#4caf50' if val >= 0 else '#e91e63' for val in df_nhnl['Net_Highs']]
        fig.add_trace(go.Bar(
            x=df_nhnl.index, y=df_nhnl['Net_Highs'], 
            marker_color=net_colors, name='淨新高 (隻)',
            hovertemplate='淨值: %{y} 隻<extra></extra>'
        ), row=3, col=1)

        # ==========================================
        # 🎨 圖表排版與美化 (🌟 爺爺修正了字體顏色)
        # ==========================================
        fig.update_layout(
            title=dict(text=f"🎯 {target_index} 多維度動能掃描 (全陣列 {count_map[target_index]} 隻)", font=dict(color='white', size=22)),
            template="plotly_dark", height=850, margin=dict(l=50, r=60, t=60, b=20),
            xaxis_rangeslider_visible=False, showlegend=True, barmode='relative',
            font=dict(color="white"), # 🌟 強制全域字體變白
            legend=dict(orientation="h", yanchor="bottom", y=1.01, xanchor="right", x=1, font=dict(color="white")), # 🌟 強制圖例變白
            paper_bgcolor="#1e212b", plot_bgcolor="#1e212b"
        )
        
        # Y 軸設定
        fig.update_yaxes(title_text="價格", row=1, col=1, secondary_y=False, gridcolor="#333", showgrid=True)
        fig.update_yaxes(title_text="市寬 %", range=[0, 100], row=1, col=1, secondary_y=True, showgrid=False, tickvals=[5,15,17.5,25,30,50,70,75,85,90], tickfont=dict(color="#ff0055"))
        fig.update_yaxes(title_text="新高/低", row=2, col=1, gridcolor="#333", zerolinecolor="#fff", zerolinewidth=1)
        fig.update_yaxes(title_text="淨新高", row=3, col=1, gridcolor="#333", zerolinecolor="#fff", zerolinewidth=1)
        
        # 隱藏上面兩層的 X 軸日期字，只在最底層顯示
        fig.update_xaxes(showticklabels=False, row=1, col=1, gridcolor="#333")
        fig.update_xaxes(showticklabels=False, row=2, col=1, gridcolor="#333")
        fig.update_xaxes(showticklabels=True, row=3, col=1, gridcolor="#333")

        st.plotly_chart(fig, use_container_width=True, config={'displayModeBar': True})
        st.markdown("<hr style='border:1px dashed #555; margin: 30px 0;'>", unsafe_allow_html=True)

if __name__ == "__main__":
    render_page_2e_hk()