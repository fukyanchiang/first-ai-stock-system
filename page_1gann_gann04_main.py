"""
Filename: page_1gann_gann04_main.py
Description: 📊 頁面 4 (Gann 04)：小龍江恩策略 Y 專屬操盤工作台 (四維共振決策卡 + 可收合計分說明拉掣版)
升級亮點：
  1. 🌟 [全新加入] 📖 四維共振計分說明與交易室戰術指引 (可折疊拉掣，隨開隨看)
  2. 🌟 時空量價「四維共振決策引擎」(Confluence Score Engine)：
     - 整合 趨勢(三雲) + 量能(Volume Plus) + 動能(SL Angle/動能波) + 時空(2R週期/S-R支阻)
     - 輸出 -100 ~ +100 分綜合評級與交易室實戰指令卡
  3. 🌟 SL Angle ATR-14 波動率標準化 (映射江恩 1x1 45° 平衡線與 ±60° 警戒線)
  4. 🌟 江恩八度音階同頻諧振 (Time Cycle 2R 與基準週期 R 實時鎖定，谷底精準對齊 12/22)
  5. 🌟 S/R 支阻動態極性翻轉 (Polarity Principle) + 頂部即時風控空間 %
  6. 🌟 26px 價格防碰撞鬆弛演算法 (已納入 S/R、現價及 Eric's Channel 中軸，徹底杜絕標籤重疊切字) + 右側 68px 安全留白保護
"""

import streamlit as st
import pandas as pd
import numpy as np
import plotly.graph_objects as go
from plotly.subplots import SubplotRef
import importlib

# 引入運算模組
try:
    import page_1gann_gann04_calc as calc_engine
    importlib.reload(calc_engine)
except ImportError:
    calc_engine = None

try:
    import page_1gann_gann02_cycle_calc as cycle_engine
    importlib.reload(cycle_engine)
except ImportError:
    cycle_engine = None

try:
    import page_1gann_gann02_extreme_calc as ext_engine
    importlib.reload(ext_engine)
except ImportError:
    ext_engine = None

try:
    import component_gann_harmonic_arcs as harmonic_comp
    importlib.reload(harmonic_comp)
except ImportError:
    harmonic_comp = None


def build_grid_ref(num_rows):
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


def get_cloud_polygon_segments(dates, lead_series, lag_series, bull_fill, bear_fill):
    """將均線切分為連續閉合多邊形，實現升勢綠帶、跌勢紅帶的動態漸變"""
    diff = lead_series.values - lag_series.values
    y1 = lead_series.values
    y2 = lag_series.values
    n = len(dates)

    traces = []
    seg_start = 0

    for i in range(1, n):
        prev_bull = diff[i - 1] >= 0
        curr_bull = diff[i] >= 0

        if prev_bull != curr_bull or i == n - 1:
            seg_end = i if (i == n - 1 and prev_bull == curr_bull) else i
            d_sub = list(dates[seg_start:seg_end + 1])
            y1_sub = list(y1[seg_start:seg_end + 1])
            y2_sub = list(y2[seg_start:seg_end + 1])

            poly_x = d_sub + d_sub[::-1]
            poly_y = y1_sub + y2_sub[::-1]

            color = bull_fill if prev_bull else bear_fill
            traces.append(go.Scatter(
                x=poly_x, y=poly_y,
                fill='toself',
                fillcolor=color,
                line=dict(color='rgba(0,0,0,0)', width=0),
                hoverinfo='skip',
                showlegend=False
            ))
            seg_start = i

    return traces


def resolve_label_collisions(items, min_gap_px=26, total_height_px=500, p_min=100, p_max=300):
    """
    一維標籤防重疊鬆弛演算法：
    以全局真實坐標為基準，自動推開距離過近的價格膠囊，確保垂直間隔至少 min_gap_px
    """
    sorted_items = sorted(items, key=lambda x: x['price'])
    n = len(sorted_items)
    if n <= 1:
        return {it['id']: 0 for it in sorted_items}

    p_range = max(1e-5, p_max - p_min)
    for it in sorted_items:
        it['pos_px'] = ((it['price'] - p_min) / p_range) * total_height_px
        it['adjusted_px'] = it['pos_px']

    for _ in range(50):
        changed = False
        for i in range(n - 1):
            gap = sorted_items[i + 1]['adjusted_px'] - sorted_items[i]['adjusted_px']
            if gap < min_gap_px:
                overlap = min_gap_px - gap
                shift = overlap / 2.0
                sorted_items[i]['adjusted_px'] -= shift
                sorted_items[i + 1]['adjusted_px'] += shift
                changed = True
        if not changed:
            break

    shifts = {}
    for it in sorted_items:
        ysh = int(round(it['adjusted_px'] - it['pos_px']))
        shifts[it['id']] = max(-45, min(45, ysh))
    return shifts


