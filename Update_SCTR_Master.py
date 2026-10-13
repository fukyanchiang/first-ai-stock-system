import os
import sys
import pandas as pd
import numpy as np
import yfinance as yf
from datetime import datetime
import warnings
warnings.filterwarnings('ignore')

# 🎯 自動搜尋本地多個可能的 CSV 名單檔名 (優先使用全宇宙大名單)
CANDIDATE_FILES = {
    "HK_Equities": ["HK_Equities_All.csv", "hk_stock.csv", "HK_Equities.csv"],
    "HK_ETFs": ["HK_ETFs_All.csv", "hk_etf.csv", "HK_ETFs.csv"],
    "US_Equities": ["US_Equities_All.csv", "SP500_Equities.csv", "US_Equities.csv"],
    "US_ETFs": ["US_ETFs_All.csv", "US_ETFs.csv"]
}

def load_tickers_for_category(category):
    files = CANDIDATE_FILES.get(category, [])
    target_file = None
    for f in files:
        if os.path.exists(f):
            target_file = f
            break
            
    if not target_file:
        print(f"⚠️ 找不到 [{category}] 的本地 CSV 檔案 (已嘗試: {files})")
        return {}

    print(f"📂 載入 [{category}] 檔案: {target_file}")
    try:
        df = pd.read_csv(target_file, dtype=str)
        possible_cols = ['Ticker', 'Symbol', 'Code', 'stock_code', 'ticker', 'symbol', 'code']
        found_col = next((col for col in df.columns if col.strip().lower() in [c.lower() for c in possible_cols]), df.columns[0])
        
        raw_tickers = df[found_col].dropna().astype(str).str.strip().tolist()
        
        ticker_map = {}
        for t in raw_tickers:
            t_clean = t.replace('.0', '').strip()
            if not t_clean:
                continue
                
            dl_ticker = t_clean
            save_ticker = t_clean
            
            if "HK" in category:
                digits = ''.join(filter(str.isdigit, t_clean))
                if digits:
                    save_ticker = str(int(digits)) # 寫入純數字如 1919
                    
                    # 🛠️ Yahoo 4 位數字終極防呆轉換 (解決 06198 變 404 問題)
                    dl_ticker = f"{str(int(digits)).zfill(4)}.HK"
                elif not t_clean.endswith('.HK'):
                    dl_ticker = f"{t_clean}.HK"
                    save_ticker = t_clean.replace('.HK', '')
            
            ticker_map[dl_ticker] = save_ticker
            
        return ticker_map
    except Exception as e:
        print(f"❌ 讀取 {target_file} 失敗: {e}")
        return {}

def calculate_sctr(df):
    if df is None or len(df) < 200:
        return None
        
    if 'Close' not in df:
        return None
        
    # 🛡️ 核心防禦：展平多維度 Close 結構，根治 cannot convert series to float
    close = df['Close']
    if isinstance(close, pd.DataFrame):
        close = close.iloc[:, 0]
    close = pd.Series(close).dropna()
    
    if len(close) < 200:
        return None

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
        'Close': float(np.ravel(close)[-1]),
        'p_ema200': float(np.ravel(p_ema200)[-1]),
        'roc125': float(np.ravel(roc125)[-1]),
        'p_ema50': float(np.ravel(p_ema50)[-1]),
        'roc20': float(np.ravel(roc20)[-1]),
        'rsi14': float(np.ravel(rsi_val)[-1])
    }

# 雙向相容別名
calculate_sctr_components = calculate_sctr

