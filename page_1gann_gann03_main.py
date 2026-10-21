"""
Filename: page_1gann_gann03_main.py
Description: 📊 頁面 3：小龍量化四線體系 + ZL-MACD (STAGE 2 動態感應版)
升級亮點：
  1. 🌟 新增「成交量 (Volume)」副圖 (可獨立自由開關)
  2. 🌟 移植「Time Cycle (200 BARS 正弦波)」與「SL Angle (幾何動能)」(可獨立自由開關)
  3. 🌟 匯入「諧波時間弧、推算暗區與未來日期探針」(可獨立自由開關)
  4. 🌟 單一 X 軸貫通技術，十字標尺百分之百自天頂一穿到底
  5. 完備「基準週期 R 滑桿」與「🔄 回復預設配置」按鈕
"""

import streamlit as st
import pandas as pd
import numpy as np
import plotly.graph_objects as go
from plotly.subplots import SubplotRef
import importlib

# 引入 Gann 03 核心運算引擎
try:
    import page_1gann_gann03_calc as calc_engine
    importlib.reload(calc_engine)
except ImportError:
    calc_engine = None

# 🌟 引入 Time Cycle 與 SL Angle 計算引擎
try:
    import page_1gann_gann02_cycle_calc as cycle_engine
    importlib.reload(cycle_engine)
except ImportError:
    cycle_engine = None

# 🌟 引入籌碼計算 (用於 Time Cycle 籌碼防護盾狀態判定)
try:
    import page_1gann_gann02_extreme_calc as ext_engine
    importlib.reload(ext_engine)
except ImportError:
    ext_engine = None

# 🌟 引入【江恩諧波時間弧與未來推算通用部件】
try:
    import component_gann_harmonic_arcs as harmonic_comp
    importlib.reload(harmonic_comp)
except ImportError:
    harmonic_comp = None


def build_grid_ref(num_rows):
    """向 Plotly 註冊動態網格指針，確保多圖層相容且共用單一 X 軸"""
    grid = []
    for r in range(1, num_rows + 1):
        y_name = 'y' if r == 1 else f'y{r}'
        ref = SubplotRef(
            subplot_type='xy',
            layout_keys=('xaxis', f'yaxis{r}' if r > 1 else 'yaxis'),
            trace_kwargs={'xaxis': 'x', 'yaxis': y_name}
        )
        grid.append([(ref,)])
    return grid


