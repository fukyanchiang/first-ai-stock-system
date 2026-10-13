import os
import pandas as pd
import numpy as np
import yfinance as yf
import streamlit as st
from datetime import datetime
import warnings
warnings.filterwarnings('ignore')

# ==========================================
# 🛸 1. 內置天外飛仙 RS 核心演算法
# ==========================================
def run_tianwai_feixian(df: pd.DataFrame, sctr_rank_from_master: float = 0.0, cross_down_90: bool = False) -> pd.DataFrame:
    df = df.sort_index().copy()
    df.ffill(inplace=True)
    df.bfill(inplace=True)
    
    C = df['Close']
    O = df['Open']
    H = df['High']
    L = df['Low']
    V = df['Volume']

    def MA(s, n): return s.rolling(window=n, min_periods=1).mean() 
    def EMA(s, n): return s.ewm(span=n, adjust=False).mean()
    def SMA(s, n, m=1): return s.ewm(alpha=m/n, adjust=False).mean()
    def HHV(s, n): return s.rolling(window=n, min_periods=1).max()
    def LLV(s, n): return s.rolling(window=n, min_periods=1).min()
    def STD(s, n): return s.rolling(window=n, min_periods=1).std()
    
    def CROSS(s1, s2):
        if isinstance(s1, (int, float)): s1 = pd.Series(s1, index=df.index)
        if isinstance(s2, (int, float)): s2 = pd.Series(s2, index=df.index)
        return (s1 > s2) & (s1.shift(1).bfill() <= s2.shift(1).bfill())
        
    def COUNT(cond, n): 
        return cond.fillna(False).astype(int).rolling(window=n, min_periods=1).sum()
        
    def BARSLAST(cond):
        idx = np.arange(len(cond))
        last_true = pd.Series(np.where(cond, idx, np.nan), index=cond.index).ffill()
        return pd.Series(idx - last_true, index=cond.index).fillna(9999)
        
    def FORCAST(S, N):
        w = np.arange(1, N + 1) - (N + 1) / 2.0
        w2_sum = np.sum(w ** 2)
        if w2_sum == 0: return S
        slope_num = pd.Series(0.0, index=S.index)
        for i in range(N):
            slope_num += w[i] * S.shift(N - 1 - i).bfill().fillna(0)
        slope = slope_num / w2_sum
        return S.rolling(N, min_periods=1).mean() + slope * (N - 1) / 2.0

    MA10, MA20 = MA(C, 10), MA(C, 20)
    MA50, MA150, MA200 = MA(C, 50), MA(C, 150), MA(C, 200)

    LC = C.shift(1).bfill()
    DIFF_C = C - LC
    UP_RSI = np.where(DIFF_C > 0, DIFF_C, 0)
    ABS_RSI = DIFF_C.abs()
    RSI_VAL = SMA(pd.Series(UP_RSI, index=df.index), 14) / (SMA(pd.Series(ABS_RSI, index=df.index), 14) + 1e-5) * 100

    L_EMA200 = EMA(C, 200)
    L_EMA_D = (C - L_EMA200) / L_EMA200 * 100
    L_EMA_S = L_EMA_D * 1.5
    L_ROC_S = (C / C.shift(125).bfill() - 1) * 20

    M_EMA50 = EMA(C, 50)
    M_EMA_S = (C - M_EMA50) / M_EMA50 * 30
    M_ROC_S = (C / C.shift(20).bfill() - 1) * 30

    PPO_F = EMA(C, 12)
    PPO_S = EMA(C, 26)
    PPO_V = (PPO_F - PPO_S) / PPO_S * 100
    S_PPO_S = (PPO_V - PPO_V.shift(3).bfill()) * 5

    S_RSI_S = (RSI_VAL - 50) * 0.5

    S_TOTAL_4_0 = (L_EMA_S + L_ROC_S + M_EMA_S + M_ROC_S + S_PPO_S + S_RSI_S)
    SCTR_RAW_4_0 = (S_TOTAL_4_0 / 10) + 50

    FINAL_SCTR_RANK = pd.Series(sctr_rank_from_master, index=df.index)
    SCTR_RISING = SCTR_RAW_4_0 >= SCTR_RAW_4_0.shift(1).fillna(0)

    HHV_250 = HHV(H, 250)
    LLV_250 = LLV(L, 250)
    
    ABOVE_BOTTOM = C > (LLV_250 * 1.25)
    NEAR_HIGH = C > (HHV_250 * 0.75)
    MA150_RISING = MA150 > MA150.shift(10).fillna(MA150) * 1.002
    UPTREND_120 = C > C.shift(120).fillna(0)
    STAGE2 = (C > MA50) & (MA50 > MA150) & (MA150 > MA200) & ABOVE_BOTTOM & NEAR_HIGH & MA150_RISING & UPTREND_120

    DIF = EMA(C, 12) - EMA(C, 26)
    DEA = EMA(DIF, 9)
    MACD_VAL = (DIF - DEA) * 2
    IS_MACD_ORANGE = (MACD_VAL > 0) & (DIF > 0.001) & (DEA > 0.001)

    RS = 2 * C / MA(C, 63) + C / MA(C, 126) + C / MA(C, 189) + C / MA(C, 252)
    POWER = RS * 5

    N_TTM = 20
    VAR1 = (HHV(H, N_TTM) + LLV(L, N_TTM)) / 2 + MA(C, N_TTM)
    TTM_MOMENTUM = FORCAST(C - VAR1 / 2, N_TTM)
    TTM_STAGE2_ON = STAGE2
    IS_TTM_TRUE_ORANGE = (TTM_MOMENTUM > 0) & TTM_STAGE2_ON

    IS_CORE_MATCH = STAGE2 & IS_MACD_ORANGE & IS_TTM_TRUE_ORANGE

    group_keys = (~IS_CORE_MATCH).cumsum()
    streak_series = IS_CORE_MATCH.groupby(group_keys).cumsum()

    IS_HOT_WINDOW = (streak_series >= 1) & (streak_series <= 3)
    IS_COOL_WINDOW = (streak_series >= 4) & (streak_series <= 10)
    
    IS_SCTR_PRIVILEGE = (FINAL_SCTR_RANK >= 90) & SCTR_RISING & (~IS_HOT_WINDOW)
    
    IS_TRUE_EMPEROR = (FINAL_SCTR_RANK >= 85) & (FINAL_SCTR_RANK < 90)
    IS_TRUE_DRAGON = (FINAL_SCTR_RANK >= 90)

    STATE_SERIES = pd.Series(np.where(IS_HOT_WINDOW, 1, np.where(IS_COOL_WINDOW, 2, np.where(IS_SCTR_PRIVILEGE, 3, 0))), index=df.index)

    VOL_MA20 = MA(V, 20)
    DAY_AMP = (H - L) / (C.shift(1).bfill() + 1e-5) * 100
    AMP_SQUEEZE = DAY_AMP < (MA(DAY_AMP, 20) * 0.75)
    VOL_SQUEEZE = V < (VOL_MA20 * 0.75)
    TR_VAL = pd.concat([H - L, (H - C.shift(1).bfill()).abs(), (L - C.shift(1).bfill()).abs()], axis=1).max(axis=1)
    ATR20 = MA(TR_VAL, 20)
    BOLLING_BAND = MA20 + 2 * STD(C, 20)
    KELTNER_BAND = MA20 + 1.5 * ATR20
    TTM_SQUEEZE = BOLLING_BAND < KELTNER_BAND
    WAS_SQUEEZED = COUNT(AMP_SQUEEZE & VOL_SQUEEZE & TTM_SQUEEZE, 5) >= 1
    
    TF_BUY_SP = C - L
    TF_SELL_SP = H - C
    INNER_POWER = (TF_BUY_SP > TF_SELL_SP) | ((C - L) / (H - L + 1e-5) > 0.60)
    STOCK_DELTA = C - C.shift(1).bfill()
    DELTA_ACC = STOCK_DELTA * STOCK_DELTA.shift(1).bfill()
    DELTA_POWER = (DELTA_ACC > 0) & (C > O)
    BETA_OK = (MA(TR_VAL, 14) / (MA20 + 1e-5)) * 100 > 1.2
    SPRING_READY = STAGE2 & WAS_SQUEEZED & BETA_OK
    SPRING_SIGNAL = SPRING_READY & INNER_POWER & DELTA_POWER

    MA200_UP = MA200 > MA200.shift(20).fillna(0)
    VCP_STAGE2 = STAGE2 & MA200_UP
    AMP_BIG = (HHV(H, 30) - LLV(L, 30)) / (LLV(L, 30) + 1e-5) * 100
    AMP_NARROW = (HHV(H, 8) - LLV(L, 8)) / (LLV(L, 8) + 1e-5) * 100
    VCP_READY = (AMP_NARROW <= AMP_BIG * 0.65) & (AMP_NARROW <= 10)
    SURGE_MOM = (C / (LLV(L, 40).shift(10).bfill() + 1e-5)) > 1.9
    FLAG_AMP = (HHV(H, 12) - LLV(L, 12)) / (LLV(L, 12) + 1e-5) * 100
    HTF_READY = VCP_STAGE2 & SURGE_MOM & (FLAG_AMP < 20)
    MAV20 = MA(V, 20)
    RECENT_HIGH = HHV(H, 10).shift(1).bfill()
    BREAKOUT = CROSS(C, RECENT_HIGH) & (V > MAV20 * 1.3)
    
    IS_VCP = BREAKOUT & VCP_READY.shift(1).fillna(False)
    IS_HTF = BREAKOUT & HTF_READY.shift(1).fillna(False)
    IS_BOTH = IS_VCP & IS_HTF
    ONLY_VCP = IS_VCP & (~IS_BOTH)
    ONLY_HTF = IS_HTF & (~IS_BOTH)
    GATHERING = HTF_READY | VCP_READY
    RECENT_GATHER = COUNT(GATHERING, 5) >= 1
    BIG_YANG = (C / (C.shift(1).bfill() + 1e-5)) > 1.04
    REAL_BREAK = (C > RECENT_HIGH) & BIG_YANG
    DRAGON = REAL_BREAK & RECENT_GATHER & (~BREAKOUT)
    EX_MEM = COUNT(GATHERING, 15) >= 1
    NEW_HIGH_15 = C > HHV(H, 15).shift(1).bfill()
    IS_SNDK = NEW_HIGH_15 & EX_MEM & (~BREAKOUT) & (~DRAGON)
    NEW_HIGH_20 = C > HHV(H, 20).shift(1).bfill()
    SINGLE_SURGE = (C / (C.shift(1).bfill() + 1e-5)) > 1.05
    IS_ULTIMATE = VCP_STAGE2 & EX_MEM & NEW_HIGH_20 & SINGLE_SURGE & (~BREAKOUT)
    PARABOLIC_TREND = (C > MA20) & (MA20 > MA50)
    RECENT_SURGE = (C / (LLV(L, 30).shift(5).bfill() + 1e-5)) > 1.5
    TODAY_STRONG_BREAK = (C > HHV(H, 10).shift(1).bfill()) & (C > O) & ((C / (C.shift(1).bfill() + 1e-5)) > 1.03)
    IS_PARABOLIC = (PARABOLIC_TREND & RECENT_SURGE & TODAY_STRONG_BREAK & (~BREAKOUT) & (~IS_ULTIMATE) & (~IS_SNDK) & (~DRAGON))
    
    N_YANG_COND = ((C / (C.shift(1).bfill() + 1e-5)) >= 1.04) & (C > O)
    N_PREV_DAYS = BARSLAST(N_YANG_COND).shift(1).fillna(0) + 1
    N_TARGET_HIGH = pd.Series(np.where(N_YANG_COND, H, np.nan), index=df.index).ffill().shift(1).bfill()
    N_BREAK = (N_PREV_DAYS <= 20) & (C > N_TARGET_HIGH) & (C.shift(1).bfill() <= N_TARGET_HIGH) & (C > O)
    
    ALL_PREV = ONLY_VCP | ONLY_HTF | IS_BOTH | DRAGON | IS_SNDK | IS_ULTIMATE | IS_PARABOLIC
    IS_N_SHAPE = VCP_STAGE2 & N_BREAK & (~ALL_PREV)
    
    BULL_TREND = (MA50 > MA150) & (MA150 > MA200) & MA200_UP
    SHORT_WASH = COUNT(MA10 < MA20, 3) >= 1
    SHORT_EVE = (MA10 <= MA20) & ((MA10 + (MA10 - MA10.shift(1).bfill())) > (MA20 + (MA20 - MA20.shift(1).bfill()))) & (C > O)
    MID_WASH = COUNT(MA20 < MA50, 5) >= 1
    MID_EVE = (MA20 <= MA50) & ((MA20 + (MA20 - MA20.shift(1).bfill())) > (MA50 + (MA50 - MA50.shift(1).bfill()))) & (C > O)
    IS_AMBUSH = (BULL_TREND & ((SHORT_WASH & SHORT_EVE) | (MID_WASH & MID_EVE)) & (~ALL_PREV) & (~IS_N_SHAPE))
    BIG_MONEY_IN = (V >= MAV20 * 1.5) & (C > O)
    ANY_BUY = ALL_PREV | IS_N_SHAPE | IS_AMBUSH
    SHOW_BIG_MONEY = ANY_BUY & BIG_MONEY_IN

    TYP_V = (H + L + C) / 3
    V1 = pd.Series(np.where(TYP_V > TYP_V.shift(1).bfill(), TYP_V * V, 0), index=df.index)
    V2 = pd.Series(np.where(TYP_V < TYP_V.shift(1).bfill(), TYP_V * V, 0), index=df.index)
    MFI_V = 100 * V1.rolling(14, min_periods=1).sum() / (V1.rolling(14, min_periods=1).sum() + V2.rolling(14, min_periods=1).sum() + 1e-5)
    
    OBV_DIR = np.where(C > C.shift(1).bfill(), V, np.where(C < C.shift(1).bfill(), -V, 0))
    OBV_RAW = EMA(pd.Series(OBV_DIR, index=df.index).rolling(120, min_periods=1).sum(), 3)
    MAX_OBV = HHV(OBV_RAW, 120)
    MIN_OBV = LLV(OBV_RAW, 120)
    OBV_NORM = (OBV_RAW - MIN_OBV) / (MAX_OBV - MIN_OBV + 1e-5) * 100
    OBV_SIG = MA(OBV_NORM, 20)
    SMART_BUY = CROSS(OBV_NORM, OBV_SIG) & (MFI_V > 40)

    VA_OBV = pd.Series(OBV_DIR, index=df.index)
    OBV_LINE = VA_OBV.rolling(250, min_periods=1).sum()
    OBV_HHV = HHV(OBV_LINE, 30).shift(1).bfill()
    OBV_BREAK = CROSS(OBV_LINE, OBV_HHV) & STAGE2
    PRICE_NOT_HIGH = C < HHV(C, 10).fillna(C)
    SMART_ACC = OBV_BREAK & PRICE_NOT_HIGH
    FUND_BREAK = OBV_BREAK & (~PRICE_NOT_HIGH)

    POC_LINE = (TYP_V * V).rolling(50, min_periods=1).sum() / (V.rolling(50, min_periods=1).sum() + 1e-5)
    VOL_VAR = (V * (TYP_V - POC_LINE)**2).rolling(50, min_periods=1).sum() / (V.rolling(50, min_periods=1).sum() + 1e-5)
    VOL_STD = np.sqrt(VOL_VAR)
    VAH_LINE = POC_LINE + 1.0 * VOL_STD
    BULL_BREAK = STAGE2 & CROSS(C, VAH_LINE) & (V > MA(V, 5).fillna(0))

    VOLMA20_BIG = MA(V, 20)
    CSPRE = (C - O).abs()
    AVGS = MA(CSPRE, 20)
    ISBIG = (V > VOLMA20_BIG.fillna(0) * 1.5) & (C > O) & (CSPRE > AVGS.fillna(0))

    S_EMA20 = EMA(C, 20)
    S_E5, S_E10 = EMA(C, 5), EMA(C, 10)
    S_INST_VOL = V > (MA(V, 5).fillna(0) * 1.2)
    S_STRONG_K = (C > O) & ((C - L) > (H - L) * 0.50)
    S_CROSS = CROSS(C, S_EMA20) | ((C > S_EMA20) & CROSS(S_E5, S_E10))
    S_PULLBACK = (L <= S_EMA20) & (C > S_EMA20) & (C > O)
    SP_BUY = STAGE2 & S_INST_VOL & S_STRONG_K & (S_CROSS | S_PULLBACK)

    MAVOL20_HUGE = MA(V, 20)
    IS_HUGE_VOL = V > (MAVOL20_HUGE.fillna(0) * 2.0)
    HUGE_VOL_SIGNAL = IS_HUGE_VOL & (C >= O)

    DMI_HD = H - H.shift(1).bfill()
    DMI_LD = L.shift(1).bfill() - L
    DMP_RAW = pd.Series(np.where((DMI_HD > 0) & (DMI_HD > DMI_LD), DMI_HD, 0), index=df.index)
    DMM_RAW = pd.Series(np.where((DMI_LD > 0) & (DMI_LD > DMI_HD), DMI_LD, 0), index=df.index)
    DMI_TR = TR_VAL.rolling(14, min_periods=1).sum()
    PDI_VAL = DMP_RAW.rolling(14, min_periods=1).sum() * 100 / (DMI_TR + 1e-5)
    MDI_VAL = DMM_RAW.rolling(14, min_periods=1).sum() * 100 / (DMI_TR + 1e-5)
    ADX_RAW = MA((MDI_VAL - PDI_VAL).abs() / (MDI_VAL + PDI_VAL + 1e-5) * 100, 6)
    DMI_BULL_CROSS = CROSS(ADX_RAW, 25) & (PDI_VAL > MDI_VAL) & (PDI_VAL - MDI_VAL > 3)
    DMI_BULL_FLIP = CROSS(PDI_VAL, MDI_VAL) & (ADX_RAW >= 25) & (PDI_VAL - MDI_VAL > 3)
    DMI_IGNITE = (DMI_BULL_CROSS | DMI_BULL_FLIP) & STAGE2
    DMI_SQUEEZE = CROSS(15, ADX_RAW)

    PZ_N = 24
    PZ_MID = MA(C, PZ_N)
    PZ_STD = STD(C, PZ_N)
    PZ_UPPER = PZ_MID + 2.5 * PZ_STD
    PZ_LOWER = PZ_MID - 2.5 * PZ_STD
    PZ_ATR = MA(TR_VAL, 20)
    PZ_EXTREME = TR_VAL > PZ_ATR * 2
    PZ_RANGE = ((PZ_UPPER - PZ_LOWER) / (PZ_MID + 1e-5) * 100) < MA((PZ_UPPER - PZ_LOWER) / (PZ_MID + 1e-5) * 100, 50)
    PZ_FORCE = (C - PZ_MID) / (PZ_STD + 1e-5) * 100
    PZ_E1 = EMA(PZ_FORCE, 13)
    PZ_E2 = EMA(PZ_E1, 13)
    PZ_SIG = 2 * PZ_E1 - PZ_E2
    PZ_BUY1 = CROSS(C, PZ_UPPER) & (PZ_SIG > 50) & (V > MA(V, 20).fillna(0)) & PZ_RANGE
    PZ_BUY2 = (PZ_SIG > 50) & (C > MA10) & (C > C.shift(1).bfill()) & STAGE2 & (~PZ_EXTREME)
    PZ_BUY3 = CROSS(PZ_SIG, 50) & (C > PZ_MID) & (V > MA(V, 20).fillna(0))

    GL_RSI1 = SMA(pd.Series(np.where(C - LC > 0, C - LC, 0), index=df.index), 14) / (SMA(DIFF_C.abs(), 14) + 1e-5) * 100
    GL_MFI1 = MFI_V
    GL_RV = (GL_RSI1 + GL_MFI1) / 2 - 50
    GL_SV = EMA(GL_RV, 9)
    GL_PRO_BUY = CROSS(GL_RV, GL_SV) & STAGE2 & (ADX_RAW >= 20) & (GL_RV < 15)

    WK_EMA200 = EMA(C, 200)
    WK_BEAR = (C < WK_EMA200) | (MA50.fillna(0) < WK_EMA200)
    WK_SPRING = CROSS(C, S_EMA20) & (C.shift(1).bfill() < S_EMA20) & ((V > MA(V, 5).fillna(0) * 1.2) | (V < MA(V, 20).fillna(0) * 0.6)) & (~WK_BEAR)

    KO_SAFE = (C > (C - ATR20.fillna(0) * 3.2).rolling(50, min_periods=1).max()) & (C > MA(C, 15).fillna(0))
    KO_RED_TRIANGLE = (V > MA(V, 5).fillna(0) * 1.35) & (C > O) & KO_SAFE

    FLOW_INST = STAGE2 & (C > C.shift(1).bfill()) & (V > V.shift(1).bfill()) & (V > MA(V, 50).fillna(0) * 1.5) & (C >= HHV(C.shift(1).bfill(), 20).fillna(0))
    FLOW_REAL_BUY = FLOW_INST & ((COUNT(V < MA(V, 50).fillna(0)*0.5, 10) > 0) | (TTM_MOMENTUM > TTM_MOMENTUM.shift(1).bfill()))

    NX_STAGE2 = (COUNT(C > MA150.fillna(0), 3) > 0) & (MA50.fillna(0) > MA150.fillna(0)) & (MA150.fillna(0) > MA150.shift(10).fillna(0))
    NX_RAW = (V > MA(V, 20).fillna(0) * 1.5) & ((H - L) > MA(H - L, 20).fillna(0) * 1.5)
    NX_SAFE = NX_STAGE2 & (COUNT(V < MA(V, 20).fillna(0), 10) > 0) & NX_RAW & (C >= O) & ((H - C.shift(1).bfill())/(C.shift(1).bfill() + 1e-5)*100 > 4.0)

    VSA_DEV60 = (C - MA(C, 60).fillna(C)) / (MA(C, 60).fillna(C) + 1e-5) * 100
    VSA_START = (V > MA(V, 20).fillna(0) * 1.5) & (C > O) & ((C - O).abs() > MA((C - O).abs(), 20).fillna(0)) & (VSA_DEV60 <= 15)

    TF_UPPER = MA(V, 20) + 2.0 * STD(V, 20)
    TF_FIRE = (V > TF_UPPER.fillna(0)) & (V > MA(V, 60).fillna(0) * 1.9) & ((C - C.shift(1).bfill()).abs() / (C.shift(1).bfill() + 1e-5) * 100 > 2.0) & (C > O) & (VSA_DEV60 <= 15)

    SV19_STATE = np.where((C > MA20.fillna(0)) & (MA20.fillna(0) > MA50.fillna(0)) & (MA50.fillna(0) > MA200.fillna(0)), 1, 3)
    SV19_RAW_BUY = CROSS(EMA(C, 5), EMA(C, 10)) & (V > MA(V, 5).fillna(0) * 1.2) & ((C > O) & ((C - L) > (H - L) * 0.55)) & (ATR20 > ATR20.shift(1).bfill()) & (RSI_VAL < 78)
    SV19_BUY_GREEN = SV19_RAW_BUY & (SV19_STATE == 1)

    TFM_V3 = H - L
    TFM_BUY = pd.Series(np.where(TFM_V3 > 0, V * (C - L) / (TFM_V3 + 1e-5), 0), index=df.index)
    TFM_SELL = pd.Series(np.where(TFM_V3 > 0, V * (H - C) / (TFM_V3 + 1e-5), 0), index=df.index)
    TFM_SUM_BUY = TFM_BUY.rolling(5, min_periods=1).sum()
    TFM_SUM_SELL = TFM_SELL.rolling(5, min_periods=1).sum()
    TFM_WIN = (TFM_SUM_BUY / (TFM_SUM_BUY + TFM_SUM_SELL + 1e-5)) > 0.65

    VCX_WR = (HHV(H, 14) - C) / (HHV(H, 14) - LLV(L, 14) + 1e-5) * -100
    VCX_CLIMAX = (V > HHV(V, 60).shift(1).bfill().fillna(0)) & (V > MA(V, 30).fillna(0) * 2.5) & (H >= HHV(H, 60).shift(1).bfill().fillna(0)) & (VCX_WR > -10)

    def get_bool(s): return bool(pd.Series(s).fillna(False).iloc[-1])
    
    tags = []
    # 🔴 [新增功能] 跌穿 90 警戒標籤
    if cross_down_90: tags.append("🚨跌穿90防線")
    
    if get_bool(IS_TRUE_DRAGON): tags.append("👑👑真龍")
    elif get_bool(IS_TRUE_EMPEROR): tags.append("👑真皇")
    
    if get_bool(SPRING_SIGNAL): tags.append("⚡爆邊(非💰)")
    if get_bool(SHOW_BIG_MONEY): tags.append("💰錢袋")
    if pd.Series(RSI_VAL).fillna(0).iloc[-1] > 50: tags.append("動力rsi(非💰)")
    if get_bool(SMART_BUY): tags.append("💰掃貨")
    if get_bool(SMART_ACC): tags.append("🕵️大戶吸籌")
    if get_bool(FUND_BREAK): tags.append("🌊資金突破")
    if get_bool(BULL_BREAK): tags.append("🎯牛突破")
    if get_bool(ISBIG): tags.append("BIG")
    if get_bool(SP_BUY): tags.append("🚀S+++突擊")
    if get_bool(HUGE_VOL_SIGNAL): tags.append("🔥天量")
    if get_bool(DMI_IGNITE): tags.append("🌪️主升狂飆(非💰)")
    if get_bool(DMI_SQUEEZE): tags.append("🥷潛伏觀察(非💰)")
    if get_bool(PZ_BUY1) or get_bool(PZ_BUY2) or get_bool(PZ_BUY3): tags.append("PZ綜合訊號")
    if get_bool(GL_PRO_BUY): tags.append("🚀全能點火")
    if get_bool(WK_SPRING): tags.append("⚡洗盤")
    if get_bool(KO_RED_TRIANGLE): tags.append("紅色三角")
    if get_bool(FLOW_REAL_BUY): tags.append("🔵真周線共振")
    if get_bool(NX_SAFE): tags.append("💎真動能")
    if get_bool(VSA_START): tags.append("🚀啟動")
    if get_bool(TF_FIRE): tags.append("🚀點火")
    if get_bool(SV19_BUY_GREEN): tags.append("🚀S級綠區主升")
    if get_bool(TFM_WIN): tags.append("買入兵力大勝")
    if get_bool(VCX_CLIMAX): tags.append("CLIMAX")
    if get_bool(PZ_BUY3): tags.append("★PZ特大注★")
    if get_bool(PZ_BUY2): tags.append("🚀浴火重生")
    if get_bool(PZ_BUY1): tags.append("■PZ大注■")
    
    tags_str = " | ".join(tags) if tags else ""
    
    if get_bool(IS_SCTR_PRIVILEGE):
        tags_str = "（非合乎飛仙） | " + tags_str if tags_str else "（非合乎飛仙）"

    df['天外飛仙_狀態'] = STATE_SERIES
    BASE_SCORE = np.where(IS_HOT_WINDOW, 100, np.where(IS_SCTR_PRIVILEGE, 0, np.where(IS_COOL_WINDOW, 0, -9999)))
    
    TOTAL_SCORE = BASE_SCORE + (len(tags) * 10) + FINAL_SCTR_RANK
    df['霸王總分'] = pd.Series(TOTAL_SCORE, index=df.index).fillna(-9999).astype(float)
    
    dragon_level = np.where(IS_TRUE_DRAGON, 2, np.where(IS_TRUE_EMPEROR, 1, 0))
    df['SCTR_Rank'] = FINAL_SCTR_RANK.fillna(0).round(1)
    df['SCTR_Raw_4_0'] = SCTR_RAW_4_0.fillna(0).round(1)
    df['Dragon_Level'] = pd.Series(dragon_level, index=df.index).fillna(0).astype(int)
    
    df['起爆日數'] = streak_series.fillna(0).astype(int)
    df['Power'] = POWER.fillna(0)
    df['EMA10'] = MA10.fillna(0)
    df['Bias'] = ((C - MA20) / (MA20 + 1e-5) * 100).fillna(0)
    df['RS'] = RS.fillna(0)
    df['EJ'] = TTM_MOMENTUM.fillna(0)
    df['SE'] = MACD_VAL.fillna(0)
    df['Vol_Ratio'] = (V / (VOL_MA20 + 1e-5)).fillna(0)
    
    df['天外飛仙_標籤'] = ""
    if len(df) > 0:
        df.at[df.index[-1], '天外飛仙_標籤'] = tags_str

    return df

