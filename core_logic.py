import pandas as pd
import numpy as np
import yfinance as yf
import time
import json
import os
from datetime import datetime

# 👴 為咗計到 200天線，預設抓取 2 年數據 (足夠應付日線/週線多頭排列)
def smart_fetch(ticker_sym, period="2y"):
    try:
        time.sleep(0.2); asset = yf.Ticker(ticker_sym)
        data = asset.history(period=period, auto_adjust=True)
        if data.empty:
            time.sleep(1.0); data = asset.history(period=period, auto_adjust=True)
        if data.index.tz is not None: data.index = data.index.tz_localize(None)
        return data.dropna(subset=['Close', 'Volume', 'High', 'Low', 'Open'])
    except: return pd.DataFrame()

def check_stop_loss(df):
    if len(df) < 15: return False
    ema10 = df['Close'].ewm(span=10, adjust=False).mean()
    return df['Close'].iloc[-1] < ema10.iloc[-1] and (df['Close'].iloc[-2] >= ema10.iloc[-2] or df['Close'].iloc[-3] >= ema10.iloc[-3])

def scan_dragon_logic(df, ticker, sector_name, market="HK", mode='NORMAL', force_return=False, vcp_52w=False, vcp_ath=False):
    if len(df) < 252: return None 
    
    # =======================================================
    # 0. 基礎數據準備
    # =======================================================
    c = df['Close']; h = df['High']; l = df['Low']; o = df['Open']; v = df['Volume']
    curr_p = c.iloc[-1]; pct = c.pct_change().fillna(0); change = pct * 100
    ma20_v = v.rolling(20).mean(); ma60_v = v.rolling(60).mean(); ma50 = c.rolling(50).mean()
    
    # 👴 MA 大軍準備 (涵蓋所有長短線需求)
    ma100 = c.rolling(100).mean()
    ma200 = c.rolling(200).mean()
    ma50_v = v.rolling(50).mean()
    
    v_std20 = v.rolling(20).std(); v_upper = ma20_v + (2.0 * v_std20)
    ema10 = c.ewm(span=10, adjust=False).mean()
    ema20 = c.ewm(span=20, adjust=False).mean()
    
    var1 = c - l; var2 = h - c; var3 = np.maximum(h - l, 0.001)
    buyvol = v * var1 / var3; sellvol = v * var2 / var3; netvol = buyvol - sellvol
    netma10 = netvol.rolling(10).mean()
    obv = (np.sign(pct) * v).cumsum()

    is_burst = (v > v_upper) & (v > ma60_v * 1.9) & (abs(change) > 2.0)
    is_magenta = is_burst & (c <= o)
    is_cyan = is_burst & (c > o)
    
    # =======================================================
    # 🏎️ 秘法 3.7 終極狀態機版 
    # =======================================================
    ma63 = c.rolling(63).mean(); ma126 = c.rolling(126).mean()
    ma189 = c.rolling(189).mean(); ma252 = c.rolling(252).mean()
    
    rs_secret = (2 * c / ma63.replace(0, np.nan)) + (c / ma126.replace(0, np.nan)) + (c / ma189.replace(0, np.nan)) + (c / ma252.replace(0, np.nan))
    power_secret = rs_secret - 5
    current_power = power_secret.iloc[-1]
    
    gt_05 = power_secret > 0.5
    block_id = (~gt_05).cumsum()
    power_inc = power_secret > power_secret.shift(1)
    is_base_car = (gt_05.rolling(7).sum() == 7) & (power_inc.rolling(7).sum() >= 3)
    
    whale_buy = (v > ma20_v) & (c > o) & (c > c.shift(1))
    whale_in_7d = whale_buy.rolling(7).sum() >= 2
    
    ignition_pulse = is_base_car & (power_secret.shift(7) <= 0.5) & whale_in_7d
    ignited_in_block = ignition_pulse.groupby(block_id).cummax().fillna(False)
    
    is_secret_bonus = ignited_in_block & (ignition_pulse.rolling(10).sum() > 0)
    is_secret_cruise = ignited_in_block & (~is_secret_bonus) & gt_05
    
    recent_high_pow = power_secret.rolling(30).max() >= 5
    drop_below_3 = (power_secret < 3).rolling(3).sum() == 3
    airplane_crash = recent_high_pow & drop_below_3

    # =======================================================
    # 🚀 TTM 2.0 雙重保險版
    # =======================================================
    n_ttm = 20
    ma_ttm = c.rolling(n_ttm).mean()
    std_ttm = c.rolling(n_ttm).std()
    atr_ttm = (h - l).rolling(n_ttm).mean()
    is_squeezing = (ma_ttm + 2*std_ttm < ma_ttm + 1.5*atr_ttm) & (ma_ttm - 2*std_ttm > ma_ttm - 1.5*atr_ttm)
    squeeze_fired = (is_squeezing.shift(1) == True) & (is_squeezing == False)

    weights_20 = np.arange(1, 21) / 210.0
    var1_ttm = (h.rolling(20).max() + l.rolling(20).min()) / 2 + ma_ttm
    delta_ttm = c - (var1_ttm / 2)
    var2_ttm = 3 * delta_ttm.rolling(20).apply(lambda x: np.dot(x, weights_20), raw=True) - 2 * delta_ttm.rolling(20).mean()

    ema12 = c.ewm(span=12, adjust=False).mean(); ema26 = c.ewm(span=26, adjust=False).mean()
    dif = ema12 - ema26; dea = dif.ewm(span=9, adjust=False).mean()
    dif_up = (dif > dea) & (dif > dif.shift(1))

    ttm_2_trigger = (squeeze_fired | ((var2_ttm > 0) & (var2_ttm.shift(1) <= 0))) & dif_up
    ttm_2_active = (ttm_2_trigger.rolling(6).sum() > 0) & (var2_ttm > 0) & (dif > dea)

    # =======================================================
    # 🔄 IND1 回升/回落
    # =======================================================
    llv55 = l.rolling(55).min(); hhv55 = h.rolling(55).max()
    denom = (hhv55 - llv55).replace(0, np.nan)
    ema2 = c.ewm(span=2, adjust=False).mean()
    ind1_raw = (ema2 - llv55) / denom
    ind1 = ind1_raw.ewm(span=13, adjust=False).mean()
    
    up_arrow = (ind1 > 0.501) & (ind1.shift(1) <= 0.501) & (ind1 >= ind1.rolling(2).max())
    down_arrow = (ind1 < 0.499) & (ind1.shift(1) >= 0.499) & (ind1 <= ind1.rolling(2).min())
    
    last_up_idx = -1; last_down_idx = -1
    for i in range(1, 31):
        idx = -i
        if len(ind1) >= i:
            if last_up_idx == -1 and up_arrow.iloc[idx]: last_up_idx = i
            if last_down_idx == -1 and down_arrow.iloc[idx]: last_down_idx = i
                
    is_rebound_active = (last_up_idx != -1) and (last_up_idx <= 6)
    is_weak_active = (last_down_idx != -1) and (last_down_idx <= 30)
    if is_weak_active and (last_up_idx != -1) and (last_up_idx < last_down_idx): is_weak_active = False

    # =======================================================
    # 第二階段 (PRUDEN + WEIS)
    # =======================================================
    e50 = c.ewm(span=50, adjust=False).mean(); e150 = c.ewm(span=150, adjust=False).mean(); e200 = c.ewm(span=200, adjust=False).mean()
    pruden_score = (c > e50).astype(int) + (e50 > e150).astype(int) + (e150 > e200).astype(int) + (((c - e50)/e50*100) > 0).astype(int)
    pruden_break = (pruden_score == 4) & (pruden_score.shift(1) < 4)
    weis_dir = np.sign(c - c.shift(1)); weis_vol = abs(v * weis_dir)
    buy_f = pd.Series(np.where(weis_dir > 0, weis_vol, 0), index=c.index).rolling(5).sum()
    sell_f = pd.Series(np.where(weis_dir < 0, weis_vol, 0), index=c.index).rolling(5).sum()
    net_thrust = buy_f - sell_f
    thrust_3_inc = (net_thrust > net_thrust.shift(1)) & (net_thrust.shift(1) > net_thrust.shift(2)) & (net_thrust.shift(2) > (0.3 * 1e6))
    stage_2_signal = thrust_3_inc & pruden_break.rolling(14).max().fillna(0).astype(bool)

    # =======================================================
    # 🚨 第一層：7大禁示 + 死線判定 (共通)
    # =======================================================
    foul_points = 0; foul_list = []
    if is_magenta.tail(20).any(): foul_points += 10; foul_list.append("犯1(-10)")
    if ((change > 0) & (netvol < 0)).tail(20).any(): foul_points += 10; foul_list.append("犯2(-10)")
    if ((v > ma60_v * 2.0) & (change < 2.0) & (change >= 0)).tail(20).any(): foul_points += 10; foul_list.append("犯3(-10)")
    if (netvol.rolling(5).sum() < 0).tail(20).any(): foul_points += 10; foul_list.append("犯4(-10)")
    if ((change.shift(1) > 5.0) & (v < v.shift(1) * 0.5)).tail(20).any(): foul_points += 10; foul_list.append("犯5(-10)")
    if ((((c - ma50)/ma50)*100 > 15) & (v > ma60_v * 3.0)).tail(20).any(): foul_points += 10; foul_list.append("犯6(-10)")
    if ((c >= c.shift(10)) & (obv < obv.shift(10))).tail(20).any(): foul_points += 10; foul_list.append("犯7(-10)")

    rs_val = 80 + (curr_p / ma50.iloc[-1] * 10)
    ej_val = 85 + (netvol.tail(20).sum() / max(ma20_v.iloc[-1]*20, 1) * 5)
    se_val = 75 + (pct.tail(20).sum() * 100)
    conc = (abs(netvol.tail(20)).max() / max(abs(netvol.tail(20)).sum(), 1)) * 100
    bias = ((curr_p - ma50.iloc[-1]) / ma50.iloc[-1]) * 100
    
    obv_curr = obv.iloc[-1] - obv.iloc[-21] if len(obv)>20 else 0
    obv_prev = obv.iloc[-21] - obv.iloc[-41] if len(obv)>40 else 1
    obv_pct = (obv_curr - obv_prev) / max(abs(obv_prev), 1) * 100
    p_trend = c.iloc[-1] - c.iloc[-21]
    if p_trend >= 0:
        if obv_curr > 0: obv_state = 1 if obv_pct > 50 else 2
        else: obv_state = 5 if obv_pct < -50 else 6
    else:
        if obv_curr < 0: obv_state = 3 if obv_pct < -50 else 4
        else: obv_state = 7 if obv_pct > 50 else 8

    is_dead = False; death_reason = ""
    if not mode.startswith('STRONG'): # 👴 STRONG 模式免受 50天線及 OBV 死線約束
        if curr_p <= ma50.iloc[-1]: is_dead = True; death_reason = "跌穿50天線"
        elif is_magenta.iloc[-1]: is_dead = True; death_reason = "今日粉紅爆缸"
        elif not (rs_val > 60 and ej_val > 85 and se_val > 75 and netvol.tail(20).sum() > 0): 
            is_dead = True; death_reason = "SE或錢流不達標"
        elif obv_state not in [1, 2, 7, 8]: is_dead = True; death_reason = f"OBV狀態({obv_state})"
        
        high_52w = h.tail(252).max()
        pct_from_52w_high = ((high_52w - curr_p) / high_52w) * 100
        if not is_dead and vcp_52w and (pct_from_52w_high > 25.0):
            is_dead = True; death_reason = f"距離52週高位太遠({pct_from_52w_high:.1f}%)"
        if not is_dead and vcp_ath and (curr_p < h.max() * 0.98):
            is_dead = True; death_reason = "未達歷史新高(ATH)極致區"
            
        if is_dead and not force_return: return None

    # =======================================================
    # 🏆 核心計分系統 (大合流版)
    # =======================================================
    bonus_list = []; core_p = 0; bias_p = 0
    is_vcp_trend = False; is_vcp_burst_7d = False
    
    score = 100.0 # 👴 所有模式底分均為 100

    # ---------------- 舊有 10 項加分 (全線激活) ----------------
    ret_40d = (curr_p - c.iloc[-40]) / c.iloc[-40] if len(c) > 40 else 0
    if curr_p > ema10.iloc[-1] > ema20.iloc[-1] > ma50.iloc[-1]:
        score += 50; bonus_list.append("VCP趨勢👑(+50)"); is_vcp_trend = True
    power_series = buyvol / np.where(sellvol > 0, sellvol, 0.1)
    vcp_burst_cond = (v > ma20_v * 1.5) & (power_series > 1.2) & (c > o)
    if vcp_burst_cond.tail(7).any():
        score += 30; bonus_list.append("VCP爆量⚡(+30)"); is_vcp_burst_7d = True 
    if ret_40d > 0.15:
        score += 20; bonus_list.append("VCP強勢🔥(+20)")

    if is_secret_bonus.iloc[-1]: score += 20; bonus_list.append("秘法起步🏎️(+20)")
    if airplane_crash.iloc[-1]: core_p += 50; foul_list.append("高位墜機🛬(-50)")
    if is_rebound_active: score += 10; bonus_list.append("回升(+10)")
    if is_weak_active: core_p += 60; foul_list.append("弱勢(-60)")
    if ttm_2_active.iloc[-1]: score += 15; bonus_list.append("TTM🚀(+15)")

    if stage_2_signal.tail(4).any(): score += 30; bonus_list.append("第二階段 ♂(+30)")
    if se_val >= 90.0: score += 5; bonus_list.append("動能(+5)")
    if (buyvol.iloc[-1] / (sellvol.iloc[-1] if sellvol.iloc[-1]>0 else 0.1)) > 1.5: score += 5; bonus_list.append("兵力(+5)")
    if obv_state in [1, 7]: score += 10; bonus_list.append("OBV(+10)")
    total_v60 = max(v.tail(60).sum(), 1)
    if netvol.tail(60).sum() > (total_v60 * 0.12): score += 5; bonus_list.append("穩定流入(+5)") 
    if rs_val >= 92.0: score += 5; bonus_list.append("RS(+5)")
    if curr_p >= h.tail(60).max(): score += 5; bonus_list.append("破頂(+5)")
            
    # ---------------- 新增 5 大戰術加分 (全線激活) ----------------
    # 👴 公式鎖定: 10MA > 20MA > 50MA > 100MA > 200MA
    aligned = (ema10 > ema20) & (ema20 > ma50) & (ma50 > ma100) & (ma100 > ma200)
    
    # 若是 STRONG 模式，必須滿足排列海選才准通行！
    if mode.startswith('STRONG') and not aligned.iloc[-1]: return None
    
    if not aligned.iloc[-9:-1].all() and aligned.iloc[-1]:
        score += 30; bonus_list.append("初排順🎖️(+30)")
        
    cross_10_20 = (ema10 > ema20) & (ema10.shift(1) <= ema20.shift(1))
    if cross_10_20.tail(4).any() and curr_p > ema20.iloc[-1]:
        score += 30; bonus_list.append("10MA金叉🏹(+30)")
        
    cross_20_50 = (ema20 > ma50) & (ema20.shift(1) <= ma50.shift(1))
    if cross_20_50.tail(5).any() and curr_p > ma50.iloc[-1]:
        score += 30; bonus_list.append("20MA金叉💥(+30)")
        
    volatility = (h - l) / l * 100
    if (volatility.tail(5) <= 1.5).all() and (v.iloc[-1] < ma50_v.iloc[-1] * 0.6):
        score += 30; bonus_list.append("極致縮量😎(+30)")
        
    # 👴 試底成功精準還原：之前穿10/20MA，落到50MA有支撐，今日重上10/20MA！
    was_below = ((c < ema10) & (c < ema20) & (l <= ma50 * 1.02) & (l >= ma50 * 0.98)).tail(20).any()
    is_above_now = (curr_p > ema10.iloc[-1]) and (curr_p > ema20.iloc[-1])
    if was_below and is_above_now:
        score += 30; bonus_list.append("試底成功🧱(+30)")

    # ---------------- 懲罰機制 ----------------
    limit = 10 if market == "HK" else 5
    if bias > limit:
        if mode == 'NORMAL':
            core_p += 25; bias_p = 50 + (bias - limit) * 10
        else: 
            score -= 40 
    elif mode == 'VCP' and bias > 8: score -= 40
    
    if mode == 'NORMAL': 
        if netvol.tail(60).sum() < 0: core_p += 30
        if v.iloc[-1] > ma60_v.iloc[-1] * 2.5: core_p += 20
        if (var2.iloc[-1] / var3.iloc[-1]) > 0.5: core_p += 15

    # =======================================================
    # 🔮 隱藏公仔裝盤 
    # =======================================================
    hidden_icons = []
    if is_squeezing.iloc[-1]: hidden_icons.append("🤐(蓄勢)")
    if is_secret_cruise.iloc[-1]: hidden_icons.append("🏎️")
        
    cond_cyan = is_cyan & (netvol > netvol.rolling(10).mean())
    cond_narrow = (netma10 > netma10.shift(1)) & ((var3 / l * 100) < 1.5)
    cond_shield = (change < 0) & (netvol > 0)
    cond_pit = (change < -1) & is_magenta
    cond_vcp = (netma10 > 0) & (netma10.shift(1) < 0) & (v < ma20_v)
    cond_lightning = (v > v_upper) & (buyvol > sellvol * 2)
    whale_days = sum((v.tail(10) > ma60_v.tail(10) * 1.5) & (netvol.tail(10) > 0))

    if cond_cyan.tail(4).any(): hidden_icons.append("💰🔥")
    if cond_narrow.tail(4).any(): hidden_icons.append("💰🤫")
    if cond_shield.tail(4).any(): hidden_icons.append("💰🛡️")
    if cond_vcp.tail(4).any(): hidden_icons.append("🧧")
    if cond_lightning.tail(4).any(): hidden_icons.append("⚡")
    if cond_pit.tail(20).any(): hidden_icons.append("💎/😱")
    if whale_days > 0: hidden_icons.append(f"🐋({whale_days}/10)")
    if netvol.tail(20).sum() > 0 and "🧧" not in hidden_icons: hidden_icons.append("🧧")

    # =======================================================
    # 🪃 事後動態過濾：N 字突破 (捕捉第1日及第2日)
    # =======================================================
    lookback = 8 
    a_point = h.shift(2).rolling(lookback).max().iloc[-1]
    a_point_yest = h.shift(3).rolling(lookback).max().iloc[-1]
    
    is_breakout_today = (c.iloc[-1] > a_point) and (c.iloc[-2] <= a_point)
    is_breakout_yest = (c.iloc[-2] > a_point_yest) and (c.iloc[-3] <= a_point_yest)
    
    if is_breakout_today or is_breakout_yest:
        score += 20
        bonus_list.append("N字突破🪃(+20)")
        hidden_icons.append("🪃")

    # =======================================================
    # 結算與回傳
    # =======================================================
    status_prefix = ""
    if mode == 'VCP':
        if is_vcp_trend and cond_narrow.tail(4).any() and cond_vcp.tail(4).any() and ((whale_days > 0) or cond_lightning.tail(4).any()) and is_vcp_burst_7d:
            status_prefix = "🐲 [真龍 VCP 股出現！請注意！] "
            score += 50 
    elif mode == 'STRONG_WEEKLY':
        status_prefix = "👑 [週線排順] "
    elif mode == 'STRONG_DAILY':
        status_prefix = "👑 [日線排順] "

    # STRONG 模式只受家法(foul_points)扣分影響
    final_score = score - foul_points if mode.startswith('STRONG') else score - core_p - bias_p - foul_points
    icons_final = " ".join(hidden_icons)
    display_info = bonus_list + foul_list
    if display_info: icons_final += " | " + ",".join(display_info)
    
    if mode.startswith('STRONG'):
        base_status = ""
    else:
        base_status = f"[☠️ 落選: {death_reason}]" if is_dead else ("[⚠️ 末段]" if bias > limit else "[👑 趨勢]")

    return {
        "Ticker": ticker, "Sector": sector_name, "Score": round(final_score, 1), 
        "RawPower": round(ej_val, 1), 
        "Penalty": round(foul_points if mode.startswith('STRONG') else core_p + bias_p + foul_points, 1),
        "RS": round(rs_val, 1),
        "EJ": round(current_power, 3), 
        "SE": round(se_val, 1),
        "Flow": f"{netvol.tail(20).sum()/1e6:.1f}M", "Conc": f"{conc:.1f}%", "OBV": f"狀態 {obv_state}",
        "Power": round(buyvol.iloc[-1]/sellvol.iloc[-1] if sellvol.iloc[-1]>0 else 1, 1), 
        "Bias": round(bias, 1), "EMA10": round(ema10.iloc[-1], 2),
        "Status": status_prefix + base_status, 
        "Icons": icons_final, "IsDead": is_dead
    }

