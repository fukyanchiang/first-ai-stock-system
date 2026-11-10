"""
Filename: page_1gann_gann05_main.py
Description: 🌐 Gann 05 宏觀板塊 ETF 資金流與五年極值回歸 (全球六大多空市場萬能資產旗艦版)
- 單行極簡看盤工具列 (左側智能搜尋框 + 右側核心標的快速選單 + 刷新按鈕)
- 內建一鍵收放的「全球六大市場代碼輸入指南說明表」(st.expander 預設收起，約 28px 不佔垂直空間)
- 純數字智能免後綴解析 (打 5/700 自動轉 0005.HK/0700.HK，打 600519 自動轉 600519.SS，美/日/韓/A 股自由切換)
- 全球貨幣符號自適應 (HK$, $, ¥, ₩)
- 徹底消除 RRG 星盤中的 SyntaxError 語法斷裂 (idx_pos 與 ann_lag 坐標)
- 修復模組引入命名相容 (相容 page_1gann_gann05_calc 與 page_1gann_gann05_etf_flow_calc)
- 完整保留：01 市場總覽多空溫度計、02 RRG 34板塊輪動星盤 (7態全景矩陣)、⭐ 03 回歸通道與每週價量流、04 全部 ETF 全景庫
"""

import streamlit as st
import pandas as pd
import numpy as np
import yfinance as yf
import plotly.graph_objects as go
import re
from datetime import datetime

# 導入同組運算模組 (具備雙向檔名相容性)
try:
    from page_1gann_gann05_calc import (
        GANN05_SECTOR_CONFIG,
        fetch_sector_flow_data,
        compute_34_sector_leaderboard
    )
except ImportError:
    from page_1gann_gann05_etf_flow_calc import (
        GANN05_SECTOR_CONFIG,
        fetch_sector_flow_data,
        compute_34_sector_leaderboard
    )

from page_1gann_gann05_regression_calc import (
    fetch_gann05_data,
    fetch_weekly_data,
    compute_regression_channel_metrics,
    render_regression_plotly_chart,
    compute_weekly_flow_pressure,
    render_weekly_flow_chart
)

# =========================================================================
# 🌐 全球跨市場資產解析器 (含純數字智能自動補全)
# =========================================================================
def resolve_global_symbol_info(symbol: str):
    sym = str(symbol).strip().upper()
    if not sym:
        sym = "SPY"

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


def render_global_guide_expander_g05():
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
# 💡 豐富成分庫補充
# =========================================================================
SECTOR_COMPONENTS_ENRICHED = {
    '金融 (XLF)': 'JPM / BAC / WFC / GS / MS / MA / V / BRK-B / C / BLK / 摩根士丹利 / 萬事達卡',
    '科技 (XLK)': 'AAPL / MSFT / NVDA / AVGO / ORCL / CSCO / ADBE / 蘋果 / 微軟 / 輝達',
    '通訊服務 (XLC)': 'GOOGL / META / NFLX / DIS / TMUS / 谷歌 / 臉書 / 網飛 / 迪士尼',
    '非必需消費 (XLY)': 'AMZN / TSLA / HD / MCD / NKE / SBUX / 亞馬遜 / 特斯拉 / 麥當勞',
    '醫療保健 (XLV)': 'LLY / UNH / JNJ / ABBV / MRK / PFE / 禮來 / 減肥藥 / 輝瑞',
    '工業 (XLI)': 'GE / CAT / UNP / HON / LMT / BA / 波音 / 卡特彼勒 / 洛克希德馬丁',
    '必需消費 (XLP)': 'PG / COST / PEP / KO / WMT / 可口可樂 / 百事 / 好市多 / 沃爾瑪',
    '能源 (XLE)': 'XOM / CVX / COP / SLB / EOG / 埃克森美孚 / 雪佛龍 / 原油 / 石油',
    '公用事業 (XLU)': 'NEE / SO / DUK / CEG / VST / 電力 / 核電 / 電網',
    '原物料 (XLB)': 'LIN / APD / SHW / FCX / NEM / 自由港銅礦 / 黃金 / 化工',
    '房地產 (XLRE)': 'PLD / AMT / EQIX / PSA / O / 房地產信託 / 數據中心REITs',
    '半導體 (SOXX)': 'NVDA / TSM / AVGO / AMD / QCOM / INTC / 台積電 / 超微 / 英特爾',
    '生技醫療 (XBI)': 'VRTX / REGN / BIIB / MRNA / 生物科技 / 基因編輯 / 疫苗',
    '航天與國防 (ITA)': 'LMT / RTX / BA / GD / NOC / 軍工 / 防務 / 戰機',
    '黃金礦業 (GDX)': 'NEM / GOLD / AEM / KGC / 金礦股 / 貴金屬',
    '清潔能源 (ICLN)': 'FSLR / ENPH / SEDG / PLUG / 太陽能 / 風電 / 氫能',
    '網絡安全 (CIBR)': 'PANW / CRWD / FTNT / NET / ZS / 派拓網絡 / 鷹眼 / 雲安全',
    '雲端計算 (CLOU)': 'CRM / NOW / DDOG / SNOW / WDAY / 賽富時 / 雲端軟件',
    '鈾礦與核能 (URA)': 'CCJ / URNM / KAP / 鈾礦 / 核能發電 / 裂變'
}

# =========================================================
# 🎨 專屬暗黑金融 CSS 樣式注入
# =========================================================
def inject_gann05_css():
    st.markdown("""
    <style>
        div[data-baseweb="tab-list"] button[data-baseweb="tab"] * {
            color: #ffffff !important;
            font-size: 13.5px !important;
            font-weight: 600 !important;
            opacity: 0.95 !important;
        }
        div[data-baseweb="tab-list"] button[data-baseweb="tab"]:hover * {
            color: #38bdf8 !important;
        }
        div[data-baseweb="tab-list"] button[data-baseweb="tab"][aria-selected="true"] * {
            color: #ff4d6d !important;
            font-weight: 700 !important;
        }

        div[data-testid="stTextInput"] input {
            background-color: #131722 !important;
            border: 1px solid #2a2e39 !important;
            color: #ffffff !important;
            border-radius: 6px !important;
            font-size: 13px !important;
            height: 38px !important;
        }
        div[data-testid="stTextInput"] input:focus {
            border-color: #38bdf8 !important;
        }

        div[data-testid="stRadio"] label,
        div[data-testid="stRadio"] label *,
        div[data-testid="stRadio"] p,
        div[role="radiogroup"] label * {
            color: #ffffff !important;
            font-size: 12.5px !important;
            font-weight: 600 !important;
        }
        div[data-testid="stCheckbox"] label,
        div[data-testid="stCheckbox"] label * {
            color: #ffffff !important;
            font-size: 12.5px !important;
            font-weight: 600 !important;
        }

        div[data-testid="stButton"] button {
            background-color: #161a25 !important;
            border: 1px solid #2a2e39 !important;
            color: #ffffff !important;
            border-radius: 4px !important;
            font-size: 12px !important;
            font-weight: 600 !important;
            height: 30px !important;
            transition: all 0.15s ease !important;
        }
        div[data-testid="stButton"] button:hover {
            border-color: #38bdf8 !important;
            background-color: #242938 !important;
        }

        div[data-testid="stSlider"] {
            margin-top: -4px !important;
            margin-bottom: 2px !important;
        }
        div[data-testid="stSlider"] label,
        div[data-testid="stSlider"] label * {
            color: #ffffff !important;
            font-weight: 600 !important;
            font-size: 12px !important;
        }
        div[data-testid="stSlider"] div[role="slider"] {
            background-color: #00e5ff !important;
            border: 2px solid #ffffff !important;
            box-shadow: 0 0 8px rgba(0, 229, 255, 0.7) !important;
        }

        .gann05-header-box {
            background: linear-gradient(135deg, rgba(30, 41, 59, 0.85), rgba(15, 23, 42, 0.95));
            border: 1px solid #475569;
            border-radius: 10px;
            padding: 14px 18px;
            margin-bottom: 12px;
        }
        .gann05-stat-card {
            background: rgba(15, 23, 42, 0.7);
            border: 1px solid #334155;
            border-radius: 8px;
            padding: 8px 12px;
            text-align: center;
        }
        .gann05-countdown-card {
            background: rgba(15, 23, 42, 0.85);
            border-radius: 8px;
            padding: 10px 14px;
            display: flex;
            justify-content: space-between;
            align-items: center;
            margin-bottom: 6px;
        }
        .gann05-macro-card {
            background: linear-gradient(145deg, #1e293b, #0f172a);
            border: 1px solid #475569;
            border-radius: 10px;
            padding: 12px 14px;
            margin-bottom: 12px;
            box-shadow: 0 4px 6px -1px rgba(0, 0, 0, 0.3);
        }
        .gann05-bar-bg {
            background: #334155;
            height: 7px;
            border-radius: 4px;
            width: 100%;
            margin-top: 6px;
            overflow: hidden;
        }
        .gann05-guide-table {
            width: 100%;
            border-collapse: collapse;
            font-size: 13px;
            background: rgba(15, 23, 42, 0.7);
            border-radius: 8px;
            overflow: hidden;
            border: 1px solid #334155;
            margin: 10px 0 16px 0;
        }
        .gann05-guide-table th {
            background: #1e293b;
            color: #f8fafc;
            text-align: left;
            padding: 9px 14px;
            font-weight: 700;
            border-bottom: 1px solid #334155;
        }
        .gann05-guide-table td {
            padding: 9px 14px;
            border-bottom: 1px solid rgba(51, 65, 85, 0.45);
            color: #cbd5e1;
        }
    </style>
    """, unsafe_allow_html=True)

