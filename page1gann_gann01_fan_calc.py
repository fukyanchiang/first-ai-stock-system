"""
Filename: page1gann_gann01_fan_calc.py
Description: 小龍原版太極時空幾何 + Auto Fibonacci 智能黃金分割回撤系統
升級功能：
  1. 波動率異常擴張濾網 (Volatility Shock Filter: TR > 2.5 * ATR20 黑天鵝預警)
  2. 幾何錨點破位自適應重置 (Dynamic Auto-Recalibration)
  3. 黃金口袋骨骼斷裂防禦警報 (跌破 78.6% - 1.5*ATR 切換防禦)
  4. 黃金分割獨立錨定最近波段，底部位穩定生成底部黃金口袋支持區
  5. 解除 Y 軸鎖死，延伸目標 (127.2% / 161.8%) 完整呈現
  6. 原生實心彩色 Box 膠囊標籤，徹底杜絕透明或程式碼洩漏
"""

import streamlit as st
import numpy as np
import pandas as pd
import plotly.graph_objects as go
from datetime import timedelta


def compute_gann_fan_and_arcs(
    df: pd.DataFrame,
    extend_bars: int = 40,
    show_fan: bool = True,
    show_mirror: bool = True,
    show_channels: bool = True,
    show_fibo: bool = True,
    show_fibo_ext: bool = False,
    anchor_mode: str = "經典前浪推演 (弧帶貫穿當前走勢)",
    manual_a_date=None,
    manual_b_date=None
):
    if df is None or len(df) < 10:
        return None

    # ==========================================
    # 0. 波動率衝擊濾網 (Volatility Shock Filter - ATR20)
    # ==========================================
    tr1 = df['High'] - df['Low']
    tr2 = (df['High'] - df['Close'].shift(1)).abs()
    tr3 = (df['Low'] - df['Close'].shift(1)).abs()
    tr = pd.concat([tr1, tr2, tr3], axis=1).max(axis=1)
    atr_20 = tr.rolling(20, min_periods=1).mean().bfill()
    last_tr = float(tr.iloc[-1])
    last_atr = float(atr_20.iloc[-1])
    is_vol_shock = bool(last_tr > 2.5 * last_atr)

    # ==========================================
    # 1. 錨點 A 與 B (太極江恩專屬，含破位自適應重置)
    # ==========================================
    recalibrated = False
    recalibrate_msg = ""

    if anchor_mode == "手動自選 A-B 錨點" and manual_a_date in df.index and manual_b_date in df.index:
        pos_a = df.index.get_loc(manual_a_date)
        pos_b = df.index.get_loc(manual_b_date)
        is_downtrend = pos_a < pos_b
        p_a = float(df.loc[manual_a_date, 'High' if is_downtrend else 'Low'])
        p_b = float(df.loc[manual_b_date, 'Low' if is_downtrend else 'High'])
        pivot_a = {"date": manual_a_date, "price": p_a, "label": "A"}
        pivot_b = {"date": manual_b_date, "price": p_b, "label": "B"}
    elif anchor_mode == "經典前浪推演 (弧帶貫穿當前走勢)":
        sub_len = min(len(df), 110)
        sub_df = df.iloc[-sub_len:-12].copy() if len(df) > 30 else df.copy()
        max_idx = sub_df['High'].idxmax()
        min_idx = sub_df['Low'].idxmin()
        pos_max = df.index.get_loc(max_idx)
        pos_min = df.index.get_loc(min_idx)

        if pos_max < pos_min:
            is_downtrend = True
            pos_a, pos_b = pos_max, pos_min
            pivot_a = {"date": max_idx, "price": float(df.loc[max_idx, 'High']), "label": "A"}
            pivot_b = {"date": min_idx, "price": float(df.loc[min_idx, 'Low']), "label": "B"}
        else:
            is_downtrend = False
            pos_a, pos_b = pos_min, pos_max
            pivot_a = {"date": min_idx, "price": float(df.loc[min_idx, 'Low']), "label": "A"}
            pivot_b = {"date": max_idx, "price": float(df.loc[max_idx, 'High']), "label": "B"}

        # 🎯 幾何錨點破位檢測：若最新價格跌破 B 點超過 1.5 ATR，觸發自適應重置
        last_close_val = float(df['Close'].iloc[-1])
        if is_downtrend and last_close_val < (pivot_b["price"] - 1.5 * last_atr):
            recalibrated = True
            recalibrate_msg = "前浪幾何骨骼斷裂，已自動向後搜尋最新次級波段錨點"
            tail_df = df.tail(50).copy()
            t_max_idx = tail_df['High'].idxmax()
            t_min_idx = tail_df['Low'].idxmin()
            t_pos_max = df.index.get_loc(t_max_idx)
            t_pos_min = df.index.get_loc(t_min_idx)
            if t_pos_max < t_pos_min:
                pos_a, pos_b = t_pos_max, t_pos_min
                pivot_a = {"date": t_max_idx, "price": float(df.loc[t_max_idx, 'High']), "label": "A'"}
                pivot_b = {"date": t_min_idx, "price": float(df.loc[t_min_idx, 'Low']), "label": "B'"}
    else:
        # 即時尾浪推演
        sub_df = df.tail(60).copy()
        max_idx = sub_df['High'].idxmax()
        min_idx = sub_df['Low'].idxmin()
        pos_max = df.index.get_loc(max_idx)
        pos_min = df.index.get_loc(min_idx)
        is_downtrend = pos_max < pos_min
        pos_a = min(pos_max, pos_min)
        pos_b = max(pos_max, pos_min)
        p_a = float(df.loc[max_idx if is_downtrend else min_idx, 'High' if is_downtrend else 'Low'])
        p_b = float(df.loc[min_idx if is_downtrend else max_idx, 'Low' if is_downtrend else 'High'])
        pivot_a = {"date": df.index[pos_a], "price": p_a, "label": "A"}
        pivot_b = {"date": df.index[pos_b], "price": p_b, "label": "B"}

    delta_t_bars = max(2, abs(pos_b - pos_a))
    delta_p = abs(pivot_a["price"] - pivot_b["price"])
    scale_1x1 = delta_p / delta_t_bars if delta_t_bars > 0 else 1.0
    bar_step_days = max(1.0, (df.index[-1] - df.index[0]).days / max(1, len(df) - 1))

    y_min_visible = float(df['Low'].tail(90).min()) * 0.96
    y_max_visible = float(df['High'].tail(90).max()) * 1.04

    # 太極弧帶評估範圍 (齊平於 A 點水平線)
    if is_downtrend:
        y_eval = np.linspace(y_min_visible, pivot_a["price"], 60)
    else:
        y_eval = np.linspace(pivot_a["price"], y_max_visible, 60)

    # ==========================================
    # 2. 構建太極雙藍雙黃平滑弧帶
    # ==========================================
    arc_bands = []
    base_dist = delta_t_bars
    band_half_width = max(1.0, delta_t_bars * 0.06)

    specs = [
        {"name": "太極鏡位 0.5T", "center_mult": 1.500, "color": "#00e5ff", "fill": "rgba(0, 229, 255, 0.16)"},
        {"name": "太極鏡位 1.0T", "center_mult": 2.000, "color": "#ffd700", "fill": "rgba(255, 215, 0, 0.16)"},
        {"name": "太極鏡位 1.618T", "center_mult": 2.618, "color": "#00e5ff", "fill": "rgba(0, 229, 255, 0.16)"},
        {"name": "太極鏡位 2.2T", "center_mult": 3.200, "color": "#ffd700", "fill": "rgba(255, 215, 0, 0.16)"},
        {"name": "太極鏡位 2.8T", "center_mult": 3.800, "color": "#00e5ff", "fill": "rgba(0, 229, 255, 0.16)"}
    ]

    for sp in specs:
        r_c = sp["center_mult"] * base_dist
        r_in = r_c - band_half_width
        r_out = r_c + band_half_width

        in_dates, in_prices = [], []
        out_dates, out_prices = [], []

        for p in y_eval:
            dy_norm = abs(p - pivot_a["price"]) / (scale_1x1 if scale_1x1 > 0 else 1.0)
            if r_in > dy_norm:
                dx_in = np.sqrt(max(0.0, r_in**2 - dy_norm**2))
                d_in = pivot_a["date"] + pd.to_timedelta(dx_in * bar_step_days, unit='D')
                in_dates.append(d_in)
                in_prices.append(p)

            if r_out > dy_norm:
                dx_out = np.sqrt(max(0.0, r_out**2 - dy_norm**2))
                d_out = pivot_a["date"] + pd.to_timedelta(dx_out * bar_step_days, unit='D')
                out_dates.append(d_out)
                out_prices.append(p)

        if len(in_dates) >= 5 and len(out_dates) >= 5:
            poly_dates = in_dates + out_dates[::-1]
            poly_prices = in_prices + out_prices[::-1]
            arc_bands.append({
                "label": sp["name"],
                "color": sp["color"],
                "fill": sp["fill"],
                "in_dates": in_dates,
                "in_prices": in_prices,
                "out_dates": out_dates,
                "out_prices": out_prices,
                "poly_dates": poly_dates,
                "poly_prices": poly_prices
            })

    # 白色基準 B 點時空弧
    base_b_dates, base_b_prices = [], []
    r_b = base_dist
    for p in y_eval:
        dy_norm = abs(p - pivot_a["price"]) / (scale_1x1 if scale_1x1 > 0 else 1.0)
        if r_b > dy_norm:
            dx_b = np.sqrt(max(0.0, r_b**2 - dy_norm**2))
            d_b = pivot_a["date"] + pd.to_timedelta(dx_b * bar_step_days, unit='D')
            base_b_dates.append(d_b)
            base_b_prices.append(p)

    # 趨勢軌線
    channel_data = {}
    if show_channels:
        slope = (pivot_b["price"] - pivot_a["price"]) / delta_t_bars
        total_forward_bars = len(df) - pos_a + extend_bars
        steps = np.arange(total_forward_bars)
        rail_dates = [pivot_a["date"] + pd.to_timedelta(i * bar_step_days, unit='D') for i in steps]
        primary_rail = pivot_a["price"] + slope * steps

        b_steps = np.arange(len(df) - pos_b + extend_bars)
        support_rail = pivot_b["price"] + slope * b_steps
        support_dates = [pivot_b["date"] + pd.to_timedelta(i * bar_step_days, unit='D') for i in b_steps]

        channel_data = {
            "primary_dates": rail_dates,
            "primary_prices": primary_rail,
            "support_dates": support_dates,
            "support_prices": support_rail,
            "is_downtrend": is_downtrend
        }

    # 江恩角度線
    fan_lines = {}
    if show_fan:
        ratios = {"4x1": 4.0, "2x1": 2.0, "1x1": 1.0, "1x2": 0.5, "1x4": 0.25}
        total_fan_bars = len(df) - pos_a + extend_bars
        x_fan = np.arange(total_fan_bars)
        fan_dates = [pivot_a["date"] + pd.to_timedelta(i * bar_step_days, unit='D') for i in x_fan]
        for name, r in ratios.items():
            line_y = pivot_a["price"] - (r * scale_1x1 * x_fan) if is_downtrend else pivot_a["price"] + (r * scale_1x1 * x_fan)
            clipped_y = [p if (y_min_visible * 0.9 <= p <= y_max_visible * 1.1) else None for p in line_y]
            fan_lines[name] = {"dates": fan_dates, "prices": clipped_y, "ratio": r}

    last_p = float(df['Close'].iloc[-1])

    # ==========================================
    # 3. Auto Fibonacci：智能鎖定最近主浪 + 骨骼破位檢測
    # ==========================================
    fibo_data = None
    if show_fibo:
        recent_window = df.tail(45)
        peak_idx = recent_window['High'].iloc[:-2].idxmax()
        peak_pos = df.index.get_loc(peak_idx)
        peak_price = float(df.loc[peak_idx, 'High'])

        lookback_start = max(0, peak_pos - 45)
        trough_window = df.iloc[lookback_start:peak_pos + 1]
        trough_idx = trough_window['Low'].idxmin()
        trough_price = float(df.loc[trough_idx, 'Low'])

        diff = peak_price - trough_price

        if diff > 0.05:
            retrace_pct = (peak_price - last_p) / diff * 100.0

            levels = [
                {"pct": "0%", "price": peak_price, "bg": "#546e7a", "border": "#78909c", "text_col": "#ffffff"},
                {"pct": "23.6%", "price": peak_price - 0.236 * diff, "bg": "#607d8b", "border": "#90a4ae", "text_col": "#ffffff"},
                {"pct": "38.2%", "price": peak_price - 0.382 * diff, "bg": "#00b0ff", "border": "#40c4ff", "text_col": "#ffffff"},
                {"pct": "50%", "price": peak_price - 0.500 * diff, "bg": "#7c4dff", "border": "#b388ff", "text_col": "#ffffff"},
                {"pct": "61.8%", "price": peak_price - 0.618 * diff, "bg": "#ffb300", "border": "#ffd54f", "text_col": "#000000"},
                {"pct": "78.6%", "price": peak_price - 0.786 * diff, "bg": "#ff7043", "border": "#ff8a65", "text_col": "#ffffff"},
                {"pct": "100%", "price": trough_price, "bg": "#546e7a", "border": "#78909c", "text_col": "#ffffff"}
            ]

            if show_fibo_ext:
                ext_127 = peak_price + 0.272 * diff
                ext_161 = peak_price + 0.618 * diff
                levels.insert(0, {"pct": "161.8%", "price": ext_161, "bg": "#00e676", "border": "#69f0ae", "text_col": "#000000"})
                levels.insert(1, {"pct": "127.2%", "price": ext_127, "bg": "#00e676", "border": "#69f0ae", "text_col": "#000000"})
                y_max_visible = max(y_max_visible, ext_161 * 1.05)

            gp_top = peak_price - 0.618 * diff
            gp_bottom = peak_price - 0.786 * diff

            # 🎯 幾何骨骼破位判定：跌破黃金口袋下沿 (78.6%) 且超過 1.5 * ATR
            is_gp_broken = bool(last_p < (gp_bottom - 1.5 * last_atr))

            fibo_data = {
                "mode": "上升波段",
                "p_start_date": trough_idx,
                "p_start_price": trough_price,
                "p_end_date": peak_idx,
                "p_end_price": peak_price,
                "diff": diff,
                "retrace_pct": retrace_pct,
                "gp_bottom": gp_bottom,
                "gp_top": gp_top,
                "is_gp_broken": is_gp_broken,
                "levels": levels,
                "start_x": trough_idx,
                "end_x": df.index[-1] + pd.to_timedelta(extend_bars * bar_step_days, unit='D')
            }

    return {
        "pivot_a": pivot_a,
        "pivot_b": pivot_b,
        "is_downtrend": is_downtrend,
        "scale_1x1": scale_1x1,
        "delta_t_bars": delta_t_bars,
        "arc_bands": arc_bands,
        "base_b_dates": base_b_dates,
        "base_b_prices": base_b_prices,
        "channel_data": channel_data,
        "fan_lines": fan_lines,
        "fibo_data": fibo_data,
        "last_price": last_p,
        "y_min": y_min_visible,
        "y_max": y_max_visible,
        "is_vol_shock": is_vol_shock,
        "last_tr": last_tr,
        "last_atr": last_atr,
        "recalibrated": recalibrated,
        "recalibrate_msg": recalibrate_msg
    }


