"""
Filename: page_2m.py
Description: 🎡 艙房 2m：華爾街板塊輪動星盤 (Sector Rotation 工業級防崩旗艦版 · 8大趨勢感知 RRG ＋ 純白高對比指南)
- 🏛️ 【11 大傳統宏觀 GICS 板塊】
- ⚡ 【53 大前沿硬科技、細分產業主題與資源霸權】
- 🌐 【全球 64 大板塊同台大混戰 · 支援一鍵全覽與 4 大快捷切換】
- 🦅 【大鱷跨資產預警星盤 (以 TLT 國債為基準) ＋ 2026 終極生死共振戰法】
- 🧠 【4升 vs 4跌：8大趨勢感知 RRG 狀態引擎】：
  * 4 升 (偏多)：🚀 加速爆發、🌟 回踩重啟、🌤️ 轉弱蓄勢 (偏向重啟)、🌱 觸底復甦
  * 4 跌 (偏空)：⚠️ 轉弱破位 (偏向續跌)、⚠️ 高位派發、📉 深度衰退、💀 弱勢陰跌
- 🎨 【雙重極致可讀性修復】：
  * 展區一 8 大狀態速查黑底指南：全面強制鎖定為高對比純白字 (#ffffff !important)，絕不發黑
  * 全展區數據表百分比：正數採用深邃森林綠 (#008000)，負數深緋紅 (#dc2626)，白底閱讀清晰銳利
- 🏷️ 【柱狀圖雙層排版修復】：底部 Margin 擴充至 220px，單行垂直向下延伸，中文在上方、英文在下方絕不重疊
- 📏 【數據表長度完全放開】：解除 600px 高度上限，64 板塊自然向下縱向平鋪全覽 (無內部滾動條)
- 🛡️ 【串流媒體防爆修復】：更名為「🎬 串流媒體與影視娛樂 (SUBZ)」，剔除 PARA，加裝 ±25% 防爆濾網
- 🛡️ 【工業級防崩加固】：多板塊隔離運算、時區純化、去除重複時間戳、RRG inf 數值免疫、Pandas 新舊相容
- 🗄️ 【64 大完整板塊成分股與代表 ETF 透明化查詢資料庫】
"""

import streamlit as st
import pandas as pd
import numpy as np
import yfinance as yf
import plotly.graph_objects as go

# =========================================================================
# 🏛️ 1. 完整板塊資料庫定義 (全部 64 大板塊均具備標準英文字代號)
# =========================================================================

MACRO_SECTORS = {
    'XLK': '科技 (XLK)', 'XLF': '金融 (XLF)', 'XLV': '醫療保健 (XLV)',
    'XLE': '能源 (XLE)', 'XLY': '非必需消費 (XLY)', 'XLP': '必需消費 (XLP)',
    'XLI': '工業 (XLI)', 'XLU': '公用事業 (XLU)', 'XLB': '原材料 (XLB)',
    'XLRE': '房地產 (XLRE)', 'XLC': '通訊服務 (XLC)'
}

MACRO_SECTOR_HOLDINGS = {
    '科技 (XLK)': {
        'category': '🏛️ 傳統宏觀 (GICS)',
        'etfs': ['XLK', 'VGT', 'IYW', 'QQQ'],
        'tickers': ['AAPL', 'MSFT', 'NVDA', 'AVGO', 'ORCL', 'CRM', 'ADBE', 'CSCO', 'AMD', 'QCOM']
    },
    '金融 (XLF)': {
        'category': '🏛️ 傳統宏觀 (GICS)',
        'etfs': ['XLF', 'VFH', 'KBE', 'KRE'],
        'tickers': ['JPM', 'BAC', 'WFC', 'GS', 'MS', 'BLK', 'C', 'AXP', 'V', 'MA']
    },
    '醫療保健 (XLV)': {
        'category': '🏛️ 傳統宏觀 (GICS)',
        'etfs': ['XLV', 'VHT', 'IBB', 'XBI'],
        'tickers': ['LLY', 'UNH', 'JNJ', 'ABBV', 'MRK', 'TMO', 'ABT', 'PFE', 'AMGN', 'ISRG']
    },
    '能源 (XLE)': {
        'category': '🏛️ 傳統宏觀 (GICS)',
        'etfs': ['XLE', 'VDE', 'OIH', 'XOP'],
        'tickers': ['XOM', 'CVX', 'COP', 'EOG', 'SLB', 'MPC', 'PSX', 'VLO', 'OXY', 'HAL']
    },
    '非必需消費 (XLY)': {
        'category': '🏛️ 傳統宏觀 (GICS)',
        'etfs': ['XLY', 'VCR', 'XRT'],
        'tickers': ['AMZN', 'TSLA', 'HD', 'MCD', 'NKE', 'LOW', 'BKNG', 'SBUX', 'TJX', 'TGT']
    },
    '必需消費 (XLP)': {
        'category': '🏛️ 傳統宏觀 (GICS)',
        'etfs': ['XLP', 'VDC', 'KXI'],
        'tickers': ['PG', 'COST', 'WMT', 'KO', 'PEP', 'PM', 'MDLZ', 'CL', 'MO', 'KMB']
    },
    '工業 (XLI)': {
        'category': '🏛️ 傳統宏觀 (GICS)',
        'etfs': ['XLI', 'VIS', 'ITA'],
        'tickers': ['GE', 'CAT', 'UNP', 'HON', 'RTX', 'BA', 'LMT', 'DE', 'UPS', 'FDX']
    },
    '公用事業 (XLU)': {
        'category': '🏛️ 傳統宏觀 (GICS)',
        'etfs': ['XLU', 'VPU', 'GRID'],
        'tickers': ['NEE', 'SO', 'DUK', 'CEG', 'VST', 'SRE', 'AEP', 'PEG', 'EXC', 'ED']
    },
    '原材料 (XLB)': {
        'category': '🏛️ 傳統宏觀 (GICS)',
        'etfs': ['XLB', 'VAW', 'LIT'],
        'tickers': ['LIN', 'SHW', 'FCX', 'APD', 'ECL', 'NEM', 'CTVA', 'DOW', 'DD', 'ALB']
    },
    '房地產 (XLRE)': {
        'category': '🏛️ 傳統宏觀 (GICS)',
        'etfs': ['XLRE', 'VNQ', 'IYR'],
        'tickers': ['PLD', 'AMT', 'EQIX', 'WELL', 'SPG', 'PSA', 'O', 'DLR', 'CCI', 'VICI']
    },
    '通訊服務 (XLC)': {
        'category': '🏛️ 傳統宏觀 (GICS)',
        'etfs': ['XLC', 'VOX', 'FCOM'],
        'tickers': ['META', 'GOOGL', 'GOOG', 'NFLX', 'DIS', 'CMCSA', 'TMUS', 'VZ', 'T', 'EA']
    }
}

