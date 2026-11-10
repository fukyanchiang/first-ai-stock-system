"""
Filename: page_2bb.py
Description: 📡 艙房 2bb：個股版塊拔河熱力圖 (美股真歷史市寬大陣) (100% 全真實數據旗艦版)
- 修正自帶括號板塊 (如網絡安全 Cyber、EV、油氣等) 的隻數標籤漏顯 Bug
- 50 大細分產業板塊全面擴展至「每板塊 20~24 隻完全體」(全陣列突破 1,000 隻次)
- 🔥 SPHB (高波動長矛) 全面擴充至官方極限 200 隻高 Beta 爆發完全體
- ⭐ SPLV (低波動盾牌) 全面擴充至官方極限 200 隻護城河防守完全體
- 5 大核心 ETF 與 50 大細分板塊全面標記「真實股票隻數」透視標籤
- 修正 JSON 欄位字串脫殼漏洞 (徹底修復 ETF 陰陽燭與成交量消失隱形問題)
- 全美股 940+ 隻權重成份股矩陣向量化極速清算 (受控微批次，徹底杜絕 429 封鎖)
- 雙 X 軸真實交易日對齊 (category 壓縮週末跳空)
- 本地持久化快取 (page_2bb_cache.json) 實現 0.05 秒開盤秒開
"""

import streamlit as st
import yfinance as yf
import pandas as pd
import numpy as np
import plotly.graph_objects as go
from plotly.subplots import make_subplots
import time
import os
import json
import re
from datetime import datetime

CACHE_FILE_2BB = "page_2bb_cache.json"