def render_gann_banner(gann_data: dict):
    """
    頂部戰術橫幅 (嚴格無行首縮排，杜絕 Markdown 灰色代碼區塊洩漏)
    """
    if not gann_data:
        return

    is_down = gann_data["is_downtrend"]
    trend_mode = "GANN FAN 向下設定" if is_down else "GANN FAN 向上設定"
    accent_color = "#ff5252" if is_down else "#00e676"
    border_color = "rgba(255, 82, 82, 0.3)" if is_down else "rgba(0, 230, 118, 0.3)"

    p_a = gann_data["pivot_a"]
    p_b = gann_data["pivot_b"]
    a_dt = pd.to_datetime(p_a["date"]).strftime("%Y-%m-%d")
    b_dt = pd.to_datetime(p_b["date"]).strftime("%Y-%m-%d")
    scale = gann_data["scale_1x1"]
    last_p = gann_data["last_price"]

    # ⚡ 1. 波動率衝擊預警 HTML
    vol_shock_html = ""
    if gann_data.get("is_vol_shock"):
        last_tr = gann_data.get("last_tr", 0)
        last_atr = gann_data.get("last_atr", 0)
        vol_shock_html = (
            f'<div style="background:rgba(234,179,8,0.15); border:1px solid #eab308; border-radius:6px; padding:5px 12px; margin-top:6px; color:#fef08a; font-size:11px; display:flex; align-items:center; gap:8px;">'
            f'<span>⚡ <b>波動率極端擴張期 (單日波幅 ${last_tr:.2f} > 2.5×ATR ${last_atr:.2f})</b>：黑天鵝/突發暴雷衝擊，幾何預測精確度暫降 40%，切換防禦姿態！</span>'
            f'</div>'
        )

    # 🎯 2. 自適應重置提示 HTML
    recal_html = ""
    if gann_data.get("recalibrated"):
        recal_html = (
            f'<div style="background:rgba(56,189,248,0.15); border:1px solid #38bdf8; border-radius:6px; padding:4px 10px; margin-top:6px; color:#bae6fd; font-size:11px;">'
            f'🔄 <b>自適應重置</b>：{gann_data.get("recalibrate_msg")}'
            f'</div>'
        )

    gann_banner_html = (
        f'<div style="background:#0d1117; border:1px solid {border_color}; border-left:4px solid {accent_color}; padding:8px 16px; border-radius:8px; margin-bottom:8px;">'
        f'<div style="display:flex; justify-content:space-between; align-items:center; flex-wrap:wrap; gap:8px;">'
        f'<div style="font-size:13px; color:#f0f6fc;">'
        f'<b style="color:{accent_color}; font-size:14px;">{trend_mode} · {scale:.6f} 價格/根</b>'
        f'<span style="color:#8b949e; margin-left:14px;">錨點 {p_a.get("label", "A")}: <b>{a_dt} (${p_a["price"]:,.2f})</b> → 錨點 {p_b.get("label", "B")}: <b>{b_dt} (${p_b["price"]:,.2f})</b></span>'
        f'</div>'
        f'<div style="font-size:12px; color:#c9d1d9;">'
        f'<span style="background:rgba(255,255,255,0.06); padding:3px 8px; border-radius:4px; margin-right:8px; border:1px solid #30363d;">時空跨度: <b>{gann_data["delta_t_bars"]} 根</b></span>'
        f'<span>現價: <b style="color:#58a6ff; font-size:13px;">${last_p:,.2f}</b></span>'
        f'</div>'
        f'</div>'
        f'{vol_shock_html}'
        f'{recal_html}'
        f'</div>'
    )
    st.markdown(gann_banner_html, unsafe_allow_html=True)

    # 3. Auto Fibonacci 橫幅 (帶黃金口袋骨骼斷裂警報)
    fibo = gann_data.get("fibo_data")
    if fibo:
        is_broken = fibo.get("is_gp_broken", False)
        if is_broken:
            badge_html = (
                f'<span style="background:rgba(239,68,68,0.2); color:#fca5a5; padding:2px 8px; border-radius:4px; border:1px solid #ef4444; font-weight:bold;">'
                f'⚠️ 幾何骨骼斷裂破位 (跌破 78.6% - 1.5×ATR)'
                f'</span>'
            )
            sub_warning_html = (
                f'<div style="background:rgba(239,68,68,0.12); border:1px solid rgba(239,68,68,0.4); border-radius:6px; padding:5px 12px; margin-top:6px; color:#fca5a5; font-size:11px;">'
                f'<b>🚫 風險防禦警報</b>：黃金口袋支撐帶 (${fibo["gp_bottom"]:.2f}) 已被實體擊穿！前浪幾何結構失衡，進入自由落體區，嚴禁死守抄底，靜待新低點構築次級錨點！'
                f'</div>'
            )
            border_left_c = "#ef4444"
        else:
            badge_html = (
                f'<span style="background:rgba(255,179,0,0.15); color:#ffd700; padding:2px 8px; border-radius:4px; border:1px solid rgba(255,215,0,0.4);">'
                f'Golden Pocket 61.8%–78.6% 支持位'
                f'</span>'
            )
            sub_warning_html = ""
            border_left_c = "#ffd700"

        fibo_banner_html = (
            f'<div style="background:rgba(18, 24, 38, 0.95); border:1px solid #30363d; border-left:4px solid {border_left_c}; padding:7px 16px; border-radius:8px; margin-bottom:12px;">'
            f'<div style="display:flex; justify-content:space-between; align-items:center; flex-wrap:wrap; gap:8px;">'
            f'<div style="font-size:13px; color:#f0f6fc;">'
            f'<b style="color:{border_left_c}; font-size:13px; margin-right:10px;">Auto Fibonacci</b>'
            f'<span style="color:#c9d1d9;">{fibo["mode"]} <b>${fibo["p_start_price"]:,.2f} → ${fibo["p_end_price"]:,.2f}</b></span>'
            f'<span style="color:#8b949e; margin-left:12px;">已回撤 <b style="color:#58a6ff;">{fibo["retrace_pct"]:.1f}%</b></span>'
            f'<span style="color:#8b949e; margin-left:12px;">黃金口袋 <b style="color:#ffb300;">${fibo["gp_bottom"]:,.2f}–${fibo["gp_top"]:,.2f}</b></span>'
            f'</div>'
            f'<div style="font-size:11px;">'
            f'{badge_html}'
            f'</div>'
            f'</div>'
            f'{sub_warning_html}'
            f'</div>'
        )
        st.markdown(fibo_banner_html, unsafe_allow_html=True)


