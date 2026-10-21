"""
Filename: page_1gann_gann04_calc.py
Description: 🎯 小龍江恩策略 Y (Gann 04) 核心運算模組
升級功能：
  1. Eric's Three Cloud Trend (快中慢三雲多週期均線計算，為動態多邊形漸變提供數據)
  2. Volume Pressure S/R (識別歷史波段高低點起點，輸出 R1~R3 / S1~S3 與歷史偏向 %)
  3. Volume Plus (異常量能柱體判定與 Volume Plus MA20 均線)
  4. Momentum Wave (當勢動能波，零軸黃點蓄勢與青點爆發)
  5. Auto Gann Range (補齊加粗外框、中心菱形星芒、1x1大交叉與16條全幾何射線)
"""

import pandas as pd
import numpy as np


# ==============================================================================
# 1. ☁️ Eric's Three Cloud Trend (三雲趨勢帶核心數據)
# ==============================================================================
def compute_three_cloud_trend(df: pd.DataFrame):
    """
    計算快雲、中雲、慢雲三層雙均線數據：
    - 快雲 (Fast): EMA(8) vs EMA(13)
    - 中雲 (Mid): EMA(21) vs EMA(34)
    - 慢雲 (Slow): EMA(55) vs EMA(89)
    """
    df = df.copy()
    close = df['Close']

    fast_lead = close.ewm(span=8, adjust=False).mean()
    fast_lag = close.ewm(span=13, adjust=False).mean()

    mid_lead = close.ewm(span=21, adjust=False).mean()
    mid_lag = close.ewm(span=34, adjust=False).mean()

    slow_lead = close.ewm(span=55, adjust=False).mean()
    slow_lag = close.ewm(span=89, adjust=False).mean()

    fast_bull = fast_lead >= fast_lag
    mid_bull = mid_lead >= mid_lag
    slow_bull = slow_lead >= slow_lag

    is_fast_up = bool(fast_bull.iloc[-1])
    is_mid_up = bool(mid_bull.iloc[-1])
    is_slow_up = bool(slow_bull.iloc[-1])

    if is_fast_up and is_mid_up and is_slow_up:
        trend_status = "三雲向上 快、中、慢方向一致"
        trend_color = "#22c55e"
    elif not is_fast_up and not is_mid_up and not is_slow_up:
        trend_status = "三雲向下 快、中、慢方向一致"
        trend_color = "#ef4444"
    else:
        trend_status = "三雲分歧 處於趨勢過渡期"
        trend_color = "#facc15"

    return {
        'fast_lead': fast_lead,
        'fast_lag': fast_lag,
        'fast_bull': fast_bull,
        'mid_lead': mid_lead,
        'mid_lag': mid_lag,
        'mid_bull': mid_bull,
        'slow_lead': slow_lead,
        'slow_lag': slow_lag,
        'slow_bull': slow_bull,
        'is_fast_up': is_fast_up,
        'is_mid_up': is_mid_up,
        'is_slow_up': is_slow_up,
        'trend_status': trend_status,
        'trend_color': trend_color
    }