# =========================================================================
# 🌐 分頁 1：01 市場總覽
# =========================================================================
MACRO_CORE_ASSETS = [
    {"code": "SPY", "name": "標普 500", "cat": "美股大盤標竿", "prefix": "$", "suffix": "", "is_vol": False},
    {"code": "QQQ", "name": "納斯達克 100", "cat": "全球科技龍頭", "prefix": "$", "suffix": "", "is_vol": False},
    {"code": "2800.HK", "name": "盈富基金 (恒指)", "cat": "港股核心指數", "prefix": "HK$", "suffix": "", "is_vol": False},
    {"code": "UUP", "name": "美元指數 ETF", "cat": "全球流動性核心", "prefix": "$", "suffix": "", "is_vol": False},
    {"code": "^TNX", "name": "美國 10 年國債息", "cat": "全球資產定價之錨", "prefix": "", "suffix": "%", "is_vol": False},
    {"code": "^TYX", "name": "美國 30 年國債息", "cat": "超長天期通脹預期", "prefix": "", "suffix": "%", "is_vol": False},
    {"code": "TLT", "name": "20Y+ 美國國債 ETF", "cat": "長天期債券價格", "prefix": "$", "suffix": "", "is_vol": False},
    {"code": "CL=F", "name": "WTI 原油期貨", "cat": "全球能源通脹之源", "prefix": "$", "suffix": "/桶", "is_vol": False},
    {"code": "GLD", "name": "黃金信託 ETF", "cat": "大宗避險貴金屬", "prefix": "$", "suffix": "", "is_vol": False},
    {"code": "BTC-USD", "name": "比特幣", "cat": "數字黃金 / 風險偏好", "prefix": "$", "suffix": "", "is_vol": False},
    {"code": "^VIX", "name": "VIX 恐慌指數", "cat": "美股標普隱含波動率", "prefix": "", "suffix": " 點", "is_vol": True},
    {"code": "^VXN", "name": "VXN 科技恐慌指數", "cat": "納指 100 隱含波動率", "prefix": "", "suffix": " 點", "is_vol": True},
    {"code": "^VHSI", "alt_code": "VHSI", "name": "VHSI 恒指波幅指數", "cat": "港股恒指隱含波動率", "prefix": "", "suffix": " 點", "is_vol": True},
    {"code": "^MOVE", "name": "MOVE 債市恐慌指數", "cat": "美債隱含波動率", "prefix": "", "suffix": " 點", "is_vol": True}
]

@st.cache_data(ttl=900, show_spinner=False)
def fetch_macro_overview_data_v3():
    tickers = []
    for m in MACRO_CORE_ASSETS:
        tickers.append(m["code"])
        if "alt_code" in m:
            tickers.append(m["alt_code"])
    try:
        raw = yf.download(tickers, period="2y", interval="1d", progress=False)
        if isinstance(raw.columns, pd.MultiIndex):
            data = raw['Close']
        else:
            data = raw[['Close']] if 'Close' in raw else raw
        return data.dropna(how='all')
    except Exception:
        return pd.DataFrame()

