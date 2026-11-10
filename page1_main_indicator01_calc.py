"""
Filename: page1_main_indicator01_calc.py
Description: 📈 艙房一 (六維王者矩陣) 主圖指標組 1 運算與渲染核心
             1. MA 均線群 (10 條自訂均線)
             2. ANCHORZONE (主力放量真陽線爆發)
             3. VOLUMEANCHORSUPPORT / S_PLUS_MAIN_V3 (VAS 天量防守 + S+++ 買賣引擎)
             4. 🌟 雙層獨立 VPVR 籌碼分佈運算 (近期青藍/粉紅 + 歷史黃褐/紫色 + 雙重 POC)
             5. 🌟 右側成交重貨柱專屬 Plotly 渲染引擎 (向左生長、右側 POC 徽章定位)
"""

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

# =========================================================================
# ⚙️ 1. 主圖指標組 1 核心計算引擎 (MA, ANCHORZONE, VAS S+++)
# =========================================================================

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

# =========================================================================
# 📊 2. 雙層獨立 VPVR 籌碼分佈運算模組
# =========================================================================

def compute_page1_dual_vpvr(df_all: pd.DataFrame, df_display: pd.DataFrame, n_bins: int = 40):
    """
    計算主圖專屬雙層 VPVR 籌碼分佈與雙重 POC：
    - 以當前可視視野 (df_display) 的最高/最低價劃分 40 個等高價格箱體 (Bins)
    - 歷史全景籌碼：統計歷史所有落在當前可視價格帶內的成交量
    - 近期趨勢籌碼：統計當前可視週期內的成交量
    """
    if df_display.empty or len(df_display) < 5:
        return None

    p_min = float(df_display['Low'].min())
    p_max = float(df_display['High'].max())
    if p_max <= p_min or np.isnan(p_min) or np.isnan(p_max):
        return None

    bin_edges = np.linspace(p_min, p_max, n_bins + 1)
    bin_width = bin_edges[1] - bin_edges[0]
    bin_centers = (bin_edges[:-1] + bin_edges[1:]) / 2.0

    def get_binned_volume(df_subset):
        buy_v = np.zeros(n_bins)
        sell_v = np.zeros(n_bins)
        for _, r in df_subset.iterrows():
            c, o, h, l = float(r['Close']), float(r['Open']), float(r['High']), float(r['Low'])
            v = float(r['Volume']) if ('Volume' in r and not pd.isna(r['Volume']) and r['Volume'] > 0) else 1000.0
            is_bull = (c >= o)
            if h < p_min or l > p_max:
                continue
            i_l = max(0, min(n_bins - 1, int((max(l, p_min) - p_min) / bin_width)))
            i_h = max(0, min(n_bins - 1, int((min(h, p_max) - p_min) / bin_width)))
            n_cov = max(1, i_h - i_l + 1)
            v_p = v / float(n_cov)
            for b in range(i_l, i_h + 1):
                if is_bull: buy_v[b] += v_p
                else: sell_v[b] += v_p
        return buy_v, sell_v

    # 1. 歷史全景籌碼分佈
    hist_buy, hist_sell = get_binned_volume(df_all)
    hist_total = hist_buy + hist_sell
    hist_poc_idx = int(np.argmax(hist_total)) if (len(hist_total) > 0 and np.max(hist_total) > 0) else 0
    hist_poc_price = float(bin_centers[hist_poc_idx])
    max_hist_vol = float(np.max(hist_total)) if (len(hist_total) > 0 and np.max(hist_total) > 0) else 1.0

    # 2. 近期趨勢籌碼分佈
    recent_buy, recent_sell = get_binned_volume(df_display)
    recent_total = recent_buy + recent_sell
    recent_poc_idx = int(np.argmax(recent_total)) if (len(recent_total) > 0 and np.max(recent_total) > 0) else 0
    recent_poc_price = float(bin_centers[recent_poc_idx])
    max_rec_vol = float(np.max(recent_total)) if (len(recent_total) > 0 and np.max(recent_total) > 0) else 1.0

    return {
        'bin_centers': bin_centers,
        'hist_buy': hist_buy,
        'hist_sell': hist_sell,
        'max_hist_vol': max_hist_vol,
        'hist_poc': hist_poc_price,
        'recent_buy': recent_buy,
        'recent_sell': recent_sell,
        'max_rec_vol': max_rec_vol,
        'recent_poc': recent_poc_price,
        'p_min': p_min,
        'p_max': p_max
    }

# =========================================================================
# 🎨 3. 右側雙層 VPVR 成交重貨柱專屬渲染模組 (向左生長)
# =========================================================================

