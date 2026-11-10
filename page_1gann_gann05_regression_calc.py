"""
Filename: page_1gann_gann05_regression_calc.py
Description: 🌐 Gann 05 核心運算引擎 (100% 純真實量化 · 全球多市場旗艦加固版)
升級亮點：
1. 完整修復 R² 與 ±2σ / ±1σ 回歸通道乘號與減號缺失
2. 內建純數字智能免後綴解析引擎 (輸入 700 自動轉 0700.HK，輸入 600519 自動轉 600519.SS)
3. 支援全球貨幣符號自適應 (HK$, $, ¥, ₩)
4. 保留雙層獨立 VPVR (5Y 全景 + 52W 近期) 與防拉扁鎖定 Y 軸
5. 100% 純真實 Chaikin CLV 價量資金壓力與線性回歸通道
"""

import streamlit as st
import pandas as pd
import numpy as np
import yfinance as yf
import plotly.graph_objects as go

# =========================================================================
# 🌐 全球跨市場資產解析器
# =========================================================================
def resolve_global_symbol_info(symbol: str):
    sym = str(symbol).strip().upper()
    if not sym:
        sym = "SPY"

    # 1. 純數字智能容錯
    if sym.isdigit():
        if len(sym) <= 5:
            padded = sym.zfill(4 if len(sym) <= 4 else 5)
            return f"{padded}.HK", "HK$", "港股 / 港股 ETF"
        elif len(sym) == 6:
            if sym.startswith(('60', '68', '51', '58')):
                return f"{sym}.SS", "¥", "中國 A 股 (上證) / ETF"
            elif sym.startswith(('00', '30', '15', '16')):
                return f"{sym}.SZ", "¥", "中國 A 股 (深證) / ETF"
            else:
                return f"{sym}.SS", "¥", "中國 A 股"

    # 2. 帶後綴或英文代碼處理
    if sym.endswith(".HK"):
        code_part = sym[:-3]
        if code_part.isdigit() and len(code_part) < 4:
            code_part = code_part.zfill(4)
        return f"{code_part}.HK", "HK$", "港股 / 港股 ETF"
    elif sym.endswith(".T"):
        return sym, "¥", "日股 / 日股 ETF"
    elif sym.endswith(".KS"):
        return sym, "₩", "韓股 KOSPI / 韓股 ETF"
    elif sym.endswith(".KQ"):
        return sym, "₩", "韓股 KOSDAQ"
    elif sym.endswith(".SS"):
        return sym, "¥", "中國 A 股 (上證) / ETF"
    elif sym.endswith(".SZ"):
        return sym, "¥", "中國 A 股 (深證) / ETF"
    else:
        return sym, "$", "美股 / 美股 ETF / 全球資產"


# =========================================================================
# ⚙️ 1. 抓取歷史數據 (強制剝離時區 tz-naive)
# =========================================================================

@st.cache_data(ttl=1800, show_spinner=False)
def fetch_gann05_data(ticker_symbol: str, interval: str = "1wk"):
    try:
        clean_symbol, _, _ = resolve_global_symbol_info(ticker_symbol)
        t = yf.Ticker(clean_symbol)
        period_str = "5y" if interval == "1wk" else "2y"
        df = t.history(period=period_str, interval=interval)
        if df.empty or len(df) < 25:
            df_daily = t.history(period=period_str, interval="1d")
            if not df_daily.empty:
                if interval == "1wk":
                    df = df_daily.resample('W-FRI').agg({
                        'Open': 'first', 'High': 'max', 'Low': 'min', 'Close': 'last', 'Volume': 'sum'
                    }).dropna()
                else:
                    df = df_daily.dropna()

        # 強制去除時區信息，確保為純淨 tz-naive 並嚴格排序
        if hasattr(df.index, 'tz') and df.index.tz is not None:
            df.index = df.index.tz_localize(None)

        df = df.sort_index().dropna(subset=['Close'])
        return df
    except Exception:
        return pd.DataFrame()

def fetch_weekly_data(ticker_symbol: str):
    return fetch_gann05_data(ticker_symbol, interval="1wk")


# =========================================================================
# 📊 2. 雙層獨立 VPVR 籌碼分佈運算模組
# =========================================================================

