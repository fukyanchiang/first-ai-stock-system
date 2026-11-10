"""
Filename: page_1gann_gann08_main.py
Description: 🌊 Gann 08 江恩自然極端終端 (Gann Natural Extreme) 主界面 (全球六大多空市場萬能資產旗艦版)
- 單行極簡看盤工具列 (左側智能搜尋框 + 右側核心標的快速選單 + 刷新按鈕)
- 內建一鍵收放的「全球六大市場代碼輸入指南說明表」(st.expander 預設收起，約 28px 不佔垂直空間)
- 純數字智能免後綴解析 (打 5/700 自動轉 0005.HK/0700.HK，打 600519 自動轉 600519.SS，美/日/韓/A 股自由切換)
- 全球貨幣符號自適應 (HK$, $, ¥, ₩)
- 徹底拔除 2026-11-26 等固定日期假光柱與倒數卡片，升級為以最新實盤 K 線為基準的真實費氏時空動態推算
- 完整保留：四軌極值包絡線、紅藍雙雲、切面垂直白虛線與四發光圓點、雙層獨立 VPVR 籌碼、雙重 POC、26 週主力價量壓力趨勢圖
"""

import streamlit as st
import pandas as pd
import numpy as np
from datetime import datetime

from page_1gann_gann08_calc import (
    resolve_global_symbol_info,
    fetch_gann08_data,
    compute_gann_natural_extreme_channel,
    render_gann_natural_extreme_plotly,
    compute_weekly_flow_pressure,
    render_weekly_flow_chart
)


def render_global_guide_expander_g08():
    """
    📘 預設收起的全球六大市場代碼輸入指南 (約 28px，不佔垂直空間)
    """
    with st.expander("📖 全球跨市場股票與 ETF 代碼輸入指南 (點擊展開 / 收起)", expanded=False):
        st.markdown("""
| 市場分類 | 支援標的類別 | 快捷輸入法 (直接鍵入) | 系統標準代碼 | 代表性股票 / ETF 範例 | 計價幣別 |
| :--- | :--- | :--- | :--- | :--- | :--- |
| **🇭🇰 港股** | 藍籌 / 科技股 | `5`、`700`、`9988` | `0005.HK`、`0700.HK` | 匯豐控股、騰訊控股、阿里巴巴 | **HK$** |
| **🇭🇰 港股 ETF** | 恒指 / 科指 ETF | `2800`、`3033`、`3119` | `2800.HK`、`3033.HK` | 盈富基金、南方恒科、華夏納指 | **HK$** |
| **🇺🇸 美股** | 科技巨頭 / 權重股 | `NVDA`、`TSLA`、`AAPL` | `NVDA`、`TSLA` | 輝達、特斯拉、蘋果 | **$** |
| **🇺🇸 美股 ETF** | 大盤 / 行業指數 | `SPY`、`QQQ`、`SOXX` | `SPY`、`QQQ` | 標普500、納指100、半導體ETF | **$** |
| **🇯🇵 日股** | 跨國巨頭 | `7203.T`、`9984.T` | `7203.T`、`9984.T` | 豐田汽車、軟銀集團 | **¥ (JPY)** |
| **🇯🇵 日股 ETF** | 日經225 / 東證ETF | `1321.T`、`1306.T` | `1321.T`、`1306.T` | 野村日經225、TOPIX 東證ETF | **¥ (JPY)** |
| **🇰🇷 韓股** | 韓國綜合 (KOSPI) | `005930.KS`、`000660.KS` | `005930.KS` | 三星電子、SK 海力士 | **₩ (KRW)** |
| **🇰🇷 韓股 ETF** | 韓國 200 指數 ETF | `069500.KS` | `069500.KS` | KODEX 200 韓股大盤 ETF | **₩ (KRW)** |
| **🇨🇳 滬 A 股** | 上證主板 / 科創板 | `600519`、`601398` | `600519.SS` | 貴州茅台、工商銀行 | **¥ (RMB)** |
| **🇨🇳 滬市 ETF** | 滬深300 / 上證50 | `510300`、`510050` | `510300.SS` | 華泰滬深300、華夏上證50 | **¥ (RMB)** |
| **🇨🇳 深 A 股** | 深證主板 / 創業板 | `000858`、`300750` | `000858.SZ` | 五糧液、寧德時代 | **¥ (RMB)** |
| **🇨🇳 深市 ETF** | 創業板 / 滬深300 | `159915`、`159919` | `159915.SZ` | 易方達創業板、嘉實300 | **¥ (RMB)** |

> 💡 **智能免後綴小提示**：
> 1. 輸入 **1～5 位純數字**，系統自動補零並轉為港股 `.HK`（如輸入 `5` 自動轉為 `0005.HK`）。
> 2. 輸入 **6 位純數字**（`60/68/51` 開頭），自動補為滬市 `.SS`；（`00/30/15` 開頭），自動補為深市 `.SZ`。
> 3. 輸入 **純英文字母**（如 `NVDA`、`SPY`），自動按美股標準查詢。
> 4. 日股請在數字後加 **`.T`**，韓股請加 **`.KS`**。
        """, unsafe_allow_html=True)


