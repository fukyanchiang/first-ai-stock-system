"""
Filename: component_gann_harmonic_arcs.py
Description: ⏳ 江恩諧波時間跳躍弧 (Harmonic Time Arcs) 與未來推算暗區共用核心組件 (全江恩頁面共用)
修復說明：
  1. 徹底解決 Streamlit 因 Markdown 4 格縮排與 HTML 註解誤判為代碼塊 (Raw Code Block) 的問題
  2. 完美渲染「交易日校準 + 頂底極性指引」未來倒數矩陣看板
  3. 主圖推算區底部膠囊採用交錯抗擠壓微錯位 (50%/100% 居下，75% 居上)
"""

import pandas as pd
import numpy as np
import plotly.graph_objects as go
import streamlit as st


def snap_to_trading_day(dt: pd.Timestamp) -> pd.Timestamp:
    """若遇到週六或週日，自動回退到週五交易日"""
    if dt.dayofweek == 5:  # Saturday
        return dt - pd.Timedelta(days=1)
    elif dt.dayofweek == 6:  # Sunday
        return dt - pd.Timedelta(days=2)
    return dt


def add_trading_days(start_date: pd.Timestamp, n_bars: int) -> pd.Timestamp:
    """按交易日 (週一至週五) 推算未來目標日期"""
    cur = pd.Timestamp(start_date)
    added = 0
    while added < n_bars:
        cur += pd.Timedelta(days=1)
        if cur.dayofweek < 5:
            added += 1
    return cur


