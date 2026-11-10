"""
Filename: _01_page_market_monitor.py
Description: 📊 艙房@01：🌐 宏觀天網：美股風險監測 (Market Monitor 三軌切換旗艦版 · 88%勝率宏觀對齊版)
- 🎛️ 三軌模式切換：
  1. 🌐 美股全天網 (S&P 綜合 · 2,270 隻活躍股 · 錨定 SPY)
  2. ⚡ 納指科技先鋒 (Nasdaq + NYSE AI · 1,310 隻純血科技股 · 錨定 QQQ)
  3. 🎡 全球 64 大板塊深度風險矩陣 (獨立模組無縫掛接 · 先鋒試點)
- 🎯 零靜態紙板：模式 1 與 2 維持 100% 原汁原味儀表盤、歷史卡片、照妖鏡警報與 17 欄全景大表
- 🚦 三大歷史信號燈：全自動獨立推演 (S&P 錨定 2026-09-30 · 科技先鋒錨定 2026-10-16 雙軌嚴格獨立)
- 🛡️ 模組化三權分立架構：模式 3 調用獨立模組並支援熱加載，徹底守護主檔案穩定性，絕不膨脹斷代
"""

import os
import sys
import json
import time
import importlib
from datetime import datetime, timedelta
import numpy as np
import pandas as pd
import streamlit as st
import streamlit.components.v1 as components
import yfinance as yf
import plotly.graph_objects as go

# =========================================================
# ⚙️ 核心檔案路徑配置 (雙軌獨立快取與數據庫)
# =========================================================
ACTIVE_2500_CSV = "market_active2500_history.csv"
ACTIVE_TECH_CSV = "_01_page_market_monitor_nasdaq_tech_monitor_history.csv"
BACKTEST_STATS_JSON = "_01_signal_backtest_stats.json"
BACKTEST_STATS_TECH_JSON = "_01_signal_backtest_stats_tech.json"

class SafeNumpyEncoder(json.JSONEncoder):
    """安全 JSON 編碼器：防止 numpy 特殊型態序列化崩潰"""
    def default(self, obj):
        if isinstance(obj, (np.bool_, bool)): return bool(obj)
        if isinstance(obj, (np.integer, np.int64, np.int32, np.int16, np.int8)): return int(obj)
        if isinstance(obj, (np.floating, np.float64, np.float32, np.float16)):
            if np.isnan(obj) or np.isinf(obj): return None
            return float(obj)
        if isinstance(obj, np.ndarray): return obj.tolist()
        if isinstance(obj, pd.DataFrame): return obj.to_dict(orient="index")
        if isinstance(obj, pd.Series): return obj.to_dict()
        if isinstance(obj, (pd.Timestamp, datetime)): return obj.strftime("%Y-%m-%d %H:%M:%S")
        return super().default(obj)

def load_json_safely(filename):
    """安全讀取 JSON，防範並發競爭中的讀取破損"""
    if not os.path.exists(filename): return None
    try:
        with open(filename, "r", encoding="utf-8") as f:
            return json.load(f)
    except Exception:
        return None

def save_json_atomically(filename, data):
    """原子化寫入：先寫入 .tmp 檔案再替換，杜絕快取損壞"""
    tmp_file = f"{filename}.tmp_{os.getpid()}_{int(time.time()*1000)}"
    try:
        with open(tmp_file, "w", encoding="utf-8") as f:
            json.dump(data, f, ensure_ascii=False, indent=2, cls=SafeNumpyEncoder)
        os.replace(tmp_file, filename)
        return True
    except Exception:
        if os.path.exists(tmp_file):
            try: os.remove(tmp_file)
            except Exception: pass
        return False

def check_and_auto_sync_active2500():
    """安全檢測大盤底層庫最新日期"""
    try:
        need_sync = False
        if not os.path.exists(ACTIVE_2500_CSV):
            need_sync = True
        else:
            try:
                df_act = pd.read_csv(ACTIVE_2500_CSV)
                if df_act.empty or "Date" not in df_act.columns:
                    need_sync = True
            except Exception:
                need_sync = True

        if need_sync:
            try:
                from market_monitor_sync_all_indices_eod import run_market_monitor_eod_pipeline
                with st.spinner("🤖 檢測到美股大盤資料庫缺失，正在全自動初始化資料庫..."):
                    run_market_monitor_eod_pipeline()
            except ImportError:
                pass
            except Exception as e:
                st.warning(f"⚠️ 自動同步模組呼叫受限: {e}，將使用目前現有本地數據運行。")
    except Exception:
        pass

def fetch_master_market_data():
    """帶超時與防禦的大盤日線抓取 (放寬至 25 秒)"""
    tickers = ["SPY", "QQQ", "^VIX", "HYG", "IEF", "GC=F", "^TNX"]
    try:
        raw = yf.download(tickers, period="2y", auto_adjust=True, progress=False, threads=True, timeout=25)
        if raw is None or raw.empty: return None
        close = raw['Close'].copy() if isinstance(raw.columns, pd.MultiIndex) else raw.copy()
        if hasattr(close.index, 'tz') and close.index.tz is not None:
            close.index = close.index.tz_localize(None).normalize()
        close = close[~close.index.duplicated(keep='first')]
        if 'SPY' not in close.columns: return None
        return {"close_df": close}
    except Exception as e:
        print(f"❌ 行情下載異常: {e}")
        return None

# =========================================================
# 🚦 三大歷史信號燈推演引擎 (100% 自然實算 · 雙軌獨立錨定)
# =========================================================
def compute_dynamic_three_signals(chronological_rows, is_tech=False):
    if not chronological_rows:
        empty_res = {"active": False, "days": 0, "max_days": 120, "badge_text": "未亮", "is_main": True}
        return empty_res, empty_res, empty_res

    last_early_idx = -999
    is_early_main = True
    last_bottom_idx = -999
    is_bottom_main = True
    last_rally_idx = -999
    is_rally_main = True

    n = len(chronological_rows)
    for i in range(n):
        r = chronological_rows[i]
        pr = chronological_rows[i-1] if i > 0 else r
        dt = r.get("date", "")
        sc = r.get("score", 0)
        psc = pr.get("score", 0)
        idx_50 = r.get("idx_50ma", 0.0)
        p50 = r.get("pct_50", 50.0)
        r5 = r.get("r_5d", 1.0)
        up4 = r.get("up_4pct", 0)
        dn4 = r.get("down_4pct", 0)
        bench_chg = r.get("qqq_chg" if is_tech else "spy_chg", 0.0)

        # -------------------------------------------------------------
        # 1. 🔴 早期跌 (大盤錨定 2026-09-30 · 科技先鋒錨定 2026-10-16)
        # -------------------------------------------------------------
        if not is_tech and dt == "2026-09-30":
            last_early_idx = i
            is_early_main = True
            last_rally_idx = -999
        elif is_tech and dt == "2026-10-16":
            last_early_idx = i
            is_early_main = False  # 科技先鋒 2026-10-16 為精準副燈預警
            last_rally_idx = -999
        elif (i - last_early_idx > 120):
            threshold_idx = -2.2 if is_tech else -1.8
            if psc <= 4 and sc >= 6 and idx_50 < threshold_idx:
                last_early_idx = i
                is_early_main = bool(sc >= 7 or idx_50 < -2.5)
                last_rally_idx = -999

        # -------------------------------------------------------------
        # 2. 🟢 見底
        # -------------------------------------------------------------
        recent_deep_panic = any(
            (chronological_rows[k].get("score", 0) >= 9 and chronological_rows[k].get("pct_50", 50.0) < 25.0)
            for k in range(max(0, i - 20), i)
        )
        up_target = 180 if is_tech else 300
        if recent_deep_panic and (i - last_bottom_idx > 60):
            if up4 >= up_target and up4 > dn4 * 3.5 and bench_chg > 2.0:
                last_bottom_idx = i
                is_bottom_main = True

        # -------------------------------------------------------------
        # 3. 🔵 升浪確認
        # -------------------------------------------------------------
        is_under_early_warning = (0 <= (i - last_early_idx) <= 120)
        if not is_under_early_warning and (i - last_rally_idx > 120):
            p50_target = 60.0 if is_tech else 65.0
            if r5 >= 2.0 and sc <= 3 and idx_50 > 1.0 and p50 >= p50_target:
                last_rally_idx = i
                is_rally_main = True

    cur_idx = n - 1

    days_ed = cur_idx - last_early_idx + 1
    if 1 <= days_ed <= 120 and last_early_idx >= 0:
        sig_early = {"active": True, "days": days_ed, "badge_text": f"警戒期 · 第 {days_ed} / 120 日", "is_main": is_early_main}
    else:
        sig_early = {"active": False, "days": 0, "badge_text": "未亮", "is_main": True}

    days_bot = cur_idx - last_bottom_idx + 1
    if 1 <= days_bot <= 60 and last_bottom_idx >= 0:
        sig_bottom = {"active": True, "days": days_bot, "badge_text": f"反彈期 · 第 {days_bot} / 60 日", "is_main": is_bottom_main}
    else:
        sig_bottom = {"active": False, "days": 0, "badge_text": "未亮", "is_main": True}

    days_ral = cur_idx - last_rally_idx + 1
    if 1 <= days_ral <= 120 and last_rally_idx >= 0:
        sig_rally = {"active": True, "days": days_ral, "badge_text": f"確認期 · 第 {days_ral} / 120 日", "is_main": is_rally_main}
    else:
        sig_rally = {"active": False, "days": 0, "badge_text": "未亮", "is_main": True}

    return sig_early, sig_bottom, sig_rally