def inject_gann08_css():
    st.markdown("""
    <style>
        .gann08-countdown-card {
            background: rgba(15, 23, 42, 0.85);
            border-radius: 8px;
            padding: 10px 14px;
            display: flex;
            justify-content: space-between;
            align-items: center;
            margin-bottom: 6px;
        }
        div[data-testid="stSlider"] label, div[data-testid="stSlider"] label * {
            color: #ffffff !important;
            font-weight: 600 !important;
            font-size: 12px !important;
        }
        div[data-testid="stSlider"] div[role="slider"] {
            background-color: #00e5ff !important;
            border: 2px solid #ffffff !important;
            box-shadow: 0 0 8px rgba(0, 229, 255, 0.7) !important;
        }
        div[data-testid="stCheckbox"] label, div[data-testid="stCheckbox"] label * {
            color: #ffffff !important;
            font-size: 12.5px !important;
            font-weight: 600 !important;
        }
        div[data-testid="stButton"] button {
            background-color: #161a25 !important;
            border: 1px solid #2a2e39 !important;
            color: #ffffff !important;
            border-radius: 4px !important;
            font-size: 11.5px !important;
            font-weight: 600 !important;
            height: 28px !important;
        }
        div[data-testid="stButton"] button:hover {
            border-color: #38bdf8 !important;
            background-color: #242938 !important;
        }
        div[data-testid="stSelectbox"] div[data-baseweb="select"] {
            background-color: #161a25 !important;
            border: 1px solid #2a2e39 !important;
            border-radius: 4px !important;
            min-height: 28px !important;
            height: 28px !important;
        }
        div[data-testid="stSelectbox"] div[data-baseweb="select"] * {
            background-color: transparent !important;
            color: #ffffff !important;
            font-size: 12px !important;
            font-weight: 600 !important;
        }
    </style>
    """, unsafe_allow_html=True)


