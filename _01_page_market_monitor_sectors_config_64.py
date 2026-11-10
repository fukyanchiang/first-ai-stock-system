"""
Filename: _01_page_market_monitor_sectors_config_64.py
Description: 64 大板塊美股風險監測官方基準資料庫 (純配置數據庫 · 零運算依賴)
- 🏛️ 一、11 大傳統宏觀板塊 (GICS 標準)
- ⚡ 二、53 大前沿主題板塊 (6 大前沿產業群)
- 🌟 支援「多 ETF 全取等權合成走勢 (etfs)」與「成份股自建純血合成」
"""

DEFAULT_BACKTEST = {
    'early_drop': {'title_wins': '9 / 9 次', 'prob_5pct': '100%', 'base_5pct': '49%', 'prob_10pct': '56%', 'base_10pct': '27%', 'sub_prob': '45%', 'sub_count': '18 次，跌 ≥5%', 'false_main': '0 / 9 次', 'false_sub': '10 / 18 次'},
    'bottom': {'title_wins': '29 / 29 次', 'ret_60d': '+8.5%', 'base_60d': '+3.2%', 'ret_1y': '+26.8%', 'base_1y': '+12.8%', 'sub_ret': '+6.2%', 'sub_count': '14 次，60 日後', 'false_main': '0 / 29 次', 'false_sub': '2 / 14 次'},
    'rally': {'title_wins': '26 / 27 次', 'ret_120d': '+13.8%', 'base_120d': '+6.5%', 'ret_1y': '+29.4%', 'base_1y': '+12.8%', 'sub_ret': '+8.4%', 'sub_count': '10 次，120 日後', 'false_main': '1 / 27 次', 'false_sub': '1 / 10 次'}
}

# 🌟 第一梯隊激活：11 大宏觀 GICS 頂層底盤 + 2 大先鋒板塊 (共 13 個)
PILOT_ACTIVE_KEYS = [
    # 🏛️ 11 大傳統宏觀 GICS
    'XLK', 'XLF', 'XLV', 'XLE', 'XLY', 'XLP', 'XLI', 'XLU', 'XLB', 'XLRE', 'XLC',
    # ⚡ 核心算力與硬體先鋒
    'SMH', 'VRT'
]

