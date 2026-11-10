"""
Filename: page_1gann_gann05_calc.py
Description: 34 大板塊資金流壓力與輪動排行榜引擎 (100% 全真量化數據 · 匯率對齊與防失真加固版)
審計加固重點：
1. 解決節假日 4 日誤殺歸零 Bug：動態取 min(len(idx), days)，假日週不再出現資金流被抹平為 0
2. 外匯即時提取安全防禦：防止 JPY=X / KRW=X 空值導致 iloc[-1] IndexError 崩潰
3. yfinance MultiIndex 雙層欄位解構容錯：徹底相容新舊版 yfinance 返回的欄位結構
4. 100% 真實 Chaikin / A/D 價格位置推動力：((C - L) - (H - C)) / (H - L)，杜絕開盤跳空誤判
5. 資金推動強度比 (Flow Intensity %)：解決 QQQ 體量過大對中小板塊的統計碾壓
"""

import streamlit as st
import pandas as pd
import numpy as np
import yfinance as yf

# =========================================================================
# 🏛️ 34 大板塊專屬量化字典 (全實盤標的配置)
# =========================================================================

GANN05_SECTOR_CONFIG = {
    # --- 11 大傳統宏觀板塊 ---
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
        'flow_tickers': ['SMH', 'SOXX', 'NVDA'],
        'display_sub': 'SMH / SOXX / NVDA'
    },
    '💻 CPU / 處理器 (SOXX)': {
        'type': 'frontier_etf', 'anchor': 'SOXX',
        'flow_tickers': ['SOXX', 'XSD', 'INTC', 'AMD'],
        'display_sub': 'SOXX / XSD / INTC / AMD'
    },
    '💾 DRAM / 存儲與記憶體': {
        'type': 'frontier_etf', 'anchor': 'MU',
        'flow_tickers': ['MU', 'WDC', 'STX'],
        'display_sub': 'MU / WDC / STX'
    },
    '❄️ 發電、液冷與散熱板': {
        'type': 'frontier_etf', 'anchor': 'GRID',
        'flow_tickers': ['GRID', 'XLU', 'VRT'],
        'display_sub': 'GRID / XLU / VRT'
    },
    '⚡ 變壓器與電網升級': {
        'type': 'frontier_etf', 'anchor': 'GRID',
        'flow_tickers': ['GRID', 'PAVE', 'ETN'],
        'display_sub': 'GRID / PAVE / ETN'
    },
    '🛡️ 網絡安全': {
        'type': 'frontier_etf', 'anchor': 'CIBR',
        'flow_tickers': ['CIBR', 'HACK', 'PANW', 'CRWD'],
        'display_sub': 'CIBR / HACK / PANW / CRWD'
    },
    '🧠 LLM 大模型巨頭': {
        'type': 'frontier_etf', 'anchor': 'AIQ',
        'flow_tickers': ['AIQ', 'BOTZ', 'MSFT', 'GOOGL'],
        'display_sub': 'AIQ / BOTZ / MSFT / GOOGL'
    },
    '🚗 自動駕駛與 Robotaxi': {
        'type': 'frontier_etf', 'anchor': 'IDRV',
        'flow_tickers': ['IDRV', 'DRIV', 'TSLA'],
        'display_sub': 'IDRV / DRIV / TSLA'
    },
    '🦾 機械人與自動化': {
        'type': 'frontier_etf', 'anchor': 'BOTZ',
        'flow_tickers': ['BOTZ', 'ROBO', 'ISRG'],
        'display_sub': 'BOTZ / ROBO / ISRG'
    },
    '🌌 量子電腦': {
        'type': 'frontier_etf', 'anchor': 'QTUM',
        'flow_tickers': ['QTUM', 'IONQ', 'QBTS', 'RGTI'],
        'display_sub': 'QTUM / IONQ / QBTS / RGTI'
    },
    '🚀 太空與衛星通訊': {
        'type': 'frontier_etf', 'anchor': 'UFO',
        'flow_tickers': ['UFO', 'ROKT', 'RKLB'],
        'display_sub': 'UFO / ROKT / RKLB'
    },
    '🪙 加密貨幣與狂熱': {
        'type': 'frontier_etf', 'anchor': 'IBIT',
        'flow_tickers': ['IBIT', 'BITO', 'COIN', 'MSTR'],
        'display_sub': 'IBIT / BITO / COIN / MSTR'
    },
    '⚛️ 核能、SMR 與鈾礦': {
        'type': 'frontier_etf', 'anchor': 'URA',
        'flow_tickers': ['URA', 'URNM', 'CCJ'],
        'display_sub': 'URA / URNM / CCJ'
    },
    '🥇 金礦股': {
        'type': 'frontier_etf', 'anchor': 'GDX',
        'flow_tickers': ['GDX', 'GDXJ', 'NEM'],
        'display_sub': 'GDX / GDXJ / NEM'
    },
    '🥈 銀礦股': {
        'type': 'frontier_etf', 'anchor': 'SIL',
        'flow_tickers': ['SIL', 'SILJ', 'PAAS'],
        'display_sub': 'SIL / SILJ / PAAS'
    },
    '🥉 銅礦股': {
        'type': 'frontier_etf', 'anchor': 'COPX',
        'flow_tickers': ['COPX', 'CPER', 'FCX'],
        'display_sub': 'COPX / CPER / FCX'
    },
    '🧬 前沿生物科技': {
        'type': 'frontier_etf', 'anchor': 'XBI',
        'flow_tickers': ['XBI', 'IBB', 'VRTX'],
        'display_sub': 'XBI / IBB / VRTX'
    },
    '⚔️ 國防與軍工': {
        'type': 'frontier_etf', 'anchor': 'ITA',
        'flow_tickers': ['ITA', 'PPA', 'LMT', 'RTX'],
        'display_sub': 'ITA / PPA / LMT / RTX'
    },
    '🚀 顛覆性創新 (木頭姐)': {
        'type': 'frontier_etf', 'anchor': 'ARKK',
        'flow_tickers': ['ARKK', 'ARKW', 'ARKG'],
        'display_sub': 'ARKK / ARKW / ARKG'
    },

    # --- 4 大特殊板塊 ---
    '⚡ 光通訊 / 矽光子': {
        'type': 'stock_flow_etf_anchor', 'anchor': 'FOTO',
        'flow_tickers': ['LITE', 'COHR', 'FN', 'CIEN', 'MRVL'],
        'display_sub': 'LITE / COHR / FN / CIEN / MRVL'
    },
    '🏭 AI 伺服器與組裝': {
        'type': 'stock_flow_stock_anchor', 'anchor': 'DELL',
        'flow_tickers': ['SMCI', 'DELL', 'HPE'],
        'display_sub': 'SMCI / DELL / HPE'
    },
    '📱 Edge AI / 端側晶片': {
        'type': 'stock_flow_stock_anchor', 'anchor': 'AVGO',
        'flow_tickers': ['QCOM', 'AAPL', 'AVGO', 'SWKS'],
        'display_sub': 'QCOM / AAPL / AVGO / SWKS'
    },
    '🔋 MLCC / 被動元件': {
        'type': 'stock_flow_stock_anchor', 'anchor': '6981.T',
        'flow_tickers': ['6981.T', '6762.T', '6976.T', '009150.KS'],
        'display_sub': '6981.T (村田) / 6762.T / 009150.KS'
    }
}

