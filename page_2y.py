"""
Filename: page_2y.py
Description: 🌌 艙房 2y : 華爾街宏觀上帝視角與全球資產戰略終端 (64 大板塊全息旗艦 · 工業級防崩終極加固版)
- 🩸 【聰明錢三大宏觀脈搏心電圖】(HYG/TLT 信貸, COPX/GLD 實體, BTC/GLD 流動性, VIX - 獨立容錯防崩)
- 🚦 【A.I. 戰略指揮燈】(Regime Indicator 風險狀態即時識別 - 帶安全除法防護)
- 👑 【兩層 MISE 市寬上帝視角】(S&P 1500 真實底層市寬 ＋ 熱錢精英視角 ＋ 維基百科 5 秒超時自動降級)
- 🎡 【全球 64 大板塊同台大混戰】(展區一 8大狀態速查指南純白字 ＋ RRG 星盤 ＋ Treemap ＋ 無限長明細表)
- 🦅 【大鱷跨資產預警星盤】(以 TLT 國債為基準的 2026 終極生死共振)
- 🧠 【4升 vs 4跌：8大趨勢感知 RRG 狀態引擎】
- 🛡️ 【全方位防崩加固】：
  * 脈搏卡片逐一隔離校驗，單一數據源缺失不引發白屏
  * 維基百科抓取設定 timeout=5，網路逾時自動降級
  * 去除時間戳重複項、時區精準純化
  * 柱狀圖橫軸 b=220px 空間充裕，單行垂直排開絕不重疊
  * 詳細數據表徹底解鎖 600px 限制，自然平鋪縱向展開
"""

import streamlit as st
import yfinance as yf
import pandas as pd
import numpy as np
import plotly.graph_objects as go
import plotly.express as px
from plotly.subplots import make_subplots
from datetime import datetime, timedelta
import urllib.request
import re

# =========================================================================
# 🏛️ 1. 完整板塊資料庫定義 (全部 64 大板塊具備標準英文字代號)
# =========================================================================

MACRO_SECTORS = {
    'XLK': '科技 (XLK)', 'XLF': '金融 (XLF)', 'XLV': '醫療保健 (XLV)',
    'XLE': '能源 (XLE)', 'XLY': '非必需消費 (XLY)', 'XLP': '必需消費 (XLP)',
    'XLI': '工業 (XLI)', 'XLU': '公用事業 (XLU)', 'XLB': '原材料 (XLB)',
    'XLRE': '房地產 (XLRE)', 'XLC': '通訊服務 (XLC)'
}

FRONTIER_SECTORS = {
    # --- 1. AI 算力、硬體與半導體鏈 ---
    '🧠 GPU / AI 核心算力 (SMH)': {
        'etfs': ['SMH', 'SOXX', 'USD'],
        'tickers': ['NVDA', 'TSM', 'AVGO', 'AMD', 'ARM', 'QCOM', 'MRVL', 'INTC']
    },
    '💻 CPU / 通用晶片處理器 (SOXX)': {
        'etfs': ['SOXX', 'XSD'],
        'tickers': ['AMD', 'INTC', 'ARM', 'QCOM', 'AAPL', 'TXN', 'ADI', 'MCHP']
    },
    '💾 DRAM / 記憶體與存儲 (CHPX)': {
        'etfs': ['CHPX'],
        'tickers': ['MU', 'WDC', 'STX', 'PSTG', 'NTAP']
    },
    '🔬 先進封裝與晶片製造設備 (AMAT)': {
        'etfs': ['SMH', 'SOXX'],
        'tickers': ['ASML', 'AMAT', 'LRCX', 'KLAC', 'ONTO', 'CAMT', 'ICHR', 'UCTT', 'ACLS', 'FORM']
    },
    '⚡ 光模組、CPO 與光通信 (FOTO)': {
        'etfs': ['FOTO'],
        'tickers': ['COHR', 'AAOI', 'FN', 'LITE', 'CIEN', 'CRDO', 'ALAB', 'MTSI', 'POET', 'GLW']
    },
    '🏭 AI 伺服器與硬體系統 (SMCI)': {
        'etfs': [],
        'tickers': ['SMCI', 'DELL', 'HPE', 'ANET', 'PSTG', 'VRT', 'CDNS', 'SNPS']
    },
    '❄️ AI 液冷散熱與電源管理 (VRT)': {
        'etfs': ['XLU', 'GRID'],
        'tickers': ['VRT', 'MOD', 'GEV', 'CAT', 'CMI', 'CEG', 'VST', 'NVT']
    },
    '⚡ 變壓器與電網升級基建 (GRID)': {
        'etfs': ['GRID', 'PAVE'],
        'tickers': ['PWR', 'ETN', 'HUBB', 'ABB', 'EME', 'MYRG', 'GEV']
    },
    '📱 Edge AI / 端側晶片終端 (QCOM)': {
        'etfs': [],
        'tickers': ['QCOM', 'AAPL', 'AVGO', 'SWKS', 'QRVO', 'LOGI', 'NXPI']
    },
    '🏢 數據中心與雲基建 (SRVR)': {
        'etfs': ['SRVR', 'DTCR'],
        'tickers': ['EQIX', 'DLR', 'AMT', 'CCI', 'GDS', 'COR', 'VRT']
    },

    # --- 2. 軟體、SaaS 與網絡安全 ---
    '🧠 LLM 大模型與 AI 科技巨頭 (AIQ)': {
        'etfs': ['AIQ', 'BOTZ', 'THNQ'],
        'tickers': ['MSFT', 'GOOGL', 'AMZN', 'META', 'ORCL', 'AAPL', 'PLTR']
    },
    '🛡️ 網絡安全與零信任 (CIBR)': {
        'etfs': ['CIBR', 'HACK', 'BUG'],
        'tickers': ['CRWD', 'PANW', 'ZS', 'FTNT', 'NET', 'CYBR', 'OKTA', 'CHKP', 'S']
    },
    '☁️ 雲計算與企業級 SaaS (IGV)': {
        'etfs': ['IGV', 'WCLD', 'CLOU'],
        'tickers': ['CRM', 'ADBE', 'NOW', 'WDAY', 'SNOW', 'DDOG', 'MDB', 'TEAM', 'PLTR', 'HUBS']
    },
    '💳 金融科技與數字支付 (FINX)': {
        'etfs': ['FINX', 'IPAY'],
        'tickers': ['V', 'MA', 'PYPL', 'SQ', 'HOOD', 'AFRM', 'SOFI', 'TOST', 'FIS', 'GPN']
    },
    '🛠️ 基礎設施軟體與 DevOps (HCP)': {
        'etfs': ['IGV'],
        'tickers': ['GTLB', 'HCP', 'ESTC', 'CFLT', 'MDB', 'DT', 'FSLY']
    },

    # --- 3. 前沿科技、機器人與空天出行 ---
    '🦾 機械人與智慧自動化 (BOTZ)': {
        'etfs': ['BOTZ', 'ROBO', 'IRBO'],
        'tickers': ['TSLA', 'ISRG', 'PATH', 'SYM', 'TER', 'ROK', 'NVDA']
    },
    '🚗 自動駕駛與 Robotaxi (IDRV)': {
        'etfs': ['IDRV', 'DRIV', 'HAIL'],
        'tickers': ['TSLA', 'GOOGL', 'MBLY', 'UBER', 'HSAI', 'AUR', 'LAZR', 'INVZ']
    },
    '🚁 低空飛行與 eVTOL 空運 (JOBY)': {
        'etfs': [],
        'tickers': ['JOBY', 'ACHR', 'EH', 'AUR', 'BLDE', 'EVTL']
    },
    '🌌 量子計算 (QTUM)': {
        'etfs': ['QTUM'],
        'tickers': ['IONQ', 'RGTI', 'QBTS', 'QUBT', 'ARQQ', 'HON', 'IBM', 'GOOGL', 'MSFT']
    },
    '🚀 商業太空與低軌通訊 (UFO)': {
        'etfs': ['UFO', 'ROKT', 'ARKX'],
        'tickers': ['RKLB', 'ASTS', 'LUNR', 'BKSY', 'PL', 'RDWR', 'SPCE', 'MNTS', 'VSAT', 'IRDM']
    },
    '🚀 顛覆性創新霸權 (ARKK)': {
        'etfs': ['ARKK', 'ARKW', 'ARKG', 'ARKF', 'ARKX'],
        'tickers': ['TSLA', 'ROKU', 'COIN', 'PLTR', 'U', 'PATH', 'CRSP']
    },

    # --- 4. 生技醫藥與前沿生命健康 ---
    '🧬 高彈性創新型生技 (XBI)': {
        'etfs': ['XBI', 'IBB', 'ARKG'],
        'tickers': ['MRNA', 'BNTX', 'CRSP', 'VRTX', 'REGN', 'ILMN', 'BIIB', 'ALNY']
    },
    '💉 減肥藥與 GLP-1 產業鏈 (LLY)': {
        'etfs': ['XLV'],
        'tickers': ['LLY', 'NVO', 'VKTX', 'ALT', 'GPCR', 'RVNC', 'TERN', 'AMGN', 'PFE']
    },
    '🩺 醫療器械與精準外科 (IHI)': {
        'etfs': ['IHI', 'ARKG'],
        'tickers': ['ISRG', 'SYK', 'BSX', 'MDT', 'EW', 'ABT', 'DXCM', 'TMO']
    },
    '🧠 腦機介面與仿生神經 (BSX)': {
        'etfs': [],
        'tickers': ['SYNA', 'TNDM', 'DXCM', 'INMD', 'NVRO', 'PRVA', 'BSX', 'MDT']
    },
    '🏥 醫療健康保險與服務 (IHF)': {
        'etfs': ['IHF'],
        'tickers': ['UNH', 'ELV', 'CI', 'CVS', 'HUM', 'CNC']
    },

    # --- 5. 能源變革、核能與關鍵金屬資源 ---
    '⚛️ 核能、SMR 與鈾礦 (URA)': {
        'etfs': ['URA', 'URNM', 'NLR'],
        'tickers': ['CCJ', 'OKLO', 'SMR', 'LEU', 'UUUU', 'CEG', 'VST', 'BWXT']
    },
    '☀️ 清潔能源與太陽能 (ICLN)': {
        'etfs': ['ICLN', 'TAN', 'QCLN'],
        'tickers': ['FSLR', 'ENPH', 'SEDG', 'RUN', 'PLUG', 'NEE', 'CSIQ', 'BE']
    },
    '🔋 電動車與鋰電池鏈 (LIT)': {
        'etfs': ['LIT', 'DRIV', 'IDRV'],
        'tickers': ['TSLA', 'ALB', 'SQM', 'QS', 'FREY', 'ON', 'RIVN', 'LCID']
    },
    '🥇 金礦開採與貴金屬 (GDX)': {
        'etfs': ['GDX', 'GDXJ', 'RING'],
        'tickers': ['NEM', 'GOLD', 'AEM', 'KGC', 'AUY', 'AU', 'HMY']
    },
    '🥈 銀礦開採 (SIL)': {
        'etfs': ['SIL', 'SILJ'],
        'tickers': ['AG', 'PAAS', 'HL', 'CDE', 'FSM', 'MAG']
    },
    '🥉 銅礦與關鍵工業金屬 (COPX)': {
        'etfs': ['COPX', 'CPER', 'PICK'],
        'tickers': ['FCX', 'SCCO', 'ERO', 'TECK', 'HBM', 'BHP', 'RIO']
    },
    '🛢️ 石油開採與油服設備 (OIH)': {
        'etfs': ['OIH', 'XOP'],
        'tickers': ['SLB', 'HAL', 'BKR', 'EOG', 'OXY', 'FANG', 'DVN', 'COP']
    },
    '🧪 特種材料與稀土資源 (REMX)': {
        'etfs': ['REMX', 'LIT'],
        'tickers': ['MP', 'ALB', 'LIN', 'APD', 'SHW', 'ECL']
    },

    # --- 6. 地緣防務、特種產業與經濟民生 ---
    '⚔️ 國防軍工與尖端航太 (ITA)': {
        'etfs': ['ITA', 'PPA', 'XAR'],
        'tickers': ['LMT', 'RTX', 'NOC', 'GD', 'BA', 'LHX', 'HII', 'TDG', 'AXON']
    },
    '🪙 區塊鏈與比特幣生態 (WGMI)': {
        'etfs': ['WGMI', 'BLOK', 'DAPP', 'IBIT'],
        'tickers': ['COIN', 'MSTR', 'MARA', 'RIOT', 'CLSK', 'HOOD', 'HUT', 'CIFR']
    },
    '🛍️ 電商平台與數位消費 (FDN)': {
        'etfs': ['FDN', 'IBUY'],
        'tickers': ['AMZN', 'MELI', 'BABA', 'PDD', 'SE', 'CHWY', 'DASH', 'SHOP', 'EBAY']
    },
    '🚚 現代交通物流與鐵路 (IYT)': {
        'etfs': ['IYT'],
        'tickers': ['UNP', 'CSX', 'NSC', 'UPS', 'FDX', 'ODFL', 'JBHT']
    },
    '🌾 農業科技與糧食化肥 (MOO)': {
        'etfs': ['MOO'],
        'tickers': ['DE', 'ADM', 'CTVA', 'MOS', 'CF', 'NTR', 'BG']
    },
    '💧 水資源與環境基建 (PHO)': {
        'etfs': ['PHO', 'FIW'],
        'tickers': ['XYL', 'AWK', 'WMS', 'ECL', 'ROP', 'PNR']
    },
    '🎰 數位娛樂與在線遊戲 (HERO)': {
        'etfs': ['HERO', 'BETZ'],
        'tickers': ['RBLX', 'EA', 'TTWO', 'DKNG', 'FLUT', 'NTES']
    },
    '🧲 被動元件與電子連接器 (TEL)': {
        'etfs': [],
        'tickers': ['TEL', 'APH', 'VSH', 'LFUS', 'GLW']
    },
    '🏠 住宅建築與地產營造 (ITB)': {
        'etfs': ['ITB', 'XHB'],
        'tickers': ['DHI', 'LEN', 'NVR', 'PHM', 'TOL', 'HD', 'LOW']
    },
    '✈️ 航空交通與休閒旅遊 (JETS)': {
        'etfs': ['JETS'],
        'tickers': ['DAL', 'UAL', 'AAL', 'LUV', 'CCL', 'RCL', 'NCLH']
    },
    '🛡️ 保險經紀與風險管理 (KIE)': {
        'etfs': ['KIE', 'IAK'],
        'tickers': ['PGR', 'CB', 'TRV', 'ALL', 'AIG', 'AON', 'MMC']
    },
    '🏦 美國區域性商業銀行 (KRE)': {
        'etfs': ['KRE', 'KBE'],
        'tickers': ['TFC', 'PNC', 'USB', 'FITB', 'MTB', 'KEY', 'CFG']
    },
    '🍔 連鎖餐飲與生活消費 (PBJ)': {
        'etfs': ['PBJ'],
        'tickers': ['MCD', 'SBUX', 'CMG', 'YUM', 'DRI', 'QSR', 'WING']
    },
    '🎬 串流媒體與影視娛樂 (SUBZ)': {
        'etfs': ['SUBZ'],
        'tickers': ['NFLX', 'SPOT', 'DIS', 'ROKU', 'WBD']
    },
    '📦 包裝材料與林業資源 (WOOD)': {
        'etfs': ['WOOD'],
        'tickers': ['IP', 'PKG', 'BALL', 'CCK', 'AVY']
    },
    '🚗 傳統汽車製造與配件 (CARZ)': {
        'etfs': ['CARZ'],
        'tickers': ['GM', 'F', 'STLA', 'APTV', 'BWA', 'LEA', 'MGA']
    },
    '🧱 重型基建材料與水泥 (PAVE)': {
        'etfs': ['PAVE'],
        'tickers': ['VMC', 'MLM', 'CRH', 'SUM', 'EXP']
    },
    '💼 企業人力與外包服務 (ADP)': {
        'etfs': [],
        'tickers': ['ADP', 'PAYX', 'ACN', 'IT', 'CTSH', 'EPAM']
    },
    '🔌 類比與電源半導體 (XSD)': {
        'etfs': ['XSD', 'SOXX'],
        'tickers': ['TXN', 'ADI', 'NXPI', 'MCHP', 'ON', 'MPWR']
    }
}

