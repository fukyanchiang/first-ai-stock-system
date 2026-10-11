import streamlit as st
import pandas as pd
import numpy as np
import yfinance as yf
import plotly.graph_objects as go
from plotly.subplots import make_subplots
from datetime import timedelta

# =========================================================================
# ⚙️ 1. 數據引擎：抓取 HYG, SPY 與 信貸利差 (代理) + 參數化
# =========================================================================
@st.cache_data(ttl=3600, show_spinner=False)
def fetch_credit_data(hyg_ma_window, quantile_pct, rolling_window):
    try:
        # 抓取 HYG (高收益債), SPY (大盤), LQD (投資級公司債 - 用作利差計算代理)
        tickers = ['HYG', 'SPY', 'LQD']
        data = yf.download(tickers, start='2014-01-01', progress=False)['Close']
        
        if data.empty or 'HYG' not in data.columns or 'SPY' not in data.columns:
            return pd.DataFrame()
            
        if data.index.tz is not None:
            data.index = data.index.tz_localize(None)
            
        data = data.ffill().dropna()
        
        # 🧠 大鱷算法：合成信貸利差血壓計 (Credit Spread Proxy)
        # LQD (高質債) / HYG (垃圾債) 的比率作為高仿真「信貸恐慌代理指標」
        data['Credit_Spread_Proxy'] = data['LQD'] / data['HYG']
        
        # 動態警戒線：參數化滾動天花板
        data['Spread_Dynamic_High'] = data['Credit_Spread_Proxy'].rolling(window=rolling_window).quantile(quantile_pct).bfill()
        
        # HYG 生命線 (參數化)
        data['HYG_MA'] = data['HYG'].rolling(window=hyg_ma_window).mean().bfill()
        
        # 🛡️️ 增強防偽鎖：加入短線跌幅條件，確保是「真實拋售」而非橫行跌穿
        data['HYG_5D_Ret'] = data['HYG'].pct_change(periods=5)
        
        # 產生「落雨收遮 (Credit Freeze)」信號：
        # 1. 利差破動態極值
        # 2. HYG 跌穿自訂生命線
        # 3. HYG 近 5 日錄得實質跌幅 (防偽)
        data['Credit_Freeze_Signal'] = (
            (data['Credit_Spread_Proxy'] > data['Spread_Dynamic_High']) & 
            (data['HYG'] < data['HYG_MA']) &
            (data['HYG_5D_Ret'] < 0)
        )
        
        return data
        
    except Exception as e:
        st.error(f"⚠️ 數據抓取失敗，請檢查網絡連線：{e}")
        return pd.DataFrame()

