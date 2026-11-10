"""
Filename: page_1gann.py
Description: 📊 艙房一_江恩：工作台主調度入口 (八分頁旗艦架構 · 全球六大多空市場旗艦版)
- 頂部 8 大艙房分拆為兩行 (4 × 2 儀表板排版)，徹底解決標籤過長橫向溢出問題
- 單行極簡看盤工具列 (左輸入框 + 右核心標的快速選單 + 刷新按鈕)
- 內建一鍵收放的「全球六大市場代碼輸入指南說明表」(預設收合，不佔垂直空間)
- 純數字智能容錯 (打 5/700 自動轉 0005.HK/0700.HK，打 600519 自動轉 600519.SS)
- 全局安全初始化 df_raw，確保 Gann 01 ~ Gann 08 全線穩定
"""

import streamlit as st
import pandas as pd
import numpy as np
import yfinance as yf
import plotly.graph_objects as go
from plotly.subplots import SubplotRef
import importlib

# 兼容導入 Gann 01 運算模組
try:
    import page_1gann_gann01_fan_calc as gann_engine
    importlib.reload(gann_engine)
except ImportError:
    try:
        import page1gann_gann01_fan_calc as gann_engine
        importlib.reload(gann_engine)
    except ImportError:
        gann_engine = None

try:
    import page1gann_pattern_calc as pattern_engine
    importlib.reload(pattern_engine)
except ImportError:
    pattern_engine = None

try:
    import page1_sidebar_diag_calc as diag_engine
    importlib.reload(diag_engine)
except ImportError:
    diag_engine = None

try:
    import page_1gann_gann02_cycle_calc as cycle_engine
    importlib.reload(cycle_engine)
except ImportError:
    cycle_engine = None

try:
    import page_1gann_gann02_extreme_calc as ext_engine
    importlib.reload(ext_engine)
except ImportError:
    ext_engine = None

try:
    import page_1gann_gann02_main as gann02_engine
    importlib.reload(gann02_engine)
except ImportError:
    gann02_engine = None

try:
    import page_1gann_gann03_main as gann03_engine
    importlib.reload(gann03_engine)
except ImportError:
    gann03_engine = None

try:
    import page_1gann_gann04_main as gann04_engine
    importlib.reload(gann04_engine)
except ImportError:
    gann04_engine = None

try:
    import page_1gann_gann05_main as gann05_engine
    importlib.reload(gann05_engine)
except ImportError:
    gann05_engine = None

try:
    import page_1gann_gann06_main as gann06_engine
    importlib.reload(gann06_engine)
except ImportError:
    gann06_engine = None

try:
    import page_1gann_gann07_main as gann07_engine
    importlib.reload(gann07_engine)
except ImportError:
    gann07_engine = None

try:
    import page_1gann_gann08_main as gann08_engine
    importlib.reload(gann08_engine)
except ImportError:
    gann08_engine = None

try:
    import component_gann_harmonic_arcs as harmonic_comp
    importlib.reload(harmonic_comp)
except ImportError:
    harmonic_comp = None

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


@st.cache_data(ttl=1800, show_spinner=False)
def fetch_gann01_dynamic_data(ticker_symbol: str, period: str = "2y", interval: str = "1d"):
    try:
        clean_symbol, _, _ = resolve_global_symbol_info(ticker_symbol)
        t = yf.Ticker(clean_symbol)
        df = t.history(period=period, interval=interval)
        if df.empty or len(df) < 15:
            df_fallback = t.history(period="1y", interval="1d")
            if not df_fallback.empty:
                df = df_fallback
        if hasattr(df.index, 'tz') and df.index.tz is not None:
            df.index = df.index.tz_localize(None)
        return df.dropna(subset=['Close'])
    except Exception:
        return pd.DataFrame()


