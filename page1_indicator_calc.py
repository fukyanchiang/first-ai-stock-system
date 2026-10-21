import os
import json
import ssl
import urllib.request
import pandas as pd
import numpy as np
try:
    import yfinance as yf
except ImportError:
    yf = None

try:
    import streamlit as st
except ImportError:
    class DummySt:
        @staticmethod
        def cache_data(ttl=None):
            def decorator(f):
                return f
            return decorator
    st = DummySt()

import plotly.graph_objects as go
from datetime import datetime
import warnings
warnings.filterwarnings('ignore')

OPTIONS_HISTORY_FILE = "options_history.json"
DARKPOOL_HISTORY_FILE = "finra_darkpool_history.json"

# ===================================================
# 🛸 1. SCTR 天外飛仙計算
# ===================================================
def calculate_historical_sctr(df: pd.DataFrame) -> pd.Series:
    df = df.copy()
    C = df['Close']
    def EMA(s, n): return s.ewm(span=n, adjust=False).mean()
    def SMA(s, n): return s.rolling(window=n, min_periods=1).mean()
    LC = C.shift(1).bfill()
    DIFF_C = C - LC
    UP_RSI = np.where(DIFF_C > 0, DIFF_C, 0)
    ABS_RSI = DIFF_C.abs()
    RSI_VAL = SMA(pd.Series(UP_RSI, index=df.index), 14) / (SMA(pd.Series(ABS_RSI, index=df.index), 14) + 1e-5) * 100
    L_EMA200 = EMA(C, 200)
    L_EMA_S = ((C - L_EMA200) / L_EMA200 * 100) * 1.5
    L_ROC_S = (C / C.shift(125).bfill() - 1) * 20
    M_EMA50 = EMA(C, 50)
    M_EMA_S = ((C - M_EMA50) / M_EMA50 * 30)
    M_ROC_S = (C / C.shift(20).bfill() - 1) * 30
    PPO_F = EMA(C, 12)
    PPO_S = EMA(C, 26)
    PPO_V = (PPO_F - PPO_S) / PPO_S * 100
    S_PPO_S = (PPO_V - PPO_V.shift(3).bfill()) * 5
    S_RSI_S = (RSI_VAL - 50) * 0.5
    S_TOTAL_4_0 = (L_EMA_S + L_ROC_S + M_EMA_S + M_ROC_S + S_PPO_S + S_RSI_S)
    SCTR_RAW = (S_TOTAL_4_0 / 10) + 50
    return SCTR_RAW.clip(lower=0, upper=99.9)

# ===================================================
# ⏱️ 2. 5 分鐘分時 VWAP 早尾盤博弈
# ===================================================
@st.cache_data(ttl=1800)
def fetch_5m_data(ticker_symbol):
    if yf is None: return pd.DataFrame()
    try:
        t = yf.Ticker(ticker_symbol)
        df_5m = t.history(period="60d", interval="5m")
        if df_5m.empty:
            df_5m = yf.download(ticker_symbol, period="60d", interval="5m", progress=False)
        return df_5m
    except Exception:
        return pd.DataFrame()