def compute_resonant_time_cycle(df: pd.DataFrame, r_period: int = 47, future_days: int = 85, harmonic_data: dict = None):
    """
    江恩八度音階同頻諧振時間週期計算引擎：
    將 Time Cycle 週期直接與主圖諧波基準週期 R (2R 主循環 + R 次級諧波) 實施相位鎖定
    """
    dates_hist = df.index
    last_date = dates_hist[-1]

    future_dates = pd.date_range(last_date + pd.Timedelta(days=1), periods=int(future_days * 1.5), freq='D')
    future_dates = future_dates[future_dates.dayofweek < 5][:future_days]

    all_dates = dates_hist.append(future_dates)
    n_total = len(all_dates)
    n_hist = len(dates_hist)

    cycle_bars = max(10, int(r_period * 2))

    a2_dt = None
    a1_dt = None
    if harmonic_data and 'a2_date' in harmonic_data and harmonic_data['a2_date']:
        try:
            a2_dt = pd.to_datetime(harmonic_data['a2_date'])
        except Exception:
            a2_dt = None

    if harmonic_data and 'a1_date' in harmonic_data and harmonic_data['a1_date']:
        try:
            a1_dt = pd.to_datetime(harmonic_data['a1_date'])
        except Exception:
            a1_dt = None

    if a2_dt is not None:
        if a2_dt in all_dates:
            a2_idx = all_dates.get_loc(a2_dt)
        else:
            a2_idx = int(np.argmin(np.abs(all_dates - a2_dt)))
    else:
        lookback = min(len(df), max(10, r_period))
        sub_highs = df['High'].iloc[-lookback:]
        sub_lows = df['Low'].iloc[-lookback:]
        h_idx = sub_highs.idxmax()
        l_idx = sub_lows.idxmin()
        if df.index.get_loc(h_idx) >= df.index.get_loc(l_idx):
            a2_dt = h_idx
        else:
            a2_dt = l_idx
        a2_idx = all_dates.get_loc(a2_dt)

    a2_is_peak = True
    if a1_dt is not None and a2_dt is not None:
        try:
            p_a1 = df.loc[a1_dt, 'Close'] if a1_dt in df.index else df['Close'].iloc[0]
            p_a2 = df.loc[a2_dt, 'Close'] if a2_dt in df.index else df['Close'].iloc[-1]
            a2_is_peak = bool(p_a2 >= p_a1)
        except Exception:
            a2_is_peak = True
    elif harmonic_data and 'a2_type' in harmonic_data:
        a2_is_peak = bool(harmonic_data['a2_type'] == 'high')

    base_phase_a2 = (np.pi / 2.0) if a2_is_peak else (3.0 * np.pi / 2.0)

    idx_arr = np.arange(n_total) - a2_idx
    omega = 2.0 * np.pi / cycle_bars
    phases = base_phase_a2 + omega * idx_arr

    cycle_vals = 100.0 * np.sin(phases)

    omega_sub = 2.0 * np.pi / max(5, int(r_period))
    sub_cycle_vals = 30.0 * np.sin(base_phase_a2 + omega_sub * idx_arr)

    pos_cycle = np.where(cycle_vals >= 0, cycle_vals, np.nan)
    neg_cycle = np.where(cycle_vals < 0, cycle_vals, np.nan)

    peaks = []
    troughs = []
    start_search = max(1, n_hist - cycle_bars * 2)
    for i in range(start_search, n_total - 1):
        if cycle_vals[i] > cycle_vals[i - 1] and cycle_vals[i] >= cycle_vals[i + 1] and cycle_vals[i] >= 90:
            peaks.append((all_dates[i], round(float(cycle_vals[i]), 1)))
        elif cycle_vals[i] < cycle_vals[i - 1] and cycle_vals[i] <= cycle_vals[i + 1] and cycle_vals[i] <= -90:
            troughs.append((all_dates[i], round(float(cycle_vals[i]), 1)))

    curr_idx = n_hist - 1
    curr_phase_rad = phases[curr_idx] % (2.0 * np.pi)
    curr_phase_deg = int(np.round(np.degrees(curr_phase_rad)))

    p_peak = np.pi / 2.0
    p_trough = 3.0 * np.pi / 2.0
    diff_peak = (p_peak - curr_phase_rad) % (2.0 * np.pi)
    diff_trough = (p_trough - curr_phase_rad) % (2.0 * np.pi)

    bars_peak = int(np.round(diff_peak / omega))
    bars_trough = int(np.round(diff_trough / omega))

    if bars_peak <= 1:
        window_status = "尋底期 (頂部回落)"
        next_turn_bars = bars_trough
    elif bars_trough <= 1:
        window_status = "尋頂期 (谷底回升)"
        next_turn_bars = bars_peak
    elif bars_trough < bars_peak:
        window_status = "尋底期 (下行向谷底)"
        next_turn_bars = bars_trough
    else:
        window_status = "尋頂期 (上行向峰頂)"
        next_turn_bars = bars_peak

    return {
        'interp_dates': all_dates,
        'pos_cycle': pos_cycle,
        'neg_cycle': neg_cycle,
        'cycle_vals': cycle_vals,
        'sub_cycle_vals': sub_cycle_vals,
        'peaks': peaks,
        'troughs': troughs,
        'window_status': window_status,
        'current_phase_deg': curr_phase_deg,
        'next_turn_bars': next_turn_bars,
        'cycle_bars': cycle_bars,
        'r_period': r_period
    }


def compute_atr_normalized_sl_angle(df: pd.DataFrame, lookback_k: int = 5, atr_len: int = 14):
    """
    SL Angle 幾何動能線 ATR 波動率標準化計算引擎：
    - 將價格位移除以 (k * ATR_14)，消除股票價格尺度的絕對偏差
    - 1 ATR/Bar 的推進速率剛好對齊 45° (江恩 1x1 線)
    """
    if df is None or len(df) < 5:
        return None

    high = df['High']
    low = df['Low']
    close = df['Close']

    tr1 = high - low
    tr2 = (high - close.shift(1)).abs()
    tr3 = (low - close.shift(1)).abs()
    tr = pd.concat([tr1, tr2, tr3], axis=1).max(axis=1)
    atr = tr.rolling(atr_len, min_periods=1).mean()
    atr_safe = atr.replace(0, 1e-4).bfill()

    delta_p = close - close.shift(lookback_k)
    norm_slope = delta_p / (lookback_k * atr_safe)

    angle_rad = np.arctan(norm_slope)
    angle_deg = np.degrees(angle_rad)

    angle_smooth = angle_deg.ewm(span=3, adjust=False).mean().fillna(0.0)

    pos_angles = np.where(angle_smooth >= 0, angle_smooth, np.nan)
    neg_angles = np.where(angle_smooth < 0, angle_smooth, np.nan)

    last_angle = round(float(angle_smooth.iloc[-1]), 1)
    last_atr = round(float(atr.iloc[-1]), 2)

    if last_angle >= 60.0:
        angle_status = "⚡ 超買衝刺 (極限加速)"
        status_color = "#f43f5e"
    elif last_angle >= 45.0:
        angle_status = "🚀 江恩 1x1 強多頭 (角度 ≥ +45°)"
        status_color = "#22c55e"
    elif last_angle > 15.0:
        angle_status = "🟢 溫和多頭 (偏多運行)"
        status_color = "#4ade80"
    elif last_angle >= -15.0:
        angle_status = "⚖️ 多空平衡 (橫盤收斂)"
        status_color = "#94a3b8"
    elif last_angle > -45.0:
        angle_status = "🟡 溫和空頭 (偏空運行)"
        status_color = "#facc15"
    elif last_angle > -60.0:
        angle_status = "🔻 江恩 1x1 強空頭 (角度 ≤ -45°)"
        status_color = "#ea580c"
    else:
        angle_status = "⚠️ 超賣崩跌 (極限鈍化)"
        status_color = "#dc2626"

    return {
        'interp_dates': df.index,
        'angles': angle_smooth,
        'pos_angles': pos_angles,
        'neg_angles': neg_angles,
        'last_angle': last_angle,
        'last_atr': last_atr,
        'angle_status': angle_status,
        'status_color': status_color
    }


