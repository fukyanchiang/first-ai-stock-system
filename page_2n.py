import streamlit as st
import pandas as pd
import numpy as np
import yfinance as yf
import plotly.graph_objects as go
from plotly.subplots import make_subplots

# =========================================================================
# ⚙️ 1. 數據引擎：純 yfinance 提取 10Y, 3M 與 SPY
# =========================================================================
@st.cache_data(ttl=3600, show_spinner=False)
def fetch_yield_curve_data():
    try:
        tickers = ['^TNX', '^IRX', 'SPY']
        data = yf.download(tickers, start='1998-01-01', progress=False)['Close']
        
        if data.empty or '^TNX' not in data.columns or '^IRX' not in data.columns or 'SPY' not in data.columns:
            return pd.DataFrame()
            
        if data.index.tz is not None:
            data.index = data.index.tz_localize(None)
            
        data = data.ffill().dropna()
        data['Spread'] = data['^TNX'] - data['^IRX']
        return data[['Spread', 'SPY', '^TNX', '^IRX']]
        
    except Exception as e:
        st.error(f"⚠️ 數據抓取失敗，請檢查網絡連線：{e}")
        return pd.DataFrame()

# =========================================================================
# 🚀 2. 主頁面渲染函數 (render_page_2n)
# =========================================================================
def render_page_2n():
    st.markdown("## 🏛️ 壓箱底第一絕：收益率曲線「解除倒掛 (10Y-3M)」預警塔")
    st.markdown("華爾街終極真相：倒掛唔可怕，倒掛解除 (Bull Steepener) 才是死神真正敲門聲！\n*(系統已開啟「抗雜訊引擎」與「牛熊陡自動判定」)*")
    st.markdown("---")

    with st.spinner("📡 正在構建 10Y-3M 終極息差大數據與抗雜訊推演..."):
        df = fetch_yield_curve_data()

    if df.empty:
        st.error("❌ 無法取得收益率曲線數據，請檢查 yfinance 連線。")
        return

    # --- 🧠 算法優化：抗騙線/抗雜訊過濾器 ---
    cross_above = (df['Spread'] >= 0) & (df['Spread'].shift(1) < 0)
    raw_trigger_dates = df[cross_above].index
    
    trigger_dates = []
    for dt in raw_trigger_dates:
        if not trigger_dates or (dt - trigger_dates[-1]).days > 180:
            trigger_dates.append(dt)
            
    last_trigger_date = None
    kill_zone_date = None
    if trigger_dates:
        last_trigger_date = trigger_dates[-1]
        kill_zone_date = last_trigger_date + pd.DateOffset(months=21)

    # --- 最新狀態與牛熊陡判定 ---
    latest_spread = df['Spread'].iloc[-1]
    prev_spread = df['Spread'].iloc[-2]
    
    lookback = 21 if len(df) > 21 else len(df) - 1
    delta_tnx = df['^TNX'].iloc[-1] - df['^TNX'].iloc[-lookback]
    delta_irx = df['^IRX'].iloc[-1] - df['^IRX'].iloc[-lookback]
    delta_spread = df['Spread'].iloc[-1] - df['Spread'].iloc[-lookback]

    steepener_status = ""
    if delta_spread > 0:
        if delta_irx < 0 and delta_tnx < 0 and abs(delta_irx) > abs(delta_tnx):
            steepener_status = "🐃 牛陡 (Bull Steepener) - 息率齊降，短息暴跌為主因！(危險🚨)"
        elif delta_irx < 0 and delta_tnx >= 0:
            steepener_status = "🐃 牛陡 (Bull Steepener) - 短息急降，長息企穩！(危險🚨)"
        elif delta_tnx > 0 and delta_irx > 0 and delta_tnx > delta_irx:
            steepener_status = "🐻 熊陡 (Bear Steepener) - 息率齊升，長息暴升為主因！(殺估值⚠️)"
        elif delta_tnx > 0 and delta_irx <= 0:
            steepener_status = "🐻 熊陡 (Bear Steepener) - 長息急升，短息高企！(殺估值⚠️)"
        else:
            steepener_status = "📈 曲線陡峭化中 (Steepening)"
    else:
        steepener_status = "📉 曲線平坦/倒掛加劇 (Flattening/Inverting)"

    if latest_spread < 0:
        status_text = "⚠️ 倒掛深淵中 (Inverted)"
        status_desc = "資金正於最後狂歡，密切留意解除倒掛的時刻！"
    elif latest_spread >= 0 and prev_spread < 0:
        status_text = "🚨 剛剛解除倒掛！"
        status_desc = "死神敲門，但需確認是否為『熊陡』假動作！"
    else:
        status_text = "🟢 正常收益率 (Normal)"
        if kill_zone_date:
            status_desc = f"最後宏觀解除日為 {last_trigger_date.strftime('%Y-%m')}，21個月極限定位在 {kill_zone_date.strftime('%Y-%m')}。"
        else:
            status_desc = "收益率曲線處於正數區間。"

    col1, col2, col3 = st.columns(3)
    with col1:
        st.metric("美債 10Y-3M 最新息差", f"{latest_spread:.2f}%", f"{latest_spread - prev_spread:.2f}%")
    with col2:
        st.info(f"**當前曲線狀態：** {status_text}")
    with col3:
        st.warning(f"**爺爺戰術雷達：** {status_desc}")
        
    st.success(f"🔎 **近一個月陡峭化驅動力判定：** {steepener_status} (10年期變化: {delta_tnx:.2f}% | 3個月期變化: {delta_irx:.2f}%)")

    # --- 繪製歷史拆解雙軸巨幕圖 ---
    fig = make_subplots(specs=[[{"secondary_y": True}]])
    fig.add_hrect(y0=-10, y1=0, line_width=0, fillcolor="rgba(255, 51, 51, 0.08)", layer="below", secondary_y=False)

    fig.add_trace(
        go.Scatter(x=df.index, y=df['Spread'], name="10Y-3M 美債息差 (%)", line=dict(color="#00e5ff", width=1.5), fill='tozeroy', fillcolor='rgba(0, 229, 255, 0.05)', hovertemplate="日期: %{x|%Y-%m-%d}<br>息差: %{y:.2f}%<extra></extra>"),
        secondary_y=False
    )
    fig.add_trace(
        go.Scatter(x=df.index, y=df['SPY'], name="標普 500 (SPY)", line=dict(color="#ffffff", width=2), hovertemplate="SPY 價格: $%{y:.2f}<extra></extra>"),
        secondary_y=True
    )
    fig.add_hline(y=0, line_width=2, line_color="#ff3333", line_dash="dash", secondary_y=False)

    for dt in trigger_dates:
        fig.add_vline(x=dt, line_width=1.5, line_color="#ffeb3b", line_dash="solid", annotation_text="🚨宏觀解除倒掛", annotation_position="top left", annotation_font=dict(color="#ffeb3b", size=11, family="Arial Black"))

    if kill_zone_date:
        current_max_date = df.index[-1]
        fig.add_vline(x=kill_zone_date, line_width=2.5, line_color="#ff1744", line_dash="dashdot", annotation_text=f"💀 21個月極限: {kill_zone_date.strftime('%Y-%m')}", annotation_position="top left", annotation_font=dict(color="#ff1744", size=14, family="Arial Black"))
        if kill_zone_date > current_max_date:
            fig.update_xaxes(range=[df.index[0], kill_zone_date + pd.DateOffset(months=3)])

    fig.update_layout(
        title=dict(text="📊 歷史大對照：10Y-3M 息差 vs 標普 500 (附牛熊判定)", font=dict(color="white", size=20)),
        template="plotly_dark", height=650, margin=dict(l=20, r=20, t=60, b=20),
        paper_bgcolor="#11141a", plot_bgcolor="#11141a", hovermode="x unified",
        legend=dict(orientation="h", yanchor="bottom", y=1.02, xanchor="right", x=1)
    )
    fig.update_xaxes(title_text="", showgrid=True, gridcolor="#222834")
    fig.update_yaxes(title_text="10Y-3M 息差 (%)", secondary_y=False, showgrid=True, gridcolor="#222834", zeroline=False)
    fig.update_yaxes(title_text="標普 500 指數 (SPY $)", secondary_y=True, showgrid=False, type="log")

    st.plotly_chart(fig, use_container_width=True)

    # =========================================================================
    # 📚 爺爺終極心法：(完全純文字 Markdown，無 HTML)
    # =========================================================================
    st.markdown("---")
    
    # 保留之前的解說
    st.markdown("## 🩸 為何「解除倒掛」才是真正的股災起點？")
    st.markdown("散戶誤以為倒掛瞬間就會暴跌，錯過了最後一段狂歡；大鱷都在等待**「倒掛結束、息差快速回正」**的那一刻！這意味著實體經濟陷入衰退，美聯儲正在實施恐慌性降息 (Bull Steepener)。")
    
    st.markdown("### ⚠️ 爺爺的壓箱底警告：打破「21 個月」的刻舟求劍迷思！")
    st.markdown("歷史上最長的滯後確實是 21 個月（如 2000年與 2007年），但這**絕對不是一個死板的計時器**。聯準會不會看著日曆來引爆股災！\n\n特別是在 2025-2026 年的環境下，我們見證了極罕見的**「熊陡 (Bear Steepener)」**—— 聯準會死不降息 (Higher for Longer)，而是財政部狂發債導致長債息率抽升而解除倒掛。這種情況下，大崩盤的真正引爆點，並非單純的「時間到」，而是**「底層資金鏈斷裂 (Something Breaks)」**！")

    st.markdown("### 🎯 大鱷軍令：如何配合【第二/第三絕】捕捉真正的死神？")
    st.markdown("* **信號一 (本面板)**：當黃色垂直線出現，代表進入「極端危險警戒區」。")
    st.markdown("* **信號二 (HYG 信貸利差)**：若黃線出現後，**HYG (垃圾債) 開始無量暴跌，信用利差急劇擴闊**。這代表銀行開始「落雨收遮」，實體企業借不到錢，這才是聯準會即將恐慌降息的**第一根致命動機**！")
    st.markdown("* **信號三 (VVIX 暗流)**：大市還在漲，但 **VVIX 突然呈大角度飆升**，代表華爾街巨鯨正在瘋狂買入末日保險。")
    st.markdown("**結論：** 結合這三大絕技，你就能過濾掉所有的假動作，在市場真正閃崩的前夕，精準按下清倉核按鈕！")

    st.markdown("---")

    # 加上全新的純文字解說 (完全照抄要求)
    st.markdown("### 🦅 爺爺壓箱底心法：如何分辨「牛陡」與「熊陡」？")
    st.markdown("短息跌得快過長息 ➔ 呢個叫 **牛陡 (Bull Steepener)**。")
    st.markdown("長息升得快過短息 ➔ 呢個叫 **熊陡 (Bear Steepener)**。")
    
    st.markdown("#### 🐃 第一隻巨獸：牛陡 (Bull Steepener) —— 「死神的敲門聲」")
    st.markdown("**【點解叫「牛」？】**：因為喺債券市場，息率下跌，代表債券價格上升（牛市）。短息急跌，帶動短債價格大升，所以叫「Bull」。")
    st.markdown("**【發生情境】**：\n當實體經濟出現大問題（例如失業率飆升、企業連環倒閉、甚至爆發金融海嘯），聯儲局（Fed）為咗救市，會恐慌性地大幅、快速減息。\n減息會令對政策最敏感嘅「短息（2年/3個月）」出現斷崖式暴跌。雖然長息都會跌，但跌幅遠遠唔及短息。結果，長短息差瞬間由負轉正，曲線急劇變陡。")
    st.markdown("**【大鱷解讀 / 對股市的影響】**：\n* **終極股災預警**：這就是爺爺之前講嘅「死神敲門聲」！歷史上，2000 年科網泡沫、2007 年金融海嘯、2020 年新冠閃崩，全部都係伴隨住極度暴力的 Bull Steepener 發生。\n* **資金流向**：大鱷知道實體經濟已經爛透，聯儲局減息都係「遠水救不能近火」。資金會瘋狂拋售股票（Risk-Off），湧入短年期國債避險。股市迎來主跌浪。")
    
    st.markdown("#### 🐻 第二隻巨獸：熊陡 (Bear Steepener) —— 「溫水煮青蛙的絞肉機」")
    st.markdown("**【點解叫「熊」？】**：因為息率上升，代表債券價格下跌（熊市）。長息急升，帶動長債價格大跌，所以叫「Bear」。")
    st.markdown("**【發生情境】**：\n這是一種相對罕見，但極具殺傷力嘅現象（正正就係 2023 - 2025 年發生緊嘅事）。\n聯儲局因為通脹壓力，死都唔肯減息（維持短息喺高位）。但係，因為美國財政部瘋狂發行長債印銀紙，或者市場擔心長期通脹失控（例如 AI 耗電、銅價大升），導致無人肯買長債，結果長息（10年期）被迫「暴力抽升」，由下而上追過短息，令曲線解除倒掛。")
    st.markdown("**【大鱷解讀 / 對股市的影響】**：\n* **溫水煮青蛙 / 估值殺手**：熊陡唔會即刻引發股災，因為實體經濟表面上仲頂得住，聯儲局都未需要減息救火。\n* **但係殺估值**：無風險嘅 10 年期長息去到 5 厘甚至更高，大資金會覺得「買股收息不如買債收息」。股市嘅估值（P/E Ratio）會被強行壓低。股市唔會直線暴跌，但會出現劇烈震盪、板塊極度分化、以及深度回調（例如跌 10-15%）。\n* **終局 (End-Game)**：熊陡係一種「慢性毒藥」。極高嘅長息最終會「勒死」實體經濟（例如令按揭利率過高、企業無法發債融資）。當企業資金鏈斷裂嗰一刻，聯儲局最終都會被迫減息，將「熊陡」強行切換成「牛陡」，到時真正嘅大崩盤就會殺到！")
    
    st.markdown("#### 🦅 爺爺的戰術總結 (一句話記實)：")
    st.markdown("* **牛陡 (Bull Steepener)** ＝ 短息暴跌 ＝ 聯儲局恐慌救市 ＝ **股市即刻大崩盤 (Crash)！**")
    st.markdown("* **熊陡 (Bear Steepener)** ＝ 長息暴升 ＝ 通脹與債務失控 ＝ **股市震盪殺估值 (Correction)，醞釀未來的崩盤！**")

if __name__ == "__main__":
    render_page_2n()