def compute_morning_afternoon_drift(ticker_symbol, daily_index):
    df_5m = fetch_5m_data(ticker_symbol)
    if df_5m.empty:
        return pd.Series(0.0, index=daily_index), pd.Series(0.0, index=daily_index)
        
    if isinstance(df_5m.columns, pd.MultiIndex):
        try: df_5m = df_5m.xs(ticker_symbol, axis=1, level='Ticker')
        except Exception:
            try: df_5m = df_5m.xs('Close', axis=1, level=0)
            except Exception: pass

    if 'Open' not in df_5m or 'Close' not in df_5m or 'Volume' not in df_5m:
        return pd.Series(0.0, index=daily_index), pd.Series(0.0, index=daily_index)

    df_5m = df_5m.sort_index()
    drift_dict = {}
    for dt, group in df_5m.groupby(df_5m.index.date):
        if len(group) >= 15:
            m_bars = group.iloc[:min(6, len(group))]
            m_open = float(m_bars['Open'].iloc[0])
            m_vol = m_bars['Volume'].values.astype(float)
            m_vol_sum = np.sum(m_vol)
            if m_vol_sum > 0:
                m_tp = ((m_bars['High'] + m_bars['Low'] + m_bars['Close']) / 3.0).values.astype(float)
                m_vwap = np.sum(m_tp * m_vol) / m_vol_sum
                m_ret = (m_vwap - m_open) / (m_open + 1e-9) * 100.0
            else:
                m_close = float(m_bars['Close'].iloc[-1])
                m_ret = (m_close - m_open) / (m_open + 1e-9) * 100.0
                
            a_bars = group.iloc[max(0, len(group)-12):]
            a_open = float(a_bars['Open'].iloc[0])
            a_vol = a_bars['Volume'].values.astype(float)
            a_vol_sum = np.sum(a_vol)
            if a_vol_sum > 0:
                a_tp = ((a_bars['High'] + a_bars['Low'] + a_bars['Close']) / 3.0).values.astype(float)
                a_vwap = np.sum(a_tp * a_vol) / a_vol_sum
                a_ret = (a_vwap - a_open) / (a_open + 1e-9) * 100.0
            else:
                a_close = float(a_bars['Close'].iloc[-1])
                a_ret = (a_close - a_open) / (a_open + 1e-9) * 100.0
            drift_dict[pd.to_datetime(dt)] = (m_ret, a_ret)
            
    if not drift_dict:
        return pd.Series(0.0, index=daily_index), pd.Series(0.0, index=daily_index)
        
    drift_df = pd.DataFrame.from_dict(drift_dict, orient='index', columns=['Morning_Ret', 'Afternoon_Ret'])
    daily_norm = pd.to_datetime(daily_index).tz_localize(None) if hasattr(daily_index, 'tz') and daily_index.tz is not None else pd.to_datetime(daily_index)
    daily_norm = daily_norm.normalize()
    drift_df.index = pd.to_datetime(drift_df.index).normalize()
    aligned = drift_df.reindex(daily_norm)
    morning_cum = aligned['Morning_Ret'].fillna(0.0).rolling(window=20, min_periods=1).sum().values
    afternoon_cum = aligned['Afternoon_Ret'].fillna(0.0).rolling(window=20, min_periods=1).sum().values
    return pd.Series(morning_cum, index=daily_index), pd.Series(afternoon_cum, index=daily_index)

# ===================================================
# 🏛️ 3. FINRA 暗池數據
# ===================================================
def load_darkpool_history():
    if os.path.exists(DARKPOOL_HISTORY_FILE):
        try:
            with open(DARKPOOL_HISTORY_FILE, "r", encoding="utf-8") as f:
                return json.load(f)
        except Exception: return {}
    return {}

def save_darkpool_history(history):
    try:
        with open(DARKPOOL_HISTORY_FILE, "w", encoding="utf-8") as f:
            json.dump(history, f, ensure_ascii=False, indent=2)
    except Exception: pass

@st.cache_data(ttl=86400)
def fetch_finra_regsho_file(date_str_nodash):
    url = f"https://regsho.finra.org/CNMSshvol{date_str_nodash}.txt"
    headers = {'User-Agent': 'Mozilla/5.0'}
    req = urllib.request.Request(url, headers=headers)
    ctx = ssl.create_default_context()
    ctx.check_hostname = False
    ctx.verify_mode = ssl.CERT_NONE
    try:
        with urllib.request.urlopen(req, context=ctx, timeout=4) as resp:
            return resp.read().decode('utf-8', errors='ignore')
    except Exception: return ""

def fetch_and_record_darkpool_ratio(symbol, market_type, df):
    if market_type != "美股" or "." in symbol:
        return pd.Series(np.nan, index=df.index), pd.Series(np.nan, index=df.index)
    history = load_darkpool_history()
    symbol_clean = str(symbol).replace('.US', '').strip().upper()
    symbol_hist = history.setdefault(symbol_clean, {})
    recent_dates = [d.strftime("%Y-%m-%d") for d in df.index[-5:]]
    missing_dates = [d for d in recent_dates if d not in symbol_hist or not isinstance(symbol_hist[d], dict)]
    has_updates = False
    for d in missing_dates:
        d_nodash = d.replace("-", "")
        file_text = fetch_finra_regsho_file(d_nodash)
        if file_text:
            for line in file_text.splitlines():
                if f"|{symbol_clean}|" in line:
                    parts = line.split("|")
                    if len(parts) >= 5 and parts[1].strip() == symbol_clean:
                        try:
                            short_vol = float(parts[2])
                            exempt_vol = float(parts[3])
                            total_vol = float(parts[4])
                            if total_vol > 0:
                                short_ratio = round((short_vol / total_vol) * 100.0, 2)
                                exempt_ratio = round((exempt_vol / total_vol) * 100.0, 2)
                                symbol_hist[d] = {"short_ratio": short_ratio, "exempt_ratio": exempt_ratio}
                                has_updates = True
                                break
                        except Exception: pass
    if has_updates: save_darkpool_history(history)
    short_series = pd.Series(np.nan, index=df.index)
    exempt_series = pd.Series(np.nan, index=df.index)
    for dt in df.index:
        d_str = dt.strftime("%Y-%m-%d")
        if d_str in symbol_hist:
            val = symbol_hist[d_str]
            if isinstance(val, dict):
                short_series.loc[dt] = val.get("short_ratio", np.nan)
                exempt_series.loc[dt] = val.get("exempt_ratio", np.nan)
            else: short_series.loc[dt] = float(val)
    return short_series, exempt_series