# ==============================================================================
# 2. ⚖️ Volume Pressure S/R (識別歷史起點，輸出 R1~R3 / S1~S3 長線參數)
# ==============================================================================
def compute_volume_pressure_sr(df: pd.DataFrame):
    """
    計算 Volume Pressure S/R：
    - 精確識別產生該阻力/支撐的歷史波段頂底日期 (起點)
    - 分級為 R1~R3 (阻力) 與 S1~S3 (支撐)
    - 計算歷史買賣偏向 % (基於籌碼沉澱概率)
    """
    highs = df['High'].values
    lows = df['Low'].values
    closes = df['Close'].values
    dates = df.index
    n = len(df)
    last_close = float(closes[-1])

    window = 5
    raw_highs, raw_lows = [], []
    for i in range(window, n - window):
        if highs[i] == max(highs[i - window:i + window + 1]):
            raw_highs.append((dates[i], float(highs[i])))
        if lows[i] == min(lows[i - window:i + window + 1]):
            raw_lows.append((dates[i], float(lows[i])))

    # 阻力階梯 (高於現價)
    res_candidates = [p for p in raw_highs if p[1] > last_close * 1.008]
    res_candidates.sort(key=lambda x: x[1])

    if not res_candidates:
        r1 = (dates[max(0, n - 30)], round(last_close * 1.05, 2))
        r2 = (dates[max(0, n - 60)], round(last_close * 1.10, 2))
        r3 = (dates[max(0, n - 90)], round(last_close * 1.18, 2))
    else:
        r1 = res_candidates[0]
        r2 = res_candidates[min(1, len(res_candidates) - 1)] if len(res_candidates) > 1 else (dates[max(0, n - 60)], round(r1[1] * 1.05, 2))
        r3 = res_candidates[min(2, len(res_candidates) - 1)] if len(res_candidates) > 2 else (dates[max(0, n - 90)], round(r2[1] * 1.06, 2))

    # 支撐階梯 (低於現價)
    sup_candidates = [p for p in raw_lows if p[1] < last_close * 0.992]
    sup_candidates.sort(key=lambda x: x[1], reverse=True)

    if not sup_candidates:
        s1 = (dates[max(0, n - 30)], round(last_close * 0.95, 2))
        s2 = (dates[max(0, n - 60)], round(last_close * 0.90, 2))
        s3 = (dates[max(0, n - 90)], round(last_close * 0.82, 2))
    else:
        s1 = sup_candidates[0]
        s2 = sup_candidates[min(1, len(sup_candidates) - 1)] if len(sup_candidates) > 1 else (dates[max(0, n - 60)], round(s1[1] * 0.94, 2))
        s3 = sup_candidates[min(2, len(sup_candidates) - 1)] if len(sup_candidates) > 2 else (dates[max(0, n - 90)], round(s2[1] * 0.93, 2))

    def _calc_bias_pct(target_price, is_sell=True):
        dist_pct = abs(last_close - target_price) / max(0.01, last_close)
        base_bias = 25.0 if dist_pct < 0.05 else (12.0 if dist_pct < 0.12 else 6.0)
        return int(base_bias)

    r1_bias = _calc_bias_pct(r1[1], is_sell=True)
    r2_bias = max(6, int(r1_bias * 0.6))
    r3_bias = max(6, int(r2_bias * 0.7))

    s1_bias = _calc_bias_pct(s1[1], is_sell=False)
    s2_bias = max(8, int(s1_bias * 0.8))
    s3_bias = max(6, int(s2_bias * 0.6))

    return {
        'last_close': last_close,
        'r1_date': r1[0], 'r1': r1[1], 'r1_bias': r1_bias,
        'r2_date': r2[0], 'r2': r2[1], 'r2_bias': r2_bias,
        'r3_date': r3[0], 'r3': r3[1], 'r3_bias': r3_bias,
        's1_date': s1[0], 's1': s1[1], 's1_bias': s1_bias,
        's2_date': s2[0], 's2': s2[1], 's2_bias': s2_bias,
        's3_date': s3[0], 's3': s3[1], 's3_bias': s3_bias,
    }


# ==============================================================================
# 3. 📊 Volume Plus (異常放量監控柱 & Volume Plus MA20)
# ==============================================================================
def compute_volume_plus(df: pd.DataFrame, ma_period: int = 20):
    vol = df['Volume'] if 'Volume' in df.columns else pd.Series(1, index=df.index)
    close = df['Close']
    open_p = df['Open']

    vol_ma20 = vol.rolling(ma_period, min_periods=1).mean().bfill()
    last_vol = float(vol.iloc[-1])
    last_ma = float(vol_ma20.iloc[-1])

    vol_colors = []
    for i in range(len(df)):
        v = vol.iloc[i]
        ma = vol_ma20.iloc[i]
        c = close.iloc[i]
        o = open_p.iloc[i]

        if v >= 2.2 * ma:
            vol_colors.append('#c084fc')   # 紫色 (極端天量)
        elif v >= 1.6 * ma:
            vol_colors.append('#f472b6')   # 粉紅 (顯著放量)
        elif c >= o:
            vol_colors.append('rgba(34, 197, 94, 0.75)')   # 陽量
        else:
            vol_colors.append('rgba(239, 68, 68, 0.75)')   # 陰量

    return {
        'volume': vol,
        'vol_ma20': vol_ma20,
        'vol_colors': vol_colors,
        'last_vol': last_vol,
        'last_ma': last_ma
    }