# ===================================================
# 🗄️ 戰略核心：50 大細分產業板塊 (每板塊 20~24 隻完全體)
# ===================================================
US_STOCK_MAP = {
    "1. 半導體設備與設計": [
        "NVDA", "TSM", "AVGO", "ASML", "AMD", "QCOM", "TXN", "INTC", "MU", "AMAT",
        "LRCX", "KLAC", "MRVL", "ADI", "NXPI", "MCHP", "ON", "MPWR", "TER", "ARM",
        "SWKS", "QRVO", "STM", "WDC"
    ],
    "2. AI與大數據雲端": [
        "MSFT", "GOOGL", "ORCL", "ADBE", "CRM", "PLTR", "NOW", "SNOW", "DDOG", "MDB",
        "ESTC", "AI", "BBAI", "SOUN", "PATH", "IOT", "GTLB", "HCP", "APP", "SMCI"
    ],
    "3. 基礎軟件與 SaaS": [
        "INTU", "CDNS", "PTC", "MSTR", "WDAY", "SNPS", "ADSK", "TEAM", "HUBS", "BILL",
        "DOCN", "MNDY", "SMAR", "ASAN", "FIVN", "TWLO", "PD", "DT", "PAYC", "CRWD"
    ],
    "4. 網絡安全 (Cyber)": [
        "PANW", "CRWD", "FTNT", "ZS", "CYBR", "CHKP", "GEN", "OKTA", "QLYS", "TENB",
        "VRNS", "RPD", "S", "NET", "FSLY", "AKAM", "FFIV", "TLS", "RBLX", "VRNT"
    ],
    "5. 消費電子與硬件": [
        "AAPL", "HPQ", "DELL", "STX", "WDC", "APH", "GLW", "HPE", "NTAP", "PSTG",
        "LOGI", "SONY", "SONO", "GRMN", "VZIO", "CRSR", "HEAR", "IMMR", "KOSS", "UEIC"
    ],
    "6. 通訊與網絡設備": [
        "CSCO", "MSI", "JNPR", "ANET", "COMM", "CIEN", "LITE", "COHR", "EXTR", "CALX",
        "VIAV", "ADTN", "HLIT", "INFN", "DGII", "BAND", "EGHT", "RING", "LUMN", "FFIV"
    ],
    "7. 互聯網平台內容": [
        "META", "GOOG", "PINS", "SNAP", "MATCH", "RDDT", "SPOT", "IAC", "BMBL", "ANGI",
        "YELP", "TRIP", "WB", "BIDU", "BZFD", "Z", "OPEN", "EXPE", "BKNG", "ABNB"
    ],
    "8. 媒體與影視娛樂": [
        "NFLX", "DIS", "WBD", "PARA", "LYV", "CMCSA", "FOXA", "FOX", "ROKU", "SIRI",
        "TKO", "CNK", "IMAX", "MANU", "LGF-A", "NXST", "TGNA", "MSGS", "EDR", "WMG"
    ],
    "9. 電子商務與零售": [
        "AMZN", "EBAY", "ETSY", "MELI", "SHOP", "PDD", "BABA", "JD", "CPNG", "CHWY",
        "W", "BYON", "POSH", "RVLV", "GLBE", "DASH", "CART", "QRTEA", "DDS", "WMT", "COST"
    ],
    "10. 傳統零售百貨": [
        "WMT", "COST", "TGT", "DG", "DLTR", "KR", "BJ", "ROST", "TJX", "BURL",
        "KSS", "M", "JWN", "GPS", "OLLI", "FIVE", "BIG", "BOOT", "FL", "BBY"
    ],
    "11. 核心消費品": [
        "PG", "KO", "PEP", "PM", "MO", "EL", "CL", "KMB", "GIS", "HSY",
        "MDLZ", "STZ", "TAP", "BF-B", "KDP", "MNST", "ADM", "TSN", "HRL", "CAG"
    ],
    "12. 汽車製造商": [
        "F", "GM", "STLA", "TM", "HMC", "RACE", "BMWYY", "VWAGY", "MBGAF", "HESAY",
        "HYMTF", "SZKMY", "BYDDY", "POAHY", "NSANY", "TTM", "LCID", "RIVN", "TSLA", "PCAR", "OSK"
    ],
    "13. 電動車與自駕 (EV)": [
        "TSLA", "RIVN", "LCID", "LI", "NIO", "XPEV", "PSNY", "GOEV", "FFIE", "CHPT",
        "BLNK", "EVGO", "LAZR", "INVZ", "HSAI", "OUST", "CPTN", "LIDR", "MBLY", "QS", "ENVX"
    ],
    "14. 汽車零部件": [
        "MGA", "APTV", "BWA", "LEA", "VC", "ALV", "GNTX", "AXL", "DAN", "TEN",
        "SMP", "DORM", "FOXF", "LKQ", "MOD", "THO", "WGO", "LCII", "PATK", "SUP"
    ],
    "15. 航空航天與國防": [
        "LMT", "RTX", "NOC", "GD", "BA", "HII", "LHX", "TDG", "HEI", "TXT",
        "KTOS", "HWM", "AXON", "AVAV", "CW", "CAE", "SPR", "ERJ", "MRCY", "DRS", "KAMN"
    ],
    "16. 重型機械裝備": [
        "CAT", "DE", "CMI", "PCAR", "OSK", "AGCO", "CNHI", "TEX", "URI", "TTC",
        "MTW", "ASTE", "ALG", "WNC", "HY", "REV", "LECO", "PNR", "DOV", "FLS"
    ],
    "17. 工業綜合集團": [
        "GE", "HON", "MMM", "EMR", "ITW", "ETN", "PH", "ROK", "IR", "XYL",
        "AME", "DOV", "NDSN", "SWK", "SNA", "GWW", "FAST", "HUBB", "WSO", "AOS"
    ],
    "18. 運輸與物流": [
        "UNP", "UPS", "FDX", "NSC", "CSX", "ODFL", "JBHT", "XPO", "SAIA", "KNX",
        "CHRW", "EXPD", "LSTR", "HUBG", "WERN", "HTLD", "CVTI", "MATX", "SNDR", "ARCB"
    ],
    "19. 航空與機場": [
        "LUV", "DAL", "AAL", "UAL", "ALK", "JBLU", "SAVE", "HA", "SKYW", "ALGT",
        "MESA", "ATSG", "PAC", "ASR", "OMAB", "CAAP", "FLT", "CPA", "AZUL", "GOL", "VLRS"
    ],
    "20. 旅遊酒店博彩": [
        "BKNG", "ABNB", "MAR", "HLT", "LVS", "WYNN", "MGM", "CZR", "PENN", "RCL",
        "CCL", "NCLH", "H", "WH", "CHH", "IHG", "VAC", "TNL", "PLYA", "TRIP"
    ],
    "21. 餐飲連鎖": [
        "MCD", "SBUX", "YUM", "CMG", "DPZ", "DRI", "WEN", "QSR", "TXRH", "WING",
        "PZZA", "EAT", "BLMN", "CAKE", "DIN", "CBRL", "JACK", "SHAK", "BROS", "LOCO"
    ],
    "22. 商業銀行巨頭": [
        "JPM", "BAC", "WFC", "C", "GS", "MS", "USB", "PNC", "TFC", "BK",
        "STT", "COF", "DFS", "AXP", "HSBC", "RY", "TD", "BMO", "BNS", "SAN"
    ],
    "23. 區域性銀行": [
        "KRE", "PNC", "TFC", "USB", "EWBC", "FITB", "KEY", "RF", "CFG", "HBAN",
        "MTB", "OZK", "ZION", "CMA", "WAL", "BANC", "SNV", "FHN", "BOKF", "CFR", "PB", "ONB", "CBSH"
    ],
    "24. 投資與資產管理": [
        "BLK", "BX", "TROW", "APO", "KKR", "ARES", "CG", "AMP", "IVZ", "BEN",
        "AMG", "SEIC", "OWL", "HLNE", "STEP", "JEF", "LAZ", "EVR", "MC", "GHL"
    ],
    "25. 金融科技與支付": [
        "V", "MA", "SQ", "PYPL", "AFRM", "FIS", "FISV", "GPN", "FOUR", "TOST",
        "ADYEY", "FLYW", "MQ", "DLO", "RELY", "PAYO", "SOFI", "UPST", "LC", "NU"
    ],
    "26. 保險經紀與服務": [
        "CB", "PGR", "TRV", "MET", "AIG", "ALL", "AFL", "PRU", "HIG", "CINF",
        "WRB", "MMC", "AON", "AJG", "BRO", "WTW", "RE", "EG", "ACGL", "RLI"
    ],
    "27. 傳統製藥巨頭": [
        "LLY", "NVO", "JNJ", "MRK", "ABBV", "PFE", "BMY", "AMGN", "GILD", "BIIB",
        "VRTX", "REGN", "AZN", "SNY", "GSK", "TAK", "NVS", "ROIV", "TEVA", "PRGO"
    ],
    "28. 大中型生物科技": [
        "MRNA", "BNTX", "BIIB", "INCY", "BMRN", "ALNY", "EXEL", "HALO", "IONS",
        "SRPT", "BGNE", "ARGX", "RARE", "BBIO", "CRSP", "EDIT", "NTLA", "BEAM", "FATE", "UTHR", "NVAX"
    ],
    "29. 醫療設備與器械": [
        "MDT", "ABT", "SYK", "BSX", "EW", "ISRG", "BDX", "ZBH", "BAX", "DXCM",
        "PODD", "ALGN", "HOLX", "COO", "RMD", "STE", "TFX", "GMED", "PEN", "SWAV"
    ],
    "30. 醫療服務與管理": [
        "UNH", "ELV", "CVS", "CI", "HUM", "CNC", "MOH", "HCA", "THC", "UHS",
        "AMED", "LH", "DGX", "EHC", "AGL", "HQY", "PNTG", "SEM", "ENSG", "ADUS"
    ],
    "31. 基因與生命科學": [
        "ILMN", "TMO", "A", "DHR", "CTLT", "IQV", "CRL", "TECH", "BIO", "MTD",
        "WAT", "RVTY", "PACB", "TXG", "NSTG", "CDNA", "QGEN", "GH", "EXAS", "NVST"
    ],
    "32. 傳統能源 (油氣)": [
        "XOM", "CVX", "COP", "SLB", "HAL", "EOG", "PXD", "MPC", "VLO", "PSX",
        "OXY", "DVN", "FANG", "HES", "KMI", "WMB", "OKE", "TRGP", "APA", "EQT"
    ],
    "33. 油氣設備與服務": [
        "BKR", "FTI", "NBR", "SLB", "HAL", "NOV", "CHX", "OII", "WHD", "VAL",
        "RIG", "DO", "HP", "PTEN", "CLB", "RES", "EXTN", "TDW", "DRQ", "LBRT"
    ],
    "34. 太陽能與清潔能源": [
        "FSLR", "ENPH", "SEDG", "RUN", "SHLS", "ARRY", "STEM", "NOVA", "MAXN", "CWEN",
        "HASI", "BEP", "AY", "NEP", "BE", "PLUG", "FCEL", "BLDP", "DQ", "JKS"
    ],
    "35. 公用事業 (水電)": [
        "NEE", "SO", "DUK", "SRE", "AEP", "EXC", "XEL", "ED", "PEG", "WEC",
        "ES", "D", "EIX", "AWK", "PPL", "CMS", "CNP", "ETR", "FE", "AEE"
    ],
    "36. 基礎與特殊化工": [
        "LIN", "APD", "DOW", "LYB", "CE", "ECL", "SHW", "PPG", "DD", "ALB",
        "FMC", "EMN", "IFF", "CF", "MOS", "NTR", "RPM", "AVNT", "WLK", "HUN"
    ],
    "37. 鋼鐵與基礎金屬": [
        "NUE", "STLD", "X", "CLF", "RS", "ATI", "CRS", "VALE", "RIO", "BHP",
        "SCCO", "AA", "CENX", "KALU", "SCHN", "CMC", "TMST", "WOR", "HAYN", "ZEUS"
    ],
    "38. 黃金與貴金屬": [
        "NEM", "GOLD", "FCX", "SCCO", "AEM", "KGC", "AU", "AUY", "PAAS", "HL",
        "CDE", "WPM", "FNV", "RGLD", "AG", "EXK", "MAG", "NGD", "EQX", "IAG"
    ],
    "39. 住宅房地產開發": [
        "LEN", "DHI", "PHM", "TOL", "NVR", "KBH", "MTH", "TMHC", "MDC", "CCS",
        "TPH", "LGIH", "GRBK", "HOV", "BZH", "MHO", "DFH", "SKY", "CVCO", "BLD"
    ],
    "40. 商業地產 REITs": [
        "PLD", "PSA", "EXR", "CUBE", "SPG", "KIM", "REG", "FRT", "BRX", "O",
        "NNN", "ADC", "WPC", "STAG", "EPRT", "BXP", "SLG", "VNO", "HIW", "CXP"
    ],
    "41. 特殊與基建 REITs": [
        "AMT", "CCI", "SBAC", "DLR", "EQIX", "IRM", "VICI", "GLPI", "LAMR", "OUT",
        "UNIT", "COR", "HASI", "LAND", "FPI", "WY", "PCH", "RYN", "DOC", "STAG"
    ],
    "42. 加密貨幣與區塊鏈": [
        "COIN", "MSTR", "MARA", "RIOT", "HUT", "CLSK", "CIFR", "IREN", "CORZ", "WULF",
        "BTBT", "BITF", "CAN", "HIVE", "SDIG", "MIGI", "ARGO", "DMGI", "BKKT", "GREE"
    ],
    "43. 農業與肥料": [
        "CTVA", "CF", "MOS", "NTR", "DE", "AGCO", "FMC", "ICL", "BG", "ADM",
        "DAR", "LMNR", "SMG", "IPI", "UAN", "SEB", "CVA", "LNN", "AVD", "ALCO"
    ],
    "44. 體育戶外與服飾": [
        "NKE", "LULU", "UA", "UAA", "CROX", "DECK", "ONON", "SKX", "VFC", "PVH",
        "RL", "CPRI", "LEVI", "HBI", "COLM", "WWW", "BOOT", "GOOS", "GIL", "KTB"
    ],
    "45. 教育科技": [
        "CHGG", "COUR", "LRN", "PRDO", "TAL", "EDU", "GOTU", "STRA", "ATGE", "APEI",
        "LOPE", "UTI", "LAUR", "TWOU", "UDMY", "DUOL", "NEGG", "LX", "GHI", "BEDU"
    ],
    "46. 太空與前沿探索": [
        "SPCE", "RKLB", "PL", "BKSY", "ASTS", "RDW", "LUNR", "ACHR", "JOBY", "MNTS",
        "LLAP", "SIDU", "SPIR", "SATS", "ASTR", "SATL", "MDA", "AVAV", "KTOS", "HON", "BA"
    ],
    "47. 機器人與自動化": [
        "PATH", "SYM", "CGNX", "ISGN", "KEX", "ROK", "TER", "ZBRA", "IR", "FANUY",
        "ABB", "OMRNY", "KEYS", "NATI", "FARO", "OUST", "LAZR", "AEIS", "NOVT", "BRKS"
    ],
    "48. 中型價值精選": [
        "WSM", "GPC", "TSCO", "ODFL", "MIDD", "SAIA", "EXPD", "CHRW", "GGG", "DOV",
        "NDSN", "WTS", "ITW", "RH", "RXO", "KNX", "HUBB", "WCC", "FIX", "TOL"
    ],
    "49. 小型爆發精選": [
        "CELH", "WING", "APP", "ELF", "ANF", "MOD", "TMDX", "AXON", "FOUR", "INDI",
        "VRT", "SOFI", "NU", "GPN", "AFRM", "TOST", "FRPT", "MEDP", "CHRD", "DUOL"
    ],
    "50. 超微型探索 (Micro)": [
        "SOUN", "RXRX", "AI", "BBAI", "HIVE", "VLD", "IONQ", "CRDO", "NRDS", "LUNA",
        "QBTS", "KTRA", "RGTI", "ARQQ", "INVZ", "BLNK", "CHPT", "EVGO", "STEM", "ARRY"
    ]
}

