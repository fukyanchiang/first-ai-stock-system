import streamlit as st
import pandas as pd
import numpy as np
import plotly.express as px
import plotly.graph_objects as go
from plotly.subplots import make_subplots
from fed_utils import fetch_fred_series, get_latest_metrics

def render():
    st.markdown("<h1 style='color:#FFA15A; font-size:36px; font-family:Arial Black;'>🟡 外國官方逆回購 (RPF) - 海外央行避險水庫</h1>", unsafe_allow_html=True)
    
    st.info("""
### 📌 戰略定位：外國官方逆回購 (RPF) —— 海外央行避險水庫
* **基準常態**：目前維持喺 **$3,000 ~ $4,000 億美元 ($300,000M ~ $400,000M)** 嘅高位水準。

---
### 💡 爺爺的新手極簡教學：RPF 係咩？點解佢急跌會引爆全球美債與匯市海嘯？
* **RPF 的真面目**：「外國央行存喺美聯儲嘅『私房錢儲蓄戶口』」。
* **點解外國央行要存錢喺度？** 日美、歐美利息有差距，日本、歐洲央行手頭上有大把多餘美金現金，平時存喺美聯儲可以穩陣收息。
* **致命警報點睇？** 
  1. 呢個戶口平時好高（幾千億美元）。但如果佢出現**斷崖式急跌（幾百甚至上千億美金被提走）**，代表外國央行正在急需現金！
  2. 點解要急提美金？因為佢哋本國貨幣（例如日圓、歐元）正在暴跌！外國央行要提走美金現金去外匯市場「賣美元、買本幣（匯市干預）」來護盤。
  3. **核彈級連鎖反應**：外國央行提走美金後，往往還會在市場拋售美國國債，導致美債收益率飆升、全球金融市場劇烈震盪！

---
### 📈 下面 2 張圖，你只需要識咁樣睇：
* **1️⃣ 圖 1 (睇大水庫水位)**：青色線。如果平穩喺 3~4千億，安全。如果突然插水式大跌，穿過黃線甚至紅線，代表外國央行瘋狂提款！
* **2️⃣ 圖 2 (捉撳錢速度 / 匯市干預)**：
  * **向上鮮紅柱**：代表外國央行正喺度「撳錢」！紅柱越長，代表佢哋越心急。
  * **紅柱穿過黃線 ($300億)**：輕度出手（例如日本央行偷偷地托日圓）。
  * **紅柱穿過紅線 ($800億)**：全球大恐慌，各國瘋狂拋美金救本幣，準備迎接環球股匯債三殺！
  * **向下暗綠柱**：代表外國央行「存錢」入去，風平浪靜。
""")

    st.markdown("""
### 🚨 兩級風暴風險預警線

| 警報級別 | 觸發條件 (億美元) | 市場流動性現況 | 機構級風暴解讀 |
| :--- | :--- | :--- | :--- |
| **🟡 警告級別 (Warning)** | **單週急跌 $> 300$ 億美元**<br>或 **總餘額 $< 2,500$ 億美元** | **匯市干預預警** | 美債收益率飆升、本國貨幣面臨貶值壓力，外國央行開始提走 RPF 現金準備介入外匯市場「拋美元救本幣」。 |
| **🔴 超級警報 (Super Alert)** | **單週急跌 $> 1,000$ 億美元**<br>或 **總餘額 $< 1,500$ 億美元** | **拋售美債與匯市海嘯** | 全球主要央行大規模抽走美元現金並拋售美債以拯救本國貨幣！美債收益率面臨暴升失控風險，全球債市與匯市劇烈震盪。 |
""")

    st.markdown("<hr style='border:2px solid #444;'>", unsafe_allow_html=True)

    with st.spinner("📡 正在抓取 FRED 全量數據並計算 4 週累積匯市干預強度..."):
        df = fetch_fred_series(["WLRRAL", "RPTCW", "RPFROTC156N"])
        val, wow = get_latest_metrics(df)

    # --- 🎯 動態計算：4週累積抽離強度 (FX Intervention Intensity) ---
    drop_4w = 0.0
    if not df.empty and len(df) >= 5:
        df = df.sort_values("date").copy()
        # 建立整個歷史的 4週變動序列 (diff(4))
        df["diff_4w"] = df["value"].diff(4)
        # 抽離量 (Drop) = - (變動量)，正數代表提款抽走，負數代表存錢入去
        df["drop_4w"] = -df["diff_4w"]
        
        drop_4w = df["drop_4w"].iloc[-1]

    # 匯市干預強度標註
    if drop_4w >= 800:
        intervention_label = "🔴 重度匯市干預（拋美元救本幣）"
    elif drop_4w >= 300:
        intervention_label = "🟡 輕度匯市干預（央行微調護盤）"
    else:
        intervention_label = "🟢 匯市常態平穩"

    # --- 動態觸發警報 ---
    if wow <= -1000 or val <= 1500 or drop_4w >= 800:
        st.error(f"🔴 **超級警報發動**：當前 RPF 餘額 (${val:,.2f} 億美元，4週累積抽離 ${drop_4w:,.2f} 億) 進入風暴級抽離區！{intervention_label}，提防美債與匯市海嘯！")
    elif wow <= -300 or val <= 2500 or drop_4w >= 300:
        st.warning(f"🟡 **警告級別發動**：當前 RPF 餘額 (${val:,.2f} 億美元，4週累積抽離 ${drop_4w:,.2f} 億) 資金出現顯著抽離。標註：{intervention_label}。")
    else:
        st.success(f"🟢 **安全常態**：當前 RPF 餘額 (${val:,.2f} 億美元) 資金極度充沛，4週累積變動處於常態健康區間。")

    # --- 頂部 Metric 卡片 (加入 4 週累積抽離強度) ---
    col1, col2 = st.columns(2)
    col1.metric("最新 RPF 餘額", f"${val:,.2f} 億美元", f"{wow:+,.2f} 億 WoW")
    
    # 4週累積抽離 Metric (提款越多，顏色越警告)
    drop_color = "inverse" if drop_4w > 0 else "normal"
    col2.metric("4週累積抽離強度 (4W Drop)", f"${drop_4w:+,.2f} 億美元", intervention_label, delta_color=drop_color)

    st.markdown("---")

    # =========================================================================
    # 📉 全尺寸高階圖表 1 & 2 (由上至下展開)
    # =========================================================================
    st.subheader("1️⃣ 外國官方逆回購 (RPF) 歷史餘額走勢 ($ 億美元)")
    if not df.empty:
        fig1 = px.line(df, x="date", y="value")
        fig1.update_traces(line_color="#FFA15A", line_width=2.5, fill='tozeroy', fillcolor="rgba(255, 161, 90, 0.15)")
        
        # 標註警告水位線
        fig1.add_hline(y=2500, line_dash="dash", line_color="#ffcc00", annotation_text="🟡 警告警戒線 ($2,500億)", annotation_position="top left", annotation_font=dict(color="#ffcc00"))
        fig1.add_hline(y=1500, line_dash="solid", line_color="#ff3333", annotation_text="🔴 風暴海嘯線 ($1,500億)", annotation_position="top left", annotation_font=dict(color="#ff3333"))

        fig1.update_layout(template="plotly_dark", height=450, margin=dict(l=40, r=40, t=30, b=20), paper_bgcolor="#1e212b", plot_bgcolor="#1e212b", hovermode="x unified", xaxis_title="", yaxis_title="億美元")
        st.plotly_chart(fig1, use_container_width=True)

    st.markdown("---")

    st.subheader("2️⃣ 4週累積抽離強度追蹤 (匯市干預脈衝圖)")
    if not df.empty and 'drop_4w' in df.columns:
        # 只顯示 2018 年打後的數據，因為太早期嘅波動無參考價值
        df_recent = df[df['date'].dt.year >= 2018].copy()
        
        fig2 = go.Figure()
        
        # 畫柱狀圖：如果係提走錢 (大於0)，用鮮紅色；存錢入去 (細於0)，用暗綠色
        colors = ["#ff3333" if val > 0 else "#005533" for val in df_recent["drop_4w"]]
        
        fig2.add_trace(go.Bar(
            x=df_recent["date"], y=df_recent["drop_4w"],
            marker_color=colors, name="4週淨抽離量 ($ 億美元)"
        ))
        
        # 標註干預強度警戒線
        fig2.add_hline(y=800, line_dash="solid", line_color="#ff3333", line_width=2, annotation_text="🔴 重度干預線 ($800億)", annotation_position="top left", annotation_font=dict(color="#ff3333"))
        fig2.add_hline(y=300, line_dash="dash", line_color="#ffcc00", line_width=2, annotation_text="🟡 輕度干預線 ($300億)", annotation_position="top left", annotation_font=dict(color="#ffcc00"))
        # 0軸線
        fig2.add_hline(y=0, line_dash="solid", line_color="#ffffff", line_width=1)

        fig2.update_layout(
            template="plotly_dark", height=450, margin=dict(l=40, r=40, t=30, b=20),
            paper_bgcolor="#1e212b", plot_bgcolor="#1e212b", hovermode="x unified",
            xaxis_title="", yaxis_title="抽離量 (億美元)",
            title="正數(紅柱)代表外國央行提走現金；負數(暗綠)代表存錢入去"
        )
        st.plotly_chart(fig2, use_container_width=True)

if __name__ == "__main__":
    render()