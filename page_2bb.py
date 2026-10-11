import streamlit as st
import yfinance as yf
import pandas as pd
import numpy as np
import plotly.graph_objects as go
from plotly.subplots import make_subplots
import time
from datetime import datetime

# =========================================================
# 🛡️ 戰略盾牌：多層級字典安全防爆取值函數
# =========================================================
def get_safe_dict_val(d, k1, k2):
    try:
        val = d.get(k1, {}).get(k2, 0.0)
        return float(val)
    except Exception:
        return 0.0

def _extract_close_series_single(raw_df, ticker):
    try:
        if raw_df is None or raw_df.empty: return pd.Series(dtype=float)
        if isinstance(raw_df.columns, pd.MultiIndex):
            if ticker in raw_df.columns.get_level_values(0):
                if "Close" in raw_df[ticker].columns: return raw_df[ticker]["Close"].dropna()
        elif "Close" in raw_df.columns: return raw_df["Close"].dropna()
    except: pass
    return pd.Series(dtype=float)

# ===================================================
# 🗄️ 戰略核心：大板塊精銳部隊
# ===================================================
TOP_N_LEADERS = 40

US_STOCK_MAP = {
    "1. 半導體設備與設計": ["NVDA", "TSM", "AVGO", "ASML", "AMD", "QCOM", "TXN"],
    "2. AI與大數據雲端": ["MSFT", "GOOGL", "ORCL", "ADBE", "CRM", "PLTR"],
    "3. 基礎軟件與 SaaS": ["INTU", "VMW", "CDNS", "PTC", "MSTR", "WDAY"],
    "4. 網絡安全 (Cyber)": ["PANW", "CRWD", "FTNT", "ZS", "CYBR"],
    "5. 消費電子與硬件": ["AAPL", "HPQ", "DELL", "STX", "WDC", "APH"],
    "6. 通訊與網絡設備": ["CSCO", "MSI", "JNPR", "ANET", "COMM"],
    "7. 互聯網平台內容": ["META", "GOOGL", "PINS", "SNAP", "MATCH"],
    "8. 媒體與影視娛樂": ["NFLX", "DIS", "WBD", "PARA", "LYV"],
    "9. 電子商務與零售": ["AMZN", "EBAY", "ETSY", "MELI", "SHOP"],
    "10. 傳統零售百貨": ["WMT", "COST", "TGT", "DG", "DLTR", "KR"],
    "11. 核心消費品": ["PG", "KO", "PEP", "PM", "MO", "EL"],
    "12. 汽車製造商": ["F", "GM", "STLA", "TM", "HMC", "RACE"],
    "13. 電動車與自駕 (EV)": ["TSLA", "RIVN", "LCID", "LI", "NIO"],
    "14. 汽車零部件": ["MGA", "APTV", "BWA", "LEA", "VC"],
    "15. 航空航天與國防": ["LMT", "RTX", "NOC", "GD", "BA"],
    "16. 重型機械裝備": ["CAT", "DE", "CMI", "PCAR", "OSK"],
    "17. 工業綜合集團": ["GE", "HON", "MMM", "EMR", "ITW"],
    "18. 運輸與物流": ["UNP", "UPS", "FDX", "NSC", "CSX"],
    "19. 航空與機場": ["LUV", "DAL", "AAL", "UAL", "ALK"],
    "20. 旅遊酒店博彩": ["BKNG", "ABNB", "MAR", "HLT", "LVS"],
    "21. 餐飲連鎖": ["MCD", "SBUX", "YUM", "CMG", "DPZ"],
    "22. 商業銀行巨頭": ["JPM", "BAC", "WFC", "C", "GS", "MS"],
    "23. 區域性銀行": ["KRE", "PNC", "TFC", "USB", "EWBC"],
    "24. 投資與資產 management": ["BLK", "BX", "TROW", "APO", "KKR"],
    "25. 金融科技與支付": ["V", "MA", "SQ", "PYPL", "AFRM"],
    "26. 保險經紀與服務": ["CB", "PGR", "TRV", "MET", "AIG"],
    "27. 傳統製藥巨頭": ["LLY", "NVO", "JNJ", "MRK", "ABBV"],
    "28. 大中型生物科技": ["MRNA", "BNTX", "BIIB", "INCY", "BMRN"],
    "29. 醫療設備與器械": ["MDT", "ABT", "SYK", "BSX", "EW"],
    "30. 醫療服務與管理": ["UNH", "ELV", "CVS", "CI", "HUM"],
    "31. 基因與生命科學": ["ILMN", "TMO", "A", "DHR", "CTLT"],
    "32. 傳統能源 (油氣)": ["XOM", "CVX", "COP", "SLB", "HAL"],
    "33. 油氣設備與服務": ["SLB", "HAL", "BKR", "FTI", "NBR"],
    "34. 太陽能與清潔能源": ["FSLR", "ENPH", "SEDG", "RUN", "SHLS"],
    "35. 公用事業 (水電)": ["NEE", "SO", "DUK", "SRE", "AEP"],
    "36. 基礎與特殊化工": ["LIN", "APD", "DOW", "LYB", "CE"],
    "37. 鋼鐵與基礎金屬": ["NUE", "STLD", "X", "CLF", "RS"],
    "38. 黃金與貴金屬": ["NEM", "GOLD", "FCX", "SCCO", "AEM"],
    "39. 住宅房地產開發": ["LEN", "DHI", "PHM", "TOL", "NVR"],
    "40. 商業地產 REITs": ["PLD", "AMT", "EQIX", "CCI", "PSA"],
    "41. 特殊與基建 REITs": ["AMT", "CCI", "SBAC", "DLR", "EQIX"],
    "42. 加密貨幣與區塊鏈": ["COIN", "MSTR", "MARA", "RIOT", "HUT"],
    "43. 農業與肥料": ["DE", "CTVA", "CF", "MOS", "NTR"],
    "44. 體育戶外與服飾": ["NKE", "LULU", "UA", "UAA", "CROX"],
    "45. 教育科技": ["CHGG", "COUR", "LRN", "TWOU", "PRDO"],
    "46. 太空與前沿探索": ["SPCE", "RKLB", "PL", "BKSY", "ASTS"],
    "47. 機器人與自動化": ["PATH", "SYM", "CGNX", "ISGN", "KEX"],
    "48. 中型價值精選": ["WSM", "GPC", "TSCO", "ODFL", "MIDD"],
    "49. 小型爆發精選": ["CELH", "WING", "APP", "ELF", "ANF"],
    "50. 超微型探索 (Micro)": ["SOUN", "RXRX", "AI", "BBAI", "HIVE"]
}

