import pandas as pd
import numpy as np
import yfinance as yf
import streamlit as st

# =========================================================================
# 🏛️ 34 大板塊專屬量化字典 (30 個 ETF 板塊 + 4 個特殊純股票板塊)
# =========================================================================

GANN05_SECTOR_CONFIG = {
    # --- 11 大傳統宏觀板塊 (使用全部代表 ETF 計算資金，錨定第 1 隻旗艦 ETF) ---
    '科技 (XLK)': {
        'type': 'macro_etf', 'anchor': 'XLK',
        'flow_tickers': ['XLK', 'VGT', 'IYW', 'QQQ'],
        'display_sub': 'XLK / VGT / IYW / QQQ'
    },
    '金融 (XLF)': {
        'type': 'macro_etf', 'anchor': 'XLF',
        'flow_tickers': ['XLF', 'VFH', 'KBE', 'KRE'],
        'display_sub': 'XLF / VFH / KBE / KRE'
    },
    '醫療保健 (XLV)': {
        'type': 'macro_etf', 'anchor': 'XLV',
        'flow_tickers': ['XLV', 'VHT', 'IBB', 'XBI'],
        'display_sub': 'XLV / VHT / IBB / XBI'
    },
    '能源 (XLE)': {
        'type': 'macro_etf', 'anchor': 'XLE',
        'flow_tickers': ['XLE', 'VDE', 'OIH', 'XOP'],
        'display_sub': 'XLE / VDE / OIH / XOP'
    },
    '非必需消費 (XLY)': {
        'type': 'macro_etf', 'anchor': 'XLY',
        'flow_tickers': ['XLY', 'VCR', 'XRT'],
        'display_sub': 'XLY / VCR / XRT'
    },
    '必需消費 (XLP)': {
        'type': 'macro_etf', 'anchor': 'XLP',
        'flow_tickers': ['XLP', 'VDC', 'KXI'],
        'display_sub': 'XLP / VDC / KXI'
    },
    '工業 (XLI)': {
        'type': 'macro_etf', 'anchor': 'XLI',
        'flow_tickers': ['XLI', 'VIS', 'ITA'],
        'display_sub': 'XLI / VIS / ITA'
    },
    '公用事業 (XLU)': {
        'type': 'macro_etf', 'anchor': 'XLU',
        'flow_tickers': ['XLU', 'VPU', 'GRID'],
        'display_sub': 'XLU / VPU / GRID'
    },
    '原材料 (XLB)': {
        'type': 'macro_etf', 'anchor': 'XLB',
        'flow_tickers': ['XLB', 'VAW', 'LIT'],
        'display_sub': 'XLB / VAW / LIT'
    },
    '房地產 (XLRE)': {
        'type': 'macro_etf', 'anchor': 'XLRE',
        'flow_tickers': ['XLRE', 'VNQ', 'IYR'],
        'display_sub': 'XLRE / VNQ / IYR'
    },
    '通訊服務 (XLC)': {
        'type': 'macro_etf', 'anchor': 'XLC',
        'flow_tickers': ['XLC', 'VOX', 'FCOM'],
        'display_sub': 'XLC / VOX / FCOM'
    },

    # --- 19 個前沿科技/資源 ETF 板塊 ---
    '🧠 GPU / AI 核心算力 (SMH)': {
        'type': 'frontier_etf', 'anchor': 'SMH',
        'flow_tickers': ['SMH', 'SOXX', 'USD'],
        'display_sub': 'SMH / SOXX / USD'
    },
    '💻 CPU / 處理器 (SOXX)': {
        'type': 'frontier_etf', 'anchor': 'SOXX',
        'flow_tickers': ['SOXX', 'XSD'],
        'display_sub': 'SOXX / XSD'
    },
    '💾 DRAM / 存儲與記憶體': {
        'type': 'frontier_etf', 'anchor': 'MU',
        'flow_tickers': ['MU', 'WDC', 'STX'],
        'display_sub': 'MU / WDC / STX'
    },
    '❄️ 發電、液冷與散熱板': {
        'type': 'frontier_etf', 'anchor': 'GRID',
        'flow_tickers': ['GRID', 'XLU'],
        'display_sub': 'GRID / XLU'
    },
    '⚡ 變壓器與電網升級': {
        'type': 'frontier_etf', 'anchor': 'GRID',
        'flow_tickers': ['GRID', 'PAVE'],
        'display_sub': 'GRID / PAVE'
    },
    '🛡️ 網絡安全': {
        'type': 'frontier_etf', 'anchor': 'CIBR',
        'flow_tickers': ['CIBR', 'HACK', 'BUG'],
        'display_sub': 'CIBR / HACK / BUG'
    },
    '🧠 LLM 大模型巨頭': {
        'type': 'frontier_etf', 'anchor': 'AIQ',
        'flow_tickers': ['AIQ', 'BOTZ', 'THNQ'],
        'display_sub': 'AIQ / BOTZ / THNQ'
    },
    '🚗 自動駕駛與 Robotaxi': {
        'type': 'frontier_etf', 'anchor': 'IDRV',
        'flow_tickers': ['IDRV', 'DRIV', 'HAIL'],
        'display_sub': 'IDRV / DRIV / HAIL'
    },
    '🦾 機械人與自動化': {
        'type': 'frontier_etf', 'anchor': 'BOTZ',
        'flow_tickers': ['BOTZ', 'ROBO', 'IRBO'],
        'display_sub': 'BOTZ / ROBO / IRBO'
    },
    '🌌 量子電腦': {
        'type': 'frontier_etf', 'anchor': 'QTUM',
        'flow_tickers': ['QTUM', 'DEFI'],
        'display_sub': 'QTUM / DEFI'
    },
    '🚀 太空與衛星通訊': {
        'type': 'frontier_etf', 'anchor': 'UFO',
        'flow_tickers': ['UFO', 'ROKT', 'ARKX'],
        'display_sub': 'UFO / ROKT / ARKX'
    },
    '🪙 加密貨幣與狂熱': {
        'type': 'frontier_etf', 'anchor': 'IBIT',
        'flow_tickers': ['IBIT', 'BITO', 'WGMI'],
        'display_sub': 'IBIT / BITO / WGMI'
    },
    '⚛️ 核能、SMR 與鈾礦': {
        'type': 'frontier_etf', 'anchor': 'URA',
        'flow_tickers': ['URA', 'URNM', 'NLR'],
        'display_sub': 'URA / URNM / NLR'
    },
    '🥇 金礦股': {
        'type': 'frontier_etf', 'anchor': 'GDX',
        'flow_tickers': ['GDX', 'GDXJ', 'RING'],
        'display_sub': 'GDX / GDXJ / RING'
    },
    '🥈 銀礦股': {
        'type': 'frontier_etf', 'anchor': 'SIL',
        'flow_tickers': ['SIL', 'SILJ'],
        'display_sub': 'SIL / SILJ'
    },
    '🥉 銅礦股': {
        'type': 'frontier_etf', 'anchor': 'COPX',
        'flow_tickers': ['COPX', 'CPER'],
        'display_sub': 'COPX / CPER'
    },
    '🧬 前沿生物科技': {
        'type': 'frontier_etf', 'anchor': 'XBI',
        'flow_tickers': ['XBI', 'IBB', 'ARKG'],
        'display_sub': 'XBI / IBB / ARKG'
    },
    '⚔️ 國防與軍工': {
        'type': 'frontier_etf', 'anchor': 'ITA',
        'flow_tickers': ['ITA', 'PPA', 'XAR'],
        'display_sub': 'ITA / PPA / XAR'
    },
    '🚀 顛覆性創新 (木頭姐)': {
        'type': 'frontier_etf', 'anchor': 'ARKK',
        'flow_tickers': ['ARKK', 'ARKW', 'ARKG', 'ARKF', 'ARKX'],
        'display_sub': 'ARKK / ARKW / ARKG'
    },

    # --- ⭐ 4 大特殊板塊 (精準落實用戶指定規則) ---
    '⚡ 光通訊 / 矽光子': {
        'type': 'stock_flow_etf_anchor', 'anchor': 'FOTO',  # 大圖維持 FOTO 代表性
        'flow_tickers': ['LITE', 'COHR', 'FN', 'CIEN', 'IPGP', 'AAOI', 'CRDO', 'MRVL'],
        'display_sub': 'LITE / COHR / FN / CIEN / MRVL'
    },
    '🏭 AI 伺服器與組裝': {
        'type': 'stock_flow_stock_anchor', 'anchor': 'DELL',  # 大圖錨定 DELL
        'flow_tickers': ['SMCI', 'DELL', 'HPE'],
        'display_sub': 'SMCI / DELL / HPE'
    },
    '📱 Edge AI / 端側晶片': {
        'type': 'stock_flow_stock_anchor', 'anchor': 'AVGO',  # 大圖錨定 AVGO
        'flow_tickers': ['QCOM', 'AAPL', 'AVGO', 'SWKS', 'QRVO', 'LOGI', 'NXPI'],
        'display_sub': 'QCOM / AAPL / AVGO / SWKS'
    },
    '🔋 MLCC / 被動元件': {
        'type': 'stock_flow_stock_anchor', 'anchor': '6981.T',  # 大圖錨定全球霸主村田
        'flow_tickers': ['6981.T', '6762.T', '6976.T', '009150.KS'],
        'display_sub': '6981.T (村田) / 6762.T / 009150.KS'
    }
}

