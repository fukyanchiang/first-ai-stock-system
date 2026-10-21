import pandas as pd
import numpy as np
import plotly.graph_objects as go
import warnings
warnings.filterwarnings('ignore')

def filter_signals(cond, n):
    res = np.zeros(len(cond), dtype=bool)
    last_true = -9999
    for i, val in enumerate(cond):
        if val:
            if i - last_true > n:
                res[i] = True
                last_true = i
            else:
                res[i] = False
        else:
            res[i] = False
    return pd.Series(res, index=cond.index)

def compute_main_group1(df):
    """
    計算主圖指標組 1:
    1. MA (10 條均線)
    2. ANCHORZONE (主力放量真陽線爆發)
    3. VOLUMEANCHORSUPPORT / S_PLUS_MAIN_V3 (VAS 天量防守 + S+++ 買賣引擎)
    """
    df = df.copy()
    C, O, H, L, V = df['Close'], df['Open'], df['High'], df['Low'], df['Volume']

    def MA(s, n): return s.rolling(n, min_periods=1).mean()
    def EMA(s, n): return s.ewm(span=n, adjust=False).mean()
    def HHV(s, n): return s.rolling(n, min_periods=1).max()
    def CROSS(s1, s2):
        if isinstance(s1, (int, float)): s1 = pd.Series(s1, index=df.index)
        if isinstance(s2, (int, float)): s2 = pd.Series(s2, index=df.index)
        return (s1 > s2) & (s1.shift(1).bfill() <= s2.shift(1).bfill())

    # 1. 10 條自訂均線
    p_periods = [5, 10, 20, 30, 50, 60, 120, 150, 200, 250]
    for i, p in enumerate(p_periods, 1):
        df[f'MA_{i}'] = MA(C, p)

    # 2. ANCHORZONE
    volma20 = MA(V, 20)
    cspre = (C - O).abs()
    avgs = MA(cspre, 20)
    df['AZ_ISBIG'] = (V > volma20 * 1.5) & (C > O) & (cspre > avgs)

    # 3. VOLUMEANCHORSUPPORT (S_PLUS_MAIN_V3)
    ema20 = EMA(C, 20)
    ema50 = EMA(C, 50)
    ema200 = EMA(C, 200)
    e5 = EMA(C, 5)
    e10 = EMA(C, 10)

    vma5 = MA(V, 5)
    inst_vol = V > (vma5 * 1.2)
    is_stage2 = (C > ema20) & (ema20 > ema50) & (ema50 > ema200)
    body_range = H - L
    strong_buy_k = (C > O) & ((C - L) > body_range * 0.50)
    cross_buy = CROSS(C, ema20) | ((C > ema20) & CROSS(e5, e10))
    pullback_buy = (L <= ema20) & (C > ema20) & (C > O)
    df['S_PLUS_BUY'] = is_stage2 & inst_vol & strong_buy_k & (cross_buy | pullback_buy)

    climax_vol = V > (vma5 * 1.5)
    max_co = np.maximum(C, O)
    weak_sell_k = (C < O) | ((H - max_co) > body_range * 0.5)
    top_reversal = climax_vol & weak_sell_k & (C > ema20)
    momentum_loss = CROSS(e10, e5)
    df['SELL_TRIM'] = filter_signals(top_reversal | momentum_loss, 4)

    strong_bear_k = (O > C) & ((O - C) > body_range * 0.6)
    df['SELL_CLEAR'] = filter_signals(CROSS(ema20, C) & strong_bear_k, 4)

    hv60 = HHV(V, 60)
    df['VAS'] = pd.Series(np.where(V == hv60, L, np.nan), index=df.index).ffill()

    return df

def render_main_group1(fig, df_display, cfg):
    """
    渲染主圖指標組 1 的 Traces
    """
    # 1. MA 均線群
    if cfg.get("show_ma_group", True):
        ma_colors = [
            '#FF8D1E', '#0CAEE6', '#E970DC', '#0080FF', '#22C57E',
            '#FF6060', '#13FFFF', '#FBCD2D', '#954FFF', '#B388FF'
        ]
        p_periods = [5, 10, 20, 30, 50, 60, 120, 150, 200, 250]
        for i in range(1, 11):
            if cfg.get(f"show_ma_{i}", True):
                fig.add_trace(go.Scatter(
                    x=df_display.index, y=df_display[f'MA_{i}'],
                    mode='lines', line=dict(color=ma_colors[i-1], width=1.4),
                    name=f'MA{i} ({p_periods[i-1]})', yaxis='y1'
                ))

    # 2. ANCHORZONE
    if cfg.get("show_anchorzone", True):
        az = df_display[df_display['AZ_ISBIG'] == True]
        if not az.empty:
            if cfg.get("show_az_text", True):
                fig.add_trace(go.Scatter(
                    x=az.index, y=az['High'] * 1.02,
                    mode='text', text=['BIG'] * len(az),
                    textposition='top center',
                    textfont=dict(color='#FF00FF', size=13, family='Arial Black'),
                    name='ANCHOR BIG', yaxis='y1'
                ))
            if cfg.get("show_az_line", True):
                for idx, row in az.iterrows():
                    fig.add_shape(
                        type="line",
                        x0=idx - pd.Timedelta(hours=12), y0=row['Low'],
                        x1=idx + pd.Timedelta(hours=12), y1=row['Low'],
                        line=dict(color="#FF00FF", width=3),
                        xref='x', yref='y1'
                    )

    # 3. VOLUMEANCHORSUPPORT (S_PLUS_MAIN_V3)
    if cfg.get("show_vas_main", True):
        if cfg.get("show_vas_line", True) and 'VAS' in df_display:
            fig.add_trace(go.Scatter(
                x=df_display.index, y=df_display['VAS'],
                mode='lines', line=dict(color='red', width=2),
                name='VAS 天量防守線', yaxis='y1'
            ))

        if cfg.get("show_s_plus_buy", True):
            buy = df_display[df_display['S_PLUS_BUY'] == True]
            if not buy.empty:
                fig.add_trace(go.Scatter(
                    x=buy.index, y=buy['Low'] * 0.95,
                    mode='text+markers',
                    marker=dict(symbol='triangle-up', color='red', size=9),
                    text=['🚀S+++突擊'] * len(buy),
                    textposition='bottom center',
                    textfont=dict(color='red', size=11, family='Arial Black'),
                    name='🚀 S+++ 突擊買入', yaxis='y1'
                ))

        if cfg.get("show_sell_trim", True):
            trim = df_display[df_display['SELL_TRIM'] == True]
            if not trim.empty:
                fig.add_trace(go.Scatter(
                    x=trim.index, y=trim['High'] * 1.03,
                    mode='text+markers',
                    marker=dict(symbol='triangle-down', color='#FBCD2D', size=8),
                    text=['⚠️鎖利'] * len(trim),
                    textposition='top center',
                    textfont=dict(color='#FBCD2D', size=11, family='Arial Black'),
                    name='⚠️ 鎖利減倉', yaxis='y1'
                ))

        if cfg.get("show_sell_clear", True):
            clear = df_display[df_display['SELL_CLEAR'] == True]
            if not clear.empty:
                fig.add_trace(go.Scatter(
                    x=clear.index, y=clear['High'] * 1.06,
                    mode='text+markers',
                    marker=dict(symbol='triangle-down', color='#22C57E', size=9),
                    text=['🛑清倉'] * len(clear),
                    textposition='top center',
                    textfont=dict(color='#22C57E', size=11, family='Arial Black'),
                    name='🛑 徹底清倉', yaxis='y1'
                ))