# =======================================================
# 🔥 爺爺滿血升級：究極資產拔河龍虎榜核心
# =======================================================
class AssetRanker:
    @staticmethod
    def get_rank_and_acceleration(tickers, lookback_days, category_name):
        is_sector_battle = "1029" in category_name
        
        data = yf.download(tickers, period="1y", progress=False, threads=False)
        if data.empty: return pd.DataFrame()
        
        if isinstance(data.columns, pd.MultiIndex):
            close_df = data['Close']; open_df = data['Open']
            high_df = data['High']; low_df = data['Low']; vol_df = data['Volume']
        else:
            close_df = pd.DataFrame(data['Close'].values, index=data.index, columns=tickers)
            open_df = pd.DataFrame(data['Open'].values, index=data.index, columns=tickers)
            high_df = pd.DataFrame(data['High'].values, index=data.index, columns=tickers)
            low_df = pd.DataFrame(data['Low'].values, index=data.index, columns=tickers)
            vol_df = pd.DataFrame(data['Volume'].values, index=data.index, columns=tickers)

        # 🚀 防爆對齊機制
        close_df = close_df.dropna(axis=1, how='all')
        valid_tickers = close_df.columns
        open_df = open_df[valid_tickers]; high_df = high_df[valid_tickers]
        low_df = low_df[valid_tickers]; vol_df = vol_df[valid_tickers]
        
        close_df = close_df.ffill(); open_df = open_df.ffill(); high_df = high_df.ffill(); low_df = low_df.ffill(); vol_df = vol_df.ffill()

        if len(close_df) < lookback_days + 10: return pd.DataFrame()

        # 基礎指標計算
        curr_ret_abs = ((close_df.iloc[-1] - close_df.iloc[-(lookback_days+1)]) / close_df.iloc[-(lookback_days+1)]) * 100
        past_ret_abs = ((close_df.iloc[-6] - close_df.iloc[-(lookback_days+6)]) / close_df.iloc[-(lookback_days+6)]) * 100
        relative_ret = curr_ret_abs - curr_ret_abs.mean() 

        high_52w = high_df.tail(252).max().replace(0, np.nan)
        dist_to_52w = (((high_52w - close_df.iloc[-1]) / high_52w) * 100).fillna(999)
        avg_vol_20 = vol_df.tail(20).mean().replace(0, np.nan)
        rvol = (vol_df.iloc[-1] / avg_vol_20).fillna(0)
        prev_close = close_df.iloc[-2].replace(0, np.nan)
        gap_pct = (((open_df.iloc[-1] - prev_close) / prev_close) * 100).fillna(0)

        ret_t0 = ((close_df.iloc[-1] - close_df.iloc[-(lookback_days+1)]) / close_df.iloc[-(lookback_days+1)]) * 100
        ret_t1 = ((close_df.iloc[-2] - close_df.iloc[-(lookback_days+2)]) / close_df.iloc[-(lookback_days+2)]) * 100
        ret_t2 = ((close_df.iloc[-3] - close_df.iloc[-(lookback_days+3)]) / close_df.iloc[-(lookback_days+3)]) * 100
        streak_3d = (ret_t0.rank(ascending=False) < ret_t1.rank(ascending=False)) & (ret_t1.rank(ascending=False) < ret_t2.rank(ascending=False))

        idx_200d = -201 if len(close_df) >= 201 else 0
        ret_200d = ((close_df.iloc[-1] - close_df.iloc[idx_200d]) / close_df.iloc[idx_200d]) * 100

        # ==================================================
        # 👑 爺爺究極大腦：19 大公仔全線向量化極速運算
        # ==================================================
        c = close_df; o = open_df; h = high_df; l = low_df; v = vol_df
        pct = c.pct_change().fillna(0); change = pct * 100
        ma20_v = v.rolling(20).mean(); ma60_v = v.rolling(60).mean()
        v_std20 = v.rolling(20).std(); v_upper = ma20_v + (2.0 * v_std20)
        
        var1 = c - l; var2 = h - c; var3 = np.maximum(h - l, 0.001)
        buyvol = v * var1 / var3; sellvol = v * var2 / var3; netvol = buyvol - sellvol
        netma10 = netvol.rolling(10).mean()

        is_burst = (v > v_upper) & (v > ma60_v * 1.9) & (abs(change) > 2.0)
        is_magenta = is_burst & (c <= o); is_cyan = is_burst & (c > o)

        ma_ttm = c.rolling(20).mean(); std_ttm = c.rolling(20).std(); atr_ttm = (h - l).rolling(20).mean()
        is_squeezing = (ma_ttm + 2*std_ttm < ma_ttm + 1.5*atr_ttm) & (ma_ttm - 2*std_ttm > ma_ttm - 1.5*atr_ttm)

        ma63 = c.rolling(63).mean(); ma126 = c.rolling(126).mean(); ma189 = c.rolling(189).mean(); ma252 = c.rolling(252).mean()
        rs_secret = (2*c/ma63.replace(0, np.nan)) + (c/ma126.replace(0, np.nan)) + (c/ma189.replace(0, np.nan)) + (c/ma252.replace(0, np.nan))
        power_secret = rs_secret - 5; is_cruise = power_secret > 0.5

        a_point = h.shift(2).rolling(8).max()
        is_breakout = (c > a_point) & (c.shift(1) <= a_point)

        cond_cyan_icon = is_cyan.iloc[-1] & (netvol.iloc[-1] > netvol.rolling(10).mean().iloc[-1])
        cond_narrow_icon = (netma10.iloc[-1] > netma10.shift(1).iloc[-1]) & ((var3.iloc[-1] / l.iloc[-1] * 100) < 1.5)
        cond_shield_icon = (change.iloc[-1] < 0) & (netvol.iloc[-1] > 0)
        cond_vcp_icon = (netma10.iloc[-1] > 0) & (netma10.shift(1).iloc[-1] < 0) & (v.iloc[-1] < ma20_v.iloc[-1])
        cond_pit_icon = (change.iloc[-1] < -1) & is_magenta.iloc[-1]
        
        cond_whale_icon = ((v.tail(10) > ma60_v.tail(10) * 1.5) & (netvol.tail(10) > 0)).sum() > 0
        cond_lucky = netvol.tail(20).sum() > 0

        cond_squeeze = is_squeezing.iloc[-1]
        cond_cruise = is_cruise.iloc[-1]
        cond_breakout = is_breakout.iloc[-1]

        cond_lion = (c.iloc[-1] > o.iloc[-1]) & (c.iloc[-1] >= h.iloc[-1] - (h.iloc[-1] - l.iloc[-1]) * 0.3)
        cond_bomb = (c.tail(20).std() / c.tail(20).mean()) < 0.035

        df = pd.DataFrame({
            'Ticker': valid_tickers,
            'Abs_Return': curr_ret_abs.values,
            'Current_Return': relative_ret.values,
            'Past_Abs': past_ret_abs.values,
            'Rank_200d': ret_200d.values,
            'RVOL': rvol.values,
            'Dist_52W': dist_to_52w.values,
            'Gap': gap_pct.values,
            'Streak': streak_3d.values,
            'Lion': cond_lion.fillna(False).values,
            'Bomb': cond_bomb.fillna(False).values,
            'I_Cyan': cond_cyan_icon.fillna(False).values,
            'I_Narrow': cond_narrow_icon.fillna(False).values,
            'I_Shield': cond_shield_icon.fillna(False).values,
            'I_VCP': cond_vcp_icon.fillna(False).values,
            'I_Pit': cond_pit_icon.fillna(False).values,
            'I_Whale': cond_whale_icon.fillna(False).values,
            'Lucky': cond_lucky.fillna(False).values, 
            'I_Squeeze': cond_squeeze.fillna(False).values,
            'I_Cruise': cond_cruise.fillna(False).values,
            'I_Breakout': cond_breakout.fillna(False).values,
        })
        
        df = df.fillna(0)

        df['Current_Rank'] = df['Abs_Return'].rank(ascending=False, method='min')
        df['Past_Rank'] = df['Past_Abs'].rank(ascending=False, method='min')
        df['Rank_Change'] = df['Past_Rank'] - df['Current_Rank']
        top_10_threshold = max(1, int(len(df) * 0.1))

        # ==================================================
        # 👑 爺爺防彈庫：黃金新星 (✨🆕) 動態記憶追蹤
        # ==================================================
        today_str = datetime.now().strftime("%Y-%m-%d")
        today_date = datetime.strptime(today_str, "%Y-%m-%d")
        memory_file = "hunt_memory.json"
        hunt_memory = {}
        
        if os.path.exists(memory_file):
            try:
                with open(memory_file, 'r', encoding='utf-8') as f:
                    hunt_memory = json.load(f)
            except: pass

        is_hk_target = "港股" in category_name
        threshold = 30 if is_hk_target else 50
        meet_criteria = (df['RVOL'] >= 1.5) & (df['Rank_Change'] >= threshold)
        qualified_tickers = df[meet_criteria]['Ticker'].tolist()

        for t in qualified_tickers:
            if t not in hunt_memory:
                hunt_memory[t] = today_str

        try:
            with open(memory_file, 'w', encoding='utf-8') as f:
                json.dump(hunt_memory, f, ensure_ascii=False)
        except: pass

        is_new_star = []
        for t in df['Ticker']:
            if t in hunt_memory:
                first_seen = datetime.strptime(hunt_memory[t], "%Y-%m-%d")
                if (today_date - first_seen).days <= 3:
                    is_new_star.append(True)
                else:
                    is_new_star.append(False)
            else:
                is_new_star.append(False)
        df['NewStar'] = is_new_star

        # 🚀 爺爺字串工廠：5 行無敵闊落大字版，防手機疊字！
        def generate_label(row):
            chg = int(row['Rank_Change'])
            ticker = row['Ticker']
            
            # --- Line 1: 排名 + 代號 ---
            if chg >= 30: icon = f"🟢 ▲ {chg}"
            elif chg <= -30: icon = f"🔵 ▼ {abs(chg)}"
            elif chg > 0: icon = f"▲ {chg}"
            elif chg < 0: icon = f"▼ {abs(chg)}"
            else: icon = "- 0"

            is_rocket = (row['Rank_200d'] <= top_10_threshold) and (chg > 0)
            rocket = "🦅 " if is_rocket else ""
            
            # --- Line 2: 動力與跳空 ---
            line2_tags = []
            if row['RVOL'] >= 3.0: line2_tags.append(f"[{row['RVOL']:.1f}x 🔋🔋]")
            elif row['RVOL'] >= 1.5: line2_tags.append(f"[{row['RVOL']:.1f}x 🔋]")
            if abs(row['Gap']) >= 1.5: line2_tags.append(f"[⚡ GAP {row['Gap']:+.1f}%]")

            # --- Line 3: 強勢與破頂 ---
            line3_tags = []
            if row['Streak']: line3_tags.append("[🔥 連續強勢]")
            if row['Dist_52W'] <= 3.0: line3_tags.append("[⚔️ 準破頂]")
            if row['NewStar']: line3_tags.append("[✨🆕 黃金新星]")

            # --- Line 4: 獵龍新徽章 ---
            line4_tags = []
            if row['Lion']: line4_tags.append("[🦁 雄獅收高]")
            if row['Bomb']: line4_tags.append("[💣 引爆在即]")
            if row['Abs_Return'] > 5.0: line4_tags.append("[🥇 金牌認證]")

            # --- Line 5: 神殿隱藏籌碼 ---
            line5_tags = []
            if row['I_Breakout']: line5_tags.append("[🪃]")
            if row['I_Squeeze']: line5_tags.append("[🤐]")
            if row['I_Cruise']: line5_tags.append("[🏎️]")
            if row['I_Cyan']: line5_tags.append("[💰🔥]")
            if row['I_Narrow']: line5_tags.append("[💰🤫]")
            if row['I_Shield']: line5_tags.append("[💰🛡️]")
            if row['I_VCP']: line5_tags.append("[🧧]")
            if row['I_Pit']: line5_tags.append("[💎/😱]")
            if row['I_Whale']: line5_tags.append("[🐋 巨鯨]")
            elif row['Lucky']: line5_tags.append("[🧧]")

            # 組裝最終 5 行 HTML 字串 (字體加大到 12px)
            final_label = f"<b>{icon} | {rocket}{ticker}</b>"
            if line2_tags:
                final_label += f"<br><span style='color:#cccccc;font-size:12px;'>{' '.join(line2_tags)}</span>"
            if line3_tags:
                final_label += f"<br><span style='color:#ffaa00;font-size:12px;'>{' '.join(line3_tags)}</span>"
            if line4_tags:
                final_label += f"<br><span style='color:#ffcc00;font-size:12px;'>{' '.join(line4_tags)}</span>"
            if line5_tags:
                final_label += f"<br><span style='color:#888888;font-size:12px;'>{' '.join(line5_tags)}</span>"
                
            return final_label

        df['Display_Label'] = df.apply(generate_label, axis=1)
        df = df[df['Display_Label'].notna()]
        df = df.sort_values(by='Current_Return', ascending=False).reset_index(drop=True)

        if is_sector_battle:
            n_30 = max(1, int(len(df) * 0.3))
            sep = pd.DataFrame([{'Ticker':'...', 'Current_Return':0, 'Display_Label':'✂️ 中間隱藏雜訊區域 ✂️'}])
            df = pd.concat([df.head(n_30), sep, df.tail(n_30)], ignore_index=True)
            
            top_performers = df.head(n_30)
            if len(top_performers) >= 3:
                df.loc[:n_30-1, 'Display_Label'] = df.loc[:n_30-1, 'Display_Label'] + " 📊"

        return df.iloc[::-1].reset_index(drop=True)

