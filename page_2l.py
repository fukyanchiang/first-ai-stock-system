import streamlit as st
import pandas as pd
import yfinance as yf
import plotly.graph_objects as go
from plotly.subplots import make_subplots
import numpy as np

# ===================================================
# ⚙️ 數據引擎：VIX 期限結構與倒掛雷達
# ===================================================
@st.cache_data(ttl=900, show_spinner=False)  # 15分鐘快取
def fetch_vix_term_structure():
    try:
        tickers = ['^VIX', '^VIX3M', '^VIX6M', '^VVIX']
        df = yf.download(tickers, period='3y')['Close']
        
        df.rename(columns={
            '^VIX': 'VIX_Spot (1個月)', 
            '^VIX3M': 'VIX_3M (3個月)', 
            '^VIX6M': 'VIX_6M (6個月)',
            '^VVIX': 'VVIX (波動率的波動率)'
        }, inplace=True)
        
        # 🧠 核心量化指標：VIX 倒掛比率 (Spot / 3M)
        df['Panic_Ratio'] = df['VIX_Spot (1個月)'] / df['VIX_3M (3個月)']
        
        return df.dropna()
    except Exception as e:
        return pd.DataFrame()

# ===================================================
# 🔴 頁面渲染
# ===================================================
def render_page_2l():
    st.markdown("<h1 style='color:#ff3333; font-family:Arial Black;'>📉 艙房 2L：VIX 恐慌期限結構 (絕望撈底雷達)</h1>", unsafe_allow_html=True)
    st.markdown("<p style='color:#aaa;'>大鱷專用：不要在別人貪婪時買入，要在 VIX 曲線發生「倒掛」的極度恐慌時重倉出擊。這裏是華爾街最準確的鐵底探測器。</p>", unsafe_allow_html=True)
    st.markdown("<hr style='border:3px solid #ff3333; margin-bottom:20px;'>", unsafe_allow_html=True)

    col1, col2 = st.columns([8, 2])
    with col2:
        if st.button("🔄 強制刷新恐慌數據", use_container_width=True):
            fetch_vix_term_structure.clear()
            st.rerun()

    with st.spinner("📡 正在抓取芝加哥期權交易所 (CBOE) 最新波動率曲線..."):
        df = fetch_vix_term_structure()

    if not df.empty:
        # --- 頂部：最新曲線截面卡片 ---
        latest = df.iloc[-1]
        prev = df.iloc[-2]
        
        st.markdown("### ⚡ 最新 VIX 期限結構 (Term Structure)")
        
        c1, c2, c3, c4 = st.columns(4)
        c1.metric("現貨 VIX (1個月恐慌)", f"{latest['VIX_Spot (1個月)']:.2f}", f"{latest['VIX_Spot (1個月)'] - prev['VIX_Spot (1個月)']:.2f}", delta_color="inverse")
        c2.metric("遠期 VIX (3個月恐慌)", f"{latest['VIX_3M (3個月)']:.2f}", f"{latest['VIX_3M (3個月)'] - prev['VIX_3M (3個月)']:.2f}", delta_color="inverse")
        c3.metric("VVIX (大鱷防禦指標)", f"{latest['VVIX (波動率的波動率)']:.2f}", f"{latest['VVIX (波動率的波動率)'] - prev['VVIX (波動率的波動率)']:.2f}", delta_color="inverse")
        
        ratio_val = latest['Panic_Ratio']
        ratio_diff = ratio_val - prev['Panic_Ratio']
        ratio_color = "🔴 極度恐慌 (倒掛)" if ratio_val > 1 else "🟢 正常水溫"
        c4.metric(f"倒掛比率 [{ratio_color}]", f"{ratio_val:.2f}", f"{ratio_diff:.2f}", delta_color="inverse")

        st.markdown("<br>", unsafe_allow_html=True)

        # --- 中間：雙 Y 軸三維倒掛雷達圖 ---
        fig = make_subplots(
            rows=2, cols=1, 
            shared_xaxes=True, 
            vertical_spacing=0.08, 
            row_heights=[0.7, 0.3],
            specs=[[{"secondary_y": True}], [{"secondary_y": False}]]  
        )

        # 1. 左 Y 軸：3個月 VIX (綠線) & 現貨 VIX (紅線)
        fig.add_trace(go.Scatter(
            x=df.index, y=df['VIX_3M (3個月)'], 
            mode='lines', line=dict(color='#00ff88', width=2), 
            name='3個月 VIX (遠期預期)'
        ), row=1, col=1, secondary_y=False)
        
        fig.add_trace(go.Scatter(
            x=df.index, y=df['VIX_Spot (1個月)'], 
            mode='lines', line=dict(color='#ff3333', width=2), 
            name='現貨 VIX (當前恐慌)'
        ), row=1, col=1, secondary_y=False)

        # 2. 💜 右 Y 軸：VVIX 歷史折線 (紫色虛線)
        fig.add_trace(go.Scatter(
            x=df.index, y=df['VVIX (波動率的波動率)'], 
            mode='lines', line=dict(color='#ab47bc', width=1.5, dash='dot'), 
            name='VVIX (大鱷防禦 / 右 Y 軸)'
        ), row=1, col=1, secondary_y=True)

        # 🛠️ 爺爺修復點：加入 VVIX 白色警戒線 (右 Y 軸)
        fig.add_hline(
            y=110, line_dash="dot", line_color="white", line_width=1, row=1, col=1, secondary_y=True,
            annotation_text="⚠️ 升爆警戒線 (110)", annotation_font_color="white", annotation_position="bottom right"
        )
        fig.add_hline(
            y=130, line_dash="dash", line_color="white", line_width=1.5, row=1, col=1, secondary_y=True,
            annotation_text="💥 觸發爆破線 (130)", annotation_font_color="white", annotation_position="top right"
        )

        # 3. 下圖：恐慌倒掛比率 (Panic Ratio 柱狀圖)
        colors = np.where(df['Panic_Ratio'] > 1, 'rgba(255, 51, 51, 0.7)', 'rgba(0, 255, 136, 0.3)')
        fig.add_trace(go.Bar(
            x=df.index, 
            y=df['Panic_Ratio'],
            marker_color=colors,
            name='倒掛比率 (Spot/3M)'
        ), row=2, col=1)
        
        fig.add_hline(
            y=1.0, line_dash="dash", line_color="white", row=2, col=1, 
            annotation_text="💥 倒掛警戒線 (Ratio=1.0)", annotation_font_color="white"
        )

        # 佈局與色彩完全對齊深色模式
        fig.update_layout(
            title=dict(
                text="🎯 VIX 恐慌曲線倒掛 vs VVIX 大鱷防禦 (過去三年)",
                font=dict(color="white", size=20)
            ),
            font=dict(color="white"),
            template="plotly_dark", 
            height=720, 
            margin=dict(l=20, r=20, t=50, b=20),
            legend=dict(orientation="h", yanchor="bottom", y=1.02, xanchor="right", x=1, font=dict(color="white")),
            paper_bgcolor="#1e212b", 
            plot_bgcolor="#1e212b", 
            hovermode="x unified"
        )
        
        # 坐標軸標籤與顏色
        fig.update_xaxes(showgrid=True, gridwidth=1, gridcolor='#333333', tickfont=dict(color="white"))
        
        # 左 Y 軸 (VIX 點數)
        fig.update_yaxes(title_text="VIX 點數 (左軸)", row=1, col=1, secondary_y=False, showgrid=True, gridwidth=1, gridcolor='#333333', tickfont=dict(color="white"), title_font=dict(color="white"))
        # 右 Y 軸 (VVIX 點數)
        fig.update_yaxes(title_text="VVIX 點數 (右軸)", row=1, col=1, secondary_y=True, showgrid=False, tickfont=dict(color="#ab47bc"), title_font=dict(color="#ab47bc"))
        
        # 下圖 Y 軸
        fig.update_yaxes(title_text="倒掛比率", row=2, col=1, showgrid=True, gridwidth=1, gridcolor='#333333', tickfont=dict(color="white"), title_font=dict(color="white"))
        
        st.plotly_chart(fig, use_container_width=True)

    else:
        st.error("⚠️ 無法獲取 VIX 數據，請檢查網絡連線。")

    # ==========================================
    # 🧠 大指揮官戰略解讀面板
    # ==========================================
    st.markdown("""
    <div style="background-color:#2b1a1a; padding:20px; border-radius:10px; border:1px solid #ff3333; margin-top:30px;">
        <h3 style="color:#ff3333; margin-top:0;">🧠 VIX 期限結構・大鱷撈底指南</h3>
        <ul style="color:#ddd; font-size:16px; line-height:1.8;">
            <li><b>【正常市況 (Contango)】</b>：時間越長，不確定性越高。正常的 VIX 曲線是向上的（<b>現貨 VIX < 3個月 VIX</b>）。此時倒掛比率小於 1 (綠色柱)，大市通常處於慢牛或震盪升市。</li>
            <li><b>【極度恐慌 (Backwardation)】</b>：當黑天鵝爆發，投資者不計成本買近期保險，導致<b>現貨 VIX 瞬間超越 3個月 VIX</b>！此時倒掛比率大於 1，圖表下方會爆出<b>紅色血柱</b>。</li>
            <li><b>【💜 VVIX 紫色虛線對照】</b>：VVIX 顯示大鱷購買 VIX 期權保險的急切程度。若發現<b>倒掛血柱出現 + VVIX 紫色線衝破 110 (升爆警戒線) 甚至 130 (觸發爆破線)</b>，代表大鱷正在進行終極避險，那絕對是離歷史鐵底不遠的強烈信號！</li>
        </ul>
    </div>
    """, unsafe_allow_html=True)

if __name__ == "__main__":
    render_page_2l()