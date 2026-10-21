"""
Filename: page1_sidebar_diag_calc.py
Description: Page 1 右側量化診斷面板計算與渲染引擎
"""

import streamlit as st
import pandas as pd
import numpy as np
import yfinance as yf
import plotly.graph_objects as go


def calculate_alpha_diagnostics(df_stock: pd.DataFrame, symbol: str = "NVDA", market_type: str = "美股"):
    """
    計算跑贏大市相對收益、成交活躍倍數、50日均線乖離率與 Sparkline 數據
    """
    if df_stock is None or len(df_stock) < 5:
        return None

    # 1. 決定大市對標基準 (美股 SPY / 港股 2800.HK)
    is_hk = "港股" in str(market_type) or str(symbol).upper().endswith(".HK")
    bench_symbol = "2800.HK" if is_hk else "SPY"
    bench_name = "2800.HK" if is_hk else "SPY"

    try:
        bench_ticker = yf.Ticker(bench_symbol)
        df_bench = bench_ticker.history(period="1y")
        if df_bench.empty:
            df_bench = df_stock.copy()
    except Exception:
        df_bench = df_stock.copy()

    # 統一時間軸
    df_s = df_stock.copy()
    df_b = df_bench.copy()
    df_s.index = pd.to_datetime(df_s.index).tz_localize(None)
    df_b.index = pd.to_datetime(df_b.index).tz_localize(None)

    # 2. 計算 1M (21日), 3M (63日), 6M (126日) 收益率
    def get_period_returns(s_series, b_series, days):
        if len(s_series) < days:
            days = max(2, len(s_series) - 1)
        ret_s = (s_series.iloc[-1] / s_series.iloc[-days] - 1.0) * 100.0
        
        b_idx = min(days, len(b_series) - 1)
        ret_b = (b_series.iloc[-1] / b_series.iloc[-b_idx] - 1.0) * 100.0 if b_idx > 0 else 0.0
        
        diff = ret_s - ret_b
        return ret_s, ret_b, diff

    close_s = df_s['Close']
    close_b = df_b['Close']

    s_1m, b_1m, diff_1m = get_period_returns(close_s, close_b, 21)
    s_3m, b_3m, diff_3m = get_period_returns(close_s, close_b, 63)
    s_6m, b_6m, diff_6m = get_period_returns(close_s, close_b, 126)

    # 3. 成交活躍度倍數 (當日 vs 近20日平均)
    curr_vol = float(df_s['Volume'].iloc[-1])
    avg_vol = float(df_s['Volume'].tail(20).mean()) if len(df_s) >= 20 else curr_vol
    vol_mult = (curr_vol / avg_vol) if avg_vol > 0 else 1.0

    # 4. 50 日均線乖離率 (MA50 Bias)
    ma50 = float(df_s['Close'].tail(50).mean()) if len(df_s) >= 50 else float(df_s['Close'].mean())
    curr_close = float(df_s['Close'].iloc[-1])
    ma50_bias = ((curr_close - ma50) / ma50) * 100.0 if ma50 > 0 else 0.0

    # 5. 相對強弱 Sparkline 走勢 (近 126 日)
    common_idx = df_s.index.intersection(df_b.index)[-126:]
    if len(common_idx) > 5:
        norm_s = df_s.loc[common_idx, 'Close'] / df_s.loc[common_idx[0], 'Close']
        norm_b = df_b.loc[common_idx, 'Close'] / df_b.loc[common_idx[0], 'Close']
        rel_curve = (norm_s - norm_b).tolist()
    else:
        rel_curve = [0.0] * 20

    last_date_str = df_s.index[-1].strftime("%Y-%m-%d")

    return {
        "date_str": last_date_str,
        "bench_name": bench_name,
        "is_same_as_bench": (str(symbol).upper() == bench_symbol),
        "periods": {
            "1M": {"stock": s_1m, "bench": b_1m, "diff": diff_1m},
            "3M": {"stock": s_3m, "bench": b_3m, "diff": diff_3m},
            "6M": {"stock": s_6m, "bench": b_6m, "diff": diff_6m},
        },
        "vol_mult": vol_mult,
        "ma50_bias": ma50_bias,
        "rel_curve": rel_curve
    }


