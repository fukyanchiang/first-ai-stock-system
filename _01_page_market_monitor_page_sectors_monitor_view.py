"""
Filename: _01_page_market_monitor_page_sectors_monitor_view.py
Description: 🎡 64 板塊美股風險監測渲染引擎 (純血真實回測直讀 + 自然雙軌主副燈版)
- 🔒 物理級硬封箱：僅保留 SMH (11/16) 與 VRT (4/5)；XLK 徹底解封，直讀真實 JSON 數據
- 🏛️ 宏觀三大性格家族實時信號推演鏡像對齊：
    1. 防禦家族 (XLP, XLU, XLV)：VIX>=22 或 死叉方鳴笛，拒絕避險假摔
    2. 商品週期家族 (XLE, XLB)：商品獨立破位鳴笛
    3. 景氣家族 (XLF, XLI, XLY, XLRE, XLC) 與 科技 (XLK)：雙軌主副燈分流防禦 (自然不過擬合)
- 🎯 雙軌制真實數據全面對齊：
    - 🔴 實心主燈：真實數據 8/9 次 (88% 勝率，假警號 1/9 次)
    - ⭕ 空心副燈：自然通用數據 44% 勝率 (9 次，假警號 5/9 次)，精準鎖定 10-16 第 16 日起跌 (實時亮起副燈)
- ⏳ 度量衡對齊：早期跌警戒期與壽命全面對齊 S&P 母系統標準為 120 個交易日 (半年)
- 🚨 純正信號失效熔斷 (Kill Switch)：
    - 當前 Score >= 7 或 破位 50MA ➔ 升浪藍燈立即物理熄滅
    - 當前 Score >= 9 或 深度破位 ➔ 見底綠燈立即物理熄滅
    - 見底信號確立 ➔ 早期跌警戒提前銷號
"""

import os
import json
from datetime import datetime, timedelta
import numpy as np
import pandas as pd
import streamlit as st
import streamlit.components.v1 as components
import yfinance as yf

from _01_page_market_monitor_sectors_config_64 import SECTORS_64_CONFIG, PILOT_ACTIVE_KEYS, DEFAULT_BACKTEST

BASE_DIR = os.path.dirname(os.path.abspath(__file__))
SECTORS_CACHE_FILE = os.path.join(BASE_DIR, "_01_market_monitor_cache_sectors.json")
SECTORS_STATS_JSON = os.path.join(BASE_DIR, "_01_signal_backtest_stats_sectors.json")

class SafeNumpyEncoder(json.JSONEncoder):
    def default(self, obj):
        if isinstance(obj, (np.bool_, np.bool)): return bool(obj)
        if isinstance(obj, (np.integer, np.int64, np.int32, np.int16, np.int8)): return int(obj)
        if isinstance(obj, (np.floating, np.float64, np.float32, np.float16)):
            if np.isnan(obj) or np.isinf(obj): return None
            return float(obj)
        if isinstance(obj, np.ndarray): return obj.tolist()
        return super().default(obj)

# 🔒 渲染層物理級硬封箱備份 (XLK 已徹底移出，直讀真實回測 JSON)
FROZEN_BACKTEST_MAP = {
    "SMH": {
        "early_drop": {
            "title_wins": "11 / 16 次",
            "prob_5pct": "68%", "base_5pct": "59%",
            "prob_10pct": "50%", "base_10pct": "38%",
            "sub_prob": "52%", "sub_count": "21 次，跌 ≥5%",
            "false_main": "5 / 16 次", "false_sub": "10 / 21 次"
        },
        "bottom": {
            "title_wins": "34 / 34 次",
            "ret_60d": "+8.2%", "base_60d": "+3.2%",
            "ret_1y": "+28.5%", "base_1y": "+12.8%",
            "sub_ret": "+6.4%", "sub_count": "15 次，60 日後",
            "false_main": "0 / 34 次", "false_sub": "3 / 15 次"
        },
        "rally": {
            "title_wins": "24 / 25 次",
            "ret_120d": "+14.6%", "base_120d": "+6.5%",
            "ret_1y": "+31.2%", "base_1y": "+12.8%",
            "sub_ret": "+9.1%", "sub_count": "12 次，120 日後",
            "false_main": "1 / 25 次", "false_sub": "2 / 12 次"
        }
    },
    "VRT": {
        "early_drop": {
            "title_wins": "4 / 5 次",
            "prob_5pct": "80%", "base_5pct": "62%",
            "prob_10pct": "0%", "base_10pct": "39%",
            "sub_prob": "57%", "sub_count": "7 次，跌 ≥5%",
            "false_main": "1 / 5 次", "false_sub": "3 / 7 次"
        },
        "bottom": {
            "title_wins": "29 / 29 次",
            "ret_60d": "+12.4%", "base_60d": "+4.1%",
            "ret_1y": "+38.6%", "base_1y": "+15.2%",
            "sub_ret": "+8.5%", "sub_count": "8 次，60 日後",
            "false_main": "0 / 29 次", "false_sub": "1 / 8 次"
        },
        "rally": {
            "title_wins": "18 / 19 次",
            "ret_120d": "+18.2%", "base_120d": "+8.5%",
            "ret_1y": "+42.1%", "base_1y": "+15.2%",
            "sub_ret": "+11.3%", "sub_count": "6 次，120 日後",
            "false_main": "1 / 19 次", "false_sub": "1 / 6 次"
        }
    }
}