ETF_COMPONENTS_MAP = {
    "🔥 [全取] 標普高波動 (SPHB)": ["CCL", "NCLH", "RCL", "AAL", "UAL", "DAL", "LUV", "CZR", "MGM", "WYNN", "PENN", "OXY", "MRO", "APA", "HAL", "SLB", "BKR", "FCX", "ALB", "GNRC", "ENPH", "FSLR", "TSLA", "AMD", "MU", "NVDA", "AMAT", "LRCX", "KLAC", "SNPS", "CDNS", "ANET", "PANW", "CRWD", "PLTR", "SQ", "PYPL", "AFRM", "COIN", "MSTR", "MARA", "RIOT", "KEY", "FITB", "RF", "CF", "MOS", "FMC", "DVN", "FANG", "EOG", "PXD", "HES", "MPC", "VLO", "PSX", "X", "CLF", "NUE", "STLD", "UPST", "CVNA", "SOUN", "AI", "BBAI", "HIVE", "HUT", "DKNG", "HOOD", "LCID", "RIVN", "LI", "NIO", "XPEV", "PATH", "SYM", "PL", "RKLB", "SPCE", "ASTS"],
    "⭐ [全取] 標普低波動 (SPLV)": ["PEP", "KO", "RSG", "WM", "PG", "JNJ", "KMB", "MCD", "SYY", "CLX", "VZ", "SO", "DUK", "AEP", "SRE", "WMT", "COST", "TRV", "AFL", "ALL", "CB", "PGR", "MMC", "AON", "AJG", "EXC", "FE", "ED", "PEG", "WEC", "ES", "LNT", "ATO", "GIS", "K", "MDLZ", "HSY", "CHD", "SJM", "CPB", "TAP", "STZ", "CL", "KR", "DG", "DLTR", "MET", "PRU", "L", "BRO", "FAST", "PAYX", "CTAS", "JKHY", "BHLB", "NTRS", "BEN", "TROW", "USB", "O", "ED", "NI", "EIX", "DTE", "CMS", "CNP", "WEC", "D", "AEE", "EVRG", "LNT", "XEL", "ETR", "FE", "DRE", "PLD", "PSA", "DLR", "CCI"],
    "🔵 [全取] 大型股核心 (OEF)": ["AAPL", "MSFT", "AMZN", "NVDA", "GOOGL", "GOOG", "META", "BRK-B", "LLY", "AVGO", "JPM", "V", "WMT", "MA", "UNH", "XOM", "ORCL", "HD", "PG", "COST", "CVX", "ABBV", "BAC", "CRM", "ADBE", "ABT", "AMD", "CMCSA", "PEP", "KO", "TMO", "CSCO", "MCD", "WFC", "DIS", "INTU", "VZ", "CAT", "AXP", "PFE", "IBM", "MS", "GE", "AMGN", "NFLX", "GS", "QCOM", "TXN", "HON", "BKNG", "RTX", "NEE", "AMAT", "LOW", "DE", "BMY", "UNP", "SCHW", "PM", "BA", "LRCX", "ADI", "SBUX", "MDLZ", "TJX", "PGR", "ISRG", "GILD", "CB", "SPGI", "C", "SNPS", "VRTX", "CI", "CVS", "ZTS", "BSX", "CDNS", "PANW", "DUK", "SO", "ETN", "MMC", "EQIX", "ELV", "ADP", "APD", "CL", "SYK", "AMT", "MU", "ADSK", "MO", "PNC", "CSX", "PLD", "AON", "MELI", "CBRE", "PH"],
    "📈 [前 200] 標普中型股 (MDY)": ["WMS", "RS", "LECO", "TTC", "EMN", "PNR", "AOS", "SNX", "ARW", "HUBB", "WCC", "FIX", "TOL", "PHM", "LEN", "DHI", "NVR", "MTH", "KBH", "TMHC", "MHK", "GPC", "LKQ", "TREX", "MAS", "ALLE", "FNF", "WRB", "CBOE", "MKTX", "SEI", "JEF", "EVR", "LPLA", "RJF", "SF", "FAF", "CNA", "THG", "AFG", "MTG", "RLI", "TEX", "URI", "HAE", "SSD", "EXP", "MLI", "AAON", "ACM", "PWR", "DY", "EME", "MYRG", "TTEK", "VMI", "XYL", "ALGT", "SKYW", "LUV", "CAR", "CHRW", "EXPD", "ODFL", "LANC", "SAIA", "KNX", "JBHT", "FLEX", "SANM", "JBL", "AVT", "TTMI", "DIOD", "CRUS", "MPWR", "ON", "LSCC", "ALTR", "WOLF", "COHR", "IPGP", "JBLU", "ANF", "URBN", "JWN", "DDS", "M", "KSS", "AEO", "PLXS", "BKE", "DKS", "HIBB", "BBY", "FIVE", "OLLIE", "RH", "WSM", "TSCO", "CHH", "MAR", "HLT", "WH", "WYN", "H", "RHP", "PENN", "BYD", "CZR", "MGM", "MTN", "LAD", "PAG", "AN", "SAH", "GPI", "CRMT", "WGO", "THO", "LCII", "PATK", "DORM", "SMP", "BWA", "DLX", "EBF", "RHI", "MAN", "ASGN", "KFRC", "BBSI", "NSP", "OFC", "HIW", "CXP", "HPP", "SLG", "VNO", "PGRE", "LTC", "SBRA", "OME", "UFPI", "BXC", "BLDR", "STLY", "AWI", "FBHS", "AMWD", "DOOR", "PGTI", "JELD", "MDC", "CCS", "GRBK", "LGIH", "HOV", "WHR", "NWL", "TPX", "CROX", "CELH", "YETI", "MEDP", "RGEN", "EXEL", "HALO", "GLPI", "KRC", "NNN", "EPR", "CUBE", "LAMR", "CFR", "PB", "UMBQ", "COLB", "ONB", "FHN", "CBSH", "PINC", "NEU", "INGR", "ARNC", "ATI", "CC", "OLN", "HUN", "KRO", "SLGN", "SON", "GEF", "PKG", "BR", "CHX", "LITE", "PI", "RMBS", "FORM", "ONTO", "MKSI", "AEIS", "NOVT", "BRKS", "VIAV", "ACLS", "VECO"],
    "🦐 [前 500] 羅素小型股 (IWM)": ["SMCI", "CELH", "ELF", "APP", "WING", "DUOL", "FRPT", "MEDP", "CHRD", "MSTR", "CVNA", "RXRX", "SYM", "IOT", "MNDY", "GLBE", "BILL", "TOST", "ASAN", "DOCN", "FSLY", "NET", "CRWD", "DDOG", "SNOW", "AMN", "INSM", "KNSA", "VCYT", "PTCT", "SRPT", "ARWR", "SWTX", "AKRO", "GERN", "ARQT", "KURA", "RYTM", "IMVT", "BCYC", "AAON", "AAWW", "ABCB", "ABG", "ACAD", "ACHC", "ACM", "ACVA", "ADUS", "AEIS", "AFI", "AGO", "AGYS", "AIN", "AIT", "AKR", "ALEX", "ALG", "ALGT", "ALRM", "AMBA", "AMBC", "AMED", "AMKR", "AMN", "AMPH", "AMSF", "AMWD", "ANGO", "ANIK", "ANIP", "AORT", "AOSL", "APA", "APAM", "APG", "APGE", "APLE", "APLS", "APOG", "APPF", "APPN", "APPS", "APTM", "APYX", "AQST", "ARCB", "RCRT", "ARLO", "AROC", "ARVN", "ASB", "ASGN", "ASH", "ASIX", "ASYS", "ATEN", "ATGE", "ATHM", "ATKR", "ATLC", "ATLO", "ATRC", "ATRI", "ATRO", "ATSG", "AVA", "AVAV", "AVID", "AVNS", "AVNT", "AVNW", "AVO", "AVPT", "AWI", "AWK", "AX", "AXL", "AXON", "AXSM", "AYI", "AZTA", "AZZ", "B", "BANC", "BANF", "BANR", "BASE", "BBIO", "BCO", "BCPC", "BDC", "BHLB", "BIG", "BIIB", "BJ", "BKD", "BKH", "BKI", "BKU", "BL", "BLD", "BLDR", "BLKB", "BLMN", "BLNK", "FLY", "BMC", "BMRE", "BNED", "BOOM", "BOOT", "BPTH", "BRC", "BRKR", "BRO", "BRP", "BRY", "BSET", "BSGM", "BSQR", "BSRR", "BTI", "BTRS", "BTT", "BUR", "BVS", "BWA", "BWXT", "BXMT", "BXP", "BY", "BYD", "BZFD", "CFFN", "CHCO", "CHCT", "CHDN", "CHEF", "CHGG", "CHH", "CHMG", "CHMI", "CHRA", "CHRS", "CHRW", "CHS", "CIEN", "CINF", "CIO", "CIR", "CIT", "CIVB", "CLAR", "CLB", "CLDT", "CLF", "CLFD", "CLH", "CLNE", "CLPR", "CLPS", "CLRO", "CLS", "CLSK", "CLVT", "CLW", "CLX", "CMBM", "CMC", "CMCO", "CMCT", "CME", "CMG", "CMI", "CMP", "CMPO", "CMPR", "CMRE", "CMS", "CNCE", "CNDT", "CNEX", "CNFR", "CNK", "CNM", "CNMD", "CNNE", "CNO", "CNP", "CNTY", "CNX", "CNXN", "CODI", "COGT", "COHU", "COHR", "COKE", "COLB", "COLM", "COMM", "COMP", "CONN", "COOP", "COPX", "CORT", "COTY", "COUR", "CPAC", "CPAH", "CPB", "CPE", "CPF", "CPHC", "CPIX", "CPK", "CPLP", "CPRI", "CPRX", "CPS", "CPSI", "CPSS", "CPT", "CRAI", "CRBG", "CRBP", "CRC", "CRCT", "CRDL", "CREE", "CREG", "CREX", "CRGY", "CRH", "CRI", "CRIS", "CRK", "CRKN", "CRMD", "CRMT", "CRNC", "CRNT", "CRNX", "CRON", "CROX", "CRTO", "CRUS", "CRVL", "CRVS", "CRWD", "CRY", "CRZO", "CSL", "CSM", "CSOD", "CSPI", "CSSE", "CSS", "CST", "CSTA", "CSTE", "CSTL", "CSTR", "CSV", "CSWC", "CSWI", "CSX", "CTAS", "CTBI", "CTCM", "CTLP", "CTLT", "CTMX", "CTOS", "CTRA", "CTRE", "CTRN", "CTS", "CTSH", "CTSO", "CTT", "CTVA", "CUB", "CUBE", "CUBI", "CUE", "CUK", "CULL", "CUNB", "CUR", "CURI", "CURO", "CUT", "CVAC", "CVBF", "CVCO", "CVCY", "CVET", "CVGI", "CVGW", "CVI", "CVLG", "CVLT", "CVLY", "CVM", "CVNA", "CVR", "CVRX", "CVSB", "CVV", "CW", "CWAN", "CWBC", "CWCO", "CWEN", "CWH", "CWK", "CWST", "CWT", "CXDC", "CXM", "CXO", "CXP", "CXW", "CYAD", "CYAN", "CYBE", "CYBN", "CYCC", "CYCN", "CYD", "CYH", "CYN", "CYRN", "CYRX", "CYTK", "CYTO", "CYTR", "CYXT", "CZFS", "CZNC", "CZR", "CZWI", "DADA", "DAIO", "DBI", "DCO", "DCPH", "DCT", "DDL", "DECK", "DENN", "DFIN", "DFRG", "DGII", "DHC", "DHIL", "DIN", "DJCO", "DLB", "DLHC", "DMRC", "DNLI", "DOC", "DOX", "DPLO", "DRH", "DRI", "DRQ", "DSPG", "DSWG", "DTC", "DTE", "DVAX", "DVD", "DWSN", "DX", "DXPE", "DZZ", "EAF", "EARN", "EAT", "EB", "EBC", "EBS", "EBSB", "EBTC", "ECPG", "EDR", "EDU", "EE", "EEFT", "EEX", "EFC", "EGBN", "EGF", "EGHT", "EGLE", "EGOV", "EGP", "EGRX", "EGY", "EHTH", "EIG", "EIGR", "ELAN", "ELLI", "ELMD", "ELY", "EMAN", "EMCF", "EMCI", "EML", "EMP", "ENDP", "ENOB", "ENR", "ENS", "ENSG", "ENTA", "ENV", "ENVA", "ENZ", "EOLS", "EPAC", "EPAM", "EPAY", "EPC", "EPRT", "EPZM", "EQBK", "EQC", "ERI", "ERII", "ESCA", "ESE", "ESNT"]
}