FRONTIER_SECTORS = {
    # --- 1. AI 算力、硬體與半導體鏈 ---
    '🧠 GPU / AI 核心算力 (SMH)': {
        'category': '⚡ AI 算力與晶片硬體',
        'etfs': ['SMH', 'SOXX', 'USD'],
        'tickers': ['NVDA', 'TSM', 'AVGO', 'AMD', 'ARM', 'QCOM', 'MRVL', 'INTC']
    },
    '💻 CPU / 通用晶片處理器 (SOXX)': {
        'category': '⚡ AI 算力與晶片硬體',
        'etfs': ['SOXX', 'XSD'],
        'tickers': ['AMD', 'INTC', 'ARM', 'QCOM', 'AAPL', 'TXN', 'ADI', 'MCHP']
    },
    '💾 DRAM / 記憶體與存儲 (CHPX)': {
        'category': '⚡ AI 算力與晶片硬體',
        'etfs': ['CHPX'],
        'tickers': ['MU', 'WDC', 'STX', 'PSTG', 'NTAP']
    },
    '🔬 先進封裝與晶片製造設備 (AMAT)': {
        'category': '⚡ AI 算力與晶片硬體',
        'etfs': ['SMH', 'SOXX'],
        'tickers': ['ASML', 'AMAT', 'LRCX', 'KLAC', 'ONTO', 'CAMT', 'ICHR', 'UCTT', 'ACLS', 'FORM']
    },
    '⚡ 光模組、CPO 與光通信 (FOTO)': {
        'category': '⚡ AI 算力與晶片硬體',
        'etfs': ['FOTO'],
        'tickers': ['COHR', 'AAOI', 'FN', 'LITE', 'CIEN', 'CRDO', 'ALAB', 'MTSI', 'POET', 'GLW']
    },
    '🏭 AI 伺服器與硬體系統 (SMCI)': {
        'category': '⚡ AI 算力與晶片硬體',
        'etfs': [],
        'tickers': ['SMCI', 'DELL', 'HPE', 'ANET', 'PSTG', 'VRT', 'CDNS', 'SNPS']
    },
    '❄️ AI 液冷散熱與電源管理 (VRT)': {
        'category': '⚡ AI 算力與晶片硬體',
        'etfs': ['XLU', 'GRID'],
        'tickers': ['VRT', 'MOD', 'GEV', 'CAT', 'CMI', 'CEG', 'VST', 'NVT']
    },
    '⚡ 變壓器與電網升級基建 (GRID)': {
        'category': '⚡ AI 算力與晶片硬體',
        'etfs': ['GRID', 'PAVE'],
        'tickers': ['PWR', 'ETN', 'HUBB', 'ABB', 'EME', 'MYRG', 'GEV']
    },
    '📱 Edge AI / 端側晶片終端 (QCOM)': {
        'category': '⚡ AI 算力與晶片硬體',
        'etfs': [],
        'tickers': ['QCOM', 'AAPL', 'AVGO', 'SWKS', 'QRVO', 'LOGI', 'NXPI']
    },
    '🏢 數據中心與雲基建 (SRVR)': {
        'category': '⚡ AI 算力與晶片硬體',
        'etfs': ['SRVR', 'DTCR'],
        'tickers': ['EQIX', 'DLR', 'AMT', 'CCI', 'GDS', 'COR', 'VRT']
    },

    # --- 2. 軟體、SaaS 與網絡安全 ---
    '🧠 LLM 大模型與 AI 科技巨頭 (AIQ)': {
        'category': '💻 軟體、SaaS 與網絡安全',
        'etfs': ['AIQ', 'BOTZ', 'THNQ'],
        'tickers': ['MSFT', 'GOOGL', 'AMZN', 'META', 'ORCL', 'AAPL', 'PLTR']
    },
    '🛡️ 網絡安全與零信任 (CIBR)': {
        'category': '💻 軟體、SaaS 與網絡安全',
        'etfs': ['CIBR', 'HACK', 'BUG'],
        'tickers': ['CRWD', 'PANW', 'ZS', 'FTNT', 'NET', 'CYBR', 'OKTA', 'CHKP', 'S']
    },
    '☁️ 雲計算與企業級 SaaS (IGV)': {
        'category': '💻 軟體、SaaS 與網絡安全',
        'etfs': ['IGV', 'WCLD', 'CLOU'],
        'tickers': ['CRM', 'ADBE', 'NOW', 'WDAY', 'SNOW', 'DDOG', 'MDB', 'TEAM', 'PLTR', 'HUBS']
    },
    '💳 金融科技與數字支付 (FINX)': {
        'category': '💻 軟體、SaaS 與網絡安全',
        'etfs': ['FINX', 'IPAY'],
        'tickers': ['V', 'MA', 'PYPL', 'SQ', 'HOOD', 'AFRM', 'SOFI', 'TOST', 'FIS', 'GPN']
    },
    '🛠️ 基礎設施軟體與 DevOps (HCP)': {
        'category': '💻 軟體、SaaS 與網絡安全',
        'etfs': ['IGV'],
        'tickers': ['GTLB', 'HCP', 'ESTC', 'CFLT', 'MDB', 'DT', 'FSLY']
    },

    # --- 3. 前沿科技、機器人與空天出行 ---
    '🦾 機械人與智慧自動化 (BOTZ)': {
        'category': '🦾 前沿科技與機器人',
        'etfs': ['BOTZ', 'ROBO', 'IRBO'],
        'tickers': ['TSLA', 'ISRG', 'PATH', 'SYM', 'TER', 'ROK', 'NVDA']
    },
    '🚗 自動駕駛與 Robotaxi (IDRV)': {
        'category': '🦾 前沿科技與機器人',
        'etfs': ['IDRV', 'DRIV', 'HAIL'],
        'tickers': ['TSLA', 'GOOGL', 'MBLY', 'UBER', 'HSAI', 'AUR', 'LAZR', 'INVZ']
    },
    '🚁 低空飛行與 eVTOL 空運 (JOBY)': {
        'category': '🦾 前沿科技與機器人',
        'etfs': [],
        'tickers': ['JOBY', 'ACHR', 'EH', 'AUR', 'BLDE', 'EVTL']
    },
    '🌌 量子計算 (QTUM)': {
        'category': '🦾 前沿科技與機器人',
        'etfs': ['QTUM'],
        'tickers': ['IONQ', 'RGTI', 'QBTS', 'QUBT', 'ARQQ', 'HON', 'IBM', 'GOOGL', 'MSFT']
    },
    '🚀 商業太空與低軌通訊 (UFO)': {
        'category': '🦾 前沿科技與機器人',
        'etfs': ['UFO', 'ROKT', 'ARKX'],
        'tickers': ['RKLB', 'ASTS', 'LUNR', 'BKSY', 'PL', 'RDWR', 'SPCE', 'MNTS', 'VSAT', 'IRDM']
    },
    '🚀 顛覆性創新霸權 (ARKK)': {
        'category': '🦾 前沿科技與機器人',
        'etfs': ['ARKK', 'ARKW', 'ARKG', 'ARKF', 'ARKX'],
        'tickers': ['TSLA', 'ROKU', 'COIN', 'PLTR', 'U', 'PATH', 'CRSP']
    },

    # --- 4. 生技醫藥與前沿生命健康 ---
    '🧬 高彈性創新型生技 (XBI)': {
        'category': '🧬 生物科技與前沿醫藥',
        'etfs': ['XBI', 'IBB', 'ARKG'],
        'tickers': ['MRNA', 'BNTX', 'CRSP', 'VRTX', 'REGN', 'ILMN', 'BIIB', 'ALNY']
    },
    '💉 減肥藥與 GLP-1 產業鏈 (LLY)': {
        'category': '🧬 生物科技與前沿醫藥',
        'etfs': ['XLV'],
        'tickers': ['LLY', 'NVO', 'VKTX', 'ALT', 'GPCR', 'RVNC', 'TERN', 'AMGN', 'PFE']
    },
    '🩺 醫療器械與精準外科 (IHI)': {
        'category': '🧬 生物科技與前沿醫藥',
        'etfs': ['IHI', 'ARKG'],
        'tickers': ['ISRG', 'SYK', 'BSX', 'MDT', 'EW', 'ABT', 'DXCM', 'TMO']
    },
    '🧠 腦機介面與仿生神經 (BSX)': {
        'category': '🧬 生物科技與前沿醫藥',
        'etfs': [],
        'tickers': ['SYNA', 'TNDM', 'DXCM', 'INMD', 'NVRO', 'PRVA', 'BSX', 'MDT']
    },
    '🏥 醫療健康保險與服務 (IHF)': {
        'category': '🧬 生物科技與前沿醫藥',
        'etfs': ['IHF'],
        'tickers': ['UNH', 'ELV', 'CI', 'CVS', 'HUM', 'CNC']
    },

    # --- 5. 能源變革、核能與關鍵金屬資源 ---
    '⚛️ 核能、SMR 與鈾礦 (URA)': {
        'category': '⚡ 能源變革與金屬資源',
        'etfs': ['URA', 'URNM', 'NLR'],
        'tickers': ['CCJ', 'OKLO', 'SMR', 'LEU', 'UUUU', 'CEG', 'VST', 'BWXT']
    },
    '☀️ 清潔能源與太陽能 (ICLN)': {
        'category': '⚡ 能源變革與金屬資源',
        'etfs': ['ICLN', 'TAN', 'QCLN'],
        'tickers': ['FSLR', 'ENPH', 'SEDG', 'RUN', 'PLUG', 'NEE', 'CSIQ', 'BE']
    },
    '🔋 電動車與鋰電池鏈 (LIT)': {
        'category': '⚡ 能源變革與金屬資源',
        'etfs': ['LIT', 'DRIV', 'IDRV'],
        'tickers': ['TSLA', 'ALB', 'SQM', 'QS', 'FREY', 'ON', 'RIVN', 'LCID']
    },
    '🥇 金礦開採與貴金屬 (GDX)': {
        'category': '⚡ 能源變革與金屬資源',
        'etfs': ['GDX', 'GDXJ', 'RING'],
        'tickers': ['NEM', 'GOLD', 'AEM', 'KGC', 'AUY', 'AU', 'HMY']
    },
    '🥈 銀礦開採 (SIL)': {
        'category': '⚡ 能源變革與金屬資源',
        'etfs': ['SIL', 'SILJ'],
        'tickers': ['AG', 'PAAS', 'HL', 'CDE', 'FSM', 'MAG']
    },
    '🥉 銅礦與關鍵工業金屬 (COPX)': {
        'category': '⚡ 能源變革與金屬資源',
        'etfs': ['COPX', 'CPER', 'PICK'],
        'tickers': ['FCX', 'SCCO', 'ERO', 'TECK', 'HBM', 'BHP', 'RIO']
    },
    '🛢️ 石油開採與油服設備 (OIH)': {
        'category': '⚡ 能源變革與金屬資源',
        'etfs': ['OIH', 'XOP'],
        'tickers': ['SLB', 'HAL', 'BKR', 'EOG', 'OXY', 'FANG', 'DVN', 'COP']
    },
    '🧪 特種材料與稀土資源 (REMX)': {
        'category': '⚡ 能源變革與金屬資源',
        'etfs': ['REMX', 'LIT'],
        'tickers': ['MP', 'ALB', 'LIN', 'APD', 'SHW', 'ECL']
    },

    # --- 6. 地緣防務、特種產業與經濟民生 ---
    '⚔️ 國防軍工與尖端航太 (ITA)': {
        'category': '🛡️ 地緣防務與特種主題',
        'etfs': ['ITA', 'PPA', 'XAR'],
        'tickers': ['LMT', 'RTX', 'NOC', 'GD', 'BA', 'LHX', 'HII', 'TDG', 'AXON']
    },
    '🪙 區塊鏈與比特幣生態 (WGMI)': {
        'category': '🛡️ 地緣防務與特種主題',
        'etfs': ['WGMI', 'BLOK', 'DAPP', 'IBIT'],
        'tickers': ['COIN', 'MSTR', 'MARA', 'RIOT', 'CLSK', 'HOOD', 'HUT', 'CIFR']
    },
    '🛍️ 電商平台與數位消費 (FDN)': {
        'category': '🛡️ 地緣防務與特種主題',
        'etfs': ['FDN', 'IBUY'],
        'tickers': ['AMZN', 'MELI', 'BABA', 'PDD', 'SE', 'CHWY', 'DASH', 'SHOP', 'EBAY']
    },
    '🚚 現代交通物流與鐵路 (IYT)': {
        'category': '🛡️ 地緣防務與特種主題',
        'etfs': ['IYT'],
        'tickers': ['UNP', 'CSX', 'NSC', 'UPS', 'FDX', 'ODFL', 'JBHT']
    },
    '🌾 農業科技與糧食化肥 (MOO)': {
        'category': '🛡️ 地緣防務與特種主題',
        'etfs': ['MOO'],
        'tickers': ['DE', 'ADM', 'CTVA', 'MOS', 'CF', 'NTR', 'BG']
    },
    '💧 水資源與環境基建 (PHO)': {
        'category': '🛡️ 地緣防務與特種主題',
        'etfs': ['PHO', 'FIW'],
        'tickers': ['XYL', 'AWK', 'WMS', 'ECL', 'ROP', 'PNR']
    },
    '🎰 數位娛樂與在線遊戲 (HERO)': {
        'category': '🛡️ 地緣防務與特種主題',
        'etfs': ['HERO', 'BETZ'],
        'tickers': ['RBLX', 'EA', 'TTWO', 'DKNG', 'FLUT', 'NTES']
    },
    '🧲 被動元件與電子連接器 (TEL)': {
        'category': '🛡️ 地緣防務與特種主題',
        'etfs': [],
        'tickers': ['TEL', 'APH', 'VSH', 'LFUS', 'GLW']
    },
    '🏠 住宅建築與地產營造 (ITB)': {
        'category': '🛡️ 地緣防務與特種主題',
        'etfs': ['ITB', 'XHB'],
        'tickers': ['DHI', 'LEN', 'NVR', 'PHM', 'TOL', 'HD', 'LOW']
    },
    '✈️ 航空交通與休閒旅遊 (JETS)': {
        'category': '🛡️ 地緣防務與特種主題',
        'etfs': ['JETS'],
        'tickers': ['DAL', 'UAL', 'AAL', 'LUV', 'CCL', 'RCL', 'NCLH']
    },
    '🛡️ 保險經紀與風險管理 (KIE)': {
        'category': '🛡️ 地緣防務與特種主題',
        'etfs': ['KIE', 'IAK'],
        'tickers': ['PGR', 'CB', 'TRV', 'ALL', 'AIG', 'AON', 'MMC']
    },
    '🏦 美國區域性商業銀行 (KRE)': {
        'category': '🛡️ 地緣防務與特種主題',
        'etfs': ['KRE', 'KBE'],
        'tickers': ['TFC', 'PNC', 'USB', 'FITB', 'MTB', 'KEY', 'CFG']
    },
    '🍔 連鎖餐飲與生活消費 (PBJ)': {
        'category': '🛡️ 地緣防務與特種主題',
        'etfs': ['PBJ'],
        'tickers': ['MCD', 'SBUX', 'CMG', 'YUM', 'DRI', 'QSR', 'WING']
    },
    # 🌟 正名為「🎬 串流媒體與影視娛樂 (SUBZ)」，剔除收購異常股 PARA，ETF 指向 SUBZ
    '🎬 串流媒體與影視娛樂 (SUBZ)': {
        'category': '🛡️ 地緣防務與特種主題',
        'etfs': ['SUBZ'],
        'tickers': ['NFLX', 'SPOT', 'DIS', 'ROKU', 'WBD']
    },
    '📦 包裝材料與林業資源 (WOOD)': {
        'category': '🛡️ 地緣防務與特種主題',
        'etfs': ['WOOD'],
        'tickers': ['IP', 'PKG', 'BALL', 'CCK', 'AVY']
    },
    '🚗 傳統汽車製造與配件 (CARZ)': {
        'category': '🛡️ 地緣防務與特種主題',
        'etfs': ['CARZ'],
        'tickers': ['GM', 'F', 'STLA', 'APTV', 'BWA', 'LEA', 'MGA']
    },
    '🧱 重型基建材料與水泥 (PAVE)': {
        'category': '🛡️ 地緣防務與特種主題',
        'etfs': ['PAVE'],
        'tickers': ['VMC', 'MLM', 'CRH', 'SUM', 'EXP']
    },
    '💼 企業人力與外包服務 (ADP)': {
        'category': '🛡️ 地緣防務與特種主題',
        'etfs': [],
        'tickers': ['ADP', 'PAYX', 'ACN', 'IT', 'CTSH', 'EPAM']
    },
    '🔌 類比與電源半導體 (XSD)': {
        'category': '🛡️ 地緣防務與特種主題',
        'etfs': ['XSD', 'SOXX'],
        'tickers': ['TXN', 'ADI', 'NXPI', 'MCHP', 'ON', 'MPWR']
    }
}

