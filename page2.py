import streamlit as st
import pandas as pd
import numpy as np
import plotly.graph_objects as go
import yfinance as yf

# ===================================================
# 🎨 獨立繪圖與大腦同步核心（由冷藏庫數據驅動）
# ===================================================
def draw_and_sync_page2(symbol, selected_date, current_spot, t_shape, calls_clean, puts_clean):
    st.markdown(f"#### 📜 經典 T 型期權鏈 (到期日: {selected_date})")
    
    def style_t_shape(row):
        styles = [''] * len(row)
        strike_idx = t_shape.columns.get_loc('Strike')
        for i in range(len(row)):
            if i < strike_idx: styles[i] = 'color: #00ff88; background-color: #1a2436;'
            elif i > strike_idx: styles[i] = 'color: #ff3366; background-color: #241a22;'
            else: styles[i] = 'color: #ffffff; background-color: #2e3d52; font-weight: bold; text-align: center;'
        return styles
    st.dataframe(t_shape.style.apply(style_t_shape, axis=1).format(precision=2), use_container_width=True, height=400)
    
    col_opt1, col_opt2 = st.columns(2)
    with col_opt1:
        fig_iv = go.Figure()
        fig_iv.add_trace(go.Scatter(x=calls_clean['Strike'], y=calls_clean['C_IV']*100, mode='lines+markers', name='Call IV', line=dict(color='#00ff88', width=2)))
        fig_iv.add_trace(go.Scatter(x=puts_clean['Strike'], y=puts_clean['P_IV']*100, mode='lines+markers', name='Put IV', line=dict(color='#ff3366', width=2)))
        fig_iv.add_vline(x=current_spot, line_dash="dash", line_color="yellow", annotation_text="現價", annotation_position="top right")
        fig_iv.update_layout(title="引伸波幅微笑曲線 (IV Smile)", template='plotly_dark', paper_bgcolor='#1f293d', plot_bgcolor='#0e1117', margin=dict(l=20, r=20, t=40, b=20))
        st.plotly_chart(fig_iv, use_container_width=True)
    with col_opt2:
        fig_oi = go.Figure()
        fig_oi.add_trace(go.Bar(x=calls_clean['Strike'], y=calls_clean['C_OI'], name='Call 未平倉', marker_color='#00ff88', opacity=0.7))
        fig_oi.add_trace(go.Bar(x=puts_clean['Strike'], y=puts_clean['P_OI'], name='Put 未平倉', marker_color='#ff3366', opacity=0.7))
        fig_oi.add_vline(x=current_spot, line_dash="dash", line_color="yellow", annotation_text="現價", annotation_position="top right")
        fig_oi.update_layout(title="主力資金未平倉合防護牆 (OI)", barmode='group', template='plotly_dark', paper_bgcolor='#1f293d', plot_bgcolor='#0e1117', margin=dict(l=20, r=20, t=40, b=20))
        st.plotly_chart(fig_oi, use_container_width=True)

    # ===================================================
    # 🧠 大腦同步情報網 (發送給艙房六)
    # ===================================================
    try:
        total_call_oi = calls_clean['C_OI'].sum()
        total_put_oi = puts_clean['P_OI'].sum()
        
        call_resist_strike = calls_clean.loc[calls_clean['C_OI'].idxmax(), 'Strike'] if total_call_oi > 0 else 0
        put_support_strike = puts_clean.loc[puts_clean['P_OI'].idxmax(), 'Strike'] if total_put_oi > 0 else 0
        
        pcr_oi = total_put_oi / total_call_oi if total_call_oi > 0 else 0
        sentiment = "看淡 (Put 防守/做空較多)" if pcr_oi > 1.2 else "看好 (Call 買盤較強)" if pcr_oi < 0.8 else "中性震盪"
        
        summary = (
            f"【{symbol} 期權多維雷達 ({selected_date}) 戰報】：\n"
            f"1. 資金情緒：現價 {current_spot:.2f}，Put-Call Ratio (未平倉量) 為 {pcr_oi:.2f}，期權市場情緒偏向【{sentiment}】。\n"
            f"2. 主力防線：Call 最大未平倉(上行阻力)在 {call_resist_strike:.2f}，Put 最大未平倉(下行支撐)在 {put_support_strike:.2f}。\n"
            f"3. 總體規模：總 Call OI {total_call_oi:,.0f} 張，總 Put OI {total_put_oi:,.0f} 張。"
        )
        st.session_state["data_page2"] = summary
    except Exception as e:
        st.session_state["data_page2"] = f"【{symbol} 期權多維雷達】：計算戰報時發生小故障 ({e})。"