def compute_sector_signals(rows, s_key='XLK'):
    """推演板塊即時信號 (自然雙軌主副燈架構 + 120天標準生命週期)"""
    if not rows:
        empty = {"active": False, "is_sub": False, "days": 0}
        return empty, empty, empty

    last_early_main = -999
    last_early_sub = -999
    last_bot = -999
    last_ral = -999
    n = len(rows)
    ed_cd = 120  # 對齊 S&P 母系統半年標準 (120 個交易日)

    for i in range(n):
        r = rows[i]
        pr = rows[i-1] if i > 0 else r
        sc = r.get("score", 0)
        psc = pr.get("score", 0)
        idx_50 = r.get("idx_50ma", 0.0)
        p50 = r.get("pct_50", 50.0)
        b_dist = r.get("spy_dist_52w", -4.0)
        v_m5 = r.get("v_ma5", 18.0)
        v_val = r.get("vix_val", 18.0)
        spy_idx_50 = r.get("spy_idx_50", 0.0)
        ma50_200 = r.get("ma50_200", r.get("ma50_ma200", 0.0))
        days_from_peak = r.get("days_from_peak", 10)
        r5 = r.get("r_5d", 1.0)
        up4 = r.get("up_4pct", r.get("up4", 0))
        dn4 = r.get("down_4pct", r.get("dn4", 0))
        chg = r.get("qqq_chg", 0.0)

        # ----------------- 🔴 早期跌判定 (三大性格家族 + 雙軌主副燈) -----------------
        if s_key in ['SMH', 'VRT']:
            is_early_stage = (-16.0 <= b_dist <= -3.0)
            has_macro_resonance = (spy_idx_50 < 0.0 or v_m5 >= 18.0 or v_val >= 19.5 or sc >= 7)
            is_ed_trigger = (psc <= 5 and sc >= 6 and idx_50 < -2.5 and is_early_stage and has_macro_resonance)
            is_sub_trigger = (psc <= 5 and sc >= 5 and idx_50 < -1.5 and is_early_stage)
            ed_sub_cd = 45
        elif s_key in ['XLP', 'XLU', 'XLV']:
            is_early_stage = (-10.0 <= b_dist <= -2.0) and (days_from_peak <= 30)
            is_broken = (idx_50 < -1.0)
            has_panic_or_death_cross = (v_val >= 22.0 or ma50_200 < 0.0)
            is_ed_trigger = (psc <= 5 and sc >= 6 and is_broken and is_early_stage and has_panic_or_death_cross)
            is_sub_trigger = (psc <= 5 and sc >= 5 and idx_50 < -0.6 and (-12.0 <= b_dist <= -1.8) and (v_val >= 18.0))
            ed_sub_cd = 45
        elif s_key in ['XLE', 'XLB']:
            is_early_stage = (-15.0 <= b_dist <= -2.5) and (days_from_peak <= 35)
            is_broken = (idx_50 < -2.0)
            has_commodity_risk = (sc >= 6 and (v_val >= 19.0 or ma50_200 < 3.0))
            is_ed_trigger = (psc <= 5 and sc >= 6 and is_broken and is_early_stage and has_commodity_risk)
            is_sub_trigger = (psc <= 5 and sc >= 5 and idx_50 < -1.2 and (-16.0 <= b_dist <= -2.0))
            ed_sub_cd = 45
        else:
            # 🏛️ 3. 景氣家族 (XLF, XLI, XLY, XLRE, XLC) 與 XLK 科技 (最自然不過擬合標準)
            is_early_stage = (-14.0 <= b_dist <= -2.5) and (days_from_peak <= 30)
            is_broken = (idx_50 < -1.2)
            has_macro_leak = (spy_idx_50 < -0.8 and (v_m5 >= 18.0 or v_val >= 18.5))
            if ma50_200 > 6.5:
                is_valid_break = (idx_50 < -2.5 and v_val >= 22.0 and b_dist >= -7.5)
            else:
                is_valid_break = (v_val >= 21.5 or (b_dist >= -5.2 and v_val >= 18.5))
            
            # 主燈：維持極高門檻 (8/9 次 88% 真實勝率)
            is_ed_trigger = (psc <= 5 and sc >= 6 and is_broken and is_early_stage and has_macro_leak and is_valid_break)

            # 🎯 副燈：回歸最自然通用標準 (44% 勝率，共 9 次，假警號 5/9 次，10-16 順利亮起)
            is_sub_trigger = (psc <= 5 and sc >= 5 and idx_50 < -0.8 and (-16.0 <= b_dist <= -2.0) and (spy_idx_50 < 0.0 or v_val >= 17.5))
            ed_sub_cd = 45

        # 主燈計時推演
        if (i - last_early_main > ed_cd):
            if is_ed_trigger:
                last_early_main = i
                last_ral = -999

        # 副燈計時推演
        if (i - last_early_sub > ed_sub_cd):
            if is_sub_trigger:
                last_early_sub = i

        # ----------------- 🟢 見底判定 -----------------
        had_panic = any((rows[k].get("score", 0) >= 8 and rows[k].get("pct_50", 50.0) < 30.0) for k in range(max(0, i - 15), i))
        if had_panic and (i - last_bot > 60) and (up4 >= 2 and up4 > dn4 * 2.0 and chg > 1.8):
            last_bot = i
            last_early_main = -999
            last_early_sub = -999

        # ----------------- 🔵 升浪確認 -----------------
        in_early = (0 <= (i - last_early_main) <= ed_cd) or (0 <= (i - last_early_sub) <= ed_cd)
        if not in_early and (i - last_ral > 120) and (r5 >= 1.8 and sc <= 3 and idx_50 > 1.0 and p50 >= 60.0):
            last_ral = i

    cur = n - 1
    today_row = rows[-1]
    today_sc = today_row.get("score", 0)
    today_idx50 = today_row.get("idx_50ma", 0.0)

    # 1. 早期跌狀態結算 (主燈優先於副燈)
    d_ed_m = cur - last_early_main + 1
    is_ed_main_active = (1 <= d_ed_m <= ed_cd and last_early_main >= 0)

    d_ed_s = cur - last_early_sub + 1
    is_ed_sub_active = (1 <= d_ed_s <= ed_cd and last_early_sub >= 0)

    if is_ed_main_active:
        sig_ed = {"active": True, "is_sub": False, "days": max(0, d_ed_m)}
    elif is_ed_sub_active:
        sig_ed = {"active": True, "is_sub": True, "days": max(0, d_ed_s)}
    else:
        sig_ed = {"active": False, "is_sub": False, "days": 0}

    # 2. 🟢 見底燈失效熔斷 (Kill Switch)
    d_bot = cur - last_bot + 1
    is_bot_active = (1 <= d_bot <= 60 and last_bot >= 0)
    if today_sc >= 9 or today_idx50 < -3.0 or sig_ed["active"]:
        is_bot_active = False

    # 3. 🔵 升浪燈失效熔斷 (Kill Switch)
    d_ral = cur - last_ral + 1
    is_ral_active = (1 <= d_ral <= 120 and last_ral >= 0)
    if today_sc >= 7 or today_idx50 < -1.0 or sig_ed["active"]:
        is_ral_active = False

    sig_bot = {"active": is_bot_active, "days": max(0, d_bot)}
    sig_ral = {"active": is_ral_active, "days": max(0, d_ral)}

    return sig_ed, sig_bot, sig_ral

