import os
import pandas as pd
import numpy as np
import yfinance as yf
import warnings
warnings.filterwarnings('ignore')

MUST_HAVE = ['1288', '1919', '1138', '1398', '0700', '9988', '3690']

def get_stock_data(ticker_symbol):
    try:
        df = yf.download(ticker_symbol, period="2y", interval="1d", progress=False)
        if isinstance(df.columns, pd.MultiIndex):
            df.columns = df.columns.get_level_values(0)
        df = df.dropna(subset=['Close'])
        if len(df) >= 200:
            return df
    except Exception:
        pass
    return None

def calculate_sctr(df):
    close = df['Close']
    ema200 = close.ewm(span=200, adjust=False).mean()
    p_ema200 = ((close.iloc[-1] - ema200.iloc[-1]) / ema200.iloc[-1]) * 100
    roc125 = ((close.iloc[-1] - close.iloc[-125]) / close.iloc[-125]) * 100
    ema50 = close.ewm(span=50, adjust=False).mean()
    p_ema50 = ((close.iloc[-1] - ema50.iloc[-1]) / ema50.iloc[-1]) * 100
    roc20 = ((close.iloc[-1] - close.iloc[-20]) / close.iloc[-20]) * 100
    delta = close.diff()
    gain = (delta.where(delta > 0, 0)).rolling(14).mean()
    loss = (-delta.where(delta < 0, 0)).rolling(14).mean()
    rs = gain / (loss + 1e-9)
    rsi14 = (100 - (100 / (1 + rs))).iloc[-1]
    
    return {
        'Close': float(close.iloc[-1]),
        'p_ema200': float(p_ema200),
        'roc125': float(roc125),
        'p_ema50': float(p_ema50),
        'roc20': float(roc20),
        'rsi14': float(rsi14)
    }

print("🚀 啟動全宇宙 SCTR 三重格式相容生成引擎...")
results = []

hk_url = "https://raw.githubusercontent.com/fukyanchiang/my-cosmos-vision/refs/heads/main/hk_stock.csv"
try:
    raw_df = pd.read_csv(hk_url, dtype=str)
    col = raw_df.columns[0]
    tickers = [str(int(''.join(filter(str.isdigit, x)))) for x in raw_df[col].dropna() if ''.join(filter(str.isdigit, x))]
except:
    tickers = []

tickers = list(set(tickers + MUST_HAVE))
print(f"✅ 載入 {len(tickers)} 隻標的 (包含保底 1288, 1919, 1138, 1398)...")

for i, t in enumerate(tickers):
    dl_t = f"{t.zfill(4)}.HK"
    df = get_stock_data(dl_t)
    if df is not None:
        m = calculate_sctr(df)
        results.append({
            'Ticker': t,
            'Category': 'HK_Equities',
            **m
        })

df_res = pd.DataFrame(results)
r_ema200 = df_res['p_ema200'].rank(pct=True) * 100
r_roc125 = df_res['roc125'].rank(pct=True) * 100
r_ema50  = df_res['p_ema50'].rank(pct=True) * 100
r_roc20  = df_res['roc20'].rank(pct=True) * 100
r_rsi14  = df_res['rsi14'].rank(pct=True) * 100

df_res['SCTR'] = (r_ema200 * 0.30 + r_roc125 * 0.30 + r_ema50 * 0.15 + r_roc20 * 0.15 + r_rsi14 * 0.10).round(2)

# 🌟【關鍵核心】：生成三種格式，確保 App 點搜尋都對得上！
rows = []
for _, row in df_res.iterrows():
    d = row.to_dict()
    t_clean = str(d['Ticker']).strip()
    if t_clean.isdigit():
        # 1. 4 位數格式 (例: 1288)
        d1 = d.copy(); d1['Ticker'] = str(int(t_clean)); rows.append(d1)
        # 2. 5 位數補零格式 (例: 01288)
        d2 = d.copy(); d2['Ticker'] = t_clean.zfill(5); rows.append(d2)
        # 3. .HK 格式 (例: 1288.HK)
        d3 = d.copy(); d3['Ticker'] = f"{t_clean.zfill(4)}.HK"; rows.append(d3)
    else:
        rows.append(d)

df_final = pd.DataFrame(rows).drop_duplicates(subset=['Ticker'])
df_final.to_csv("SCTR_Master.csv", index=False)
print(f"🎉【三重相容寫入完成】`SCTR_Master.csv` 現已包含 {len(df_final)} 筆全格式搜尋紀錄！")