def compute_harmonic_arcs_data(df: pd.DataFrame, r_period: int = 47, manual_a1_date=None, manual_a2_date=None):
    if df is None or len(df) < 5:
        return None

    dates_hist = df.index
    last_close = float(df['Close'].iloc[-1])

    if manual_a2_date and pd.to_datetime(manual_a2_date) in dates_hist:
        a2_date = pd.to_datetime(manual_a2_date)
    else:
        a2_date = dates_hist[-1]

    a2_idx = dates_hist.get_loc(a2_date)
    a1_idx = max(0, a2_idx - r_period)
    a1_date = dates_hist[a1_idx]

    p_a1 = float(df.loc[a1_date, 'Close'])
    p_a2 = float(df.loc[a2_date, 'Close'])

    a2_is_peak = bool(p_a2 > p_a1 and p_a2 >= df['Close'].iloc[-min(len(df), r_period):].max() * 0.98)
    a1_type_str = "結構高點" if a2_is_peak else "結構低點"
    a2_type_str = "結構高點" if a2_is_peak else "結構低點"

    bars_50 = max(1, int(round(r_period * 0.50)))
    bars_75 = max(1, int(round(r_period * 0.75)))
    bars_100 = max(1, int(r_period))

    dt_50_center = snap_to_trading_day(add_trading_days(a2_date, bars_50))
    dt_75_center = snap_to_trading_day(add_trading_days(a2_date, bars_75))
    dt_100_center = snap_to_trading_day(add_trading_days(a2_date, bars_100))

    dt_50_start = snap_to_trading_day(dt_50_center - pd.Timedelta(days=3))
    dt_50_end = snap_to_trading_day(dt_50_center + pd.Timedelta(days=3))

    dt_75_start = snap_to_trading_day(dt_75_center - pd.Timedelta(days=3))
    dt_75_end = snap_to_trading_day(dt_75_center + pd.Timedelta(days=3))

    dt_100_start = snap_to_trading_day(dt_100_center - pd.Timedelta(days=3))
    dt_100_end = snap_to_trading_day(dt_100_center + pd.Timedelta(days=3))

    if not a2_is_peak:
        pol_50 = {
            'role': 'PEAK',
            'title': '50% 諧波峰值',
            'desc': '預期波段見頂 · 逢高減倉防守',
            'badge': '▲ 頂部峰值',
            'color': '#f59e0b',
            'bg': 'rgba(245, 158, 11, 0.25)',
            'border': '#f59e0b'
        }
        pol_75 = {
            'role': 'TRANS',
            'title': '75% 尋底過渡',
            'desc': '下行尋底過渡期 · 防回踩整理',
            'badge': '⏳ 尋底過渡',
            'color': '#c084fc',
            'bg': 'rgba(192, 132, 252, 0.25)',
            'border': '#a855f7'
        }
        pol_100 = {
            'role': 'TROUGH',
            'title': '週期邊界谷底',
            'desc': '預期大週期變盤見底 · 逢低佈局',
            'badge': '▼ 週期谷底',
            'color': '#2dd4bf',
            'bg': 'rgba(45, 212, 191, 0.25)',
            'border': '#14b8a6'
        }
    else:
        pol_50 = {
            'role': 'TROUGH',
            'title': '50% 諧波谷底',
            'desc': '預期回踩到位 · 逢低試多',
            'badge': '▼ 谷底支撐',
            'color': '#2dd4bf',
            'bg': 'rgba(45, 212, 191, 0.25)',
            'border': '#14b8a6'
        }
        pol_75 = {
            'role': 'TRANS',
            'title': '75% 尋頂過渡',
            'desc': '上行脈衝過渡期 · 關注量能',
            'badge': '⏳ 尋頂過渡',
            'color': '#c084fc',
            'bg': 'rgba(192, 132, 252, 0.25)',
            'border': '#a855f7'
        }
        pol_100 = {
            'role': 'PEAK',
            'title': '週期邊界峰頂',
            'desc': '預期大週期見頂 · 戰略獲利',
            'badge': '▲ 週期峰值',
            'color': '#f59e0b',
            'bg': 'rgba(245, 158, 11, 0.25)',
            'border': '#f59e0b'
        }

    chart_end_date = snap_to_trading_day(dt_100_end + pd.Timedelta(days=12))

    return {
        'df': df,
        'r_period': r_period,
        'a1_date': a1_date,
        'a2_date': a2_date,
        'a1_type_str': a1_type_str,
        'a2_type_str': a2_type_str,
        'a2_is_peak': a2_is_peak,
        'last_close': last_close,
        'chart_end_date': chart_end_date,
        'dt_50_center': dt_50_center,
        'dt_50_start': dt_50_start,
        'dt_50_end': dt_50_end,
        'bars_50': bars_50,
        'pol_50': pol_50,
        'dt_75_center': dt_75_center,
        'dt_75_start': dt_75_start,
        'dt_75_end': dt_75_end,
        'bars_75': bars_75,
        'pol_75': pol_75,
        'dt_100_center': dt_100_center,
        'dt_100_start': dt_100_start,
        'dt_100_end': dt_100_end,
        'bars_100': bars_100,
        'pol_100': pol_100,
    }


def inject_future_projection_zone(fig: go.Figure, harmonic_data: dict, yaxis_name: str = 'y'):
    if not harmonic_data:
        return

    df = harmonic_data['df']
    a2_date = harmonic_data['a2_date']
    chart_end = harmonic_data['chart_end_date']

    p_min = float(df['Low'].min()) * 0.96
    p_max = float(df['High'].max()) * 1.04

    fig.add_shape(
        type="rect", xref="x", yref=yaxis_name,
        x0=a2_date, x1=chart_end, y0=p_min, y1=p_max,
        line=dict(color="rgba(56, 189, 248, 0.40)", width=1.5, dash="dash"),
        fillcolor="rgba(15, 23, 42, 0.20)", layer="below"
    )

    fig.add_annotation(
        xref="x", yref=yaxis_name,
        x=a2_date, y=p_max,
        text="<b>🔮 推算區域 (Future Zone)</b>",
        bgcolor="#0f172a", bordercolor="#38bdf8", borderwidth=1.2, borderpad=4,
        font=dict(color="#38bdf8", size=9.5, family="Arial, sans-serif"),
        showarrow=False, xanchor="left", yanchor="top"
    )

    windows = [
        (harmonic_data['dt_50_start'], harmonic_data['dt_50_end'], harmonic_data['dt_50_center'], harmonic_data['pol_50'], 4),
        (harmonic_data['dt_75_start'], harmonic_data['dt_75_end'], harmonic_data['dt_75_center'], harmonic_data['pol_75'], 24),
        (harmonic_data['dt_100_start'], harmonic_data['dt_100_end'], harmonic_data['dt_100_center'], harmonic_data['pol_100'], 4),
    ]

    for w_st, w_ed, w_center, pol, y_offset_px in windows:
        fig.add_shape(
            type="rect", xref="x", yref=yaxis_name,
            x0=w_st, x1=w_ed, y0=p_min, y1=p_max,
            line=dict(color=pol['border'], width=1.2, dash="dash"),
            fillcolor=pol['bg'], layer="below"
        )
        fig.add_shape(
            type="line", xref="x", yref=yaxis_name,
            x0=w_center, x1=w_center, y0=p_min, y1=p_max,
            line=dict(color=pol['color'], width=1.4, dash="dot")
        )
        txt_label = f"<b>{pol['badge']}<br>{w_center.strftime('%m/%d')}</b>"
        fig.add_annotation(
            xref="x", yref=yaxis_name,
            x=w_center, y=p_min,
            yshift=y_offset_px,
            text=txt_label,
            bgcolor="#0a0e14",
            bordercolor=pol['border'],
            borderwidth=1.5,
            borderpad=3,
            font=dict(color=pol['color'], size=9.0, family="monospace"),
            showarrow=False, xanchor="center", yanchor="bottom"
        )