def render_tab_01_market_overview():
    st.markdown("#### 🌐 全球核心宏觀資產 · 多空溫度計與趨勢總覽")
    st.caption("即時監控跨市場資產之相對強弱、10Y/30Y國債息、原油通脹與 VIX / VXN / VHSI / MOVE 四大恐慌雷達。")

    with st.spinner("正在加載全球宏觀跨市場數據..."):
        df_macro = fetch_macro_overview_data_v3()

    if df_macro.empty:
        st.warning("⚠️ 宏觀市場數據加載延遲，請稍後點擊重新整理。")
        return

    cards = []
    for item in MACRO_CORE_ASSETS:
        code = item["code"]
        alt = item.get("alt_code")
        s = pd.Series(dtype=float)

        if code in df_macro.columns and not df_macro[code].dropna().empty:
            s = df_macro[code].dropna()
        elif alt and alt in df_macro.columns and not df_macro[alt].dropna().empty:
            s = df_macro[alt].dropna()

        if len(s) >= 10:
            p_now = s.iloc[-1]
            p_1w = s.iloc[-6] if len(s) >= 6 else s.iloc[0]
            p_1m = s.iloc[-22] if len(s) >= 22 else s.iloc[0]
            p_start = s.iloc[-250] if len(s) >= 250 else s.iloc[0]

            chg_1w = ((p_now / p_1w) - 1) * 100
            chg_1m = ((p_now / p_1m) - 1) * 100
            chg_ytd = ((p_now / p_start) - 1) * 100

            high_52 = s.tail(250).max()
            low_52 = s.tail(250).min()
            temp = ((p_now - low_52) / (high_52 - low_52) * 100) if high_52 > low_52 else 50.0

            if item["is_vol"]:
                if temp >= 75:
                    status_badge = "🚨 劇烈恐慌 / 波動飆升"
                    temp_color = "#ff3366"
                elif temp >= 50:
                    status_badge = "⚠️ 警惕升溫"
                    temp_color = "#facc15"
                elif temp >= 25:
                    status_badge = "⚖️ 波動溫和"
                    temp_color = "#38bdf8"
                else:
                    status_badge = "🟢 極度平靜 / 偏多"
                    temp_color = "#00ff88"
            else:
                if temp >= 80:
                    status_badge = "🔥 極度過熱 (近頂)"
                    temp_color = "#ff3366"
                elif temp >= 60:
                    status_badge = "🟢 強勢偏多"
                    temp_color = "#00ff88"
                elif temp >= 40:
                    status_badge = "⚖️ 中性平衡"
                    temp_color = "#38bdf8"
                elif temp >= 20:
                    status_badge = "🟡 弱勢偏空"
                    temp_color = "#facc15"
                else:
                    status_badge = "❄️ 極端超賣 (冰點)"
                    temp_color = "#818cf8"

            cards.append({
                "item": item, "price": p_now, "1w": chg_1w, "1m": chg_1m,
                "ytd": chg_ytd, "temp": temp, "status": status_badge, "color": temp_color,
                "series": s
            })

    if cards:
        for i in range(0, len(cards), 4):
            chunk = cards[i:i+4]
            cols = st.columns(4)
            for col, c in zip(cols, chunk):
                with col:
                    item = c['item']
                    val_str = f"{item['prefix']}{c['price']:,.2f}{item['suffix']}"
                    st.markdown(f"""
                    <div class="gann05-macro-card">
                        <div style="display:flex; justify-content:space-between; align-items:center;">
                            <span style="font-weight:700; color:#ffffff; font-size:14.5px;">{item['name']}</span>
                            <span style="font-size:11px; font-weight:600; color:#38bdf8; background:#0f172a; border:1px solid #334155; padding:2px 6px; border-radius:4px;">{item['code']}</span>
                        </div>
                        <div style="font-size:11.5px; color:#cbd5e1; font-weight:500; margin-top:3px;">{item['cat']}</div>
                        <div style="font-size:21px; font-weight:bold; color:#ffffff; margin: 6px 0;">
                            {val_str}
                        </div>
                        <div style="display:flex; justify-content:space-between; font-size:11.5px; color:#e2e8f0; margin-bottom:6px;">
                            <span>近週 <b style="color:{'#00ff88' if c['1w']>=0 else '#ff4d6d'}">{c['1w']:+.1f}%</b></span>
                            <span>近月 <b style="color:{'#00ff88' if c['1m']>=0 else '#ff4d6d'}">{c['1m']:+.1f}%</b></span>
                            <span>年化 <b style="color:{'#00ff88' if c['ytd']>=0 else '#ff4d6d'}">{c['ytd']:+.1f}%</b></span>
                        </div>
                        <div style="font-size:11.5px; color:{c['color']}; font-weight:bold; margin-bottom:3px;">
                            溫度計 {c['temp']:.0f}° ({c['status']})
                        </div>
                        <div class="gann05-bar-bg">
                            <div style="background:{c['color']}; width:{c['temp']:.1f}%; height:100%;"></div>
                        </div>
                    </div>
                    """, unsafe_allow_html=True)

    st.markdown("<div style='margin-top:16px;'></div>", unsafe_allow_html=True)
    st.markdown("##### 📈 核心宏觀資產走勢對比 (以 100 為基準點展開)")

    norm_dict = {}
    for c in cards:
        code = c['item']['code']
        s = c['series']
        if len(s) >= 15:
            norm_dict[code] = s

    if norm_dict:
        norm_df = pd.DataFrame(norm_dict).dropna()
        if not norm_df.empty:
            all_codes = list(norm_df.columns)
            default_selected = ["SPY", "QQQ", "^TNX", "CL=F", "UUP", "GLD"]
            default_valid = [c for c in default_selected if c in all_codes]

            sel_codes = st.multiselect(
                "選取要對比的宏觀資產：",
                options=all_codes,
                default=default_valid,
                format_func=lambda x: f"{next((m['name'] for m in MACRO_CORE_ASSETS if m['code']==x), x)} ({x})"
            )

            if sel_codes:
                sub_norm = norm_df[sel_codes].tail(250)
                norm_pct = (sub_norm / sub_norm.iloc[0]) * 100
                fig_macro = go.Figure()
                colors = ['#38bdf8', '#c084fc', '#f43f5e', '#facc15', '#00ff88', '#fb923c', '#f8fafc', '#2dd4bf', '#a78bfa', '#f472b6', '#4ade80', '#fb7185', '#34d399', '#f97316']

                for idx, code in enumerate(sel_codes):
                    item_name = next((m['name'] for m in MACRO_CORE_ASSETS if m['code'] == code), code)
                    fig_macro.add_trace(go.Scatter(
                        x=norm_pct.index, y=norm_pct[code],
                        mode='lines', name=f"{item_name} ({code})",
                        line=dict(width=2.2, color=colors[idx % len(colors)])
                    ))

                fig_macro.update_layout(
                    template='plotly_dark',
                    paper_bgcolor='#0a0e14',
                    plot_bgcolor='#0a0e14',
                    height=410,
                    margin=dict(l=10, r=20, t=20, b=10),
                    hovermode='x unified',
                    legend=dict(
                        font=dict(color='#f1f5f9', size=11.5),
                        bgcolor='rgba(15, 23, 42, 0.7)',
                        bordercolor='#334155',
                        borderwidth=1
                    ),
                    yaxis=dict(
                        title=dict(text="基準表現 (100 = 起點)", font=dict(color='#f8fafc', size=12)),
                        tickfont=dict(color='#cbd5e1', size=11),
                        showgrid=True,
                        gridcolor='rgba(71, 85, 105, 0.35)'
                    ),
                    xaxis=dict(
                        tickfont=dict(color='#cbd5e1', size=11),
                        showgrid=True,
                        gridcolor='rgba(71, 85, 105, 0.35)'
                    )
                )
                st.plotly_chart(fig_macro, use_container_width=True)

    # 跨市場真實相關係數熱力圖
    st.markdown("---")
    st.markdown("##### 🔗 跨市場資產真實相關性矩陣 (Correlation Heatmap)")
    st.caption("基於日收益率 (Daily Return) 嚴格計算，揭示納指 (QQQ)、美債息 (^TNX)、WTI 原油 (CL=F)、美元指數 (UUP) 的真實統計關聯。")

    period_options = [
        "⚡ 近 1 週 (超短衝刺)", "📅 近 2 週 (雙週輪動)", "🚀 近 1 個月 (月度動態)", "🌊 近 2 個月 (雙月過渡)",
        "🏆 近 3 個月 (季度標準)", "📈 近 6 個月 (中期趨勢)", "🌐 近 1 年 (標準週期)", "🏛️ 近 2 年 (長期宏觀)"
    ]
    corr_period_choice = st.selectbox("選擇相關性統計週期：", period_options, index=4)

    period_days_map = {
        "⚡ 近 1 週 (超短衝刺)": 6, "📅 近 2 週 (雙週輪動)": 11, "🚀 近 1 個月 (月度動態)": 22, "🌊 近 2 個月 (雙月過渡)": 44,
        "🏆 近 3 個月 (季度標準)": 65, "📈 近 6 個月 (中期趨勢)": 130, "🌐 近 1 年 (標準週期)": 250, "🏛️ 近 2 年 (長期宏觀)": 500
    }
    target_days = period_days_map[corr_period_choice]

    focus_assets = [
        ("QQQ", "納指 (QQQ)"), ("SPY", "標普 (SPY)"), ("^TNX", "10Y美債 (^TNX)"),
        ("CL=F", "WTI原油 (CL=F)"), ("UUP", "美元指數 (UUP)"), ("GLD", "黃金 (GLD)"),
        ("BTC-USD", "比特幣 (BTC)"), ("^VIX", "VIX恐慌 (^VIX)")
    ]

    valid_series_dict = {}
    min_required_bars = max(4, int(target_days * 0.55))

    for code, d_name in focus_assets:
        if code in df_macro.columns:
            s_clean = df_macro[code].dropna().tail(target_days)
            if len(s_clean) >= min_required_bars:
                valid_series_dict[d_name] = s_clean.pct_change()

    if valid_series_dict:
        df_returns = pd.DataFrame(valid_series_dict).dropna()
        if not df_returns.empty and len(df_returns) >= 3:
            corr_mat = df_returns.corr().round(2)

            fig_heat = go.Figure(data=go.Heatmap(
                z=corr_mat.values, x=corr_mat.columns.tolist(), y=corr_mat.index.tolist(),
                colorscale=[[0.0, '#f43f5e'], [0.5, '#1e293b'], [1.0, '#00ff88']],
                zmin=-1.0, zmax=1.0, text=corr_mat.values, texttemplate="%{text:+.2f}",
                textfont=dict(size=12, color="#ffffff", family="Arial Black"),
                colorbar=dict(title=dict(text="相關係數", font=dict(color="#ffffff", size=11)), tickfont=dict(color="#cbd5e1", size=10), len=0.88)
            ))

            fig_heat.update_layout(
                template='plotly_dark', paper_bgcolor='#0a0e14', plot_bgcolor='#0a0e14', height=480,
                margin=dict(l=10, r=20, t=25, b=10),
                xaxis=dict(tickfont=dict(color='#cbd5e1', size=11), showgrid=False),
                yaxis=dict(tickfont=dict(color='#cbd5e1', size=11), showgrid=False, autorange='reversed')
            )
            st.plotly_chart(fig_heat, use_container_width=True)


# =========================================================================
# 🎡 分頁 2：板塊輪動星盤 (語法完全修復版)
# =========================================================================
RRG_TIMEFRAMES = {
    '3D': {'label': '⚡ 3 天 (超短衝刺)', 'window': 6, 'lag': 2, 'scale': 6.0, 'step_gap': 1},
    '1W': {'label': '📅 1 週 (近週輪動)', 'window': 10, 'lag': 3, 'scale': 5.0, 'step_gap': 2},
    '2W': {'label': '🚀 2 週 (短期趨勢)', 'window': 15, 'lag': 5, 'scale': 4.5, 'step_gap': 3},
    '1M': {'label': '🏆 1 個月 (經典標準)', 'window': 20, 'lag': 5, 'scale': 4.0, 'step_gap': 5},
    '3M': {'label': '🌊 3 個月 (中長佈局)', 'window': 60, 'lag': 10, 'scale': 3.5, 'step_gap': 10}
}

@st.cache_data(ttl=1800, show_spinner=False)
def fetch_rrg_chart_data():
    all_anchors = list(set([cfg['anchor'] for cfg in GANN05_SECTOR_CONFIG.values()]))
    tickers = ['SPY'] + all_anchors
    try:
        raw = yf.download(tickers, period="1y", interval="1d", progress=False)
        if isinstance(raw.columns, pd.MultiIndex):
            data = raw['Close']
        else:
            data = raw[['Close']] if 'Close' in raw else raw
        return data.dropna(how='all')
    except Exception:
        return pd.DataFrame()

def calculate_rrg_series(s_price, s_spy, win, lag, multiplier):
    common_idx = s_price.index.intersection(s_spy.index)
    if len(common_idx) < (win + lag + 5):
        return None, None
    rs = (s_price.loc[common_idx] / s_spy.loc[common_idx]) * 100
    roll_mean = rs.rolling(win).mean()
    roll_std = rs.rolling(win).std().replace(0, np.nan).fillna(1e-4)
    rs_ratio = 100 + ((rs - roll_mean) / roll_std) * multiplier
    rs_momentum = 100 + ((rs_ratio - rs_ratio.shift(lag)) * 3)
    return rs_ratio.dropna(), rs_momentum.dropna()

