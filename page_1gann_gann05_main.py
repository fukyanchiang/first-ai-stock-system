import streamlit as st
import pandas as pd
import numpy as np
import plotly.graph_objects as go
from datetime import datetime

# 導入同組的兩大核心運算引擎
from page_1gann_gann05_etf_flow_calc import (
    GANN05_SECTOR_CONFIG,
    fetch_sector_flow_data,
    compute_34_sector_leaderboard
)
from page_1gann_gann05_regression_calc import (
    fetch_weekly_data,
    compute_regression_channel_metrics,
    render_regression_plotly_chart
)

# =========================================================================
# 🎨 專屬暗黑金融 CSS 樣式注入
# =========================================================================
def inject_gann05_css():
    st.markdown("""
    <style>
        .gann05-header-box {
            background: linear-gradient(135deg, rgba(30, 41, 59, 0.7), rgba(15, 23, 42, 0.9));
            border: 1px solid #334155;
            border-radius: 10px;
            padding: 12px 18px;
            margin-bottom: 12px;
        }
        .gann05-stat-card {
            background: rgba(15, 23, 42, 0.6);
            border: 1px solid #1e293b;
            border-radius: 8px;
            padding: 8px 12px;
            text-align: center;
        }
        .gann05-flow-card {
            background: rgba(15, 23, 42, 0.75);
            border: 1px solid #1e293b;
            border-radius: 8px;
            padding: 8px 12px;
            margin-bottom: 8px;
            display: flex;
            justify-content: space-between;
            align-items: center;
        }
        .gann05-bar-bg {
            background: #1e293b;
            height: 6px;
            border-radius: 3px;
            width: 100%;
            margin-top: 4px;
            overflow: hidden;
        }
    </style>
    """, unsafe_allow_html=True)