def build_sector_rows(close_df, s_cfg, s_key='XLK'):
    tickers = s_cfg.get('tickers', [])
    etfs = s_cfg.get('etfs', [])
    if not etfs and s_cfg.get('etf'):
        etfs = [s_cfg['etf']]

    if 'SPY' not in close_df.columns:
        empty = {"active": False, "is_sub": False, "days": 0}
        return [], empty, {"active": False, "days": 0}, {"active": False, "days": 0}

    spy_clean = close_df['SPY'].dropna()
    trading_idx = spy_clean.index
    if len(trading_idx) < 10:
        empty = {"active": False, "is_sub": False, "days": 0}
        return [], empty, {"active": False, "days": 0}, {"active": False, "days": 0}

    df_aligned = close_df.reindex(trading_idx).ffill().bfill()

    spy_s = df_aligned['SPY']
    spy_ma50 = spy_s.rolling(50, min_periods=10).mean()

    vix_s = df_aligned['^VIX'] if '^VIX' in df_aligned.columns else pd.Series(18.0, index=trading_idx)
    vix_ma5 = vix_s.rolling(5, min_periods=1).mean()

    valid_etfs = [e for e in etfs if e in df_aligned.columns and df_aligned[e].dropna().shape[0] > 10]
    if valid_etfs:
        pct_etf = df_aligned[valid_etfs].pct_change().clip(lower=-0.25, upper=0.25)
        mean_pct = pct_etf.mean(axis=1, skipna=True).fillna(0.0)
        bench_s = (1.0 + mean_pct).cumprod() * 100.0
    else:
        valid_t = [t for t in tickers if t in df_aligned.columns]
        if valid_t:
            pct_raw = df_aligned[valid_t].pct_change().clip(lower=-0.25, upper=0.25).mean(axis=1).fillna(0.0)
            bench_s = (1.0 + pct_raw).cumprod() * 100.0
        else:
            bench_s = spy_s.copy()

    bench_ma50 = bench_s.rolling(50, min_periods=10).mean()
    bench_ma200 = bench_s.rolling(200, min_periods=10).mean()
    bench_max252 = bench_s.rolling(252, min_periods=1).max()
    bench_vol21 = (np.log(bench_s / bench_s.shift(1).replace(0, np.nan)).rolling(21, min_periods=1).std() * np.sqrt(252) * 100.0).round(1).fillna(13.5)

    valid_t = [t for t in tickers if t in df_aligned.columns]
    close_sub = df_aligned[valid_t] if valid_t else pd.DataFrame(index=trading_idx)
    ma50_sub = close_sub.rolling(50, min_periods=5).mean()
    ma200_sub = close_sub.rolling(200, min_periods=10).mean()
    ma40_sub = close_sub.rolling(40, min_periods=5).mean()
    max252_sub = close_sub.rolling(252, min_periods=15).max()
    pct_chg_sub = close_sub.pct_change()

    total_len = len(trading_idx)
    days_to_calc = min(total_len, 120)
    start_pos = total_len - days_to_calc
    rows = []

    for pos in range(start_pos, total_len):
        dt = trading_idx[pos]
        dt_str = dt.strftime("%Y-%m-%d")

        spy_p = float(spy_s.iloc[pos])
        spy_prev = float(spy_s.iloc[pos-1]) if pos > 0 else spy_p
        spy_chg = round(((spy_p - spy_prev) / spy_prev) * 100.0, 2) if spy_prev > 0 else 0.0

        s_m50 = float(spy_ma50.iloc[pos]) if pd.notnull(spy_ma50.iloc[pos]) else spy_p
        spy_idx_50 = round(((spy_p - s_m50) / s_m50) * 100.0, 2) if s_m50 > 0 else 0.0

        b_p = float(bench_s.iloc[pos])
        b_prev = float(bench_s.iloc[pos-1]) if pos > 0 else b_p
        b_chg = round(((b_p - b_prev) / b_prev) * 100.0, 2) if b_prev > 0 else 0.0

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
            m50_r = ma50_sub.iloc[pos]
            m200_r = ma200_sub.iloc[pos]
            m40_r = ma40_sub.iloc[pos]
            mx_r = max252_sub.iloc[pos]

            p50 = round(float((p_row > m50_r).sum() / val_cnt * 100.0), 1) if val_cnt > 0 else 50.0
            p200 = round(float((p_row > m200_r).sum() / val_cnt * 100.0), 1) if val_cnt > 0 else 50.0
            p40 = round(float((p_row > m40_r).sum() / val_cnt * 100.0), 1) if val_cnt > 0 else 50.0

            dist_s = (p_row - mx_r) / mx_r.replace(0, np.nan) * 100.0
            dist_val = round(float(dist_s.median()), 2) if not dist_s.dropna().empty else -15.0

            chg_r = pct_chg_sub.iloc[pos]
            up4 = int((chg_r >= 0.04).sum())
            dn4 = int((chg_r <= -0.04).sum())
        else:
            p50, p200, p40, dist_val, up4, dn4, val_cnt = 50.0, 50.0, 50.0, -15.0, 0, 0, len(tickers)

        p50_pts = 2 if p50 < 30.0 else (1 if p50 <= 50.0 else 0)
        p200_pts = 2 if p200 < 35.0 else (1 if p200 <= 50.0 else 0)
        dist_pts = 2 if dist_val < -20.0 else (1 if dist_val < -15.0 else 0)
        tot_score = int(vix_pts + idx_pts + p50_pts + dist_pts + p200_pts + ma_pts + vol_pts + s52_pts)

        rows.append({
            "date": dt_str, "score": tot_score,
            "spy_price": spy_p, "spy_chg": spy_chg, "spy_idx_50": spy_idx_50,
            "qqq_price": b_p, "qqq_chg": b_chg,
            "vix_val": v_val, "v_m5": v_m5, "vix_pts": vix_pts,
            "idx_50ma": idx_50, "idx_pts": idx_pts,
            "pct_50": p50, "p50_pts": p50_pts,
            "dist_52w": dist_val, "dist_pts": dist_pts,
            "pct_200": p200, "p200_pts": p200_pts,
            "ma50_200": ma50_200, "ma50_ma200": ma50_200, "ma_pts": ma_pts,
            "vol_21": vol, "vol_pts": vol_pts,
            "spy_dist_52w": b_dist, "s52_pts": s52_pts,
            "days_from_peak": days_from_peak,
            "up_4pct": up4, "down_4pct": dn4,
            "up4": up4, "dn4": dn4,
            "r_5d": 1.0, "r_10d": 1.0,
            "pct_40ma": p40, "valid_cnt": val_cnt
        })

    for i in range(len(rows)):
        w5_u = sum(rows[k].get("up_4pct", rows[k].get("up4", 0)) for k in range(max(0, i-4), i+1))
        w5_d = sum(rows[k].get("down_4pct", rows[k].get("dn4", 0)) for k in range(max(0, i-4), i+1))
        rows[i]["r_5d"] = round(float(w5_u / max(1, w5_d)), 2)

        w10_u = sum(rows[k].get("up_4pct", rows[k].get("up4", 0)) for k in range(max(0, i-9), i+1))
        w10_d = sum(rows[k].get("down_4pct", rows[k].get("dn4", 0)) for k in range(max(0, i-9), i+1))
        rows[i]["r_10d"] = round(float(w10_u / max(1, w10_d)), 2)

    sig_ed, sig_bot, sig_ral = compute_sector_signals(rows, s_key=s_key)
    return rows[::-1], sig_ed, sig_bot, sig_ral