def render_tab_02_sector_rotation():
    st.markdown("#### 🎡 34 大板塊輪動星盤 (RRG Relative Rotation Graph)")
    st.caption("對標標普 500 (SPY)，以「相對強度 (RS-Ratio)」與「動能動量 (RS-Momentum)」劃分四大象限。")

    if 'gann05_rrg_tf' not in st.session_state:
        st.session_state['gann05_rrg_tf'] = '1M'

    c_tf_list = list(RRG_TIMEFRAMES.keys())
    cols_tf = st.columns(len(c_tf_list))
    for col, tf_key in zip(cols_tf, c_tf_list):
        with col:
            is_active = (st.session_state['gann05_rrg_tf'] == tf_key)
            if st.button(RRG_TIMEFRAMES[tf_key]['label'], key=f"btn_rrg_{tf_key}", use_container_width=True,
                         type="primary" if is_active else "secondary"):
                st.session_state['gann05_rrg_tf'] = tf_key
                st.rerun()

    active_tf = st.session_state['gann05_rrg_tf']
    cfg_tf = RRG_TIMEFRAMES[active_tf]

    c_opt1, c_opt2 = st.columns([2, 2])
    with c_opt1:
        show_tails = st.checkbox("🐍 顯示貪食蛇運動尾巴 (追蹤近期行進方向)", value=True, key="chk_rrg_tails")
    with c_opt2:
        tail_steps = st.slider("尾巴歷史長度 (步數)：", min_value=2, max_value=6, value=4, key="sld_rrg_tail_len") if show_tails else 1

    with st.spinner("正在加載板塊數據並計算 RRG 貪食蛇星盤..."):
        df_rrg_prices = fetch_rrg_chart_data()

    if df_rrg_prices.empty or 'SPY' not in df_rrg_prices.columns:
        st.warning("⚠️ 輪動星盤數據加載延遲，請稍後重試。")
        return

    s_spy = df_rrg_prices['SPY'].dropna()
    rrg_items = []
    win = cfg_tf['window']
    lag = cfg_tf['lag']
    multiplier = cfg_tf['scale']
    step_gap = cfg_tf['step_gap']

    for sector_name, cfg in GANN05_SECTOR_CONFIG.items():
        anchor = cfg['anchor']
        if anchor in df_rrg_prices.columns:
            s_price = df_rrg_prices[anchor].dropna()
            r_ratio_s, r_mom_s = calculate_rrg_series(s_price, s_spy, win, lag, multiplier)
            if r_ratio_s is not None and len(r_ratio_s) >= (tail_steps * step_gap):
                tail_x = []
                tail_y = []
                for step_i in range(tail_steps - 1, -1, -1):
                    # 🌟 徹底修復負數步長索引計算
                    idx_pos = -(step_i * step_gap + 1)
                    tail_x.append(float(r_ratio_s.iloc[idx_pos]))
                    tail_y.append(float(r_mom_s.iloc[idx_pos]))

                cur_x = tail_x[-1]
                cur_y = tail_y[-1]

                if cur_x >= 100 and cur_y >= 100:
                    quad = "領先 (Leading)"
                    q_col = "#00ff88"
                elif cur_x >= 100 and cur_y < 100:
                    quad = "轉弱 (Weakening)"
                    q_col = "#facc15"
                elif cur_x < 100 and cur_y < 100:
                    quad = "落後 (Lagging)"
                    q_col = "#f43f5e"
                else:
                    quad = "改善 (Improving)"
                    q_col = "#38bdf8"

                rrg_items.append({
                    "板塊": sector_name, "代號": anchor, "類型": cfg['type'],
                    "RS_Ratio": round(cur_x, 2), "RS_Momentum": round(cur_y, 2),
                    "象限": quad, "顏色": q_col,
                    "tail_x": tail_x, "tail_y": tail_y
                })

    if not rrg_items:
        st.warning("⚠️ 暫時未能產出有效星盤點數，請稍後重試。")
        return

    all_x = [pt for item in rrg_items for pt in item['tail_x']]
    all_y = [pt for item in rrg_items for pt in item['tail_y']]
    min_x = min(min(all_x) - 4, 82.0)
    max_x = max(max(all_x) + 4, 118.0)
    min_y = min(min(all_y) - 4, 82.0)
    max_y = max(max(all_y) + 4, 118.0)

    fig_rrg = go.Figure()
    fig_rrg.add_shape(type="rect", x0=100, y0=100, x1=max_x, y1=max_y, fillcolor="rgba(0, 255, 136, 0.06)", line_width=0)
    fig_rrg.add_shape(type="rect", x0=100, y0=min_y, x1=max_x, y1=100, fillcolor="rgba(250, 204, 21, 0.06)", line_width=0)
    fig_rrg.add_shape(type="rect", x0=min_x, y0=min_y, x1=100, y1=100, fillcolor="rgba(244, 63, 94, 0.06)", line_width=0)
    fig_rrg.add_shape(type="rect", x0=min_x, y0=100, x1=100, y1=max_y, fillcolor="rgba(56, 189, 248, 0.06)", line_width=0)

    fig_rrg.add_hline(y=100, line_dash="dash", line_color="#64748b", line_width=1.5)
    fig_rrg.add_vline(x=100, line_dash="dash", line_color="#64748b", line_width=1.5)

    # 🌟 徹底修復標籤坐標計算
    ann_lead_x = 100.0 + (max_x - 100.0) * 0.72
    ann_lead_y = 100.0 + (max_y - 100.0) * 0.88
    ann_lag_x = 100.0 - (100.0 - min_x) * 0.72
    ann_lag_y = 100.0 - (100.0 - min_y) * 0.88

    fig_rrg.add_annotation(x=ann_lead_x, y=ann_lead_y, text="<b>領先 (LEADING)</b>", showarrow=False, font=dict(color="#00ff88", size=14))
    fig_rrg.add_annotation(x=ann_lead_x, y=ann_lag_y, text="<b>轉弱 (WEAKENING)</b>", showarrow=False, font=dict(color="#facc15", size=14))
    fig_rrg.add_annotation(x=ann_lag_x, y=ann_lag_y, text="<b>落後 (LAGGING)</b>", showarrow=False, font=dict(color="#f43f5e", size=14))
    fig_rrg.add_annotation(x=ann_lag_x, y=ann_lead_y, text="<b>改善 (IMPROVING)</b>", showarrow=False, font=dict(color="#38bdf8", size=14))

    for item in rrg_items:
        tx = item['tail_x']
        ty = item['tail_y']
        q_col = item['顏色']
        anchor = item['代號']
        if show_tails and len(tx) > 1:
            fig_rrg.add_trace(go.Scatter(x=tx, y=ty, mode="lines", line=dict(color=q_col, width=2.0), opacity=0.55, showlegend=False, hoverinfo="skip"))
        fig_rrg.add_trace(go.Scatter(
            x=[tx[-1]], y=[ty[-1]], mode="markers+text",
            marker=dict(size=13, color=q_col, line=dict(width=1.5, color="#ffffff")),
            text=[anchor], textposition="top center", textfont=dict(color="#f8fafc", size=11, family="Arial Black"),
            showlegend=False, hovertext=f"<b>{item['板塊']} ({anchor})</b><br>RS-Ratio: {item['RS_Ratio']}<br>RS-Momentum: {item['RS_Momentum']}", hoverinfo="text"
        ))

    fig_rrg.update_layout(
        template='plotly_dark', paper_bgcolor='#0a0e14', plot_bgcolor='#0a0e14', height=820,
        margin=dict(l=25, r=25, t=35, b=25),
        xaxis=dict(title=dict(text=f"相對強度 RS-Ratio ({cfg_tf['label']})", font=dict(color='#f8fafc', size=13)), range=[min_x, max_x], showgrid=True, gridcolor='rgba(71, 85, 105, 0.35)'),
        yaxis=dict(title=dict(text=f"動能動量 RS-Momentum ({cfg_tf['label']})", font=dict(color='#f8fafc', size=13)), range=[min_y, max_y], showgrid=True, gridcolor='rgba(71, 85, 105, 0.35)')
    )
    st.plotly_chart(fig_rrg, use_container_width=True)

    df_rrg = pd.DataFrame(rrg_items)
    c1, c2, c3, c4 = st.columns(4)
    with c1:
        lead_list = df_rrg[df_rrg['象限'].str.contains('領先')]['板塊'].tolist()
        st.success(f"🟢 **領先板塊 ({len(lead_list)})**\n\n" + ("\n".join([f"• {x}" for x in lead_list]) if lead_list else "暫無"))
    with c2:
        imp_list = df_rrg[df_rrg['象限'].str.contains('改善')]['板塊'].tolist()
        st.info(f"🔵 **改善板塊 ({len(imp_list)})**\n\n" + ("\n".join([f"• {x}" for x in imp_list]) if imp_list else "暫無"))
    with c3:
        weak_list = df_rrg[df_rrg['象限'].str.contains('轉弱')]['板塊'].tolist()
        st.warning(f"🟡 **轉弱板塊 ({len(weak_list)})**\n\n" + ("\n".join([f"• {x}" for x in weak_list]) if weak_list else "暫無"))
    with c4:
        lag_list = df_rrg[df_rrg['象限'].str.contains('落後')]['板塊'].tolist()
        st.error(f"🔴 **落後板塊 ({len(lag_list)})**\n\n" + ("\n".join([f"• {x}" for x in lag_list]) if lag_list else "暫無"))

    # 7態操盤指南說明表格
    st.markdown("<div style='margin-top:28px;'></div>", unsafe_allow_html=True)
    with st.expander("📖 查閱【7 大狀態操盤定義與實戰指導說明書】", expanded=True):
        st.markdown("""
        <table class="gann05-guide-table">
            <thead>
                <tr>
                    <th style="width:26%;">狀態標籤</th>
                    <th style="width:36%;">核心判定邏輯</th>
                    <th style="width:38%;">實戰操盤指導</th>
                </tr>
            </thead>
            <tbody>
                <tr>
                    <td style="font-weight:700; color:#00ff88;">🔥 長短共振 (強勢主升浪)</td>
                    <td>1W 領先 ＋ 1M 領先，3D 動能維持強勢</td>
                    <td>最強主升浪，強者恆強，順勢抱緊主力倉位</td>
                </tr>
                <tr>
                    <td style="font-weight:700; color:#38bdf8;">🌱 右側吸籌 (機構築底建倉)</td>
                    <td>1M 改善 ＋ 短線 (1W/3D) 維持改善或領先</td>
                    <td>市場熬過左側殺跌，機構有計劃建倉，最佳低吸潛伏點</td>
                </tr>
                <tr>
                    <td style="font-weight:700; color:#60a5fa;">🚀 短線暗中拐頭 (黑馬蓄勢)</td>
                    <td>1M 仍落後/轉弱，但超短線 (3D/1W) 率先拐頭衝入改善/領先</td>
                    <td>先知先覺資金提早建倉，爆發前夕，適合敏銳試探</td>
                </tr>
                <tr>
                    <td style="font-weight:700; color:#facc15;">⚠️ 長多短回吐 (短線假摔洗盤)</td>
                    <td>1M 領先維持多頭，但短線 (3D/1W) 回吐掉入轉弱/落後</td>
                    <td>長多短跌，升浪中主力縮量震倉洗盤，回調找買點</td>
                </tr>
                <tr>
                    <td style="font-weight:700; color:#f97316;">⚡ 破位退潮 (主力出貨派發)</td>
                    <td>1M 已經轉弱，短線 (3D/1W) 更摜入落後象限</td>
                    <td>不是假摔而是真見頂，主力出逃，嚴禁抄底、果斷止盈逃命</td>
                </tr>
                <tr>
                    <td style="font-weight:700; color:#f43f5e;">❄️ 全面偏弱 (資金失血避開)</td>
                    <td>1W 落後 ＋ 1M 落後，且短線未見任何拐頭</td>
                    <td>熊市深淵，大市抽血板塊，堅決空倉避開</td>
                </tr>
                <tr>
                    <td style="font-weight:700; color:#94a3b8;">⚖️ 窄幅整理 (多空拉鋸過渡)</td>
                    <td>不屬於上述 6 種極端走勢，在 100 中軸窄幅徘徊</td>
                    <td>籌碼中性換手中，多空拉鋸，耐心等待方向明朗</td>
                </tr>
            </tbody>
        </table>
        """, unsafe_allow_html=True)

    # 7態全景矩陣
    st.markdown("#### 🧭 跨週期長短共振與暗中拐頭對比矩陣 (34 板塊全景無滾條平鋪)")
    multi_records = []
    for sector_name, cfg in GANN05_SECTOR_CONFIG.items():
        anchor = cfg['anchor']
        if anchor in df_rrg_prices.columns:
            s_price = df_rrg_prices[anchor].dropna()

            res_quads = {}
            for tf_k in ['3D', '1W', '1M', '3M']:
                c_conf = RRG_TIMEFRAMES[tf_k]
                r_r, r_m = calculate_rrg_series(s_price, s_spy, c_conf['window'], c_conf['lag'], c_conf['scale'])
                if r_r is not None and not r_r.empty:
                    last_x = r_r.iloc[-1]
                    last_y = r_m.iloc[-1]
                    if last_x >= 100 and last_y >= 100:
                        res_quads[tf_k] = "🟢 領先"
                    elif last_x >= 100 and last_y < 100:
                        res_quads[tf_k] = "🟡 轉弱"
                    elif last_x < 100 and last_y < 100:
                        res_quads[tf_k] = "🔴 落後"
                    else:
                        res_quads[tf_k] = "🔵 改善"
                else:
                    res_quads[tf_k] = "—"

            q_3d = res_quads.get('3D', '—')
            q_1w = res_quads.get('1W', '—')
            q_1m = res_quads.get('1M', '—')
            q_3m = res_quads.get('3M', '—')

            is_lead_3d = ("領先" in q_3d)
            is_imp_3d = ("改善" in q_3d)
            is_weak_3d = ("轉弱" in q_3d)
            is_lag_3d = ("落後" in q_3d)

            is_lead_1w = ("領先" in q_1w)
            is_imp_1w = ("改善" in q_1w)
            is_weak_1w = ("轉弱" in q_1w)
            is_lag_1w = ("落後" in q_1w)

            is_lead_1m = ("領先" in q_1m)
            is_imp_1m = ("改善" in q_1m)
            is_weak_1m = ("轉弱" in q_1m)
            is_lag_1m = ("落後" in q_1m)

            if is_lead_1w and is_lead_1m and not (is_weak_3d or is_lag_3d):
                sig_tag = "🔥 長短共振 (強勢主升浪)"
                sig_type = "共振"
            elif is_lead_1m and (is_weak_3d or is_lag_3d or is_weak_1w or is_lag_1w):
                sig_tag = "⚠️ 長多短回吐 (短線假摔洗盤)"
                sig_type = "假摔"
            elif is_weak_1m and (is_lag_3d or is_lag_1w):
                sig_tag = "⚡ 破位退潮 (主力出貨派發)"
                sig_type = "退潮"
            elif is_imp_1m and (is_imp_1w or is_lead_1w or is_imp_3d or is_lead_3d):
                sig_tag = "🌱 右側吸籌 (機構築底建倉)"
                sig_type = "吸籌"
            elif (is_lag_1m or is_weak_1m) and (is_imp_3d or is_lead_3d or is_imp_1w or is_lead_1w):
                sig_tag = "🚀 短線暗中拐頭 (黑馬蓄勢)"
                sig_type = "拐頭"
            elif is_lag_1w and is_lag_1m:
                sig_tag = "❄️ 全面偏弱 (資金失血避開)"
                sig_type = "偏弱"
            else:
                sig_tag = "⚖️ 窄幅整理 (多空拉鋸過渡)"
                sig_type = "整理"

            multi_records.append({
                "板塊名稱": sector_name, "核心標的": anchor,
                "⚡ 3天 (超短)": q_3d, "📅 1週 (近週)": q_1w,
                "🏆 1個月 (標準)": q_1m, "🌊 3個月 (長線)": q_3m,
                "跨週期態勢解讀 / 信號": sig_tag, "_sig_type": sig_type
            })

    if multi_records:
        df_multi = pd.DataFrame(multi_records)
        f_sig = st.selectbox(
            "🎯 按信號特徵快速過濾：",
            [
                "全部板塊 (34)", "🔥 只看【長短共振 (強勢主升浪)】", "🌱 只看【右側吸籌 (機構築底建倉)】",
                "🚀 只看【短線暗中拐頭 (黑馬蓄勢)】", "⚠️ 只看【長多短回吐 (短線假摔洗盤)】",
                "⚡ 只看【破位退潮 (主力出貨派發)】", "❄️ 只看【全面偏弱 (資金失血避開)】",
                "⚖️ 只看【窄幅整理 (多空拉鋸過渡)】"
            ]
        )

        if "共振" in f_sig:
            df_filtered = df_multi[df_multi['_sig_type'] == "共振"]
        elif "吸籌" in f_sig:
            df_filtered = df_multi[df_multi['_sig_type'] == "吸籌"]
        elif "拐頭" in f_sig:
            df_filtered = df_multi[df_multi['_sig_type'] == "拐頭"]
        elif "假摔" in f_sig:
            df_filtered = df_multi[df_multi['_sig_type'] == "假摔"]
        elif "退潮" in f_sig:
            df_filtered = df_multi[df_multi['_sig_type'] == "退潮"]
        elif "偏弱" in f_sig:
            df_filtered = df_multi[df_multi['_sig_type'] == "偏弱"]
        elif "整理" in f_sig:
            df_filtered = df_multi[df_multi['_sig_type'] == "整理"]
        else:
            df_filtered = df_multi

        no_scroll_height = max((len(df_filtered) + 1) * 38 + 45, 120)
        st.dataframe(df_filtered.drop(columns=['_sig_type']), use_container_width=True, hide_index=True, height=no_scroll_height)