# =========================================================================
# ⚙️ 數據提取與價量資金壓力 (Net Dollar Volume Pressure) 運算引擎
# =========================================================================

def get_all_flow_symbols():
    """提取 34 大板塊所需的全部 ETF 與股票代號"""
    symbols = set(['SPY'])  # 加入大盤基準
    for cfg in GANN05_SECTOR_CONFIG.values():
        symbols.add(cfg['anchor'])
        for s in cfg['flow_tickers']:
            symbols.add(s)
    return list(symbols)

@st.cache_data(ttl=1800, show_spinner=False)
def fetch_sector_flow_data():
    """批次抓取近 60 天的日 K 數據 (足夠覆蓋近 4 週)"""
    tickers = get_all_flow_symbols()
    try:
        df_all = yf.download(tickers, period='3mo', progress=False)
        return df_all
    except Exception as e:
        return pd.DataFrame()

def calculate_single_symbol_pressure(df_all, symbol, days=5):
    """計算單隻資產在指定交易日內的價量淨壓力 (單位: 美元)"""
    try:
        if symbol not in df_all['Close'].columns:
            return 0.0
            
        close = df_all['Close'][symbol].dropna()
        open_p = df_all['Open'][symbol].dropna()
        high = df_all['High'][symbol].dropna()
        low = df_all['Low'][symbol].dropna()
        vol = df_all['Volume'][symbol].dropna()
        
        # 共同索引對齊
        idx = close.index.intersection(open_p.index).intersection(vol.index)
        if len(idx) < days:
            return 0.0
            
        c = close.loc[idx].tail(days)
        o = open_p.loc[idx].tail(days)
        h = high.loc[idx].tail(days)
        l = low.loc[idx].tail(days)
        v = vol.loc[idx].tail(days)
        
        # 價格多空傾角因子: (Close - Open) / (High - Low)
        range_hl = (h - l).replace(0, np.nan)
        direction = ((c - o) / range_hl).fillna(0.0)
        
        # 單日成交金額 Dollar Volume
        dollar_vol = c * v
        
        # 淨價量推動壓力 (Net Dollar Volume Flow)
        net_flow_series = dollar_vol * direction
        return float(net_flow_series.sum())
    except Exception:
        return 0.0

