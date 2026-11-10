"""
Filename: page_1gann_gann07_calc.py
Description: 🪐 Gann 07 核心運算引擎 (100% 全真實量化微積分旗艦版)
- 徹底修復 Git Diff 語法殘渣與乘號遺漏錯誤 (R^2, 2.0*std_err, 2.0*a_coef, 2.0*a_coef*(n-1))
- 100% 動態二階曲線擬合、微積分曲率加速度 (y''=2a) 與最新切線斜率 (y'=2ax+b)
- 徹底拔除寫死的固定預測日期，升級為以最新實盤 K 線為基準的真實費氏時空動態推算
- 雙層獨立 VPVR 籌碼分箱 (42 Bins) 與雙重 POC 水平線穿透
- 26 週真實價量壓力 (CLV 加權真實成交金額)
- 嚴格動態觸軌預警訊號 (▲ 買入 / ▼ 減倉 / ▼ 賣出)
- 內建純數字智能補全與全球貨幣 (HK$, $, ¥, ₩) 自適應
"""

import pandas as pd
import numpy as np
import yfinance as yf
import streamlit as st
import plotly.graph_objects as go

# =========================================================================
# 🌐 全球跨市場資產解析器 (含純數字智能自動補全)
# =========================================================================
def resolve_global_symbol_info(symbol: str):
    sym = str(symbol).strip().upper()
    if not sym:
        sym = "2800.HK"

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
# ⚙️ 1. 數據抓取引擎 (時區安全防禦 ＋ 純數字解析)
# =========================================================================

@st.cache_data(ttl=1800, show_spinner=False)
def fetch_gann07_data(ticker_symbol: str, period: str = "5y", interval: str = "1d"):
    try:
        clean_symbol, _, _ = resolve_global_symbol_info(ticker_symbol)
        t = yf.Ticker(clean_symbol)
        df = t.history(period=period, interval=interval)
        
        if df.empty or len(df) < 30:
            df_fallback = t.history(period="2y", interval="1d")
            if not df_fallback.empty:
                df = df_fallback
                
        if hasattr(df.index, 'tz') and df.index.tz is not None:
            df.index = df.index.tz_localize(None)

        df = df.sort_index().dropna(subset=['Close'])
        df.attrs["symbol"] = clean_symbol
        return df
    except Exception:
        return pd.DataFrame()


# =========================================================================
# 📐 2. 二階曲線回歸通道 + 曲率加速度 + 觸軌預警訊號引擎 (語法完全修復)
# =========================================================================