# ==========================================
# 🌐 2. 直連 GitHub Raw 全宇宙數據庫 (🌟加入代碼清洗容錯)
# ==========================================
RAW_SCTR_URL = "https://raw.githubusercontent.com/fukyanchiang/my-cosmos-vision/main/SCTR_Master.csv"

@st.cache_data(ttl=300)
def load_sctr_master():
    try:
        df = pd.read_csv(RAW_SCTR_URL)
        # 🌟 自動清洗：增加 Ticker_Clean 欄位，強制斬走 .HK 同 .US
        if df is not None and 'Ticker' in df.columns:
            df['Ticker_Clean'] = df['Ticker'].astype(str).str.replace('.HK', '', regex=False).str.replace('.US', '', regex=False).str.strip()
            # 🛡️ 港股 5 位數暴力保護：6198 擴充為 06198
            df['Ticker_Clean_5'] = df['Ticker_Clean'].apply(lambda x: x.zfill(5) if x.isdigit() and len(x) < 5 else x)
        return df, "雲端 GitHub Raw 直連"
    except Exception as e:
        if os.path.exists("SCTR_Master.csv"):
            df = pd.read_csv("SCTR_Master.csv")
            if 'Ticker' in df.columns:
                df['Ticker_Clean'] = df['Ticker'].astype(str).str.replace('.HK', '', regex=False).str.replace('.US', '', regex=False).str.strip()
                df['Ticker_Clean_5'] = df['Ticker_Clean'].apply(lambda x: x.zfill(5) if x.isdigit() and len(x) < 5 else x)
            return df, "本地 SCTR_Master.csv 備份"
        return None, str(e)

