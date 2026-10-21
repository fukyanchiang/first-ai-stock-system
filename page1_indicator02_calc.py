import pandas as pd
import numpy as np
import plotly.graph_objects as go
import warnings
warnings.filterwarnings('ignore')

# ===================================================
# 🧠 4 大富途神兵技術指標運算庫 (Stage2 / MACD / TTM / VCP / SPRING)
# ===================================================
def compute_group2_indicators(df):
    df = df.copy()
    C, O, H, L, V = df['Close'], df['Open'], df['High'], df['Low'], df['Volume']

    def MA(s, n): return s.rolling(n, min_periods=1).mean()
    def EMA(s, n): return s.ewm(span=n, adjust=False).mean()
    def HHV(s, n): return s.rolling(n, min_periods=1).max()
    def LLV(s, n): return s.rolling(n, min_periods=1).min()
    def STD(s, n): return s.rolling(n, min_periods=1).std()
    def CROSS(s1, s2):
        if isinstance(s1, (int, float)): s1 = pd.Series(s1, index=df.index)
        if isinstance(s2, (int, float)): s2 = pd.Series(s2, index=df.index)
        return (s1 > s2) & (s1.shift(1).bfill() <= s2.shift(1).bfill())
    def COUNT(cond, n): return cond.fillna(False).astype(int).rolling(n, min_periods=1).sum()
    def FORCAST(S, N):
        w = np.arange(1, N + 1) - (N + 1) / 2.0
        w2_sum = np.sum(w ** 2)
        if w2_sum == 0: return S
        slope_num = pd.Series(0.0, index=S.index)
        for i in range(N): slope_num += w[i] * S.shift(N - 1 - i).bfill().fillna(0)
        return S.rolling(N, min_periods=1).mean() + (slope_num / w2_sum) * (N - 1) / 2.0

    # 1. MARK MINERVINI STAGE 2 趨勢過濾
    MA50, MA150, MA200 = MA(C, 50), MA(C, 150), MA(C, 200)
    STAGE2 = (C > MA50) & (C > MA150) & (MA50 > MA150) & (MA150 > MA200) & (MA200 > MA200.shift(20).fillna(0)) & (C > (LLV(L, 250) * 1.3))
    df['STAGE2'] = STAGE2

    # 2. 正宗 MACD (動態感應版)
    DIF = EMA(C, 12) - EMA(C, 26)
    DEA = EMA(DIF, 9)
    MACD_VAL = (DIF - DEA) * 2
    df['NEW_DIF'] = DIF
    df['NEW_DEA'] = DEA
    df['NEW_MACD'] = MACD_VAL

    WATER_DEAD_STAGE2 = STAGE2 & (MACD_VAL < 0) & (DIF > 0) & (DEA > 0)
    NON_STAGE2_BULL = (~STAGE2) & (MACD_VAL >= 0)
    STAGE2_WATER_BULL = STAGE2 & (MACD_VAL >= 0) & (DIF > 0) & (DEA > 0)
    STAGE2_UNDER_BULL = STAGE2 & (MACD_VAL >= 0) & (~STAGE2_WATER_BULL)
    NORMAL_BEAR = (MACD_VAL < 0) & (~WATER_DEAD_STAGE2)
    MACD_DIR = MACD_VAL >= MACD_VAL.shift(1).fillna(0)
    
    MACD_C = pd.Series('#aaaaaa', index=df.index)
    MACD_C = np.where(NON_STAGE2_BULL & MACD_DIR, '#888888', MACD_C)
    MACD_C = np.where(NON_STAGE2_BULL & ~MACD_DIR, '#aaaaaa', MACD_C)
    MACD_C = np.where(STAGE2_WATER_BULL & MACD_DIR, '#FF6600', MACD_C)
    MACD_C = np.where(STAGE2_WATER_BULL & ~MACD_DIR, '#FFB266', MACD_C)
    MACD_C = np.where(STAGE2_UNDER_BULL & MACD_DIR, '#9900CC', MACD_C)
    MACD_C = np.where(STAGE2_UNDER_BULL & ~MACD_DIR, '#CC66FF', MACD_C)
    MACD_C = np.where(WATER_DEAD_STAGE2 & ~MACD_DIR, '#0000FF', MACD_C)
    MACD_C = np.where(WATER_DEAD_STAGE2 & MACD_DIR, '#3399FF', MACD_C)
    MACD_C = np.where(NORMAL_BEAR & ~MACD_DIR, '#00AA00', MACD_C)
    MACD_C = np.where(NORMAL_BEAR & MACD_DIR, '#00FFFF', MACD_C)
    df['NEW_MACD_COLOR'] = MACD_C
    df['MACD_GOLD'] = CROSS(DIF, DEA) & (DIF > 0) & (DEA > 0)
    df['MACD_TOP_DIV'] = CROSS(DEA, DIF) & (H > HHV(H, 10).shift(1).fillna(H)) & (DIF < HHV(DIF, 10).shift(1).fillna(DIF)) & (DIF > 0)
    df['MACD_BOT_DIV'] = CROSS(DIF, DEA) & (L < LLV(L, 10).shift(1).fillna(L)) & (DIF > LLV(DIF, 10).shift(1).fillna(DIF)) & (DIF < 0)

    # 3. GRANDPA TTM STAGE2 (擠壓動能)
    N_TTM = 20
    TR = pd.concat([H - L, (H - C.shift(1).bfill()).abs(), (L - C.shift(1).bfill()).abs()], axis=1).max(axis=1)
    VAR1 = (HHV(H, N_TTM) + LLV(L, N_TTM)) / 2 + MA(C, N_TTM)
    VAR2 = FORCAST(C - VAR1 / 2, N_TTM)
    df['TTM_VAR2'] = VAR2
    TTM_DIR = VAR2 > VAR2.shift(1).fillna(0)
    TTM_C = pd.Series('gray', index=df.index)
    TTM_C = np.where((VAR2 >= 0) & STAGE2 & TTM_DIR, '#FFA500', TTM_C)
    TTM_C = np.where((VAR2 >= 0) & STAGE2 & ~TTM_DIR, '#CC6600', TTM_C)
    TTM_C = np.where((VAR2 >= 0) & (~STAGE2) & TTM_DIR, '#00FFFF', TTM_C)
    TTM_C = np.where((VAR2 >= 0) & (~STAGE2) & ~TTM_DIR, '#009B9B', TTM_C)
    TTM_C = np.where((VAR2 < 0) & STAGE2 & ~TTM_DIR, '#FF9BFF', TTM_C)
    TTM_C = np.where((VAR2 < 0) & STAGE2 & TTM_DIR, '#CC00CC', TTM_C)
    TTM_C = np.where((VAR2 < 0) & (~STAGE2) & ~TTM_DIR, '#FF3366', TTM_C)
    TTM_C = np.where((VAR2 < 0) & (~STAGE2) & TTM_DIR, '#880000', TTM_C)
    df['TTM_COLOR'] = TTM_C
    BB = MA(C, N_TTM) + 2 * STD(C, N_TTM)
    KB = EMA(C, N_TTM) + EMA(TR, N_TTM)
    df['TTM_SQZ'] = BB < KB

    # 4. GRANDPA VCP 4.0 / 5.3.4 (波動收縮雷達)
    AMP_BIG = (HHV(H, 30) - LLV(L, 30)) / (LLV(L, 30) + 1e-9) * 100
    AMP_NARROW = (HHV(H, 8) - LLV(L, 8)) / (LLV(L, 8) + 1e-9) * 100
    VCP_READY = (AMP_NARROW <= (AMP_BIG * 0.65)) & (AMP_NARROW <= 10)
    HTF_READY = STAGE2 & ((C / (LLV(L, 40).shift(10).bfill() + 1e-9)) > 1.9) & (((HHV(H, 12) - LLV(L, 12)) / (LLV(L, 12) + 1e-9) * 100) < 20)
    MA20_C = MA(C, 20)
    WASH_REC = (COUNT(C < MA20_C, 5) <= 2) & (C > MA20_C)
    MAV20 = MA(V, 20)
    RECENT_HIGH = HHV(H, 10).shift(1).bfill()
    BREAKOUT = CROSS(C, RECENT_HIGH) & (V > (MAV20 * 1.3))
    GATHER = HTF_READY | VCP_READY
    EX_MEM = COUNT(GATHER, 15) >= 1
    AI_DRAGON = (C > RECENT_HIGH) & ((C / C.shift(1).bfill()) > 1.04) & (COUNT(GATHER, 5) >= 1) & (~BREAKOUT)
    IS_ULTIMATE = STAGE2 & EX_MEM & (C > HHV(H, 20).shift(1).bfill()) & ((C / C.shift(1).bfill()) > 1.05) & (~BREAKOUT)
    IS_PARABOLIC = (C > MA(C, 20)) & (MA(C, 20) > MA50) & ((C / (LLV(L, 30).shift(5).bfill() + 1e-9)) > 1.5) & (C > HHV(H, 10).shift(1).bfill()) & (C > O) & ((C / C.shift(1).bfill()) > 1.03) & (~BREAKOUT) & (~IS_ULTIMATE) & (~AI_DRAGON)
    MA10 = MA(C, 10)
    IS_AMBUSH = (MA50 > MA150) & (MA150 > MA200) & (MA200 > MA200.shift(20).fillna(0)) & (((COUNT(MA10 < MA20_C, 3) >= 1) & (MA10 <= MA20_C) & ((MA10 + (MA10 - MA10.shift(1).bfill())) > (MA20_C + (MA20_C - MA20_C.shift(1).bfill()))) & (C > O)) | ((COUNT(MA20_C < MA50, 5) >= 1) & (MA20_C <= MA50) & ((MA20_C + (MA20_C - MA20_C.shift(1).bfill())) > (MA50 + (MA50 - MA50.shift(1).bfill()))) & (C > O)))
    
    IS_VCP = BREAKOUT & VCP_READY.shift(1).fillna(False)
    IS_HTF = BREAKOUT & HTF_READY.shift(1).fillna(False)
    df['VCP_BOTH'] = IS_VCP & IS_HTF
    df['VCP_VCP'] = IS_VCP & (~df['VCP_BOTH'])
    df['VCP_HTF'] = IS_HTF & (~df['VCP_BOTH'])
    df['VCP_AI'] = AI_DRAGON
    df['VCP_ULT'] = IS_ULTIMATE
    df['VCP_PARA'] = IS_PARABOLIC
    df['VCP_AMBUSH'] = IS_AMBUSH
    df['VCP_STAGE2'] = STAGE2
    df['VCP_HTF_READY'] = HTF_READY
    df['VCP_VCP_READY'] = VCP_READY
    df['VCP_WASH_REC'] = STAGE2 & WASH_REC

    # 5. GRANDPA VOLA SPRING DELTA PRO (爆邊神器)
    PRICE_HOLD = COUNT(C > MA150, 3) > 0
    STAGE2_ON = PRICE_HOLD & (MA50 > MA150) & (MA150 > MA150.shift(10).fillna(0))
    DAY_AMP = (H - L) / (C.shift(1).bfill() + 1e-9) * 100
    AMP_SQZ = DAY_AMP < (MA(DAY_AMP, N_TTM) * 0.75)
    VOL_SQZ = V < (MA(V, N_TTM) * 0.75)
    WAS_SQZ = COUNT(AMP_SQZ & VOL_SQZ & (BB < MA(C, N_TTM) + 1.5 * MA(TR, N_TTM)), 5) >= 1
    INNER_PWR = ((C - L) > (H - C)) | (((C - L) / (H - L + 1e-9)) > 0.60)
    STOCK_DELTA = C - C.shift(1).bfill()
    DELTA_PWR = ((STOCK_DELTA - STOCK_DELTA.shift(1).bfill()) > 0) & (C > O)
    BETA_OK = (MA(TR, 14) / (MA20_C + 1e-9)) * 100 > 1.2
    df['SP_STAGE2'] = STAGE2_ON
    df['SP_READY'] = STAGE2_ON & WAS_SQZ & BETA_OK
    df['SP_SIG'] = df['SP_READY'] & INNER_PWR & DELTA_PWR
    df['SP_TEXT'] = df['SP_SIG'] & (~df['SP_SIG'].shift(1).fillna(False))

    return df