ULTIMATE_SECTORS = {
    '📈 股市總體風險 (SPY)': 'SPY',
    '🗑️ 聰明錢信用風險 (HYG)': 'HYG',
    '🪙 極限流動性 (BTC-USD)': 'BTC-USD',
    '👑 黃金終極避險 (GLD)': 'GLD',
    '🏭 實體基建與通脹 (COPX)': 'COPX',
    '🛍️ 美國消費信心 (XLY)': 'XLY',
    '🧠 AI 算力命脈 (SMH)': 'SMH',
    '⚛️ 核能與終極能源 (URA)': 'URA',
    '⚔️ 地緣政治與軍工 (ITA)': 'ITA'
}

def format_name(full_name):
    return full_name.split(" (")[0]

# =========================================================================
# 頁面主體函式
# =========================================================================
def app():
    st.set_page_config(layout="wide")
    st.title("🌌 艙房 2y : 華爾街宏觀上帝視角與全球資產戰略終端")
    
    with st.expander("📖 點擊展開：雷達信號實戰解讀指南 (How to Trade)", expanded=True):
        st.markdown("### 🎯 1. 尋找「假突破 / 假跌破」 (紅綠三角形)")
        st.markdown("""
-   🔻 **紅色向下三角 (頂背馳 / 假突破)**：當大盤價格創出 20 日新高，但代表底層實體經濟的小型股市寬卻**拒絕跟隨創新高，甚至掉頭向下**。代表主力拉抬巨頭掩護出貨。**行動：準備清倉、做空或買入 Put 避險。**
-   🔺 **綠色向上三角 (底背馳 / 假跌破)**：當大盤價格創出 20 日新低，市場一片恐慌，但小型股市寬卻**拒絕創新低，甚至率先反彈**。代表主力正在暗中吸納平貨。**行動：準備大舉抄底、做多或買入 Call。**
        """)
        
        st.markdown("### 📊 2. 判斷資金撕裂度 (下方紅綠柱狀圖)")
        st.markdown("""
-   🟥 **紅色柱 (巨頭吸血 / 危險信號)**：大型股遠遠拋離小型股，市場資金被抽乾去炒作頂端少數巨頭，通常發生在牛市末期或極端泡沫。
-   🟩 **綠色柱 (細股狂熱 / 健康牛市)**：小型股表現遠超大型股，資金全面向下尋寶，牛市健康特徵。
        """)

        st.markdown("### 📏 3. 捕捉極端情緒邊界 (紅綠橫向虛線與灰色軌道)")
        st.markdown("""
-   🔴 **紅色虛線 (80 樓上 - 極度超買)**：超過 80% 股票在均線之上，市場極度貪婪，切忌追高。
-   🟢 **綠色虛線 (20 樓下 - 極度超賣)**：市場血流成河，通常為長線資金黃金買點。
-   🌪️ **淺灰色動態帶 (2-StdDev 軌道)**：突破頂部為真正極端超買，跌破底部為絕望超賣。
        """)
    st.divider()

    col_cfg1, col_cfg2, col_cfg3 = st.columns([1, 1.2, 1.2])
    with col_cfg1:
        lookback_days = st.slider("歷史回溯日數 (畫圖範圍)", min_value=100, max_value=800, value=250)
    with col_cfg2:
        macro_mode = st.radio(
            "📡 選擇【上層大局視角】數據深度", 
            ["👑 華爾街機構級 S&P 1500 (最精準 / 載入需時)", "🚀 實打實 600 隻全覆蓋模式 (極速平衡)"], 
            index=0
        )
    with col_cfg3:
        bg_benchmark_choice = st.radio(
            "📈 選擇背景對比指數 (灰虛線)", 
            ["SPY (標普500)", "QQQ (納斯達克)", "IWM (羅素2000)", "DIA (道瓊斯)"], 
            index=0
        )

    end_date = datetime.today()
    end_date = datetime(end_date.year, end_date.month, end_date.day)
    start_date = end_date - timedelta(days=lookback_days)
    fetch_start = start_date - timedelta(days=365) 
    bg_ticker = bg_benchmark_choice.split(" ")[0]

    # ==========================================
    # 核心一：數據抓取 (防崩純化版)
    # ==========================================
    @st.cache_data(ttl=900, show_spinner=False)
    def load_macro_pulses_data():
        macro_tickers = ['HYG', 'TLT', 'COPX', 'GLD', 'BTC-USD', '^VIX', 'SPY']
        try:
            raw = yf.download(macro_tickers, start=fetch_start, end=end_date, progress=False)
            if raw is None or raw.empty: return pd.DataFrame()
            if isinstance(raw.columns, pd.MultiIndex):
                data = raw['Close'].copy() if 'Close' in raw.columns.levels[0] else raw.iloc[:, 0]
            elif 'Close' in raw:
                data = raw[['Close']].copy()
            else:
                data = raw.copy()
            data = data.ffill().bfill()
            if hasattr(data.index, 'tz') and data.index.tz is not None:
                data.index = data.index.tz_localize(None).normalize()
            # 去除重複時間戳
            data = data[~data.index.duplicated(keep='first')]
            return data
        except Exception:
            return pd.DataFrame()

    macro_data = load_macro_pulses_data()

    # 安全提取各子項序列
    def safe_get_series(df, col):
        if not df.empty and col in df.columns:
            s = df[col].dropna()
            return s if not s.empty else pd.Series()
        return pd.Series()

    hyg_s = safe_get_series(macro_data, 'HYG')
    tlt_s = safe_get_series(macro_data, 'TLT')
    copx_s = safe_get_series(macro_data, 'COPX')
    gld_s = safe_get_series(macro_data, 'GLD')
    btc_s = safe_get_series(macro_data, 'BTC-USD')
    vix_series = safe_get_series(macro_data, '^VIX')
    spy_price = safe_get_series(macro_data, 'SPY')

    # 安全比率計算
    hyg_tlt = (hyg_s / tlt_s).dropna() if (not hyg_s.empty and not tlt_s.empty) else pd.Series()
    copx_gld = (copx_s / gld_s).dropna() if (not copx_s.empty and not gld_s.empty) else pd.Series()
    btc_gld = (btc_s / gld_s).dropna() if (not btc_s.empty and not gld_s.empty) else pd.Series()

    # ==========================================
    # 🚦 0. A.I. 戰略指揮燈 (帶安全防護)
    # ==========================================
    st.markdown("### 🚦 A.I. 戰略指揮燈 (Regime Indicator)")
    
    vix_latest = vix_series.iloc[-1] if len(vix_series) >= 1 else 15.0
    vix_chg_20d = 0.0
    if len(vix_series) >= 20 and vix_series.iloc[-20] > 0:
        vix_chg_20d = ((vix_series.iloc[-1] / vix_series.iloc[-20]) - 1.0) * 100.0

    hyg_tlt_chg_20d = 0.0
    if len(hyg_tlt) >= 20 and hyg_tlt.iloc[-20] > 0:
        hyg_tlt_chg_20d = ((hyg_tlt.iloc[-1] / hyg_tlt.iloc[-20]) - 1.0) * 100.0
    
    if vix_latest > 25 or (vix_chg_20d > 20 and hyg_tlt_chg_20d < -3):
        st.error("🔴 **【系統警告：宏觀資產避險 (Risk-Off 警報)】** —— VIX 恐慌飆升，債市信用利差擴大！聰明錢撤退，建議減倉或轉入避險防守！")
    elif hyg_tlt_chg_20d > 2 and vix_latest < 18:
        st.success("🟢 **【系統判定：全面狂暴牛市 (Risk-On 極致)】** —— 信用風險情緒健康，VIX 沉寂，大鱷全力押注風險資產，滿倉進攻！")
    else:
        st.warning("🟡 **【系統判定：資金高位撕裂 / 結構性分化 (Caution)】** —— 巨頭與細股出現撕裂背馳，市場進入高位震盪，建議精選龍頭，控制槓桿！")

    st.divider()

    # ==========================================
    # 🩸 1. 聰明錢三大宏觀脈搏 (獨立防崩容錯)
    # ==========================================
    st.markdown("### 🩸 聰明錢三大宏觀脈搏 (Macro Pulses)")
    st.caption("債市與商品市場講真話：追蹤華爾街大鱷的真實風險偏好與實體經濟體溫。")

    col_p1, col_p2, col_p3 = st.columns(3)
    
    with col_p1:
        if len(hyg_tlt) >= 2:
            curr_ht = hyg_tlt.iloc[-1]
            ht_1m = ((hyg_tlt.iloc[-1] / hyg_tlt.iloc[-22]) - 1.0) * 100.0 if (len(hyg_tlt) >= 22 and hyg_tlt.iloc[-22] > 0) else 0.0
            st.metric("🏦 信貸脈搏 (HYG/TLT)", f"{curr_ht:.3f}", f"{ht_1m:+.2f}% (1個月)")
            st.markdown("<div style='font-size:0.85em; color:gray;'><b>用法</b>：睇華爾街肯唔肯借貴利冒險。<br><span style='color:#00AA00'>▲ 升 (Risk-On)</span> 代表大鱷願意借錢炒股，利好大市；<br><span style='color:red'>▼ 跌 (Risk-Off)</span> 代表債市危機，資金撤退避險。</div>", unsafe_allow_html=True)
            fig_p1 = px.line(hyg_tlt.loc[start_date:end_date], labels={'value': 'HYG/TLT'})
            fig_p1.update_traces(line_color='#FF4500', line_width=2)
            fig_p1.update_layout(height=180, margin=dict(l=10, r=10, t=10, b=10), showlegend=False, xaxis_title=None, yaxis_title=None)
            st.plotly_chart(fig_p1, use_container_width=True)
        else:
            st.info("ℹ️ HYG/TLT 信貸脈搏資料加載中...")

    with col_p2:
        if len(copx_gld) >= 2:
            curr_cg = copx_gld.iloc[-1]
            cg_1m = ((copx_gld.iloc[-1] / copx_gld.iloc[-22]) - 1.0) * 100.0 if (len(copx_gld) >= 22 and copx_gld.iloc[-22] > 0) else 0.0
            st.metric("🏭 增長脈搏 (COPX/GLD 銅金比)", f"{curr_cg:.3f}", f"{cg_1m:+.2f}% (1個月)")
            st.markdown("<div style='font-size:0.85em; color:gray;'><b>用法</b>：實時測量全球實體開工率同衰退陰霾。<br><span style='color:#00AA00'>▲ 升</span> 代表全球工廠開工，實體經濟強勁；<br><span style='color:red'>▼ 跌</span> 代表經濟衰退預期升溫，資金買黃金避險。</div>", unsafe_allow_html=True)
            fig_p2 = px.line(copx_gld.loc[start_date:end_date], labels={'value': 'COPX/GLD'})
            fig_p2.update_traces(line_color='#DAA520', line_width=2)
            fig_p2.update_layout(height=180, margin=dict(l=10, r=10, t=10, b=10), showlegend=False, xaxis_title=None, yaxis_title=None)
            st.plotly_chart(fig_p2, use_container_width=True)
        else:
            st.info("ℹ️ COPX/GLD 增長脈搏資料加載中...")

    with col_p3:
        if len(btc_gld) >= 2:
            curr_bg = btc_gld.iloc[-1]
            bg_1m = ((btc_gld.iloc[-1] / btc_gld.iloc[-22]) - 1.0) * 100.0 if (len(btc_gld) >= 22 and btc_gld.iloc[-22] > 0) else 0.0
            st.metric("🪙 流動性脈搏 (BTC/GLD)", f"{curr_bg:.1f}", f"{bg_1m:+.2f}% (1個月)")
            st.markdown("<div style='font-size:0.85em; color:gray;'><b>用法</b>：測量央行水塘嘅剩餘流動性！<br><span style='color:#00AA00'>▲ 升</span> 代表市場銀紙氾濫，熱錢瘋狂湧入投機資產；<br><span style='color:red'>▼ 跌</span> 代表全球流動性收緊，央行正在「收水」。</div>", unsafe_allow_html=True)
            fig_p3 = px.line(btc_gld.loc[start_date:end_date], labels={'value': 'BTC/GLD'})
            fig_p3.update_traces(line_color='#0000FF', line_width=2)
            fig_p3.update_layout(height=180, margin=dict(l=10, r=10, t=10, b=10), showlegend=False, xaxis_title=None, yaxis_title=None)
            st.plotly_chart(fig_p3, use_container_width=True)
        else:
            st.info("ℹ️ BTC/GLD 流動性脈搏資料加載中...")

    st.divider()

    # ==========================================
    # 核心二：MISE 數據獲取與處理 (帶 5 秒超時自動降級)
    # ==========================================
    @st.cache_data(ttl=86400)
    def get_sp1500_tickers_from_web():
        try:
            req_500 = urllib.request.Request('https://en.wikipedia.org/wiki/List_of_S%26P_500_companies', headers={'User-Agent': 'Mozilla/5.0'})
            sp500_table = pd.read_html(urllib.request.urlopen(req_500, timeout=5))[0]
            sp500 = sp500_table['Symbol'].str.replace('.', '-', regex=False).tolist()
            
            req_400 = urllib.request.Request('https://en.wikipedia.org/wiki/List_of_S%26P_400_companies', headers={'User-Agent': 'Mozilla/5.0'})
            sp400_table = pd.read_html(urllib.request.urlopen(req_400, timeout=5))[0]
            sp400 = sp400_table['Symbol'].str.replace('.', '-', regex=False).tolist()
            
            req_600 = urllib.request.Request('https://en.wikipedia.org/wiki/List_of_S%26P_600_companies', headers={'User-Agent': 'Mozilla/5.0'})
            sp600_table = pd.read_html(urllib.request.urlopen(req_600, timeout=5))[0]
            sp600 = sp600_table['Symbol'].str.replace('.', '-', regex=False).tolist()
            return {"Large (SPY)": sp500, "Mid (MDY)": sp400, "Small (IWM)": sp600}
        except Exception:
            return None

    @st.cache_data(ttl=86400)
    def get_market_cap_tickers(mode_str):
        if not mode_str:
            mode_str = "🚀"

        if "👑" in mode_str:
            sp1500 = get_sp1500_tickers_from_web()
            if sp1500: 
                return sp1500
            mode_str = "🚀"

        large_cap = ['AAPL', 'MSFT', 'NVDA', 'AMZN', 'META', 'GOOGL', 'GOOG', 'BRK-B', 'LLY', 'AVGO', 'JPM', 'TSLA', 'UNH', 'XOM', 'V', 'PG', 'MA', 'JNJ', 'HD', 'ABBV', 'COST', 'MRK', 'CRM', 'CVX', 'NFLX', 'AMD', 'BAC', 'PEP', 'KO', 'WMT', 'LIN', 'TMO', 'MCD', 'DIS', 'ADBE', 'CSCO', 'ABT', 'INTU', 'QCOM', 'IBM', 'CMCSA', 'CAT', 'GE', 'PFE', 'VZ', 'NOW', 'UBER', 'AMAT', 'AXP', 'TXN', 'ISRG', 'PM', 'BKNG', 'GS', 'LOW', 'MS', 'SPGI', 'RTX', 'SPG', 'HON', 'BLK', 'NEE', 'C', 'PGR', 'TJX', 'ELV', 'AMGN', 'SCHW', 'SYK', 'DE', 'UNP', 'COP', 'MDLZ', 'REGN', 'LMT', 'ADP', 'PLTR', 'ADI', 'BSX', 'BX', 'PANW', 'MU']
        mid_cap = ['DECK', 'WWD', 'RGA', 'KNF', 'LBRDA', 'CASY', 'SAIA', 'TOL', 'PEN', 'FN', 'RPM', 'WMS', 'MTD', 'CHDN', 'LECO', 'MUR', 'LSCC', 'SF', 'EGP', 'GL', 'MORN', 'KEX', 'TR', 'SLG', 'CFR', 'PRI', 'SON', 'CBSH', 'UGI', 'HWC', 'GBCI', 'FFIN', 'UHT', 'NJR', 'SRCE', 'TMP', 'NWE', 'MGEE', 'SJI', 'ALE']
        small_cap = ['SMCI', 'CELH', 'RMD', 'ELF', 'ALGN', 'CROX', 'MED', 'FOXF', 'LANC', 'SITM', 'WNC', 'THRM', 'BOOM', 'AMPH', 'LNN', 'ATGE', 'GTY', 'HSTM', 'FLGT', 'EZPW', 'TSRI', 'PBPB', 'TAST', 'RRGB', 'LOCO', 'RICK', 'DINE', 'CHUY', 'PLAY', 'BJRI', 'BLMN', 'CBRL', 'DENN', 'TXRH', 'CAKE', 'IRWD']

        large_clean = list(dict.fromkeys(large_cap))
        mid_clean = [t for t in dict.fromkeys(mid_cap) if t not in large_clean]
        small_clean = [t for t in dict.fromkeys(small_cap) if t not in large_clean and t not in mid_clean]
        return {"Large (SPY)": large_clean, "Mid (MDY)": mid_clean, "Small (IWM)": small_clean}

    @st.cache_data(ttl=3600)
    def calculate_mise_index(tickers, fetch_start):
        try:
            data = yf.download(tickers, start=fetch_start, end=datetime.today(), progress=False)
            if data.empty: return pd.Series()
            closes = data['Close'] if 'Close' in data.columns.levels[0] else data
            if isinstance(closes, pd.Series): closes = closes.to_frame()
                
            closes.index = closes.index.tz_localize(None)
            closes = closes[~closes.index.duplicated(keep='first')]
            
            ma20 = closes.rolling(20, min_periods=5).mean()
            ma50 = closes.rolling(50, min_periods=10).mean()
            ma200 = closes.rolling(200, min_periods=20).mean()
            
            valid_counts = closes.notna().sum(axis=1).replace(0, np.nan)
            pct_20 = (closes > ma20).sum(axis=1) / valid_counts * 100.0
            pct_50 = (closes > ma50).sum(axis=1) / valid_counts * 100.0
            pct_200 = (closes > ma200).sum(axis=1) / valid_counts * 100.0
            
            mise_raw = (pct_20 * 0.3) + (pct_50 * 0.4) + (pct_200 * 0.3)
            return mise_raw.ewm(span=5, adjust=False).mean().fillna(50.0)
        except Exception:
            return pd.Series()

    def detect_divergence(price_series, breadth_series, window=20):
        if price_series.empty or breadth_series.empty or len(price_series) < window:
            return [], [], [], []
        price_roll_max = price_series.rolling(window, min_periods=5).max()
        breadth_roll_max = breadth_series.rolling(window, min_periods=5).max()
        price_roll_min = price_series.rolling(window, min_periods=5).min()
        breadth_roll_min = breadth_series.rolling(window, min_periods=5).min()
        
        bear_x, bear_y, bull_x, bull_y = [], [], [], []
        
        for i in range(window, len(price_series)):
            if price_series.iloc[i] >= price_roll_max.iloc[i] and breadth_series.iloc[i] < (breadth_roll_max.iloc[i] - 10):
                if len(bear_x) == 0 or (price_series.index[i] - bear_x[-1]).days > 5:
                    bear_x.append(price_series.index[i])
                    bear_y.append(price_series.iloc[i])
            if price_series.iloc[i] <= price_roll_min.iloc[i] and breadth_series.iloc[i] > (breadth_roll_min.iloc[i] + 10):
                if len(bull_x) == 0 or (price_series.index[i] - bull_x[-1]).days > 5:
                    bull_x.append(price_series.index[i])
                    bull_y.append(price_series.iloc[i])
        return bear_x, bear_y, bull_x, bull_y

    def render_mise_chart(title_text, tickers_dict, bg_series, bg_name):
        st.markdown(f"#### {title_text}")

        f_large = calculate_mise_index(tickers_dict["Large (SPY)"], fetch_start)
        f_mid = calculate_mise_index(tickers_dict["Mid (MDY)"], fetch_start)
        f_small = calculate_mise_index(tickers_dict["Small (IWM)"], fetch_start)
        if f_large.empty: 
            st.info("ℹ️ 市寬資料不足或抓取中...")
            return

        try:
            m_large = f_large.loc[start_date:end_date]
            m_mid = f_mid.loc[start_date:end_date]
            m_small = f_small.loc[start_date:end_date]
            p_bg = bg_series.loc[start_date:end_date] if not bg_series.empty else pd.Series()
        except Exception:
            m_large, m_mid, m_small, p_bg = f_large, f_mid, f_small, bg_series

        spread = m_large - m_small
        roll_m = f_large.rolling(126, min_periods=20).mean().loc[start_date:end_date]
        roll_s = f_large.rolling(126, min_periods=20).std().loc[start_date:end_date]
        up_band = roll_m + (2.0 * roll_s)
        low_band = roll_m - (2.0 * roll_s)
        
        bear_x, bear_y, bull_x, bull_y = detect_divergence(p_bg, m_small)

        fig = make_subplots(rows=2, cols=1, shared_xaxes=True, row_heights=[0.75, 0.25], vertical_spacing=0.05, specs=[[{"secondary_y": True}], [{"secondary_y": False}]])
        
        if not p_bg.empty:
            fig.add_trace(go.Scatter(x=p_bg.index, y=p_bg, name=f"{bg_name}價格", line=dict(color='rgba(148,163,184,0.6)', width=2.5, dash='dot')), row=1, col=1, secondary_y=True)
        if bear_x: fig.add_trace(go.Scatter(x=bear_x, y=bear_y, mode='markers', marker=dict(symbol='triangle-down', size=12, color='#ef4444'), name="頂背馳(紅三角)"), row=1, col=1, secondary_y=True)
        if bull_x: fig.add_trace(go.Scatter(x=bull_x, y=bull_y, mode='markers', marker=dict(symbol='triangle-up', size=12, color='#10b981'), name="底背馳(綠三角)"), row=1, col=1, secondary_y=True)

        fig.add_trace(go.Scatter(x=up_band.index, y=up_band, line=dict(width=0), showlegend=False, hoverinfo='skip'), row=1, col=1)
        fig.add_trace(go.Scatter(x=low_band.index, y=low_band, line=dict(width=0), fill='tonexty', fillcolor='rgba(148,163,184,0.12)', name="2-StdDev灰色軌道"), row=1, col=1)

        fig.add_trace(go.Scatter(x=m_large.index, y=m_large, name="大型(藍)", line=dict(color='#00e5ff', width=2.2)), row=1, col=1)
        fig.add_trace(go.Scatter(x=m_mid.index, y=m_mid, name="中型(橙)", line=dict(color='#ffaa00', width=2)), row=1, col=1)
        fig.add_trace(go.Scatter(x=m_small.index, y=m_small, name="小型(綠)", line=dict(color='#00ff88', width=2)), row=1, col=1)
        
        fig.add_hline(y=80, line_dash="dash", line_color="#ef4444", opacity=0.5, row=1, col=1)
        fig.add_hline(y=20, line_dash="dash", line_color="#10b981", opacity=0.5, row=1, col=1)
        
        colors = ['#ef4444' if (pd.notnull(v) and v > 15) else '#10b981' if (pd.notnull(v) and v < -15) else 'rgba(148,163,184,0.3)' for v in spread]
        fig.add_trace(go.Bar(x=spread.index, y=spread, marker_color=colors, name="藍綠撕裂度(紅綠柱)"), row=2, col=1)
        fig.add_hline(y=15, line_dash="dot", line_color="#ef4444", opacity=0.5, row=2, col=1, annotation_text="紅柱界線", annotation_position="top left")
        fig.add_hline(y=-15, line_dash="dot", line_color="#10b981", opacity=0.5, row=2, col=1, annotation_text="綠柱界線", annotation_position="bottom left")

        fig.update_layout(height=520, margin=dict(l=20, r=20, t=10, b=10), template="plotly_dark", paper_bgcolor="#171b26", plot_bgcolor="#171b26", legend=dict(orientation="h", yanchor="bottom", y=1.02, xanchor="right", x=1))
        fig.update_yaxes(title_text="同步率 (0-100)", range=[0, 100], row=1, col=1, secondary_y=False)
        fig.update_yaxes(title_text="撕裂度", row=2, col=1)
        fig.update_xaxes(range=[start_date, end_date], row=1, col=1)
        fig.update_xaxes(range=[start_date, end_date], row=2, col=1)
        st.plotly_chart(fig, use_container_width=True)

    with st.spinner(f"正在掃描市寬底層數據與 {bg_ticker} 價格..."):
        try:
            bg_bench_raw = yf.download(bg_ticker, start=fetch_start, end=end_date, progress=False)
            bg_bench_full = bg_bench_raw['Close'] if ('Close' in bg_bench_raw) else pd.Series()
            if isinstance(bg_bench_full, pd.DataFrame): bg_bench_full = bg_bench_full.iloc[:, 0]
            if not bg_bench_full.empty:
                bg_bench_full.index = bg_bench_full.index.tz_localize(None)
                bg_bench_full = bg_bench_full[~bg_bench_full.index.duplicated(keep='first')]
        except Exception:
            bg_bench_full = pd.Series()
            
        render_mise_chart(
            "👑 第一層：上帝視角 (絕對真實底層) —— 動態標準差與極端背馳預警" if "👑" in macro_mode else "🚀 第一層：全景視角 (600隻 平衡大局) —— 動態標準差與極端背馳預警", 
            get_market_cap_tickers(macro_mode), bg_bench_full, bg_ticker
        )
        st.markdown("<br>", unsafe_allow_html=True)
        render_mise_chart("🎯 第二層：熱錢視角 (~158 隻活躍精英) —— 捕捉龍頭背馳與熱錢撕裂", get_market_cap_tickers("🚀"), bg_bench_full, bg_ticker)

    st.divider()

    # =========================================================================
    # 核心三：華爾街 64 大板塊全息星盤與熱力全景
    # =========================================================================
    st.markdown("<h3 style='color:#00e5ff; font-family:Arial Black;'>🎡 核心二：華爾街 64 大板塊全息星盤與熱力全景</h3>", unsafe_allow_html=True)
    st.caption("全景覆蓋：涵蓋 11 大傳統宏觀 (GICS) ＋ 53 大前沿硬科技、細分產業與資源霸權，共 64 大板塊。")

    @st.cache_data(ttl=900, show_spinner=False)
    def load_all_market_data():
        all_tickers = set(['SPY', 'TLT']) 
        all_tickers.update(MACRO_SECTORS.keys())
        all_tickers.update(ULTIMATE_SECTORS.values())
        for sec, info in FRONTIER_SECTORS.items():
            if 'etfs' in info:
                for etf in info['etfs']:
                    if etf: all_tickers.add(etf)
            for t in info.get('tickers', []):
                if '.' not in t:
                    all_tickers.add(t)
        try:
            raw = yf.download(list(all_tickers), period='1y', auto_adjust=True, progress=False, timeout=20)
            if raw is None or raw.empty: return pd.DataFrame()
            if isinstance(raw.columns, pd.MultiIndex):
                data = raw['Close'].copy() if 'Close' in raw.columns.levels[0] else raw.iloc[:, 0]
            elif 'Close' in raw:
                data = raw[['Close']].copy()
            else:
                data = raw.copy()
            if hasattr(data.index, 'tz') and data.index.tz is not None:
                data.index = data.index.tz_localize(None).normalize()
            data = data[~data.index.duplicated(keep='first')]
            return data.dropna(how='all', axis=1).ffill().bfill()
        except Exception:
            return pd.DataFrame()

    col_rf1, col_rf2 = st.columns([8, 2])
    with col_rf2:
        if st.button("🔄 強制刷新資金大數據", use_container_width=True):
            load_all_market_data.clear()
            load_macro_pulses_data.clear()
            st.rerun()

    def calculate_momentum_table(series_dict, mid_days, short_days):
        data = []
        for name, series in series_dict.items():
            if series is None or series.empty: continue
            s = series.dropna()
            if len(s) >= 2:
                p_now = s.iloc[-1]
                p_1d = s.iloc[-2]
                chg_1d = (p_now / p_1d - 1.0) * 100.0 if (p_1d > 0 and pd.notnull(p_1d)) else 0.0
                chg_5d = (p_now / s.iloc[-6] - 1.0) * 100.0 if len(s) >= 6 and s.iloc[-6] > 0 else np.nan
                chg_10d = (p_now / s.iloc[-11] - 1.0) * 100.0 if len(s) >= 11 and s.iloc[-11] > 0 else np.nan
                chg_22d = (p_now / s.iloc[-23] - 1.0) * 100.0 if len(s) >= 23 and s.iloc[-23] > 0 else np.nan
                chg_44d = (p_now / s.iloc[-45] - 1.0) * 100.0 if len(s) >= 45 and s.iloc[-45] > 0 else np.nan
                chg_66d = (p_now / s.iloc[-67] - 1.0) * 100.0 if len(s) >= 67 and s.iloc[-67] > 0 else np.nan
                chg_130d = (p_now / s.iloc[-131] - 1.0) * 100.0 if len(s) >= 131 and s.iloc[-131] > 0 else np.nan
                
                chg_mid = (p_now / s.iloc[-mid_days-1] - 1.0) * 100.0 if len(s) >= mid_days + 1 and s.iloc[-mid_days-1] > 0 else np.nan
                chg_short = (p_now / s.iloc[-short_days-1] - 1.0) * 100.0 if len(s) >= short_days + 1 and s.iloc[-short_days-1] > 0 else np.nan
                
                # 剔除 inf
                chg_1d = 0.0 if np.isinf(chg_1d) else chg_1d
                
                data.append({
                    '板塊': name, 
                    '1日變化 (%)': chg_1d, 
                    '1週 (5日) (%)': chg_5d, 
                    '2週 (10日) (%)': chg_10d, 
                    '1個月 (22日) (%)': chg_22d, 
                    '2個月 (44日) (%)': chg_44d, 
                    '1季 (66日) (%)': chg_66d, 
                    '半年 (130日) (%)': chg_130d, 
                    '動態中線 (%)': chg_mid, 
                    '動態短線 (%)': chg_short
                })
        df = pd.DataFrame(data)
        if not df.empty: df = df.sort_values(by='動態短線 (%)', ascending=False)
        return df

    # =========================================================================
    # 🧠 8大趨勢感知 RRG 計算引擎
    # =========================================================================
    def calculate_rrg_metrics_8_status(price_df, sector_series_dict, window=14, benchmark='SPY', tail_len=10):
        if price_df.empty or benchmark not in price_df.columns: return pd.DataFrame(), []
            
        bench_price = price_df[benchmark]
        if bench_price.empty or (bench_price <= 0).all(): return pd.DataFrame(), []

        rs_ratio_dict = {}
        rs_mom_dict = {}

        for name, series in sector_series_dict.items():
            if series is None or series.empty: continue
            aligned = pd.concat([series, bench_price], axis=1).dropna()
            if len(aligned) < window * 2: continue
            
            s_sec = aligned.iloc[:, 0]
            s_bench = aligned.iloc[:, 1]
            
            rs = s_sec / s_bench
            rs_mean = rs.rolling(window, min_periods=max(5, window // 2)).mean()
            rs_std = rs.rolling(window, min_periods=max(5, window // 2)).std().replace(0, np.nan)
            
            ratio = 100.0 + ((rs - rs_mean) / rs_std) * 2.0
            ratio = ratio.ffill().bfill()
            
            ratio_mean = ratio.rolling(window, min_periods=max(5, window // 2)).mean()
            ratio_std = ratio.rolling(window, min_periods=max(5, window // 2)).std().replace(0, np.nan)
            
            mom = 100.0 + ((ratio - ratio_mean) / ratio_std) * 2.0
            mom = mom.ffill().bfill()
            
            rs_ratio_dict[name] = ratio
            rs_mom_dict[name] = mom

        df_ratio = pd.DataFrame(rs_ratio_dict)
        df_mom = pd.DataFrame(rs_mom_dict)
        
        colors = [
            '#00ff88', '#ff3344', '#00e5ff', '#ffaa00', '#ab47bc', '#ffeb3b', '#76ff03', '#f06292',
            '#ff9800', '#00bcd4', '#e91e63', '#00e676', '#9c27b0', '#673ab7', '#3f51b5', '#2196f3',
            '#03a9f4', '#00bac7', '#009688', '#4caf50', '#8bc34a', '#cddc39', '#ffc107', '#ff5722',
            '#e040fb', '#ff1744', '#18ffff', '#ffd600', '#ff80ab', '#82b1ff'
        ]
        
        scatter_data = []
        for i, col in enumerate(df_ratio.columns):
            s_r = df_ratio[col].dropna()
            s_m = df_mom[col].dropna()
            s_price = sector_series_dict[col].dropna() if col in sector_series_dict else pd.Series()
            if s_r.empty or s_m.empty: continue
            
            tail_x = s_r.tail(tail_len).values.tolist()
            tail_y = s_m.tail(tail_len).values.tolist()
            if not tail_x or not tail_y: continue
            
            curr_ratio, curr_mom = tail_x[-1], tail_y[-1]
            p_now = s_price.iloc[-1] if not s_price.empty else 100.0
            
            # 趨勢指標安全取值
            ma20 = s_price.rolling(20, min_periods=5).mean().iloc[-1] if len(s_price) >= 20 else p_now
            ma50 = s_price.rolling(50, min_periods=10).mean().iloc[-1] if len(s_price) >= 50 else p_now
            is_above_ma20 = bool(p_now >= ma20) if pd.notnull(ma20) else True
            is_above_ma50 = bool(p_now >= ma50) if pd.notnull(ma50) else True
            
            mom_slope = tail_y[-1] - tail_y[-3] if len(tail_y) >= 3 else 0.0
            ret_half = 0.0
            if len(s_price) >= 130 and s_price.iloc[-130] > 0:
                ret_half = ((p_now / s_price.iloc[-130]) - 1.0) * 100.0

            # 4 升 vs 4 跌 嚴密判定
            if curr_ratio >= 100.0 and curr_mom >= 100.0:
                status, emoji = ("加速爆發 (Leading)", "🚀") if is_above_ma50 else ("觸底復甦 (Accumulation)", "🌱")
            elif curr_ratio < 100.0 and curr_mom >= 100.0:
                status, emoji = ("回踩重啟 (Rebounding)", "🌟") if is_above_ma50 else ("觸底復甦 (Accumulation)", "🌱")
            elif curr_ratio >= 100.0 and curr_mom < 100.0:
                if is_above_ma50:
                    status, emoji = ("轉弱蓄勢 (偏向重啟)", "🌤️") if (is_above_ma20 and mom_slope >= -0.5) else ("轉弱破位 (偏向續跌)", "⚠️")
                else:
                    status, emoji = ("弱勢陰跌 (Chronic Lagging)", "💀")
            else:  # curr_ratio < 100.0 and curr_mom < 100.0
                status, emoji = ("高位派發 (Distribution)", "⚠️") if (is_above_ma50 or ret_half > 15.0) else ("深度衰退 (Lagging)", "📉")
            
            scatter_data.append({
                "full_name": col, "short_name": format_name(col), 
                "x": tail_x, "y": tail_y, "color": colors[i % len(colors)], "status": f"{emoji} {status}"
            })
            
        return df_ratio, scatter_data

    def plot_rrg_chart(scatter_data, chart_title):
        if not scatter_data: return
        fig = go.Figure()

        fig.add_shape(type="rect", x0=100, y0=100, x1=130, y1=130, fillcolor="rgba(0, 255, 136, 0.05)", layer="below", line_width=0)
        fig.add_shape(type="rect", x0=100, y0=70, x1=130, y1=100, fillcolor="rgba(255, 235, 59, 0.05)", layer="below", line_width=0)
        fig.add_shape(type="rect", x0=70, y0=70, x1=100, y1=100, fillcolor="rgba(255, 51, 68, 0.05)", layer="below", line_width=0)
        fig.add_shape(type="rect", x0=70, y0=100, x1=100, y1=130, fillcolor="rgba(0, 229, 255, 0.05)", layer="below", line_width=0)
        
        fig.add_vline(x=100, line_width=1.5, line_color="#64748b", line_dash="dash")
        fig.add_hline(y=100, line_width=1.5, line_color="#64748b", line_dash="dash")
        
        fig.add_annotation(x=0.98, y=0.98, text="領先 (Leading)", showarrow=False, xref="paper", yref="paper", font=dict(color="#00ff88", size=24, family="Arial Black"), opacity=0.3)
        fig.add_annotation(x=0.98, y=0.02, text="轉弱 (Weakening)", showarrow=False, xref="paper", yref="paper", font=dict(color="#ffeb3b", size=24, family="Arial Black"), opacity=0.3)
        fig.add_annotation(x=0.02, y=0.02, text="落後 (Lagging)", showarrow=False, xref="paper", yref="paper", font=dict(color="#ff3344", size=24, family="Arial Black"), opacity=0.3)
        fig.add_annotation(x=0.02, y=0.98, text="改善 (Improving)", showarrow=False, xref="paper", yref="paper", font=dict(color="#00e5ff", size=24, family="Arial Black"), opacity=0.3)

        all_x, all_y = [], []
        for d in scatter_data:
            if len(d['x']) > 1:
                fig.add_trace(go.Scatter(x=d['x'], y=d['y'], mode='lines', line=dict(color=d['color'], width=1.5), opacity=0.6, showlegend=False, hoverinfo='skip'))
            all_x.extend(d['x'])
            all_y.extend(d['y'])

        text_positions = ['top center', 'bottom center', 'middle right', 'middle left', 'top right', 'bottom left', 'top left', 'bottom right']

        for i, d in enumerate(scatter_data):
            pos = text_positions[i % len(text_positions)]
            fig.add_trace(go.Scatter(
                x=[d['x'][-1]], y=[d['y'][-1]], mode='markers+text',
                marker=dict(color=d['color'], size=11, line=dict(color='#ffffff', width=1.2)),
                text=[f" <b>{d['short_name']}</b> "], textposition=pos, textfont=dict(color="#ffffff", size=11, family="Arial Black"),
                name=d['short_name'], hovertemplate=f"<b>{d['full_name']}</b><br>強度: %{{x:.2f}}<br>動能: %{{y:.2f}}<extra></extra>"
            ))

        valid_x = [v for v in all_x if pd.notnull(v) and not np.isinf(v)]
        valid_y = [v for v in all_y if pd.notnull(v) and not np.isinf(v)]
        min_x = min(valid_x) if valid_x else 96.0
        max_x = max(valid_x) if valid_x else 104.0
        min_y = min(valid_y) if valid_y else 96.0
        max_y = max(valid_y) if valid_y else 104.0
        padding = 2.5
        
        fig.update_layout(
            title=dict(text=f"🎡 {chart_title}", font=dict(color="#00e5ff", size=20, family="Arial Black")),
            template="plotly_dark", height=850, margin=dict(l=50, r=50, t=50, b=50),
            paper_bgcolor="#11141a", plot_bgcolor="#11141a",
            xaxis=dict(title="RS-Ratio (強度 > 100 為跑贏大市)", title_font=dict(color="#ffffff"), tickfont=dict(color="#e2e8f0"), range=[min(min_x - padding, 95.0), max(max_x + padding, 105.0)], showgrid=True, gridcolor='#222834', zeroline=False),
            yaxis=dict(title="RS-Momentum (動能 > 100 為向上加速)", title_font=dict(color="#ffffff"), tickfont=dict(color="#e2e8f0"), range=[min(min_y - padding, 95.0), max(max_y + padding, 105.0)], showgrid=True, gridcolor='#222834', zeroline=False),
            showlegend=False
        )
        st.plotly_chart(fig, use_container_width=True)

    def render_treemap(mom_df, size_col, color_col):
        st.markdown("#### 🗺️ 資金實時板塊熱力圖 (Treemap)")
        st.caption(f"方塊大小代表 **{size_col}** 的絕對波幅，顏色深淺代表 **{color_col}** 的資金流入(綠)或流出(紅)強度。")
        
        tree_df = mom_df.copy()
        tree_df['short_name'] = tree_df['板塊'].apply(format_name)
        tree_df['size'] = tree_df[size_col].abs().fillna(0.0) + 0.1 
        
        fig_tree = px.treemap(
            tree_df, path=['short_name'], values='size',
            color=color_col,
            color_continuous_scale=['#ff3344', '#1e293b', '#00ff88'],
            color_continuous_midpoint=0,
            hover_data={size_col: ':.2f', color_col: ':.2f'}
        )
        fig_tree.update_layout(height=420, margin=dict(l=10, r=10, t=10, b=10), template="plotly_dark", paper_bgcolor="#171b26")
        st.plotly_chart(fig_tree, use_container_width=True)

    # =========================================================================
    # 🌟 柱狀圖（充足縱向空間）與數據表（無限縱向平鋪全覽）
    # =========================================================================
    def render_momentum_section(mom_df, scatter_data, section_title, mid_label, short_label, tree_size_col, tree_color_col):
        if mom_df.empty: return
        
        render_treemap(mom_df, tree_size_col, tree_color_col)
        
        st.markdown(f"#### 📊 {section_title} 資金動能對比")
        fig_bar = go.Figure()
        
        # 單行文字垂直排開，中文在上、英文代碼在下，絕不折行撞車
        fig_bar.add_trace(go.Bar(
            x=mom_df['板塊'], y=mom_df['動態中線 (%)'],
            name=mid_label, marker_color='#00d2ff',
            hovertemplate=f'%{{x}}<br>{mid_label}: %{{y:.2f}}%<extra></extra>'
        ))
        colors_short = ['#00ff88' if (pd.notnull(val) and val > 0) else '#ff3344' for val in mom_df['動態短線 (%)']]
        fig_bar.add_trace(go.Bar(
            x=mom_df['板塊'], y=mom_df['動態短線 (%)'],
            name=short_label, marker_color=colors_short,
            hovertemplate=f'%{{x}}<br>{short_label}: %{{y:.2f}}%<extra></extra>'
        ))
        
        fig_bar.update_layout(
            barmode='group',
            height=680,
            margin=dict(l=20, r=20, t=40, b=220), # 底部預留 220px 空間，字字清晰
            template="plotly_dark", paper_bgcolor="#171b26", plot_bgcolor="#171b26",
            font=dict(color="#ffffff", size=12),
            legend=dict(
                orientation="h", yanchor="bottom", y=1.02, xanchor="right", x=1,
                font=dict(color="#ffffff", size=12, family="Arial Black"),
                bgcolor="rgba(23, 27, 38, 0.8)", bordercolor="#334155", borderwidth=1
            )
        )
        fig_bar.update_xaxes(
            tickangle=-90,
            automargin=True,
            tickfont=dict(color="#e2e8f0", size=11),
            gridcolor="#222834"
        )
        fig_bar.update_yaxes(tickfont=dict(color="#e2e8f0", size=11), gridcolor="#222834")
        st.plotly_chart(fig_bar, use_container_width=True)

        # ----------------------------------------------------
        # 📋 8 大趨勢感知狀態全景徽章數據表 (移除高度上限，自然縱向全覽！)
        # ----------------------------------------------------
        st.markdown(f"#### 📋 {section_title} 詳細數據表 (搭載 8 大趨勢感知徽章)")
        status_dict = {d['full_name']: d['status'] for d in scatter_data}
        mom_df['RRG 狀態'] = mom_df['板塊'].map(status_dict)
        
        # 白底高對比專業字體配色：深邃森林綠 (#008000) + 深緋紅 (#dc2626) + 石墨灰 (#475569)
        def color_pct(val):
            if pd.isna(val): return ''
            color = '#008000' if val > 0 else '#dc2626' if val < 0 else '#475569'
            return f'color: {color}; font-weight: bold;'
            
        def color_status_8(val):
            if not isinstance(val, str): return ""
            if "加速爆發" in val:
                return "background-color: #064e3b; color: #a7f3d0; font-weight: bold;"
            elif "回踩重啟" in val:
                return "background-color: #065f46; color: #6ee7b7; font-weight: bold;"
            elif "轉弱蓄勢" in val:
                return "background-color: #1e3a8a; color: #bfdbfe; font-weight: bold;"
            elif "觸底復甦" in val:
                return "background-color: #172554; color: #93c5fd; font-weight: bold;"
            elif "轉弱破位" in val:
                return "background-color: #78350f; color: #fde68a; font-weight: bold;"
            elif "高位派發" in val:
                return "background-color: #854d0e; color: #fef08a; font-weight: bold;"
            elif "深度衰退" in val:
                return "background-color: #7f1d1d; color: #fecaca; font-weight: bold;"
            elif "弱勢陰跌" in val:
                return "background-color: #4c0519; color: #fda4af; font-weight: bold;"
            return ""

        subset_cols = [
            '1日變化 (%)', '1週 (5日) (%)', '2週 (10日) (%)', 
            '1個月 (22日) (%)', '2個月 (44日) (%)', '1季 (66日) (%)', '半年 (130日) (%)'
        ]
        display_cols = ['板塊'] + subset_cols + ['RRG 狀態']

        # 徹底解鎖 600px 限制！根據板塊總數自然向下展開長表
        dynamic_height = max(180, int((len(mom_df) * 36) + 48))

        styler = mom_df[display_cols].style
        map_attr = "map" if hasattr(styler, "map") else "applymap"
        styled_df = getattr(styler, map_attr)(color_pct, subset=subset_cols)
        styled_df = getattr(styled_df, map_attr)(color_status_8, subset=['RRG 狀態']).format(
            {col: '{:.2f}%' for col in subset_cols}
        )
        st.dataframe(styled_df, use_container_width=True, height=dynamic_height, hide_index=True)

    with st.spinner("📡 正在全量抓取並計算全網 64 大板塊數據 (含多 ETF 籃子與自建純血指數)..."):
        price_data = load_all_market_data()

    if not price_data.empty:
        # 1. 傳統宏觀 11 大
        macro_series = {name: price_data[symbol] for symbol, name in MACRO_SECTORS.items() if symbol in price_data.columns}
        
        # 2. 前沿 53 大 (加裝防爆截斷濾網)
        frontier_series = {}
        for name, info in FRONTIER_SECTORS.items():
            valid_cols = [c for c in info.get('tickers', []) if c in price_data.columns]
            if 'etfs' in info:
                for etf in info['etfs']:
                    if etf in price_data.columns and etf not in valid_cols: 
                        valid_cols.append(etf)
            if valid_cols:
                clean_pct = price_data[valid_cols].pct_change().clip(lower=-0.25, upper=0.25).mean(axis=1)
                frontier_series[name] = (1.0 + clean_pct.fillna(0.0)).cumprod() * 100.0
                
        # 3. 全球 64 大混戰
        combined_series = {**macro_series, **frontier_series}
        ultimate_series = {name: price_data[symbol] for name, symbol in ULTIMATE_SECTORS.items() if symbol in price_data.columns}

        # =========================================================================
        # 🎯 展區一：全球 64 大板塊大混戰 (全景對比 · 純白高對比速查指南)
        # =========================================================================
        st.markdown("<h3 style='color:#ffd700;'>🌐 展區一：全球 64 大板塊大混戰 (全景對比)</h3>", unsafe_allow_html=True)
        
        # 8 大趨勢感知狀態速查指南 (加裝全域 CSS 穿透，確保 100% 高對比純白字)
        with st.expander("🧭 點擊展開：趨勢感知 RRG 8 大狀態實戰解讀指南 (4 升 vs 4 跌 鏡像對稱)", expanded=True):
            col_st_up, col_st_down = st.columns(2)
            
            with col_st_up:
                st.markdown("""<style>
.rrg-guide-card-green * { color: #ffffff !important; }
</style>
<div class="rrg-guide-card-green" style="background-color: #0f172a; border-left: 5px solid #00ff88; padding: 14px 16px; border-radius: 8px;">
    <div style="color: #00ff88 !important; font-size: 16px; font-weight: bold; margin-bottom: 12px;">🟢 【4 大偏多 / 上升狀態】(綠/藍系)</div>
    <div style="margin-bottom: 10px;">
        <div style="color: #ffffff !important; font-weight: bold; font-size: 14px;">1. 🚀 加速爆發 (Leading)</div>
        <div style="color: #f1f5f9 !important; font-size: 13px;">➔ 50MA 上方，RS ≥ 100 且 Mom ≥ 100</div>
        <div style="color: #ffffff !important; font-size: 13px;"><span style="color: #38bdf8 !important; font-weight: bold;">【實戰涵義】</span>：狂暴主升浪，均線多頭全場領跑。</div>
    </div>
    <div style="margin-bottom: 10px;">
        <div style="color: #ffffff !important; font-weight: bold; font-size: 14px;">2. 🌟 回踩重啟 (Rebounding)</div>
        <div style="color: #f1f5f9 !important; font-size: 13px;">➔ 50MA 上方，RS &lt; 100 且 Mom ≥ 100</div>
        <div style="color: #ffffff !important; font-size: 13px;"><span style="color: #38bdf8 !important; font-weight: bold;">【實戰涵義】</span>：回踩 50MA 確認支撐二度起爆，牛市再點火。</div>
    </div>
    <div style="margin-bottom: 10px;">
        <div style="color: #ffffff !important; font-weight: bold; font-size: 14px;">3. 🌤️ 轉弱蓄勢 (偏向重啟)</div>
        <div style="color: #f1f5f9 !important; font-size: 13px;">➔ 50MA 上方，RS ≥ 100 且 Mom &lt; 100，<b style="color: #fde047 !important;">但守穩 20MA</b></div>
        <div style="color: #ffffff !important; font-size: 13px;"><span style="color: #38bdf8 !important; font-weight: bold;">【實戰涵義】</span>：牛市良性洗盤回吐，短線未破生命線，預視高機率重拾升軌。</div>
    </div>
    <div>
        <div style="color: #ffffff !important; font-weight: bold; font-size: 14px;">4. 🌱 觸底復甦 (Accumulation)</div>
        <div style="color: #f1f5f9 !important; font-size: 13px;">➔ 50MA 下方，Mom ≥ 100</div>
        <div style="color: #ffffff !important; font-size: 13px;"><span style="color: #38bdf8 !important; font-weight: bold;">【實戰涵義】</span>：水底左側超跌見底，動能率先金叉抬頭，聰明錢暗中吸籌。</div>
    </div>
</div>""", unsafe_allow_html=True)
                
            with col_st_down:
                st.markdown("""<style>
.rrg-guide-card-red * { color: #ffffff !important; }
</style>
<div class="rrg-guide-card-red" style="background-color: #0f172a; border-left: 5px solid #ff3344; padding: 14px 16px; border-radius: 8px;">
    <div style="color: #ff4d4d !important; font-size: 16px; font-weight: bold; margin-bottom: 12px;">🔴 【4 大偏空 / 下跌狀態】(紅/橙系)</div>
    <div style="margin-bottom: 10px;">
        <div style="color: #ffffff !important; font-weight: bold; font-size: 14px;">5. ⚠️ 轉弱破位 (偏向續跌)</div>
        <div style="color: #f1f5f9 !important; font-size: 13px;">➔ 50MA 上方，RS ≥ 100 且 Mom &lt; 100，<b style="color: #f87171 !important;">但失守 20MA</b></div>
        <div style="color: #ffffff !important; font-size: 13px;"><span style="color: #f87171 !important; font-weight: bold;">【實戰涵義】</span>：失守短線生命線，動能快速下插，預視極大機會持續下跌。</div>
    </div>
    <div style="margin-bottom: 10px;">
        <div style="color: #ffffff !important; font-weight: bold; font-size: 14px;">6. ⚠️ 高位派發 (Distribution)</div>
        <div style="color: #f1f5f9 !important; font-size: 13px;">➔ 50MA 上方或半年大升，RS &lt; 100 且 Mom &lt; 100</div>
        <div style="color: #ffffff !important; font-size: 13px;"><span style="color: #f87171 !important; font-weight: bold;">【實戰涵義】</span>：歷史高位跳水跌出第一棍，頂部出貨防禦 (如 XLE 昨晚)。</div>
    </div>
    <div style="margin-bottom: 10px;">
        <div style="color: #ffffff !important; font-weight: bold; font-size: 14px;">7. 📉 深度衰退 (Lagging)</div>
        <div style="color: #f1f5f9 !important; font-size: 13px;">➔ 50MA 下方，RS &lt; 100 且 Mom &lt; 100</div>
        <div style="color: #ffffff !important; font-size: 13px;"><span style="color: #f87171 !important; font-weight: bold;">【實戰涵義】</span>：跌穿所有均線支撐，進入單邊主跌浪 (如 XLK)。</div>
    </div>
    <div>
        <div style="color: #ffffff !important; font-weight: bold; font-size: 14px;">8. 💀 弱勢陰跌 (Chronic Lagging)</div>
        <div style="color: #f1f5f9 !important; font-size: 13px;">➔ 50MA 下方，RS ≥ 100 且 Mom &lt; 100</div>
        <div style="color: #ffffff !important; font-size: 13px;"><span style="color: #f87171 !important; font-weight: bold;">【實戰涵義】</span>：死貓反彈後再破底，長期深陷泥潭陰跌數月 (如 XSD)。</div>
    </div>
</div>""", unsafe_allow_html=True)
                
        st.markdown("<br>", unsafe_allow_html=True)

        col_bar1, col_bar2 = st.columns(2)
        with col_bar1:
            mid_days_1 = st.selectbox("📊 選擇動態【中線】時間窗", [10, 22, 44, 66, 130], index=1, format_func=lambda x: f"{x} 個交易日 (" + ("兩週" if x==10 else "1個月" if x==22 else "2個月" if x==44 else "1季" if x==66 else "半年") + ")", key="mid_1")
        with col_bar2:
            short_days_1 = st.selectbox("📊 選擇動態【短線】時間窗", [1, 5, 10], index=1, format_func=lambda x: f"{x} 個交易日 (" + ("單日" if x==1 else "1週" if x==5 else "兩週") + ")", key="short_1")

        col_tree1, col_tree2 = st.columns(2)
        mid_label_1 = "1個月趨勢" if mid_days_1==22 else "2個月趨勢" if mid_days_1==44 else "1季趨勢" if mid_days_1==66 else "半年趨勢" if mid_days_1==130 else "兩週趨勢"
        short_label_1 = "1週爆發力" if short_days_1==5 else "單日爆發力" if short_days_1==1 else "兩週爆發力"
        
        tree_options = [
            '1日變化 (%)', '1週 (5日) (%)', '2週 (10日) (%)', 
            '1個月 (22日) (%)', '2個月 (44日) (%)', '1季 (66日) (%)', '半年 (130日) (%)'
        ]
        tree_display_map = {
            '1日變化 (%)': '1日', '1週 (5日) (%)': '1週 (5日)', '2週 (10日) (%)': '2週 (10日)',
            '1個月 (22日) (%)': '1個月 (22日)', '2個月 (44日) (%)': '2個月 (44日)',
            '1季 (66日) (%)': '1季 (66日)', '半年 (130日) (%)': '半年 (130日)'
        }
        
        with col_tree1:
            tree_size_1 = st.selectbox("🗺️ 熱力圖方塊【大細】代表", tree_options, index=3, format_func=lambda x: tree_display_map[x], key="tree_s_1")
        with col_tree2:
            tree_color_1 = st.selectbox("🗺️ 熱力圖方塊【顏色】代表", tree_options, index=1, format_func=lambda x: tree_display_map[x], key="tree_c_1")

        col_rrg1, col_rrg2 = st.columns(2)
        with col_rrg1: tail_3 = st.selectbox("🐍 選擇動態軌跡時間窗 (SPY 基準)", [1, 5, 10, 20, 40], index=2, key="tail_3")
        with col_rrg2: smooth_3 = st.selectbox("⚙️ RRG 計算靈敏度 (SPY 基準)", [10, 14, 20], index=1, key="smooth_3")
        
        _, comb_scatter = calculate_rrg_metrics_8_status(price_data, combined_series, window=smooth_3, benchmark='SPY', tail_len=tail_3)
        plot_rrg_chart(comb_scatter, f"全球 64 大板塊 RRG 星盤 (基準: SPY)")
        
        comb_mom = calculate_momentum_table(combined_series, mid_days_1, short_days_1)
        render_momentum_section(comb_mom, comb_scatter, "全球 64 大混戰", mid_label_1, short_label_1, tree_size_1, tree_color_1)
        st.markdown("<hr style='border:1px dashed #334155; margin: 30px 0;'>", unsafe_allow_html=True)

        # =========================================================================
        # 🦅 展區二：大鱷跨資產預警星盤 (以 TLT 為基準)
        # =========================================================================
        st.markdown("<h3 style='color:#ff3344;'>🦅 展區二：大鱷跨資產預警星盤 (以 TLT 為基準)</h3>", unsafe_allow_html=True)
        
        col_bar3, col_bar4 = st.columns(2)
        with col_bar3:
            mid_days_2 = st.selectbox("📊 選擇動態【中線】時間窗", [10, 22, 44, 66, 130], index=1, format_func=lambda x: f"{x} 個交易日 (" + ("兩週" if x==10 else "1個月" if x==22 else "2個月" if x==44 else "1季" if x==66 else "半年") + ")", key="mid_2")
        with col_bar4:
            short_days_2 = st.selectbox("📊 選擇動態【短線】時間窗", [1, 5, 10], index=1, format_func=lambda x: f"{x} 個交易日 (" + ("單日" if x==1 else "1週" if x==5 else "兩週") + ")", key="short_2")

        mid_label_2 = "1個月趨勢" if mid_days_2==22 else "2個月趨勢" if mid_days_2==44 else "1季趨勢" if mid_days_2==66 else "半年趨勢" if mid_days_2==130 else "兩週趨勢"
        short_label_2 = "1週爆發力" if short_days_2==5 else "單日爆發力" if short_days_2==1 else "兩週爆發力"
        
        col_tree3, col_tree4 = st.columns(2)
        with col_tree3:
            tree_size_2 = st.selectbox("🗺️ 熱力圖方塊【大細】代表", tree_options, index=3, format_func=lambda x: tree_display_map[x], key="tree_s_2")
        with col_tree4:
            tree_color_2 = st.selectbox("🗺️ 熱力圖方塊【顏色】代表", tree_options, index=1, format_func=lambda x: tree_display_map[x], key="tree_c_2")

        col_rrg3, col_rrg4 = st.columns(2)
        with col_rrg3: tail_4 = st.selectbox("🐍 選擇動態軌跡時間窗 (TLT 基準)", [1, 5, 10, 20, 40], index=2, key="tail_4")
        with col_rrg4: smooth_4 = st.selectbox("⚙️ RRG 計算靈敏度 (TLT 基準)", [10, 14, 20], index=1, key="smooth_4")
        
        _, ulti_scatter = calculate_rrg_metrics_8_status(price_data, ultimate_series, window=smooth_4, benchmark='TLT', tail_len=tail_4)
        plot_rrg_chart(ulti_scatter, f"🔥 跨資產宏觀生死共振 (基準: TLT 美債)")
        
        ulti_mom = calculate_momentum_table(ultimate_series, mid_days_2, short_days_2)
        render_momentum_section(ulti_mom, ulti_scatter, "跨資產預警", mid_label_2, short_label_2, tree_size_2, tree_color_2)
        
    st.divider()

    st.markdown("## 🦅 爺爺壓箱底傳授：2026 九維跨資產共振 (The Macro End-Game)")
    st.markdown("展區二係華爾街頂級大鱷嘅**「抄底與逃頂核按鈕」**。呢個圖**唔係同 SPY 比較，而係同 TLT (20年期國債/終極避險資產) 比較！**\n\n2026 年宏觀已由 **AI 算力 (SMH)、核能/鈾礦 (URA) 與 地緣軍工 (ITA)** 主導，佢哋已經加入生死共振監測網！")
    
    st.markdown("### 🔥 【核按鈕用法】：")
    st.markdown("* **終極逃頂信號 (Crash Warning)**：當你見到 SPY, HYG, COPX, BTC-USD 呢幾條蛇，集體由右邊急轉彎，插水進入「落後區 (紅)」（即係跑輸 TLT），代表全球大資金正在瘋狂拋售高風險資產，湧入美債避險。**大崩盤即將來臨，清倉保命！**")
    st.markdown("* **終極抄底信號 (Generational Buy)**：當大市一片恐慌，但你見到 HYG (垃圾債) 同 BTC 率先由「落後區」抬頭，衝入「改善區 (藍)」甚至「領先區 (綠)」，代表大鱷已經開始暗中吸籌Risk-On。**呢個就係十年一遇嘅重倉抄底時機！**")

def render_page_2y():
    app()

if __name__ == "__main__":
    app()