SECTORS_64_CONFIG = {
    # =========================================================================
    # 🏛️ 一、11 大傳統宏觀板塊 (GICS 標準 · SPDR 行業龍頭)
    # =========================================================================
    'XLK': {
        'id': 1, 'name': '🏛️ 科技 (XLK)', 'etf': 'XLK', 'etfs': ['XLK'],
        'group': '宏觀 GICS',
        'tickers': ['AAPL', 'MSFT', 'NVDA', 'AVGO', 'ORCL', 'CRM', 'ADBE', 'CSCO', 'AMD', 'QCOM']
    },
    'XLF': {
        'id': 2, 'name': '🏛️ 金融 (XLF)', 'etf': 'XLF', 'etfs': ['XLF'],
        'group': '宏觀 GICS',
        'tickers': ['JPM', 'BAC', 'WFC', 'GS', 'MS', 'BLK', 'C', 'AXP', 'V', 'MA']
    },
    'XLV': {
        'id': 3, 'name': '🏛️ 醫療保健 (XLV)', 'etf': 'XLV', 'etfs': ['XLV'],
        'group': '宏觀 GICS',
        'tickers': ['LLY', 'UNH', 'JNJ', 'ABBV', 'MRK', 'TMO', 'ABT', 'PFE', 'AMGN', 'ISRG']
    },
    'XLE': {
        'id': 4, 'name': '🏛️ 能源 (XLE)', 'etf': 'XLE', 'etfs': ['XLE'],
        'group': '宏觀 GICS',
        'tickers': ['XOM', 'CVX', 'COP', 'EOG', 'SLB', 'MPC', 'PSX', 'VLO', 'OXY', 'HAL']
    },
    'XLY': {
        'id': 5, 'name': '🏛️ 非必需消費 (XLY)', 'etf': 'XLY', 'etfs': ['XLY'],
        'group': '宏觀 GICS',
        'tickers': ['AMZN', 'TSLA', 'HD', 'MCD', 'NKE', 'LOW', 'BKNG', 'SBUX', 'TJX', 'TGT']
    },
    'XLP': {
        'id': 6, 'name': '🏛️ 必需消費 (XLP)', 'etf': 'XLP', 'etfs': ['XLP'],
        'group': '宏觀 GICS',
        'tickers': ['PG', 'COST', 'WMT', 'KO', 'PEP', 'PM', 'MDLZ', 'CL', 'MO', 'KMB']
    },
    'XLI': {
        'id': 7, 'name': '🏛️ 工業 (XLI)', 'etf': 'XLI', 'etfs': ['XLI'],
        'group': '宏觀 GICS',
        'tickers': ['GE', 'CAT', 'UNP', 'HON', 'RTX', 'BA', 'LMT', 'DE', 'UPS', 'FDX']
    },
    'XLU': {
        'id': 8, 'name': '🏛️ 公用事業 (XLU)', 'etf': 'XLU', 'etfs': ['XLU'],
        'group': '宏觀 GICS',
        'tickers': ['NEE', 'SO', 'DUK', 'CEG', 'VST', 'SRE', 'AEP', 'PEG', 'EXC', 'ED']
    },
    'XLB': {
        'id': 9, 'name': '🏛️ 原材料 (XLB)', 'etf': 'XLB', 'etfs': ['XLB'],
        'group': '宏觀 GICS',
        'tickers': ['LIN', 'SHW', 'FCX', 'APD', 'ECL', 'NEM', 'CTVA', 'DOW', 'DD', 'ALB']
    },
    'XLRE': {
        'id': 10, 'name': '🏛️ 房地產 (XLRE)', 'etf': 'XLRE', 'etfs': ['XLRE'],
        'group': '宏觀 GICS',
        'tickers': ['PLD', 'AMT', 'EQIX', 'WELL', 'SPG', 'PSA', 'O', 'DLR', 'CCI', 'VICI']
    },
    'XLC': {
        'id': 11, 'name': '🏛️ 通訊服務 (XLC)', 'etf': 'XLC', 'etfs': ['XLC'],
        'group': '宏觀 GICS',
        'tickers': ['META', 'GOOGL', 'GOOG', 'NFLX', 'DIS', 'CMCSA', 'TMUS', 'VZ', 'T', 'EA']
    },

    # =========================================================================
    # ⚡ 二、53 大前沿細分領域主題霸權 (6 大前沿產業群)
    # =========================================================================
    # 1. AI 算力、硬體與半導體鏈 (10 個)
    'SMH': {
        'id': 12, 'name': '🧠 GPU / AI 核心算力 (SMH)', 'etf': 'SMH', 'etfs': ['SMH'],
        'group': 'AI算力與半導體',
        'tickers': ['NVDA', 'TSM', 'AVGO', 'AMD', 'ARM', 'QCOM', 'MRVL', 'INTC']
    },
    'SOXX': {
        'id': 13, 'name': '💻 CPU / 通用晶片處理器 (SOXX)', 'etf': 'SOXX', 'etfs': ['SOXX'],
        'group': 'AI算力與半導體',
        'tickers': ['AMD', 'INTC', 'ARM', 'QCOM', 'AAPL', 'TXN', 'ADI', 'MCHP']
    },
    'CHPX': {
        'id': 14, 'name': '💾 DRAM / 記憶體與存儲 (CHPX)', 'etf': 'CHPX', 'etfs': ['CHPX'],
        'group': 'AI算力與半導體',
        'tickers': ['MU', 'WDC', 'STX', 'PSTG', 'NTAP']
    },
    'AMAT': {
        'id': 15, 'name': '🔬 先進封裝與晶片製造設備 (AMAT)', 'etf': 'SMH', 'etfs': ['SMH', 'SOXX'],
        'group': 'AI算力與半導體',
        'tickers': ['ASML', 'AMAT', 'LRCX', 'KLAC', 'ONTO', 'CAMT', 'ICHR', 'UCTT', 'ACLS', 'FORM']
    },
    'FOTO': {
        'id': 16, 'name': '⚡ 光模組、CPO 與光通信 (FOTO)', 'etf': 'FOTO', 'etfs': ['FOTO'],
        'group': 'AI算力與半導體',
        'tickers': ['COHR', 'AAOI', 'FN', 'LITE', 'CIEN', 'CRDO', 'ALAB', 'MTSI', 'POET', 'GLW']
    },
    'SMCI': {
        'id': 17, 'name': '🖥️ AI 伺服器與硬體系統 (SMCI)', 'etf': None, 'etfs': [],
        'group': 'AI算力與半導體',
        'tickers': ['SMCI', 'DELL', 'HPE', 'ANET', 'PSTG', 'VRT', 'CDNS', 'SNPS']
    },
    'VRT': {
        'id': 18, 'name': '❄️ AI 液冷散熱與電源管理 (VRT)', 'etf': None, 'etfs': ['XLU', 'GRID'],
        'group': 'AI算力與半導體',
        'tickers': ['VRT', 'MOD', 'GEV', 'CAT', 'CMI', 'CEG', 'VST', 'NVT']
    },
    'GRID': {
        'id': 19, 'name': '⚡ 變壓器與電網升級基建 (GRID)', 'etf': 'GRID', 'etfs': ['GRID', 'PAVE'],
        'group': 'AI算力與半導體',
        'tickers': ['PWR', 'ETN', 'HUBB', 'ABB', 'EME', 'MYRG', 'GEV']
    },
    'QCOM': {
        'id': 20, 'name': '📱 Edge AI / 端側晶片終端 (QCOM)', 'etf': None, 'etfs': [],
        'group': 'AI算力與半導體',
        'tickers': ['QCOM', 'AAPL', 'AVGO', 'SWKS', 'QRVO', 'LOGI', 'NXPI']
    },
    'SRVR': {
        'id': 21, 'name': '🏢 數據中心與雲基建 (SRVR)', 'etf': 'SRVR', 'etfs': ['SRVR', 'DTCR'],
        'group': 'AI算力與半導體',
        'tickers': ['EQIX', 'DLR', 'AMT', 'CCI', 'GDS', 'COR', 'VRT']
    },

    # 2. 軟體、SaaS 與網絡安全 (5 個)
    'AIQ': {
        'id': 22, 'name': '🧠 LLM 大模型與 AI 科技巨頭 (AIQ)', 'etf': 'AIQ', 'etfs': ['AIQ', 'BOTZ', 'THNQ'],
        'group': '軟體、SaaS 與網安',
        'tickers': ['MSFT', 'GOOGL', 'AMZN', 'META', 'ORCL', 'AAPL', 'PLTR']
    },
    'CIBR': {
        'id': 23, 'name': '🛡️ 網絡安全與零信任 (CIBR)', 'etf': 'CIBR', 'etfs': ['CIBR', 'HACK', 'BUG'],
        'group': '軟體、SaaS 與網安',
        'tickers': ['CRWD', 'PANW', 'ZS', 'FTNT', 'NET', 'CYBR', 'OKTA', 'CHKP', 'S']
    },
    'IGV': {
        'id': 24, 'name': '☁️ 雲計算與企業級 SaaS (IGV)', 'etf': 'IGV', 'etfs': ['IGV', 'WCLD', 'CLOU'],
        'group': '軟體、SaaS 與網安',
        'tickers': ['CRM', 'ADBE', 'NOW', 'WDAY', 'SNOW', 'DDOG', 'MDB', 'TEAM', 'PLTR', 'HUBS']
    },
    'FINX': {
        'id': 25, 'name': '💳 金融科技與數字支付 (FINX)', 'etf': 'FINX', 'etfs': ['FINX', 'IPAY'],
        'group': '軟體、SaaS 與網安',
        'tickers': ['V', 'MA', 'PYPL', 'SQ', 'HOOD', 'AFRM', 'SOFI', 'TOST', 'FIS', 'GPN']
    },
    'HCP': {
        'id': 26, 'name': '🛠️ 基礎設施軟體與 DevOps (HCP)', 'etf': 'IGV', 'etfs': ['IGV'],
        'group': '軟體、SaaS 與網安',
        'tickers': ['GTLB', 'HCP', 'ESTC', 'CFLT', 'MDB', 'DT', 'FSLY']
    },

    # 3. 前沿科技、機器人與空天出行 (6 個)
    'BOTZ': {
        'id': 27, 'name': '🦾 機械人與智慧自動化 (BOTZ)', 'etf': 'BOTZ', 'etfs': ['BOTZ', 'ROBO', 'IRBO'],
        'group': '前沿科技與空天',
        'tickers': ['TSLA', 'ISRG', 'PATH', 'SYM', 'TER', 'ROK', 'NVDA']
    },
    'IDRV': {
        'id': 28, 'name': '🚘 自動駕駛與 Robotaxi (IDRV)', 'etf': 'IDRV', 'etfs': ['IDRV', 'DRIV', 'HAIL'],
        'group': '前沿科技與空天',
        'tickers': ['TSLA', 'GOOGL', 'MBLY', 'UBER', 'HSAI', 'AUR', 'LAZR', 'INVZ']
    },
    'JOBY': {
        'id': 29, 'name': '🚁 低空飛行與 eVTOL 空運 (JOBY)', 'etf': None, 'etfs': [],
        'group': '前沿科技與空天',
        'tickers': ['JOBY', 'ACHR', 'EH', 'AUR', 'BLDE', 'EVTL']
    },
    'QTUM': {
        'id': 30, 'name': '💻 量子計算 (QTUM)', 'etf': 'QTUM', 'etfs': ['QTUM'],
        'group': '前沿科技與空天',
        'tickers': ['IONQ', 'RGTI', 'QBTS', 'QUBT', 'ARQQ', 'HON', 'IBM', 'GOOGL', 'MSFT']
    },
    'UFO': {
        'id': 31, 'name': '🚀 商業太空與低軌通訊 (UFO)', 'etf': 'UFO', 'etfs': ['UFO', 'ROKT', 'ARKX'],
        'group': '前沿科技與空天',
        'tickers': ['RKLB', 'ASTS', 'LUNR', 'BKSY', 'PL', 'RDWR', 'SPCE', 'MNTS', 'VSAT', 'IRDM']
    },
    'ARKK': {
        'id': 32, 'name': '🦅 顛覆性創新霸權 (ARKK)', 'etf': 'ARKK', 'etfs': ['ARKK', 'ARKW', 'ARKG'],
        'group': '前沿科技與空天',
        'tickers': ['TSLA', 'ROKU', 'COIN', 'PLTR', 'U', 'PATH', 'CRSP']
    },

    # 4. 生技醫藥與前沿生命健康 (5 個)
    'XBI': {
        'id': 33, 'name': '🧬 高彈性創新型生技 (XBI)', 'etf': 'XBI', 'etfs': ['XBI', 'IBB', 'ARKG'],
        'group': '生技醫藥與生命健康',
        'tickers': ['MRNA', 'BNTX', 'CRSP', 'VRTX', 'REGN', 'ILMN', 'BIIB', 'ALNY']
    },
    'LLY': {
        'id': 34, 'name': '💉 減肥藥與 GLP-1 產業鏈 (LLY)', 'etf': 'XLV', 'etfs': ['XLV'],
        'group': '生技醫藥與生命健康',
        'tickers': ['LLY', 'NVO', 'VKTX', 'ALT', 'GPCR', 'RVNC', 'TERN', 'AMGN', 'PFE']
    },
    'IHI': {
        'id': 35, 'name': '🩺 醫療器械與精準外科 (IHI)', 'etf': 'IHI', 'etfs': ['IHI', 'ARKG'],
        'group': '生技醫藥與生命健康',
        'tickers': ['ISRG', 'SYK', 'BSX', 'MDT', 'EW', 'ABT', 'DXCM', 'TMO']
    },
    'BSX': {
        'id': 36, 'name': '🧠 腦機介面與仿生神經 (BSX)', 'etf': None, 'etfs': [],
        'group': '生技醫藥與生命健康',
        'tickers': ['SYNA', 'TNDM', 'DXCM', 'INMD', 'NVRO', 'PRVA', 'BSX', 'MDT']
    },
    'IHF': {
        'id': 37, 'name': '🏥 醫療健康保險與服務 (IHF)', 'etf': 'IHF', 'etfs': ['IHF'],
        'group': '生技醫藥與生命健康',
        'tickers': ['UNH', 'ELV', 'CI', 'CVS', 'HUM', 'CNC']
    },

    # 5. 能源變革、核能與關鍵金屬資源 (8 個)
    'URA': {
        'id': 38, 'name': '⚛️ 核能、SMR 與鈾礦 (URA)', 'etf': 'URA', 'etfs': ['URA', 'URNM', 'NLR'],
        'group': '能源核能與金屬資源',
        'tickers': ['CCJ', 'OKLO', 'SMR', 'LEU', 'UUUU', 'CEG', 'VST', 'BWXT']
    },
    'ICLN': {
        'id': 39, 'name': '☀️ 清潔能源與太陽能 (ICLN)', 'etf': 'ICLN', 'etfs': ['ICLN', 'TAN', 'QCLN'],
        'group': '能源核能與金屬資源',
        'tickers': ['FSLR', 'ENPH', 'SEDG', 'RUN', 'PLUG', 'NEE', 'CSIQ', 'BE']
    },
    'LIT': {
        'id': 40, 'name': '🔋 電動車與鋰電池鏈 (LIT)', 'etf': 'LIT', 'etfs': ['LIT', 'DRIV', 'IDRV'],
        'group': '能源核能與金屬資源',
        'tickers': ['TSLA', 'ALB', 'SQM', 'QS', 'FREY', 'ON', 'RIVN', 'LCID']
    },
    'GDX': {
        'id': 41, 'name': '🥇 金礦開採與貴金屬 (GDX)', 'etf': 'GDX', 'etfs': ['GDX', 'GDXJ', 'RING'],
        'group': '能源核能與金屬資源',
        'tickers': ['NEM', 'GOLD', 'AEM', 'KGC', 'AUY', 'AU', 'HMY']
    },
    'SIL': {
        'id': 42, 'name': '🥈 銀礦開採 (SIL)', 'etf': 'SIL', 'etfs': ['SIL', 'SILJ'],
        'group': '能源核能與金屬資源',
        'tickers': ['AG', 'PAAS', 'HL', 'CDE', 'FSM', 'MAG']
    },
    'COPX': {
        'id': 43, 'name': '🥉 銅礦與關鍵工業金屬 (COPX)', 'etf': 'COPX', 'etfs': ['COPX', 'CPER', 'PICK'],
        'group': '能源核能與金屬資源',
        'tickers': ['FCX', 'SCCO', 'ERO', 'TECK', 'HBM', 'BHP', 'RIO']
    },
    'OIH': {
        'id': 44, 'name': '🛢️ 石油開採與油服設備 (OIH)', 'etf': 'OIH', 'etfs': ['OIH', 'XOP'],
        'group': '能源核能與金屬資源',
        'tickers': ['SLB', 'HAL', 'BKR', 'EOG', 'OXY', 'FANG', 'DVN', 'COP']
    },
    'REMX': {
        'id': 45, 'name': '🧪 特種材料與稀土資源 (REMX)', 'etf': 'REMX', 'etfs': ['REMX', 'LIT'],
        'group': '能源核能與金屬資源',
        'tickers': ['MP', 'ALB', 'LIN', 'APD', 'SHW', 'ECL']
    },

    # 6. 地緣防務、特種產業與經濟民生 (19 個)
    'ITA': {
        'id': 46, 'name': '⚔️ 國防軍工與尖端航太 (ITA)', 'etf': 'ITA', 'etfs': ['ITA', 'PPA', 'XAR'],
        'group': '地緣特種與民生',
        'tickers': ['LMT', 'RTX', 'NOC', 'GD', 'BA', 'LHX', 'HII', 'TDG', 'AXON']
    },
    'WGMI': {
        'id': 47, 'name': '🪙 區塊鏈與比特幣生態 (WGMI)', 'etf': 'WGMI', 'etfs': ['WGMI', 'BLOK', 'IBIT'],
        'group': '地緣特種與民生',
        'tickers': ['COIN', 'MSTR', 'MARA', 'RIOT', 'CLSK', 'HOOD', 'HUT', 'CIFR']
    },
    'FDN': {
        'id': 48, 'name': '🛍️ 電商平台與數位消費 (FDN)', 'etf': 'FDN', 'etfs': ['FDN', 'IBUY'],
        'group': '地緣特種與民生',
        'tickers': ['AMZN', 'MELI', 'BABA', 'PDD', 'SE', 'CHWY', 'DASH', 'SHOP', 'EBAY']
    },
    'IYT': {
        'id': 49, 'name': '🚚 現代交通物流與鐵路 (IYT)', 'etf': 'IYT', 'etfs': ['IYT'],
        'group': '地緣特種與民生',
        'tickers': ['UNP', 'CSX', 'NSC', 'UPS', 'FDX', 'ODFL', 'JBHT']
    },
    'MOO': {
        'id': 50, 'name': '🌾 農業科技與糧食化肥 (MOO)', 'etf': 'MOO', 'etfs': ['MOO'],
        'group': '地緣特種與民生',
        'tickers': ['DE', 'ADM', 'CTVA', 'MOS', 'CF', 'NTR', 'BG']
    },
    'PHO': {
        'id': 51, 'name': '💧 水資源與環境基建 (PHO)', 'etf': 'PHO', 'etfs': ['PHO', 'FIW'],
        'group': '地緣特種與民生',
        'tickers': ['XYL', 'AWK', 'WMS', 'ECL', 'ROP', 'PNR']
    },
    'HERO': {
        'id': 52, 'name': '🎮 數位娛樂與在線遊戲 (HERO)', 'etf': 'HERO', 'etfs': ['HERO', 'BETZ'],
        'group': '地緣特種與民生',
        'tickers': ['RBLX', 'EA', 'TTWO', 'DKNG', 'FLUT', 'NTES']
    },
    'TEL': {
        'id': 53, 'name': '🧲 被動元件與電子連接器 (TEL)', 'etf': None, 'etfs': [],
        'group': '地緣特種與民生',
        'tickers': ['TEL', 'APH', 'VSH', 'LFUS', 'GLW']
    },
    'ITB': {
        'id': 54, 'name': '🏠 住宅建築與地產營造 (ITB)', 'etf': 'ITB', 'etfs': ['ITB', 'XHB'],
        'group': '地緣特種與民生',
        'tickers': ['DHI', 'LEN', 'NVR', 'PHM', 'TOL', 'HD', 'LOW']
    },
    'JETS': {
        'id': 55, 'name': '✈️ 航空交通與休閒旅遊 (JETS)', 'etf': 'JETS', 'etfs': ['JETS'],
        'group': '地緣特種與民生',
        'tickers': ['DAL', 'UAL', 'AAL', 'LUV', 'CCL', 'RCL', 'NCLH']
    },
    'KIE': {
        'id': 56, 'name': '🛡️ 保險經紀與風險管理 (KIE)', 'etf': 'KIE', 'etfs': ['KIE', 'IAK'],
        'group': '地緣特種與民生',
        'tickers': ['PGR', 'CB', 'TRV', 'ALL', 'AIG', 'AON', 'MMC']
    },
    'KRE': {
        'id': 57, 'name': '🏛️ 美國區域性商業銀行 (KRE)', 'etf': 'KRE', 'etfs': ['KRE', 'KBE'],
        'group': '地緣特種與民生',
        'tickers': ['TFC', 'PNC', 'USB', 'FITB', 'MTB', 'KEY', 'CFG']
    },
    'PBJ': {
        'id': 58, 'name': '🍔 連鎖餐飲與生活消費 (PBJ)', 'etf': 'PBJ', 'etfs': ['PBJ'],
        'group': '地緣特種與民生',
        'tickers': ['MCD', 'SBUX', 'CMG', 'YUM', 'DRI', 'QSR', 'WING']
    },
    'SUBZ': {
        'id': 59, 'name': '🎬 串流媒體與影視娛樂 (SUBZ)', 'etf': 'SUBZ', 'etfs': ['SUBZ'],
        'group': '地緣特種與民生',
        'tickers': ['NFLX', 'SPOT', 'DIS', 'ROKU', 'WBD']
    },
    'WOOD': {
        'id': 60, 'name': '📦 包裝材料與林業資源 (WOOD)', 'etf': 'WOOD', 'etfs': ['WOOD'],
        'group': '地緣特種與民生',
        'tickers': ['IP', 'PKG', 'BALL', 'CCK', 'AVY']
    },
    'CARZ': {
        'id': 61, 'name': '🚗 傳統汽車製造與配件 (CARZ)', 'etf': 'CARZ', 'etfs': ['CARZ'],
        'group': '地緣特種與民生',
        'tickers': ['GM', 'F', 'STLA', 'APTV', 'BWA', 'LEA', 'MGA']
    },
    'PAVE': {
        'id': 62, 'name': '🧱 重型基建材料與水泥 (PAVE)', 'etf': 'PAVE', 'etfs': ['PAVE'],
        'group': '地緣特種與民生',
        'tickers': ['VMC', 'MLM', 'CRH', 'SUM', 'EXP']
    },
    'ADP': {
        'id': 63, 'name': '💼 企業人力與外包服務 (ADP)', 'etf': None, 'etfs': [],
        'group': '地緣特種與民生',
        'tickers': ['ADP', 'PAYX', 'ACN', 'IT', 'CTSH', 'EPAM']
    },
    'XSD': {
        'id': 64, 'name': '🔌 類比與電源半導體 (XSD)', 'etf': 'XSD', 'etfs': ['XSD', 'SOXX'],
        'group': '地緣特種與民生',
        'tickers': ['TXN', 'ADI', 'NXPI', 'MCHP', 'ON', 'MPWR']
    }
}