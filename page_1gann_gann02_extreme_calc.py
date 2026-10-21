"""
Filename: page_1gann_gann02_extreme_calc.py
Description: 江恩自然極限軌道、VPVR 70% 價值區間 (VAH/VAL) 與真空帶 (LVN) 識別、
             VQC 歷史與未來轉勢日預測、動態天文 24 節氣引擎、時空籌碼多維共振雷達
"""

import math
import datetime
import pandas as pd
import numpy as np

# ==============================================================================
# 🌌 Jean Meeus 純數學天文動態解算引擎 (無年份限制，支持 1900 - 2100+)
# ==============================================================================

SOLAR_TERMS_CONFIG = [
    ("小寒", 285, 1, 5, False),
    ("大寒", 300, 1, 20, False),
    ("立春", 315, 2, 4, True),    # ★ 四立 (紅色最高階)
    ("雨水", 330, 2, 19, False),
    ("驚蟄", 345, 3, 5, False),
    ("春分", 0,   3, 20, False),
    ("清明", 15,  4, 4, False),
    ("穀雨", 30,  4, 20, False),
    ("立夏", 45,  5, 5, True),    # ★ 四立 (紅色最高階)
    ("小滿", 60,  5, 21, False),
    ("芒種", 75,  6, 5, False),
    ("夏至", 90,  6, 21, False),
    ("小暑", 105, 7, 7, False),
    ("大暑", 120, 7, 22, False),
    ("立秋", 135, 8, 7, True),    # ★ 四立 (紅色最高階)
    ("處暑", 150, 8, 23, False),
    ("白露", 165, 9, 7, False),
    ("秋分", 180, 9, 23, False),
    ("寒露", 195, 10, 8, False),
    ("霜降", 210, 10, 23, False),
    ("立冬", 225, 11, 7, True),   # ★ 四立 (紅色最高階)
    ("小雪", 240, 11, 22, False),
    ("大雪", 255, 12, 7, False),
    ("冬至", 270, 12, 21, False)
]

def _calc_julian_day(year, month, day, hour=0, minute=0):
    if month <= 2:
        year -= 1
        month += 12
    a = math.floor(year / 100)
    b = 2 - a + math.floor(a / 4)
    day_fraction = day + (hour + minute / 60.0) / 24.0
    return math.floor(365.25 * (year + 4716)) + math.floor(30.6001 * (month + 1)) + day_fraction + b - 1524.5

def _calc_solar_longitude(jd):
    t = (jd - 2451545.0) / 36525.0
    l0 = 280.46646 + 36000.76983 * t + 0.0003032 * t * t
    m = 357.52911 + 35999.05029 * t - 0.0001537 * t * t
    c = (1.914602 - 0.004817 * t - 0.000014 * t * t) * math.sin(math.radians(m)) + \
        (0.019993 - 0.000101 * t) * math.sin(math.radians(2 * m)) + \
        0.000289 * math.sin(math.radians(3 * m))
    true_long = l0 + c
    omega = 125.04 - 1934.136 * t
    lambda_app = true_long - 0.00569 - 0.00478 * math.sin(math.radians(omega))
    return lambda_app % 360.0

def _find_exact_term_datetime(year, target_angle, approx_m, approx_d):
    t_utc = datetime.datetime(year, approx_m, max(1, approx_d - 2), 0, 0)
    step_hours = 2
    prev_diff = None
    anchor_utc = t_utc
    for _ in range(60):
        jd = _calc_julian_day(t_utc.year, t_utc.month, t_utc.day, t_utc.hour, t_utc.minute)
        sl = _calc_solar_longitude(jd)
        diff = (sl - target_angle + 180) % 360 - 180
        if prev_diff is not None and prev_diff < 0 and diff >= 0:
            anchor_utc = t_utc - datetime.timedelta(hours=step_hours)
            break
        prev_diff = diff
        t_utc += datetime.timedelta(hours=step_hours)

    t_fine = anchor_utc
    prev_fine_diff = None
    for _ in range(step_hours * 60 + 10):
        jd = _calc_julian_day(t_fine.year, t_fine.month, t_fine.day, t_fine.hour, t_fine.minute)
        sl = _calc_solar_longitude(jd)
        diff = (sl - target_angle + 180) % 360 - 180
        if prev_fine_diff is not None and prev_fine_diff < 0 and diff >= 0:
            return t_fine + datetime.timedelta(hours=8)
        prev_fine_diff = diff
        t_fine += datetime.timedelta(minutes=1)

    return anchor_utc + datetime.timedelta(hours=8)