# =======================================================
# 💰 爺爺全新研發：大戶資金流透視 (福德金字塔) 掃描器
# =======================================================
def scan_fude_logic(df, ticker):
    if df is None or len(df) < 200:
        return None 
        
    d = df.copy() 
    
    d['TP'] = (d['High'] + d['Low'] + d['Close']) / 3
    d['MF'] = d['TP'] * d['Volume']
    d['Net_Flow'] = d['MF'] * np.where(d['Close'] > d['Close'].shift(1).fillna(d['Close']), 1, -1)
    d['VWAP_20'] = d['MF'].rolling(20).sum() / np.maximum(d['Volume'].rolling(20).sum(), 1)
    
    d['Force_Index'] = (d['Close'] - d['Close'].shift(1)) * d['Volume']
    d['Merit_20'] = d['Force_Index'].rolling(20).sum()
    d['Merit_60'] = d['Force_Index'].rolling(60).sum()
    d['Merit_200'] = d['Force_Index'].rolling(200).sum()
    
    var3 = np.maximum(d['High'] - d['Low'], 0.001)
    clv = ((d['Close'] - d['Low']) - (d['High'] - d['Close'])) / var3
    d['AD'] = clv * d['Volume']
    d['CMF_20'] = d['AD'].rolling(20).sum() / np.maximum(d['Volume'].rolling(20).sum(), 1)
    d['CMF_60'] = d['AD'].rolling(60).sum() / np.maximum(d['Volume'].rolling(60).sum(), 1)
    
    d['OBV_Daily'] = (np.sign(d['Close'].diff()).fillna(0) * d['Volume'])
    d['OBV_Cum'] = d['OBV_Daily'].cumsum()

    d['Vol_200MA'] = d['Volume'].rolling(200).mean()
    d['RVOL'] = d['Volume'] / np.maximum(d['Vol_200MA'], 1)
    
    recent_200 = d.tail(200)
    counts, bins = np.histogram(recent_200['Close'], bins=40, weights=recent_200['Volume'])
    poc_idx = np.argmax(counts)
    poc_price = (bins[poc_idx] + bins[poc_idx+1]) / 2

    def safe_pct(c, p):
        if p == 0 or pd.isna(p): return 0.0
        return ((c - p) / abs(p)) * 100

    def get_flow_stats(period):
        if len(d) < period: return 0.0, 0.0
        c_flow = d['Net_Flow'].tail(period).sum()
        p_flow = d['Net_Flow'].iloc[-(period*2):-period].sum() if len(d) >= period*2 else c_flow
        return c_flow, safe_pct(c_flow, p_flow)

    f20_v, f20_p = get_flow_stats(20)
    f60_v, f60_p = get_flow_stats(60)
    f200_v, f200_p = get_flow_stats(200)

    def calc_shares(flow_val, period):
        avg_p = d['Close'].tail(period).mean()
        if avg_p == 0 or np.isnan(avg_p): return 0
        raw_shares = flow_val / avg_p
        return int(np.round(raw_shares / 1000) * 1000)

    s20 = calc_shares(f20_v, 20)
    s60 = calc_shares(f60_v, 60)
    s200 = calc_shares(f200_v, 200)

    def get_obv_stats(period):
        if len(d) < period: return 0.0, 0.0
        c_obv = d['OBV_Daily'].tail(period).sum()
        p_obv = d['OBV_Daily'].iloc[-(period*2):-period].sum() if len(d) >= period*2 else c_obv
        return c_obv, safe_pct(c_obv, p_obv)

    o20_v, o20_p = get_obv_stats(20)
    o60_v, o60_p = get_obv_stats(60)
    o200_v, o200_p = get_obv_stats(200)

    avg_252 = max(d['Volume'].tail(252).mean(), 1)
    def get_ej_stats(period):
        if len(d) < period: return 50.0, 0.0
        curr_ej = (d['Volume'].tail(period).mean() / avg_252) * 100
        prev_ej = (d['Volume'].iloc[-(period*2):-period].mean() / avg_252) * 100 if len(d) >= period*2 else curr_ej
        curr_ej = min(999.0, max(0.0, curr_ej))
        prev_ej = min(999.0, max(0.0, prev_ej))
        return curr_ej, safe_pct(curr_ej, prev_ej)

    ej20, ej20_p = get_ej_stats(20)
    ej60, ej60_p = get_ej_stats(60)
    ej200, ej200_p = get_ej_stats(200)

    def get_se_stats(period):
        if len(d) < period + 1: return 75.0, 0.0
        pct_chg = d['Close'].pct_change().fillna(0)
        curr_se = 75.0 + (pct_chg.tail(period).sum() * 100)
        prev_se = 75.0 + (pct_chg.iloc[-(period*2):-period].sum() * 100) if len(d) >= period*2 else curr_se
        curr_se = min(999.0, max(0.1, curr_se))
        prev_se = min(999.0, max(0.1, prev_se))
        return curr_se, safe_pct(curr_se, prev_se)

    se20, se20_p = get_se_stats(20)
    se60, se60_p = get_se_stats(60)
    se200, se200_p = get_se_stats(200)

    def get_conc_stats(period):
        if len(d) < period: return 0.0, 0.0
        da = abs(d['Net_Flow'].tail(period))
        curr_conc = (da.max() / max(da.sum(), 1)) * 100
        if len(d) < period * 2: return curr_conc, 0.0
        da_prev = abs(d['Net_Flow'].iloc[-(period*2):-period])
        prev_conc = (da_prev.max() / max(da_prev.sum(), 1)) * 100
        return curr_conc, safe_pct(curr_conc, prev_conc)

    c20, c20_p = get_conc_stats(20)
    c60, c60_p = get_conc_stats(60)
    c200, c200_p = get_conc_stats(200)

    if f20_v > 0: mood = "💪 明目張膽買貨" if c20 > 25 else "🤫 默默暗中吸籌"
    else: mood = "😱 明目張膽掟貨" if c20 > 25 else "📉 默默分批派發"

    curr_c = d['Close'].iloc[-1]
    m20 = d['Merit_20'].iloc[-1]; m60 = d['Merit_60'].iloc[-1]; m200 = d['Merit_200'].iloc[-1]
    m20_prev = d['Merit_20'].iloc[-2] if len(d) > 2 else 0
    vwap_20 = d['VWAP_20'].iloc[-1]
    
    if m20 > 0 and m60 > 0 and m200 > 0:
        fude_lvl, fude_col, fude_desc = "🌟 福德深厚 (大金主)", "#FFD700", "三線資金皆正，長中短大戶齊心建倉，身家極厚。"
    elif m200 > 0 and m60 > 0 and m20 <= 0:
        fude_lvl, fude_col, fude_desc = "🕳️ 黃金坑 (長線好,短線洗)", "#00FFCC", "長中線底氣強大，短線游資流出僅為震倉，留意低吸。"
    elif m20 > 0 and m200 <= 0:
        fude_lvl, fude_col, fude_desc = "💨 虛火熱錢 (短線強,家底薄)", "#FF4B4B", "長線大戶派發中，只靠短線游資炒作，慎防接火棒。"
    else:
        fude_lvl, fude_col, fude_desc = "🥀 無主孤魂 (資金流失)", "#888888", "三線資金皆負，大戶徹底放棄，切勿胡亂撈底。"
    
    tags = []
    if m200 > 0 and m60 > 0: tags.append("<span style='background:#111; border:1px solid #FFD700; color:#FFD700; padding:5px 10px; border-radius:5px;'>🌟 名門望族</span>")
    if m20 > m20_prev: tags.append("<span style='background:#111; border:1px solid #FF4B4B; color:#FF4B4B; padding:5px 10px; border-radius:5px;'>🔥 熱錢湧入</span>")
    if curr_c > vwap_20: tags.append("<span style='background:#111; border:1px solid #00FFCC; color:#00FFCC; padding:5px 10px; border-radius:5px;'>🛡️ 跌不破位</span>")
    if m20 > 0 and m200 < 0: tags.append("<span style='background:#111; border:1px solid #FF00FF; color:#FF00FF; padding:5px 10px; border-radius:5px;'>⚠️ 虛有其表</span>")
    
    plot_data = d.tail(120)[['Open', 'High', 'Low', 'Close', 'Volume', 'VWAP_20', 'RVOL', 'Merit_20', 'Merit_60', 'Merit_200', 'CMF_20', 'CMF_60', 'Net_Flow', 'OBV_Daily']]
    
    return {
        "Ticker": ticker,
        "Current_Price": curr_c,
        "POC_Price": poc_price,
        "VWAP_20": vwap_20,
        "Merit_20": m20,
        "Merit_60": m60,
        "Merit_200": m200,
        "CMF_20": d['CMF_20'].iloc[-1],
        "CMF_60": d['CMF_60'].iloc[-1],
        "Fude_Level": fude_lvl,
        "FColor": fude_col, 
        "Fude_Color": fude_col,
        "Fude_Desc": fude_desc,
        "Tags": tags,
        "Flow_20_val": f20_v, "Flow_20_pct": f20_p, 
        "Flow_60_val": f60_v, "Flow_60_pct": f60_p, 
        "Flow_200_val": f200_v, "Flow_200_pct": f200_p,
        "OBV_20_val": o20_v, "OBV_20_pct": o20_p, 
        "OBV_60_val": o60_v, "OBV_60_pct": o60_p, 
        "OBV_200_val": o200_v, "OBV_200_pct": o200_p,
        "EJ_20": ej20, "EJ_20_pct": ej20_p,
        "EJ_60": ej60, "EJ_60_pct": ej60_p,
        "EJ_200": ej200, "EJ_200_pct": ej200_p,
        "SE_20": se20, "SE_20_pct": se20_p,
        "SE_60": se60, "SE_60_pct": se60_p,
        "SE_200": se200, "SE_200_pct": se200_p,
        "Conc_20": c20, "Conc_20_pct": c20_p,
        "Conc_60": c60, "Conc_60_pct": c60_p,
        "Conc_200": c200, "Conc_200_pct": c200_p,
        "Shares_20": s20, "Shares_60": s60, "Shares_200": s200,
        "Mood": mood,
        "Plot_Data": plot_data
    }