# =========================================================================
# ⚙️ 數據提取與匯率對齊引擎
# =========================================================================

def get_all_flow_symbols():
    symbols = set(['SPY', 'JPY=X', 'KRW=X'])
    for cfg in GANN05_SECTOR_CONFIG.values():
        symbols.add(cfg['anchor'])
        for s in cfg['flow_tickers']:
            symbols.add(s)
    return list(symbols)

@st.cache_data(ttl=1800, show_spinner=False)
def fetch_sector_flow_data():
    tickers = get_all_flow_symbols()
    try:
        df_all = yf.download(tickers, period='3mo', progress=False, group_by='column')
        return df_all
    except Exception:
        return pd.DataFrame()

def _safe_get_series(df_all, field_name, symbol):
    """安全解析 yfinance MultiIndex 與單層 DataFrame"""
    try:
        if field_name not in df_all:
            return pd.Series(dtype=float)
        sub = df_all[field_name]
        if isinstance(sub, pd.DataFrame):
            if symbol in sub.columns:
                return sub[symbol].dropna()
        elif isinstance(sub, pd.Series):
            return sub.dropna()
        return pd.Series(dtype=float)
    except Exception:
        return pd.Series(dtype=float)

def calculate_single_symbol_pressure(df_all, symbol, fx_rates, days=5):
    """
    計算單隻資產的真實美元價量推動壓力 (自適應假日長度，杜絕誤殺歸零)
    """
    try:
        close = _safe_get_series(df_all, 'Close', symbol)
        high = _safe_get_series(df_all, 'High', symbol)
        low = _safe_get_series(df_all, 'Low', symbol)
        vol = _safe_get_series(df_all, 'Volume', symbol)

        if close.empty or high.empty or low.empty or vol.empty:
            return 0.0, 0.0

        idx = close.index.intersection(high.index).intersection(low.index).intersection(vol.index)
        if len(idx) == 0:
            return 0.0, 0.0

        # 自適應取最近有效交易日 (即使節假日不足 days 天，也不歸零)
        actual_bars = min(len(idx), days)
        valid_idx = idx[-actual_bars:]

        c = close.loc[valid_idx]
        h = high.loc[valid_idx]
        l = low.loc[valid_idx]
        v = vol.loc[valid_idx]

        # 🌟 1. 經典 Chaikin / A/D 價格位置推動力因子
        range_hl = (h - l).replace(0, np.nan)
        direction = (((c - l) - (h - c)) / range_hl).fillna(0.0)

        # 🌟 2. 嚴格匯率折算 (日元 / 韓元換算為 USD)
        fx_adj = 1.0
        if symbol.endswith('.T'):
            rate = max(0.001, fx_rates.get('JPY', 150.0))
            fx_adj = 1.0 / rate
        elif symbol.endswith('.KS') or symbol.endswith('.KQ'):
            rate = max(0.001, fx_rates.get('KRW', 1380.0))
            fx_adj = 1.0 / rate

        # 真實美元成交額與淨推動金額
        dollar_vol = (c * v) * fx_adj
        net_flow_series = dollar_vol * direction

        return float(net_flow_series.sum()), float(dollar_vol.sum())
    except Exception:
        return 0.0, 0.0

