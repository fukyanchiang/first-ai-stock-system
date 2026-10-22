import pandas as pd
import numpy as np
import yfinance as yf
import streamlit as st
import plotly.graph_objects as go

# =========================================================================
# ⚙️ 1. 抓取 5 年週線歷史數據
# =========================================================================

@st.cache_data(ttl=3600, show_spinner=False)
def fetch_weekly_data(ticker_symbol: str):
    """
    抓取指定標的 5 年週線數據 (約 260 根週 K 線)
    """
    try:
        t = yf.Ticker(ticker_symbol)
        df = t.history(period="5y", interval="1wk")
        if df.empty or len(df) < 30:
            # 備用方案: 抓日線再轉週線
            df_daily = t.history(period="5y", interval="1d")
            if not df_daily.empty:
                df = df_daily.resample('W').agg({
                    'Open': 'first', 'High': 'max', 'Low': 'min', 'Close': 'last', 'Volume': 'sum'
                }).dropna()
        return df.dropna(subset=['Close'])
    except Exception:
        return pd.DataFrame()

# =========================================================================
# 📐 2. 線性回歸中心線與 ±2σ 極端通道運算引擎
# =========================================================================

def compute_regression_channel_metrics(df_weekly: pd.DataFrame):
    """
    計算 5 年週線線性回歸通道、R²、斜率、距中線百分比、波段買賣信號
    """
    if df_weekly.empty or len(df_weekly) < 30:
        return {}, df_weekly

    data = df_weekly.copy()
    
    # 取最多 260 根週線 (5 年)
    if len(data) > 260:
        data = data.tail(260).copy()
    
    n = len(data)
    x = np.arange(n)
    y = data['Close'].values

    # 1. 一元線性回歸: y = slope * x + intercept
    slope, intercept = np.polyfit(x, y, 1)
    center_line = slope * x + intercept
    residuals = y - center_line
    std_err = np.std(residuals)

    # 2. 統計指標: R² 判定係數
    ss_res = np.sum(residuals ** 2)
    ss_tot = np.sum((y - np.mean(y)) ** 2)
    r_squared = 1.0 - (ss_res / ss_tot) if ss_tot > 0 else 0.0

    # 3. 每週斜率百分比 (相對於均價)
    mean_price = np.mean(y)
    slope_pct_per_week = (slope / mean_price) * 100 if mean_price > 0 else 0.0

    # 4. 軌道帶 (中心線 ±2σ)
    data['LR_Center'] = center_line
    data['LR_Upper_2s'] = center_line + 2.0 * std_err
    data['LR_Lower_2s'] = center_line - 2.0 * std_err
    data['LR_Upper_1s'] = center_line + 1.0 * std_err
    data['LR_Lower_1s'] = center_line - 1.0 * std_err

    # 5. 最新價距中線距離 (%)
    curr_close = float(data['Close'].iloc[-1])
    curr_center = float(data['LR_Center'].iloc[-1])
    dist_from_center_pct = ((curr_close - curr_center) / curr_center) * 100

    # 6. 快線 (EMA 8週) 與 慢線 (EMA 21週)
    data['Fast_MA'] = data['Close'].ewm(span=8, adjust=False).mean()
    data['Slow_MA'] = data['Close'].ewm(span=21, adjust=False).mean()

    # 7. 波段買賣訊號 (快慢線黃金交叉 / 死亡交叉 + 通道極值輔助)
    data['Buy_Signal'] = (data['Fast_MA'] > data['Slow_MA']) & (data['Fast_MA'].shift(1) <= data['Slow_MA'].shift(1))
    data['Sell_Signal'] = (data['Fast_MA'] < data['Slow_MA']) & (data['Fast_MA'].shift(1) >= data['Slow_MA'].shift(1))

    # 8. 週期回報率統計 (1W, 1M, 3M, YTD)
    chg_1w = ((data['Close'].iloc[-1] / data['Close'].iloc[-2] - 1) * 100) if len(data) >= 2 else 0.0
    chg_1m = ((data['Close'].iloc[-1] / data['Close'].iloc[-5] - 1) * 100) if len(data) >= 5 else 0.0
    chg_3m = ((data['Close'].iloc[-1] / data['Close'].iloc[-13] - 1) * 100) if len(data) >= 13 else 0.0

    # YTD 計算
    curr_year = data.index[-1].year
    ytd_data = data[data.index.year == curr_year]
    chg_ytd = ((data['Close'].iloc[-1] / ytd_data['Close'].iloc[0] - 1) * 100) if not ytd_data.empty else 0.0

    # 趨勢狀態判定
    if curr_close > data['LR_Upper_2s'].iloc[-1]:
        trend_status = "⚠️ 極端超買 (觸及 +2σ 壓力區)"
    elif curr_close < data['LR_Lower_2s'].iloc[-1]:
        trend_status = "🚀 極端超跌 (觸及 -2σ 支撐區)"
    elif data['Fast_MA'].iloc[-1] > data['Slow_MA'].iloc[-1]:
        trend_status = "🟢 中線多頭蓄勢 (觀望待突破)"
    else:
        trend_status = "🔴 中線回調整理"

    metrics = {
        'current_price': curr_close,
        'center_price': curr_center,
        'r_squared': r_squared,
        'slope_pct': slope_pct_per_week,
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
# 🎨 3. 高清 5 年週線回歸通道圖表渲染
# =========================================================================

def render_regression_plotly_chart(data: pd.DataFrame, metrics: dict, symbol_name: str, show_signals=True):
    """
    繪製精緻的 Plotly 暗色 5 年線性回歸通道圖表 (100% 契合截圖設計)
    """
    if data.empty or 'LR_Center' not in data.columns:
        return go.Figure()

    fig = go.Figure()

    # 1. ±2σ 外部極端軌道 (虛線與填充帶)
    fig.add_trace(go.Scatter(
        x=data.index, y=data['LR_Upper_2s'],
        mode='lines', line=dict(color='rgba(255, 107, 107, 0.45)', width=1.2, dash='dot'),
        name='+2σ 極端壓力', hoverinfo='skip'
    ))
    fig.add_trace(go.Scatter(
        x=data.index, y=data['LR_Lower_2s'],
        mode='lines', line=dict(color='rgba(0, 255, 136, 0.45)', width=1.2, dash='dot'),
        fill='tonexty', fillcolor='rgba(30, 41, 59, 0.25)',  # 通道半透明背景
        name='-2σ 極端支撐', hoverinfo='skip'
    ))

    # 2. 線性回歸中心線 (亮紫色實線)
    fig.add_trace(go.Scatter(
        x=data.index, y=data['LR_Center'],
        mode='lines', line=dict(color='#d946ef', width=2.0),
        name='線性回歸中線', hovertemplate='LR中線: %{y:.2f}<extra></extra>'
    ))

    # 3. 慢線 (橙色/黃色)
    fig.add_trace(go.Scatter(
        x=data.index, y=data['Slow_MA'],
        mode='lines', line=dict(color='#f59e0b', width=1.5),
        name='慢線 (21W)', hovertemplate='慢線: %{y:.2f}<extra></extra>'
    ))

    # 4. 快線 (青藍色)
    fig.add_trace(go.Scatter(
        x=data.index, y=data['Fast_MA'],
        mode='lines', line=dict(color='#06b6d4', width=1.8),
        name='快線 (8W)', hovertemplate='快線: %{y:.2f}<extra></extra>'
    ))

    # 5. 週 K 線圖 (Candlestick)
    fig.add_trace(go.Candlestick(
        x=data.index,
        open=data['Open'], high=data['High'],
        low=data['Low'], close=data['Close'],
        name='週K線',
        increasing=dict(line=dict(color='#00ff88', width=1), fillcolor='#00ff88'),
        decreasing=dict(line=dict(color='#ff3366', width=1), fillcolor='#ff3366')
    ))

    # 6. 買賣訊號標記 (綠色買入 ▲ / 紅色賣出 ▼)
    if show_signals:
        buy_df = data[data['Buy_Signal']]
        sell_df = data[data['Sell_Signal']]

        if not buy_df.empty:
            fig.add_trace(go.Scatter(
                x=buy_df.index, y=buy_df['Low'] * 0.96,
                mode='markers+text',
                marker=dict(symbol='triangle-up', size=11, color='#00ff88'),
                text=['買入'] * len(buy_df),
                textposition='bottom center',
                textfont=dict(color='#00ff88', size=11, family='Arial Black'),
                name='買入訊號', hoverinfo='x+text'
            ))

        if not sell_df.empty:
            fig.add_trace(go.Scatter(
                x=sell_df.index, y=sell_df['High'] * 1.04,
                mode='markers+text',
                marker=dict(symbol='triangle-down', size=11, color='#f43f5e'),
                text=['賣出'] * len(sell_df),
                textposition='top center',
                textfont=dict(color='#f43f5e', size=11, family='Arial Black'),
                name='賣出訊號', hoverinfo='x+text'
            ))

    # 佈局與尺寸設定
    fig.update_layout(
        template='plotly_dark',
        paper_bgcolor='#0e1117',
        plot_bgcolor='#131722',
        xaxis_rangeslider_visible=False,
        margin=dict(l=35, r=50, t=20, b=30),
        height=580,
        hovermode='x unified',
        hoverlabel=dict(bgcolor='#1e293b', font_size=12),
        legend=dict(
            orientation="h", yanchor="bottom", y=1.02, xanchor="left", x=0.0,
            font=dict(color="#cbd5e1", size=11), bgcolor="rgba(0,0,0,0)"
        )
    )

    fig.update_xaxes(showgrid=True, gridcolor='#1e293b', zeroline=False)
    fig.update_yaxes(showgrid=True, gridcolor='#1e293b', zeroline=False, side='right')

    return fig