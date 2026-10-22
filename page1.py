import os
import pandas as pd
import numpy as np
import streamlit as st
import plotly.graph_objects as go

# 導入主圖運算與渲染模組
from page1_main_indicator01_calc import (
    compute_main_group1,
    render_main_group1
)
from page1_main_indicator02_calc import (
    compute_main_group2,
    render_main_group2
)

# 導入副圖運算與渲染模組
from page1_indicator_calc import (
    compute_group1_indicators,
    render_group1_traces,
    get_spread_metrics,
    get_hud_tags
)
from page1_indicator02_calc import (
    compute_group2_indicators,
    render_group2_traces
)

# 🚀 引入獨立封裝的右側量化診斷模組 (Alpha + 成交活躍度 + 50日線)
from page1_sidebar_diag_calc import (
    calculate_alpha_diagnostics,
    render_sidebar_diagnostics
)

# ===================================================
# 🎨 繪圖與大腦同步核心
# ===================================================
def draw_and_sync_page1(df_display, df_clean, current_price, delta_val, delta_percent, ma20_text, cur_sym, symbol, market_type, period, benchmark_ticker, active_indicators, main_cfg):
    last_row = df_clean.iloc[-1]
    latest_score = float(last_row.get('Spread_Score', 0.0))
    latest_trap_pct, status_label, status_color, badge = get_spread_metrics(latest_score)
    d1_tag, d2_tag, d3_tag, d4_tag, d5_tag = get_hud_tags(last_row)

    # 1. 頂部 4 大指標卡
    col1, col2, col3, col4 = st.columns([1, 1, 1, 1.35])
    with col1:
        st.markdown(f'<div class="metric-box"><div class="metric-title">最新價格</div><div class="metric-value">{cur_sym}{current_price:,.2f}</div></div>', unsafe_allow_html=True)
    with col2:
        if delta_val >= 0:
            st.markdown(f'<div class="metric-box"><div class="metric-title">今日變動</div><div class="metric-value" style="color:#00ff88;">+{cur_sym}{delta_val:,.2f}</div><div style="color:#00ff88; font-size:16px;">(+{delta_percent:.2f}%)</div></div>', unsafe_allow_html=True)
        else:
            st.markdown(f'<div class="metric-box"><div class="metric-title">今日變動</div><div class="metric-value" style="color:#ff3366;">-{cur_sym}{abs(delta_val):,.2f}</div><div style="color:#ff3366; font-size:16px;">({delta_percent:.2f}%)</div></div>', unsafe_allow_html=True)
    with col3:
        st.markdown(f'<div class="metric-box"><div class="metric-title">20日平均線 (MA20)</div><div class="metric-value" style="color:#00f2ff;">{cur_sym}{ma20_text}</div></div>', unsafe_allow_html=True)
    with col4:
        st.markdown(f'''
        <div class="metric-box" style="border: 1px solid {status_color}88; background: rgba(15, 23, 42, 0.65);">
            <div class="metric-title" style="display:flex; justify-content:space-between; align-items:center;">
                <span>五維共振 · 散戶套牢風險</span>
                <span style="font-size:10px; color:#cbd5e1; background:{status_color}33; padding:2px 6px; border-radius:4px; border:1px solid {status_color}; font-weight:700;">{badge}</span>
            </div>
            <div class="metric-value" style="color:{status_color}; font-size:26px;">{latest_trap_pct:.1f}%</div>
            <div style="color:#94a3b8; font-size:12px; margin-top:2px;">剪刀差總分: <b style="color:{status_color};">{latest_score:+.1f}</b> (-100~+100)</div>
        </div>
        ''', unsafe_allow_html=True)

    # 2. 五維共振戰術 HUD 狀態看板
    st.markdown(f'''
    <div style="
        background: linear-gradient(135deg, rgba(30, 41, 59, 0.85), rgba(15, 23, 42, 0.95));
        border: 1px solid #334155;
        border-left: 4px solid {status_color};
        border-radius: 10px;
        padding: 10px 16px;
        margin-top: 14px;
        margin-bottom: 14px;
        box-shadow: 0 4px 15px rgba(0,0,0,0.3);
        font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, sans-serif;
    ">
        <div style="display:flex; justify-content:space-between; align-items:center; flex-wrap:wrap; gap:10px;">
            <div style="display:flex; align-items:center; gap:8px;">
                <span style="font-size:18px;">🧭</span>
                <div>
                    <span style="font-size:13.5px; font-weight:700; color:#f8fafc;">五維共振決策雷達 (Smart/Dumb Spread Index)</span>
                    <span style="margin-left:8px; font-size:12px; color:{status_color}; font-weight:bold;">{status_label}</span>
                </div>
            </div>
            <div style="display:flex; align-items:center; gap:14px; font-size:11.5px; color:#cbd5e1;">
                <span>🟢 影線套牢: <b>{d1_tag}</b></span>
                <span>🔵 隔夜背馳: <b>{d2_tag}</b></span>
                <span>⏱️ 早尾博弈: <b>{d3_tag}</b></span>
                <span>🟠 暗池豁免: <b>{d4_tag}</b></span>
                <span>🟣 期權狂熱: <b>{d5_tag}</b></span>
            </div>
        </div>
    </div>
    ''', unsafe_allow_html=True)

    # 👁️【關鍵升級】圖表頂部精確眼仔開關（預設 False 隱藏圖例，手機滿版不擠壓）
    ctrl_col1, _ = st.columns([2.5, 1.5])
    with ctrl_col1:
        show_legend = st.checkbox("👁️ 顯示指標圖例說明 (手機睇盤建議關閉以獲取超闊 K 線)", value=False, key="p1_show_legend_toggle")

    # 3. 副圖圖層排列與動態 Domain 計算 (已徹底修復減號與折行語法)
    ordered_keys = ["sctr", "rs", "vol", "chive", "drift", "vwap", "finra", "otm", "spring", "vcp", "ttm", "macd", "deltame", "turnvix", "change", "rsi"]
    display_keys = [k for k in ordered_keys if k in active_indicators]
    
    num_subs = len(display_keys)
    if num_subs == 0:
        price_domain = [0.0, 1.0]
        chart_height = 650
        domains = {}
    else:
        chart_height = max(700, 450 + num_subs * 140)
        price_ratio = 0.22 if num_subs >= 8 else 0.30
        price_domain = [round(1.0 - price_ratio, 3), 1.0]
        
        rem_space = 1.0 - price_ratio - 0.02
        sub_gap = 0.012
        sub_h = (rem_space - (num_subs - 1) * sub_gap) / num_subs
        
        domains = {}
        curr_top = 1.0 - price_ratio - 0.02
        for idx_sub in range(num_subs):
            bot = max(0.0, curr_top - sub_h)
            domains[idx_sub + 2] = [round(bot, 3), round(curr_top, 3)]
            curr_top = bot - sub_gap

    y_axes_config = {}
    y_axes_config['yaxis'] = dict(domain=price_domain, anchor='x', title_text="價格", gridcolor='#2e3d52')

    fig = go.Figure()
    
    # 📈 主圖 (y1) - 基礎 K 線
    fig.add_trace(go.Candlestick(
        x=df_display.index,
        open=df_display['Open'], high=df_display['High'],
        low=df_display['Low'], close=df_display['Close'],
        name='K線圖', yaxis='y1'
    ))

    # 📈 主圖 (y1) - 模組化渲染：組 1 (MA, ANCHORZONE, VAS S+++)
    render_main_group1(fig, df_display, main_cfg)

    # 📈 主圖 (y1) - 模組化渲染：組 2 (GP_ALL_IN_ONE: 包含一支支線彩帶、BB、SAR、AI▲、H50、TD9、起爆)
    render_main_group2(fig, df_display, main_cfg)

    # 4. 委託副圖兩大模組繪製選中的副圖 Traces
    day_ms = 86400000
    group2_set = {"spring", "vcp", "ttm", "macd"}
    for i, k in enumerate(display_keys):
        y_num = i + 2
        y_ax = f"y{y_num}"
        dm = domains[y_num]
        if k in group2_set:
            render_group2_traces(fig, k, df_display, y_ax, dm, y_num, y_axes_config)
        else:
            render_group1_traces(fig, k, df_display, y_ax, dm, benchmark_ticker, day_ms, y_num, y_axes_config)

    bottom_ax = f"y{num_subs + 1}" if num_subs > 0 else 'y1'
    y_axes_config['xaxis'] = dict(
        anchor=bottom_ax, showgrid=True, gridcolor='#2e3d52',
        showspikes=True, spikemode='across', spikedash='dash',
        spikecolor='#a0aec0', spikethickness=1, spikesnap='cursor'
    )

    # 👁️ 將 showlegend 與眼仔開關連動，並緊縮邊距以極大化手機顯示空間
    fig.update_layout(
        template='plotly_dark', paper_bgcolor='#0e1117', plot_bgcolor='#1f293d',
        xaxis_rangeslider_visible=False, barmode='overlay',
        margin=dict(l=35, r=15, t=10, b=30), height=chart_height,
        hovermode='x unified',             
        hoverlabel=dict(bgcolor='#1f293d', font_size=12, font_family='Arial'),
        showlegend=show_legend,
        legend=dict(
            font=dict(color="white", size=11),
            bgcolor="rgba(15, 23, 42, 0.75)",
            bordercolor="#334155",
            borderwidth=1
        ) if show_legend else dict(),
        **y_axes_config
    )

    # 🎯 核心佈局重構：主畫布 (左 76%) + 專屬量化體檢面板 (右 24%)
    chart_col, diag_col = st.columns([3.1, 1.0])

    with chart_col:
        st.plotly_chart(fig, use_container_width=True)

    with diag_col:
        # 調用獨立計算與渲染引擎
        diag_data = calculate_alpha_diagnostics(df_stock=df_clean, symbol=symbol, market_type=market_type)
        render_sidebar_diagnostics(diag_data)

    # 5. 最底部使用說明
    with st.expander("📚 點擊展開：5 大暗網韭菜/主力背離指標用法說明", expanded=False):
        st.markdown("""
        ### 🕵️‍♂️ 華爾街量化終端：散戶 vs 主力資金背離雷達
        這 5 個副圖不是傳統的滯後技術指標，而是透過 **「拆解訂單流、交易時段、市場結構」** 來透視背後莊家與散戶的真實博弈。

        ---

        ### 🧭【核心決策總部】五維共振 · 散戶套牢風險指數 (Smart/Dumb Spread)
        系統自動將下方 5 大暗網副圖的即時數值進行矩陣權重運算，提純為頂部的綜合決策看板：
- **散戶套牢風險 % (0% ~ 100%)** 與 **剪刀差總分 (-100 ~ +100)**：
- 🚨 **極度危險 (風險 ≥ 80% / 總分 ≤ -60)**：5 大維度出現嚴重共振套牢，主力全面出貨完畢，隨時引發踩踏暴跌。
- ⚠️ **警戒出貨 (風險 60% ~ 80% / 總分 -20 ~ -60)**：隔夜跳空或早盤出現誘多背馳，造市商暗池空頭對沖加劇。
- ⚪ **多空平衡 (風險 40% ~ 60% / 更多 -20 ~ +20)**：資金博弈溫和，處於洗盤整理區間，建議觀望為主。
- 🟢 **主力吸籌 (風險 20% ~ 40% / 總分 +20 ~ +60)**：散戶熱情消退，機構尾盤與低位暗中收集籌碼。
- 🚀 **黃金底背離 (風險 ≤ 20% / 總分 ≥ +60)**：散戶恐慌割肉完畢，主力極度強勢控盤，大級別反轉前夕。
        """)

    # 6. 王者矩陣戰報
    summary_text = "數據計算中..."
    try:
        ma20_val = df_clean['MA_3'].iloc[-1] if 'MA_3' in df_clean else df_clean['Close'].rolling(20).mean().iloc[-1]
        is_above_ma20 = current_price > ma20_val
        ma20_status = f"現價 {cur_sym}{current_price:,.2f} {'企穩於' if is_above_ma20 else '跌破'} MA20 ({cur_sym}{ma20_val:,.2f})"
        vas_price = df_clean['VAS'].iloc[-1] if 'VAS' in df_clean and not pd.isna(df_clean['VAS'].iloc[-1]) else 0
        vas_status = f"VAS 天量支撐線位於 {cur_sym}{vas_price:,.2f}" if vas_price > 0 else "目前無明顯 VAS 天量支撐記錄"
        latest_netvol = df_clean['NETVOL'].iloc[-1] if 'NETVOL' in df_clean else 0
        deltame_text = f"單日淨量(NETVOL) {'流入' if latest_netvol>0 else '流出'} {abs(latest_netvol):,.0f}"
        summary_text = f"【{symbol} 王者矩陣】：MA20: {ma20_status} | {vas_status} | 散戶套牢風險 {latest_trap_pct:.1f}% ({badge}) | 剪刀差總分 {latest_score:+.1f}"
    except Exception as e:
        summary_text = f"【{symbol} 王者矩陣】：計算發生錯誤 ({e})。"
    finally:
        st.session_state["data_page1"] = summary_text

