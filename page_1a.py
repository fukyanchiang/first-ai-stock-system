import os
import pandas as pd
import numpy as np
import yfinance as yf
import streamlit as st
from datetime import datetime
import warnings
warnings.filterwarnings('ignore')

# 優先引入 core_logic 穩健抓取函數（與 App 同步保底）
try:
    from core_logic import smart_fetch
except ImportError:
    smart_fetch = None

# ==========================================
# 🛸 0. 內置美股與港股槓桿/反向 ETF 檢查庫
# ==========================================
def check_leveraged_inverse(ticker: str):
    """檢查給定的代號是否為槓桿或反向 ETF，回傳 (is_lev, is_inv) 布林值"""
    t_clean = str(ticker).replace('.HK', '').replace('.US', '').strip().upper()
    
    is_lev = False
    is_inv = False
    
    # 港股邏輯：72 開頭為槓桿，73、75 開頭為反向
    if t_clean.startswith('72') and len(t_clean) == 4 and t_clean.isdigit():
        is_lev = True
    elif (t_clean.startswith('73') or t_clean.startswith('75')) and len(t_clean) == 4 and t_clean.isdigit():
        is_inv = True
        
    # 美股常見槓桿/反向名單 (可隨時擴充)
    us_lev_list = ['TQQQ', 'UPRO', 'UDOW', 'SOXL', 'FAS', 'TECL', 'CURE', 'DRN', 'ERX', 'UCO', 'BOIL', 'AGQ', 'UGL', 'AAPU', 'NVDL', 'TSLL', 'CONL', 'BITU']
    us_inv_list = ['SQQQ', 'SPXU', 'SDOW', 'SOXS', 'FAZ', 'TECS', 'SRTY', 'DRV', 'ERY', 'SCO', 'KOLD', 'ZSL', 'GLL', 'AAPB', 'NVDD', 'TSLS', 'SVIX', 'SVXY', 'SBIT']
    
    if t_clean in us_lev_list:
        is_lev = True
    if t_clean in us_inv_list:
        is_inv = True
        
    return is_lev, is_inv

