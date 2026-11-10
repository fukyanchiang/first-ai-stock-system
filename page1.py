"""
Filename: page1.py
Description: 📊 艙房一：六維王者矩陣 (股票) 主調度引擎 (100% 直連納指 3,380 隻全量資料庫·已徹底根除時區失配與快取死鎖)
- 🎛️ 頂部控制工具列：【日線圖/週線圖切換掣】＋【🔭 K 線縮放拉桿 (30-250 Bars)】
- 🌟 4 大 DataLouder 機構級真實副圖 (嚴格置於 SCTR 上方)：
  0a. ATR-14 (真實個股波幅與動態風控通道)
  0b. 恐慌貪婪指數 (納指 3,380 隻多因子大腦 ＋ 252 日動態微彎高斯包絡帶)
  0c. 納指全量市寬-50 (直連本地 nasdaq_macro_history.csv 3,380 隻全景生命線)
  0d. 納指 52 週淨新高/新低 (直連本地 3,380 隻全景推進力，長短錯落雙色柱狀圖)
- 主圖 4 大指標與信號模組 (MA, ANCHORZONE, VAS S+++, GP_ALL_IN_ONE)
- 🌟 右側雙層 VPVR 重貨柱 (近期青藍/粉紅 + 歷史黃褐/紫色 + 雙重 POC)
- 🌟 注入右側未來時間軌道點，實現十字準星線 100% 貫穿「右側重貨柱 ＋ 20 層副圖」
- 側邊欄 Checkbox 圖層控制台 (主圖 + 20 個副圖獨立開關，勾選自適應排版)
- 五維共振 Smart/Dumb Spread 決策雷達 + 右側 Alpha 體檢面板
"""

import os
import pandas as pd
import numpy as np
import streamlit as st
import plotly.graph_objects as go