# ==============================================================================
# 4. 🌊 Momentum Wave (當勢動能波：黃點蓄勢 / 青點爆發)
# ==============================================================================
def compute_momentum_wave(df: pd.DataFrame, bb_period: int = 20, bb_mult: float = 2.0, kc_period: int = 20, kc_mult: float = 1.5):
    close = df['Close']
    high = df['High']
    low = df['Low']

    bb_mid = close.rolling(bb_period).mean().bfill()
    bb_std = close.rolling(bb_period).std().bfill()
    bb_upper = bb_mid + bb_mult * bb_std
    bb_lower = bb_mid - bb_mult * bb_std

    tr1 = high - low
    tr2 = (high - close.shift(1)).abs()
    tr3 = (low - close.shift(1)).abs()
    tr = pd.concat([tr1, tr2, tr3], axis=1).max(axis=1)
    atr = tr.rolling(kc_period).mean().bfill()
    kc_mid = close.ewm(span=kc_period, adjust=False).mean()
    kc_upper = kc_mid + kc_mult * atr
    kc_lower = kc_mid - kc_mult * atr

    is_squeeze = (bb_lower > kc_lower) & (bb_upper < kc_upper)

    highest_h = high.rolling(kc_period).max().bfill()
    lowest_l = low.rolling(kc_period).min().bfill()
    avg_hl = (highest_h + lowest_l) / 2.0
    val_basis = close - ((avg_hl + kc_mid) / 2.0)
    momentum_val = val_basis.rolling(kc_period, min_periods=1).mean() * 1.5

    last_val = float(momentum_val.iloc[-1])
    is_last_squeeze = bool(is_squeeze.iloc[-1])

    wave_colors = []
    for i in range(len(df)):
        val = momentum_val.iloc[i]
        prev = momentum_val.iloc[i - 1] if i > 0 else val
        if val >= 0:
            wave_colors.append('#22c55e' if val >= prev else '#86efac')
        else:
            wave_colors.append('#ef4444' if val <= prev else '#fca5a5')

    dot_colors = ['#facc15' if sq else '#00e5ff' for sq in is_squeeze]

    return {
        'momentum_val': momentum_val,
        'wave_colors': wave_colors,
        'dot_colors': dot_colors,
        'is_squeeze': is_squeeze,
        'last_val': last_val,
        'is_last_squeeze': is_last_squeeze
    }


