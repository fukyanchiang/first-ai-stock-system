import streamlit as st
import pandas as pd
import numpy as np
import yfinance as yf
import plotly.graph_objects as go
from plotly.subplots import make_subplots
from datetime import timedelta

# =========================================================================
# ⚙️ 1. 數據引擎：動態抓取與防偽過濾 (加入快取參數)
# =========================================================================
@st.cache_data(ttl=3600, show_spinner=False)
def fetch_vvix_data(vix_threshold, quantile_pct, rolling_window, vvix_min_floor):
    try:
        tickers = ['^VVIX', '^VIX', 'SPY']
        data = yf.download(tickers, start='2014-01-01', progress=False)['Close']
        
        if data.empty or '^VVIX' not in data.columns or '^VIX' not in data.columns or 'SPY' not in data.columns:
            return pd.DataFrame()
            
        if data.index.tz is not None:
            data.index = data.index.tz_localize(None)
            
        data = data.ffill().dropna()
        
        # 🧠 大鱷算法：計算 VVIX 與 VIX 的比率
        data['Ratio'] = data['^VVIX'] / data['^VIX']
        
        # 動態計算極值天花板
        data['Ratio_1Y_High'] = data['Ratio'].rolling(window=rolling_window).quantile(quantile_pct).bfill()
        
        # 🛡️ 終極三重防偽鎖：
        # 1. 散戶麻痺 (VIX < threshold)
        # 2. 比例破頂 (Ratio > Ratio_1Y_High)
        # 3. 絕對值防偽 (VVIX >= vvix_min_floor) -> 防止單純因為 VIX 極低導致的數學假突破
        data['Divergence_Signal'] = (
            (data['Ratio'] > data['Ratio_1Y_High']) & 
            (data['^VIX'] < vix_threshold) & 
            (data['^VVIX'] >= vvix_min_floor)
        )
        
        return data
        
    except Exception as e:
        st.error(f"⚠️ 數據抓取失敗，請檢查網絡連線：{e}")
        return pd.DataFrame()