ALL_64_SECTOR_HOLDINGS = {**MACRO_SECTOR_HOLDINGS, **FRONTIER_SECTORS}

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

# =========================================================================
# ⚙️ 2. 全量數據抓取與合成引擎 (加固防崩純化版)
# =========================================================================
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
        if raw is None or raw.empty:
            return pd.DataFrame()
            
        if isinstance(raw.columns, pd.MultiIndex):
            if 'Close' in raw.columns.levels[0]:
                data = raw['Close'].copy()
            else:
                data = raw.xs('Close', level='Price', axis=1) if 'Price' in raw.columns.names else raw.iloc[:, 0]
        elif 'Close' in raw:
            data = raw[['Close']].copy()
        else:
            data = raw.copy()
            
        if hasattr(data.index, 'tz') and data.index.tz is not None:
            data.index = data.index.tz_localize(None).normalize()
            
        # 去除重複時間戳
        data = data[~data.index.duplicated(keep='first')]
        data = data.dropna(how='all', axis=1).ffill().bfill()
        return data
    except Exception as e:
        print(f"❌ 行情下載異常: {e}")
        return pd.DataFrame()

def calculate_momentum_table(series_dict):
    data = []
    for name, series in series_dict.items():
        if series is None or series.empty:
            continue
        s = series.dropna()
        if len(s) >= 22:
            p_now = s.iloc[-1]
            p_1d = s.iloc[-2]
            p_1w = s.iloc[-6]
            p_1m = s.iloc[-22]
            
            chg_1d = (p_now / p_1d - 1.0) * 100.0 if (p_1d > 0 and pd.notnull(p_1d)) else 0.0
            chg_1w = (p_now / p_1w - 1.0) * 100.0 if (p_1w > 0 and pd.notnull(p_1w)) else 0.0
            chg_1m = (p_now / p_1m - 1.0) * 100.0 if (p_1m > 0 and pd.notnull(p_1m)) else 0.0
            
            chg_1d = 0.0 if (np.isinf(chg_1d) or np.isnan(chg_1d)) else chg_1d
            chg_1w = 0.0 if (np.isinf(chg_1w) or np.isnan(chg_1w)) else chg_1w
            chg_1m = 0.0 if (np.isinf(chg_1m) or np.isnan(chg_1m)) else chg_1m
            
            data.append({
                '板塊': name, '1日變化 (%)': chg_1d, '1週變化 (%)': chg_1w, '1個月變化 (%)': chg_1m
            })
    df = pd.DataFrame(data)
    if not df.empty:
        df = df.sort_values(by='1週變化 (%)', ascending=False)
    return df

