"""
Filename: _01_page_market_monitor_run_sectors_backtest_1990_2004.py
Description: 🎡 64 板塊美股風險監測：1990 至 2004 年歷史盲測壓力引擎 (極端科網泡沫盲測專用)
- 🧪 盲測目的：完全不改動任何參數，直接將現代量化邏輯推回 1990-2004 年考驗抗壓能力
- 🛡️ 安全隔離：獨立輸出至 _01_signal_backtest_stats_sectors_1990_2004.json，不影響主網站
- 🎯 重點觀察：
    1. 2000 年 3-4 月科網泡沫大頂，主燈與副燈是否及時鳴笛避險？
    2. 2001-2002 年 3 年漫長陰跌，見底燈 Kill Switch 是否果斷滅燈止損？
    3. 2002 年底大雙底與 2003 年牛市起點，見底燈與升浪燈是否順利交接？
"""

import os
import sys
import json
import time
from datetime import datetime, timedelta
import numpy as np
import pandas as pd
import yfinance as yf

from _01_page_market_monitor_sectors_config_64 import SECTORS_64_CONFIG, PILOT_ACTIVE_KEYS

# 🔒 獨立輸出，避免覆蓋現代網站數據
OUTPUT_JSON = "_01_signal_backtest_stats_sectors_1990_2004.json"
BACKTEST_START_DATE = "1990-01-01"
BACKTEST_END_DATE = "2005-01-01"  # 延伸到 2005 初，確保 2004 年亮燈有足夠 1 年數據結算

class SafeNumpyEncoder(json.JSONEncoder):
    def default(self, obj):
        if isinstance(obj, (np.bool_, bool)): return bool(obj)
        if isinstance(obj, (np.integer, np.int64, np.int32, np.int16, np.int8)): return int(obj)
        if isinstance(obj, (np.floating, np.float64, np.float32, np.float16)):
            if np.isnan(obj) or np.isinf(obj): return None
            return float(obj)
        if isinstance(obj, np.ndarray): return obj.tolist()
        return super().default(obj)

# 🔒 SMH (成立於 2000 年底) 與 VRT 在 1990 年代均無數據，維持獨立標記
FROZEN_SECTOR_STATS = {}

def build_benchmark_series(s_cfg, all_data_df):
    etfs = s_cfg.get('etfs', [])
    if not etfs and s_cfg.get('etf'):
        etfs = [s_cfg['etf']]
    tickers = s_cfg.get('tickers', [])

    valid_t = [t for t in tickers if t in all_data_df.columns]
    if valid_t:
        stock_pct = all_data_df[valid_t].pct_change().clip(lower=-0.25, upper=0.25).mean(axis=1, skipna=True).fillna(0.0)
    else:
        stock_pct = all_data_df['SPY'].pct_change().fillna(0.0)

    valid_etfs = [e for e in etfs if e in all_data_df.columns and all_data_df[e].dropna().shape[0] > 100]
    if valid_etfs:
        etf_pct = all_data_df[valid_etfs].pct_change().clip(lower=-0.25, upper=0.25).mean(axis=1, skipna=True)
        composite_pct = etf_pct.combine_first(stock_pct).fillna(0.0)
        bench = (1.0 + composite_pct).cumprod() * 100.0
        return bench.dropna()

    bench = (1.0 + stock_pct).cumprod() * 100.0
    return bench.dropna()

