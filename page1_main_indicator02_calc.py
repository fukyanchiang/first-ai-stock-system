import pandas as pd
import numpy as np
import plotly.graph_objects as go
import warnings
warnings.filterwarnings('ignore')

def calculate_sar(high, low, close, af_step=0.02, af_max=0.2):
    length = len(close)
    if length < 2: return pd.Series(close, index=close.index)
    sar = np.zeros(length)
    bull = True
    af = af_step
    ep = high.iloc[0]
    sar[0] = low.iloc[0]
    for i in range(1, length):
        prev_sar = sar[i-1]
        if bull:
            cur_sar = prev_sar + af * (ep - prev_sar)
            cur_sar = min(cur_sar, low.iloc[i-1], low.iloc[max(0, i-2)])
            if low.iloc[i] < cur_sar:
                bull = False
                cur_sar = ep
                ep = low.iloc[i]
                af = af_step
            else:
                if high.iloc[i] > ep:
                    ep = high.iloc[i]
                    af = min(af + af_step, af_max)
        else:
            cur_sar = prev_sar + af * (ep - prev_sar)
            cur_sar = max(cur_sar, high.iloc[i-1], high.iloc[max(0, i-2)])
            if high.iloc[i] > cur_sar:
                bull = True
                cur_sar = ep
                ep = high.iloc[i]
                af = af_step
            else:
                if low.iloc[i] < ep:
                    ep = low.iloc[i]
                    af = min(af + af_step, af_max)
        sar[i] = cur_sar
    return pd.Series(sar, index=close.index)

def calculate_td_sequential(close):
    length = len(close)
    up_count = np.zeros(length, dtype=int)
    down_count = np.zeros(length, dtype=int)
    for i in range(4, length):
        up_count[i] = up_count[i-1] + 1 if close.iloc[i] > close.iloc[i-4] else 0
        down_count[i] = down_count[i-1] + 1 if close.iloc[i] < close.iloc[i-4] else 0
    up_ay = np.zeros(length, dtype=int)
    down_ay = np.zeros(length, dtype=int)
    for i in range(length):
        if up_count[i] == 9:
            for k in range(9):
                if i - k >= 0: up_ay[i - k] = up_count[i - k]
        elif i == length - 1 and 5 <= up_count[i] <= 9:
            for k in range(up_count[i]):
                if i - k >= 0: up_ay[i - k] = up_count[i - k]
        if down_count[i] == 9:
            for k in range(9):
                if i - k >= 0: down_ay[i - k] = down_count[i - k]
        elif i == length - 1 and 5 <= down_count[i] <= 9:
            for k in range(down_count[i]):
                if i - k >= 0: down_ay[i - k] = down_count[i - k]
    return pd.Series(up_ay, index=close.index), pd.Series(down_ay, index=close.index)

def build_stickline_coords(dates, s1, s2, cond):
    """
    高效構建 Plotly 垂直線段 (STICKLINE 一支支線)
    每個點 (x, y_min) -> (x, y_max) -> (None, None) 斷開
    """
    x, y = [], []
    for d, v1, v2, c in zip(dates, s1, s2, cond):
        if c and not pd.isna(v1) and not pd.isna(v2):
            x.extend([d, d, None])
            y.extend([min(v1, v2), max(v1, v2), None])
    return x, y