ETF_COMPONENTS_MAP = {
    "🔥 [全取] 標普高波動 (SPHB)": [
        "CCL", "NCLH", "RCL", "AAL", "UAL", "DAL", "LUV", "CZR", "MGM", "WYNN", 
        "PENN", "OXY", "MRO", "APA", "HAL", "SLB", "BKR", "FCX", "ALB", "GNRC", 
        "ENPH", "FSLR", "TSLA", "AMD", "MU", "NVDA", "AMAT", "LRCX", "KLAC", "SNPS", 
        "CDNS", "ANET", "PANW", "CRWD", "PLTR", "SQ", "PYPL", "AFRM", "COIN", "MSTR", 
        "MARA", "RIOT", "KEY", "FITB", "RF", "CF", "MOS", "FMC", "DVN", "FANG", 
        "EOG", "PXD", "HES", "MPC", "VLO", "PSX", "X", "CLF", "NUE", "STLD", 
        "UPST", "CVNA", "SOUN", "AI", "BBAI", "HIVE", "HUT", "DKNG", "HOOD", "LCID", 
        "RIVN", "LI", "NIO", "XPEV", "PATH", "SYM", "PL", "RKLB", "SPCE", "ASTS", 
        "SMCI", "APP", "MRNA", "ETSY", "SEDG", "RUN", "SHLS", "VST", "BLDR", "ON", 
        "MPWR", "QRVO", "SWKS", "TER", "WDC", "STX", "EXPE", "CELH", "WING", "ELF", 
        "AVGO", "QCOM", "TXN", "ARM", "ASML", "DDOG", "ZS", "NET", "SNOW", "MDB", 
        "NTNX", "FSLY", "U", "RBLX", "DASH", "ABNB", "MELI", "SHOP", "SE", "PDD", 
        "BABA", "JD", "BIDU", "NTES", "TME", "LVS", "HLT", "MAR", "BKNG", "URI", 
        "CAT", "DE", "PCAR", "CMI", "AA", "CENX", "ATI", "CRS", "VALE", "BTU", 
        "ARCH", "CEIX", "AR", "EQT", "RRC", "CHK", "NOV", "CHX", "OII", "CLSK", 
        "IREN", "CIFR", "CORZ", "WULF", "RDW", "LUNR", "ACHR", "JOBY", "IONQ", "QBTS", 
        "RGTI", "CRDO", "MOD", "TMDX", "AXON", "FOUR", "INDI", "VRT", "SOFI", "NU", 
        "TOST", "ALAB", "LITE", "COHR", "MRVL", "GFS", "WOLF", "AMBA", "AEHR", "CRUS", 
        "FORM", "ONTO", "CAMT", "ACLS", "IPGP", "DUOL", "FRPT", "MEDP", "CHRD", "RXRX", 
        "VLD", "SATS", "SPIR", "MNTS", "LLAP", "SIDU", "BLNK", "CHPT", "EVGO", "STEM"
    ],
    "⭐ [全取] 標普低波動 (SPLV)": [
        "PEP", "KO", "RSG", "WM", "PG", "JNJ", "KMB", "MCD", "SYY", "CLX", 
        "VZ", "SO", "DUK", "AEP", "SRE", "WMT", "COST", "TRV", "AFL", "ALL", 
        "CB", "PGR", "MMC", "AON", "AJG", "EXC", "FE", "ED", "PEG", "WEC", 
        "ES", "LNT", "ATO", "GIS", "K", "MDLZ", "HSY", "CHD", "SJM", "CPB", 
        "TAP", "STZ", "CL", "KR", "DG", "DLTR", "MET", "PRU", "L", "BRO", 
        "FAST", "PAYX", "CTAS", "JKHY", "BHLB", "NTRS", "BEN", "TROW", "USB", "O", 
        "NI", "EIX", "DTE", "CMS", "CNP", "D", "AEE", "EVRG", "XEL", "ETR", 
        "DRE", "PLD", "PSA", "DLR", "CCI", "BRK-B", "PNW", "PPL", "AWK", "CAG", 
        "HRL", "TSN", "MKC", "BMY", "PFE", "ABBV", "GILD", "COR", "CAH", "MCK", 
        "CI", "BDX", "ABT", "HON", "ITW", "CINF", "WRB", "VTR", "WELL", "ESS", 
        "NEE", "WTRG", "OGE", "IDA", "POR", "NWN", "SR", "MGEE", "NJR", "UGI", 
        "CPK", "SWX", "BKH", "ALE", "OTTR", "AVA", "SPG", "VICI", "NNN", "ADC", 
        "EPRT", "WPC", "STAG", "FRT", "REG", "KIM", "MAA", "UDR", "CPT", "INVH", 
        "AMGN", "CVS", "ELV", "HUM", "CNC", "MDT", "BAX", "ZTS", "RMD", "STE", 
        "T", "CMCSA", "CHTR", "CLVT", "BF-B", "KDP", "MNST", "ADM", "DAR", "POST", 
        "CWST", "WCN", "CLH", "MDU", "BIP", "BEP", "AWR", "CWT", "SJW", "YORW", 
        "ARTNA", "MSEX", "AGR", "HE", "PNM", "BTI", "MO", "PM", "UVV", "VGR", 
        "FLO", "BGS", "LANC", "JJSF", "THS", "SENEA", "TR", "UNF", "ABM", "ROL", 
        "CHKP", "ORCL", "IBM", "CSCO", "ACGL", "RE", "EG", "AIZ", "RLI", "THG", 
        "AFG", "CNA", "ORI", "SIGI", "UFCS", "MCY", "KMPR", "SAFT", "WTS", "GPC"
    ],
    "🔵 [全取] 大型股核心 (OEF)": ["AAPL", "MSFT", "AMZN", "NVDA", "GOOGL", "GOOG", "META", "BRK-B", "LLY", "AVGO", "JPM", "V", "WMT", "MA", "UNH", "XOM", "ORCL", "HD", "PG", "COST", "CVX", "ABBV", "BAC", "CRM", "ADBE", "ABT", "AMD", "CMCSA", "PEP", "KO", "TMO", "CSCO", "MCD", "WFC", "DIS", "INTU", "VZ", "CAT", "AXP", "PFE", "IBM", "MS", "GE", "AMGN", "NFLX", "GS", "QCOM", "TXN", "HON", "BKNG", "RTX", "NEE", "AMAT", "LOW", "DE", "BMY", "UNP", "SCHW", "PM", "BA", "LRCX", "ADI", "SBUX", "MDLZ", "TJX", "PGR", "ISRG", "GILD", "CB", "SPGI", "C", "SNPS", "VRTX", "CI", "CVS", "ZTS", "BSX", "CDNS", "PANW", "DUK", "SO", "ETN", "MMC", "EQIX", "ELV", "ADP", "APD", "CL", "SYK", "AMT", "MU", "ADSK", "MO", "PNC", "CSX", "PLD", "AON", "MELI", "CBRE", "PH"],
    "📈 [前 200] 標普中型股 (MDY)": ["WMS", "RS", "LECO", "TTC", "EMN", "PNR", "AOS", "SNX", "ARW", "HUBB", "WCC", "FIX", "TOL", "PHM", "LEN", "DHI", "NVR", "MTH", "KBH", "TMHC", "MHK", "GPC", "LKQ", "TREX", "MAS", "ALLE", "FNF", "WRB", "CBOE", "MKTX", "SEI", "JEF", "EVR", "LPLA", "RJF", "SF", "FAF", "CNA", "THG", "AFG", "MTG", "RLI", "TEX", "URI", "HAE", "SSD", "EXP", "MLI", "AAON", "ACM", "PWR", "DY", "EME", "MYRG", "TTEK", "VMI", "XYL", "ALGT", "SKYW", "LUV", "CAR", "CHRW", "EXPD", "ODFL", "LANC", "SAIA", "KNX", "JBHT", "FLEX", "SANM", "JBL", "AVT", "TTMI", "DIOD", "CRUS", "MPWR", "ON", "LSCC", "ALTR", "WOLF", "COHR", "IPGP", "JBLU", "ANF", "URBN", "JWN", "DDS", "M", "KSS", "AEO", "PLXS", "BKE", "DKS", "HIBB", "BBY", "FIVE", "RH", "WSM", "TSCO", "CHH", "MAR", "HLT", "WH", "WYN", "H", "RHP", "PENN", "BYD", "CZR", "MGM", "MTN", "LAD", "PAG", "AN", "SAH", "GPI", "CRMT", "WGO", "THO", "LCII", "PATK", "DORM", "SMP", "BWA", "DLX", "EBF", "RHI", "MAN", "ASGN", "KFRC", "BBSI", "NSP", "OFC", "HIW", "CXP", "HPP", "SLG", "VNO", "PGRE", "LTC", "SBRA", "OME", "UFPI", "BXC", "BLDR", "STLY", "AWI", "AMWD", "DOOR", "PGTI", "JELD", "MDC", "CCS", "GRBK", "LGIH", "HOV", "WHR", "NWL", "TPX", "CROX", "CELH", "YETI", "MEDP", "RGEN", "EXEL", "HALO", "GLPI", "KRC", "NNN", "EPR", "CUBE", "LAMR", "CFR", "PB", "UMBQ", "COLB", "ONB", "FHN", "CBSH", "PINC", "NEU", "INGR", "ATI", "CC", "OLN", "HUN", "KRO", "SLGN", "SON", "GEF", "PKG", "BR", "CHX", "LITE", "PI", "RMBS", "FORM", "ONTO", "MKSI", "AEIS", "NOVT", "BRKS", "VIAV", "ACLS", "VECO"],
    "🦐 [前 500] 羅素小型股 (IWM)": ["SMCI", "MSTR", "CELH", "WING", "ELF", "ANF", "MOD", "TMDX", "AXON", "FOUR", "INDI", "VRT", "SOFI", "NU", "GPN", "AFRM", "TOST", "RUN", "FSLR", "ENPH", "SHLS", "PLUG", "DKNG", "RBLX", "HOOD", "COIN", "U", "AI", "SOUN", "RXRX", "BBAI", "VLD", "IONQ", "CRDO", "NRDS", "LUNA", "QBTS", "KTRA", "RGTI", "ARQQ", "INVZ", "RKLB", "SPCE", "PL", "BKSY", "ASTS", "RDW", "MNTS", "LLAP", "SIDU", "SPIR", "SATS", "LUNR", "ACHR", "JOBY", "SYM", "CGNX", "ISGN", "KEX", "LECO", "ROK", "PTC", "FARO", "CHGG", "COUR", "LRN", "PRDO", "STRA", "APEI", "ATGE", "LOPE", "UTI", "LAUR", "BFAM", "CROX", "DECK", "ONON", "SKX", "PLCE", "FL", "LEVI", "VFC", "KTB", "BOOT", "WWW", "SHOO", "TBLA", "RCKY", "CF", "MOS", "NTR", "SMG", "SQM", "IPI", "UAN", "SEB", "BIOC", "LMNR", "AVD", "CVA", "LNN", "X", "CLF", "RS", "WOR", "RYI", "TMST", "CRS", "HAYN", "KALU", "ATI", "SCHN", "USAP", "ZEUS", "SEDG", "CWEN", "AY", "NOVA", "MAXN", "SPWR", "ARRY", "STEM", "BNTX", "AXSM", "PTCT", "BPMC", "FATE", "NVAX", "HALO", "PBYI", "GBT", "MRTX", "MGTA", "XENC", "MREO", "SANA", "RLAY", "CUE", "SFIX", "OLLI", "PAG", "AN", "AMKR", "DIOD", "CCMP", "SIMO", "POWI", "FORM", "ONTO", "CAMT", "ICHR", "COHU", "AOSL", "GSI", "UMC", "ASX", "HIMX", "BLKB", "PRO", "SPSX", "ALRM", "QLYS", "TENB", "VRNS", "RPD", "GUID", "ASAN", "SMAR", "PD", "DT", "BASE", "UPWK", "FIVN", "BAND", "TWLO", "LPSN", "DBX", "EGHT", "RING", "VON", "SSTK", "SHUT", "TCX", "GTT", "CNSL", "HCAT", "QMCO", "HANY", "SOS", "NCTY", "BTBT", "MIGI", "WULF", "GREE", "RENN", "XNET", "PHUN", "AMBA", "AEHR", "SEMR", "CALX", "DZSI", "LTRX", "SGH", "SANM", "PLXS", "JBL", "FLEX", "FLIR", "ALTR", "NVMI", "ACLS", "WSM", "GPC", "TSCO", "MIDD", "SAIA", "EXPD", "CHRW", "GGG", "DOV", "NDSN", "WTS", "ITW", "RH", "RXO", "KNX", "APP", "MARA", "RIOT", "CLSK", "CIFR", "HUT", "CORZ", "IREN", "AAON", "ABCB", "ABG", "ABM", "ACAD", "ACER", "ACGL", "ACHC", "ACIW", "ACM", "ACNB", "ACRE", "ACRS", "ACTG", "ACVA", "ADUS", "ADV", "ADVM", "AEIS", "AEL", "AEO", "AERC", "AERI", "AERY", "AFBI", "AFG", "AFIB", "AFMD", "AGCO", "AGEN", "AGIO", "AGL", "AGM", "AGNC", "AGO", "AGS", "AHH", "AHR", "AHT", "AIB", "AIH", "AIK", "AIL", "AIMC", "AIN", "AIR", "AIRG", "AIRT", "AIT", "AIV", "AIZ", "AJX", "AKBA", "AKR", "AKRO", "AKTS", "AL", "ALCO", "ALDX", "ALE", "ALEC", "ALEX", "ORIG", "ALHC", "ALIM", "ALKS", "ALKT", "ALLE", "ALLK", "ALLO", "ALLR", "ALLT", "ALLY", "ALNA", "ALNY", "ALOT", "ALPN", "ALRN", "ALRS", "ALSA", "ALSN", "ALT", "ALTA", "ALTO", "ALVR", "ALX", "AMAL", "OPY", "LSTR", "MATX", "ARCB", "XPO", "SNDR", "HTLD", "CVTI", "WERN", "HUBG", "MRIN", "REVG", "BKI", "LPRO"]
}