def compute_confluence_score(cloud_data, vol_data, mome_data, cycle_data, sl_data, sr_levels, df_chart):
    items = []
    total_score = 0

    # 1. 趨勢維度 (Eric's Three Cloud) - 25分
    trend_score = 0
    if cloud_data:
        status_txt = cloud_data.get('trend_status', '')
        if '多頭' in status_txt or 'Bull' in status_txt:
            trend_score = 25
            trend_desc = "多頭排列"
        elif '空頭' in status_txt or 'Bear' in status_txt:
            trend_score = -25
            trend_desc = "空頭排列"
        else:
            trend_score = 0
            trend_desc = "震盪收斂"
    else:
        trend_desc = "未啟用"
    items.append(('趨勢雲帶', trend_desc, trend_score))
    total_score += trend_score

    # 2. 量能維度 (Volume Plus) - 25分
    vol_score = 0
    if vol_data and len(df_chart) >= 2:
        last_v = vol_data['volume'].iloc[-1]
        last_ma = vol_data['last_ma']
        is_up = df_chart['Close'].iloc[-1] >= df_chart['Close'].iloc[-2]
        ratio = last_v / max(1.0, last_ma)
        if ratio >= 1.5:
            vol_score = 25 if is_up else -25
            vol_desc = f"放量爆發 {ratio:.1f}x"
        elif ratio >= 1.0:
            vol_score = 15 if is_up else -15
            vol_desc = f"溫和放量 {ratio:.1f}x"
        else:
            vol_score = 0
            vol_desc = f"量縮收斂 {ratio:.1f}x"
    else:
        vol_desc = "未啟用"
    items.append(('量能爆發', vol_desc, vol_score))
    total_score += vol_score

    # 3. 動能與幾何維度 (Momentum Wave & SL Angle) - 25分
    m_val = mome_data['last_val'] if mome_data else 0
    m_pt = 10 if m_val >= 0 else -10

    sl_ang = sl_data['last_angle'] if sl_data else 0
    if sl_ang >= 45:
        sl_pt = 15
    elif sl_ang > 15:
        sl_pt = 10
    elif sl_ang >= -15:
        sl_pt = 0
    elif sl_ang > -45:
        sl_pt = -10
    else:
        sl_pt = -15

    mome_score = m_pt + sl_pt
    mome_desc = f"動能{m_val:+.1f} / 角度{sl_ang:+.1f}°"
    items.append(('幾何動能', mome_desc, mome_score))
    total_score += mome_score

    # 4. 時空週期維度 (Time Cycle & S/R 支撐) - 25分
    c_status = cycle_data.get('window_status', '') if cycle_data else ''
    if '谷底回升' in c_status or '尋頂期' in c_status:
        cycle_pt = 15
    elif '頂部回落' in c_status or '尋底期' in c_status:
        cycle_pt = -15
    else:
        cycle_pt = 0

    sr_pt = 0
    if sr_levels and len(df_chart) > 0:
        supports = [it for it in sr_levels if it['is_support']]
        resistances = [it for it in sr_levels if not it['is_support']]
        last_c = df_chart['Close'].iloc[-1]
        if supports:
            nearest_s = max(it['val'] for it in supports)
            buf_pct = (last_c / nearest_s - 1.0) * 100
            if buf_pct >= 1.0:
                sr_pt = 10
            elif buf_pct < -0.5:
                sr_pt = -10
        if resistances and sr_pt == 0:
            nearest_r = min(it['val'] for it in resistances)
            gap_pct = (1.0 - last_c / nearest_r) * 100
            if gap_pct < 1.0:
                sr_pt = -5

    cycle_score = cycle_pt + sr_pt
    short_c_status = "谷底回升" if "谷底" in c_status else ("頂部回落" if "頂部" in c_status else "週期運行")
    sr_status = "守住支撐" if sr_pt >= 0 else "跌破支撐"
    cycle_desc = f"{short_c_status} / {sr_status}"
    items.append(('時空幾何', cycle_desc, cycle_score))
    total_score += cycle_score

    total_score = max(-100, min(100, total_score))

    # 決策等級判定
    if total_score >= 60:
        level = "🔥 強烈多頭共振 (戰略進攻)"
        bg_col = "rgba(16, 185, 129, 0.20)"
        bd_col = "#10b981"
        txt_col = "#34d399"
        tactics = "四維多頭全面共鳴：三雲趨勢明確，週期向上共振，具備強波段發動特徵，建議積極作多。"
    elif total_score >= 20:
        level = "🟢 偏多共振蓄勢 (逢低佈局)"
        bg_col = "rgba(45, 212, 191, 0.18)"
        bd_col = "#14b8a6"
        txt_col = "#2dd4bf"
        tactics = "多方微幅佔優：處於回測支撐或週期轉折點，短線動能蓄勢，建議依托 S1 支撐分批低吸。"
    elif total_score > -20:
        level = "⚖️ 多空中立平衡 (區間觀望)"
        bg_col = "rgba(100, 116, 139, 0.20)"
        bd_col = "#64748b"
        txt_col = "#cbd5e1"
        tactics = "信號分化互抵：多空力量均衡，量能未有效釋放，建議耐心等待量能放大或突破關鍵價位。"
    elif total_score > -60:
        level = "🟡 偏空承壓回調 (反彈減倉)"
        bg_col = "rgba(245, 158, 11, 0.18)"
        bd_col = "#f59e0b"
        txt_col = "#fbbf24"
        tactics = "空方動能佔優：承壓於阻力位下方或動能轉負，建議嚴守止損線，反彈適度減倉鎖利。"
    else:
        level = "🔴 強烈空頭共振 (嚴格避險)"
        bg_col = "rgba(239, 68, 68, 0.20)"
        bd_col = "#ef4444"
        txt_col = "#f87171"
        tactics = "四維空頭重挫：均線雲帶破位且放量承壓，嚴禁盲目抄底，維持空倉或避險防禦策略。"

    return {
        'total_score': total_score,
        'level': level,
        'bg_col': bg_col,
        'bd_col': bd_col,
        'txt_col': txt_col,
        'tactics': tactics,
        'items': items
    }