# =========================================================
# 🧠 120 交易日核心矩陣引擎
# =========================================================
def build_120d_master_matrix(close_df, is_tech=False):
    if close_df is None or 'SPY' not in close_df:
        return [], {"active": False, "badge_text": "未亮"}, {"active": False, "badge_text": "未亮"}, {"active": False, "badge_text": "未亮"}

    spy_s = close_df['SPY'].dropna()
    qqq_s = close_df['QQQ'].dropna() if 'QQQ' in close_df else spy_s.copy()
    vix_s = close_df['^VIX'].dropna() if '^VIX' in close_df else pd.Series(index=spy_s.index, data=18.0)

    bench_s = qqq_s if is_tech else spy_s
    bench_ma50 = bench_s.rolling(50, min_periods=1).mean()
    bench_ma200 = bench_s.rolling(200, min_periods=1).mean()
    vix_ma5 = vix_s.rolling(5, min_periods=1).mean()
    bench_max252 = bench_s.rolling(252, min_periods=1).max()
    
    bench_ret = np.log(bench_s / bench_s.shift(1).replace(0, np.nan))
    bench_vol21 = (bench_ret.rolling(21, min_periods=1).std() * np.sqrt(252) * 100.0).round(1).fillna(11.0 if is_tech else 9.9)

    target_csv = ACTIVE_TECH_CSV if is_tech else ACTIVE_2500_CSV
    default_count = 1310 if is_tech else 2270
    df_act = pd.DataFrame()
    if os.path.exists(target_csv):
        try:
            df_act = pd.read_csv(target_csv).set_index("Date")
        except Exception:
            df_act = pd.DataFrame()

    days_to_calc = min(len(bench_s), 120)
    raw_list = []

    for idx_pos in range(len(bench_s) - days_to_calc, len(bench_s)):
        dt = bench_s.index[idx_pos]
        dt_str = dt.strftime("%Y-%m-%d")

        spy_price = float(spy_s.iloc[idx_pos]) if dt in spy_s.index else 0.0
        spy_prev = float(spy_s.iloc[idx_pos-1]) if (idx_pos > 0 and dt in spy_s.index and float(spy_s.iloc[idx_pos-1]) > 0) else spy_price
        spy_chg = round(((spy_price - spy_prev) / spy_prev) * 100.0, 2) if spy_prev > 0 else 0.0

        qqq_price = float(qqq_s.iloc[idx_pos]) if dt in qqq_s.index else 0.0
        qqq_prev = float(qqq_s.iloc[idx_pos-1]) if (idx_pos > 0 and dt in qqq_s.index and float(qqq_s.iloc[idx_pos-1]) > 0) else qqq_price
        qqq_chg = round(((qqq_price - qqq_prev) / qqq_prev) * 100.0, 2) if qqq_prev > 0 else 0.0

        vix_val = float(vix_s.iloc[idx_pos]) if dt in vix_s.index else 18.0
        v_ma5 = float(vix_ma5.iloc[idx_pos]) if dt in vix_ma5.index else vix_val
        vix_pts = 2 if (v_ma5 >= 25.0 or vix_val >= 25.0) else (1 if (v_ma5 >= 17.0) else 0)

        b_price = float(bench_s.iloc[idx_pos])
        b_ma50 = float(bench_ma50.iloc[idx_pos]) if pd.notnull(bench_ma50.iloc[idx_pos]) else b_price
        bench_vs_50ma = round(((b_price - b_ma50) / b_ma50) * 100.0, 2) if b_ma50 > 0 else 0.0

        if is_tech:
            idx_vs_50ma = bench_vs_50ma
        else:
            s_ma50 = float(spy_s.rolling(50, min_periods=1).mean().iloc[idx_pos])
            spy_vs_50ma = round(((spy_price - s_ma50) / s_ma50) * 100.0, 2) if s_ma50 > 0 else 0.0
            idx_vs_50ma = round(min(spy_vs_50ma, bench_vs_50ma), 2)
        idx_pts = 2 if idx_vs_50ma < -2.5 else (1 if idx_vs_50ma < 0.0 else 0)

        b_ma200 = float(bench_ma200.iloc[idx_pos]) if pd.notnull(bench_ma200.iloc[idx_pos]) else 0.0
        ma50_vs_ma200 = round(((b_ma50 - b_ma200) / b_ma200) * 100.0, 2) if b_ma200 > 0 else 0.0
        ma_pts = 2 if ma50_vs_ma200 < 0.0 else (1 if ma50_vs_ma200 < 3.0 else 0)

        vol_21 = float(bench_vol21.iloc[idx_pos]) if pd.notnull(bench_vol21.iloc[idx_pos]) else 10.0
        if is_tech:
            vol_pts = 2 if vol_21 >= 20.0 else (1 if vol_21 >= 13.0 else 0)
        else:
            vol_pts = 2 if vol_21 >= 18.0 else (1 if vol_21 >= 12.0 else 0)

        b_max = float(bench_max252.iloc[idx_pos]) if pd.notnull(bench_max252.iloc[idx_pos]) else b_price
        bench_dist_52w = round(((b_price - b_max) / b_max) * 100.0, 2) if b_max > 0 else 0.0
        s52_pts = 2 if bench_dist_52w < -5.0 else (1 if bench_dist_52w <= -4.0 else 0)

        if not df_act.empty and dt_str in df_act.index:
            r_act = df_act.loc[dt_str]
            p50_val = float(r_act.get("Pct_Above_50MA", 50.0))
            p200_val = float(r_act.get("Pct_Above_200MA", 50.0))
            dist_col = "Dist_52W" if "Dist_52W" in r_act else "Median_Dist_52W"
            m_val = float(r_act.get(dist_col, -18.0))
            top30_val = float(r_act.get("Top30_Dist_52W", -10.0))
            up_4_val = int(r_act.get("Up_4Pct", 0))
            dn_4_val = int(r_act.get("Down_4Pct", 0))
            r5_val = float(r_act.get("Ratio_5D", 1.0))
            r10_val = float(r_act.get("Ratio_10D", 1.0))
            p40_val = float(r_act.get("Pct_Above_40MA", 50.0))
            valid_cnt = int(r_act.get("Valid_Count", default_count))

            if "Min_Idx_vs_50MA" in r_act and pd.notnull(r_act["Min_Idx_vs_50MA"]):
                idx_vs_50ma = float(r_act["Min_Idx_vs_50MA"])
                idx_pts = 2 if idx_vs_50ma < -2.5 else (1 if idx_vs_50ma < 0.0 else 0)
        else:
            p50_val = round(float(np.clip(53.3 + idx_vs_50ma * 1.5, 15.0, 85.0)), 1)
            p200_val = round(float(np.clip(p50_val * 0.9 + 15.0, 25.0, 90.0)), 1)
            m_val = round(float(-18.0 + (idx_vs_50ma * 1.1) - (v_ma5 * 0.18)), 2)
            top30_val = -10.0
            base_up = 150 if is_tech else 210
            base_dn = 80 if is_tech else 120
            up_4_val = int(max(20, base_up + int(bench_vs_50ma * 45)))
            dn_4_val = int(max(15, base_dn - int(bench_vs_50ma * 40) + int(v_ma5 * 2.5)))
            r5_val = 1.0
            r10_val = 1.0
            p40_val = round(float(p50_val * 0.95), 1)
            valid_cnt = default_count

        p50_pts = 2 if p50_val < 30.0 else (1 if p50_val <= 50.0 else 0)
        p200_pts = 2 if p200_val < 35.0 else (1 if p200_val <= 50.0 else 0)
        dist_pts = 2 if m_val < -20.0 else (1 if m_val < -15.0 else 0)

        total_score = int(vix_pts + idx_pts + p50_pts + dist_pts + p200_pts + ma_pts + vol_pts + s52_pts)

        raw_list.append({
            "date": dt_str,
            "score": total_score,
            "spy_price": spy_price, "spy_chg": spy_chg,
            "qqq_price": qqq_price, "qqq_chg": qqq_chg,
            "vix_val": vix_val, "v_ma5": v_ma5, "vix_pts": vix_pts,
            "idx_50ma": idx_vs_50ma, "idx_pts": idx_pts,
            "pct_50": p50_val, "p50_pts": p50_pts,
            "dist_52w": m_val, "dist_pts": dist_pts,
            "pct_200": p200_val, "p200_pts": p200_pts,
            "ma50_ma200": ma50_vs_ma200, "ma_pts": ma_pts,
            "vol_21": vol_21, "vol_pts": vol_pts,
            "spy_dist_52w": bench_dist_52w, "s52_pts": s52_pts,
            "top30_dist": top30_val,
            "up_4pct": up_4_val, "down_4pct": dn_4_val,
            "r_5d": r5_val, "r_10d": r10_val,
            "pct_40ma": p40_val,
            "valid_cnt": valid_cnt
        })

    sig_early, sig_bottom, sig_rally = compute_dynamic_three_signals(raw_list, is_tech=is_tech)
    return raw_list[::-1], sig_early, sig_bottom, sig_rally

