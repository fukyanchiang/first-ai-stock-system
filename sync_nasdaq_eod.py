"""
Filename: sync_nasdaq_eod.py
Description: 🏛️ 納斯達克 3,380 隻全量股票真實市寬 EOD 盤後計算引擎 (七層全維指標完全體)
"""

import time
import os
import pandas as pd
import numpy as np
import yfinance as yf

TARGET_COUNT = 3380

def get_nasdaq_3380_symbols():
    print("📡 正在向納斯達克官方 FTP 下載股票名冊...")
    url = "http://www.nasdaqtrader.com/dynamic/SymDir/nasdaqtraded.txt"
    try:
        df_sym = pd.read_csv(url, sep="|")
        df_clean = df_sym[(df_sym['Test Issue'] == 'N') & (df_sym['ETF'] == 'N')].copy()
        
        valid_symbols = [
            s.strip().replace('.', '-') for s in df_clean['Symbol'].dropna().tolist() 
            if s.isalpha() or ('-' in s and not any(c in s for c in ['$', '+', '=']))
        ]
        valid_symbols = sorted(list(set(valid_symbols)))
        selected_symbols = valid_symbols[:TARGET_COUNT] if len(valid_symbols) >= TARGET_COUNT else valid_symbols
        print(f"✅ 成功鎖定納斯達克股票總數：{len(selected_symbols)} 隻")
        return selected_symbols
    except Exception as e:
        print(f"⚠️ 無法下載官方名單 ({e})")
        return []