def compute_solar_terms_signals(start_date, end_date, trading_dates=None):
    results = []
    st_dt = pd.to_datetime(start_date)
    ed_dt = pd.to_datetime(end_date)
    start_year = st_dt.year
    end_year = ed_dt.year

    for y in range(start_year, end_year + 1):
        for name, angle, approx_m, approx_d, is_four_li in SOLAR_TERMS_CONFIG:
            event_dt = _find_exact_term_datetime(y, angle, approx_m, approx_d)
            event_ts = pd.to_datetime(event_dt)

            if st_dt <= event_ts <= ed_dt:
                aligned_date = event_ts.date()
                if event_ts.hour >= 16:
                    aligned_date = aligned_date + datetime.timedelta(days=1)

                if trading_dates is not None and len(trading_dates) > 0:
                    t_dates = pd.to_datetime(trading_dates).tz_localize(None)
                    valid_days = t_dates[t_dates >= pd.to_datetime(aligned_date)]
                    effective_dt = valid_days[0] if len(valid_days) > 0 else pd.to_datetime(aligned_date)
                else:
                    w = aligned_date.weekday()
                    if w == 5:
                        aligned_date += datetime.timedelta(days=2)
                    elif w == 6:
                        aligned_date += datetime.timedelta(days=1)
                    effective_dt = pd.to_datetime(aligned_date)

                results.append({
                    'date': effective_dt,
                    'exact_time': event_ts,
                    'name': name,
                    'date_str': event_ts.strftime('%m/%d'),
                    'time_str': event_ts.strftime('%H:%M'),
                    'is_four_li': is_four_li
                })
    return results

# ==============================================================================
# 📊 江恩自然極限軌道
# ==============================================================================

def compute_gann_natural_extreme(df: pd.DataFrame, period: int = 20):
    df = df.copy()
    close = df['Close']
    high = df['High']
    low = df['Low']

    tr1 = high - low
    tr2 = (high - close.shift(1)).abs()
    tr3 = (low - close.shift(1)).abs()
    tr = pd.concat([tr1, tr2, tr3], axis=1).max(axis=1)
    atr = tr.rolling(window=period).mean().bfill()
    mid = close.rolling(window=period).mean().bfill()

    ext_plus = mid + 2.35 * atr
    near_plus = mid + 1.25 * atr
    near_minus = mid - 1.25 * atr
    ext_minus = mid - 2.35 * atr

    touch_near_p = high >= near_plus
    touch_near_m = low <= near_minus

    return {
        'mid': mid,
        'ext_plus': ext_plus,
        'near_plus': near_plus,
        'near_minus': near_minus,
        'ext_minus': ext_minus,
        'touch_near_p': touch_near_p,
        'touch_near_m': touch_near_m,
        'last_close': float(close.iloc[-1]),
        'last_ext_p': float(ext_plus.iloc[-1]),
        'last_near_p': float(near_plus.iloc[-1]),
        'last_near_m': float(near_minus.iloc[-1]),
        'last_ext_m': float(ext_minus.iloc[-1]),
    }

# ==============================================================================
# 🛡️ VPVR 籌碼分佈：70% 價值區間 (VAH / VAL) 與 真空帶 (LVN) 計算
# ==============================================================================