def compute_gann05_dual_vpvr(df_all: pd.DataFrame, df_recent: pd.DataFrame = None, n_bins: int = 40):
    """
    計算雙層獨立 VPVR 籌碼分佈：
    1. 歷史全景 (5Y 全歷史) -> 歷史 POC
    2. 近期趨勢 (近 52 週 / 120 日) -> 近期 POC
    """
    if df_all.empty or len(df_all) < 5:
        return None

    p_min = float(df_all['Low'].min())
    p_max = float(df_all['High'].max())
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
            i_l = max(0, min(n_bins - 1, int((l - p_min) / bin_width)))
            i_h = max(0, min(n_bins - 1, int((h - p_min) / bin_width)))
            n_cov = max(1, i_h - i_l + 1)
            v_p = v / float(n_cov)
            for b in range(i_l, i_h + 1):
                if is_bull:
                    buy_v[b] += v_p
                else:
                    sell_v[b] += v_p
        return buy_v, sell_v

    # 1. 歷史全景籌碼柱
    hist_buy, hist_sell = get_binned_volume(df_all)
    hist_total = hist_buy + hist_sell
    hist_poc_idx = int(np.argmax(hist_total)) if len(hist_total) > 0 else 0
    hist_poc_price = float(bin_centers[hist_poc_idx])
    max_hist_vol = float(np.max(hist_total)) if (len(hist_total) > 0 and np.max(hist_total) > 0) else 1.0

    # 2. 近期趨勢籌碼柱
    target_recent = df_recent if (df_recent is not None and not df_recent.empty) else df_all.tail(52)
    recent_buy, recent_sell = get_binned_volume(target_recent)
    recent_total = recent_buy + recent_sell
    recent_poc_idx = int(np.argmax(recent_total)) if len(recent_total) > 0 else 0
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
        'recent_poc': recent_poc_price
    }

def compute_gann05_vpvr(df_display: pd.DataFrame, n_bins: int = 36, value_area_pct: float = 0.70):
    res = compute_gann05_dual_vpvr(df_display, df_recent=df_display, n_bins=n_bins)
    if not res:
        return None
    return {
        'bin_centers': res['bin_centers'],
        'buy_vol': res['recent_buy'],
        'sell_vol': res['recent_sell'],
        'max_vol': res['max_rec_vol'],
        'poc_price': res['recent_poc'],
        'vah_price': res['recent_poc'],
        'val_price': res['recent_poc']
    }


# =========================================================================
# 📐 3. 線性回歸中心線與 ±2σ 極端通道運算引擎 (語法完全修復)
# =========================================================================