# =========================================================================
# 🚀 2. 主頁面渲染函數 (render_page_2o)
# =========================================================================
def render_page_2o():
    st.markdown("## 🏛️ 艙房2o : 壓箱底第二絕 大鱷嘅隱形保單 —— VVIX 與 VIX 嘅「暗流背馳」！")
    st.markdown("散戶只識睇 VIX，大鱷係睇 VVIX！當大市破頂但 VVIX 異常爆升，代表華爾街巨鯨正在瘋狂買入末日保險！")
    
    # 🎛️ 參數中控台
    with st.expander("⚙️ 打開大師級參數中控台 (微調系統敏感度)", expanded=False):
        col_p1, col_p2, col_p3, col_p4 = st.columns(4)
        with col_p1:
            vix_threshold = st.number_input("VIX 散戶麻痺線 (<)", min_value=12.0, max_value=25.0, value=18.0, step=0.5)
        with col_p2:
            vvix_min_floor = st.number_input("VVIX 絕對值防偽線 (>=)", min_value=70.0, max_value=120.0, value=90.0, step=1.0)
        with col_p3:
            quantile_pct = st.slider("歷史極值百分位", min_value=0.80, max_value=0.99, value=0.90, step=0.01)
        with col_p4:
            rolling_window = st.selectbox("滾動參考窗口", [126, 252, 504], index=1, format_func=lambda x: f"{x} 日 (約 {x//252} 年)")

    st.markdown("---")

    with st.spinner("📡 正在深潛華爾街期權池，追蹤 VVIX 巨鯨暗流..."):
        df = fetch_vvix_data(vix_threshold, quantile_pct, rolling_window, vvix_min_floor)

    if df.empty:
        st.error("❌ 無法取得 VVIX 或 VIX 數據，請檢查 yfinance 連線。")
        return

    # --- 提煉信號與過濾 (至少相隔 20 日才算新一次爆發) ---
    signal_dates = df[df['Divergence_Signal']].index
    filtered_signals = []
    for dt in signal_dates:
        if not filtered_signals or (dt - filtered_signals[-1]).days > 20:
            filtered_signals.append(dt)

    days_since_last_signal = "無近期信號"
    if filtered_signals:
        last_signal_date = filtered_signals[-1]
        today_date = df.index[-1]
        days_diff = (today_date - last_signal_date).days
        if days_diff == 0:
            days_since_last_signal = "🚨 今日爆發！"
        elif days_diff <= 21:
            days_since_last_signal = f"🚨 {days_diff} 日前 (危險期)"
        else:
            days_since_last_signal = f"🟢 {days_diff} 日前 (已解除)"

    # --- 提煉最新狀態 ---
    latest_vvix = df['^VVIX'].iloc[-1]
    latest_vix = df['^VIX'].iloc[-1]
    latest_ratio = df['Ratio'].iloc[-1]
    latest_threshold = df['Ratio_1Y_High'].iloc[-1]
    is_divergence = df['Divergence_Signal'].iloc[-1]
    
    if is_divergence:
        status_text = "🚨 極度危險：暗流背馳爆發！"
    elif latest_vix < 15 and latest_vvix > 105:
        status_text = "⚠️ 警惕：巨鯨開始吸納保險"
    else:
        status_text = "🟢 正常波動 (無明顯背馳)"

    # --- KPI 儀表板 ---
    col1, col2, col3, col4 = st.columns(4)
    with col1:
        st.metric("VIX (散戶) | VVIX (大鱷)", f"{latest_vix:.2f} | {latest_vvix:.2f}")
    with col2:
        st.metric("當前比率 vs 動態極值", f"{latest_ratio:.2f}", f"臨界線: {latest_threshold:.2f}", delta_color="off")
    with col3:
        st.info(f"**當前狀態：** {status_text}")
    with col4:
        warn_color = "#ff3333" if "🚨" in days_since_last_signal else "#00ff88"
        st.markdown(f"**⏳ 上次黃線距今：**<br><span style='color:{warn_color}; font-size:18px; font-weight:bold;'>{days_since_last_signal}</span>", unsafe_allow_html=True)

    st.markdown("<br>", unsafe_allow_html=True)

    # =========================================================================
    # 🧮 原版恢復：一秒睇明極簡數學算式卡片
    # =========================================================================
    st.markdown("""
    <div style="background-color:#1b263b; padding:18px; border-radius:8px; border-left:6px solid #ff3333; margin-bottom:15px; box-shadow: 0px 4px 10px rgba(255, 51, 51, 0.2);">
        <h3 style="color:#ff3333; margin:0 0 10px 0; font-size:18px; font-family:Arial Black;">🧮 一秒睇明！暗紅區（黃線爆發）極簡數學算式：</h3>
        <p style="color:#ffffff; font-size:17px; margin:0; font-weight:bold; line-height:1.5;">
            🚨 暗紅爆發區 ＝ <span style="color:#00ff88;">【 VIX < 18 (散戶麻痺) 】</span> ＋ <span style="color:#ffaa00;">【 Ratio (VVIX/VIX) 衝破 7.5 – 8.5+ (衝破1年90%極值) 】</span>
        </p>
        <p style="color:#bbb; font-size:13px; margin-top:8px; margin-bottom:0; line-height:1.5;">
            💡 <b>白話大鱷邏輯：</b> 當散戶以為天下太平、把 VIX 壓在 18 以下的極低位時，華爾街大鱷卻不惜成本瘋狂搶購 VIX Call 末日保險，把 VVIX 比率強行抽高到 <b>7.5 – 8.5 以上</b>（超越過去一年 90% 的天花板）。系統就會立刻刷出暗紅直條與黃線警報！
            <br>*(註：系統內部已額外加入 VVIX ≥ 90 的防偽鎖定)*
        </p>
    </div>
    """, unsafe_allow_html=True)

    st.markdown("""
    <div style="background-color:#2b2b2b; padding:15px; border-radius:8px; border-left:5px solid #ffaa00; margin-bottom:15px;">
        <h4 style="color:#ffaa00; margin:0 0 10px 0;">🚨 圖表上的「黃色垂直線與暗紅區」代表什麼？</h4>
        <p style="color:#ddd; margin:0; font-size:14px; line-height:1.6;">
            <b>黃線與最底層的「暗紅區」即「暗流背馳」爆發點！</b> 系統偵測到大市表面平靜，但期權市場的恐慌極限卻異常狂飆，觸發上述極簡數學條件。<br>
            <b>【大鱷信號】</b>：當黃線與暗紅色直條密集出現，代表巨鯨正買好防彈衣。通常喺信號出現後嘅 <b>1 到 3 個星期內</b>，隨時迎來閃崩洗盤，係極佳嘅減倉與避險預警！
        </p>
    </div>
    """, unsafe_allow_html=True)

    # =========================================================================
    # 📉 繪製三層巨幕圖
    # =========================================================================
    fig = make_subplots(
        rows=3, cols=1, 
        shared_xaxes=True, 
        vertical_spacing=0.03, 
        row_heights=[0.5, 0.25, 0.25] 
    )

    # 第一層：SPY
    fig.add_trace(go.Scatter(x=df.index, y=df['SPY'], name="標普 500 (SPY)", line=dict(color="#ffffff", width=2)), row=1, col=1)
    for dt in filtered_signals:
        fig.add_vline(x=dt, line_width=1.5, line_color="#ffaa00", line_dash="solid", row=1, col=1,
                      annotation_text="🚨暗流", annotation_position="top left", annotation_font=dict(color="#ffaa00", size=10))

    # 第二層：VVIX vs VIX
    fig.add_trace(go.Scatter(x=df.index, y=df['^VVIX'], name="VVIX (大鱷恐慌指數)", line=dict(color="#00e5ff", width=1.5)), row=2, col=1)
    fig.add_trace(go.Scatter(x=df.index, y=df['^VIX'] * 5, name="VIX (放大5倍對比)", line=dict(color="#ff3333", width=1.5, dash='dot')), row=2, col=1)
    # 畫出防偽線
    fig.add_hline(y=vvix_min_floor, line_width=1, line_color="#00e5ff", line_dash="dash", row=2, col=1, opacity=0.5)

    # 第三層：Ratio
    fig.add_trace(go.Scatter(x=df.index, y=df['Ratio'], name="VVIX/VIX 比率 (Ratio)", line=dict(color="#ffaa00", width=1.5)), row=3, col=1)
    fig.add_trace(go.Scatter(x=df.index, y=df['Ratio_1Y_High'], name="動態極值警戒線", line=dict(color="#ff3333", width=1.5, dash='dash')), row=3, col=1)

    # 強制高亮背馳區域
    divergence_max_value = df[['Ratio', 'Ratio_1Y_High']].max().max() * 1.1
    fig.add_trace(go.Bar(
        x=df.index, y=np.where(df['Divergence_Signal'], divergence_max_value, 0),
        name="🚨 暗紅爆發區", marker_color="rgba(255, 51, 51, 0.35)", marker_line_width=0, hoverinfo='skip', showlegend=False
    ), row=3, col=1)

    fig.update_layout(
        title=dict(text="📊 大鱷期權暗流雷達 (極致防偽版)", font=dict(color="white", size=20)),
        template="plotly_dark", height=850, margin=dict(l=20, r=20, t=60, b=20),
        paper_bgcolor="#11141a", plot_bgcolor="#11141a", hovermode="x unified",
        legend=dict(orientation="h", yanchor="bottom", y=1.02, xanchor="right", x=1),
        barmode='overlay'
    )

    fig.update_yaxes(title_text="標普 500 (SPY)", row=1, col=1, showgrid=True, gridcolor="#222834", type="log")
    fig.update_yaxes(title_text="恐慌指數", row=2, col=1, showgrid=True, gridcolor="#222834")
    fig.update_yaxes(title_text="暗流比率", row=3, col=1, showgrid=True, gridcolor="#222834", range=[2, divergence_max_value])
    fig.update_xaxes(showgrid=True, gridcolor="#222834")

    st.plotly_chart(fig, use_container_width=True)

    # =========================================================================
    # 🕵️‍♂️ 全新引擎：實戰回測追蹤器 (Historical Backtest)
    # =========================================================================
    st.markdown("---")
    st.markdown("### 🕵️‍♂️ 大鱷買保險後，大市跌幾多？(最近 10 次信號回測)")
    
    if filtered_signals:
        backtest_data = []
        for i, dt in enumerate(filtered_signals[-10:]): # 取最近 10 次
            try:
                # 獲取信號當日及未來的 SPY 價格
                idx_loc = df.index.get_loc(dt)
                price_t0 = df['SPY'].iloc[idx_loc]
                
                # 計算 T+10 (約兩週) 及 T+20 (約一個月) 的回報
                price_t10 = df['SPY'].iloc[idx_loc + 10] if (idx_loc + 10) < len(df) else np.nan
                price_t20 = df['SPY'].iloc[idx_loc + 20] if (idx_loc + 20) < len(df) else np.nan
                
                ret_t10 = (price_t10 / price_t0 - 1) * 100 if not np.isnan(price_t10) else np.nan
                ret_t20 = (price_t20 / price_t0 - 1) * 100 if not np.isnan(price_t20) else np.nan
                
                backtest_data.append({
                    "🚨 爆發日期": dt.strftime("%Y-%m-%d"),
                    "觸發時 SPY 價格": f"${price_t0:.2f}",
                    "T+10日 後果 (約2週)": f"{ret_t10:.2f}%" if not np.isnan(ret_t10) else "⏳ 發酵中",
                    "T+20日 後果 (約1個月)": f"{ret_t20:.2f}%" if not np.isnan(ret_t20) else "⏳ 發酵中"
                })
            except Exception:
                continue
                
        if backtest_data:
            bt_df = pd.DataFrame(backtest_data)
            
            # 簡單的顏色渲染 (負回報顯示紅色，正回報顯示綠色)
            def color_returns(val):
                if "發酵中" in str(val): return 'color: white'
                try:
                    num = float(val.replace('%', ''))
                    return 'color: #ff3333; font-weight: bold' if num < 0 else 'color: #00ff88'
                except: return ''

            st.dataframe(bt_df.style.map(color_returns, subset=['T+10日 後果 (約2週)', 'T+20日 後果 (約1個月)']), 
                         use_container_width=True, hide_index=True)
            st.caption("💡 *大鱷買入保險後，通常需要 1-3 星期（10-20 個交易日）讓危機發酵。留意表格中紅色的負回報，這就是大鱷避開的跌幅！*")
    else:
        st.info("近期未有符合極端條件的回測信號。")

    # =========================================================================
    # 📚 原版恢復：爺爺終極心法與量化判定標準
    # =========================================================================
    st.markdown("---")
    st.markdown("### 2️⃣ 華爾街巨鯨暗中買末日保險 —— 【對應第二絕：VVIX 恐慌暗流】")
    st.markdown("**真相：** 大危機爆發前夕，散戶睇嘅 VIX (恐慌指數) 通常好平靜（跌到 12-13），因為大市仲喺度溫水煮青蛙。")
    st.markdown("**第一時間嘅信號：** 你要睇 VVIX (VIX 嘅期權波動率)！當大市仲升緊，VIX 仲跌緊，但 VVIX 突然以極大角度抽升！")
    st.markdown("**大鱷邏輯：** 這代表華爾街最頂級嘅機構（佢哋有內幕、有最快嘅數據），已經聞到燶味，開始不惜成本咁瘋狂掃入「極度價外嘅 VIX Call (末日保險)」。佢哋唔出聲，但錢嘅流向出賣咗佢哋。當 VVIX 異常爆升，通常 1 到 3 個禮拜內，就會爆發令聯儲局恐慌減息嘅黑天鵝！")

    st.markdown("---")
    st.markdown("### 📊 量化判定標準：三個級別的「暗流血壓計」")
    
    st.markdown("#### 🟢 正常狀態 (Normal Phase)")
    st.markdown("* **數據指標**：VIX 介乎 14–18，VVIX 介乎 80–95。")
    st.markdown("* **比率 (Ratio)**：Ratio = (VVIX / VIX) 介乎 5.0 – 6.2。")
    st.markdown("* **戰術含義**：散戶同大鱷都認為市場平靜，期權市場無異常對沖。")
    
    st.markdown("#### ⚠️ 異動警惕 (Early Accumulation - 巨鯨開始進場)")
    st.markdown("* **數據指標**：VIX 依然沉睡在 12–15 的低位（散戶以為天下太平），但 VVIX 獨自抽升至 105 – 110。")
    st.markdown("* **比率 (Ratio)**：Ratio = (VVIX / VIX) 升至 6.8 – 7.4。")
    st.markdown("* **戰術含義**：大市溫水煮青蛙，但期權池開始出現靜靜雞掃入 VIX Call 買保險嘅資金。")
    
    st.markdown("#### 🚨 明顯背馳爆發 (Clear Divergence Signal - 系統亮黃線警告)")
    st.markdown("* **數據指標**：VIX 被壓在 12–15（低於 18），但 VVIX 以極大角度暴升至 115 – 125+。")
    st.markdown("* **比率 (Ratio)**：Ratio = (VVIX / VIX) 衝破 7.5 – 8.5 以上（突破過去 252 個交易日 / 一年的 90% 百分位數極值）。")
    st.markdown("* **戰術含義**：大市表面創新高或高位橫行，但大鱷正不惜成本搶購末日保險！這代表華爾街巨鯨預感有黑天鵝，通常在 1 到 3 個星期內 就會迎來大市閃崩或劇烈變盤。")

if __name__ == "__main__":
    render_page_2o()