FULL_US_STOCK_MAP = {**ETF_COMPONENTS_MAP, **US_STOCK_MAP}

# =========================================================
# ⚙️ 高階矩陣運算引擎 (原子化單算版，無敵防爆！)
# =========================================================
@st.cache_data(ttl=43200, show_spinner=False)
def fetch_full_dashboard_data():
    special_etfs = {
        "🔵 大型股核心 (OEF)": ETF_COMPONENTS_MAP["🔵 [全取] 大型股核心 (OEF)"],
        "📈 中型股主力 (MDY)": ETF_COMPONENTS_MAP["📈 [前 200] 標普中型股 (MDY)"],
        "🦐 小型股爆發 (IWM)": ETF_COMPONENTS_MAP["🦐 [前 500] 羅素小型股 (IWM)"],
        "🔥 高波動長矛 (SPHB)": ETF_COMPONENTS_MAP["🔥 [全取] 標普高波動 (SPHB)"],
        "⭐ 低波動盾牌 (SPLV)": ETF_COMPONENTS_MAP["⭐ [全取] 標普低波動 (SPLV)"]
    }
    
    breadth_results = {}
    current_day_data = {}
    price_results = {}

    etf_tickers = ["OEF", "MDY", "IWM", "SPHB", "SPLV"]
    try:
        raw_etf = yf.download(etf_tickers, period="1y", auto_adjust=True, progress=False, group_by="ticker")
    except Exception:
        raw_etf = pd.DataFrame()

    for name, tickers in special_etfs.items():
        try:
            raw_comp = yf.download(tickers, period="1y", auto_adjust=True, progress=False)
            
            # 安全防護：如果下載回來是 None 或者空的，直接跳到 except 處理
            if raw_comp is None or raw_comp.empty:
                raise ValueError(f"{name} 下載的資料為空")

            if "Close" in raw_comp: close_prices = raw_comp["Close"]
            else: close_prices = raw_comp
            
            if not close_prices.empty and isinstance(close_prices.index, pd.DatetimeIndex):
                str_idx = pd.Series(close_prices.index.astype(str))
                valid_mask = str_idx.str.startswith('20').values
                close_prices = close_prices.iloc[valid_mask]
                close_prices.index = pd.to_datetime(close_prices.index).tz_localize(None).normalize()
            
            total_b5 = pd.Series(0, index=close_prices.index)
            total_b20 = pd.Series(0, index=close_prices.index)
            total_b50 = pd.Series(0, index=close_prices.index)
            total_b100 = pd.Series(0, index=close_prices.index)
            total_b200 = pd.Series(0, index=close_prices.index)
            valid_counts = pd.Series(0, index=close_prices.index)

            for ticker in close_prices.columns:
                series = close_prices[ticker].dropna()
                # 🛡️ 門檻微調：降低為 150 天，確保能容忍 Yahoo 的漏單，又不會放入剛上市幾天的妖股！
                if len(series) >= 150:
                    ma5 = series.rolling(5).mean()
                    ma20 = series.rolling(20).mean()
                    ma50 = series.rolling(50).mean()
                    ma100 = series.rolling(100).mean()
                    ma200 = series.rolling(200).mean()

                    total_b5 = total_b5.add((series > ma5).astype(int), fill_value=0)
                    total_b20 = total_b20.add((series > ma20).astype(int), fill_value=0)
                    total_b50 = total_b50.add((series > ma50).astype(int), fill_value=0)
                    total_b100 = total_b100.add((series > ma100).astype(int), fill_value=0)
                    total_b200 = total_b200.add((series > ma200).astype(int), fill_value=0)
                    valid_counts = valid_counts.add(pd.Series(1, index=series.index), fill_value=0)
            
            df_b = pd.DataFrame({
                "Breadth_MA5": (total_b5 / valid_counts * 100).fillna(0),
                "Breadth_MA20": (total_b20 / valid_counts * 100).fillna(0),
                "Breadth_MA50": (total_b50 / valid_counts * 100).fillna(0),
                "Breadth_MA100": (total_b100 / valid_counts * 100).fillna(0),
                "Breadth_MA200": (total_b200 / valid_counts * 100).fillna(0)
            })

            try: b5_val = float(df_b["Breadth_MA5"].iloc[-1])
            except: b5_val = 0.0
            try: b20_val = float(df_b["Breadth_MA20"].iloc[-1])
            except: b20_val = 0.0
            try: b50_val = float(df_b["Breadth_MA50"].iloc[-1])
            except: b50_val = 0.0
            try: b200_val = float(df_b["Breadth_MA200"].iloc[-1])
            except: b200_val = 0.0

            current_day_data[name] = {
                "MA5_Pct": b5_val, "MA20_Pct": b20_val,
                "MA50_Pct": b50_val, "MA200_Pct": b200_val
            }
            breadth_results[name] = df_b.tail(60)

        except Exception as e:
            # 防爆墊：如果報錯，這一個 ETF 就給空殼，不影響其他圖表
            breadth_results[name] = pd.DataFrame()
            current_day_data[name] = {"MA5_Pct":0.0, "MA20_Pct":0.0, "MA50_Pct":0.0, "MA200_Pct":0.0}

        # 抓取單一 ETF
        ticker_symbol = name.split("(")[-1].replace(")", "").strip()
        df_p = pd.DataFrame()
        if not raw_etf.empty and ticker_symbol in raw_etf.columns.get_level_values(0):
            df_p = raw_etf[ticker_symbol].copy().dropna(subset=["Close"])
            if not df_p.empty and isinstance(df_p.index, pd.DatetimeIndex):
                str_idx = pd.Series(df_p.index.astype(str))
                valid_mask = str_idx.str.startswith('20').values
                df_p = df_p.iloc[valid_mask]
                df_p.index = pd.to_datetime(df_p.index).tz_localize(None).normalize()
            
        if not breadth_results.get(name, pd.DataFrame()).empty and not df_p.empty:
            df_b = breadth_results[name]
            union_dates = df_p.index.intersection(df_b.index).sort_values()
            
            if not union_dates.empty:
                df_p_aligned = df_p.reindex(union_dates).ffill().fillna(0)
                df_b_aligned = df_b.reindex(union_dates).ffill().fillna(0)
                
                if len(df_p_aligned) == len(df_b_aligned) and len(df_p_aligned) > 0:
                    price_results[name] = df_p_aligned.tail(60)
                    breadth_results[name] = df_b_aligned.tail(60)
                else:
                    price_results[name] = pd.DataFrame()
                    breadth_results[name] = pd.DataFrame()
            else:
                price_results[name] = pd.DataFrame()
                breadth_results[name] = pd.DataFrame()
        else:
            price_results[name] = pd.DataFrame()
            breadth_results[name] = pd.DataFrame()

    return breadth_results, current_day_data, price_results

