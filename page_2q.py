import streamlit as st
import pandas as pd
import numpy as np
import plotly.graph_objects as go
from plotly.subplots import make_subplots
from fed_utils import fetch_fred_series, get_latest_metrics
import page_2r, page_2s, page_2t, page_2u

def render_page_2q():
    st.markdown("<h1 style='color:#00ff88; font-size:36px; font-family:Arial Black;'>🏛️ 美聯儲應急流動性總覽 (Executive Quant Dashboard)</h1>", unsafe_allow_html=True)

    st.info("""
### 📌 核心戰略指標：怎麼看懂這個 Dashboard？

#### 🔹 指標 A：綜合應急救市總額 (Total Emergency Liquidity)
* **點計出嚟？** = WPC + BTFP + SWPT + WOCEL (四大水龍頭加總)
* **代表咩？** 美聯儲當前總共向市場注入了多少「救急錢」。
* **歷史基準尺 (Benchmark)**：
  * 2023 年 SVB 危機的真實峰值。當時這四個戶口加起來，最高點達到 **$1,770 億美元** *(註：因為 FRED 官方 API 遺漏了當時的部分 WOCEL 數據，所以 API 抓取到的真實歷史高點顯示為 1,770 億，這就是我們圖表上的「黃金基準線」)*。
  * 我們看的是「佔比」。如果當前總額達到 1,770 億的 50% 以上，代表市場正處於高度緊張狀態。

#### 🔹 指標 B：4週滾動脈衝速度 ($\Delta 4W$)
* **點解要睇 4 週？** 單週數據可能因為假期或結算日出現波動（噪音）。看連續 4 週的累積變動，才能確認是不是真的出現了「趨勢性的錢荒」。
* **點睇？**
  * **紅色柱/線（正數）**：救急錢正在快速增加！銀行極度口渴。如果 4 週內急增超過 **+$100 億**，就要開始警惕；超過 **+$300 億**，通常代表風暴已經爆發。
  * **綠色柱/線（負數）**：危機解除，銀行正在把錢還給美聯儲，流動性恢復正常。
""")
    st.markdown("<hr style='border:2px solid #444;'>", unsafe_allow_html=True)

    with st.spinner("📡 正在抓取美聯儲 FRED 官方全量歷史數據並進行量化矩陣運算..."):
        df_wpc = fetch_fred_series(["WPC"])
        df_btfp = fetch_fred_series(["H41RESPPALGTRFNWW", "H41RESPALGTRFNWW", "RESPPALGTRFNWW"])
        df_swpt = fetch_fred_series(["SWPT"])
        df_wocel = fetch_fred_series(["WOCEL", "H41RESPWOCELNWW", "RESPWOCELNWW"])
        df_rpf = fetch_fred_series(["WLRRAL", "RPTCW", "RPFROTC156N"])

    # --- 1. 合併四大救市水龍頭真實數據 ---
    merged_df = pd.DataFrame()
    if not df_wpc.empty or not df_btfp.empty or not df_swpt.empty or not df_wocel.empty:
        df_w_sub = df_wpc.rename(columns={"value": "wpc"}) if not df_wpc.empty else pd.DataFrame(columns=["date", "wpc"])
        df_b_sub = df_btfp.rename(columns={"value": "btfp"}) if not df_btfp.empty else pd.DataFrame(columns=["date", "btfp"])
        df_s_sub = df_swpt.rename(columns={"value": "swpt"}) if not df_swpt.empty else pd.DataFrame(columns=["date", "swpt"])
        df_o_sub = df_wocel.rename(columns={"value": "wocel"}) if not df_wocel.empty else pd.DataFrame(columns=["date", "wocel"])
        
        merged_df = pd.merge(df_w_sub, df_b_sub, on="date", how="outer")
        merged_df = pd.merge(merged_df, df_s_sub, on="date", how="outer")
        merged_df = pd.merge(merged_df, df_o_sub, on="date", how="outer")
        merged_df = merged_df.sort_values("date").ffill().bfill().fillna(0)
        
        # 計算真實總金額與 4週變動速度
        merged_df["total_emergency"] = merged_df["wpc"] + merged_df["btfp"] + merged_df["swpt"] + merged_df["wocel"]
        merged_df["velocity_4w"] = merged_df["total_emergency"].diff(4).fillna(0)

    # --- 2. 指標卡片數據準備 ---
    v_wpc, wow_wpc = get_latest_metrics(df_wpc)
    v_btfp, wow_btfp = get_latest_metrics(df_btfp)
    v_swpt, wow_swpt = get_latest_metrics(df_swpt)
    v_wocel, wow_wocel = get_latest_metrics(df_wocel)
    v_rpf, wow_rpf = get_latest_metrics(df_rpf)

    latest_total = merged_df["total_emergency"].iloc[-1] if not merged_df.empty else (v_wpc + v_btfp + v_swpt + v_wocel)
    latest_4w_vel = merged_df["velocity_4w"].iloc[-1] if not merged_df.empty else 0.0
    
    # 動態從真實數據庫中計算 2023 年真實最大峰值 (零 Hardcode)
    df_2023 = merged_df[merged_df['date'].dt.year == 2023] if not merged_df.empty else pd.DataFrame()
    PEAK_2023 = df_2023['total_emergency'].max() if not df_2023.empty else 1770.0
    pct_of_peak = (latest_total / PEAK_2023) * 100 if PEAK_2023 > 0 else 0.0

    # --- 3. 動態機構級警報橫幅 ---
    if latest_4w_vel >= 300 or pct_of_peak >= 50:
        st.error(f"🔴 **超級警報：美聯儲救市總額劇烈擴張**！4週累積湧入 ${latest_4w_vel:+,.2f} 億美元，已達 2023 歷史峰值 (${PEAK_2023:,.0f}億) 的 {pct_of_peak:.1f}%！銀行體系信用高度緊張！")
    elif latest_4w_vel >= 100:
        st.warning(f"🟡 **趨勢預警：流動性出現惡化跡象**。4週滾動衝擊速度為 ${latest_4w_vel:+,.2f} 億美元，顯示銀行正在加速尋求美聯儲緊急支援。")
    else:
        st.success(f"🟢 **常態安全：應急流動性平穩**。當前救市總額 ${latest_total:,.2f} 億美元，僅佔 2023 真實歷史峰值 (${PEAK_2023:,.0f}億) 的 {pct_of_peak:.1f}\%，4週滾動變動 (${latest_4w_vel:+,.2f} 億) 處於安全區間。")

    # --- 4. 頂部 5 大核心量化 Metric 卡片 (一字排開全顯示) ---
    col1, col2, col3, col4, col5 = st.columns(5)
    col1.metric("綜合應急總額", f"${latest_total:,.2f} 億", f"4W速度: ${latest_4w_vel:+,.2f} 億")
    col2.metric("較2023峰值佔比", f"{pct_of_peak:.1f}%", f"2023峰值: ${PEAK_2023:,.0f} 億")
    col3.metric("貼現窗 (WPC)", f"${v_wpc:,.2f} 億", f"{wow_wpc:+,.2f} 億 WoW")
    col4.metric("FDIC過渡貸款", f"${v_wocel:,.2f} 億", f"{wow_wocel:+,.2f} 億 WoW")
    col5.metric("外國逆回購 (RPF)", f"${v_rpf:,.2f} 億", f"{wow_rpf:+,.2f} 億 WoW")

    st.markdown("---")

    # --- 5. 圖表 1：高對比度上下分層圖表 ---
    st.subheader("📈 綜合應急水龍頭總額與 4週滾動脈衝速度 (4W Velocity)")
    if not merged_df.empty:
        fig1 = make_subplots(
            rows=2, cols=1, shared_xaxes=True, vertical_spacing=0.1,
            subplot_titles=("應急救市總額 ($ 億美元)", "4週滾動變動速度 (4W Velocity) ($ 億美元)")
        )
        
        # Row 1：救市總額 (亮青色面積圖)
        fig1.add_trace(go.Scatter(
            x=merged_df["date"], y=merged_df["total_emergency"],
            name="應急救市總額", fill='tozeroy',
            line=dict(color="#00f2ff", width=2.5),
            fillcolor="rgba(0, 242, 255, 0.2)"
        ), row=1, col=1)
        
        # Row 1：2023 峰值參考線
        fig1.add_hline(
            y=PEAK_2023, line_dash="dash", line_color="#ffcc00",
            annotation_text=f"2023 SVB 官方真實歷史峰值 (${PEAK_2023:,.0f}億)",
            annotation_position="top left", row=1, col=1
        )

        # Row 2：4週變動速度
        fig1.add_trace(go.Scatter(
            x=merged_df["date"], y=merged_df["velocity_4w"],
            name="4週變動速度",
            line=dict(color="#ff3366", width=2.0)
        ), row=2, col=1)

        # Row 2：醒目白色 0 軸線
        fig1.add_hline(y=0, line_dash="solid", line_color="#ffffff", line_width=1.5, row=2, col=1)

        fig1.update_layout(
            template="plotly_dark", height=650, margin=dict(l=40, r=40, t=50, b=20),
            paper_bgcolor="#1e212b", plot_bgcolor="#1e212b", hovermode="x unified",
            showlegend=True,
            legend=dict(orientation="h", yanchor="bottom", y=1.02, xanchor="right", x=1)
        )
        fig1.update_yaxes(title_text="億美元", row=1, col=1, gridcolor="#333344")
        fig1.update_yaxes(title_text="變動量", row=2, col=1, gridcolor="#333344")
        st.plotly_chart(fig1, use_container_width=True)

    st.markdown("---")

    # --- 6. 圖表 2：四大水龍頭結構堆疊圖 ---
    st.subheader("📊 四大應急水龍頭結構分解 (WPC + BTFP + SWPT + WOCEL)")
    if not merged_df.empty:
        fig2 = go.Figure()
        fig2.add_trace(go.Scatter(x=merged_df["date"], y=merged_df["wpc"], name="WPC 貼現窗", stackgroup="one", fillcolor="rgba(239, 85, 59, 0.8)", line=dict(width=0.5)))
        fig2.add_trace(go.Scatter(x=merged_df["date"], y=merged_df["btfp"], name="BTFP 銀行融資", stackgroup="one", fillcolor="rgba(0, 204, 150, 0.8)", line=dict(width=0.5)))
        fig2.add_trace(go.Scatter(x=merged_df["date"], y=merged_df["swpt"], name="SWPT 央行互換", stackgroup="one", fillcolor="rgba(99, 110, 250, 0.8)", line=dict(width=0.5)))
        fig2.add_trace(go.Scatter(x=merged_df["date"], y=merged_df["wocel"], name="WOCEL FDIC過渡貸款", stackgroup="one", fillcolor="rgba(255, 161, 90, 0.8)", line=dict(width=0.5)))

        fig2.update_layout(
            template="plotly_dark", height=450, margin=dict(l=40, r=40, t=40, b=20),
            paper_bgcolor="#1e212b", plot_bgcolor="#1e212b", hovermode="x unified",
            legend=dict(orientation="h", yanchor="bottom", y=1.02, xanchor="right", x=1)
        )
        fig2.update_yaxes(title_text="億美元 ($ 100 Millions)", gridcolor="#333344")
        st.plotly_chart(fig2, use_container_width=True)

    st.markdown("---")

    # --- 7. 圖表 3：RPF 外資避險水庫 ---
    st.subheader("🟡 海外美元避險與儲蓄水庫 (RPF)")
    if not df_rpf.empty:
        fig_rpf = go.Figure()
        fig_rpf.add_trace(go.Scatter(x=df_rpf["date"], y=df_rpf["value"], name="RPF 外國逆回購", line=dict(color="#FFA15A", width=2.5)))
        fig_rpf.update_layout(
            template="plotly_dark", height=400, margin=dict(l=40, r=40, t=40, b=20),
            paper_bgcolor="#1e212b", plot_bgcolor="#1e212b", hovermode="x unified"
        )
        fig_rpf.update_yaxes(title_text="億美元 ($ 100 Millions)", gridcolor="#333344")
        st.plotly_chart(fig_rpf, use_container_width=True)

# 兼容舊函數名稱，確保外部呼叫萬無一失
render_dashboard = render_page_2q

# 🛡️ 關鍵修復點：加上防護罩！只有獨立運行 `python page_2q.py` 才會啟動小導航；被大網站 import 時絕對不執行！
if __name__ == "__main__":
    pg = st.navigation([
        st.Page(render_page_2q, title="美聯儲總覽 (Dashboard)", icon="🏛️"),
        st.Page("page_2r.py", title="貼現窗 (WPC)", icon="🔴"),
        st.Page("page_2s.py", title="銀行融資 (BTFP)", icon="🟢"),
        st.Page("page_2t.py", title="央行互換 (SWPT)", icon="🔵"),
        st.Page("page_2u.py", title="外國逆回購 (RPF)", icon="🟡"),
    ])
    pg.run()