def inject_harmonic_arcs_traces(fig: go.Figure, harmonic_data: dict, yaxis_name: str = 'y'):
    if not harmonic_data:
        return

    df = harmonic_data['df']
    a1_date = harmonic_data['a1_date']
    a2_date = harmonic_data['a2_date']
    chart_end = harmonic_data['chart_end_date']

    all_dates = pd.date_range(df.index[0], chart_end, freq='D')
    all_dates = all_dates[all_dates.dayofweek < 5]

    a1_idx = all_dates.get_loc(a1_date) if a1_date in all_dates else int(np.argmin(np.abs(all_dates - a1_date)))
    a2_idx = all_dates.get_loc(a2_date) if a2_date in all_dates else int(np.argmin(np.abs(all_dates - a2_date)))

    cycle_bars = max(10, a2_idx - a1_idx)
    idx_arr = np.arange(len(all_dates)) - a1_idx

    w_full = np.pi / cycle_bars
    h_full = np.abs(np.sin(w_full * idx_arr)) * 100.0

    w_half = np.pi / (cycle_bars * 0.5)
    h_half = np.abs(np.sin(w_half * idx_arr)) * 60.0

    w_quarter = np.pi / (cycle_bars * 0.25)
    h_quarter = np.abs(np.sin(w_quarter * idx_arr)) * 35.0

    mask_hist = (idx_arr <= (a2_idx - a1_idx))
    mask_future = ~mask_hist

    fig.add_trace(go.Scatter(
        x=all_dates[mask_hist], y=h_full[mask_hist],
        mode='lines', line=dict(color='#2dd4bf', width=1.8),
        name='全弧 (歷史)', yaxis=yaxis_name, showlegend=False
    ))
    fig.add_trace(go.Scatter(
        x=all_dates[mask_future], y=h_full[mask_future],
        mode='lines', line=dict(color='#2dd4bf', width=1.8, dash='dash'),
        name='全弧 (未來)', yaxis=yaxis_name, showlegend=False
    ))

    fig.add_trace(go.Scatter(
        x=all_dates[mask_hist], y=h_half[mask_hist],
        mode='lines', line=dict(color='#f59e0b', width=1.4),
        name='半弧 (歷史)', yaxis=yaxis_name, showlegend=False
    ))
    fig.add_trace(go.Scatter(
        x=all_dates[mask_future], y=h_half[mask_future],
        mode='lines', line=dict(color='#f59e0b', width=1.4, dash='dash'),
        name='半弧 (未來)', yaxis=yaxis_name, showlegend=False
    ))

    fig.add_trace(go.Scatter(
        x=all_dates[mask_hist], y=h_quarter[mask_hist],
        mode='lines', line=dict(color='#a855f7', width=1.1),
        name='四分弧 (歷史)', yaxis=yaxis_name, showlegend=False
    ))
    fig.add_trace(go.Scatter(
        x=all_dates[mask_future], y=h_quarter[mask_future],
        mode='lines', line=dict(color='#a855f7', width=1.1, dash='dash'),
        name='四分弧 (未來)', yaxis=yaxis_name, showlegend=False
    ))

    mask_a1_a2 = (idx_arr >= 0) & (idx_arr <= (a2_idx - a1_idx))
    h_a1_a2 = np.sin((np.pi / (a2_idx - a1_idx)) * idx_arr) * 115.0
    fig.add_trace(go.Scatter(
        x=all_dates[mask_a1_a2], y=h_a1_a2[mask_a1_a2],
        mode='lines', line=dict(color='rgba(255, 255, 255, 0.85)', width=1.5, dash='dash'),
        name='A1-A2 實線', yaxis=yaxis_name, showlegend=False
    ))

    fig.add_annotation(
        xref="paper", yref=f"{yaxis_name} domain",
        x=0.015, y=0.90,
        text="<b>HARMONIC TIME ARCS</b> · <span style='color:#2dd4bf;'>● 全弧</span> <span style='color:#f59e0b;'>● 半弧</span> <span style='color:#a855f7;'>● 四分弧</span> · <span style='color:#ffffff;'>-- A1→A2 實線</span>",
        bgcolor="rgba(15, 23, 42, 0.85)", font=dict(color="#ffffff", size=9.5, family="monospace"),
        showarrow=False, xanchor="left"
    )