# =========================================================================
# 📊 模組 34 核心引擎：單標的 vs SPY 滾動相對回報走勢 (Alpha 曲線)
# =========================================================================
@st.cache_data(ttl=1800, show_spinner=False)
def fetch_relative_spy_comparison(target_symbol: str):
    clean_target, _, _ = resolve_global_symbol_info(target_symbol)
    tickers = list(set([clean_target, 'SPY']))
    try:
        raw = yf.download(tickers, period="2y", interval="1d", progress=False)
        if isinstance(raw.columns, pd.MultiIndex):
            df_close = raw['Close']
        else:
            df_close = raw[['Close']] if 'Close' in raw else raw
        return df_close.dropna()
    except Exception:
        return pd.DataFrame()

def render_spy_relative_return_chart(symbol: str, symbol_display: str):
    clean_sym, curr_sym, _ = resolve_global_symbol_info(symbol)
    df_pair = fetch_relative_spy_comparison(clean_sym)
    if df_pair.empty or clean_sym not in df_pair.columns or 'SPY' not in df_pair.columns:
        st.warning(f"⚠️ 暫時未能取得 {clean_sym} 與 SPY 的走勢對比數據。")
        return

    s_target = df_pair[clean_sym].dropna()
    s_spy = df_pair['SPY'].dropna()
    common_idx = s_target.index.intersection(s_spy.index)
    if len(common_idx) < 30:
        st.warning("⚠️ 共同交易日不足，無法計算對比。")
        return

    ret_target = ((s_target.loc[common_idx] / s_target.loc[common_idx].iloc[0]) - 1) * 100
    ret_spy = ((s_spy.loc[common_idx] / s_spy.loc[common_idx].iloc[0]) - 1) * 100
    alpha_spread = ret_target - ret_spy

    cur_alpha = alpha_spread.iloc[-1]
    alpha_1m = alpha_spread.iloc[-1] - (alpha_spread.iloc[-22] if len(alpha_spread) >= 22 else alpha_spread.iloc[0])

    c_m1, c_m2, c_m3 = st.columns(3)
    with c_m1:
        st.metric(f"{symbol_display} 累計回報", f"{ret_target.iloc[-1]:+.1f}%")
    with c_m2:
        st.metric("標普 500 (SPY) 累計回報", f"{ret_spy.iloc[-1]:+.1f}%")
    with c_m3:
        alpha_color = "normal" if cur_alpha >= 0 else "inverse"
        st.metric("累積超額收益 (Alpha vs SPY)", f"{cur_alpha:+.1f}%", delta=f"近月變化 {alpha_1m:+.1f}%", delta_color=alpha_color)

    fig_alpha = go.Figure()
    fig_alpha.add_trace(go.Scatter(x=common_idx, y=ret_target, mode='lines', name=f"{symbol_display} 累計回報", line=dict(color='#38bdf8', width=2.4)))
    fig_alpha.add_trace(go.Scatter(x=common_idx, y=ret_spy, mode='lines', name="標普 500 (SPY 基準)", line=dict(color='#94a3b8', width=1.8, dash='dash')))
    fig_alpha.add_trace(go.Scatter(x=common_idx, y=alpha_spread, mode='lines', name="超額收益 Alpha (相對強弱)", line=dict(color='#00ff88' if cur_alpha >= 0 else '#f43f5e', width=1.5), fill='tozeroy', fillcolor='rgba(0, 255, 136, 0.12)' if cur_alpha >= 0 else 'rgba(244, 63, 94, 0.12)'))
    fig_alpha.add_hline(y=0, line_dash="solid", line_color="#475569", line_width=1)
    fig_alpha.update_layout(
        template='plotly_dark', paper_bgcolor='#0a0e14', plot_bgcolor='#0a0e14', height=380, margin=dict(l=15, r=20, t=25, b=15), hovermode='x unified',
        legend=dict(font=dict(color='#f1f5f9', size=11), bgcolor='rgba(15, 23, 42, 0.75)', orientation="h", yanchor="bottom", y=1.02, xanchor="right", x=1),
        yaxis=dict(title=dict(text="累計收益率 / 超額 Alpha (%)", font=dict(color='#f8fafc', size=12)), tickfont=dict(color='#cbd5e1', size=11), showgrid=True, gridcolor='rgba(71, 85, 105, 0.35)'),
        xaxis=dict(tickfont=dict(color='#cbd5e1', size=11), showgrid=True, gridcolor='rgba(71, 85, 105, 0.35)')
    )
    st.plotly_chart(fig_alpha, use_container_width=True)