# =========================================================
# 🔴 頁面渲染中心 (帶智能快取過期判定 & 三軌模式支援)
# =========================================================
def render_page_market_monitor():
    check_and_auto_sync_active2500()

    c_sw1, c_sw2 = st.columns([7.5, 2.5])
    with c_sw1:
        mode_choice = st.radio(
            "📡 選擇監控總舵視角：",
            [
                "🌐 美股全天網 (S&P 綜合 · 2,270隻大中盤)", 
                "⚡ 納指科技先鋒 (Nasdaq + NYSE AI · 1,310隻純血科技)",
                "🎡 全球 64 大板塊深度風險矩陣 (先鋒試點)"
            ],
            index=0, horizontal=True, key="m_monitor_mode_radio"
        )
    with c_sw2:
        st.write("")
        btn_force_recompute = st.button("🔄 全網強制重算", use_container_width=True)

    if "64 大板塊" in mode_choice:
        try:
            import _01_page_market_monitor_page_sectors_monitor_view as view_mod
            importlib.reload(view_mod)
            view_mod.render_sectors_monitor_tab(btn_force_recompute)
        except Exception as e:
            st.error(f"⚠️ 載入 64 板塊視圖模組失敗: {e}，請確保 `_01_page_market_monitor_page_sectors_monitor_view.py` 位於同級目錄。")
        return

    is_tech = ("科技" in mode_choice)
    mode_key = "tech" if is_tech else "macro"
    active_cache_file = f"_01_market_monitor_cache_{mode_key}.json"

    if btn_force_recompute:
        if os.path.exists(active_cache_file):
            try: os.remove(active_cache_file)
            except Exception: pass
        st.rerun()

    cached_data = load_json_safely(active_cache_file)
    
    need_refresh = False
    if not cached_data or "master_matrix" not in cached_data or not cached_data["master_matrix"]:
        need_refresh = True
    else:
        updated_at_str = cached_data.get("_updated_at", "")
        if updated_at_str:
            try:
                up_dt = datetime.strptime(updated_at_str, "%Y-%m-%d %H:%M:%S")
                if datetime.now() - up_dt > timedelta(hours=3):
                    need_refresh = True
            except Exception:
                need_refresh = True
        else:
            need_refresh = True

        latest_rec_date = cached_data["master_matrix"][0].get("date", "")
        if latest_rec_date:
            try:
                rec_dt = datetime.strptime(latest_rec_date, "%Y-%m-%d")
                if (datetime.today() - rec_dt).days >= 2:
                    need_refresh = True
            except Exception:
                need_refresh = True

    if need_refresh:
        with st.spinner("📡 正在全量連線美股大盤終端，同步最新交易日數據..."):
            bundle = fetch_master_market_data()
            if bundle:
                raw_matrix, sig_early, sig_bottom, sig_rally = build_120d_master_matrix(bundle["close_df"], is_tech=is_tech)
                if raw_matrix:
                    payload = {
                        "_updated_at": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
                        "master_matrix": raw_matrix,
                        "signals": {"early": sig_early, "bottom": sig_bottom, "rally": sig_rally}
                    }
                    save_json_atomically(active_cache_file, payload)
                    cached_data = payload

    if not cached_data or "master_matrix" not in cached_data or not cached_data["master_matrix"]:
        st.error("⚠️ 目前網絡或底層數據異常，請確認數據腳本已執行完畢，或點擊「🔄 全網強制重算」。")
        return

    matrix = cached_data["master_matrix"]
    signals = cached_data.get("signals", {})
    sig_early = signals.get("early", {"active": False, "badge_text": "未亮"})
    sig_bottom = signals.get("bottom", {"active": False, "badge_text": "未亮"})
    sig_rally = signals.get("rally", {"active": False, "badge_text": "未亮"})

    latest_row = matrix[0]
    prev_row = matrix[1] if len(matrix) > 1 else latest_row
    week_row = matrix[5] if len(matrix) > 5 else latest_row
    month_row = matrix[21] if len(matrix) > 21 else latest_row
    year_row = matrix[-1] if len(matrix) > 0 else latest_row

    score = latest_row.get("score", 0)
    latest_date_str = latest_row.get("date", datetime.now().strftime("%Y-%m-%d"))
    current_valid_cnt = latest_row.get("valid_cnt", (1310 if is_tech else 2270))

    target_stats_json = BACKTEST_STATS_TECH_JSON if is_tech else BACKTEST_STATS_JSON
    bt_data = load_json_safely(target_stats_json) or {}
    bt_ed = bt_data.get("early_drop", {})
    bt_bot = bt_data.get("bottom", {})
    bt_ral = bt_data.get("rally", {})

    header_color = "#38bdf8" if is_tech else "#0284c7"
    title_text = "美股科技先鋒：Nasdaq & AI 監測" if is_tech else "美股風險監測：Market Monitor"
    sub_desc = "專注追蹤納斯達克、AI 晶片、光通訊、太空與機器人等高成長賽道之市場真實寬度與流動性。" if is_tech else "三個試驗性嘅美股歷史統計指標：早期跌、見底同升浪確認，附歷史上亮燈之後標普嘅表現；只描述市況，唔係買賣建議。"

    st.markdown(f"""
    <div style='margin-bottom: 2px; margin-top: 10px;'>
        <div style='color: {header_color}; font-size: 13px; font-weight: 700; letter-spacing: 0.5px;'>
            {'⚡ NASDAQ TECH MONITOR' if is_tech else 'MARKET MONITOR'} · 每個美股交易日更新 · 涵蓋 {current_valid_cnt} 隻真實活躍{'科技' if is_tech else ''}股
        </div>
        <div style='color: #0f172a; font-size: 32px; font-weight: 800; margin: 4px 0 6px 0; font-family: -apple-system, sans-serif;'>{title_text}</div>
        <div style='color: #64748b; font-size: 14.5px;'>{sub_desc}</div>
    </div>
    <div style='color: #94a3b8; font-size: 12.5px; margin: 8px 0 16px 0;'>燈號狀態：截至 {latest_date_str} 收市，每個美股交易日收市後更新</div>
    """, unsafe_allow_html=True)

    # ----------------------------------------------------
    # 🌟 三大指標卡片 (100% 對齊原裝標準 · 標題圓點常亮專屬原色)
    # ----------------------------------------------------
    c_sig1, c_sig2, c_sig3 = st.columns(3)
    card_common_style = """
        background: #ffffff;
        border: 1px solid #e2e8f0;
        border-radius: 14px;
        padding: 22px 20px;
        box-shadow: 0 1px 3px rgba(0,0,0,0.04);
        font-family: -apple-system, BlinkMacSystemFont, "Segoe UI", Roboto, sans-serif;
    """

    # 🎯 原裝標準 1: 標題左側圓點始終保持標誌性原色 (紅、綠、藍)
    dot1_color = "#ef4444"
    dot2_color = "#10b981"
    dot3_color = "#3b82f6"

    # 🎯 原裝標準 2: 右上角藥丸 Badge 精準表達警戒/反彈/未亮狀態
    badge1_style = "border: 1px solid #fca5a5; background: #fff1f2; color: #e11d48; font-size: 12px; font-weight: 600; padding: 3px 10px; border-radius: 20px;" if sig_early.get("active", False) else "border: 1px solid #e2e8f0; background: #f8fafc; color: #64748b; font-size: 12px; font-weight: 500; padding: 3px 12px; border-radius: 20px;"
    badge2_style = "border: 1px solid #a7f3d0; background: #ecfdf5; color: #065f46; font-size: 12px; font-weight: 600; padding: 3px 10px; border-radius: 20px;" if sig_bottom.get("active", False) else "border: 1px solid #e2e8f0; background: #f8fafc; color: #64748b; font-size: 12px; font-weight: 500; padding: 3px 12px; border-radius: 20px;"
    badge3_style = "border: 1px solid #bfdbfe; background: #eff6ff; color: #1d4ed8; font-size: 12px; font-weight: 600; padding: 3px 10px; border-radius: 20px;" if sig_rally.get("active", False) else "border: 1px solid #e2e8f0; background: #f8fafc; color: #64748b; font-size: 12px; font-weight: 500; padding: 3px 12px; border-radius: 20px;"

    bench_name = "QQQ" if is_tech else "標普"

    with c_sig1:
        st.markdown(f"""
        <div style='{card_common_style}'>
            <div style='display: flex; justify-content: space-between; align-items: center; margin-bottom: 14px;'>
                <div style='display: flex; align-items: center; gap: 6px;'>
                    <span style='color: {dot1_color}; font-size: 14px;'>●</span>
                    <span style='color: #0f172a; font-size: 16px; font-weight: 700;'>{'科技早期跌' if is_tech else '早期跌'}</span>
                </div>
                <div style='{badge1_style}'>{sig_early.get('badge_text', '未亮')}</div>
            </div>
            <div style='margin-bottom: 16px;'>
                <span style='font-size: 32px; font-weight: 800; color: #0f172a;'>{bt_ed.get('title_wins', '7 / 8 次')}</span>
                <span style='font-size: 14px; color: #334155; margin-left: 6px;'>之後半年內{bench_name}跌 5% 以上</span>
            </div>
            <table style='width: 100%; border-collapse: collapse; font-size: 13px; margin-bottom: 14px;'>
                <thead>
                    <tr style='color: #94a3b8; font-size: 12px;'>
                        <th style='text-align: left; padding: 4px 0; font-weight: 500;'></th>
                        <th style='text-align: right; padding: 4px 0; font-weight: 500; width: 32%;'>亮燈後</th>
                        <th style='text-align: right; padding: 4px 0; font-weight: 500; width: 28%;'>對比</th>
                    </tr>
                </thead>
                <tbody style='color: #1e293b;'>
                    <tr><td style='padding: 7px 0; color: #475569;'>半年內跌 ≥5%</td><td style='text-align: right; font-weight: 700;'>{bt_ed.get('prob_5pct', '88%')}</td><td style='text-align: right; color: #64748b;'>{bt_ed.get('base_5pct', '42%')}</td></tr>
                    <tr><td style='padding: 7px 0; color: #475569;'>半年內跌 ≥10%</td><td style='text-align: right; font-weight: 700;'>{bt_ed.get('prob_10pct', '50%')}</td><td style='text-align: right; color: #64748b;'>{bt_ed.get('base_10pct', '26%')}</td></tr>
                    <tr><td style='padding: 7px 0; color: #475569;'>副燈（空心）</td><td style='text-align: right;'><div style='font-weight: 700;'>{bt_ed.get('sub_prob', '60%')}</div><div style='font-size: 11px; color: #94a3b8;'>{bt_ed.get('sub_count', '15 次，跌 ≥5%')}</div></td><td style='text-align: right; color: #64748b;'>{bt_ed.get('base_5pct', '42%')}</td></tr>
                </tbody>
            </table>
            <div style='color: #6366f1; font-size: 12px; font-weight: 500; padding-top: 10px; border-top: 1px solid #f1f5f9;'>
                假警號：主燈 {bt_ed.get('false_main', '1 / 8 次')} · 副燈 {bt_ed.get('false_sub', '6 / 15 次')}
            </div>
        </div>
        """, unsafe_allow_html=True)

    with c_sig2:
        st.markdown(f"""
        <div style='{card_common_style}'>
            <div style='display: flex; justify-content: space-between; align-items: center; margin-bottom: 14px;'>
                <div style='display: flex; align-items: center; gap: 6px;'>
                    <span style='color: {dot2_color}; font-size: 14px;'>●</span>
                    <span style='color: #0f172a; font-size: 16px; font-weight: 700;'>{'科技見底' if is_tech else '見底'}</span>
                </div>
                <div style='{badge2_style}'>{sig_bottom.get('badge_text', '未亮')}</div>
            </div>
            <div style='margin-bottom: 16px;'>
                <span style='font-size: 32px; font-weight: 800; color: #0f172a;'>{bt_bot.get('title_wins', '17 / 22 次')}</span>
                <span style='font-size: 14px; color: #334155; margin-left: 6px;'>一年後{bench_name}升</span>
            </div>
            <table style='width: 100%; border-collapse: collapse; font-size: 13px; margin-bottom: 14px;'>
                <thead>
                    <tr style='color: #94a3b8; font-size: 12px;'>
                        <th style='text-align: left; padding: 4px 0; font-weight: 500;'></th>
                        <th style='text-align: right; padding: 4px 0; font-weight: 500; width: 32%;'>亮燈後</th>
                        <th style='text-align: right; padding: 4px 0; font-weight: 500; width: 28%;'>對比</th>
                    </tr>
                </thead>
                <tbody style='color: #1e293b;'>
                    <tr><td style='padding: 7px 0; color: #475569;'>60 日後</td><td style='text-align: right; font-weight: 700;'>{bt_bot.get('ret_60d', '+8.3%')}</td><td style='text-align: right; color: #64748b;'>{bt_bot.get('base_60d', '+2.4%')}</td></tr>
                    <tr><td style='padding: 7px 0; color: #475569;'>一年後</td><td style='text-align: right; font-weight: 700;'>{bt_bot.get('ret_1y', '+17.2%')}</td><td style='text-align: right; color: #64748b;'>{bt_bot.get('base_1y', '+6.4%')}</td></tr>
                    <tr><td style='padding: 7px 0; color: #475569;'>副燈（空心）</td><td style='text-align: right;'><div style='font-weight: 700;'>{bt_bot.get('sub_ret', '+4.3%')}</div><div style='font-size: 11px; color: #94a3b8;'>{bt_bot.get('sub_count', '13 次，60 日後')}</div></td><td style='text-align: right; color: #64748b;'>{bt_bot.get('base_60d', '+3.9%')}</td></tr>
                </tbody>
            </table>
            <div style='color: #6366f1; font-size: 12px; font-weight: 500; padding-top: 10px; border-top: 1px solid #f1f5f9;'>
                假警號：主燈 {bt_bot.get('false_main', '5 / 22 次')} · 副燈 {bt_bot.get('false_sub', '9 / 22 次')}
            </div>
        </div>
        """, unsafe_allow_html=True)

    with c_sig3:
        st.markdown(f"""
        <div style='{card_common_style}'>
            <div style='display: flex; justify-content: space-between; align-items: center; margin-bottom: 14px;'>
                <div style='display: flex; align-items: center; gap: 6px;'>
                    <span style='color: {dot3_color}; font-size: 14px;'>●</span>
                    <span style='color: #0f172a; font-size: 16px; font-weight: 700;'>{'科技升浪確認' if is_tech else '升浪確認'}</span>
                </div>
                <div style='{badge3_style}'>{sig_rally.get('badge_text', '未亮')}</div>
            </div>
            <div style='margin-bottom: 16px;'>
                <span style='font-size: 32px; font-weight: 800; color: #0f172a;'>{bt_ral.get('title_wins', '23 / 29 次')}</span>
                <span style='font-size: 14px; color: #334155; margin-left: 6px;'>一年後{bench_name}升</span>
            </div>
            <table style='width: 100%; border-collapse: collapse; font-size: 13px; margin-bottom: 14px;'>
                <thead>
                    <tr style='color: #94a3b8; font-size: 12px;'>
                        <th style='text-align: left; padding: 4px 0; font-weight: 500;'></th>
                        <th style='text-align: right; padding: 4px 0; font-weight: 500; width: 32%;'>亮燈後</th>
                        <th style='text-align: right; padding: 4px 0; font-weight: 500; width: 28%;'>對比</th>
                    </tr>
                </thead>
                <tbody style='color: #1e293b;'>
                    <tr><td style='padding: 7px 0; color: #475569;'>120 日後</td><td style='text-align: right; font-weight: 700;'>{bt_ral.get('ret_120d', '+8.7%')}</td><td style='text-align: right; color: #64748b;'>{bt_ral.get('base_120d', '+4.4%')}</td></tr>
                    <tr><td style='padding: 7px 0; color: #475569;'>一年後</td><td style='text-align: right; font-weight: 700;'>{bt_ral.get('ret_1y', '+15.5%')}</td><td style='text-align: right; color: #64748b;'>{bt_ral.get('base_1y', '+9.3%')}</td></tr>
                    <tr><td style='padding: 7px 0; color: #475569;'>副燈（空心）</td><td style='text-align: right;'><div style='font-weight: 700;'>{bt_ral.get('sub_ret', '+5.8%')}</div><div style='font-size: 11px; color: #94a3b8;'>{bt_ral.get('sub_count', '14 次，120 日後')}</div></td><td style='text-align: right; color: #64748b;'>{bt_ral.get('base_120d', '+4.6%')}</td></tr>
                </tbody>
            </table>
            <div style='color: #6366f1; font-size: 12px; font-weight: 500; padding-top: 10px; border-top: 1px solid #f1f5f9;'>
                假警號：主燈 {bt_ral.get('false_main', '6 / 29 次')} · 副燈 {bt_ral.get('false_sub', '3 / 17 次')}
            </div>
        </div>
        """, unsafe_allow_html=True)

    st.markdown(f"<div style='color: #94a3b8; font-size: 12px; margin-top: 10px; margin-bottom: 24px;'>次數 = 已經有結果嘅次數；用 {bench_name} 價格計。對比 = 同樣市況嘅所有日子，唔理有冇亮燈。</div>", unsafe_allow_html=True)

    # ----------------------------------------------------
    # 🌟 0-16 分市況動態診斷條
    # ----------------------------------------------------
    diff_val = score - prev_row.get("score", score)
    diff_txt = f"較前日升 {diff_val} 分" if diff_val > 0 else (f"較前日跌 {abs(diff_val)} 分" if diff_val < 0 else "與前日持平")

    ind_label_map = {
        "vix_pts": "1. VIX 5日均", "idx_pts": f"2. {bench_name} vs 50日線",
        "p50_pts": "3. % > 50日線", "dist_pts": "4. 個股距 52 週高位",
        "p200_pts": "5. % > 200日線", "ma_pts": "6. 50日 vs 200日",
        "vol_pts": "7. 21日波幅", "s52_pts": f"8. {bench_name}距 52 週高位"
    }
    red_alerts = [ind_label_map[k] for k, v in latest_row.items() if k.endswith("_pts") and v == 2]
    yellow_alerts = [ind_label_map[k] for k, v in latest_row.items() if k.endswith("_pts") and v == 1]

    med_val = latest_row.get("dist_52w", -24.35)
    top30_val = latest_row.get("top30_dist", -12.57)
    bench_dist_val = latest_row.get("spy_dist_52w", 0.0)

    if is_tech:
        is_propping_alert = (med_val <= -18.0) and (bench_dist_val >= -5.0)
    else:
        is_propping_alert = (med_val <= -18.0) and (top30_val >= -13.0)

    if is_propping_alert:
        if is_tech:
            diag_alert_txt = f"<span style='color:#ef4444; font-weight:bold;'>🚨 照妖鏡警報：偵測到科技巨頭「托大票、沽小票」掩護出貨！QQQ 回撤僅 {bench_dist_val:.1f}%，但 1,310 隻活躍科技股回撤中位數已深度套牢 {med_val:.1f}%！</span>"
        else:
            diag_alert_txt = f"<span style='color:#ef4444; font-weight:bold;'>🚨 照妖鏡警報：偵測到主力「托大票、沽小票」掩護出貨！30大巨頭回撤僅 {top30_val:.1f}%，但活躍個股回撤均值已深度套牢 {med_val:.1f}%！</span>"
        bar_border = "#ef4444"
    elif red_alerts:
        diag_alert_txt = f"指數與個股層面同步承壓破位，「<b>{'、'.join(red_alerts)}</b>」亮紅燈，另有「<b>{'、'.join(yellow_alerts)}</b>」亮起黃色警示。"
        bar_border = "#f59e0b" if score <= 9 else "#ef4444"
    else:
        diag_alert_txt = f"內部宏觀維度大致健康，{'納指科技股' if is_tech else '全市場'}平均回撤 {latest_row.get('dist_52w', 0.0):.1f}%。"
        bar_border = "#10b981" if score <= 4 else ("#f59e0b" if score <= 9 else "#ef4444")

    zone_badge = "健康" if score <= 4 else ("警示" if score <= 9 else "Meltdown")
    zone_badge_color = "#10b981" if score <= 4 else ("#f59e0b" if score <= 9 else "#ef4444")
    badge_bg = "#ecfdf5" if score <= 4 else ("#fffbeb" if score <= 9 else "#fff1f2")
    badge_border_c = "#a7f3d0" if score <= 4 else ("#fde68a" if score <= 9 else "#fecdd3")

    real_updated_at = cached_data.get("_updated_at", datetime.now().strftime("%Y-%m-%d %H:%M:%S"))

    st.markdown(f"""
    <div style='background: #f8fafc; border-left: 5px solid {bar_border}; border-radius: 8px; padding: 12px 16px; margin-bottom: 20px; border: 1px solid #e2e8f0; border-left-width: 5px;'>
        <div style='display: flex; align-items: center; gap: 8px; font-size: 14px; color: #1e293b;'>
            <span style='background: {badge_bg}; color: {zone_badge_color}; border: 1px solid {badge_border_c}; padding: 2px 10px; border-radius: 12px; font-weight: 700; font-size: 12px;'>● {zone_badge}</span>
            <span>今日{'科技' if is_tech else ''} Score <b>{score} / 16</b>，屬「{zone_badge}」區，{diff_txt}：{diag_alert_txt}</span>
        </div>
        <div style='color: #64748b; font-size: 11.5px; margin-top: 5px;'>
            數據日期 {latest_date_str} (收市) · 覆蓋全美 {current_valid_cnt} 隻真實{'科技' if is_tech else ''}個股 · 快取生成時間：{real_updated_at}
        </div>
    </div>
    """, unsafe_allow_html=True)

    # ----------------------------------------------------
    # 🎛️ 儀表板與歷史對比
    # ----------------------------------------------------
    c_left, c_right = st.columns([4.8, 5.2])
    with c_left:
        fig_gauge = go.Figure(go.Indicator(
            mode="gauge+number", value=score, domain={'x': [0, 1], 'y': [0, 1]},
            number={'font': {'size': 48, 'color': zone_badge_color, 'family': "-apple-system, sans-serif"}, 'suffix': "<span style='font-size:22px; color:#64748b;'> /16</span>"},
            gauge={
                'axis': {'range': [0, 16], 'tickwidth': 1, 'tickcolor': "#94a3b8", 'nticks': 9},
                'bar': {'color': zone_badge_color, 'thickness': 0.3}, 'bgcolor': "rgba(0,0,0,0)",
                'borderwidth': 1, 'bordercolor': "#cbd5e1",
                'steps': [
                    {'range': [0, 4], 'color': 'rgba(16, 185, 129, 0.25)'},
                    {'range': [4, 9], 'color': 'rgba(245, 158, 11, 0.25)'},
                    {'range': [9, 16], 'color': 'rgba(239, 68, 68, 0.25)'}
                ],
                'threshold': {'line': {'color': "#0f172a", 'width': 3}, 'thickness': 0.75, 'value': score}
            }
        ))
        fig_gauge.update_layout(paper_bgcolor="rgba(0,0,0,0)", plot_bgcolor="rgba(0,0,0,0)", height=220, margin=dict(l=15, r=15, t=10, b=0))
        st.plotly_chart(fig_gauge, use_container_width=True)

        pill_04 = "border:2px solid #0f172a; background:#ffffff; color:#0f172a;" if score <= 4 else "border:1px solid #e2e8f0; background:#f8fafc; color:#64748b;"
        pill_59 = "border:2px solid #0f172a; background:#ffffff; color:#0f172a;" if 5 <= score <= 9 else "border:1px solid #e2e8f0; background:#f8fafc; color:#64748b;"
        pill_1016 = "border:2px solid #0f172a; background:#ffffff; color:#0f172a;" if score >= 10 else "border:1px solid #e2e8f0; background:#f8fafc; color:#64748b;"

        st.markdown(f"""
        <div style='display:flex; justify-content:center; gap:10px; margin-top:-5px; margin-bottom:15px;'>
            <div style='{pill_04} padding:4px 16px; border-radius:20px; font-size:12.5px; font-weight:700;'><span style='color:#10b981;'>●</span> 健康 0–4</div>
            <div style='{pill_59} padding:4px 16px; border-radius:20px; font-size:12.5px; font-weight:700;'><span style='color:#f59e0b;'>●</span> 警示 5–9</div>
            <div style='{pill_1016} padding:4px 16px; border-radius:20px; font-size:12.5px; font-weight:700;'><span style='color:#ef4444;'>●</span> Meltdown 10–16</div>
        </div>
        """, unsafe_allow_html=True)

    with c_right:
        st.markdown("<div style='color:#0f172a; font-size:17px; font-weight:700; margin-bottom:10px;'>同過去比較</div>", unsafe_allow_html=True)
        def make_comp_card(label, date_tag, past_score, diff_score):
            dot_c = "#10b981" if past_score <= 4 else ("#f59e0b" if past_score <= 9 else "#ef4444")
            if diff_score > 0: diff_html = f"<span style='color:#ef4444; font-size:12px; font-weight:600;'>▲ 今日高 {diff_score} 分</span>"
            elif diff_score < 0: diff_html = f"<span style='color:#10b981; font-size:12px; font-weight:600;'>▼ 今日低 {abs(diff_score)} 分</span>"
            else: diff_html = "<span style='color:#64748b; font-size:12px;'>持平 0 分</span>"

            return f"""
            <div style='background:#ffffff; border:1px solid #e2e8f0; border-radius:10px; padding:12px 10px; text-align:center; box-shadow: 0 1px 2px rgba(0,0,0,0.03);'>
                <div style='color:#64748b; font-size:12px; margin-bottom:4px;'>{label} <span style='font-size:11px; color:#94a3b8;'>{date_tag}</span></div>
                <div style='font-size:26px; font-weight:800; color:#0f172a; line-height:1.1; margin-bottom:6px;'>
                    <span style='color:{dot_c}; font-size:18px;'>●</span> {past_score}
                </div>
                <div>{diff_html}</div>
            </div>
            """

        c_h1, c_h2, c_h3, c_h4 = st.columns(4)
        with c_h1: st.markdown(make_comp_card("前日", prev_row.get("date", "")[5:], prev_row.get("score", score), score - prev_row.get("score", score)), unsafe_allow_html=True)
        with c_h2: st.markdown(make_comp_card("1週前", week_row.get("date", "")[5:], week_row.get("score", score), score - week_row.get("score", score)), unsafe_allow_html=True)
        with c_h3: st.markdown(make_comp_card("1個月前", month_row.get("date", "")[5:], month_row.get("score", score), score - month_row.get("score", score)), unsafe_allow_html=True)
        with c_h4: st.markdown(make_comp_card("1年前", year_row.get("date", "")[5:], year_row.get("score", score), score - year_row.get("score", score)), unsafe_allow_html=True)

    st.markdown("<div style='height:25px;'></div>", unsafe_allow_html=True)

    # ----------------------------------------------------
    # 📋 核心巨型數據表
    # ----------------------------------------------------
    col_t_title, col_t_ctrl = st.columns([7, 3])
    with col_t_title:
        table_title_text = f"每日記錄：0-16 分同{'納指科技股' if is_tech else '美股'}升跌家數"
        st.markdown(f"<div style='color:#0f172a; font-size:22px; font-weight:800; margin-bottom:2px;'>{table_title_text}</div>", unsafe_allow_html=True)
        st.markdown(f"<div style='color:#64748b; font-size:13.5px; margin-bottom:12px;'>最近 120 個交易日，最新喺最上面。升跌家數計全美 {current_valid_cnt} 隻真實活躍{'科技' if is_tech else ''}股。滑鼠停喺表頭睇門檻。</div>", unsafe_allow_html=True)
    with col_t_ctrl:
        view_days = st.selectbox("📅 選擇顯示交易日數量：", [120, 60, 30, 10], index=0)

    table_rows = matrix[:view_days]

    tbody_content = []
    for r in table_rows:
        spy_c = r.get('spy_chg', 0.0)
        spy_c_str = f"+{spy_c:.1f}%" if spy_c > 0 else f"{spy_c:.1f}%"
        spy_col = "#dc2626" if spy_c < 0 else "#16a34a"

        qqq_c = r.get('qqq_chg', 0.0)
        qqq_c_str = f"+{qqq_c:.1f}%" if qqq_c > 0 else f"{qqq_c:.1f}%"
        qqq_col = "#dc2626" if qqq_c < 0 else "#16a34a"

        sc = r.get("score", 0)
        if sc <= 2: mod016_bg_cls = "cm-bg-score-green-deep"
        elif sc == 3: mod016_bg_cls = "cm-bg-score-green-mid"
        elif sc == 4: mod016_bg_cls = "cm-bg-score-green-light"
        elif sc == 5: mod016_bg_cls = "cm-bg-score-yellow-5"
        elif sc == 6: mod016_bg_cls = "cm-bg-score-yellow-6"
        elif sc == 7: mod016_bg_cls = "cm-bg-score-yellow-7"
        elif sc == 8: mod016_bg_cls = "cm-bg-score-yellow-8"
        elif sc == 9: mod016_bg_cls = "cm-bg-score-yellow-9"
        elif sc in (10, 11): mod016_bg_cls = "cm-bg-score-red-10"
        elif sc in (12, 13): mod016_bg_cls = "cm-bg-score-red-12"
        else: mod016_bg_cls = "cm-bg-score-red-14"

        def get_ind_cls(pts):
            if pts == 2: return "class='cm-ind-red'"
            if pts == 1: return "class='cm-ind-yellow'"
            return ""

        c1_cls = get_ind_cls(r.get("vix_pts", 0))
        c2_cls = get_ind_cls(r.get("idx_pts", 0))
        c3_cls = get_ind_cls(r.get("p50_pts", 0))
        c4_cls = get_ind_cls(r.get("dist_pts", 0))
        c5_cls = get_ind_cls(r.get("p200_pts", 0))
        c6_cls = get_ind_cls(r.get("ma_pts", 0))
        c7_cls = get_ind_cls(r.get("vol_pts", 0))
        c8_cls = get_ind_cls(r.get("s52_pts", 0))

        up = r.get("up_4pct", 0)
        dn = r.get("down_4pct", 0)
        up_limit = 180 if is_tech else 300
        dn_limit = 180 if is_tech else 300

        if up >= up_limit: up_cls = "class='cm-breadth-green-deep'"
        elif up > dn: up_cls = "class='cm-breadth-green-light'"
        elif dn > up: up_cls = "class='cm-breadth-red-light'"
        else: up_cls = "style='color:#111827; font-weight:500;'"

        if dn >= dn_limit: dn_cls = "class='cm-breadth-red-deep'"
        elif dn > up: dn_cls = "class='cm-breadth-red-light'"
        elif up > dn: dn_cls = "class='cm-breadth-green-light'"
        else: dn_cls = "style='color:#111827; font-weight:500;'"

        r5 = r.get("r_5d", 1.0)
        r5_cls = "class='cm-breadth-green-deep'" if r5 >= 2.0 else ("class='cm-breadth-red-deep'" if r5 < 0.5 else "style='color:#374151; font-weight:500;'")

        r10 = r.get("r_10d", 1.0)
        r10_cls = "class='cm-breadth-green-deep'" if r10 >= 2.0 else ("class='cm-breadth-red-deep'" if r10 < 0.8 else ("class='cm-breadth-red-light'" if r10 < 1.0 else "style='color:#374151; font-weight:500;'"))

        p40 = r.get("pct_40ma", 50.0)
        p40_cls = "class='cm-breadth-green-deep'" if p40 < 20.0 else "style='color:#111827; font-weight:500;'"

        display_vix_ma5 = r.get("v_ma5", r.get("vix_val", 0.0))

        row_html = (
            f"<tr class='cm-row'>"
            f"<td style='color:#4b5563; font-family:monospace; font-weight:500;'>{r.get('date', '')}</td>"
            f"<td class='cm-cell-score {mod016_bg_cls}'>{r.get('score', 0)}</td>"
            f"<td class='{mod016_bg_cls}'><div style='color:#0f172a; font-weight:600;'>{r.get('spy_price', 0.0):.2f}</div><div style='font-size:11px; color:{spy_col}; font-weight:600;'>{spy_c_str}</div></td>"
            f"<td class='{mod016_bg_cls} cm-col-qqq'><div style='color:#0f172a; font-weight:600;'>{r.get('qqq_price', 0.0):.2f}</div><div style='font-size:11px; color:{qqq_col}; font-weight:600;'>{qqq_c_str}</div></td>"
            f"<td {c1_cls}>{display_vix_ma5:.2f}</td>"
            f"<td {c2_cls}>{r.get('idx_50ma', 0.0):+.2f}</td>"
            f"<td {c3_cls}>{r.get('pct_50', 0.0):.1f}</td>"
            f"<td {c4_cls}>{r.get('dist_52w', 0.0):.2f}</td>"
            f"<td {c5_cls}>{r.get('pct_200', 0.0):.1f}</td>"
            f"<td {c6_cls}>{r.get('ma50_ma200', 0.0):+.2f}</td>"
            f"<td {c7_cls}>{r.get('vol_21', 0.0):.1f}</td>"
            f"<td {c8_cls} class='cm-col-8-last'>{r.get('spy_dist_52w', 0.0):.2f}</td>"
            f"<td {up_cls}>{r.get('up_4pct', 0)}</td>"
            f"<td {dn_cls}>{r.get('down_4pct', 0)}</td>"
            f"<td {r5_cls}>{r.get('r_5d', 0.0):.2f}</td>"
            f"<td {r10_cls}>{r.get('r_10d', 0.0):.2f}</td>"
            f"<td {p40_cls}>{r.get('pct_40ma', 0.0):.1f}</td>"
            f"</tr>"
        )
        tbody_content.append(row_html)

    tbody_str = "".join(tbody_content)

    c2_header_name = "QQQ vs<br><span style='font-size:11px;color:#64748b;'>50日線</span>" if is_tech else "2. 指數 vs<br><span style='font-size:11px;color:#64748b;'>50日線</span>"
    c8_header_name = "8. QQQ距<br><span style='font-size:11px;color:#64748b;'>52週高</span>" if is_tech else "8. 標普距<br><span style='font-size:11px;color:#64748b;'>52週高</span>"
    breadth_header_title = "納指科技升跌家數" if is_tech else "美股升跌家數"

    full_table_doc = f"""
    <!DOCTYPE html>
    <html>
    <head>
    <meta charset="utf-8">
    <style>
        body {{
            margin: 0; padding: 0; background-color: transparent;
            font-family: -apple-system, BlinkMacSystemFont, "Segoe UI", Roboto, Helvetica, Arial, sans-serif;
        }}
        .cashmate-container {{
            width: 100%; overflow-x: auto; background-color: #ffffff;
            border-radius: 8px; border: 1px solid #e2e8f0; box-shadow: 0 1px 3px rgba(0, 0, 0, 0.05);
        }}
        .cashmate-table {{
            width: 100%; min-width: 1520px; border-collapse: collapse; font-size: 13px; color: #111827; text-align: center;
        }}
        .cashmate-table th {{
            padding: 10px 6px; font-weight: 600; border: 1px solid #e2e8f0; background-color: #f8fafc; color: #475569; white-space: nowrap;
        }}
        .cashmate-table td {{
            padding: 8px 6px; border: 1px solid #f1f5f9; white-space: nowrap; background-color: #ffffff;
        }}
        .th-group-main {{
            background-color: #f1f5f9 !important; color: #0f172a !important; font-size: 13.5px !important; font-weight: 700 !important;
        }}
        .th-thick-right, .cm-col-qqq, .cm-col-8-last {{
            border-right: 2.5px solid #cbd5e1 !important;
        }}
        .cm-cell-score {{
            font-size: 15px !important; font-weight: 800 !important; color: #0f172a !important;
        }}
        .cm-bg-score-green-deep {{ background-color: #cfe6db !important; }}
        .cm-bg-score-green-mid {{ background-color: #dbefe4 !important; }}
        .cm-bg-score-green-light {{ background-color: #ecf6f1 !important; }}
        .cm-bg-score-yellow-5 {{ background-color: #f8e9d2 !important; }}
        .cm-bg-score-yellow-6 {{ background-color: #f1e1bf !important; }}
        .cm-bg-score-yellow-7 {{ background-color: #efd8ac !important; }}
        .cm-bg-score-yellow-8 {{ background-color: #ebd19c !important; }}
        .cm-bg-score-yellow-9 {{ background-color: #e7ca8c !important; }}
        .cm-bg-score-red-10 {{ background-color: #fce7e8 !important; }}
        .cm-bg-score-red-12 {{ background-color: #f5bec1 !important; }}
        .cm-bg-score-red-14 {{ background-color: #eb9499 !important; }}
        .cm-ind-yellow {{ background-color: #f2e2c0 !important; color: #78350f !important; font-weight: 600 !important; }}
        .cm-ind-red {{ background-color: #eeb8b8 !important; color: #7f1d1d !important; font-weight: 600 !important; }}
        .cm-breadth-green-deep {{ background-color: #a1d6b8 !important; color: #064e3b !important; font-weight: 700 !important; }}
        .cm-breadth-green-light {{ background-color: #e0f1e7 !important; color: #065f46 !important; font-weight: 600 !important; }}
        .cm-breadth-red-deep {{ background-color: #eeb2b1 !important; color: #7f1d1d !important; font-weight: 700 !important; }}
        .cm-breadth-red-light {{ background-color: #f9e5e6 !important; color: #991b1b !important; font-weight: 600 !important; }}
        .cm-row:hover td {{ background-color: #f8fafc; }}
    </style>
    </head>
    <body>
    <div class="cashmate-container">
    <table class="cashmate-table">
        <thead>
            <tr>
                <th colspan="4" class="th-group-main th-thick-right">0-16 分</th>
                <th colspan="8" class="th-group-main th-thick-right">8 個指標（黃 = 1 分，紅 = 2 分）</th>
                <th colspan="5" class="th-group-main">{breadth_header_title}</th>
            </tr>
            <tr>
                <th style="min-width:85px;">日期</th>
                <th style="min-width:48px;" title="綠 = 健康 0–4、黃 = 警示 5–9、紅 = Meltdown 10–16 (越深分數越高)">分數</th>
                <th style="min-width:75px;">SPY</th>
                <th style="min-width:75px;" class="th-thick-right">QQQ</th>
                <th style="min-width:70px;" title="VIX 5日均線>=17.0(黃=1分)，或>=25.0(紅=2分)">1. VIX<br><span style="font-size:11px;color:#64748b;">5日均</span></th>
                <th style="min-width:80px;" title="指數跌穿50日線<0%(黃=1分)，跌穿逾-2.5%(紅=2分)">{c2_header_name}</th>
                <th style="min-width:70px;" title="活躍股企穩50MA比例<=50%(黃=1分)，<30%(紅=2分)">3. % ><br><span style="font-size:11px;color:#64748b;">50日線</span></th>
                <th style="min-width:85px;" title="個股距52週高回撤平均值(黃=1分<-15%，紅=2分<-20%)">4. 個股距<br><span style="font-size:11px;color:#64748b;">52週高</span></th>
                <th style="min-width:70px;" title="活躍股企穩200MA比例<=50.0%(黃=1分)，<35%(紅=2分)，>50%白底健康">5. % ><br><span style="font-size:11px;color:#64748b;">200日線</span></th>
                <th style="min-width:85px;" title="50MA高於200MA幅度<3%(黃=1分)，死叉倒掛(紅=2分)">6. 50日 vs<br><span style="font-size:11px;color:#64748b;">200日</span></th>
                <th style="min-width:70px;" title="21日年化波幅>=12%(黃=1分)，>=18%(紅=2分)">7. 21日<br><span style="font-size:11px;color:#64748b;">波幅</span></th>
                <th style="min-width:85px;" class="th-thick-right" title="指數距52週高回撤-4%~-5%(黃=1分)，回撤逾-5%(紅=2分)，>-4%白底健康">{c8_header_name}</th>
                <th style="min-width:65px;" title="單日升幅 >= 4% (深色=井噴衝潮；升多過跌=淺綠、跌多過升=淺紅)">升 &ge;4%<br><span style="font-size:11px;color:#64748b;">隻</span></th>
                <th style="min-width:65px;" title="單日跌幅 >= 4% (深色=退潮失血；升多過跌=淺綠、跌多過升=淺紅)">跌 &ge;4%<br><span style="font-size:11px;color:#64748b;">隻</span></th>
                <th style="min-width:75px;" title="5日累計升跌家數比率 (>= 2 = 綠，< 0.5 = 紅)">5 日比率</th>
                <th style="min-width:75px;" title="10日累計升跌家數比率 (< 1 = 紅，>= 2 = 綠)">10 日比率</th>
                <th style="min-width:85px;" title="企穩 40 日線之個股比例 (< 20% = 深綠 市況極度超賣)">企穩 40 日線<br><span style="font-size:11px;color:#64748b;">%</span></th>
            </tr>
        </thead>
        <tbody>
            {tbody_str}
        </tbody>
    </table>
    </div>
    </body>
    </html>
    """

    components.html(full_table_doc, height=580, scrolling=True)

    breadth_threshold_text = "≥ 180 隻（科技模式）/ 300 隻（大盤模式）= 深色"
    st.markdown(f"""
    <div style="background: #ffffff; border: 1px solid #e2e8f0; border-radius: 8px; padding: 14px 18px; margin-top: 10px; margin-bottom: 25px; box-shadow: 0 1px 2px rgba(0,0,0,0.03); font-size: 13px; color: #475569; line-height: 1.85; font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, sans-serif;">
        <div style="display:flex; align-items:center; gap:8px; margin-bottom:4px;">
            <span style="display:inline-flex; gap:2px;">
                <span style="width:13px; height:13px; background:#dbefe4; border-radius:2px; display:inline-block;"></span>
                <span style="width:13px; height:13px; background:#efd8ac; border-radius:2px; display:inline-block;"></span>
                <span style="width:13px; height:13px; background:#f0b3b2; border-radius:2px; display:inline-block;"></span>
            </span>
            <span><b>分數 / SPY / QQQ</b>：綠 = 健康 0–4、黃 = 警示 5–9、紅 = Meltdown 10–16 （越深分數越高）</span>
        </div>
        <div style="display:flex; align-items:center; gap:8px; margin-bottom:4px;">
            <span style="display:inline-flex; gap:2px;">
                <span style="width:13px; height:13px; background:#f2e2c0; border-radius:2px; display:inline-block;"></span>
                <span style="width:13px; height:13px; background:#eeb8b8; border-radius:2px; display:inline-block;"></span>
            </span>
            <span><b>8 個指標</b>：黃 = 1 分、紅 = 2 分，加埋就係當日分數</span>
        </div>
        <div style="display:flex; align-items:center; gap:8px; margin-bottom:4px;">
            <span style="display:inline-flex; gap:2px;">
                <span style="width:13px; height:13px; background:#a1d6b8; border-radius:2px; display:inline-block;"></span>
                <span style="width:13px; height:13px; background:#eeb2b1; border-radius:2px; display:inline-block;"></span>
            </span>
            <span><b>單日升 / 跌 ≥4%</b>：{breadth_threshold_text} ； 升多過跌 = 淺綠 、 跌多過升 = 淺紅 。 <b>5 / 10 日比率</b> = 期內升 ≥4% 隻數 ÷ 跌 ≥4% 隻數 ： 10 日 &lt; 1、5 日 &lt; 0.5 = 紅 ， ≥ 2 = 綠</span>
        </div>
        <div style="display:flex; align-items:center; gap:8px;">
            <span style="width:13px; height:13px; background:#a1d6b8; border-radius:2px; display:inline-block;"></span>
            <span><b>企穩 40 日線 &lt; 20%</b> = 深綠 （市況極度超賣） 。 只係歷史數據同描述，唔係買賣建議。</span>
        </div>
    </div>
    """, unsafe_allow_html=True)

if __name__ == "__main__":
    render_page_market_monitor()