def render_harmonic_countdown_matrix_ui(harmonic_data: dict):
    if not harmonic_data:
        return

    p50 = harmonic_data['pol_50']
    p75 = harmonic_data['pol_75']
    p100 = harmonic_data['pol_100']

    # 確保 HTML 每一行均無 4 格縮排，且無 HTML 註解，防止 Markdown 誤轉為代碼塊
    lines = [
        '<div style="background-color:#0d1117; border:1px solid #30363d; border-radius:8px; padding:12px 16px; margin-top:14px; font-family:sans-serif;">',
        '<div style="display:flex; justify-content:space-between; align-items:center; margin-bottom:10px;">',
        '<div style="color:#ffffff; font-size:13px; font-weight:bold;">⏳ 未來時間窗口倒數矩陣 (Time Window Countdown Matrix · 交易日校準版)</div>',
        '<div style="color:#8b949e; font-size:11px;">時間結構不代表價格方向，但具備頂底轉折高勝率 · 自動跳過非交易日</div>',
        '</div>',
        '<div style="display:flex; gap:16px; flex-wrap:wrap;">',
        '<div style="flex:2.2; display:flex; flex-direction:column; gap:8px;">',
        f'<div style="background:#161b22; border:1px solid {p50["border"]}; border-left:4px solid {p50["border"]}; border-radius:6px; padding:8px 12px; display:flex; justify-content:space-between; align-items:center;">',
        '<div>',
        f'<span style="color:{p50["color"]}; font-weight:bold; font-size:12px; margin-right:8px;">{p50["title"]}</span>',
        f'<span style="color:#ffffff; font-size:12px; font-weight:600;">{harmonic_data["dt_50_start"].strftime("%Y-%m-%d")} ~ {harmonic_data["dt_50_end"].strftime("%Y-%m-%d")}</span>',
        f'<span style="color:#94a3b8; font-size:11px; margin-left:6px;">(中心 {harmonic_data["dt_50_center"].strftime("%Y-%m-%d")})</span>',
        f'<div style="color:#cbd5e1; font-size:11px; margin-top:2px;">⚡ 戰術預期：{p50["desc"]}</div>',
        '</div>',
        f'<div style="background:{p50["bg"]}; color:{p50["color"]}; border:1px solid {p50["border"]}; padding:3px 10px; border-radius:4px; font-weight:bold; font-size:11.5px; font-family:monospace;">約 {harmonic_data["bars_50"]} bars</div>',
        '</div>',
        f'<div style="background:#161b22; border:1px solid {p75["border"]}; border-left:4px solid {p75["border"]}; border-radius:6px; padding:8px 12px; display:flex; justify-content:space-between; align-items:center;">',
        '<div>',
        f'<span style="color:{p75["color"]}; font-weight:bold; font-size:12px; margin-right:8px;">{p75["title"]}</span>',
        f'<span style="color:#ffffff; font-size:12px; font-weight:600;">{harmonic_data["dt_75_start"].strftime("%Y-%m-%d")} ~ {harmonic_data["dt_75_end"].strftime("%Y-%m-%d")}</span>',
        f'<span style="color:#94a3b8; font-size:11px; margin-left:6px;">(中心 {harmonic_data["dt_75_center"].strftime("%Y-%m-%d")})</span>',
        f'<div style="color:#cbd5e1; font-size:11px; margin-top:2px;">⚡ 戰術預期：{p75["desc"]}</div>',
        '</div>',
        f'<div style="background:{p75["bg"]}; color:{p75["color"]}; border:1px solid {p75["border"]}; padding:3px 10px; border-radius:4px; font-weight:bold; font-size:11.5px; font-family:monospace;">約 {harmonic_data["bars_75"]} bars</div>',
        '</div>',
        f'<div style="background:#161b22; border:1px solid {p100["border"]}; border-left:4px solid {p100["border"]}; border-radius:6px; padding:8px 12px; display:flex; justify-content:space-between; align-items:center;">',
        '<div>',
        f'<span style="color:{p100["color"]}; font-weight:bold; font-size:12px; margin-right:8px;">{p100["title"]}</span>',
        f'<span style="color:#ffffff; font-size:12px; font-weight:600;">{harmonic_data["dt_100_start"].strftime("%Y-%m-%d")} ~ {harmonic_data["dt_100_end"].strftime("%Y-%m-%d")}</span>',
        f'<span style="color:#94a3b8; font-size:11px; margin-left:6px;">(中心 {harmonic_data["dt_100_center"].strftime("%Y-%m-%d")})</span>',
        f'<div style="color:#cbd5e1; font-size:11px; margin-top:2px;">⚡ 戰術預期：{p100["desc"]}</div>',
        '</div>',
        f'<div style="background:{p100["bg"]}; color:{p100["color"]}; border:1px solid {p100["border"]}; padding:3px 10px; border-radius:4px; font-weight:bold; font-size:11.5px; font-family:monospace;">約 {harmonic_data["bars_100"]} bars</div>',
        '</div>',
        '</div>',
        '<div style="flex:1; background:#161b22; border:1px solid #30363d; border-radius:6px; padding:10px 14px; display:flex; flex-direction:column; justify-content:space-between;">',
        '<div>',
        '<div style="color:#ffffff; font-size:12px; font-weight:bold; margin-bottom:8px;">結構起點與鎖相 (Phase Locking)</div>',
        '<div style="display:flex; justify-content:space-between; font-size:11.5px; margin-bottom:5px;">',
        f'<span style="color:#8b949e;">A1 {harmonic_data["a1_type_str"]}:</span>',
        f'<span style="color:#ffffff; font-family:monospace; font-weight:bold;">{harmonic_data["a1_date"].strftime("%Y-%m-%d")}</span>',
        '</div>',
        '<div style="display:flex; justify-content:space-between; font-size:11.5px; margin-bottom:8px;">',
        f'<span style="color:#8b949e;">A2 {harmonic_data["a2_type_str"]}:</span>',
        f'<span style="color:#ffffff; font-family:monospace; font-weight:bold;">{harmonic_data["a2_date"].strftime("%Y-%m-%d")}</span>',
        '</div>',
        '</div>',
        '<div style="background:rgba(2,132,199,0.15); border:1px solid #0284c7; border-radius:4px; padding:6px 10px; text-align:center;">',
        f'<span style="color:#38bdf8; font-size:11px; font-weight:bold;">沿用基準週期: R = {harmonic_data["r_period"]} 根 K 線</span>',
        '</div>',
        '</div>',
        '</div>',
        '</div>'
    ]
    st.markdown("".join(lines), unsafe_allow_html=True)