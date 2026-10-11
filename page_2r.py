import streamlit as st
import pandas as pd
import numpy as np
import plotly.graph_objects as go
import plotly.express as px
from plotly.subplots import make_subplots
from fed_utils import fetch_fred_series, get_latest_metrics

def render():
    st.markdown("<h1 style='color:#EF553B; font-size:36px; font-family:Arial Black;'>🔴 貼現窗 (WPC) 深度診斷與利差壓力測試</h1>", unsafe_allow_html=True)
    
    st.info("""
### 📌 戰略定位：銀行體系的「急症室」與懲罰性借貸
* **俗稱**：「銀行急症室」。
* **睇法**：平時應該接近 $0。一旦數字飆升（例如升破百億），代表有銀行在同業市場借不到錢，出現了流動性危機，被迫向美聯儲支付懲罰性高息來求救。**這是最前線的金融海嘯警報器**。

---
### 💡 爺爺的極簡比喻：貼現窗 =「銀行的急症室」兼「大耳窿」
* **平時銀行點借錢？** 銀行同銀行之間，平時會互相借錢周轉，利息好平，呢個叫「同業拆息市場」。
* **咩情況要去貼現窗？** 想像下，如果有一日全村人都覺得你間銀行有問題，冇其他銀行肯借錢畀你，但外面又有大把客排隊撳錢（擠提），你可以點算？
* **貼現窗 (WPC) 的真正面目**：你就只能夠攞住手上嘅資產（例如債券），去敲美聯儲嘅大門，求佢借錢救命。美聯儲會借，但佢會收你極度昂貴嘅「懲罰性高息」（貼現率），就好似你去撳財仔或者大耳窿咁！
* **結論點睇？** 所以，如果貼現窗（WPC）嘅借款金額（餘額）突然爆升，就代表出面一定有銀行瀕臨破產，或者整個金融村都冇曬現金（錢荒）！ 呢個數字平時必須係接近 $0。

---
### 📈 下面 4 張圖，你只需要識咁樣睇：
1. **圖 1 (睇量)**：條青色線有冇突然飆高？有飆高 = 出面火燭。
2. **圖 2 (睇價)**：綠色虛線 (利差) 有冇跌穿紅色 0 軸線？跌穿 = 利息倒掛，機制崩壞。
3. **圖 3 (睇位置)**：綠色虛線跌到去山腳左邊 (低於 20%)？代表借錢成本異常緊迫。
4. **圖 4 (睇恐慌)**：最新嘅大圓點係咪飛咗去「左上角」？係嘅話，代表銀行連貴息都唔理，發了瘋一樣去借錢，極度恐慌！
""")

    st.markdown("""
### 🚨 兩級風暴與利差壓力預警線

| 警報級別 | 觸發條件 (億美元 / bps) | 市場流動性現況 | 機構級風暴解讀 |
| :--- | :--- | :--- | :--- |
| **🟡 警告 (Warning)** | **餘額 $> 200$ 億美元** <br>或 **利差 $+1 \sim +5$ bps** | **資金流動性趨緊** | 代表中小型銀行面臨缺口，無法喺同業拆借市場借錢，被迫向美聯儲求援。 |
| **🔴 超級 (Super Alert)** | **餘額 $> 1,000$ 億美元** <br>或 **利差 $\le 0$ bps (倒掛)** | **系統性信用凍結** | 重演 2008 海嘯或 2023 SVB 倒閉潮！同業市場拒絕借貸，爆發擠提與錢荒。 |
| **⚠️ 雙重壓力警報** | **利差縮窄** 且 **餘額急升** | **恐慌性撲水** | 銀行無視懲罰性息差收窄，依然瘋狂湧入急症室借錢，顯示市場極度恐慌。 |
""")

    st.markdown("<hr style='border:2px solid #444;'>", unsafe_allow_html=True)

    with st.spinner("📡 正在抓取 FRED 全量歷史數據並進行機構級量化陣列運算..."):
        df_wpc = fetch_fred_series(["WPC"])
        df_disc = fetch_fred_series(["DPCREDIT", "INTDSRUSM193N"])
        df_effr = fetch_fred_series(["EFFR", "FEDFUNDS"])

    val_wpc, wow_wpc = get_latest_metrics(df_wpc)
    
    latest_disc, latest_effr, spread = 0.0, 0.0, 0.0
    wow_spread = 0.0
    spread_percentile_3y = 0.0
    df_rates = pd.DataFrame()
    df_3y = pd.DataFrame()

    if not df_disc.empty and not df_effr.empty:
        df_rates = pd.merge(df_disc, df_effr, on="date", how="outer", suffixes=("_disc", "_effr")).sort_values("date")
        df_rates = df_rates.ffill().dropna() 
        df_rates["spread"] = df_rates["value_disc"] - df_rates["value_effr"]
        
        if not df_rates.empty:
            latest_disc = df_rates["value_disc"].iloc[-1]
            latest_effr = df_rates["value_effr"].iloc[-1]
            spread = df_rates["spread"].iloc[-1]
            
            if len(df_rates) >= 2:
                wow_spread = spread - df_rates["spread"].iloc[-2]

            latest_date = df_rates["date"].iloc[-1]
            three_years_ago = latest_date - pd.DateOffset(years=3)
            df_3y = df_rates[df_rates["date"] >= three_years_ago].copy()
            if not df_3y.empty:
                spread_percentile_3y = (df_3y["spread"] <= spread).mean() * 100

    spread_bps = spread * 100
    wow_spread_bps = wow_spread * 100

    is_double_pressure = (wow_spread < 0) and (wow_wpc > 0) and (val_wpc > 10.0)

    if val_wpc >= 1000 or spread_bps <= 0:
        st.error(f"🔴 **超級警報發動**：當前貼現窗餘額 (${val_wpc:,.2f} 億美元) 或利差 ({spread_bps:.0f} bps) 已進入風暴級警戒區！")
    elif is_double_pressure:
        st.error(f"⚠️ **【雙重壓力警報】發動**：利差正在收窄 ({wow_spread_bps:+.0f} bps)，但銀行依然湧入貼現窗借錢 (餘額上升 {wow_wpc:+.2f} 億)！市場出現恐慌性撲水跡象！")
    elif val_wpc >= 200 or spread_bps <= 5:
        st.warning(f"🟡 **警告級別發動**：當前貼現窗餘額 (${val_wpc:,.2f} 億美元) 或利差 ({spread_bps:.0f} bps) 超出常態上限，顯示銀行資金趨緊。")
    else:
        st.success(f"🟢 **安全常態**：當前貼現窗餘額 (${val_wpc:,.2f} 億美元) 與利差 ({spread_bps:.0f} bps) 均處於安全健康區間。")

    col1, col2, col3 = st.columns(3)
    col1.metric("最新貼現窗 (WPC) 餘額", f"${val_wpc:,.2f} 億美元", f"{wow_wpc:+,.2f} 億 WoW")
    col2.metric("貼現率 vs EFFR 利差", f"{spread:.2f}% ({spread_bps:.0f} bps)", f"{wow_spread_bps:+.0f} bps WoW")
    
    pct_color = "normal" if spread_percentile_3y >= 20 else "inverse" 
    col3.metric("利差 3年歷史分位數", f"{spread_percentile_3y:.1f}%", "低於 20% 代表歷史極度偏緊", delta_color=pct_color)

    st.markdown("---")

    # 1. 貼現窗餘額歷史走勢
    st.subheader("1️⃣ 貼現窗 (WPC) 歷史餘額走勢 ($ 億美元)")
    if not df_wpc.empty:
        fig1 = px.line(df_wpc, x="date", y="value")
        fig1.update_traces(line_color="#EF553B", line_width=2.5, fill='tozeroy', fillcolor="rgba(239, 85, 59, 0.2)")
        fig1.update_layout(template="plotly_dark", height=480, margin=dict(l=40, r=40, t=30, b=20), paper_bgcolor="#1e212b", plot_bgcolor="#1e212b", hovermode="x unified", xaxis_title="", yaxis_title="億美元")
        st.plotly_chart(fig1, use_container_width=True)

    st.markdown("---")

    # 2. 貼現率 vs 同業拆息 (EFFR) 雙 Y 軸走勢與利差
    st.subheader("2️⃣ 貼現率 vs 基準利率 (EFFR) 雙 Y 軸走勢與利差 (bps)")
    if not df_rates.empty:
        fig2 = make_subplots(specs=[[{"secondary_y": True}]])
        fig2.add_trace(go.Scatter(x=df_rates["date"], y=df_rates["value_disc"], name="貼現率 (Discount Rate)", line=dict(color="#EF553B", width=2)), secondary_y=False)
        fig2.add_trace(go.Scatter(x=df_rates["date"], y=df_rates["value_effr"], name="有效聯邦基金利率 (EFFR)", line=dict(color="#636EFA", width=2)), secondary_y=False)
        fig2.add_trace(go.Scatter(x=df_rates["date"], y=df_rates["spread"] * 100, name="利差 Spread (bps)", line=dict(color="#00ff88", width=1.8, dash="dot")), secondary_y=True)
        fig2.add_hline(y=0, line_dash="solid", line_color="#ff3333", secondary_y=True, annotation_text="0 bps 倒掛危險線", annotation_position="bottom right")
        fig2.update_layout(template="plotly_dark", height=480, margin=dict(l=40, r=40, t=30, b=20), paper_bgcolor="#1e212b", plot_bgcolor="#1e212b", hovermode="x unified", legend=dict(orientation="h", yanchor="bottom", y=1.02, xanchor="right", x=1))
        fig2.update_yaxes(title_text="百分比 (%)", secondary_y=False, gridcolor="#333344")
        fig2.update_yaxes(title_text="利差 (bps)", secondary_y=True, showgrid=False)
        st.plotly_chart(fig2, use_container_width=True)

    st.markdown("---")

    # 3. 利差 3 年歷史分佈直方圖與當前位階
    st.subheader("3️⃣ 利差 3 年歷史分佈直方圖與當前位階 (Percentile Location)")
    if not df_3y.empty:
        df_3y["spread_bps"] = df_3y["spread"] * 100
        fig3 = go.Figure()
        fig3.add_trace(go.Histogram(x=df_3y["spread_bps"], name="近 3 年利差分佈", marker_color="rgba(99, 110, 250, 0.7)", nbinsx=40))
        fig3.add_vline(x=spread_bps, line_dash="dash", line_color="#00ff88", line_width=3, annotation_text=f"當前利差位置 ({spread_bps:.0f} bps | 分位數: {spread_percentile_3y:.1f}%)", annotation_position="top right")
        fig3.update_layout(template="plotly_dark", height=480, margin=dict(l=40, r=40, t=30, b=20), paper_bgcolor="#1e212b", plot_bgcolor="#1e212b", hovermode="x unified", xaxis_title="利差 (bps)", yaxis_title="歷史出現天數")
        fig3.update_xaxes(gridcolor="#333344")
        fig3.update_yaxes(gridcolor="#333344")
        st.plotly_chart(fig3, use_container_width=True)

    st.markdown("---")

    # 4. 雙重壓力四象限定位矩陣
    st.subheader("4️⃣ 雙重壓力四象限定位矩陣 (WoW 利差變動 vs WoW 餘額變動)")
    
    if not df_wpc.empty and not df_rates.empty:
        df_wpc_clean = df_wpc.rename(columns={"value": "wpc"}).sort_values("date")
        df_rates_clean = df_rates[["date", "spread"]].sort_values("date")
        df_combo = pd.merge_asof(df_wpc_clean, df_rates_clean, on="date", direction="backward")
        
        df_combo["wpc_wow"] = df_combo["wpc"].diff()
        df_combo["spread_wow_bps"] = df_combo["spread"].diff() * 100
        df_combo = df_combo.dropna()

        if not df_combo.empty:
            fig4 = go.Figure()
            fig4.add_trace(go.Scatter(x=df_combo["spread_wow_bps"], y=df_combo["wpc_wow"], mode="markers", name="歷史週數據", marker=dict(color="#444466", size=7, opacity=0.6)))
            
            latest_point = df_combo.iloc[-1]
            fig4.add_trace(go.Scatter(x=[latest_point["spread_wow_bps"]], y=[latest_point["wpc_wow"]], mode="markers+text", name="當前最新狀態", marker=dict(color="#00ff88" if not is_double_pressure else "#ff3333", size=16, line=dict(color="#ffffff", width=2)), text=["  當前位置"], textposition="top right"))

            fig4.add_vline(x=0, line_dash="solid", line_color="#888888", line_width=1)
            fig4.add_hline(y=0, line_dash="solid", line_color="#888888", line_width=1)

            x_lim = max(abs(df_combo["spread_wow_bps"].min()), abs(df_combo["spread_wow_bps"].max()), 15) * 0.6
            y_pos_lim = max(df_combo["wpc_wow"].max(), 100) * 0.5
            y_neg_lim = min(df_combo["wpc_wow"].min(), -100) * 0.5

            fig4.add_annotation(x=-x_lim, y=y_pos_lim, text="⚠️ 雙重壓力區<br>(利差縮窄 + 餘額激增)", showarrow=False, font=dict(color="#ff3366", size=13))
            fig4.add_annotation(x=x_lim, y=y_pos_lim, text="🟡 正常提領區<br>(利差擴大 + 餘額增加)", showarrow=False, font=dict(color="#ffcc00", size=12))
            fig4.add_annotation(x=-x_lim, y=y_neg_lim, text="🟢 壓力舒緩區<br>(利差縮窄 + 餘額還款)", showarrow=False, font=dict(color="#00ff88", size=12))
            fig4.add_annotation(x=x_lim, y=y_neg_lim, text="🔵 常態回穩區<br>(利差擴大 + 餘額還款)", showarrow=False, font=dict(color="#00f2ff", size=12))

            fig4.update_layout(template="plotly_dark", height=500, margin=dict(l=40, r=40, t=30, b=20), paper_bgcolor="#1e212b", plot_bgcolor="#1e212b", hovermode="closest", xaxis_title="利差週變動 WoW Spread Change (bps)", yaxis_title="貼現窗餘額週變動 WoW WPC Change (億美元)")
            fig4.update_xaxes(gridcolor="#333344")
            fig4.update_yaxes(gridcolor="#333344")
            st.plotly_chart(fig4, use_container_width=True)

if __name__ == "__main__":
    render()