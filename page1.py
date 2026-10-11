import streamlit as st
import plotly.graph_objects as go
import pandas as pd
import numpy as np

# ===================================================
# 🎨 獨立繪圖與大腦同步核心（由冷藏庫數據驅動）
# ===================================================
def draw_and_sync_page1(df_display, df_clean, current_price, delta_val, delta_percent, ma20_text, cur_sym, symbol, market_type, period):
    col1, col2, col3 = st.columns(3)
    with col1:
        st.markdown(f'<div class="metric-box"><div class="metric-title">最新價格</div><div class="metric-value">{cur_sym}{current_price:,.2f}</div></div>', unsafe_allow_html=True)
    with col2:
        if delta_val >= 0:
            st.markdown(f'<div class="metric-box"><div class="metric-title">今日變動</div><div class="metric-value" style="color:#00ff88;">+{cur_sym}{delta_val:,.2f}</div><div style="color:#00ff88; font-size:16px;">(+{delta_percent:.2f}%)</div></div>', unsafe_allow_html=True)
        else:
            st.markdown(f'<div class="metric-box"><div class="metric-title">今日變動</div><div class="metric-value" style="color:#ff3366;">-{cur_sym}{abs(delta_val):,.2f}</div><div style="color:#ff3366; font-size:16px;">({delta_percent:.2f}%)</div></div>', unsafe_allow_html=True)
    with col3:
        st.markdown(f'<div class="metric-box"><div class="metric-title">20日平均線 (MA20)</div><div class="metric-value" style="color:#00f2ff;">{cur_sym}{ma20_text}</div></div>', unsafe_allow_html=True)

    st.markdown("<br>", unsafe_allow_html=True)
    
    fig = go.Figure()
    # 📈 主圖
    fig.add_trace(go.Candlestick(x=df_display.index, open=df_display['Open'], high=df_display['High'], low=df_display['Low'], close=df_display['Close'], name='K線圖', yaxis='y1'))
    fig.add_trace(go.Scatter(x=df_display.index, y=df_display['MA20'], mode='lines', line=dict(color='#00f2ff', width=1.5), name='MA20', yaxis='y1'))
    fig.add_trace(go.Scatter(x=df_display.index, y=df_display['VAS'], mode='lines', line=dict(color='red', width=2), name='VAS 天量支撐', yaxis='y1'))
    
    big_signals = df_display[df_display['ISBIG'] == True]
    if not big_signals.empty:
        fig.add_trace(go.Scatter(x=big_signals.index, y=big_signals['High'] * 1.015, mode='text', text=['BIG'] * len(big_signals), textposition='top center', textfont=dict(color='#FF00FF', size=13, family='Arial Black'), name='主力爆發 (BIG)', showlegend=True, yaxis='y1'))
        for idx, row_data in big_signals.iterrows():
            fig.add_shape(type="line", x0=idx - pd.Timedelta(hours=12), y0=row_data['Low'], x1=idx + pd.Timedelta(hours=12), y1=row_data['Low'], line=dict(color="#FF00FF", width=3), xref='x', yref='y1')
    
    # 📊 副圖 1: DELTAME
    day_ms = 86400000 
    fig.add_trace(go.Bar(x=df_display.index, y=df_display['BUYVOL'], marker_color='#808000', width=day_ms*0.8, name='BUYVOL', yaxis='y2'))
    fig.add_trace(go.Bar(x=df_display.index, y=-df_display['SELLVOL'], marker_color='#800000', width=day_ms*0.8, name='SELLVOL', yaxis='y2'))
    net_colors = np.where(df_display['NETVOL'] > 0, '#00ff88', '#ff3366') 
    fig.add_trace(go.Bar(x=df_display.index, y=df_display['NETVOL'], marker_color=net_colors, width=day_ms*0.35, name='NETVOL', yaxis='y2'))
    fig.add_trace(go.Scatter(x=df_display.index, y=df_display['NETMA'], mode='lines', line=dict(color='#ffffff', width=2), name='NETMA', yaxis='y2'))
    
    # 📊 副圖 2: TURN VIX
    vix_colors = np.full(len(df_display), '#444444', dtype=object)
    is_breakout = df_display['真正爆發'] == True
    is_bull = df_display['Close'] > df_display['Open']
    vix_colors[is_breakout & is_bull] = '#00ffff'   
    vix_colors[is_breakout & ~is_bull] = '#ff00ff'  
    fig.add_trace(go.Bar(x=df_display.index, y=df_display['Volume'], marker_color=vix_colors, name='TURN VIX 量能', yaxis='y3'))
    fig.add_trace(go.Scatter(x=df_display.index, y=df_display['V_UPPER'], mode='lines', line=dict(color='rgba(0,242,255,0.6)', width=1, dash='dot'), name='V_UPPER(短防)', yaxis='y3'))
    fig.add_trace(go.Scatter(x=df_display.index, y=df_display['均量60'], mode='lines', line=dict(color='rgba(255,255,0,0.6)', width=1.5), name='均量60(長防)', yaxis='y3'))
    
    # 📊 副圖 3: DAILY PRICE CHANGE
    change_colors = np.where(df_display['CHANGE'] >= 0, '#ff3366', '#00ff88')
    fig.add_trace(go.Bar(x=df_display.index, y=df_display['CHANGE'], marker_color=change_colors, name='DAILY PRICE CHANGE', yaxis='y4'))

    # 📊 副圖 4: MACD
    fig.add_trace(go.Scatter(x=df_display.index, y=df_display['DIF'], mode='lines', line=dict(color='#00f2ff', width=1.5), name='DIF', yaxis='y5'))
    fig.add_trace(go.Scatter(x=df_display.index, y=df_display['DEA'], mode='lines', line=dict(color='#ffaa00', width=1.5), name='DEA', yaxis='y5'))
    macd_colors = np.where(df_display['MACD_HIST'] >= 0, '#00ff88', '#ff3366')
    fig.add_trace(go.Bar(x=df_display.index, y=df_display['MACD_HIST'], marker_color=macd_colors, name='MACD HIST', yaxis='y5'))

    # 📊 副圖 5: RSI
    fig.add_trace(go.Scatter(x=df_display.index, y=df_display['RSI'], mode='lines', line=dict(color='#ffaa00', width=1.5), name='RSI(14)', yaxis='y6'))
    fig.add_shape(type="line", x0=df_display.index[0], y0=70, x1=df_display.index[-1], y1=70, line=dict(color="gray", width=1, dash="dash"), xref='x', yref='y6')
    fig.add_shape(type="line", x0=df_display.index[0], y0=30, x1=df_display.index[-1], y1=30, line=dict(color="gray", width=1, dash="dash"), xref='x', yref='y6')

    fig.update_layout(
        template='plotly_dark', paper_bgcolor='#0e1117', plot_bgcolor='#1f293d', xaxis_rangeslider_visible=False,
        barmode='overlay', margin=dict(l=50, r=50, t=10, b=50), height=1200, hovermode='x unified',             
        hoverlabel=dict(bgcolor='#1f293d', font_size=12, font_family='Arial'),
        xaxis=dict(anchor='y6', showgrid=True, gridcolor='#2e3d52', showspikes=True, spikemode='across', spikedash='dash', spikecolor='#a0aec0', spikethickness=1, spikesnap='cursor'),
        yaxis=dict( domain=[0.65, 1.00], anchor='x', title_text="價格", gridcolor='#2e3d52'),
        yaxis2=dict(domain=[0.52, 0.63], anchor='x', title_text="TRADE FORCE<br>DELTAME", gridcolor='#2e3d52', title_font=dict(size=10)),
        yaxis3=dict(domain=[0.39, 0.50], anchor='x', title_text="TRADE FORCE<br>TURN VIX", gridcolor='#2e3d52', title_font=dict(size=10)),
        yaxis4=dict(domain=[0.26, 0.37], anchor='x', title_text="DAILY PRICE<br>CHANGE", gridcolor='#2e3d52', title_font=dict(size=10)),
        yaxis5=dict(domain=[0.13, 0.24], anchor='x', title_text="MACD", gridcolor='#2e3d52', title_font=dict(size=10)),
        yaxis6=dict(domain=[0.00, 0.11], anchor='x', title_text="RSI(14)", gridcolor='#2e3d52', title_font=dict(size=10), range=[0, 100])
    )
    st.plotly_chart(fig, use_container_width=True)

    # ===================================================
    # 🧠 核心大腦強制刷新戰報機制
    # ===================================================
    summary_text = "數據計算中..."
    try:
        ma20_val = df_clean['MA20'].iloc[-1]
        is_above_ma20 = current_price > ma20_val
        ma20_status = f"現價 {cur_sym}{current_price:,.2f} {'企穩於' if is_above_ma20 else '跌破'} MA20 ({cur_sym}{ma20_val:,.2f})"

        vas_price = df_clean['VAS'].iloc[-1] if not pd.isna(df_clean['VAS'].iloc[-1]) else 0
        if vas_price > 0:
            vas_dist = ((current_price - vas_price) / vas_price) * 100
            vas_status = f"VAS 天量支撐線位於 {cur_sym}{vas_price:,.2f} (距離現價 {vas_dist:+.1f}%)"
        else:
            vas_status = "目前無明顯 VAS 天量支撐記錄"

        latest_netvol = df_clean['NETVOL'].iloc[-1]
        latest_netma = df_clean['NETMA'].iloc[-1]
        deltame_text = f"單日淨量(NETVOL) {'流入' if latest_netvol>0 else '流出'} {abs(latest_netvol):,.0f}，10日均量(NETMA)趨勢{'向上' if latest_netma>0 else '向下'}"

        recent_5_days = df_clean.tail(5)
        has_big = recent_5_days['ISBIG'].any()
        has_breakout = recent_5_days['真正爆發'].any()
        turnvix_text = "🔥 觸發【TURN VIX 真正爆發】極強信號！" if has_breakout else "⚠️ 觸發【主力爆發 (BIG)】吸籌信號。" if has_big else "量能平穩，未見異常爆發柱。"

        change_text = f"今日單日漲跌幅為 {delta_percent:+.2f}%"

        latest_macd = df_clean['MACD_HIST'].iloc[-1]
        latest_macd_val = float(latest_macd) if not pd.isna(latest_macd) else 0.0
        macd_text = f"MACD Histogram 為 {'多頭正值' if latest_macd_val > 0 else '空頭負值'} ({latest_macd_val:.3f})"

        latest_rsi = df_clean['RSI'].iloc[-1]
        latest_rsi_val = float(latest_rsi) if not pd.isna(latest_rsi) else 50.0
        rsi_text = f"RSI(14) 讀數為 {latest_rsi_val:.1f}"

        summary_text = (
            f"【{symbol} 六維王者矩陣戰報 (全指標解碼)】：\n"
            f"--- 主圖指標 ---\n"
            f"1. MA20 均線：{ma20_status}\n"
            f"2. VAS 防線：{vas_status}\n"
            f"--- 副圖指標 ---\n"
            f"3. DELTAME (買賣力道)：{deltame_text}\n"
            f"4. TURN VIX (量能爆發)：{turnvix_text}\n"
            f"5. DAILY PRICE CHANGE：{change_text}\n"
            f"6. MACD 指標：{macd_text}\n"
            f"7. RSI(14) 指標：{rsi_text}"
        )
    except Exception as e:
        summary_text = f"【{symbol} 六維王者矩陣】：全指標解碼時發生錯誤 ({e})。"
    finally:
        st.session_state["data_page1"] = summary_text

