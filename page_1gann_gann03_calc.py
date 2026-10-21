"""
Filename: page_1gann_gann03_calc.py
Description: Gann 03 核心運算模組
升級功能：
  1. Eric's Channel（小龍量化三線通道：黃色上軌、紅色生命線中軌、綠色下軌）
  2. Chop Index (市場震盪指數) + 帶寬壓縮狀態機 (DORMANT 休眠震盪防禦)
  3. ATR 0.3x 緩衝防禦帶 (Buffer Band)，精確過濾假刺穿與假跌破
  4. ZL-MACD 噪聲死區過濾 (Dead-band Hysteresis)，杜絕零軸微小抖動頻繁翻色
  5. Eric's Regression (4Y)（四年長週期線性回歸軌道）
"""

import pandas as pd
import numpy as np


def compute_chop_index(df: pd.DataFrame, period: int = 14) -> pd.Series:
    """計算 Choppiness Index (市場震盪指數, 0-100)"""
    high = df['High']
    low = df['Low']
    close = df['Close']

    tr1 = high - low
    tr2 = (high - close.shift(1)).abs()
    tr3 = (low - close.shift(1)).abs()
    tr = pd.concat([tr1, tr2, tr3], axis=1).max(axis=1)

    sum_tr = tr.rolling(period, min_periods=1).sum()
    max_hi = high.rolling(period, min_periods=1).max()
    min_lo = low.rolling(period, min_periods=1).min()

    diff = (max_hi - min_lo).replace(0, np.nan)
    ci = 100 * np.log10(sum_tr / diff) / np.log10(period)
    return ci.bfill().fillna(50.0)


def compute_erics_channel(
    df: pd.DataFrame,
    period: int = 50,
    atr_period: int = 20,
    atr_mult: float = 2.8,
    buffer_mult: float = 0.3
):
    """
    計算 Eric's Channel 三線通道，升級：
    1. Chop Index 盤整指數 + 帶寬壓縮狀態機 (DORMANT 休眠震盪防禦)
    2. ATR 緩衝防禦帶 (Buffer Band = 0.3 * ATR)，過濾盤中假刺穿
    """
    df = df.copy()
    close = df['Close']
    high = df['High']
    low = df['Low']

    mid = close.ewm(span=period, adjust=False).mean()

    tr1 = high - low
    tr2 = (high - close.shift(1)).abs()
    tr3 = (low - close.shift(1)).abs()
    tr = pd.concat([tr1, tr2, tr3], axis=1).max(axis=1)
    atr = tr.rolling(window=atr_period, min_periods=1).mean().bfill()

    band = atr * atr_mult
    upper = mid + band
    lower = mid - band

    # 🎯 升級 1: 0.3 * ATR 生命線緩衝防禦帶 (過濾假刺穿)
    buffer_dist = atr * buffer_mult
    mid_buffer_upper = mid + buffer_dist
    mid_buffer_lower = mid - buffer_dist

    # 🎯 升級 2: Chop Index 震盪指數與帶寬壓縮狀態機
    chop_idx = compute_chop_index(df, period=14)
    bandwidth = (upper - lower) / (mid.replace(0, np.nan)) * 100.0
    bw_low_quantile = bandwidth.rolling(60, min_periods=10).quantile(0.18).bfill()

    last_close = float(close.iloc[-1])
    last_mid = float(mid.iloc[-1])
    last_upper = float(upper.iloc[-1])
    last_lower = float(lower.iloc[-1])
    last_buf_up = float(mid_buffer_upper.iloc[-1])
    last_buf_down = float(mid_buffer_lower.iloc[-1])
    last_chop = float(chop_idx.iloc[-1])
    last_bw = float(bandwidth.iloc[-1])
    last_atr = float(atr.iloc[-1])

    # 判定市場狀態 (震盪休眠 vs 趨勢跟隨)
    is_dormant = bool(last_chop >= 60.0 or last_bw <= float(bw_low_quantile.iloc[-1]))
    if is_dormant:
        regime = "DORMANT_CHOP"
        regime_badge = "⚠️ 休眠震盪防禦模式 (DORMANT)"
        regime_text = "當前處於無趨勢窄幅整理：生命線暫停單邊突破觸發，嚴防摩擦打臉！"
    else:
        regime = "TRENDING"
        regime_badge = "🚀 單邊趨勢跟蹤模式 (TRENDING)"
        regime_text = "市場處於有效趨勢週期：生命線趨勢防禦全面生效！"

    # 判定生命線防禦狀態 (是否為良性回踩測試 vs 真正破位)
    if last_close >= last_mid:
        defense_status = "BULL_HEALTHY"
        defense_badge = "🟢 生命線上·多頭主導"
        defense_text = "股價位於生命線上方，多頭結構健康"
    elif last_close >= last_buf_down:
        defense_status = "BENIGN_TEST"
        defense_badge = "🛡️ 生命線良性防守測試中 (未實體破位)"
        defense_text = f"盤中微幅回踩生命線，守於 0.3×ATR 緩衝帶 (${last_buf_down:.2f}) 之上，視為良性測試"
    else:
        defense_status = "TRUE_BREAKDOWN"
        defense_badge = "🔴 實體破位跌破生命線"
        defense_text = f"收盤已明確跌破 0.3×ATR 緩衝帶 (${last_buf_down:.2f})，趨勢轉入防守偏弱期"

    return {
        'mid': mid,
        'upper': upper,
        'lower': lower,
        'mid_buffer_upper': mid_buffer_upper,
        'mid_buffer_lower': mid_buffer_lower,
        'bandwidth': bandwidth,
        'chop_idx': chop_idx,
        'last_mid': last_mid,
        'last_upper': last_upper,
        'last_lower': last_lower,
        'last_close': last_close,
        'last_buf_up': last_buf_up,
        'last_buf_down': last_buf_down,
        'last_chop': last_chop,
        'last_bw': last_bw,
        'last_atr': last_atr,
        'is_dormant': is_dormant,
        'regime': regime,
        'regime_badge': regime_badge,
        'regime_text': regime_text,
        'defense_status': defense_status,
        'defense_badge': defense_badge,
        'defense_text': defense_text
    }