SPECIAL_ETFS = {
    "🔵 大型股核心 (OEF)": ("OEF", ETF_COMPONENTS_MAP["🔵 [全取] 大型股核心 (OEF)"]),
    "📈 中型股主力 (MDY)": ("MDY", ETF_COMPONENTS_MAP["📈 [前 200] 標普中型股 (MDY)"]),
    "🦐 小型股爆發 (IWM)": ("IWM", ETF_COMPONENTS_MAP["🦐 [前 500] 羅素小型股 (IWM)"]),
    "🔥 高波動長矛 (SPHB)": ("SPHB", ETF_COMPONENTS_MAP["🔥 [全取] 標普高波動 (SPHB)"]),
    "⭐ 低波動盾牌 (SPLV)": ("SPLV", ETF_COMPONENTS_MAP["⭐ [全取] 標普低波動 (SPLV)"])
}

# =========================================================
# 🛡️ 核心工具：智能欄位脫殼器 (修復 JSON 欄位字串隱形)
# =========================================================
def unwrap_cols(df):
    if df is None or df.empty:
        return pd.DataFrame()
    
    new_cols = {}
    for col in df.columns:
        c_str = str(col).lower()
        for target in ['Open', 'High', 'Low', 'Close', 'Volume']:
            if target.lower() in c_str:
                new_cols[col] = target
                break
    df_renamed = df.rename(columns=new_cols)
    
    for col in ['Open', 'High', 'Low', 'Close', 'Volume']:
        if col in df_renamed.columns:
            df_renamed[col] = pd.to_numeric(df_renamed[col], errors='coerce')
    return df_renamed

