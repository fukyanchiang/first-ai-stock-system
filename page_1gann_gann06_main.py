"""
Filename: page_1gann_gann06_main.py
Description: 🎯 Gann 06 旗艦視覺主界面 (全球六大多空市場萬能資產旗艦版)
- 單行極簡看盤工具列 (左側智能搜尋框 + 右側核心標的快速選單 + 刷新按鈕)
- 內建一鍵收放的「全球六大市場代碼輸入指南說明表」(st.expander 預設收起，約 28px 不佔垂直空間)
- 純數字智能免後綴解析 (打 5/700 自動轉 0005.HK/0700.HK，打 600519 自動轉 600519.SS，美/日/韓/A 股自由切換)
- 全球貨幣符號自適應 (HK$, $, ¥, ₩)
- 徹底拔除原本寫死的「2026-11-26」等固定日期假光柱，升級為以最新實盤 K 線為基準的真實費氏時空動態推算
- 完整保留：L1~L7 平行通道延伸線、雙層獨立 VPVR (近期/歷史)、雙重 POC、18/90 EMA 態勢機與成交量副圖
"""

import streamlit as st
import pandas as pd
import numpy as np
import plotly.graph_objects as go
from datetime import datetime

from page_1gann_gann06_calc import (
    fetch_daily_asset_data,
    compute_l1_l7_structural_overlays,
    compute_minimalist_signal_engine,
    compute_gann06_dual_vpvr,
    L_LAYER_SPECS
)

# =========================================================================
# 🌐 全球跨市場資產解析器 (含純數字智能自動補全)
# =========================================================================
def resolve_global_symbol_info(symbol: str):
    sym = str(symbol).strip().upper()
    if not sym:
        sym = "2800.HK"

    # 1. 純數字智能容錯
    if sym.isdigit():
        if len(sym) <= 5:
            padded = sym.zfill(4 if len(sym) <= 4 else 5)
            return f"{padded}.HK", "HK$", "港股 / 港股 ETF"
        elif len(sym) == 6:
            if sym.startswith(('60', '68', '51', '58')):
                return f"{sym}.SS", "¥", "中國 A 股 (上證) / ETF"
            elif sym.startswith(('00', '30', '15', '16')):
                return f"{sym}.SZ", "¥", "中國 A 股 (深證) / ETF"
            else:
                return f"{sym}.SS", "¥", "中國 A 股"

    # 2. 帶後綴或英文代碼處理
    if sym.endswith(".HK"):
        code_part = sym[:-3]
        if code_part.isdigit() and len(code_part) < 4:
            code_part = code_part.zfill(4)
        return f"{code_part}.HK", "HK$", "港股 / 港股 ETF"
    elif sym.endswith(".T"):
        return sym, "¥", "日股 / 日股 ETF"
    elif sym.endswith(".KS"):
        return sym, "₩", "韓股 KOSPI / 韓股 ETF"
    elif sym.endswith(".KQ"):
        return sym, "₩", "韓股 KOSDAQ"
    elif sym.endswith(".SS"):
        return sym, "¥", "中國 A 股 (上證) / ETF"
    elif sym.endswith(".SZ"):
        return sym, "¥", "中國 A 股 (深證) / ETF"
    else:
        return sym, "$", "美股 / 美股 ETF / 全球資產"


def render_global_guide_expander_g06():
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