def inject_gann_workspace_white_controls_css():
    st.markdown("""
    <style>
        /* 導航中心深黑字 */
        div[data-testid="stRadio"]:not(div[data-baseweb="tab-panel"] div[data-testid="stRadio"]) label,
        div[data-testid="stRadio"]:not(div[data-baseweb="tab-panel"] div[data-testid="stRadio"]) label *,
        div[data-testid="stRadio"]:not(div[data-baseweb="tab-panel"] div[data-testid="stRadio"]) p,
        div[role="radiogroup"]:not(div[data-baseweb="tab-panel"] div[role="radiogroup"]) label,
        div[role="radiogroup"]:not(div[data-baseweb="tab-panel"] div[role="radiogroup"]) label * {
            color: #1e293b !important;
            font-size: 13.5px !important;
            font-weight: 600 !important;
            opacity: 1 !important;
        }

        div.stMarkdown:not(div[data-baseweb="tab-panel"] div.stMarkdown) p,
        div.stMarkdown:not(div[data-baseweb="tab-panel"] div.stMarkdown) span {
            color: #1e293b !important;
        }

        /* =========================================================================
           🌟 頂部 8 大 Gann 分頁標籤：強制分為 2 行 × 4 列排列
           ========================================================================= */
        div[data-baseweb="tab-list"] {
            background-color: transparent !important;
            gap: 6px !important;
            flex-wrap: wrap !important;
            display: flex !important;
            padding: 4px 0 10px 0 !important;
        }
        div[data-baseweb="tab-list"] button[data-baseweb="tab"] {
            background-color: #131722 !important;
            border: 1px solid #2a2e39 !important;
            border-radius: 6px !important;
            padding: 7px 10px !important;
            flex: 1 1 calc(25% - 8px) !important;
            min-width: 170px !important;
            justify-content: center !important;
            margin-bottom: 2px !important;
            transition: all 0.15s ease !important;
        }
        div[data-baseweb="tab-list"] button[data-baseweb="tab"] * {
            color: #cbd5e1 !important;
            font-size: 12.5px !important;
            font-weight: 600 !important;
            opacity: 0.95 !important;
        }
        div[data-baseweb="tab-list"] button[data-baseweb="tab"]:hover {
            border-color: #38bdf8 !important;
            background-color: #1e293b !important;
        }
        div[data-baseweb="tab-list"] button[data-baseweb="tab"]:hover * {
            color: #38bdf8 !important;
        }
        div[data-baseweb="tab-list"] button[data-baseweb="tab"][aria-selected="true"] {
            background-color: rgba(255, 77, 109, 0.16) !important;
            border: 1px solid #ff4d6d !important;
        }
        div[data-baseweb="tab-list"] button[data-baseweb="tab"][aria-selected="true"] * {
            color: #ff4d6d !important;
            font-weight: 700 !important;
        }
        div[data-baseweb="tab-highlight"] {
            display: none !important;
        }

        /* 艙房內部面板文字純白 */
        div[data-baseweb="tab-panel"] div[data-testid="stRadio"] label,
        div[data-baseweb="tab-panel"] div[data-testid="stRadio"] label *,
        div[data-baseweb="tab-panel"] div[data-testid="stRadio"] p,
        div[data-baseweb="tab-panel"] div[role="radiogroup"] label * {
            color: #ffffff !important;
            font-size: 13px !important;
            font-weight: 600 !important;
            opacity: 1 !important;
        }

        div[data-baseweb="tab-panel"] div[data-testid="stCheckbox"] label,
        div[data-baseweb="tab-panel"] div[data-testid="stCheckbox"] label *,
        div[data-baseweb="tab-panel"] div[data-testid="stCheckbox"] p {
            color: #ffffff !important;
            font-size: 13px !important;
            font-weight: 500 !important;
            opacity: 1 !important;
        }

        div[data-baseweb="tab-panel"] div[data-testid="stExpander"] {
            background-color: #131722 !important;
            border: 1px solid #2a2e39 !important;
            border-radius: 6px !important;
        }
        div[data-baseweb="tab-panel"] div[data-testid="stExpander"] summary {
            background-color: #161a25 !important;
            color: #ffffff !important;
            border-radius: 6px !important;
        }
        div[data-baseweb="tab-panel"] div[data-testid="stExpander"] summary * {
            color: #ffffff !important;
            font-size: 12.5px !important;
            font-weight: 600 !important;
        }
        div[data-baseweb="tab-panel"] div[data-testid="stExpander"] div[data-testid="stExpanderDetails"] {
            background-color: #0c1017 !important;
        }

        div[data-baseweb="tab-panel"] div[data-testid="stButton"] button,
        div[data-baseweb="tab-panel"] div[data-testid="stButton"] button * {
            color: #ffffff !important;
            font-weight: 600 !important;
        }
        div[data-baseweb="tab-panel"] div[data-testid="stSlider"] label,
        div[data-baseweb="tab-panel"] div[data-testid="stSlider"] label * {
            color: #ffffff !important;
            font-weight: 600 !important;
        }
    </style>
    """, unsafe_allow_html=True)


def build_grid_ref(num_rows):
    grid = []
    for r in range(1, num_rows + 1):
        y_name = 'y' if r == 1 else f'y{r}'
        ref = SubplotRef(
            subplot_type='xy',
            layout_keys=('xaxis', f'yaxis{r}' if r > 1 else 'yaxis'),
            trace_kwargs={'xaxis': 'x', 'yaxis': y_name}
        )
        grid.append([(ref,)])
    return grid


