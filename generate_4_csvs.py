import pandas as pd
import requests

print("🚀 正在啟動全宇宙資產清單獲取引擎 (美股全量 + 港股/港股ETF全量擴展版)...")

# ==========================================================
# 1. 抓取美股個股 & 美股 ETF (NASDAQ 官方 FTP 伺服器)
# ==========================================================
print("\n🇺🇸 [1/2] 正在連線納斯達克官方伺服器下載全美股名單...")
nasdaq_ftp_url = "ftp://ftp.nasdaqtrader.com/SymbolDirectory/nasdaqtraded.txt"

try:
    df_us = pd.read_csv(nasdaq_ftp_url, sep='|')
    df_us = df_us[df_us['Test Issue'] == 'N'].dropna(subset=['Symbol'])
    df_us = df_us[~df_us['Symbol'].astype(str).str.contains(r'[\$\.\=]', regex=True)]
    
    # 1.1 分離美股 ETF
    us_etfs = df_us[df_us['ETF'] == 'Y'][['Symbol', 'Security Name']].copy()
    us_etfs.columns = ['Ticker', 'Name']
    us_etfs.to_csv("US_ETFs_All.csv", index=False)
    print(f"  ✅ 成功生成 【US_ETFs_All.csv】 (共 {len(us_etfs)} 隻美股 ETF)")

    # 1.2 分離美股 個股
    us_stocks = df_us[df_us['ETF'] == 'N'][['Symbol', 'Security Name']].copy()
    us_stocks.columns = ['Ticker', 'Name']
    us_stocks.to_csv("US_Equities_All.csv", index=False)
    print(f"  ✅ 成功生成 【US_Equities_All.csv】 (共 {len(us_stocks)} 隻美股個股)")

except Exception as e:
    print(f"❌ 美股下載失敗: {e}")

# ==========================================================
# 2. 抓取港股個股 & 港股 ETF (全量名單擴展)
# ==========================================================
print("\n🇭🇰 [2/2] 正在生成港股個股與港股 ETF 全量名單...")

# 2.1 港股個股 (全量 00001.HK - 03000.HK 覆蓋)
try:
    hk_stock_url = "https://raw.githubusercontent.com/fukyanchiang/my-cosmos-vision/refs/heads/main/hk_stock.csv"
    df_hk_base = pd.read_csv(hk_stock_url)
    col = [c for c in df_hk_base.columns if c.lower() in ['ticker', 'symbol', '代號', 'code']][0]
    base_tickers = df_hk_base[col].astype(str).str.strip().apply(lambda x: x.zfill(4) + ".HK" if not x.endswith(".HK") else x).tolist()

    expanded_hk = [f"{str(i).zfill(4)}.HK" for i in range(1, 3000)]
    all_hk_stocks = sorted(list(set(base_tickers + expanded_hk)))

    df_hk_all = pd.DataFrame({'Ticker': all_hk_stocks})
    df_hk_all.to_csv("HK_Equities_All.csv", index=False)
    print(f"  ✅ 成功生成全量 【HK_Equities_All.csv】 (共 {len(df_hk_all)} 隻港股標的)")

except Exception as e:
    print(f"❌ 港股個股擴展失敗: {e}")

# 2.2 港股 ETF (覆蓋所有港交所 ETF & 槓桿反向產品號碼段落)
try:
    hk_etf_url = "https://raw.githubusercontent.com/fukyanchiang/my-cosmos-vision/refs/heads/main/hk_etf.csv"
    df_hk_etf = pd.read_csv(hk_etf_url)
    col = [c for c in df_hk_etf.columns if c.lower() in ['ticker', 'symbol', '代號', 'code']][0]
    base_etfs = df_hk_etf[col].astype(str).str.strip().apply(lambda x: x.zfill(4) + ".HK" if not x.endswith(".HK") else x).tolist()

    # 港交所專用 ETF 及 槓桿/反向產品 號碼段落
    # 2800-2849, 3000-3199, 3400-3499, 7200-7399, 7500-7599
    expanded_etfs = []
    for i in range(2800, 2850): expanded_etfs.append(f"{str(i).zfill(4)}.HK")
    for i in range(3000, 3200): expanded_etfs.append(f"{str(i).zfill(4)}.HK")
    for i in range(3400, 3500): expanded_etfs.append(f"{str(i).zfill(4)}.HK")
    for i in range(7200, 7400): expanded_etfs.append(f"{str(i).zfill(4)}.HK")
    for i in range(7500, 7600): expanded_etfs.append(f"{str(i).zfill(4)}.HK")

    all_hk_etfs = sorted(list(set(base_etfs + expanded_etfs)))
    
    df_hk_etf_all = pd.DataFrame({'Ticker': all_hk_etfs})
    df_hk_etf_all.to_csv("HK_ETFs_All.csv", index=False)
    print(f"  ✅ 成功生成全量 【HK_ETFs_All.csv】 (共 {len(df_hk_etf_all)} 隻港股 ETF)")

except Exception as e:
    print(f"❌ 港股 ETF 獲取失敗: {e}")

print("\n🎉 全宇宙 4 大 CSV 檔案已全部自動生成完成！")