# =========================================================================
# 🎨 專屬暗黑金融 CSS 樣式注入
# =========================================================================
def inject_gann06_tv_css():
    st.markdown("""
    <style>
        .stApp { background-color: #0c1017 !important; color: #d1d4dc !important; }
        header[data-testid="stHeader"] { background-color: #0c1017 !important; }
        .block-container { padding-top: 1.0rem !important; }

        .gann06-title { font-size: 18px !important; font-weight: 700 !important; letter-spacing: 0.3px !important; color: #ffffff !important; line-height: 1.3 !important; }
        .gann06-subtitle { font-size: 12px !important; color: #cbd5e1 !important; margin-top: 2px !important; line-height: 1.2 !important; }
        .gann06-subtitle b { color: #ffffff !important; }

        div[data-baseweb="tab-list"] button[data-baseweb="tab"] * { color: #ffffff !important; font-size: 13.5px !important; font-weight: 600 !important; opacity: 0.95 !important; }
        div[data-baseweb="tab-list"] button[data-baseweb="tab"]:hover * { color: #38bdf8 !important; opacity: 1 !important; }
        div[data-baseweb="tab-list"] button[data-baseweb="tab"][aria-selected="true"] * { color: #ff4d6d !important; font-weight: 700 !important; opacity: 1 !important; }

        div[data-testid="stButton"] button {
            background-color: #161a25 !important; border: 1px solid #2a2e39 !important; color: #ffffff !important;
            border-radius: 4px !important; padding: 2px 8px !important; font-size: 12px !important; font-weight: 600 !important;
            height: 28px !important; box-shadow: none !important; transition: all 0.15s ease !important;
        }
        div[data-testid="stButton"] button * { color: #ffffff !important; }
        div[data-testid="stButton"] button:hover { border-color: #38bdf8 !important; color: #ffffff !important; background-color: #242938 !important; }
        div[data-testid="stButton"] button[kind="primary"] { background-color: #202634 !important; border: 1px solid #475569 !important; color: #ffffff !important; }
        div[data-testid="stButton"] button[kind="secondary"] { background-color: #11141c !important; border: 1px solid #1c212c !important; color: #ffffff !important; }

        div[class*="st-key-btn_l_L1"] button { border-left: 3.5px solid #38bdf8 !important; }
        div[class*="st-key-btn_l_L2"] button { border-left: 3.5px solid #fbbf24 !important; }
        div[class*="st-key-btn_l_L3"] button { border-left: 3.5px solid #10b981 !important; }
        div[class*="st-key-btn_l_L4"] button { border-left: 3.5px solid #3b82f6 !important; }
        div[class*="st-key-btn_l_L5"] button { border-left: 3.5px solid #f97316 !important; }
        div[class*="st-key-btn_l_L6"] button { border-left: 3.5px solid #eab308 !important; }
        div[class*="st-key-btn_l_L7"] button { border-left: 3.5px solid #cbd5e1 !important; }
        div[class*="st-key-btn_rvpvr"] button { border-left: 3.5px solid #2dd4bf !important; }
        div[class*="st-key-btn_hvpvr"] button { border-left: 3.5px solid #a855f7 !important; }
        div[class*="st-key-btn_tw"] button { border-left: 3.5px solid #f59e0b !important; }

        div[data-testid="stSelectbox"] div[data-baseweb="select"] { background-color: #161a25 !important; border: 1px solid #2a2e39 !important; border-radius: 4px !important; min-height: 28px !important; height: 28px !important; }
        div[data-testid="stSelectbox"] div[data-baseweb="select"] * { background-color: transparent !important; color: #ffffff !important; font-size: 12px !important; font-weight: 600 !important; }
        div[data-testid="stSelectbox"] svg { fill: #ffffff !important; }

        div[data-testid="stSlider"] { margin-top: -6px !important; margin-bottom: 2px !important; }
        div[data-testid="stSlider"] label, div[data-testid="stSlider"] label * { color: #ffffff !important; font-weight: 600 !important; }
        div[data-testid="stSlider"] div[role="slider"] { background-color: #00e5ff !important; border: 2px solid #ffffff !important; box-shadow: 0 0 8px rgba(0, 229, 255, 0.7) !important; }

        .gann06-guide-box { background-color: #131722 !important; border: 1px solid #2a2e39 !important; border-radius: 6px !important; padding: 8px 16px !important; margin: 6px 0 10px 0 !important; display: flex !important; flex-wrap: wrap !important; align-items: center !important; gap: 16px !important; font-size: 12px !important; }
        .gann06-card { background: #131722; border: 1px solid #2a2e39; border-radius: 6px; padding: 12px 16px; }
        .gann06-note { font-size: 11.5px; color: #cbd5e1; margin: 4px 0 12px 2px; }

        div[data-testid="stExpander"] { background-color: #131722 !important; border: 1px solid #2a2e39 !important; border-radius: 6px !important; }
        div[data-testid="stExpander"] summary { background-color: #161a25 !important; color: #ffffff !important; border-radius: 6px !important; }
        div[data-testid="stExpander"] summary * { color: #ffffff !important; font-size: 12.5px !important; font-weight: 600 !important; }
        div[data-testid="stExpander"] div[data-testid="stExpanderDetails"] { background-color: #0c1017 !important; }
    </style>
    """, unsafe_allow_html=True)