def calculate_rrg_metrics(price_df, sector_series_dict, window=14, benchmark='SPY'):
    if price_df.empty or benchmark not in price_df.columns:
        return pd.DataFrame(), pd.DataFrame()
        
    bench_price = price_df[benchmark]
    if bench_price.empty or (bench_price <= 0).all():
        return pd.DataFrame(), pd.DataFrame()

    rs_ratio_dict = {}
    rs_mom_dict = {}

    for name, series in sector_series_dict.items():
        if series is None or series.empty:
            continue
        aligned = pd.concat([series, bench_price], axis=1).dropna()
        if len(aligned) < window * 2:
            continue
        
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

    df_ratio = pd.DataFrame(rs_ratio_dict).dropna(how='all')
    df_mom = pd.DataFrame(rs_mom_dict).dropna(how='all')
    return df_ratio, df_mom

# =========================================================================
# 🧠 8大趨勢感知 RRG 狀態引擎 (4升 vs 4跌 嚴密鏡像對稱)
# =========================================================================
def get_trend_aware_8_status_dict(rs_ratio, rs_mom, sector_series_dict):
    if rs_ratio is None or rs_mom is None or rs_ratio.empty or rs_mom.empty:
        return {}
    status_dict = {}
    
    for col in rs_ratio.columns:
        if col in rs_mom.columns and col in sector_series_dict:
            s_r = rs_ratio[col].dropna()
            s_m = rs_mom[col].dropna()
            s_price = sector_series_dict[col].dropna()
            
            if not s_r.empty and not s_m.empty and len(s_price) >= 50:
                curr_ratio = s_r.iloc[-1]
                curr_mom = s_m.iloc[-1]
                p_now = s_price.iloc[-1] if not s_price.empty else 100.0
                
                # 均線指標安全取值
                ma20 = s_price.rolling(20, min_periods=5).mean().iloc[-1] if len(s_price) >= 20 else p_now
                ma50 = s_price.rolling(50, min_periods=10).mean().iloc[-1] if len(s_price) >= 50 else p_now
                is_above_ma20 = bool(p_now >= ma20) if pd.notnull(ma20) else True
                is_above_ma50 = bool(p_now >= ma50) if pd.notnull(ma50) else True
                
                # 動能斜率與半年動量
                mom_slope = s_m.iloc[-1] - s_m.iloc[-3] if len(s_m) >= 3 else 0.0
                ret_half = 0.0
                if len(s_price) >= 130 and s_price.iloc[-130] > 0 and pd.notnull(s_price.iloc[-130]):
                    ret_half = ((p_now / s_price.iloc[-130]) - 1.0) * 100.0
                if np.isnan(ret_half) or np.isinf(ret_half):
                    ret_half = 0.0

                # 4 升 (偏多) vs 4 跌 (偏空) 嚴密鏡像對稱判定
                if curr_ratio >= 100.0 and curr_mom >= 100.0:
                    status_dict[col] = "🚀 加速爆發 (Leading)" if is_above_ma50 else "🌱 觸底復甦 (Accumulation)"
                elif curr_ratio < 100.0 and curr_mom >= 100.0:
                    status_dict[col] = "🌟 回踩重啟 (Rebounding)" if is_above_ma50 else "🌱 觸底復甦 (Accumulation)"
                elif curr_ratio >= 100.0 and curr_mom < 100.0:
                    if is_above_ma50:
                        status_dict[col] = "🌤️ 轉弱蓄勢 (偏向重啟)" if (is_above_ma20 and mom_slope >= -0.5) else "⚠️ 轉弱破位 (偏向續跌)"
                    else:
                        status_dict[col] = "💀 弱勢陰跌 (Chronic Lagging)"
                else:  # curr_ratio < 100.0 and curr_mom < 100.0
                    status_dict[col] = "⚠️ 高位派發 (Distribution)" if (is_above_ma50 or ret_half > 15.0) else "📉 深度衰退 (Lagging)"
                        
    return status_dict

