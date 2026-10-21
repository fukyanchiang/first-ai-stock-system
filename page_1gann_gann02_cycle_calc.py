"""
Filename: page_1gann_gann02_cycle_calc.py
Description: 🌊 Time Cycle 正弦波震盪器 (藍/黃雙色，推演至 2027 年，含完整 PEAK 與 TROUGH 圓點)
             與 SL Angle 幾何動能角度 (綠/紅雙色) 運算引擎
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
    計算副圖一：TIME CYCLE 正弦波震盪指標
    向前推演 85 天貫穿未來時空，自動捕捉歷史與未來的 PEAK 和 TROUGH 谷底轉折
    """
    if df is None or len(df) < 15:
        return None

    hist_dates = pd.to_datetime(df.index)
    n_hist = len(hist_dates)

    # 產生未來日期序列 (向未來延伸 85 天至翌年年初)
    last_date = hist_dates[-1]
    future_dates = pd.date_range(last_date + pd.Timedelta(days=1), periods=future_days, freq='D')
    all_dates = hist_dates.append(future_dates)
    n_total = len(all_dates)

    bar_indices = np.arange(n_total)
    phase = 2.0 * np.pi * (bar_indices - shift_bars) / cycle_bars
    cycle_val = 100.0 * np.sin(phase)

    current_val = float(cycle_val[n_hist - 1])
    current_phase_deg = int(np.rad2deg(phase[n_hist - 1]) % 360)

    # 當前狀態判斷
    if current_val <= -70:
        window_status = "谷底窗口"
        status_color = "#f59e0b"
    elif current_val >= 70:
        window_status = "頂峰窗口"
        status_color = "#38bdf8"
    elif current_val > 0:
        window_status = "回落階段" if np.cos(phase[n_hist - 1]) < 0 else "上升階段"
        status_color = "#38bdf8"
    else:
        window_status = "回升階段" if np.cos(phase[n_hist - 1]) > 0 else "築底階段"
        status_color = "#facc15"

    next_turn_bars = int(abs(cycle_bars / 4.0 - (bar_indices[n_hist - 1] % (cycle_bars / 2.0))))
    if next_turn_bars <= 0:
        next_turn_bars = int(cycle_bars / 4.0)

    # 捕捉波峰 (PEAK) 與波谷 (TROUGH)
    peaks = []
    troughs = []
    for i in range(2, n_total - 2):
        if cycle_val[i] > cycle_val[i - 1] and cycle_val[i] >= cycle_val[i + 1] and cycle_val[i] > 60:
            peaks.append((all_dates[i], float(cycle_val[i])))
        if cycle_val[i] < cycle_val[i - 1] and cycle_val[i] <= cycle_val[i + 1] and cycle_val[i] < -60:
            troughs.append((all_dates[i], float(cycle_val[i])))

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
        'peaks': peaks,
        'troughs': troughs
    }


def compute_sl_angle(df: pd.DataFrame, period: int = 14):
    """
    計算副圖二：SL ANGLE — 幾何角度動能擺動指標 (正: 翠綠, 負: 玫瑰紅)
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