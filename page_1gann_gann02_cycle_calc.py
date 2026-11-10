"""
Filename: page_1gann_gann02_cycle_calc.py
Description: 🌊 Time Cycle 正弦波震盪器 (100% 真實歷史大底錨定版)
             與 SL Angle 幾何動能角度 (綠/紅雙色) 運算引擎
- 100% 真實量化數據：波谷 (-100) 嚴格動態錨定於個股真實歷史最低點 (Swing Low: idxmin)
- SL Angle 動能角度：嚴格依據 14 週期一階多項式線性回歸 (polyfit) 動態擬合
- 徹底修復 (0.0 - y0) 減號與 2.0 * np.pi 乘號損壞
- 兼容最新版 Pandas DatetimeIndex 索引拼接
"""

import numpy as np
import pandas as pd


def create_seamless_bicolor_curve(dates, values):
    """
    精確計算正負零軸交叉點的時間戳記，確保雙色曲線完全閉合、無縫銜接
    """
    ts = pd.to_datetime(dates)
    n = len(values)
    if n == 0:
        return ts, [], []

    interp_dates = []
    interp_vals = []

    for i in range(n - 1):
        interp_dates.append(ts[i])
        interp_vals.append(float(values[i]))

        y0 = float(values[i])
        y1 = float(values[i + 1])
        if (y0 > 0 and y1 < 0) or (y0 < 0 and y1 > 0):
            t0 = ts[i].timestamp()
            t1 = ts[i + 1].timestamp()
            # 精確計算零軸交叉時間點
            t_zero = t0 + (0.0 - y0) * (t1 - t0) / (y1 - y0)
            zero_date = pd.to_datetime(t_zero, unit='s')
            interp_dates.append(zero_date)
            interp_vals.append(0.0)

    interp_dates.append(ts[-1])
    interp_vals.append(float(values[-1]))

    pos_vals = [v if v >= 0.0 else np.nan for v in interp_vals]
    neg_vals = [v if v <= 0.0 else np.nan for v in interp_vals]

    return interp_dates, pos_vals, neg_vals