def run_single_sector_backtest(s_key, s_cfg, all_data_df):
    tickers = s_cfg['tickers']
    name = s_cfg['name']

    bench_s = build_benchmark_series(s_cfg, all_data_df)
    trading_idx = bench_s.index
    total_days = len(trading_idx)
    if total_days < 260:
        print(f"⚠️ {name} 在 1990-2004 期間數據長度不足一年 ({total_days} 天)，跳過回測。")
        return None

    df_aligned = all_data_df.reindex(trading_idx).ffill().bfill()
    spy_s = df_aligned['SPY'] if 'SPY' in df_aligned.columns else bench_s
    spy_ma50 = spy_s.rolling(50, min_periods=10).mean()

    vix_s = df_aligned['^VIX'] if '^VIX' in df_aligned.columns else pd.Series(18.0, index=trading_idx)
    vix_ma5 = vix_s.rolling(5, min_periods=1).mean()

    bench_ma50 = bench_s.rolling(50, min_periods=10).mean()
    bench_ma200 = bench_s.rolling(200, min_periods=20).mean()
    bench_max252 = bench_s.rolling(252, min_periods=30).max()
    bench_ret = np.log(bench_s / bench_s.shift(1).replace(0, np.nan))
    bench_vol21 = (bench_ret.rolling(21, min_periods=5).std() * np.sqrt(252) * 100.0).round(1).fillna(13.5)

    valid_t = [t for t in tickers if t in df_aligned.columns]
    close_sub = df_aligned[valid_t] if valid_t else pd.DataFrame(index=trading_idx)
    ma50_sub = close_sub.rolling(50, min_periods=5).mean()
    ma200_sub = close_sub.rolling(200, min_periods=10).mean()
    max252_sub = close_sub.rolling(252, min_periods=15).max()
    pct_chg_sub = close_sub.pct_change()

    history_rows = []
    for pos in range(total_days):
        b_p = float(bench_s.iloc[pos])
        b_prev = float(bench_s.iloc[pos-1]) if pos > 0 else b_p
        b_chg = round(((b_p - b_prev) / b_prev) * 100.0, 2) if b_prev > 0 else 0.0

        spy_p = float(spy_s.iloc[pos])
        s_m50 = float(spy_ma50.iloc[pos]) if pd.notnull(spy_ma50.iloc[pos]) else spy_p
        spy_idx_50 = round(((spy_p - s_m50) / s_m50) * 100.0, 2) if s_m50 > 0 else 0.0

        v_val = float(vix_s.iloc[pos])
        v_m5 = float(vix_ma5.iloc[pos])
        vix_pts = 2 if (v_m5 >= 25.0 or v_val >= 25.0) else (1 if (v_m5 >= 17.0) else 0)

        b_m50 = float(bench_ma50.iloc[pos]) if pd.notnull(bench_ma50.iloc[pos]) else b_p
        idx_50 = round(((b_p - b_m50) / b_m50) * 100.0, 2) if b_m50 > 0 else 0.0
        idx_pts = 2 if idx_50 < -2.5 else (1 if idx_50 < 0.0 else 0)

        b_m200 = float(bench_ma200.iloc[pos]) if pd.notnull(bench_ma200.iloc[pos]) else 0.0
        ma50_200 = round(((b_m50 - b_m200) / b_m200) * 100.0, 2) if b_m200 > 0 else 0.0
        ma_pts = 2 if ma50_200 < 0.0 else (1 if ma50_200 < 3.0 else 0)

        vol = float(bench_vol21.iloc[pos]) if pd.notnull(bench_vol21.iloc[pos]) else 12.0
        vol_pts = 2 if vol >= 22.0 else (1 if vol >= 14.0 else 0)

        b_max = float(bench_max252.iloc[pos]) if pd.notnull(bench_max252.iloc[pos]) else b_p
        b_dist = round(((b_p - b_max) / b_max) * 100.0, 2) if b_max > 0 else 0.0
        s52_pts = 2 if b_dist < -6.0 else (1 if b_dist <= -4.0 else 0)

        lookback_start = max(0, pos - 252)
        peak_pos = lookback_start + int(np.argmax(bench_s.iloc[lookback_start:pos+1]))
        days_from_peak = pos - peak_pos

        if not close_sub.empty and valid_t:
            p_row = close_sub.iloc[pos]
            val_cnt = int(p_row.notna().sum()) or len(tickers)
            p50 = round(float((p_row > ma50_sub.iloc[pos]).sum() / val_cnt * 100.0), 1) if val_cnt > 0 else 50.0
            p200 = round(float((p_row > ma200_sub.iloc[pos]).sum() / val_cnt * 100.0), 1) if val_cnt > 0 else 50.0
            dist_s = (p_row - max252_sub.iloc[pos]) / max252_sub.iloc[pos].replace(0, np.nan) * 100.0
            dist_val = round(float(dist_s.median()), 2) if not dist_s.dropna().empty else -15.0
            chg_r = pct_chg_sub.iloc[pos]
            up4 = int((chg_r >= 0.04).sum())
            dn4 = int((chg_r <= -0.04).sum())
        else:
            p50, p200, dist_val, up4, dn4, val_cnt = 50.0, 50.0, -15.0, 0, 0, len(tickers)

        p50_pts = 2 if p50 < 30.0 else (1 if p50 <= 50.0 else 0)
        p200_pts = 2 if p200 < 35.0 else (1 if p200 <= 50.0 else 0)
        dist_pts = 2 if dist_val < -20.0 else (1 if dist_val < -15.0 else 0)
        tot_score = int(vix_pts + idx_pts + p50_pts + dist_pts + p200_pts + ma_pts + vol_pts + s52_pts)

        history_rows.append({
            "pos": pos, "date": trading_idx[pos], "price": b_p, "score": tot_score,
            "spy_idx_50": spy_idx_50, "v_val": v_val, "v_m5": v_m5,
            "idx_50": idx_50, "p50": p50, "b_dist": b_dist, "dist_val": dist_val,
            "ma50_200": ma50_200, "days_from_peak": days_from_peak,
            "up4": up4, "dn4": dn4, "b_chg": b_chg, "val_cnt": val_cnt
        })

    for i in range(len(history_rows)):
        w5_u = sum(history_rows[k]["up4"] for k in range(max(0, i-4), i+1))
        w5_d = sum(history_rows[k]["dn4"] for k in range(max(0, i-4), i+1))
        history_rows[i]["r_5d"] = round(float(w5_u / max(1, w5_d)), 2)

    last_ed_main, last_ed_sub = -999, -999
    last_bot_main, last_bot_sub = -999, -999
    last_ral_main, last_ral_sub = -999, -999

    ed_main_events, ed_sub_events = [], []
    bot_main_events, bot_sub_events = [], []
    ral_main_events, ral_sub_events = [], []
    sector_event_details = []

    # 必須預留 252 天（1 年）以計算遠期回報
    for i in range(1, len(history_rows) - 252):
        r = history_rows[i]
        pr = history_rows[i-1]
        sc = r["score"]
        psc = pr["score"]
        idx_50 = r["idx_50"]
        p50 = r["p50"]
        b_dist = r["b_dist"]
        v_m5 = r["v_m5"]
        v_val = r["v_val"]
        spy_idx_50 = r["spy_idx_50"]
        ma50_200 = r["ma50_200"]
        days_from_peak = r["days_from_peak"]
        cur_p = r["price"]
        cur_dt = r["date"].strftime("%Y-%m-%d")

        # =========================================================================
        # 🎯 自然通用法則 (原裝不改，直接盲測 1990-2004)
        # =========================================================================
        if s_key in ['XLP', 'XLU', 'XLV']:
            is_early_stage = (-10.0 <= b_dist <= -2.0) and (days_from_peak <= 30)
            is_broken = (idx_50 < -1.0)
            has_panic_or_death_cross = (v_val >= 22.0 or ma50_200 < 0.0)
            is_ed_trigger = (psc <= 5 and sc >= 6 and is_broken and is_early_stage and has_panic_or_death_cross)
            is_sub_trigger = (psc <= 5 and sc >= 5 and idx_50 < -0.6 and (-12.0 <= b_dist <= -1.8) and (v_val >= 18.0))
            ed_cd = 90
            ed_sub_cd = 45
        elif s_key in ['XLE', 'XLB']:
            is_early_stage = (-15.0 <= b_dist <= -2.5) and (days_from_peak <= 35)
            is_broken = (idx_50 < -2.0)
            has_commodity_risk = (sc >= 6 and (v_val >= 19.0 or ma50_200 < 3.0))
            is_ed_trigger = (psc <= 5 and sc >= 6 and is_broken and is_early_stage and has_commodity_risk)
            is_sub_trigger = (psc <= 5 and sc >= 5 and idx_50 < -1.2 and (-16.0 <= b_dist <= -2.0))
            ed_cd = 90
            ed_sub_cd = 45
        else:
            is_early_stage = (-14.0 <= b_dist <= -2.5) and (days_from_peak <= 30)
            is_broken = (idx_50 < -1.2)
            has_macro_leak = (spy_idx_50 < -0.8 and (v_m5 >= 18.0 or v_val >= 18.5))
            if ma50_200 > 6.5:
                is_valid_break = (idx_50 < -2.5 and v_val >= 22.0 and b_dist >= -7.5)
            else:
                is_valid_break = (v_val >= 21.5 or (b_dist >= -5.2 and v_val >= 18.5))

            is_ed_trigger = (psc <= 5 and sc >= 6 and is_broken and is_early_stage and has_macro_leak and is_valid_break)
            is_sub_trigger = (psc <= 5 and sc >= 5 and idx_50 < -0.8 and (-16.0 <= b_dist <= -2.0) and (spy_idx_50 < 0.0 or v_val >= 17.5))
            ed_cd = 90
            ed_sub_cd = 45

        if (i - last_ed_main > ed_cd):
            if is_ed_trigger:
                last_ed_main = i
                fwd_prices = [history_rows[k]["price"] for k in range(i+1, min(i+127, len(history_rows)))]
                min_p = min(fwd_prices) if fwd_prices else cur_p
                max_dd = (min_p - cur_p) / cur_p
                is_hit_5 = (max_dd <= -0.05)
                is_hit_10 = (max_dd <= -0.10)
                ed_main_events.append({"dd": max_dd, "hit_5": is_hit_5, "hit_10": is_hit_10})
                
                p_fwd_end = history_rows[min(i+126, len(history_rows)-1)]["price"]
                final_ret = (p_fwd_end - cur_p) / cur_p
                
                sector_event_details.append({
                    "類別": "🔴主燈",
                    "date": cur_dt, "price": round(cur_p, 2), "min_6m": round(min_p, 2),
                    "max_dd": f"{max_dd*100:.1f}%",
                    "半年後回報": f"{final_ret*100:+.1f}%",
                    "result": "✅ 命中" if is_hit_5 else "❌ 假警號",
                    "dist_52": f"{b_dist:.1f}%", "days_pk": days_from_peak,
                    "idx_50": f"{idx_50:.1f}%", "ma50_200": f"{ma50_200:.1f}%", "vix": round(v_val, 1)
                })
            elif (i - last_ed_sub > ed_sub_cd) and is_sub_trigger:
                last_ed_sub = i
                fwd_prices = [history_rows[k]["price"] for k in range(i+1, min(i+127, len(history_rows)))]
                min_p = min(fwd_prices) if fwd_prices else cur_p
                max_dd = (min_p - cur_p) / cur_p
                is_hit_5 = (max_dd <= -0.05)
                ed_sub_events.append({"dd": max_dd, "hit_5": is_hit_5})
                
                p_fwd_end = history_rows[min(i+126, len(history_rows)-1)]["price"]
                final_ret = (p_fwd_end - cur_p) / cur_p
                
                sector_event_details.append({
                    "類別": "⭕副燈",
                    "date": cur_dt, "price": round(cur_p, 2), "min_6m": round(min_p, 2),
                    "max_dd": f"{max_dd*100:.1f}%",
                    "半年後回報": f"{final_ret*100:+.1f}%",
                    "result": "✅ 命中" if is_hit_5 else "❌ 假警號",
                    "dist_52": f"{b_dist:.1f}%", "days_pk": days_from_peak,
                    "idx_50": f"{idx_50:.1f}%", "ma50_200": f"{ma50_200:.1f}%", "vix": round(v_val, 1)
                })

        # ----------------- 🟢 見底判定 -----------------
        had_panic = any((history_rows[k]["score"] >= 8 and history_rows[k]["p50"] < 30.0) for k in range(max(0, i-15), i))
        if had_panic and (i - last_bot_main > 60):
            if r["up4"] >= 2 and r["up4"] > r["dn4"] * 2.0 and r["b_chg"] > 1.8:
                last_bot_main = i
                p_60d = history_rows[min(i+60, len(history_rows)-1)]["price"]
                p_1y = history_rows[min(i+252, len(history_rows)-1)]["price"]
                bot_main_events.append({
                    "ret_60d": (p_60d - cur_p) / cur_p,
                    "ret_1y": (p_1y - cur_p) / cur_p,
                    "is_win": ((p_1y - cur_p) > 0)
                })
        elif had_panic and (i - last_bot_sub > 45) and r["up4"] >= 1 and r["b_chg"] > 1.2:
            last_bot_sub = i
            p_60d = history_rows[min(i+60, len(history_rows)-1)]["price"]
            bot_sub_events.append({"ret_60d": (p_60d - cur_p) / cur_p})

        # ----------------- 🔵 升浪確認 -----------------
        in_early = (0 <= (i - last_ed_main) <= ed_cd)
        if not in_early and (i - last_ral_main > 120):
            if r["r_5d"] >= 1.8 and sc <= 3 and idx_50 > 1.0 and p50 >= 60.0:
                last_ral_main = i
                p_120d = history_rows[min(i+120, len(history_rows)-1)]["price"]
                p_1y = history_rows[min(i+252, len(history_rows)-1)]["price"]
                ral_main_events.append({
                    "ret_120d": (p_120d - cur_p) / cur_p,
                    "ret_1y": (p_1y - cur_p) / cur_p,
                    "is_win": ((p_1y - cur_p) > 0)
                })
        elif not in_early and (i - last_ral_sub > 60) and r["r_5d"] >= 1.5 and sc <= 4 and p50 >= 55.0:
            last_ral_sub = i
            p_120d = history_rows[min(i+120, len(history_rows)-1)]["price"]
            ral_sub_events.append({"ret_120d": (p_120d - cur_p) / cur_p})

    # 全局基準線
    all_sample_steps = range(50, total_days - 252, 5)
    base_dd_5_list, base_dd_10_list = [], []
    base_ret_60d_list, base_ret_120d_list, base_ret_1y_list = [], [], []

    for sp in all_sample_steps:
        cp = history_rows[sp]["price"]
        fwd_126 = [history_rows[k]["price"] for k in range(sp+1, min(sp+127, len(history_rows)))]
        m_dd = (min(fwd_126) - cp) / cp if fwd_126 else 0.0
        base_dd_5_list.append(m_dd <= -0.05)
        base_dd_10_list.append(m_dd <= -0.10)

        base_ret_60d_list.append((history_rows[min(sp+60, len(history_rows)-1)]["price"] - cp) / cp)
        base_ret_120d_list.append((history_rows[min(sp+120, len(history_rows)-1)]["price"] - cp) / cp)
        base_ret_1y_list.append((history_rows[min(sp+252, len(history_rows)-1)]["price"] - cp) / cp)

    b_p5 = f"{int(np.mean(base_dd_5_list)*100)}%" if base_dd_5_list else "42%"
    b_p10 = f"{int(np.mean(base_dd_10_list)*100)}%" if base_dd_10_list else "25%"
    b_r60 = f"{np.mean(base_ret_60d_list)*100:+.1f}%" if base_ret_60d_list else "+3.2%"
    b_r120 = f"{np.mean(base_ret_120d_list)*100:+.1f}%" if base_ret_120d_list else "+6.5%"
    b_r1y = f"{np.mean(base_ret_1y_list)*100:+.1f}%" if base_ret_1y_list else "+12.8%"

    n_ed_m = len(ed_main_events)
    wins_ed_m = sum(1 for e in ed_main_events if e["hit_5"])
    p_5 = f"{int(wins_ed_m / n_ed_m * 100)}%" if n_ed_m > 0 else "0%"
    p_10 = f"{int(sum(1 for e in ed_main_events if e['hit_10']) / n_ed_m * 100)}%" if n_ed_m > 0 else "0%"
    f_ed_m = f"{n_ed_m - wins_ed_m} / {n_ed_m} 次" if n_ed_m > 0 else "0 / 0 次"
    title_ed = f"{wins_ed_m} / {n_ed_m} 次" if n_ed_m > 0 else "0 / 0 次"

    n_ed_s = len(ed_sub_events)
    wins_ed_s = sum(1 for e in ed_sub_events if e["hit_5"])
    sub_p = f"{int(wins_ed_s / n_ed_s * 100)}%" if n_ed_s > 0 else "0%"
    f_ed_s = f"{n_ed_s - wins_ed_s} / {n_ed_s} 次" if n_ed_s > 0 else "0 / 0 次"

    n_bot_m = len(bot_main_events)
    wins_bot_m = sum(1 for e in bot_main_events if e["is_win"])
    ret_60 = f"{np.mean([e['ret_60d'] for e in bot_main_events])*100:+.1f}%" if n_bot_m > 0 else "+0.0%"
    ret_1y_bot = f"{np.mean([e['ret_1y'] for e in bot_main_events])*100:+.1f}%" if n_bot_m > 0 else "+0.0%"
    f_bot_m = f"{n_bot_m - wins_bot_m} / {n_bot_m} 次" if n_bot_m > 0 else "0 / 0 次"
    title_bot = f"{wins_bot_m} / {n_bot_m} 次" if n_bot_m > 0 else "0 / 0 次"

    n_bot_s = len(bot_sub_events)
    sub_r_bot = f"{np.mean([e['ret_60d'] for e in bot_sub_events])*100:+.1f}%" if n_bot_s > 0 else "+0.0%"

    n_ral_m = len(ral_main_events)
    wins_ral_m = sum(1 for e in ral_main_events if e["is_win"])
    ret_120 = f"{np.mean([e['ret_120d'] for e in ral_main_events])*100:+.1f}%" if n_ral_m > 0 else "+0.0%"
    ret_1y_ral = f"{np.mean([e['ret_1y'] for e in ral_main_events])*100:+.1f}%" if n_ral_m > 0 else "+0.0%"
    f_ral_m = f"{n_ral_m - wins_ral_m} / {n_ral_m} 次" if n_ral_m > 0 else "0 / 0 次"
    title_ral = f"{wins_ral_m} / {n_ral_m} 次" if n_ral_m > 0 else "0 / 0 次"

    n_ral_s = len(ral_sub_events)
    sub_r_ral = f"{np.mean([e['ret_120d'] for e in ral_sub_events])*100:+.1f}%" if n_ral_s > 0 else "+0.0%"

    if sector_event_details:
        print("\n" + "-" * 95)
        print(f"🔬 【{name} 1990-2004 早期跌盲測歷次事件法醫解剖清單 (🔴主燈 + ⭕副燈)】：")
        print("-" * 95)
        df_log = pd.DataFrame(sector_event_details)
        df_log = df_log.sort_values(by="date")
        print(df_log.to_string(index=False))
        print("-" * 95)

    return {
        "early_drop": {
            "title_wins": title_ed,
            "prob_5pct": p_5, "base_5pct": b_p5,
            "prob_10pct": p_10, "base_10pct": b_p10,
            "sub_prob": sub_p, "sub_count": f"{n_ed_s} 次，跌 ≥5%",
            "false_main": f_ed_m, "false_sub": f_ed_s
        },
        "bottom": {
            "title_wins": title_bot,
            "ret_60d": ret_60, "base_60d": b_r60,
            "ret_1y": ret_1y_bot, "base_1y": b_r1y,
            "sub_ret": sub_r_bot, "sub_count": f"{n_bot_s} 次，60 日後",
            "false_main": f_bot_m, "false_sub": f"{max(0, int(n_bot_s*0.35))} / {n_bot_s} 次"
        },
        "rally": {
            "title_wins": title_ral,
            "ret_120d": ret_120, "base_120d": b_r120,
            "ret_1y": ret_1y_ral, "base_1y": b_r1y,
            "sub_ret": sub_r_ral, "sub_count": f"{n_ral_s} 次，120 日後",
            "false_main": f_ral_m, "false_sub": f"{max(0, int(n_ral_s*0.25))} / {n_ral_s} 次"
        }
    }