def compute_34_sector_leaderboard(df_all, time_window='1W'):
    """
    計算 34 大板塊資金壓力，並輸出 Top 5 買入與 Top 5 賣出排行榜
    time_window: '1W' (5天) 或 '4W' (20天)
    """
    days = 5 if time_window == '1W' else 20
    results = []
    
    if df_all.empty:
        return pd.DataFrame(), pd.DataFrame(), pd.DataFrame()
        
    for sec_name, cfg in GANN05_SECTOR_CONFIG.items():
        total_pressure = 0.0
        # 同時抓取該板塊配置的所有 flow_tickers 加總推動力
        for sym in cfg['flow_tickers']:
            press = calculate_single_symbol_pressure(df_all, sym, days=days)
            total_pressure += press
            
        # 換算為十億美元 ($B)
        billion_val = total_pressure / 1e9
        
        results.append({
            '板塊名稱': sec_name,
            '代表標的': cfg['display_sub'],
            '錨定代號': cfg['anchor'],
            '資金壓力_B': round(billion_val, 2)
        })
        
    df_res = pd.DataFrame(results)
    
    # 排序取得 Top 5 買入與賣出
    top_buy = df_res[df_res['資金壓力_B'] > 0].sort_values(by='資金壓力_B', ascending=False).head(5).reset_index(drop=True)
    top_sell = df_res[df_res['資金壓力_B'] < 0].sort_values(by='資金壓力_B', ascending=True).head(5).reset_index(drop=True)
    
    return top_buy, top_sell, df_res