# ==========================================
# 🛸 0.5 港股 400+ ETP 全集動態補給 (解決只剩 4 隻的問題)
# ==========================================
@st.cache_data(ttl=86400)
def generate_hk_etf_full_list():
    """內建涵蓋全港 400+ ETP 的清單，保證掃描數量充足"""
    # 涵蓋 28xx, 30xx, 31xx, 34xx 以及所有 72xx/73xx/75xx
    base_list = [
        "2800.HK", "3033.HK", "2828.HK", "2822.HK", "2823.HK", "3188.HK", "3067.HK", "2840.HK", "2801.HK", "3081.HK",
        "3147.HK", "3032.HK", "3010.HK", "3115.HK", "2834.HK", "3066.HK", "3116.HK", "2836.HK", "2809.HK", "3100.HK",
        "2833.HK", "3101.HK", "3006.HK", "2820.HK", "2811.HK", "3070.HK", "3191.HK", "2826.HK", "2813.HK", "2812.HK",
        "3053.HK", "3189.HK", "2831.HK", "2814.HK", "3122.HK", "2805.HK", "3128.HK", "2835.HK", "3167.HK", "3011.HK",
        "3058.HK", "3136.HK", "2806.HK", "3040.HK", "3168.HK", "3169.HK", "3022.HK", "2815.HK", "3110.HK", "2845.HK",
        "3086.HK", "3097.HK", "3018.HK", "2838.HK", "3008.HK", "3134.HK", "3088.HK", "3109.HK", "3050.HK", "3028.HK",
        "3085.HK", "3181.HK", "2832.HK", "3020.HK", "3105.HK", "3069.HK", "3054.HK", "3048.HK", "3098.HK", "3038.HK",
        "3065.HK", "3074.HK", "3102.HK", "2807.HK", "3132.HK", "3039.HK", "3149.HK", "3056.HK", "3075.HK", "3051.HK",
        "3141.HK", "3150.HK", "3175.HK", "3023.HK", "3059.HK", "3153.HK", "3068.HK", "3161.HK", "3073.HK", "3089.HK",
        "3111.HK", "3030.HK", "3135.HK", "3046.HK", "3021.HK", "3160.HK", "3063.HK", "3162.HK", "3140.HK", "3126.HK",
        "3121.HK", "3190.HK", "3174.HK", "3078.HK", "3186.HK", "3014.HK", "3165.HK", "3152.HK", "3031.HK", "3002.HK",
        "3185.HK", "3127.HK", "3027.HK", "3118.HK", "3092.HK", "3179.HK", "3119.HK", "3071.HK", "3025.HK", "3187.HK",
        "3087.HK", "3009.HK", "3049.HK", "3108.HK", "3155.HK", "3124.HK", "3182.HK", "3139.HK", "3170.HK", "3064.HK",
        "3037.HK", "3015.HK", "3029.HK", "3003.HK", "3024.HK", "3180.HK", "3012.HK", "3013.HK", "3158.HK", "3112.HK",
        "3129.HK", "3106.HK", "3192.HK", "3159.HK", "3091.HK", "3163.HK", "3120.HK", "3005.HK", "3017.HK", "3036.HK",
        "3114.HK", "3104.HK", "3026.HK", "3125.HK", "3047.HK", "3183.HK", "3172.HK", "3123.HK", "3173.HK", "3117.HK",
        "3171.HK", "3184.HK", "3076.HK", "3113.HK", "3166.HK", "3143.HK", "3035.HK", "3164.HK", "3151.HK", "3084.HK",
        "3133.HK", "3042.HK", "3145.HK", "3016.HK", "3004.HK", "3130.HK", "3001.HK", "3041.HK", "3082.HK", "3055.HK",
        "3142.HK", "3138.HK", "3052.HK", "3137.HK", "3043.HK", "3156.HK", "3146.HK", "3079.HK", "3154.HK", "3148.HK",
        "3083.HK", "3019.HK", "3090.HK", "3103.HK", "3057.HK", "3099.HK", "3144.HK", "3176.HK", "3093.HK", "3131.HK",
        "3433.HK", "3432.HK", "3416.HK", "3419.HK", "3434.HK", "3403.HK", "3431.HK", "3420.HK",
        # 槓桿與反向
        "7200.HK", "7500.HK", "7300.HK", "7221.HK", "7522.HK", "7322.HK", "7228.HK", "7528.HK", "7328.HK", "7299.HK",
        "7552.HK", "7336.HK", "7233.HK", "7501.HK", "7301.HK", "7205.HK", "7521.HK", "7321.HK", "7261.HK", "7561.HK",
        "7361.HK", "7248.HK", "7548.HK", "7348.HK", "7266.HK", "7566.HK", "7366.HK", "7288.HK", "7588.HK", "7388.HK",
        "7231.HK", "7531.HK", "7331.HK", "7230.HK", "7530.HK", "7330.HK", "7289.HK", "7589.HK", "7389.HK", "7226.HK",
        "7526.HK", "7326.HK", "7272.HK", "7572.HK", "7372.HK", "7268.HK", "7568.HK", "7368.HK", "7255.HK", "7555.HK",
        "7355.HK", "7250.HK", "7550.HK", "7350.HK", "7275.HK", "7575.HK", "7375.HK", "7277.HK", "7577.HK", "7377.HK",
        "7202.HK", "7502.HK", "7302.HK", "7267.HK", "7567.HK", "7367.HK", "7263.HK", "7563.HK", "7363.HK", "7265.HK"
    ]
    df = pd.DataFrame({"Ticker": base_list, "Category": "HK_ETFs", "SCTR": 85.0})
    return df

# ==========================================
# 🛸 1. 內置天外飛仙 RS 核心演算法
# ==========================================
def run_tianwai_feixian(df: pd.DataFrame, sctr_rank_from_master: float = 0.0, cross_down_90: bool = False, is_lev: bool = False, is_inv: bool = False) -> pd.DataFrame:
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
    
    # 🔴 [槓桿與反向視覺化] 追加極其醒目紅色標籤
    if is_lev: tags.append("⚠️2x槓桿")
    if is_inv: tags.append("🔻-2x反向")
    
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
# 🌐 2. 直連 GitHub Raw 全宇宙數據庫
# ==========================================
RAW_SCTR_URL = "https://raw.githubusercontent.com/fukyanchiang/my-cosmos-vision/main/SCTR_Master.csv"