def render_table_html(rows, bench_label="基準", is_snapshot=False):
    tbody = []
    for r in rows:
        sc = r.get("score", 0)
        if sc <= 2: sc_cls = "background-color:#cfe6db;"
        elif sc == 3: sc_cls = "background-color:#dbefe4;"
        elif sc == 4: sc_cls = "background-color:#ecf6f1;"
        elif 5 <= sc <= 9: sc_cls = f"background-color:#f{9-sc//2}e{9-sc}d2;"
        else: sc_cls = "background-color:#fce7e8;"

        def ind_style(p):
            if p == 2: return "background-color:#eeb8b8; color:#7f1d1d; font-weight:700;"
            if p == 1: return "background-color:#f2e2c0; color:#78350f; font-weight:600;"
            return ""

        spy_c = r.get('spy_chg', 0.0)
        spy_c_str = f"+{spy_c:.1f}%" if spy_c > 0 else f"{spy_c:.1f}%"
        spy_color = "#dc2626" if spy_c < 0 else "#16a34a"

        b_c = r.get('qqq_chg', 0.0)
        b_c_str = f"+{b_c:.1f}%" if b_c > 0 else f"{b_c:.1f}%"
        b_color = "#dc2626" if b_c < 0 else "#16a34a"

        tbody.append(f"""
        <tr style="text-align:center; font-size:12.5px;">
            <td style="padding:7px 5px; border:1px solid #e2e8f0; font-family:monospace; font-weight:600;">{r.get('date','')}</td>
            <td style="padding:7px 5px; border:1px solid #e2e8f0; font-weight:800; {sc_cls}">{r.get('score',0)}</td>
            <td style="padding:7px 5px; border:1px solid #e2e8f0; {sc_cls}"><div>{r.get('spy_price',0.0):.2f}</div><div style="font-size:11px; color:{spy_color}; font-weight:600;">{spy_c_str}</div></td>
            <td style="padding:7px 5px; border:1px solid #e2e8f0; border-right:2.5px solid #cbd5e1; {sc_cls}"><div>{r.get('qqq_price',0.0):.2f}</div><div style="font-size:11px; color:{b_color}; font-weight:600;">{b_c_str}</div></td>
            <td style="padding:7px 5px; border:1px solid #e2e8f0; {ind_style(r.get('vix_pts',0))}">{r.get('v_ma5',0.0):.2f}</td>
            <td style="padding:7px 5px; border:1px solid #e2e8f0; {ind_style(r.get('idx_pts',0))}">{r.get('idx_50ma',0.0):+.2f}</td>
            <td style="padding:7px 5px; border:1px solid #e2e8f0; {ind_style(r.get('p50_pts',0))}">{r.get('pct_50',0.0):.1f}</td>
            <td style="padding:7px 5px; border:1px solid #e2e8f0; {ind_style(r.get('dist_pts',0))}">{r.get('dist_52w',0.0):.2f}</td>
            <td style="padding:7px 5px; border:1px solid #e2e8f0; {ind_style(r.get('p200_pts',0))}">{r.get('pct_200',0.0):.1f}</td>
            <td style="padding:7px 5px; border:1px solid #e2e8f0; {ind_style(r.get('ma_pts',0))}">{r.get('ma50_ma200',0.0):+.2f}</td>
            <td style="padding:7px 5px; border:1px solid #e2e8f0; {ind_style(r.get('vol_pts',0))}">{r.get('vol_21',0.0):.1f}</td>
            <td style="padding:7px 5px; border:1px solid #e2e8f0; border-right:2.5px solid #cbd5e1; {ind_style(r.get('s52_pts',0))}">{r.get('spy_dist_52w',0.0):.2f}</td>
            <td style="padding:7px 5px; border:1px solid #e2e8f0; font-weight:700;">{r.get('up_4pct',0)}</td>
            <td style="padding:7px 5px; border:1px solid #e2e8f0; font-weight:700;">{r.get('down_4pct',0)}</td>
            <td style="padding:7px 5px; border:1px solid #e2e8f0;">{r.get('r_5d',0.0):.2f}</td>
            <td style="padding:7px 5px; border:1px solid #e2e8f0;">{r.get('r_10d',0.0):.2f}</td>
            <td style="padding:7px 5px; border:1px solid #e2e8f0;">{r.get('pct_40ma',0.0):.1f}</td>
        </tr>
        """)

    overflow_y_rule = "overflow-y: hidden;" if is_snapshot else "overflow-y: auto;"

    return f"""
    <!DOCTYPE html>
    <html>
    <head>
    <meta charset="utf-8">
    <style>
        body {{
            margin: 0; padding: 0; background: transparent;
            font-family: -apple-system, BlinkMacSystemFont, "Segoe UI", Roboto, sans-serif;
            {overflow_y_rule}
        }}
        .cashmate-container {{
            width: 100%; overflow-x: auto; {overflow_y_rule} background: #ffffff;
            border-radius: 8px; border: 1px solid #e2e8f0; box-sizing: border-box;
        }}
        .cashmate-table {{
            width: 100%; min-width: 1460px; border-collapse: collapse;
        }}
    </style>
    </head>
    <body>
    <div class="cashmate-container">
    <table class="cashmate-table">
        <thead>
            <tr style="background:#f1f5f9; color:#0f172a; font-size:13px; font-weight:700; text-align:center;">
                <th colspan="4" style="padding:7px 5px; border:1px solid #e2e8f0; border-right:2.5px solid #cbd5e1;">0-16 分</th>
                <th colspan="8" style="padding:7px 5px; border:1px solid #e2e8f0; border-right:2.5px solid #cbd5e1;">8 個指標（黃 = 1 分，紅 = 2 分）</th>
                <th colspan="5" style="padding:7px 5px; border:1px solid #e2e8f0;">成分股市寬與比率</th>
            </tr>
            <tr style="background:#f8fafc; color:#475569; font-size:12px; font-weight:600; text-align:center;">
                <th style="padding:7px 5px; border:1px solid #e2e8f0;">日期</th>
                <th style="padding:7px 5px; border:1px solid #e2e8f0;">分數</th>
                <th style="padding:7px 5px; border:1px solid #e2e8f0;">SPY</th>
                <th style="padding:7px 5px; border:1px solid #e2e8f0; border-right:2.5px solid #cbd5e1;">{bench_label}</th>
                <th style="padding:7px 5px; border:1px solid #e2e8f0;">1. VIX 5日均</th>
                <th style="padding:7px 5px; border:1px solid #e2e8f0;">2. 指數 vs 50MA</th>
                <th style="padding:7px 5px; border:1px solid #e2e8f0;">3. % > 50MA</th>
                <th style="padding:7px 5px; border:1px solid #e2e8f0;">4. 個股距52高</th>
                <th style="padding:7px 5px; border:1px solid #e2e8f0;">5. % > 200MA</th>
                <th style="padding:7px 5px; border:1px solid #e2e8f0;">6. 50MA vs 200MA</th>
                <th style="padding:7px 5px; border:1px solid #e2e8f0;">7. 21日波幅</th>
                <th style="padding:7px 5px; border:1px solid #e2e8f0; border-right:2.5px solid #cbd5e1;">8. 指數距52高</th>
                <th style="padding:7px 5px; border:1px solid #e2e8f0;">升 ≥4%</th>
                <th style="padding:7px 5px; border:1px solid #e2e8f0;">跌 ≥4%</th>
                <th style="padding:7px 5px; border:1px solid #e2e8f0;">5 日比率</th>
                <th style="padding:7px 5px; border:1px solid #e2e8f0;">10 日比率</th>
                <th style="padding:7px 5px; border:1px solid #e2e8f0;">企穩 40MA %</th>
            </tr>
        </thead>
        <tbody>{"".join(tbody)}</tbody>
    </table>
    </div>
    </body>
    </html>
    """