def compute_curved_trend_channel(df_data: pd.DataFrame, window: int = 120, future_bars: int = 25):
    if df_data.empty or len(df_data) < 30:
        return {}, df_data, pd.DataFrame()

    df = df_data.copy().sort_index()
    if hasattr(df.index, 'tz') and df.index.tz is not None:
        df.index = df.index.tz_localize(None)

    calc_window = min(window, len(df))
    df_window = df.tail(calc_window).copy()

    n = len(df_window)
    x = np.arange(n)
    y = df_window['Close'].values

    # 二階多項式擬合: y = a*x^2 + b*x + c
    poly_coeffs = np.polyfit(x, y, 2)
    poly_fit = np.poly1d(poly_coeffs)

    center_curve = poly_fit(x)
    residuals = y - center_curve
    std_err = float(np.std(residuals))

    ss_res = float(np.sum(residuals ** 2))
    ss_tot = float(np.sum((y - np.mean(y)) ** 2))
    r_squared = max(0.0, float(1.0 - (ss_res / ss_tot))) if ss_tot > 0 else 0.0

    df_window['Curve_Center'] = center_curve
    df_window['Curve_Upper'] = center_curve + 2.0 * std_err
    df_window['Curve_Lower'] = center_curve - 2.0 * std_err

    # 通道觸軌與突破預警訊號 (▲ 買入 / ▼ 減倉 / ▼ 賣出)
    touch_lower_bounce = (
        (df_window['Low'] <= df_window['Curve_Lower'] * 1.002) &
        (df_window['Close'] >= df_window['Curve_Lower']) &
        (df_window['Close'] >= df_window['Open'])
    )
    cross_above_center = (
        (df_window['Close'].shift(1) <= df_window['Curve_Center'].shift(1)) &
        (df_window['Close'] > df_window['Curve_Center'])
    )
    buy_sig = touch_lower_bounce | cross_above_center

    touch_upper_reject = (
        (df_window['High'] >= df_window['Curve_Upper'] * 0.998) &
        (df_window['Close'] < df_window['High'] * 0.995)
    )
    reduce_sig = touch_upper_reject & (~buy_sig)

    cross_below_center = (
        (df_window['Close'].shift(1) >= df_window['Curve_Center'].shift(1)) &
        (df_window['Close'] < df_window['Curve_Center'])
    )
    break_below_lower = (
        (df_window['Close'] < df_window['Curve_Lower']) &
        (df_window['Close'].shift(1) >= df_window['Curve_Lower'].shift(1))
    )
    sell_sig = (cross_below_center | break_below_lower) & (~reduce_sig) & (~buy_sig)

    df_window['Buy_Signal'] = buy_sig
    df_window['Reduce_Signal'] = reduce_sig
    df_window['Sell_Signal'] = sell_sig

    # 未來拋物線延續推演 (虛線通道)
    last_dt = df_window.index[-1]
    future_dates = pd.date_range(start=last_dt + pd.Timedelta(days=1), periods=future_bars * 2, freq='B')[:future_bars]
    
    x_future = np.arange(n - 1, n + future_bars)
    future_center = poly_fit(x_future)
    future_upper = future_center + 2.0 * std_err
    future_lower = future_center - 2.0 * std_err

    proj_dates = [last_dt] + list(future_dates)
    df_future = pd.DataFrame({
        'Future_Center': future_center,
        'Future_Upper': future_upper,
        'Future_Lower': future_lower
    }, index=proj_dates)

    curr_close = float(df_window['Close'].iloc[-1])
    curr_center = float(df_window['Curve_Center'].iloc[-1])
    curr_upper = float(df_window['Curve_Upper'].iloc[-1])
    curr_lower = float(df_window['Curve_Lower'].iloc[-1])

    # 通道動態分位 %B
    ch_width = curr_upper - curr_lower
    pct_b = ((curr_close - curr_lower) / ch_width * 100.0) if ch_width > 0 else 50.0
    dist_center_pct = ((curr_close - curr_center) / curr_center * 100.0) if curr_center > 0 else 0.0

    if pct_b >= 95.0:
        band_status = "⚠️ 觸及上軌 (極端超買 · 慎防見頂回撤)"
        band_color = "#ef4444"
    elif pct_b >= 50.0:
        band_status = "🟢 強勢多頭 (中上軌間加速推進)"
        band_color = "#00ff88"
    elif pct_b >= 15.0:
        band_status = "⚖️ 弱勢整理 (回踩中軌蓄勢)"
        band_color = "#38bdf8"
    else:
        band_status = "🚀 觸及下軌 (極端超跌 · 圓弧底托底買點)"
        band_color = "#f59e0b"

    # 微積分曲率加速度 (y'' = 2a) 與切線斜率 (y' = 2ax + b)
    a_coef = poly_coeffs[0]
    accel_val = 2.0 * a_coef
    tangent_slope = 2.0 * a_coef * (n - 1) + poly_coeffs[1]
    slope_pct_per_bar = (tangent_slope / curr_close * 100.0) if curr_close > 0 else 0.0

    if accel_val > 0.001:
        if pct_b < 45.0:
            curve_shape = "🌱 圓弧底打樁托底 (具向上正加速度)"
            curve_shape_color = "#00ff88"
        else:
            curve_shape = "🚀 拋物線加速主升浪 (曲率共振向上)"
            curve_shape_color = "#00ff88"
    elif accel_val < -0.001:
        if pct_b > 55.0:
            curve_shape = "⚠️ 圓弧頂減速滯漲 (上升加速度耗盡 · 慎防拐頭)"
            curve_shape_color = "#f43f5e"
        else:
            curve_shape = "⚡ 拋物線破位下殺 (加速探底中)"
            curve_shape_color = "#f43f5e"
    else:
        curve_shape = "📈 平穩多項式通道 (線性勻速延伸)"
        curve_shape_color = "#38bdf8"

    metrics = {
        'window_bars': calc_window,
        'current_price': curr_close,
        'upper_price': curr_upper,
        'center_price': curr_center,
        'lower_price': curr_lower,
        'r_squared': r_squared,
        'std_err': std_err,
        'pct_b': pct_b,
        'dist_center_pct': dist_center_pct,
        'band_status': band_status,
        'band_color': band_color,
        'curve_shape': curve_shape,
        'curve_shape_color': curve_shape_color,
        'accel_val': accel_val,
        'slope_pct': slope_pct_per_bar,
        'curvature_a': a_coef
    }

    return metrics, df_window, df_future


# =========================================================================
# 📊 3. 雙層分離 VPVR 籌碼分佈 (近期 120 根 + 歷史全景雙分佈)
# =========================================================================

