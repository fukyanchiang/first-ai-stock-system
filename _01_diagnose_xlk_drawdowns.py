"""
Filename: _01_diagnose_xlk_drawdowns.py
Description: 🔬 XLK 22 年歷史病理診斷：抓出 2004-2026 所有跌逾 10% 的重大歷史事件
- 精確定位每一次大跌的頂部日期、底部日期、最大回撤幅度
- 打印起跌當天的 SPY 表現、VIX 數值、50MA 破位深度
"""

import yfinance as yf
import pandas as pd
import numpy as np

def main():
    print("=" * 70)
    print("🔬 啟動 XLK 2004-2026 歷史病理診斷：掃描所有 ≥ 10% 的大跌週期...")
    print("=" * 70)

    raw = yf.download(['XLK', 'SPY', '^VIX'], start="2004-01-01", auto_adjust=True, progress=False)
    close = raw['Close'] if isinstance(raw.columns, pd.MultiIndex) else raw

    xlk = close['XLK'].dropna()
    spy = close['SPY'].reindex(xlk.index).ffill()
    vix = close['^VIX'].reindex(xlk.index).ffill()

    # 計算 50MA 與回撤
    xlk_ma50 = xlk.rolling(50).mean()
    spy_ma50 = spy.rolling(50).mean()
    
    # 逐日找峰值與跌幅
    drawdowns = []
    in_dd = False
    peak_p, peak_dt = -1, None
    trough_p, trough_dt = 999999, None

    for i in range(len(xlk)):
        p = xlk.iloc[i]
        dt = xlk.index[i]

        if not in_dd:
            if p > peak_p:
                peak_p = p
                peak_dt = dt
            dd = (p - peak_p) / peak_p
            if dd <= -0.10: # 跌穿 10%，正式確認大調整
                in_dd = True
                trough_p = p
                trough_dt = dt
        else:
            if p < trough_p:
                trough_p = p
                trough_dt = dt
            
            # 從谷底反彈超過 10%，視為該輪跌浪結束
            if (p - trough_p) / trough_p >= 0.10:
                tot_drop = (trough_p - peak_p) / peak_p
                # 抓取跌穿 -3% 時的指標狀態 (早期)
                drawdowns.append({
                    "peak": peak_dt.strftime("%Y-%m-%d"),
                    "trough": trough_dt.strftime("%Y-%m-%d"),
                    "max_drop": f"{tot_drop * 100:.1f}%",
                    "trough_price": round(trough_p, 2),
                    "peak_price": round(peak_p, 2)
                })
                in_dd = False
                peak_p = p
                peak_dt = dt

    print(f"\n📊 22 年間共捕捉到 {len(drawdowns)} 次跌幅超過 10% 的重大歷史調整：\n")
    df_res = pd.DataFrame(drawdowns)
    print(df_res.to_string(index=False))
    print("\n" + "=" * 70)

if __name__ == "__main__":
    main()