# ===================================================
# 🎰 4. 期權狂熱比
# ===================================================
def load_options_history():
    if os.path.exists(OPTIONS_HISTORY_FILE):
        try:
            with open(OPTIONS_HISTORY_FILE, "r", encoding="utf-8") as f: return json.load(f)
        except Exception: return {}
    return {}

def save_options_history(history):
    try:
        with open(OPTIONS_HISTORY_FILE, "w", encoding="utf-8") as f: json.dump(history, f, ensure_ascii=False, indent=2)
    except Exception: pass

@st.cache_data(ttl=900)
def fetch_live_otm_call_ratio(symbol, current_price):
    if yf is None: return 0.0
    try:
        t = yf.Ticker(symbol)
        options_dates = getattr(t, "options", None)
        if not options_dates or len(options_dates) == 0: return 0.0
        nearest_exp = options_dates[0]
        chain = t.option_chain(nearest_exp)
        if chain is None or not hasattr(chain, 'calls') or chain.calls.empty: return 0.0
        calls = chain.calls.copy()
        calls['volume'] = calls['volume'].fillna(0)
        otm_calls = calls[calls['strike'] >= current_price * 1.10]
        otm_vol = float(otm_calls['volume'].sum())
        atm_calls = calls[(calls['strike'] >= current_price * 0.975) & (calls['strike'] <= current_price * 1.025)]
        atm_vol = float(atm_calls['volume'].sum())
        if atm_vol > 0: return round(otm_vol / atm_vol, 2)
        elif otm_vol > 0: return round(otm_vol / 100.0, 2)
        else: return 0.0
    except Exception: return 0.0

def fetch_and_record_otm_call_ratio(symbol, df, current_price):
    history = load_options_history()
    symbol_hist = history.setdefault(symbol, {})
    latest_ratio = fetch_live_otm_call_ratio(symbol, current_price)
    if len(df) > 0 and latest_ratio > 0.0:
        latest_date_str = df.index[-1].strftime("%Y-%m-%d")
        symbol_hist[latest_date_str] = latest_ratio
        save_options_history(history)
    ratio_series = pd.Series(0.0, index=df.index)
    for dt in df.index:
        d_str = dt.strftime("%Y-%m-%d")
        if d_str in symbol_hist: ratio_series.loc[dt] = symbol_hist[d_str]
    return ratio_series

# ===================================================
# 🧭 5. 五維共振評級矩陣
# ===================================================
def compute_spread_series(df):
    chive_z = df['Chive_Z'].fillna(0.0)
    smart_z = df['Smart_Z'].fillna(0.0)
    diff1 = np.clip((smart_z - chive_z) / 2.0, -1.0, 1.0) * 25.0
    overnight_z = df['Overnight_Z'].fillna(0.0)
    intraday_z = df['Intraday_Z'].fillna(0.0)
    diff2 = np.clip((intraday_z - overnight_z) / 2.0, -1.0, 1.0) * 25.0
    morning_z = df['Morning_Z'].fillna(0.0)
    afternoon_z = df['Afternoon_Z'].fillna(0.0)
    diff3 = np.clip((afternoon_z - morning_z) / 2.0, -1.0, 1.0) * 20.0
    dp_score = pd.Series(0.0, index=df.index)
    if 'Dark_Pool_Ratio' in df:
        dp = df['Dark_Pool_Ratio']
        valid_dp = (~dp.isna()) & (dp > 0)
        dp_diff = np.clip((48.0 - dp) / 5.0, -1.0, 1.0)
        exempt_pen = pd.Series(0.0, index=df.index)
        if 'Short_Exempt_Ratio' in df:
            ex = df['Short_Exempt_Ratio']
            exempt_pen = np.where(ex >= 2.5, -1.0, np.where(ex <= 1.0, 0.5, 0.0))
        dp_score = np.where(valid_dp, (dp_diff * 0.6 + exempt_pen * 0.4) * 15.0, 0.0)
    otm_score = pd.Series(0.0, index=df.index)
    if 'OTM_Call_Ratio' in df:
        otm = df['OTM_Call_Ratio']
        valid_otm = (~otm.isna()) & (otm > 0)
        otm_pen = np.where(otm >= 1.5, -15.0, np.where(otm >= 1.0, -7.5, np.where(otm <= 0.4, 15.0, 5.0)))
        otm_score = np.where(valid_otm, otm_pen, 0.0)
    total_score = diff1 + diff2 + diff3 + dp_score + otm_score
    return np.clip(total_score, -100.0, 100.0).round(1)