def render_options_tab(ticker, market_type, symbol, df_clean):
    st.markdown("### 🔮 期權雷達：主力資金與引伸波幅探測")
    current_spot = float(df_clean['Close'].iloc[-1]) if not df_clean.empty else 100.0
    
    def safe_get(df, possible_names):
        for name in possible_names:
            if name in df.columns: return df[name]
        return pd.Series(0.0, index=df.index)

    # 1. 📅 獲取可用的到期日列表
    opt_dates = []
    is_futu_connected = False
    quote_ctx = None
    futu_code = None

    if market_type == "港股":
        try:
            from futu import OpenQuoteContext, RET_OK
            quote_ctx = OpenQuoteContext(host='127.0.0.1', port=11111)
            quote_ctx.start()
            clean_code = symbol.split('.')[0]
            futu_code = f"HK.{int(clean_code):05d}"
            ret_date, date_df = quote_ctx.get_option_expiration_date(code=futu_code)
            if ret_date == RET_OK and not date_df.empty:
                opt_dates = date_df['strike_time'].tolist()
                is_futu_connected = True
        except: pass
    else:
        try:
            opt_dates = ticker.options
        except: pass

    if not opt_dates:
        opt_dates = ["模擬到期日"]

    # 2. 🎛️ 顯示到期日選單
    col_date, col_space = st.columns([1, 3])
    with col_date:
        selected_date = st.selectbox("📅 選擇期權到期日", opt_dates, key=f"opt_dt_{symbol}")
    st.markdown("<hr style='border:1px solid #2e3d52'>", unsafe_allow_html=True)

    # --- 🔒 數據冷藏庫身份標籤 ---
    storage_key = f"store_p2_{symbol}_{selected_date}"

    # 3. 🔍 檢查冷藏庫 (如果命中，0秒讀取並結束)
    if storage_key in st.session_state:
        if quote_ctx: 
            try: quote_ctx.close()
            except: pass
        d = st.session_state[storage_key]
        draw_and_sync_page2(symbol, selected_date, current_spot, d['t_shape'], d['calls_clean'], d['puts_clean'])
        
        if st.button("🔄 重新向伺服器提取最新期權鏈"):
            del st.session_state[storage_key]
            st.rerun()
        return

    # 4. 🚀 全新下載與計算
    calls = pd.DataFrame()
    puts = pd.DataFrame()
    run_rendering = False

    with st.spinner(f"⏳ 正在探測 {symbol} 於 {selected_date} 的期權雷達數據..."):
        if selected_date == "模擬到期日":
            st.warning("⚠️ 無法獲取真實數據，已切換至【離線高仿真演練模式】。")
            strikes = np.linspace(current_spot * 0.8, current_spot * 1.2, 20)
            calls = pd.DataFrame({'strike': strikes, 'lastPrice': np.random.uniform(0.1, 5.0, 20), 'bid': np.random.uniform(0.1, 4.8, 20), 'ask': np.random.uniform(0.2, 5.2, 20), 'volume': np.random.randint(10, 1000, 20), 'openInterest': np.random.randint(100, 5000, 20), 'impliedVolatility': np.random.uniform(0.2, 0.6, 20)})
            puts = pd.DataFrame({'strike': strikes, 'lastPrice': np.random.uniform(0.1, 5.0, 20), 'bid': np.random.uniform(0.1, 4.8, 20), 'ask': np.random.uniform(0.2, 5.2, 20), 'volume': np.random.randint(10, 1000, 20), 'openInterest': np.random.randint(100, 5000, 20), 'impliedVolatility': np.random.uniform(0.2, 0.6, 20)})
            run_rendering = True
        elif market_type == "港股" and is_futu_connected:
            from futu import RET_OK
            ret_chain, chain_df = quote_ctx.get_option_chain(code=futu_code, start=selected_date, end=selected_date)
            if ret_chain == RET_OK and not chain_df.empty:
                option_codes = chain_df['code'].tolist()
                snapshots = []
                for i in range(0, len(option_codes), 100):
                    ret_snap, snap_df = quote_ctx.get_market_snapshot(option_codes[i:i+100])
                    if ret_snap == RET_OK and not snap_df.empty:
                        snapshots.append(snap_df)
                if snapshots:
                    full_snap_df = pd.concat(snapshots, ignore_index=True)
                    merged = pd.merge(chain_df[['code', 'strike_price', 'option_type']], full_snap_df, on='code', how='inner')
                    if 'option_type_x' in merged.columns: merged['option_type'] = merged['option_type_x']
                    calls = merged[merged['option_type'] == 'CALL'].copy()
                    puts = merged[merged['option_type'] == 'PUT'].copy()
                    run_rendering = True
        else:
            try:
                opt_chain = ticker.option_chain(selected_date)
                calls = opt_chain.calls
                puts = opt_chain.puts
                run_rendering = True
            except: pass

    # 確保富途連線安全關閉
    if quote_ctx:
        try: quote_ctx.close()
        except: pass

    # 5. 💾 數據清洗與封裝進冷藏庫
    if run_rendering and not calls.empty and not puts.empty:
        calls_clean = pd.DataFrame()
        calls_clean['Strike'] = safe_get(calls, ['strike', 'Strike', 'strike_price', 'strikePrice'])
        calls_clean['C_Last'] = safe_get(calls, ['lastPrice', 'LastPrice', 'last_price', 'last_fill_price'])
        calls_clean['C_Bid']  = safe_get(calls, ['bid', 'Bid', 'bid_price'])
        calls_clean['C_Ask']  = safe_get(calls, ['ask', 'Ask', 'ask_price'])
        calls_clean['C_Vol']  = safe_get(calls, ['volume', 'Volume', 'vol'])
        calls_clean['C_OI']   = safe_get(calls, ['openInterest', 'OpenInterest', 'open_interest', 'oi'])
        calls_clean['C_IV']   = safe_get(calls, ['impliedVolatility', 'ImpliedVolatility', 'implied_volatility', 'iv'])
        
        puts_clean = pd.DataFrame()
        puts_clean['Strike'] = safe_get(puts, ['strike', 'Strike', 'strike_price', 'strikePrice'])
        puts_clean['P_Last'] = safe_get(puts, ['lastPrice', 'LastPrice', 'last_price', 'last_fill_price'])
        puts_clean['P_Bid']  = safe_get(puts, ['bid', 'Bid', 'bid_price'])
        puts_clean['P_Ask']  = safe_get(puts, ['ask', 'Ask', 'ask_price'])
        puts_clean['P_Vol']  = safe_get(puts, ['volume', 'Volume', 'vol'])
        puts_clean['P_OI']   = safe_get(puts, ['openInterest', 'OpenInterest', 'open_interest', 'oi'])
        puts_clean['P_IV']   = safe_get(puts, ['impliedVolatility', 'ImpliedVolatility', 'implied_volatility', 'iv'])

        t_shape = pd.merge(calls_clean, puts_clean, on='Strike', how='outer').fillna(0).sort_values('Strike')
        t_shape['Dist'] = abs(t_shape['Strike'] - current_spot)
        t_shape = t_shape.sort_values('Dist').head(40).sort_values('Strike').drop(columns=['Dist'])
        
        for col in ['C_IV', 'P_IV']: 
            t_shape[col] = np.where(t_shape[col] > 1.0, t_shape[col], t_shape[col] * 100)
            t_shape[col] = t_shape[col].round(2).astype(str) + '%'
        for col in ['C_Last', 'C_Bid', 'C_Ask', 'P_Last', 'P_Bid', 'P_Ask']: t_shape[col] = t_shape[col].round(2)
        t_shape = t_shape[['C_IV', 'C_OI', 'C_Vol', 'C_Bid', 'C_Ask', 'C_Last', 'Strike', 'P_Last', 'P_Bid', 'P_Ask', 'P_Vol', 'P_OI', 'P_IV']]
        
        # 鎖入記憶體
        st.session_state[storage_key] = {
            't_shape': t_shape,
            'calls_clean': calls_clean,
            'puts_clean': puts_clean
        }
        
        # 強制刷新畫面，讓系統讀取存檔並光速顯示！
        st.rerun()
    else:
        st.session_state["data_page2"] = f"【{symbol} 期權多維雷達】：暫無該資產的有效期權數據，或仍在等待選擇到期日。"