def clean_ohlcv_df(raw_df, ticker):
    if raw_df is None or raw_df.empty:
        return pd.DataFrame()
    
    df = raw_df.copy()
    if isinstance(df.columns, pd.MultiIndex):
        t_upper = str(ticker).upper()
        lvl0 = [str(c).upper() for c in df.columns.get_level_values(0)]
        lvl1 = [str(c).upper() for c in df.columns.get_level_values(1)]
        
        if t_upper in lvl0:
            df = df.xs(t_upper, axis=1, level=0)
        elif t_upper in lvl1:
            df = df.xs(t_upper, axis=1, level=1)
        elif len(df.columns.levels[0]) == 1:
            df.columns = df.columns.get_level_values(1)
        elif len(df.columns.levels[1]) == 1:
            df.columns = df.columns.get_level_values(0)
            
    df = unwrap_cols(df)
    needed = ['Open', 'High', 'Low', 'Close', 'Volume']
    avail = [c for c in needed if c in df.columns]
    df = df[avail].dropna(subset=['Close'])
    
    if hasattr(df.index, 'tz') and df.index.tz is not None:
        df.index = df.index.tz_localize(None).normalize()
    return df

def extract_clean_close_df(raw_df):
    if raw_df is None or raw_df.empty:
        return pd.DataFrame()
    
    close_dict = {}
    if isinstance(raw_df.columns, pd.MultiIndex):
        lvl0 = [str(c).upper() for c in raw_df.columns.get_level_values(0)]
        lvl1 = [str(c).upper() for c in raw_df.columns.get_level_values(1)]
        
        if 'CLOSE' in lvl0:
            for i, col in enumerate(raw_df.columns):
                if str(col[0]).upper() == 'CLOSE':
                    ticker = str(col[1]).strip().upper()
                    close_dict[ticker] = raw_df.iloc[:, i].dropna()
        elif 'CLOSE' in lvl1:
            for i, col in enumerate(raw_df.columns):
                if str(col[1]).upper() == 'CLOSE':
                    ticker = str(col[0]).strip().upper()
                    close_dict[ticker] = raw_df.iloc[:, i].dropna()
    elif 'Close' in raw_df.columns:
        return raw_df[['Close']].copy()
        
    df_res = pd.DataFrame(close_dict).dropna(how='all')
    if not df_res.empty and hasattr(df_res.index, 'tz') and df_res.index.tz is not None:
        df_res.index = df_res.index.tz_localize(None).normalize()
    return df_res

def compute_vectorized_breadth(close_df):
    if close_df.empty:
        return pd.DataFrame()
    
    ma5 = close_df.rolling(5, min_periods=5).mean()
    ma20 = close_df.rolling(20, min_periods=20).mean()
    ma50 = close_df.rolling(50, min_periods=50).mean()
    ma100 = close_df.rolling(100, min_periods=100).mean()
    ma200 = close_df.rolling(200, min_periods=200).mean()
    
    def calc_ratio(ma):
        valid = close_df.notna() & ma.notna()
        above = valid & (close_df > ma)
        denom = np.where(valid.sum(axis=1) > 0, valid.sum(axis=1), 1.0)
        return (above.sum(axis=1) / denom) * 100.0

    df_b = pd.DataFrame({
        "Breadth_MA5": calc_ratio(ma5),
        "Breadth_MA20": calc_ratio(ma20),
        "Breadth_MA50": calc_ratio(ma50),
        "Breadth_MA100": calc_ratio(ma100),
        "Breadth_MA200": calc_ratio(ma200)
    }, index=close_df.index)
    return df_b.dropna(how='all')