def render_page_gann06():
    inject_gann06_tv_css()

    if 'gann06_symbol' not in st.session_state:
        st.session_state['gann06_symbol'] = '2800.HK'
    if 'gann06_timeframe' not in st.session_state:
        st.session_state['gann06_timeframe'] = '1Y'
    if 'gann06_interval' not in st.session_state:
        st.session_state['gann06_interval'] = '1d'
    if 'gann06_sig_mode' not in st.session_state:
        st.session_state['gann06_sig_mode'] = '精簡文字'

    # 雙層獨立 VPVR 狀態開關初始化
    if 'gann06_show_recent_vpvr' not in st.session_state:
        st.session_state['gann06_show_recent_vpvr'] = True
    if 'gann06_show_hist_vpvr' not in st.session_state:
        st.session_state['gann06_show_hist_vpvr'] = True
    if 'gann06_show_timewindow' not in st.session_state:
        st.session_state['gann06_show_timewindow'] = True

    if 'gann06_layers_inited' not in st.session_state:
        st.session_state['gann06_chk_L1'] = False
        st.session_state['gann06_chk_L2'] = False
        st.session_state['gann06_chk_L3'] = True
        st.session_state['gann06_chk_L4'] = True
        st.session_state['gann06_chk_L5'] = True
        st.session_state['gann06_chk_L6'] = True
        st.session_state['gann06_chk_L7'] = True
        st.session_state['gann06_layers_inited'] = True

    active_symbol, curr_prefix, market_label = resolve_global_symbol_info(st.session_state['gann06_symbol'])

    # 🌟 1. 單行極簡看盤工具列 (輸入框 + 核心標的快速選單 + 刷新按鈕)
    col_search, col_select, col_refresh = st.columns([5.2, 3.8, 1.0])

    with col_search:
        raw_in = st.text_input(
            "全球標的搜尋 (Gann 06)",
            value=st.session_state['gann06_symbol'],
            placeholder="輸入代碼 (例: 0005, 700, NVDA, SPY, 1321.T, 600519)...",
            label_visibility="collapsed",
            key=f"g06_txt_input_{st.session_state['gann06_symbol']}"
        ).strip().upper()

        if raw_in:
            norm_sym, _, _ = resolve_global_symbol_info(raw_in)
            if norm_sym != st.session_state['gann06_symbol']:
                st.session_state['gann06_symbol'] = norm_sym
                st.rerun()

    with col_select:
        preset_options = [
            f"📌 常用核心標的快速選取 ({active_symbol})",
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
            "🇯🇵 9984.T (軟銀集團)",
            "🇰🇷 069500.KS (KODEX200 ETF)",
            "🇰🇷 005930.KS (三星電子)",
            "🇨🇳 510300.SS (滬深300 ETF)",
            "🇨🇳 510050.SS (上證50 ETF)",
            "🇨🇳 600519.SS (貴州茅台)",
            "🇨🇳 159919.SZ (嘉實300 ETF)",
            "🇨🇳 000858.SZ (五糧液)",
            "🇨🇳 300750.SZ (寧德時代)"
        ]
        sel_val = st.selectbox(
            "快捷選擇 (Gann 06)",
            preset_options,
            index=0,
            label_visibility="collapsed",
            key=f"g06_sel_{st.session_state['gann06_symbol']}"
        )
        if sel_val and not sel_val.startswith("📌"):
            chosen_ticker = sel_val.split()[1]
            norm_sym, _, _ = resolve_global_symbol_info(chosen_ticker)
            if norm_sym != st.session_state['gann06_symbol']:
                st.session_state['gann06_symbol'] = norm_sym
                st.rerun()

    with col_refresh:
        if st.button("🔄", key="g06_btn_refresh_now", help="刷新實盤行情", use_container_width=True):
            st.rerun()

    # 🌟 2. 緊隨其後的收放指南表 (預設收合，約 28px)
    render_global_guide_expander_g06()

    active_interval = st.session_state['gann06_interval']
    interval_label = "週線" if active_interval == "1wk" else "日線"

    with st.spinner(f"加載 {active_symbol} ({market_label}) {interval_label} 平行結構射線中..."):
        df_raw = fetch_daily_asset_data(active_symbol, period="3y", interval=active_interval)

    if df_raw.empty or len(df_raw) < 25:
        st.warning(f"⚠️ 暫時未能取得代碼 '{active_symbol}' 的 {interval_label} 數據。")
        return

    if hasattr(df_raw.index, 'tz') and df_raw.index.tz is not None:
        df_raw.index = df_raw.index.tz_localize(None)

    base_default_bars = 330 if active_interval == "1d" else 52
    if st.session_state['gann06_timeframe'] == '3Y':
        base_default_bars = min(len(df_raw), 750 if active_interval == "1d" else 156)

    max_possible_bars = min(len(df_raw), base_default_bars)
    slider_key = f"gann06_zoom_{active_symbol}_{active_interval}_{st.session_state['gann06_timeframe']}"
    if slider_key not in st.session_state:
        st.session_state[slider_key] = max_possible_bars

    df_calc = df_raw.tail(base_default_bars).copy()
    df_calc.attrs['symbol'] = active_symbol
    df_calc.attrs['interval'] = active_interval

    layers, pivot_dots, anchor_info = compute_l1_l7_structural_overlays(df_calc, future_bars=45)
    signals, trend_card, perf_card, ema_f, ema_s = compute_minimalist_signal_engine(
        df_calc, text_mode=st.session_state['gann06_sig_mode']
    )

    r1_col_left, r1_spacer, r1_col_tf, r1_col_range = st.columns([5.6, 1.4, 1.5, 1.5])
    last_bar = df_calc.iloc[-1]
    last_close = float(last_bar['Close'])
    last_date = df_calc.index[-1].strftime('%Y-%m-%d')
    o_val = float(last_bar['Open'])
    h_val = float(last_bar['High'])
    l_val = float(last_bar['Low'])
    c_val = float(last_bar['Close'])

    with r1_col_left:
        st.markdown(f"""
        <div style="margin-bottom: 2px;">
            <div class="gann06-title">{interval_label} {active_symbol} : 疊加結構</div>
            <div class="gann06-subtitle">{last_date} · 上次收盤 <b>{curr_prefix}{last_close:.2f}</b></div>
        </div>
        """, unsafe_allow_html=True)

    with r1_col_tf:
        c_d, c_w = st.columns(2)
        with c_d:
            if st.button("日線", key="g06_btn_daily", type="primary" if active_interval == '1d' else "secondary", use_container_width=True):
                st.session_state['gann06_interval'] = '1d'
                st.rerun()
        with c_w:
            if st.button("週線", key="g06_btn_weekly", type="primary" if active_interval == '1wk' else "secondary", use_container_width=True):
                st.session_state['gann06_interval'] = '1wk'
                st.rerun()

    with r1_col_range:
        c_1y, c_3y = st.columns(2)
        with c_1y:
            if st.button("1Y", key="g06_btn_1y", type="primary" if st.session_state['gann06_timeframe'] == '1Y' else "secondary", use_container_width=True):
                st.session_state['gann06_timeframe'] = '1Y'
                st.rerun()
        with c_3y:
            if st.button("3Y", key="g06_btn_3y", type="primary" if st.session_state['gann06_timeframe'] == '3Y' else "secondary", use_container_width=True):
                st.session_state['gann06_timeframe'] = '3Y'
                st.rerun()

    st.markdown("<div style='margin-top:6px;'></div>", unsafe_allow_html=True)

    # 控制列：L1~L7 + [📊 近期籌碼] + [🟣 歷史籌碼] + [⏳ 窗口] + 訊號開關
    r2_cols = st.columns([0.5, 0.5, 0.5, 0.5, 0.5, 0.5, 0.5, 0.95, 0.95, 0.9, 0.65, 1.2])

    for idx, (lk, lspec) in enumerate(L_LAYER_SPECS.items()):
        with r2_cols[idx]:
            state_key = f"gann06_chk_{lk}"
            is_active = st.session_state[state_key]
            btn_label = f"— {lk}"
            if st.button(btn_label, key=f"btn_l_{lk}", use_container_width=True, type="primary" if is_active else "secondary"):
                st.session_state[state_key] = not is_active
                st.rerun()

    with r2_cols[7]:
        is_rv = st.session_state.get('gann06_show_recent_vpvr', True)
        btn_lbl = "📊 近期籌碼" if is_rv else "近期 (關)"
        if st.button(btn_lbl, key="btn_rvpvr", use_container_width=True, type="primary" if is_rv else "secondary"):
            st.session_state['gann06_show_recent_vpvr'] = not is_rv
            st.rerun()

    with r2_cols[8]:
        is_hv = st.session_state.get('gann06_show_hist_vpvr', True)
        btn_lbl = "🟣 歷史籌碼" if is_hv else "歷史 (關)"
        if st.button(btn_lbl, key="btn_hvpvr", use_container_width=True, type="primary" if is_hv else "secondary"):
            st.session_state['gann06_show_hist_vpvr'] = not is_hv
            st.rerun()

    with r2_cols[9]:
        is_tw = st.session_state.get('gann06_show_timewindow', True)
        tw_btn_label = "⏳ 窗口" if is_tw else "窗口 (關)"
        if st.button(tw_btn_label, key="btn_tw", use_container_width=True, type="primary" if is_tw else "secondary"):
            st.session_state['gann06_show_timewindow'] = not is_tw
            st.rerun()

    with r2_cols[10]:
        st.markdown("<div style='font-size:12px; color:#ffffff; font-weight:600; line-height:28px; text-align:right;'>訊號標記</div>", unsafe_allow_html=True)
    with r2_cols[11]:
        sel_sig = st.selectbox(
            "訊號模式",
            ["精簡文字", "全部文字", "僅保留箭頭"],
            index=["精簡文字", "全部文字", "僅保留箭頭"].index(st.session_state['gann06_sig_mode']),
            key="g06_sel_sig_mode",
            label_visibility="collapsed"
        )
        if sel_sig != st.session_state['gann06_sig_mode']:
            st.session_state['gann06_sig_mode'] = sel_sig
            st.rerun()

    min_zoom = min(25, max_possible_bars)
    zoom_val = st.slider(
        "K線縮放拉桿",
        min_value=min_zoom,
        max_value=max_possible_bars,
        value=min(max_possible_bars, max(min_zoom, st.session_state[slider_key])),
        step=5 if active_interval == '1d' else 2,
        key=slider_key,
        help="拉小根數即可縮短視野，K 線隨之放大展示"
    )

    df_display = df_calc.tail(zoom_val).copy()
    display_start_dt = df_display.index[0]
    last_candle_dt = pd.to_datetime(df_display.index[-1])

    future_extension_days = 65 if active_interval == '1d' else 350
    chart_right_edge_dt = last_candle_dt + pd.Timedelta(days=future_extension_days)

    vis_p_min = float(df_display['Low'].min())
    vis_p_max = float(df_display['High'].max())
    for lk in L_LAYER_SPECS.keys():
        if st.session_state.get(f"gann06_chk_{lk}") and lk in layers:
            ly_vals = [layers[lk]['y'][i] for i, x_dt in enumerate(layers[lk]['x']) if x_dt in df_display.index]
            if ly_vals:
                vis_p_min = min(vis_p_min, float(min(ly_vals)))
                vis_p_max = max(vis_p_max, float(max(ly_vals)))

    y_pad = (vis_p_max - vis_p_min) * 0.08
    target_y_range = [vis_p_min - y_pad, vis_p_max + y_pad]

    fig = go.Figure()

    # 1. 🌟 100% 全動態未來變盤時間窗口 (依據真實最新 K 棒日期向未來費氏時空推演，杜絕寫死假日期)
    if st.session_state.get('gann06_show_timewindow', True):
        step_days = 1 if active_interval == '1d' else 7
        t_w1 = last_candle_dt + pd.Timedelta(days=int(21 * step_days))
        t_w2 = last_candle_dt + pd.Timedelta(days=int(34 * step_days))
        t_w3 = last_candle_dt + pd.Timedelta(days=int(55 * step_days))

        time_windows = [
            {
                "start": t_w1 - pd.Timedelta(days=int(2 * step_days)),
                "end": t_w1 + pd.Timedelta(days=int(2 * step_days)),
                "center": t_w1,
                "label": f"▲ 頂部峰值 {t_w1.strftime('%m/%d')}",
                "color": "rgba(245, 158, 11, 0.12)", "border": "#f59e0b"
            },
            {
                "start": t_w2 - pd.Timedelta(days=int(3 * step_days)),
                "end": t_w2 + pd.Timedelta(days=int(3 * step_days)),
                "center": t_w2,
                "label": f"⏳ 尋底過渡 {t_w2.strftime('%m/%d')}",
                "color": "rgba(168, 85, 247, 0.12)", "border": "#a855f7"
            },
            {
                "start": t_w3 - pd.Timedelta(days=int(3 * step_days)),
                "end": t_w3 + pd.Timedelta(days=int(3 * step_days)),
                "center": t_w3,
                "label": f"▼ 週期谷底 {t_w3.strftime('%m/%d')}",
                "color": "rgba(16, 185, 129, 0.12)", "border": "#10b981"
            }
        ]
        for tw in time_windows:
            w_start = tw['start']
            w_end = tw['end']
            w_center = tw['center']
            if w_end >= display_start_dt:
                fig.add_shape(
                    type="rect", x0=w_start, x1=w_end, y0=0, y1=1, yref='paper',
                    fillcolor=tw['color'], line=dict(color=tw['border'], width=1, dash="dash"),
                    layer="below"
                )
                fig.add_shape(
                    type="line", x0=w_center, x1=w_center, y0=0, y1=1, yref='paper',
                    line=dict(color=tw['border'], width=1.2, dash="dot")
                )
                fig.add_annotation(
                    x=w_center, y=0.01, yref='paper', text=f"<b>{tw['label']}</b>",
                    showarrow=False, yanchor='bottom',
                    font=dict(color="#ffffff", size=10),
                    bgcolor="#161a25", bordercolor=tw['border'], borderwidth=1
                )

    # 2. 上層主圖：主 K 線
    fig.add_trace(go.Candlestick(
        x=df_display.index,
        open=df_display['Open'], high=df_display['High'],
        low=df_display['Low'], close=df_display['Close'],
        name=active_symbol,
        increasing_line_color='#00ff88', decreasing_line_color='#ff4d6d',
        increasing_fillcolor='#00ff88', decreasing_fillcolor='#ff4d6d',
        showlegend=False, yaxis='y1'
    ))

    # 上層主圖：橘色慢線 + 青藍色快線 (18 / 90 EMA)
    fig.add_trace(go.Scatter(
        x=df_display.index, y=ema_s.tail(zoom_val),
        mode='lines', line=dict(color='#ff8800', width=2.4),
        showlegend=False, hoverinfo='skip', yaxis='y1'
    ))
    fig.add_trace(go.Scatter(
        x=df_display.index, y=ema_f.tail(zoom_val),
        mode='lines', line=dict(color='#00e5ff', width=2.0),
        showlegend=False, hoverinfo='skip', yaxis='y1'
    ))

    # 上層主圖：平行通道延伸線
    for lk, lspec in L_LAYER_SPECS.items():
        if st.session_state.get(f"gann06_chk_{lk}") and lk in layers:
            ly = layers[lk]
            valid_idx = [i for i, x_dt in enumerate(ly['x']) if x_dt >= display_start_dt]
            if valid_idx:
                sliced_x = [ly['x'][i] for i in valid_idx]
                sliced_y = [ly['y'][i] for i in valid_idx]
                fig.add_trace(go.Scatter(
                    x=sliced_x, y=sliced_y,
                    mode='lines',
                    line=dict(color=ly['color'], width=ly['width'], dash=ly['dash']),
                    name=f"— {lk}",
                    hovertext=[f"<b>{lk}</b>: {curr_prefix}{v:.2f}" for v in sliced_y],
                    hoverinfo='text', yaxis='y1'
                ))

    # 上層主圖：垂直錨定軸與圓點
    if anchor_info and anchor_info['date'] >= display_start_dt:
        anchor_dt = anchor_info['date']
        fig.add_vline(
            x=anchor_dt,
            line_dash="dash", line_color="rgba(148, 163, 184, 0.45)", line_width=1.2,
            annotation_text=f"<b>{anchor_info['date_str']}</b>",
            annotation_position="bottom",
            annotation_font=dict(color="#ffffff", size=10.5),
            annotation_bgcolor="#161a25", annotation_bordercolor="#2a2e39",
            annotation_borderwidth=1, annotation_borderpad=3
        )
        active_dots = [d for d in pivot_dots if st.session_state.get(f"gann06_chk_{d['layer']}")]
        if active_dots:
            fig.add_trace(go.Scatter(
                x=[anchor_dt] * len(active_dots),
                y=[d['price'] for d in active_dots],
                mode='markers',
                marker=dict(size=8, color=[d['color'] for d in active_dots], line=dict(width=1.5, color='#ffffff')),
                showlegend=False, hoverinfo='skip', yaxis='y1'
            ))

    # 3. 上層主圖：雙層獨立 VPVR 籌碼柱 (歷史全景 + 近期趨勢)
    recent_bars_count = 120 if active_interval == "1d" else 52
    df_recent_vpvr = df_raw.tail(min(len(df_raw), recent_bars_count))
    dual_vpvr = compute_gann06_dual_vpvr(df_raw, df_recent_vpvr, n_bins=40)

    if dual_vpvr:
        future_gap = chart_right_edge_dt - last_candle_dt
        vpvr_max_width_delta = future_gap * 0.38
        b_centers = dual_vpvr['bin_centers']
        x_base = chart_right_edge_dt

        # A. 歷史全景籌碼柱
        if st.session_state.get('gann06_show_hist_vpvr', True):
            h_buy = dual_vpvr['hist_buy']
            h_sell = dual_vpvr['hist_sell']
            m_h = dual_vpvr['max_hist_vol']

            h_brown_x, h_brown_y = [], []
            h_purple_x, h_purple_y = [], []

            for i in range(len(b_centers)):
                y_lvl = b_centers[i]
                v_b = h_buy[i]
                v_s = h_sell[i]
                if (v_b + v_s) <= 0 or m_h <= 0:
                    continue

                b_span = (vpvr_max_width_delta * 0.88) * (v_b / m_h)
                s_span = (vpvr_max_width_delta * 0.88) * (v_s / m_h)

                x_b_end = x_base - b_span
                x_s_end = x_b_end - s_span

                h_brown_x.extend([x_base, x_b_end, None])
                h_brown_y.extend([y_lvl, y_lvl, None])
                h_purple_x.extend([x_b_end, x_s_end, None])
                h_purple_y.extend([y_lvl, y_lvl, None])

            fig.add_trace(go.Scatter(
                x=h_brown_x, y=h_brown_y, mode='lines',
                line=dict(color='rgba(217, 119, 6, 0.60)', width=6.5),
                name='歷史買盤', showlegend=False, hoverinfo='skip', yaxis='y1'
            ))
            fig.add_trace(go.Scatter(
                x=h_purple_x, y=h_purple_y, mode='lines',
                line=dict(color='rgba(139, 92, 246, 0.60)', width=6.5),
                name='歷史賣盤', showlegend=False, hoverinfo='skip', yaxis='y1'
            ))

        # B. 近期趨勢籌碼柱
        if st.session_state.get('gann06_show_recent_vpvr', True):
            r_buy = dual_vpvr['recent_buy']
            r_sell = dual_vpvr['recent_sell']
            m_r = dual_vpvr['max_rec_vol']

            r_teal_x, r_teal_y = [], []
            r_pink_x, r_pink_y = [], []

            for i in range(len(b_centers)):
                y_lvl = b_centers[i]
                v_b = r_buy[i]
                v_s = r_sell[i]
                if (v_b + v_s) <= 0 or m_r <= 0:
                    continue

                b_span = (vpvr_max_width_delta * 0.96) * (v_b / m_r)
                s_span = (vpvr_max_width_delta * 0.96) * (v_s / m_r)

                r_teal_x.extend([x_base, x_b_end, None])
                r_teal_y.extend([y_lvl, y_lvl, None])
                r_pink_x.extend([x_b_end, x_s_end, None])
                r_pink_y.extend([y_lvl, y_lvl, None])

            fig.add_trace(go.Scatter(
                x=r_teal_x, y=r_teal_y, mode='lines',
                line=dict(color='rgba(45, 212, 191, 0.88)', width=6.5),
                name='近期買盤', showlegend=False, hoverinfo='skip', yaxis='y1'
            ))
            fig.add_trace(go.Scatter(
                x=r_pink_x, y=r_pink_y, mode='lines',
                line=dict(color='rgba(244, 63, 94, 0.82)', width=6.5),
                name='近期賣盤', showlegend=False, hoverinfo='skip', yaxis='y1'
            ))

        # 🟡 近期 POC (黃色虛線)
        rec_poc = dual_vpvr['recent_poc']
        if target_y_range[0] <= rec_poc <= target_y_range[1]:
            fig.add_hline(
                y=rec_poc, line_dash="dash", line_color="#f59e0b", line_width=1.5,
                annotation_text=f"<b>近期 POC {curr_prefix}{rec_poc:.2f}</b>",
                annotation_position="top right",
                annotation_font=dict(color="#ffffff", size=10, family="Arial Black"),
                annotation_bgcolor="#b45309", annotation_bordercolor="#f59e0b",
                yref='y1'
            )

        # 🟣 歷史 POC (紫色實線)
        hist_poc = dual_vpvr['hist_poc']
        if target_y_range[0] <= hist_poc <= target_y_range[1]:
            fig.add_hline(
                y=hist_poc, line_dash="solid", line_color="#a855f7", line_width=1.8,
                annotation_text=f"<b>歷史 POC {curr_prefix}{hist_poc:.2f}</b>",
                annotation_position="bottom right",
                annotation_font=dict(color="#ffffff", size=10, family="Arial Black"),
                annotation_bgcolor="#6b21a8", annotation_bordercolor="#a855f7",
                yref='y1'
            )

    # 4. 上層主圖：三色箭頭訊號
    visible_signals = [s for s in signals if pd.to_datetime(s['date']) >= display_start_dt]
    buy_sigs = [s for s in visible_signals if s['type'] == 'buy']
    reduce_sigs = [s for s in visible_signals if s['type'] == 'reduce']
    breakdown_sigs = [s for s in visible_signals if s['type'] == 'breakdown']

    if buy_sigs:
        fig.add_trace(go.Scatter(
            x=[s['date'] for s in buy_sigs], y=[s['pos_y'] for s in buy_sigs],
            mode='markers+text', marker=dict(symbol='triangle-up', size=11, color='#00ff88'),
            text=[s['label'] if s['show_text'] else "" for s in buy_sigs],
            textposition='bottom center', textfont=dict(color='#00ff88', size=11, family='Arial Black'),
            name='買入訊號', showlegend=False,
            hovertext=[f"<b>買入訊號</b>: {curr_prefix}{s['price']:.2f}" for s in buy_sigs], hoverinfo='text',
            yaxis='y1'
        ))

    if reduce_sigs:
        fig.add_trace(go.Scatter(
            x=[s['date'] for s in reduce_sigs], y=[s['pos_y'] for s in reduce_sigs],
            mode='markers+text', marker=dict(symbol='triangle-down', size=11, color='#fb923c'),
            text=[s['label'] if s['show_text'] else "" for s in reduce_sigs],
            textposition='top center', textfont=dict(color='#fb923c', size=11, family='Arial Black'),
            name='減倉', showlegend=False,
            hovertext=[f"<b>減倉</b>: {curr_prefix}{s['price']:.2f}" for s in reduce_sigs], hoverinfo='text',
            yaxis='y1'
        ))

    if breakdown_sigs:
        fig.add_trace(go.Scatter(
            x=[s['date'] for s in breakdown_sigs], y=[s['pos_y'] for s in breakdown_sigs],
            mode='markers+text', marker=dict(symbol='triangle-down', size=11, color='#ef4444'),
            text=[s['label'] if s['show_text'] else "" for s in breakdown_sigs],
            textposition='top center', textfont=dict(color='#ef4444', size=11, family='Arial Black'),
            name='破位清倉', showlegend=False,
            hovertext=[f"<b>破位清倉</b>: {curr_prefix}{s['price']:.2f}" for s in breakdown_sigs], hoverinfo='text',
            yaxis='y1'
        ))

    ref_h = float(df_display['High'].max())
    fig.add_hline(y=ref_h, line_dash="dash", line_color="rgba(148, 163, 184, 0.4)", line_width=1, annotation_text=f"{curr_prefix}{ref_h:.2f}", annotation_position="right", yref='y1')

    fig.add_hline(
        y=last_close, line_dash="dot", line_color="#ef4444", line_width=1.2,
        annotation_text=f"<b>{curr_prefix}{last_close:.2f}</b>", annotation_position="right",
        annotation_font=dict(color="#ffffff", size=11), annotation_bgcolor="#ef4444",
        yref='y1'
    )

    # 5. 下層副圖：成交量 (Volume) ＋ 20 均量線
    vol_series = df_display['Volume'] if 'Volume' in df_display else pd.Series(0, index=df_display.index)
    vol_colors = ['rgba(0, 255, 136, 0.7)' if c >= o else 'rgba(255, 77, 109, 0.7)'
                  for c, o in zip(df_display['Close'], df_display['Open'])]

    fig.add_trace(go.Bar(
        x=df_display.index, y=vol_series,
        marker_color=vol_colors,
        name='成交量', showlegend=False,
        hovertemplate='成交量: %{y:,.0f}<extra></extra>',
        yaxis='y2'
    ))

    vol_ma20 = vol_series.rolling(min(20, len(vol_series)), min_periods=1).mean()
    fig.add_trace(go.Scatter(
        x=df_display.index, y=vol_ma20,
        mode='lines', line=dict(color='#f59e0b', width=1.3),
        name='20均量', hovertemplate='20均量: %{y:,.0f}<extra></extra>',
        yaxis='y2'
    ))

    # 內嵌 OHLC 報價
    ohlc_text = f"O <span style='color:#ffffff; font-weight:bold;'>{curr_prefix}{o_val:.2f}</span>&nbsp;&nbsp;&nbsp;&nbsp;H <span style='color:#ffffff; font-weight:bold;'>{curr_prefix}{h_val:.2f}</span>&nbsp;&nbsp;&nbsp;&nbsp;L <span style='color:#ffffff; font-weight:bold;'>{curr_prefix}{l_val:.2f}</span>&nbsp;&nbsp;&nbsp;&nbsp;C <span style='color:#ffffff; font-weight:bold;'>{curr_prefix}{c_val:.2f}</span>"
    fig.add_annotation(
        xref="paper", yref="paper", x=0.005, y=0.985, text=ohlc_text, showarrow=False,
        font=dict(family="monospace", size=12, color="#ffffff"), xanchor="left", yanchor="top"
    )

    # 6. 單一 X 軸貫穿十字連貫準星線佈局 (100% 自動座標)
    fig.update_layout(
        template='plotly_dark',
        paper_bgcolor='#131722',
        plot_bgcolor='#131722',
        height=680,
        margin=dict(l=10, r=45, t=30, b=10),
        xaxis_rangeslider_visible=False,
        hovermode='x unified',
        showlegend=False,
        xaxis=dict(
            anchor='y2',
            range=[display_start_dt, chart_right_edge_dt],
            tickmode='auto',
            tickfont=dict(color='#cbd5e1', size=11),
            showgrid=True, gridcolor='rgba(42, 46, 57, 0.45)',
            showspikes=True, spikemode='across', spikesnap='cursor',
            spikedash='dash', spikecolor='#a0aec0', spikethickness=1.2
        ),
        yaxis=dict(
            domain=[0.24, 1.0],
            range=target_y_range,
            side='right', tickformat='.2f', tickfont=dict(color='#cbd5e1', size=11.5),
            showgrid=True, gridcolor='rgba(42, 46, 57, 0.45)',
            showspikes=True, spikemode='across', spikesnap='cursor',
            spikedash='dash', spikecolor='#a0aec0', spikethickness=1.2
        ),
        yaxis2=dict(
            domain=[0.0, 0.20],
            side='right', tickformat='.2s', tickfont=dict(color='#94a3b8', size=9.5),
            showgrid=True, gridcolor='rgba(42, 46, 57, 0.3)',
            showspikes=True, spikemode='across', spikesnap='cursor',
            spikedash='dash', spikecolor='#a0aec0', spikethickness=1.2
        )
    )

    st.plotly_chart(fig, use_container_width=True)

    # 底部戰術卡片
    st.markdown("""
    <div class="gann06-guide-box">
        <span style="color:#ffffff; font-weight:700; letter-spacing:0.2px;">📌 訊號法則指南：</span>
        <span style="color:#00ff88; font-weight:600;">▲ 綠色向上 ➔ 買入訊號 <span style="color:#94a3b8; font-size:11px; font-weight:normal;">(支撐抄底 / 結構收復)</span></span>
        <span style="color:#fb923c; font-weight:600;">▼ 橙色向下 ➔ 減倉 <span style="color:#94a3b8; font-size:11px; font-weight:normal;">(阻力遇阻 / 波段獲利)</span></span>
        <span style="color:#ef4444; font-weight:600;">▼ 紅色向下 ➔ 破位清倉 <span style="color:#94a3b8; font-size:11px; font-weight:normal;">(實體跌破生命線)</span></span>
    </div>
    """, unsafe_allow_html=True)

    st.markdown("""
    <div class="gann06-note">
        點擊圖層可切換顯示。精簡模式保留全部箭頭，只顯示最近 3 個訊號文字。各時間範圍均顯示通道直線延伸，K 線止於最新交易日。
    </div>
    """, unsafe_allow_html=True)

    b1, b2, b3 = st.columns(3)
    with b1:
        st.markdown(f"""
        <div class="gann06-card">
            <div style="font-size:12px; color:#ffffff; font-weight:600;">⬡ 支撐 / 阻力</div>
            <div style="display:flex; justify-content:space-between; align-items:center; margin-top:8px;">
                <span style="font-size:13px; font-weight:bold; color:{trend_card['color']}; background:rgba(239, 68, 68, 0.15); border:1px solid rgba(239, 68, 68, 0.3); padding:2px 6px; border-radius:4px;">趨勢 {trend_card['status']}</span>
                <span style="font-size:12px; color:#cbd5e1;">強度 <b>{trend_card['strength']}</b></span>
            </div>
        </div>
        """, unsafe_allow_html=True)

    with b2:
        st.markdown(f"""
        <div class="gann06-card">
            <div style="display:flex; justify-content:space-between; align-items:center;">
                <span style="font-size:12px; color:#ffffff; font-weight:600;">🎯 買入訊號</span>
                <span style="font-size:11px; font-weight:bold; color:#00ff88; background:#1e222d; padding:1px 6px; border-radius:10px; border:1px solid #2a2e39;">{perf_card['total_buy_count']}</span>
            </div>
            <div style="display:flex; justify-content:space-between; align-items:center; margin-top:8px;">
                <span style="font-size:12.5px; color:#cbd5e1;">{perf_card['latest_buy_date']}</span>
                <span style="font-size:13.5px; font-weight:bold; color:#00ff88;">{curr_prefix}{perf_card['latest_buy_price']}</span>
            </div>
        </div>
        """, unsafe_allow_html=True)

    with b3:
        st.markdown(f"""
        <div class="gann06-card">
            <div style="display:flex; justify-content:space-between; align-items:center;">
                <span style="font-size:12px; color:#ffffff; font-weight:600;">🎯 最近交易</span>
            </div>
            <div style="display:flex; justify-content:space-between; align-items:center; margin-top:8px;">
                <span style="font-size:12px; color:#cbd5e1;">{perf_card['last_trade_range']}</span>
                <span style="font-size:14px; font-weight:bold; color:#00ff88;">{perf_card['last_trade_pnl']}</span>
            </div>
        </div>
        """, unsafe_allow_html=True)

if __name__ == "__main__":
    render_page_gann06()