def compute_4y_regression(df: pd.DataFrame, lookback_bars: int = 1000):
    """計算 Eric's Regression (4Y) 四年線性回歸通道"""
    n = min(len(df), lookback_bars)
    if n < 10:
        return None

    sub_df = df.tail(n).copy()
    y = sub_df['Close'].values
    x = np.arange(n)

    slope, intercept = np.polyfit(x, y, 1)
    reg_line = slope * x + intercept

    residuals = y - reg_line
    std = np.std(residuals)

    dates = sub_df.index
    return {
        'dates': dates,
        'reg_center': pd.Series(reg_line, index=dates),
        'upper_2std': pd.Series(reg_line + 2.0 * std, index=dates),
        'upper_1std': pd.Series(reg_line + 1.0 * std, index=dates),
        'lower_1std': pd.Series(reg_line - 1.0 * std, index=dates),
        'lower_2std': pd.Series(reg_line - 2.0 * std, index=dates),
        'slope': slope,
        'last_center': float(reg_line[-1]),
        'last_upper_2std': float(reg_line[-1] + 2.0 * std),
        'last_lower_2std': float(reg_line[-1] - 2.0 * std)
    }


def compute_zl_macd(
    df: pd.DataFrame,
    fast: int = 12,
    slow: int = 26,
    signal: int = 9,
    target_index=None,
    deadband_ratio: float = 0.08
):
    """
    計算 ZL-MACD（融入 Mark Minervini STAGE 2 與 水上/水下 動態感應版）
    升級：噪聲死區過濾 (Dead-band Hysteresis)，杜絕零軸附近微小抖動頻繁翻色
    """
    df = df.copy()
    C, H, L = df['Close'], df['High'], df['Low']

    def MA(s, n): return s.rolling(n, min_periods=1).mean()
    def LLV(s, n): return s.rolling(n, min_periods=1).min()

    # 1. MARK MINERVINI STAGE 2 趨勢過濾
    MA50, MA150, MA200 = MA(C, 50), MA(C, 150), MA(C, 200)
    stage2 = (
        (C > MA50) &
        (C > MA150) &
        (MA50 > MA150) &
        (MA150 > MA200) &
        (MA200 > MA200.shift(20).fillna(0)) &
        (C > (LLV(L, 250) * 1.3))
    )

    # 2. ZLEMA 零滯後雙均線運算
    def _zlema(series, span):
        ema1 = series.ewm(span=span, adjust=False).mean()
        ema2 = ema1.ewm(span=span, adjust=False).mean()
        return 2 * ema1 - ema2

    fast_zl = _zlema(C, fast)
    slow_zl = _zlema(C, slow)
    zl_diff = fast_zl - slow_zl
    zl_dea = _zlema(zl_diff, signal)
    zl_hist = (zl_diff - zl_dea) * 2

    # 3. STAGE 2 + 水上水下動態色彩狀態機
    water_dead_stage2 = stage2 & (zl_hist < 0) & (zl_diff > 0) & (zl_dea > 0)
    stage2_water_bull = stage2 & (zl_hist >= 0) & (zl_diff > 0) & (zl_dea > 0)
    stage2_under_bull = stage2 & (zl_hist >= 0) & (~stage2_water_bull)
    non_stage2_bull = (~stage2) & (zl_hist >= 0)
    normal_bear = (zl_hist < 0) & (~water_dead_stage2)

    macd_dir = zl_hist >= zl_hist.shift(1).fillna(0)

    # 原始顏色賦值 (使用 NumPy 陣列安全賦值)
    raw_color = np.full(len(df), '#aaaaaa', dtype=object)
    raw_color = np.where(non_stage2_bull & macd_dir, '#888888', raw_color)
    raw_color = np.where(non_stage2_bull & ~macd_dir, '#aaaaaa', raw_color)
    raw_color = np.where(stage2_water_bull & macd_dir, '#FF6600', raw_color)
    raw_color = np.where(stage2_water_bull & ~macd_dir, '#FFB266', raw_color)
    raw_color = np.where(stage2_under_bull & macd_dir, '#9900CC', raw_color)
    raw_color = np.where(stage2_under_bull & ~macd_dir, '#CC66FF', raw_color)
    raw_color = np.where(water_dead_stage2 & ~macd_dir, '#0000FF', raw_color)
    raw_color = np.where(water_dead_stage2 & macd_dir, '#3399FF', raw_color)
    raw_color = np.where(normal_bear & ~macd_dir, '#00AA00', raw_color)
    raw_color = np.where(normal_bear & macd_dir, '#00FFFF', raw_color)

    # 🎯 升級 3: 噪聲死區遲滯過濾 (Dead-band Hysteresis)
    tr1 = H - L
    tr2 = (H - C.shift(1)).abs()
    tr3 = (L - C.shift(1)).abs()
    tr = pd.concat([tr1, tr2, tr3], axis=1).max(axis=1)
    atr_val = tr.rolling(20, min_periods=1).mean().bfill()
    db_thresh = np.asarray(atr_val * deadband_ratio)

    color_vals = np.copy(raw_color)
    hist_vals = np.asarray(zl_hist)

    # 狀態機遲滯過濾：柱體在微小死區內時，鎖定沿用前一棒色彩
    for i in range(1, len(color_vals)):
        if abs(hist_vals[i]) < db_thresh[i]:
            color_vals[i] = color_vals[i - 1]

    macd_color = pd.Series(color_vals, index=df.index)

    # 水上金叉信號 (DIF 向上金叉 DEA 且都在水上)
    cross_gold = (zl_diff > zl_dea) & (zl_diff.shift(1).bfill() <= zl_dea.shift(1).bfill()) & (zl_diff > 0) & (zl_dea > 0)

    # 若指定了可視範圍的索引，精確切片回傳
    if target_index is not None:
        return {
            'diff': zl_diff.loc[target_index],
            'dea': zl_dea.loc[target_index],
            'hist': zl_hist.loc[target_index],
            'color': macd_color.loc[target_index],
            'cross_gold': cross_gold.loc[target_index],
            'stage2': stage2.loc[target_index]
        }

    return {
        'diff': zl_diff,
        'dea': zl_dea,
        'hist': zl_hist,
        'color': macd_color,
        'cross_gold': cross_gold,
        'stage2': stage2
    }