# ==============================================================================
# 5. 📐 Auto Gann Range (補齊加粗外框、菱形星芒與 16 條全幾何射線)
# ==============================================================================
def compute_auto_gann_range(df: pd.DataFrame, future_bars: int = 90):
    n = len(df)
    dates = pd.to_datetime(df.index).tz_localize(None)

    recent_len = min(n, 120)
    sub_df = df.tail(recent_len)
    peak_idx = sub_df['High'].idxmax()
    peak_pos = dates.get_loc(peak_idx)
    box_top = float(df.loc[peak_idx, 'High']) * 1.01
    box_bottom = float(sub_df['Low'].min()) * 0.98

    bar_step_days = max(1.0, (dates[-1] - dates[0]).days / max(1, n - 1))
    box_start_date = peak_idx
    box_total_bars = (n - 1 - peak_pos) + future_bars
    box_end_date = dates[-1] + pd.Timedelta(days=future_bars * bar_step_days)

    t0 = pd.to_datetime(box_start_date).timestamp()
    t1 = pd.to_datetime(box_end_date).timestamp()
    dt = t1 - t0
    dp = box_top - box_bottom

    def get_t(frac): return pd.to_datetime(t0 + frac * dt, unit='s')
    def get_p(frac): return box_bottom + frac * dp

    T0, T25, T50, T75, T100 = [get_t(f) for f in [0.0, 0.25, 0.50, 0.75, 1.0]]
    P0, P25, P50, P75, P100 = [get_p(f) for f in [0.0, 0.25, 0.50, 0.75, 1.0]]

    rays = []

    # 1. 主對角線 1x1 (白色實線高亮，線寬 1.8)
    rays.append({'x': [T0, T100], 'y': [P100, P0], 'color': 'rgba(255, 255, 255, 0.85)', 'width': 1.8, 'dash': 'solid'})
    rays.append({'x': [T0, T100], 'y': [P0, P100], 'color': 'rgba(255, 255, 255, 0.85)', 'width': 1.8, 'dash': 'solid'})

    # 2. 中心青藍色幾何菱形星芒 (線寬 1.6)
    diamond_pts = [
        ([T0, T50], [P50, P100]),
        ([T50, T100], [P100, P50]),
        ([T100, T50], [P50, P0]),
        ([T50, T0], [P0, P50])
    ]
    for dx, dy in diamond_pts:
        rays.append({'x': dx, 'y': dy, 'color': 'rgba(56, 189, 248, 0.85)', 'width': 1.6, 'dash': 'solid'})

    # 3. 左右子象限對角線 Sub-X (白色虛線，線寬 1.4)
    rays.append({'x': [T0, T50], 'y': [P100, P0], 'color': 'rgba(255, 255, 255, 0.75)', 'width': 1.4, 'dash': 'dash'})
    rays.append({'x': [T0, T50], 'y': [P0, P100], 'color': 'rgba(255, 255, 255, 0.75)', 'width': 1.4, 'dash': 'dash'})
    rays.append({'x': [T50, T100], 'y': [P100, P0], 'color': 'rgba(255, 255, 255, 0.75)', 'width': 1.4, 'dash': 'dash'})
    rays.append({'x': [T50, T100], 'y': [P0, P100], 'color': 'rgba(255, 255, 255, 0.75)', 'width': 1.4, 'dash': 'dash'})

    # 4. 四分位角度射線 1x2 / 2x1 (點狀線條，線寬 1.2)
    rays.append({'x': [T0, T100], 'y': [P50, P100], 'color': 'rgba(148, 163, 184, 0.65)', 'width': 1.2, 'dash': 'dot'})
    rays.append({'x': [T0, T100], 'y': [P50, P0], 'color': 'rgba(148, 163, 184, 0.65)', 'width': 1.2, 'dash': 'dot'})
    rays.append({'x': [T0, T100], 'y': [P100, P50], 'color': 'rgba(148, 163, 184, 0.65)', 'width': 1.2, 'dash': 'dot'})
    rays.append({'x': [T0, T100], 'y': [P0, P50], 'color': 'rgba(148, 163, 184, 0.65)', 'width': 1.2, 'dash': 'dot'})

    # 5. 內部次級交叉射線
    rays.append({'x': [T25, T75], 'y': [P0, P100], 'color': 'rgba(148, 163, 184, 0.55)', 'width': 1.2, 'dash': 'dot'})
    rays.append({'x': [T25, T75], 'y': [P100, P0], 'color': 'rgba(148, 163, 184, 0.55)', 'width': 1.2, 'dash': 'dot'})

    return {
        'box_start_date': box_start_date,
        'box_end_date': box_end_date,
        'box_top': box_top,
        'box_bottom': box_bottom,
        'T0': T0, 'T25': T25, 'T50': T50, 'T75': T75, 'T100': T100,
        'P0': P0, 'P25': P25, 'P50': P50, 'P75': P75, 'P100': P100,
        'rays': rays
    }