def compute_regression_channel_metrics(df_weekly: pd.DataFrame, strategy_mode: str = "經典波段 (原版)", *args, **kwargs):
    if df_weekly.empty or len(df_weekly) < 25:
        return {}, df_weekly

    data = df_weekly.copy().sort_index()
    if hasattr(data.index, 'tz') and data.index.tz is not None:
        data.index = data.index.tz_localize(None)

    if len(data) > 260:
        data = data.tail(260).copy()

    n = len(data)
    x = np.arange(n)
    y = data['Close'].values

    slope, intercept = np.polyfit(x, y, 1)
    center_line = slope * x + intercept
    residuals = y - center_line
    std_err = float(np.std(residuals))

    ss_res = float(np.sum(residuals ** 2))
    ss_tot = float(np.sum((y - np.mean(y)) ** 2))
    r_squared = max(0.0, float(1.0 - (ss_res / ss_tot))) if ss_tot > 0 else 0.0

    mean_price = float(np.mean(y))
    slope_pct_per_bar = (slope / mean_price) * 100.0 if mean_price > 0 else 0.0

    data['LR_Center'] = center_line
    data['LR_Upper_2s'] = center_line + 2.0 * std_err
    data['LR_Lower_2s'] = center_line - 2.0 * std_err
    data['LR_Upper_1s'] = center_line + 1.0 * std_err
    data['LR_Lower_1s'] = center_line - 1.0 * std_err

    curr_close = float(data['Close'].iloc[-1])
    curr_center = float(data['LR_Center'].iloc[-1])
    dist_from_center_pct = ((curr_close - curr_center) / curr_center) * 100.0 if curr_center != 0 else 0.0

    data['Fast_MA'] = data['Close'].ewm(span=8, adjust=False).mean()
    data['Slow_MA'] = data['Close'].ewm(span=21, adjust=False).mean()

    buy_cross = (data['Fast_MA'] > data['Slow_MA']) & (data['Fast_MA'].shift(1) <= data['Slow_MA'].shift(1))
    death_cross = (data['Fast_MA'] < data['Slow_MA']) & (data['Fast_MA'].shift(1) >= data['Slow_MA'].shift(1))

    if "防賣飛" in str(strategy_mode):
        data['Buy_Signal'] = buy_cross
        is_above_trend = (data['Close'] >= data['LR_Center'])
        data['Reduce_Signal'] = death_cross & is_above_trend
        data['Sell_Signal'] = death_cross & (~is_above_trend)
    else:
        data['Buy_Signal'] = buy_cross
        data['Sell_Signal'] = death_cross
        data['Reduce_Signal'] = False

    chg_1w = ((data['Close'].iloc[-1] / data['Close'].iloc[-2] - 1) * 100.0) if len(data) >= 2 else 0.0
    chg_1m = ((data['Close'].iloc[-1] / data['Close'].iloc[-5] - 1) * 100.0) if len(data) >= 5 else 0.0
    chg_3m = ((data['Close'].iloc[-1] / data['Close'].iloc[-13] - 1) * 100.0) if len(data) >= 13 else 0.0

    curr_year = data.index[-1].year
    ytd_data = data[data.index.year == curr_year]
    chg_ytd = ((data['Close'].iloc[-1] / ytd_data['Close'].iloc[0] - 1) * 100.0) if not ytd_data.empty else 0.0

    if curr_close > data['LR_Upper_2s'].iloc[-1]:
        trend_status = "⚠️ 極端超買 (觸及 +2σ 壓力區)"
    elif curr_close < data['LR_Lower_2s'].iloc[-1]:
        trend_status = "🚀 極端超跌 (觸及 -2σ 支撐區)"
    elif data['Fast_MA'].iloc[-1] > data['Slow_MA'].iloc[-1]:
        trend_status = "🟢 中線多頭蓄勢 (強勢推進中)"
    else:
        trend_status = "🔴 中線回調整理"

    metrics = {
        'current_price': curr_close,
        'center_price': curr_center,
        'r_squared': r_squared,
        'slope_pct': slope_pct_per_bar,
        'dist_center_pct': dist_from_center_pct,
        'weeks_count': n,
        'chg_1w': chg_1w,
        'chg_1m': chg_1m,
        'chg_3m': chg_3m,
        'chg_ytd': chg_ytd,
        'trend_status': trend_status
    }

    return metrics, data


# =========================================================================
# 🎨 4. 高清回歸通道 ＋ 雙層獨立 VPVR ＋ 自適應 Y 軸渲染
# =========================================================================