def get_spread_metrics(score):
    trap_risk_pct = round((100.0 - score) / 2.0, 1)
    if trap_risk_pct >= 80.0: return trap_risk_pct, "🚨 極度危險 (散戶嚴重套牢 · 主力派發)", "#ff3366", "極度危險"
    elif trap_risk_pct >= 60.0: return trap_risk_pct, "⚠️ 警戒狀態 (散戶偏熱 · 主力倒貨背離)", "#ffaa00", "警戒出貨"
    elif trap_risk_pct >= 40.0: return trap_risk_pct, "⚪ 多空平衡 (資金博弈平穩 · 觀望洗盤)", "#94a3b8", "多空平衡"
    elif trap_risk_pct >= 20.0: return trap_risk_pct, "🟢 機構主導 (主力暗中吸籌 · 散戶離場)", "#00f2ff", "主力吸籌"
    else: return trap_risk_pct, "🚀 黃金反轉底 (散戶恐慌割肉 · 主力強勢控盤)", "#00ff88", "黃金底背離"

def get_hud_tags(row):
    cz = row.get('Chive_Z', 0.0); sz = row.get('Smart_Z', 0.0)
    cz = 0.0 if pd.isna(cz) else cz; sz = 0.0 if pd.isna(sz) else sz
    if cz >= 2.0: d1 = f"<span style='color:#ff3366;'>🚨套牢({cz:+.1f}σ)</span>"
    elif sz >= 2.0: d1 = f"<span style='color:#00ff88;'>🟢吸籌({sz:+.1f}σ)</span>"
    else: d1 = f"<span style='color:#94a3b8;'>⚪平衡({cz-sz:+.1f}σ)</span>"
    oz = row.get('Overnight_Z', 0.0); iz = row.get('Intraday_Z', 0.0)
    oz = 0.0 if pd.isna(oz) else oz; iz = 0.0 if pd.isna(iz) else iz
    if oz >= 2.0 and iz <= 0: d2 = f"<span style='color:#ff3366;'>🚨出貨({oz:+.1f}σ)</span>"
    elif iz >= 2.0: d2 = f"<span style='color:#00ff88;'>🟢買盤({iz:+.1f}σ)</span>"
    else: d2 = "<span style='color:#94a3b8;'>⚪正常</span>"
    mz = row.get('Morning_Z', 0.0); az = row.get('Afternoon_Z', 0.0)
    mz = 0.0 if pd.isna(mz) else mz; az = 0.0 if pd.isna(az) else az
    if mz >= 2.0 and az <= 0: d3 = f"<span style='color:#ff3366;'>🚨誘多({mz:+.1f}σ)</span>"
    elif az >= 2.0: d3 = f"<span style='color:#00ff88;'>🟢定盤({az:+.1f}σ)</span>"
    else: d3 = "<span style='color:#94a3b8;'>⚪正常</span>"
    dp = row.get('Dark_Pool_Ratio', np.nan); ex = row.get('Short_Exempt_Ratio', np.nan)
    if not pd.isna(dp) and dp > 0:
        if not pd.isna(ex) and ex >= 2.5: d4 = f"<span style='color:#FF0080;'>🚨豁免做空({ex:.1f}%)</span>"
        elif dp >= 50.0: d4 = f"<span style='color:#ffaa00;'>⚠️空頭({dp:.1f}%)</span>"
        else: d4 = f"<span style='color:#00ff88;'>🟢安全({dp:.1f}%)</span>"
    else: d4 = "<span style='color:#64748b;'>— 非美股</span>"
    otm = row.get('OTM_Call_Ratio', np.nan)
    if not pd.isna(otm) and otm > 0:
        if otm >= 1.5: d5 = f"<span style='color:#FF00FF;'>🔥踩踏({otm:.2f}x)</span>"
        elif otm >= 1.0: d5 = f"<span style='color:#ffaa00;'>⚠️狂熱({otm:.2f}x)</span>"
        else: d5 = f"<span style='color:#00ff88;'>🟢冷靜({otm:.2f}x)</span>"
    else: d5 = "<span style='color:#64748b;'>— 無期權</span>"
    return d1, d2, d3, d4, d5