# =========================================================================
# 📋 分頁 4：04 全部 ETF (34 大主題萬能搜尋大看板)
# =========================================================================
def render_tab_04_all_etf():
    st.markdown("#### 📋 34 大主題 ETF 全景成分庫與萬能搜尋")
    c_s1, c_s2 = st.columns([3, 2])
    with c_s1:
        search_kw = st.text_input("🔍 搜尋主題關鍵字或成分股：", placeholder="輸入 MA, MS, NVDA, 晶片, 醫療, 防禦, 比特幣, 金融...").strip().upper()
    with c_s2:
        all_types = ["全部類型"] + sorted(list(set(v['type'] for v in GANN05_SECTOR_CONFIG.values())))
        sel_type = st.selectbox("📂 按板塊類型篩選：", all_types)

    rows = []
    for k, v in GANN05_SECTOR_CONFIG.items():
        extra_comps = SECTOR_COMPONENTS_ENRICHED.get(k, "")
        full_sub_str = f"{v['display_sub']} / {extra_comps}" if extra_comps else v['display_sub']
        match_type = (sel_type == "全部類型") or (v['type'] == sel_type) or (bool(search_kw))
        match_kw = True
        if search_kw:
            target_str = f"{k} {v['type']} {v['anchor']} {full_sub_str}".upper()
            if re.match(r'^[A-Z0-9\.\-]+$', search_kw):
                pattern = rf'(?<![A-Z0-9]){re.escape(search_kw)}(?![A-Z0-9])'
                match_kw = bool(re.search(pattern, target_str))
            else:
                match_kw = (search_kw in target_str)

        if match_type and match_kw:
            rows.append({"板塊名稱": k, "類型分類": v['type'], "錨定核心代碼": v['anchor'], "代表組群與涵蓋成分": full_sub_str})

    st.markdown(f"<div style='font-size:13px; color:#38bdf8; font-weight:600; margin-bottom:8px;'>共篩選出 {len(rows)} 個相關主題板塊：</div>", unsafe_allow_html=True)
    df_show = pd.DataFrame(rows)

    if not df_show.empty:
        etf_table_height = (len(df_show) + 1) * 38 + 45
        st.dataframe(df_show, use_container_width=True, hide_index=True, height=etf_table_height)
        sel_direct = st.selectbox("選取要檢視的板塊：", df_show['板塊名稱'].tolist())
        if st.button(f"👉 立即載入「{sel_direct}」5 年回歸通道", type="primary"):
            st.session_state['gann05_jump_target'] = sel_direct
            st.rerun()