# ===================================================
# 🚀 頁面主入口函數
# ===================================================
def render_stock_tab(df, period, market_type, symbol):
    currency_symbols = {"美股": "$", "港股": "HK$", "日股": "¥", "韓股": "₩", "台股": "NT$", "A股": "¥", "加密貨幣": "$"}
    cur_sym = currency_symbols.get(market_type, "$")
    benchmark_ticker = "2800.HK" if market_type == "港股" else "SPY"

    # ===================================================
    # 🎛️ 方案 B：側邊欄 Checkbox 圖層控制台 (主圖 + 副圖)
    # ===================================================
    main_cfg = {}
    with st.sidebar:
        st.markdown("---")
        st.markdown("### 📈 主圖 4 大指標與信號開關")
        
        # 1. MA 均線組 (10條均線獨立開關)
        with st.expander("1. MA 均線群 (10條均線)", expanded=False):
            main_cfg["show_ma_group"] = st.checkbox("啟用 MA 均線群 (總開關)", value=True, key="p1_main_ma_all")
            c1, c2 = st.columns(2)
            with c1:
                main_cfg["show_ma_1"] = st.checkbox("MA1 (5)", value=True, key="p1_ma_1")
                main_cfg["show_ma_2"] = st.checkbox("MA2 (10)", value=True, key="p1_ma_2")
                main_cfg["show_ma_3"] = st.checkbox("MA3 (20)", value=True, key="p1_ma_3")
                main_cfg["show_ma_4"] = st.checkbox("MA4 (30)", value=False, key="p1_ma_4")
                main_cfg["show_ma_5"] = st.checkbox("MA5 (50)", value=True, key="p1_ma_5")
            with c2:
                main_cfg["show_ma_6"] = st.checkbox("MA6 (60)", value=False, key="p1_ma_6")
                main_cfg["show_ma_7"] = st.checkbox("MA7 (120)", value=False, key="p1_ma_7")
                main_cfg["show_ma_8"] = st.checkbox("MA8 (150)", value=True, key="p1_ma_8")
                main_cfg["show_ma_9"] = st.checkbox("MA9 (200)", value=True, key="p1_ma_9")
                main_cfg["show_ma_10"] = st.checkbox("MA10 (250)", value=False, key="p1_ma_10")

        # 2. ANCHORZONE 主力爆發區
        with st.expander("2. ANCHORZONE 主力爆發", expanded=False):
            main_cfg["show_anchorzone"] = st.checkbox("啟用 ANCHORZONE (總開關)", value=True, key="p1_az_all")
            main_cfg["show_az_text"] = st.checkbox("顯示 'BIG' 標記文字", value=True, key="p1_az_txt")
            main_cfg["show_az_line"] = st.checkbox("顯示 K線底部防守實線", value=True, key="p1_az_line")

        # 3. VOLUMEANCHORSUPPORT (S+++ 極致防守版)
        with st.expander("3. S+++ VOLUMEANCHORSUPPORT", expanded=False):
            main_cfg["show_vas_main"] = st.checkbox("啟用 S+++ 終極防守 (總開關)", value=True, key="p1_vas_all")
            main_cfg["show_vas_line"] = st.checkbox("顯示 VAS 天量防守線 (紅線)", value=True, key="p1_vas_line")
            main_cfg["show_s_plus_buy"] = st.checkbox("顯示 🚀S+++ 突擊買入", value=True, key="p1_vas_buy")
            main_cfg["show_sell_trim"] = st.checkbox("顯示 ⚠️ 鎖利減倉提示", value=True, key="p1_vas_trim")
            main_cfg["show_sell_clear"] = st.checkbox("顯示 🛑 徹底清倉訊號", value=True, key="p1_vas_clear")

        # 4. GP_ALL_IN_ONE (主圖終極合體版)
        with st.expander("4. GP_ALL_IN_ONE 終極合體", expanded=True):
            main_cfg["show_gp_all"] = st.checkbox("啟用 GP_ALL_IN_ONE (總開關)", value=True, key="p1_gp_all")
            main_cfg["show_gp_stick_mid"] = st.checkbox("★ 中期彩帶一支支線 (MA2 vs MA3 藍/粉)", value=True, key="p1_gp_stick_mid")
            main_cfg["show_gp_stick_short"] = st.checkbox("短期彩帶一支支線 (MA1 vs MA2 青/灰)", value=False, key="p1_gp_stick_short")
            main_cfg["show_gp_stick_long"] = st.checkbox("長期彩帶一支支線 (MA3 vs MA4 灰/黃)", value=False, key="p1_gp_stick_long")
            main_cfg["show_gp_ribbon"] = st.checkbox("彩色均線邊界實線 (5/10/20/60)", value=True, key="p1_gp_ribbon")
            main_cfg["show_gp_ma50l"] = st.checkbox("MA50L 特種低點均線", value=False, key="p1_gp_ma50l")
            main_cfg["show_gp_bb"] = st.checkbox("布林通道 (BB 20, 2.0)", value=False, key="p1_gp_bb")
            main_cfg["show_gp_sar"] = st.checkbox("SAR 拋物轉向點", value=True, key="p1_gp_sar")
            main_cfg["show_gp_aibuy"] = st.checkbox("AI BUY 點火 (綠三角 ▲)", value=True, key="p1_gp_ai")
            main_cfg["show_gp_h50"] = st.checkbox("H50 50日新高提示", value=True, key="p1_gp_h50")
            main_cfg["show_gp_td9"] = st.checkbox("TD 九轉序列 (1-9 數字)", value=True, key="p1_gp_td9")
            main_cfg["show_gp_boll_burst"] = st.checkbox("保力加單邊起爆/暴跌", value=True, key="p1_gp_burst")

        st.markdown("---")
        st.markdown("### 🎛️ 副圖 16 大指標開關")
        st.caption("勾選/取消副圖指標，主畫布即時重新排版適配：")

        show_sctr = st.checkbox("1. SCTR 分數 (0-100)", value=True, key="p1_chk_sctr")
        show_rs = st.checkbox("2. RS Line 對標大盤", value=True, key="p1_chk_rs")
        show_vol = st.checkbox("3. 普通成交量 (Volume)", value=True, key="p1_chk_vol")
        show_chive = st.checkbox("4. 韭菜 vs 主力 (量價套牢)", value=True, key="p1_chk_chive")
        show_drift = st.checkbox("5. 隔夜 vs 盤中漂移背馳", value=True, key="p1_chk_drift")
        show_vwap = st.checkbox("6. 早尾盤 VWAP 博弈", value=True, key="p1_chk_vwap")
        show_finra = st.checkbox("7. FINRA 場外暗池做空%", value=True, key="p1_chk_finra")
        show_otm = st.checkbox("8. 虛值 Call 狂熱期權比", value=True, key="p1_chk_otm")
        show_spring = st.checkbox("9. SPRING DELTA 爆邊", value=True, key="p1_chk_spring")
        show_vcp = st.checkbox("10. VCP4-00 突破雷達", value=True, key="p1_chk_vcp")
        show_ttm = st.checkbox("11. GRANDPA TTM STAGE2", value=True, key="p1_chk_ttm")
        show_macd = st.checkbox("12. 正宗 MACD (動態色彩)", value=True, key="p1_chk_macd")
        show_deltame = st.checkbox("13. TRADE FORCE DELTAME", value=True, key="p1_chk_deltame")
        show_turnvix = st.checkbox("14. TRADE FORCE TURN VIX", value=True, key="p1_chk_turnvix")
        show_change = st.checkbox("15. DAILY PRICE CHANGE", value=True, key="p1_chk_change")
        show_rsi = st.checkbox("16. RSI(14) 強弱指標", value=True, key="p1_chk_rsi")

    active_indicators = []
    if show_sctr: active_indicators.append("sctr")
    if show_rs: active_indicators.append("rs")
    if show_vol: active_indicators.append("vol")
    if show_chive: active_indicators.append("chive")
    if show_drift: active_indicators.append("drift")
    if show_vwap: active_indicators.append("vwap")
    if show_finra: active_indicators.append("finra")
    if show_otm: active_indicators.append("otm")
    if show_spring: active_indicators.append("spring")
    if show_vcp: active_indicators.append("vcp")
    if show_ttm: active_indicators.append("ttm")
    if show_macd: active_indicators.append("macd")
    if show_deltame: active_indicators.append("deltame")
    if show_turnvix: active_indicators.append("turnvix")
    if show_change: active_indicators.append("change")
    if show_rsi: active_indicators.append("rsi")

    if df.empty:
        st.warning("⚠️ 暫無資產歷史價格數據，請檢查母艦主控室連線。")
        return

    # 1. 執行主圖指標計算 (組 1: MA, ANCHORZONE, VAS)
    df = compute_main_group1(df)

    # 2. 執行主圖指標計算 (組 2: GP_ALL_IN_ONE)
    df = compute_main_group2(df)

    # 3. 執行副圖第一組指標計算 (量價、訂單流、暗池、期權等)
    df = compute_group1_indicators(df, symbol, market_type, benchmark_ticker)
    
    # 4. 執行副圖第二組指標計算 (4 大富途神兵：SPRING, VCP, TTM, MACD)
    df = compute_group2_indicators(df)

    df_clean = df.dropna(subset=['Close']).copy()
    current_price = float(df_clean['Close'].iloc[-1])
    
    if len(df_clean) > 1:
        prev_price = float(df_clean['Close'].iloc[-2])
        delta_val = current_price - prev_price
        delta_percent = (delta_val / prev_price) * 100
    else:
        delta_val = 0.0
        delta_percent = 0.0
        
    ma20_val = df_clean['MA_3'].dropna() if 'MA_3' in df_clean else df_clean['Close'].rolling(20).mean().dropna()
    ma20_text = f"{ma20_val.iloc[-1]:,.2f}" if not ma20_val.empty else "更新中..."
    
    period_map = {"1mo": 21, "3mo": 63, "6mo": 126, "1y": 252, "5y": len(df_clean)}
    display_days = period_map.get(period, 63)
    df_display = df_clean.tail(display_days).copy()

    draw_and_sync_page1(df_display, df_clean, current_price, delta_val, delta_percent, ma20_text, cur_sym, symbol, market_type, period, benchmark_ticker, active_indicators, main_cfg)