def compute_dual_vpvr(df_all: pd.DataFrame, df_window: pd.DataFrame, n_bins: int = 42):
    if df_window.empty or len(df_window) < 10:
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

    # 1. 歷史全景籌碼分佈
    hist_buy, hist_sell = get_binned_volume(df_all)
    hist_total = hist_buy + hist_sell
    hist_poc_idx = int(np.argmax(hist_total)) if len(hist_total) > 0 else 0
    hist_poc_price = float(bin_centers[hist_poc_idx])
    max_hist_vol = float(np.max(hist_total)) if (len(hist_total) > 0 and np.max(hist_total) > 0) else 1.0

    # 2. 近期 120 根趨勢籌碼分佈
    recent_buy, recent_sell = get_binned_volume(df_window)
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


# =========================================================================
# 🎨 4. 高清二階曲線通道 ＋ 訊號標記 ＋ 自適應 Y 軸渲染 (全動態時空推演)
# =========================================================================

def render_curved_trend_plotly(df_display: pd.DataFrame, df_window: pd.DataFrame, df_future: pd.DataFrame,
                               curve_metrics: dict, dual_vpvr: dict, symbol_name: str = "",
                               show_signals: bool = True, show_timewindows: bool = True,
                               show_recent_vpvr: bool = True, show_hist_vpvr: bool = True,
                               curr_sym: str = "$"):
    if df_display.empty or 'Curve_Center' not in df_window.columns:
        return go.Figure()

    display_start_dt = pd.to_datetime(df_display.index[0])
    last_candle_dt = pd.to_datetime(df_display.index[-1])
    chart_right_edge_dt = pd.to_datetime(df_future.index[-1]) + pd.Timedelta(days=25)

    # 自適應 Y 軸範圍計算
    common_idx = df_display.index.intersection(df_window.index)
    if not common_idx.empty:
        c_low = df_window.loc[common_idx, 'Curve_Lower'].min()
        c_high = df_window.loc[common_idx, 'Curve_Upper'].max()
    else:
        c_low = df_display['Low'].min()
        c_high = df_display['High'].max()

    vis_p_min = min(float(df_display['Low'].min()), float(c_low))
    vis_p_max = max(float(df_display['High'].max()), float(c_high))

    if not df_future.empty:
        vis_p_min = min(vis_p_min, float(df_future['Future_Lower'].min()))
        vis_p_max = max(vis_p_max, float(df_future['Future_Upper'].max()))

    y_pad = (vis_p_max - vis_p_min) * 0.08
    locked_y_range = [vis_p_min - y_pad, vis_p_max + y_pad]

    fig = go.Figure()

    # 1. 🌟 拔除寫死固定日期，改為基於實盤最新 K 棒之動態費氏時空光錐推算
    if show_timewindows:
        tw_1 = last_candle_dt + pd.Timedelta(days=21)
        tw_2 = last_candle_dt + pd.Timedelta(days=34)
        tw_3 = last_candle_dt + pd.Timedelta(days=55)

        time_windows = [
            {"start": tw_1 - pd.Timedelta(days=2), "end": tw_1 + pd.Timedelta(days=2), "center": tw_1, "label": f"▲ 頂部峰值 {tw_1.strftime('%m/%d')}", "color": "rgba(245, 158, 11, 0.12)", "border": "#f59e0b"},
            {"start": tw_2 - pd.Timedelta(days=3), "end": tw_2 + pd.Timedelta(days=3), "center": tw_2, "label": f"⏳ 尋底過渡 {tw_2.strftime('%m/%d')}", "color": "rgba(168, 85, 247, 0.12)", "border": "#a855f7"},
            {"start": tw_3 - pd.Timedelta(days=3), "end": tw_3 + pd.Timedelta(days=3), "center": tw_3, "label": f"▼ 週期谷底 {tw_3.strftime('%m/%d')}", "color": "rgba(16, 185, 129, 0.12)", "border": "#10b981"}
        ]
        for tw in time_windows:
            w_start = tw['start']
            w_end = tw['end']
            w_center = tw['center']

            if w_end >= display_start_dt:
                fig.add_shape(
                    type="rect", x0=w_start, x1=w_end, y0=0, y1=1, yref='paper',
                    fillcolor=tw['color'], line=dict(color=tw['border'], width=1, dash="dash"),
                    layer="below"
                )
                fig.add_shape(
                    type="line", x0=w_center, x1=w_center, y0=0, y1=1, yref='paper',
                    line=dict(color=tw['border'], width=1.2, dash="dot")
                )
                fig.add_annotation(
                    x=w_center, y=0.01, yref='paper', text=f"<b>{tw['label']}</b>",
                    showarrow=False, yanchor='bottom',
                    font=dict(color="#ffffff", size=10),
                    bgcolor="#161a25", bordercolor=tw['border'], borderwidth=1
                )

    # 2. 曲線實體通道 + 雙層薄霧填色
    fig.add_trace(go.Scatter(
        x=df_window.index, y=df_window['Curve_Lower'],
        mode='lines', line=dict(color='#ff4d6d', width=2.0),
        name='下軌', hovertemplate=f'曲線下軌: {curr_sym}%{{y:.2f}}<extra></extra>', yaxis='y1'
    ))

    fig.add_trace(go.Scatter(
        x=df_window.index, y=df_window['Curve_Center'],
        mode='lines', line=dict(color='#3b82f6', width=2.0),
        fill='tonexty', fillcolor='rgba(255, 77, 109, 0.08)',
        name='中線', hovertemplate=f'曲線中線: {curr_sym}%{{y:.2f}}<extra></extra>', yaxis='y1'
    ))

    fig.add_trace(go.Scatter(
        x=df_window.index, y=df_window['Curve_Upper'],
        mode='lines', line=dict(color='#00e5ff', width=2.0),
        fill='tonexty', fillcolor='rgba(0, 229, 255, 0.08)',
        name='上軌', hovertemplate=f'曲線上軌: {curr_sym}%{{y:.2f}}<extra></extra>', yaxis='y1'
    ))

    # 3. 未來虛線推演 + 喇叭口光錐 + 三顆端點圓點
    if not df_future.empty:
        fig.add_trace(go.Scatter(
            x=df_future.index, y=df_future['Future_Lower'],
            mode='lines', line=dict(color='#ff4d6d', width=1.5, dash='dot'),
            showlegend=False, hovertemplate=f'未來下軌推演: {curr_sym}%{{y:.2f}}<extra></extra>', yaxis='y1'
        ))

        fig.add_trace(go.Scatter(
            x=df_future.index, y=df_future['Future_Center'],
            mode='lines', line=dict(color='#3b82f6', width=1.5, dash='dot'),
            fill='tonexty', fillcolor='rgba(255, 77, 109, 0.05)',
            showlegend=False, hovertemplate=f'未來中線推演: {curr_sym}%{{y:.2f}}<extra></extra>', yaxis='y1'
        ))

        fig.add_trace(go.Scatter(
            x=df_future.index, y=df_future['Future_Upper'],
            mode='lines', line=dict(color='#00e5ff', width=1.5, dash='dot'),
            fill='tonexty', fillcolor='rgba(0, 229, 255, 0.05)',
            showlegend=False, hovertemplate=f'未來上軌推演: {curr_sym}%{{y:.2f}}<extra></extra>', yaxis='y1'
        ))

        end_dt = df_future.index[-1]
        fig.add_trace(go.Scatter(
            x=[end_dt, end_dt, end_dt],
            y=[df_future['Future_Upper'].iloc[-1], df_future['Future_Center'].iloc[-1], df_future['Future_Lower'].iloc[-1]],
            mode='markers',
            marker=dict(size=[8, 8, 8], color=['#00e5ff', '#3b82f6', '#ff4d6d'], line=dict(width=1.8, color='#ffffff')),
            showlegend=False, hoverinfo='skip', yaxis='y1'
        ))

    # 4. K 線圖
    fig.add_trace(go.Candlestick(
        x=df_display.index,
        open=df_display['Open'], high=df_display['High'],
        low=df_display['Low'], close=df_display['Close'],
        name=symbol_name,
        increasing=dict(line=dict(color='#00ff88', width=1.2), fillcolor='#00ff88'),
        decreasing=dict(line=dict(color='#ff3366', width=1.2), fillcolor='#ff3366'),
        yaxis='y1'
    ))

    # 通道預警訊號標記 (▲ 買入 / ▼ 減倉 / ▼ 賣出)
    if show_signals:
        disp_sig = df_window.loc[df_window.index.intersection(df_display.index)]
        buy_df = disp_sig[disp_sig.get('Buy_Signal', False)]
        reduce_df = disp_sig[disp_sig.get('Reduce_Signal', False)]
        sell_df = disp_sig[disp_sig.get('Sell_Signal', False)]

        if not buy_df.empty:
            fig.add_trace(go.Scatter(
                x=buy_df.index, y=buy_df['Low'] * 0.985,
                mode='markers+text',
                marker=dict(symbol='triangle-up', size=11, color='#00ff88'),
                text=['買入'] * len(buy_df), textposition='bottom center',
                textfont=dict(color='#00ff88', size=11, family='Arial Black'),
                name='買入訊號', hoverinfo='x+text', yaxis='y1'
            ))

        if not reduce_df.empty:
            fig.add_trace(go.Scatter(
                x=reduce_df.index, y=reduce_df['High'] * 1.018,
                mode='markers+text',
                marker=dict(symbol='triangle-down', size=10, color='#fb923c'),
                text=['減倉'] * len(reduce_df), textposition='top center',
                textfont=dict(color='#fb923c', size=11, family='Arial Black'),
                name='減倉預警', hoverinfo='x+text', yaxis='y1'
            ))

        if not sell_df.empty:
            fig.add_trace(go.Scatter(
                x=sell_df.index, y=sell_df['High'] * 1.028,
                mode='markers+text',
                marker=dict(symbol='triangle-down', size=11, color='#ef4444'),
                text=['賣出'] * len(sell_df), textposition='top center',
                textfont=dict(color='#ef4444', size=11, family='Arial Black'),
                name='賣出訊號', hoverinfo='x+text', yaxis='y1'
            ))

    # 5. 右側雙層 VPVR 重貨柱 (近期 vs 歷史)
    if dual_vpvr:
        future_gap = chart_right_edge_dt - last_candle_dt
        vpvr_max_width_delta = future_gap * 0.38
        b_centers = dual_vpvr['bin_centers']
        x_base = chart_right_edge_dt

        # 歷史全景籌碼柱
        if show_hist_vpvr:
            h_buy = dual_vpvr['hist_buy']
            h_sell = dual_vpvr['hist_sell']
            m_h_vol = dual_vpvr['max_hist_vol']

            h_brown_x, h_brown_y = [], []
            h_purple_x, h_purple_y = [], []

            for i in range(len(b_centers)):
                y_lvl = b_centers[i]
                v_b = h_buy[i]
                v_s = h_sell[i]
                if (v_b + v_s) <= 0 or m_h_vol <= 0:
                    continue

                b_span = (vpvr_max_width_delta * 0.88) * (v_b / m_h_vol)
                s_span = (vpvr_max_width_delta * 0.88) * (v_s / m_h_vol)

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

        # 近期 120 根趨勢籌碼柱
        if show_recent_vpvr:
            r_buy = dual_vpvr['recent_buy']
            r_sell = dual_vpvr['recent_sell']
            m_r_vol = dual_vpvr['max_rec_vol']

            r_teal_x, r_teal_y = [], []
            r_pink_x, r_pink_y = [], []

            for i in range(len(b_centers)):
                y_lvl = b_centers[i]
                v_b = r_buy[i]
                v_s = r_sell[i]
                if (v_b + v_s) <= 0 or m_r_vol <= 0:
                    continue

                b_span = (vpvr_max_width_delta * 0.96) * (v_b / m_r_vol)
                s_span = (vpvr_max_width_delta * 0.96) * (v_s / m_r_vol)

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

        # 近期 POC (黃色虛線)
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

        # 歷史 POC (紫色實線)
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

    # 6. 下層副圖：成交量 (Volume) ＋ 20 均量線
    vol_series = df_display['Volume'] if 'Volume' in df_display else pd.Series(0, index=df_display.index)
    vol_colors = ['rgba(0, 255, 136, 0.7)' if c >= o else 'rgba(255, 77, 109, 0.7)'
                  for c, o in zip(df_display['Close'], df_display['Open'])]

    fig.add_trace(go.Bar(
        x=df_display.index, y=vol_series,
        marker_color=vol_colors,
        name='成交量', showlegend=False,
        hovertemplate='成交量: %{y:,.0f}<extra></extra>',
        yaxis='y2'
    ))

    vol_ma20 = vol_series.rolling(min(20, len(vol_series)), min_periods=1).mean()
    fig.add_trace(go.Scatter(
        x=df_display.index, y=vol_ma20,
        mode='lines', line=dict(color='#f59e0b', width=1.3),
        name='20均量', hovertemplate='20均量: %{y:,.0f}<extra></extra>',
        yaxis='y2'
    ))

    # 7. 全圖貫穿十字準星線佈局
    fig.update_layout(
        template='plotly_dark',
        paper_bgcolor='#0c1017',
        plot_bgcolor='#131722',
        xaxis_rangeslider_visible=False,
        margin=dict(l=20, r=55, t=25, b=25),
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
# 🌟 5. 單標的每週價量壓力運算引擎 (最近 26 週 + 4W/13W 累計)
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