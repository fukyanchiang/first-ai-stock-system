"""
Filename: page_1gann_gann08_calc.py
Description: 🌊 Gann 08 核心運算引擎 (全球六大多空市場萬能資產旗艦版)
- 100% 全真量化數據邏輯：基於 21 週期自然基線與真實波幅 (ATR) 動態展開四軌包絡線
- 內建全球跨市場解析器 (含純數字免後綴自動補全：700 -> 0700.HK, 600519 -> 600519.SS)，自動適配幣別 (HK$, $, ¥, ₩)
- 徹底拔除 2026-11-26 等固定日期假光柱，升級為以最新實盤 K 線為基準的真實費氏時空動態推算
- 四軌極值雲：極上(Ext+) / 近上(Near+) 紅色賣出雲 + 近下(Near-) / 極下(Ext-) 藍色抄底雲
- 最新 K 線切面上以垂直白虛線貫穿四軌彩色發光圓點 (粉/橙/綠/藍)
- 未來 15 bars 平滑自然延伸光錐 (阻尼算法防陡峭跌落)
- 現價虛線向右單向射線 (只從最新 K 線延伸至右軸徽章，不逆向橫穿歷史 K 線)
- 圖表左上角內嵌兩行原版風格數據行，右軸專屬四軌彩色徽章 + 雙重 POC 貫穿
- 雙層獨立 VPVR 籌碼柱 + 雙重 POC + 自適應防壓扁 Y 軸
- 單一 X 軸頂底貫穿十字準星線 (spikemode across)
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
    """
    解析全球六大多空市場代碼後綴，自動匹配所屬市場分類與法定貨幣符號
    支援純數字免後綴智能補全
    """
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
# ⚙️ 1. 數據抓取引擎 (支援全球六大多空市場 + 時區安全防禦)
# =========================================================================

@st.cache_data(ttl=1800, show_spinner=False)
def fetch_gann08_data(ticker_symbol: str, period: str = "5y", interval: str = "1d"):
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
# 🌊 2. 江恩自然極端四軌道與紅藍雙雲運算引擎 (含未來空間延伸)
# =========================================================================

def compute_gann_natural_extreme_channel(df_data: pd.DataFrame, span: int = 21,
                                         atr_near_mult: float = 1.25, atr_ext_mult: float = 2.45,
                                         future_bars: int = 15):
    if df_data.empty or len(df_data) < 20:
        return {}, df_data, pd.DataFrame()

    df = df_data.copy().sort_index()
    if hasattr(df.index, 'tz') and df.index.tz is not None:
        df.index = df.index.tz_localize(None)

    # 1. 計算自然基線 (Gann Baseline) 與真實波幅 ATR (100% 動態無寫死)
    basis = df['Close'].ewm(span=span, adjust=False).mean()
    
    tr1 = df['High'] - df['Low']
    tr2 = (df['High'] - df['Close'].shift(1)).abs()
    tr3 = (df['Low'] - df['Close'].shift(1)).abs()
    tr = pd.concat([tr1, tr2, tr3], axis=1).max(axis=1)
    atr = tr.ewm(span=span, adjust=False).mean()

    # 2. 生成實體四軌動態邊界
    df['Gann_Ext_Plus'] = basis + atr_ext_mult * atr
    df['Gann_Near_Plus'] = basis + atr_near_mult * atr
    df['Gann_Basis'] = basis
    df['Gann_Near_Minus'] = basis - atr_near_mult * atr
    df['Gann_Ext_Minus'] = basis - atr_ext_mult * atr

    # 3. 實戰訊號識別 (每根 K 棒即時掃描)
    bounce_lower_cloud = (
        (df['Low'] <= df['Gann_Near_Minus'] * 1.002) &
        (df['Close'] >= df['Gann_Near_Minus']) &
        (df['Close'] >= df['Open'])
    )
    cross_above_baseline = (
        (df['Close'].shift(1) <= df['Gann_Basis'].shift(1)) &
        (df['Close'] > df['Gann_Basis'])
    )
    buy_sig = bounce_lower_cloud | cross_above_baseline

    touch_upper_cloud = (
        (df['High'] >= df['Gann_Near_Plus'] * 0.998) &
        (df['Close'] < df['High'] * 0.995)
    )
    reduce_sig = touch_upper_cloud & (~buy_sig)

    cross_below_baseline = (
        (df['Close'].shift(1) >= df['Gann_Basis'].shift(1)) &
        (df['Close'] < df['Gann_Basis'])
    )
    break_ext_minus = (
        (df['Close'] < df['Gann_Ext_Minus']) &
        (df['Close'].shift(1) >= df['Gann_Ext_Minus'].shift(1))
    )
    sell_sig = (cross_below_baseline | break_ext_minus) & (~reduce_sig) & (~buy_sig)

    df['Buy_Signal'] = buy_sig
    df['Reduce_Signal'] = reduce_sig
    df['Sell_Signal'] = sell_sig

    # 4. 平滑未來延伸 (阻尼斜率算法)
    last_dt = df.index[-1]
    future_dates = pd.date_range(start=last_dt + pd.Timedelta(days=1), periods=future_bars * 2, freq='B')[:future_bars]
    raw_slope = (basis.iloc[-1] - basis.iloc[-min(5, len(basis))]) / float(min(5, len(basis)))
    last_atr = float(atr.iloc[-1])

    f_basis = []
    curr_b = float(basis.iloc[-1])
    for i in range(future_bars):
        curr_b += raw_slope * (0.82 ** i)
        f_basis.append(curr_b)

    f_ext_p = [b + atr_ext_mult * last_atr for b in f_basis]
    f_near_p = [b + atr_near_mult * last_atr for b in f_basis]
    f_near_m = [b - atr_near_mult * last_atr for b in f_basis]
    f_ext_m = [b - atr_ext_mult * last_atr for b in f_basis]

    df_future = pd.DataFrame({
        'Future_Ext_Plus': f_ext_p,
        'Future_Near_Plus': f_near_p,
        'Future_Basis': f_basis,
        'Future_Near_Minus': f_near_m,
        'Future_Ext_Minus': f_ext_m
    }, index=future_dates)

    df_future_conn = pd.concat([
        pd.DataFrame({
            'Future_Ext_Plus': [df['Gann_Ext_Plus'].iloc[-1]],
            'Future_Near_Plus': [df['Gann_Near_Plus'].iloc[-1]],
            'Future_Basis': [df['Gann_Basis'].iloc[-1]],
            'Future_Near_Minus': [df['Gann_Near_Minus'].iloc[-1]],
            'Future_Ext_Minus': [df['Gann_Ext_Minus'].iloc[-1]]
        }, index=[last_dt]),
        df_future
    ])

    curr_c = float(df['Close'].iloc[-1])
    c_ext_p = float(df['Gann_Ext_Plus'].iloc[-1])
    c_near_p = float(df['Gann_Near_Plus'].iloc[-1])
    c_basis = float(df['Gann_Basis'].iloc[-1])
    c_near_m = float(df['Gann_Near_Minus'].iloc[-1])
    c_ext_m = float(df['Gann_Ext_Minus'].iloc[-1])

    total_range = c_ext_p - c_ext_m
    pos_pct = ((curr_c - c_ext_m) / total_range * 100.0) if total_range > 0 else 50.0

    if curr_c >= c_ext_p:
        status_text = "🚨 突破極上天花板 (極端瘋狂泡沬 · 逢高止盈)"
        status_color = "#ef4444"
    elif curr_c >= c_near_p:
        status_text = "⚠️ 處於紅色預警賣出雲 (主力派發區 · 減倉觀望)"
        status_color = "#fb923c"
    elif curr_c <= c_ext_m:
        status_text = "🚀 跌破極下地板線 (恐慌極端超賣 · 逢低大膽建倉)"
        status_color = "#00ff88"
    elif curr_c <= c_near_m:
        status_text = "🌱 處於藍色黃金抄底雲 (機構吸籌區 · 逢低潛伏)"
        status_color = "#38bdf8"
    else:
        status_text = "⚖️ 處於自然中性震盪區間 (多空平衡)"
        status_color = "#cbd5e1"

    metrics = {
        'current_price': curr_c,
        'ext_plus': c_ext_p,
        'near_plus': c_near_p,
        'baseline': c_basis,
        'near_minus': c_near_m,
        'ext_minus': c_ext_m,
        'pos_pct': pos_pct,
        'status_text': status_text,
        'status_color': status_color,
        'current_atr': last_atr
    }

    return metrics, df, df_future_conn

# =========================================================================
# 📊 3. 雙層獨立 VPVR 籌碼分佈運算模組
# =========================================================================

def compute_gann08_dual_vpvr(df_all: pd.DataFrame, df_recent: pd.DataFrame, n_bins: int = 40):
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

    hist_buy, hist_sell = get_binned_volume(df_all)
    hist_total = hist_buy + hist_sell
    hist_poc_idx = int(np.argmax(hist_total)) if len(hist_total) > 0 else 0
    hist_poc_price = float(bin_centers[hist_poc_idx])
    max_hist_vol = float(np.max(hist_total)) if (len(hist_total) > 0 and np.max(hist_total) > 0) else 1.0

    target_recent = df_recent if (df_recent is not None and not df_recent.empty) else df_all.tail(120)
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

# =========================================================================
# 🎨 4. 高清自然極端通道 ＋ 全動態時間光錐 ＋ 100% 幣別自適應渲染
# =========================================================================

def render_gann_natural_extreme_plotly(df_display: pd.DataFrame, df_future: pd.DataFrame,
                                       metrics: dict, symbol_name: str,
                                       show_signals: bool = False, show_timewindows: bool = True,
                                       show_recent_vpvr: bool = True, show_hist_vpvr: bool = True,
                                       interval: str = "1d", df_full: pd.DataFrame = None):
    if df_display.empty or 'Gann_Ext_Plus' not in df_display.columns:
        return go.Figure()

    clean_sym, curr_sym, _ = resolve_global_symbol_info(symbol_name)
    display_start_dt = pd.to_datetime(df_display.index[0])
    last_candle_dt = pd.to_datetime(df_display.index[-1])
    chart_right_edge_dt = pd.to_datetime(df_future.index[-1]) + pd.Timedelta(days=15)

    c_low = min(float(df_display['Gann_Ext_Minus'].min()), float(df_future['Future_Ext_Minus'].min()))
    c_high = max(float(df_display['Gann_Ext_Plus'].max()), float(df_future['Future_Ext_Plus'].max()))
    vis_p_min = min(float(df_display['Low'].min()), c_low)
    vis_p_max = max(float(df_display['High'].max()), c_high)
    y_pad = (vis_p_max - vis_p_min) * 0.08
    locked_y_range = [vis_p_min - y_pad, vis_p_max + y_pad]

    fig = go.Figure()

    # 1. 🌟 拔除寫死假日期，全面改為依據實盤最新 K 棒之費氏時間步長動態外推
    if show_timewindows:
        step_days = 1 if interval == '1d' else (7 if interval == '1wk' else 30)
        tw_1 = last_candle_dt + pd.Timedelta(days=int(21 * step_days))
        tw_2 = last_candle_dt + pd.Timedelta(days=int(34 * step_days))
        tw_3 = last_candle_dt + pd.Timedelta(days=int(55 * step_days))

        time_windows = [
            {"start": tw_1 - pd.Timedelta(days=int(2 * step_days)), "end": tw_1 + pd.Timedelta(days=int(2 * step_days)), "center": tw_1, "label": f"▲ 頂部峰值 {tw_1.strftime('%m/%d')}", "color": "rgba(245, 158, 11, 0.12)", "border": "#f59e0b"},
            {"start": tw_2 - pd.Timedelta(days=int(3 * step_days)), "end": tw_2 + pd.Timedelta(days=int(3 * step_days)), "center": tw_2, "label": f"⏳ 尋底過渡 {tw_2.strftime('%m/%d')}", "color": "rgba(168, 85, 247, 0.12)", "border": "#a855f7"},
            {"start": tw_3 - pd.Timedelta(days=int(3 * step_days)), "end": tw_3 + pd.Timedelta(days=int(3 * step_days)), "center": tw_3, "label": f"▼ 週期谷底 {tw_3.strftime('%m/%d')}", "color": "rgba(16, 185, 129, 0.12)", "border": "#10b981"}
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

    # 2. 實體四軌道 ＋ 紅藍雙雲
    fig.add_trace(go.Scatter(
        x=df_display.index, y=df_display['Gann_Ext_Plus'],
        mode='lines', line=dict(color='#ff6b81', width=1.8),
        name='極上 (Ext+)', hovertemplate=f'極上: {curr_sym}%{{y:.2f}}<extra></extra>',
        showlegend=False, yaxis='y1'
    ))

    fig.add_trace(go.Scatter(
        x=df_display.index, y=df_display['Gann_Near_Plus'],
        mode='lines', line=dict(color='#f97316', width=1.6),
        fill='tonexty', fillcolor='rgba(244, 63, 94, 0.22)',
        name='近上 (Near+)', hovertemplate=f'近上: {curr_sym}%{{y:.2f}}<extra></extra>',
        showlegend=False, yaxis='y1'
    ))

    fig.add_trace(go.Scatter(
        x=df_display.index, y=df_display['Gann_Near_Minus'],
        mode='lines', line=dict(color='#10b981', width=1.6),
        name='近下 (Near-)', hovertemplate=f'近下: {curr_sym}%{{y:.2f}}<extra></extra>',
        showlegend=False, yaxis='y1'
    ))

    fig.add_trace(go.Scatter(
        x=df_display.index, y=df_display['Gann_Ext_Minus'],
        mode='lines', line=dict(color='#38bdf8', width=1.8),
        fill='tonexty', fillcolor='rgba(56, 189, 248, 0.22)',
        name='極下 (Ext-)', hovertemplate=f'極下: {curr_sym}%{{y:.2f}}<extra></extra>',
        showlegend=False, yaxis='y1'
    ))

    # 3. 最新 K 線切面：垂直十字白線 ＋ 四顆彩色發光小圓點
    fig.add_vline(x=last_candle_dt, line_dash="dash", line_color="rgba(255, 255, 255, 0.55)", line_width=1.2)
    fig.add_trace(go.Scatter(
        x=[last_candle_dt] * 4,
        y=[
            df_display['Gann_Ext_Plus'].iloc[-1],
            df_display['Gann_Near_Plus'].iloc[-1],
            df_display['Gann_Near_Minus'].iloc[-1],
            df_display['Gann_Ext_Minus'].iloc[-1]
        ],
        mode='markers',
        marker=dict(
            size=[8.5, 8.5, 8.5, 8.5],
            color=['#ff6b81', '#f97316', '#10b981', '#38bdf8'],
            line=dict(width=1.8, color='#ffffff')
        ),
        showlegend=False, hoverinfo='skip', yaxis='y1'
    ))

    # 4. 未來 15 bars 平滑延伸
    if not df_future.empty:
        fig.add_trace(go.Scatter(
            x=df_future.index, y=df_future['Future_Ext_Plus'],
            mode='lines', line=dict(color='#ff6b81', width=1.5, dash='dash'),
            showlegend=False, hovertemplate=f'未來極上推演: {curr_sym}%{{y:.2f}}<extra></extra>', yaxis='y1'
        ))

        fig.add_trace(go.Scatter(
            x=df_future.index, y=df_future['Future_Near_Plus'],
            mode='lines', line=dict(color='#f97316', width=1.3, dash='dash'),
            fill='tonexty', fillcolor='rgba(244, 63, 94, 0.12)',
            showlegend=False, hovertemplate=f'未來近上推演: {curr_sym}%{{y:.2f}}<extra></extra>', yaxis='y1'
        ))

        fig.add_trace(go.Scatter(
            x=df_future.index, y=df_future['Future_Near_Minus'],
            mode='lines', line=dict(color='#10b981', width=1.3, dash='dash'),
            showlegend=False, hovertemplate=f'未來近下推演: {curr_sym}%{{y:.2f}}<extra></extra>', yaxis='y1'
        ))

        fig.add_trace(go.Scatter(
            x=df_future.index, y=df_future['Future_Ext_Minus'],
            mode='lines', line=dict(color='#38bdf8', width=1.5, dash='dash'),
            fill='tonexty', fillcolor='rgba(56, 189, 248, 0.12)',
            showlegend=False, hovertemplate=f'未來極下推演: {curr_sym}%{{y:.2f}}<extra></extra>', yaxis='y1'
        ))

    # 5. 主 K 線圖
    fig.add_trace(go.Candlestick(
        x=df_display.index,
        open=df_display['Open'], high=df_display['High'],
        low=df_display['Low'], close=df_display['Close'],
        name=clean_sym,
        increasing=dict(line=dict(color='#00ff88', width=1.2), fillcolor='#00ff88'),
        decreasing=dict(line=dict(color='#ff3366', width=1.2), fillcolor='#ff3366'),
        showlegend=False,
        yaxis='y1'
    ))

    # 6. 實戰預警訊號
    if show_signals:
        buy_df = df_display[df_display.get('Buy_Signal', False)]
        reduce_df = df_display[df_display.get('Reduce_Signal', False)]
        sell_df = df_display[df_display.get('Sell_Signal', False)]

        if not buy_df.empty:
            fig.add_trace(go.Scatter(
                x=buy_df.index, y=buy_df['Low'] * 0.985,
                mode='markers',
                marker=dict(symbol='triangle-up', size=9, color='#00ff88'),
                name='買入訊號', showlegend=False, hoverinfo='x', yaxis='y1'
            ))

        if not reduce_df.empty:
            fig.add_trace(go.Scatter(
                x=reduce_df.index, y=reduce_df['High'] * 1.018,
                mode='markers',
                marker=dict(symbol='triangle-down', size=9, color='#fb923c'),
                name='減倉預警', showlegend=False, hoverinfo='x', yaxis='y1'
            ))

        if not sell_df.empty:
            fig.add_trace(go.Scatter(
                x=sell_df.index, y=sell_df['High'] * 1.028,
                mode='markers',
                marker=dict(symbol='triangle-down', size=9, color='#ef4444'),
                name='賣出訊號', showlegend=False, hoverinfo='x', yaxis='y1'
            ))

    # 7. 右側雙層獨立 VPVR 籌碼柱 ＋ 雙重 POC
    df_history = df_full if (df_full is not None and not df_full.empty) else df_display
    recent_len = 120 if interval == "1d" else 52
    df_recent = df_history.tail(min(recent_len, len(df_history)))

    dual_vpvr = compute_gann08_dual_vpvr(df_history, df_recent, n_bins=40)
    if dual_vpvr:
        future_gap = chart_right_edge_dt - last_candle_dt
        vpvr_max_width_delta = future_gap * 0.38
        b_centers = dual_vpvr['bin_centers']
        x_base = chart_right_edge_dt

        # 歷史全景籌碼柱
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

        # 近期趨勢籌碼柱
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

        # 近期 POC (黃色虛線)
        rec_poc = dual_vpvr['recent_poc']
        if locked_y_range[0] <= rec_poc <= locked_y_range[1]:
            fig.add_hline(
                y=rec_poc, line_dash="dash", line_color="#f59e0b", line_width=1.5,
                annotation_text=f"<b>POC {curr_sym}{rec_poc:.2f}</b>",
                annotation_position="top right",
                annotation_font=dict(color="#ffffff", size=9.5, family="Arial Black"),
                annotation_bgcolor="#b45309", annotation_bordercolor="#f59e0b",
                yref='y1'
            )

        # 歷史 POC (點狀虛線)
        hist_poc = dual_vpvr['hist_poc']
        if locked_y_range[0] <= hist_poc <= locked_y_range[1]:
            fig.add_hline(
                y=hist_poc, line_dash="dot", line_color="rgba(168, 85, 247, 0.65)", line_width=1.2,
                annotation_text=f"<b>歷史 POC {curr_sym}{hist_poc:.2f}</b>",
                annotation_position="bottom right",
                annotation_font=dict(color="#ffffff", size=9.0, family="Arial Black"),
                annotation_bgcolor="rgba(107, 33, 168, 0.85)", annotation_bordercolor="#a855f7",
                yref='y1'
            )

    # 8. 右側價格軸專屬「四軌彩色徽章」＋「亮色現價徽章與向右單向射線」
    axis_badges = [
        {'y': metrics['ext_plus'], 'text': f"Gann Ext+  {curr_sym}{metrics['ext_plus']:.2f}", 'bg': '#ef4444'},
        {'y': metrics['near_plus'], 'text': f"Gann Near+ {curr_sym}{metrics['near_plus']:.2f}", 'bg': '#f97316'},
        {'y': metrics['near_minus'], 'text': f"Gann Near- {curr_sym}{metrics['near_minus']:.2f}", 'bg': '#10b981'},
        {'y': metrics['ext_minus'], 'text': f"Gann Ext-  {curr_sym}{metrics['ext_minus']:.2f}", 'bg': '#0284c7'}
    ]
    for badge in axis_badges:
        if locked_y_range[0] <= badge['y'] <= locked_y_range[1]:
            fig.add_annotation(
                xref="paper", yref="y1",
                x=1.002, y=badge['y'],
                text=f"<b>{badge['text']}</b>",
                showarrow=False,
                xanchor="left", yanchor="middle",
                font=dict(color="#ffffff", size=9.0, family="Arial Black"),
                bgcolor=badge['bg'], borderpad=2.4, borderwidth=1, bordercolor="#ffffff"
            )

    curr_p = metrics['current_price']
    last_o = float(df_display['Open'].iloc[-1])
    price_badge_bg = "#00ff88" if curr_p >= last_o else "#ff3366"
    if locked_y_range[0] <= curr_p <= locked_y_range[1]:
        fig.add_annotation(
            xref="paper", yref="y1",
            x=1.002, y=curr_p,
            text=f"<b>{curr_sym}{curr_p:.2f}</b>",
            showarrow=False,
            xanchor="left", yanchor="middle",
            font=dict(color="#ffffff", size=9.5, family="Arial Black"),
            bgcolor=price_badge_bg, borderpad=2.8, borderwidth=1, bordercolor="#ffffff"
        )
        fig.add_shape(
            type="line",
            x0=last_candle_dt, x1=chart_right_edge_dt,
            y0=curr_p, y1=curr_p,
            yref='y1', xref='x',
            line=dict(color=price_badge_bg, width=1.0, dash="dot")
        )

    # 9. 圖表左上角：自適應幣別兩行抬頭
    last_dt_str = last_candle_dt.strftime('%Y年%m月%d日')
    last_h = float(df_display['High'].iloc[-1])
    last_l = float(df_display['Low'].iloc[-1])
    chg_val = curr_p - float(df_display['Close'].iloc[-2]) if len(df_display) >= 2 else 0.0
    chg_pct = (chg_val / float(df_display['Close'].iloc[-2]) * 100.0) if len(df_display) >= 2 else 0.0
    c_color = "#00ff88" if chg_val >= 0 else "#ff3366"
    last_vol = float(df_display['Volume'].iloc[-1]) if 'Volume' in df_display else 0.0

    header_line1 = (
        f"<b>{last_dt_str}</b>  "
        f"O <span style='color:#ffffff; font-weight:bold;'>{curr_sym}{last_o:.2f}</span>  "
        f"H <span style='color:#ffffff; font-weight:bold;'>{curr_sym}{last_h:.2f}</span>  "
        f"L <span style='color:#ffffff; font-weight:bold;'>{curr_sym}{last_l:.2f}</span>  "
        f"C <span style='color:{c_color}; font-weight:bold;'>{curr_sym}{curr_p:.2f}</span>  "
        f"<span style='color:{c_color}; font-weight:bold;'>{chg_val:+.2f} ({chg_pct:+.2f}%)</span>  "
        f"V <span style='color:#38bdf8; font-weight:bold;'>{last_vol/1e6:.2f}M</span>"
    )

    header_line2 = (
        f"<span style='color:#cbd5e1; font-weight:bold;'>Gann Natural Extreme</span>  "
        f"<span style='color:#ff6b81; font-weight:bold;'>● 極上 {curr_sym}{metrics['ext_plus']:.2f}</span>  "
        f"<span style='color:#38bdf8; font-weight:bold;'>● 極下 {curr_sym}{metrics['ext_minus']:.2f}</span>  "
        f"<span style='color:#f97316; font-weight:bold;'>● 近上 {curr_sym}{metrics['near_plus']:.2f}</span>  "
        f"<span style='color:#10b981; font-weight:bold;'>● 近下 {curr_sym}{metrics['near_minus']:.2f}</span>"
    )

    fig.add_annotation(
        xref="paper", yref="paper", x=0.005, y=0.995,
        text=f"{header_line1}<br>{header_line2}",
        showarrow=False, xanchor="left", yanchor="top",
        font=dict(size=11.5, family="monospace", color="#ffffff")
    )

    # 10. 下層副圖：成交量 ＋ 20 均量線
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
        showlegend=False, yaxis='y2'
    ))

    fig.add_annotation(
        xref="paper", yref="y2",
        x=1.002, y=last_vol,
        text=f"<b>{last_vol/1e6:.2f}M</b>",
        showarrow=False, xanchor="left", yanchor="middle",
        font=dict(color="#ffffff", size=9.0, family="Arial Black"),
        bgcolor=price_badge_bg, borderpad=2.2, borderwidth=1, bordercolor="#ffffff"
    )

    # 11. 全圖佈局
    fig.update_layout(
        template='plotly_dark',
        paper_bgcolor='#0c1017',
        plot_bgcolor='#131722',
        xaxis_rangeslider_visible=False,
        margin=dict(l=20, r=95, t=25, b=25),
        height=680,
        hovermode='x unified',
        hoverlabel=dict(bgcolor='#1e293b', font_size=12),
        showlegend=False,
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
            tickfont=dict(color='#94a3b8', size=10),
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
        showlegend=False,
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