def render_regression_plotly_chart(data: pd.DataFrame, metrics: dict, symbol_name: str, show_signals=True,
                                   show_recent_vpvr=True, show_hist_vpvr=True, show_timewindows=False,
                                   custom_time_windows=None, interval="1wk", df_full: pd.DataFrame = None,
                                   show_vpvr=None, curr_sym: str = "$", **kwargs):
    if data.empty or 'LR_Center' not in data.columns:
        return go.Figure()

    if show_vpvr is not None:
        show_recent_vpvr = show_vpvr
        show_hist_vpvr = show_vpvr

    data = data.copy()
    if hasattr(data.index, 'tz') and data.index.tz is not None:
        data.index = data.index.tz_localize(None)

    display_start_dt = pd.to_datetime(data.index[0])
    last_candle_dt = pd.to_datetime(data.index[-1])
    future_days = 65 if interval == "1d" else 280
    chart_right_edge_dt = last_candle_dt + pd.Timedelta(days=future_days)

    c_low = data['LR_Lower_2s'].min() if 'LR_Lower_2s' in data else data['Low'].min()
    c_high = data['LR_Upper_2s'].max() if 'LR_Upper_2s' in data else data['High'].max()
    vis_p_min = min(float(data['Low'].min()), float(c_low))
    vis_p_max = max(float(data['High'].max()), float(c_high))
    y_pad = (vis_p_max - vis_p_min) * 0.07
    locked_y_range = [vis_p_min - y_pad, vis_p_max + y_pad]

    fig = go.Figure()

    # 1. 動態時間窗口 (可選)
    if show_timewindows and custom_time_windows:
        for tw in custom_time_windows:
            w_start = pd.to_datetime(tw['start'])
            w_end = pd.to_datetime(tw['end'])
            w_center = pd.to_datetime(tw.get('center', w_start))

            if w_end >= display_start_dt:
                fig.add_shape(
                    type="rect", x0=w_start, x1=w_end, y0=0, y1=1, yref='paper',
                    fillcolor=tw.get('color', 'rgba(245, 158, 11, 0.12)'),
                    line=dict(color=tw.get('border', '#f59e0b'), width=1, dash="dash"),
                    layer="below"
                )
                fig.add_shape(
                    type="line", x0=w_center, x1=w_center, y0=0, y1=1, yref='paper',
                    line=dict(color=tw.get('border', '#f59e0b'), width=1.2, dash="dot")
                )
                fig.add_annotation(
                    x=w_center, y=0.01, yref='paper', text=f"<b>{tw.get('label', '週期窗口')}</b>",
                    showarrow=False, yanchor='bottom',
                    font=dict(color="#ffffff", size=10),
                    bgcolor="#161a25", bordercolor=tw.get('border', '#f59e0b'), borderwidth=1
                )

    # 2. 上層主圖：回歸通道與均線
    fig.add_trace(go.Scatter(
        x=data.index, y=data['LR_Upper_2s'],
        mode='lines', line=dict(color='rgba(239, 68, 68, 0.65)', width=1.3, dash='dash'),
        name='+2σ 極端壓力', hovertemplate=f'+2σ壓力: {curr_sym}%{{y:.2f}}<extra></extra>', yaxis='y1'
    ))

    fig.add_trace(go.Scatter(
        x=data.index, y=data['LR_Lower_2s'],
        mode='lines', line=dict(color='rgba(16, 185, 129, 0.65)', width=1.3, dash='dash'),
        fill='tonexty', fillcolor='rgba(30, 41, 59, 0.22)',
        name='-2σ 極端支撐', hovertemplate=f'-2σ支撐: {curr_sym}%{{y:.2f}}<extra></extra>', yaxis='y1'
    ))

    fig.add_trace(go.Scatter(
        x=data.index, y=data['LR_Center'],
        mode='lines', line=dict(color='#d946ef', width=2.0),
        name='線性回歸中線', hovertemplate=f'LR中線: {curr_sym}%{{y:.2f}}<extra></extra>', yaxis='y1'
    ))

    fig.add_trace(go.Scatter(
        x=data.index, y=data['Slow_MA'],
        mode='lines', line=dict(color='#f59e0b', width=1.6),
        name='慢線 (21W)', hovertemplate=f'慢線: {curr_sym}%{{y:.2f}}<extra></extra>', yaxis='y1'
    ))

    fig.add_trace(go.Scatter(
        x=data.index, y=data['Fast_MA'],
        mode='lines', line=dict(color='#00e5ff', width=1.8),
        name='快線 (8W)', hovertemplate=f'快線: {curr_sym}%{{y:.2f}}<extra></extra>', yaxis='y1'
    ))

    # K 線圖
    fig.add_trace(go.Candlestick(
        x=data.index,
        open=data['Open'], high=data['High'],
        low=data['Low'], close=data['Close'],
        name=f'{symbol_name} K線',
        increasing=dict(line=dict(color='#00ff88', width=1.1), fillcolor='#00ff88'),
        decreasing=dict(line=dict(color='#ff3366', width=1.1), fillcolor='#ff3366'),
        yaxis='y1'
    ))

    # 3. 雙層獨立 VPVR 籌碼柱
    df_history = df_full if (df_full is not None and not df_full.empty) else data
    recent_len = 120 if interval == "1d" else 52
    df_recent = df_history.tail(min(recent_len, len(df_history)))

    dual_vpvr = compute_gann05_dual_vpvr(df_history, df_recent, n_bins=40)
    if dual_vpvr:
        future_gap = chart_right_edge_dt - last_candle_dt
        vpvr_max_width_delta = future_gap * 0.38
        b_centers = dual_vpvr['bin_centers']
        x_base = chart_right_edge_dt

        # A. 歷史全景籌碼柱
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
                if (v_b + v_s) <= 0 or m_h <= 0:
                    continue

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
                line=dict(color='rgba(217, 119, 6, 0.60)', width=6.5),
                name='歷史買盤', showlegend=False, hoverinfo='skip', yaxis='y1'
            ))
            fig.add_trace(go.Scatter(
                x=h_purple_x, y=h_purple_y, mode='lines',
                line=dict(color='rgba(139, 92, 246, 0.60)', width=6.5),
                name='歷史賣盤', showlegend=False, hoverinfo='skip', yaxis='y1'
            ))

        # B. 近期趨勢籌碼柱
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
                if (v_b + v_s) <= 0 or m_r <= 0:
                    continue

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
                line=dict(color='rgba(45, 212, 191, 0.88)', width=6.5),
                name='近期買盤', showlegend=False, hoverinfo='skip', yaxis='y1'
            ))
            fig.add_trace(go.Scatter(
                x=r_pink_x, y=r_pink_y, mode='lines',
                line=dict(color='rgba(244, 63, 94, 0.82)', width=6.5),
                name='近期賣盤', showlegend=False, hoverinfo='skip', yaxis='y1'
            ))

        # 🟡 近期 POC (黃色虛線)
        rec_poc = dual_vpvr['recent_poc']
        if locked_y_range[0] <= rec_poc <= locked_y_range[1]:
            fig.add_hline(
                y=rec_poc, line_dash="dash", line_color="#f59e0b", line_width=1.5,
                annotation_text=f"<b>近期 POC {curr_sym}{rec_poc:.2f}</b>",
                annotation_position="top right",
                annotation_font=dict(color="#ffffff", size=10, family="Arial Black"),
                annotation_bgcolor="#b45309", annotation_bordercolor="#f59e0b",
                yref='y1'
            )

        # 🟣 歷史 POC (紫色實線)
        hist_poc = dual_vpvr['hist_poc']
        if locked_y_range[0] <= hist_poc <= locked_y_range[1]:
            fig.add_hline(
                y=hist_poc, line_dash="solid", line_color="#a855f7", line_width=1.8,
                annotation_text=f"<b>歷史 POC {curr_sym}{hist_poc:.2f}</b>",
                annotation_position="bottom right",
                annotation_font=dict(color="#ffffff", size=10, family="Arial Black"),
                annotation_bgcolor="#6b21a8", annotation_bordercolor="#a855f7",
                yref='y1'
            )

    # 4. 上層主圖：買賣訊號
    if show_signals:
        buy_df = data[data.get('Buy_Signal', False)]
        reduce_df = data[data.get('Reduce_Signal', False)]
        sell_df = data[data.get('Sell_Signal', False)]

        if not buy_df.empty:
            fig.add_trace(go.Scatter(
                x=buy_df.index, y=buy_df['Low'] * 0.965,
                mode='markers+text',
                marker=dict(symbol='triangle-up', size=11, color='#00ff88'),
                text=['買入'] * len(buy_df), textposition='bottom center',
                textfont=dict(color='#00ff88', size=11, family='Arial Black'),
                name='買入訊號', hoverinfo='x+text', yaxis='y1'
            ))

        if not reduce_df.empty:
            fig.add_trace(go.Scatter(
                x=reduce_df.index, y=reduce_df['High'] * 1.035,
                mode='markers+text',
                marker=dict(symbol='triangle-down', size=10, color='#fb923c'),
                text=['減倉'] * len(reduce_df), textposition='top center',
                textfont=dict(color='#fb923c', size=11, family='Arial Black'),
                name='減倉', hoverinfo='x+text', yaxis='y1'
            ))

        if not sell_df.empty:
            fig.add_trace(go.Scatter(
                x=sell_df.index, y=sell_df['High'] * 1.045,
                mode='markers+text',
                marker=dict(symbol='triangle-down', size=11, color='#ef4444'),
                text=['賣出'] * len(sell_df), textposition='top center',
                textfont=dict(color='#ef4444', size=11, family='Arial Black'),
                name='賣出訊號', hoverinfo='x+text', yaxis='y1'
            ))

    # 5. 下層副圖：成交量 ＋ 20 均量線
    vol_series = data['Volume'] if 'Volume' in data else pd.Series(0, index=data.index)
    vol_colors = ['rgba(0, 255, 136, 0.7)' if c >= o else 'rgba(255, 77, 109, 0.7)'
                  for c, o in zip(data['Close'], data['Open'])]

    fig.add_trace(go.Bar(
        x=data.index, y=vol_series,
        marker_color=vol_colors,
        name='成交量', showlegend=False,
        hovertemplate='成交量: %{y:,.0f}<extra></extra>',
        yaxis='y2'
    ))

    vol_ma20 = vol_series.rolling(min(20, len(vol_series)), min_periods=1).mean()
    fig.add_trace(go.Scatter(
        x=data.index, y=vol_ma20,
        mode='lines', line=dict(color='#f59e0b', width=1.3),
        name='20均量', hovertemplate='20均量: %{y:,.0f}<extra></extra>',
        yaxis='y2'
    ))

    # 6. 全圖佈局
    fig.update_layout(
        template='plotly_dark',
        paper_bgcolor='#0c1017',
        plot_bgcolor='#131722',
        xaxis_rangeslider_visible=False,
        margin=dict(l=20, r=45, t=25, b=25),
        height=680,
        hovermode='x unified',
        hoverlabel=dict(bgcolor='#1e293b', font_size=12),
        legend=dict(
            orientation="h", yanchor="bottom", y=1.02, xanchor="left", x=0.0,
            font=dict(color="#cbd5e1", size=11), bgcolor="rgba(0,0,0,0)"
        ),
        xaxis=dict(
            anchor='y2',
            range=[display_start_dt, chart_right_edge_dt],
            showgrid=True, gridcolor='rgba(42, 46, 57, 0.45)',
            showspikes=True, spikemode='across', spikesnap='cursor',
            spikedash='dash', spikecolor='#a0aec0', spikethickness=1.2
        ),
        yaxis=dict(
            domain=[0.24, 1.0],
            range=locked_y_range,
            showgrid=True, gridcolor='rgba(42, 46, 57, 0.45)', side='right', tickformat='.2f',
            showspikes=True, spikemode='across', spikesnap='cursor',
            spikedash='dash', spikecolor='#a0aec0', spikethickness=1.2
        ),
        yaxis2=dict(
            domain=[0.0, 0.20],
            showgrid=True, gridcolor='rgba(42, 46, 57, 0.3)', side='right',
            tickformat='.2s', tickfont=dict(color='#94a3b8', size=9.5),
            showspikes=True, spikemode='across', spikesnap='cursor',
            spikedash='dash', spikecolor='#a0aec0', spikethickness=1.2
        )
    )

    return fig