def render_stock_tab(df, period, market_type, symbol):
    storage_key = f"store_p1_{symbol}_{period}"
    
    currency_symbols = {"美股": "$", "港股": "HK$", "日股": "¥", "韓股": "₩", "台股": "NT$", "A股": "¥", "加密貨幣": "$"}
    cur_sym = currency_symbols.get(market_type, "$")

    if storage_key in st.session_state:
        d = st.session_state[storage_key]
        draw_and_sync_page1(
            d['df_display'], d['df_clean'], d['current_price'], d['delta_val'], 
            d['delta_percent'], d['ma20_text'], cur_sym, symbol, market_type, period
        )
        return

    if df.empty:
        st.warning("⚠️ 暫無資產歷史價格數據，請檢查母艦主控室連線。")
        return

    df['MA20'] = df['Close'].rolling(window=20).mean()
    df['HV60'] = df['Volume'].rolling(window=60).max()
    df['VAS_raw'] = np.where(df['Volume'] == df['HV60'], df['Low'], np.nan)
    df['VAS'] = df['VAS_raw'].ffill()  
    
    df['VOLMA20_BIG'] = df['Volume'].rolling(window=20).mean()
    df['ISBIG'] = (df['Volume'] > df['VOLMA20_BIG'] * 1.5) & (df['Close'] > df['Open'])

    df['VAR1'] = df['Close'] - df['Low']
    df['VAR2'] = df['High'] - df['Close']
    df['VAR3'] = df['High'] - df['Low']
    df['BUYVOL'] = np.where(df['VAR3'] > 0, df['Volume'] * df['VAR1'] / df['VAR3'], 0)
    df['SELLVOL'] = np.where(df['VAR3'] > 0, df['Volume'] * df['VAR2'] / df['VAR3'], 0)
    df['NETVOL'] = df['BUYVOL'] - df['SELLVOL']
    df['NETMA'] = df['NETVOL'].rolling(window=10).mean() 

    df['V_MA'] = df['Volume'].rolling(window=20).mean()
    df['V_STD'] = df['Volume'].rolling(window=20).std()
    df['V_UPPER'] = df['V_MA'] + (2.0 * df['V_STD'])
    df['均量60'] = df['Volume'].rolling(window=60).mean()
    df['prev_Close'] = df['Close'].shift(1)
    df['升跌幅'] = (df['Close'] - df['prev_Close']).abs() / df['prev_Close'] * 100
    df['真正爆發'] = (df['Volume'] > df['V_UPPER']) & (df['Volume'] > df['均量60'] * 1.9) & (df['升跌幅'] > 2.0)

    df['CHANGE'] = (df['Close'] - df['prev_Close']) / df['prev_Close'] * 100
    
    df['EMA12'] = df['Close'].ewm(span=12, adjust=False).mean()
    df['EMA26'] = df['Close'].ewm(span=26, adjust=False).mean()
    df['DIF'] = df['EMA12'] - df['EMA26']
    df['DEA'] = df['DIF'].ewm(span=9, adjust=False).mean()
    df['MACD_HIST'] = (df['DIF'] - df['DEA']) * 2
    
    delta = df['Close'].diff()
    gain = delta.clip(lower=0)
    loss = (-delta).clip(lower=0)
    avg_gain = gain.rolling(window=14).mean()
    avg_loss = loss.rolling(window=14).mean()
    rs = avg_gain / (avg_loss + 1e-9)  
    df['RSI'] = 100 - (100 / (1 + rs))

    df_clean = df.dropna(subset=['Close']).copy()
    current_price = float(df_clean['Close'].iloc[-1])
    
    if len(df_clean) > 1:
        prev_price = float(df_clean['Close'].iloc[-2])
        delta_val = current_price - prev_price
        delta_percent = (delta_val / prev_price) * 100
    else:
        delta_val = 0.0
        delta_percent = 0.0
        
    ma20_series = df_clean['MA20'].dropna()
    ma20_text = f"{ma20_series.iloc[-1]:,.2f}" if not ma20_series.empty else "更新中..."
    
    period_map = {"1mo": 21, "3mo": 63, "6mo": 126, "1y": 252, "5y": len(df_clean)}
    display_days = period_map.get(period, 63)
    df_display = df_clean.tail(display_days).copy()
    
    st.session_state[storage_key] = {
        'df_display': df_display, 'df_clean': df_clean, 'current_price': current_price,
        'delta_val': delta_val, 'delta_percent': delta_percent, 'ma20_text': ma20_text
    }

    draw_and_sync_page1(df_display, df_clean, current_price, delta_val, delta_percent, ma20_text, cur_sym, symbol, market_type, period)