def render_page_1gann_gann03_workspace(df: pd.DataFrame, symbol: str = "2330.TW"):
    if df is None or df.empty:
        st.warning("⚠️ 查無歷史 K 線數據。")
        return

    df_full = df.copy()
    df_full.index = pd.to_datetime(df_full.index).tz_localize(None)

    # 1. 視角切換控制
    c_scope, _ = st.columns([4.0, 6.0])
    with c_scope:
        view_scope = st.radio(
            "Gann03 顯示範圍",
            ["⚡ 近 6 個月", "📊 近 1 年 (推薦)", "🌐 4 年全景 (對齊 4Y 回歸)"],
            index=1,
            horizontal=True,
            label_visibility="collapsed",
            key="gann03_scope_select"
        )

    target_bars = 130 if "6 個月" in view_scope else (250 if "1 年" in view_scope else 1000)
    df_chart = df_full.tail(target_bars).copy()

    # 🎯 處理一鍵回復預設邏輯
    if st.session_state.get("trigger_reset_gann03", False):
        st.session_state["gann03_r_period"] = 47
        st.session_state["gann03_channel"] = True
        st.session_state["gann03_reg"] = False
        st.session_state["gann03_zl_macd"] = True
        st.session_state["gann03_vol"] = True
        st.session_state["gann03_cycle"] = True
        st.session_state["gann03_sl"] = True
        st.session_state["gann03_harmonic"] = True
        st.session_state["trigger_reset_gann03"] = False

    # 2. 控制面板 (清楚分類為 5 大欄位)
    with st.expander("⚙️ Gann 03 工作台控制面板 (四線通道、動能與時空幾何)", expanded=True):
        c_b1, c_b2, c_b3, c_b4, c_b5 = st.columns([2.0, 2.2, 2.2, 1.8, 2.2])
        with c_b1:
            show_channel = st.checkbox("✓ Eric's Channel (四線)", value=st.session_state.get("gann03_channel", True), key="gann03_channel")
            show_reg = st.checkbox("✓ Eric's Regression (4Y)", value=st.session_state.get("gann03_reg", False), key="gann03_reg")
        with c_b2:
            show_zl_macd = st.checkbox("✓ ZL-MACD (Stage 2)", value=st.session_state.get("gann03_zl_macd", True), key="gann03_zl_macd")
            show_volume = st.checkbox("📊 成交量 (Volume)", value=st.session_state.get("gann03_vol", True), key="gann03_vol")
        with c_b3:
            show_cycle = st.checkbox("✓ Time Cycle (正弦波)", value=st.session_state.get("gann03_cycle", True), key="gann03_cycle")
            show_sl_angle = st.checkbox("✓ SL Angle (動能角度)", value=st.session_state.get("gann03_sl", True), key="gann03_sl")
        with c_b4:
            show_harmonic = st.checkbox("⏳ 諧波時間弧 (未來推算)", value=st.session_state.get("gann03_harmonic", True), key="gann03_harmonic")
            if st.button("🔄 回復預設配置", key="btn_reset_defaults_gann03"):
                st.session_state["trigger_reset_gann03"] = True
                st.rerun()
        with c_b5:
            r_period = st.slider("基準週期 R (K線)", min_value=10, max_value=120, value=st.session_state.get("gann03_r_period", 47), step=1, key="gann03_r_period")

    # 3. 數據運算
    future_span_days = 85
    chart_start = df_chart.index[0]
    chart_end_base = df_chart.index[-1] + pd.Timedelta(days=future_span_days)

    channel_data = calc_engine.compute_erics_channel(df_chart) if (calc_engine and show_channel) else None
    reg_data = calc_engine.compute_4y_regression(df_full) if (calc_engine and show_reg) else None
    macd_data = calc_engine.compute_zl_macd(df_full, target_index=df_chart.index) if (calc_engine and show_zl_macd) else None

    # Time Cycle 與 SL Angle 計算
    cycle_data = None
    sl_data = None
    if cycle_engine is not None:
        if show_cycle and hasattr(cycle_engine, "compute_time_cycle"):
            cycle_data = cycle_engine.compute_time_cycle(df_chart, future_days=future_span_days)
        if show_sl_angle and hasattr(cycle_engine, "compute_sl_angle"):
            sl_data = cycle_engine.compute_sl_angle(df_chart)

    vpvr_data = None
    if ext_engine and hasattr(ext_engine, "compute_vpvr_and_poc"):
        vpvr_data = ext_engine.compute_vpvr_and_poc(df_chart)

    # 諧波時間弧運算
    harmonic_data = None
    if show_harmonic and harmonic_comp is not None and hasattr(harmonic_comp, "compute_harmonic_arcs_data"):
        try:
            harmonic_data = harmonic_comp.compute_harmonic_arcs_data(
                df=df_chart, r_period=r_period, manual_a1_date=None, manual_a2_date=None
            )
        except Exception as e:
            st.error(f"諧波時間弧運算錯誤: {e}")

    # 4. 頂部深黑戰術橫幅
    if channel_data:
        pct_defense = (channel_data['last_close'] - channel_data['last_mid']) / channel_data['last_mid'] * 100
        is_dormant = channel_data.get('is_dormant', False)
        regime_col = "#eab308" if is_dormant else "#38bdf8"
        regime_bg = "rgba(234, 179, 8, 0.15)" if is_dormant else "rgba(56, 189, 248, 0.12)"

        def_status = channel_data.get('defense_status', 'BULL_HEALTHY')
        if def_status == 'BULL_HEALTHY':
            def_col = "#22c55e"
            def_bg = "rgba(34, 197, 94, 0.15)"
        elif def_status == 'BENIGN_TEST':
            def_col = "#fbbf24"
            def_bg = "rgba(251, 191, 36, 0.15)"
        else:
            def_col = "#ef4444"
            def_bg = "rgba(239, 68, 68, 0.15)"

        buf_dn = channel_data.get('last_buf_down', channel_data['last_mid'] * 0.99)
        regime_badge = channel_data.get('regime_badge', '趨勢模式')
        defense_badge = channel_data.get('defense_badge', '防守狀態')
        defense_text = channel_data.get('defense_text', '戰術指引')

        banner_html = (
            f'<div style="background-color:#0d1117; border:1px solid #30363d; border-radius:6px; padding:8px 14px; margin-bottom:12px; font-family:sans-serif; font-size:12px;">'
            f'<div style="display:flex; justify-content:space-between; align-items:center; margin-bottom:6px; border-bottom:1px solid #21262d; padding-bottom:6px;">'
            f'<div>'
            f'<span style="font-weight:bold; color:#ffffff; margin-right:12px;">Eric\'s Quantitative 4-Line System</span>'
            f'<span style="color:#facc15; margin-right:12px;">● 上軌阻力 <b>${channel_data["last_upper"]:.2f}</b></span>'
            f'<span style="color:#00e676; margin-right:12px;">● 現價基準 <b>${channel_data["last_close"]:.2f}</b></span>'
            f'<span style="color:#ef4444; margin-right:12px;">● 紅色生命線 <b>${channel_data["last_mid"]:.2f}</b></span>'
            f'<span style="color:#84cc16;">● 下軌支撐 <b>${channel_data["last_lower"]:.2f}</b></span>'
            f'</div>'
            f'<div style="display:flex; align-items:center; gap:10px;">'
            f'<span style="color:#FF6600; font-size:11px;">● 橙色: Stage2主升</span>'
            f'<span style="color:#9900CC; font-size:11px;">● 紫色: 啟爆</span>'
            f'<span style="color:#0000FF; font-size:11px;">● 藍色: 洗盤</span>'
            f'<span style="color:#94a3b8; font-size:11px; margin-left:6px;">防守空間: <b style="color:{"#22c55e" if pct_defense >= 0 else "#ef4444"};">{pct_defense:+.2f}%</b></span>'
            f'</div>'
            f'</div>'
            f'<div style="display:flex; justify-content:space-between; align-items:center;">'
            f'<div>'
            f'<span style="background:{regime_bg}; color:{regime_col}; border:1px solid {regime_col}; padding:2px 6px; border-radius:4px; font-weight:bold; font-size:11px; margin-right:8px;">'
            f'{regime_badge}'
            f'</span>'
            f'<span style="background:{def_bg}; color:{def_col}; border:1px solid {def_col}; padding:2px 6px; border-radius:4px; font-weight:bold; font-size:11px; margin-right:8px;">'
            f'{defense_badge}'
            f'</span>'
            f'<span style="color:#cbd5e1; font-size:11px;">0.3×ATR緩衝帶: <b>${buf_dn:.2f}</b></span>'
            f'</div>'
            f'<div>'
            f'<span style="color:#fbbf24; font-size:11px;">戰術指引: <b>{defense_text}</b></span>'
            f'</div>'
            f'</div>'
            f'</div>'
        )
        st.markdown(banner_html, unsafe_allow_html=True)

    # ===================================================
    # 5. 🎯 動態 Y 軸佈局引擎 (Dynamic Subplot Mapper)
    # ===================================================
    layers = []
    if show_harmonic and harmonic_data:
        layers.append(('harmonic', 0.18))
    if show_zl_macd and macd_data:
        layers.append(('zl_macd', 0.13))
    if show_sl_angle and sl_data:
        layers.append(('sl_angle', 0.10))
    if show_cycle and cycle_data:
        layers.append(('cycle', 0.12))
    if show_volume:
        layers.append(('volume', 0.10))

    current_bottom = 0.0
    gap = 0.02
    y_axes_config = {}
    axes_map = {}
    y_idx = 2

    spike_common = dict(
        showspikes=True, spikemode='across+toaxis', spikesnap='cursor',
        spikedash='dash', spikecolor='rgba(255, 255, 255, 0.85)', spikethickness=1.2
    )

    for name, height in layers:
        domain = [round(current_bottom, 3), round(current_bottom + height, 3)]
        axes_map[name] = f"y{y_idx}"
        y_axes_config[f'yaxis{y_idx}'] = dict(
            domain=domain, anchor='x', side='right',
            showgrid=True, gridcolor='rgba(48, 54, 61, 0.35)', color='#8b949e', **spike_common
        )
        if name == 'cycle':
            y_axes_config[f'yaxis{y_idx}']['range'] = [-120, 120]
        elif name == 'sl_angle':
            y_axes_config[f'yaxis{y_idx}']['range'] = [-95, 95]
        elif name == 'harmonic':
            y_axes_config[f'yaxis{y_idx}']['range'] = [-5, 125]
            y_axes_config[f'yaxis{y_idx}']['gridcolor'] = 'rgba(48, 54, 61, 0.25)'

        current_bottom += height + gap
        y_idx += 1

    price_domain = [round(current_bottom, 3), 1.0]
    axes_map['price'] = 'y'
    y_axes_config['yaxis'] = dict(
        domain=price_domain, anchor='x', side='right',
        showgrid=True, gridcolor='rgba(48, 54, 61, 0.35)', color='#8b949e', **spike_common
    )

    bottom_ax = axes_map[layers[0][0]] if layers else 'y'
    chart_end_final = harmonic_data['chart_end_date'] if (show_harmonic and harmonic_data) else chart_end_base

    y_axes_config['xaxis'] = dict(
        anchor=bottom_ax,
        range=[chart_start, chart_end_final],
        showgrid=True, gridcolor='rgba(48, 54, 61, 0.35)', color='#8b949e',
        rangeslider=dict(visible=False), **spike_common
    )

    total_rows = 1 + len(layers)
    chart_total_height = max(750, 520 + len(layers) * 115)
    fig = go.Figure()
    fig._grid_ref = build_grid_ref(total_rows)

    # ==========================================
    # --- 圖層 1: K 線主圖 + Eric 四線 + 回歸 ---
    # ==========================================
    fig.add_trace(go.Candlestick(
        x=df_chart.index,
        open=df_chart['Open'], high=df_chart['High'], low=df_chart['Low'], close=df_chart['Close'],
        name=f'{symbol} K線',
        increasing_line_color='#00e676', decreasing_line_color='#ff5252',
        increasing_fillcolor='#00e676', decreasing_fillcolor='#ff5252',
        yaxis=axes_map['price'], showlegend=False
    ), row=1, col=1)

    # --- 渲染 Eric's Channel 三線通道 + 0.3×ATR 緩衝帶 + 4 條核心基準橫線 ---
    if channel_data:
        # 1. 0.3×ATR 生命線緩衝防禦雲帶
        if 'mid_buffer_upper' in channel_data and 'mid_buffer_lower' in channel_data:
            fig.add_trace(go.Scatter(
                x=df_chart.index, y=channel_data['mid_buffer_upper'],
                mode='lines', line=dict(color='rgba(239, 68, 68, 0.25)', width=1.0, dash='dot'),
                name='Buffer Upper', yaxis=axes_map['price'], showlegend=False, hoverinfo='skip'
            ))
            fig.add_trace(go.Scatter(
                x=df_chart.index, y=channel_data['mid_buffer_lower'],
                mode='lines', line=dict(color='rgba(239, 68, 68, 0.25)', width=1.0, dash='dot'),
                fill='tonexty', fillcolor='rgba(239, 68, 68, 0.08)',
                name='0.3x ATR 緩衝防禦帶', yaxis=axes_map['price'], showlegend=False, hoverinfo='skip'
            ))

        # 2. Eric's Channel 三線通道
        fig.add_trace(go.Scatter(
            x=df_chart.index, y=channel_data['upper'],
            mode='lines', line=dict(color='#eab308', width=2.0),
            name='Upper Band', yaxis=axes_map['price'], showlegend=False
        ))
        fig.add_trace(go.Scatter(
            x=df_chart.index, y=channel_data['mid'],
            mode='lines', line=dict(color='#ef4444', width=2.4),
            name='Life Line', yaxis=axes_map['price'], showlegend=False
        ))
        fig.add_trace(go.Scatter(
            x=df_chart.index, y=channel_data['lower'],
            mode='lines', line=dict(color='#84cc16', width=2.0),
            name='Lower Band', yaxis=axes_map['price'], showlegend=False
        ))

        four_lines_config = [
            {'price': channel_data['last_upper'], 'color': 'rgba(234, 179, 8, 0.55)', 'dash': 'dot'},
            {'price': channel_data['last_close'], 'color': 'rgba(0, 230, 118, 0.85)', 'dash': 'dash'},
            {'price': channel_data['last_mid'],   'color': 'rgba(239, 68, 68, 0.65)', 'dash': 'dot'},
            {'price': channel_data['last_lower'], 'color': 'rgba(132, 204, 22, 0.55)', 'dash': 'dot'}
        ]

        for item in four_lines_config:
            fig.add_shape(
                type="line", xref="paper", yref=axes_map['price'],
                x0=0, x1=1,
                y0=item['price'], y1=item['price'],
                line=dict(color=item['color'], width=1.3, dash=item['dash'])
            )

        # 4 大膠囊標籤
        fig.add_annotation(
            xref="x domain", yref=axes_map['price'],
            x=0.998, y=channel_data['last_upper'],
            text=f"<b>{channel_data['last_upper']:.2f}</b>",
            bgcolor="#854d0e", bordercolor="#facc15", borderpad=3,
            font=dict(color="#fef08a", size=10, family="monospace"),
            showarrow=False, xanchor="right", yanchor="middle"
        )
        fig.add_annotation(
            xref="x domain", yref=axes_map['price'],
            x=0.998, y=channel_data['last_close'],
            text=f"<b>{channel_data['last_close']:.2f}</b>",
            bgcolor="#065f46", bordercolor="#00e676", borderpad=3,
            font=dict(color="#a7f3d0", size=10, family="monospace"),
            showarrow=False, xanchor="right", yanchor="middle"
        )
        fig.add_annotation(
            xref="x domain", yref=axes_map['price'],
            x=0.998, y=channel_data['last_mid'],
            text=f"<span style='background:#b91c1c; padding:2px 6px; border-radius:3px; color:#ffffff;'>Eric's Channel</span> <b style='color:#ffffff;'>{channel_data['last_mid']:.2f}</b>",
            bgcolor="#991b1b", bordercolor="#ef4444", borderpad=3,
            font=dict(color="#ffffff", size=10, family="monospace"),
            showarrow=False, xanchor="right", yanchor="middle"
        )
        fig.add_annotation(
            xref="x domain", yref=axes_map['price'],
            x=0.998, y=channel_data['last_lower'],
            text=f"<b>{channel_data['last_lower']:.2f}</b>",
            bgcolor="#365314", bordercolor="#84cc16", borderpad=3,
            font=dict(color="#bef264", size=10, family="monospace"),
            showarrow=False, xanchor="right", yanchor="middle"
        )

    # --- 渲染 Eric's Regression (4Y) ---
    if reg_data:
        r_dates = reg_data['dates'].intersection(df_chart.index)
        if len(r_dates) > 0:
            fig.add_trace(go.Scatter(
                x=r_dates, y=reg_data['reg_center'].loc[r_dates],
                mode='lines', line=dict(color='rgba(255, 255, 255, 0.7)', width=1.5, dash='dash'),
                name='4Y Reg Center', yaxis=axes_map['price'], showlegend=False
            ))
            fig.add_trace(go.Scatter(
                x=r_dates, y=reg_data['upper_2std'].loc[r_dates],
                mode='lines', line=dict(color='rgba(168, 85, 247, 0.75)', width=1.2, dash='dot'),
                name='4Y Reg +2σ', yaxis=axes_map['price'], showlegend=False
            ))
            fig.add_trace(go.Scatter(
                x=r_dates, y=reg_data['lower_2std'].loc[r_dates],
                mode='lines', line=dict(color='rgba(168, 85, 247, 0.75)', width=1.2, dash='dot'),
                name='4Y Reg -2σ', yaxis=axes_map['price'], showlegend=False
            ))

    # 🎯 🌟 注入主圖右側推算暗區與時空探針 (Future Projection Zone)
    if show_harmonic and harmonic_data and harmonic_comp:
        harmonic_comp.inject_future_projection_zone(fig, harmonic_data, yaxis_name=axes_map['price'])

    # ==========================================
    # --- 圖層 2: 📊 成交量 (Volume) ---
    # ==========================================
    if show_volume:
        vol_colors = ['#00e676' if c >= o else '#ff5252' for c, o in zip(df_chart['Close'], df_chart['Open'])]
        fig.add_trace(go.Bar(
            x=df_chart.index, y=df_chart['Volume'],
            marker_color=vol_colors, name='成交量',
            showlegend=False, opacity=0.75, yaxis=axes_map['volume']
        ))

    # ==========================================
    # --- 圖層 3: TIME CYCLE (藍/黃正弦波) ---
    # ==========================================
    if show_cycle and cycle_data:
        c_yax = axes_map['cycle']
        fig.add_trace(go.Scatter(x=cycle_data['interp_dates'], y=cycle_data['pos_cycle'], mode='lines', line=dict(color='#38bdf8', width=2.4), name='Cycle Peak Phase', yaxis=c_yax, showlegend=False))
        fig.add_trace(go.Scatter(x=cycle_data['interp_dates'], y=cycle_data['neg_cycle'], mode='lines', line=dict(color='#facc15', width=2.4), name='Cycle Trough Phase', yaxis=c_yax, showlegend=False))

        for y_r, c_r, d_r in [(100, "rgba(244, 63, 94, 0.4)", "dash"), (0, "rgba(148, 163, 184, 0.3)", "solid"), (-100, "rgba(250, 204, 21, 0.4)", "dash")]:
            fig.add_shape(type="line", xref="paper", yref=c_yax, x0=0, x1=1, y0=y_r, y1=y_r, line=dict(color=c_r, width=1, dash=d_r))

        for pk_date, pk_val in cycle_data['peaks']:
            fig.add_trace(go.Scatter(x=[pk_date], y=[pk_val], mode='markers', marker=dict(color='#38bdf8', size=7, line=dict(color='#ffffff', width=1.5)), yaxis=c_yax, showlegend=False, hoverinfo='skip'))
            fig.add_annotation(x=pk_date, y=pk_val, xref="x", yref=c_yax, text="<b>PEAK</b>", font=dict(color="#38bdf8", size=9, family="Arial Black"), showarrow=False, yshift=14, xanchor="center")

        for tg_date, tg_val in cycle_data['troughs']:
            fig.add_trace(go.Scatter(x=[tg_date], y=[tg_val], mode='markers', marker=dict(color='#facc15', size=7, line=dict(color='#ffffff', width=1.5)), yaxis=c_yax, showlegend=False, hoverinfo='skip'))
            fig.add_annotation(x=tg_date, y=tg_val, xref="x", yref=c_yax, text="<b>TROUGH</b>", bgcolor="#78350f", bordercolor="#f59e0b", borderwidth=1, borderpad=2, font=dict(color="#fde68a", size=9, family="Arial Black"), showarrow=False, yshift=-16, xanchor="center")

        fig.add_annotation(xref="x domain", yref=c_yax, x=0.995, y=100, text="<b>PEAK ZONE</b>", bgcolor="#0284c7", font=dict(color="#ffffff", size=9), showarrow=False, xanchor="right")
        fig.add_annotation(xref="x domain", yref=c_yax, x=0.995, y=0, text="<b>MID</b>", bgcolor="#334155", font=dict(color="#ffffff", size=9), showarrow=False, xanchor="right")
        fig.add_annotation(xref="x domain", yref=c_yax, x=0.995, y=-100, text="<b>TROUGH ZONE</b>", bgcolor="#b45309", font=dict(color="#ffffff", size=9), showarrow=False, xanchor="right")

        chip_guard_html = ""
        if vpvr_data:
            if vpvr_data.get('is_lvn'):
                chip_guard_html = "  |  <span style='background:#7f1d1d; color:#fca5a5; border:1px solid #ef4444; padding:1px 6px; border-radius:3px;'><b>⚠️ 籌碼真空加速區：防週期鈍化</b></span>"
            elif vpvr_data.get('near_poc') or vpvr_data.get('is_hvn'):
                chip_guard_html = f"  |  <span style='background:#14532d; color:#86efac; border:1px solid #22c55e; padding:1px 6px; border-radius:3px;'><b>🛡️ POC籌碼重兵區 (${vpvr_data.get('poc_price', 0):.2f})：時空共振變盤</b></span>"
            elif vpvr_data.get('is_in_value_area'):
                chip_guard_html = "  |  <span style='background:#0f3854; color:#7dd3fc; border:1px solid #38bdf8; padding:1px 6px; border-radius:3px;'><b>⚖️ 70%價值區內：平衡震盪週期勝率 >85%</b></span>"
            else:
                chip_guard_html = "  |  <span style='background:#3b1e54; color:#f0abfc; border:1px solid #c084fc; padding:1px 6px; border-radius:3px;'><b>⚡ 突破價值區：單邊趨勢失衡</b></span>"

        hud_cycle = f"<b>TIME CYCLE</b>  200 BARS  |  <span style='background:#78350f; color:#fde68a; padding:1px 4px;'><b>{cycle_data['window_status']}</b></span>  |  相位 {cycle_data['current_phase_deg']}°  |  距轉折 {cycle_data['next_turn_bars']}B{chip_guard_html}"
        fig.add_annotation(xref="paper", yref=f"{c_yax} domain", x=0.015, y=0.92, text=hud_cycle, bgcolor="rgba(15, 23, 42, 0.85)", bordercolor="#38bdf8", borderwidth=1, borderpad=4, font=dict(color="#ffffff", size=10, family="monospace"), showarrow=False, xanchor="left")

    # ==========================================
    # --- 圖層 4: SL ANGLE (幾何動能線) ---
    # ==========================================
    if show_sl_angle and sl_data:
        sl_y = axes_map['sl_angle']
        fig.add_trace(go.Scatter(x=sl_data['interp_dates'], y=sl_data['pos_angles'], mode='lines', line=dict(color='#22c55e', width=2.0), name='SL Angle Bullish', yaxis=sl_y, showlegend=False))
        fig.add_trace(go.Scatter(x=sl_data['interp_dates'], y=sl_data['neg_angles'], mode='lines', line=dict(color='#f43f5e', width=2.0), name='SL Angle Bearish', yaxis=sl_y, showlegend=False))
        fig.add_shape(type="line", xref="paper", yref=sl_y, x0=0, x1=1, y0=0, y1=0, line=dict(color="rgba(148, 163, 184, 0.4)", width=1, dash="dot"))

        last_a = sl_data['last_angle']
        bg_a = "#16a34a" if last_a >= 0 else "#e11d48"
        fig.add_annotation(xref="x domain", yref=sl_y, x=0.995, y=last_a, text=f"<b>SL Angle {last_a:+.1f}°</b>", bgcolor=bg_a, bordercolor=bg_a, borderpad=3, font=dict(color="#ffffff", size=9, family="monospace"), showarrow=False, xanchor="right")
        fig.add_annotation(xref="paper", yref=f"{sl_y} domain", x=0.015, y=0.90, text="<b>SL ANGLE — 幾何動能角度</b>", bgcolor="rgba(15, 23, 42, 0.85)", font=dict(color="#94a3b8", size=10), showarrow=False, xanchor="left")

    # ==========================================
    # --- 圖層 5: 🚀 ZL-MACD (STAGE 2 動態感應版) ---
    # ==========================================
    if show_zl_macd and macd_data:
        macd_yax = axes_map['zl_macd']
        # 1. 直方圖
        fig.add_trace(go.Bar(
            x=df_chart.index, y=macd_data['hist'],
            marker_color=macd_data['color'], name='ZL-Hist (Stage2)',
            yaxis=macd_yax, showlegend=False
        ))
        # 2. 快線 DIF
        fig.add_trace(go.Scatter(
            x=df_chart.index, y=macd_data['diff'],
            mode='lines', line=dict(color='#FF8D1E', width=2.0),
            name='ZL-DIF', yaxis=macd_yax, showlegend=False
        ))
        # 3. 慢線 DEA
        fig.add_trace(go.Scatter(
            x=df_chart.index, y=macd_data['dea'],
            mode='lines', line=dict(color='#0CAEE6', width=2.0),
            name='ZL-DEA', yaxis=macd_yax, showlegend=False
        ))
        # 4. 平水零軸線
        fig.add_shape(
            type="line", xref="paper", yref=macd_yax,
            x0=0, x1=1, y0=0, y1=0,
            line=dict(color="#ffffff", width=1.2)
        )
        # 5. 水上金叉標記
        gold_dates = df_chart.index[macd_data['cross_gold']]
        if len(gold_dates) > 0:
            fig.add_trace(go.Scatter(
                x=gold_dates, y=macd_data['diff'].loc[gold_dates] * 0.95,
                mode='markers', marker=dict(symbol='triangle-up', color='red', size=8),
                name='水上金叉', showlegend=False, yaxis=macd_yax
            ))
        fig.add_annotation(
            xref="paper", yref=f"{macd_yax} domain",
            x=0.015, y=0.90, text="<b>ZL-MACD (12, 26, 9) — STAGE 2 動態感應版 (死區防噪)</b>",
            bgcolor="rgba(15, 23, 42, 0.85)", font=dict(color="#FF8D1E", size=10, family="monospace"),
            showarrow=False, xanchor="left"
        )

    # ==========================================
    # --- 圖層 6: ⏳ 諧波時間跳躍弧 (Harmonic Arcs) ---
    # ==========================================
    if show_harmonic and harmonic_data and harmonic_comp:
        harmonic_comp.inject_harmonic_arcs_traces(fig, harmonic_data, yaxis_name=axes_map['harmonic'])

    # ===================================================
    # 6. 整合佈局 (十字線 across+toaxis 全軸貫通)
    # ===================================================
    fig.update_layout(
        template='plotly_dark',
        paper_bgcolor='#0a0e14',
        plot_bgcolor='#0a0e14',
        xaxis_rangeslider_visible=False,
        hovermode='x',
        hoverlabel=dict(bgcolor='#1f293d', font_size=12, font_family='Arial'),
        height=chart_total_height,
        margin=dict(l=10, r=45, t=10, b=25),
        newshape=dict(line=dict(color="#facc15", width=1.5, dash="dash")),
        **y_axes_config
    )

    st.plotly_chart(
        fig,
        use_container_width=True,
        config={
            'displayModeBar': True,
            'scrollZoom': True,
            'displaylogo': False,
            'modeBarButtonsToAdd': ['drawline', 'eraseshape']
        }
    )

    # 🎯 渲染底部未來倒數矩陣看板
    if show_harmonic and harmonic_data and harmonic_comp and hasattr(harmonic_comp, "render_harmonic_countdown_matrix_ui"):
        harmonic_comp.render_harmonic_countdown_matrix_ui(harmonic_data)