# ===================================================
# 📊 6. 計算組 1 指標 (量價、背離、流動性)
# ===================================================
def compute_group1_indicators(df, symbol, market_type, benchmark_ticker):
    df = df.copy()
    if hasattr(df.index, 'tz') and df.index.tz is not None:
        df.index = df.index.tz_localize(None)

    C, O, H, L, V = df['Close'], df['Open'], df['High'], df['Low'], df['Volume']

    df['V_MA'] = V.rolling(window=20).mean()
    df['V_STD'] = V.rolling(window=20).std()
    df['V_UPPER'] = df['V_MA'] + (2.0 * df['V_STD'])
    df['均量60'] = V.rolling(window=60).mean()
    df['MA20'] = C.rolling(window=20).mean()
    df['HV60'] = V.rolling(window=60).max()
    df['VAS_raw'] = np.where(V == df['HV60'], L, np.nan)
    df['VAS'] = df['VAS_raw'].ffill()
    df['VOLMA20_BIG'] = V.rolling(window=20).mean()
    df['ISBIG'] = (V > df['VOLMA20_BIG'] * 1.5) & (C > O)

    # 影線量價套牢
    df['Vol_Ratio'] = V / (V.rolling(window=20).mean() + 1e-9)
    df['Retail_Action'] = df['Vol_Ratio'] * (H - C)
    df['Chive_Line'] = df['Retail_Action'].rolling(window=14).sum()
    df['Smart_Action'] = df['Vol_Ratio'] * (C - L)
    df['Smart_Line'] = df['Smart_Action'].rolling(window=14).sum()
    df['Chive_Z'] = (df['Chive_Line'] - df['Chive_Line'].rolling(20).mean()) / (df['Chive_Line'].rolling(20).std() + 1e-9)
    df['Smart_Z'] = (df['Smart_Line'] - df['Smart_Line'].rolling(20).mean()) / (df['Smart_Line'].rolling(20).std() + 1e-9)

    # 隔夜盤中漂移
    df['Overnight_Ret'] = (O - C.shift(1)) / (C.shift(1) + 1e-9) * 100
    df['Intraday_Ret'] = (C - O) / (O + 1e-9) * 100
    df['Overnight_Cum'] = df['Overnight_Ret'].rolling(window=20).sum()
    df['Intraday_Cum'] = df['Intraday_Ret'].rolling(window=20).sum()
    df['Overnight_Z'] = (df['Overnight_Cum'] - df['Overnight_Cum'].rolling(20).mean()) / (df['Overnight_Cum'].rolling(20).std() + 1e-9)
    df['Intraday_Z'] = (df['Intraday_Cum'] - df['Intraday_Cum'].rolling(20).mean()) / (df['Intraday_Cum'].rolling(20).std() + 1e-9)

    # 早尾盤 VWAP
    try:
        m_cum, a_cum = compute_morning_afternoon_drift(symbol, df.index)
        df['Morning_Cum'] = m_cum; df['Afternoon_Cum'] = a_cum
        df['Morning_Z'] = (df['Morning_Cum'] - df['Morning_Cum'].rolling(20).mean()) / (df['Morning_Cum'].rolling(20).std() + 1e-9)
        df['Afternoon_Z'] = (df['Afternoon_Cum'] - df['Afternoon_Cum'].rolling(20).mean()) / (df['Afternoon_Cum'].rolling(20).std() + 1e-9)
    except Exception:
        df['Morning_Cum'] = 0.0; df['Afternoon_Cum'] = 0.0; df['Morning_Z'] = 0.0; df['Afternoon_Z'] = 0.0

    # FINRA 暗池
    try:
        dp_ratio, exempt_ratio = fetch_and_record_darkpool_ratio(symbol, market_type, df)
        df['Dark_Pool_Ratio'] = dp_ratio; df['Short_Exempt_Ratio'] = exempt_ratio
    except Exception:
        df['Dark_Pool_Ratio'] = np.nan; df['Short_Exempt_Ratio'] = np.nan

    # 期權狂熱比
    current_price_probe = float(C.dropna().iloc[-1]) if not C.dropna().empty else 1.0
    try:
        df['OTM_Call_Ratio'] = fetch_and_record_otm_call_ratio(symbol, df, current_price_probe)
    except Exception:
        df['OTM_Call_Ratio'] = 0.0

    df['Spread_Score'] = compute_spread_series(df)
    df['Trap_Risk'] = ((100.0 - df['Spread_Score']) / 2.0).round(1)

    # DELTAME
    df['VAR1'] = C - L; df['VAR2'] = H - C; df['VAR3'] = H - L
    df['BUYVOL'] = np.where(df['VAR3'] > 0, V * df['VAR1'] / df['VAR3'], 0)
    df['SELLVOL'] = np.where(df['VAR3'] > 0, V * df['VAR2'] / df['VAR3'], 0)
    df['NETVOL'] = df['BUYVOL'] - df['SELLVOL']
    df['NETMA'] = df['NETVOL'].rolling(window=10).mean()

    # TURN VIX
    df['prev_Close'] = C.shift(1)
    df['升跌幅'] = (C - df['prev_Close']).abs() / df['prev_Close'] * 100
    df['真正爆發'] = (V > df['V_UPPER']) & (V > df['均量60'] * 1.9) & (df['升跌幅'] > 2.0)
    df['CHANGE'] = (C - df['prev_Close']) / df['prev_Close'] * 100

    # RSI(14)
    delta = C.diff()
    gain = delta.clip(lower=0); loss = (-delta).clip(lower=0)
    avg_gain = gain.rolling(window=14).mean(); avg_loss = loss.rolling(window=14).mean()
    rs_val = avg_gain / (avg_loss + 1e-9)
    df['RSI'] = 100 - (100 / (1 + rs_val))

    # RS Line
    df['RS_Line'] = np.nan; df['RS_MA50'] = np.nan
    if yf is not None:
        try:
            start_date = df.index.min(); end_date = df.index.max() + pd.Timedelta(days=1)
            bm_df = yf.download(benchmark_ticker, start=start_date, end=end_date, progress=False)
            if not bm_df.empty:
                if hasattr(bm_df.index, 'tz') and bm_df.index.tz is not None:
                    bm_df.index = bm_df.index.tz_localize(None)
                if isinstance(bm_df.columns, pd.MultiIndex):
                    try: bm_close = bm_df['Close'][benchmark_ticker]
                    except Exception: bm_close = bm_df.xs('Close', axis=1, level=0).iloc[:, 0]
                else: bm_close = bm_df['Close']
                if isinstance(bm_close, pd.DataFrame): bm_close = bm_close.iloc[:, 0]
                bm_close_aligned = bm_close.reindex(df.index).ffill().bfill()
                df['RS_Line'] = C / (bm_close_aligned + 1e-9)
                df['RS_MA50'] = df['RS_Line'].rolling(window=50, min_periods=1).mean()
        except Exception: pass

    # SCTR
    df['SCTR'] = calculate_historical_sctr(df)
    return df

