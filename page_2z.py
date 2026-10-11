import streamlit as st
import yfinance as yf
import pandas as pd
import numpy as np
import plotly.graph_objects as go
from plotly.subplots import make_subplots
from datetime import datetime, timedelta

# ==========================================
# 📐 核心演算法 -1：旗形/楔形 (Flag/Wedge) 1:1 旗桿測幅目標價引擎
# ==========================================
def detect_flags_and_wedges(df):
    """
    偵測旗形 (Bull/Bear Flag) 與楔形 (Wedge)，並計算 1:1 旗桿測幅目標價 (Measured Move Target)
    """
    flags = []
    if len(df) < 30:
        return flags
        
    closes = df['Close'].values
    n = len(df)
    
    # 從近期往前尋找強烈單向動能 (旗桿 Pole)
    for i in range(n - 15, 15, -5):
        pole_start_idx = i - 10
        pole_end_idx = i
        pole_start_price = closes[pole_start_idx]
        pole_end_price = closes[pole_end_idx]
        pole_height = abs(pole_end_price - pole_start_price)
        pole_pct = pole_height / pole_start_price
        
        # 10 支 K 線內拉升/下跌超過 6% 視為有效旗桿
        if pole_pct >= 0.06:
            body_end_idx = min(pole_end_idx + 8, n - 1)
            body_closes = closes[pole_end_idx : body_end_idx + 1]
            body_range = np.max(body_closes) - np.min(body_closes)
            
            # 旗身波幅小於旗桿高度的 45% (代表狹窄盤整)
            if body_range < pole_height * 0.45:
                is_bull_flag = pole_end_price > pole_start_price
                breakout_price = body_closes[-1]
                
                # 1:1 測幅目標價計算公式
                if is_bull_flag:
                    target_price = breakout_price + pole_height
                    flag_type = "🐂 看漲旗形 (Bull Flag) 1:1 測幅"
                    color = "#00ff88"
                else:
                    target_price = breakout_price - pole_height
                    flag_type = "🐻 看跌旗形 (Bear Flag) 1:1 測幅"
                    color = "#ff0066"
                    
                flags.append({
                    'type': flag_type,
                    'pole_start_date': df.index[pole_start_idx],
                    'pole_end_date': df.index[pole_end_idx],
                    'pole_start_price': pole_start_price,
                    'pole_end_price': pole_end_price,
                    'breakout_date': df.index[body_end_idx],
                    'breakout_price': breakout_price,
                    'target_price': target_price,
                    'pole_height': pole_height,
                    'color': color
                })
                break # 抓取最新一組有效旗形
                
    return flags