# 導入主圖運算與渲染模組
from page1_main_indicator01_calc import (
    compute_main_group1,
    render_main_group1,
    compute_page1_dual_vpvr,
    render_page1_dual_vpvr
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

# 引入獨立封裝的右側量化診斷模組
from page1_sidebar_diag_calc import (
    calculate_alpha_diagnostics,
    render_sidebar_diagnostics
)

# ===================================================
# 🏛️ 1. 本地全量 3,380 隻真實宏觀資料庫載入引擎
# ===================================================
def load_real_nasdaq_3380_macro(chart_dates: pd.DatetimeIndex):
    csv_path = "nasdaq_macro_history.csv"
    
    if not os.path.exists(csv_path):
        empty_breadth = pd.DataFrame({"Slow_50MA": [50.0] * len(chart_dates)}, index=chart_dates)
        empty_nhnl = pd.DataFrame({
            "New_Highs": [0] * len(chart_dates),
            "New_Lows": [0] * len(chart_dates),
            "Net_Highs": [0] * len(chart_dates),
            "Sentiment": [50.0] * len(chart_dates),
            "Upper_2SD": [75.0] * len(chart_dates),
            "Upper_1SD": [60.0] * len(chart_dates),
            "Lower_1SD": [35.0] * len(chart_dates),
            "Lower_2SD": [15.0] * len(chart_dates),
            "Total_Valid": [3380] * len(chart_dates)
        }, index=chart_dates)
        return empty_breadth, empty_nhnl, 200, False

    try:
        df_macro = pd.read_csv(csv_path)
        if "Date" in df_macro.columns:
            df_macro["Date"] = pd.to_datetime(df_macro["Date"])
            df_macro.set_index("Date", inplace=True)
        else:
            df_macro.index = pd.to_datetime(df_macro.index)

        # 消除時區並標準化為純日期
        if hasattr(df_macro.index, 'tz') and df_macro.index.tz is not None:
            macro_index = df_macro.index.tz_localize(None).normalize()
        else:
            macro_index = pd.to_datetime(df_macro.index).normalize()
        df_macro.index = macro_index
        df_macro = df_macro[~df_macro.index.duplicated(keep='last')]

        # 對齊目標 K 線日期
        if hasattr(chart_dates, 'tz') and chart_dates.tz is not None:
            target_dates = chart_dates.tz_localize(None).normalize()
        else:
            target_dates = pd.to_datetime(chart_dates).normalize()

        df_aligned = df_macro.reindex(target_dates).ffill().bfill()
        df_aligned.index = chart_dates

        df_breadth = pd.DataFrame({
            "Slow_50MA": df_aligned["Breadth_50"].round(2)
        }, index=chart_dates)

        df_nhnl = pd.DataFrame({
            "New_Highs": df_aligned.get("New_Highs", 0).astype(int),
            "New_Lows": df_aligned.get("New_Lows", 0).astype(int),
            "Net_Highs": df_aligned.get("Net_Highs", 0).astype(int),
            "Sentiment": df_aligned.get("Sentiment", 50.0).round(2),
            "Upper_2SD": df_aligned.get("Upper_2SD", 75.0).round(3),
            "Upper_1SD": df_aligned.get("Upper_1SD", 60.0).round(3),
            "Lower_1SD": df_aligned.get("Lower_1SD", 35.0).round(3),
            "Lower_2SD": df_aligned.get("Lower_2SD", 15.0).round(3),
            "Total_Valid": 3380
        }, index=chart_dates)

        max_net_abs = int(max(abs(df_nhnl["Net_Highs"].min()), abs(df_nhnl["Net_Highs"].max())))
        ceil_net = max(int(max_net_abs * 1.35), 200)

        return df_breadth, df_nhnl, ceil_net, True

    except Exception as e:
        st.error(f"⚠️ 解析本地 3,380 隻全量宏觀資料庫失敗: {e}")
        empty_breadth = pd.DataFrame({"Slow_50MA": [50.0] * len(chart_dates)}, index=chart_dates)
        empty_nhnl = pd.DataFrame({
            "New_Highs": [0] * len(chart_dates),
            "New_Lows": [0] * len(chart_dates),
            "Net_Highs": [0] * len(chart_dates),
            "Sentiment": [50.0] * len(chart_dates),
            "Upper_2SD": [75.0] * len(chart_dates),
            "Upper_1SD": [60.0] * len(chart_dates),
            "Lower_1SD": [35.0] * len(chart_dates),
            "Lower_2SD": [15.0] * len(chart_dates),
            "Total_Valid": [3380] * len(chart_dates)
        }, index=chart_dates)
        return empty_breadth, empty_nhnl, 200, False

def compute_atr14(df: pd.DataFrame, period: int = 14) -> pd.Series:
    """計算真實個股真實波幅 ATR-14 (Wilder's TR 平滑)"""
    high = df['High']
    low = df['Low']
    close = df['Close'].shift(1)
    tr1 = high - low
    tr2 = (high - close).abs()
    tr3 = (low - close).abs()
    tr = pd.concat([tr1, tr2, tr3], axis=1).max(axis=1)
    return tr.rolling(window=period, min_periods=1).mean()

# ===================================================
# 🎨 2. 渲染 4 大宏觀與波幅副圖模組
# ===================================================
def render_macro_traces(fig, indicator_key, df_display, df_breadth, df_nhnl, ceil_net, y_ax, dm, y_num, y_axes_config, cur_sym, is_db_ready):
    if indicator_key == "atr14":
        atr_val = df_display['ATR_14'] if 'ATR_14' in df_display else pd.Series(0.0, index=df_display.index)
        fig.add_trace(go.Scatter(
            x=df_display.index, y=atr_val,
            mode='lines', line=dict(color='#26a69a', width=2.0),
            name='ATR-14 (真實波幅)', yaxis=y_ax,
            hovertemplate=f'<b>ATR-14: {cur_sym}%{{y:.2f}}</b><extra></extra>'
        ))
        y_axes_config[f'yaxis{y_num}'] = dict(
            domain=dm, anchor='x', title_text="ATR-14", gridcolor='#2e3d52',
            showspikes=True, spikemode='across', spikedash='dash',
            spikecolor='#a0aec0', spikethickness=1.2, spikesnap='cursor'
        )

    elif indicator_key == "fear_greed":
        sent = df_nhnl['Sentiment'].fillna(50.0)
        u2 = df_nhnl['Upper_2SD'].fillna(75.0)
        u1 = df_nhnl['Upper_1SD'].fillna(60.0)
        l1 = df_nhnl['Lower_1SD'].fillna(35.0)
        l2 = df_nhnl['Lower_2SD'].fillna(15.0)

        fig.add_trace(go.Scatter(
            x=df_display.index, y=u2, mode='lines',
            line=dict(color='#ef5350', width=1.4, dash='dash'),
            name='恐慌貪婪 upper 2sd', yaxis=y_ax,
            hovertemplate='<b>● 恐慌貪婪 upper 2sd: %{y:.3f}</b><extra></extra>'
        ))
        fig.add_trace(go.Scatter(
            x=df_display.index, y=u1, mode='lines',
            line=dict(color='#00e5ff', width=1.1, dash='dot'),
            name='恐慌貪婪 upper 1sd', yaxis=y_ax,
            hovertemplate='<b>● 恐慌貪婪 upper 1sd: %{y:.3f}</b><extra></extra>'
        ))
        fig.add_trace(go.Scatter(
            x=df_display.index, y=l1, mode='lines',
            line=dict(color='#00e5ff', width=1.1, dash='dot'),
            name='恐慌貪婪 lower 1sd', yaxis=y_ax,
            hovertemplate='<b>● 恐慌貪婪 lower 1sd: %{y:.3f}</b><extra></extra>'
        ))
        fig.add_trace(go.Scatter(
            x=df_display.index, y=l2, mode='lines',
            line=dict(color='#ef5350', width=1.4, dash='dash'),
            name='恐慌貪婪 lower 2sd', yaxis=y_ax,
            hovertemplate='<b>● 恐慌貪婪 lower 2sd: %{y:.3f}</b><extra></extra>'
        ))

        fig.add_trace(go.Scatter(
            x=df_display.index, y=sent, mode='lines',
            line=dict(color='#ff2a55', width=2.2),
            name='恐慌貪婪指數 (3380隻)', yaxis=y_ax,
            hovertemplate='<b>● 恐慌貪婪指數: %{y:.1f}</b><extra></extra>'
        ))

        y_axes_config[f'yaxis{y_num}'] = dict(
            domain=dm, anchor='x', title_text="恐慌貪婪", range=[0, 100],
            tickvals=[0, 20, 40, 60, 80, 100], tickfont=dict(color="#ffffff", size=10),
            gridcolor='#2e3d52', showspikes=True, spikemode='across',
            spikedash='dash', spikecolor='#a0aec0', spikethickness=1.2, spikesnap='cursor'
        )

    elif indicator_key == "breadth50":
        b50 = df_breadth['Slow_50MA'].fillna(50.0)
        fig.add_trace(go.Scatter(
            x=df_display.index, y=b50, mode='lines',
            line=dict(color='#ef5350', width=2.2),
            name='全量市寬-50 (3,380隻)', yaxis=y_ax,
            hovertemplate='<b>全量市寬-50: %{y:.2f}%</b><extra></extra>'
        ))

        for y_ref, c_ref, dash_style in [(80, '#ff3366', 'dash'), (50, '#94a3b8', 'dot'), (20, '#00ff88', 'dash')]:
            fig.add_trace(go.Scatter(
                x=[df_display.index[0], df_display.index[-1]],
                y=[y_ref, y_ref], mode='lines',
                line=dict(color=c_ref, width=1.0, dash=dash_style),
                showlegend=False, yaxis=y_ax, hoverinfo='skip'
            ))

        y_axes_config[f'yaxis{y_num}'] = dict(
            domain=dm, anchor='x', title_text="全量市寬 %", range=[0, 100],
            tickvals=[20, 50, 80], ticktext=["20.00%", "50.00%", "80.00%"],
            tickfont=dict(color="#00ff88", size=10), gridcolor='#2e3d52',
            showspikes=True, spikemode='across', spikedash='dash',
            spikecolor='#a0aec0', spikethickness=1.2, spikesnap='cursor'
        )

    elif indicator_key == "net_nhnl":
        net_h = df_nhnl['Net_Highs'].fillna(0).astype(int)
        net_colors = ['#4caf50' if val >= 0 else '#e91e63' for val in net_h]

        fig.add_trace(go.Bar(
            x=df_display.index, y=net_h,
            marker_color=net_colors, opacity=0.88,
            name='52 週淨新高/低 (3,380隻)', yaxis=y_ax,
            hovertemplate='<b>淨新高/低: %{y} 隻</b><extra></extra>'
        ))

        y_axes_config[f'yaxis{y_num}'] = dict(
            domain=dm, anchor='x', title_text="淨新高/低",
            range=[-ceil_net, ceil_net], zeroline=True,
            zerolinecolor='#ffffff', zerolinewidth=1.2,
            gridcolor='#2e3d52', showspikes=True, spikemode='across',
            spikedash='dash', spikecolor='#a0aec0', spikethickness=1.2, spikesnap='cursor'
        )

# ===================================================
# 🎨 3. 繪圖與大腦同步核心
# ===================================================
def draw_and_sync_page1(df_display, df_clean, current_price, delta_val, delta_percent, ma20_text, cur_sym, symbol, market_type, period, benchmark_ticker, active_indicators, main_cfg, df_breadth, df_nhnl, ceil_net, is_db_ready):
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

    if not is_db_ready:
        st.info("💡 **資料庫狀態提示**：尚未檢測到本機全量歷史庫 `nasdaq_macro_history.csv`。請在 Terminal 執行 `python3 sync_all_indices_eod.py --target qqq`。目前已開啟安全連動。")

    ctrl_col1, _ = st.columns([2.5, 1.5])
    with ctrl_col1:
        show_legend = st.checkbox("👁️ 顯示指標圖例說明 (手機睇盤建議關閉以獲取超闊 K 線)", value=False, key="p1_show_legend_toggle")

    # 3. 副圖圖層排列：新指標置於 SCTR 上方
    ordered_keys = [
        "atr14", "fear_greed", "breadth50", "net_nhnl",
        "sctr", "rs", "vol", "chive", "drift", "vwap", "finra", "otm",
        "spring", "vcp", "ttm", "macd", "deltame", "turnvix", "change", "rsi"
    ]
    display_keys = [k for k in ordered_keys if k in active_indicators]

    num_subs = len(display_keys)
    if num_subs == 0:
        price_domain = [0.0, 1.0]
        chart_height = 650
        domains = {}
    else:
        chart_height = max(700, 450 + num_subs * 140)
        price_ratio = 0.20 if num_subs >= 8 else 0.28
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
    y_axes_config['yaxis'] = dict(
        domain=price_domain, anchor='x', title_text="價格", gridcolor='#2e3d52',
        showspikes=True, spikemode='across', spikedash='dash',
        spikecolor='#a0aec0', spikethickness=1.2, spikesnap='cursor'
    )

    fig = go.Figure()

    # 4. 右側雙層 VPVR 成交重貨柱與時間軸延伸
    show_vpvr = main_cfg.get("show_vpvr", True)
    display_start_dt = pd.to_datetime(df_display.index[0])
    display_end_dt = pd.to_datetime(df_display.index[-1])
    time_span = display_end_dt - display_start_dt

    chart_left_edge_dt = display_start_dt

    if show_vpvr:
        right_gap = max(pd.Timedelta(days=12), time_span * 0.18)
        chart_right_edge_dt = display_end_dt + right_gap
    else:
        right_gap = pd.Timedelta(days=2)
        chart_right_edge_dt = display_end_dt + right_gap

    if show_vpvr:
        future_track_dates = pd.date_range(start=display_end_dt, end=chart_right_edge_dt, periods=25)
        fig.add_trace(go.Scatter(
            x=future_track_dates,
            y=[current_price] * len(future_track_dates),
            mode='lines',
            line=dict(color='rgba(0,0,0,0)', width=0),
            name='重貨區',
            hovertemplate='<b>%{x|%m-%d} 籌碼分佈區</b><extra></extra>',
            showlegend=False,
            yaxis='y1'
        ))

    if show_vpvr:
        dual_vpvr = compute_page1_dual_vpvr(df_clean, df_display, n_bins=40)
        render_page1_dual_vpvr(fig, dual_vpvr, chart_right_edge_dt, right_gap, main_cfg)

    # 主圖 K 線
    fig.add_trace(go.Candlestick(
        x=df_display.index,
        open=df_display['Open'], high=df_display['High'],
        low=df_display['Low'], close=df_display['Close'],
        name='K線圖', yaxis='y1'
    ))

    render_main_group1(fig, df_display, main_cfg)
    render_main_group2(fig, df_display, main_cfg)

    # 5. 繪製副圖
    day_ms = 86400000
    group2_set = {"spring", "vcp", "ttm", "macd"}
    macro_set = {"atr14", "fear_greed", "breadth50", "net_nhnl"}

    for i, k in enumerate(display_keys):
        y_num = i + 2
        y_ax = f"y{y_num}"
        dm = domains[y_num]
        if k in macro_set:
            render_macro_traces(fig, k, df_display, df_breadth, df_nhnl, ceil_net, y_ax, dm, y_num, y_axes_config, cur_sym, is_db_ready)
        elif k in group2_set:
            render_group2_traces(fig, k, df_display, y_ax, dm, y_num, y_axes_config)
        else:
            render_group1_traces(fig, k, df_display, y_ax, dm, benchmark_ticker, day_ms, y_num, y_axes_config)

    # 6. 全圖唯一 X 軸鎖定
    bottom_ax = f"y{num_subs + 1}" if num_subs > 0 else 'y1'
    y_axes_config['xaxis'] = dict(
        anchor=bottom_ax,
        range=[chart_left_edge_dt, chart_right_edge_dt],
        showgrid=True, gridcolor='#2e3d52',
        showspikes=True, spikemode='across', spikedash='dash',
        spikecolor='#a0aec0', spikethickness=1.2, spikesnap='cursor'
    )

    fig.update_layout(
        template='plotly_dark', paper_bgcolor='#0e1117', plot_bgcolor='#1f293d',
        xaxis_rangeslider_visible=False, barmode='overlay',
        margin=dict(l=35, r=60, t=10, b=30), height=chart_height,
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

    chart_col, diag_col = st.columns([3.1, 1.0])

    with chart_col:
        st.plotly_chart(
            fig,
            use_container_width=True,
            config={
                'displayModeBar': True,
                'scrollZoom': True,
                'displaylogo': False,
                'modeBarButtonsToRemove': ['lasso2d', 'select2d']
            }
        )

    with diag_col:
        diag_data = calculate_alpha_diagnostics(df_stock=df_clean, symbol=symbol, market_type=market_type)
        render_sidebar_diagnostics(diag_data)

    with st.expander("📚 點擊展開：5 大暗網韭菜/主力背離指標用法說明", expanded=False):
        st.markdown("""
        ### 🕵️‍♂️ 華爾街量化終端：散戶 vs 主力資金背離雷達
        這 5 個副圖不是傳統的滯後技術指標，而是透過 **「拆解訂單流、交易時段、市場結構」** 來透視背後莊家與散戶的真實博弈。

        ---

        ### 🧭【核心決策總部】五維共振 · 散戶套牢風險指數 (Smart/Dumb Spread)
        系統自動將下方 5 大暗網副圖的即時數值進行矩陣權重運算，提純為頂部的綜合決策看板：
- 🚨 **極度危險 (風險 ≥ 80% / 總分 ≤ -60)**：5 大維度出現嚴重共振套牢，主力全面出貨完畢，隨時引發踩踏暴跌。
- ⚠️ **警戒出貨 (風險 60% ~ 80% / 總分 -20 ~ -60)**：隔夜跳空或早盤出現誘多背馳，造市商暗池空頭對沖加劇。
- ⚪ **多空平衡 (風險 40% ~ 60% / 50% / 總分 -20 ~ +20)**：資金博弈溫和，處於洗盤整理區間，建議觀望為主。
- 🟢 **主力吸籌 (風險 20% ~ 40% / 總分 +20 ~ +60)**：散戶熱情消退，機構尾盤與低位暗中收集籌碼。
- 🚀 **黃金底背離 (風險 ≤ 20% / 總分 ≥ +60)**：散戶恐慌割肉完畢，主力極度強勢控盤，大級別反轉前夕。
        """)

    summary_text = "數據計算中..."
    try:
        ma20_val = df_clean['MA_3'].iloc[-1] if 'MA_3' in df_clean else df_clean['Close'].rolling(20).mean().iloc[-1]
        is_above_ma20 = current_price > ma20_val
        ma20_status = f"現價 {cur_sym}{current_price:,.2f} {'企穩於' if is_above_ma20 else '跌破'} MA20 ({cur_sym}{ma20_val:,.2f})"
        vas_price = df_clean['VAS'].iloc[-1] if 'VAS' in df_clean and not pd.isna(df_clean['VAS'].iloc[-1]) else 0
        vas_status = f"VAS 天量支撐線位於 {cur_sym}{vas_price:,.2f}" if vas_price > 0 else "目前無明顯 VAS 天量支撐記錄"
        latest_netvol = df_clean['NETVOL'].iloc[-1] if 'NETVOL' in df_clean else 0
        summary_text = f"【{symbol} 王者矩陣】：MA20: {ma20_status} | {vas_status} | 散戶套牢風險 {latest_trap_pct:.1f}% ({badge}) | 剪刀差總分 {latest_score:+.1f}"
    except Exception as e:
        summary_text = f"【{symbol} 王者矩陣】：計算發生錯誤 ({e})。"
    finally:
        st.session_state["data_page1"] = summary_text

# ===================================================
# 🚀 4. 頁面主入口函數
# ===================================================
def render_stock_tab(df, period, market_type, symbol):
    currency_symbols = {"美股": "$", "港股": "HK$", "日股": "¥", "韓股": "₩", "台股": "NT$", "A股": "¥", "加密貨幣": "$"}
    cur_sym = currency_symbols.get(market_type, "$")
    benchmark_ticker = "2800.HK" if market_type == "港股" else "SPY"

    # 控制工具列
    c_ctrl1, c_ctrl2 = st.columns([1.8, 3.2])
    with c_ctrl1:
        timeframe = st.radio("K 線級別", ["日線圖 (Daily)", "週線圖 (Weekly)"], horizontal=True, key="p1_kline_timeframe")
    with c_ctrl2:
        zoom_bars = st.slider("🔭 K 線縮放拉桿 (控制時間窗)", min_value=30, max_value=250, value=120, step=10, key="p1_kline_zoom")

    st.markdown("<div style='margin-bottom:12px;'></div>", unsafe_allow_html=True)

    # 側邊欄 Checkbox 圖層控制台
    main_cfg = {}
    with st.sidebar:
        st.markdown("---")
        st.markdown("### 📈 主圖指標與信號開關")

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

        with st.expander("2. ANCHORZONE 主力爆發", expanded=False):
            main_cfg["show_anchorzone"] = st.checkbox("啟用 ANCHORZONE (總開關)", value=True, key="p1_az_all")
            main_cfg["show_az_text"] = st.checkbox("顯示 'BIG' 標記文字", value=True, key="p1_az_txt")
            main_cfg["show_az_line"] = st.checkbox("顯示 K線底部防守實線", value=True, key="p1_az_line")

        with st.expander("3. S+++ VOLUMEANCHORSUPPORT", expanded=False):
            main_cfg["show_vas_main"] = st.checkbox("啟用 S+++ 終極防守 (總開關)", value=True, key="p1_vas_all")
            main_cfg["show_vas_line"] = st.checkbox("顯示 VAS 天量防守線 (紅線)", value=True, key="p1_vas_line")
            main_cfg["show_s_plus_buy"] = st.checkbox("顯示 🚀S+++ 突擊買入", value=True, key="p1_vas_buy")
            main_cfg["show_sell_trim"] = st.checkbox("顯示 ⚠️ 鎖利減倉提示", value=True, key="p1_vas_trim")
            main_cfg["show_sell_clear"] = st.checkbox("顯示 🛑 徹底清倉訊號", value=True, key="p1_vas_clear")

        with st.expander("4. GP_ALL_IN_ONE 終極合體", expanded=False):
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

        with st.expander("5. 📊 成交量分佈 (VPVR 重貨柱)", expanded=True):
            main_cfg["show_vpvr"] = st.checkbox("啟用 VPVR 重貨柱 (總開關)", value=True, key="p1_vpvr_all")
            main_cfg["show_recent_vpvr"] = st.checkbox("近期趨勢籌碼 (青藍/粉紅)", value=True, key="p1_vpvr_recent")
            main_cfg["show_hist_vpvr"] = st.checkbox("歷史全景籌碼 (黃褐/紫色)", value=True, key="p1_vpvr_hist")
            main_cfg["show_poc"] = st.checkbox("顯示 POC 核心籌碼密集線", value=True, key="p1_vpvr_poc")

        st.markdown("---")
        st.markdown("### 🎛️ 副圖 20 大指標開關")

        show_atr14 = st.checkbox("0a. ATR-14 (真實波幅與風控通道)", value=True, key="p1_chk_atr14")
        show_fear_greed = st.checkbox("0b. 恐慌貪婪指數 (±2SD 極值通道)", value=True, key="p1_chk_fear_greed")
        show_breadth50 = st.checkbox("0c. 納指全量市寬-50 (3,380 隻全景)", value=True, key="p1_chk_breadth50")
        show_net_nhnl = st.checkbox("0d. 納指 52 週淨新高/新低 (3,380 隻推進力)", value=True, key="p1_chk_net_nhnl")

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
    if show_atr14: active_indicators.append("atr14")
    if show_fear_greed: active_indicators.append("fear_greed")
    if show_breadth50: active_indicators.append("breadth50")
    if show_net_nhnl: active_indicators.append("net_nhnl")

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

    # 週線切換邏輯重採樣
    if "週線" in timeframe:
        df_weekly = df.resample('W').agg({
            'Open': 'first', 'High': 'max', 'Low': 'min', 'Close': 'last', 'Volume': 'sum'
        }).dropna(subset=['Close'])
        df_proc = df_weekly
    else:
        df_proc = df.copy()

    # 執行指標計算
    df_proc = compute_main_group1(df_proc)
    df_proc = compute_main_group2(df_proc)
    df_proc = compute_group1_indicators(df_proc, symbol, market_type, benchmark_ticker)
    df_proc = compute_group2_indicators(df_proc)
    df_proc['ATR_14'] = compute_atr14(df_proc, period=14)

    df_clean = df_proc.dropna(subset=['Close']).copy()
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

    if "週線" in timeframe:
        display_bars = min(len(df_clean), max(20, zoom_bars // 2))
    else:
        display_bars = min(len(df_clean), zoom_bars)

    df_display = df_clean.tail(display_bars).copy()

    # 直連本地真實 3,380 隻宏觀歷史資料庫
    df_breadth, df_nhnl, ceil_net, is_db_ready = load_real_nasdaq_3380_macro(df_display.index)

    draw_and_sync_page1(
        df_display, df_clean, current_price, delta_val, delta_percent,
        ma20_text, cur_sym, symbol, market_type, period, benchmark_ticker,
        active_indicators, main_cfg, df_breadth, df_nhnl, ceil_net, is_db_ready
    )