@st.cache_data(ttl=1800)
def fetch_historical_data(tickers):
    if not tickers:
        return {}
    try:
        data = yf.download(tickers, period="1y", interval="1d", group_by='ticker', progress=False, threads=True)
        results = {}
        if len(tickers) == 1:
            t = tickers[0]
            if not data.empty and 'Close' in data:
                results[t] = data.dropna(subset=['Close'])
        else:
            for t in tickers:
                if t in data and not data[t].dropna(how='all').empty:
                    df_t = data[t].dropna(subset=['Close'])
                    if len(df_t) >= 150:
                        results[t] = df_t
        return results
    except Exception as e:
        st.error(f"⚠️ 下載行情數據失敗: {e}")
        return {}

# ==========================================
# 🎯 單一獨立市場渲染組件 (🌟加入雙重字典匹配與 90 警戒)
# ==========================================
def render_single_market_search(cat_code, cat_name, df_master):
    df_cat = df_master[df_master['Category'] == cat_code].copy()
    
    st.subheader(f"{cat_name}（庫存總計: {len(df_cat):,} 隻）")
    
    col_a, col_b = st.columns(2)
    min_sctr = col_a.slider(f"[{cat_name}] SCTR 最低門檻", 50.0, 99.0, 80.0, 1.0, key=f"sctr_{cat_code}")
    # 🌟 爺爺特別修改：將預設數量上限由 100 降至 30，徹底解決 YF 深夜塞車斷線問題！
    max_scan = col_b.slider(f"[{cat_name}] 掃描 Top 數量上限", 20, 300, 30, 10, key=f"max_{cat_code}")
    
    df_filtered = df_cat[df_cat['SCTR'] >= min_sctr].sort_values(by='SCTR', ascending=False)
    candidate_tickers = df_filtered['Ticker'].tolist()[:max_scan]
    
    # 🌟 建立全方位字典容錯：保證無論輸入乜嘢格式都搵到分數與狀態！
    sctr_dict = {}
    cross_dict = {}
    prev_sctr_dict = {}
    change_sctr_dict = {}
    
    for _, row in df_filtered.iterrows():
        raw_t = str(row['Ticker'])
        clean_t = str(row.get('Ticker_Clean', raw_t))
        clean_t5 = str(row.get('Ticker_Clean_5', raw_t))
        score = row['SCTR']
        
        is_cross_down = row.get('Cross_Down_90', False) == True
        prev_sctr = row.get('SCTR_Prev', 0.0)
        change_sctr = row.get('SCTR_Change', 0.0)
        
        for k in [raw_t, clean_t, clean_t5]:
            sctr_dict[k] = score
            cross_dict[k] = is_cross_down
            prev_sctr_dict[k] = prev_sctr
            change_sctr_dict[k] = change_sctr

    st.info(f"📊 已鎖定 **{len(candidate_tickers)}** 隻 SCTR ≥ {min_sctr} 的頂尖強勢標的。")

    if st.button(f"🚀 開始【{cat_name}】獨立天外飛仙大掃描", type="primary", key=f"btn_{cat_code}"):
        with st.spinner(f"正在為 [{cat_name}] {len(candidate_tickers)} 隻標的抓取行情與執行 Minervini 雙軌運算..."):
            hist_dict = fetch_historical_data(candidate_tickers)
            results = []
            
            for ticker in candidate_tickers:
                if ticker not in hist_dict:
                    continue
                df_k = hist_dict[ticker]
                
                clean_ticker = str(ticker).replace('.HK', '').replace('.US', '').strip()
                sctr_rank = sctr_dict.get(clean_ticker, sctr_dict.get(ticker, 0.0))
                
                # 🔴 [新增功能] 獲取跌穿 90 狀態
                is_cross = cross_dict.get(clean_ticker, cross_dict.get(ticker, False))
                prev_s = prev_sctr_dict.get(clean_ticker, prev_sctr_dict.get(ticker, 0.0))
                chg_s = change_sctr_dict.get(clean_ticker, change_sctr_dict.get(ticker, 0.0))
                
                try:
                    df_res = run_tianwai_feixian(df_k, sctr_rank_from_master=sctr_rank, cross_down_90=is_cross)
                    if not df_res.empty:
                        last_row = df_res.iloc[-1]
                        state = last_row.get('天外飛仙_狀態', 0)
                        score = last_row.get('霸王總分', -9999)
                        tags = last_row.get('天外飛仙_標籤', '')
                        
                        if state in [1, 2, 3] or score > 0 or len(tags) > 0:
                            results.append({
                                'Ticker': ticker,
                                'SCTR排名': last_row.get('SCTR_Rank', sctr_rank),
                                '昨日防線': round(prev_s, 1) if is_cross else "",
                                '動能變化': f"{round(chg_s, 2):+}" if is_cross else "",
                                'SCTR4.0原始分': last_row.get('SCTR_Raw_4_0', 0),
                                '霸王總分': round(score, 1),
                                '最新收盤價': round(last_row.get('Close', 0), 2),
                                '起爆日數': last_row.get('起爆日數', 0),
                                'RS強度': round(last_row.get('RS', 0), 2),
                                '量比': round(last_row.get('Vol_Ratio', 0), 2),
                                '戰略標籤': tags
                            })
                except Exception:
                    continue
            
            if not results:
                st.warning(f"⚠️ [{cat_name}] 暫無觸發熱區/特權之標的。可嘗試調低 SCTR 門檻。")
                return

            df_show = pd.DataFrame(results).sort_values(by='霸王總分', ascending=False)

            m1, m2, m3 = st.columns(3)
            m1.metric("👑 觸發標的數", f"{len(df_show)} 隻")
            m2.metric("🐉 真龍/真皇數", f"{len(df_show[df_show['戰略標籤'].str.contains('真龍|真皇', na=False)])} 隻")
            m3.metric("🚨 跌穿90防線數量", f"{len(df_show[df_show['戰略標籤'].str.contains('🚨跌穿90防線', na=False)])} 隻")

            st.dataframe(
                df_show,
                use_container_width=True,
                hide_index=True,
                height=600,
                column_config={
                    "Ticker": st.column_config.TextColumn("代號", width="small"),
                    "SCTR排名": st.column_config.NumberColumn("SCTR", format="%.1f", width="small"),
                    "昨日防線": st.column_config.TextColumn("昨日防線", width="small"),
                    "動能變化": st.column_config.TextColumn("動能變化", width="small"),
                    "SCTR4.0原始分": st.column_config.NumberColumn("SCTR4", format="%.1f", width="small"),
                    "霸王總分": st.column_config.NumberColumn("總分", format="%.1f", width="small"),
                    "最新收盤價": st.column_config.NumberColumn("收盤價", format="%.2f", width="small"),
                    "起爆日數": st.column_config.NumberColumn("起爆", format="%d", width="small"),
                    "RS強度": st.column_config.NumberColumn("RS強度", format="%.2f", width="small"),
                    "量比": st.column_config.NumberColumn("量比", format="%.2f", width="small"),
                    "戰略標籤": st.column_config.TextColumn("戰略標籤 / 爆發訊號", width=600)
                }
            )