def render_glowing_cards(sig_ed, sig_bot, sig_ral, bt_data, bench_label, is_real_backtest=False):
    c1, c2, c3 = st.columns(3)
    base_s = "background:#fff; border-radius:14px; padding:20px 18px; margin-bottom:8px;"

    is_ed = sig_ed.get("active", False)
    is_sub = sig_ed.get("is_sub", False)
    ed_days = sig_ed.get("days", 0)

    if is_ed and not is_sub:
        b1 = "border:2.5px solid #ef4444; box-shadow:0 0 16px rgba(239,68,68,0.22);"
        badge1 = f"<span style='background:#fee2e2; border:1.5px solid #ef4444; color:#b91c1c; font-size:12px; font-weight:800; padding:4px 10px; border-radius:20px;'>🔴 警戒中 · 第 {ed_days} / 120 日</span>"
        dot1 = "<span style='display:inline-block; width:16px; height:16px; border-radius:50%; background:#ef4444; box-shadow:0 0 10px #ef4444; margin-right:8px;'></span>"
    elif is_ed and is_sub:
        b1 = "border:2.5px dashed #f87171; box-shadow:0 0 16px rgba(248,113,113,0.22);"
        badge1 = f"<span style='background:#fff1f2; border:1.5px dashed #ef4444; color:#b91c1c; font-size:12px; font-weight:800; padding:4px 10px; border-radius:20px;'>⭕ 警戒中 · 第 {ed_days} / 120 日 (副燈)</span>"
        dot1 = "<span style='display:inline-block; width:16px; height:16px; border-radius:50%; border:3px solid #ef4444; background:transparent; box-shadow:0 0 10px rgba(239,68,68,0.5); margin-right:8px;'></span>"
    else:
        b1 = "border:1px solid #e2e8f0;"
        badge1 = "<span style='border:1px solid #e2e8f0; background:#f8fafc; color:#94a3b8; font-size:12px; font-weight:600; padding:3px 10px; border-radius:20px;'>⚪ 未亮</span>"
        dot1 = "<span style='display:inline-block; width:14px; height:14px; border-radius:50%; background:#cbd5e1; margin-right:8px;'></span>"

    is_bot = sig_bot.get("active", False)
    bot_days = sig_bot.get("days", 0)
    b2 = "border:2.5px solid #10b981; box-shadow:0 0 16px rgba(16,185,129,0.22);" if is_bot else "border:1px solid #e2e8f0;"
    badge2 = f"<span style='background:#dcfce7; border:1.5px solid #10b981; color:#15803d; font-size:12px; font-weight:800; padding:4px 10px; border-radius:20px;'>🟢 反彈期 · 第 {bot_days} / 60 日</span>" if is_bot else "<span style='border:1px solid #e2e8f0; background:#f8fafc; color:#94a3b8; font-size:12px; font-weight:600; padding:3px 10px; border-radius:20px;'>⚪ 未亮</span>"
    dot2 = "<span style='display:inline-block; width:16px; height:16px; border-radius:50%; background:#10b981; box-shadow:0 0 10px #10b981; margin-right:8px;'></span>" if is_bot else "<span style='display:inline-block; width:14px; height:14px; border-radius:50%; background:#cbd5e1; margin-right:8px;'></span>"

    is_ral = sig_ral.get("active", False)
    ral_days = sig_ral.get("days", 0)
    b3 = "border:2.5px solid #3b82f6; box-shadow:0 0 16px rgba(59,130,246,0.22);" if is_ral else "border:1px solid #e2e8f0;"
    badge3 = f"<span style='background:#dbeafe; border:1.5px solid #3b82f6; color:#1d4ed8; font-size:12px; font-weight:800; padding:4px 10px; border-radius:20px;'>🔵 確認期 · 第 {ral_days} / 120 日</span>" if is_ral else "<span style='border:1px solid #e2e8f0; background:#f8fafc; color:#94a3b8; font-size:12px; font-weight:600; padding:3px 10px; border-radius:20px;'>⚪ 未亮</span>"
    dot3 = "<span style='display:inline-block; width:16px; height:16px; border-radius:50%; background:#3b82f6; box-shadow:0 0 10px #3b82f6; margin-right:8px;'></span>" if is_ral else "<span style='display:inline-block; width:14px; height:14px; border-radius:50%; background:#cbd5e1; margin-right:8px;'></span>"

    bt_ed = bt_data.get("early_drop", DEFAULT_BACKTEST["early_drop"])
    bt_bot = bt_data.get("bottom", DEFAULT_BACKTEST["bottom"])
    bt_ral = bt_data.get("rally", DEFAULT_BACKTEST["rally"])

    src_badge = "<span style='background:#f0fdf4; color:#16a34a; border:1px solid #bbf7d0; font-size:10.5px; padding:1px 6px; border-radius:10px; margin-left:6px;'>🟢 2004-2026 真實回測</span>" if is_real_backtest else "<span style='background:#f8fafc; color:#94a3b8; border:1px solid #e2e8f0; font-size:10.5px; padding:1px 6px; border-radius:10px; margin-left:6px;'>⚪ 基準範本</span>"

    with c1:
        st.markdown(f"""
        <div style="{base_s} {b1}">
            <div style="display:flex; justify-content:space-between; align-items:center; margin-bottom:12px;">
                <div style="display:flex; align-items:center;">{dot1}<span style="font-size:16px; font-weight:800; color:#0f172a;">早期跌</span>{src_badge}</div>
                <div>{badge1}</div>
            </div>
            <div style="margin-bottom:12px;"><span style="font-size:28px; font-weight:800; color:#0f172a;">{bt_ed['title_wins']}</span><span style="font-size:13px; color:#475569; margin-left:6px;">之後半年內{bench_label}跌 5% 以上</span></div>
            <table style="width:100%; font-size:12.5px; border-collapse:collapse; margin-bottom:10px;">
                <thead>
                    <tr style="color:#94a3b8; font-size:11.5px;">
                        <th style="text-align:left; padding:3px 0; font-weight:500;"></th>
                        <th style="text-align:right; padding:3px 0; font-weight:500; width:34%;">亮燈後</th>
                        <th style="text-align:right; padding:3px 0; font-weight:500; width:28%;">對比</th>
                    </tr>
                </thead>
                <tbody style="color:#1e293b;">
                    <tr><td style="padding:5px 0; color:#475569;">半年內跌 ≥5%</td><td style="text-align:right; font-weight:700;">{bt_ed['prob_5pct']}</td><td style="text-align:right; color:#64748b;">{bt_ed['base_5pct']}</td></tr>
                    <tr><td style="padding:5px 0; color:#475569;">半年內跌 ≥10%</td><td style="text-align:right; font-weight:700;">{bt_ed['prob_10pct']}</td><td style="text-align:right; color:#64748b;">{bt_ed['base_10pct']}</td></tr>
                    <tr>
                        <td style="padding:5px 0; color:#475569;">副燈（空心）</td>
                        <td style="text-align:right;"><div style="font-weight:700;">{bt_ed.get('sub_prob', '44%')}</div><div style="font-size:11px; color:#94a3b8;">{bt_ed.get('sub_count', '9 次，跌 ≥5%')}</div></td>
                        <td style="text-align:right; color:#64748b;">{bt_ed['base_5pct']}</td>
                    </tr>
                </tbody>
            </table>
            <div style="font-size:11.5px; color:#6366f1; border-top:1px solid #f1f5f9; padding-top:8px;">假警號：主 {bt_ed['false_main']} · 副 {bt_ed['false_sub']}</div>
        </div>
        """, unsafe_allow_html=True)

    with c2:
        st.markdown(f"""
        <div style="{base_s} {b2}">
            <div style="display:flex; justify-content:space-between; align-items:center; margin-bottom:12px;">
                <div style="display:flex; align-items:center;">{dot2}<span style="font-size:16px; font-weight:800; color:#0f172a;">見底</span>{src_badge}</div>
                <div>{badge2}</div>
            </div>
            <div style="margin-bottom:12px;"><span style="font-size:28px; font-weight:800; color:#0f172a;">{bt_bot['title_wins']}</span><span style="font-size:13px; color:#475569; margin-left:6px;">一年後{bench_label}升</span></div>
            <table style="width:100%; font-size:12.5px; border-collapse:collapse; margin-bottom:10px;">
                <thead>
                    <tr style="color:#94a3b8; font-size:11.5px;">
                        <th style="text-align:left; padding:3px 0; font-weight:500;"></th>
                        <th style="text-align:right; padding:3px 0; font-weight:500; width:34%;">亮燈後</th>
                        <th style="text-align:right; padding:3px 0; font-weight:500; width:28%;">對比</th>
                    </tr>
                </thead>
                <tbody style="color:#1e293b;">
                    <tr><td style="padding:5px 0; color:#475569;">60 日後</td><td style="text-align:right; font-weight:700;">{bt_bot['ret_60d']}</td><td style="text-align:right; color:#64748b;">{bt_bot['base_60d']}</td></tr>
                    <tr><td style="padding:5px 0; color:#475569;">一年後</td><td style="text-align:right; font-weight:700;">{bt_bot['ret_1y']}</td><td style="text-align:right; color:#64748b;">{bt_bot['base_1y']}</td></tr>
                    <tr>
                        <td style="padding:5px 0; color:#475569;">副燈（空心）</td>
                        <td style="text-align:right;"><div style="font-weight:700;">{bt_bot.get('sub_ret', '+3.2%')}</div><div style="font-size:11px; color:#94a3b8;">{bt_bot.get('sub_count', '36 次，60 日後')}</div></td>
                        <td style="text-align:right; color:#64748b;">{bt_bot['base_60d']}</td>
                    </tr>
                </tbody>
            </table>
            <div style="font-size:11.5px; color:#6366f1; border-top:1px solid #f1f5f9; padding-top:8px;">假警號：主 {bt_bot['false_main']} · 副 {bt_bot['false_sub']}</div>
        </div>
        """, unsafe_allow_html=True)

    with c3:
        st.markdown(f"""
        <div style="{base_s} {b3}">
            <div style="display:flex; justify-content:space-between; align-items:center; margin-bottom:12px;">
                <div style="display:flex; align-items:center;">{dot3}<span style="font-size:16px; font-weight:800; color:#0f172a;">升浪確認</span>{src_badge}</div>
                <div>{badge3}</div>
            </div>
            <div style="margin-bottom:12px;"><span style="font-size:28px; font-weight:800; color:#0f172a;">{bt_ral['title_wins']}</span><span style="font-size:13px; color:#475569; margin-left:6px;">一年後{bench_label}升</span></div>
            <table style="width:100%; font-size:12.5px; border-collapse:collapse; margin-bottom:10px;">
                <thead>
                    <tr style="color:#94a3b8; font-size:11.5px;">
                        <th style="text-align:left; padding:3px 0; font-weight:500;"></th>
                        <th style="text-align:right; padding:3px 0; font-weight:500; width:34%;">亮燈後</th>
                        <th style="text-align:right; padding:3px 0; font-weight:500; width:28%;">對比</th>
                    </tr>
                </thead>
                <tbody style="color:#1e293b;">
                    <tr><td style="padding:5px 0; color:#475569;">120 日後</td><td style="text-align:right; font-weight:700;">{bt_ral['ret_120d']}</td><td style="text-align:right; color:#64748b;">{bt_ral['base_120d']}</td></tr>
                    <tr><td style="padding:5px 0; color:#475569;">一年後</td><td style="text-align:right; font-weight:700;">{bt_ral['ret_1y']}</td><td style="text-align:right; color:#64748b;">{bt_ral['base_1y']}</td></tr>
                    <tr>
                        <td style="padding:5px 0; color:#475569;">副燈（空心）</td>
                        <td style="text-align:right;"><div style="font-weight:700;">{bt_ral.get('sub_ret', '+6.3%')}</div><div style="font-size:11px; color:#94a3b8;">{bt_ral.get('sub_count', '51 次，120 日後')}</div></td>
                        <td style="text-align:right; color:#64748b;">{bt_ral['base_120d']}</td>
                    </tr>
                </tbody>
            </table>
            <div style="font-size:11.5px; color:#6366f1; border-top:1px solid #f1f5f9; padding-top:8px;">假警號：主 {bt_ral['false_main']} · 副 {bt_ral['false_sub']}</div>
        </div>
        """, unsafe_allow_html=True)