@st.cache_data(ttl=43200, show_spinner=False)
def fetch_traditional_breadth():
    all_sectors = list(US_STOCK_MAP.keys())
    results_dict_list = []
    total_ma5, total_ma20, total_ma50, total_ma200, total_valid = 0, 0, 0, 0, 0

    for sector_name in all_sectors:
        constituents = US_STOCK_MAP.get(sector_name, [])[:TOP_N_LEADERS]
        sec_ma5, sec_ma20, sec_ma50, sec_ma200, sec_valid = 0, 0, 0, 0, 0
        try:
            if constituents:
                raw = yf.download(constituents, period="250d", auto_adjust=True, progress=False, threads=False, group_by="ticker")
                for sym in constituents:
                    close_series = _extract_close_series_single(raw, sym)
                    # 🛡️ 門檻微調：降低為 150 天，確保能容忍 Yahoo 的漏單！
                    if not close_series.empty and len(close_series) >= 150:
                        curr_p = float(close_series.iloc[-1])
                        if curr_p > float(close_series.rolling(5).mean().iloc[-1]): sec_ma5 += 1
                        if curr_p > float(close_series.rolling(20).mean().iloc[-1]): sec_ma20 += 1
                        if len(close_series) >= 50 and curr_p > float(close_series.rolling(50).mean().iloc[-1]): sec_ma50 += 1
                        if len(close_series) >= 200 and curr_p > float(close_series.rolling(200).mean().iloc[-1]): sec_ma200 += 1
                        sec_valid += 1
        except: pass

        if sec_valid > 0:
            results_dict_list.append({
                "板塊": sector_name, "MA5_Pct": (sec_ma5 / sec_valid * 100.0), "MA20_Pct": (sec_ma20 / sec_valid * 100.0),
                "MA50_Pct": (sec_ma50 / sec_valid * 100.0), "MA200_Pct": (sec_ma200 / sec_valid * 100.0), "sort_order": 999
            })
            total_ma5 += sec_ma5; total_ma20 += sec_ma20; total_ma50 += sec_ma50; total_ma200 += sec_ma200; total_valid += sec_valid
        time.sleep(0.01)

    top_banners = {
        "MA5": (total_ma5 / total_valid * 100.0) if total_valid > 0 else 0.0,
        "MA20": (total_ma20 / total_valid * 100.0) if total_valid > 0 else 0.0,
        "MA50": (total_ma50 / total_valid * 100.0) if total_valid > 0 else 0.0,
        "MA200": (total_ma200 / total_valid * 100.0) if total_valid > 0 else 0.0
    }
    return pd.DataFrame(results_dict_list), top_banners