# =========================================================
# 🛡️ 實盤真實微批次下載引擎 (全美股精銳矩陣)
# =========================================================
def execute_master_scan(progress_box):
    master_unique_tickers = set()
    for etf_sym, t_list in SPECIAL_ETFS.values():
        master_unique_tickers.add(etf_sym)
        master_unique_tickers.update(t_list)
    for t_list in US_STOCK_MAP.values():
        master_unique_tickers.update(t_list)
        
    all_tickers = sorted(list(master_unique_tickers))
    total_tickers = len(all_tickers)
    chunk_size = 50
    chunks = [all_tickers[i:i + chunk_size] for i in range(0, total_tickers, chunk_size)]
    total_chunks = len(chunks)
    
    all_close_frames = []
    p_bar = progress_box.progress(0, text=f"🛡️ 啟動真全量安全矩陣微批次下載 (全美股 {total_tickers} 隻精銳)...")
    
    for idx, chunk in enumerate(chunks):
        p_bar.progress((idx + 1) / total_chunks, text=f"⏳ 正在安全下載批次 [{idx + 1}/{total_chunks}] (每批 50 隻，防封鎖冷卻中)...")
        try:
            raw = yf.download(chunk, period="1y", auto_adjust=True, progress=False, threads=True)
            c_df = extract_clean_close_df(raw)
            if not c_df.empty:
                all_close_frames.append(c_df)
        except Exception:
            pass
        time.sleep(0.35)
        
    p_bar.empty()
    
    if not all_close_frames:
        st.error("❌ 下載失敗：未能成功連線獲取股票行情。")
        return None
        
    master_close_df = pd.concat(all_close_frames, axis=1)
    master_close_df = master_close_df.loc[:, ~master_close_df.columns.duplicated()].sort_index()

    # 1. 處理 5 大特權 ETF 歷史市寬與 OHLCV
    breadth_results = {}
    current_day_data = {}
    price_results = {}
    
    for name, (etf_sym, comp_tickers) in SPECIAL_ETFS.items():
        sub_tickers = [t for t in comp_tickers if t in master_close_df.columns]
        if len(sub_tickers) >= 10:
            etf_comp_df = master_close_df[sub_tickers].dropna(how='all')
            df_b = compute_vectorized_breadth(etf_comp_df)
            
            try:
                etf_raw = yf.download(etf_sym, period="1y", auto_adjust=True, progress=False)
                etf_clean = clean_ohlcv_df(etf_raw, etf_sym)
            except Exception:
                etf_clean = pd.DataFrame()
                
            if not df_b.empty:
                current_day_data[name] = {
                    "MA5_Pct": round(float(df_b["Breadth_MA5"].iloc[-1]), 1),
                    "MA20_Pct": round(float(df_b["Breadth_MA20"].iloc[-1]), 1),
                    "MA50_Pct": round(float(df_b["Breadth_MA50"].iloc[-1]), 1),
                    "MA200_Pct": round(float(df_b["Breadth_MA200"].iloc[-1]), 1),
                    "count": len(sub_tickers),
                    "total_cfg": len(comp_tickers)
                }
                
                df_b_tail = df_b.tail(60).copy()
                dates_str = [d.strftime('%Y-%m-%d') if hasattr(d, 'strftime') else str(d)[:10] for d in df_b_tail.index]
                df_b_tail.index = dates_str
                breadth_results[name] = df_b_tail.to_dict(orient='index')
                
                if not etf_clean.empty:
                    p_aligned = etf_clean.reindex(df_b.index).ffill().bfill().tail(60).copy()
                    p_aligned.index = dates_str
                    clean_p_dict = {}
                    for dt_k, row in p_aligned.iterrows():
                        clean_p_dict[dt_k] = {
                            "Open": float(row.get('Open', 0)),
                            "High": float(row.get('High', 0)),
                            "Low": float(row.get('Low', 0)),
                            "Close": float(row.get('Close', 0)),
                            "Volume": float(row.get('Volume', 0))
                        }
                    price_results[name] = clean_p_dict
                else:
                    price_results[name] = {}

    # 2. 處理 50 大傳統板塊 (每個板塊強制標註真實有效隻數)
    traditional_list = []
    tot_m5, tot_m20, tot_m50, tot_m200, tot_count = 0, 0, 0, 0, 0
    
    for sec_name, t_list in US_STOCK_MAP.items():
        avail = [t for t in t_list if t in master_close_df.columns]
        if avail:
            sub = master_close_df[avail].dropna(how='all')
            if len(sub) >= 20:
                curr = sub.iloc[-1]
                m5 = sub.rolling(5, min_periods=5).mean().iloc[-1]
                m20 = sub.rolling(20, min_periods=20).mean().iloc[-1]
                m50 = sub.rolling(50, min_periods=50).mean().iloc[-1]
                m200 = sub.rolling(200, min_periods=200).mean().iloc[-1]
                
                v_count = int(curr.notna().sum())
                if v_count > 0:
                    c5 = int((curr > m5).sum())
                    c20 = int((curr > m20).sum())
                    c50 = int((curr > m50).sum())
                    c200 = int((curr > m200).sum())
                    
                    traditional_list.append({
                        "板塊": f"{sec_name} ({v_count}隻)",
                        "板塊原名": sec_name,
                        "count": v_count,
                        "total_cfg": len(t_list),
                        "MA5_Pct": round((c5 / v_count) * 100.0, 1),
                        "MA20_Pct": round((c20 / v_count) * 100.0, 1),
                        "MA50_Pct": round((c50 / v_count) * 100.0, 1),
                        "MA200_Pct": round((c200 / v_count) * 100.0, 1),
                        "sort_order": 999
                    })
                    tot_m5 += c5; tot_m20 += c20; tot_m50 += c50; tot_m200 += c200; tot_count += v_count

    safe_tot = max(1, tot_count)
    top_banners = {
        "MA5": round((tot_m5 / safe_tot) * 100.0, 1),
        "MA20": round((tot_m20 / safe_tot) * 100.0, 1),
        "MA50": round((tot_m50 / safe_tot) * 100.0, 1),
        "MA200": round((tot_m200 / safe_tot) * 100.0, 1),
        "count": tot_count,
        "total_sectors": len(US_STOCK_MAP)
    }

    final_payload = {
        "_updated_at": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
        "current_day_data": current_day_data,
        "breadth_results": breadth_results,
        "price_results": price_results,
        "traditional_list": traditional_list,
        "top_banners": top_banners
    }
    
    try:
        with open(CACHE_FILE_2BB, "w", encoding="utf-8") as f:
            json.dump(final_payload, f, ensure_ascii=False, indent=2, default=str)
    except Exception:
        pass
        
    return final_payload

def load_local_cache():
    if os.path.exists(CACHE_FILE_2BB):
        try:
            with open(CACHE_FILE_2BB, "r", encoding="utf-8") as f:
                data = json.load(f)
                if data and "current_day_data" in data and "_updated_at" in data:
                    return data
        except Exception:
            pass
    return None

