import streamlit as st
import pandas as pd
import numpy as np
import plotly.express as px
from fed_utils import fetch_fred_series, get_latest_metrics

def render():
    st.markdown("<h1 style='color:#00CC96; font-size:36px; font-family:Arial Black;'>🟢 銀行定期融資計劃 (BTFP) 到期監測</h1>", unsafe_allow_html=True)
    
    st.info("""
### 📌 戰略定位：銀行定期融資計劃 (BTFP) —— 資產負債表浮虧與到期壓力
* **基準常態**：已於 2024 年 3 月 11 日停止發放新貸款，目前餘額應持續歸零或維持喺 **$0 億美元**。

---
### 💡 爺爺的新手極簡教學：BTFP 係咩？點解仲要監察佢？
* **BTFP 的誕生**：2023 年 SVB 破產，原因係手頭上嘅美國國債蝕入肉（浮虧），無人肯買。美聯儲於是特製咗這支「特效吊命針」，畀銀行按債券**原價**抵押借錢救命。最高峰時借咗 $1,670 億出去！
* **點解要監察佢？** 呢支針喺 2024 年 3 月已經停咗。正常嚟講，銀行借夠 1 年就要還錢。如果這條青色線順利跌返落 $0，代表銀行已經「戒奶」康復。
* **致命警報點睇？** 
  1. 如果條線**跌唔落去（死魚平坦）**，甚至喺 $100 億以上橫行，代表有班中小型銀行根本無錢還，底層虧損仲未搞掂！
  2. 如果 BTFP 條數跌咗，但隔籬台 **WPC (貼現窗) 條數升返**，代表銀行只不過係「借大耳窿去還卡數」，危機根本無解除！
""")

    st.markdown("""
### 🚨 兩級風暴與溢出風險預警線

| 警報級別 | 觸發條件 (億美元) | 市場流動性現況 | 機構級風暴解讀 |
| :--- | :--- | :--- | :--- |
| **🟡 警告 (Warning)** | **餘額 $> 100$ 億美元** <br>或 **還款進度停滯** | **貸款還款進度受阻** | 代表部分中小型銀行嘅美債浮虧壓力尚未消化，無法順利按時歸還 BTFP 救市貸款。 |
| **🔴 超級 (Super Alert)** | **餘額 $> 1,000$ 億美元** | **銀行業風暴爆發** | 重演 2023 年矽谷銀行倒閉潮！代表中小銀行浮虧爆雷，流動性危機全面擴散。 |
| **⚠️ 債務轉移警報** | **BTFP 下降，但 WPC 上升** | **左手交右手 (借新還舊)** | 銀行只不過是把債務從 BTFP 轉移到 WPC (貼現窗)，資金並未真正還清，底層流動性依然乾涸！ |
""")

    st.markdown("<hr style='border:2px solid #444;'>", unsafe_allow_html=True)

    with st.spinner("📡 正在抓取 FRED 數據並計算歷史峰值歸零進度..."):
        # 抓取 BTFP 數據
        df_btfp = fetch_fred_series(["H41RESPPALGTRFNWW", "H41RESPALGTRFNWW", "RESPPALGTRFNWW"])
        val_btfp, wow_btfp = get_latest_metrics(df_btfp)

        # 抓取 WPC 數據（用作溢出監測）
        df_wpc = fetch_fred_series(["WPC"])
        val_wpc, wow_wpc = get_latest_metrics(df_wpc)

    # --- 🎯 歷史峰值歸零進度 (Runoff Progress) ---
    PEAK_BTFP_2024 = 1670.0 # 2024 年 3 月最高峰值約 1670 億美元
    if val_btfp <= 0:
        runoff_progress = 100.0
    elif val_btfp >= PEAK_BTFP_2024:
        runoff_progress = 0.0
    else:
        runoff_progress = (1.0 - (val_btfp / PEAK_BTFP_2024)) * 100.0

    # --- 動態觸發警報 ---
    is_spillover = (wow_btfp < 0) and (wow_wpc > 0) # BTFP 下降，但 WPC 上升

    if val_btfp >= 1000:
        st.error(f"🔴 **超級警報發動**：當前 BTFP 餘額 (${val_btfp:,.2f} 億美元) 達風暴級水平！大量銀行需靠美聯儲續命！")
    elif is_spillover:
        st.error(f"⚠️ **【債務轉移溢出警報】發動**：BTFP 本週縮減 ({wow_btfp:+.2f} 億)，但貼現窗 (WPC) 同步上升 ({wow_wpc:+.2f} 億)！銀行極可能只是在拆東牆補西牆，並未真正恢復流動性！")
    elif val_btfp >= 100:
        st.warning(f"🟡 **警告級別發動**：當前 BTFP 餘額 (${val_btfp:,.2f} 億美元) 超出正常歸零區間，還有 {100-runoff_progress:.1f}% 貸款未還，還款進度滯後。")
    else:
        st.success(f"🟢 **安全常態**：當前 BTFP 餘額 (${val_btfp:,.2f} 億美元) 穩定歸零，歷史峰值消化進度達 {runoff_progress:.1f}%，救市任務即將圓滿完成。")

    # --- 頂部 Metric 卡片 (加入歸零進度條) ---
    col1, col2 = st.columns(2)
    col1.metric("最新 BTFP 餘額", f"${val_btfp:,.2f} 億美元", f"{wow_btfp:+,.2f} 億 WoW")
    
    # 進度條顏色邏輯：越高越好 (歸零代表健康)
    progress_color = "normal"
    col2.metric("歷史峰值歸零進度 (Runoff Rate)", f"{runoff_progress:.1f}%", "100% 代表完全消化 $1670億 負債", delta_color=progress_color)

    # 模擬簡單嘅 Streamlit 原生進度條 (視覺化體驗)
    st.progress(int(runoff_progress) if runoff_progress <= 100 else 100, text=f"債務消除進度: {runoff_progress:.1f}%")

    st.markdown("---")

    # =========================================================================
    # 📉 全尺寸高階圖表 (由上至下展開)
    # =========================================================================

    st.subheader("1️⃣ BTFP 餘額歷史與到期衰減曲線 ($ 億美元)")
    if not df_btfp.empty:
        fig1 = px.line(df_btfp, x="date", y="value")
        fig1.update_traces(line_color="#00CC96", line_width=2.5, fill='tozeroy', fillcolor="rgba(0, 204, 150, 0.2)")
        
        # 標註歷史峰值 1670 基準線
        fig1.add_hline(y=PEAK_BTFP_2024, line_dash="dash", line_color="#ffcc00", annotation_text="2024/03 歷史最高峰 ($1,670億)", annotation_position="top left")

        fig1.update_layout(
            template="plotly_dark", height=480, margin=dict(l=40, r=40, t=30, b=20),
            paper_bgcolor="#1e212b", plot_bgcolor="#1e212b", hovermode="x unified",
            xaxis_title="", yaxis_title="億美元 ($ 100 Millions)"
        )
        st.plotly_chart(fig1, use_container_width=True)

if __name__ == "__main__":
    render()