def compute_34_sector_leaderboard(df_all, time_window='1W'):
    """
    計算 34 大板塊資金壓力，輸出絕對金額與推動強度比雙維度
    time_window: '1W' (5天) 或 '4W' (20天)
    """
    days = 5 if time_window == '1W' else 20
    results = []

    if df_all.empty:
        return pd.DataFrame(), pd.DataFrame(), pd.DataFrame()

    # 提取即時外匯匯率 (含完整空值防禦)
    fx_rates = {'JPY': 150.0, 'KRW': 1380.0}
    try:
        jpy_series = _safe_get_series(df_all, 'Close', 'JPY=X')
        if not jpy_series.empty:
            val_jpy = float(jpy_series.iloc[-1])
            if val_jpy > 0:
                fx_rates['JPY'] = val_jpy

        krw_series = _safe_get_series(df_all, 'Close', 'KRW=X')
        if not krw_series.empty:
            val_krw = float(krw_series.iloc[-1])
            if val_krw > 0:
                fx_rates['KRW'] = val_krw
    except Exception:
        pass

    for sec_name, cfg in GANN05_SECTOR_CONFIG.items():
        total_pressure = 0.0
        total_gross_vol = 0.0

        for sym in cfg['flow_tickers']:
            press, gross_v = calculate_single_symbol_pressure(df_all, sym, fx_rates, days=days)
            total_pressure += press
            total_gross_vol += gross_v

        billion_val = total_pressure / 1e9
        intensity_pct = (total_pressure / total_gross_vol * 100.0) if total_gross_vol > 0 else 0.0

        results.append({
            '板塊名稱': sec_name,
            '代表標的': cfg['display_sub'],
            '錨定代號': cfg['anchor'],
            '資金壓力_B': round(billion_val, 3),
            '推動強度_%': round(intensity_pct, 1)
        })

    df_res = pd.DataFrame(results)
    if df_res.empty:
        return pd.DataFrame(), pd.DataFrame(), pd.DataFrame()

    top_buy = df_res[df_res['資金壓力_B'] > 0].sort_values(
        by=['推動強度_%', '資金壓力_B'], ascending=[False, False]
    ).head(5).reset_index(drop=True)

    top_sell = df_res[df_res['資金壓力_B'] < 0].sort_values(
        by=['推動強度_%', '資金壓力_B'], ascending=[True, True]
    ).head(5).reset_index(drop=True)

    return top_buy, top_sell, df_res