def render_global_guide_expander():
    """
    📘 可收放的全球六大市場代碼輸入指南 (預設收起，不佔螢幕空間)
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


def render_gann_taichi_tab(df: pd.DataFrame, period: str = "1y", market_type: str = "美股", symbol: str = "NVDA"):
    inject_gann_workspace_white_controls_css()

    # 頂層全域安全初始化 df_raw (防護 Gann 02~08 不崩潰)
    if df is not None and not df.empty:
        df_raw = df.copy()
        if hasattr(df_raw.index, 'tz') and df_raw.index.tz is not None:
            df_raw.index = df_raw.index.tz_localize(None)
        else:
            df_raw.index = pd.to_datetime(df_raw.index)
    else:
        try:
            df_raw = yf.Ticker(symbol if symbol else "NVDA").history(period="1y", interval="1d")
            if hasattr(df_raw.index, 'tz') and df_raw.index.tz is not None:
                df_raw.index = df_raw.index.tz_localize(None)
        except Exception:
            df_raw = pd.DataFrame()

    if 'gann01_symbol' not in st.session_state:
        st.session_state['gann01_symbol'] = symbol if symbol else '2800.HK'

    # 頂部 8 大旗艦分頁 (配合 CSS 自動排成 2 行 × 4 列)
    tab_gann01, tab_gann02, tab_gann03, tab_gann04, tab_gann05, tab_gann06, tab_gann07, tab_gann08 = st.tabs([
        "🌌 太極時空幾何 (Gann 01)",
        "📊 自然極限動能 (Gann 02)",
        "📈 量化通道結構 (Gann 03)",
        "🎯 江恩策略 Y (Gann 04)",
        "🌐 宏觀板塊資金 (Gann 05)",
        "📐 L1–L7 延伸訊號 (Gann 06)",
        "🪐 曲線趨勢籌碼 (Gann 07)",
        "🌊 自然極端極值 (Gann 08)"
    ])

    # ==========================================
    # 分頁 1 (Gann 01)
    # ==========================================
    with tab_gann01:
        active_g01_sym, curr_sym, market_label = resolve_global_symbol_info(st.session_state['gann01_symbol'])

        # 🌟 1. 單行極簡看盤工具列
        col_search, col_select, col_refresh = st.columns([5.2, 3.8, 1.0])

        with col_search:
            raw_in = st.text_input(
                "全球標的搜尋",
                value=st.session_state['gann01_symbol'],
                placeholder="輸入代碼 (例: 0005, 700, NVDA, SPY, 1321.T, 600519)...",
                label_visibility="collapsed",
                key=f"g01_txt_input_{st.session_state['gann01_symbol']}"
            ).strip().upper()

            if raw_in:
                norm_sym, _, _ = resolve_global_symbol_info(raw_in)
                if norm_sym != st.session_state['gann01_symbol']:
                    st.session_state['gann01_symbol'] = norm_sym
                    st.rerun()

        with col_select:
            preset_options = [
                f"📌 常用核心標的快速選取 ({active_g01_sym})",
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
                "快捷選擇",
                preset_options,
                index=0,
                label_visibility="collapsed",
                key=f"g01_sel_{st.session_state['gann01_symbol']}"
            )
            if sel_val and not sel_val.startswith("📌"):
                chosen_ticker = sel_val.split()[1]
                norm_sym, _, _ = resolve_global_symbol_info(chosen_ticker)
                if norm_sym != st.session_state['gann01_symbol']:
                    st.session_state['gann01_symbol'] = norm_sym
                    st.rerun()

        with col_refresh:
            if st.button("🔄", key="g01_btn_refresh_now", help="刷新實盤行情", use_container_width=True):
                st.rerun()

        # 🌟 2. 緊隨其後的一鍵收放指南表 (預設收起，不佔高度)
        render_global_guide_expander()

        # 加載實盤數據
        current_g01_sym = st.session_state['gann01_symbol']
        with st.spinner(f"正在加載 {current_g01_sym} ({market_label}) 實盤行情數據..."):
            df_g01_data = fetch_gann01_dynamic_data(current_g01_sym, period="3y", interval="1d")

        if df_g01_data.empty or len(df_g01_data) < 15:
            df_g01_data = df_raw.copy()

        if df_g01_data.empty:
            st.warning(f"⚠️ 暫時未能取得代碼 '{current_g01_sym}' 的歷史行情數據，請確認代碼是否正確。")
            return

        c_tf, c_scope, _ = st.columns([1.8, 3.2, 5.0])
        with c_tf:
            timeframe = st.radio("K線級別", ["📅 日線", "📆 週線"], index=0, horizontal=True, label_visibility="collapsed", key="gann01_tf")
        with c_scope:
            view_scope = st.radio("顯示範圍", ["⚡ 近 3 個月 (特寫放大)", "📊 近 6 個月", "🌐 1 年全景"], index=1, horizontal=True, label_visibility="collapsed", key="gann01_scope")

        # 週線切換邏輯
        if "週線" in timeframe:
            try:
                clean_sym, _, _ = resolve_global_symbol_info(current_g01_sym)
                df_w = yf.Ticker(clean_sym).history(period="3y", interval="1wk")
                if df_w is not None and not df_w.empty and len(df_w) >= 15:
                    df_active = df_w.copy()
                    df_active.index = pd.to_datetime(df_active.index).tz_localize(None)
                else:
                    raise ValueError("週線不足")
            except Exception:
                df_active = df_g01_data.resample('W-FRI').agg({
                    'Open': 'first', 'High': 'max', 'Low': 'min', 'Close': 'last', 'Volume': 'sum'
                }).dropna()
        else:
            df_active = df_g01_data.copy()

        is_weekly = "週線" in timeframe
        if "3 個月" in view_scope:
            target_bars = 14 if is_weekly else 63
            df_chart = df_active.tail(target_bars).copy()
        elif "6 個月" in view_scope:
            target_bars = 26 if is_weekly else 126
            df_chart = df_active.tail(target_bars).copy()
        else:
            df_chart = df_active.copy()

        if st.session_state.get("trigger_reset_gann01", False):
            st.session_state["gann01_r_period"] = 47
            st.session_state["gann01_extend"] = 35
            st.session_state["gann01_anchor_mode"] = "經典前浪推演 (弧帶貫穿當前走勢)"
            st.session_state["gann01_fibo"] = True
            st.session_state["gann01_mirror"] = True
            st.session_state["gann01_ext"] = False
            st.session_state["gann01_channels"] = True
            st.session_state["gann01_patterns"] = True
            st.session_state["gann01_fan"] = True
            st.session_state["gann01_vol"] = True
            st.session_state["gann01_cycle"] = True
            st.session_state["gann01_sl"] = True
            st.session_state["gann01_harmonic"] = True
            st.session_state["trigger_reset_gann01"] = False

        with st.expander("⚙️ 太極幾何、黃金分割與形態識別控制 (Geometry & Pattern Controls)", expanded=True):
            c_mode, c_a, c_b, c_rst = st.columns([2.5, 1.8, 1.8, 1.4])
            with c_mode:
                anchor_mode = st.selectbox("🎯 幾何錨點推演模式", ["經典前浪推演 (弧帶貫穿當前走勢)", "手動自選 A-B 錨點", "即時尾浪推演"], index=0, key="gann01_anchor_mode")

            manual_a, manual_b = None, None
            date_options = [d.strftime("%Y-%m-%d") for d in df_chart.index]
            if anchor_mode == "手動自選 A-B 錨點":
                with c_a:
                    sel_a = st.selectbox("錨點 A 日期", date_options, index=max(0, len(date_options) - 50), key="gann01_sel_a")
                    manual_a = pd.to_datetime(sel_a)
                with c_b:
                    sel_b = st.selectbox("錨點 B 日期", date_options, index=max(0, len(date_options) - 25), key="gann01_sel_b")
                    manual_b = pd.to_datetime(sel_b)

            with c_rst:
                st.write("")
                if st.button("🔄 回復預設", key="btn_reset_defaults", help="一鍵將所有指標與 R 週期復位"):
                    st.session_state["trigger_reset_gann01"] = True
                    st.rerun()

            c1, c2, c3, c4 = st.columns([2.1, 2.2, 2.5, 3.2])
            with c1:
                show_fibo = st.checkbox("🔥 Auto Fibonacci (黃金分割)", value=st.session_state.get("gann01_fibo", True), key="gann01_fibo")
                show_mirror = st.checkbox("✓ 太極鏡位 (雙藍雙黃弧帶)", value=st.session_state.get("gann01_mirror", True), key="gann01_mirror")
                show_fibo_ext = st.checkbox("🎯 延伸目標 (127.2% / 161.8%)", value=st.session_state.get("gann01_ext", False), key="gann01_ext")
            with c2:
                show_channels = st.checkbox("✓ 自動軌線與支持線 (DA1)", value=st.session_state.get("gann01_channels", True), key="gann01_channels")
                show_patterns = st.checkbox("📐 經典與諧波形態 (三角形/蝴蝶/ABCD)", value=st.session_state.get("gann01_patterns", True), key="gann01_patterns")
                show_gann_fan = st.checkbox("✓ Lung's GANN FAN (角度線)", value=st.session_state.get("gann01_fan", True), key="gann01_fan")
            with c3:
                show_volume = st.checkbox("📊 成交量 (Volume)", value=st.session_state.get("gann01_vol", True), key="gann01_vol")
                show_cycle = st.checkbox("✓ Time Cycle (正弦波)", value=st.session_state.get("gann01_cycle", True), key="gann01_cycle")
                show_sl_angle = st.checkbox("✓ SL Angle (動能角度)", value=st.session_state.get("gann01_sl", True), key="gann01_sl")
            with c4:
                show_harmonic = st.checkbox("⏳ 諧波時間弧 (推算暗區+倒數)", value=st.session_state.get("gann01_harmonic", True), key="gann01_harmonic")
                r_period = st.slider("基準週期 R (K線根數)", min_value=10, max_value=120, value=st.session_state.get("gann01_r_period", 47), step=1, key="gann01_r_period")
                extend_bars = st.slider("未來時空推移 (根數)", min_value=15, max_value=80, value=st.session_state.get("gann01_extend", 35), step=5, key="gann01_extend")

        future_span_days = 85
        gann_data = None
        if gann_engine is not None and hasattr(gann_engine, "compute_gann_fan_and_arcs"):
            try:
                gann_data = gann_engine.compute_gann_fan_and_arcs(
                    df=df_chart, extend_bars=extend_bars, show_fan=show_gann_fan,
                    show_mirror=show_mirror, show_channels=show_channels,
                    show_fibo=show_fibo, show_fibo_ext=show_fibo_ext,
                    anchor_mode=anchor_mode, manual_a_date=manual_a, manual_b_date=manual_b,
                    curr_sym=curr_sym
                )
            except Exception as e:
                st.error(f"太極運算錯誤: {e}")

        pattern_data = None
        if show_patterns and pattern_engine is not None and hasattr(pattern_engine, "detect_chart_patterns"):
            try:
                pattern_data = pattern_engine.detect_chart_patterns(df_chart)
            except Exception as e:
                st.error(f"形態運算錯誤: {e}")

        cycle_data = None
        sl_data = None
        if cycle_engine is not None:
            if show_cycle and hasattr(cycle_engine, "compute_time_cycle"):
                cycle_data = cycle_engine.compute_time_cycle(df_chart, future_days=future_span_days)
            if show_sl_angle and hasattr(cycle_engine, "compute_sl_angle"):
                sl_data = cycle_engine.compute_sl_angle(df_chart)

        vpvr_data = None
        if ext_engine and hasattr(ext_engine, "compute_vpvr_and_poc"):
            vpvr_data = ext_engine.compute_vpvr_and_poc(df_chart)

        harmonic_data = None
        if show_harmonic and harmonic_comp is not None and hasattr(harmonic_comp, "compute_harmonic_arcs_data"):
            try:
                harmonic_data = harmonic_comp.compute_harmonic_arcs_data(
                    df=df_chart, r_period=r_period, manual_a1_date=manual_a, manual_a2_date=manual_b
                )
            except Exception as e:
                st.error(f"諧波時間弧運算錯誤: {e}")

        if gann_engine and gann_data and hasattr(gann_engine, "render_gann_banner"):
            gann_engine.render_gann_banner(gann_data)

        layers = []
        if show_harmonic and harmonic_data:
            layers.append(('harmonic', 0.18))
        if show_sl_angle and sl_data:
            layers.append(('sl_angle', 0.11))
        if show_cycle and cycle_data:
            layers.append(('cycle', 0.13))
        if show_volume:
            layers.append(('volume', 0.11))

        current_bottom = 0.0
        gap = 0.02
        y_axes_config = {}
        axes_map = {}
        y_idx = 2

        spike_common = dict(
            showspikes=True, spikemode='across+toaxis', spikesnap='cursor',
            spikedash='dash', spikecolor='rgba(255, 255, 255, 0.85)', spikethickness=1.2
        )

        for name, height in layers:
            domain = [round(current_bottom, 3), round(current_bottom + height, 3)]
            axes_map[name] = f"y{y_idx}"
            y_axes_config[f'yaxis{y_idx}'] = dict(
                domain=domain, anchor='x', side='right',
                showgrid=True, gridcolor='rgba(48, 54, 61, 0.35)', color='#8b949e', **spike_common
            )
            if name == 'cycle':
                y_axes_config[f'yaxis{y_idx}']['range'] = [-120, 120]
            elif name == 'sl_angle':
                y_axes_config[f'yaxis{y_idx}']['range'] = [-95, 95]
            elif name == 'harmonic':
                y_axes_config[f'yaxis{y_idx}']['range'] = [-5, 125]
                y_axes_config[f'yaxis{y_idx}']['gridcolor'] = 'rgba(48, 54, 61, 0.25)'

            current_bottom += height + gap
            y_idx += 1

        price_domain = [round(current_bottom, 3), 1.0]
        axes_map['price'] = 'y'
        y_axes_config['yaxis'] = dict(
            domain=price_domain, anchor='x', side='right',
            showgrid=True, gridcolor='rgba(48, 54, 61, 0.35)', color='#8b949e', **spike_common
        )

        bottom_ax = axes_map[layers[0][0]] if layers else 'y'
        chart_end_base = df_chart.index[-1] + pd.Timedelta(days=future_span_days)
        chart_end_final = harmonic_data['chart_end_date'] if (show_harmonic and harmonic_data) else chart_end_base

        y_axes_config['xaxis'] = dict(
            anchor=bottom_ax,
            range=[df_chart.index[0], chart_end_final],
            showgrid=True, gridcolor='rgba(48, 54, 61, 0.35)', color='#8b949e',
            rangeslider=dict(visible=False), **spike_common
        )

        total_rows = 1 + len(layers)
        chart_total_height = max(750, 520 + len(layers) * 115)
        fig = go.Figure()
        fig._grid_ref = build_grid_ref(total_rows)

        fig.add_trace(go.Candlestick(
            x=df_chart.index,
            open=df_chart['Open'], high=df_chart['High'],
            low=df_chart['Low'], close=df_chart['Close'],
            name=f'{current_g01_sym} K線',
            increasing_line_color='#00e676', decreasing_line_color='#ff5252',
            increasing_fillcolor='#00e676', decreasing_fillcolor='#ff5252',
            yaxis=axes_map['price'], showlegend=False
        ), row=1, col=1)

        if gann_engine and gann_data and hasattr(gann_engine, "render_gann_fan_traces"):
            gann_engine.render_gann_fan_traces(fig, gann_data)

        if show_patterns and pattern_engine and pattern_data and hasattr(pattern_engine, "render_pattern_traces_and_hud"):
            pattern_engine.render_pattern_traces_and_hud(fig, pattern_data)

        if show_harmonic and harmonic_data and harmonic_comp:
            harmonic_comp.inject_future_projection_zone(fig, harmonic_data, yaxis_name=axes_map['price'])

        if show_volume:
            vol_colors = ['#00e676' if c >= o else '#ff5252' for c, o in zip(df_chart['Close'], df_chart['Open'])]
            fig.add_trace(go.Bar(
                x=df_chart.index, y=df_chart['Volume'],
                marker_color=vol_colors, name='成交量',
                showlegend=False, opacity=0.75, yaxis=axes_map['volume']
            ))

        if show_cycle and cycle_data:
            c_yax = axes_map['cycle']
            fig.add_trace(go.Scatter(x=cycle_data['interp_dates'], y=cycle_data['pos_cycle'], mode='lines', line=dict(color='#38bdf8', width=2.4), name='Cycle Peak Phase', yaxis=c_yax, showlegend=False))
            fig.add_trace(go.Scatter(x=cycle_data['interp_dates'], y=cycle_data['neg_cycle'], mode='lines', line=dict(color='#facc15', width=2.4), name='Cycle Trough Phase', yaxis=c_yax, showlegend=False))

            for y_r, c_r, d_r in [(100, "rgba(244, 63, 94, 0.4)", "dash"), (0, "rgba(148, 163, 184, 0.3)", "solid"), (-100, "rgba(250, 204, 21, 0.4)", "dash")]:
                fig.add_shape(type="line", xref="paper", yref=c_yax, x0=0, x1=1, y0=y_r, y1=y_r, line=dict(color=c_r, width=1, dash=d_r))

            for pk_date, pk_val in cycle_data['peaks']:
                fig.add_trace(go.Scatter(x=[pk_date], y=[pk_val], mode='markers', marker=dict(color='#38bdf8', size=7, line=dict(color='#ffffff', width=1.5)), yaxis=c_yax, showlegend=False, hoverinfo='skip'))
                fig.add_annotation(x=pk_date, y=pk_val, xref="x", yref=c_yax, text="<b>PEAK</b>", font=dict(color="#38bdf8", size=9, family="Arial Black"), showarrow=False, yshift=14, xanchor="center")

            for tg_date, tg_val in cycle_data['troughs']:
                fig.add_trace(go.Scatter(x=[tg_date], y=[tg_val], mode='markers', marker=dict(color='#facc15', size=7, line=dict(color='#ffffff', width=1.5)), yaxis=c_yax, showlegend=False, hoverinfo='skip'))
                fig.add_annotation(x=tg_date, y=tg_val, xref="x", yref=c_yax, text="<b>TROUGH</b>", bgcolor="#78350f", bordercolor="#f59e0b", borderwidth=1, borderpad=2, font=dict(color="#fde68a", size=9, family="Arial Black"), showarrow=False, yshift=-16, xanchor="center")

            fig.add_annotation(xref="x domain", yref=c_yax, x=0.995, y=100, text="<b>PEAK ZONE</b>", bgcolor="#0284c7", font=dict(color="#ffffff", size=9), showarrow=False, xanchor="right")
            fig.add_annotation(xref="x domain", yref=c_yax, x=0.995, y=0, text="<b>MID</b>", bgcolor="#334155", font=dict(color="#ffffff", size=9), showarrow=False, xanchor="right")
            fig.add_annotation(xref="x domain", yref=c_yax, x=0.995, y=-100, text="<b>TROUGH ZONE</b>", bgcolor="#b45309", font=dict(color="#ffffff", size=9), showarrow=False, xanchor="right")

            chip_guard_html = ""
            if vpvr_data:
                if vpvr_data.get('is_lvn'):
                    chip_guard_html = "  |  <span style='background:#7f1d1d; color:#fca5a5; border:1px solid #ef4444; padding:1px 6px; border-radius:3px;'><b>⚠️ 籌碼真空加速區：防週期鈍化</b></span>"
                elif vpvr_data.get('near_poc') or vpvr_data.get('is_hvn'):
                    chip_guard_html = f"  |  <span style='background:#14532d; color:#86efac; border:1px solid #22c55e; padding:1px 6px; border-radius:3px;'><b>🛡️ POC籌碼重兵區 ({curr_sym}{vpvr_data.get('poc_price', 0):.2f})：時空共振變盤</b></span>"
                elif vpvr_data.get('is_in_value_area'):
                    chip_guard_html = "  |  <span style='background:#0f3854; color:#7dd3fc; border:1px solid #38bdf8; padding:1px 6px; border-radius:3px;'><b>⚖️ 70%價值區內：平衡震盪週期勝率 >85%</b></span>"
                else:
                    chip_guard_html = "  |  <span style='background:#3b1e54; color:#f0abfc; border:1px solid #c084fc; padding:1px 6px; border-radius:3px;'><b>⚡ 突破價值區：單邊趨勢失衡</b></span>"

            hud_cycle = f"<b>TIME CYCLE</b>  200 BARS  |  <span style='background:#78350f; color:#fde68a; padding:1px 4px;'><b>{cycle_data['window_status']}</b></span>  |  相位 {cycle_data['current_phase_deg']}°  |  距轉折 {cycle_data['next_turn_bars']}B{chip_guard_html}"
            fig.add_annotation(xref="paper", yref=f"{c_yax} domain", x=0.015, y=0.92, text=hud_cycle, bgcolor="rgba(15, 23, 42, 0.85)", bordercolor="#38bdf8", borderwidth=1, borderpad=4, font=dict(color="#ffffff", size=10, family="monospace"), showarrow=False, xanchor="left")

        if show_sl_angle and sl_data:
            sl_y = axes_map['sl_angle']
            fig.add_trace(go.Scatter(x=sl_data['interp_dates'], y=sl_data['pos_angles'], mode='lines', line=dict(color='#22c55e', width=2.0), name='SL Angle Bullish', yaxis=sl_y, showlegend=False))
            fig.add_trace(go.Scatter(x=sl_data['interp_dates'], y=sl_data['neg_angles'], mode='lines', line=dict(color='#f43f5e', width=2.0), name='SL Angle Bearish', yaxis=sl_y, showlegend=False))
            fig.add_shape(type="line", xref="paper", yref=sl_y, x0=0, x1=1, y0=0, y1=0, line=dict(color="rgba(148, 163, 184, 0.4)", width=1, dash="dot"))

            last_a = sl_data['last_angle']
            bg_a = "#16a34a" if last_a >= 0 else "#e11d48"
            fig.add_annotation(xref="x domain", yref=sl_y, x=0.995, y=last_a, text=f"<b>SL Angle {last_a:+.1f}°</b>", bgcolor=bg_a, bordercolor=bg_a, borderpad=3, font=dict(color="#ffffff", size=9, family="monospace"), showarrow=False, xanchor="right")
            fig.add_annotation(xref="paper", yref=f"{sl_y} domain", x=0.015, y=0.90, text="<b>SL ANGLE — 幾何動能角度</b>", bgcolor="rgba(15, 23, 42, 0.85)", font=dict(color="#94a3b8", size=10), showarrow=False, xanchor="left")

        if show_harmonic and harmonic_data and harmonic_comp:
            harmonic_comp.inject_harmonic_arcs_traces(fig, harmonic_data, yaxis_name=axes_map['harmonic'])

        fig.update_layout(
            template='plotly_dark',
            paper_bgcolor='#0a0e14',
            plot_bgcolor='#0a0e14',
            height=chart_total_height,
            margin=dict(l=10, r=40, t=10, b=10),
            dragmode='zoom',
            hovermode='x',
            hoverlabel=dict(bgcolor='#1f293d', font_size=12, font_family='Arial'),
            newshape=dict(line=dict(color="#facc15", width=1.5, dash="dash")),
            **y_axes_config
        )

        st.plotly_chart(
            fig,
            use_container_width=True,
            config={
                'displayModeBar': True,
                'scrollZoom': True,
                'displaylogo': False,
                'modeBarButtonsToAdd': ['drawline', 'eraseshape']
            }
        )

        if show_harmonic and harmonic_data and harmonic_comp and hasattr(harmonic_comp, "render_harmonic_countdown_matrix_ui"):
            harmonic_comp.render_harmonic_countdown_matrix_ui(harmonic_data)

        if diag_engine is not None and hasattr(diag_engine, "calculate_alpha_diagnostics"):
            try:
                diag_data = diag_engine.calculate_alpha_diagnostics(
                    df_stock=df_g01_data, symbol=current_g01_sym, market_type=market_label
                )
                st.markdown("<div style='margin-top:16px;'></div>", unsafe_allow_html=True)
                with st.expander("📊 大市跑贏度與資產多維體檢 (Alpha Diagnostics)", expanded=True):
                    c_d1, c_d2 = st.columns([6.0, 4.0])
                    with c_d1:
                        diag_engine.render_sidebar_diagnostics(diag_data)
            except Exception as e:
                st.error(f"體檢運算錯誤: {e}")

    # ==========================================
    # 分頁 2：江恩自然極限與動能通道 (Gann 02)
    # ==========================================
    with tab_gann02:
        if gann02_engine is not None and hasattr(gann02_engine, "render_page_1gann_gann02_workspace"):
            gann02_engine.render_page_1gann_gann02_workspace(df_raw, symbol=symbol)
        else:
            st.error("⚠️ 未能載入 `page_1gann_gann02_main.py` 模組。")

    # ==========================================
    # 分頁 3：小龍量化三線通道與結構流 (Gann 03)
    # ==========================================
    with tab_gann03:
        if gann03_engine is not None and hasattr(gann03_engine, "render_page_1gann_gann03_workspace"):
            gann03_engine.render_page_1gann_gann03_workspace(df_raw, symbol=symbol)
        else:
            st.error("⚠️ 未能載入 `page_1gann_gann03_main.py` 模組。")

    # ==========================================
    # 🎯 分頁 4：小龍江恩策略 Y (Gann 04)
    # ==========================================
    with tab_gann04:
        if gann04_engine is not None and hasattr(gann04_engine, "render_page_1gann_gann04_workspace"):
            gann04_engine.render_page_1gann_gann04_workspace(df_raw, symbol=symbol)
        else:
            st.error("⚠️ 未能載入 `page_1gann_gann04_main.py` 模組。")

    # ==========================================
    # 🌐 分頁 5：宏觀板塊ETF 資金流與五年極值回歸 (Gann 05)
    # ==========================================
    with tab_gann05:
        if gann05_engine is not None and hasattr(gann05_engine, "render_page_gann05"):
            gann05_engine.render_page_gann05()
        else:
            st.error("⚠️ 未能載入 `page_1gann_gann05_main.py` 模組。")

    # ==========================================
    # 📐 分頁 6：L1–L7 多層結構延伸與精簡訊號 (Gann 06)
    # ==========================================
    with tab_gann06:
        if gann06_engine is not None and hasattr(gann06_engine, "render_page_gann06"):
            gann06_engine.render_page_gann06()
        else:
            st.error("⚠️ 未能載入 `page_1gann_gann06_main.py` 模組。")

    # ==========================================
    # 🪐 分頁 7：江恩二階曲線趨勢與雙重籌碼 (Gann 07)
    # ==========================================
    with tab_gann07:
        if gann07_engine is not None and hasattr(gann07_engine, "render_page_gann07"):
            gann07_engine.render_page_gann07()
        else:
            st.error("⚠️ 未能載入 `page_1gann_gann07_main.py` 模組。")

    # ==========================================
    # 🌊 分頁 8：江恩自然極端通道與極值雲 (Gann 08)
    # ==========================================
    with tab_gann08:
        if gann08_engine is not None and hasattr(gann08_engine, "render_page_gann08"):
            gann08_engine.render_page_gann08()
        else:
            st.error("⚠️ 未能載入 `page_1gann_gann08_main.py` 模組。")