def run_nasdaq_eod_pipeline():
    symbols = get_nasdaq_3380_symbols()
    if not symbols:
        return

    chunk_size = 100
    total_chunks = (len(symbols) + chunk_size - 1) // chunk_size

    print(f"🚀 開始全量統計 3,380 隻七層樓真實指標 (分 {total_chunks} 批次下載)...")
    all_closes = []
    start_time = time.time()

    for i in range(total_chunks):
        chunk = symbols[i * chunk_size : (i + 1) * chunk_size]
        print(f"📦 正在下載第 {i+1}/{total_chunks} 批 ({len(chunk)} 隻)...", end="\r")
        try:
            data = yf.download(chunk, period="1y", interval="1d", auto_adjust=True, progress=False)
            if not data.empty and 'Close' in data:
                c = data['Close']
                if isinstance(c, pd.Series):
                    c = c.to_frame()
                all_closes.append(c)
        except Exception:
            pass
        time.sleep(1.0)

    if not all_closes:
        print("\n❌ 未能下載任何有效數據。")
        return

    print("\n\n📊 正在整合數據並計算七層樓真實量化指標...")
    df_all_closes = pd.concat(all_closes, axis=1)
    df_all_closes = df_all_closes.loc[:, ~df_all_closes.columns.duplicated()]
    df_all_closes = df_all_closes.dropna(how='all')

    actual_stocks = df_all_closes.shape[1]
    denom = max(actual_stocks, TARGET_COUNT)
    print(f"🏛️ 實際參與運算股票數：{actual_stocks} 隻 (基準: {TARGET_COUNT})")

    # 1. 20MA 與 50MA 真實市寬
    sma20 = df_all_closes.rolling(window=20, min_periods=5).mean()
    sma50 = df_all_closes.rolling(window=50, min_periods=10).mean()
    real_breadth_20 = ((df_all_closes > sma20).sum(axis=1) / denom) * 100.0
    real_breadth_50 = ((df_all_closes > sma50).sum(axis=1) / denom) * 100.0

    # 2. 52 週新高新低 (252 日窗口)
    high_252 = df_all_closes.rolling(window=252, min_periods=30).max()
    low_252 = df_all_closes.rolling(window=252, min_periods=30).min()
    new_highs = (df_all_closes >= high_252 * 0.995).sum(axis=1)
    new_lows = (df_all_closes <= low_252 * 1.005).sum(axis=1)
    net_nhnl = new_highs - new_lows

    # 3. 高低位 10% 存量 (Proximity Pools)
    near_high_counts = (df_all_closes >= high_252 * 0.90).sum(axis=1)
    near_low_counts = (df_all_closes <= low_252 * 1.10).sum(axis=1)
    near_high_rate = near_high_counts / denom
    near_low_rate = near_low_counts / denom

    # 4. 主力量能市寬 (上漲股票比例映射)
    pct_changes = df_all_closes.pct_change()
    up_stocks = (pct_changes > 0).sum(axis=1)
    down_stocks = (pct_changes < 0).sum(axis=1)
    tot_active = (up_stocks + down_stocks).replace(0, 1)
    up_vol_pct = ((up_stocks / tot_active) * 100.0).clip(5.0, 95.0)
    down_vol_pct = 100.0 - up_vol_pct

    # 5. 真實 VXN 與 AGI / SSI 多因子合成
    vxn_raw = yf.download("^VXN", period="1y", interval="1d", auto_adjust=True, progress=False)
    if not vxn_raw.empty and 'Close' in vxn_raw:
        vxn_s = vxn_raw['Close']
        if isinstance(vxn_s, pd.DataFrame):
            vxn_s = vxn_s.iloc[:, 0]
        vxn_aligned = vxn_s.reindex(df_all_closes.index).ffill().bfill()
    else:
        vxn_aligned = pd.Series(22.0, index=df_all_closes.index)

    fear_from_vxn = (50.0 - (vxn_aligned - 20.0) * 2.2).clip(5.0, 95.0)
    net_ratio_score = (50.0 + (net_nhnl / (TARGET_COUNT * 0.08)) * 50.0).clip(0.0, 100.0)
    score_scissors = (50.0 + (near_high_rate - near_low_rate) * 120.0).clip(0.0, 100.0)

    # AGI: 30% 均線趨勢 + 25% 存量剪刀差 + 25% 量能 + 20% 淨新高
    score_trend = (real_breadth_50 * 0.6 + real_breadth_20 * 0.4)
    real_agi_score = (score_trend * 0.30 + score_scissors * 0.25 + up_vol_pct * 0.25 + net_ratio_score * 0.20)
    real_agi_score = real_agi_score.rolling(3, min_periods=1).mean().clip(0.0, 100.0)

    # SSI: 40% 均線支撐 + 30% 高位集群 + 30% 買盤量能
    high_cluster = (near_high_rate * 200.0).clip(0.0, 100.0)
    real_ssi_score = (score_trend * 0.40 + high_cluster * 0.30 + up_vol_pct * 0.30).rolling(3, min_periods=1).mean().clip(0.0, 100.0)

    # 動態微彎通道
    roll_mean = real_agi_score.rolling(120, min_periods=20).mean().bfill()
    roll_std = real_agi_score.rolling(120, min_periods=20).std().fillna(15.0).clip(lower=10.0, upper=20.0)
    roll_mean_smooth = roll_mean.ewm(span=15).mean()
    roll_std_smooth = roll_std.ewm(span=15).mean()
    u2 = (roll_mean_smooth + 2.0 * roll_std_smooth).clip(upper=98.0)
    u1 = (roll_mean_smooth + 1.0 * roll_std_smooth).clip(upper=92.0)
    l1 = (roll_mean_smooth - 1.0 * roll_std_smooth).clip(lower=15.0)
    l2 = (roll_mean_smooth - 2.0 * roll_std_smooth).clip(lower=5.0)

    df_output = pd.DataFrame({
        "Date": df_all_closes.index.strftime('%Y-%m-%d'),
        "Total_Stocks": TARGET_COUNT,
        "Breadth_20": real_breadth_20.round(2),
        "Breadth_50": real_breadth_50.round(2),
        "New_Highs": new_highs.astype(int),
        "New_Lows": new_lows.astype(int),
        "Net_Highs": net_nhnl.astype(int),
        "Near_High_10Pct": near_high_counts.astype(int),
        "Near_Low_10Pct": near_low_counts.astype(int),
        "Up_Vol_Pct": up_vol_pct.round(1),
        "Down_Vol_Pct": down_vol_pct.round(1),
        "AGI_Score": real_agi_score.round(1),
        "SSI_Score": real_ssi_score.round(1),
        "Sentiment": real_agi_score.round(2),
        "Upper_2SD": u2.round(3),
        "Upper_1SD": u1.round(3),
        "Lower_1SD": l1.round(3),
        "Lower_2SD": l2.round(3)
    }).set_index("Date")

    csv_path = "nasdaq_macro_history.csv"
    df_output.to_csv(csv_path)
    print(f"\n🎉 納斯達克 3,380 隻全維度歷史庫儲存完成：{csv_path} (耗時: {(time.time() - start_time)/60:.1f} 分鐘)")

if __name__ == "__main__":
    run_nasdaq_eod_pipeline()