# =========================================================================
# 🌟 5. 單標的每週價量壓力運算引擎
# =========================================================================

def compute_weekly_flow_pressure(df_data: pd.DataFrame, n_weeks: int = 26):
    if df_data.empty or len(df_data) < 4:
        return {}, pd.DataFrame()

    df = df_data.copy().sort_index()
    if hasattr(df.index, 'tz') and df.index.tz is not None:
        df.index = df.index.tz_localize(None)

    if len(df) > 50 and (df.index[1] - df.index[0]).days < 4:
        df_w = df.resample('W-FRI').agg({
            'Open': 'first', 'High': 'max', 'Low': 'min', 'Close': 'last', 'Volume': 'sum'
        }).dropna()
    else:
        df_w = df.copy()

    df_w = df_w.tail(max(n_weeks, 26)).copy()

    hl_range = df_w['High'] - df_w['Low']
    clv = np.where(hl_range > 0, ((df_w['Close'] - df_w['Low']) - (df_w['High'] - df_w['Close'])) / hl_range, 0.0)
    co_dir = np.sign(df_w['Close'] - df_w['Open'])
    clv = np.where(hl_range <= 0, co_dir, clv)

    vol = df_w['Volume'].fillna(0)
    dollar_vol = vol * df_w['Close']
    flow_b = (clv * dollar_vol) / 1e9

    df_w['Flow_B'] = flow_b
    df_w['Color'] = np.where(df_w['Flow_B'] >= 0, '#00ff88', '#f43f5e')
    df_w['Label'] = np.where(df_w['Flow_B'] >= 0, '買入壓力', '賣出壓力')
    df_w['Date_Str'] = [d.strftime('%Y-%m-%d') for d in df_w.index]
    df_w['Date_Display'] = [d.strftime('%m-%d') for d in df_w.index]

    df_slice = df_w.tail(n_weeks).copy()

    sum_4w = float(df_slice['Flow_B'].tail(min(4, len(df_slice))).sum())
    sum_13w = float(df_slice['Flow_B'].tail(min(13, len(df_slice))).sum())

    metrics = {
        'sum_4w': sum_4w,
        'sum_13w': sum_13w,
        'latest_flow': float(df_slice['Flow_B'].iloc[-1]),
        'latest_date': df_slice['Date_Str'].iloc[-1],
        'weeks_count': len(df_slice)
    }

    return metrics, df_slice