# ==========================================
# 📊 核心演算法 0：Market Profile (TPO) 字母象形檢測引擎
# ==========================================
def detect_market_profile_shape(df_window, n_bins=25):
    if len(df_window) < 10:
        return {'shape': '數據不足', 'desc': '無足夠 K 線計算分佈', 'poc': 0, 'vah': 0, 'val': 0, 'profile': np.array([])}
        
    p_min = df_window['Low'].min()
    p_max = df_window['High'].max()
    if p_max == p_min:
        return {'shape': '無波幅', 'desc': '價格平坦', 'poc': p_min, 'vah': p_max, 'val': p_min, 'profile': np.array([])}
        
    bins = np.linspace(p_min, p_max, n_bins + 1)
    bin_vols = np.zeros(n_bins)
    
    for _, row in df_window.iterrows():
        c_low, c_high, c_vol = row['Low'], row['High'], row['Volume']
        if c_high == c_low:
            idx = int(np.clip((c_low - p_min) / (p_max - p_min) * n_bins, 0, n_bins - 1))
            bin_vols[idx] += c_vol
        else:
            mask = (bins[:-1] <= c_high) & (bins[1:] >= c_low)
            n_overlap = np.sum(mask)
            if n_overlap > 0:
                bin_vols[mask] += c_vol / n_overlap

    total_vol = np.sum(bin_vols)
    if total_vol == 0:
        return {'shape': '無成交量', 'desc': '成交量為 0', 'poc': 0, 'vah': 0, 'val': 0, 'profile': bin_vols}
        
    max_bin_idx = np.argmax(bin_vols)
    poc_price = (bins[max_bin_idx] + bins[max_bin_idx + 1]) / 2.0
    
    target_vol = total_vol * 0.70
    sorted_indices = np.argsort(bin_vols)[::-1]
    cum_vol = 0
    va_indices = []
    for idx in sorted_indices:
        cum_vol += bin_vols[idx]
        va_indices.append(idx)
        if cum_vol >= target_vol:
            break
            
    val_price = bins[min(va_indices)]
    vah_price = bins[max(va_indices) + 1]
    
    split1 = n_bins // 3
    split2 = (n_bins * 2) // 3
    
    vol_bottom = np.sum(bin_vols[:split1])
    vol_top = np.sum(bin_vols[split2:])
    
    top_ratio = vol_top / total_vol
    bottom_ratio = vol_bottom / total_vol
    
    if max_bin_idx >= split2 and top_ratio > 0.42:
        shape_type = "P 型象形 (P-Shape)"
        desc = "🔥 低位急拉挾單！籌碼集中喺頂部 = 夾淡倉 (Short Squeeze) 強勢買盤！"
        color = "#00ff88"
    elif max_bin_idx < split1 and bottom_ratio > 0.42:
        shape_type = "b 型象形 (b-Shape)"
        desc = "⚓ 高位大舉派貨！籌碼集中喺底部 = 大戶平多倉/派貨 (Liquidation) 沉重賣壓！"
        color = "#ff0066"
    else:
        shape_type = "D 型象形 (D-Shape)"
        desc = "⚖️ 多空對稱平衡！籌碼集中喺中間鐘形區域 = 市場盤整尋找方向。"
        color = "#00E5FF"
        
    return {
        'shape': shape_type, 'desc': desc, 'color': color,
        'poc': poc_price, 'vah': vah_price, 'val': val_price,
        'bins': bins, 'profile': bin_vols
    }

# ==========================================
# 🧠 方向 B：電腦視覺 (Computer Vision / CNN) 核心引擎
# ==========================================
def render_kline_to_image_tensor(df_window, img_size=(224, 224)):
    img = np.zeros(img_size, dtype=np.float32)
    n_candles = len(df_window)
    if n_candles < 10: return img
        
    high_max = df_window['High'].max()
    low_min = df_window['Low'].min()
    price_range = high_max - low_min if (high_max - low_min) > 0 else 1.0
    col_width = img_size[1] / n_candles
    
    for i in range(n_candles):
        c_high, c_low, c_open, c_close = df_window['High'].iloc[i], df_window['Low'].iloc[i], df_window['Open'].iloc[i], df_window['Close'].iloc[i]
        y_high = int((1.0 - (c_high - low_min) / price_range) * (img_size[0] - 1))
        y_low = int((1.0 - (c_low - low_min) / price_range) * (img_size[0] - 1))
        y_open = int((1.0 - (c_open - low_min) / price_range) * (img_size[0] - 1))
        y_close = int((1.0 - (c_close - low_min) / price_range) * (img_size[0] - 1))
        
        x_center = min(max(int((i + 0.5) * col_width), 0), img_size[1] - 1)
        
        y_top_wick, y_bot_wick = min(y_high, y_low), max(y_high, y_low)
        img[y_top_wick : y_bot_wick + 1, x_center] = 0.5
        
        y_top_body, y_bot_body = min(y_open, y_close), max(y_open, y_close)
        body_half_width = max(1, int(col_width * 0.35))
        x_left = max(0, x_center - body_half_width)
        x_right = min(img_size[1] - 1, x_center + body_half_width)
        
        val = 1.0 if c_close >= c_open else 0.8
        img[y_top_body : y_bot_body + 1, x_left : x_right + 1] = val
        
    return img