def compute_main_group2(df):
    """
    計算主圖指標組 2:
    GP_ALL_IN_ONE (主圖終極合體版)
    """
    df = df.copy()
    C, O, H, L, V = df['Close'], df['Open'], df['High'], df['Low'], df['Volume']

    def MA(s, n): return s.rolling(n, min_periods=1).mean()
    def HHV(s, n): return s.rolling(n, min_periods=1).max()
    def STD(s, n): return s.rolling(n, min_periods=1).std()
    def CROSS(s1, s2):
        if isinstance(s1, (int, float)): s1 = pd.Series(s1, index=df.index)
        if isinstance(s2, (int, float)): s2 = pd.Series(s2, index=df.index)
        return (s1 > s2) & (s1.shift(1).bfill() <= s2.shift(1).bfill())
    def COUNT(cond, n): return cond.fillna(False).astype(int).rolling(n, min_periods=1).sum()

    # 1. 均線與特種線
    df['GP_MA1'] = MA(C, 5)
    df['GP_MA2'] = MA(C, 10)
    df['GP_MA3'] = MA(C, 20)
    df['GP_MA4'] = MA(C, 60)
    df['GP_MA50L'] = MA(L, 50)
    df['GP_MA50LREF'] = df['GP_MA50L'].shift(8)

    # 2. 布林通道 (20, 2.0)
    sd_period = 20
    dis = STD(C, sd_period)
    df['BB_MID'] = MA(C, sd_period)
    df['BB_UPPER'] = df['BB_MID'] + 2 * dis
    df['BB_LOWER'] = df['BB_MID'] - 2 * dis

    # 3. SAR
    df['SAR'] = calculate_sar(H, L, C, 0.02, 0.2)

    # 4. AI BUY (綠三角 ▲)
    aibb_sd = STD(C, 20)
    df['AIBUY'] = CROSS(C, df['BB_MID'] + 1.5 * aibb_sd) & (C > O)

    # 5. H50 新高
    df['H50'] = C > HHV(H, 50).shift(1)

    # 6. TD 九轉序列
    df['TD_UP'], df['TD_DN'] = calculate_td_sequential(C)

    # 7. 保力加起爆預警 (Chris Lo 量化版)
    bb_width = (df['BB_UPPER'] - df['BB_LOWER']) / (df['BB_MID'] + 1e-9)
    squeeze_days = COUNT(bb_width < 0.12, 8) >= 2
    vol_expand = (V > V.shift(1)) | (V > MA(V, 5) * 1.1)
    band_open = bb_width > bb_width.shift(1)
    
    bb_bull_start = squeeze_days & vol_expand & band_open & (C > df['BB_UPPER']) & (C > O)
    bb_bear_start = squeeze_days & vol_expand & band_open & (C < df['BB_LOWER']) & (C < O)
    df['FIRST_BULL'] = bb_bull_start & (COUNT(bb_bull_start, 5) == 1)
    df['FIRST_BEAR'] = bb_bear_start & (COUNT(bb_bear_start, 5) == 1)

    return df