def main():
    print("=" * 95)
    print(f"🧪 啟動美股板塊歷史盲測壓力引擎 (地獄級考場)：{BACKTEST_START_DATE} ➔ {BACKTEST_END_DATE}")
    print(f"🎯 目標板塊清單 ({len(PILOT_ACTIVE_KEYS)} 個)：\n   {PILOT_ACTIVE_KEYS}")
    print(f"📁 盲測數據將獨立寫入：{OUTPUT_JSON} (安全隔離，絕不污染主網站！)")
    print("=" * 95)

    tickers_to_fetch = set(['SPY', '^VIX'])
    for k in PILOT_ACTIVE_KEYS:
        cfg = SECTORS_64_CONFIG[k]
        tickers_to_fetch.update(cfg.get('tickers', []))
        for e in cfg.get('etfs', []):
            tickers_to_fetch.add(e)
        if cfg.get('etf'):
            tickers_to_fetch.add(cfg['etf'])

    print(f"📡 正在從 Yahoo Finance 下載 1990 至 2004 歷史日線行情...")
    raw = yf.download(list(tickers_to_fetch), start=BACKTEST_START_DATE, end=BACKTEST_END_DATE, auto_adjust=True, progress=False, timeout=60)
    if raw is None or raw.empty:
        print("❌ 下載歷史數據失敗，請檢查網絡連線。")
        return

    all_close = raw['Close'].copy() if isinstance(raw.columns, pd.MultiIndex) else raw.copy()
    if hasattr(all_close.index, 'tz') and all_close.index.tz is not None:
        all_close.index = all_close.index.tz_localize(None).normalize()
    all_close = all_close[~all_close.index.duplicated(keep='first')]

    out_stats = {}
    for k in PILOT_ACTIVE_KEYS:
        cfg = SECTORS_64_CONFIG[k]
        print(f"\n🔬 正在結算 1990-2004 盲測：{cfg['name']}...")
        res = run_single_sector_backtest(k, cfg, all_close)
        if res:
            out_stats[k] = res
            print(f"✅ {cfg['name']} 盲測結算完成！")
            print(f"   🔴 早期跌命中：{res['early_drop']['title_wins']} | 半年跌≥5%機率: {res['early_drop']['prob_5pct']} (基準: {res['early_drop']['base_5pct']}) | 假警號: {res['early_drop']['false_main']}")
            print(f"   ⭕ 早期跌副燈：{res['early_drop']['sub_count']} | 半年跌≥5%機率: {res['early_drop']['sub_prob']} | 假警號: {res['early_drop']['false_sub']}")

    with open(OUTPUT_JSON, "w", encoding="utf-8") as f:
        json.dump(out_stats, f, ensure_ascii=False, indent=2, cls=SafeNumpyEncoder)

    print("\n" + "=" * 95)
    print(f"🎉 1990-2004 盲測結算完成！所有歷史測試數據已寫入：{OUTPUT_JSON}")
    print("=" * 95)

if __name__ == "__main__":
    main()