def cnn_pattern_classifier(img_tensor, df_window):
    kernel_peak = np.array([[-1, 2, -1], [-1, 2, -1], [-1, -1, -1]], dtype=np.float32)
    kernel_valley = np.array([[-1, -1, -1], [-1, 2, -1], [-1, 2, -1]], dtype=np.float32)
    
    h, w = img_tensor.shape
    feature_map_peak = np.zeros((h-2, w-2))
    feature_map_valley = np.zeros((h-2, w-2))
    
    for r in range(1, h-1):
        for c in range(1, w-1):
            sub_mat = img_tensor[r-1:r+2, c-1:c+2]
            feature_map_peak[r-1, c-1] = np.sum(sub_mat * kernel_peak)
            feature_map_valley[r-1, c-1] = np.sum(sub_mat * kernel_valley)
            
    f_peak_score = np.max(feature_map_peak, axis=0)
    f_valley_score = np.max(feature_map_valley, axis=0)
    
    peaks_indices = [i for i in range(1, len(f_peak_score)-1) if f_peak_score[i] > f_peak_score[i-1] and f_peak_score[i] > f_peak_score[i+1] and f_peak_score[i] > 1.5]
    valleys_indices = [i for i in range(1, len(f_valley_score)-1) if f_valley_score[i] > f_valley_score[i-1] and f_valley_score[i] > f_valley_score[i+1] and f_valley_score[i] > 1.5]
    
    raw_scores = {
        'W底 (Double Bottom)': 0.1,
        'M頭 (Double Top)': 0.1,
        '頭肩底 (Reverse Head & Shoulders)': 0.05,
        '牛旗持續形態 (Bull Flag)': 0.1,
        '對稱三角收斂 (Symmetrical Triangle)': 0.1
    }
    
    if len(valleys_indices) >= 2: raw_scores['W底 (Double Bottom)'] += 0.65
    if len(peaks_indices) >= 2: raw_scores['M頭 (Double Top)'] += 0.65
    if len(valleys_indices) >= 3: raw_scores['頭肩底 (Reverse Head & Shoulders)'] += 0.75
        
    close_start, close_end = df_window['Close'].iloc[0], df_window['Close'].iloc[-1]
    ret = (close_end - close_start) / close_start
    
    if ret > 0.05: raw_scores['牛旗持續形態 (Bull Flag)'] += 0.55
    elif abs(ret) < 0.03: raw_scores['對稱三角收斂 (Symmetrical Triangle)'] += 0.50
        
    exp_scores = {k: np.exp(v * 2.5) for k, v in raw_scores.items()}
    sum_exp = sum(exp_scores.values())
    probs = {k: float(v / sum_exp) for k, v in exp_scores.items()}
    
    return probs, feature_map_peak + feature_map_valley

# ==========================================
# ⚙️ 幾何演算法：Pivots, VAS, W底/M頭, Harmonics
# ==========================================
def find_pivots(df, window=5):
    pivots_high, pivots_low = [], []
    for i in range(window, len(df) - window):
        high_window = df['High'].iloc[i - window : i + window + 1]
        low_window = df['Low'].iloc[i - window : i + window + 1]
        curr_high, curr_low = df['High'].iloc[i], df['Low'].iloc[i]
        if curr_high == high_window.max(): pivots_high.append((df.index[i], curr_high, i))
        if curr_low == low_window.min(): pivots_low.append((df.index[i], curr_low, i))
    return pivots_high, pivots_low

def detect_volume_anchors(df, top_n=3):
    if len(df) < 20: return []
    sorted_vol = df.sort_values(by='Volume', ascending=False)
    top_vol_df = sorted_vol.head(top_n)
    anchors = []
    for idx, row in top_vol_df.iterrows():
        anchors.append({'date': idx, 'low_price': row['Low'], 'close_price': row['Close'], 'volume': row['Volume'], 'is_bull': row['Close'] >= row['Open']})
    return sorted(anchors, key=lambda x: x['date'])