# =========================================================================
# 🎨 3. 繪圖核心：柱狀圖 + 數據表 (帶 8大狀態徽章 ＋ 自然縱向展開) + RRG星盤
# =========================================================================
def render_momentum_section(mom_df, section_title, rs_ratio=None, rs_mom=None, sector_series_dict=None):
    if mom_df is None or mom_df.empty: 
        return
    st.markdown("#### 📊 最新板塊動能雷達 (近期資金湧入方向)")
    fig_bar = go.Figure()
    
    # 單行連續排列，文字順暢自然
    fig_bar.add_trace(go.Bar(
        x=mom_df['板塊'], y=mom_df['1個月變化 (%)'],
        name='1個月趨勢 (中線資金)', marker_color='#00d2ff',
        hovertemplate='%{y:.2f}%<extra></extra>'
    ))
    
    colors_1w = ['#00ff88' if (pd.notnull(val) and val > 0) else '#ff3344' for val in mom_df['1週變化 (%)']]
    fig_bar.add_trace(go.Bar(
        x=mom_df['板塊'], y=mom_df['1週變化 (%)'],
        name='1週爆發力 (短線資金)', marker_color=colors_1w,
        hovertemplate='%{y:.2f}%<extra></extra>'
    ))
    
    # 🌟 底部預留 220px 巨大空間，高度擴充至 680px，單行垂直排開絕不橫向撞車
    fig_bar.update_layout(
        barmode='group',
        title=dict(text=f"🎯 {section_title} 板塊資金動能對比", font=dict(color="#ffffff", size=18, family="Arial Black")),
        font=dict(color="#ffffff", size=12),
        template="plotly_dark",
        height=680,
        margin=dict(l=20, r=20, t=55, b=220),
        legend=dict(
            orientation="h",
            yanchor="bottom",
            y=1.02,
            xanchor="right",
            x=1,
            font=dict(size=13, color="#ffffff", family="Arial Black"),
            bgcolor="rgba(23, 27, 38, 0.8)",
            bordercolor="#334155",
            borderwidth=1
        ),
        paper_bgcolor="#171b26",
        plot_bgcolor="#171b26",
        hovermode="x unified"
    )
    
    fig_bar.update_xaxes(
        tickangle=-90,
        automargin=True,
        tickfont=dict(color="#e2e8f0", size=11),
        gridcolor="#222834",
        zeroline=False
    )
    fig_bar.update_yaxes(tickfont=dict(color="#e2e8f0", size=11), gridcolor="#222834", zerolinecolor="#475569")
    st.plotly_chart(fig_bar, use_container_width=True)

    # ----------------------------------------------------
    # 📋 詳細資金流向數據表 (解除 600px 封印，無限縱向自然展開！)
    # ----------------------------------------------------
    st.markdown("#### 📋 詳細資金流向與真實 RRG 狀態全景數據表")
    
    df_display = mom_df.copy()
    if rs_ratio is not None and rs_mom is not None and sector_series_dict is not None:
        status_dict = get_trend_aware_8_status_dict(rs_ratio, rs_mom, sector_series_dict)
        df_display['RRG 狀態'] = df_display['板塊'].map(status_dict).fillna("⚪ 觀望整理")
    
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
    
    # 🌟 徹底拔除 min(600, ...) 限制！根據板塊總數自然縱向平鋪全覽
    dynamic_height = max(180, int((len(df_display) * 36) + 48))
    
    cols_order = ['板塊', '1日變化 (%)', '1週變化 (%)', '1個月變化 (%)']
    if 'RRG 狀態' in df_display.columns:
        cols_order.append('RRG 狀態')
    df_display = df_display[cols_order]

    styler = df_display.style
    map_func = getattr(styler, "map", getattr(styler, "applymap", None))
    pct_cols = ['1日變化 (%)', '1週變化 (%)', '1個月變化 (%)']
    
    if map_func:
        styled_df = map_func(color_pct, subset=pct_cols)
        if 'RRG 狀態' in df_display.columns:
            styled_df = map_func(color_status_8, subset=['RRG 狀態'])
        styled_df = styled_df.format({col: '{:.2f}%' for col in pct_cols})
    else:
        styled_df = styler
        
    st.dataframe(styled_df, use_container_width=True, height=dynamic_height, hide_index=True)