# =========================================================================
# 🚀 2. 主頁面渲染函數 (render_page_2p)
# =========================================================================
def render_page_2p():
    st.markdown("## 🏛️ 艙房2p : 壓箱底第三絕 HYG 與信貸利差")
    st.markdown("股市跌聯儲局唔會理，但「企業借唔到錢」，聯儲局就會嚇到標尿！當 HYG 暴跌、信貸利差擴闊，這就是大減息最直接、最暴力的「第一根動機」！")
    
    # 🎛️ 參數中控台
    with st.expander("⚙️ 打開大師級參數中控台 (微調系統敏感度)", expanded=False):
        col_p1, col_p2, col_p3 = st.columns(3)
        with col_p1:
            hyg_ma_window = st.selectbox("HYG 生命線 (跌穿則警戒)", [20, 50, 100, 200], index=1, format_func=lambda x: f"{x} 天移動平均線")
        with col_p2:
            quantile_pct = st.slider("利差極值百分位", min_value=0.80, max_value=0.99, value=0.90, step=0.01)
        with col_p3:
            rolling_window = st.selectbox("滾動參考窗口", [126, 252, 504], index=1, format_func=lambda x: f"{x} 日 (約 {x//252} 年)")

    st.markdown("---")

    with st.spinner("📡 正在連接華爾街暗網，監聽企業資金鏈與信貸利差血壓計..."):
        df = fetch_credit_data(hyg_ma_window, quantile_pct, rolling_window)

    if df.empty:
        st.error("❌ 無法取得 HYG 或相關數據，請檢查 yfinance 連線。")
        return

    # --- 提煉信號與過濾 (至少相隔 20 日才算新一次爆發) ---
    signal_dates = df[df['Credit_Freeze_Signal']].index
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
            days_since_last_signal = "🚨 今日斷鏈！"
        elif days_diff <= 21:
            days_since_last_signal = f"🚨 {days_diff} 日前 (爆煲期)"
        else:
            days_since_last_signal = f"🟢 {days_diff} 日前 (已紓緩)"

    # --- 提煉最新狀態 ---
    latest_hyg = df['HYG'].iloc[-1]
    latest_ma = df['HYG_MA'].iloc[-1]
    latest_spread = df['Credit_Spread_Proxy'].iloc[-1]
    latest_threshold = df['Spread_Dynamic_High'].iloc[-1]
    is_freeze = df['Credit_Freeze_Signal'].iloc[-1]
    
    if is_freeze:
        status_text = "🚨 極度危險：信用市場心臟停頓！"
    elif latest_hyg < latest_ma:
        status_text = f"⚠️ 警惕：HYG 跌穿 {hyg_ma_window} 天線"
    else:
        status_text = "🟢 資金充裕 (企業發債正常)"

    # --- KPI 儀表板 ---
    col1, col2, col3, col4 = st.columns(4)
    with col1:
        st.metric("HYG 垃圾債 (企業血脈)", f"${latest_hyg:.2f}", f"MA{hyg_ma_window}: ${latest_ma:.2f}", delta_color="off")
    with col2:
        st.metric(f"信貸利差指標 vs {quantile_pct*100:.0f}% 極值", f"{latest_spread:.3f}", f"臨界: {latest_threshold:.3f}", delta_color="off")
    with col3:
        st.info(f"**當前狀態：** {status_text}")
    with col4:
        warn_color = "#ff3333" if "🚨" in days_since_last_signal else "#00ff88"
        st.markdown(f"**⏳ 上次斷鏈距今：**<br><span style='color:{warn_color}; font-size:18px; font-weight:bold;'>{days_since_last_signal}</span>", unsafe_allow_html=True)

    st.markdown("<br>", unsafe_allow_html=True)

    # =========================================================================
    # 🧮 核心亮點：一秒睇明極簡數學算式卡片
    # =========================================================================
    st.markdown(f"""
    <div style="background-color:#1b263b; padding:18px; border-radius:8px; border-left:6px solid #ffaa00; margin-bottom:15px; box-shadow: 0px 4px 10px rgba(255, 170, 0, 0.2);">
        <h3 style="color:#ffaa00; margin:0 0 10px 0; font-size:18px; font-family:Arial Black;">🧮 一秒睇明！落雨收遮（紅線爆發）極簡算式：</h3>
        <p style="color:#ffffff; font-size:16px; margin:0; font-weight:bold; line-height:1.6;">
            🚨 信用冰封區 ＝ 
            <span style="color:#ff3333;">【HYG 跌穿 {hyg_ma_window} 天線 (垃圾債拋售)】</span> ＋ 
            <span style="color:#00e5ff;">【利差衝破 {rolling_window//252} 年 {quantile_pct*100:.0f}% 極值 (銀行收遮)】</span>
        </p>
        <p style="color:#bbb; font-size:13px; margin-top:8px; margin-bottom:0; line-height:1.5;">
            💡 <b>白話大鱷邏輯：</b> 當實體企業（特別是高風險公司）發行的債券無人問津（HYG 暴跌），同時銀行向他們收取的利息溢價狂飆（利差破頂），代表資金鏈正式斷裂。系統就會立刻刷出暗黃色直條與紅色警報！
            <br>*(註：系統已加入 HYG 5日負回報防偽鎖，過濾橫行假跌穿)*
        </p>
    </div>
    """, unsafe_allow_html=True)

    # =========================================================================
    # 📉 繪製三層巨幕圖 (3 Subplots)
    # =========================================================================
    fig = make_subplots(
        rows=3, cols=1, 
        shared_xaxes=True, 
        vertical_spacing=0.03, 
        row_heights=[0.5, 0.25, 0.25] 
    )

    # 【第一層】：SPY 走勢 + 信用冰封警告線
    fig.add_trace(go.Scatter(x=df.index, y=df['SPY'], name="標普 500 (SPY)", line=dict(color="#ffffff", width=2)), row=1, col=1)
    
    for dt in filtered_signals:
        fig.add_vline(x=dt, line_width=1.5, line_color="#ff1744", line_dash="solid", row=1, col=1,
                      annotation_text="🚨斷鏈", annotation_position="top left", annotation_font=dict(color="#ff1744", size=10))

    # 【第二層】：HYG 價格 vs 自訂生命線
    fig.add_trace(go.Scatter(x=df.index, y=df['HYG'], name="HYG (垃圾債 ETF)", line=dict(color="#00e5ff", width=1.5)), row=2, col=1)
    fig.add_trace(go.Scatter(x=df.index, y=df['HYG_MA'], name=f"HYG {hyg_ma_window}天線", line=dict(color="#ffaa00", width=1.5, dash='dot')), row=2, col=1)

    # 【第三層】：終極透視 - 信貸利差代理指標 vs 動態極值線
    fig.add_trace(go.Scatter(x=df.index, y=df['Credit_Spread_Proxy'], name="信貸利差指標 (LQD/HYG)", line=dict(color="#ffaa00", width=1.5)), row=3, col=1)
    fig.add_trace(go.Scatter(x=df.index, y=df['Spread_Dynamic_High'], name=f"{rolling_window//252} 年 {quantile_pct*100:.0f}% 極值線", line=dict(color="#ff3333", width=1.5, dash='dash')), row=3, col=1)

    # 強制高亮背馳區域
    spread_max_value = df[['Credit_Spread_Proxy', 'Spread_Dynamic_High']].max().max() * 1.05
    fig.add_trace(go.Bar(
        x=df.index, 
        y=np.where(df['Credit_Freeze_Signal'], spread_max_value, 0),
        name="🚨 信用冰封區", 
        marker_color="rgba(255, 170, 0, 0.35)", 
        marker_line_width=0,
        hoverinfo='skip',
        showlegend=False
    ), row=3, col=1)

    fig.update_layout(
        title=dict(text="📊 大鱷實體血壓計：HYG 資金鏈斷裂雷達 (極致回測版)", font=dict(color="white", size=20)),
        template="plotly_dark", height=850, margin=dict(l=20, r=20, t=60, b=20),
        paper_bgcolor="#11141a", plot_bgcolor="#11141a", hovermode="x unified",
        legend=dict(orientation="h", yanchor="bottom", y=1.02, xanchor="right", x=1),
        barmode='overlay'
    )

    fig.update_yaxes(title_text="標普 500 (SPY)", row=1, col=1, showgrid=True, gridcolor="#222834", type="log")
    fig.update_yaxes(title_text="HYG 價格", row=2, col=1, showgrid=True, gridcolor="#222834")
    fig.update_yaxes(title_text="信貸利差", row=3, col=1, showgrid=True, gridcolor="#222834", range=[df['Credit_Spread_Proxy'].min()*0.95, spread_max_value])
    fig.update_xaxes(showgrid=True, gridcolor="#222834")

    st.plotly_chart(fig, use_container_width=True)

    # =========================================================================
    # 🕵️‍♂️ 全新引擎：實戰回測追蹤器 (Historical Backtest)
    # =========================================================================
    st.markdown("---")
    st.markdown("### 🕵️‍♂️ 信用冰封後，大市跌幾多？(最近 10 次信號回測)")
    
    if filtered_signals:
        backtest_data = []
        for i, dt in enumerate(filtered_signals[-10:]): 
            try:
                idx_loc = df.index.get_loc(dt)
                price_t0 = df['SPY'].iloc[idx_loc]
                
                # 計算 T+10 (約兩週) 及 T+20 (約一個月) 的回報
                price_t10 = df['SPY'].iloc[idx_loc + 10] if (idx_loc + 10) < len(df) else np.nan
                price_t20 = df['SPY'].iloc[idx_loc + 20] if (idx_loc + 20) < len(df) else np.nan
                
                ret_t10 = (price_t10 / price_t0 - 1) * 100 if not np.isnan(price_t10) else np.nan
                ret_t20 = (price_t20 / price_t0 - 1) * 100 if not np.isnan(price_t20) else np.nan
                
                backtest_data.append({
                    "🚨 斷鏈日期": dt.strftime("%Y-%m-%d"),
                    "觸發時 SPY 價格": f"${price_t0:.2f}",
                    "T+10日 後果 (約2週)": f"{ret_t10:.2f}%" if not np.isnan(ret_t10) else "⏳ 發酵中",
                    "T+20日 後果 (約1個月)": f"{ret_t20:.2f}%" if not np.isnan(ret_t20) else "⏳ 發酵中"
                })
            except Exception:
                continue
                
        if backtest_data:
            bt_df = pd.DataFrame(backtest_data)
            
            def color_returns(val):
                if "發酵中" in str(val): return 'color: white'
                try:
                    num = float(val.replace('%', ''))
                    return 'color: #ff3333; font-weight: bold' if num < 0 else 'color: #00ff88'
                except: return ''

            st.dataframe(bt_df.style.map(color_returns, subset=['T+10日 後果 (約2週)', 'T+20日 後果 (約1個月)']), 
                         use_container_width=True, hide_index=True)
            st.caption("💡 *信用冰封引發的股市拋售通常極其猛烈！留意表格中紅色的負回報，這就是及時逃生避開的連環暴跌。*")
    else:
        st.info("近期未有符合極端條件的信用冰封信號。")

    # =========================================================================
    # 📚 爺爺終極心法：(純文字 Markdown)
    # =========================================================================
    st.markdown("---")
    st.markdown("### 1️⃣ 信用市場心電圖停頓 (Credit Freeze) —— 【對應第三絕：HYG 與信貸利差】")
    st.markdown("**真相：** 股市跌 20%，聯儲局根本唔會理你。但如果「企業借唔到錢」，聯儲局就會嚇到標尿！")
    st.markdown("**第一時間嘅信號：** 當你見到 HYG (高收益垃圾債 ETF) 突然無量暴跌，或者 BofA 高收益債利差 (Credit Spreads) 突然急速擴闊。")
    st.markdown("**大鱷邏輯：** 這代表銀行同大機構突然「落雨收遮」，唔肯再借錢畀高風險企業。資金鏈一斷，下個禮拜就會有公司破產、裁員。聯儲局一見到信貸利差飆升，就知道如果唔即刻大減息放水，全美國嘅企業就會連環骨牌式倒閉！呢個就係大減息最直接、最暴力嘅「第一根動機」！")

if __name__ == "__main__":
    render_page_2p()