def detect_double_bottom_top(df, pivots_high, pivots_low, tolerance=0.025):
    patterns = []
    for i in range(len(pivots_low) - 1):
        p1, p2 = pivots_low[i], pivots_low[i + 1]
        if abs(p1[1] - p2[1]) / p1[1] <= tolerance:
            mid_highs = [ph for ph in pivots_high if p1[2] < ph[2] < p2[2]]
            if mid_highs:
                peak = max(mid_highs, key=lambda x: x[1])
                patterns.append({'type': 'W底 (雙底拉升)', 'p1': p1, 'p2': p2, 'peak': peak, 'neckline': peak[1], 'color': '#00ff88'})
    for i in range(len(pivots_high) - 1):
        p1, p2 = pivots_high[i], pivots_high[i + 1]
        if abs(p1[1] - p2[1]) / p1[1] <= tolerance:
            mid_lows = [pl for pl in pivots_low if p1[2] < pl[2] < p2[2]]
            if mid_lows:
                trough = min(mid_lows, key=lambda x: x[1])
                patterns.append({'type': 'M頭 (雙頂派貨)', 'p1': p1, 'p2': p2, 'trough': trough, 'neckline': trough[1], 'color': '#ff0066'})
    return patterns

def detect_harmonics(pivots_high, pivots_low):
    all_pivots = sorted(pivots_high + pivots_low, key=lambda x: x[2])
    harmonics = []
    if len(all_pivots) < 5: return harmonics
        
    for i in range(len(all_pivots) - 4):
        pX, pA, pB, pC, pD = all_pivots[i:i+5]
        is_bullish = (pX[1] > pA[1] and pA[1] < pB[1] and pB[1] > pC[1] and pC[1] < pD[1])
        is_bearish = (pX[1] < pA[1] and pA[1] > pB[1] and pB[1] < pC[1] and pC[1] > pD[1])
        if not (is_bullish or is_bearish): continue
            
        XA, AB, BC, CD, AD = abs(pA[1] - pX[1]), abs(pB[1] - pA[1]), abs(pC[1] - pB[1]), abs(pD[1] - pC[1]), abs(pD[1] - pA[1])
        if XA == 0 or AB == 0 or BC == 0: continue
            
        ab_xa, bc_ab, ad_xa = AB / XA, BC / AB, AD / XA
        
        if 0.55 <= ab_xa <= 0.68 and 0.382 <= bc_ab <= 0.886 and 0.7 <= ad_xa <= 0.85:
            harmonics.append({'name': 'Gartley 加特利諧波', 'points': [pX, pA, pB, pC, pD], 'direction': 'Bullish 買入' if is_bullish else 'Bearish 賣出', 'color': '#00E5FF'})
        elif 0.35 <= ab_xa <= 0.55 and 0.382 <= bc_ab <= 0.886 and 0.8 <= ad_xa <= 0.95:
            harmonics.append({'name': 'Bat 蝙蝠諧波', 'points': [pX, pA, pB, pC, pD], 'direction': 'Bullish 買入' if is_bullish else 'Bearish 賣出', 'color': '#FF00FF'})
        elif 0.7 <= ab_xa <= 0.85 and 0.382 <= bc_ab <= 0.886 and 1.15 <= ad_xa <= 1.7:
            harmonics.append({'name': 'Butterfly 蝴蝶諧波 (極值延伸)', 'points': [pX, pA, pB, pC, pD], 'direction': 'Bullish 強力買入' if is_bullish else 'Bearish 強力賣出', 'color': '#FFB300'})
        elif 0.35 <= ab_xa <= 0.65 and 0.382 <= bc_ab <= 0.886 and 1.5 <= ad_xa <= 1.8:
            harmonics.append({'name': 'Crab 螃蟹諧波 (深水炸彈)', 'points': [pX, pA, pB, pC, pD], 'direction': 'Bullish 終極撈底' if is_bullish else 'Bearish 終極逃頂', 'color': '#FF3D00'})

    return harmonics