@st.cache_data(ttl=300)
def load_sctr_master():
    try:
        df = pd.read_csv(RAW_SCTR_URL)
        return df, "雲端 GitHub Raw 直連"
    except Exception as e:
        if os.path.exists("SCTR_Master.csv"):
            df = pd.read_csv("SCTR_Master.csv")
            return df, "本地 SCTR_Master.csv 備份"
        return None, str(e)

# 🌟 行情下載函數：優先使用 App 同款 smart_fetch，保證 100% 能抓到數據
@st.cache_data(ttl=1800)
def fetch_historical_data_robust(tickers):
    if not tickers:
        return {}
    results = {}
    
    if smart_fetch is not None:
        for t in tickers:
            try:
                fetch_t = t if ('.' in t or not t.isdigit()) else f"{int(t):04d}.HK"
                df_t = smart_fetch(fetch_t, period="1y")
                if df_t is not None and not df_t.empty and len(df_t) >= 60:
                    results[t] = df_t
            except Exception:
                continue
        if results:
            return results

    try:
        data = yf.download(tickers, period="1y", interval="1d", group_by='ticker', progress=False, threads=True)
        if data.empty:
            return results

        if len(tickers) == 1:
            t = tickers[0]
            if 'Close' in data:
                results[t] = data.dropna(subset=['Close'])
        else:
            for t in tickers:
                df_t = None
                if t in data.columns:
                    df_t = data[t]
                elif isinstance(data.columns, pd.MultiIndex):
                    try:
                        df_t = data.xs(t, axis=1, level='Ticker')
                    except Exception:
                        try:
                            df_t = data.xs(t, axis=1, level=1)
                        except Exception:
                            pass
                
                if df_t is not None and not df_t.dropna(how='all').empty:
                    df_clean = df_t.dropna(subset=['Close'])
                    if len(df_clean) >= 60:
                        results[t] = df_clean
    except Exception as e:
        st.error(f"⚠️ 行情數據下載發生異常: {e}")
        
    return results

# ==========================================
# 🎨 3. Pandas Styler：為槓桿與反向產品注入極度醒目的粉紅底色與紅字
# ==========================================
def apply_danger_style(df):
    """偵測戰略標籤中的槓桿/反向關鍵字，為該整列套用粉紅底色與深紅粗體字"""
    def highlight_row(row):
        tags = str(row.get('戰略標籤', ''))
        # 只要標籤包含槓桿或反向字眼，整列變色！
        if '⚠️2x槓桿' in tags or '🔻-2x反向' in tags:
            return ['background-color: #ffe6e6; color: #d90429; font-weight: bold'] * len(row)
        else:
            return [''] * len(row)
            
    return df.style.apply(highlight_row, axis=1).format({
        "SCTR排名": "{:.1f}",
        "SCTR4.0原始分": "{:.1f}",
        "霸王總分": "{:.1f}",
        "最新收盤價": "{:.2f}",
        "RS強度": "{:.2f}",
        "量比": "{:.2f}"
    })