def render_main_group2(fig, df_display, cfg):
    """
    渲染 GP_ALL_IN_ONE 各信號 Traces (包含富途牛牛彩色均線帶 STICKLINE 一支支線)
    """
    if not cfg.get("show_gp_all", True):
        return

    dates = df_display.index
    ma1 = df_display['GP_MA1']
    ma2 = df_display['GP_MA2']
    ma3 = df_display['GP_MA3']
    ma4 = df_display['GP_MA4']

    # =========================================================
    # 🌈 1. 富途牛牛「一支支線」彩帶 (STICKLINE)
    # =========================================================
    # (B) ★ 中期彩帶：MA2 (10日) VS MA3 (20日) - 【截圖核心呈現】
    if cfg.get("show_gp_stick_mid", True):
        # 多頭 (MA2 > MA3) -> 亮藍色垂直柱線
        xb_mid, yb_mid = build_stickline_coords(dates, ma2, ma3, ma2 > ma3)
        if xb_mid:
            fig.add_trace(go.Scatter(
                x=xb_mid, y=yb_mid, mode='lines',
                line=dict(color='#0088FF', width=2),
                name='中期彩帶·多頭 (藍色一支支)', hoverinfo='skip', yaxis='y1'
            ))
        # 空頭 (MA2 <= MA3) -> 洋紅/粉紫色垂直柱線
        xr_mid, yr_mid = build_stickline_coords(dates, ma2, ma3, ma2 <= ma3)
        if xr_mid:
            fig.add_trace(go.Scatter(
                x=xr_mid, y=yr_mid, mode='lines',
                line=dict(color='#FF1493', width=2),
                name='中期彩帶·空頭 (粉紫一支支)', hoverinfo='skip', yaxis='y1'
            ))

    # (A) 短期彩帶：MA1 (5日) VS MA2 (10日)
    if cfg.get("show_gp_stick_short", False):
        xb_s, yb_s = build_stickline_coords(dates, ma1, ma2, ma1 > ma2)
        if xb_s:
            fig.add_trace(go.Scatter(
                x=xb_s, y=yb_s, mode='lines',
                line=dict(color='#00FFFF', width=1.5),
                name='短期彩帶·多頭 (青色一支支)', hoverinfo='skip', yaxis='y1'
            ))
        xr_s, yr_s = build_stickline_coords(dates, ma1, ma2, ma1 <= ma2)
        if xr_s:
            fig.add_trace(go.Scatter(
                x=xr_s, y=yr_s, mode='lines',
                line=dict(color='#555555', width=1.5),
                name='短期彩帶·空頭 (深灰一支支)', hoverinfo='skip', yaxis='y1'
            ))

    # (C) 長期彩帶：MA3 (20日) VS MA4 (60日)
    if cfg.get("show_gp_stick_long", False):
        xb_l, yb_l = build_stickline_coords(dates, ma3, ma4, ma3 > ma4)
        if xb_l:
            fig.add_trace(go.Scatter(
                x=xb_l, y=yb_l, mode='lines',
                line=dict(color='#808080', width=1.5),
                name='長期彩帶·多頭 (灰色一支支)', hoverinfo='skip', yaxis='y1'
            ))
        xr_l, yr_l = build_stickline_coords(dates, ma3, ma4, ma3 <= ma4)
        if xr_l:
            fig.add_trace(go.Scatter(
                x=xr_l, y=yr_l, mode='lines',
                line=dict(color='#FFD700', width=1.5),
                name='長期彩帶·空頭 (黃色一支支)', hoverinfo='skip', yaxis='y1'
            ))

    # =========================================================
    # 📈 2. 彩色均線邊界實線 (MA1~MA4)
    # =========================================================
    if cfg.get("show_gp_ribbon", True):
        fig.add_trace(go.Scatter(x=dates, y=ma1, mode='lines', line=dict(color='#BA55D3', width=1.2), name='GP MA1 (5)', yaxis='y1'))
        fig.add_trace(go.Scatter(x=dates, y=ma2, mode='lines', line=dict(color='#FFD700', width=1.8), name='GP MA2 (10 黃線)', yaxis='y1'))
        fig.add_trace(go.Scatter(x=dates, y=ma3, mode='lines', line=dict(color='#FFAEC9', width=1.8), name='GP MA3 (20 粉線)', yaxis='y1'))
        fig.add_trace(go.Scatter(x=dates, y=ma4, mode='lines', line=dict(color='#00FF7F', width=1.5), name='GP MA4 (60)', yaxis='y1'))

    # 特種 MA50L
    if cfg.get("show_gp_ma50l", False):
        fig.add_trace(go.Scatter(x=dates, y=df_display['GP_MA50L'], mode='lines', line=dict(color='#FF4500', width=1.5), name='MA50L (低點50)', yaxis='y1'))
        fig.add_trace(go.Scatter(x=dates, y=df_display['GP_MA50LREF'], mode='lines', line=dict(color='#A9A9A9', width=1, dash='dot'), name='MA50L 偏移8日', yaxis='y1'))

    # 布林通道
    if cfg.get("show_gp_bb", False):
        fig.add_trace(go.Scatter(x=dates, y=df_display['BB_UPPER'], mode='lines', line=dict(color='#FFC90E', width=1, dash='dot'), name='BB 上軌', yaxis='y1'))
        fig.add_trace(go.Scatter(x=dates, y=df_display['BB_MID'], mode='lines', line=dict(color='#FFAEC9', width=1.2), name='BB 中軌', yaxis='y1'))
        fig.add_trace(go.Scatter(x=dates, y=df_display['BB_LOWER'], mode='lines', line=dict(color='#0CAEE6', width=1, dash='dot'), name='BB 下軌', yaxis='y1'))

    # SAR
    if cfg.get("show_gp_sar", True):
        fig.add_trace(go.Scatter(x=dates, y=df_display['SAR'], mode='markers', marker=dict(size=3.5, color='#0CAEE6', symbol='circle'), name='SAR 轉向點', yaxis='y1'))

    # AI BUY (綠三角 ▲)
    if cfg.get("show_gp_aibuy", True):
        ai = df_display[df_display['AIBUY'] == True]
        if not ai.empty:
            fig.add_trace(go.Scatter(x=ai.index, y=ai['Low'] * 0.96, mode='text', text=['▲'] * len(ai), textposition='bottom center', textfont=dict(color='#00FF00', size=14, family='Arial Black'), name='AI BUY 點火', yaxis='y1'))

    # H50 新高
    if cfg.get("show_gp_h50", True):
        h50 = df_display[df_display['H50'] == True]
        if not h50.empty:
            fig.add_trace(go.Scatter(x=h50.index, y=h50['High'] * 1.04, mode='text', text=['H50'] * len(h50), textposition='top center', textfont=dict(color='#FF3366', size=10, family='Arial Black'), name='H50 突破', yaxis='y1'))

    # TD 九轉序列
    if cfg.get("show_gp_td9", True):
        up_18 = df_display[(df_display['TD_UP'] > 0) & (df_display['TD_UP'] < 9)]
        if not up_18.empty:
            fig.add_trace(go.Scatter(x=up_18.index, y=up_18['High'] * 1.015, mode='text', text=up_18['TD_UP'].astype(str), textposition='top center', textfont=dict(color='#FF00FF', size=9), showlegend=False, yaxis='y1'))
        up_9 = df_display[df_display['TD_UP'] == 9]
        if not up_9.empty:
            fig.add_trace(go.Scatter(x=up_9.index, y=up_9['High'] * 1.02, mode='text', text=['9'] * len(up_9), textposition='top center', textfont=dict(color='#00FF00', size=13, family='Arial Black'), name='TD 上升9轉', yaxis='y1'))

        dn_18 = df_display[(df_display['TD_DN'] > 0) & (df_display['TD_DN'] < 9)]
        if not dn_18.empty:
            fig.add_trace(go.Scatter(x=dn_18.index, y=dn_18['Low'] * 0.985, mode='text', text=dn_18['TD_DN'].astype(str), textposition='bottom center', textfont=dict(color='#00FF00', size=9), showlegend=False, yaxis='y1'))
        dn_9 = df_display[df_display['TD_DN'] == 9]
        if not dn_9.empty:
            fig.add_trace(go.Scatter(x=dn_9.index, y=dn_9['Low'] * 0.98, mode='text', text=['9'] * len(dn_9), textposition='bottom center', textfont=dict(color='#FF00FF', size=13, family='Arial Black'), name='TD 下跌9轉', yaxis='y1'))

    # 保力加起爆 / 暴跌
    if cfg.get("show_gp_boll_burst", True):
        bull = df_display[df_display['FIRST_BULL'] == True]
        if not bull.empty:
            fig.add_trace(go.Scatter(x=bull.index, y=bull['Low'] * 0.92, mode='text', text=['★單邊起爆'] * len(bull), textposition='bottom center', textfont=dict(color='#FF3333', size=12, family='Arial Black'), name='★ 單邊起爆', yaxis='y1'))
        bear = df_display[df_display['FIRST_BEAR'] == True]
        if not bear.empty:
            fig.add_trace(go.Scatter(x=bear.index, y=bear['High'] * 1.08, mode='text', text=['▼單邊暴跌'] * len(bear), textposition='top center', textfont=dict(color='#00FF88', size=12, family='Arial Black'), name='▼ 單邊暴跌', yaxis='y1'))