# ==========================================
# 🖥️ 3. Streamlit 主 UI 渲染
# ==========================================
def render_page_1a():
    st.title("🛸 艙房 1a：天外飛仙 (RS 強勢爆發獨立掃描器)")
    st.caption("四大市場獨立分立 Search 站點：港股個股 | 港股 ETF | 美股個股 | 美股 ETF")
    
    df_master, source_info = load_sctr_master()
    
    if df_master is None or df_master.empty:
        st.warning(f"⚠️ 尚未能讀取全宇宙 SCTR Master 數據庫 ({source_info})，請確認 GitHub Actions 是否已執行完畢！")
        return

    st.success(f"🌐 成功連線全宇宙數據庫 [{source_info}]！共計載入 **{len(df_master):,}** 隻資產。")

    tab1, tab2, tab3, tab4 = st.tabs([
        "🇭🇰 港股個股 (HK Equities)",
        "🇭🇰 港股 ETF (HK ETFs)",
        "🇺🇸 美股個股 (US Equities)",
        "🇺🇸 美股 ETF (US ETFs)"
    ])

    with tab1:
        render_single_market_search("HK_Equities", "🇭🇰 港股個股", df_master)

    with tab2:
        render_single_market_search("HK_ETFs", "🇭🇰 港股 ETF", df_master)

    with tab3:
        render_single_market_search("US_Equities", "🇺🇸 美股個股", df_master)

    with tab4:
        render_single_market_search("US_ETFs", "🇺🇸 美股 ETF", df_master)

if __name__ == "__main__":
    render_page_1a()