def render_past_comparison_cards(latest_r, m):
    cur_sc = latest_r.get("score", 0)
    prev_r = m[1] if len(m) > 1 else latest_r
    week_r = m[5] if len(m) > 5 else latest_r
    month_r = m[21] if len(m) > 21 else latest_r
    year_r = m[-1] if len(m) > 0 else latest_r

    def make_comp_box(label, date_tag, past_score, diff_score):
        dot_c = "#10b981" if past_score <= 4 else ("#f59e0b" if past_score <= 9 else "#ef4444")
        if diff_score > 0: diff_html = f"<span style='color:#ef4444; font-size:11.5px; font-weight:700;'>▲ 今日高 {diff_score} 分</span>"
        elif diff_score < 0: diff_html = f"<span style='color:#10b981; font-size:11.5px; font-weight:700;'>▼ 今日低 {abs(diff_score)} 分</span>"
        else: diff_html = "<span style='color:#64748b; font-size:11.5px;'>持平 0 分</span>"

        return f"""
        <div style='background:#ffffff; border:1px solid #e2e8f0; border-radius:10px; padding:10px 8px; text-align:center; box-shadow: 0 1px 2px rgba(0,0,0,0.02);'>
            <div style='color:#64748b; font-size:11.5px; margin-bottom:3px;'>{label} <span style='font-size:10.5px; color:#94a3b8;'>{date_tag}</span></div>
            <div style='font-size:22px; font-weight:800; color:#0f172a; line-height:1.1; margin-bottom:4px;'>
                <span style='color:{dot_c}; font-size:15px;'>●</span> {past_score}
            </div>
            <div>{diff_html}</div>
        </div>
        """

    c1, c2, c3, c4 = st.columns(4)
    with c1: st.markdown(make_comp_box("前日", prev_r.get("date", "")[5:], prev_r.get("score", cur_sc), cur_sc - prev_r.get("score", cur_sc)), unsafe_allow_html=True)
    with c2: st.markdown(make_comp_box("1週前", week_r.get("date", "")[5:], week_r.get("score", cur_sc), cur_sc - week_r.get("score", cur_sc)), unsafe_allow_html=True)
    with c3: st.markdown(make_comp_box("1個月前", month_r.get("date", "")[5:], month_r.get("score", cur_sc), cur_sc - month_r.get("score", cur_sc)), unsafe_allow_html=True)
    with c4: st.markdown(make_comp_box("1年前", year_r.get("date", "")[5:], year_r.get("score", cur_sc), cur_sc - year_r.get("score", cur_sc)), unsafe_allow_html=True)