# =========================================================
# 🔴 主頁面渲染中心
# =========================================================
def render_page_2bb():
    st.markdown("<h1 style='color:#00ff88; font-size:46px; font-family:Arial Black;'>📡 B-2 艙：真實歷史市寬總攻大陣 (60天全景圖版)</h1>", unsafe_allow_html=True)
    st.markdown("<hr style='border:3px solid #00ff88; margin:bottom:20px;'>", unsafe_allow_html=True)

    st.markdown("### ⏱️ 選擇短期市寬觀測雷達範圍")
    short_term_mode = st.radio(
        "切換短線範圍（圖表將連動切換 5天 或 20天 短期市寬線）：",
        ["🟢 顯示 5天短期線 + (50/100/200)", "🟢 顯示 20天短期線 + (50/100/200)"],
        horizontal=True
    )
    use_ma5 = "5天" in short_term_mode

    if st.button("🔄 火力全開：啟動矩陣運算清算 (約需十幾秒)"):
        st.cache_data.clear()
        st.success("💥 快取已強制融冰！正在重新清算大市...")

    # 🛡️ 安全墊：預先宣告 df_rs，防止後續呼叫時出錯
    df_rs = pd.DataFrame()
    top_banners = {}

    with st.spinner("📡 正在執行高階矩陣歷史運算 (範圍: 60日)..."):
        try:
            breadth_results, current_day_data, price_results = fetch_full_dashboard_data()
            df_rs, top_banners = fetch_traditional_breadth()
        except Exception as e:
            st.error(f"數據讀取異常，請點擊上方「火力全開」。錯誤訊息: {e}")
            return
            
    short_col_name = "MA5_Pct" if use_ma5 else "MA20_Pct"
    short_col_hist = "Breadth_MA5" if use_ma5 else "Breadth_MA20"
    short_banner_val = top_banners.get("MA5", 0.0) if use_ma5 else top_banners.get("MA20", 0.0)
    short_legend_label = "🟢 MA5 短期爆發" if use_ma5 else "🟢 MA20 短期健康"

    # =========================================================
    # 🎯 置頂 6 行戰略儀表板
    # =========================================================
    st.markdown("<h3 style='color:#ffaa00; margin-top:10px; margin-bottom:15px;'>📊 戰略靈魂：美股 6 大維度市寬全景雷達</h3>", unsafe_allow_html=True)
    
    st.markdown(f'''
    <div style="background-color:rgba(0,0,0,0.05); padding:12px 15px; border-radius:8px; margin-bottom:12px; border-left:8px solid #000000; display:flex; justify-content:space-between; align-items:center;">
        <div style="color:#ffffff; font-size:19px; font-weight:900; width:30%;">🎯 傳統板塊均值 (扣除特權ETF)</div>
        <div style="color:#008844; font-size:18px; font-weight:bold; width:23%; text-align:center;">{short_legend_label}: {short_banner_val:.1f}%</div>
        <div style="color:#cc9900; font-size:18px; font-weight:bold; width:23%; text-align:center;">🟡 MA50: {top_banners.get("MA50", 0.0):.1f}%</div>
        <div style="color:#cc1111; font-size:18px; font-weight:bold; width:23%; text-align:center;">🔴 MA200: {top_banners.get("MA200", 0.0):.1f}%</div>
    </div>
    ''', unsafe_allow_html=True)

    rows_config = [
        ("🔵 大型股 (OEF)", "#ffffff", "🔵 大型股核心 (OEF)"),
        ("📈 中型股 (MDY)", "#ffffff", "📈 中型股主力 (MDY)"),
        ("🦐 小型股 (IWM)", "#ffffff", "🦐 小型股爆發 (IWM)"),
        ("🔥 高波動 (SPHB)", "#ffffff", "🔥 高波動長矛 (SPHB)"),
        ("⭐ 低波動 (SPLV)", "#ffffff", "⭐ 低波動盾牌 (SPLV)")
    ]

    for label, color, key in rows_config:
        try:
            v_short = float(current_day_data.get(key, {}).get(short_col_name, 0.0))
            v_50 = float(current_day_data.get(key, {}).get("MA50_Pct", 0.0))
            v_200 = float(current_day_data.get(key, {}).get("MA200_Pct", 0.0))
        except:
            v_short, v_50, v_200 = 0.0, 0.0, 0.0
            
        # Left border colors to distinguish rows
        border_colors = {"🔵 大型股 (OEF)": "#00f2ff", "📈 中型股 (MDY)": "#a200ff", "🦐 小型股 (IWM)": "#ff00ff", "🔥 高波動 (SPHB)": "#ff3333", "⭐ 低波動 (SPLV)": "#00ff88"}
        b_color = border_colors.get(label, "#ffffff")

        st.markdown(f'''
        <div style="background-color:#1e212b; padding:10px 15px; border-radius:8px; margin-bottom:8px; border-left:6px solid {b_color}; display:flex; justify-content:space-between; align-items:center;">
            <div style="color:{color}; font-size:18px; font-weight:bold; width:30%;">{label}</div>
            <div style="color:#00ff88; font-size:18px; font-weight:bold; width:23%; text-align:center;">{short_legend_label}: {v_short:.1f}%</div>
            <div style="color:#ffbb00; font-size:18px; font-weight:bold; width:23%; text-align:center;">🟡 MA50: {v_50:.1f}%</div>
            <div style="color:#ff3333; font-size:18px; font-weight:bold; width:23%; text-align:center;">🔴 MA200: {v_200:.1f}%</div>
        </div>
        ''', unsafe_allow_html=True)

    st.markdown("<hr style='border:2px solid #444; margin:30px 0;'>", unsafe_allow_html=True)

    # =========================================================
    # 📈 5 大核心圖表：K線陰陽燭與真實市寬線「雙 Y 軸完美疊加版」
    # =========================================================
    st.markdown("<h3 style='color:#00ff88;'>📈 5 大核心特權 ETF：真實技術K線與內部市寬融合大圖</h3>", unsafe_allow_html=True)
    st.markdown("<p style='color:#aaa;'>（展示近 60 日走勢，主圖：陰陽燭 K 線與真實市寬重疊疊加，取消普通價格均線；副圖：成交量）</p>", unsafe_allow_html=True)
    
    def render_ultimate_chart(df_p, df_b, title_text):
        if df_p.empty or df_b.empty:
            return None

        # 這裡不強求日期完全一樣，只要有一邊有資料就畫！絕對不報錯！
        fig = make_subplots(rows=2, cols=1, shared_xaxes=True, 
                            vertical_spacing=0.04, 
                            row_heights=[0.7, 0.3],
                            specs=[[{"secondary_y": True}], [{"secondary_y": False}]])

        # --- Row 1 (左軸 secondary_y=False): ETF 真實 K 線陰陽燭 ---
        if not df_p.empty and 'Close' in df_p.columns:
            fig.add_trace(go.Candlestick(x=df_p.index, open=df_p['Open'], high=df_p['High'], low=df_p['Low'], close=df_p['Close'], name='價格陰陽燭'), row=1, col=1, secondary_y=False)
        
        # --- Row 1 (右軸 secondary_y=True): 直接把 4 條真實市寬歷史線疊在圖表上 ---
        if not df_b.empty:
            if short_col_hist in df_b.columns:
                fig.add_trace(go.Scatter(x=df_b.index, y=df_b[short_col_hist], mode='lines', line=dict(color='#00ff88', width=3), name=f"市寬 {short_legend_label}"), row=1, col=1, secondary_y=True)
            if "Breadth_MA50" in df_b.columns:
                fig.add_trace(go.Scatter(x=df_b.index, y=df_b["Breadth_MA50"], mode='lines', line=dict(color='#ffbb00', width=2), name="市寬 🟡 MA50 中期"), row=1, col=1, secondary_y=True)
            if "Breadth_MA100" in df_b.columns:
                fig.add_trace(go.Scatter(x=df_b.index, y=df_b["Breadth_MA100"], mode='lines', line=dict(color='#00f2ff', width=2, dash='dot'), name="市寬 🔵 MA100 長期"), row=1, col=1, secondary_y=True)
            if "Breadth_MA200" in df_b.columns:
                fig.add_trace(go.Scatter(x=df_b.index, y=df_b["Breadth_MA200"], mode='lines', line=dict(color='#ff3333', width=3), name="市寬 🔴 MA200 牛熊"), row=1, col=1, secondary_y=True)

        # --- Row 2: 下層成交量 (單色防呆) ---
        if not df_p.empty and 'Volume' in df_p.columns:
            fig.add_trace(go.Bar(x=df_p.index, y=df_p['Volume'], marker_color='#4a5568', opacity=0.8, name='成交量'), row=2, col=1)

        fig.update_layout(
            title=dict(text=title_text, font=dict(color='white', size=24, family='Arial Black')),
            template="plotly_dark", height=750, margin=dict(l=50, r=60, t=60, b=20),
            xaxis_rangeslider_visible=False, showlegend=True,
            legend=dict(orientation="h", yanchor="bottom", y=1.02, xanchor="right", x=1, font=dict(color="white", size=14)),
            paper_bgcolor="#1e212b", plot_bgcolor="#1e212b"
        )
        
        fig.update_yaxes(title_text="ETF 價格 (USD)", row=1, col=1, secondary_y=False, gridcolor="#333", tickfont=dict(size=14))
        fig.update_yaxes(title_text="真實市寬擴散 %", range=[-5, 105], row=1, col=1, secondary_y=True, gridcolor="#444", side="right", showgrid=False, tickfont=dict(color="#00ff88", size=14))
        fig.update_yaxes(title_text="Volume", row=2, col=1, gridcolor="#333", showticklabels=False)
        fig.update_xaxes(gridcolor="#333", tickfont=dict(size=14))

        return fig

    chart_order = [
        ("🔵 大型股核心 (OEF)", "🔵 大型股核心 (OEF) 戰略背離全景圖"),
        ("📈 中型股主力 (MDY)", "📈 中型股主力 (MDY) 戰略背離全景圖"),
        ("🦐 小型股爆發 (IWM)", "🦐 小型股爆發 (IWM) 戰略背離全景圖"),
        ("🔥 高波動長矛 (SPHB)", "🔥 高波動長矛 (SPHB) 戰略背離全景圖"),
        ("⭐ 低波動盾牌 (SPLV)", "⭐ 低波動盾牌 (SPLV) 戰略背離全景圖")
    ]
    
    for key, title in chart_order:
        df_p = price_results.get(key, pd.DataFrame())
        df_b = breadth_results.get(key, pd.DataFrame())
        
        if not df_p.empty and not df_b.empty and len(df_p) == len(df_b) and len(df_p) > 0:
            fig = render_ultimate_chart(df_p, df_b, title)
            if fig:
                # Add config to always show the Modebar
                st.plotly_chart(fig, use_container_width=True, config={'displayModeBar': True})
                st.markdown("<br>", unsafe_allow_html=True)
        else:
            st.warning(f"⚠️ {title} 數據獲取中或未產生交易數據，請稍後重試。")

    st.markdown("<hr style='border:2px solid #444; margin:30px 0;'>", unsafe_allow_html=True)

    # =========================================================
    # 📊 底層傳統 50 板塊 3D 長條圖繪製
    # =========================================================
    st.markdown("<h3 style='color:#00ff88;'>📊 全量板塊大陣：今日真實市寬總動員切片</h3>", unsafe_allow_html=True)
    
    def get_val_for_bar(d, k1, k2):
        try: return float(d.get(k1, {}).get(k2, 0.0))
        except: return 0.0
    
    agg_rows = [
        {"板塊": "🎯 傳統板塊均值 (扣除特權ETF)", "MA5_Pct": top_banners.get("MA5",0), "MA20_Pct": top_banners.get("MA20",0), "MA50_Pct": top_banners.get("MA50",0), "MA200_Pct": top_banners.get("MA200",0), "sort_order": 1},
        {"板塊": "🔵 大型股核心 (OEF)", "MA5_Pct": get_val_for_bar(current_day_data, "🔵 大型股核心 (OEF)", "MA5_Pct"), "MA20_Pct": get_val_for_bar(current_day_data, "🔵 大型股核心 (OEF)", "MA20_Pct"), "MA50_Pct": get_val_for_bar(current_day_data, "🔵 大型股核心 (OEF)", "MA50_Pct"), "MA200_Pct": get_val_for_bar(current_day_data, "🔵 大型股核心 (OEF)", "MA200_Pct"), "sort_order": 2},
        {"板塊": "📈 中型股主力 (MDY)", "MA5_Pct": get_val_for_bar(current_day_data, "📈 中型股主力 (MDY)", "MA5_Pct"), "MA20_Pct": get_val_for_bar(current_day_data, "📈 中型股主力 (MDY)", "MA20_Pct"), "MA50_Pct": get_val_for_bar(current_day_data, "📈 中型股主力 (MDY)", "MA50_Pct"), "MA200_Pct": get_val_for_bar(current_day_data, "📈 中型股主力 (MDY)", "MA200_Pct"), "sort_order": 3},
        {"板塊": "🦐 小型股爆發 (IWM)", "MA5_Pct": get_val_for_bar(current_day_data, "🦐 小型股爆發 (IWM)", "MA5_Pct"), "MA20_Pct": get_val_for_bar(current_day_data, "🦐 小型股爆發 (IWM)", "MA20_Pct"), "MA50_Pct": get_val_for_bar(current_day_data, "🦐 小型股爆發 (IWM)", "MA50_Pct"), "MA200_Pct": get_val_for_bar(current_day_data, "🦐 小型股爆發 (IWM)", "MA200_Pct"), "sort_order": 4},
        {"板塊": "🔥 高波動長矛 (SPHB)", "MA5_Pct": get_val_for_bar(current_day_data, "🔥 高波動長矛 (SPHB)", "MA5_Pct"), "MA20_Pct": get_val_for_bar(current_day_data, "🔥 高波動長矛 (SPHB)", "MA20_Pct"), "MA50_Pct": get_val_for_bar(current_day_data, "🔥 高波動長矛 (SPHB)", "MA50_Pct"), "MA200_Pct": get_val_for_bar(current_day_data, "🔥 高波動長矛 (SPHB)", "MA200_Pct"), "sort_order": 5},
        {"板塊": "⭐ 低波動盾牌 (SPLV)", "MA5_Pct": get_val_for_bar(current_day_data, "⭐ 低波動盾牌 (SPLV)", "MA5_Pct"), "MA20_Pct": get_val_for_bar(current_day_data, "⭐ 低波動盾牌 (SPLV)", "MA20_Pct"), "MA50_Pct": get_val_for_bar(current_day_data, "⭐ 低波動盾牌 (SPLV)", "MA50_Pct"), "MA200_Pct": get_val_for_bar(current_day_data, "⭐ 低波動盾牌 (SPLV)", "MA200_Pct"), "sort_order": 6},
    ]
    df_agg = pd.DataFrame(agg_rows)
    
    if not df_rs.empty:
        df_rs["sort_order"] = 999
        df_final_plot = pd.concat([df_agg, df_rs], ignore_index=True)
    else:
        df_final_plot = df_agg
    
    for col in ["MA200_Pct", "MA50_Pct", short_col_name]:
        if col not in df_final_plot.columns: df_final_plot[col] = 0.0

    df_final_plot = df_final_plot.sort_values(by=["sort_order", "MA200_Pct", "MA50_Pct", short_col_name], ascending=[False, True, True, True])

    chart_height = 2800
    y_data = df_final_plot["板塊"].tolist()

    fig2 = go.Figure()
    fig2.add_trace(go.Bar(
        x=df_final_plot["MA200_Pct"].tolist(), y=y_data, name="🔴 MA200 長期牛熊", orientation='h', marker_color='#ff3333',
        text=[f"{v:.1f}%" for v in df_final_plot["MA200_Pct"].tolist()], textposition='outside', textfont=dict(color='#ffffff', size=18, family='Arial Black')
    ))
    fig2.add_trace(go.Bar(
        x=df_final_plot["MA50_Pct"].tolist(), y=y_data, name="🟡 MA50 中期穩定", orientation='h', marker_color='#ffbb00',
        text=[f"{v:.1f}%" for v in df_final_plot["MA50_Pct"].tolist()], textposition='outside', textfont=dict(color='#ffffff', size=18, family='Arial Black')
    ))
    fig2.add_trace(go.Bar(
        x=df_final_plot[short_col_name].tolist(), y=y_data, name=short_legend_label, orientation='h', marker_color='#00ff88',
        text=[f"{v:.1f}%" for v in df_final_plot[short_col_name].tolist()], textposition='outside', textfont=dict(color='#ffffff', size=18, family='Arial Black')
    ))

    fig2.update_layout(
        barmode='group', template="plotly_dark", height=chart_height, bargap=0.06, barcornerradius=8,
        xaxis=dict(title="各均線之上股票佔比 (%)", tickfont=dict(size=18, color="white"), gridcolor="#222222", range=[0, 130]),
        yaxis=dict(tickfont=dict(size=20, color="white", family='Arial Black'), gridcolor="#222222", automargin=True),
        legend=dict(orientation="h", yanchor="bottom", y=1.01, xanchor="right", x=1, font=dict(size=18, color="white")),
        margin=dict(l=320, r=100, t=100, b=40), paper_bgcolor="#0e1117", plot_bgcolor="#0e1117"
    )

    # Add config to always show the Modebar
    st.plotly_chart(fig2, use_container_width=True, config={'displayModeBar': True})

if __name__ == "__main__":
    render_page_2bb()