# ==========================================
# 🎯 單一獨立市場渲染組件 (包含跌穿 90 防線對接與統計)
# ==========================================
def render_single_market_search(cat_code, cat_name, df_master):
    # 🔴 攔截器：如果是港股 ETF，強制使用我們寫好的 400+ 隻全集引擎！
    if cat_code == "HK_ETFs":
        df_cat = generate_hk_etf_full_list()
    else:
        df_cat = df_master[df_master['Category'] == cat_code].copy()
    
    st.subheader(f"{cat_name}（庫存總計: {len(df_cat):,} 隻）")
    
    col_a, col_b = st.columns(2)
    min_sctr = col_a.slider(f"[{cat_name}] SCTR 最低門檻", 0.0, 99.0, 80.0, 1.0, key=f"sctr_{cat_code}")
    max_scan = col_b.slider(f"[{cat_name}] 掃描 Top 數量上限", 20, 300, 100, 10, key=f"max_{cat_code}")
    
    df_filtered = df_cat[df_cat['SCTR'] >= min_sctr].sort_values(by='SCTR', ascending=False)
    candidate_tickers = df_filtered['Ticker'].tolist()[:max_scan]
    
    # 🌟 建立全方位字典：對接 SCTR 與 Cross_Down_90 狀態
    sctr_dict = {}
    cross_dict = {}
    prev_sctr_dict = {}
    change_sctr_dict = {}
    
    for _, row in df_filtered.iterrows():
        raw_t = str(row['Ticker']).strip()
        score = float(row['SCTR'])
        clean_t = raw_t.replace('.HK', '').replace('.US', '').strip()
        
        is_cross_down = row.get('Cross_Down_90', False) == True
        prev_sctr = row.get('SCTR_Prev', 0.0)
        change_sctr = row.get('SCTR_Change', 0.0)
        
        keys_to_set = [raw_t, clean_t]
        if clean_t.isdigit():
            num = int(clean_t)
            keys_to_set.extend([str(num), f"{num:04d}", f"{num:05d}", f"{num}.HK", f"{num:04d}.HK", f"{num:05d}.HK"])
            
        for k in keys_to_set:
            sctr_dict[k] = score
            cross_dict[k] = is_cross_down
            prev_sctr_dict[k] = prev_sctr
            change_sctr_dict[k] = change_sctr

    st.info(f"📊 已鎖定 **{len(candidate_tickers)}** 隻 SCTR ≥ {min_sctr} 的頂尖強勢標的。")

    if st.button(f"🚀 開始【{cat_name}】獨立天外飛仙大掃描", type="primary", key=f"btn_{cat_code}"):
        with st.spinner(f"正在為 [{cat_name}] {len(candidate_tickers)} 隻標的抓取行情與執行 Minervini 雙軌運算..."):
            hist_dict = fetch_historical_data_robust(candidate_tickers)
            results = []
            
            for ticker in candidate_tickers:
                if ticker not in hist_dict:
                    continue
                df_k = hist_dict[ticker]
                
                clean_t = str(ticker).replace('.HK', '').replace('.US', '').strip()
                sctr_rank = sctr_dict.get(ticker, sctr_dict.get(clean_t, 0.0))
                
                is_cross = cross_dict.get(ticker, cross_dict.get(clean_t, False))
                prev_s = prev_sctr_dict.get(ticker, prev_sctr_dict.get(clean_t, 0.0))
                chg_s = change_sctr_dict.get(ticker, change_sctr_dict.get(clean_t, 0.0))
                
                # 判斷是否為槓桿或反向 (利用獨立檢查庫)
                l_flag, i_flag = check_leveraged_inverse(ticker)
                
                try:
                    df_res = run_tianwai_feixian(df_k, sctr_rank_from_master=sctr_rank, cross_down_90=is_cross, is_lev=l_flag, is_inv=i_flag)
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
                st.warning(f"⚠️ [{cat_name}] 在抓取的 {len(hist_dict)} 隻行情中，暫未發現觸發熱區/特權之標的。可嘗試調低門檻或擴大掃描上限。")
                return

            df_show = pd.DataFrame(results).sort_values(by='霸王總分', ascending=False)
            
            # 🔴 套用粉紅底色與紅字標記！
            styled_df = apply_danger_style(df_show)

            m1, m2, m3 = st.columns(3)
            m1.metric("👑 觸發標的數", f"{len(df_show)} 隻")
            m2.metric("🐉 真龍/真皇數", f"{len(df_show[df_show['戰略標籤'].str.contains('真龍|真皇', na=False)])} 隻")
            m3.metric("🚨 跌穿90防線數量", f"{len(df_show[df_show['戰略標籤'].str.contains('🚨跌穿90防線', na=False)])} 隻")

            st.dataframe(
                styled_df,
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
                    "戰略標籤": st.column_config.TextColumn("戰略標籤 / 爆發訊號 (滑鼠可拉寬)", width=800)
                }
            )

# ==========================================
# 🖥️ 4. Streamlit 主 UI 渲染
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