def render_sidebar_diagnostics(diag_data: dict):
    """
    渲染右側黑客戰術風診斷看板
    """
    if not diag_data:
        st.info("📊 數據計算中...")
        return

    date_str = diag_data["date_str"]
    bench_name = diag_data["bench_name"]
    periods = diag_data["periods"]
    vol_mult = diag_data["vol_mult"]
    ma50_bias = diag_data["ma50_bias"]
    rel_curve = diag_data["rel_curve"]

    # 1. 頂部三卡 (大市比較 / 成交 / 50日線)
    diff_3m = periods["3M"]["diff"]
    p_status = "跑贏" if diff_3m >= 0 else "跑輸"
    p_color = "#00e676" if diff_3m >= 0 else "#ff5252"
    p_sign = "+" if diff_3m >= 0 else ""

    v_status = "活躍" if vol_mult >= 1.3 else "正常" if vol_mult >= 0.8 else "偏低"
    v_color = "#00e676" if vol_mult >= 1.0 else "#8b949e"

    m_status = "偏強" if ma50_bias >= 0 else "偏弱"
    m_color = "#00e676" if ma50_bias >= 0 else "#ff5252"
    m_sign = "+" if ma50_bias >= 0 else ""

    st.markdown(f"""
    <div style="background:#161b22; border-radius:12px; padding:12px; border:1px solid #30363d; margin-bottom:14px;">
        <div style="display:flex; justify-content:space-between; font-size:11px; color:#8b949e; margin-bottom:8px;">
            <span>以日線計算</span>
            <span>{date_str}</span>
        </div>
        <div style="display:grid; grid-template-columns:1fr 1fr 1fr; gap:6px;">
            <div style="background:#0d1117; border-radius:8px; padding:8px 4px; text-align:center; border:1px solid #30363d;">
                <div style="font-size:10px; color:#8b949e;">大市比較</div>
                <div style="font-size:13px; font-weight:700; color:{p_color}; margin:2px 0;">{p_status}</div>
                <div style="font-size:11px; color:#c9d1d9;">{p_sign}{diff_3m:.1f}%</div>
            </div>
            <div style="background:#0d1117; border-radius:8px; padding:8px 4px; text-align:center; border:1px solid #30363d;">
                <div style="font-size:10px; color:#8b949e;">成交</div>
                <div style="font-size:13px; font-weight:700; color:{v_color}; margin:2px 0;">{v_status}</div>
                <div style="font-size:11px; color:#c9d1d9;">{vol_mult:.2f}x</div>
            </div>
            <div style="background:#0d1117; border-radius:8px; padding:8px 4px; text-align:center; border:1px solid #30363d;">
                <div style="font-size:10px; color:#8b949e;">50 日線</div>
                <div style="font-size:13px; font-weight:700; color:{m_color}; margin:2px 0;">{m_status}</div>
                <div style="font-size:11px; color:#c9d1d9;">{m_sign}{ma50_bias:.1f}%</div>
            </div>
        </div>
    </div>
    """, unsafe_allow_html=True)

    # 2. 週期切換單選
    st.markdown("<p style='font-size:13px; font-weight:700; margin-bottom:4px;'>跑贏大市嗎？</p>", unsafe_allow_html=True)
    
    r_1m = f"1 個月 ({'+' if periods['1M']['diff'] >= 0 else ''}{periods['1M']['diff']:.1f}%)"
    r_3m = f"3 個月 ({'+' if periods['3M']['diff'] >= 0 else ''}{periods['3M']['diff']:.1f}%)"
    r_6m = f"6 個月 ({'+' if periods['6M']['diff'] >= 0 else ''}{periods['6M']['diff']:.1f}%)"

    sel_period = st.radio("選擇比較週期", [r_1m, r_3m, r_6m], index=2, label_visibility="collapsed")

    if "1 個月" in sel_period:
        active_key = "1M"
        label_txt = "近 1 個月"
    elif "3 個月" in sel_period:
        active_key = "3M"
        label_txt = "近 3 個月"
    else:
        active_key = "6M"
        label_txt = "近 6 個月"

    p_data = periods[active_key]
    diff_val = p_data["diff"]
    s_ret = p_data["stock"]
    b_ret = p_data["bench"]

    is_win = diff_val >= 0
    box_bg = "rgba(0, 230, 118, 0.12)" if is_win else "rgba(255, 82, 82, 0.15)"
    box_border = "#00e676" if is_win else "#ff5252"
    txt_color = "#00e676" if is_win else "#ff6b6b"
    action_word = "跑贏" if is_win else "跑輸"

    # 動態橫幅
    st.markdown(f"""
    <div style="background:{box_bg}; border-left:4px solid {box_border}; border-radius:4px; padding:8px 12px; margin:8px 0; font-size:12px; font-weight:700; color:{txt_color};">
        {label_txt} {action_word}大市 ({bench_name}) {abs(diff_val):.1f}%
    </div>
    """, unsafe_allow_html=True)

    # 3. 雙條形數值展示
    st.markdown(f"""
    <div style="background:#161b22; border-radius:8px; padding:10px 12px; border:1px solid #30363d; margin-bottom:12px;">
        <div style="display:flex; justify-content:space-between; align-items:center; margin-bottom:6px; font-size:11.5px;">
            <span style="color:#c9d1d9;">呢隻股票</span>
            <span style="color:{'#00e676' if s_ret >= 0 else '#ff5252'}; font-weight:700;">{'+' if s_ret >= 0 else ''}{s_ret:.1f}%</span>
        </div>
        <div style="display:flex; justify-content:space-between; align-items:center; font-size:11.5px;">
            <span style="color:#8b949e;">大市 ({bench_name})</span>
            <span style="color:{'#00e676' if b_ret >= 0 else '#ff5252'}; font-weight:700;">{'+' if b_ret >= 0 else ''}{b_ret:.1f}%</span>
        </div>
    </div>
    """, unsafe_allow_html=True)

    # 4. 微型走勢線 (Sparkline)
    if rel_curve:
        line_color = "#00e676" if is_win else "#ff5252"
        fig_spark = go.Figure()
        fig_spark.add_trace(go.Scatter(
            y=rel_curve,
            mode='lines',
            line=dict(color=line_color, width=2),
            hoverinfo='skip'
        ))
        fig_spark.update_layout(
            height=70,
            margin=dict(l=0, r=0, t=2, b=2),
            xaxis=dict(visible=False),
            yaxis=dict(visible=False),
            plot_bgcolor='rgba(0,0,0,0)',
            paper_bgcolor='#0d1117'
        )
        st.plotly_chart(fig_spark, use_container_width=True, config={'displayModeBar': False})


# 保留別名相容
calculate_diagnostics = calculate_alpha_diagnostics
render_diagnostics = render_sidebar_diagnostics