# ===================================================
# 🎨 7. 繪製組 1 副圖 Trace 輔助函數
# ===================================================
def render_group1_traces(fig, k, df_display, y_ax, dm, benchmark_ticker, day_ms, y_num, y_axes_config):
    y_key = f"yaxis{y_num}"
    if k == "sctr":
        fig.add_trace(go.Scatter(x=df_display.index, y=df_display['SCTR'], mode='lines', line=dict(color='#FFD700', width=2), name='SCTR 分數', yaxis=y_ax))
        fig.add_shape(type="line", x0=df_display.index[0], y0=90, x1=df_display.index[-1], y1=90, line=dict(color="#FF3366", width=2, dash="dash"), xref='x', yref=y_ax)
        fig.add_shape(type="rect", x0=df_display.index[0], y0=90, x1=df_display.index[-1], y1=100, fillcolor="rgba(255, 51, 102, 0.15)", line_width=0, xref='x', yref=y_ax)
        y_axes_config[y_key] = dict(domain=dm, anchor='x', title_text="SCTR<br>(0-100)", gridcolor='#2e3d52', title_font=dict(size=10), range=[0, 100])
    elif k == "rs":
        fig.add_trace(go.Scatter(x=df_display.index, y=df_display['RS_Line'], mode='lines', line=dict(color='#00bfff', width=2), name=f'RS Line vs {benchmark_ticker}', yaxis=y_ax))
        fig.add_trace(go.Scatter(x=df_display.index, y=df_display['RS_MA50'], mode='lines', line=dict(color='rgba(255, 255, 0, 0.8)', width=1.5, dash='dot'), name='50 RS-MA', yaxis=y_ax))
        y_axes_config[y_key] = dict(domain=dm, anchor='x', title_text=f"RS Line<br>vs {benchmark_ticker}", gridcolor='#2e3d52', title_font=dict(size=10))
    elif k == "vol":
        vol_colors = np.where(df_display['Close'] >= df_display['Open'], '#00ff88', '#ff3366')
        fig.add_trace(go.Bar(x=df_display.index, y=df_display['Volume'], marker_color=vol_colors, name='成交量', yaxis=y_ax))
        y_axes_config[y_key] = dict(domain=dm, anchor='x', title_text="成交量<br>Volume", gridcolor='#2e3d52', title_font=dict(size=10))
    elif k == "chive":
        fig.add_trace(go.Bar(x=df_display.index, y=df_display['Chive_Z'], marker_color='#00ff88', name='韭菜套牢(Z)', yaxis=y_ax))
        fig.add_trace(go.Bar(x=df_display.index, y=-df_display['Smart_Z'], marker_color='#FFD700', name='主力吸籌(Z)', yaxis=y_ax))
        fig.add_shape(type="line", x0=df_display.index[0], y0=0, x1=df_display.index[-1], y1=0, line=dict(color="rgba(255,255,255,0.3)", width=1), xref='x', yref=y_ax)
        fig.add_shape(type="line", x0=df_display.index[0], y0=2.0, x1=df_display.index[-1], y1=2.0, line=dict(color="rgba(255, 0, 255, 0.6)", width=1.5, dash="dot"), xref='x', yref=y_ax)
        fig.add_shape(type="line", x0=df_display.index[0], y0=-2.0, x1=df_display.index[-1], y1=-2.0, line=dict(color="rgba(255, 0, 255, 0.6)", width=1.5, dash="dot"), xref='x', yref=y_ax)
        y_axes_config[y_key] = dict(domain=dm, anchor='x', title_text="韭菜vs主力<br>(Z-Score)", gridcolor='#2e3d52', title_font=dict(size=10))
    elif k == "drift":
        fig.add_trace(go.Scatter(x=df_display.index, y=df_display['Overnight_Z'], mode='lines', line=dict(color='#00bfff', width=2), name='隔夜累積(Z)', yaxis=y_ax))
        fig.add_trace(go.Scatter(x=df_display.index, y=df_display['Intraday_Z'], mode='lines', line=dict(color='#ff3366', width=2), name='盤中真實(Z)', yaxis=y_ax))
        fig.add_shape(type="line", x0=df_display.index[0], y0=0, x1=df_display.index[-1], y1=0, line=dict(color="rgba(255,255,255,0.3)", width=1), xref='x', yref=y_ax)
        fig.add_shape(type="line", x0=df_display.index[0], y0=2.0, x1=df_display.index[-1], y1=2.0, line=dict(color="rgba(255, 0, 255, 0.6)", width=1.5, dash="dot"), xref='x', yref=y_ax)
        fig.add_shape(type="line", x0=df_display.index[0], y0=-2.0, x1=df_display.index[-1], y1=-2.0, line=dict(color="rgba(255, 0, 255, 0.6)", width=1.5, dash="dot"), xref='x', yref=y_ax)
        y_axes_config[y_key] = dict(domain=dm, anchor='x', title_text="漂移背馳<br>(Z-Score)", gridcolor='#2e3d52', title_font=dict(size=10))
    elif k == "vwap":
        fig.add_trace(go.Scatter(x=df_display.index, y=df_display['Morning_Z'], mode='lines', line=dict(color='#00ff88', width=2), name='早盤散戶VWAP(Z)', yaxis=y_ax))
        fig.add_trace(go.Scatter(x=df_display.index, y=df_display['Afternoon_Z'], mode='lines', line=dict(color='#FFD700', width=2), name='尾盤機構VWAP(Z)', yaxis=y_ax))
        fig.add_shape(type="line", x0=df_display.index[0], y0=0, x1=df_display.index[-1], y1=0, line=dict(color="rgba(255,255,255,0.3)", width=1), xref='x', yref=y_ax)
        fig.add_shape(type="line", x0=df_display.index[0], y0=2.0, x1=df_display.index[-1], y1=2.0, line=dict(color="rgba(255, 0, 255, 0.6)", width=1.5, dash="dot"), xref='x', yref=y_ax)
        fig.add_shape(type="line", x0=df_display.index[0], y0=-2.0, x1=df_display.index[-1], y1=-2.0, line=dict(color="rgba(255, 0, 255, 0.6)", width=1.5, dash="dot"), xref='x', yref=y_ax)
        y_axes_config[y_key] = dict(domain=dm, anchor='x', title_text="早尾盤VWAP<br>(Z-Score)", gridcolor='#2e3d52', title_font=dict(size=10))
    elif k == "finra":
        fig.add_trace(go.Scatter(x=df_display.index, y=df_display['Dark_Pool_Ratio'], mode='lines+markers', line=dict(color='#ffaa00', width=2), connectgaps=True, name='FINRA 暗池做空比 (%)', yaxis=y_ax))
        fig.add_shape(type="line", x0=df_display.index[0], y0=50, x1=df_display.index[-1], y1=50, line=dict(color="red", width=1.5, dash="dash"), xref='x', yref=y_ax)
        y_axes_config[y_key] = dict(domain=dm, anchor='x', title_text="FINRA<br>場外暗池%", gridcolor='#2e3d52', title_font=dict(size=10))
        if 'Short_Exempt_Ratio' in df_display:
            y15_num = y_num + 50
            y15_ax = f"y{y15_num}"
            fig.add_trace(go.Bar(x=df_display.index, y=df_display['Short_Exempt_Ratio'], marker_color='rgba(255, 0, 128, 0.75)', name='造市商豁免做空 (%)', yaxis=y15_ax))
            fig.add_shape(type="line", x0=df_display.index[0], y0=2.5, x1=df_display.index[-1], y1=2.5, line=dict(color="rgba(255, 0, 128, 0.8)", width=1.2, dash="dot"), xref='x', yref=y15_ax)
            y_axes_config[f"yaxis{y15_num}"] = dict(domain=dm, anchor='x', overlaying=y_ax, side='right', title_text="豁免做空%", showgrid=False, title_font=dict(size=9, color="#FF0080"), tickfont=dict(size=9, color="#FF0080"), range=[0, 6])
    elif k == "otm":
        fig.add_trace(go.Bar(x=df_display.index, y=df_display['OTM_Call_Ratio'], marker_color='#FF00FF', name='虛值期權狂熱比', yaxis=y_ax))
        fig.add_shape(type="line", x0=df_display.index[0], y0=1.0, x1=df_display.index[-1], y1=1.0, line=dict(color="rgba(255, 255, 0, 0.5)", width=1, dash="dot"), xref='x', yref=y_ax)
        fig.add_shape(type="line", x0=df_display.index[0], y0=1.5, x1=df_display.index[-1], y1=1.5, line=dict(color="rgba(255, 0, 255, 0.8)", width=1.5, dash="dash"), xref='x', yref=y_ax)
        y_axes_config[y_key] = dict(domain=dm, anchor='x', title_text="虛值 Call<br>狂熱期權比", gridcolor='#2e3d52', title_font=dict(size=10))
    elif k == "deltame":
        fig.add_trace(go.Bar(x=df_display.index, y=df_display['BUYVOL'], marker_color='#808000', width=day_ms*0.8, name='BUYVOL', yaxis=y_ax))
        fig.add_trace(go.Bar(x=df_display.index, y=-df_display['SELLVOL'], marker_color='#800000', width=day_ms*0.8, name='SELLVOL', yaxis=y_ax))
        net_colors = np.where(df_display['NETVOL'] > 0, '#00ff88', '#ff3366') 
        fig.add_trace(go.Bar(x=df_display.index, y=df_display['NETVOL'], marker_color=net_colors, width=day_ms*0.35, name='NETVOL', yaxis=y_ax))
        fig.add_trace(go.Scatter(x=df_display.index, y=df_display['NETMA'], mode='lines', line=dict(color='#ffffff', width=2), name='NETMA', yaxis=y_ax))
        y_axes_config[y_key] = dict(domain=dm, anchor='x', title_text="TRADE FORCE<br>DELTAME", gridcolor='#2e3d52', title_font=dict(size=10))
    elif k == "turnvix":
        vix_colors = np.full(len(df_display), '#444444', dtype=object)
        is_breakout = df_display['真正爆發'] == True; is_bull = df_display['Close'] > df_display['Open']
        vix_colors[is_breakout & is_bull] = '#00ffff'; vix_colors[is_breakout & ~is_bull] = '#ff00ff'
        fig.add_trace(go.Bar(x=df_display.index, y=df_display['Volume'], marker_color=vix_colors, name='TURN VIX 量能', yaxis=y_ax))
        fig.add_trace(go.Scatter(x=df_display.index, y=df_display['V_UPPER'], mode='lines', line=dict(color='rgba(0,242,255,0.6)', width=1, dash='dot'), name='V_UPPER(短防)', yaxis=y_ax))
        fig.add_trace(go.Scatter(x=df_display.index, y=df_display['均量60'], mode='lines', line=dict(color='rgba(255,255,0,0.6)', width=1.5), name='均量60(長防)', yaxis=y_ax))
        y_axes_config[y_key] = dict(domain=dm, anchor='x', title_text="TRADE FORCE<br>TURN VIX", gridcolor='#2e3d52', title_font=dict(size=10))
    elif k == "change":
        change_colors = np.where(df_display['CHANGE'] >= 0, '#ff3366', '#00ff88')
        fig.add_trace(go.Bar(x=df_display.index, y=df_display['CHANGE'], marker_color=change_colors, name='DAILY PRICE CHANGE', yaxis=y_ax))
        y_axes_config[y_key] = dict(domain=dm, anchor='x', title_text="DAILY PRICE<br>CHANGE", gridcolor='#2e3d52', title_font=dict(size=10))
    elif k == "rsi":
        fig.add_trace(go.Scatter(x=df_display.index, y=df_display['RSI'], mode='lines', line=dict(color='#ffaa00', width=1.5), name='RSI(14)', yaxis=y_ax))
        fig.add_shape(type="line", x0=df_display.index[0], y0=70, x1=df_display.index[-1], y1=70, line=dict(color="gray", width=1, dash="dash"), xref='x', yref=y_ax)
        fig.add_shape(type="line", x0=df_display.index[0], y0=30, x1=df_display.index[-1], y1=30, line=dict(color="gray", width=1, dash="dash"), xref='x', yref=y_ax)
        y_axes_config[y_key] = dict(domain=dm, anchor='x', title_text="RSI(14)", gridcolor='#2e3d52', title_font=dict(size=10), range=[0, 100])