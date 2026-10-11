import os
import pandas as pd
import numpy as np
import yfinance as yf

# 1. 讀取美股同港股所有 CSV 檔案
csv_files = [
    "SP500_Equities.csv",
    "Market_Focus.csv",
    "Industry_Focus.csv",
    "US_ETFs.csv",
    "hk_stock.csv",
    "hk_etf.csv"
]

all_tickers = []
for f in csv_files:
    if os.path.exists(f):
        try:
            df = pd.read_csv(f)
            col = [c for c in df.columns if c.lower() in ['ticker', 'symbol', '代號', 'code']][0]
            raw_list = df[col].dropna().astype(str).str.strip().tolist()
            if f in ['hk_stock.csv', 'hk_etf.csv']:
                # 港股格式化 (例如 700 變 0700.HK)
                formatted = [t.zfill(4) + ".HK" if not t.endswith(".HK") else t for t in raw_list]
                all_tickers.extend(formatted)
            else:
                all_tickers.extend(raw_list)
        except Exception as e:
            print(f"Error reading {f}: {e}")

all_tickers = sorted(list(set(all_tickers)))
print(f"📡 總共載入 {len(all_tickers)} 隻美股同港股標的進行 SCTR 全宇宙排名計算...")

def compute_sctr_raw(df):
    if df is None or len(df) < 150:
        return None
    try:
        C = df['Close']
        if isinstance(C, pd.DataFrame):
            C = C.iloc[:, 0]
        C = C.dropna()
        if len(C) < 150:
            return None
            
        def EMA(s, n): return s.ewm(span=n, adjust=False).mean()
        def SMA(s, n, m=1): return s.ewm(alpha=m/n, adjust=False).mean()
        
        LC = C.shift(1).bfill()
        DIFF_C = C - LC
        UP_RSI = np.where(DIFF_C > 0, DIFF_C, 0)
        ABS_RSI = DIFF_C.abs()
        RSI_VAL = SMA(pd.Series(UP_RSI, index=C.index), 14) / (SMA(pd.Series(ABS_RSI, index=C.index), 14) + 1e-5) * 100

        L_EMA200 = EMA(C, 200)
        L_EMA_D = (C - L_EMA200) / L_EMA200 * 100
        L_EMA_S = L_EMA_D * 1.5
        L_ROC_S = (C / C.shift(125).bfill() - 1) * 20

        M_EMA50 = EMA(C, 50)
        M_EMA_S = (C - M_EMA50) / M_EMA50 * 30
        M_ROC_S = (C / C.shift(20).bfill() - 1) * 30

        PPO_F = EMA(C, 12)
        PPO_S = EMA(C, 26)
        PPO_V = (PPO_F - PPO_S) / PPO_S * 100
        S_PPO_S = (PPO_V - PPO_V.shift(3).bfill()) * 5

        S_RSI_S = (RSI_VAL - 50) * 0.5

        S_TOTAL = (L_EMA_S + L_ROC_S + M_EMA_S + M_ROC_S + S_PPO_S + S_RSI_S)
        RAW_SCTR = (S_TOTAL / 10) + 50
        val = RAW_SCTR.iloc[-1]
        return float(val) if not np.isnan(val) else None
    except Exception as e:
        return None

# 2. 分批下載數據 (防止單次請求過大)
batch_size = 100
results = {}

for i in range(0, len(all_tickers), batch_size):
    batch = all_tickers[i:i + batch_size]
    print(f"⏳ 正在批次處理 {i+1} 至 {min(i+batch_size, len(all_tickers))}...")
    try:
        data = yf.download(batch, period="1y", group_by='ticker', progress=False, threads=True)
        for t in batch:
            try:
                if len(batch) == 1:
                    df_t = data
                else:
                    df_t = data[t] if t in data else None
                
                if df_t is not None and not df_t.empty:
                    score = compute_sctr_raw(df_t)
                    if score is not None:
                        results[t] = score
            except Exception as e:
                pass
    except Exception as e:
        print(f"Batch error: {e}")

print(f"✅ 成功計算 {len(results)} 隻資產的 SCTR 原始分數。")

# 3. 全宇宙 Percentile Rank (0.1 - 99.9) 排名結算
if results:
    sctr_series = pd.Series(results)
    ranked = (sctr_series.rank(pct=True) * 99.8 + 0.1).round(1)

    master_rows = []
    for ticker, rank_val in ranked.items():
        master_rows.append({'Ticker': ticker, 'SCTR_Rank': rank_val})
        # 港股自動備份無 .HK 版本 (例如 "0700.HK" 同時儲存 "0700")，雙重保險！
        if ticker.endswith(".HK"):
            clean_code = ticker.replace(".HK", "")
            master_rows.append({'Ticker': clean_code, 'SCTR_Rank': rank_val})

    master_df = pd.DataFrame(master_rows).drop_duplicates(subset=['Ticker'])
    master_df.to_csv("SCTR_Master.csv", index=False)
    print("🎉 SCTR_Master.csv 生成成功！包含美股與港股全宇宙排名！")
else:
    print("❌ 警告：沒有成功計算任何資產分數。")
