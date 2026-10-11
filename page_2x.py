import streamlit as st
import yfinance as yf
import pandas as pd
import numpy as np
import plotly.graph_objects as go
from plotly.subplots import make_subplots
from datetime import datetime, timedelta
import requests

def app():
    st.title("⚔️ 艙房 2x : 華爾街市寬雙核神兵 (MCO & ZBT)")
    st.markdown("""
    **機構級量化雙核引擎**：
    左手 **MCO 零軸動能狙擊槍** (捕捉極速波段)，右手 **ZBT 10日大市推力核彈** (捕捉歷史大底)。
    底層數據 100% 復用，無損效能，四大指數同步雙向掃描！
    """)
    
    st.divider()

    # --- 1. 設置參數 ---
    col1, col2, col3 = st.columns(3)
    with col1:
        lookback_days = st.slider("歷史回溯日數 (畫圖範圍)", min_value=100, max_value=800, value=365)
    with col2:
        sp500_sample = st.selectbox("🇺🇸 S&P 500 火力控制", ["極速測試 (Top 50)", "中度平衡 (Top 100)", "完全火力 (全量 500 隻)"], index=2)
    with col3:
        rut_sample = st.selectbox("🔥 羅素 (S&P 600) 火力控制", ["極速測試 (Top 50)", "中度平衡 (Top 100)", "完全火力 (全量 600 隻)"], index=2)
    
    end_date = datetime.today()
    start_date = end_date - timedelta(days=lookback_days)
    # ZBT 同 MCO 需要 EMA，需要提早最少 100 日攞數據做緩衝，確保第一日數值準確
    fetch_start_date = start_date - timedelta(days=150) 

    # --- 2. 爬蟲與鈦合金備用名單 (完美復用 2w 的穩健邏輯) ---
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
                    if 'symbol' in str(col).lower() or 'ticker' in str(col).lower():
                        temp = [str(t).split('[')[0].strip().replace('.', '-') for t in df[col].tolist() if pd.notna(t)]
                        if len(temp) > len(valid_tickers): valid_tickers = temp
        except Exception: pass 
            
        if valid_tickers: return valid_tickers
        
        # 鈦合金保底名單
        fallbacks = {
            "DOW": ['AAPL', 'AMGN', 'AMZN', 'AXP', 'BA', 'CAT', 'CRM', 'CSCO', 'CVX', 'DIS', 'DOW', 'GS', 'HD', 'HON', 'IBM', 'INTC', 'JNJ', 'JPM', 'KO', 'MCD', 'MMM', 'MRK', 'MSFT', 'NKE', 'PG', 'TRV', 'UNH', 'V', 'VZ', 'WMT'],
            "NDX": ['AAPL', 'MSFT', 'AMZN', 'NVDA', 'META', 'TSLA', 'GOOGL', 'GOOG', 'AVGO', 'PEP', 'COST', 'CSCO', 'TMUS', 'ADBE', 'TXN', 'CMCSA', 'AMD', 'NFLX', 'QCOM', 'INTC', 'HON', 'INTU', 'AMGN', 'SBUX', 'AMAT', 'ISRG', 'BKNG', 'MDLZ', 'GILD', 'LRCX', 'ADP', 'ADI', 'VRTX', 'REGN', 'PANW', 'SNPS', 'KLAC', 'CDNS', 'MELI', 'PYPL', 'MU', 'CSX', 'MAR', 'ASML', 'CTAS', 'NXPI', 'MNST', 'ORLY', 'WDAY', 'ABNB', 'LULU', 'PCAR', 'CRWD', 'MRVL', 'KDP', 'PAYX', 'DXCM', 'CPRT', 'ROST', 'SGEN', 'KHC', 'ODFL', 'AEP', 'IDXX', 'EA', 'EXC', 'FAST', 'BIIB', 'CTSH', 'VRSK', 'AZN', 'GEHC', 'CSGP', 'ON', 'CEG', 'GFS', 'CDW', 'FANG', 'WBD', 'DLTR', 'MCHP', 'TEAM', 'DDOG', 'ZS', 'WBA', 'ILMN', 'SIRI', 'LCID', 'ENPH', 'PDD', 'JD', 'NTES', 'BIDU']
        }
        return fallbacks.get(index_type, [])

    # --- 3. 雙核神兵運算核心 (只抓一次數據，計足兩套神兵) ---
    @st.cache_data(ttl=3600) 
    def calculate_mco_zbt(start, end, fetch_start, index_type, etf_symbol, sp500_mode, rut_mode):
        all_tickers = get_index_tickers(index_type)
        if not all_tickers: return pd.DataFrame()
            
        # 火力控制
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
            
        # 1. 每日計算：淨上升股數 (Advances) 同 下跌股數 (Declines)
        pct_change = close_prices.diff()
        advances = (pct_change > 0).sum(axis=1)
        declines = (pct_change < 0).sum(axis=1)
        
        ad_net = advances - declines
        total_issues = (advances + declines).replace(0, np.nan)
        ad_ratio = (advances / total_issues) * 100 # 轉做百分比
        
        df = pd.DataFrame(index=spy_df.index)
        df['Index_Close'] = spy_df['Close'].iloc[:, 0] if isinstance(spy_df['Close'], pd.DataFrame) else spy_df['Close']
        
        # 2. 運算 MCO (McClellan Oscillator) : 19 EMA - 39 EMA
        ema19 = ad_net.ewm(span=19, adjust=False).mean()
        ema39 = ad_net.ewm(span=39, adjust=False).mean()
        df['MCO'] = (ema19 - ema39).reindex(df.index)
        
        # 3. 運算 ZBT (Zweig Breadth Thrust) : AD Ratio 的 10 日 EMA
        df['ZBT'] = ad_ratio.ewm(span=10, adjust=False).mean().reindex(df.index)
        
        return df.loc[start:end].dropna(subset=['Index_Close', 'MCO'])

    # --- 4. 雷達掃描算法 ---
    def scan_signals(df):
        mco_signals = [] # 零軸黃金交叉
        zbt_signals = [] # 10日內 <40% 爆上 >61.5%
        
        if len(df) < 15: return mco_signals, zbt_signals
        
        last_mco_sig = -999
        last_zbt_sig = -999
        
        for i in range(10, len(df)):
            # 🟢 MCO 零軸交叉狙擊 (尋日負，今日正)
            if df['MCO'].iloc[i] > 0 and df['MCO'].iloc[i-1] <= 0:
                if i - last_mco_sig > 10: # 冷卻期
                    mco_signals.append(df.index[i])
                    last_mco_sig = i
                    
            # 🚀 ZBT 核彈大推力 (今日 > 61.5%，且過去 10 日內曾經 < 40%)
            if df['ZBT'].iloc[i] > 61.5:
                if df['ZBT'].iloc[i-10:i].min() < 40:
                    if i - last_zbt_sig > 20: # ZBT 冷卻期要長啲，因為係大底
                        zbt_signals.append(df.index[i])
                        last_zbt_sig = i
                        
        return mco_signals, zbt_signals

    # --- 畫圖函數 ---
    def plot_mco_chart(df, etf_name, signals):
        fig = make_subplots(specs=[[{"secondary_y": True}]])
        # 畫指數
        fig.add_trace(go.Scatter(x=df.index, y=df['Index_Close'], name=f"{etf_name} (右軸)", line=dict(color='orange', width=2)), secondary_y=True)
        # 畫 MCO 柱狀圖 (正綠負紅)
        colors = ['rgba(0, 200, 0, 0.6)' if val > 0 else 'rgba(200, 0, 0, 0.6)' for val in df['MCO']]
        fig.add_trace(go.Bar(x=df.index, y=df['MCO'], name="MCO (左軸)", marker_color=colors), secondary_y=False)
        
        # 畫信號
        for sig in signals:
            fig.add_annotation(x=sig, y=0, text="🟢 動能交叉", showarrow=True, arrowhead=1, ax=0, ay=40, font=dict(color="green", size=10), bordercolor="green", secondary_y=False)
            
        fig.update_layout(height=400, margin=dict(l=20, r=20, t=30, b=20), legend=dict(orientation="h", yanchor="bottom", y=1.02, xanchor="right", x=1))
        fig.update_yaxes(title_text="MCO 擺盪值", secondary_y=False)
        return fig

    def plot_zbt_chart(df, etf_name, signals):
        fig = make_subplots(specs=[[{"secondary_y": True}]])
        # 畫指數
        fig.add_trace(go.Scatter(x=df.index, y=df['Index_Close'], name=f"{etf_name} (右軸)", line=dict(color='orange', width=2)), secondary_y=True)
        # 畫 ZBT 線
        fig.add_trace(go.Scatter(x=df.index, y=df['ZBT'], name="ZBT 10-EMA % (左軸)", line=dict(color='blue', width=1.5)), secondary_y=False)
        
        # 畫 40% 同 61.5% 兩條生死線
        fig.add_hline(y=61.5, line_dash="dash", line_color="green", annotation_text="61.5% (核彈引爆線)")
        fig.add_hline(y=40.0, line_dash="dash", line_color="red", annotation_text="40.0% (恐慌極值區)")
        
        for sig in signals:
            fig.add_annotation(x=sig, y=df.loc[sig, 'ZBT'], text="🚀 ZBT 掃底炮", showarrow=True, arrowhead=1, ax=0, ay=-40, font=dict(color="blue", size=12, weight="bold"), bordercolor="blue", secondary_y=False)
            
        fig.update_layout(height=400, margin=dict(l=20, r=20, t=30, b=20), legend=dict(orientation="h", yanchor="bottom", y=1.02, xanchor="right", x=1))
        fig.update_yaxes(title_text="ZBT 比率 (%)", range=[20, 80], secondary_y=False)
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
            df = calculate_mco_zbt(start_date, end_date, fetch_start_date, config['type'], config['etf'], sp500_sample, rut_sample)
            
            if not df.empty:
                mco_sigs, zbt_sigs = scan_signals(df)
                
                # S+ 級神兵診斷
                if len(zbt_sigs) > 0 and (df.index[-1] - zbt_sigs[-1]).days < 15:
                    st.success(f"🚀 【ZBT 核彈信號啟動】數年一遇嘅歷史大底部確認！大鱷正在瘋狂掃貨，全軍重倉突擊！")
                elif len(mco_sigs) > 0 and (df.index[-1] - mco_sigs[-1]).days < 5:
                    st.info(f"🟢 【MCO 動能黃金交叉】市寬動能剛剛升穿零軸，短期波段買點確認，建議加倉！")
                elif df['MCO'].iloc[-1] < -100:
                    st.warning(f"🧲 【MCO 恐慌極值】MCO 跌入極度超賣區 ({df['MCO'].iloc[-1]:.1f})，全市場血流成河，密切留意勾頭信號！")
                else:
                    st.info(f"⚖️ 【神兵待命中】MCO 動能：{df['MCO'].iloc[-1]:.1f} | ZBT 推力：{df['ZBT'].iloc[-1]:.1f}%")
                
                # 左右互搏畫圖
                colA, colB = st.columns(2)
                with colA:
                    st.subheader("🟢 狙擊槍：MCO 零軸動能雷達")
                    st.plotly_chart(plot_mco_chart(df, config['etf'], mco_sigs), use_container_width=True)
                with colB:
                    st.subheader("🚀 掃底炮：ZBT 大市推力雷達")
                    st.plotly_chart(plot_zbt_chart(df, config['etf'], zbt_sigs), use_container_width=True)
                
                st.divider() 
            else:
                st.error(f"❌ 獲取 {config['name']} 數據失敗。")

if __name__ == "__main__":
    app()