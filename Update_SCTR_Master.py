import pandas as pd
import yfinance as yf
import numpy as np
from datetime import datetime

def calculate_sctr_raw(df):
    if len(df) < 200: return 0
    C = df['Close']
    def EMA(s, n): return s.ewm(span=n, adjust=False).mean()
    def SMA(s, n, m=1): return s.ewm(alpha=m/n, adjust=False).mean()
    
    # 100% 原裝 StockCharts 算式
    LT_EMA = (C.iloc[-1] - EMA(C, 200).iloc[-1]) / EMA(C, 200).iloc[-1] * 100
    LT_ROC = (C.iloc[-1] / C.shift(125).bfill().iloc[-1] - 1) * 100
    MT_EMA = (C.iloc[-1] - EMA(C, 50).iloc[-1]) / EMA(C, 50).iloc[-1] * 100
    MT_ROC = (C.iloc[-1] / C.shift(20).bfill().iloc[-1] - 1) * 100
    
    PPO_Line = (EMA(C, 12) - EMA(C, 26)) / EMA(C, 26) * 100
    PPO_Sig = EMA(PPO_Line, 9)
    PPO_Hist = PPO_Line - PPO_Sig
    PPO_Slope = (PPO_Hist.iloc[-1] - PPO_Hist.shift(3).bfill().iloc[-1]) / 3
    
    LC = C.shift(1).bfill()
    DIFF_C = C - LC
    UP_RSI = np.where(DIFF_C > 0, DIFF_C, 0)
    ABS_RSI = DIFF_C.abs()
    RSI_VAL = SMA(pd.Series(UP_RSI, index=df.index), 14) / (SMA(pd.Series(ABS_RSI, index=df.index), 14) + 1e-5) * 100
    
    SCTR_RAW = (LT_EMA * 0.30) + (LT_ROC * 0.30) + (MT_EMA * 0.15) + (MT_ROC * 0.15) + (PPO_Slope * 0.05) + (RSI_VAL.iloc[-1] * 0.05)
    return SCTR_RAW

def main():
    print(f"🚀 [{datetime.now().strftime('%H:%M:%S')}] 啟動全宇宙 SCTR 排名更新程式...")
    
    # 讀取你的美股宇宙 (可自行加減檔案)
    csv_files = ["SP500_Equities.csv", "Market_Focus.csv", "Industry_Focus.csv", "US_ETFs.csv"]
    all_tickers = []
    
    for f in csv_files:
        try:
            df = pd.read_csv(f)
            col = [c for c in df.columns if c.lower() in ['ticker', 'symbol', '代號']][0]
            all_tickers.extend(df[col].dropna().astype(str).tolist())
        except:
            print(f"⚠️ 找不到檔案 {f}，跳過。")
            
    unique_tickers = list(set(all_tickers))
    unique_tickers = [t for t in unique_tickers if not t.endswith(".HK")] # 排除港股
    print(f"📦 成功集結 {len(unique_tickers)} 隻美股精華，準備下載數據...")
    
    data = yf.download(unique_tickers, period="1y", group_by='ticker', threads=True, progress=True)
    
    results = []
    for ticker in unique_tickers:
        try:
            df = data[ticker].dropna() if len(unique_tickers) > 1 else data.dropna()
            if len(df) >= 200:
                raw_score = calculate_sctr_raw(df)
                results.append({'Ticker': ticker, 'Raw_SCTR': raw_score})
        except: pass
        
    res_df = pd.DataFrame(results)
    if not res_df.empty:
        # 核心：轉化為 0.1 - 99.9 的百分位排名！
        res_df['SCTR_Rank'] = res_df['Raw_SCTR'].rank(pct=True) * 100
        res_df['SCTR_Rank'] = res_df['SCTR_Rank'].round(1).clip(0.1, 99.9)
        
        # 儲存字典檔案
        res_df[['Ticker', 'SCTR_Rank']].to_csv("SCTR_Master.csv", index=False)
        print(f"✅ 更新完成！已將 {len(res_df)} 隻股票排名寫入 SCTR_Master.csv！")
    else:
        print("❌ 運算失敗。")

if __name__ == "__main__":
    main()
