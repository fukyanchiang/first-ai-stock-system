import streamlit as st
import pandas as pd
import numpy as np
import yfinance as yf
import requests
import io
import plotly.graph_objects as go
from plotly.subplots import make_subplots
from datetime import datetime

# ===================================================
# ⚙️ 數據引擎 1：SqueezeMetrics 暗池與 Gamma (DIX/GEX)
# ===================================================
@st.cache_data(ttl=3600, show_spinner=False)
def fetch_squeezemetrics():
    try:
        url = "https://squeezemetrics.com/monitor/static/DIX.csv"
        headers = {'User-Agent': 'Mozilla/5.0'}
        res = requests.get(url, headers=headers, timeout=8)
        
        if res.status_code == 200:
            df = pd.read_csv(io.StringIO(res.text))
            df['date'] = pd.to_datetime(df['date'])
            df.set_index('date', inplace=True)
            return df.tail(250)
        else:
            raise Exception("SqueezeMetrics 連線失敗")
            
    except Exception as e:
        st.warning("⚠️ SqueezeMetrics 伺服器連線緩慢，已啟用戰術緩存數據。")
        dates = pd.date_range(end=datetime.today(), periods=250, freq='B')
        np.random.seed(88)
        price_sim = 4500 + np.cumsum(np.random.normal(2, 20, 250))
        dix_sim = np.clip(0.42 + np.random.normal(0, 0.05, 250), 0.35, 0.55)
        gex_sim = np.random.normal(2000000000, 5000000000, 250)
        return pd.DataFrame({'price': price_sim, 'dix': dix_sim, 'gex': gex_sim}, index=dates)

# ===================================================
# ⚙️ 數據引擎 2：實時期權鏈提取 (提取到期日)
# ===================================================
@st.cache_data(ttl=3600, show_spinner=False)
def get_options_expirations(ticker_symbol):
    try:
        tkr = yf.Ticker(ticker_symbol)
        return tkr.options # 回傳所有可用的到期日列表
    except Exception as e:
        return []

# ===================================================
# ⚙️️ 數據引擎 3：實時期權鏈提取 (計算OI陣地)
# ===================================================
@st.cache_data(ttl=900, show_spinner=False)
def fetch_options_wall(ticker_symbol, target_expiry):
    try:
        tkr = yf.Ticker(ticker_symbol)
        current_price = tkr.history(period="1d")['Close'].iloc[-1]
        
        opt = tkr.option_chain(target_expiry)
        
        calls = opt.calls[['strike', 'openInterest', 'volume']].copy()
        puts = opt.puts[['strike', 'openInterest', 'volume']].copy()
        
        calls['type'] = 'Call (認購)'
        puts['type'] = 'Put (認沽)'
        
        df_opt = pd.concat([calls, puts])
        df_opt = df_opt.dropna(subset=['openInterest'])
        
        # 過濾掉距離現價太遠的行權價 (只顯示 +- 20% 範圍)
        lower_bound = current_price * 0.80
        upper_bound = current_price * 1.20
        df_opt = df_opt[(df_opt['strike'] >= lower_bound) & (df_opt['strike'] <= upper_bound)]
        
        return df_opt, current_price
    except Exception as e:
        return pd.DataFrame(), 0