def render_gann_fan_traces(fig: go.Figure, gann_data: dict):
    if not gann_data:
        return

    is_down = gann_data.get("is_downtrend", True)

    # 1. 雙黃雙藍平滑弧帶
    arc_bands = gann_data.get("arc_bands", [])
    for band in arc_bands:
        fig.add_trace(go.Scatter(
            x=band["poly_dates"],
            y=band["poly_prices"],
            fill='toself',
            fillcolor=band["fill"],
            line=dict(color='rgba(0,0,0,0)'),
            hoverinfo='skip',
            showlegend=False
        ), row=1, col=1)

        fig.add_trace(go.Scatter(
            x=band["in_dates"],
            y=band["in_prices"],
            mode='lines',
            line=dict(color=band["color"], width=1.5),
            name=f"{band['label']} (內弧)",
            hoverinfo='name',
            showlegend=False
        ), row=1, col=1)

        fig.add_trace(go.Scatter(
            x=band["out_dates"],
            y=band["out_prices"],
            mode='lines',
            line=dict(color=band["color"], width=1.5),
            name=f"{band['label']} (外弧)",
            hoverinfo='name',
            showlegend=False
        ), row=1, col=1)

        if len(band["in_dates"]) > 0 and len(band["out_dates"]) > 0:
            top_idx = -1 if is_down else 0
            fig.add_trace(go.Scatter(
                x=[band["in_dates"][top_idx], band["out_dates"][top_idx]],
                y=[band["in_prices"][top_idx], band["out_prices"][top_idx]],
                mode='lines',
                line=dict(color=band["color"], width=1.5),
                hoverinfo='skip',
                showlegend=False
            ), row=1, col=1)

    # 2. 基準 B 點時空弧
    if gann_data.get("base_b_dates"):
        fig.add_trace(go.Scatter(
            x=gann_data["base_b_dates"],
            y=gann_data["base_b_prices"],
            mode='lines',
            line=dict(color='rgba(255, 255, 255, 0.7)', width=1.6),
            name='基準 B 點時空弧',
            hoverinfo='name',
            showlegend=False
        ), row=1, col=1)

    # 3. A-B 軸線
    p_a = gann_data["pivot_a"]
    p_b = gann_data["pivot_b"]
    fig.add_trace(go.Scatter(
        x=[p_a["date"], p_b["date"]],
        y=[p_a["price"], p_b["price"]],
        mode='lines+markers',
        line=dict(color='#ffffff', width=2.4),
        marker=dict(size=8, color=['#ffffff', '#ffd700']),
        name='A-B 主軸',
        showlegend=False
    ), row=1, col=1)

    c_data = gann_data.get("channel_data", {})
    if c_data:
        fig.add_trace(go.Scatter(
            x=c_data["primary_dates"],
            y=c_data["primary_prices"],
            mode='lines',
            line=dict(color='#ffd700', width=1.5, dash='dash'),
            name='主軌線',
            showlegend=False
        ), row=1, col=1)

        tag_txt = "DA1 支持線" if is_down else "UA1 阻力線"
        fig.add_trace(go.Scatter(
            x=c_data["support_dates"],
            y=c_data["support_prices"],
            mode='lines+text',
            line=dict(color='#00e5ff', width=1.5, dash='longdash'),
            name=tag_txt,
            text=["", tag_txt],
            textposition="bottom right",
            textfont=dict(color="#00e5ff", size=11),
            showlegend=False
        ), row=1, col=1)

    # 4. 江恩角度線
    fan_lines = gann_data.get("fan_lines", {})
    for name, item in fan_lines.items():
        ratio = item["ratio"]
        col = "#ffd700" if name == "1x1" else "rgba(0, 229, 255, 0.55)" if ratio > 1.0 else "rgba(224, 64, 251, 0.55)"
        fig.add_trace(go.Scatter(
            x=item["dates"],
            y=item["prices"],
            mode='lines',
            line=dict(color=col, width=2.0 if name == "1x1" else 1.0, dash="solid" if name == "1x1" else "dash"),
            name=f"江恩 {name}",
            showlegend=False
        ), row=1, col=1)

    # ==========================================
    # 5. Auto Fibonacci：黃金口袋與實心彩色膠囊 Box 標籤
    # ==========================================
    fibo = gann_data.get("fibo_data")
    if fibo:
        is_broken = fibo.get("is_gp_broken", False)

        # A. 連接起點至頂點的紅色點線
        fig.add_trace(go.Scatter(
            x=[fibo["p_start_date"], fibo["p_end_date"]],
            y=[fibo["p_start_price"], fibo["p_end_price"]],
            mode='lines+markers',
            line=dict(color='rgba(255, 82, 82, 0.85)', width=1.8, dash='dot'),
            marker=dict(size=6, color='#ff5252'),
            name='上升主浪',
            hoverinfo='name',
            showlegend=False
        ), row=1, col=1)

        # B. 黃金口袋 (Golden Pocket) 陰影帶 (破位時自動轉為半透明紅色警告)
        gp_y0 = min(fibo["gp_bottom"], fibo["gp_top"])
        gp_y1 = max(fibo["gp_bottom"], fibo["gp_top"])
        gp_fill = 'rgba(239, 68, 68, 0.18)' if is_broken else 'rgba(255, 179, 0, 0.22)'

        fig.add_trace(go.Scatter(
            x=[fibo["start_x"], fibo["end_x"], fibo["end_x"], fibo["start_x"]],
            y=[gp_y0, gp_y0, gp_y1, gp_y1],
            fill='toself',
            fillcolor=gp_fill,
            line=dict(color='rgba(0,0,0,0)'),
            hoverinfo='skip',
            showlegend=False
        ), row=1, col=1)

        if is_broken:
            fig.add_annotation(
                xref="x", yref="y",
                x=fibo["end_x"], y=fibo["gp_bottom"],
                text="<b>⚠️ 幾何骨骼已破位</b>",
                bgcolor="#7f1d1d", bordercolor="#ef4444", borderwidth=1, borderpad=3,
                font=dict(color="#fca5a5", size=9, family="monospace"),
                showarrow=False, xanchor="right", yanchor="top",
                row=1, col=1
            )

        # C. 橫向黃金分割線與實心彩色 Box 標籤
        for lvl in fibo["levels"]:
            p = lvl["price"]
            pct = lvl["pct"]
            bg_col = lvl["bg"]
            border_col = lvl["border"]
            txt_col = lvl["text_col"]

            is_gp_boundary = pct in ["61.8%", "78.6%"]
            line_w = 2.0 if is_gp_boundary else 1.2
            dash_style = "dash" if is_gp_boundary else "dot" if pct not in ["0%", "100%"] else "solid"

            if is_broken and pct == "78.6%":
                border_col = "#ef4444"

            fig.add_trace(go.Scatter(
                x=[fibo["start_x"], fibo["end_x"]],
                y=[p, p],
                mode='lines',
                line=dict(color=bg_col, width=line_w, dash=dash_style),
                hoverinfo='skip',
                showlegend=False
            ), row=1, col=1)

            badge_text = f"<b>{pct}</b>  {p:,.2f}"
            fig.add_annotation(
                xref="x domain",
                yref="y",
                x=0.998,
                y=p,
                text=badge_text,
                bgcolor=bg_col,
                bordercolor=border_col,
                borderwidth=1.5,
                borderpad=4,
                font=dict(color=txt_col, size=10, family="monospace, Arial, sans-serif"),
                showarrow=False,
                xanchor="right",
                yanchor="middle",
                align="center",
                row=1,
                col=1
            )

    # 6. 錨點與現價
    label_a = p_a.get("label", "A")
    label_b = p_b.get("label", "B")
    fig.add_trace(go.Scatter(
        x=[p_a["date"], p_b["date"]],
        y=[p_a["price"], p_b["price"]],
        mode='markers+text',
        marker=dict(symbol='circle', size=9, color=['#ffffff', '#ffd700'], line=dict(color='#000000', width=1.5)),
        text=[f" 錨點 {label_a}", f" 錨點 {label_b}"],
        textposition="top right",
        textfont=dict(color="#ffffff", size=11, family="Arial Black"),
        showlegend=False
    ), row=1, col=1)

    fig.add_hline(
        y=p_a["price"],
        line=dict(color="rgba(255, 255, 255, 0.45)", width=1.0, dash="dot"),
        annotation_text=f"{label_a} 點極值 ${p_a['price']:.2f}",
        annotation_position="top left",
        annotation_font=dict(color="#ffffff", size=9),
        row=1, col=1
    )

    last_p = gann_data["last_price"]
    fig.add_hline(
        y=last_p,
        line=dict(color="rgba(255, 82, 82, 0.85)", width=1.2, dash="dash"),
        annotation_text=f"現價 ${last_p:.2f}",
        annotation_position="right",
        annotation_font=dict(color="#ff5252", size=10),
        row=1, col=1
    )

    if "y_min" in gann_data and "y_max" in gann_data:
        fig.update_yaxes(range=[gann_data["y_min"], gann_data["y_max"]], row=1, col=1)