def process_universe():
    print("🚀 啟動全宇宙資產 SCTR 主更新引擎...")
    all_results = []
    
    for category in CANDIDATE_FILES.keys():
        ticker_map = load_tickers_for_category(category)
        dl_tickers = list(ticker_map.keys())
        print(f"✅ 成功載入 [{category}] 共 {len(dl_tickers)} 隻標的")
        
        if not dl_tickers:
            continue

        chunk_size = 200
        for i in range(0, len(dl_tickers), chunk_size):
            chunk = dl_tickers[i:i + chunk_size]
            print(f"⏳ [{category}] 下載進度: {i+1} ~ {min(i+chunk_size, len(dl_tickers))} / {len(dl_tickers)}...")
            
            try:
                data = yf.download(chunk, period="2y", interval="1d", group_by='ticker', progress=False, threads=True)
                for dl_ticker in chunk:
                    save_ticker = ticker_map[dl_ticker]
                    try:
                        if len(chunk) == 1:
                            df_t = data.copy()
                        else:
                            if dl_ticker in data and not data[dl_ticker].dropna(how='all').empty:
                                df_t = data[dl_ticker].dropna(how='all')
                            else:
                                continue
                        
                        if 'Close' not in df_t:
                            continue
                            
                        clean_df = df_t.dropna(subset=['Close'])
                        if len(clean_df) < 200:
                            continue
                            
                        metrics = calculate_sctr(clean_df)
                        if metrics:
                            all_results.append({
                                'Ticker': save_ticker,
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
        print("❌ 未能獲取任何有效數據！")
        return

    df_all = pd.DataFrame(all_results)
    print("\n🧮 正在計算 0 - 99.9 百分位 SCTR 綜合動能得分...")
    
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
    df_final['Ticker'] = df_final['Ticker'].astype(str)

    # -------------------------------------------------------------
    # 🗄️ 讀取現有舊版 SCTR_Master.csv (同時供美股救援與昨日比對使用)
    # -------------------------------------------------------------
    old_master = None
    if os.path.exists("SCTR_Master.csv"):
        try:
            old_master = pd.read_csv("SCTR_Master.csv", dtype=str)
        except Exception as e:
            print(f"⚠️ 讀取現有 SCTR_Master.csv 失敗: {e}")

    # -------------------------------------------------------------
    # 🛡️ 1. 美股自動救援機制 (若網絡逾時導致美股缺失，自動讀取備份)
    # -------------------------------------------------------------
    has_us = df_final['Category'].str.startswith('US', na=False).any()
    if not has_us and old_master is not None and not old_master.empty:
        print("⚠️ 檢測到本次未計算出美股數據，正在從現有 SCTR_Master.csv 讀取美股備份...")
        old_us = old_master[old_master['Category'].str.startswith('US', na=False)]
        if not old_us.empty:
            df_final = pd.concat([df_final, old_us], ignore_index=True)
            print(f"✅ 成功救援並補回美股數據 {len(old_us)} 筆！")

    # -------------------------------------------------------------
    # 🇭🇰 2. 港股搜尋格式多重擴充 (支援 1288, 01288, 1288.HK 等多格式相容)
    # -------------------------------------------------------------
    rows = []
    for _, row in df_final.iterrows():
        d = row.to_dict()
        t = str(d['Ticker']).strip()
        cat = str(d.get('Category', '')).upper()
        rows.append(d)
        
        digits = ''.join(filter(str.isdigit, t))
        if digits and ('HK' in cat or 'HK' in t.upper()):
            d1 = d.copy(); d1['Ticker'] = str(int(digits)); rows.append(d1)
            d2 = d.copy(); d2['Ticker'] = digits.zfill(5); rows.append(d2)
            d3 = d.copy(); d3['Ticker'] = digits.zfill(4); rows.append(d3)

    df_final = pd.DataFrame(rows).drop_duplicates(subset=['Ticker', 'Category'])
    df_final['SCTR'] = pd.to_numeric(df_final['SCTR'], errors='coerce')
    df_final = df_final.sort_values(by=['Category', 'SCTR'], ascending=[True, False])

    # -------------------------------------------------------------
    # 📉 3. 昨日 SCTR 記憶與跌穿 90 偵測機制 (SCTR Breach-Down)
    # -------------------------------------------------------------
    if old_master is not None and not old_master.empty and 'SCTR' in old_master.columns:
        print("🔍 正在比對昨日 SCTR 分數，檢測動能跌穿 90 標的...")
        try:
            old_dict = {}
            for _, r in old_master.dropna(subset=['Ticker', 'SCTR']).iterrows():
                k = (str(r['Ticker']).strip(), str(r.get('Category', '')).strip())
                try:
                    old_dict[k] = float(r['SCTR'])
                except:
                    pass
            
            df_final['SCTR_Prev'] = df_final.apply(
                lambda r: old_dict.get((str(r['Ticker']).strip(), str(r.get('Category', '')).strip()), np.nan),
                axis=1
            )
            df_final['SCTR_Change'] = (df_final['SCTR'] - df_final['SCTR_Prev']).round(2)
            df_final['Cross_Down_90'] = (df_final['SCTR_Prev'] >= 90.0) & (df_final['SCTR'] < 90.0)
            
            drop_count = df_final[df_final['Cross_Down_90'] == True]['Ticker'].nunique()
            print(f"🚨 比對完成！今日全市場共偵測到 {drop_count} 隻標的自 90 分高檔跌穿！")
        except Exception as e:
            print(f"⚠️ 比對昨日 SCTR 失敗: {e}")
            df_final['SCTR_Prev'] = np.nan
            df_final['SCTR_Change'] = np.nan
            df_final['Cross_Down_90'] = False
    else:
        df_final['SCTR_Prev'] = np.nan
        df_final['SCTR_Change'] = np.nan
        df_final['Cross_Down_90'] = False

    # -------------------------------------------------------------
    # 🔒 4. 10,000 筆終極安全防護鎖 (筆數過少拒絕存檔)
    # -------------------------------------------------------------
    total_count = len(df_final)
    if total_count < 10000:
        print(f"❌ 終極安全防護啟動：計算結果僅 {total_count} 筆 (< 10,000)，疑似數據缺失！拒絕覆蓋存檔以保護資料庫。")
        return

    output_file = "SCTR_Master.csv"
    df_final.to_csv(output_file, index=False)
    print(f"\n🎉【終極全宇宙 SCTR 運算完成】共成功寫入 {total_count} 隻股票至【{output_file}】！")

if __name__ == "__main__":
    process_universe()