def plot_rrg_chart(rs_ratio, rs_mom, tail_length, chart_title):
    if rs_ratio.empty or rs_mom.empty: 
        return

    fig = go.Figure()

    colors = [
        '#00ff88', '#ff3344', '#00e5ff', '#ffaa00', '#ab47bc', '#ffeb3b', '#76ff03', '#f06292',
        '#ff9800', '#00bcd4', '#e91e63', '#00e676', '#9c27b0', '#673ab7', '#3f51b5', '#2196f3',
        '#03a9f4', '#00bac7', '#009688', '#4caf50', '#8bc34a', '#cddc39', '#ffc107', '#ff5722',
        '#e040fb', '#ff1744', '#18ffff', '#ffd600', '#ff80ab', '#82b1ff'
    ]
    text_positions = ['top center', 'bottom center', 'top right', 'bottom left', 'middle right', 'middle left', 'top left', 'bottom right']

    fig.add_shape(type="rect", x0=100, y0=100, x1=200, y1=200, fillcolor="rgba(0, 255, 136, 0.05)", layer="below", line_width=0)
    fig.add_shape(type="rect", x0=100, y0=0, x1=200, y1=100, fillcolor="rgba(255, 235, 59, 0.05)", layer="below", line_width=0)
    fig.add_shape(type="rect", x0=0, y0=0, x1=100, y1=100, fillcolor="rgba(255, 51, 68, 0.05)", layer="below", line_width=0)
    fig.add_shape(type="rect", x0=0, y0=100, x1=100, y1=200, fillcolor="rgba(0, 229, 255, 0.05)", layer="below", line_width=0)
    fig.add_vline(x=100, line_width=1.5, line_color="#64748b", line_dash="dash")
    fig.add_hline(y=100, line_width=1.5, line_color="#64748b", line_dash="dash")
    
    fig.add_annotation(x=0.98, y=0.98, text="領先 (Leading)", showarrow=False, xref="paper", yref="paper", font=dict(color="#00ff88", size=24, family="Arial Black"), opacity=0.3)
    fig.add_annotation(x=0.98, y=0.02, text="轉弱 (Weakening)", showarrow=False, xref="paper", yref="paper", font=dict(color="#ffeb3b", size=24, family="Arial Black"), opacity=0.3)
    fig.add_annotation(x=0.02, y=0.02, text="落後 (Lagging)", showarrow=False, xref="paper", yref="paper", font=dict(color="#ff3344", size=24, family="Arial Black"), opacity=0.3)
    fig.add_annotation(x=0.02, y=0.98, text="改善 (Improving)", showarrow=False, xref="paper", yref="paper", font=dict(color="#00e5ff", size=24, family="Arial Black"), opacity=0.3)

    for i, col in enumerate(rs_ratio.columns):
        if col not in rs_mom.columns:
            continue
        x_data = rs_ratio[col].dropna().tail(tail_length).values
        y_data = rs_mom[col].dropna().tail(tail_length).values
        if len(x_data) > 1 and len(y_data) > 1:
            fig.add_trace(go.Scatter(
                x=x_data, y=y_data, mode='lines',
                line=dict(color=colors[i % len(colors)], width=1.2),
                showlegend=False, hoverinfo='skip'
            ))

    for i, col in enumerate(rs_ratio.columns):
        if col not in rs_mom.columns:
            continue
        s_x = rs_ratio[col].dropna()
        s_y = rs_mom[col].dropna()
        if s_x.empty or s_y.empty:
            continue
        last_x = s_x.iloc[-1]
        last_y = s_y.iloc[-1]
        
        fig.add_trace(go.Scatter(
            x=[last_x], y=[last_y], mode='markers+text',
            marker=dict(color=colors[i % len(colors)], size=11, line=dict(color='#ffffff', width=1.5)),
            text=[f" <b>{col}</b> "], textposition=text_positions[i % len(text_positions)],
            textfont=dict(color="#ffffff", size=12, family="Arial Black"),
            name=col, hovertemplate=f"<b>{col}</b><br>RS-Ratio: %{{x:.2f}}<br>RS-Mom: %{{y:.2f}}<extra></extra>"
        ))

    # 🛡️ 安全邊界計算：嚴格排除 inf 與 -inf，徹底防止 Plotly 軸線崩潰！
    tail_r = rs_ratio.tail(tail_length).values.flatten()
    tail_m = rs_mom.tail(tail_length).values.flatten()
    valid_r = [v for v in tail_r if pd.notnull(v) and not np.isinf(v)]
    valid_m = [v for v in tail_m if pd.notnull(v) and not np.isinf(v)]
    
    min_x = min(valid_r) if valid_r else 96.0
    max_x = max(valid_r) if valid_r else 104.0
    min_y = min(valid_m) if valid_m else 96.0
    max_y = max(valid_m) if valid_m else 104.0
    
    padding = 2.5
    fig.update_layout(
        title=dict(text=f"🎡 {chart_title}", font=dict(color="#00e5ff", size=22, family="Arial Black")),
        font=dict(color="#ffffff"), template="plotly_dark", height=950, margin=dict(l=50, r=50, t=70, b=60),
        paper_bgcolor="#11141a", plot_bgcolor="#11141a", hovermode="closest", showlegend=True,
        legend=dict(orientation="h", yanchor="bottom", y=-0.14, xanchor="center", x=0.5, font=dict(size=12, color="#ffffff"), bgcolor="rgba(17, 20, 26, 0.8)", bordercolor="#334155", borderwidth=1)
    )
    fig.update_xaxes(title_text="RS-Ratio (相對強度 →)", title_font=dict(color="#ffffff"), tickfont=dict(color="#e2e8f0"), range=[min(min_x - padding, 95.0), max(max_x + padding, 105.0)], showgrid=True, gridcolor='#222834', zeroline=False)
    fig.update_yaxes(title_text="RS-Momentum (相對動能 ↑)", title_font=dict(color="#ffffff"), tickfont=dict(color="#e2e8f0"), range=[min(min_y - padding, 95.0), max(max_y + padding, 105.0)], showgrid=True, gridcolor='#222834', zeroline=False)
    st.plotly_chart(fig, use_container_width=True)