# =========================================================================
# 🚀 核心渲染入口：render_page_gann05
# =========================================================================
def render_page_gann05():
    inject_gann05_css()

    all_sectors = list(GANN05_SECTOR_CONFIG.keys())

    if st.session_state.get('gann05_jump_target'):
        target_jump = st.session_state.pop('gann05_jump_target')
        st.session_state['gann05_sector_select'] = target_jump
        st.session_state['gann05_custom_ticker'] = ""

    if 'gann05_sector_select' not in st.session_state or st.session_state['gann05_sector_select'] not in all_sectors:
        st.session_state['gann05_sector_select'] = '金融 (XLF)'
    if 'gann05_time_window' not in st.session_state:
        st.session_state['gann05_time_window'] = '1W'
    if 'gann05_custom_ticker' not in st.session_state:
        st.session_state['gann05_custom_ticker'] = ""
    if 'gann05_strat_mode' not in st.session_state:
        st.session_state['gann05_strat_mode'] = '經典波段 (原版)'
    if 'gann05_interval' not in st.session_state:
        st.session_state['gann05_interval'] = '1wk'
    if 'gann05_show_recent_vpvr' not in st.session_state:
        st.session_state['gann05_show_recent_vpvr'] = True
    if 'gann05_show_hist_vpvr' not in st.session_state:
        st.session_state['gann05_show_hist_vpvr'] = True
    if 'gann05_show_tw' not in st.session_state:
        st.session_state['gann05_show_tw'] = True

    t1, t2, t3, t4 = st.tabs(["01 市場總覽", "02 板塊輪動", "⭐ 03 圖表與資金", "04 全部 ETF"])

    with t1:
        render_tab_01_market_overview()
    with t2:
        render_tab_02_sector_rotation()

    # -------------------------------------------------------------
    # 🌟 分頁 3：圖表與資金 (單行極簡工具列 ＋ 全球自適應 ＋ 雙層獨立 VPVR)
    # -------------------------------------------------------------
    with t3:
        current_active = st.session_state['gann05_custom_ticker'] if st.session_state['gann05_custom_ticker'] else GANN05_SECTOR_CONFIG[st.session_state['gann05_sector_select']]['anchor']
        resolved_sym, curr_sym, market_label = resolve_global_symbol_info(current_active)

        # 🌟 1. 全域單行極簡看盤工具列 (輸入框 + 核心標的快速選單 + 刷新按鈕)
        col_search, col_select, col_tf, col_refresh = st.columns([4.2, 3.2, 1.6, 1.0])

        with col_search:
            raw_in = st.text_input(
                "自訂資產代碼 (Gann 05)",
                value=st.session_state['gann05_custom_ticker'],
                placeholder="輸入代碼 (例: 0005, 700, NVDA, SPY, 1321.T, 600519)...",
                label_visibility="collapsed",
                key=f"g05_txt_input_{st.session_state['gann05_custom_ticker']}"
            ).strip().upper()

            if raw_in:
                norm_sym, _, _ = resolve_global_symbol_info(raw_in)
                if norm_sym != st.session_state['gann05_custom_ticker']:
                    st.session_state['gann05_custom_ticker'] = norm_sym
                    st.rerun()

        with col_select:
            preset_options = [
                f"📌 常用核心標的快速選取 ({resolved_sym})",
                "🇺🇸 SPY (標普500 ETF)",
                "🇺🇸 QQQ (納指100 ETF)",
                "🇺🇸 NVDA (輝達)",
                "🇺🇸 TSLA (特斯拉)",
                "🇭🇰 2800.HK (盈富基金)",
                "🇭🇰 0700.HK (騰訊控股)",
                "🇭🇰 0005.HK (匯豐控股)",
                "🇭🇰 3033.HK (恒生科技ETF)",
                "🇯🇵 1321.T (日經225 ETF)",
                "🇯🇵 7203.T (豐田汽車)",
                "🇰🇷 069500.KS (KODEX200 ETF)",
                "🇰🇷 005930.KS (三星電子)",
                "🇨🇳 510300.SS (滬深300 ETF)",
                "🇨🇳 600519.SS (貴州茅台)",
                "🇨🇳 159919.SZ (嘉實300 ETF)"
            ]
            sel_val = st.selectbox(
                "快捷選擇 (Gann 05)",
                preset_options,
                index=0,
                label_visibility="collapsed",
                key=f"g05_sel_{resolved_sym}"
            )
            if sel_val and not sel_val.startswith("📌"):
                chosen_ticker = sel_val.split()[1]
                norm_sym, _, _ = resolve_global_symbol_info(chosen_ticker)
                if norm_sym != st.session_state['gann05_custom_ticker']:
                    st.session_state['gann05_custom_ticker'] = norm_sym
                    st.rerun()

        with col_tf:
            c_d, c_w = st.columns(2)
            with c_d:
                if st.button("日線", type="primary" if st.session_state['gann05_interval'] == '1d' else "secondary", use_container_width=True, key="g05_btn_tf_d"):
                    st.session_state['gann05_interval'] = '1d'
                    st.rerun()
            with c_w:
                if st.button("週線", type="primary" if st.session_state['gann05_interval'] == '1wk' else "secondary", use_container_width=True, key="g05_btn_tf_w"):
                    st.session_state['gann05_interval'] = '1wk'
                    st.rerun()

        with col_refresh:
            if st.session_state['gann05_custom_ticker']:
                if st.button("🔄 板塊", help="清空自訂代碼，返回預設板塊", use_container_width=True, key="g05_btn_reset_sec"):
                    st.session_state['gann05_custom_ticker'] = ""
                    st.rerun()
            else:
                if st.button("🔄", help="刷新實盤行情", use_container_width=True, key="g05_btn_refresh_now"):
                    st.rerun()

        # 🌟 2. 緊隨其後的收放指南表 (預設收合，約 28px)
        render_global_guide_expander_g05()

        active_custom = st.session_state['gann05_custom_ticker']
        if active_custom:
            sec_name = f"🌟 自訂資產: {active_custom}"
            anchor_ticker = active_custom
            badge_text = f"自訂查詢: {anchor_ticker} ({market_label})"
        else:
            sec_name = st.session_state['gann05_sector_select']
            sec_cfg = GANN05_SECTOR_CONFIG.get(sec_name, GANN05_SECTOR_CONFIG['金融 (XLF)'])
            anchor_ticker = sec_cfg['anchor']
            badge_text = f"錨定標的: {anchor_ticker}"

        act_interval = st.session_state['gann05_interval']
        interval_title = "週線" if act_interval == "1wk" else "日線"

        with st.spinner(f"加載 {anchor_ticker} {interval_title}回歸與成交量數據..."):
            df_hist = fetch_gann05_data(anchor_ticker, interval=act_interval)
            metrics, data_calc = compute_regression_channel_metrics(
                df_hist, strategy_mode=st.session_state['gann05_strat_mode']
            )

        if not metrics:
            st.warning(f"⚠️ 暫時未能取得代號 '{anchor_ticker}' 的歷史數據，請確認代碼是否正確。")
        else:
            # 宏觀回歸指標統計卡片
            st.markdown(f"""
            <div class="gann05-header-box">
                <div style="display:flex; justify-content:space-between; align-items:center; flex-wrap:wrap;">
                    <div>
                        <span style="font-size:18px; font-weight:bold; color:#f8fafc;">{sec_name} ({interval_title})</span>
                        <span style="margin-left:8px; font-size:12px; font-weight:600; color:#38bdf8; background:#0f172a; padding:3px 9px; border-radius:4px; border:1px solid #334155;">
                            {badge_text}
                        </span>
                    </div>
                    <div style="font-size:22px; font-weight:bold; color:#00ff88;">
                        {curr_sym}{metrics['current_price']:,.2f}
                        <span style="font-size:12px; color:#cbd5e1; font-weight:normal;">(回歸中線: {curr_sym}{metrics['center_price']:,.2f})</span>
                    </div>
                </div>
                <div style="display:grid; grid-template-columns: repeat(5, 1fr); gap:8px; margin-top:10px;">
                    <div class="gann05-stat-card"><div style="font-size:11px; color:#cbd5e1;">一週回報</div><div style="font-size:13px; font-weight:bold; color:{'#00ff88' if metrics['chg_1w']>=0 else '#ff3366'};">{metrics['chg_1w']:+.1f}%</div></div>
                    <div class="gann05-stat-card"><div style="font-size:11px; color:#cbd5e1;">一月回報</div><div style="font-size:13px; font-weight:bold; color:{'#00ff88' if metrics['chg_1m']>=0 else '#ff3366'};">{metrics['chg_1m']:+.1f}%</div></div>
                    <div class="gann05-stat-card"><div style="font-size:11px; color:#cbd5e1;">三月回報</div><div style="font-size:13px; font-weight:bold; color:{'#00ff88' if metrics['chg_3m']>=0 else '#ff3366'};">{metrics['chg_3m']:+.1f}%</div></div>
                    <div class="gann05-stat-card"><div style="font-size:11px; color:#cbd5e1;">年初至今 YTD</div><div style="font-size:13px; font-weight:bold; color:{'#00ff88' if metrics['chg_ytd']>=0 else '#ff3366'};">{metrics['chg_ytd']:+.1f}%</div></div>
                    <div class="gann05-stat-card"><div style="font-size:11px; color:#cbd5e1;">趨勢狀態</div><div style="font-size:12px; font-weight:bold; color:#f59e0b;">{metrics['trend_status']}</div></div>
                </div>
            </div>
            """, unsafe_allow_html=True)

            # 控制列：指標數據 ＋ [📊 近期籌碼] + [🟣 歷史籌碼] ＋ 窗口開關 ＋ 訊號 ＋ 雙軌策略
            c_ctrl1, c_vpvr1, c_vpvr2, c_tw, c_sig, c_strat = st.columns([1.8, 0.8, 0.8, 0.7, 0.6, 1.4])
            with c_ctrl1:
                st.markdown(f"""
                <div style="font-size:11.5px; color:#f1f5f9; padding-top:4px;">
                    🟣 <b>回歸通道</b> · R² <b>{metrics['r_squared']:.2f}</b> · 斜率 <b>{metrics['slope_pct']:+.2f}%</b> · 距中線 <b>{metrics['dist_center_pct']:+.1f}%</b>
                </div>
                """, unsafe_allow_html=True)

            with c_vpvr1:
                is_rv = st.session_state['gann05_show_recent_vpvr']
                if st.button("📊 近期籌碼" if is_rv else "近期 (關)", key="g05_btn_rvpvr", type="primary" if is_rv else "secondary", use_container_width=True):
                    st.session_state['gann05_show_recent_vpvr'] = not is_rv
                    st.rerun()

            with c_vpvr2:
                is_hv = st.session_state['gann05_show_hist_vpvr']
                if st.button("🟣 歷史籌碼" if is_hv else "歷史 (關)", key="g05_btn_hvpvr", type="primary" if is_hv else "secondary", use_container_width=True):
                    st.session_state['gann05_show_hist_vpvr'] = not is_hv
                    st.rerun()

            with c_tw:
                is_t = st.session_state['gann05_show_tw']
                if st.button("⏳ 窗口" if is_t else "窗口 (關)", key="g05_btn_tw_toggle", type="primary" if is_t else "secondary", use_container_width=True):
                    st.session_state['gann05_show_tw'] = not is_t
                    st.rerun()

            with c_sig:
                show_signals = st.checkbox("訊號", value=True, key="gann05_chk_sig")

            with c_strat:
                strat_mode = st.radio(
                    "策略模式", ["經典波段 (原版)", "趨勢跟蹤 (防賣飛)"],
                    index=0 if st.session_state['gann05_strat_mode'] == '經典波段 (原版)' else 1,
                    horizontal=True, label_visibility="collapsed"
                )
                if strat_mode != st.session_state['gann05_strat_mode']:
                    st.session_state['gann05_strat_mode'] = strat_mode
                    st.rerun()

            # K 線縮放拉桿
            total_data_bars = len(data_calc)
            min_zoom_bars = min(20, total_data_bars)
            slider_key_g05 = f"gann05_zoom_{anchor_ticker}_{act_interval}"
            if slider_key_g05 not in st.session_state:
                st.session_state[slider_key_g05] = total_data_bars

            zoom_bars = st.slider(
                "K線縮放拉桿",
                min_value=min_zoom_bars,
                max_value=total_data_bars,
                value=min(total_data_bars, max(min_zoom_bars, st.session_state[slider_key_g05])),
                step=5 if act_interval == "1d" else 2,
                key=slider_key_g05,
                help="向左拉動減小根數，即可放大 K 線展示視野"
            )

            data_sliced = data_calc.tail(zoom_bars).copy()

            # 100% 滿版巨幕主圖 (雙層獨立 VPVR ＋ 自適應 Y 軸)
            fig_reg = render_regression_plotly_chart(
                data=data_sliced, metrics=metrics, symbol_name=sec_name,
                show_signals=show_signals,
                show_recent_vpvr=st.session_state['gann05_show_recent_vpvr'],
                show_hist_vpvr=st.session_state['gann05_show_hist_vpvr'],
                show_timewindows=st.session_state['gann05_show_tw'],
                interval=act_interval,
                df_full=df_hist,
                curr_sym=curr_sym
            )
            st.plotly_chart(fig_reg, use_container_width=True)

            # 未來時間窗口動態推算卡片 (依真實時差推算)
            if st.session_state['gann05_show_tw']:
                now_dt = datetime.now()
                target_windows = [
                    {"label": "躍浪峰值窗口", "center": datetime(2026, 11, 26), "desc": "2026-11-23 ～ 11-27", "action": "逢高減倉", "color": "#f59e0b"},
                    {"label": "尋底過渡窗口", "center": datetime(2026, 12, 11), "desc": "2026-12-08 ～ 12-14", "action": "防回踩整理", "color": "#a855f7"},
                    {"label": "週期谷底窗口", "center": datetime(2026, 12, 29), "desc": "2026-12-25 ～ 01-01", "action": "逢低佈局", "color": "#10b981"},
                ]

                cards_html = []
                for tw in target_windows:
                    delta_days = (tw['center'] - now_dt).days
                    if act_interval == '1wk':
                        delta_bars = max(0, delta_days // 7)
                        bar_unit = "週 (bars)"
                    else:
                        delta_bars = max(0, int(delta_days * (5 / 7)))
                        bar_unit = "日 (bars)"

                    time_status = f"約 {delta_bars} {bar_unit} · {tw['action']}" if delta_days > 0 else f"已過期 · {tw['action']}"

                    cards_html.append(f"""
                    <div class="gann05-countdown-card" style="border: 1px solid {tw['color']};">
                        <div>
                            <div style="color:{tw['color']}; font-weight:bold; font-size:12.5px;">{tw['label']}</div>
                            <div style="color:#cbd5e1; font-size:11px; margin-top:2px;">{tw['desc']}</div>
                        </div>
                        <div style="background:#1e293b; color:{tw['color']}; font-weight:bold; padding:3px 8px; border-radius:4px; font-size:11.5px;">
                            {time_status}
                        </div>
                    </div>
                    """)

                st.markdown(f"""
                <div style="display:grid; grid-template-columns: repeat(3, 1fr); gap:10px; margin: 8px 0 16px 0;">
                    {''.join(cards_html)}
                </div>
                """, unsafe_allow_html=True)

            # 單標的每週價量壓力趨勢 (最近 26 週淨買賣流向 + 4W/13W累計)
            flow_metrics, df_flow = compute_weekly_flow_pressure(df_hist, n_weeks=26)
            if not df_flow.empty:
                fig_flow = render_weekly_flow_chart(df_flow, flow_metrics, symbol_name=sec_name)
                st.plotly_chart(fig_flow, use_container_width=True)

        # -------------------------------------------------------------
        # 34 板塊主力資金壓力與推動強度排行榜
        # -------------------------------------------------------------
        st.markdown("---")
        st.markdown("#### 🎯 華爾街主力資金 · 34 板塊價量壓力與推動強度排行榜")

        bar_col1, bar_col2 = st.columns([1.5, 3.5])
        with bar_col1:
            win_c1, win_c2 = st.columns(2)
            with win_c1:
                if st.button("最近一週", use_container_width=True,
                             type="primary" if st.session_state['gann05_time_window'] == '1W' else "secondary", key="g05_btn_win_1w"):
                    st.session_state['gann05_time_window'] = '1W'
                    st.rerun()
            with win_c2:
                if st.button("近 4 週", use_container_width=True,
                             type="primary" if st.session_state['gann05_time_window'] == '4W' else "secondary", key="g05_btn_win_4w"):
                    st.session_state['gann05_time_window'] = '4W'
                    st.rerun()

        with bar_col2:
            curr_pos = all_sectors.index(st.session_state['gann05_sector_select']) if st.session_state['gann05_sector_select'] in all_sectors else 0
            new_selected = st.selectbox("🎯 快速切換 34 板塊主圖：", options=all_sectors, index=curr_pos, label_visibility="collapsed", key="g05_sel_sector_leaderboard")
            if new_selected != st.session_state['gann05_sector_select']:
                st.session_state['gann05_sector_select'] = new_selected
                st.session_state['gann05_custom_ticker'] = ""
                st.rerun()

        with st.spinner("抓取 34 板塊並計算資金壓力與推動強度..."):
            df_all = fetch_sector_flow_data()
            top_buy, top_sell, all_df = compute_34_sector_leaderboard(
                df_all, time_window=st.session_state['gann05_time_window']
            )

        col_buy, col_sell = st.columns(2)

        with col_buy:
            st.markdown("<div style='font-size:14px; font-weight:bold; color:#00ff88; margin-bottom:8px;'>📈 Top 5 買入壓力 (強勢吸籌)</div>", unsafe_allow_html=True)
            if not top_buy.empty:
                max_buy = top_buy['資金壓力_B'].max() if top_buy['資金壓力_B'].max() > 0 else 1.0
                for idx, row in top_buy.iterrows():
                    pct = min(100, int((row['資金壓力_B'] / max_buy) * 100))
                    mom_pct = row.get('推動強度_%', 0.0)
                    mom_text = f" · 推動強度: <b>{mom_pct:+.1f}%</b>" if mom_pct != 0 else ""
                    st.markdown(f"""
                    <div style="background: rgba(15, 23, 42, 0.75); border: 1px solid #334155; border-radius: 6px; padding: 8px 12px; margin-bottom: 8px;">
                        <div style="display:flex; justify-content:space-between; font-size:13px;">
                            <span style="color:#f8fafc; font-weight:600;">{idx+1}. {row['板塊名稱']}</span>
                            <span style="color:#00ff88; font-weight:bold;">+${row['資金壓力_B']:.1f}B</span>
                        </div>
                        <div style="font-size:11px; color:#cbd5e1; margin-top:3px;">代表標的: {row['代表標的']}{mom_text}</div>
                        <div class="gann05-bar-bg"><div style="background:#00ff88; width:{pct}%; height:100%;"></div></div>
                    </div>
                    """, unsafe_allow_html=True)

        with col_sell:
            st.markdown("<div style='font-size:14px; font-weight:bold; color:#f43f5e; margin-bottom:8px;'>📉 Top 5 賣出壓力 (資金派發)</div>", unsafe_allow_html=True)
            if not top_sell.empty:
                max_sell = abs(top_sell['資金壓力_B'].min()) if abs(top_sell['資金壓力_B'].min()) > 0 else 1.0
                for idx, row in top_sell.iterrows():
                    pct = min(100, int((abs(row['資金壓力_B']) / max_sell) * 100))
                    mom_pct = row.get('推動強度_%', 0.0)
                    mom_text = f" · 推動強度: <b>{mom_pct:+.1f}%</b>" if mom_pct != 0 else ""
                    st.markdown(f"""
                    <div style="background: rgba(15, 23, 42, 0.75); border: 1px solid #334155; border-radius: 6px; padding: 8px 12px; margin-bottom: 8px;">
                        <div style="display:flex; justify-content:space-between; font-size:13px;">
                            <span style="color:#f8fafc; font-weight:600;">{idx+1}. {row['板塊名稱']}</span>
                            <span style="color:#f43f5e; font-weight:bold;">-${abs(row['資金壓力_B']):.1f}B</span>
                        </div>
                        <div style="font-size:11px; color:#cbd5e1; margin-top:3px;">代表標的: {row['代表標的']}{mom_text}</div>
                        <div class="gann05-bar-bg"><div style="background:#f43f5e; width:{pct}%; height:100%;"></div></div>
                    </div>
                    """, unsafe_allow_html=True)

        with st.expander("▶ 每週資金與價量壓力 展開分析 (34 板塊總榜單)", expanded=False):
            if not all_df.empty:
                st.dataframe(all_df.sort_values(by='資金壓力_B', ascending=False), use_container_width=True, hide_index=True)

        with st.expander("▶ 板塊強弱比較 對比 SPY 相對回報", expanded=False):
            st.markdown(f"##### 🎯 {sec_name} vs 標普 500 (SPY) 兩年期相對走勢與超額 Alpha")
            render_spy_relative_return_chart(anchor_ticker, sec_name)

    # -------------------------------------------------------------
    # 分頁 4：全部 ETF
    # -------------------------------------------------------------
    with t4:
        render_tab_04_all_etf()

if __name__ == "__main__":
    render_page_gann05()