def compute_time_cycle(df: pd.DataFrame, cycle_bars: int = 150, shift_bars: int = 25, future_days: int = 85):
    """
    計算副圖一：TIME CYCLE 正弦波震盪指標 (100% 真實大底時間錨定)
    向前推演 85 天貫穿未來時空，自動捕捉歷史與未來的 PEAK 和 TROUGH 谷底轉折，
    並精確推算下一個公曆具體轉勢日 (例如: 10月19日 ±1天)
    """
    if df is None or len(df) < 15:
        return None

    hist_dates = pd.to_datetime(df.index)
    n_hist = len(hist_dates)

    # 產生未來日期序列 (向未來延伸 85 天)
    last_date = hist_dates[-1]
    future_dates = pd.date_range(last_date + pd.Timedelta(days=1), periods=future_days, freq='D')
    all_dates = hist_dates.union(future_dates)
    n_total = len(all_dates)

    # 🌟 真實江恩時間錨定：鎖定個股在當前歷史區間內的真實大底 (Swing Low)
    if 'Low' in df.columns:
        anchor_date = df['Low'].idxmin()
    else:
        anchor_date = df['Close'].idxmin()

    # 計算相對於真實大底的時間跨度，徹底根除相位漂移
    delta_days = np.array([(d - anchor_date).days for d in all_dates], dtype=float)
    phase = (-np.pi / 2.0) + (2.0 * np.pi * delta_days / float(cycle_bars))
    cycle_val = 100.0 * np.sin(phase)

    current_val = float(cycle_val[n_hist - 1])
    current_phase_deg = int(np.rad2deg(phase[n_hist - 1]) % 360)

    # 捕捉波峰 (PEAK) 與波谷 (TROUGH)
    peaks = []
    troughs = []
    peaks_raw = []
    troughs_raw = []

    for i in range(2, n_total - 2):
        if cycle_val[i] > cycle_val[i - 1] and cycle_val[i] >= cycle_val[i + 1] and cycle_val[i] > 60:
            peaks.append((all_dates[i], float(cycle_val[i])))
            peaks_raw.append((all_dates[i], float(cycle_val[i]), i))
        if cycle_val[i] < cycle_val[i - 1] and cycle_val[i] <= cycle_val[i + 1] and cycle_val[i] < -60:
            troughs.append((all_dates[i], float(cycle_val[i])))
            troughs_raw.append((all_dates[i], float(cycle_val[i]), i))

    # 精準推算下一個未來的具體公曆轉勢日
    future_turns = []
    for d, val, i in peaks_raw:
        if i >= n_hist - 1:
            future_turns.append((d, "頂峰轉勢", i, "PEAK"))
    for d, val, i in troughs_raw:
        if i >= n_hist - 1:
            future_turns.append((d, "谷底轉勢", i, "TROUGH"))

    future_turns.sort(key=lambda x: x[2])

    if future_turns:
        next_dt, next_type, next_idx, next_tag = future_turns[0]
        next_turn_bars = max(0, next_idx - (n_hist - 1))
        next_turn_date_str = f"{next_dt.month}月{next_dt.day}日"
    else:
        next_turn_bars = max(1, int(cycle_bars / 4.0))
        next_dt = last_date + pd.Timedelta(days=next_turn_bars)
        next_type = "週期轉勢"
        next_turn_date_str = f"{next_dt.month}月{next_dt.day}日"

    # 當前階段基礎狀態判定
    if current_val <= -70:
        base_status = "谷底窗口"
        status_color = "#f59e0b"
    elif current_val >= 70:
        base_status = "頂峰窗口"
        status_color = "#38bdf8"
    elif current_val > 0:
        base_status = "回落階段" if np.cos(phase[n_hist - 1]) < 0 else "上升階段"
        status_color = "#38bdf8"
    else:
        base_status = "回升階段" if np.cos(phase[n_hist - 1]) > 0 else "築底階段"
        status_color = "#facc15"

    window_status = f"{base_status} · 轉勢日:{next_turn_date_str}±1天"
    interp_dates, pos_cycle, neg_cycle = create_seamless_bicolor_curve(all_dates, cycle_val)

    return {
        'cycle_val': cycle_val,
        'all_dates': all_dates,
        'interp_dates': interp_dates,
        'pos_cycle': pos_cycle,
        'neg_cycle': neg_cycle,
        'current_val': current_val,
        'current_phase_deg': current_phase_deg,
        'window_status': window_status,
        'status_color': status_color,
        'next_turn_bars': next_turn_bars,
        'next_turn_date': next_dt,
        'next_turn_date_str': next_turn_date_str,
        'next_turn_type': next_type,
        'peaks': peaks,
        'troughs': troughs,
        'anchor_date': anchor_date
    }


def compute_sl_angle(df: pd.DataFrame, period: int = 14):
    """
    計算副圖二：SL ANGLE — 幾何角度動能擺動指標 (100% 真實價格回歸運算)
    """
    if df is None or len(df) < period:
        return None

    closes = df['Close'].values
    n = len(closes)
    angles = np.zeros(n)

    std_p = np.std(closes[-min(60, n):])
    if std_p == 0:
        std_p = 1.0

    for i in range(period, n):
        y = closes[i - period:i + 1]
        y_norm = (y - np.mean(y)) / std_p
        x = np.arange(len(y))
        slope, _ = np.polyfit(x, y_norm, 1)
        deg = np.rad2deg(np.arctan(slope * 10.0))
        angles[i] = np.clip(deg, -90.0, 90.0)

    angles[:period] = angles[period]
    last_angle = float(angles[-1])

    interp_dates, pos_angles, neg_angles = create_seamless_bicolor_curve(df.index, angles)

    return {
        'angles': angles,
        'interp_dates': interp_dates,
        'pos_angles': pos_angles,
        'neg_angles': neg_angles,
        'last_angle': last_angle
    }