# =========================================================================
# 🚀 4. 主頁面渲染函數 (render_page_2m)
# =========================================================================
def render_page_2m():
    st.markdown("<h2 style='color:#00e5ff; font-family:Arial Black;'>🎡 艙房 2m：華爾街板塊輪動星盤 (Sector Rotation 終極全景版)</h2>", unsafe_allow_html=True)
    st.markdown("<p style='color:#cbd5e1;'>大鱷專用：資金從來唔會休息，只會由一個板塊流去另一個板塊。捕捉全美 <b>64 大板塊</b> 資金輪動，比人早一步埋伏下一個爆升點！</p>", unsafe_allow_html=True)
    st.markdown("<hr style='border:1px solid #334155; margin-bottom:20px;'>", unsafe_allow_html=True)

    col_a, col_b = st.columns([7.5, 2.5])
    with col_b:
        if st.button("🔄 強制刷新資金大數據", use_container_width=True):
            load_all_market_data.clear()
            st.rerun()
            
    with st.spinner("📡 正在全量掃描並合成全球 64 大板塊實時大數據 (涵蓋多 ETF 去重籃子與自建 100 點純血指數)..."):
        price_data = load_all_market_data()

    if price_data.empty:
        st.error("❌ 無法取得價格數據，請稍後重試。")
        return

    # --- 數據預處理 ---
    macro_series = {name: price_data[symbol] for symbol, name in MACRO_SECTORS.items() if symbol in price_data.columns}
    macro_mom_df = calculate_momentum_table(macro_series)
    
    frontier_series = {}
    for name, info in FRONTIER_SECTORS.items():
        valid_cols = [c for c in info.get('tickers', []) if c in price_data.columns]
        if 'etfs' in info:
            for etf in info['etfs']:
                if etf in price_data.columns and etf not in valid_cols:
                    valid_cols.append(etf)
                    
        if valid_cols:
            # 🛡️ 加裝單日 ±25% 防爆截斷濾網與 inf 安全清洗，徹底防止壞數據炸飛板塊
            pct_raw = price_data[valid_cols].pct_change().replace([np.inf, -np.inf], 0.0)
            clean_pct = pct_raw.clip(lower=-0.25, upper=0.25).mean(axis=1).fillna(0.0)
            frontier_series[name] = (1.0 + clean_pct).cumprod() * 100.0
            
    frontier_mom_df = calculate_momentum_table(frontier_series)
    combined_series = {**macro_series, **frontier_series}
    combined_mom_df = calculate_momentum_table(combined_series)
    ultimate_series = {name: price_data[symbol] for name, symbol in ULTIMATE_SECTORS.items() if symbol in price_data.columns}
    ultimate_mom_df = calculate_momentum_table(ultimate_series)

    # =================================================================
    # 🎯 展區 1：傳統宏觀 11 大板塊 (純白高對比 8大狀態指南)
    # =================================================================
    st.markdown("<h3 style='color:#00ff88;'>🏛️ 展區一：傳統宏觀 11 大板塊 (GICS 標準)</h3>", unsafe_allow_html=True)
    
    # 🌟 8 大趨勢感知狀態實戰速查指南卡片 (全域 CSS 強制穿透，100% 高對比純白字)
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
    st.markdown("<p style='color:#cbd5e1; font-weight:bold;'>⚙️ 調整 [展區一] 星盤與 RRG 靈敏度參數：</p>", unsafe_allow_html=True)
    col1_1, col1_2 = st.columns(2)
    with col1_1: tail_1 = st.selectbox("🐍 選擇動態軌跡時間窗", [1, 5, 10, 20, 40], index=2, key="tail_1")
    with col1_2: smooth_1 = st.selectbox("⚙️ RRG 計算靈敏度", [10, 14, 20], index=1, key="smooth_1")
    macro_ratio, macro_mom = calculate_rrg_metrics(price_data, macro_series, window=smooth_1, benchmark='SPY')
    
    render_momentum_section(macro_mom_df, "傳統宏觀 11 大", macro_ratio, macro_mom, macro_series)
    plot_rrg_chart(macro_ratio, macro_mom, tail_1, f"傳統宏觀 11 大板塊 RRG 星盤 (尾巴: {tail_1}天, 平滑: {smooth_1}天)")
    st.markdown("<hr style='border:1px dashed #334155; margin: 30px 0;'>", unsafe_allow_html=True)

    # =================================================================
    # 🎯 展區 2：前沿 53 大硬科技、細分產業與資源霸權
    # =================================================================
    st.markdown("<h3 style='color:#00e5ff;'>⚡ 展區二：前沿 53 大硬科技、細分產業主題與資源霸權</h3>", unsafe_allow_html=True)
    
    categories = [
        "全部 53 個前沿主題",
        "⚡ AI 算力與晶片硬體",
        "💻 軟體、SaaS 與網絡安全",
        "🦾 前沿科技與機器人",
        "🧬 生物科技與前沿醫藥",
        "⚡ 能源變革與金屬資源",
        "🛡️ 地緣防務與特種主題"
    ]
    sel_cat = st.selectbox("🎯 篩選前沿細分領域視角：", categories, index=0)
    
    if sel_cat == "全部 53 個前沿主題":
        filtered_frontier_series = frontier_series
    else:
        filtered_names = [k for k, v in FRONTIER_SECTORS.items() if v.get('category') == sel_cat]
        filtered_frontier_series = {k: frontier_series[k] for k in filtered_names if k in frontier_series}

    filtered_frontier_mom = calculate_momentum_table(filtered_frontier_series)
    
    st.markdown(f"<p style='color:#cbd5e1; font-weight:bold;'>⚙️ 調整 [{sel_cat}] 星盤與 RRG 靈敏度參數：</p>", unsafe_allow_html=True)
    col2_1, col2_2 = st.columns(2)
    with col2_1: tail_2 = st.selectbox("🐍 選擇動態軌跡時間窗", [1, 5, 10, 20, 40], index=2, key="tail_2")
    with col2_2: smooth_2 = st.selectbox("⚙️ RRG 計算靈敏度", [10, 14, 20], index=1, key="smooth_2")
    frontier_ratio, frontier_mom = calculate_rrg_metrics(price_data, filtered_frontier_series, window=smooth_2, benchmark='SPY')
    
    render_momentum_section(filtered_frontier_mom, f"前沿細分 ({sel_cat})", frontier_ratio, frontier_mom, filtered_frontier_series)
    plot_rrg_chart(frontier_ratio, frontier_mom, tail_2, f"{sel_cat} RRG 星盤 (尾巴: {tail_2}天, 平滑: {smooth_2}天)")
    st.markdown("<hr style='border:1px dashed #334155; margin: 30px 0;'>", unsafe_allow_html=True)

    # =================================================================
    # 🎯 展區 3：全球 64 大板塊同台大混戰 (全景對比 · 帶一鍵全覽)
    # =================================================================
    st.markdown("<h3 style='color:#ffd700;'>🌐 展區三：全球 64 大板塊同台大混戰 (全景對比)</h3>", unsafe_allow_html=True)
    st.markdown("<p style='color:#cbd5e1;'>點擊下方按鈕可 <b>一鍵全覽 64 大板塊</b>，或一鍵切換焦點板塊，省去逐個勾選的繁瑣操作！</p>", unsafe_allow_html=True)

    all_64_names = list(combined_series.keys())
    top_16_names = combined_mom_df['板塊'].head(16).tolist() if len(combined_mom_df) >= 16 else all_64_names[:16]
    macro_11_names = list(MACRO_SECTORS.values())

    if "p2m_chosen_sectors" not in st.session_state:
        st.session_state["p2m_chosen_sectors"] = all_64_names

    def set_chosen_sectors(target_list):
        st.session_state["p2m_chosen_sectors"] = target_list

    c_btn1, c_btn2, c_btn3, c_btn4 = st.columns(4)
    with c_btn1:
        st.button("🌐 一鍵全覽 (64 大板塊全開)", on_click=set_chosen_sectors, args=(all_64_names,), use_container_width=True)
    with c_btn2:
        st.button("🔥 動能最強 Top 16", on_click=set_chosen_sectors, args=(top_16_names,), use_container_width=True)
    with c_btn3:
        st.button("🏛️ 傳統宏觀 11 大", on_click=set_chosen_sectors, args=(macro_11_names,), use_container_width=True)
    with c_btn4:
        st.button("🧹 一鍵清空", on_click=set_chosen_sectors, args=([],), use_container_width=True)

    safe_defaults = [x for x in st.session_state["p2m_chosen_sectors"] if x in all_64_names]

    chosen_sectors = st.multiselect(
        "🎯 選擇要在混戰星盤中呈現的板塊 (已支援上方一鍵按鈕切換)：",
        all_64_names,
        default=safe_defaults,
        key="multiselect_p2m_sectors"
    )

    if chosen_sectors:
        custom_series = {k: combined_series[k] for k in chosen_sectors if k in combined_series}
        custom_mom_df = calculate_momentum_table(custom_series)
        
        st.markdown(f"<p style='color:#cbd5e1; font-weight:bold;'>⚙️ 調整 [混戰星盤 ({len(chosen_sectors)} 板塊)] 參數：</p>", unsafe_allow_html=True)
        col3_1, col3_2 = st.columns(2)
        with col3_1: tail_3 = st.selectbox("🐍 選擇動態軌跡時間窗", [1, 5, 10, 20, 40], index=2, key="tail_3")
        with col3_2: smooth_3 = st.selectbox("⚙️ RRG 計算靈敏度", [10, 14, 20], index=1, key="smooth_3")
        combined_ratio, combined_mom = calculate_rrg_metrics(price_data, custom_series, window=smooth_3, benchmark='SPY')
        
        render_momentum_section(custom_mom_df, f"混戰星盤 (共 {len(chosen_sectors)} 個板塊)", combined_ratio, combined_mom, custom_series)
        plot_rrg_chart(combined_ratio, combined_mom, tail_3, f"全球 64 大板塊混戰 RRG 星盤 (當前顯示: {len(chosen_sectors)} 個板塊)")
    else:
        st.info("ℹ️ 當前未選擇板塊，請點選上方【🌐 一鍵全覽 (64 大板塊全開)】或自選板塊以繪製混戰星盤。")
        
    st.markdown("<hr style='border:1px dashed #334155; margin: 30px 0;'>", unsafe_allow_html=True)

    # =================================================================
    # 🦅 展區 4：大鱷跨資產預警星盤 (以 TLT 為基準)
    # =================================================================
    st.markdown("<h3 style='color:#ff3344;'>🦅 展區四：大鱷跨資產預警星盤 (2026 年終極生死共振)</h3>", unsafe_allow_html=True)
    st.markdown("<p style='color:#cbd5e1; font-weight:bold;'>⚙️ 調整 [跨資產預警] 參數：</p>", unsafe_allow_html=True)
    col4_1, col4_2 = st.columns(2)
    with col4_1: tail_4 = st.selectbox("🐍 選擇動態軌跡時間窗", [1, 5, 10, 20, 40], index=2, key="tail_4_1")
    with col4_2: smooth_4 = st.selectbox("⚙️ RRG 計算靈敏度", [10, 14, 20], index=1, key="smooth_4_1")
    ulti_ratio, ulti_mom = calculate_rrg_metrics(price_data, ultimate_series, window=smooth_4, benchmark='TLT')
    
    render_momentum_section(ultimate_mom_df, "九大跨資產預警", ulti_ratio, ulti_mom, ultimate_series)
    plot_rrg_chart(ulti_ratio, ulti_mom, tail_4, f"🔥 跨資產宏觀生死共振 (基準: TLT 美債) (尾巴: {tail_4}天)")

    st.markdown("<hr style='border:1px solid #334155; margin: 30px 0;'>", unsafe_allow_html=True)

    # =========================================================================
    # 📚 大指揮官獨家秘技 (純文字 Markdown 格式)
    # =========================================================================
    st.markdown("## 🦅 爺爺壓箱底傳授：2026 九維跨資產共振 (The Macro End-Game)")
    st.markdown("展區四係華爾街頂級大鱷嘅**「抄底與逃頂核按鈕」**。呢個圖**唔係同 SPY 比較，而係同 TLT (20年期國債/終極避險資產) 比較！**\n\n2026 年宏觀已由 **AI 算力 (SMH)、核能/鈾礦 (URA) 與 地緣軍工 (ITA)** 主導，佢哋已經加入生死共振監測網！")
    
    st.markdown("### 🔥 【核按鈕用法】：")
    st.markdown("* **終極逃頂信號 (Crash Warning)**：當你見到 SPY, HYG, COPX, BTC-USD 呢幾條蛇，集體由右邊急轉彎，插水進入「落後區 (紅)」（即係跑輸 TLT），代表全球大資金正在瘋狂拋售高風險資產，湧入美債避險。**大崩盤即將來臨，清倉保命！**")
    st.markdown("* **終極抄底信號 (Generational Buy)**：當大市一片恐慌，但你見到 HYG (垃圾債) 同 BTC 率先由「落後區」抬頭，衝入「改善區 (藍)」甚至「領先區 (綠)」，代表大鱷已經開始暗中吸籌Risk-On。**呢個就係十年一遇嘅重倉抄底時機！**")
    
    st.markdown("### ⚙️ 雙控制鈕「黃金組合」實戰用法：")
    st.markdown("* **1️⃣ 玩法一：極簡速覽今日大局** ➔ 左手選【1】 ＋ 右手選【14】\n👉 畫面無雜亂線條，只睇今日蛇頭落喺邊個象限，3秒掃完所有大板塊形勢。")
    st.markdown("* **2️⃣ 玩法二：短線狙擊剛起爆妖股** ➔ 左手選【5】 ＋ 右手選【10】\n👉 5天軌跡搭配高靈敏度，第一時間捕抓由「落後區 💀」大角度抬頭衝入「改善區 🚀」嘅板塊。")
    st.markdown("* **3️⃣ 玩法三：跟隨大鱷季度大調倉** ➔ 左手選【20】 ＋ 右手選【20】\n👉 拉長 1 個月軌跡並極致平滑，確認主力資金係咪跨板塊長期轉移。")

    st.markdown("<hr style='border:1px dashed #334155; margin: 30px 0;'>", unsafe_allow_html=True)

    # =========================================================================
    # 🗄️ 5. 全球 64 大完整板塊成分股資料庫 (Holdings Database)
    # =========================================================================
    st.markdown("<hr style='border:1px solid #334155; margin: 30px 0;'>", unsafe_allow_html=True)
    
    with st.expander("🗄️ 點擊展開：全球 64 大完整板塊成分股資料庫 (Holdings Database)", expanded=False):
        st.markdown("### 🔍 查詢板塊核心成分股與代表 ETF")
        st.markdown("想知道邊隻 ETF 或者邊個板塊包含咩股票？喺度一撳就知！ *(已全面涵蓋 11 大傳統宏觀 GICS 板塊 ＋ 53 大前沿硬科技與主題霸權，共 64 大板塊)*")
        
        sector_names = list(ALL_64_SECTOR_HOLDINGS.keys())
        selected_sector = st.selectbox("👇 選擇要查詢的板塊 (共 64 個)：", sector_names)
        
        sector_info = ALL_64_SECTOR_HOLDINGS[selected_sector]
        cat_tag = sector_info.get('category', '主題板塊')
        etfs_list = sector_info.get('etfs', [])
        tickers_list = sector_info.get('tickers', [])
        
        st.markdown(f"<span style='background-color:#7c4dff; color:white; padding:4px 12px; border-radius:8px; font-size:12px; font-weight:bold;'>標籤分類：{cat_tag}</span>", unsafe_allow_html=True)
        st.markdown("<br>", unsafe_allow_html=True)
        
        if etfs_list:
            etfs_html = " ".join([f"<span style='background-color:#ffaa00; color:black; padding:4px 10px; border-radius:12px; margin-right:6px; margin-bottom:6px; display:inline-block; font-weight:bold;'>{e}</span>" for e in etfs_list])
            st.markdown(f"**代表 ETF / 籃子基準：**<br><div>{etfs_html}</div>", unsafe_allow_html=True)
        else:
            st.info("**代表 ETF / 基準：** 無專屬純種 ETF (由下方核心個股以 100 點等權重完全合成)")
        
        st.markdown("<br>", unsafe_allow_html=True)
        
        tickers_html = " ".join([f"<span style='background-color:#1e88e5; color:white; padding:5px 12px; border-radius:15px; margin-right:8px; margin-bottom:8px; display:inline-block; font-weight:bold; font-family:Arial Black;'>{t}</span>" for t in tickers_list])
        st.markdown(f"**核心成分股池 (Holdings / Tickers)：**")
        st.markdown(f"<div>{tickers_html}</div>", unsafe_allow_html=True)
        st.markdown("<br>", unsafe_allow_html=True)

if __name__ == "__main__":
    render_page_2m()