def render_page_gann08():
    inject_gann08_css()

    if 'gann08_symbol' not in st.session_state:
        st.session_state['gann08_symbol'] = '2800.HK'
    if 'gann08_interval' not in st.session_state:
        st.session_state['gann08_interval'] = '1d'
    if 'gann08_period' not in st.session_state:
        st.session_state['gann08_period'] = '3y'
    if 'gann08_show_signals' not in st.session_state:
        st.session_state['gann08_show_signals'] = False
    if 'gann08_show_tw' not in st.session_state:
        st.session_state['gann08_show_tw'] = True
    if 'gann08_show_recent_vpvr' not in st.session_state:
        st.session_state['gann08_show_recent_vpvr'] = True
    if 'gann08_show_hist_vpvr' not in st.session_state:
        st.session_state['gann08_show_hist_vpvr'] = True

    active_sym, curr_sym, market_label = resolve_global_symbol_info(st.session_state['gann08_symbol'])

    st.markdown("### 🌊 江恩自然極端通道與極值雲終端 (Gann 08)")
    st.caption(f"基於江恩自然極端彈性波幅包絡帶 (Gann Natural Extreme)，當前監控：**{active_sym}** ({market_label} · 計價單位: {curr_sym})")

    # 🌟 1. 單行極簡看盤工具列 (輸入框 + 核心標的快速選單 + 刷新按鈕)
    col_search, col_select, col_refresh = st.columns([5.2, 3.8, 1.0])

    with col_search:
        raw_in = st.text_input(
            "全球標的搜尋 (Gann 08)",
            value=st.session_state['gann08_symbol'],
            placeholder="輸入代碼 (例: 0005, 700, NVDA, SPY, 1321.T, 600519)...",
            label_visibility="collapsed",
            key=f"g08_txt_input_{st.session_state['gann08_symbol']}"
        ).strip().upper()

        if raw_in:
            norm_sym, _, _ = resolve_global_symbol_info(raw_in)
            if norm_sym != st.session_state['gann08_symbol']:
                st.session_state['gann08_symbol'] = norm_sym
                st.rerun()

    with col_select:
        preset_options = [
            f"📌 常用核心標的快速選取 ({active_sym})",
            "🇭🇰 2800.HK (盈富基金)",
            "🇭🇰 0700.HK (騰訊控股)",
            "🇭🇰 0005.HK (匯豐控股)",
            "🇭🇰 3033.HK (恒生科技ETF)",
            "🇺🇸 SPY (標普500 ETF)",
            "🇺🇸 QQQ (納指100 ETF)",
            "🇺🇸 NVDA (輝達)",
            "🇺🇸 TSLA (特斯拉)",
            "🇯🇵 1321.T (日經225 ETF)",
            "🇯🇵 7203.T (豐田汽車)",
            "🇰🇷 069500.KS (KODEX200 ETF)",
            "🇰🇷 005930.KS (三星電子)",
            "🇨🇳 510300.SS (滬深300 ETF)",
            "🇨🇳 600519.SS (貴州茅台)",
            "🇨🇳 159919.SZ (嘉實300 ETF)"
        ]
        sel_val = st.selectbox(
            "快捷選擇 (Gann 08)",
            preset_options,
            index=0,
            label_visibility="collapsed",
            key=f"g08_sel_{active_sym}"
        )
        if sel_val and not sel_val.startswith("📌"):
            chosen_ticker = sel_val.split()[1]
            norm_sym, _, _ = resolve_global_symbol_info(chosen_ticker)
            if norm_sym != st.session_state['gann08_symbol']:
                st.session_state['gann08_symbol'] = norm_sym
                st.rerun()

    with col_refresh:
        if st.button("🔄", key="g08_btn_refresh_now", help="刷新實盤行情", use_container_width=True):
            st.rerun()

    # 🌟 2. 緊隨其後的收放指南表 (預設收合，約 28px)
    render_global_guide_expander_g08()

    # 3. 控制列：週期圖掣 ＋ 時間跨度 ＋ 訊號開關 ＋ 雙層籌碼獨立開關 ＋ 窗口開關
    col_tf1, col_tf2, col_sig, col_vpvr1, col_vpvr2, col_tw = st.columns([1.4, 1.8, 0.7, 0.9, 0.9, 0.8])
    with col_tf1:
        c_d, c_w, c_m = st.columns(3)
        with c_d:
            if st.button("日線", key="g08_btn_interval_d", type="primary" if st.session_state['gann08_interval'] == '1d' else "secondary", use_container_width=True):
                st.session_state['gann08_interval'] = '1d'
                st.rerun()
        with c_w:
            if st.button("週線", key="g08_btn_interval_w", type="primary" if st.session_state['gann08_interval'] == '1wk' else "secondary", use_container_width=True):
                st.session_state['gann08_interval'] = '1wk'
                st.rerun()
        with c_m:
            if st.button("月線", key="g08_btn_interval_m", type="primary" if st.session_state['gann08_interval'] == '1mo' else "secondary", use_container_width=True):
                st.session_state['gann08_interval'] = '1mo'
                st.rerun()

    with col_tf2:
        c_1y, c_2y, c_3y, c_5y = st.columns(4)
        with c_1y:
            if st.button("1Y", key="g08_btn_period_1y", type="primary" if st.session_state['gann08_period'] == '1y' else "secondary", use_container_width=True):
                st.session_state['gann08_period'] = '1y'
                st.rerun()
        with c_2y:
            if st.button("2Y", key="g08_btn_period_2y", type="primary" if st.session_state['gann08_period'] == '2y' else "secondary", use_container_width=True):
                st.session_state['gann08_period'] = '2y'
                st.rerun()
        with c_3y:
            if st.button("3Y", key="g08_btn_period_3y", type="primary" if st.session_state['gann08_period'] == '3y' else "secondary", use_container_width=True):
                st.session_state['gann08_period'] = '3y'
                st.rerun()
        with c_5y:
            if st.button("5Y", key="g08_btn_period_5y", type="primary" if st.session_state['gann08_period'] == '5y' else "secondary", use_container_width=True):
                st.session_state['gann08_period'] = '5y'
                st.rerun()

    with col_sig:
        show_signals = st.checkbox("訊號", value=st.session_state['gann08_show_signals'], key="g08_chk_signals", help="預設關閉以保持圖表極簡乾淨")
        if show_signals != st.session_state['gann08_show_signals']:
            st.session_state['gann08_show_signals'] = show_signals
            st.rerun()

    with col_vpvr1:
        is_rv = st.session_state['gann08_show_recent_vpvr']
        if st.button("📊 近期籌碼" if is_rv else "近期 (關)", key="g08_btn_rvpvr", type="primary" if is_rv else "secondary", use_container_width=True):
            st.session_state['gann08_show_recent_vpvr'] = not is_rv
            st.rerun()

    with col_vpvr2:
        is_hv = st.session_state['gann08_show_hist_vpvr']
        if st.button("🟣 歷史籌碼" if is_hv else "歷史 (關)", key="g08_btn_hvpvr", type="primary" if is_hv else "secondary", use_container_width=True):
            st.session_state['gann08_show_hist_vpvr'] = not is_hv
            st.rerun()

    with col_tw:
        is_t = st.session_state['gann08_show_tw']
        if st.button("⏳ 窗口" if is_t else "窗口 (關)", key="g08_btn_tw", type="primary" if is_t else "secondary", use_container_width=True):
            st.session_state['gann08_show_tw'] = not is_t
            st.rerun()

    active_symbol = st.session_state['gann08_symbol']
    active_interval = st.session_state['gann08_interval']
    active_period = st.session_state['gann08_period']

    # 4. 抓取實盤行情並運算 (100% 全真實數據邏輯)
    with st.spinner(f"正在加載 {active_symbol} ({market_label}) 自然極端通道數據..."):
        df_raw = fetch_gann08_data(active_symbol, period=active_period, interval=active_interval)

    if df_raw.empty or len(df_raw) < 25:
        st.warning(f"⚠️ 暫時未能取得代碼 '{active_symbol}' 的足夠歷史行情數據，請確認代碼是否正確。")
        return

    metrics, df_calc, df_future = compute_gann_natural_extreme_channel(df_raw, span=21, future_bars=15)

    # 5. K 線縮放拉桿 (預設 160 根特寫視野)
    total_bars = len(df_calc)
    min_bars = min(30, total_bars)
    zoom_key = f"g08_zoom_{active_symbol}_{active_interval}_{active_period}"
    
    if zoom_key not in st.session_state:
        st.session_state[zoom_key] = min(total_bars, 160)
    
    st.session_state[zoom_key] = min(total_bars, max(min_bars, st.session_state[zoom_key]))

    zoom_bars = st.slider(
        "K線縮放拉桿",
        min_value=min_bars,
        max_value=total_bars,
        step=5 if active_interval == '1d' else 2,
        key=zoom_key,
        help="預設鎖定 160 根特寫視野；向左滑動可放大蠟燭，向右滑動可縱覽全景"
    )

    df_display = df_calc.tail(zoom_bars).copy()

    # 6. 滿版圖表渲染
    fig_extreme = render_gann_natural_extreme_plotly(
        df_display=df_display,
        df_future=df_future,
        metrics=metrics,
        symbol_name=active_symbol,
        show_signals=st.session_state['gann08_show_signals'],
        show_timewindows=st.session_state['gann08_show_tw'],
        show_recent_vpvr=st.session_state['gann08_show_recent_vpvr'],
        show_hist_vpvr=st.session_state['gann08_show_hist_vpvr'],
        interval=active_interval,
        df_full=df_raw
    )
    
    st.plotly_chart(
        fig_extreme,
        use_container_width=True,
        config={
            'displayModeBar': True,
            'scrollZoom': True,
            'displaylogo': False,
            'modeBarButtonsToRemove': ['lasso2d', 'select2d']
        }
    )

    # 7. 主圖正下方：三大未來時間窗口 100% 動態費氏外推倒數卡片 (徹底拔除寫死日期)
    if st.session_state['gann08_show_tw']:
        last_candle_dt = pd.to_datetime(df_raw.index[-1])
        now_dt = datetime.now()

        step_days = 1 if active_interval == '1d' else (7 if active_interval == '1wk' else 30)
        t_w1 = last_candle_dt + pd.Timedelta(days=int(21 * step_days))
        t_w2 = last_candle_dt + pd.Timedelta(days=int(34 * step_days))
        t_w3 = last_candle_dt + pd.Timedelta(days=int(55 * step_days))

        target_windows = [
            {"label": "50% 躍浪峰值窗口", "center": t_w1, "desc": f"中心: {t_w1.strftime('%m/%d')}", "action": "逢高減倉", "color": "#f59e0b", "bars": 21},
            {"label": "75% 尋底過渡窗口", "center": t_w2, "desc": f"中心: {t_w2.strftime('%m/%d')}", "action": "防回踩整理", "color": "#a855f7", "bars": 34},
            {"label": "週期邊界谷底窗口", "center": t_w3, "desc": f"中心: {t_w3.strftime('%m/%d')}", "action": "逢低佈局", "color": "#10b981", "bars": 55},
        ]
        
        cards_html = []
        for tw in target_windows:
            delta_days = (tw['center'] - now_dt).days
            if active_interval == '1wk':
                unit_str = "週 (bars)"
                bar_count = max(0, delta_days // 7)
            elif active_interval == '1mo':
                unit_str = "月 (bars)"
                bar_count = max(0, delta_days // 30)
            else:
                unit_str = "日 (bars)"
                bar_count = max(0, int(delta_days * (5 / 7)))
                
            time_status = f"約 {bar_count} {unit_str} · {tw['action']}" if delta_days > 0 else f"已過期 · {tw['action']}"
            
            card_item = (
                f'<div class="gann08-countdown-card" style="border: 1px solid {tw["color"]};">'
                f'<div><div style="color:{tw["color"]}; font-weight:bold; font-size:12.5px;">{tw["label"]}</div>'
                f'<div style="color:#cbd5e1; font-size:11px; margin-top:2px;">{tw["desc"]}</div></div>'
                f'<div style="background:#1e293b; color:{tw["color"]}; font-weight:bold; padding:3px 8px; border-radius:4px; font-size:11.5px;">{time_status}</div>'
                f'</div>'
            )
            cards_html.append(card_item)

        grid_html = f'<div style="display:grid; grid-template-columns: repeat(3, 1fr); gap:10px; margin: 8px 0 16px 0;">{"".join(cards_html)}</div>'
        st.markdown(grid_html, unsafe_allow_html=True)

    # 8. 常駐大作戰區：單標的每週價量壓力趨勢 (最近 26 週淨流向 + 4W/13W 累計)
    flow_metrics, df_flow = compute_weekly_flow_pressure(df_raw, n_weeks=26)
    if not df_flow.empty:
        fig_flow = render_weekly_flow_chart(df_flow, flow_metrics, symbol_name=active_symbol)
        st.plotly_chart(
            fig_flow,
            use_container_width=True,
            config={'displayModeBar': False, 'scrollZoom': False}
        )

if __name__ == "__main__":
    render_page_gann08()