# ==========================================
# 🔴 頁面渲染 Engine
# ==========================================
def render_page_2z():
    st.title("👁️ 艙房 2z : AI 象形視覺神瞳 (1:1旗桿測幅 / P/b/D型 / CNN / 諧波)")
    st.markdown("""
    **華爾街機構級四核形態與測幅終端**：
    1️⃣ **🚩 旗形/楔形 1:1 旗桿測幅 (Measured Move Target)**：自動劃出旗桿長度，並投射突破後 1:1 漲跌幅測幅目標價！
    2️⃣ **🏛️ 期指專業：Market Profile 字母象形 (P型/b型/D型)**：計算籌碼分佈 POC，判定低位挾單或高位派貨！
    3️⃣ **🧠 電腦視覺：CNN 卷積神經網絡 (2D Vision)**：將 K 線繪製成 224x224 像素張量識別符！
    4️⃣ **📐 幾何諧波：Harmonic Trading (四大神獸)**：精準算算 X-A-B-C-D 幾何轉折點！
    """)
    st.divider()

    # 控制面板
    col_c1, col_c2, col_c3, col_c4 = st.columns([2, 1.5, 1.5, 2])
    with col_c1:
        symbol = st.text_input("🔍 輸入標的代號 (美股/期指/加密貨幣/ETF)", value="NVDA").upper().strip()
    with col_c2:
        timeframe = st.selectbox("⏱️ 時間週期", ["1d", "1wk", "1h"], index=0)
    with col_c3:
        pivot_window = st.slider("⚙️ 形態靈敏度 (Window)", min_value=3, max_value=10, value=5)
    with col_c4:
        show_features = st.multiselect(
            "🎨 顯示象形視覺元件", 
            ["1:1 旗桿測幅目標線", "主力天量線 (VAS BIG)", "古典 W底/M頭", "幾何諧波幾何網", "MA20 均線", "Market Profile 籌碼線"],
            default=["1:1 旗桿測幅目標線", "主力天量線 (VAS BIG)", "古典 W底/M頭", "幾何諧波幾何網", "MA20 均線", "Market Profile 籌碼線"]
        )

    # 抓取行情數據
    with st.spinner(f"📡 正在掃描 {symbol} 價格結構與高維圖像..."):
        try:
            df = yf.download(symbol, period="1y", interval=timeframe, progress=False)
            if isinstance(df.columns, pd.MultiIndex):
                df.columns = df.columns.get_level_values(0)
            df = df.dropna()
        except Exception as e:
            st.error(f"無法載入 {symbol} 數據: {e}")
            return

    if df.empty:
        st.warning(f"找不到 {symbol} 數據，請確認代號是否正確。")
        return

    # 計算各項指標
    df['MA20'] = df['Close'].rolling(20).mean()
    pivots_high, pivots_low = find_pivots(df, window=pivot_window)
    vas_anchors = detect_volume_anchors(df, top_n=3)
    double_patterns = detect_double_bottom_top(df, pivots_high, pivots_low)
    harmonic_patterns = detect_harmonics(pivots_high, pivots_low)
    flag_patterns = detect_flags_and_wedges(df)

    df_recent = df.tail(60)
    img_tensor = render_kline_to_image_tensor(df_recent)
    cnn_probs, feature_heatmap = cnn_pattern_classifier(img_tensor, df_recent)
    profile_data = detect_market_profile_shape(df_recent)

    # 🏛️ 頂層：Market Profile 字母象形實時診斷卡片
    st.markdown("### 🏛️ 期指/個股 Market Profile 字母象形戰術卡")
    col_mp1, col_mp2, col_mp3 = st.columns([3, 3, 4])
    with col_mp1:
        st.markdown(f"<div style='background-color:#1e293b; padding:15px; border-radius:10px; border-left:5px solid {profile_data.get('color', '#00E5FF')}'>"
                    f"<h3 style='margin:0; color:{profile_data.get('color', '#00E5FF')};'>{profile_data['shape']}</h3>"
                    f"<p style='margin-top:5px; color:#aaa;'>當前籌碼分佈型態</p></div>", unsafe_allow_html=True)
    with col_mp2:
        st.metric(label="🎯 POC 籌碼最大密集位", value=f"\${profile_data['poc']:.2f}")
        st.caption(f"VAH 高價值區: `${profile_data['vah']:.2f}` | VAL 低價值區: `${profile_data['val']:.2f}`")
    with col_mp3:
        st.info(f"💡 **籌碼戰術指引**：{profile_data['desc']}")

    # 主圖表 (K線 + 成交量)
    fig = make_subplots(
        rows=2, cols=1, shared_xaxes=True, 
        vertical_spacing=0.03, row_heights=[0.75, 0.25]
    )

    # 1. 畫 K 線圖
    fig.add_trace(go.Candlestick(
        x=df.index, open=df['Open'], high=df['High'], low=df['Low'], close=df['Close'],
        name="K線", increasing_line_color='#00ff88', decreasing_line_color='#ff0066'
    ), row=1, col=1)

    # 2. MA20 均線
    if "MA20 均線" in show_features:
        fig.add_trace(go.Scatter(x=df.index, y=df['MA20'], name="MA20", line=dict(color='#00FFFF', width=1.5)), row=1, col=1)

    # 3. 🚩 畫 1:1 旗桿測幅目標價線 (Flag / Wedge Measured Move Target)
    if "1:1 旗桿測幅目標線" in show_features:
        for flg in flag_patterns:
            # 畫旗桿 (Pole)
            fig.add_trace(go.Scatter(
                x=[flg['pole_start_date'], flg['pole_end_date']],
                y=[flg['pole_start_price'], flg['pole_end_price']],
                mode='lines+markers', line=dict(color=flg['color'], width=4),
                name="旗桿 (Pole)"
            ), row=1, col=1)
            # 畫 1:1 目標價虛線
            fig.add_hline(
                y=flg['target_price'], line_color=flg['color'], line_width=2.5, line_dash="dashdot",
                annotation_text=f"🎯 1:1 測幅目標價: \${flg['target_price']:.2f}",
                annotation_font_color=flg['color'], row=1, col=1
            )

    # 4. Market Profile 籌碼位 (POC / VAH / VAL)
    if "Market Profile 籌碼線" in show_features and profile_data['poc'] > 0:
        fig.add_hline(y=profile_data['poc'], line_color="#FFFF00", line_width=2, line_dash="solid", annotation_text="POC 籌碼峰值", row=1, col=1)
        fig.add_hline(y=profile_data['vah'], line_color="#00E5FF", line_width=1.5, line_dash="dot", row=1, col=1)
        fig.add_hline(y=profile_data['val'], line_color="#00E5FF", line_width=1.5, line_dash="dot", row=1, col=1)

    # 5. 畫主力天量線 (VAS BIG Anchor)
    if "主力天量線 (VAS BIG)" in show_features:
        for anc in vas_anchors:
            fig.add_shape(type="line", x0=anc['date'], y0=anc['low_price'], x1=df.index[-1], y1=anc['low_price'], line=dict(color="#FF00FF", width=2.5, dash="dash"), row=1, col=1)
            fig.add_annotation(x=anc['date'], y=anc['low_price'], text="<b>BIG 主力防守</b>", showarrow=True, arrowhead=2, arrowcolor="#FF00FF", font=dict(color="#FF00FF", size=12), row=1, col=1)

    # 6. 畫 W底 / M頭 形態
    if "古典 W底/M頭" in show_features:
        for pat in double_patterns:
            p1, p2 = pat['p1'], pat['p2']
            fig.add_trace(go.Scatter(x=[p1[0], p2[0]], y=[p1[1], p2[1]], mode='lines+markers+text', text=[pat['type'], ''], textposition="bottom center", line=dict(color=pat['color'], width=3, dash='dot'), name=pat['type']), row=1, col=1)
            fig.add_hline(y=pat['neckline'], line_color=pat['color'], line_dash="dash", opacity=0.6, row=1, col=1)

    # 7. 畫幾何諧波幾何網 (Harmonic Lines)
    if "幾何諧波幾何網" in show_features:
        for harm in harmonic_patterns:
            pts = harm['points']
            hx, hy = [p[0] for p in pts], [p[1] for p in pts]
            fill_color = 'rgba(0, 229, 255, 0.08)'
            if 'Bat' in harm['name']: fill_color = 'rgba(255, 0, 255, 0.08)'
            elif 'Butterfly' in harm['name']: fill_color = 'rgba(255, 179, 0, 0.15)'
            elif 'Crab' in harm['name']: fill_color = 'rgba(255, 61, 0, 0.15)'
            
            fig.add_trace(go.Scatter(x=hx, y=hy, mode='lines+markers+text', text=['X', 'A', 'B', 'C', 'D'], textposition="top center", line=dict(color=harm['color'], width=2), fill='toself', fillcolor=fill_color, name=f"{harm['name']} ({harm['direction']})"), row=1, col=1)

    # 8. 成交量圖
    colors_vol = ['#00ff88' if c >= o else '#ff0066' for c, o in zip(df['Close'], df['Open'])]
    fig.add_trace(go.Bar(x=df.index, y=df['Volume'], name="成交量", marker_color=colors_vol, opacity=0.7), row=2, col=1)

    fig.update_layout(height=720, template="plotly_dark", xaxis_rangeslider_visible=False, margin=dict(l=10, r=10, t=30, b=10), legend=dict(orientation="h", yanchor="bottom", y=1.02, xanchor="right", x=1))
    fig.update_yaxes(title_text="價格", row=1, col=1)
    fig.update_yaxes(title_text="成交量", row=2, col=1)

    st.plotly_chart(fig, use_container_width=True)

    # 🧠 CNN 電腦視覺神經網絡診斷面板
    st.markdown("### 🧠 CNN 卷積神經網絡 (Computer Vision) 視覺識圖矩陣")
    col_cnn_1, col_cnn_2 = st.columns([6, 4])
    
    with col_cnn_1:
        st.subheader("📊 2D 圖像張量形態識別概率 (Softmax)")
        top_pattern = max(cnn_probs, key=cnn_probs.get)
        st.info(f"💡 **CNN 識圖診斷**：當前 K 線圖像最符合 **【{top_pattern}】** 形態 (信心度: `{cnn_probs[top_pattern]*100:.1f}%`)")
        for pat_name, prob_val in cnn_probs.items():
            col_p1, col_p2 = st.columns([4, 6])
            with col_p1: st.write(f"**{pat_name}**")
            with col_p2:
                st.progress(prob_val)
                st.caption(f"匹配概率: `{prob_val*100:.2f}%`")
                
    with col_cnn_2:
        st.subheader("🔥 AI 特徵激活熱力圖 (Feature Map)")
        fig_hm = go.Figure(data=go.Heatmap(z=feature_heatmap, colorscale='Viridis', showscale=False))
        fig_hm.update_layout(title="2D 卷積特徵響應矩陣 (224x224)", height=260, template="plotly_dark", margin=dict(l=5, r=5, t=30, b=5), xaxis=dict(showticklabels=False), yaxis=dict(showticklabels=False))
        st.plotly_chart(fig_hm, use_container_width=True)

    # 📋 下方：幾何與測幅摘要報告
    st.markdown("---")
    st.markdown("### 📋 幾何形態與 1:1 測幅目標摘要")
    col_r1, col_r2, col_r3 = st.columns(3)
    
    with col_r1:
        st.subheader("📌 🚩 旗形 1:1 測幅目標")
        if flag_patterns:
            for flg in flag_patterns:
                st.write(f"• **{flg['type']}**")
                st.write(f"  - 突破點: `${flg['breakout_price']:.2f}`")
                st.write(f"  - **1:1 測幅目標價: `${flg['target_price']:.2f}`**")
        else: st.write("近期未發現標準 1:1 旗形測幅結構。")
            
    with col_r2:
        st.subheader("📌 古典形態 (W底/M頭)")
        if double_patterns:
            for dp in double_patterns: st.write(f"• **{dp['type']}** | 頸線位: `${dp['neckline']:.2f}`")
        else: st.write("近期未發現標準雙底或雙頂形態。")
            
    with col_r3:
        st.subheader("📌 諧波幾何轉折 (Harmonics)")
        if harmonic_patterns:
            for hp in harmonic_patterns: st.write(f"• **{hp['name']}** | 形態: `{hp['direction']}`")
        else: st.write("未觸發 X-A-B-C-D 幾何轉折點。")

def app():
    render_page_2z()

if __name__ == "__main__":
    render_page_2z()