def render_page_1gann_gann04_workspace(df: pd.DataFrame, symbol: str = "2330.TW"):
    if df is None or df.empty:
        st.warning("⚠️ 查無歷史 K 線數據。")
        return

    df_full = df.copy()
    df_full.index = pd.to_datetime(df_full.index).tz_localize(None)

    # 1. 視角切換控制
    c_scope, _ = st.columns([5.2, 4.8])
    with c_scope:
        view_scope = st.radio(
            "Gann04 顯示範圍",
            ["⚡ 近 3 個月 (特寫放大)", "📊 近 6 個月", "🌐 近 1 年 (原版推薦)", "🗺️ 2 年全景"],
            index=0,
            horizontal=True,
            label_visibility="collapsed",
            key="gann04_scope_select"
        )

    target_bars = 65 if "3 個月" in view_scope else (130 if "6 個月" in view_scope else (250 if "1 年" in view_scope else 500))
    df_chart = df_full.tail(target_bars).copy()

    # 處理一鍵回復預設邏輯
    if st.session_state.get("trigger_reset_gann04", False):
        st.session_state["gann04_r_period"] = 47
        st.session_state["gann04_cloud"] = True
        st.session_state["gann04_sr"] = True
        st.session_state["gann04_sr_rays"] = True
        st.session_state["gann04_vol_plus"] = True
        st.session_state["gann04_mome_wave"] = True
        st.session_state["gann04_gann_range"] = True
        st.session_state["gann04_cycle"] = True
        st.session_state["gann04_sl"] = True
        st.session_state["gann04_harmonic"] = True
        st.session_state["gann04_confluence"] = True
        st.session_state["trigger_reset_gann04"] = False

    # 2. 控制面板
    with st.expander("⚙️ Gann 04 策略 Y 控制面板 (三雲趨勢、支阻長線與時空幾何)", expanded=True):
        c1, c2, c3, c4, c5 = st.columns([2.0, 2.2, 2.2, 2.0, 2.0])
        with c1:
            show_cloud = st.checkbox("✓ Eric's Three Cloud", value=st.session_state.get("gann04_cloud", True), key="gann04_cloud")
            show_sr = st.checkbox("✓ Volume Pressure S/R", value=st.session_state.get("gann04_sr", True), key="gann04_sr")
        with c2:
            show_sr_rays = st.checkbox("✓ 主要支阻長線 (S/R Rays)", value=st.session_state.get("gann04_sr_rays", True), key="gann04_sr_rays")
            show_vol_plus = st.checkbox("✓ Volume Plus (量能)", value=st.session_state.get("gann04_vol_plus", True), key="gann04_vol_plus")
        with c3:
            show_mome_wave = st.checkbox("✓ Momentum Wave (動能)", value=st.session_state.get("gann04_mome_wave", True), key="gann04_mome_wave")
            show_gann_range = st.checkbox("✓ Auto Gann Range", value=st.session_state.get("gann04_gann_range", True), key="gann04_gann_range")
        with c4:
            show_cycle = st.checkbox("✓ Time Cycle (正弦波)", value=st.session_state.get("gann04_cycle", True), key="gann04_cycle")
            show_sl_angle = st.checkbox("✓ SL Angle (動能角度)", value=st.session_state.get("gann04_sl", True), key="gann04_sl")
        with c5:
            show_harmonic = st.checkbox("⏳ 諧波時間弧 (未來推算)", value=st.session_state.get("gann04_harmonic", True), key="gann04_harmonic")
            show_confluence = st.checkbox("🎯 四維共振決策卡", value=st.session_state.get("gann04_confluence", True), key="gann04_confluence")
            r_period = st.slider("基準週期 R (K線)", min_value=10, max_value=120, value=st.session_state.get("gann04_r_period", 47), step=1, key="gann04_r_period")
            if st.button("🔄 回復預設配置", key="btn_reset_defaults_gann04"):
                st.session_state["trigger_reset_gann04"] = True
                st.rerun()

    # 3. 數據運算
    future_span_days = 85
    chart_start_dt = df_chart.index[0]
    chart_end_base = df_chart.index[-1] + pd.Timedelta(days=future_span_days)

    cloud_data = calc_engine.compute_three_cloud_trend(df_chart) if (calc_engine and show_cloud) else None
    sr_data = calc_engine.compute_volume_pressure_sr(df_chart) if (calc_engine and show_sr) else None
    vol_data = calc_engine.compute_volume_plus(df_chart) if (calc_engine and show_vol_plus) else None
    mome_data = calc_engine.compute_momentum_wave(df_chart) if (calc_engine and show_mome_wave) else None
    gann_box = calc_engine.compute_auto_gann_range(df_chart, future_bars=90) if (calc_engine and show_gann_range) else None

    harmonic_data = None
    if show_harmonic and harmonic_comp is not None and hasattr(harmonic_comp, "compute_harmonic_arcs_data"):
        try:
            harmonic_data = harmonic_comp.compute_harmonic_arcs_data(
                df=df_chart, r_period=r_period, manual_a1_date=None, manual_a2_date=None
            )
        except Exception as e:
            st.error(f"諧波時間弧運算錯誤: {e}")

    cycle_data = None
    if show_cycle:
        cycle_data = compute_resonant_time_cycle(
            df=df_chart,
            r_period=r_period,
            future_days=future_span_days,
            harmonic_data=harmonic_data
        )

    sl_data = None
    if show_sl_angle:
        sl_data = compute_atr_normalized_sl_angle(df_chart, lookback_k=5, atr_len=14)

    vpvr_data = None
    if ext_engine and hasattr(ext_engine, "compute_vpvr_and_poc"):
        vpvr_data = ext_engine.compute_vpvr_and_poc(df_chart)

    # =========================================================================
    # S/R 支阻階梯「極性動態翻轉運算引擎」(Polarity Principle Engine)
    # =========================================================================
    sr_levels = []
    if sr_data:
        last_c = sr_data['last_close']
        raw_defs = [
            ('r3', sr_data['r3'], sr_data['r3_date'], 'R3', sr_data['r3_bias'], 'R'),
            ('r2', sr_data['r2'], sr_data['r2_date'], 'R2', sr_data['r2_bias'], 'R'),
            ('r1', sr_data['r1'], sr_data['r1_date'], 'R1', sr_data['r1_bias'], 'R'),
            ('s1', sr_data['s1'], sr_data['s1_date'], 'S1', sr_data['s1_bias'], 'S'),
            ('s2', sr_data['s2'], sr_data['s2_date'], 'S2', sr_data['s2_bias'], 'S'),
            ('s3', sr_data['s3'], sr_data['s3_date'], 'S3', sr_data['s3_bias'], 'S'),
        ]

        for lid, val, dt, name, bias, otype in raw_defs:
            if otype == 'R':
                if last_c >= val:
                    diff_pct = (last_c / val - 1.0) * 100
                    sr_levels.append({
                        'id': lid, 'val': val, 'date': dt,
                        'display_name': f"突破轉支撐 {name}",
                        'status_badge': f"已站上 +{diff_pct:.1f}%",
                        'color': '#2dd4bf', 'border': '#0f766e', 'bg': '#2dd4bf', 'font_col': '#000000',
                        'dash': 'solid', 'width': 2.6, 'is_support': True, 'bias': bias, 'orig_type': 'R'
                    })
                else:
                    diff_pct = (1.0 - last_c / val) * 100
                    sr_levels.append({
                        'id': lid, 'val': val, 'date': dt,
                        'display_name': f"主要阻力 {name}",
                        'status_badge': f"阻力空間 -{diff_pct:.1f}%",
                        'color': '#eab308', 'border': '#ca8a04', 'bg': '#facc15', 'font_col': '#000000',
                        'dash': 'dash', 'width': 2.0, 'is_support': False, 'bias': bias, 'orig_type': 'R'
                    })
            else:
                if last_c < val:
                    diff_pct = (1.0 - last_c / val) * 100
                    sr_levels.append({
                        'id': lid, 'val': val, 'date': dt,
                        'display_name': f"破位轉阻力 {name}",
                        'status_badge': f"破位承壓 -{diff_pct:.1f}%",
                        'color': '#fb923c', 'border': '#ea580c', 'bg': '#fb923c', 'font_col': '#000000',
                        'dash': 'dash', 'width': 2.0, 'is_support': False, 'bias': bias, 'orig_type': 'S'
                    })
                else:
                    diff_pct = (last_c / val - 1.0) * 100
                    sr_levels.append({
                        'id': lid, 'val': val, 'date': dt,
                        'display_name': f"主要支撐 {name}",
                        'status_badge': f"支撐緩衝 +{diff_pct:.1f}%",
                        'color': '#2dd4bf', 'border': '#0f766e', 'bg': '#2dd4bf', 'font_col': '#000000',
                        'dash': 'solid', 'width': 2.8, 'is_support': True, 'bias': bias, 'orig_type': 'S'
                    })

    # 4. 執行四維共振評分引擎運算
    conf_data = compute_confluence_score(
        cloud_data=cloud_data,
        vol_data=vol_data,
        mome_data=mome_data,
        cycle_data=cycle_data,
        sl_data=sl_data,
        sr_levels=sr_levels,
        df_chart=df_chart
    ) if show_confluence else None

    # =========================================================================
    # 5. 頂部深黑戰術橫幅 (極性翻轉徽章 + 四維共振決策卡)
    # =========================================================================
    trend_title = cloud_data['trend_status'] if cloud_data else "三雲趨勢監控"
    trend_col = cloud_data['trend_color'] if cloud_data else "#ffffff"

    vol_ma_str = ""
    if vol_data:
        vol_ma_val = vol_data['last_ma']
        vol_ma_str = f"{vol_ma_val / 1e6:.2f}M" if vol_ma_val >= 1e6 else f"{vol_ma_val:,.0f}"

    vol_badge_html = ""
    if vol_ma_str:
        vol_badge_html = (
            f'<span style="background:rgba(2,132,199,0.25); color:#38bdf8; border:1px solid #0284c7; padding:2px 8px; border-radius:4px; font-size:11px; margin-right:8px;">'
            f'<b>Volume Plus MA20:</b> <b style="color:#ffffff;">{vol_ma_str}</b>'
            f'</span>'
        )

    sr_pills_html = ""
    if sr_levels:
        pills_list = []
        for it in sr_levels:
            if it['is_support']:
                pill = (
                    f'<span style="background:rgba(45,212,191,0.15); color:#2dd4bf; border:1px solid #14b8a6; padding:2px 8px; border-radius:4px; font-size:11px;">'
                    f'<b>{it["display_name"]} {it["val"]:.2f}</b> <span style="font-size:10px; color:#a7f3d0;">({it["status_badge"]})</span> 偏買 {it["bias"]}%'
                    f'</span>'
                )
            else:
                border_c = "#ea580c" if it.get('orig_type') == 'S' else "#eab308"
                text_c = "#fb923c" if it.get('orig_type') == 'S' else "#facc15"
                pill = (
                    f'<span style="background:rgba(234,179,8,0.15); color:{text_c}; border:1px solid {border_c}; padding:2px 8px; border-radius:4px; font-size:11px;">'
                    f'<b>{it["display_name"]} {it["val"]:.2f}</b> <span style="font-size:10px; color:#fef08a;">({it["status_badge"]})</span> 偏賣 {it["bias"]}%'
                    f'</span>'
                )
            pills_list.append(pill)

        sr_pills_html = (
            f'<div style="display:flex; align-items:center; flex-wrap:wrap; gap:8px; margin-top:8px;">'
            f'{"".join(pills_list)}'
            f'{vol_badge_html}'
            f'<span style="color:#94a3b8; font-size:10.5px; margin-left:4px;">⚡ 極性自適應：突破阻力自動翻為回踩支撐，破位支撐翻為反彈阻力。</span>'
            f'</div>'
        )

    confluence_card_html = ""
    if conf_data:
        sub_badges = []
        for d_title, d_desc, d_sc in conf_data['items']:
            d_col = "#2dd4bf" if d_sc > 0 else ("#f87171" if d_sc < 0 else "#94a3b8")
            sub_badges.append(
                f'<div style="background:#161b22; border:1px solid #30363d; border-radius:6px; padding:6px 10px; min-width:125px; flex:1;">'
                f'<div style="color:#8b949e; font-size:10px; font-weight:600; text-transform:uppercase;">{d_title}</div>'
                f'<div style="color:#ffffff; font-size:11.5px; font-weight:bold; margin-top:2px;">{d_desc}</div>'
                f'<div style="color:{d_col}; font-size:10.5px; font-weight:bold; margin-top:1px;">{d_sc:+d} 分</div>'
                f'</div>'
            )

        confluence_card_html = (
            f'<div style="background:#090d13; border:1px solid {conf_data["bd_col"]}; border-radius:8px; padding:12px 16px; margin-top:10px; box-shadow:0 4px 14px rgba(0,0,0,0.4);">'
            f'<div style="display:flex; justify-content:space-between; align-items:center; flex-wrap:wrap; gap:12px;">'
            f'<div style="display:flex; align-items:center; gap:12px;">'
            f'<div style="background:{conf_data["bg_col"]}; border:1.5px solid {conf_data["bd_col"]}; border-radius:8px; padding:6px 14px; text-align:center; min-width:110px;">'
            f'<div style="color:#94a3b8; font-size:9.5px; font-weight:bold; letter-spacing:0.5px;">CONFLUENCE</div>'
            f'<div style="color:{conf_data["txt_col"]}; font-size:24px; font-weight:900; font-family:monospace; line-height:1.1;">{conf_data["total_score"]:+d}</div>'
            f'</div>'
            f'<div>'
            f'<div style="color:{conf_data["txt_col"]}; font-size:14px; font-weight:bold;">{conf_data["level"]}</div>'
            f'<div style="color:#cbd5e1; font-size:11px; margin-top:3px; max-width:440px; line-height:1.4;">{conf_data["tactics"]}</div>'
            f'</div>'
            f'</div>'
            f'<div style="display:flex; gap:8px; flex:1; justify-content:flex-end; flex-wrap:wrap;">'
            f'{"".join(sub_badges)}'
            f'</div>'
            f'</div>'
            f'</div>'
        )

    banner_html = (
        f'<div style="background-color:#0d1117; border:1px solid #30363d; border-radius:8px; padding:10px 16px; margin-bottom:12px; font-family:sans-serif;">'
        f'<div style="display:flex; justify-content:space-between; align-items:center;">'
        f'<div>'
        f'<span style="color:#94a3b8; font-size:12px; margin-right:8px;">三雲趨勢:</span>'
        f'<span style="color:{trend_col}; font-weight:bold; font-size:13px; margin-right:14px;">{trend_title}</span>'
        f'<span style="color:#cbd5e1; font-size:11px;">● 快雲 · 中雲 · 慢雲 (雲色由淺至深：快 → 中 → 慢)</span>'
        f'</div>'
        f'<div>'
        f'<span style="color:#94a3b8; font-size:11px;">主要支撐 / 阻力: <b style="color:#ffffff;">青綠實線=支撐防守 · 黃/橙虛線=阻力壓制</b></span>'
        f'</div>'
        f'</div>'
        f'{sr_pills_html}'
        f'{confluence_card_html}'
        f'</div>'
    )
    st.markdown(banner_html, unsafe_allow_html=True)

    # =========================================================================
    # 5.1 📖 四維共振計分說明與交易室戰術指引 (可收合拉掣)
    # =========================================================================
    with st.expander("📖 點擊展開／收合：四維共振系統 (Confluence Score) 計分說明與交易室戰術指引", expanded=False):
        expander_md = """
#### 📐 關於 4 組分數與最高分設計
整套四維共振系統的**理論最高滿分是 $+100$ 分**（最低為 $-100$ 分），由 4 個核心維度各自貢獻 **最高 25 分** 組成：

| # | 維度名稱 | 衡量指標與核心依據 | 最高滿分 | 當前得分 | 盤面現況診斷 |
| :-: | :--- | :--- | :-: | :-: | :--- |
| **1** | **趨勢雲帶** | Eric's Three Cloud 快中慢三雲排列結構 | **$+25$ 分** | `0 分` | 股價自 234 回檔，三雲處於收斂整理階段 |
| **2** | **量能爆發** | Volume Plus 爆量倍數（vs MA20）與多空方向 | **$+25$ 分** | `0 分` | 成交量約為 0.9x MA20，屬於健康量縮回踩，未見恐慌拋壓 |
| **3** | **幾何動能** | Momentum Wave 極性（10分）+ SL Angle 角度（15分） | **$+25$ 分** | `0 分` | 動能柱微正、角度 $-21.7^\circ$（溫和回調），多空正負相抵 |
| **4** | **時空幾何** | 2R 正弦波轉折（15分）+ S1 支撐防守緩衝（10分） | **$+25$ 分** | **`+25 分 (滿分)`** | **正弦波確認「谷底回升」，且股價穩守 S1 支撐線上方** |
| **Σ** | **綜合總分** | **四維累加總分（-100 ~ +100）** | **`+100 分`** | **`+25 分`** | **🟢 偏多共振蓄勢 (逢低佈局)** |

---

#### 🎯 總分區間與交易室指令對照
- **$+60 \sim +100$ 分【🔥 強烈多頭共振】**：四維全線爆發，具備主升段特徵，戰略積極做多；
- **$+20 \sim +59$ 分【🟢 偏多共振蓄勢】（當前狀態）**：時空維度已拿滿 25 分（跌不動了，時間見底），處於回測 S1 支撐的左側/次低點黃金佈局區；
- **$-19 \sim +19$ 分【⚖️ 多空中立平衡】**：多空信號互抵，觀望等待方向；
- **$-20 \sim -59$ 分【🟡 偏空承壓回調】**：空方動能佔優，反彈減倉；
- **$-60 \sim -100$ 分【🔴 強烈空頭共振】**：破位大跌且帶量，嚴禁抄底。
        """
        st.markdown(expander_md)

    # =========================================================================
    # 6. Micro-Domain 緊湊副圖架構 (主圖垂直空間釋放至 56.5% 以上)
    # =========================================================================
    layers = []
    if show_harmonic and harmonic_data:
        layers.append(('harmonic', 0.090))
    if show_sl_angle and sl_data:
        layers.append(('sl_angle', 0.065))
    if show_cycle and cycle_data:
        layers.append(('cycle', 0.075))
    if show_mome_wave and mome_data:
        layers.append(('momentum', 0.080))
    if show_vol_plus and vol_data:
        layers.append(('volume', 0.075))

    current_bottom = 0.0
    gap = 0.010
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
            y_axes_config[f'yaxis{y_idx}']['gridcolor'] = 'rgba(48, 54, 61, 0.20)'

        current_bottom += height + gap
        y_idx += 1

    price_domain = [round(current_bottom, 3), 1.0]
    axes_map['price'] = 'y'
    y_axes_config['yaxis'] = dict(
        domain=price_domain, anchor='x', side='right',
        showgrid=True, gridcolor='rgba(48, 54, 61, 0.35)', color='#8b949e', **spike_common
    )

    bottom_ax = axes_map[layers[0][0]] if layers else 'y'

    if show_harmonic and harmonic_data:
        chart_end_final = harmonic_data['chart_end_date']
    elif gann_box:
        chart_end_final = gann_box['box_end_date']
    else:
        chart_end_final = chart_end_base

    y_axes_config['xaxis'] = dict(
        anchor=bottom_ax,
        range=[chart_start_dt, chart_end_final],
        showgrid=True, gridcolor='rgba(48, 54, 61, 0.35)', color='#8b949e',
        rangeslider=dict(visible=False), **spike_common
    )

    chart_height = max(860, 560 + len(layers) * 110)
    fig = go.Figure()
    fig._grid_ref = build_grid_ref(1 + len(layers))

    # ==========================================
    # --- 圖層 1: K 線主圖 + 三雲 + S/R + Gann Box ---
    # ==========================================

    # A. ☁️ Eric's Three Cloud
    if cloud_data:
        dates_arr = df_chart.index

        slow_traces = get_cloud_polygon_segments(
            dates_arr, cloud_data['slow_lead'], cloud_data['slow_lag'],
            bull_fill='rgba(21, 128, 61, 0.40)', bear_fill='rgba(190, 18, 60, 0.38)'
        )
        for t in slow_traces:
            fig.add_trace(t, row=1, col=1)

        mid_traces = get_cloud_polygon_segments(
            dates_arr, cloud_data['mid_lead'], cloud_data['mid_lag'],
            bull_fill='rgba(34, 197, 94, 0.46)', bear_fill='rgba(244, 63, 94, 0.44)'
        )
        for t in mid_traces:
            fig.add_trace(t, row=1, col=1)

        fast_traces = get_cloud_polygon_segments(
            dates_arr, cloud_data['fast_lead'], cloud_data['fast_lag'],
            bull_fill='rgba(74, 222, 128, 0.55)', bear_fill='rgba(255, 99, 132, 0.52)'
        )
        for t in fast_traces:
            fig.add_trace(t, row=1, col=1)

    # B. 📐 Auto Gann Range (天地分流避讓)
    if gann_box:
        b_st = gann_box['box_start_date']
        b_ed = gann_box['box_end_date']
        b_top = gann_box['box_top']
        b_bot = gann_box['box_bottom']

        fig.add_shape(
            type="rect", xref="x", yref=axes_map['price'],
            x0=b_st, x1=b_ed, y0=b_bot, y1=b_top,
            line=dict(color="rgba(255, 255, 255, 0.85)", width=1.8),
            fillcolor="rgba(15, 23, 42, 0.30)", layer="below"
        )

        fig.add_annotation(
            xref="x", yref=axes_map['price'], x=b_st, y=b_top,
            text="<b>AUTO GANN RANGE</b>",
            bgcolor="#0f172a", bordercolor="#ffffff", borderwidth=1.5, borderpad=4,
            font=dict(color="#ffffff", size=9.5, family="monospace"),
            showarrow=False, xanchor="left", yanchor="bottom"
        )

        for h_val, h_pct in [(gann_box['P25'], '25%'), (gann_box['P50'], '50%'), (gann_box['P75'], '75%')]:
            fig.add_shape(type="line", xref="x", yref=axes_map['price'], x0=b_st, x1=b_ed, y0=h_val, y1=h_val, line=dict(color="rgba(255, 255, 255, 0.6)", width=1.4, dash="dash"))

        has_harmonic_zone = bool(show_harmonic and harmonic_data)
        for t_dt, t_label in [(gann_box['T25'], '25%'), (gann_box['T50'], '50% 中軸'), (gann_box['T75'], '75%')]:
            fig.add_shape(type="line", xref="x", yref=axes_map['price'], x0=t_dt, x1=t_dt, y0=b_bot, y1=b_top, line=dict(color="#eab308", width=1.6, dash="dash"))

            if not has_harmonic_zone:
                fig.add_annotation(
                    xref="x", yref=axes_map['price'], x=t_dt, y=b_bot,
                    text=f"<b>{t_label}<br>{t_dt.strftime('%m/%d')}</b>",
                    bgcolor="#0f172a", bordercolor="#eab308", borderwidth=1.2, borderpad=3,
                    font=dict(color="#fde047", size=8.5, family="monospace"),
                    showarrow=False, xanchor="center", yanchor="top"
                )
            else:
                fig.add_annotation(
                    xref="x", yref=axes_map['price'], x=t_dt, y=b_top,
                    text=f"<b>{t_label} {t_dt.strftime('%m/%d')}</b>",
                    bgcolor="#0f172a", bordercolor="#eab308", borderwidth=1.2, borderpad=3,
                    font=dict(color="#fde047", size=8.5, family="monospace"),
                    showarrow=False, xanchor="center", yanchor="bottom"
                )

        for ray in gann_box['rays']:
            fig.add_trace(go.Scatter(
                x=ray['x'], y=ray['y'], mode='lines',
                line=dict(color=ray['color'], width=ray['width'], dash=ray['dash']),
                yaxis=axes_map['price'], showlegend=False, hoverinfo='skip'
            ), row=1, col=1)

    # C. 📈 主圖 K 線
    fig.add_trace(go.Candlestick(
        x=df_chart.index,
        open=df_chart['Open'], high=df_chart['High'], low=df_chart['Low'], close=df_chart['Close'],
        name=f'{symbol} K線',
        increasing_line_color='#00e676', decreasing_line_color='#ff5252',
        increasing_fillcolor='#00e676', decreasing_fillcolor='#ff5252',
        yaxis=axes_map['price'], showlegend=False
    ), row=1, col=1)

    # D. ⚖️ 主要支阻長線 (極性翻轉 S-R Flip + 26px 防碰撞鬆弛演算法)
    if sr_levels and show_sr_rays:
        right_boundary_dt = chart_end_final

        # 偵測 Eric's Channel 通道中軸數值 (若有)
        channel_val = None
        if cloud_data:
            channel_val = cloud_data.get('channel_val', cloud_data.get('channel_price', None))
            if channel_val is None and 'mid_lead' in cloud_data and hasattr(cloud_data['mid_lead'], 'iloc'):
                channel_val = float(cloud_data['mid_lead'].iloc[-1])

        all_p = [
            float(df_chart['Low'].min()), float(df_chart['High'].max()),
            sr_data['last_close']
        ] + [it['val'] for it in sr_levels]
        if gann_box:
            all_p.extend([gann_box['box_top'], gann_box['box_bottom']])
        if channel_val is not None:
            all_p.append(float(channel_val))

        p_min_est = min(all_p)
        p_max_est = max(all_p)

        label_collision_items = [{'id': it['id'], 'price': it['val']} for it in sr_levels]
        label_collision_items.append({'id': 'close', 'price': sr_data['last_close']})

        # 🌟 將通道中軸真正加入防碰撞項目陣列，與現價及 S/R 標籤同步避讓
        if channel_val is not None:
            label_collision_items.append({'id': 'channel', 'price': float(channel_val)})

        label_shifts = resolve_label_collisions(
            label_collision_items,
            min_gap_px=26,
            total_height_px=int(chart_height * (price_domain[1] - price_domain[0])),
            p_min=p_min_est,
            p_max=p_max_est
        )

        for it in sr_levels:
            fig.add_shape(
                type="line", xref="x", yref=axes_map['price'],
                x0=it['date'], x1=right_boundary_dt, y0=it['val'], y1=it['val'],
                line=dict(color=it['color'], width=it['width'], dash=it['dash'])
            )
            fig.add_annotation(
                xref="x domain", yref=axes_map['price'],
                x=0.998, y=it['val'],
                yshift=label_shifts.get(it['id'], 0),
                text=f"<b>{it['display_name']} │ {it['val']:.2f}</b>",
                bgcolor=it['bg'],
                bordercolor=it['border'],
                borderwidth=1.5,
                borderpad=4,
                font=dict(color=it['font_col'], size=10, family="Arial, sans-serif"),
                showarrow=False, xanchor="right", yanchor="middle"
            )

        # 🟩 即時現價基準線與實心綠膠囊 (接入防碰撞偏移)
        last_c = sr_data['last_close']
        fig.add_shape(
            type="line", xref="paper", yref=axes_map['price'],
            x0=0, x1=1, y0=last_c, y1=last_c,
            line=dict(color="rgba(0, 230, 118, 0.75)", width=1.2, dash="dot")
        )
        fig.add_annotation(
            xref="x domain", yref=axes_map['price'],
            x=0.998, y=last_c,
            yshift=label_shifts.get('close', 0),
            text=f"<b>{last_c:.2f}</b>",
            bgcolor="#065f46", bordercolor="#00e676", borderwidth=1.5, borderpad=4,
            font=dict(color="#ffffff", size=10.5, family="monospace"),
            showarrow=False, xanchor="right", yanchor="middle"
        )

        # 🟥 若存在 Eric's Channel 數值，渲染專屬通道標籤並應用防碰撞位移
        if channel_val is not None:
            fig.add_shape(
                type="line", xref="paper", yref=axes_map['price'],
                x0=0, x1=1, y0=channel_val, y1=channel_val,
                line=dict(color="rgba(239, 68, 68, 0.70)", width=1.2, dash="dash")
            )
            fig.add_annotation(
                xref="x domain", yref=axes_map['price'],
                x=0.998, y=channel_val,
                yshift=label_shifts.get('channel', 0),
                text=f"<b>Eric's Channel {channel_val:.2f}</b>",
                bgcolor="#b91c1c", bordercolor="#ef4444", borderwidth=1.5, borderpad=4,
                font=dict(color="#ffffff", size=10, family="Arial, sans-serif"),
                showarrow=False, xanchor="right", yanchor="middle"
            )

    # E. 注入主圖右側推算暗區
    if show_harmonic and harmonic_data and harmonic_comp:
        harmonic_comp.inject_future_projection_zone(fig, harmonic_data, yaxis_name=axes_map['price'])

    # ==========================================
    # --- 圖層 2: 📊 Volume Plus (異常量能柱 & MA20 標籤) ---
    # ==========================================
    if show_vol_plus and vol_data:
        v_yax = axes_map['volume']
        fig.add_trace(go.Bar(
            x=df_chart.index, y=vol_data['volume'],
            marker_color=vol_data['vol_colors'], name='Volume Plus',
            showlegend=False, opacity=0.85, yaxis=v_yax
        ))
        fig.add_trace(go.Scatter(
            x=df_chart.index, y=vol_data['vol_ma20'],
            mode='lines', line=dict(color='#38bdf8', width=1.5),
            name='Volume Plus MA20', yaxis=v_yax, showlegend=False
        ))

        fig.add_annotation(
            xref="x domain", yref=f"{v_yax} domain",
            x=0.998, y=0.5,
            text=f"<b>Volume Plus MA20 │ {vol_ma_str}</b>",
            bgcolor="#0284c7",
            bordercolor="#38bdf8",
            borderwidth=1.5,
            borderpad=4,
            font=dict(color="#ffffff", size=9.5, family="monospace"),
            showarrow=False, xanchor="right", yanchor="middle"
        )

        fig.add_annotation(
            xref="paper", yref=f"{v_yax} domain",
            x=0.015, y=0.90, text=f"<b>Volume Plus</b> · MA20 {vol_data['last_ma']:,.0f}",
            bgcolor="rgba(15, 23, 42, 0.85)", font=dict(color="#38bdf8", size=9.5, family="monospace"),
            showarrow=False, xanchor="left"
        )

    # ==========================================
    # --- 圖層 3: 🌊 Momentum Wave (當勢動能波) ---
    # ==========================================
    if show_mome_wave and mome_data:
        m_yax = axes_map['momentum']
        fig.add_trace(go.Bar(
            x=df_chart.index, y=mome_data['momentum_val'],
            marker_color=mome_data['wave_colors'], name='動能波',
            showlegend=False, yaxis=m_yax
        ))
        fig.add_shape(type="line", xref="paper", yref=m_yax, x0=0, x1=1, y0=0, y1=0, line=dict(color="rgba(148, 163, 184, 0.5)", width=1.0))
        fig.add_trace(go.Scatter(
            x=df_chart.index, y=[0] * len(df_chart),
            mode='markers', marker=dict(size=5, color=mome_data['dot_colors']),
            name='蓄勢/爆發', showlegend=False, yaxis=m_yax, hoverinfo='skip'
        ))

        last_m_val = mome_data['last_val']
        m_badge_bg = "#166534" if last_m_val >= 0 else "#991b1b"
        fig.add_annotation(
            xref="x domain", yref=m_yax,
            x=0.995, y=last_m_val, text=f"<b>動能波 {last_m_val:+.2f}</b>",
            bgcolor=m_badge_bg, bordercolor="#ffffff", borderpad=3,
            font=dict(color="#ffffff", size=9, family="monospace"),
            showarrow=False, xanchor="right"
        )
        fig.add_annotation(
            xref="paper", yref=f"{m_yax} domain",
            x=0.015, y=0.90, text="<b>動能波 — 當勢與動能波</b> · <span style='color:#facc15;'>● 黃點=蓄勢</span> <span style='color:#00e5ff;'>● 青點=爆發</span>",
            bgcolor="rgba(15, 23, 42, 0.85)", font=dict(color="#ffffff", size=9.5, family="monospace"),
            showarrow=False, xanchor="left"
        )

    # =========================================================================
    # --- 圖層 4: TIME CYCLE (江恩八度音階同頻諧振 2R 正弦波) ---
    # =========================================================================
    if show_cycle and cycle_data:
        c_yax = axes_map['cycle']

        fig.add_trace(go.Scatter(
            x=cycle_data['interp_dates'], y=cycle_data['pos_cycle'],
            mode='lines', line=dict(color='#38bdf8', width=2.5),
            name='Cycle Peak Phase', yaxis=c_yax, showlegend=False
        ))
        fig.add_trace(go.Scatter(
            x=cycle_data['interp_dates'], y=cycle_data['neg_cycle'],
            mode='lines', line=dict(color='#facc15', width=2.5),
            name='Cycle Trough Phase', yaxis=c_yax, showlegend=False
        ))

        if 'sub_cycle_vals' in cycle_data:
            fig.add_trace(go.Scatter(
                x=cycle_data['interp_dates'], y=cycle_data['sub_cycle_vals'],
                mode='lines', line=dict(color='rgba(147, 197, 253, 0.40)', width=1.2, dash='dot'),
                name='Octave Harmonic (R)', yaxis=c_yax, showlegend=False, hoverinfo='skip'
            ))

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

        hud_cycle = (
            f"<b>TIME CYCLE 同頻諧振</b> 2R={cycle_data['cycle_bars']}B (基頻 R={cycle_data['r_period']}B)  |  "
            f"<span style='background:#78350f; color:#fde68a; padding:1px 5px; border-radius:3px;'><b>{cycle_data['window_status']}</b></span>  |  "
            f"相位 <b>{cycle_data['current_phase_deg']}°</b>  |  "
            f"距轉折 <b>{cycle_data['next_turn_bars']}B</b>"
            f"{chip_guard_html}"
        )
        fig.add_annotation(
            xref="paper", yref=f"{c_yax} domain",
            x=0.015, y=0.92, text=hud_cycle,
            bgcolor="rgba(15, 23, 42, 0.85)", bordercolor="#38bdf8", borderwidth=1, borderpad=4,
            font=dict(color="#ffffff", size=10, family="monospace"), showarrow=False, xanchor="left"
        )

    # =========================================================================
    # --- 圖層 5: SL ANGLE (ATR-14 波動率標準化幾何動能線) ---
    # =========================================================================
    if show_sl_angle and sl_data:
        sl_y = axes_map['sl_angle']

        fig.add_trace(go.Scatter(
            x=sl_data['interp_dates'], y=sl_data['pos_angles'],
            mode='lines', line=dict(color='#22c55e', width=2.2),
            name='SL Angle Bullish', yaxis=sl_y, showlegend=False
        ))
        fig.add_trace(go.Scatter(
            x=sl_data['interp_dates'], y=sl_data['neg_angles'],
            mode='lines', line=dict(color='#f43f5e', width=2.2),
            name='SL Angle Bearish', yaxis=sl_y, showlegend=False
        ))

        for ang_val, col_l, dash_t in [
            (60, "rgba(244, 63, 94, 0.35)", "dot"),
            (45, "rgba(250, 204, 21, 0.45)", "dash"),
            (0, "rgba(148, 163, 184, 0.35)", "solid"),
            (-45, "rgba(250, 204, 21, 0.45)", "dash"),
            (-60, "rgba(244, 63, 94, 0.35)", "dot")
        ]:
            fig.add_shape(
                type="line", xref="paper", yref=sl_y,
                x0=0, x1=1, y0=ang_val, y1=ang_val,
                line=dict(color=col_l, width=1.0, dash=dash_t)
            )

        last_a = sl_data['last_angle']
        badge_bg = sl_data['status_color']
        fig.add_annotation(
            xref="x domain", yref=sl_y,
            x=0.995, y=last_a,
            text=f"<b>SL {last_a:+.1f}°</b>",
            bgcolor=badge_bg,
            bordercolor="#ffffff",
            borderwidth=1.2,
            borderpad=3,
            font=dict(color="#ffffff", size=9, family="monospace"),
            showarrow=False, xanchor="right"
        )

        hud_sl = (
            f"<b>SL ANGLE 幾何動能 (ATR-14 標準化)</b>  |  "
            f"<span style='background:#1e293b; color:{sl_data['status_color']}; border:1px solid {sl_data['status_color']}; padding:1px 6px; border-radius:3px;'><b>{sl_data['angle_status']}</b></span>  |  "
            f"當前角度 <b>{sl_data['last_angle']:+.1f}°</b> (1x1基準 ±45°)  |  "
            f"ATR(14): <b>{sl_data['last_atr']}</b>"
        )
        fig.add_annotation(
            xref="paper", yref=f"{sl_y} domain",
            x=0.015, y=0.90, text=hud_sl,
            bgcolor="rgba(15, 23, 42, 0.85)", bordercolor="#64748b", borderwidth=1, borderpad=3,
            font=dict(color="#ffffff", size=9.5, family="monospace"), showarrow=False, xanchor="left"
        )

    # ==========================================
    # --- 圖層 6: ⏳ 諧波時間跳躍弧 (Harmonic Arcs) ---
    # ==========================================
    if show_harmonic and harmonic_data and harmonic_comp:
        harmonic_comp.inject_harmonic_arcs_traces(fig, harmonic_data, yaxis_name=axes_map['harmonic'])

    # ===================================================
    # 7. 整合佈局 (十字線全軸貫通 + 安全邊界)
    # ===================================================
    fig.update_layout(
        template='plotly_dark',
        paper_bgcolor='#0a0e14',
        plot_bgcolor='#0a0e14',
        xaxis_rangeslider_visible=False,
        hovermode='x',
        hoverlabel=dict(bgcolor='#1f293d', font_size=12, font_family='Arial'),
        height=chart_height,
        margin=dict(l=10, r=68, t=18, b=25),
        modebar=dict(
            orientation='h',
            bgcolor='rgba(15, 23, 42, 0.65)',
            color='#94a3b8',
            activecolor='#38bdf8'
        ),
        newshape=dict(line=dict(color="#facc15", width=1.5, dash="dash")),
        **y_axes_config
    )

    st.plotly_chart(
        fig,
        use_container_width=True,
        config={
            'displayModeBar': 'hover',
            'scrollZoom': True,
            'displaylogo': False,
            'modeBarButtonsToAdd': ['drawline', 'eraseshape']
        }
    )

    # 渲染底部未來倒數矩陣看板
    if show_harmonic and harmonic_data and harmonic_comp and hasattr(harmonic_comp, "render_harmonic_countdown_matrix_ui"):
        harmonic_comp.render_harmonic_countdown_matrix_ui(harmonic_data)