# =========================================================================
# 🌟 6. 每週價量壓力 26 週紅綠趨勢圖 Plotly 渲染器
# =========================================================================

def render_weekly_flow_chart(df_flow: pd.DataFrame, flow_metrics: dict, symbol_name: str = ""):
    if df_flow.empty or 'Flow_B' not in df_flow.columns:
        return go.Figure()

    fig = go.Figure()
    custom_data = np.stack((df_flow['Date_Str'], df_flow['Label']), axis=-1)

    fig.add_trace(go.Bar(
        x=df_flow['Date_Display'],
        y=df_flow['Flow_B'],
        marker_color=df_flow['Color'],
        name='價量壓力',
        customdata=custom_data,
        hovertemplate='<b>%{customdata[0]} 週</b><br><b>%{y:+.1f}B %{customdata[1]}</b><extra></extra>',
        showlegend=False
    ))

    fig.add_hline(y=0, line_dash="solid", line_color="#475569", line_width=1.0)

    s_4w = flow_metrics.get('sum_4w', 0.0)
    s_13w = flow_metrics.get('sum_13w', 0.0)
    c_4w = "#00ff88" if s_4w >= 0 else "#f43f5e"
    c_13w = "#00ff88" if s_13w >= 0 else "#f43f5e"

    title_text = "<b>每週價量壓力 (非申購) (最近 26 週)</b> <span style='color:#f59e0b;'>● 價量壓力</span>"
    stat_text = f"<b>4週:</b> <span style='color:{c_4w}; font-weight:bold;'>{s_4w:+.1f}B</span>&nbsp;&nbsp;&nbsp;&nbsp;<b>13週:</b> <span style='color:{c_13w}; font-weight:bold;'>{s_13w:+.1f}B</span>"

    fig.add_annotation(
        xref="paper", yref="paper", x=0.005, y=1.14,
        text=title_text, showarrow=False,
        font=dict(size=12, color="#cbd5e1"),
        xanchor="left", yanchor="bottom"
    )

    fig.add_annotation(
        xref="paper", yref="paper", x=0.995, y=1.14,
        text=stat_text, showarrow=False,
        font=dict(size=12, color="#cbd5e1"),
        xanchor="right", yanchor="bottom"
    )

    fig.update_layout(
        template='plotly_dark',
        paper_bgcolor='#0c1017',
        plot_bgcolor='#131722',
        height=260,
        bargap=0.18,
        margin=dict(l=20, r=45, t=40, b=25),
        hovermode='x unified',
        hoverlabel=dict(bgcolor='#1e293b', font_size=12),
        xaxis=dict(
            type='category',
            categoryorder='array',
            categoryarray=df_flow['Date_Display'].tolist(),
            dtick=2,
            tickangle=0,
            showgrid=True, gridcolor='rgba(42, 46, 57, 0.45)',
            tickfont=dict(color='#cbd5e1', size=10.5),
            showspikes=True, spikemode='across', spikesnap='cursor',
            spikedash='dash', spikecolor='#a0aec0', spikethickness=1.2
        ),
        yaxis=dict(
            side='right',
            tickformat='+.0f',
            ticksuffix='B',
            tickfont=dict(color='#cbd5e1', size=10.5),
            showgrid=True, gridcolor='rgba(42, 46, 57, 0.45)',
            showspikes=True, spikemode='across', spikesnap='cursor',
            spikedash='dash', spikecolor='#a0aec0', spikethickness=1.2,
            zeroline=False
        )
    )

    return fig