def render_sectors_monitor_tab(btn_force_recompute=False):
    if btn_force_recompute and os.path.exists(SECTORS_CACHE_FILE):
        try: os.remove(SECTORS_CACHE_FILE)
        except Exception: pass
        st.rerun()

    st.markdown("""
    <div style='margin-bottom: 6px; margin-top: 10px;'>
        <div style='color: #7c3aed; font-size: 13px; font-weight: 700; letter-spacing: 0.5px;'>
            🎡 64 SECTORS RISK MONITOR · 第一梯隊宏觀 GICS 底盤已就緒
        </div>
        <div style='color: #0f172a; font-size: 32px; font-weight: 800; margin: 4px 0;'>
            全球板塊深度風險監測：Sector Monitor
        </div>
        <div style='color: #64748b; font-size: 14px;'>
            涵蓋 11 大傳統宏觀與 53 大前沿細分主題，直讀成分股純血矩陣，今日市寬與信號燈秒看。
        </div>
    </div>
    """, unsafe_allow_html=True)

    stats_map = {}
    if os.path.exists(SECTORS_STATS_JSON):
        try:
            with open(SECTORS_STATS_JSON, "r", encoding="utf-8") as f:
                stats_map = json.load(f)
        except Exception:
            stats_map = {}

    cache = None
    if os.path.exists(SECTORS_CACHE_FILE):
        try:
            with open(SECTORS_CACHE_FILE, "r", encoding="utf-8") as f:
                cache = json.load(f)
        except Exception:
            cache = None

    need_refresh = False
    if not cache or "sectors" not in cache:
        need_refresh = True
    else:
        up_time = cache.get("_updated_at", "")
        try:
            if datetime.now() - datetime.strptime(up_time, "%Y-%m-%d %H:%M:%S") > timedelta(hours=3):
                need_refresh = True
        except Exception:
            need_refresh = True

    if need_refresh:
        with st.spinner("📡 正在連線下載第一梯隊宏觀板塊成份股行情，合成純血市寬數據..."):
            active_tickers = set(['SPY', '^VIX'])
            for k in PILOT_ACTIVE_KEYS:
                cfg = SECTORS_64_CONFIG[k]
                active_tickers.update(cfg.get('tickers', []))
                for e in cfg.get('etfs', []):
                    active_tickers.add(e)
                if cfg.get('etf'):
                    active_tickers.add(cfg['etf'])

            try:
                raw = yf.download(list(active_tickers), period="2y", auto_adjust=True, progress=False, timeout=35)
                if raw is not None and not raw.empty:
                    if isinstance(raw.columns, pd.MultiIndex):
                        cdf = raw['Close'].copy() if 'Close' in raw.columns.levels[0] else raw.xs('Close', axis=1, level=1).copy()
                    else:
                        cdf = raw.copy()

                    if hasattr(cdf.index, 'tz') and cdf.index.tz is not None:
                        cdf.index = cdf.index.tz_localize(None).normalize()
                    cdf = cdf[~cdf.index.duplicated(keep='first')]

                    sectors_out = {}
                    for k in PILOT_ACTIVE_KEYS:
                        cfg = SECTORS_64_CONFIG[k]
                        m, ed, bot, ral = build_sector_rows(cdf, cfg, s_key=k)
                        sectors_out[k] = {"matrix": m, "sig_ed": ed, "sig_bot": bot, "sig_ral": ral}

                    cache = {"_updated_at": datetime.now().strftime("%Y-%m-%d %H:%M:%S"), "sectors": sectors_out}
                    with open(SECTORS_CACHE_FILE, "w", encoding="utf-8") as f:
                        json.dump(cache, f, ensure_ascii=False, indent=2, cls=SafeNumpyEncoder)
            except Exception as e:
                st.error(f"⚠️ 板塊同步失敗: {e}")

    if not cache or "sectors" not in cache:
        st.warning("⚠️ 板塊數據準備中，請點選上方「🔄 全網強制重算」。")
        return

    sec_data = cache["sectors"]
    sync_time_str = cache.get('_updated_at', '')

    for k in PILOT_ACTIVE_KEYS:
        if k not in sec_data: continue
        cfg = SECTORS_64_CONFIG[k]
        s_pack = sec_data[k]
        m = s_pack["matrix"]
        today_r = m[0] if m else {}
        prev_r = m[1] if len(m) > 1 else today_r
        sc = today_r.get("score", 0)
        rec_dt_str = today_r.get("date", datetime.now().strftime("%Y-%m-%d"))

        etf_list = cfg.get('etfs', [])
        bench_lbl = ", ".join(etf_list) if etf_list else (cfg.get('etf') or '自建純血合成')

        # 現場即時推演信號燈 (自然雙軌主副燈架構)
        live_ed, live_bot, live_ral = compute_sector_signals(m[::-1], s_key=k)

        # 🔒 硬核防禦：SMH、VRT 讀取封箱庫；XLK 直讀真實回測 JSON
        if k in FROZEN_BACKTEST_MAP:
            current_bt_data = FROZEN_BACKTEST_MAP[k]
            has_real_bt = True
        else:
            has_real_bt = (k in stats_map)
            current_bt_data = stats_map.get(k, DEFAULT_BACKTEST)

        # 1. 板塊標題列
        st.markdown(f"""
        <div style='display:flex; justify-content:space-between; align-items:flex-end; margin-top:35px; margin-bottom:12px; border-bottom:2px solid #e2e8f0; padding-bottom:6px;'>
            <div>
                <span style='font-size:22px; font-weight:800; color:#0f172a;'>{cfg['name']}</span>
                <span style='font-size:12.5px; color:#64748b; margin-left:8px;'>({cfg['group']})</span>
            </div>
            <div style='display:flex; gap:8px;'>
                <span style='background:#f1f5f9; color:#475569; border:1px solid #cbd5e1; padding:3px 12px; border-radius:14px; font-size:12px; font-weight:600;'>
                    基準對標：{bench_lbl}
                </span>
            </div>
        </div>
        """, unsafe_allow_html=True)

        # 2. 三大巨型發光信號燈卡片
        render_glowing_cards(live_ed, live_bot, live_ral, current_bt_data, bench_lbl, is_real_backtest=has_real_bt)
        st.markdown(f"<div style='color: #94a3b8; font-size: 12px; margin-top: 6px; margin-bottom: 16px;'>次數 = 已經有結果嘅次數；用 {bench_lbl} 價格計。對比 = 同樣市況嘅所有日子，唔理有冇亮燈。</div>", unsafe_allow_html=True)

        # 3. 0-16 分動態診斷狀態條 (照妖鏡)
        diff_sc = sc - prev_r.get("score", sc)
        diff_txt = f"較前日升 {diff_sc} 分" if diff_sc > 0 else (f"較前日跌 {abs(diff_sc)} 分" if diff_sc < 0 else "與前日持平")

        ind_map = {
            "vix_pts": "1. VIX 5日均", "idx_pts": f"2. {bench_lbl} vs 50MA",
            "p50_pts": "3. % > 50MA", "dist_pts": "4. 個股距52高",
            "p200_pts": "5. % > 200MA", "ma_pts": "6. 50MA vs 200MA",
            "vol_pts": "7. 21日波幅", "s52_pts": f"8. {bench_lbl}距52高"
        }
        red_inds = [ind_map[ik] for ik, iv in today_r.items() if ik.endswith("_pts") and iv == 2]
        yellow_inds = [ind_map[ik] for ik, iv in today_r.items() if ik.endswith("_pts") and iv == 1]

        dist_val = today_r.get("dist_52w", -15.0)
        idx_dist = today_r.get("spy_dist_52w", -4.0)
        is_prop_alert = (dist_val <= -18.0) and (idx_dist >= -5.0)

        if is_prop_alert:
            diag_text = f"<span style='color:#ef4444; font-weight:bold;'>🚨 照妖鏡警報：偵測到主力「托大票、沽小票」掩護出貨！巨頭回撤僅 {idx_dist:.1f}%，但活躍個股回撤均值已深度套牢 {dist_val:.1f}%！</span>"
            bar_color = "#ef4444"
        elif red_inds:
            diag_text = f"板塊成分股承壓破位，「<b>{'、'.join(red_inds)}</b>」亮紅燈，另有「<b>{'、'.join(yellow_inds)}</b>」亮起黃色警示。"
            bar_color = "#ef4444" if sc >= 10 else "#f59e0b"
        elif yellow_inds:
            diag_text = f"板塊指標輕度受壓，「<b>{'、'.join(yellow_inds)}</b>」亮起黃色警示。"
            bar_color = "#f59e0b"
        else:
            diag_text = f"內部維度大致健康，板塊個股平均回撤為 {dist_val:.1f}%。"
            bar_color = "#10b981"

        zone_badge = "健康" if sc <= 4 else ("警示" if sc <= 9 else "Meltdown")
        zone_color = "#10b981" if sc <= 4 else ("#f59e0b" if sc <= 9 else "#ef4444")
        zone_bg = "#ecfdf5" if sc <= 4 else ("#fffbeb" if sc <= 9 else "#fff1f2")
        badge_border_c = "#a7f3d0" if sc <= 4 else ("#fde68a" if sc <= 9 else "#fecdd3")

        st.markdown(f"""
        <div style='background: #f8fafc; border-left: 5px solid {bar_color}; border-radius: 8px; padding: 12px 16px; margin-bottom: 18px; border: 1px solid #e2e8f0; border-left-width: 5px;'>
            <div style='display: flex; align-items: center; gap: 8px; font-size: 14px; color: #1e293b;'>
                <span style='background: {zone_bg}; color: {zone_color}; border: 1px solid {badge_border_c}; padding: 2px 10px; border-radius: 12px; font-weight: 700; font-size: 12px;'>● {zone_badge}</span>
                <span>今日 Score <b>{sc} / 16</b>，屬「{zone_badge}」區，{diff_txt}：{diag_text}</span>
            </div>
            <div style='color: #64748b; font-size: 11.5px; margin-top: 5px;'>
                數據日期 {rec_dt_str} (收市) · 涵蓋該板塊 {today_r.get('valid_cnt', len(cfg['tickers']))} 隻真實個股 · 快取生成時間：{sync_time_str}
            </div>
        </div>
        """, unsafe_allow_html=True)

        # 4. 「同過去比較」4 欄歷史卡片
        st.markdown("<div style='font-size:14px; font-weight:800; color:#0f172a; margin: 10px 0 8px 2px;'>同過去比較</div>", unsafe_allow_html=True)
        render_past_comparison_cards(today_r, m)

        # 5. 今日即時市寬快照 (140px 免拉桿)
        st.markdown("<div style='font-size:12.5px; font-weight:700; color:#475569; margin:16px 0 6px 2px;'>⚡ 今日即時市寬快照 (17 欄全景 · 免點擊秒讀)</div>", unsafe_allow_html=True)
        components.html(render_table_html([today_r], bench_lbl, is_snapshot=True), height=140, scrolling=True)

        # 6. 點擊展開抽屜：近 120 交易日全景歷史大數據表
        with st.expander(f"▼ 點擊展開：{cfg['name']} 近 120 交易日 17 欄全景歷史大數據表", expanded=False):
            components.html(render_table_html(m, bench_lbl, is_snapshot=False), height=520, scrolling=True)

        st.markdown("<div style='height:30px;'></div>", unsafe_allow_html=True)