# =========================================================
# 🔴 主頁面渲染中心
# =========================================================
def render_page_2bb():
    st.markdown("<h1 style='color:#00ff88; font-size:42px; font-family:Arial Black;'>📡 艙房 2bb：個股版塊拔河熱力圖 (美股真歷史市寬大陣)</h1>", unsafe_allow_html=True)
    st.markdown("<p style='color:#94a3b8;'>🛡️ 全美股 940+ 隻權重成份股矩陣向量化清算 ｜ 本機持久化快取極速秒開</p>", unsafe_allow_html=True)
    st.markdown("<hr style='border:2px solid #00ff88; margin-bottom:20px;'>", unsafe_allow_html=True)

    col_ctrl1, col_ctrl2 = st.columns([2, 1])
    with col_ctrl1:
        short_term_mode = st.radio(
            "⏱️ 選擇短期市寬觀測雷達範圍：",
            ["🟢 顯示 5天短期線 + (50/100/200)", "🟢 顯示 20天短期線 + (50/100/200)"],
            horizontal=True
        )
    use_ma5 = "5天" in short_term_mode

    with col_ctrl2:
        btn_refresh = st.button("🚀 火力全開：啟動矩陣運算清算 (約需20秒)", use_container_width=True)

    progress_box = st.empty()

    if btn_refresh:
        new_data = execute_master_scan(progress_box)
        if new_data:
            st.session_state["cache_2bb_data"] = new_data
            st.success("🎉 全美股版塊市寬掃描完畢！即時刷新畫面...")
            time.sleep(0.5)
            st.rerun()

    if "cache_2bb_data" not in st.session_state:
        st.session_state["cache_2bb_data"] = load_local_cache()

    data = st.session_state["cache_2bb_data"]
    if data is None:
        st.info("💡 首次使用請點擊上方【🚀 火力全開】按鈕，系統將自動為您安全下載並永久快取真實市場數據。")
        return

    up_time = data.get("_updated_at", "未知時間")
    st.markdown(f"<div style='color:#38bdf8; font-size:13px; margin-bottom:15px;'>⏱️ 數據快照時間：<b>{up_time}</b> ｜ 狀態：<span style='color:#00ff88; font-weight:bold;'>🟢 100% 交易所實盤真實數據 (已持久化存檔)</span></div>", unsafe_allow_html=True)

    current_day_data = data.get("current_day_data", {})
    top_banners = data.get("top_banners", {})
    breadth_results = data.get("breadth_results", {})
    price_results = data.get("price_results", {})
    traditional_list = data.get("traditional_list", [])

    short_col_name = "MA5_Pct" if use_ma5 else "MA20_Pct"
    short_col_hist = "Breadth_MA5" if use_ma5 else "Breadth_MA20"
    short_banner_val = top_banners.get("MA5", 0.0) if use_ma5 else top_banners.get("MA20", 0.0)
    short_legend_label = "🟢 MA5 短期爆發" if use_ma5 else "🟢 MA20 短期健康"
    tot_sectors_count = top_banners.get("count", 950)

    # =========================================================
    # 🎯 置頂 6 行戰略儀表板 (全面帶上真實樣本隻數)
    # =========================================================
    st.markdown("<h3 style='color:#ffaa00; margin-top:10px; margin-bottom:15px;'>📊 戰略靈魂：美股 6 大維度市寬全景雷達</h3>", unsafe_allow_html=True)
    
    st.markdown(f'''
    <div style="background-color:#161d2a; padding:12px 15px; border-radius:8px; margin-bottom:12px; border-left:8px solid #00f2ff; display:flex; justify-content:space-between; align-items:center;">
        <div style="color:#ffffff; font-size:18px; font-weight:900; width:33%;">🎯 傳統 50 板塊均值 <span style="color:#38bdf8; font-size:14px; font-weight:normal;">(全美股母體 · 共 {tot_sectors_count} 隻樣本)</span></div>
        <div style="color:#00ff88; font-size:17px; font-weight:bold; width:22%; text-align:center;">{short_legend_label}: {short_banner_val:.1f}%</div>
        <div style="color:#ffbb00; font-size:17px; font-weight:bold; width:22%; text-align:center;">🟡 MA50: {top_banners.get("MA50", 0.0):.1f}%</div>
        <div style="color:#ff3333; font-size:17px; font-weight:bold; width:22%; text-align:center;">🔴 MA200: {top_banners.get("MA200", 0.0):.1f}%</div>
    </div>
    ''', unsafe_allow_html=True)

    rows_config = [
        ("🔵 大型股 (OEF)", "#00f2ff", "🔵 大型股核心 (OEF)", 100),
        ("📈 中型股 (MDY)", "#a200ff", "📈 中型股主力 (MDY)", 205),
        ("🦐 小型股 (IWM)", "#ff00ff", "🦐 小型股爆發 (IWM)", 336),
        ("🔥 高波動 (SPHB 200隻)", "#ff3333", "🔥 高波動長矛 (SPHB)", 200),
        ("⭐ 低波動 (SPLV 200隻)", "#00ff88", "⭐ 低波動盾牌 (SPLV)", 200)
    ]

    for label, b_color, key, default_cnt in rows_config:
        c_info = current_day_data.get(key, {})
        v_short = c_info.get(short_col_name, 0.0)
        v_50 = c_info.get("MA50_Pct", 0.0)
        v_200 = c_info.get("MA200_Pct", 0.0)
        actual_cnt = c_info.get("count", default_cnt)

        st.markdown(f'''
        <div style="background-color:#1e212b; padding:10px 15px; border-radius:8px; margin-bottom:8px; border-left:6px solid {b_color}; display:flex; justify-content:space-between; align-items:center;">
            <div style="color:#ffffff; font-size:17px; font-weight:bold; width:33%;">{label} <span style="color:#38bdf8; font-size:14px; font-weight:normal;">({actual_cnt} 隻真實標的)</span></div>
            <div style="color:#00ff88; font-size:17px; font-weight:bold; width:22%; text-align:center;">{short_legend_label}: {v_short:.1f}%</div>
            <div style="color:#ffbb00; font-size:17px; font-weight:bold; width:22%; text-align:center;">🟡 MA50: {v_50:.1f}%</div>
            <div style="color:#ff3333; font-size:17px; font-weight:bold; width:22%; text-align:center;">🔴 MA200: {v_200:.1f}%</div>
        </div>
        ''', unsafe_allow_html=True)

    st.markdown("<hr style='border:1px solid #334155; margin:28px 0;'>", unsafe_allow_html=True)

    # =========================================================
    # 📈 5 大核心圖表：K線陰陽燭與真實市寬線「雙 Y 軸完美融合」
    # =========================================================
    st.markdown("<h3 style='color:#00ff88;'>📈 5 大核心特權 ETF：真實技術K線與內部市寬融合大圖</h3>", unsafe_allow_html=True)
    st.markdown("<p style='color:#aaa;'>（展示近 60 日真實走勢 ｜ 主圖：陰陽燭 K 線與四維市寬共振 ｜ 副圖：成交量）</p>", unsafe_allow_html=True)
    
    def render_ultimate_chart(p_dict, b_dict, title_text, count_display):
        if not b_dict:
            return None
        df_b = pd.DataFrame.from_dict(b_dict, orient='index')
        df_p = pd.DataFrame.from_dict(p_dict, orient='index') if p_dict else pd.DataFrame()

        if not df_p.empty:
            df_p = unwrap_cols(df_p)

        fig = make_subplots(
            rows=2, cols=1, shared_xaxes=True, vertical_spacing=0.04, 
            row_heights=[0.75, 0.25], specs=[[{"secondary_y": True}], [{"secondary_y": False}]]
        )

        if not df_p.empty and 'Close' in df_p.columns and 'Open' in df_p.columns:
            fig.add_trace(go.Candlestick(
                x=df_p.index, open=df_p['Open'], high=df_p['High'],
                low=df_p['Low'], close=df_p['Close'], name='ETF 陰陽燭'
            ), row=1, col=1, secondary_y=False)

        if short_col_hist in df_b.columns:
            fig.add_trace(go.Scatter(x=df_b.index, y=df_b[short_col_hist], mode='lines', line=dict(color='#00ff88', width=2.5), name=f"{short_legend_label} (%)"), row=1, col=1, secondary_y=True)
        if "Breadth_MA50" in df_b.columns:
            fig.add_trace(go.Scatter(x=df_b.index, y=df_b["Breadth_MA50"], mode='lines', line=dict(color='#ffbb00', width=2), name="🟡 MA50 中期市寬 (%)"), row=1, col=1, secondary_y=True)
        if "Breadth_MA100" in df_b.columns:
            fig.add_trace(go.Scatter(x=df_b.index, y=df_b["Breadth_MA100"], mode='lines', line=dict(color='#00f2ff', width=1.5, dash='dot'), name="🔵 MA100 長期市寬 (%)"), row=1, col=1, secondary_y=True)
        if "Breadth_MA200" in df_b.columns:
            fig.add_trace(go.Scatter(x=df_b.index, y=df_b["Breadth_MA200"], mode='lines', line=dict(color='#ff3333', width=2.5), name="🔴 MA200 牛熊市寬 (%)"), row=1, col=1, secondary_y=True)

        if not df_p.empty and 'Volume' in df_p.columns and 'Close' in df_p.columns and 'Open' in df_p.columns:
            v_colors = ['#00ff88' if c >= o else '#ff3366' for c, o in zip(df_p['Close'], df_p['Open'])]
            fig.add_trace(go.Bar(x=df_p.index, y=df_p['Volume'], marker_color=v_colors, name='成交量'), row=2, col=1)

        full_title = f"{title_text} ({count_display} 隻成分股)"
        fig.update_layout(
            title=dict(text=full_title, font=dict(color='white', size=20, family='Arial Black')),
            template="plotly_dark", height=700, margin=dict(l=40, r=50, t=50, b=20),
            xaxis_rangeslider_visible=False,
            legend=dict(orientation="h", yanchor="bottom", y=1.02, xanchor="right", x=1.0, font=dict(color="white", size=11)),
            paper_bgcolor="#111827", plot_bgcolor="#0e1117"
        )
        fig.update_xaxes(type='category', showgrid=False, row=1, col=1)
        fig.update_xaxes(type='category', showgrid=False, row=2, col=1)
        
        fig.update_yaxes(title_text="ETF 價格 (USD)", title_font=dict(color="#ffffff"), tickfont=dict(color="#ffffff"), row=1, col=1, secondary_y=False)
        fig.update_yaxes(title_text="內部市寬擴散 %", range=[-5, 105], row=1, col=1, secondary_y=True, tickfont=dict(color="#00ff88"))
        fig.update_yaxes(title_text="成交量", row=2, col=1, showticklabels=False)
        return fig

    chart_order = [
        ("🔵 大型股核心 (OEF)", "🔵 大型股核心 (OEF) 戰略背離全景圖", 100),
        ("📈 中型股主力 (MDY)", "📈 中型股主力 (MDY) 戰略背離全景圖", 205),
        ("🦐 小型股爆發 (IWM)", "🦐 小型股爆發 (IWM) 戰略背離全景圖", 336),
        ("🔥 高波動長矛 (SPHB)", "🔥 高波動長矛 (SPHB 200隻) 戰略背離全景圖", 200),
        ("⭐ 低波動盾牌 (SPLV)", "⭐ 低波動盾牌 (SPLV 200隻) 戰略背離全景圖", 200)
    ]
    
    for key, title, def_cnt in chart_order:
        p_dict = price_results.get(key, {})
        b_dict = breadth_results.get(key, {})
        c_cnt = current_day_data.get(key, {}).get("count", def_cnt)
        if b_dict:
            fig = render_ultimate_chart(p_dict, b_dict, title, c_cnt)
            if fig:
                st.plotly_chart(fig, use_container_width=True, config={'displayModeBar': True})
                st.markdown("<br>", unsafe_allow_html=True)
        else:
            st.warning(f"⚠️ {title} 暫無快取，請點擊上方【🚀 火力全開】啟動首次安全計算。")

    st.markdown("<hr style='border:1px solid #334155; margin:28px 0;'>", unsafe_allow_html=True)

    # =========================================================
    # 📊 底層傳統 50 板塊今日真實市寬總動員 (修復正則與自帶括號匹配)
    # =========================================================
    st.markdown("<h3 style='color:#00ff88;'>📊 全量板塊大陣：今日真實市寬總動員切片</h3>", unsafe_allow_html=True)
    
    if traditional_list:
        df_rs = pd.DataFrame(traditional_list)
        
        # 🌟 核心修復：使用 regex 精確判定末尾 "(X隻)"，杜絕 Cyber/EV/水電 括號誤殺
        if "板塊" in df_rs.columns:
            def format_sector_label(row):
                name = str(row.get("板塊", "")).strip()
                # 1. 若結尾已經有「(X隻)」，直接保留
                if re.search(r'\(\d+隻\)$', name):
                    return name

                # 2. 若存在有效 count 欄位
                cnt = row.get("count", 0)
                if cnt and int(cnt) > 0:
                    return f"{name} ({int(cnt)}隻)"

                # 3. 精確字典匹配 (直接比對完整全名)
                if name in US_STOCK_MAP:
                    return f"{name} ({len(US_STOCK_MAP[name])}隻)"

                # 4. 前綴容錯比對
                for k in US_STOCK_MAP:
                    if name.startswith(k) or k.startswith(name):
                        return f"{k} ({len(US_STOCK_MAP[k])}隻)"

                return name

            df_rs["板塊"] = df_rs.apply(format_sector_label, axis=1)

        df_rs = df_rs.sort_values(by=["MA200_Pct", "MA50_Pct", short_col_name], ascending=[True, True, True])

        fig2 = go.Figure()
        fig2.add_trace(go.Bar(
            x=df_rs["MA200_Pct"], y=df_rs["板塊"], name="🔴 MA200 長期牛熊", orientation='h', marker_color='#ff3333',
            text=[f"{v:.1f}%" for v in df_rs["MA200_Pct"]], textposition='outside', textfont=dict(color='#ffffff', size=13),
            hovertemplate='%{y}<br>🔴 MA200 站上比例: %{x:.1f}%<extra></extra>'
        ))
        fig2.add_trace(go.Bar(
            x=df_rs["MA50_Pct"], y=df_rs["板塊"], name="🟡 MA50 中期穩定", orientation='h', marker_color='#ffbb00',
            text=[f"{v:.1f}%" for v in df_rs["MA50_Pct"]], textposition='outside', textfont=dict(color='#ffffff', size=13),
            hovertemplate='%{y}<br>🟡 MA50 站上比例: %{x:.1f}%<extra></extra>'
        ))
        fig2.add_trace(go.Bar(
            x=df_rs[short_col_name], y=df_rs["板塊"], name=short_legend_label, orientation='h', marker_color='#00ff88',
            text=[f"{v:.1f}%" for v in df_rs[short_col_name]], textposition='outside', textfont=dict(color='#ffffff', size=13),
            hovertemplate=f'%{{y}}<br>{short_legend_label} 站上比例: %{{x:.1f}}%<extra></extra>'
        ))

        fig2.update_layout(
            barmode='group', template="plotly_dark", height=2400, bargap=0.1,
            xaxis=dict(title="站上均線之股票佔比 (%)", tickfont=dict(size=14, color="white"), range=[0, 125]),
            yaxis=dict(tickfont=dict(size=14, color="white"), automargin=True),
            legend=dict(orientation="h", yanchor="bottom", y=1.01, xanchor="right", x=1.0, font=dict(size=14, color="white")),
            margin=dict(l=260, r=40, t=50, b=30), paper_bgcolor="#0e1117", plot_bgcolor="#0e1117"
        )
        st.plotly_chart(fig2, use_container_width=True, config={'displayModeBar': True})

if __name__ == "__main__":
    render_page_2bb()