def compute_vpvr_and_poc(df: pd.DataFrame, num_bins: int = 40):
    p_min = df['Low'].min()
    p_max = df['High'].max()
    if p_min == p_max or pd.isna(p_min):
        return None

    bins = np.linspace(p_min, p_max, num_bins + 1)
    bin_centers = (bins[:-1] + bins[1:]) / 2
    bin_width = bins[1] - bins[0]

    up_vols = np.zeros(num_bins)
    down_vols = np.zeros(num_bins)

    for i in range(len(df)):
        c = df['Close'].iloc[i]
        o = df['Open'].iloc[i]
        v = df['Volume'].iloc[i] if 'Volume' in df.columns else 1
        idx = int(np.clip((c - p_min) / (p_max - p_min) * (num_bins - 1), 0, num_bins - 1))
        if c >= o:
            up_vols[idx] += v
        else:
            down_vols[idx] += v

    total_vols = up_vols + down_vols
    max_idx = int(np.argmax(total_vols))
    poc_price = float(bin_centers[max_idx])
    max_vol = float(np.max(total_vols))

    # 1. 機構專用 70% 價值區間 (Value Area: VAH & VAL)
    target_va_vol = 0.70 * np.sum(total_vols)
    included_indices = {max_idx}
    accumulated_vol = total_vols[max_idx]
    up_idx = max_idx + 1
    dn_idx = max_idx - 1

    while accumulated_vol < target_va_vol and (up_idx < num_bins or dn_idx >= 0):
        up_v = total_vols[up_idx] if up_idx < num_bins else 0
        dn_v = total_vols[dn_idx] if dn_idx >= 0 else 0

        if up_v >= dn_v and up_idx < num_bins:
            included_indices.add(up_idx)
            accumulated_vol += up_v
            up_idx += 1
        elif dn_idx >= 0:
            included_indices.add(dn_idx)
            accumulated_vol += dn_v
            dn_idx -= 1
        elif up_idx < num_bins:
            included_indices.add(up_idx)
            accumulated_vol += up_v
            up_idx += 1
        else:
            break

    val_price = float(bin_centers[min(included_indices)])
    vah_price = float(bin_centers[max(included_indices)])
    va_mask = np.array([i in included_indices for i in range(num_bins)])

    # 2. 籌碼真空帶 (LVN) 與 密集區 (HVN) 判定
    last_close = float(df['Close'].iloc[-1])
    curr_bin_idx = int(np.clip((last_close - p_min) / (p_max - p_min) * (num_bins - 1), 0, num_bins - 1))
    curr_vol = total_vols[curr_bin_idx]
    avg_vol = float(np.mean(total_vols))

    is_lvn = bool(curr_vol < (0.45 * avg_vol))
    is_hvn = bool(curr_vol > (0.80 * max_vol) or curr_bin_idx == max_idx)
    near_poc = bool(abs(last_close - poc_price) / poc_price <= 0.018)
    is_in_value_area = bool(val_price <= last_close <= vah_price)

    if is_in_value_area:
        if is_lvn:
            market_regime = "價值區內·真空加速帶 (LVN)"
        elif near_poc or is_hvn:
            market_regime = "價值區內·POC重兵平衡區 (HVN)"
        else:
            market_regime = "70% 價值區平衡震盪 (Value Area)"
    elif last_close > vah_price:
        market_regime = "向上突破價值區失衡 (Trend Imbalance)"
    else:
        market_regime = "向下跌破價值區失衡 (Trend Imbalance)"

    return {
        'bin_centers': bin_centers,
        'bin_width': bin_width,
        'up_vols': up_vols,
        'down_vols': down_vols,
        'max_vol': max_vol,
        'poc_price': poc_price,
        'vah_price': vah_price,
        'val_price': val_price,
        'va_mask': va_mask,
        'is_lvn': is_lvn,
        'is_hvn': is_hvn,
        'near_poc': near_poc,
        'is_in_value_area': is_in_value_area,
        'market_regime': market_regime
    }

# ==============================================================================
# 🎯 時空籌碼多維共振雷達 (Confluence Score 演算法)
# ==============================================================================

def compute_confluence_score(last_close: float, ext_data: dict, vpvr_data: dict, cycle_data: dict, solar_terms: list, last_date=None):
    score = 0
    checks = []

    # 條件 1: Time Cycle 進入轉折窗口 (PEAK / TROUGH)
    c1 = False
    if cycle_data:
        w_status = cycle_data.get('window_status', '')
        bars_left = cycle_data.get('next_turn_bars', 99)
        if "窗口" in w_status or "ZONE" in w_status or bars_left <= 2:
            c1 = True
            score += 1
            checks.append(f"時間週期窗口 ({w_status})")

    # 條件 2: K 線碰觸江恩極限軌道 (Near+ / Near-)
    c2 = False
    if ext_data:
        near_p = ext_data['last_near_p']
        near_m = ext_data['last_near_m']
        if last_close >= near_p * 0.992 or last_close <= near_m * 1.008:
            c2 = True
            score += 1
            target_rail = "Near+壓力" if last_close >= near_p * 0.992 else "Near-支撐"
            checks.append(f"極限軌道觸及 ({target_rail})")

    # 條件 3: 價格剛好落在 POC / HVN 籌碼大峰值支撐阻力處
    c3 = False
    if vpvr_data:
        if vpvr_data.get('near_poc') or vpvr_data.get('is_hvn'):
            c3 = True
            score += 1
            checks.append(f"POC籌碼密集共振 (${vpvr_data['poc_price']:.2f})")
        elif vpvr_data.get('is_lvn'):
            checks.append("⚠️ 處於籌碼真空區(LVN)")

    # 條件 4: 前後 3 日內是否有「★ 四立」或「二十四節氣」變盤日
    c4 = False
    if solar_terms and last_date is not None:
        l_dt = pd.to_datetime(last_date).tz_localize(None)
        near_terms = []
        for t in solar_terms:
            t_dt = pd.to_datetime(t['date']).tz_localize(None)
            diff_days = abs((t_dt - l_dt).days)
            if diff_days <= 3:
                c4 = True
                term_prefix = "★" if t.get('is_four_li') else ""
                near_terms.append(f"{term_prefix}{t['name']}({t['date_str']})")
        if c4:
            score += 1
            checks.append(f"節氣變盤共振 [{','.join(near_terms)}]")

    is_lvn = vpvr_data.get('is_lvn', False) if vpvr_data else False

    # 華爾街戰術評級與防鈍化警報
    if score == 4:
        level_tag = "⭐⭐⭐⭐ 頂級時空籌碼大共振"
        color = "#f43f5e"
        advice = "時空籌碼 4 維合一！極限反轉高勝率變盤窗口，重度防守/出擊！"
    elif score == 3:
        level_tag = "⭐⭐⭐ 強度時空變盤共振"
        color = "#fb923c"
        advice = "3 維時空交匯，密切觀察 K 線右側分型與動能扳機！"
    elif score == 2:
        level_tag = "⭐⭐ 局部共振蓄勢"
        color = "#facc15"
        advice = "局部時空共振，需等待突破確認。"
    elif c1 and is_lvn:
        level_tag = "⚠️ 單一週期警報 (防鈍化)"
        color = "#e11d48"
        advice = "⚠️ 警報：週期到達拐點但處於籌碼真空區！行情極易單邊暴衝致週期鈍化，嚴禁盲目摸頂/抄底！"
    else:
        level_tag = "🌐 常規常態波動"
        color = "#38bdf8"
        advice = "未觸發密集共振，以 70% 價值區與軌道常規震盪策略應對。"

    return {
        'score': score,
        'level_tag': level_tag,
        'color': color,
        'advice': advice,
        'checks': checks,
        'is_lvn': is_lvn
    }

