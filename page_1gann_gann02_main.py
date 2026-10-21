"""
Filename: page_1gann_gann02_main.py
Description: 📊 頁面 2：江恩自然極限與動能通道工作台
升級亮點：
  1. 🌟 新增「成交量 (Volume)」圖層
  2. 🌟 全面匯入「江恩諧波時間弧與未來推算部件」
  3. 🌟 實裝單一 X 軸貫通技術 (十字標尺直穿到底 + 點擊未來日期探針)
  4. 完美解析渲染「時空籌碼多維共振雷達」與 VPVR
"""

import streamlit as st
import pandas as pd
import numpy as np
import plotly.graph_objects as go
import importlib

try:
    import page_1gann_gann02_extreme_calc as ext_engine
    importlib.reload(ext_engine)
except ImportError:
    ext_engine = None

try:
    import page_1gann_gann02_cycle_calc as cycle_engine
    importlib.reload(cycle_engine)
except ImportError:
    cycle_engine = None

# 🌟 引入【江恩諧波時間弧與未來推算通用部件】
try:
    import component_gann_harmonic_arcs as harmonic_comp
    importlib.reload(harmonic_comp)
except ImportError:
    harmonic_comp = None


def render_page_1gann_gann02_workspace(df: pd.DataFrame, symbol: str = "2330.TW"):
    if df is None or df.empty:
        st.warning("⚠️ 查無歷史 K 線數據。")
        return

    df_full = df.copy()
    df_full.index = pd.to_datetime(df_full.index).tz_localize(None)

    # 1. 視角範圍控制
    c_scope, _ = st.columns([4.0, 6.0])
    with c_scope:
        view_scope = st.radio(
            "Gann02 顯示範圍",
            ["⚡ 近 3 個月 (特寫放大)", "📊 近 6 個月 (原版推薦)", "🌐 1 年全景"],
            index=1,
            horizontal=True,
            label_visibility="collapsed",
            key="gann02_scope_select"
        )

    target_bars = 65 if "3 個月" in view_scope else (130 if "6 個月" in view_scope else 250)
    df_chart = df_full.tail(target_bars).copy()

    # 🎯 處理一鍵回復預設邏輯
    if st.session_state.get("trigger_reset_gann02", False):
        st.session_state["gann02_r_period"] = 47
        st.session_state["gann02_ma50"] = False
        st.session_state["gann02_ma200"] = False
        st.session_state["gann02_vqc"] = True
        st.session_state["gann02_solar"] = True
        st.session_state["gann02_vpvr"] = True
        st.session_state["gann02_vol"] = True
        st.session_state["gann02_cycle"] = True
        st.session_state["gann02_ext"] = True
        st.session_state["gann02_sl"] = True
        st.session_state["gann02_harmonic"] = True
        st.session_state["trigger_reset_gann02"] = False

    # 2. 指標控制列 (新增 Volume、Harmonic 勾選框與 R滑桿)
    with st.expander("⚙️ Gann 02 工作台控制面板 (指標、籌碼與時空參數)", expanded=True):
        c_b1, c_b2, c_b3, c_b4, c_b5, c_b6, c_b7 = st.columns([1.2, 1.2, 1.5, 2.0, 1.5, 1.8, 1.8])
        with c_b1:
            show_ma50 = st.checkbox("+ MA50", value=st.session_state.get("gann02_ma50", False), key="gann02_ma50")
            show_ma200 = st.checkbox("+ MA200", value=st.session_state.get("gann02_ma200", False), key="gann02_ma200")
        with c_b2:
            show_vqc = st.checkbox("✓ VQC (紫色)", value=st.session_state.get("gann02_vqc", True), key="gann02_vqc")
            show_solar = st.checkbox("✓ 24節氣", value=st.session_state.get("gann02_solar", True), key="gann02_solar")
        with c_b3:
            show_vpvr = st.checkbox("✓ VPVR 籌碼", value=st.session_state.get("gann02_vpvr", True), key="gann02_vpvr")
            show_extreme = st.checkbox("✓ Natural Ext", value=st.session_state.get("gann02_ext", True), key="gann02_ext")
        with c_b4:
            show_volume = st.checkbox("📊 成交量 (Volume)", value=st.session_state.get("gann02_vol", True), key="gann02_vol")
            show_harmonic = st.checkbox("⏳ 諧波時間弧 (未來推算)", value=st.session_state.get("gann02_harmonic", True), key="gann02_harmonic")
        with c_b5:
            show_cycle = st.checkbox("✓ Time Cycle", value=st.session_state.get("gann02_cycle", True), key="gann02_cycle")
            show_sl_angle = st.checkbox("✓ SL Angle 動能", value=st.session_state.get("gann02_sl", True), key="gann02_sl")
        with c_b6:
            st.write("")
            if st.button("🔄 回復預設配置", key="btn_reset_defaults_gann02"):
                st.session_state["trigger_reset_gann02"] = True
                st.rerun()
        with c_b7:
            r_period = st.slider("基準週期 R (K線)", min_value=10, max_value=120, value=st.session_state.get("gann02_r_period", 47), step=1, key="gann02_r_period")

    # 3. 核心數據運算 (Gann 02 原有數據)
    future_span_days = 85
    chart_start = df_chart.index[0]
    chart_end_base = df_chart.index[-1] + pd.Timedelta(days=future_span_days)

    ext_data = ext_engine.compute_gann_natural_extreme(df_chart) if ext_engine else None
    vpvr_data = ext_engine.compute_vpvr_and_poc(df_chart) if (ext_engine and show_vpvr) else None
    vqc_signals = ext_engine.compute_vqc_signals(df_chart, ext_data) if (ext_engine and show_vqc and ext_data) else []

    solar_terms = []
    if ext_engine and show_solar:
        solar_terms = ext_engine.compute_solar_terms_signals(
            chart_start, chart_end_base, trading_dates=df_chart.index
        )

    cycle_data = cycle_engine.compute_time_cycle(df_chart, future_days=future_span_days) if cycle_engine else None
    sl_data = cycle_engine.compute_sl_angle(df_chart) if cycle_engine else None

    # 🎯 運算「諧波時間弧與未來倒數」
    harmonic_data = None
    if show_harmonic and harmonic_comp is not None and hasattr(harmonic_comp, "compute_harmonic_arcs_data"):
        try:
            harmonic_data = harmonic_comp.compute_harmonic_arcs_data(
                df=df_chart, r_period=r_period, manual_a1_date=None, manual_a2_date=None
            )
        except Exception as e:
            st.error(f"諧波時間弧運算錯誤: {e}")

    # 🎯 運算「時空籌碼多維共振雷達」評分
    last_close_val = float(df_chart['Close'].iloc[-1])
    confluence_data = None
    if ext_engine and hasattr(ext_engine, "compute_confluence_score"):
        confluence_data = ext_engine.compute_confluence_score(
            last_close=last_close_val,
            ext_data=ext_data,
            vpvr_data=vpvr_data,
            cycle_data=cycle_data,
            solar_terms=solar_terms,
            last_date=df_chart.index[-1]
        )

    # 4. 頂部深黑戰術橫幅
    if ext_data:
        confluence_html = ""
        if confluence_data:
            checks_str = " + ".join(confluence_data['checks']) if confluence_data['checks'] else "未觸發密集條件"
            confluence_html = (
                f'<div style="display:flex; justify-content:space-between; align-items:center; margin-top:6px; border-top:1px solid #21262d; padding-top:6px;">'
                f'<div>'
                f'<span style="color:#94a3b8; font-weight:bold; margin-right:8px;">🎯 時空籌碼多維共振雷達:</span>'
                f'<span style="background:rgba(244,63,94,0.15); color:{confluence_data["color"]}; border:1px solid {confluence_data["color"]}; padding:1px 6px; border-radius:3px; font-weight:bold; font-size:11px; margin-right:8px;">'
                f'{confluence_data["level_tag"]} ({confluence_data["score"]}/4 命中)'
                f'</span>'
                f'<span style="color:#cbd5e1; font-size:11px;">[{checks_str}]</span>'
                f'</div>'
                f'<div>'
                f'<span style="color:#fbbf24; font-size:11px;">戰術指引: <b>{confluence_data["advice"]}</b></span>'
                f'</div>'
                f'</div>'
            )

        banner_html = (
            f'<div style="background-color:#0d1117; border:1px solid #30363d; border-radius:6px; padding:8px 14px; margin-bottom:12px; font-family:sans-serif; font-size:12px;">'
            f'<div style="display:flex; justify-content:space-between; align-items:center;">'
            f'<div>'
            f'<span style="font-weight:bold; color:#ffffff; margin-right:12px;">Gann Natural Extreme</span>'
            f'<span style="color:#f43f5e; margin-right:10px;">● 極上 <b>{ext_data["last_ext_p"]:.2f}</b></span>'
            f'<span style="color:#38bdf8; margin-right:10px;">● 極下 <b>{ext_data["last_ext_m"]:.2f}</b></span>'
            f'<span style="color:#fb923c; margin-right:10px;">● 近上 <b>{ext_data["last_near_p"]:.2f}</b></span>'
            f'<span style="color:#4ade80; margin-right:10px;">● 近下 <b>{ext_data["last_near_m"]:.2f}</b></span>'
            f'</div>'
            f'<div style="display:flex; align-items:center; gap:10px;">'
            f'<span style="color:#fca5a5; font-size:11px;">🔴 <b>四立轉折 (最高階)</b></span>'
            f'<span style="color:#93c5fd; font-size:11px;">🔵 <b>二十四節氣</b></span>'
            f'<span style="color:#c7d2fe; font-size:11px;">🟣 <b>VQC共振</b></span>'
            f'<span style="color:#94a3b8; margin-left:8px;">現價: <b style="color:#ffffff;">${ext_data["last_close"]:.2f}</b></span>'
            f'</div>'
            f'</div>'
            f'{confluence_html}'
            f'</div>'
        )
        st.markdown(banner_html, unsafe_allow_html=True)

    # ===================================================
    # 5. 🎯 動態 Y 軸佈局引擎 (Dynamic Subplot Mapper)
    # ===================================================
    layers = []
    if show_harmonic and harmonic_data:
        layers.append(('harmonic', 0.20))
    if show_sl_angle and sl_data:
        layers.append(('sl_angle', 0.12))
    if show_cycle and cycle_data:
        layers.append(('cycle', 0.14))
    if show_volume:
        layers.append(('volume', 0.12))

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

    chart_total_height = 650 + len(layers) * 110
    fig = go.Figure()

    # ==========================================
    # --- 圖層 1: K線、Gann 4 軌、VPVR (VAH/VAL)、VQC 與節氣 ---
    # ==========================================
    fig.add_trace(go.Candlestick(
        x=df_chart.index,
        open=df_chart['Open'], high=df_chart['High'], low=df_chart['Low'], close=df_chart['Close'],
        name=f'{symbol} K線',
        increasing_line_color='#00e676', decreasing_line_color='#ff5252',
        increasing_fillcolor='#00e676', decreasing_fillcolor='#ff5252',
        yaxis=axes_map['price'], showlegend=False
    ))

    if show_ma50 and len(df_chart) >= 50:
        ma50 = df_chart['Close'].rolling(50).mean()
        fig.add_trace(go.Scatter(x=df_chart.index, y=ma50, mode='lines', line=dict(color='#38bdf8', width=1.2), name='MA50', yaxis=axes_map['price'], showlegend=False))
    if show_ma200 and len(df_chart) >= 200:
        ma200 = df_chart['Close'].rolling(200).mean()
        fig.add_trace(go.Scatter(x=df_chart.index, y=ma200, mode='lines', line=dict(color='#eab308', width=1.5), name='MA200', yaxis=axes_map['price'], showlegend=False))

    # Gann 4 軌極限通道
    if show_extreme and ext_data:
        fig.add_trace(go.Scatter(x=df_chart.index, y=ext_data['ext_plus'], mode='lines', line=dict(color='#f43f5e', width=1.5), yaxis=axes_map['price'], showlegend=False, hoverinfo='skip'))
        fig.add_trace(go.Scatter(x=df_chart.index, y=ext_data['near_plus'], mode='lines', line=dict(color='#fb923c', width=1.2), fill='tonexty', fillcolor='rgba(244, 63, 94, 0.12)', yaxis=axes_map['price'], showlegend=False, hoverinfo='skip'))
        fig.add_trace(go.Scatter(x=df_chart.index, y=ext_data['near_minus'], mode='lines', line=dict(color='#4ade80', width=1.2), yaxis=axes_map['price'], showlegend=False, hoverinfo='skip'))
        fig.add_trace(go.Scatter(x=df_chart.index, y=ext_data['ext_minus'], mode='lines', line=dict(color='#0284c7', width=1.5), fill='tonexty', fillcolor='rgba(2, 132, 199, 0.15)', yaxis=axes_map['price'], showlegend=False, hoverinfo='skip'))

        touch_np = df_chart.index[ext_data['touch_near_p']]
        if len(touch_np) > 0:
            fig.add_trace(go.Scatter(x=touch_np, y=ext_data['near_plus'].loc[touch_np], mode='markers', marker=dict(color='#fb923c', size=6), yaxis=axes_map['price'], showlegend=False, hoverinfo='skip'))
        touch_nm = df_chart.index[ext_data['touch_near_m']]
        if len(touch_nm) > 0:
            fig.add_trace(go.Scatter(x=touch_nm, y=ext_data['near_minus'].loc[touch_nm], mode='markers', marker=dict(color='#38bdf8', size=6), yaxis=axes_map['price'], showlegend=False, hoverinfo='skip'))

        rail_capsules = [
            {'label': f"Gann Ext+  {ext_data['last_ext_p']:.2f}", 'p': ext_data['last_ext_p'], 'bg': '#e11d48'},
            {'label': f"Gann Near+ {ext_data['last_near_p']:.2f}", 'p': ext_data['last_near_p'], 'bg': '#ea580c'},
            {'label': f"Gann Near- {ext_data['last_near_m']:.2f}", 'p': ext_data['last_near_m'], 'bg': '#16a34a'},
            {'label': f"Gann Ext-  {ext_data['last_ext_m']:.2f}", 'p': ext_data['last_ext_m'], 'bg': '#0284c7'}
        ]
        for cap in rail_capsules:
            fig.add_annotation(
                xref="x domain", yref=axes_map['price'],
                x=0.998, y=cap['p'], text=f"<b>{cap['label']}</b>",
                bgcolor=cap['bg'], bordercolor=cap['bg'], borderpad=3,
                font=dict(color="#ffffff", size=10, family="monospace"),
                showarrow=False, xanchor="right", yanchor="middle"
            )

    # 🛡️ VPVR 籌碼分佈：POC 控制線 + 70% 價值區間 (VAH / VAL) 渲染
    if show_vpvr and vpvr_data:
        poc_p = vpvr_data['poc_price']
        vah_p = vpvr_data.get('vah_price', poc_p)
        val_p = vpvr_data.get('val_price', poc_p)

        fig.add_shape(type="line", xref="x", yref=axes_map['price'], x0=chart_start, x1=chart_end_base, y0=poc_p, y1=poc_p, line=dict(color="#facc15", width=1.5, dash="dot"))
        fig.add_annotation(xref="x domain", yref=axes_map['price'], x=0.92, y=poc_p, text=f"<b>POC {poc_p:.2f}</b>", bgcolor="#854d0e", bordercolor="#facc15", borderwidth=1, borderpad=3, font=dict(color="#fef08a", size=10, family="monospace"), showarrow=False, xanchor="right", yanchor="middle")
        fig.add_shape(type="line", xref="paper", yref=axes_map['price'], x0=0.88, x1=1.0, y0=vah_p, y1=vah_p, line=dict(color="rgba(56, 189, 248, 0.65)", width=1.2, dash="dash"))
        fig.add_annotation(xref="x domain", yref=axes_map['price'], x=0.998, y=vah_p, text=f"<b>VAH {vah_p:.2f}</b>", bgcolor="#0369a1", bordercolor="#38bdf8", borderpad=2, font=dict(color="#e0f2fe", size=9, family="monospace"), showarrow=False, xanchor="right", yanchor="middle")
        fig.add_shape(type="line", xref="paper", yref=axes_map['price'], x0=0.88, x1=1.0, y0=val_p, y1=val_p, line=dict(color="rgba(56, 189, 248, 0.65)", width=1.2, dash="dash"))
        fig.add_annotation(xref="x domain", yref=axes_map['price'], x=0.998, y=val_p, text=f"<b>VAL {val_p:.2f}</b>", bgcolor="#0369a1", bordercolor="#38bdf8", borderpad=2, font=dict(color="#e0f2fe", size=9, family="monospace"), showarrow=False, xanchor="right", yanchor="middle")
        fig.add_shape(type="rect", xref="x domain", yref=axes_map['price'], x0=0.945, x1=0.998, y0=val_p, y1=vah_p, fillcolor="rgba(56, 189, 248, 0.08)", line_width=0)

        max_v = vpvr_data['max_vol']
        va_mask = vpvr_data.get('va_mask', [True] * len(vpvr_data['bin_centers']))

        for i in range(len(vpvr_data['bin_centers'])):
            bc = vpvr_data['bin_centers'][i]
            bw = vpvr_data['bin_width']
            in_va = va_mask[i] if i < len(va_mask) else True

            alpha = "0.75" if in_va else "0.30"
            up_w = 0.05 * (vpvr_data['up_vols'][i] / max_v)
            dn_w = 0.05 * (vpvr_data['down_vols'][i] / max_v)

            if up_w > 0.002:
                fig.add_shape(type="rect", xref="x domain", yref=axes_map['price'], x0=0.998 - up_w - dn_w, x1=0.998 - dn_w, y0=bc - bw * 0.45, y1=bc + bw * 0.45, fillcolor=f"rgba(34, 197, 94, {alpha})", line_width=0)
            if dn_w > 0.002:
                fig.add_shape(type="rect", xref="x domain", yref=axes_map['price'], x0=0.998 - dn_w, x1=0.998, y0=bc - bw * 0.45, y1=bc + bw * 0.45, fillcolor=f"rgba(239, 68, 68, {alpha})", line_width=0)

    # 🟣 1. 原版 VQC 轉勢日
    if show_vqc and vqc_signals:
        for s in vqc_signals:
            is_fut = s.get('is_future', False)
            if is_fut and s['type'] == 'top':
                target_y = s['price'] - 8.0
                ay_off = 38
            elif is_fut and s['type'] == 'bottom':
                target_y = s['price']
                ay_off = 32
            else:
                target_y = s['price']
                ay_off = -32 if s['type'] == 'top' else 32

            fig.add_annotation(
                x=s['date'], y=target_y, xref="x", yref=axes_map['price'],
                text=f"<span style='font-size:9px; color:#c7d2fe;'>VQC</span><br><b style='font-size:10px; color:#ffffff;'>{s['date_str']}</b>",
                bgcolor="#312e81", bordercolor="#818cf8", borderwidth=1.5, borderpad=3,
                font=dict(family="monospace"), showarrow=True, arrowhead=2, arrowcolor="#818cf8", ay=ay_off, xanchor="center"
            )

    # 🔴 2. 四立與二十四節氣
    if show_solar and solar_terms:
        for t in solar_terms:
            dt = t['date']
            name = t['name']
            d_str = t['date_str']
            time_str = t.get('time_str', '')
            is_four_li = t['is_four_li']

            if is_four_li:
                bg_col, bd_col, line_col, line_w, line_dash, y_sky = "#881337", "#f43f5e", "rgba(244, 63, 94, 0.85)", 1.6, "dash", 0.94
                tag_html = f"<span style='font-size:9px; color:#fca5a5;'>★ 四立</span><br><b style='font-size:10.5px; color:#ffffff;'>{name} {d_str}</b><br><span style='font-size:8.5px; color:#fecdd3;'>{time_str}</span>"
            else:
                bg_col, bd_col, line_col, line_w, line_dash, y_sky = "#1e3a8a", "#38bdf8", "rgba(56, 189, 248, 0.45)", 1.0, "dot", 0.87
                tag_html = f"<span style='font-size:8.5px; color:#93c5fd;'>節氣</span><br><b style='font-size:9.5px; color:#ffffff;'>{name} {d_str}</b><br><span style='font-size:8px; color:#bae6fd;'>{time_str}</span>"

            fig.add_shape(type="line", xref="x", yref="paper", x0=dt, x1=dt, y0=0.01, y1=y_sky - 0.05, line=dict(color=line_col, width=line_w, dash=line_dash))
            fig.add_annotation(xref="x", yref="paper", x=dt, y=y_sky, text=tag_html, bgcolor=bg_col, bordercolor=bd_col, borderwidth=1.5, borderpad=3, font=dict(family="monospace"), showarrow=False, xanchor="center", yanchor="middle")

    # 🎯 🌟 注入推算暗區與時空探針 (Future Projection Zone)
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
                chip_guard_html = "<span style='background:#7f1d1d; color:#fca5a5; border:1px solid #ef4444; padding:1px 6px; border-radius:3px; margin-left:6px;'><b>⚠️ 籌碼真空加速區：禁止逆向摸頂/抄底，防週期鈍化！</b></span>"
            elif vpvr_data.get('near_poc') or vpvr_data.get('is_hvn'):
                chip_guard_html = f"<span style='background:#14532d; color:#86efac; border:1px solid #22c55e; padding:1px 6px; border-radius:3px; margin-left:6px;'><b>🛡️ POC籌碼重兵區 (${vpvr_data['poc_price']:.2f})：時空籌碼共振真變盤 (勝率高)</b></span>"
            elif vpvr_data.get('is_in_value_area'):
                chip_guard_html = "<span style='background:#0f3854; color:#7dd3fc; border:1px solid #38bdf8; padding:1px 6px; border-radius:3px; margin-left:6px;'><b>⚖️ 70%價值區內：平衡震盪週期勝率 >85%</b></span>"
            else:
                chip_guard_html = "<span style='background:#3b1e54; color:#f0abfc; border:1px solid #c084fc; padding:1px 6px; border-radius:3px; margin-left:6px;'><b>⚡ 突破價值區：單邊趨勢失衡，防週期鈍化</b></span>"

        hud_cycle = f"<b>TIME CYCLE</b>  200 BARS  |  <span style='background:#78350f; color:#fde68a; padding:1px 4px;'><b>{cycle_data['window_status']}</b></span>  |  相位 {cycle_data['current_phase_deg']}°  |  距轉折 {cycle_data['next_turn_bars']}B  |  {chip_guard_html}"
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
    # --- 圖層 5: ⏳ 諧波時間跳躍弧 (Harmonic Arcs) ---
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
        hovermode='x',  # 🎯 單一 X 軸配合 hovermode='x'，實現十字線全軸貫通！
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