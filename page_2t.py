import streamlit as st
import pandas as pd
import numpy as np
import plotly.express as px
from fed_utils import fetch_fred_series, get_latest_metrics

def render():
    st.markdown("<h1 style='color:#636EFA; font-size:36px; font-family:Arial Black;'>🔵 中央銀行流動性互換 (SWPT) - 全球離岸美元荒</h1>", unsafe_allow_html=True)
    
    st.info("""
### 📌 戰略定位：中央銀行流動性互換 (SWPT) —— 離岸美元荒
* **基準常態**：平時維持喺 **$0 ~ $10 億美元** 附近。

---
### 💡 爺爺的新手極簡教學：SWPT 係咩？點解會引發全球股災？
* **SWPT 的真面目**：「美聯儲借錢畀『外國央行』嘅國際急症室」。
* **點解外國要借？** 美元係全球通行嘅錢。如果歐洲、日本、英國嘅銀行突然搵唔到美元找數，佢哋就會面臨破產。呢個時候，外國央行（例如歐洲央行 ECB）就會打電話求美聯儲印美金借畀佢哋救命。
* **致命警報點睇？** 
  1. 平時呢個數字係 **$0**。只要佢一跳高，代表**海外爆發咗「美元荒」**！
  2. 世界上無美元流通，所有人都會掟賣外國資產（例如歐股、日股、甚至港股）去換美金救命。所以 **SWPT 一旦爆升，全球股市必定大跌，美金匯率必定暴升！** 
  3. 佢就係你預判「全球級股災」最準確嘅核彈雷達！
""")

    st.markdown("""
### 🚨 兩級風暴風險預警線

| 警報級別 | 觸發條件 (億美元) | 市場流動性現況 | 機構級風暴解讀 |
| :--- | :--- | :--- | :--- |
| **🟡 警告 (Warning)** | **餘額 $> 100$ 億美元** | **離岸美元資金緊張** | 歐洲央行 (ECB)、日本央行 (BOJ) 等啟動 Swap Line，代表海外商業銀行難以融資美元。 |
| **🔴 超級警報 (Super Alert)** | **餘額 $> 1,000$ 億美元** | **全球離岸美元海嘯** | 重演 2008 金融海嘯或 2020 疫情全球錢荒！海外美元完全凍結，伴隨全球股市恐慌性暴跌。 |
""")

    st.markdown("<hr style='border:2px solid #444;'>", unsafe_allow_html=True)

    with st.spinner("📡 正在抓取 FRED 數據並比對歷史三大海嘯事件..."):
        df = fetch_fred_series(["SWPT"])
        val, wow = get_latest_metrics(df)

    # --- 🎯 動態計算：離岸美元抽離連續週數 (Duration) ---
    consecutive_weeks = 0
    if not df.empty:
        vals = df['value'].values
        # 從最新一週開始倒數，只要餘額大於 $1 億 (過濾極微小雜訊)，就當作正在發生美元荒
        for v in reversed(vals):
            if v > 1.0:
                consecutive_weeks += 1
            else:
                break

    # --- 動態觸發警報 ---
    if val >= 1000:
        st.error(f"🔴 **超級警報發動**：當前 SWPT 餘額 (${val:,.2f} 億美元) 達風暴級水平，全球離岸美元極度枯竭！")
    elif val >= 100:
        st.warning(f"🟡 **警告級別發動**：當前 SWPT 餘額 (${val:,.2f} 億美元) 突破上限，海外美元資金出現緊張。")
    elif consecutive_weeks >= 4:
        st.warning(f"⚠️ **【慢性錢荒預警】發動**：雖然餘額未達風暴級，但已連續 {consecutive_weeks} 週出現外國央行借款，需提防慢性股災陰乾！")
    else:
        st.success(f"🟢 **安全常態**：當前 SWPT 餘額 (${val:,.2f} 億美元) 處於安全平穩區間，全球無美元荒跡象。")

    # --- 頂部 Metric 卡片 ---
    col1, col2 = st.columns(2)
    col1.metric("最新 SWPT 餘額", f"${val:,.2f} 億美元", f"{wow:+,.2f} 億 WoW")
    
    # 連續週數 Metric 顏色邏輯 (越長越危險)
    dur_color = "inverse" if consecutive_weeks > 0 else "off"
    status_text = "全球美元流動性充裕" if consecutive_weeks == 0 else f"正在發生急性/慢性美元荒"
    col2.metric("離岸美元荒 持續週數", f"{consecutive_weeks} 週 (Weeks)", status_text, delta_color=dur_color)

    st.markdown("---")

    # =========================================================================
    # 📉 加入三大歷史海嘯事件基準對照 (Event Study)
    # =========================================================================
    st.subheader("1️⃣ SWPT 歷史餘額走勢與三大海嘯極限危機打卡標記")
    if not df.empty:
        fig = px.line(df, x="date", y="value")
        fig.update_traces(line_color="#636EFA", line_width=2.5, fill='tozeroy', fillcolor="rgba(99, 110, 250, 0.15)")
        
        # 📌 歷史極限危機打卡標記 (Event Study Benchmarks)
        fig.add_hline(y=5800, line_dash="solid", line_color="#ff3333", line_width=1.5, annotation_text="🔴 2008 雷曼兄弟海嘯 ($5,800億)", annotation_position="top left", annotation_font=dict(color="#ff3333"))
        fig.add_hline(y=4500, line_dash="solid", line_color="#ff8800", line_width=1.5, annotation_text="🟠 2020 疫情全球錢荒 ($4,500億)", annotation_position="top left", annotation_font=dict(color="#ff8800"))
        fig.add_hline(y=600, line_dash="dash", line_color="#ffcc00", line_width=1.5, annotation_text="🟡 2023 SVB 危機 ($600億)", annotation_position="top left", annotation_font=dict(color="#ffcc00"))

        fig.update_layout(
            template="plotly_dark", height=500, margin=dict(l=40, r=40, t=30, b=20),
            paper_bgcolor="#1e212b", plot_bgcolor="#1e212b", hovermode="x unified",
            xaxis_title="", yaxis_title="億美元 ($ 100 Millions)"
        )
        st.plotly_chart(fig, use_container_width=True)

if __name__ == "__main__":
    render()