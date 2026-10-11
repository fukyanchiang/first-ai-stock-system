import streamlit as st
import yfinance as yf
import pandas as pd
import numpy as np
import plotly.graph_objects as go
from plotly.subplots import make_subplots
from datetime import datetime, timedelta
import requests

def app():
    st.title("📈 艙房 2w : 全球四大指數內部結構與背馳雷達")
    st.markdown("""
    **機構級量化監控 (S+ 級終極完全體)**：
    ✅ 零滯後 $\Delta$ 5D 動能捕捉 ✅ 頂/底雙向背馳雷達 ✅ 雙重認證狂暴牛市護罩
    """)
    
    st.divider()

    # --- 1. 設置參數 ---
    col1, col2, col3 = st.columns(3)
    with col1:
        lookback_days = st.slider("歷史回溯日數 (畫圖範圍)", min_value=100, max_value=800, value=365)
    with col2:
        sp500_sample = st.selectbox("🇺🇸 S&P 500 火力控制", ["極速測試 (Top 50)", "中度平衡 (Top 100)", "完全火力 (全量 500 隻)"])
    with col3:
        rut_sample = st.selectbox("🔥 羅素 (S&P 600) 火力控制", ["極速測試 (Top 50)", "中度平衡 (Top 100)", "完全火力 (全量 600 隻)"])
    
    end_date = datetime.today()
    start_date = end_date - timedelta(days=lookback_days)
    fetch_start_date = start_date - timedelta(days=300) 

    # --- 2. 爬蟲與鈦合金名單 ---
    @st.cache_data(ttl=86400) 
    def get_index_tickers(index_type):
        headers = {'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) Chrome/91.0.4472.124 Safari/537.36'}
        urls = {
            "SP500": 'https://en.wikipedia.org/wiki/List_of_S%26P_500_companies',
            "NDX": 'https://en.wikipedia.org/wiki/Nasdaq-100',
            "DOW": 'https://en.wikipedia.org/wiki/Dow_Jones_Industrial_Average',
            "RUT_PROXY": 'https://en.wikipedia.org/wiki/List_of_S%26P_600_companies'
        }
        
        valid_tickers = []
        try:
            response = requests.get(urls[index_type], headers=headers)
            response.raise_for_status() 
            dfs = pd.read_html(response.text)
            for df in dfs:
                for col in df.columns:
                    col_str = str(col).lower()
                    if 'symbol' in col_str or 'ticker' in col_str:
                        temp = [str(t).split('[')[0].strip().replace('.', '-') for t in df[col].tolist() if pd.notna(t)]
                        if len(temp) > len(valid_tickers): valid_tickers = temp
        except Exception: pass 
            
        if valid_tickers: return valid_tickers
        fallbacks = {
            "DOW": ['AAPL', 'AMGN', 'AMZN', 'AXP', 'BA', 'CAT', 'CRM', 'CSCO', 'CVX', 'DIS', 'DOW', 'GS', 'HD', 'HON', 'IBM', 'INTC', 'JNJ', 'JPM', 'KO', 'MCD', 'MMM', 'MRK', 'MSFT', 'NKE', 'PG', 'TRV', 'UNH', 'V', 'VZ', 'WMT'],
            "NDX": ['AAPL', 'MSFT', 'AMZN', 'NVDA', 'META', 'TSLA', 'GOOGL', 'GOOG', 'AVGO', 'PEP', 'COST', 'CSCO', 'TMUS', 'ADBE', 'TXN', 'CMCSA', 'AMD', 'NFLX', 'QCOM', 'INTC', 'HON', 'INTU', 'AMGN', 'SBUX', 'AMAT', 'ISRG', 'BKNG', 'MDLZ', 'GILD', 'LRCX', 'ADP', 'ADI', 'VRTX', 'REGN', 'PANW', 'SNPS', 'KLAC', 'CDNS', 'MELI', 'PYPL', 'MU', 'CSX', 'MAR', 'ASML', 'CTAS', 'NXPI', 'MNST', 'ORLY', 'WDAY', 'ABNB', 'LULU', 'PCAR', 'CRWD', 'MRVL', 'KDP', 'PAYX', 'DXCM', 'CPRT', 'ROST', 'SGEN', 'KHC', 'ODFL', 'AEP', 'IDXX', 'EA', 'EXC', 'FAST', 'BIIB', 'CTSH', 'VRSK', 'AZN', 'GEHC', 'CSGP', 'ON', 'CEG', 'GFS', 'CDW', 'FANG', 'WBD', 'DLTR', 'MCHP', 'TEAM', 'DDOG', 'ZS', 'WBA', 'ILMN', 'SIRI', 'LCID', 'ENPH', 'PDD', 'JD', 'NTES', 'BIDU']
        }
        return fallbacks.get(index_type, [])

    # --- 3. 四維運算核心 (+ 注入 Delta 5D 動能) ---
    @st.cache_data(ttl=3600) 
    def calculate_4d_breadth(start, end, fetch_start, index_type, etf_symbol, sp500_mode, rut_mode):
        all_tickers = get_index_tickers(index_type)
        if not all_tickers: return pd.DataFrame()
            
        if index_type == "SP500":
            tickers = all_tickers[:50] if "Top 50" in sp500_mode else all_tickers[:100] if "Top 100" in sp500_mode else all_tickers
        elif index_type == "RUT_PROXY":
            tickers = all_tickers[:50] if "Top 50" in rut_mode else all_tickers[:100] if "Top 100" in rut_mode else all_tickers
        else:
            tickers = all_tickers 
            
        spy_df = yf.download(etf_symbol, start=fetch_start, end=end, progress=False)
        if spy_df.empty: return pd.DataFrame()
            
        data = yf.download(tickers, start=fetch_start, end=end, progress=False)
        close_prices = data['Close'] if 'Close' in data.columns.levels[0] else data
        if isinstance(close_prices, pd.Series): close_prices = close_prices.to_frame()
            
        ma20 = close_prices.rolling(window=20).mean()
        ma50 = close_prices.rolling(window=50).mean()
        ma200 = close_prices.rolling(window=200).mean()
        total_valid = close_prices.notna().sum(axis=1).replace(0, np.nan)
        
        df = pd.DataFrame(index=spy_df.index)
        df['Index_Close'] = spy_df['Close'].iloc[:, 0] if isinstance(spy_df['Close'], pd.DataFrame) else spy_df['Close']
        df['Price_above_50'] = ((close_prices > ma50).sum(axis=1) / total_valid * 100).reindex(df.index)
        df['Price_above_200'] = ((close_prices > ma200).sum(axis=1) / total_valid * 100).reindex(df.index)
        df['MA20_above_50'] = ((ma20 > ma50).sum(axis=1) / total_valid * 100).reindex(df.index)
        df['MA50_above_200'] = ((ma50 > ma200).sum(axis=1) / total_valid * 100).reindex(df.index)
        
        # ⚡ 核心升級 1：計算 5 日動能變動率 (Delta 5D)
        df['Delta_5D'] = df['Price_above_50'].diff(5)
        
        return df.loc[start:end].dropna(subset=['Index_Close', 'Price_above_50'])

    # --- 4. S+ 級智能背馳與動能雷達 ---
    def scan_smart_signals(df, window=20):
        top_div = []    # 頂背馳
        bottom_div = [] # 底背馳
        momentum_hook = [] # ⚡ 資金異動 (Delta 5D)
        
        if len(df) < window: return top_div, bottom_div, momentum_hook
        
        last_top = -999 
        last_bottom = -999
        last_hook = -999
        
        for i in range(window, len(df)):
            idx_close = df['Index_Close'].iloc[i]
            breadth = df['Price_above_50'].iloc[i]
            
            # 🚨 升級 2A：頂背馳
            if idx_close >= df['Index_Close'].iloc[i-window:i].max():
                if breadth < (df['Price_above_50'].iloc[i-window:i].max() - 10): # 嚴格觸發標準改為 10%
                    if i - last_top > 15: 
                        top_div.append(df.index[i])
                        last_top = i 
                        
            # 🟢 升級 2B：底背馳
            if idx_close <= df['Index_Close'].iloc[i-window:i].min():
                if breadth > (df['Price_above_50'].iloc[i-window:i].min() + 10): 
                    if i - last_bottom > 15:
                        bottom_div.append(df.index[i])
                        last_bottom = i
                        
            # ⚡ 升級 1B：底層資金異動 (Delta 5D 捕捉 V 彈)
            if breadth < 35 and df['Delta_5D'].iloc[i] > 15: # 在低位突然 5日內飆升 15%
                if i - last_hook > 10:
                    momentum_hook.append(df.index[i])
                    last_hook = i

        return top_div, bottom_div, momentum_hook

    # --- 畫圖函數 ---
    def plot_breadth_chart(df, y_col, title, etf_name, signals=None):
        top_div, bottom_div, momentum_hook = signals if signals else ([], [], [])
        
        fig = make_subplots(specs=[[{"secondary_y": True}]])
        fig.add_trace(go.Scatter(x=df.index, y=df['Index_Close'], name=f"{etf_name} (右軸)", line=dict(color='orange', width=2)), secondary_y=True)
        fig.add_trace(go.Scatter(x=df.index, y=df[y_col], name=f"{title} (左軸)", line=dict(color='black', width=1.5)), secondary_y=False)
        fig.add_hrect(y0=70, y1=100, line_width=0, fillcolor="red", opacity=0.1, secondary_y=False)
        fig.add_hrect(y0=0, y1=30, line_width=0, fillcolor="green", opacity=0.1, secondary_y=False)
        
        # 標記 S+ 信號
        for sig in top_div:
            fig.add_annotation(x=sig, y=df.loc[sig, y_col], text="🚨 頂背馳", showarrow=True, arrowhead=1, ax=0, ay=-40, font=dict(color="red", size=10), bordercolor="red")
        for sig in bottom_div:
            fig.add_annotation(x=sig, y=df.loc[sig, y_col], text="🟢 底背馳", showarrow=True, arrowhead=1, ax=0, ay=40, font=dict(color="green", size=10), bordercolor="green")
        for sig in momentum_hook:
            fig.add_annotation(x=sig, y=df.loc[sig, y_col], text="⚡ 資金異動", showarrow=True, arrowhead=1, ax=0, ay=30, font=dict(color="blue", size=10), bordercolor="blue")
                
        fig.update_layout(height=400, margin=dict(l=20, r=20, t=30, b=20), legend=dict(orientation="h", yanchor="bottom", y=1.02, xanchor="right", x=1))
        fig.update_yaxes(title_text="比率 (%)", range=[0, 100], secondary_y=False)
        return fig

    # ==========================================
    # 🚀 執行區：四大指數矩陣
    # ==========================================
    INDEX_CONFIG = [
        {"name": "🇺🇸 S&P 500 (主宰全球)", "etf": "SPY", "type": "SP500"},
        {"name": "🦅 Nasdaq 100 (科技巨頭)", "etf": "QQQ", "type": "NDX"},
        {"name": "🏛️ Dow Jones (傳統三十大)", "etf": "DIA", "type": "DOW"},
        {"name": "🔥 Russell 動能 (細價股 S&P 600)", "etf": "IWM", "type": "RUT_PROXY"}
    ]

    for config in INDEX_CONFIG:
        st.markdown(f"## {config['name']}")
        
        with st.spinner(f"正在從華爾街提取 {config['name']} 內部市寬數據..."):
            df = calculate_4d_breadth(start_date, end_date, fetch_start_date, config['type'], config['etf'], sp500_sample, rut_sample)
            
            if not df.empty:
                # 獲取 S+ 雷達信號
                signals = scan_smart_signals(df)
                top_div, bottom_div, momentum_hook = signals
                
                # S+ 級診斷面板
                curr_val = df['Price_above_50'].iloc[-1]
                ma50_200_val = df['MA50_above_200'].iloc[-1]
                
                # 🛡️ 核心升級 3：雙重認證狂暴牛市護罩 (Melt-Up Guard)
                if ma50_200_val > 60 and curr_val > 80:
                    st.warning(f"🔥 【狂暴牛市護罩啟動】長線極強 (50>200MA: {ma50_200_val:.1f}%) 疊加市寬超買 ({curr_val:.1f}%)。系統判定為「強力順勢推進」，切勿盲目估頂做淡！改用移動止賺。")
                elif len(top_div) > 0 and (df.index[-1] - top_div[-1]).days < 10:
                    st.error(f"🚨 【核彈級警報】最近 10 日內偵測到「頂背馳」！指數強衝，士兵走佬。大暴跌風險極高！")
                elif len(bottom_div) > 0 and (df.index[-1] - bottom_div[-1]).days < 10:
                    st.success(f"🟢 【絕地反擊】最近 10 日內偵測到「底背馳」！指數新低但市寬拒絕再跌，準備撈底！")
                elif len(momentum_hook) > 0 and (df.index[-1] - momentum_hook[-1]).days < 5:
                    st.info(f"⚡ 【資金底層異動】市寬出現極高速勾頭向上 (Delta 5D 爆發)。大戶正在靜靜雞掃貨！")
                elif curr_val < 20: 
                    st.success(f"🧲 【血流成河】市寬跌入極度超賣區 ({curr_val:.1f}%)，密切留意 ⚡異動信號出現。")
                else:
                    st.info(f"⚖️ 【大局觀中性】市寬處於健康波動區間 ({curr_val:.1f}%)。")
                
                # 畫圖
                colA, colB = st.columns(2)
                with colA:
                    st.subheader("1️⃣ 短中線強弱 (股價 > 50MA)")
                    st.plotly_chart(plot_breadth_chart(df, 'Price_above_50', "Price > 50MA", config['etf'], signals), use_container_width=True)
                    st.subheader("3️⃣ 短中線黃金交叉 (20MA > 50MA)")
                    st.plotly_chart(plot_breadth_chart(df, 'MA20_above_50', "20MA > 50MA", config['etf']), use_container_width=True)
                with colB:
                    st.subheader("2️⃣ 長線牛熊情緒 (股價 > 200MA)")
                    st.plotly_chart(plot_breadth_chart(df, 'Price_above_200', "Price > 200MA", config['etf']), use_container_width=True)
                    st.subheader("4️⃣ 長線大牛熊分水嶺 (50MA > 200MA)")
                    st.plotly_chart(plot_breadth_chart(df, 'MA50_above_200', "50MA > 200MA", config['etf']), use_container_width=True)
                
                st.divider() 
            else:
                st.error(f"❌ 獲取 {config['name']} 數據失敗。")

if __name__ == "__main__":
    app()