def render_page1_dual_vpvr(fig, dual_vpvr, chart_right_edge_dt, right_gap, cfg):
    """
    在主圖右側邊界渲染雙層 VPVR 重貨柱與雙重 POC 線：
    - 錨定右邊界 (chart_right_edge_dt)，向左側延伸生長
    - 歷史底層：黃褐/紫色
    - 近期表層：青藍/粉紅
    - 雙重 POC 密集價位標籤 (右側定位)
    """
    if not dual_vpvr or not cfg.get("show_vpvr", True):
        return

    show_recent_vpvr = cfg.get("show_recent_vpvr", True)
    show_hist_vpvr = cfg.get("show_hist_vpvr", True)
    show_poc = cfg.get("show_poc", True)

    vpvr_max_width_delta = right_gap * 0.88
    b_centers = dual_vpvr['bin_centers']
    x_base = chart_right_edge_dt

    # 1. 歷史全景籌碼柱 (黃褐色 / 紫色) - 底層 (從右邊向左生長)
    if show_hist_vpvr:
        h_buy = dual_vpvr['hist_buy']
        h_sell = dual_vpvr['hist_sell']
        m_h = dual_vpvr['max_hist_vol']

        h_brown_x, h_brown_y = [], []
        h_purple_x, h_purple_y = [], []

        for i in range(len(b_centers)):
            y_lvl = b_centers[i]
            v_b = h_buy[i]
            v_s = h_sell[i]
            if (v_b + v_s) <= 0 or m_h <= 0: continue

            b_span = (vpvr_max_width_delta * 0.88) * (v_b / m_h)
            s_span = (vpvr_max_width_delta * 0.88) * (v_s / m_h)

            x_b_end = x_base - b_span
            x_s_end = x_b_end - s_span

            h_brown_x.extend([x_base, x_b_end, None])
            h_brown_y.extend([y_lvl, y_lvl, None])
            h_purple_x.extend([x_b_end, x_s_end, None])
            h_purple_y.extend([y_lvl, y_lvl, None])

        fig.add_trace(go.Scatter(
            x=h_brown_x, y=h_brown_y, mode='lines',
            line=dict(color='rgba(217, 119, 6, 0.60)', width=6.0),
            name='歷史買盤 (VPVR)', showlegend=False, hoverinfo='skip', yaxis='y1'
        ))
        fig.add_trace(go.Scatter(
            x=h_purple_x, y=h_purple_y, mode='lines',
            line=dict(color='rgba(139, 92, 246, 0.60)', width=6.0),
            name='歷史賣盤 (VPVR)', showlegend=False, hoverinfo='skip', yaxis='y1'
        ))

    # 2. 近期趨勢籌碼柱 (青藍色 / 粉紅色) - 上層 (從右邊向左生長)
    if show_recent_vpvr:
        r_buy = dual_vpvr['recent_buy']
        r_sell = dual_vpvr['recent_sell']
        m_r = dual_vpvr['max_rec_vol']

        r_teal_x, r_teal_y = [], []
        r_pink_x, r_pink_y = [], []

        for i in range(len(b_centers)):
            y_lvl = b_centers[i]
            v_b = r_buy[i]
            v_s = r_sell[i]
            if (v_b + v_s) <= 0 or m_r <= 0: continue

            b_span = (vpvr_max_width_delta * 0.96) * (v_b / m_r)
            s_span = (vpvr_max_width_delta * 0.96) * (v_s / m_r)

            x_b_end = x_base - b_span
            x_s_end = x_b_end - s_span

            r_teal_x.extend([x_base, x_b_end, None])
            r_teal_y.extend([y_lvl, y_lvl, None])
            r_pink_x.extend([x_b_end, x_s_end, None])
            r_pink_y.extend([y_lvl, y_lvl, None])

        fig.add_trace(go.Scatter(
            x=r_teal_x, y=r_teal_y, mode='lines',
            line=dict(color='rgba(45, 212, 191, 0.88)', width=6.0),
            name='近期買盤 (VPVR)', showlegend=False, hoverinfo='skip', yaxis='y1'
        ))
        fig.add_trace(go.Scatter(
            x=r_pink_x, y=r_pink_y, mode='lines',
            line=dict(color='rgba(244, 63, 94, 0.82)', width=6.0),
            name='近期賣盤 (VPVR)', showlegend=False, hoverinfo='skip', yaxis='y1'
        ))

    # 3. POC 密集線與立體標籤 (右側定位)
    if show_poc:
        rec_poc = dual_vpvr['recent_poc']
        fig.add_hline(
            y=rec_poc, line_dash="dash", line_color="#f59e0b", line_width=1.5,
            annotation_text=f"<b>近期 POC {rec_poc:.2f}</b>",
            annotation_position="top right",
            annotation_font=dict(color="#ffffff", size=9.5, family="Arial Black"),
            annotation_bgcolor="#b45309", annotation_bordercolor="#f59e0b",
            yref='y1'
        )

        hist_poc = dual_vpvr['hist_poc']
        fig.add_hline(
            y=hist_poc, line_dash="dot", line_color="rgba(168, 85, 247, 0.65)", line_width=1.2,
            annotation_text=f"<b>歷史 POC {hist_poc:.2f}</b>",
            annotation_position="bottom right",
            annotation_font=dict(color="#ffffff", size=9.0, family="Arial Black"),
            annotation_bgcolor="rgba(107, 33, 168, 0.85)", annotation_bordercolor="#a855f7",
            yref='y1'
        )

# =========================================================================
# 🎨 4. 主圖指標組 1 渲染模組 (MA, ANCHORZONE, VAS)
# =========================================================================

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