# ===================================================
# 🎨 繪製組 2 副圖 Trace 輔助函數
# ===================================================
def render_group2_traces(fig, k, df_display, y_ax, dm, y_num, y_axes_config):
    y_key = f"yaxis{y_num}"
    if k == "spring":
        fig.add_trace(go.Bar(x=df_display.index, y=np.where(df_display['SP_STAGE2'], -0.2, 0), marker_color='#00ff88', name='STAGE2底線', yaxis=y_ax))
        fig.add_trace(go.Bar(x=df_display.index, y=np.where(df_display['SP_READY'], 1, 0), marker_color='#005599', name='蓄勢待發', yaxis=y_ax))
        fig.add_trace(go.Bar(x=df_display.index, y=np.where(df_display['SP_SIG'], 3, 0), marker_color='#FFA500', name='點火爆發', yaxis=y_ax))
        sig_text_dates = df_display[df_display['SP_TEXT'] == True].index
        for d in sig_text_dates:
            fig.add_trace(go.Scatter(x=[d], y=[3.5], mode='text', text=['⚡爆邊'], textposition='top center', textfont=dict(color='#FFA500', size=11, family='Arial Black'), showlegend=False, yaxis=y_ax))
        y_axes_config[y_key] = dict(domain=dm, anchor='x', title_text="SPRING<br>DELTA", gridcolor='#2e3d52', title_font=dict(size=10), range=[-0.5, 4.5])

    elif k == "vcp":
        fig.add_trace(go.Bar(x=df_display.index, y=np.where(df_display['VCP_STAGE2'], -5, 0), marker_color='#00ffff', name='STAGE2趨勢', yaxis=y_ax))
        fig.add_trace(go.Bar(x=df_display.index, y=np.where(df_display['VCP_HTF_READY'], 50, 0), marker_color='#FF00FF', name='HTF預備', yaxis=y_ax))
        fig.add_trace(go.Bar(x=df_display.index, y=np.where(df_display['VCP_VCP_READY'], 30, 0), marker_color='#888888', name='VCP預備', yaxis=y_ax))
        fig.add_trace(go.Bar(x=df_display.index, y=np.where(df_display['VCP_WASH_REC'], 15, 0), marker_color='#FF00FF', name='洗盤恢復', yaxis=y_ax))
        
        # 各類信號大柱
        fig.add_trace(go.Bar(x=df_display.index, y=np.where(df_display['VCP_VCP'], 100, 0), marker_color='#FFFF00', name='VCP-GO', yaxis=y_ax))
        fig.add_trace(go.Bar(x=df_display.index, y=np.where(df_display['VCP_HTF'], 100, 0), marker_color='#FF0000', name='HTF-GO', yaxis=y_ax))
        fig.add_trace(go.Bar(x=df_display.index, y=np.where(df_display['VCP_BOTH'], 120, 0), marker_color='#00FF00', name='SUPER-GO', yaxis=y_ax))
        fig.add_trace(go.Bar(x=df_display.index, y=np.where(df_display['VCP_AI'], 100, 0), marker_color='#00FFFF', name='AI-GO', yaxis=y_ax))
        fig.add_trace(go.Bar(x=df_display.index, y=np.where(df_display['VCP_ULT'], 100, 0), marker_color='#FFFFFF', name='BLACK-GO', yaxis=y_ax))
        fig.add_trace(go.Bar(x=df_display.index, y=np.where(df_display['VCP_PARA'], 100, 0), marker_color='#A52A2A', name='ORANGE-GO', yaxis=y_ax))
        fig.add_trace(go.Bar(x=df_display.index, y=np.where(df_display['VCP_AMBUSH'], 100, 0), marker_color='rgba(0,0,0,0)', marker_line=dict(color='#A52A2A', width=2), name='AMBUSH埋伏', yaxis=y_ax))

        # 文字標籤
        for idx, r in df_display[df_display['VCP_VCP']].iterrows():
            fig.add_trace(go.Scatter(x=[idx], y=[110], mode='text', text=['VCP-GO'], textfont=dict(color='#FFFF00', size=9), yaxis=y_ax, showlegend=False))
        for idx, r in df_display[df_display['VCP_HTF']].iterrows():
            fig.add_trace(go.Scatter(x=[idx], y=[110], mode='text', text=['HTF-GO'], textfont=dict(color='#FF0000', size=9), yaxis=y_ax, showlegend=False))
        for idx, r in df_display[df_display['VCP_BOTH']].iterrows():
            fig.add_trace(go.Scatter(x=[idx], y=[130], mode='text', text=['SUPER-GO'], textfont=dict(color='#00FF00', size=9), yaxis=y_ax, showlegend=False))
        for idx, r in df_display[df_display['VCP_AI']].iterrows():
            fig.add_trace(go.Scatter(x=[idx], y=[110], mode='text', text=['AI-GO'], textfont=dict(color='#00FFFF', size=9), yaxis=y_ax, showlegend=False))
        for idx, r in df_display[df_display['VCP_AMBUSH']].iterrows():
            fig.add_trace(go.Scatter(x=[idx], y=[110], mode='text', text=['AMBUSH'], textfont=dict(color='#FFA500', size=9), yaxis=y_ax, showlegend=False))
        y_axes_config[y_key] = dict(domain=dm, anchor='x', title_text="VCP4-00<br>突破雷達", gridcolor='#2e3d52', title_font=dict(size=10), range=[-10, 140])

    elif k == "ttm":
        fig.add_trace(go.Bar(x=df_display.index, y=df_display['TTM_VAR2'], marker_color=df_display['TTM_COLOR'], name='TTM 動能', yaxis=y_ax))
        # 零軸 Squeeze 點點
        fig.add_trace(go.Scatter(x=df_display.index, y=[0]*len(df_display), mode='markers', marker=dict(color='#00ff88', size=4), name='波幅釋放', yaxis=y_ax))
        sqz_dates = df_display[df_display['TTM_SQZ'] == True].index
        if len(sqz_dates) > 0:
            fig.add_trace(go.Scatter(x=sqz_dates, y=[0]*len(sqz_dates), mode='markers', marker=dict(color='#ff3366', size=5), name='縮盤蓄勢', yaxis=y_ax))
        y_axes_config[y_key] = dict(domain=dm, anchor='x', title_text="TTM<br>STAGE2", gridcolor='#2e3d52', title_font=dict(size=10))

    elif k == "macd":
        fig.add_trace(go.Scatter(x=df_display.index, y=df_display['NEW_DIF'], mode='lines', line=dict(color='#FF8D1E', width=2), name='DIF', yaxis=y_ax))
        fig.add_trace(go.Scatter(x=df_display.index, y=df_display['NEW_DEA'], mode='lines', line=dict(color='#0CAEE6', width=2), name='DEA', yaxis=y_ax))
        fig.add_trace(go.Bar(x=df_display.index, y=df_display['NEW_MACD'], marker_color=df_display['NEW_MACD_COLOR'], name='MACD 柱體', yaxis=y_ax))
        
        # 水上金叉向上紅箭嘴
        gold_dates = df_display[df_display['MACD_GOLD'] == True].index
        for d in gold_dates:
            fig.add_trace(go.Scatter(x=[d], y=[df_display.loc[d, 'NEW_DIF'] * 0.95], mode='markers', marker=dict(symbol='triangle-up', color='red', size=8), showlegend=False, yaxis=y_ax))
        # 頂底背馳符號
        top_div = df_display[df_display['MACD_TOP_DIV'] == True].index
        for d in top_div:
            fig.add_trace(go.Scatter(x=[d], y=[df_display.loc[d, 'NEW_DIF'] * 1.05], mode='markers', marker=dict(symbol='triangle-down', color='#00ff88', size=8), showlegend=False, yaxis=y_ax))
        bot_div = df_display[df_display['MACD_BOT_DIV'] == True].index
        for d in bot_div:
            fig.add_trace(go.Scatter(x=[d], y=[df_display.loc[d, 'NEW_DIF'] * 0.95], mode='markers', marker=dict(symbol='triangle-up', color='#FF00FF', size=8), showlegend=False, yaxis=y_ax))
        y_axes_config[y_key] = dict(domain=dm, anchor='x', title_text="正宗MACD<br>(STAGE2)", gridcolor='#2e3d52', title_font=dict(size=10))