# =========================================================================
# 🚀 核心渲染函數：render_page_gann05
# =========================================================================
def render_page_gann05():
    inject_gann05_css()

    # 1. 初始化 Session State 選擇板塊、時間窗與自訂資產搜尋
    if 'gann05_selected_sector' not in st.session_state:
        st.session_state['gann05_selected_sector'] = '金融 (XLF)'
    if 'gann05_time_window' not in st.session_state:
        st.session_state['gann05_time_window'] = '1W'
    if 'gann05_custom_ticker' not in st.session_state:
        st.session_state['gann05_custom_ticker'] = ""

    # 2. 頂部 4 大導航分頁 (01 市場總覽 / 02 板塊輪動 / 03 圖表與資金 / 04 全部 ETF)
    t1, t2, t3, t4 = st.tabs(["01 市場總覽", "02 板塊輪動", "⭐ 03 圖表與資金", "04 全部 ETF"])

    with t3:
        # =================================================================
        # 左右分欄：左邊 72% (主圖與狀態卡) + 右邊 28% (34板塊資金看板)
        # =================================================================
        chart_col, flow_col = st.columns([2.6, 1.0])

        # -------------------------------------------------------------
        # 右側：34 大板塊資金壓力看板 (Top 5 買入 / 賣出)
        # -------------------------------------------------------------
        with flow_col:
            st.markdown("""
            <div style="font-size:11px; color:#94a3b8; margin-bottom:4px;">
                各來源獨立排名 · 價量壓力並非申購資金流
            </div>
            """, unsafe_allow_html=True)

            # 時間窗切換 (最近一週 vs 近 4 週)
            win_c1, win_c2 = st.columns(2)
            with win_c1:
                if st.button("最近一週", use_container_width=True, 
                             type="primary" if st.session_state['gann05_time_window'] == '1W' else "secondary"):
                    st.session_state['gann05_time_window'] = '1W'
                    st.rerun()
            with win_c2:
                if st.button("近 4 週", use_container_width=True,
                             type="primary" if st.session_state['gann05_time_window'] == '4W' else "secondary"):
                    st.session_state['gann05_time_window'] = '4W'
                    st.rerun()

            st.markdown("""
            <div style="background:#0f172a; border:1px solid #334155; border-radius:6px; padding:4px 8px; text-align:center; font-size:12px; font-weight:700; color:#38bdf8; margin: 8px 0;">
                價量壓力 (34板塊大混戰)
            </div>
            """, unsafe_allow_html=True)

            # 抓取數據並運算
            with st.spinner("計算資金壓力中..."):
                df_all = fetch_sector_flow_data()
                top_buy, top_sell, all_df = compute_34_sector_leaderboard(
                    df_all, time_window=st.session_state['gann05_time_window']
                )

            # --- Top 5 買入壓力 (綠色) ---
            st.markdown("<div style='font-size:12.5px; font-weight:bold; color:#00ff88; margin-bottom:4px;'>📈 Top 5 買入壓力</div>", unsafe_allow_html=True)
            if not top_buy.empty:
                max_buy = top_buy['資金壓力_B'].max() if top_buy['資金壓力_B'].max() > 0 else 1.0
                for idx, row in top_buy.iterrows():
                    pct = min(100, int((row['資金壓力_B'] / max_buy) * 100))
                    is_active = (row['板塊名稱'] == st.session_state['gann05_selected_sector'] and not st.session_state['gann05_custom_ticker'])
                    border_style = "border: 1px solid #00ff88;" if is_active else "border: 1px solid #1e293b;"

                    st.markdown(f"""
                    <div style="background: rgba(15, 23, 42, 0.7); {border_style} border-radius: 6px; padding: 6px 10px; margin-bottom: 6px;">
                        <div style="display:flex; justify-content:space-between; font-size:12px;">
                            <span style="color:#f8fafc; font-weight:600;">{idx+1} {row['板塊名稱']}</span>
                            <span style="color:#00ff88; font-weight:bold;">+${row['資金壓力_B']:.1f}B</span>
                        </div>
                        <div style="font-size:10px; color:#64748b; margin-top:1px;">{row['代表標的']}</div>
                        <div class="gann05-bar-bg"><div style="background:#00ff88; width:{pct}%; height:100%;"></div></div>
                    </div>
                    """, unsafe_allow_html=True)
            else:
                st.caption("暫無買入淨流入板塊")

            # --- Top 5 賣出壓力 (紅色) ---
            st.markdown("<div style='font-size:12.5px; font-weight:bold; color:#f43f5e; margin: 10px 0 4px 0;'>📉 Top 5 賣出壓力</div>", unsafe_allow_html=True)
            if not top_sell.empty:
                max_sell = abs(top_sell['資金壓力_B'].min()) if abs(top_sell['資金壓力_B'].min()) > 0 else 1.0
                for idx, row in top_sell.iterrows():
                    pct = min(100, int((abs(row['資金壓力_B']) / max_sell) * 100))
                    is_active = (row['板塊名稱'] == st.session_state['gann05_selected_sector'] and not st.session_state['gann05_custom_ticker'])
                    border_style = "border: 1px solid #f43f5e;" if is_active else "border: 1px solid #1e293b;"

                    st.markdown(f"""
                    <div style="background: rgba(15, 23, 42, 0.7); {border_style} border-radius: 6px; padding: 6px 10px; margin-bottom: 6px;">
                        <div style="display:flex; justify-content:space-between; font-size:12px;">
                            <span style="color:#f8fafc; font-weight:600;">{idx+1} {row['板塊名稱']}</span>
                            <span style="color:#f43f5e; font-weight:bold;">-${abs(row['資金壓力_B']):.1f}B</span>
                        </div>
                        <div style="font-size:10px; color:#64748b; margin-top:1px;">{row['代表標的']}</div>
                        <div class="gann05-bar-bg"><div style="background:#f43f5e; width:{pct}%; height:100%;"></div></div>
                    </div>
                    """, unsafe_allow_html=True)
            else:
                st.caption("暫無賣出淨流出板塊")

            st.caption("部分資金流為估算，未必準確，僅供參考。")

            # 快速切換任何 34 大板塊下拉選單
            st.markdown("---")
            all_sectors = list(GANN05_SECTOR_CONFIG.keys())
            curr_idx = all_sectors.index(st.session_state['gann05_selected_sector']) if st.session_state['gann05_selected_sector'] in all_sectors else 0
            new_sec = st.selectbox("🎯 快速切換 34 板塊主圖：", all_sectors, index=curr_idx)
            if new_sec != st.session_state['gann05_selected_sector']:
                st.session_state['gann05_selected_sector'] = new_sec
                # 切換板塊時自動清空自訂資產代號，回到板塊大圖模式
                st.session_state['gann05_custom_ticker'] = ""
                st.rerun()

        # -------------------------------------------------------------
        # 左側：5 年週線回歸通道大圖表與狀態資訊
        # -------------------------------------------------------------
        with chart_col:
            # 🌟 1. 自訂資產查詢輸入列 (支援美股 / 港股 / 加密幣 / ETF 5 年回歸通道)
            col_inp, col_btn = st.columns([3.4, 1.2])
            with col_inp:
                searched_code = st.text_input(
                    "自訂資產代碼",
                    value=st.session_state['gann05_custom_ticker'],
                    placeholder="🔍 自訂輸入任何資產代碼 (例如 NVDA, TSLA, 0700.HK, 2800.HK, BTC-USD)...",
                    label_visibility="collapsed"
                ).strip().upper()
                if searched_code != st.session_state['gann05_custom_ticker']:
                    st.session_state['gann05_custom_ticker'] = searched_code
                    st.rerun()

            with col_btn:
                if st.session_state['gann05_custom_ticker']:
                    if st.button("🔄 返回板塊", use_container_width=True):
                        st.session_state['gann05_custom_ticker'] = ""
                        st.rerun()
                else:
                    st.markdown("<div style='font-size:11.5px; color:#94a3b8; padding-top:7px;'>👈 輸入代碼即畫 5 年圖</div>", unsafe_allow_html=True)

            # 判定當前繪圖目標 (若有自訂輸入則優先繪製自訂資產，否則繪製當前選中之板塊)
            active_custom = st.session_state['gann05_custom_ticker']
            if active_custom:
                sec_name = f"🌟 自訂資產: {active_custom}"
                anchor_ticker = active_custom
                badge_text = f"自訂查詢: {active_custom}"
            else:
                sec_name = st.session_state['gann05_selected_sector']
                sec_cfg = GANN05_SECTOR_CONFIG.get(sec_name, GANN05_SECTOR_CONFIG['金融 (XLF)'])
                anchor_ticker = sec_cfg['anchor']
                badge_text = f"錨定標的: {anchor_ticker}"

            # 抓取 5 年週線並運算
            with st.spinner(f"正在加載 {anchor_ticker} 5 年週線數據..."):
                df_weekly = fetch_weekly_data(anchor_ticker)
                metrics, data_calc = compute_regression_channel_metrics(df_weekly)

            if not metrics:
                st.warning(f"⚠️ 暫時未能取得代號 '{anchor_ticker}' 的 5 年歷史週線數據，請確認代碼是否正確 (例如美股 NVDA、港股 0700.HK、加密貨幣 BTC-USD)。")
            else:
                # 2. 頂部狀態列 (對齊截圖 10.34.01)
                st.markdown(f"""
                <div class="gann05-header-box">
                    <div style="display:flex; justify-content:space-between; align-items:center; flex-wrap:wrap;">
                        <div>
                            <span style="font-size:18px; font-weight:bold; color:#f8fafc;">{sec_name}</span>
                            <span style="margin-left:8px; font-size:12px; color:#38bdf8; background:#0f172a; padding:2px 8px; border-radius:4px; border:1px solid #1e293b;">
                                {badge_text}
                            </span>
                        </div>
                        <div style="font-size:22px; font-weight:bold; color:#00ff88;">
                            ${metrics['current_price']:,.2f}
                            <span style="font-size:12px; color:#94a3b8; font-weight:normal;">(5年週線中線: ${metrics['center_price']:,.2f})</span>
                        </div>
                    </div>
                    <div style="display:grid; grid-template-columns: repeat(5, 1fr); gap:8px; margin-top:10px;">
                        <div class="gann05-stat-card"><div style="font-size:10.5px; color:#94a3b8;">一週回報</div><div style="font-size:13px; font-weight:bold; color:{'#00ff88' if metrics['chg_1w']>=0 else '#ff3366'};">{metrics['chg_1w']:+.1f}%</div></div>
                        <div class="gann05-stat-card"><div style="font-size:10.5px; color:#94a3b8;">一月回報</div><div style="font-size:13px; font-weight:bold; color:{'#00ff88' if metrics['chg_1m']>=0 else '#ff3366'};">{metrics['chg_1m']:+.1f}%</div></div>
                        <div class="gann05-stat-card"><div style="font-size:10.5px; color:#94a3b8;">三月回報</div><div style="font-size:13px; font-weight:bold; color:{'#00ff88' if metrics['chg_3m']>=0 else '#ff3366'};">{metrics['chg_3m']:+.1f}%</div></div>
                        <div class="gann05-stat-card"><div style="font-size:10.5px; color:#94a3b8;">年初至今 YTD</div><div style="font-size:13px; font-weight:bold; color:{'#00ff88' if metrics['chg_ytd']>=0 else '#ff3366'};">{metrics['chg_ytd']:+.1f}%</div></div>
                        <div class="gann05-stat-card"><div style="font-size:10.5px; color:#94a3b8;">趨勢狀態</div><div style="font-size:12px; font-weight:bold; color:#f59e0b;">{metrics['trend_status']}</div></div>
                    </div>
                </div>
                """, unsafe_allow_html=True)

                # 3. 圖表控制欄 (線性回歸統計、買賣訊號開關)
                c_ctrl1, c_ctrl2 = st.columns([3, 1])
                with c_ctrl1:
                    st.markdown(f"""
                    <div style="font-size:11.5px; color:#cbd5e1; padding: 4px 0;">
                        🟣 <b>線性回歸通道</b> · ±2σ 區間 <b>{metrics['weeks_count']} 週</b> · 
                        R² <b>{metrics['r_squared']:.2f}</b> · 
                        斜率 <b>{metrics['slope_pct']:+.2f}%/週</b> · 
                        距中線 <b>{metrics['dist_center_pct']:+.1f}%</b>
                    </div>
                    """, unsafe_allow_html=True)
                with c_ctrl2:
                    show_signals = st.checkbox("買賣訊號", value=True, key="gann05_chk_sig")

                # 4. 繪製 5 年回歸大圖
                fig_reg = render_regression_plotly_chart(
                    data=data_calc, metrics=metrics, symbol_name=sec_name, show_signals=show_signals
                )
                st.plotly_chart(fig_reg, use_container_width=True)

        # =================================================================
        # 底部展開分析板塊 (對齊截圖 10.34.01 下方清單)
        # =================================================================
        with st.expander("▶ 每週資金與價量壓力 展開分析 (34 板塊總榜單)", expanded=False):
            if not all_df.empty:
                st.dataframe(
                    all_df.sort_values(by='資金壓力_B', ascending=False),
                    use_container_width=True, hide_index=True
                )

        with st.expander("▶ 板塊強弱比較 對比 SPY 相對回報", expanded=False):
            st.info("💡 該板塊目前對標 SPY 基準展開滾動 Alpha 分析，可觀察長線資金輪動節奏。")

        with st.expander("▼ 全部 ETF 34 個主題 · 搜尋及篩選", expanded=False):
            st.write(pd.DataFrame([
                {'板塊': k, '類型': v['type'], '錨定標的': v['anchor'], '代表組群': v['display_sub']} 
                for k, v in GANN05_SECTOR_CONFIG.items()
            ]))

    with t1:
        st.info("🌐 01 市場總覽：正在彙整全球跨市場宏觀流向...")
    with t2:
        st.info("🎡 02 板塊輪動：可聯動至 2m 華爾街板塊輪動星盤進行跨資產對比。")
    with t4:
        st.info("📋 04 全部 ETF：涵蓋 34 大完整板塊成分庫。")

if __name__ == "__main__":
    render_page_gann05()