# ==============================================================================
# 🟣 VQC 轉勢日 (含歷史確認點 + 未來週期投影預測)
# ==============================================================================

def _get_future_trading_date(start_date, bar_count):
    cur = pd.to_datetime(start_date)
    added = 0
    while added < bar_count:
        cur += datetime.timedelta(days=1)
        if cur.weekday() < 5:  # 週一至週五
            added += 1
    return cur

def compute_vqc_signals(df: pd.DataFrame, ext_data: dict):
    signals = []
    n = len(df)
    if n < 10 or not ext_data:
        return signals

    highs = df['High'].values
    lows = df['Low'].values
    dates = df.index

    # --- A. 歷史確認點 ---
    last_pivot_type = 'bottom'
    last_pivot_date = dates[-1]

    for i in range(3, n - 2):
        d = dates[i]
        is_swing_high = highs[i] == max(highs[i - 2: i + 3])
        is_swing_low = lows[i] == min(lows[i - 2: i + 3])

        if is_swing_high and highs[i] >= ext_data['near_plus'].iloc[i] * 0.995:
            signals.append({
                'date': d,
                'price': highs[i],
                'type': 'top',
                'date_str': d.strftime('%m/%d'),
                'is_future': False
            })
            last_pivot_type = 'top'
            last_pivot_date = d

        elif is_swing_low and lows[i] <= ext_data['near_minus'].iloc[i] * 1.005:
            signals.append({
                'date': d,
                'price': lows[i],
                'type': 'bottom',
                'date_str': d.strftime('%m/%d'),
                'is_future': False
            })
            last_pivot_type = 'bottom'
            last_pivot_date = d

    # --- B. 未來預測點 (江恩 8 交易日與費氏 21 交易日投射) ---
    future_near_p = ext_data['last_near_p']
    future_near_m = ext_data['last_near_m']

    # 預測窗口 1：江恩短期轉折 (約 8 個交易日)
    next_date_1 = _get_future_trading_date(dates[-1], 8)
    next_type_1 = 'bottom' if last_pivot_type == 'top' else 'top'
    next_price_1 = future_near_m if next_type_1 == 'bottom' else future_near_p

    signals.append({
        'date': next_date_1,
        'price': next_price_1,
        'type': next_type_1,
        'date_str': next_date_1.strftime('%m/%d'),
        'is_future': True
    })

    # 預測窗口 2：江恩中線共振轉折 (約 21 個交易日)
    next_date_2 = _get_future_trading_date(dates[-1], 21)
    next_type_2 = 'top' if next_type_1 == 'bottom' else 'bottom'
    next_price_2 = future_near_p if next_type_2 == 'top' else future_near_m

    signals.append({
        'date': next_date_2,
        'price': next_price_2,
        'type': next_type_2,
        'date_str': next_date_2.strftime('%m/%d'),
        'is_future': True
    })

    return signals