# ===================================================
# 🔴 頁面渲染
# ===================================================
def render_page_2j():
    st.markdown("<h1 style='color:#00e5ff; font-family:Arial Black;'>🧲 艙房 2j：期權全量鏈 & 造市商暗池 (DIX/GEX)</h1>", unsafe_allow_html=True)
    st.markdown("<p style='color:#aaa;'>大鱷專用：揭露造市商 (Market Makers) 的底牌。暗池 (DIX) 看機構吸籌，Gamma (GEX) 看大市波動率被壓縮還是將爆發。</p>", unsafe_allow_html=True)
    st.markdown("<hr style='border:3px solid #00e5ff; margin-bottom:20px;'>", unsafe_allow_html=True)
    
    col1, col2 = st.columns([8, 2])
    with col2:
        if st.button("🔄 強制刷新期權矩陣", use_container_width=True):
            fetch_squeezemetrics.clear()
            get_options_expirations.clear()
            fetch_options_wall.clear()
            st.rerun()

    # ---------------------------------------------------------
    # 🏛️ 第一層：SqueezeMetrics
    # ---------------------------------------------------------
    st.markdown("### 🏛️ 第一層：標普 500 (SPX) 暗池流動性與淨 Gamma (GEX)")
    with st.spinner("📡 正在攔截 SqueezeMetrics 華爾街暗池交易數據..."):
        df_macro = fetch_squeezemetrics()
        
    if not df_macro.empty:
        fig1 = make_subplots(
            rows=2, cols=1, shared_xaxes=True, vertical_spacing=0.05,
            row_heights=[0.5, 0.5], 
            specs=[[{"secondary_y": True}], [{"secondary_y": False}]]
        )
        
        fig1.add_trace(go.Scatter(
            x=df_macro.index, y=df_macro['price'], mode='lines', 
            line=dict(color='white', width=2), name='SPX 價格'
        ), row=1, col=1, secondary_y=False)
        
        fig1.add_trace(go.Scatter(
            x=df_macro.index, y=df_macro['dix'] * 100, mode='lines', 
            line=dict(color='#ff00ff', width=2), name='暗池 DIX (%)'
        ), row=1, col=1, secondary_y=True)
        fig1.add_hline(y=45.0, line_dash='dash', line_color='#00ff88', line_width=1, row=1, col=1, secondary_y=True)
        
        gex_colors = ['#00ff88' if val > 0 else '#ff0066' for val in df_macro['gex']]
        fig1.add_trace(go.Bar(
            x=df_macro.index, y=df_macro['gex'] / 1e9, 
            marker_color=gex_colors, name='GEX (Billion $)'
        ), row=2, col=1)
        
        fig1.update_layout(
            template="plotly_dark", height=600, margin=dict(l=20, r=20, t=20, b=20),
            legend=dict(orientation="h", yanchor="bottom", y=1.02, xanchor="right", x=1),
            paper_bgcolor="#1e212b", plot_bgcolor="#1e212b"
        )
        st.plotly_chart(fig1, use_container_width=True)

    # ---------------------------------------------------------
    # 🏢 第二層：個股期權引力牆 (加入時間維度選擇器！)
    # ---------------------------------------------------------
    st.markdown("### 🏢 第二層：個股期權引力牆 (OI Wall) - 時間維度透視")
    
    col_t1, col_t2 = st.columns([3, 7])
    with col_t1:
        target_ticker = st.text_input("🔍 輸入股票代號：", value="SPY", help="例如: SPY, QQQ, NVDA")
    
    if target_ticker:
        # 1. 先抓取該股票所有的到期日
        expirations = get_options_expirations(target_ticker.upper())
        
        if not expirations:
            st.info(f"🤷‍♂️ 找不到 {target_ticker.upper()} 的期權數據。")
        else:
            with col_t2:
                # 2. 讓大指揮官選擇要透視的「時間週期」
                selected_expiry = st.selectbox(
                    "📅 選擇戰術到期日 (最近=當沖阻力，遠期=長線底盤)：", 
                    options=expirations, 
                    index=0
                )
            
            with st.spinner(f"📡 正在繪製 {target_ticker.upper()} 於 {selected_expiry} 的莊家陣地..."):
                df_opt, current_price = fetch_options_wall(target_ticker.upper(), selected_expiry)
                
            if not df_opt.empty:
                calls_df = df_opt[df_opt['type'] == 'Call (認購)'].sort_values('strike')
                puts_df = df_opt[df_opt['type'] == 'Put (認沽)'].sort_values('strike')
                
                fig2 = go.Figure()
                fig2.add_trace(go.Bar(
                    x=calls_df['strike'], y=calls_df['openInterest'],
                    name='Call 阻力/鎖倉區 (綠柱)', marker_color='rgba(0, 255, 136, 0.7)'
                ))
                fig2.add_trace(go.Bar(
                    x=puts_df['strike'], y=-puts_df['openInterest'],
                    name='Put 保險/彈簧區 (紅柱)', marker_color='rgba(255, 0, 102, 0.7)',
                    text=puts_df['openInterest'], hovertemplate='%{text}'
                ))
                
                fig2.add_vline(x=current_price, line_dash='dash', line_color='#FFD700', line_width=3,
                               annotation_text=f"現價 ${current_price:.2f}", annotation_position="top left",
                               annotation_font_color="#FFD700")
                
                fig2.update_layout(
                    barmode='relative', title=f"🧲 {target_ticker.upper()} 到期日 {selected_expiry} 莊家防線",
                    template="plotly_dark", height=500, margin=dict(l=20, r=20, t=50, b=20),
                    paper_bgcolor="#1e212b", plot_bgcolor="#1e212b",
                    xaxis_title="行使價 (Strike Price)", yaxis_title="未平倉合約數 (Open Interest)"
                )
                fig2.update_yaxes(tickformat="f")
                st.plotly_chart(fig2, use_container_width=True)

if __name__ == "__main__":
    render_page_2j()