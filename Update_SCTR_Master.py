import os
import sys
import pandas as pd
import numpy as np
import yfinance as yf
from datetime import datetime

# ----------------------------------------------------
# 1. 配置與載入 4 大全宇宙 CSV 名單
# ----------------------------------------------------
CSV_FILES = {
    "HK_Equities": "HK_Equities_All.csv",
    "HK_ETFs": "HK_ETFs_All.csv",
    "US_Equities": "US_Equities_All.csv",
    "US_ETFs": "US_ETFs_All.csv"
}

def load_tickers_from_csv(file_path, category):
    if not os.path.exists(file_path):
        print(f"⚠️ 找不到檔案: {file_path}")
        return []
    
    try:
        df = pd.read_csv(file_path)
        possible_cols = ['Ticker', 'Symbol', 'Code', 'stock_code', 'ticker', 'symbol', 'code']
        found_col = None
        for col in df.columns:
            if col.strip().lower() in [c.lower() for c in possible_cols]:
                found_col = col
                break
        
        if not found_col:
            found_col = df.columns[0]
            
        tickers = df[found_col].dropna().astype(str).str.strip()
        
        # 自動為港股補上 .HK 後綴 (如果沒有的話)，確保 Yahoo Finance 能讀取
        if "HK" in category:
            tickers = tickers.apply(lambda x: f"{x.zfill(4)}.HK" if x.isdigit() else x)
            
        return tickers.tolist()
    except Exception as e:
        print(f"❌ 讀取 {file_path} 失敗: {e}")
        return []

# ----------------------------------------------------
# 2. SCTR 標準指標計算核心邏輯
# ----------------------------------------------------
def calculate_sctr_components(df):
    if len(df) < 200:
        return None
    
    close = df['Close']
    
    ema200 = close.ewm(span=200, adjust=False).mean()
    p_ema200 = ((close.iloc[-1] - ema200.iloc[-1]) / ema200.iloc[-1]) * 100
    
    roc125 = ((close.iloc[-1] - close.iloc[-125]) / close.iloc[-125]) * 100
    
    ema50 = close.ewm(span=50, adjust=False).mean()
    p_ema50 = ((close.iloc[-1] - ema50.iloc[-1]) / ema50.iloc[-1]) * 100
    
    roc20 = ((close.iloc[-1] - close.iloc[-20]) / close.iloc[-20]) * 100
    
    delta = close.diff()
    gain = (delta.where(delta > 0, 0)).rolling(window=14).mean()
    loss = (-delta.where(delta < 0, 0)).rolling(window=14).mean()
    rs = gain / (loss + 1e-9)
    rsi14 = 100 - (100 / (1 + rs))
    rsi_val = rsi14.iloc[-1]
    
    return {
        'Close': float(close.iloc[-1]),
        'p_ema200': float(p_ema200),
        'roc125': float(roc125),
        'p_ema50': float(p_ema50),
        'roc20': float(roc20),
        'rsi14': float(rsi_val)
    }

# ----------------------------------------------------
# 3. 批次下載與全宇宙 SCTR 計算主流程
# ----------------------------------------------------
def process_universe():
    print("🚀 啟動全宇宙 16,000+ 資產 SCTR 主更新引擎...")
    all_results = []
    
    for category, file_name in CSV_FILES.items():
        print(f"\n📂 讀取類別 [{category}] <- 檔案: {file_name}...")
        tickers = load_tickers_from_csv(file_name, category)
        print(f"✅ 成功載入 {len(tickers)} 隻標的代號")
        
        if not tickers:
            continue

        chunk_size = 200
        for i in range(0, len(tickers), chunk_size):
            chunk = tickers[i:i + chunk_size]
            print(f"⏳ [{category}] 下載進度: {i+1} ~ {min(i+chunk_size, len(tickers))} / {len(tickers)}...")
            
            try:
                # 將 period 改為 "2y"，確保獲取超過 200 天的數據
                data = yf.download(
                    chunk, 
                    period="2y", 
                    interval="1d", 
                    group_by='ticker', 
                    progress=False, 
                    threads=True
                )
                
                for ticker in chunk:
                    try:
                        if len(chunk) == 1:
                            df_t = data.copy()
                        else:
                            if ticker in data and not data[ticker].dropna(how='all').empty:
                                df_t = data[ticker].dropna(how='all')
                            else:
                                continue
                        
                        if 'Close' not in df_t:
                            continue
                            
                        clean_df = df_t.dropna(subset=['Close'])
                        if len(clean_df) < 200:
                            continue
                            
                        metrics = calculate_sctr_components(clean_df)
                        if metrics:
                            all_results.append({
                                'Ticker': ticker,
                                'Category': category,
                                'Close': metrics['Close'],
                                'p_ema200': metrics['p_ema200'],
                                'roc125': metrics['roc125'],
                                'p_ema50': metrics['p_ema50'],
                                'roc20': metrics['roc20'],
                                'rsi14': metrics['rsi14']
                            })
                    except Exception:
                        continue
            except Exception as e:
                print(f"⚠️ 批次下載發生異常: {e}")

    if not all_results:
        print("❌ 未能獲取任何有效數據，請檢查網絡或 CSV 代碼格式！")
        return

    df_all = pd.DataFrame(all_results)
    print(f"\n✅ 全宇宙數據抓取完成！成功處理 {len(df_all)} 隻資產。")

    # ----------------------------------------------------
    # 4. 按 Category 個別進行全宇宙 SCTR 百分位排名 (0 到 99.9 分)
    # ----------------------------------------------------
    print("🧮 正在計算 0 - 99.9 百分位 SCTR 綜合動能得分...")
    
    final_dfs = []
    for cat, group in df_all.groupby('Category'):
        group = group.copy()
        
        r_ema200 = group['p_ema200'].rank(pct=True) * 100
        r_roc125 = group['roc125'].rank(pct=True) * 100
        r_ema50  = group['p_ema50'].rank(pct=True) * 100
        r_roc20  = group['roc20'].rank(pct=True) * 100
        r_rsi14  = group['rsi14'].rank(pct=True) * 100
        
        group['SCTR'] = (
            r_ema200 * 0.30 +
            r_roc125 * 0.30 +
            r_ema50  * 0.15 +
            r_roc20  * 0.15 +
            r_rsi14  * 0.10
        ).round(2)
        
        final_dfs.append(group)
        
    df_final = pd.concat(final_dfs, ignore_index=True)
    df_final = df_final.sort_values(by=['Category', 'SCTR'], ascending=[True, False])
    
    output_file = "SCTR_Master.csv"
    df_final.to_csv(output_file, index=False)
    print(f"🎉【終極全宇宙 SCTR 運算完成】共 {len(df_final)} 隻資產排名成功！已覆蓋並寫入【{output_file}】！")

if __name__ == "__main__":
    process_universe()
