import streamlit as st 
import yfinance as yf 
import pandas as pd 
import numpy as np 
import plotly.graph_objects as go 
from plotly.subplots import make_subplots 
import time

st.set_page_config(page_title="環球資產透視評估儀", layout="wide") 

st.markdown("""
    <style>
    .stApp { background-color: #0e1117; color: white; }
    section[data-testid="stMain"] div[data-testid="stWidgetLabel"] p, 
    section[data-testid="stMain"] div[data-testid="stWidgetLabel"] span { color: #FFFFFF !important; font-size: 1.1rem !important; font-weight: bold !important; }
    section[data-testid="stMain"] div[data-testid="stRadio"] label div[data-testid="stMarkdownContainer"] p { color: #FFFFFF !important; }
    section[data-testid="stMain"] div[data-baseweb="select"] span { color: #000000 !important; font-weight: bold !important; }
    section[data-testid="stMain"] div[data-baseweb="select"] ul li { color: #000000 !important; }
    section[data-testid="stMain"] button p { color: #000000 !important; font-weight: 900 !important; font-size: 1.1rem !important; }
    section[data-testid="stMain"] div[data-baseweb="input"] input { color: #000000 !important; font-weight: bold !important; }
    section[data-testid="stSidebar"] div[data-testid="stWidgetLabel"] p { color: #31333F !important; }
    section[data-testid="stSidebar"] div[data-testid="stRadio"] label div[data-testid="stMarkdownContainer"] p { color: #31333F !important; }
    .main-title { text-align: center; color: #FFD700 !important; font-size: 3.5rem; font-weight: 900; margin-bottom: 25px; }
    .cosmos-box { background-color: #000 !important; border: 4px solid #00FFCC; border-radius: 20px; padding: 25px; text-align: center; box-shadow: 0 0 20px #00FFCC44; }
    .cosmos-label { color: #00FFCC !important; font-size: 1.8rem; font-weight: bold; margin-bottom: 10px; }
    .cosmos-value { color: #FFFFFF !important; font-size: 5rem; font-weight: 900; }
    .ej-header { color: #00FFFF !important; font-size: 1.8rem; font-weight: 900; margin-bottom: 8px; }
    .bar-group-container { display: flex; gap: 8px; margin-bottom: 15px; }
    .bar-triad { display: flex; gap: 3px; }
    .ej-seg { width: 16px; height: 35px; border-radius: 2px; border: 1.2px solid rgba(255,255,255,0.4); }
    .val-box { background-color: #000 !important; border: 2px solid #FFD700; border-radius: 12px; padding: 20px; text-align: center; min-height: 220px; margin-bottom: 15px; }
    .val-label { color: #FFFFFF !important; font-size: 1.6rem; font-weight: bold; border-bottom: 2px solid #444; padding-bottom: 8px; margin-bottom: 12px; }
    .val-text { font-size: 1.2rem; color: #ccc; margin: 8px 0; }
    .val-focus { color: #FFD700 !important; font-weight: bold; font-size: 1.8rem; }
    .red-bar { color: #fff !important; border-radius: 10px; text-align: center; font-weight: 900; }
    .val-box-purple { border: 3px solid #BC13FE; border-radius: 15px; padding: 30px; background-color: #000; box-shadow: 0 0 25px #BC13FE66; margin: 25px 0; }
    .energy-bar-container-8d { display: flex; gap: 4px; margin-top: 10px; margin-bottom: 15px; }
    .energy-seg-8d { flex: 1; height: 16px; border-radius: 2px; }
    .whale-box { background-color: #000; border: 3px solid #FFD700; border-radius: 15px; padding: 35px; margin-top: 30px; }
    .whale-row { display: flex; justify-content: space-between; padding: 15px 0; border-bottom: 1px solid #333; }
    .whale-n { color: #FFD700 !important; font-weight: bold; font-size: 2.5rem; }
    .whale-a { color: #00FFCC !important; font-size: 1.6rem; text-align: right; }
    .scan-card-fire { border-left: 5px solid #00FFCC; background-color: #111; padding: 15px; margin-bottom: 10px; border-radius: 8px; }
    .scan-card-super { border-left: 8px solid #FF4B4B; background-color: #310000; padding: 15px; margin-bottom: 10px; border-radius: 8px; box-shadow: 0 0 15px #FF4B4B66; }
    .bear-warning { color: #FF0000 !important; font-size: 2.5rem; font-weight: 900; text-align: center; text-shadow: 2px 2px 5px #000; padding: 20px; border: 4px dashed red; background-color: #220000; margin: 20px 0; border-radius: 15px;}
    .exit-radar { background-color: #220000; border: 2px solid #FF0000; padding: 15px; border-radius: 10px; margin-top: 20px;}
    .pullback-card { border-left: 8px solid #BC13FE; background-color: #1a0024; padding: 15px; margin-bottom: 10px; border-radius: 8px; }
    </style>
    """, unsafe_allow_html=True)

@st.cache_data(ttl=3600)
def smart_fetch(ticker_sym, period="1y"):
    try:
        time.sleep(0.3) 
        data = yf.Ticker(ticker_sym).history(period=period, auto_adjust=True)
        if data.empty:
            time.sleep(1.0) 
            data = yf.Ticker(ticker_sym).history(period=period, auto_adjust=True)
        return data.dropna(subset=['Close', 'Volume', 'High', 'Low', 'Open'])
    except: return pd.DataFrame()

@st.cache_data(ttl=3600)
def get_all_data(ticker_sym):
    try:
        time.sleep(0.3); asset = yf.Ticker(ticker_sym); info = asset.info
        try: holders = asset.institutional_holders
        except: holders = None
        iv = "N/A"
        try:
            options = asset.options
            if options:
                chain = asset.option_chain(options[0])
                if not chain.calls.empty:
                    mid_idx = len(chain.calls) // 2
                    iv = f"{chain.calls.iloc[mid_idx]['impliedVolatility'] * 100:.1f}%"
        except: pass
        return info, holders, iv
    except: return {}, None, "N/A"

def cap_pct(val):
    try:
        v = float(val)
        return max(-999.0, min(999.0, v)) if not np.isnan(v) and not np.isinf(v) else 0.0
    except: return 0.0

def add_energy_subplots(fig, df, row_start):
    # 第一層：買賣力度 (2層4色立體化)
    var1 = df['Close'] - df['Low']
    var2 = df['High'] - df['Close']
    var3 = np.maximum(df['High'] - df['Low'], 0.001)
    buyvol = np.where(var3 > 0, df['Volume'] * var1 / var3, 0)
    sellvol = np.where(var3 > 0, df['Volume'] * var2 / var3, 0)
    netvol = buyvol - sellvol
    netma = pd.Series(netvol).rolling(10, min_periods=1).mean()
    dates = df.index.strftime('%Y-%m-%d')
    
    # 總兵力底色 (暗色, 闊身)
    fig.add_trace(go.Bar(x=dates, y=buyvol, marker_color='#808000', name='買盤背景', opacity=0.6, hoverinfo='skip'), row=row_start, col=1)
    fig.add_trace(go.Bar(x=dates, y=-sellvol, marker_color='#800000', name='賣盤背景', opacity=0.6, hoverinfo='skip'), row=row_start, col=1)
    # 淨勝方高光 (鮮色, 幼身疊加)
    net_colors = ['#00FF00' if val > 0 else '#FF0000' for val in netvol]
    fig.add_trace(go.Bar(x=dates, y=netvol, marker_color=net_colors, name='淨勝方', width=0.4), row=row_start, col=1)
    fig.add_trace(go.Scatter(x=dates, y=netma, mode='lines', line=dict(color='white', width=2), name='氣脈10MA'), row=row_start, col=1)

    # 第二層：王者能量雷達
    v_ma = df['Volume'].rolling(20, min_periods=1).mean()
    v_std = df['Volume'].rolling(20, min_periods=1).std().fillna(0)
    v_upper = v_ma + (2.0 * v_std)
    ma60 = df['Volume'].rolling(60, min_periods=1).mean()
    roc = abs(df['Close'].pct_change()) * 100
    is_burst = (df['Volume'] > v_upper) & (df['Volume'] > ma60 * 1.9) & (roc > 2.0)
    burst_colors = ['#00FFFF' if (is_burst.iloc[i] and df['Close'].iloc[i] > df['Open'].iloc[i]) else ('#FF00FF' if is_burst.iloc[i] else 'rgba(136,136,136,0.3)') for i in range(len(df))]
    fig.add_trace(go.Bar(x=dates, y=df['Volume'], marker_color=burst_colors, name='能量雷達'), row=row_start+1, col=1)

    # 第三層：日波幅%
    daily_change = df['Close'].pct_change() * 100
    change_colors = ['#00FF00' if val >= 0 else '#FF0000' for val in daily_change]
    fig.add_trace(go.Bar(x=dates, y=daily_change, marker_color=change_colors, name='日波幅%'), row=row_start+2, col=1)

def safe_n(val, alt=50.0): 
    try: v = float(val); return v if not np.isnan(v) and not np.isinf(v) else alt
    except: return alt 

def safe_s(info, keys, suffix="", alt="N/A"): 
    for k in keys: 
        v = info.get(k)
        if v is not None and v != "" and str(v).lower() not in ['nan', 'inf', 'none']:
            try: return f"{float(v):.2f}{suffix}"
            except: pass
    return alt 

def get_beta(info, df, spy_df): 
    b = info.get('beta')
    if b is not None and str(b).lower() not in ['nan', 'none', '']: return f"{float(b):.2f}"
    try:
        da, sa = df['Close'].align(spy_df['Close'], join='inner')
        ar = da.pct_change().dropna().tail(252); sr = sa.pct_change().dropna().tail(252)
        if len(ar) > 30:
            cov = np.cov(ar, sr)[0][1]; var = np.var(sr)
            if var > 0: return f"{(cov / var):.2f}"
    except: pass
    return "1.00"

def get_alpha(beta, df, spy_df):
    try:
        b = float(beta); df_aligned, spy_aligned = df['Close'].align(spy_df['Close'], join='inner')
        asset_ret = (df_aligned.iloc[-1] - df_aligned.iloc[0]) / df_aligned.iloc[0]
        spy_ret = (spy_aligned.iloc[-1] - spy_aligned.iloc[0]) / spy_aligned.iloc[0]
        risk_free = 0.04; alpha = asset_ret - (risk_free + b * (spy_ret - risk_free))
        return f"{alpha * 100:.1f}%"
    except: return "N/A"

def get_volatility(df):
    try:
        ret = df['Close'].pct_change().dropna().tail(252)
        vol = ret.std() * np.sqrt(252)
        return f"{vol * 100:.1f}%"
    except: return "N/A"

HK_STOCK_MAP = {
    "1. 互聯網巨頭": "0700.HK 9988.HK 3690.HK 1810.HK 9618.HK 1024.HK 9888.HK 0772.HK 0020.HK 0241.HK 0136.HK 1999.HK 2018.HK 3888.HK 2142.HK 1896.HK 0777.HK 0113.HK 0590.HK 1980.HK 1797.HK 6618.HK 2400.HK 0285.HK".split(),
    "2. 半導體與芯片": "0981.HK 1347.HK 0285.HK 1478.HK 1833.HK 0522.HK 0732.HK 2382.HK 2018.HK 0099.HK 1385.HK 1138.HK 1910.HK 6088.HK 3898.HK 6123.HK 3389.HK".split(),
    "3. 新能源車與整車": "1211.HK 2015.HK 9866.HK 9868.HK 0175.HK 2333.HK 1114.HK 0489.HK 3606.HK 0867.HK 1316.HK 1958.HK 1585.HK 0315.HK 1274.HK 2150.HK 1122.HK 3808.HK 9863.HK".split(),
    "4. 重型工業與機械": "1133.HK 1072.HK 1888.HK 1286.HK 3399.HK 1157.HK 2727.HK 1727.HK 6030.HK 0598.HK 0165.HK 0350.HK 1071.HK 1839.HK 1866.HK 0316.HK 0148.HK 1651.HK 1829.HK 1044.HK".split(),
    "5. 國有大行與金融": "0005.HK 0939.HK 1398.HK 3988.HK 2318.HK 2388.HK 0011.HK 3968.HK 3328.HK 0998.HK 0023.HK 2016.HK 1658.HK 6198.HK 0410.HK 6066.HK 1551.HK 1963.HK 1988.HK 3866.HK".split(),
    "6. 基礎化工與材料": "0148.HK 1651.HK 1378.HK 3360.HK 1963.HK 0860.HK 1282.HK 1387.HK 0386.HK 1812.HK 2128.HK 1126.HK 0268.HK 0338.HK 2009.HK 3389.HK 1008.HK 1898.HK 3993.HK 0868.HK".split(),
    "7. 石油氣與能源設備": "0883.HK 0857.HK 0386.HK 1193.HK 1083.HK 0003.HK 2688.HK 0392.HK 1035.HK 0135.HK 1600.HK 1250.HK 0855.HK 3330.HK 1138.HK 0164.HK 2883.HK 0135.HK".split(),
    "8. 煤炭與有色金屬": "1088.HK 1171.HK 1898.HK 2899.HK 0358.HK 3993.HK 0471.HK 1378.HK 3939.HK 0895.HK 0868.HK 1258.HK 1818.HK 3983.HK 2099.HK 1208.HK 1963.HK 2302.HK 0347.HK".split(),
    "9. 電力與綠能": "0902.HK 0836.HK 1816.HK 0916.HK 1798.HK 0958.HK 0006.HK 1071.HK 1250.HK 3800.HK 0002.HK 1193.HK 0819.HK 2380.HK 0735.HK 0384.HK 0066.HK 1038.HK".split(),
    "10. 房地產開發": "1109.HK 0688.HK 0960.HK 1918.HK 3383.HK 0884.HK 1233.HK 2777.HK 0813.HK 2007.HK 3301.HK 1638.HK 0012.HK 0016.HK 0017.HK 0101.HK 3900.HK 0817.HK 1966.HK".split(),
    "11. 物業管理服務": "6098.HK 1209.HK 2669.HK 3319.HK 1516.HK 1755.HK 1995.HK 2869.HK 9909.HK 0873.HK 9928.HK 6626.HK 9983.HK 9979.HK 2168.HK 2602.HK 3316.HK".split(),
    "12. 消費電子硬件": "2382.HK 2018.HK 0669.HK 0992.HK 1310.HK 0008.HK 1478.HK 0285.HK 0321.HK 0596.HK 0732.HK 0522.HK 1070.HK 0099.HK 0285.HK".split(),
    "13. 核心消費與餐飲": "0291.HK 2319.HK 0322.HK 1876.HK 9633.HK 6186.HK 0220.HK 1117.HK 0151.HK 1458.HK 1368.HK 6862.HK 9922.HK 2005.HK 0831.HK 0341.HK 1089.HK 6868.HK 1929.HK".split(),
    "14. 生物科技探索": "2269.HK 2359.HK 1801.HK 2162.HK 9966.HK 9969.HK 3759.HK 1548.HK 9926.HK 6990.HK 2126.HK 9939.HK 1099.HK 2171.HK 0512.HK 1952.HK 2096.HK".split(),
    "15. 傳統中西藥業": "1093.HK 1177.HK 1515.HK 0511.HK 2666.HK 3320.HK 2196.HK 0867.HK 1099.HK 0460.HK 0853.HK 1513.HK 3933.HK 1528.HK 1513.HK 2005.HK".split(),
    "16. 澳門博彩": "1928.HK 0027.HK 1128.HK 0880.HK 0200.HK 0037.HK 1628.HK 0576.HK 3918.HK 1180.HK 0256.HK".split(),
    "17. 體育與服裝": "2020.HK 2331.HK 1368.HK 3813.HK 6110.HK 0551.HK 1910.HK 3998.HK 2238.HK 2999.HK 1968.HK 1361.HK 3306.HK 0411.HK 0484.HK 1999.HK".split(),
    "18. 海運航運物流": "1919.HK 1308.HK 2343.HK 2600.HK 0591.HK 1519.HK 1101.HK 2866.HK 0316.HK 0598.HK 0368.HK".split(),
    "19. 電訊與網絡": "0941.HK 0728.HK 0762.HK 1883.HK 6823.HK 6033.HK 0008.HK 0215.HK 1098.HK 0066.HK 0116.HK".split(),
    "20. 公用與基礎建設": "0002.HK 1038.HK 0066.HK 1186.HK 0390.HK 1800.HK 0270.HK 3311.HK 1618.HK 1083.HK 0371.HK 0165.HK 0250.HK".split(),
    "21. 農業與食品供應": "2319.HK 1610.HK 1117.HK 1431.HK 0061.HK 0220.HK 0341.HK 3998.HK 1089.HK 1269.HK 1006.HK".split(),
    "22. 券商與保險": "3908.HK 6030.HK 6881.HK 1299.HK 2628.HK 2318.HK 0966.HK 1336.HK 6099.HK 1776.HK 6178.HK 3968.HK 1551.HK 6066.HK 1339.HK".split()
}

US_STOCK_MAP = {
    "1. 半導體設備與設計": "NVDA TSM AVGO ASML AMD QCOM TXN MU INTC AMAT LRCX KLAC ADI NXPI MRVL MCHP SWKS MPWR ON LSCC TER QRVO SLAB WOLF SYNA RMBS ALGM SITM ACLS CRUS".split(),
    "2. AI與大數據雲端": "MSFT GOOGL ORCL ADBE CRM PLTR SNOW PANW FTNT NOW WDAY ZS DDOG CRWD MDB NET OKTA TEAM SPLK GEN CYBR CHKP VRSN ESTC TENB SQSP PCOR DOCN AI FSLY MSTR".split(),
    "3. 基礎軟件與 SaaS": "INTU VMW CDNS PTC MSTR SPT ALTR MANH GWRE PAYC APPN TYL BLK PEGA BL DT DBX PATH BSY NCNO WK ME LAW ALIT VRM HCP RNG".split(),
    "4. 網絡安全 (Cyber)": "PANW CRWD FTNT ZS CYBR CHKP GEN TENB NET OKTA S OKTA VRNS QLYS SAIL MIME RPD PFPT FEYE EVBG IMPV".split(),
    "5. 消費電子與硬件": "AAPL HPQ DELL STX WDC APH TEL LOGI HPE NTAP GLW ST ANET FFIV GRMN LITE SMCI VRT JBL FLEX NVT ROK CSL HUBB CNHI GWW PH SANM PLXS".split(),
    "6. 通訊與網絡設備": "CSCO MSI JNPR ANET COMM ZBRA JNPR CIEN LITE VIAV ADTN CALX HLIT INFN NTGR ACIA EXTR CRDO FN CLFD".split(),
    "7. 互聯網平台內容": "META GOOGL PINS SNAP MATCH MTCH IAC OGI YELP BMBL BUMBLE GRND COMP ZIP TRUE CARG MTTR LEA GRPN".split(),
    "8. 媒體與影視娛樂": "NFLX DIS WBD PARA LYV SPOT SIRI ROKU NWSA NYT FOXA OMC IPG WPP NWS EVC NXST MEG TGNA SSP GTN SGA".split(),
    "9. 電子商務與零售": "AMZN EBAY ETSY MELI SHOP PDD BABA JD SE CPNG W GMED CVNA FAIR FTCH CHWY OSTK REAL RVLV PRTS QRTEA POSH VIPS BZUN".split(),
    "10. 傳統零售百貨": "WMT COST TGT DG DLTR KR SYY K DLTR BIG BBY BJ CFG SFM UNFI IMKTA SPTN ANDE VLGEA INTA GROC".split(),
    "11. 核心消費品": "PG KO PEP PM MO EL CL KDP GIS HSY KHC CPB MKC MDLZ SJM CAG STZ TSN K CPB KHC GIS HSY CPB SJM TAP BF.B CHD POST".split(),
    "12. 汽車製造商": "F GM STLA TM HMC RACE CARZ HOG WGO REV GOLF LCII WGO REVG SRG".split(),
    "13. 電動車與自駕 (EV)": "TSLA RIVN LCID LI NIO XPEV MSTR UBER LYFT QS AUR GWB ALV LEA MGA BWA APTV VC THO DORM WGO PSNY FSR GOEV HYZN PTRA LEV VLTA".split(),
    "14. 汽車零部件": "MGA APTV BWA LEA VC DAN ALV GNTX AXA FOXF SMP THO TEN CTB HY MLR SUP MOD PRG".split(),
    "15. 航空航天與國防": "LMT RTX NOC GD BA TDG HWM LHX LDOS TXT HEI WWD SPR BWXT AVAV KTOS MRCY ATRO NP KEX ESLT CW ST VSEC ASIX AJRD KAMN".split(),
    "16. 重型機械裝備": "CAT DE CMI PCAR OSK TEX TRN ALG GGW HY ALG REVG B RC BRC RAIL ARNC WNC GBX".split(),
    "17. 工業綜合集團": "GE HON MMM EMR ITW ETN PH ROK DOV URI IR PNR GWW NDSN AOS SWK SNA FLS LECO IEX GGG TTC NVT HUBB".split(),
    "18. 運輸與物流": "UNP UPS FDX NSC CSX LSTR OPY SAIA MATX ARCB XPO KNX SNDR HTLD PTEN CVTI WERN HUBG MRIN YELL EEX USX".split(),
    "19. 航空與機場": "LUV DAL AAL UAL ALK JBLU SAVE HA SKYW SNC LTM ULCC MESA JOBY ACHR".split(),
    "20. 旅遊酒店博彩": "BKNG ABNB MAR HLT LVS WYNN MGM RCL CCL EXPE NCLH WH CHH PENN CZR BALY CHDN RRR GDEN PLCE SG".split(),
    "21. 餐飲連鎖": "MCD SBUX YUM CMG DPZ DRI QSR YUMC TXRH DARD BLMN EAT CAKE PLAY DENN RUTH PZZA WEN SHAK JACK TACO CHUY".split(),
    "22. 商業銀行巨頭": "JPM BAC WFC C GS MS AXP BLK V MA PYPL DFS SYF ALL COF COF AXP DFS SYF ALL RF CFG FITB MTB HBAN KEY CMA ZION".split(),
    "23. 區域性銀行": "KRE PNC TFC USB EWBC WAL PACW FRC SNV FHN BOKF WTFC CFR CUBI PB CTBI ONB BOH UMBF CBSH FNB CATY".split(),
    "24. 投資與資產管理": "BLK BX TROW APO KKC KKR CG ARES OWL OAK STEP BEN STT BK NTRS IVZ JHG AMG LAZ APAM".split(),
    "25. 金融科技與支付": "V MA SQ PYPL AFRM SOFI NU GPN FIS FI FISV TOST MQ BILL FLYW REVG BKI LPRO IIIV HAE FOR EVTC RPCE FLT WEX REVG".split(),
    "26. 保險經紀與服務": "CB PGR TRV MET AIG PRU TRV HIG AFL L AL MKL CINF RGA RE WRB GL CNA AFG SIGI THG KMPR".split(),
    "27. 傳統製藥巨頭": "LLY NVO JNJ MRK ABBV PFE AMGN VRTX REGN GILD BMY BMY GSK SNY AZN NVS TEVA TAK RHHBY".split(),
    "28. 大中型生物科技": "MRNA BNTX BIIB INCY BMRN ALXN SGEN EXAS ILMN ALNY SRPT VRTX BMRN UTHR ARGX DNA CRSP NTLA EDIT BEAM".split(),
    "29. 醫療設備與器械": "MDT ABT SYK BSX EW BDX ISRG ZBH STE ALGN RMD HOLX XRAY COO TFX PEN RES IART GMED OMCL".split(),
    "30. 醫療服務與管理": "UNH ELV CVS CI HUM HCA CNC MOH ACHC SEM EHC CHE MODV OPK ADUS DVA USPH AMN EHC NHC CHE".split(),
    "31. 基因與生命科學": "ILMN TMO A TMO DHR CTLT WAT IQV MTD BRKR PKI CRL BIO TECH MED PINC QGEN NEO NEO EXAS".split(),
    "32. 傳統能源 (油氣)": "XOM CVX COP SLB HAL MPC PSX VLO OXY HES DVN EOG PXD FANG CXO CLR MRO PXD FANG MUR MRO APA MTDR".split(),
    "33. 油氣設備與服務": "SLB HAL BKR FTI NBR NOV CHX WTTR PTEN LBRT OIS RES HLX NCS NEX NINE SOI WTTR".split(),
    "34. 太陽能與清潔能源": "FSLR ENPH SEDG RUN SHLS NEE BE CWEN AY NOVA MAXN SPWR ARRY STEM PLUG DQ JKS CSIQ NEP HASI BEP PEGI TPIC".split(),
    "35. 公用事業 (水電)": "NEE SO DUK SRE AEP D EXC PCG FE ED PEG XEL WEC ES AWK LNT CMS NI ATO EVRG PNW CNP DTE PPL".split(),
    "36. 基礎與特殊化工": "LIN APD DOW LYB CE IFF ECL FMC EMN CF MOS NTR SMG WLK HUN ALB OLN ASH KRA GRA GGG FUL".split(),
    "37. 鋼鐵與基礎金屬": "NUE STLD X CLF RS RS CMP WOR RYI TMST CRS HAYN KALU ATI SCHN USAP ZEUS".split(),
    "38. 黃金與貴金屬": "NEM GOLD FCX SCCO AEM KGC WPM RGLD FNV HL CDE EXK IAG GORO GSS SA MUX TRX EGO AUY".split(),
    "39. 住宅房地產開發": "LEN DHI PHM TOL NVR KBH TMHC MDC MHO LGIH GRBK CCS BLD BZH HOV TPH".split(),
    "40. 商業地產 REITs": "PLD AMT EQIX CCI PSA O SPG VICI CBRE ARE DRE EXR DLR MAA AVB WELL VTR PEAK INV INVH CPT ESS UDR EQR".split(),
    "41. 特殊與基建 REITs": "AMT CCI SBAC DLR EQIX CONE COR QTS IRM LAMR OUT UNIT GLPI VICI EPR LXP".split(),
    "42. 加密貨幣與區塊鏈": "COIN MSTR MARA RIOT HUT CLSK CIFR BITF HIVE SDIG BTBT GLXY WULF CORZ ARBK IREN".split(),
    "43. 農業與肥料": "DE CTVA CF MOS NTR FMC SMG SQM IPI UAN SEB BIOC LMNR AVD CVA LNN".split(),
    "44. 體育戶外與服飾": "NKE LULU UA UAA CROX DECK ONON SKX PLCE FL LEVI VFC KTB BOOT WWW SHOO TBLA RCKY".split(),
    "45. 教育科技": "CHGG COUR LRN TWOU PRDO STRA APEI ATGE LOPE UTI LAUR BFAM".split(),
    "46. 太空與前沿探索": "SPCE RKLB PL BKSY ASTS RDW MNTS LLAP SIDU SPIR SATS SPIR LUNR ACHR JOBY".split(),
    "47. 機器人與自動化": "PATH SYM CGNX ISGN KEX LECO ROK PTC FARO FLIR ALTR NVMI ACLS CAMT ICHR COHU".split(),
    "48. 中型價值精選": "WSM GPC WSM WILLIAMS TSCO ODFL MIDD SAIA R EXPD CHRW GGG DOV NDSN LECO WTS ITW".split(),
    "49. 小型爆發精選": "CELH WING APP ELF ANF MOD MSTR SMCI TMDX AXON FOUR INDI VRT ALKT ACLS MOD ONTO POWI".split(),
    "50. 超微型探索 (Micro)": "SOUN RXRX AI BBAI HIVE VLD IONQ BBAI CRDO NRDS INDI LUNA QBTS KTRA RGTI ARQQ INVZ".split()
}

HK_ETF_MAP = {
    "H1. A股門戶/旗艦大盤": "2822.HK 3188.HK 3109.HK 2823.HK 2846.HK 3147.HK 2801.HK 3010.HK 3081.HK 3151.HK 3072.HK 3042.HK 2839.HK 3180.HK 2827.HK 3139.HK 3118.HK 2838.HK".split(),
    "H2. 港股科技/AI/芯片": "3033.HK 3088.HK 9888.HK 3067.HK 3167.HK 3191.HK 7709.HK 9191.HK 3434.HK 3112.HK 3171.HK 3091.HK 3032.HK 3001.HK 3060.HK 2826.HK".split(),
    "H3. A股及港股行業板塊": "3134.HK 2845.HK 9845.HK 3136.HK 3069.HK 3174.HK 2820.HK 3133.HK 3111.HK 3141.HK 3148.HK 3149.HK 2842.HK 3120.HK 2806.HK 3143.HK 3137.HK 3051.HK".split(),
    "H4. 紅利收息/Covered Call": "3110.HK 3070.HK 3101.HK 3037.HK 3145.HK 3010.HK 3081.HK 3115.HK 3006.HK 3150.HK 3422.HK 3116.HK 3113.HK 3031.HK 3153.HK".split(),
    "H5. 虛擬資產/加密貨幣": "3066.HK 3068.HK 3439.HK 3419.HK 3460.HK 3461.HK 3471.HK 3472.HK 3083.HK 3087.HK 3135.HK 3175.HK 7799.HK 7711.HK 7747.HK".split(),
    "H6. 商品/債券/貨幣基金": "2840.HK 3030.HK 3152.HK 3192.HK 3196.HK 3161.HK 3071.HK 2812.HK 3140.HK 3181.HK 3187.HK 3189.HK 3192.HK 3117.HK 3011.HK 3119.HK".split(),
    "H7. 槓桿/反向 (指數/商品)": "7200.HK 7226.HK 7205.HK 7299.HK 7266.HK 7500.HK 7522.HK 7552.HK 7300.HK 7333.HK 7348.HK 7233.HK 7248.HK 7288.HK 7231.HK".split()
}

US_ETF_MAP = {
    "U1. Thematic 主題 A (1-70)": "BWET OIH LIT GSG XTL PDBC DBC SOXX FCG SLX IXC REMX ROKT FENY VDE AIS SMH XOP IYE XLE AIRR UFO XBI IDGT TAN DTCR ICLN XME KRE GRID IFRA PAVE XSMO XMMO KBWB VIS SPHB XLI SLYG IJK XSD IJT IVOG EXI ARTY URNM ROBO FXR IWM RSPT QTUM VBK IXN IWO VTWG ARKQ ARKX NUKZ URA NLR GNR GUNR SIL COPX GDX GDXJ IAU GLD IBB GDE QQQ VOX".split(),
    "U2. Thematic 主題 B (71-140)": "FCOM ONEQ MLPX FBCG SPMO IVW SPYG XLK IGM QGRW FTEC VGT QTEC TDIV IYW AIQ XT FELG MGK VUG IWF IWY SCHG MAGS EMLP XLB KOMP BOTZ VAW SOYB AMLP BCI ARKG FTGC KBE CORN EUFN USRT RWR SPXT ICF SCHH NFRA RWO DFAR DIA IYJ REET FUTY VPU IYR VNQ FREL DFGR UTES IMCG FTC SLV XAR SILJ ITA WEAT PPLT VEGI MOO IGF TAGS VDC".split(),
    "U3. Thematic 主題 C (141-214)": "FSTA XLP DBA FXU SPY IDU XLU XLRE CGW QQQE IYF XLC IAI JGRO FDIS VCR SHLD ARKK BLOK SPLV XLY FTXG IYK IXJ IYG PALL XHB BKCH ARKW LQD HYG VHT FHLC IYH XLV VNQI IYC QQEW ITB TLT FIW XLF VFH FNCL IWP CIBR HACK VOT FDN SKYY IHI PHO BIZD CANE BUG IGV GBTC BTC HODL FBTC ARKB BITB IBIT BITO ARKF ETHA".split(),
    "U4. SPDR 核心板塊": "XLE XBI XLI XLK XLB XLP XLU XLRE XLC XLY XLV XLF".split(),
    "U5. 全球國家/地區": "EWY EWZ ILF EIS EWT TUR ECH EFNL EWC EWP EWH EWI EPOL EPU EWW THD VNM EWM EWA EWJ EWN EWS EWQ EZA EWU EWL SPY KSA EWD EWG UAE QAT EPHE FXI EIDO INDA".split()
}

@st.cache_data(ttl=3600)
def get_breadth_data(tickers):
    stats = {'20MA':0, '50MA':0, '150MA':0, '200MA':0, 'valid':0, 'above_50_list': [], 'hist_20MA': [0]*20, 'hist_50MA': [0]*20, 'hist_150MA': [0]*20, 'hist_200MA': [0]*20}
    if not tickers: return {'valid': 1, 'above_50_list': [], 'hist_20MA': [0]*20, 'hist_50MA': [0]*20, 'hist_150MA': [0]*20, 'hist_200MA': [0]*20}
    for t in tickers:
        try:
            c = smart_fetch(t, period="1y")['Close'].dropna(); n = len(c)
            if n < 50: continue
            curr = c.iloc[-1]
            if curr > c.tail(20).mean(): stats['20MA'] += 1
            if curr > c.tail(50).mean(): stats['50MA'] += 1; stats['above_50_list'].append(t)
            if n >= 150 and curr > c.tail(150).mean(): stats['150MA'] += 1
            if n >= 200 and curr > c.tail(200).mean(): stats['200MA'] += 1
            for i in range(20):
                end_idx = n - (19 - i)
                if end_idx >= 20:
                    past_curr = c.iloc[end_idx - 1]
                    if past_curr > c.iloc[end_idx-20:end_idx].mean(): stats['hist_20MA'][i] += 1
                    if end_idx >= 50 and past_curr > c.iloc[end_idx-50:end_idx].mean(): stats['hist_50MA'][i] += 1
                    if end_idx >= 150 and past_curr > c.iloc[end_idx-150:end_idx].mean(): stats['hist_150MA'][i] += 1
                    if end_idx >= 200 and past_curr > c.iloc[end_idx-200:end_idx].mean(): stats['hist_200MA'][i] += 1
            stats['valid'] += 1
        except: pass
    stats['valid'] = max(1, stats['valid'])
    return stats

st.sidebar.markdown("## 🛰️ 戰術控制台 (V188.0)")
app_mode = st.sidebar.radio("請選擇操作", ["🚀 個股深度透視", "🛡️ 環球市底大師指揮塔", "📡 個股版塊拔河熱力圖", "📡 ETF 資產拔河熱力圖", "🔍 千龍起步尋龍雷達 (個股)", "🛡️ 美股 ETF 專屬雷達", "🛡️ 港/A股 ETF 專屬雷達", "📈 VCP 形態戰術掃描 & 防守圖", "🌊 海龜回測加注雷達 (Mode E)"])
show_b_idx = show_b_ma20 = show_b_ma50 = show_b_ma150 = show_b_ma200 = True

if app_mode in ["🚀 個股深度透視", "🛡️ 環球市底大師指揮塔"]:
    st.sidebar.markdown("---")
    st.sidebar.header("🎭 投行定性打分 (X-Factor)")
    s10_mgmt = st.sidebar.slider("10. 靈魂人物溢價 (CEO/執行力)", 0, 100, 70)
    s11_story = st.sidebar.slider("11. 時代敘事溢價", 0, 100, 80)
    x_factor = st.sidebar.selectbox("🕵️‍♂️ 投行隱藏 X 因子", ["無特殊狀況", "跨界第二曲線 (+10分)", "自動印鈔機護城河 (+5分)", "隱形吸血鬼SBC (-15分)"])
    st.sidebar.markdown("---")
    st.sidebar.markdown("### 🛠️ 圖表顯示開關")
    st.sidebar.markdown("**📈 個股均線區**")
    show_s_ma20 = st.sidebar.checkbox("20日線 (短線動能)", value=False)
    show_s_ma50 = st.sidebar.checkbox("50日線 / 10周 (中期趨勢)", value=False)
    show_s_ma150 = st.sidebar.checkbox("150日線 / 30周 (大師分界)", value=False)
    show_s_ma200 = st.sidebar.checkbox("200日線 (終極牛熊)", value=False)

# =========================================================================
# 🚀 模式 A：個股深度透視
# =========================================================================
if app_mode == "🚀 個股深度透視":
    ticker = st.sidebar.text_input("🚀 輸入資產代號", "6869.HK").upper()
    with st.spinner(f"⏳ 系統正在切換引擎，重新為您下載海量數據及繪製摩訶圖... 請稍候 ☕🚀"):
        try:
            info, holders, iv_val = get_all_data(ticker)
            df = smart_fetch(ticker, period="2y")
            bench_sym_for_rs = "^HSI" if ".HK" in ticker else "SPY"
            spy = smart_fetch(bench_sym_for_rs, period="2y")
            b_sym_plot = "2800.HK" if ".HK" in ticker else "SPY"
            b_df_plot = smart_fetch(b_sym_plot, period="2y")
            
            if not b_df_plot.empty:
                b_df_plot['20MA'] = b_df_plot['Close'].rolling(20, min_periods=1).mean().bfill()
                b_df_plot['50MA'] = b_df_plot['Close'].rolling(50, min_periods=1).mean().bfill()
                b_df_plot['150MA'] = b_df_plot['Close'].rolling(150, min_periods=1).mean().bfill()
                b_df_plot['200MA'] = b_df_plot['Close'].rolling(200, min_periods=1).mean().bfill()

            if not df.empty:
                if df.index.tz is not None: df.index = df.index.tz_localize(None)
                df.index = df.index.normalize()
                if spy.index.tz is not None: spy.index = spy.index.tz_localize(None)
                spy.index = spy.index.normalize()
                curr_p = df['Close'].iloc[-1]
                
                asset_name = info.get('shortName', info.get('longName', ''))
                industry_str = f" | {info.get('sector', 'N/A')} - {info.get('industry', 'N/A')}" if info.get('sector') else ""
                name_html = f"<span style='font-size: 1.8rem; color: #AAAAAA; font-weight: 500; margin-left: 15px;'>{asset_name}{industry_str}</span>" if asset_name else ""
                st.markdown(f"""<div class='main-title' style='margin-bottom:10px;'>環球資產透視評估儀 [{ticker}]{name_html}</div>""", unsafe_allow_html=True)
                
                ath_val = df['High'].tail(252).max() if len(df) > 0 else curr_p
                dist_ath = ((curr_p / ath_val) - 1) * 100 if ath_val and ath_val > 0 else 0
                df['50MA_strat'] = df['Close'].rolling(50, min_periods=1).mean().bfill()
                ma50_bias = ((curr_p / df['50MA_strat'].iloc[-1]) - 1) * 100 if df['50MA_strat'].iloc[-1] > 0 else 0
                
                st.markdown(f"""<div style='display: flex; gap: 15px; margin-bottom: 25px;'><div class='red-bar' style='flex: 1; background-color: #310000; border: 2px solid #FF4B4B; padding: 15px; font-size: 1.8rem;'>🎯 巔峰收復進度：距離 52周高位 [ {dist_ath:.1f}% ]</div><div class='red-bar' style='flex: 1; background-color: #002222; border: 2px solid #00FFCC; padding: 15px; font-size: 1.8rem;'>⚖️ 地心引力監控：偏離 50日線 [ {ma50_bias:+.1f}% ]</div></div>""", unsafe_allow_html=True)
                st.markdown(f"""<div style='text-align: center; color: #00FFCC; font-size: 1.2rem; font-weight: bold; margin-bottom: 25px; padding: 10px; background-color: rgba(0, 255, 204, 0.1); border-radius: 8px; border: 1px dashed #00FFCC;'>🛡️ 必勝潛伏方程式：COSMOS-RS (星系強弱) > 52, EJ 錢流底氣 > 85, 短期能量 > 75, 最近 20 日主力資金池淨額是正數買入，OBV 大戶籌碼流入或觀望，資金部署集中度是分散</div>""", unsafe_allow_html=True)

# ================= 爺爺修正：核心動能與EJ底氣 (PART A 醫好0688) =================
                c_tail = df['Close'].tail(125)
                if len(c_tail) > 15:
                    days_arr = np.arange(len(c_tail))
                    slope, intercept = np.polyfit(days_arr, c_tail, 1)
                    avg_p = max(c_tail.mean(), 0.01)
                    v_std_ann = max(0.001, c_tail.pct_change().std() * np.sqrt(252))
                    # 修正：移除不穩定 mom 乘數，確保 0688 呢類強勢股唔會變 0
                    # 爺爺終極真龍版：底分 75 起跳，再加上動能增幅
                    raw_val = 75.0 + (((slope * 252) / avg_p / v_std_ann) * 50)
                    cx_val = safe_n(raw_val, 50.0)
                    cx_val = max(5.0, cx_val) # 強制保底，唔好出 0
                else:
                    cx_val = 50.0

                # 修正 RS (星系強弱)
                spy_aligned = spy['Close'].reindex(df.index).ffill().bfill() 
                rs_look_idx = min(63, len(df)-1)
                crs_val = safe_n(50 + ((curr_p / df['Close'].iloc[-rs_look_idx]) - (spy_aligned.iloc[-1] / spy_aligned.iloc[-rs_look_idx])) * 100, 50.0)
                
                # 修正 EJ (錢流底氣)：鎖定分母，避免數據缺失導致負數
                v21_avg = df['Volume'].tail(21).mean()
                v252_ref = df['Volume'].tail(252).mean() if len(df) > 200 else df['Volume'].mean()
                cej_s = safe_n((v21_avg / max(v252_ref, 0.001)) * 100, 50.0)
                cej_s = max(1.0, cej_s) # 確保係正數
                
                # 修正 SE (短期能量)
                se_look_idx = max(1, min(5, len(df)-1))
                se_s = safe_n(50 + (((curr_p / df['Close'].iloc[-se_look_idx]) - 1) * 1200), 50.0)
                se_s = max(1.0, se_s) # 確保係正數
                # ============================================================================
                def get_trend_stats(metric):
                    try:
                        if len(df) < 5: return "數據累積中", "#888"
                        compare_idx = max(1, min(20, len(df)-1))
                        if metric == "RS":
                            past_p = df['Close'].iloc[-compare_idx]; past_spy = spy_aligned.iloc[-compare_idx]
                            past_bench = df['Close'].iloc[-max(1, min(83, len(df)-1))]
                            past_bench_spy = spy_aligned.iloc[-max(1, min(83, len(spy_aligned)-1))]
                            past = 50 + ((past_p / past_bench) - (past_spy / past_bench_spy)) * 100
                            diff = cap_pct(crs_val - past)
                        elif metric == "EJ":
                            v_past_21 = df['Volume'].iloc[-min(len(df)-1, compare_idx+21):-compare_idx].mean() if len(df) > compare_idx+21 else df['Volume'].iloc[0]
                            past = (v_past_21 / max(v252_ref, 0.001)) * 100
                            diff = cap_pct(cej_s - past)
                        else: 
                            past = 50 + (((df['Close'].iloc[-compare_idx] / df['Close'].iloc[-max(1, min(compare_idx+5, len(df)-1))]) - 1) * 1200)
                            diff = cap_pct(se_s - past)
                        color = "#00FF00" if diff >= 0 else "#FF4B4B"
                        return f"{'+' if diff>=0 else ''}{diff:.1f}%", color
                    except: return "N/A", "#888"

                def get_pulse_fig(pulse_vals):
                    try:
                        colors = ['#00FFCC' if v >= 0 else '#FF4B4B' for v in pulse_vals]
                        fig = go.Figure(go.Bar(x=list(range(len(pulse_vals))), y=pulse_vals, marker_color=colors, hoverinfo='skip'))
                        fig.update_layout(height=130, margin=dict(l=0,r=0,t=5,b=0), paper_bgcolor='rgba(0,0,0,0)', plot_bgcolor='rgba(0,0,0,0)', xaxis=dict(visible=False, fixedrange=True), yaxis=dict(visible=False, fixedrange=True), showlegend=False)
                        return fig
                    except: return go.Figure().update_layout(height=130, paper_bgcolor='rgba(0,0,0,0)', plot_bgcolor='rgba(0,0,0,0)', xaxis=dict(visible=False), yaxis=dict(visible=False))

                q_asset = int(min(100, max(0, safe_n(info.get('returnOnEquity', 0.1)*300 + 50, 75)))); q_trend = int(min(100, max(0, crs_val))); q_power = int(min(100, max(0, cx_val * 1.5)))
                q_money = int(min(100, max(0, cej_s))); q_sent  = int(min(100, max(0, se_s))); q_total = int((q_asset + q_trend + q_power + q_money + q_sent) / 5)
                q_pivot = df['Close'].tail(120).mean() if not df.empty else 0; q_vol_ratio = df['Volume'].iloc[-1] / max(1, df['Volume'].tail(20).mean()) if not df.empty else 0

                st.markdown("<div style='margin-bottom: 20px;'>", unsafe_allow_html=True); qc1, qc2, qc3, qc4 = st.columns(4)
                def q_card(col, icon, title, val, suffix=""): col.markdown(f"<div style='background-color:#111; border-radius:10px; padding:15px; border:1px solid #00FFCC; margin-bottom:15px; box-shadow: 0 0 10px rgba(0,255,204,0.2);'><div style='color:#00FFCC; font-size:1.1rem; font-weight:bold; margin-bottom:8px;'>{icon} {title}</div><div style='color:white; font-size:2.2rem; font-weight:900;'>{val}{suffix}</div></div>", unsafe_allow_html=True)
                q_card(qc1, "🏢", "資產質量", f"{q_asset}/100"); q_card(qc2, "📈", "趨勢強度", f"{q_trend}/100"); q_card(qc3, "⚡", "動能 (Power)", f"{q_power}/100"); q_card(qc4, "🐋", "大資金", f"{q_money}/100")
                qc5, qc6, qc7, qc8 = st.columns(4); q_card(qc5, "🎭", "市場情緒", f"{q_sent}/100"); q_card(qc6, "🏆", "綜合總分", f"{q_total}/100"); q_card(qc7, "🏛️", "歷史中軸價", f"${q_pivot:.2f}"); q_card(qc8, "💰", "成交比率", f"{q_vol_ratio:.1f}x")
                st.markdown("</div>", unsafe_allow_html=True)
                
                c1, c2, c3 = st.columns([1, 1.2, 1.6])
                with c1: st.markdown(f"""<div class='cosmos-box' style='height: 460px; display:flex; flex-direction:column; justify-content:center;'><div class='cosmos-label'>COSMOS-X (天體動能)</div><div class='cosmos-value'>{cx_val:.1f}</div></div>""", unsafe_allow_html=True)
                with c2:
                    stat_rs, col_rs = get_trend_stats("RS")
                    st.markdown(f"""<div class='cosmos-box' style='border-color:#FFD700; height: 330px; display:flex; flex-direction:column; justify-content:center;'><div class='cosmos-label' style='font-size:1.6rem;'>COSMOS-RS (星系強弱)</div><div class='cosmos-value' style='font-size:4rem;'>{crs_val:.1f}</div><div style='color:{col_rs}; font-size:1.5rem; font-weight:bold; margin-top:15px;'>20日推力: {stat_rs}</div></div>""", unsafe_allow_html=True)
                    pulse_df = df.tail(21).copy(); rs_line = pulse_df['Close'] / spy_aligned.tail(21); rs_pulse_vals = rs_line.pct_change().tail(20).fillna(0).values * 600
                    st.plotly_chart(get_pulse_fig(rs_pulse_vals), use_container_width=True, theme=None, config={'displayModeBar': False}, key=f"rs_pulse_{ticker}")
                with c3:
                    def draw_triad_bar(val, color):
                        lit = int((min(120, val)/120)*21); html = f"<div class='bar-group-container' style='margin:0;'>"
                        for g in range(7):
                            html += "<div class='bar-triad'>"
                            for i in range(3):
                                idx = g*3+i; c_code = "#FF4B4B" if idx<6 else ("#FFD700" if idx<12 else color)
                                html += f"<div class='ej-seg' style='height:14px; width:12px; background-color:{c_code if idx < lit else '#222'}; opacity:{1 if idx < lit else 0.1};'></div>"
                            html += "</div>"
                        return html + "</div>"
                    avg_vol = df['Volume'].tail(252).mean() or 1
                    stat_ej, col_ej = get_trend_stats("EJ")
                    st.markdown(f"""<div class='cosmos-box' style='border-color:#00FFFF; padding: 15px; height: 100px; display:flex; flex-direction:column; justify-content:center;'><div style='display:flex; justify-content:space-between; align-items:flex-end; margin-bottom:5px;'><span style='color:#00FFFF; font-size:1.4rem; font-weight:bold;'>EJ 錢流底氣: {cej_s:.1f}%</span><span style='color:{col_ej}; font-size:1.2rem; font-weight:bold;'>20日吸金: {stat_ej}</span></div>{draw_triad_bar(cej_s, "#00FFFF")}</div>""", unsafe_allow_html=True)
                    vol_ratio = (pulse_df['Volume'].tail(20) / avg_vol).values; direction = np.where(pulse_df['Close'].tail(20) >= pulse_df['Open'].tail(20), 1, -1); ej_pulse_vals = vol_ratio * direction * 50 
                    st.plotly_chart(get_pulse_fig(ej_pulse_vals), use_container_width=True, theme=None, config={'displayModeBar': False}, key=f"ej_pulse_{ticker}")
                    stat_se, col_se = get_trend_stats("SE")
                    st.markdown(f"""<div class='cosmos-box' style='border-color:#FF00FF; padding: 15px; height: 100px; display:flex; flex-direction:column; justify-content:center; margin-top:0px;'><div style='display:flex; justify-content:space-between; align-items:flex-end; margin-bottom:5px;'><span style='color:#FF00FF; font-size:1.4rem; font-weight:bold;'>短期能量 BAR: {se_s:.1f}%</span><span style='color:{col_se}; font-size:1.2rem; font-weight:bold;'>20日動能: {stat_se}</span></div>{draw_triad_bar(se_s, "#FF00FF")}</div>""", unsafe_allow_html=True)
                    se_pulse_vals = pulse_df['Close'].pct_change().tail(20).fillna(0).values * 200
                    st.plotly_chart(get_pulse_fig(se_pulse_vals), use_container_width=True, theme=None, config={'displayModeBar': False}, key=f"se_pulse_{ticker}")

            try:
                mf_df = df.copy(); mf_df['Typical_Price'] = (mf_df['High'] + mf_df['Low'] + mf_df['Close']) / 3
                mf_df['Net_Flow'] = mf_df['Typical_Price'] * mf_df['Volume'] * np.where(mf_df['Close'] > mf_df['Close'].shift(1).fillna(mf_df['Close']), 1, -1)
                mf_df['OBV_Daily'] = (np.sign(mf_df['Close'].diff()) * mf_df['Volume']).fillna(0); mf_df['OBV'] = mf_df['OBV_Daily'].cumsum()
                curr_20d_flow = mf_df['Net_Flow'].tail(20).sum(); prev_20d_flow = mf_df['Net_Flow'].iloc[-40:-20].sum() if len(mf_df) > 20 else 0
                if abs(curr_20d_flow) >= 1e8: flow_str = f"{'+' if curr_20d_flow>0 else ''}${curr_20d_flow/1e8:.1f} 億"
                elif abs(curr_20d_flow) >= 1e6: flow_str = f"{'+' if curr_20d_flow>0 else ''}${curr_20d_flow/1e6:.1f} M (百萬)"
                else: flow_str = f"{'+' if curr_20d_flow>0 else ''}${curr_20d_flow:,.0f}"
                flow_color = "#00FF00" if curr_20d_flow > 0 else "#FF4B4B"
                mf_pct = cap_pct((curr_20d_flow - prev_20d_flow) / abs(prev_20d_flow + 1) * 100)
                compare_idx = max(1, min(20, len(mf_df)-1))
                obv_curr_val = mf_df['OBV'].iloc[-1] - mf_df['OBV'].iloc[-compare_idx]
                obv_prev_val = mf_df['OBV'].iloc[-compare_idx] - mf_df['OBV'].iloc[0] if len(mf_df) > compare_idx else 1
                obv_pct = cap_pct((obv_curr_val - obv_prev_val) / abs(obv_prev_val + 1) * 100)
                price_trend = mf_df['Close'].iloc[-1] - mf_df['Close'].iloc[-compare_idx]
                obv_total_vol = mf_df['Volume'].tail(20).sum() or 1
                if abs(obv_curr_val) / obv_total_vol < 0.02: trend_str, trend_color, obv_state = "9. 🧊 資金膠著盤整 (觀望)", "#888888", 9
                else:
                    if price_trend >= 0:
                        if obv_curr_val > 0: 
                            if obv_pct > 20: trend_str, trend_color, obv_state = "1. 👑 強烈流入", "#00FF00", 1
                            else: trend_str, trend_color, obv_state = "2. 📈 流入", "#00FF00", 2
                        else:
                            if obv_pct < -20: trend_str, trend_color, obv_state = "5. 💣 資金高位撤離 (量價強烈背離 - 大兇兆)", "#FF4B4B", 5
                            else: trend_str, trend_color, obv_state = "6. ⚠️ 資金高位撤離 (量價背離 - 兇兆)", "#FF4B4B", 6
                    else:
                        if obv_curr_val < 0:
                            if obv_pct < -20: trend_str, trend_color, obv_state = "3. 💀 大戶持續派發 (強烈流出)", "#FF4B4B", 3
                            else: trend_str, trend_color, obv_state = "4. 📉 大戶持續派發 (流出)", "#FF4B4B", 4
                        else:
                            if obv_pct > 20: trend_str, trend_color, obv_state = "7. 🐉 底部分歧掃貨 (量價強烈背離 - 大吉兆)", "#00FFCC", 7
                            else: trend_str, trend_color, obv_state = "8. 🐲 底部分歧掃貨 (量價背離 - 吉兆)", "#00FFCC", 8
                daily_abs_flow = abs(mf_df['Net_Flow'].tail(20)); total_abs_flow = daily_abs_flow.sum() or 1; conc_pct = (daily_abs_flow.max() / total_abs_flow) * 100
                if conc_pct > 35: conc_level, conc_color, conc_note = "⚡ 高度集中", "#FF4B4B", "（突發買入或掟貨）"
                elif conc_pct > 15: conc_level, conc_color, conc_note = "🌿 正常分佈", "#FFD700", "（公開正常進出）"
                else: conc_level, conc_color, conc_note = "💎 穩定分散", "#00FFCC", "（隱密吸籌/派發）"
                st.write(""); st.markdown("<h3 style='color:#FFF; margin-bottom:10px;'>🌊 獨家解密：20日主力資金池淨額 (Money Flow & OBV)</h3>", unsafe_allow_html=True)
                st.markdown("<div style='background-color:#000; border-radius:15px; padding:20px; border: 2px solid #333;'>", unsafe_allow_html=True)
                mc1, mc2 = st.columns(2)
                with mc1:
                    st.markdown(f"<div class='cosmos-box' style='border-color:{flow_color}; padding:15px; height:120px; display:flex; flex-direction:column; justify-content:center;'><div style='display:flex; justify-content:space-between;'><span style='color:{flow_color}; font-size:1.4rem; font-weight:bold;'>資金總數: {flow_str}</span><span style='color:{'#00FF00' if mf_pct>=0 else '#FF4B4B'}; font-size:1.2rem; font-weight:bold;'>20日變化: {mf_pct:.1f}%</span></div></div>", unsafe_allow_html=True)
                    st.plotly_chart(get_pulse_fig(mf_df['Net_Flow'].tail(20).values), use_container_width=True, theme=None, config={'displayModeBar': False}, key=f"flow_chart_{ticker}")
                with mc2:
                    st.markdown(f"<div class='cosmos-box' style='border-color:{trend_color}; padding:15px; height:120px; display:flex; flex-direction:column; justify-content:center;'><div style='display:flex; justify-content:space-between;'><span style='color:{trend_color}; font-size:1.4rem; font-weight:bold;'>OBV軌跡: {trend_str}</span><span style='color:{'#00FF00' if obv_pct>=0 else '#FF4B4B'}; font-size:1.2rem; font-weight:bold;'>20日變化: {obv_pct:.1f}%</span></div></div>", unsafe_allow_html=True)
                    st.plotly_chart(get_pulse_fig(mf_df['OBV_Daily'].tail(20).values), use_container_width=True, theme=None, config={'displayModeBar': False}, key=f"obv_chart_{ticker}")
                st.markdown(f"<div style='margin-top:20px; border-top:1px dashed #444; padding-top:15px;'><div style='display:flex; justify-content:space-between;'><span style='font-weight:bold;'>🎯 資金部署集中度：<span style='color:{conc_color};'>{conc_level}</span></span><span>極值佔比: {conc_pct:.1f}% <span style='color:{conc_color}; font-weight:bold;'>{conc_note}</span></span></div><div style='width:100%; background-color:#222; border-radius:10px; height:12px; margin-top:8px; border:1px solid #444;'><div style='width:{conc_pct}%; background-color:{conc_color}; height:100%; box-shadow:0 0 10px {conc_color};'></div></div></div>", unsafe_allow_html=True)
                st.markdown("</div>", unsafe_allow_html=True)
            except: pass

            st.write("### 📊 摩訶釋達・能量與籌碼透視圖 (個股均線 vs 大盤市寬疊加)")
            try:
                df['20MA'] = df['Close'].rolling(20, min_periods=1).mean().bfill()
                df['50MA'] = df['Close'].rolling(50, min_periods=1).mean().bfill()
                df['150MA'] = df['Close'].rolling(150, min_periods=1).mean().bfill()
                df['200MA'] = df['Close'].rolling(200, min_periods=1).mean().bfill()
                
                recent = df.tail(120).dropna(subset=['Close', 'Volume']).copy()
                if not recent.empty:
                    dates = recent.index.strftime('%Y-%m-%d')
                    fig = make_subplots(rows=5, cols=1, shared_xaxes=True, row_heights=[0.45, 0.1, 0.2, 0.15, 0.1], vertical_spacing=0.02)
                    
                    o_col = recent['Open'].values; c_col = recent['Close'].values
                    h_col = recent['High'].values; l_col = recent['Low'].values
                    v_col = recent['Volume'].values

                    fig.add_trace(go.Candlestick(x=dates, open=o_col, high=h_col, low=l_col, close=c_col, name='個股股價'), row=1, col=1)
                    if show_s_ma20: fig.add_trace(go.Scatter(x=dates, y=recent['20MA'], mode='lines', name='個股20日線', line=dict(color='white', width=1.5)), row=1, col=1)
                    if show_s_ma50: fig.add_trace(go.Scatter(x=dates, y=recent['50MA'], mode='lines', name='個股50日線', line=dict(color='yellow', width=1.5)), row=1, col=1)
                    if show_s_ma150: fig.add_trace(go.Scatter(x=dates, y=recent['150MA'], mode='lines', name='個股150日線', line=dict(color='cyan', width=1.5)), row=1, col=1)
                    if show_s_ma200: fig.add_trace(go.Scatter(x=dates, y=recent['200MA'], mode='lines', name='個股200日線', line=dict(color='magenta', width=1.5)), row=1, col=1)

                    if not b_df_plot.empty:
                        align_b = b_df_plot.reindex(recent.index).ffill().bfill()
                        if len(align_b)>0 and align_b['Close'].iloc[0]!=0 and c_col[0]!=0:
                            norm = c_col[0] / align_b['Close'].iloc[0]
                            if show_b_idx: fig.add_trace(go.Scatter(x=dates, y=align_b['Close']*norm, mode='lines', name=f'{b_sym_plot} 基準', line=dict(color='#FF4B4B', width=2)), row=1, col=1)
                            if show_b_ma20: fig.add_trace(go.Scatter(x=dates, y=align_b['20MA']*norm, mode='lines', name='20市寬線', line=dict(color='rgba(255,255,255,0.6)', width=1.5, dash='dot')), row=1, col=1)
                            if show_b_ma50: fig.add_trace(go.Scatter(x=dates, y=align_b['50MA']*norm, mode='lines', name='50市寬線', line=dict(color='rgba(255,215,0,0.6)', width=1.5, dash='dot')), row=1, col=1)

                    colors = ['#00FF00' if c_col[i] >= o_col[i] else '#FF0000' for i in range(len(recent))]
                    fig.add_trace(go.Bar(x=dates, y=v_col, marker_color=colors, name='成交量'), row=2, col=1)
                    
                    recent['Vol50'] = recent['Volume'].rolling(50, min_periods=1).mean()
                    for i in range(len(recent)):
                        if recent['Close'].iloc[i] > recent['Open'].iloc[i] and recent['Volume'].iloc[i] > recent['Vol50'].iloc[i]*1.5:
                            fig.add_annotation(x=dates[i], y=recent['Volume'].iloc[i], text="🌟", showarrow=False, yanchor="bottom", xanchor="center", font=dict(size=14, color="#FFD700"), row=2, col=1)
                    
                    counts, bins = np.histogram(c_col, bins=20, weights=v_col)
                    max_c = max(counts) if len(counts) > 0 and max(counts) > 0 else 1
                    fig.add_trace(go.Bar(y=(bins[:-1] + bins[1:]) / 2, x=counts, orientation='h', marker_color='rgba(0, 255, 204, 0.4)', name='蟹貨區', xaxis='x6', yaxis='y1'))
                    
                    add_energy_subplots(fig, recent, row_start=3)
                    
                    fig.update_layout(
                        template="plotly_dark", paper_bgcolor='#0e1117', plot_bgcolor='#0e1117', height=950, barmode='overlay',
                        showlegend=True, legend=dict(font=dict(color="white"), orientation="h", yanchor="bottom", y=1.02, xanchor="right", x=1), 
                        xaxis_rangeslider_visible=False, xaxis=dict(type='category', showgrid=False), 
                        yaxis=dict(showgrid=True, gridcolor='#333'), xaxis6=dict(overlaying='x1', side='top', range=[0, max_c*1.1], showgrid=False, showticklabels=False)
                    )
                    st.plotly_chart(fig, use_container_width=True, theme=None, config={'scrollZoom': True, 'displayModeBar': True}, key=f"main_chart_{ticker}") 
            except Exception as e: pass

            st.write("---"); d_c1, d_c2 = st.columns([1, 2.5]); is_etf = info.get('quoteType') == 'ETF'; real_roe = info.get('returnOnEquity')
            if is_etf or real_roe is None or real_roe == 0:
                dna_v = round(safe_n((cx_val * 0.5) + (crs_val * 0.5), 50.0), 1); dna_title = "ETF 綜合質量基因"
                m9 = {"🚀 增長加速度 (15%)": int(safe_n(cx_val / 10, 5)), "🔭 營收天花板 (15%)": int(safe_n(crs_val / 10, 5)), "🛡️ 定價權護城河 (15%)": int(safe_n(cej_s / 10, 5)), "🦖 市場佔有率 (15%)": 9 if info.get('totalAssets', 0) > 1e9 else 5, "💰 資本效率 (10%)": int(safe_n(se_s / 10, 5)), "💎 獲利含金量 (10%)": int(max(1, 10 - (v_ann * 20))), "🧱 財務安全墊 (10%)": int(safe_n(crs_val / 10, 5)), "🎁 股東回饋 (5%)": int(safe_n(info.get('yield', info.get('dividendYield', 0))*200+2, 5)), "📈 經營穩定性 (5%)": int(safe_n(cx_val / 12, 5))}
            else:
                f1_growth = min(100, max(0, safe_n(info.get('earningsGrowth', 0)) * 200 + 40)); f2_rev = min(100, max(0, safe_n(info.get('revenueGrowth', 0)) * 150 + 40))
                f3_moat = min(100, max(0, safe_n(info.get('profitMargins', 0)) * 300 + 30)); rev_val = safe_n(info.get('totalRevenue', 0)); f4_dom = min(100, max(40, (rev_val / 1e10) * 5 + 50))
                f5_roe = min(100, max(0, safe_n(info.get('returnOnEquity', 0)) * 300 + 30)); f6_cash = min(100, max(0, safe_n(info.get('operatingMargins', 0)) * 250 + 40))
                de_ratio = safe_n(info.get('debtToEquity', 100)); f7_safe = min(100, max(0, 100 - (de_ratio / 2))); f8_yield = min(100, safe_n(info.get('dividendYield', 0)) * 2000 + 20 if info.get('dividendYield') else 30)
                f9_stable = min(100, max(0, safe_n(info.get('forwardPE', 15)) * -1 + 100 if safe_n(info.get('forwardPE', 0)) > 0 else 50))
                dna_v = (f1_growth * 0.15) + (f2_rev * 0.15) + (f3_moat * 0.15) + (f4_dom * 0.15) + (f5_roe * 0.10) + (f6_cash * 0.10) + (f7_safe * 0.10) + (f8_yield * 0.05) + (f9_stable * 0.05)
                dna_v = round(max(0.0, min(100.0, dna_v)), 1); dna_title = "投行級股王基因"
                m9 = {"🚀 增長加速度 (15%)": int(max(1, min(10, f1_growth / 10))), "🔭 營收天花板 (15%)": int(max(1, min(10, f2_rev / 10))), "🛡️ 定價權護城河 (15%)": int(max(1, min(10, f3_moat / 10))), "🦖 市場佔有率 (15%)": int(max(1, min(10, f4_dom / 10))), "💰 資本效率 (10%)": int(max(1, min(10, f5_roe / 10))), "💎 獲利含金量 (10%)": int(max(1, min(10, f6_cash / 10))), "🧱 財務安全墊 (10%)": int(max(1, min(10, f7_safe / 10))), "🎁 股東回饋 (5%)": int(max(1, min(10, f8_yield / 10))), "📈 經營穩定性 (5%)": int(max(1, min(10, f9_stable / 10)))}
            dna_v = max(0.0, min(100.0, dna_v)); d_lv = "第 1 級" if dna_v>=90 else ("第 2 級" if dna_v>=80 else ("第 3 級" if dna_v>=70 else "後續"))
            with d_c1: st.markdown(f"<div class='cosmos-box' style='border-color:#FF4B4B; height:420px; display:flex; flex-direction:column; justify-content:center;'><div style='color:#FF4B4B; font-weight:900; font-size:1.8rem;'>🧬 COSMOS-DNA</div><div style='font-size:0.9rem; opacity:0.7; margin:5px 0;'>{dna_title}</div><div style='font-size:6rem; font-weight:900;'>{dna_v}</div><div style='color:#FFD700;'>[ 現屬 {d_lv} ]</div></div>", unsafe_allow_html=True)
            with d_c2:
                colors_9d = ["#00FFCC", "#00FFCC", "#00FFCC", "#00FFCC", "#FF4B4B", "#BC13FE", "#FFFFFF", "#FFD700", "#FF00FF"]
                for i, (l, s) in enumerate(m9.items()):
                    sc = max(1, min(10, s)); grid = '<div class="energy-bar-container-8d">' + "".join([f'<div class="energy-seg-8d" style="background-color:{colors_9d[i%9]}; opacity:{"1" if j<=sc else "0.1"};"></div>' for j in range(1,11)]) + '</div>'
                    st.markdown(f"<div style='display:flex; justify-content:space-between; font-weight:bold;'><span>{l}</span><span>{sc}/10</span></div>{grid}", unsafe_allow_html=True)
            st.write("---")
            f_eps = info.get('forwardEps'); t_eps = info.get('trailingEps', 0)
            if not f_eps or f_eps <= 0:
                f_pe = info.get('forwardPE')
                if f_pe and f_pe > 0: f_eps = curr_p / f_pe
                else: f_eps = max(t_eps, 0.1) * (1 + (dna_v/100))
            if t_eps > 0 and f_eps > (t_eps * 2.5): f_eps = t_eps * 2.5 
            g_score = m9.get("🚀 增長加速度 (15%)", 5) if not is_etf else 5; sector = info.get('sector', ''); industry = info.get('industry', '')
            is_semi_or_hardware = "Semiconductor" in industry or "Hardware" in industry or "Technology" in sector
            if is_semi_or_hardware: fair_pe = 18.0 if g_score >= 8 else (15.0 if g_score >= 5 else 10.0)
            else:
                if g_score >= 9: fair_pe = 35.0
                elif g_score >= 7: fair_pe = 25.0
                elif g_score >= 5: fair_pe = 18.0
                else: fair_pe = 12.0
            forward_price = f_eps * fair_pe; price_diff = ((forward_price - curr_p) / curr_p) * 100 if curr_p > 0 else 0
            base_score = (dna_v * 0.70) + (s10_mgmt * 0.15) + (s11_story * 0.15)
            if "第二曲線" in x_factor: base_score += 10
            elif "印鈔機" in x_factor: base_score += 5
            elif "吸血鬼" in x_factor: base_score -= 15
            dragon_index = round(max(5.0, min(98.5, base_score)), 1)
            if dragon_index >= 80: t_lv, t_desc, val_title, val_color = "第 1 級", "極致真龍", "🔥 烈火鳳凰", "#BC13FE"; act_desc = "【順勢重倉】強大動能與財報支撐，緊貼趨勢操作。"
            elif dragon_index >= 65: t_lv, t_desc, val_title, val_color = "第 2 級", "潛力金龍", "🌟 潛龍伏躍", "#00FFCC"; act_desc = "【分批建倉】財報穩健，動能醞釀中，適合持有觀望。"
            elif dragon_index >= 40: t_lv, t_desc, val_title, val_color = "第 3 級", "中庸凡骨", "⚠️ 海市蜃樓", "#FFA500"; act_desc = "【謹慎觀望】動能與財報平平，注意回調風險。"
            else: t_lv, t_desc, val_title, val_color = "第 4 級", "高危泥鰍", "☠️ 末路狂花", "#FF4B4B"; act_desc = "【規避風險】財報轉弱且動能破位，嚴格止損。"
            vc1, vc2, vc3 = st.columns(3)
            with vc1: st.markdown(f"""<div class='val-box-purple' style='height:280px;'><div class='val-label'>🎯 遠期目標價 (預測)</div><div style='font-size:3.5rem; font-weight:900; color:#00FFCC;'>${forward_price:,.2f}</div><div style='font-size:1.2rem; margin-top:10px;'>潛在空間: <span style='color:{"#00FFCC" if price_diff>0 else "#FF4B4B"}; font-weight:900;'>{"+" if price_diff>0 else ""}{price_diff:.1f}%</span></div><div style='font-size:1.2rem; font-weight:bold; margin-top:10px; opacity:0.9;'>TTM EPS: ${t_eps:.2f} | Fwd EPS: ${f_eps:.2f}</div></div>""", unsafe_allow_html=True)
            with vc2: st.markdown(f"""<div class='val-box-purple' style='border-color:{val_color}; box-shadow: 0 0 25px {val_color}44; height:280px;'><div class='val-label'>🏆 真龍指數 ({val_title})</div><div style='font-size:5rem; font-weight:900; color:{val_color};'>{dragon_index}</div><div style='font-size:1.1rem; color:{val_color};'>[ 現屬 {t_lv} ({t_desc}) ]</div></div>""", unsafe_allow_html=True)
            with vc3: st.markdown(f"""<div class='val-box-purple' style='border-color:#00FFFF; box-shadow: 0 0 25px #00FFFF44; height:280px;'><div class='val-label'>🎭 時代敘事與決策</div><div style='font-size:1.5rem; font-weight:bold; margin-top:10px;'>{x_factor}</div><p style='color:#00FFFF; margin-top:5px; font-size:1.2rem;'>敘事溢價信心: {s11_story}%</p><div style='background:#111; padding:10px; border-radius:5px; margin-top:15px; font-weight:bold;'>{act_desc}</div></div>""", unsafe_allow_html=True)
            st.write("---")
            v1,v2,v3 = st.columns(3); v4,v5,v6 = st.columns(3); v7,v8,v9 = st.columns(3)
            def v_card(col, t, t_v, f_v, d): col.markdown(f"<div class='val-box'><div class='val-label'>{t}</div><div class='val-text'>TTM: <span class='val-focus'>{t_v}</span></div><div class='val-text'>預期: <span class='val-focus'>{f_v}</span></div><div style='color:#FFA500; font-size:0.9rem;'>{d}</div></div>", unsafe_allow_html=True)
            v_card(v1, "PE 獲利比", safe_s(info, ['trailingPE'], "x"), safe_s(info, ['forwardPE'], "x"), "獲利估值")
            v_card(v2, "PEG 增長比", safe_s(info, ['pegRatio']), "N/A", "增長性價比")
            v_card(v3, "PS 營收比", safe_s(info, ['priceToSalesTrailing12Months'], "x"), "N/A", "營收規模")
            v_card(v4, "PB 淨資產", safe_s(info, ['priceToBook'], "x"), "N/A", "賬面價值")
            v_card(v5, "EV/EBITDA", safe_s(info, ['enterpriseToEbitda'], "x"), "N/A", "企業估值")
            v_card(v6, "股息率", safe_s(info, ['dividendYield', 'yield'], "%"), "N/A", "回報率")
            v7.markdown(f"<div class='val-box'><div class='val-label'>Beta 敏感度</div><div class='val-focus' style='margin-top:20px;'>{get_beta(info, df, spy)}</div><div style='color:#FFA500; font-size:0.9rem; margin-top:15px;'>對大盤聯動性</div></div>", unsafe_allow_html=True)
            v8.markdown(f"<div class='val-box'><div class='val-label'>@ (Alpha) 超額回報</div><div class='val-focus' style='margin-top:20px;'>{get_alpha(get_beta(info, df, spy), df, spy)}</div><div style='color:#FFA500; font-size:0.9rem; margin-top:15px;'>大盤外表現</div></div>", unsafe_allow_html=True)
            hv_v = get_volatility(df); iv_warning = ""
            if iv_val != 'N/A' and hv_v != 'N/A':
                try:
                    if float(iv_val[:-1]) > float(hv_v[:-1]): iv_warning = '[ IV > HV 期權溢價中 ]'
                except: pass
            v9.markdown(f"<div class='val-box'><div class='val-label'>🌪️ 波動率雙併 (Risk)</div><div class='val-text' style='margin-top:15px;'>年化 (HV): <span class='val-focus'>{hv_v}</span></div><div class='val-text'>隱含 (IV): <span class='val-focus'>{iv_val}</span></div><div style='color:#FFA500; font-size:0.8rem; margin-top:10px;'>{iv_warning}</div></div>", unsafe_allow_html=True)
            
            st.markdown("<div class='whale-box'><div style='color:#FFD700; font-size:2.2rem; font-weight:bold; text-align:center;'>🧙 90 大名家：真實申報持倉</div>", unsafe_allow_html=True)
            total_shares = info.get('sharesOutstanding', 1)
            if holders is not None and not holders.empty and 'Holder' in holders.columns:
                for _, row in holders.head(8).iterrows():
                    shares = row.get('Shares', 0); calc_pct = (shares/total_shares); val_m = row.get('Value', 0)/1e6
                    st.markdown(f"<div class='whale-row'><span class='whale-n'>{row['Holder']}</span><span class='whale-a'>持有 {shares:,.0f} 股 | 佔比 {calc_pct:.2%} | 市值 ${val_m:.1f}M</span></div>", unsafe_allow_html=True)
            else:
                st.markdown("<div style='text-align:center; color:white; font-size:1.2rem; padding: 20px;'>暫無大名家持倉數據。</div>", unsafe_allow_html=True)
            st.markdown("</div>", unsafe_allow_html=True)
        except Exception as e: st.error(f"系統分析受阻，原因: {e}")

# =========================================================================
# 🛡️ 模式 B：環球市底大師指揮塔 
# =========================================================================
elif app_mode == "🛡️ 環球市底大師指揮塔":
    st.markdown("<h1 class='main-title'>🛡️ 環球市底大師指揮塔</h1>", unsafe_allow_html=True)
    st.markdown("<span style='color:white; font-size:16px; font-weight:bold;'>請選擇大盤陣營：</span>", unsafe_allow_html=True)
    market_choice = st.radio("", ["🇭🇰 港股市寬系統", "🇺🇸 美股市寬系統"], horizontal=True, label_visibility="collapsed")
    st.markdown("<span style='color:white; font-size:16px; font-weight:bold;'>請選擇指數：</span>", unsafe_allow_html=True)
    if "港股" in market_choice: idx_choice = st.radio("", ["恒指", "科指"], horizontal=True, label_visibility="collapsed")
    else: idx_choice = st.radio("", ["道指", "標指", "納市", "IWM"], horizontal=True, label_visibility="collapsed")
    st.write("---")
    
    HSI_71 = (HK_STOCK_MAP["1. 互聯網巨頭"] + HK_STOCK_MAP["5. 國有大行與金融"] + HK_STOCK_MAP["10. 房地產開發"] + HK_STOCK_MAP["13. 核心消費與餐飲"])[:71]
    TECH_30 = (HK_STOCK_MAP["1. 互聯網巨頭"] + HK_STOCK_MAP["2. 半導體與芯片"] + HK_STOCK_MAP["12. 消費電子硬件"])[:30]
    DOW_30 = "AAPL MSFT UNH JNJ XOM JPM V PG HD CVX MRK KO ABBV BAC AVGO PEP TMO COST CSCO MCD CRM DIS LIN ABT ACN AMD WFC NFLX INTC CAT".split()
    SPX_80 = (DOW_30 + US_STOCK_MAP["2. AI與大數據雲端"] + US_STOCK_MAP["11. 核心消費品"] + US_STOCK_MAP["22. 商業銀行巨頭"])[:80]
    NDX_43 = (US_STOCK_MAP["2. AI與大數據雲端"] + US_STOCK_MAP["1. 半導體設備與設計"] + US_STOCK_MAP["6. 通訊與網絡設備"])[:43]
    IWM_32 = (US_STOCK_MAP["49. 小型爆發精選"] + US_STOCK_MAP["50. 超微型探索 (Micro)"])[:32]

    if "恒指" in idx_choice: ticker_sym = "2800.HK"; b_tickers = HSI_71 
    elif "科指" in idx_choice: ticker_sym = "3032.HK"; b_tickers = TECH_30
    elif "道指" in idx_choice: ticker_sym = "DIA"; b_tickers = DOW_30
    elif "標指" in idx_choice: ticker_sym = "SPY"; b_tickers = SPX_80
    elif "納市" in idx_choice: ticker_sym = "QQQ"; b_tickers = NDX_43
    else: ticker_sym = "IWM"; b_tickers = IWM_32

    with st.spinner(f"⏳ 大宗師正在計算市寬數據... 請稍候 ☕🚀"):
        try:
            idx_df = smart_fetch(ticker_sym, period="2y")
            if not idx_df.empty:
                idx_df['20MA'] = idx_df['Close'].rolling(20, min_periods=1).mean()
                idx_df['50MA'] = idx_df['Close'].rolling(50, min_periods=1).mean()
                idx_df['150MA'] = idx_df['Close'].rolling(150, min_periods=1).mean()
                idx_df['200MA'] = idx_df['Close'].rolling(200, min_periods=1).mean()
                
                clean_recent = idx_df.tail(250).copy(); dates = clean_recent.index.strftime('%Y-%m-%d')
                if len(clean_recent) > 150:
                    curr_50 = clean_recent['50MA'].iloc[-1]; curr_150 = clean_recent['150MA'].iloc[-1]; past_150 = clean_recent['150MA'].iloc[-10] 
                    if curr_50 < curr_150 and curr_150 < past_150: st.markdown("<div class='bear-warning'>🚨 警告：已進入熊市 (10周線跌穿30周線，且30周線向下) 🚨</div>", unsafe_allow_html=True)
                
                b_stats = get_breadth_data(b_tickers); v_count = b_stats['valid']
                st.markdown(f"### 🌊 {idx_choice} - 內部成份股市寬健康度")
                st.markdown(f"<div style='color: white; font-size:1.1rem; margin-bottom:15px;'>（系統真實成功掃描：<b style='color:#00FFCC;'>{v_count}</b> 隻核心成份股）</div>", unsafe_allow_html=True)
                st.markdown(f"<div style='display: flex; justify-content: space-between; text-align: center; background-color: #111; padding: 20px; border-radius: 15px;'><div><span style='color: #00FFCC; font-size: 1.2rem; font-weight: bold;'>20市寬線之上</span><br><span style='color: white; font-size: 3rem; font-weight: 900;'>{(b_stats['20MA']/v_count)*100:.1f}%</span></div><div><span style='color: #00FFCC; font-size: 1.2rem; font-weight: bold;'>50市寬線之上</span><br><span style='color: white; font-size: 3rem; font-weight: 900;'>{(b_stats['50MA']/v_count)*100:.1f}%</span></div><div><span style='color: #00FFCC; font-size: 1.2rem; font-weight: bold;'>150市寬線之上</span><br><span style='color: white; font-size: 3rem; font-weight: 900;'>{(b_stats['150MA']/v_count)*100:.1f}%</span></div><div><span style='color: #00FFCC; font-size: 1.2rem; font-weight: bold;'>200市寬線之上</span><br><span style='color: white; font-size: 3rem; font-weight: 900;'>{(b_stats['200MA']/v_count)*100:.1f}%</span></div></div>", unsafe_allow_html=True)

                st.markdown("<h4 style='color:#FFF; margin-top:20px; margin-bottom:5px;'>📊 最近 20 日市寬變化趨勢</h4>", unsafe_allow_html=True)
                fig_trend = go.Figure()
                x_dates = clean_recent.index[-20:].strftime('%m-%d').tolist()
                if len(x_dates) < 20: x_dates = [f"D{i}" for i in range(-19, 1)]
                y_20 = [(v/v_count)*100 for v in b_stats['hist_20MA']]; y_50 = [(v/v_count)*100 for v in b_stats['hist_50MA']]
                y_150 = [(v/v_count)*100 for v in b_stats['hist_150MA']]; y_200 = [(v/v_count)*100 for v in b_stats['hist_200MA']]

                fig_trend.add_trace(go.Scatter(x=x_dates, y=y_20, mode='lines+markers', name='20市寬線', line=dict(color='white', width=2)))
                fig_trend.add_trace(go.Scatter(x=x_dates, y=y_50, mode='lines+markers', name='50市寬線', line=dict(color='yellow', width=2)))
                fig_trend.add_trace(go.Scatter(x=x_dates, y=y_150, mode='lines+markers', name='150市寬線', line=dict(color='cyan', width=2)))
                fig_trend.add_trace(go.Scatter(x=x_dates, y=y_200, mode='lines+markers', name='200市寬線', line=dict(color='magenta', width=2)))
                fig_trend.add_annotation(x=x_dates[-1], y=y_20[-1], text="20市寬", showarrow=False, xanchor="left", xshift=10, font=dict(color="white", size=12))
                fig_trend.add_annotation(x=x_dates[-1], y=y_50[-1], text="50市寬", showarrow=False, xanchor="left", xshift=10, font=dict(color="yellow", size=12))
                fig_trend.add_annotation(x=x_dates[-1], y=y_150[-1], text="150市寬", showarrow=False, xanchor="left", xshift=10, font=dict(color="cyan", size=12))
                fig_trend.add_annotation(x=x_dates[-1], y=y_200[-1], text="200市寬", showarrow=False, xanchor="left", xshift=10, font=dict(color="magenta", size=12))
                fig_trend.update_layout(template="plotly_dark", paper_bgcolor='#0e1117', plot_bgcolor='#111', height=300, margin=dict(l=20, r=60, t=10, b=20), xaxis=dict(title="", showgrid=True, gridcolor='#333', type='category'), yaxis=dict(title="市寬 %", range=[0, 105], showgrid=True, gridcolor='#333'), legend=dict(orientation="h", yanchor="bottom", y=1.02, xanchor="right", x=1))
                st.plotly_chart(fig_trend, use_container_width=True, config={'displayModeBar': False})

                st.write("")
                fig = make_subplots(rows=2, cols=1, shared_xaxes=True, row_heights=[0.7, 0.3], vertical_spacing=0.05)
                o_col = clean_recent['Open'].values; c_col = clean_recent['Close'].values; h_col = clean_recent['High'].values; l_col = clean_recent['Low'].values; v_col = clean_recent['Volume'].values
                if show_b_idx: fig.add_trace(go.Candlestick(x=dates, open=o_col, high=h_col, low=l_col, close=c_col, name=f'{ticker_sym} 基準指數'), row=1, col=1)
                else: fig.add_trace(go.Scatter(x=dates, y=c_col, mode='lines', name='隱藏基準', line=dict(color='rgba(255,255,255,0)')), row=1, col=1)
                if show_b_ma20: fig.add_trace(go.Scatter(x=dates, y=clean_recent['20MA'], mode='lines', name='20市寬線', line=dict(color='white', width=1.5, dash='dot')), row=1, col=1)
                if show_b_ma50: fig.add_trace(go.Scatter(x=dates, y=clean_recent['50MA'], mode='lines', name='50市寬線', line=dict(color='yellow', width=1.5, dash='dot')), row=1, col=1)
                if show_b_ma150: 
                    fig.add_trace(go.Scatter(x=dates, y=clean_recent['150MA'], mode='lines', name='150市寬線', line=dict(color='cyan', width=2, dash='dot')), row=1, col=1)
                    if len(clean_recent) > 10 and clean_recent['150MA'].iloc[-1] < clean_recent['150MA'].iloc[-10]: fig.add_annotation(x=dates[-1], y=clean_recent['150MA'].iloc[-1], ax=0, ay=-40, xref="x", yref="y", showarrow=True, arrowhead=3, arrowsize=2, arrowwidth=3, arrowcolor="red", text="⬇")
                if show_b_ma200: 
                    fig.add_trace(go.Scatter(x=dates, y=clean_recent['200MA'], mode='lines', name='200市寬線', line=dict(color='magenta', width=2, dash='dot')), row=1, col=1)
                    if len(clean_recent) > 10 and clean_recent['200MA'].iloc[-1] < clean_recent['200MA'].iloc[-10]: fig.add_annotation(x=dates[-1], y=clean_recent['200MA'].iloc[-1], ax=0, ay=-40, xref="x", yref="y", showarrow=True, arrowhead=3, arrowsize=2, arrowwidth=3, arrowcolor="red", text="⬇")

                colors = ['#00FF00' if c_col[i] >= o_col[i] else '#FF0000' for i in range(len(clean_recent))]
                fig.add_trace(go.Bar(x=dates, y=v_col, marker_color=colors, name='成交量'), row=2, col=1)
                counts, bins = np.histogram(c_col, bins=20, weights=v_col); max_c = max(counts) if len(counts) > 0 and max(counts) > 0 else 1
                fig.add_trace(go.Bar(y=(bins[:-1] + bins[1:]) / 2, x=counts, orientation='h', marker_color='rgba(0, 255, 204, 0.4)', name='蟹貨區', xaxis='x3', yaxis='y1'))
                fig.update_layout(template="plotly_dark", paper_bgcolor='#0e1117', plot_bgcolor='#0e1117', height=750, showlegend=True, legend=dict(font=dict(color="white"), orientation="h", yanchor="bottom", y=1.02, xanchor="right", x=1), xaxis_rangeslider_visible=False, xaxis=dict(type='category', showgrid=False), yaxis=dict(showgrid=True, gridcolor='#333'), xaxis3=dict(overlaying='x', side='top', range=[0, max_c*1.1], showgrid=False, showticklabels=False))
                st.plotly_chart(fig, use_container_width=True, config={'displayModeBar': False}, key=f"b_chart_{ticker_sym}")

                if ("科指" in idx_choice or "道指" in idx_choice) and b_stats['above_50_list']:
                    st.markdown(f"<h3 style='color: white;'>🏆 逆市名單 ({idx_choice.split(' ')[0]}) - 企穩 50天線之上</h3>", unsafe_allow_html=True)
                    cols = st.columns(6)
                    for i, t in enumerate(b_stats['above_50_list'][:30]): cols[i % 6].info(t)
        except Exception as e: st.error(f"⚠️ 數據載入失敗：{e}")

# =========================================================================
# 📡 拔河熱力圖 
# =========================================================================
elif "熱力圖" in app_mode:
    st.markdown(f"<h1 class='main-title'>{app_mode}</h1>", unsafe_allow_html=True)
    is_etf = "ETF" in app_mode
    m_view = st.sidebar.radio("🌌 選擇星系", ["🇺🇸 美股陣列", "🇭🇰 港股陣列"])
    lookback = st.sidebar.selectbox("⏰ 戰術時間窗", [5, 20], index=1)
    is_us = "美股" in m_view
    bench_sym = "SPY" if is_us else "^HSI"
    target_map = (US_ETF_MAP if is_etf else US_STOCK_MAP) if is_us else (HK_ETF_MAP if is_etf else HK_STOCK_MAP)
    
    if is_etf:
        all_items = list(set([t for sub in target_map.values() for t in sub]))
        label_text = f"正在掃描 {'260' if is_us else '113'} 隻精選 ETF..."; chart_title = f"{'美股' if is_us else '港股'} ETF 究極龍虎榜 ({lookback}日)"; chart_height = 3000 if is_us else 1500
    else:
        all_items = list(target_map.keys()) 
        label_text = "正在計算板塊力水..."; chart_title = f"{'美股 50 大' if is_us else '港股 22 大'} 板塊拔河圖 ({lookback}日)"; chart_height = 1200 if is_us else 700

    if st.button(f"📡 啟動全星系 {lookback}日 拔河掃描！"):
        with st.spinner(label_text):
            try:
                bench_df = smart_fetch(bench_sym, period="60d")['Close'].dropna()
                results = []
                pb = st.progress(0)
                for idx, item in enumerate(all_items):
                    pb.progress((idx+1)/len(all_items))
                    target_ticker = item if is_etf else target_map[item][0]
                    try:
                        d = smart_fetch(target_ticker, period="60d")['Close'].dropna()
                        if len(d) >= lookback and len(bench_df) >= lookback:
                            rs = 50 + ((d.iloc[-1]/d.iloc[-lookback]) - (bench_df.iloc[-1]/bench_df.iloc[-lookback])) * 100
                            results.append({"項目": item, "RS強弱": round(rs, 1)})
                    except: continue
                if results:
                    df_rs = pd.DataFrame(results).sort_values("RS強弱", ascending=True)
                    fig = go.Figure(go.Bar(x=df_rs["RS強弱"], y=df_rs["項目"], orientation='h', marker=dict(color=df_rs["RS強弱"], colorscale='Portland')))
                    fig.update_layout(template="plotly_dark", height=chart_height, title=chart_title, xaxis=dict(title=f"RS 強度 (50為基準) - {lookback}日"), margin=dict(l=20, r=20, t=50, b=20), paper_bgcolor='#0e1117', plot_bgcolor='#0e1117', font=dict(color='white'))
                    st.plotly_chart(fig, use_container_width=True, theme=None, config={'displayModeBar': False})
                else: st.warning("💤 無法獲取足夠數據繪製圖表。")
            except Exception as e: st.error(f"拔河失敗: {e}")

# =========================================================================
# 🔍 模式 C/F/G：起步尋龍雷達 (🌟 Fix 3: 升級戰術圖表與三層能量指標)
# =========================================================================
elif "雷達" in app_mode and "Mode E" not in app_mode:
    st.markdown(f"<h1 class='main-title'>{app_mode}</h1>", unsafe_allow_html=True)
    c_mkt, c_sec, c_strat = st.columns([1, 1, 1.5])
    if app_mode == "🔍 千龍起步尋龍雷達 (個股)":
        with c_mkt: m_choice = st.radio("1. 選擇市場", ["🇺🇸 美股", "🇭🇰 港股"])
        is_us = "美股" in m_choice; is_etf = False
    else:
        is_us = "美股" in app_mode; is_etf = True
        with c_mkt: st.info(f"鎖定 {app_mode.split(' ')[1]}")
        
    bench_sym = "SPY" if is_us else "^HSI"
    target_dict = (US_ETF_MAP if is_etf else US_STOCK_MAP) if is_us else (HK_ETF_MAP if is_etf else HK_STOCK_MAP)
    
    with c_sec: s_choice = st.selectbox("2. 選擇掃描範圍", ["🌐 啟動全星系大規模搜索"] + list(target_dict.keys()))
    with c_strat: t_strat = st.radio("3. 戰術過濾 (機變)", ["🔥 極致新高 (ATH)", "🐉 潛龍伏躍 (10-20% 空間)"])
    
    if 'c_scanned_stocks' not in st.session_state:
        st.session_state.c_scanned_stocks = []

    if st.button("📡 發射撒網尋龍電波！"):
        bench_data = smart_fetch(bench_sym, period="2y")
        tickers_to_scan = list(set([t for sub in target_dict.values() for t in sub])) if "全星系" in s_choice else target_dict[s_choice]
        found_stocks = []
        pb = st.progress(0)
        with st.spinner("⏳ 慢速防封鎖引擎過濾中，請稍候..."):
            for idx, t in enumerate(tickers_to_scan):
                pb.progress((idx + 1) / len(tickers_to_scan))
                if idx > 0 and idx % 10 == 0: time.sleep(1.0)
                try:
                    d_full = smart_fetch(t, period="1y")
                    # 🌟 Fix 1: 0100.hk 醫治 (確保20日即可掃描)
                    if len(d_full) >= 20:
                        d = d_full.tail(63)
                        curr_p = d['Close'].iloc[-1]; ath = d_full['High'].tail(252).max()
                        if t_strat == "🔥 極致新高 (ATH)":
                            if (curr_p / ath) < 0.93: continue
                        else: 
                            if not (0.75 <= (curr_p / ath) <= 0.90): continue

                        tp = (d['High']+d['Low']+d['Close'])/3; nf = tp*d['Volume']*np.where(d['Close']>d['Close'].shift(1).fillna(d['Close']),1,-1)
                        net_flow_20 = nf.tail(20).sum(); conc_20 = (abs(nf.tail(20)).max()/max(abs(nf.tail(20)).sum(), 1))*100
                        obv = (np.sign(d['Close'].diff())*d['Volume']).fillna(0).cumsum()
                        obv_curr = obv.iloc[-1]-obv.iloc[-21] if len(obv)>20 else obv.iloc[-1]-obv.iloc[0]
                        obv_prev = obv.iloc[-21]-obv.iloc[-41] if len(obv)>40 else 1
                        obv_pct = cap_pct((obv_curr-obv_prev)/max(abs(obv_prev), 1)*100)
                        p_trend = d['Close'].iloc[-1]-d['Close'].iloc[-21] if len(d)>20 else d['Close'].iloc[-1]-d['Close'].iloc[0]
                        state = 9
                        if p_trend>=0: state = 1 if obv_pct>20 else 2
                        else: state = 7 if obv_pct>20 else 8
                        
                        crs = safe_n(50+((curr_p/d['Close'].iloc[-max(1, min(63, len(d)-1))])-(bench_data['Close'].iloc[-1]/bench_data['Close'].iloc[-max(1, min(63, len(bench_data)-1))]))*100)
                        ej = safe_n((d['Volume'].tail(21).mean()/max(d['Volume'].tail(252).mean() if len(d)>200 else d['Volume'].mean(),1))*100)
                        se = safe_n(50+(((curr_p/d['Close'].iloc[-max(1, min(5, len(d)-1))])-1)*1200))

                        v_ma20 = d['Volume'].rolling(20, min_periods=1).mean()
                        v_std20 = d['Volume'].rolling(20, min_periods=1).std().fillna(0)
                        v_upper = v_ma20 + (2.0 * v_std20)
                        v_ma60 = d['Volume'].rolling(60, min_periods=1).mean()
                        roc = d['Close'].pct_change() * 100
                        is_cyan = (d['Volume'] > v_upper) & (d['Volume'] > v_ma60 * 1.9) & (roc.abs() > 2.0) & (d['Close'] > d['Open'])
                        has_cyan_3d = is_cyan.tail(3).any()

                        if net_flow_20 > 0 and conc_20 < 50 and state in [1, 2, 7, 8, 9] and se > 75 and ej > 85 and crs > 52:
                            found_stocks.append({
                                'Ticker': t, 'RS Rating': crs, 'Tags': f"💰 異動" if has_cyan_3d else "",
                                'se': se, 'ej': ej, 'net_flow_20': net_flow_20, 'conc_20': conc_20, 'state': state
                            })
                except: pass
            st.session_state.c_scanned_stocks = sorted(found_stocks, key=lambda x: x['RS Rating'], reverse=True)
            
    if st.session_state.c_scanned_stocks:
        st.success(f"🎉 捕捉到 {len(st.session_state.c_scanned_stocks)} 隻大戶佈局目標！")
        for s in st.session_state.c_scanned_stocks:
            st.markdown(f"<div class='scan-card-fire'><h2>🎯 {s['Ticker']} | 符合大戶佈局！{s['Tags']} 🔥 大戶掃貨</h2><p>💰 資金流: {s['net_flow_20']/1e8:.1f}億 | 🎯 集中度: {s['conc_20']:.1f}% | 🌊 OBV: {s['state']}<br>⚡ SE: {s['se']:.1f} | 🔋 EJ: {s['ej']:.1f} | 📈 RS: {s['RS Rating']:.1f}</p></div>", unsafe_allow_html=True)

        st.write("---")
        sel_target = st.selectbox("🎯 選擇目標查看 X 光戰術圖", [s['Ticker'] for s in st.session_state.c_scanned_stocks])
        if sel_target:
            with st.spinner("正在為您繪製戰術圖表..."):
                try:
                    df = smart_fetch(sel_target, period="6mo")
                    df['MA50'] = df['Close'].rolling(50, min_periods=1).mean()
                    df['EMA10'] = df['Close'].ewm(span=10, adjust=False).mean()
                    
                    fig = make_subplots(rows=5, cols=1, shared_xaxes=True, row_heights=[0.45, 0.1, 0.2, 0.15, 0.1], vertical_spacing=0.02)
                    dates = df.index.strftime('%Y-%m-%d')
                    
                    fig.add_trace(go.Candlestick(x=dates, open=df['Open'], high=df['High'], low=df['Low'], close=df['Close'], name="K線"), row=1, col=1)
                    fig.add_trace(go.Scatter(x=dates, y=df['MA50'], mode='lines', name='50MA', line=dict(color='yellow', width=1.5)), row=1, col=1)
                    fig.add_trace(go.Scatter(x=dates, y=df['EMA10'], mode='lines', name='10 EMA', line=dict(color='orange', width=2, dash='dot')), row=1, col=1)
                    
                    recent_high = df['High'].tail(20).max()
                    fig.add_hline(y=recent_high, line_dash="dash", line_color="#00FFCC", annotation_text=f"🎯 破頂買入: ${recent_high:.2f}", annotation_position="top left", annotation_font=dict(color="white", size=13), row=1, col=1)
                    
                    counts, bins = np.histogram(df['Close'], bins=30, weights=df['Volume'])
                    max_c = max(counts) if len(counts) > 0 and max(counts) > 0 else 1
                    fig.add_trace(go.Bar(y=(bins[:-1]+bins[1:])/2, x=counts, orientation='h', marker_color='rgba(150,150,150,0.3)', name='重貨區', hoverinfo='skip', xaxis='x6', yaxis='y1'))

                    v_colors = ['#00FF00' if df['Close'].iloc[i] >= df['Open'].iloc[i] else '#FF0000' for i in range(len(df))]
                    fig.add_trace(go.Bar(x=dates, y=df['Volume'], marker_color=v_colors, name="成交量"), row=2, col=1)
                    
                    # 加入 🌟 星星邏輯
                    df['Vol50'] = df['Volume'].rolling(50, min_periods=1).mean()
                    for i in range(len(df)):
                        if df['Close'].iloc[i] > df['Open'].iloc[i] and df['Volume'].iloc[i] > df['Vol50'].iloc[i]*1.5:
                            fig.add_annotation(x=dates[i], y=df['Volume'].iloc[i], text="🌟", showarrow=False, yanchor="bottom", xanchor="center", font=dict(size=14, color="#FFD700"), row=2, col=1)
                    
                    add_energy_subplots(fig, df, row_start=3)
                    
                    fig.update_layout(template="plotly_dark", paper_bgcolor='#0e1117', plot_bgcolor='#111', height=950, barmode='overlay',
                                      hovermode='x unified', xaxis_rangeslider_visible=False, 
                                      xaxis=dict(type='category', showticklabels=False, showspikes=True, spikemode='across', spikecolor="white", spikethickness=1, spikedash='dot'), 
                                      xaxis6=dict(overlaying='x1', anchor='y1', side='top', range=[0, max_c*4], showgrid=False, showticklabels=False),
                                      yaxis=dict(title="股價", showspikes=True, spikemode='across', spikecolor="white", spikethickness=1, spikedash='dot'), 
                                      legend=dict(font=dict(color="white", size=13), orientation="h", yanchor="bottom", y=1.02, xanchor="right", x=1))
                    st.plotly_chart(fig, use_container_width=True, key=f"c_chart_{sel_target}")
                except Exception as e: st.error(f"繪圖出錯: {e}")
    else:
        if 'c_scanned_stocks' in st.session_state and not st.session_state.c_scanned_stocks:
            st.warning("💤 雷達掃描完畢，目前未有起飛目標。")

# =========================================================================
# 📈 模式 D：VCP 形態戰術掃描 & 防守圖
# =========================================================================
elif app_mode == "📈 VCP 形態戰術掃描 & 防守圖":
    st.markdown("<h1 class='main-title'>📈 VCP 形態戰術掃描 & 防守圖</h1>", unsafe_allow_html=True)
    st.markdown("""
    <div style='background-color:#111; padding:15px; border-radius:10px; border-left: 5px solid #BC13FE; margin-bottom: 20px;'>
        <h3 style='color:#BC13FE; margin-top:0;'>🐉 終極獵龍引擎 (Mark Minervini)</h3>
        <p style='color:#ddd; margin-bottom:0;'>海選：50>150>200多頭排列 | RS Rating > 80 | 大戶掃貨標籤<br>
        狙擊：VCP 形態偵測 | HVN 重貨區動態止損 | 獨立 RS 領先線 | 雙戰術過濾</p>
    </div>
    """, unsafe_allow_html=True)

    c_cat, c_mkt, c_sec, c_strat = st.columns([1, 1, 1.5, 1.5])
    with c_cat: asset_type = st.radio("1. 資產類別", ["🏢 領頭個股", "🧺 優質 ETF"])
    with c_mkt: market_choice = st.radio("2. 掃描市場", ["🇺🇸 美股", "🇭🇰 港股"])
    is_us = "美股" in market_choice; is_etf = "ETF" in asset_type; bench_sym = "SPY" if is_us else "2800.HK"
    if is_etf: target_dict = US_ETF_MAP if is_us else HK_ETF_MAP
    else: target_dict = US_STOCK_MAP if is_us else HK_STOCK_MAP
    
    # 🌟 Fix: 防撞保險絲 (Unique Key)
    with c_sec: s_choice = st.selectbox("3. 選擇掃描範圍", ["🌐 啟動全星系大規模搜索"] + list(target_dict.keys()), key=f"vcp_rng_{asset_type}_{market_choice}")
    with c_strat: vcp_strat = st.radio("4. 戰術過濾 (機變)", ["🔥 極致新高 (ATH)", "🐉 潛龍伏躍 (10-20% 空間)"])

    if 'vcp_scanned_stocks' not in st.session_state: st.session_state.vcp_scanned_stocks = []

    if st.button("📡 [神掣] 發射！執行核心 RS 海選與大戶偵測"):
        tickers_to_scan = list(set([t for sub in target_dict.values() for t in sub])) if "星系" in s_choice else target_dict.get(s_choice, [])
        found_stocks = []; pb = st.progress(0)
        with st.spinner("⏳ 慢速防封鎖引擎已啟動，正在對比大盤 RS 同尋找大戶足跡..."):
            try:
                bench_df = smart_fetch(bench_sym, period="1y")['Close'].dropna()
                yearly_returns = {}; valid_dfs = {}
                for idx, t in enumerate(tickers_to_scan):
                    pb.progress((idx + 1) / len(tickers_to_scan))
                    if idx > 0 and idx % 10 == 0: time.sleep(1.0)
                    try:
                        df_t = smart_fetch(t, period="1y")
                        # 🌟 Fix 1: 0100.hk 醫治 (確保20日即可掃描)
                        if len(df_t) >= 20:
                            ret = (df_t['Close'].iloc[-1] / df_t['Close'].iloc[0]) - 1
                            yearly_returns[t] = ret; valid_dfs[t] = df_t
                    except: continue

                if yearly_returns:
                    all_rets = pd.Series(list(yearly_returns.values()))
                    for t, ret in yearly_returns.items():
                        df_vcp = valid_dfs[t].copy()
                        df_vcp['MA50'] = df_vcp['Close'].rolling(50, min_periods=1).mean()
                        df_vcp['MA150'] = df_vcp['Close'].rolling(150, min_periods=1).mean()
                        df_vcp['MA200'] = df_vcp['Close'].rolling(200, min_periods=1).mean()
                        curr = df_vcp.iloc[-1]; ath = df_vcp['High'].tail(252).max()
                        
                        if not (curr['Close'] > df_vcp['MA50'].iloc[-1] and df_vcp['MA50'].iloc[-1] > df_vcp['MA150'].iloc[-1]): continue
                        if vcp_strat == "🔥 極致新高 (ATH)":
                            if not (df_vcp['MA150'].iloc[-1] > df_vcp['MA200'].iloc[-1]): continue
                            if (curr['Close'] / ath) < 0.93: continue
                        else:
                            if not (0.75 <= (curr['Close'] / ath) <= 0.90): continue

                        rs_rating = int((all_rets[all_rets <= ret].count() / len(all_rets)) * 99)
                        if rs_rating < 80: continue
                        
                        df_vcp['Vol50'] = df_vcp['Volume'].rolling(50, min_periods=1).mean()
                        whale_count = len(df_vcp.tail(10)[(df_vcp.tail(10)['Close'] > df_vcp.tail(10)['Open']) & (df_vcp.tail(10)['Volume'] > df_vcp.tail(10)['Vol50'] * 1.5)])
                        
                        v_ma20 = df_vcp['Volume'].rolling(20, min_periods=1).mean(); v_std20 = df_vcp['Volume'].rolling(20, min_periods=1).std().fillna(0)
                        v_upper = v_ma20 + (2.0 * v_std20); ma60 = df_vcp['Volume'].rolling(60, min_periods=1).mean(); roc = df_vcp['Close'].pct_change() * 100
                        has_cyan_3d = ((df_vcp['Volume'] > v_upper) & (df_vcp['Volume'] > ma60 * 1.9) & (roc.abs() > 2.0) & (df_vcp['Close'] > df_vcp['Open'])).tail(3).any()
                        
                        found_stocks.append({'Ticker': t, 'RS Rating': rs_rating, 'Tags': f"🔥 大戶掃貨 ({whale_count}/10)" + (" 💰" if has_cyan_3d else ""), 'Pivot': df_vcp['High'].tail(20).max()})
                st.session_state.vcp_scanned_stocks = sorted(found_stocks, key=lambda x: x['RS Rating'], reverse=True)
            except Exception as e: st.error(f"掃描受限: {e}")

    if st.session_state.vcp_scanned_stocks:
        st.success(f"🎉 成功尋獲 {len(st.session_state.vcp_scanned_stocks)} 隻終極潛力標的！")
        st.markdown("### 🏆 領頭羊精銳名單")
        for s in st.session_state.vcp_scanned_stocks:
            bg = "scan-card-super" if '🔥' in s['Tags'] else "scan-card-fire"
            st.markdown(f"<div class='{bg}'><div style='display:flex; justify-content:space-between;'><span style='font-size:1.5rem; font-weight:bold; color:white;'>[{s['Ticker']}] 趨勢: ✅ | RS Rating: <span style='color:#00FFCC;'>{s['RS Rating']}</span></span><span style='font-size:1.2rem; font-weight:bold; color:#FFD700;'>{s['Tags']}</span></div></div>", unsafe_allow_html=True)

        st.write("---")
        sel_target = st.selectbox("🎯 選擇目標查看「3 層視覺化戰術儀表板」", [s['Ticker'] for s in st.session_state.vcp_scanned_stocks])
        if sel_target:
            sel_data = next((item for item in st.session_state.vcp_scanned_stocks if item["Ticker"] == sel_target), None)
            pivot_price = sel_data['Pivot']
            
            with st.spinner("正在繪製 K線、重貨區 HVN 及 RS 領先線..."):
                try:
                    df = smart_fetch(sel_target, period="6mo")
                    if df.empty: st.warning("數據不足繪製圖表"); st.stop()
                    b_df = smart_fetch(bench_sym, period="6mo")['Close']
                    df['MA50'] = df['Close'].rolling(50, min_periods=1).mean()
                    df['Vol50'] = df['Volume'].rolling(50, min_periods=1).mean()
                    df['EMA10'] = df['Close'].ewm(span=10, adjust=False).mean()
                    
                    df_a, b_a = df['Close'].align(b_df, join='inner')
                    rs_line = (df_a / b_a).reindex(df.index).ffill().bfill() 
                    
                    counts, bins = np.histogram(df['Close'], bins=25, weights=df['Volume'])
                    hvn_price = (bins[np.argmax(counts)] + bins[np.argmax(counts)+1]) / 2
                    stop_loss = hvn_price * 0.985
                    
                    df['H-L'] = np.maximum(df['High'] - df['Low'], 0.001)
                    df['H-PC'] = abs(df['High'] - df['Close'].shift(1))
                    df['L-PC'] = abs(df['Low'] - df['Close'].shift(1))
                    df['TR'] = df[['H-L', 'H-PC', 'L-PC']].max(axis=1)
                    df['ATR'] = df['TR'].rolling(14, min_periods=1).mean()
                    atr_stop = df['Close'].iloc[-1] - (1.5 * df['ATR'].iloc[-1]) if not pd.isna(df['ATR'].iloc[-1]) else stop_loss
                    risk_pct = ((df['Close'].iloc[-1] - stop_loss) / df['Close'].iloc[-1]) * 100

                    # 🌟 Fix 4: VCP 圖表加入三層能量指標 (共 6 行)
                    fig = make_subplots(rows=6, cols=1, shared_xaxes=True, row_heights=[0.35, 0.1, 0.2, 0.1, 0.1, 0.15], vertical_spacing=0.02)
                    dates = df.index.strftime('%Y-%m-%d')
                    
                    fig.add_trace(go.Candlestick(x=dates, open=df['Open'], high=df['High'], low=df['Low'], close=df['Close'], name="K線"), row=1, col=1)
                    fig.add_trace(go.Scatter(x=dates, y=df['MA50'], mode='lines', name='50MA', line=dict(color='yellow', width=1.5)), row=1, col=1)
                    fig.add_trace(go.Scatter(x=dates, y=df['EMA10'], mode='lines', name='10 EMA', line=dict(color='orange', width=1.5, dash='dot')), row=1, col=1)
                    
                    fig.add_hline(y=pivot_price, line_dash="dash", line_color="#00FFCC", annotation_text=f"🎯 買入: ${pivot_price:.2f}", annotation_position="top left", annotation_font=dict(color="white", size=13), row=1, col=1)
                    fig.add_hline(y=stop_loss, line_dash="solid", line_color="#FF4B4B", annotation_text=f"🛑 重貨區止損: ${stop_loss:.2f}", annotation_position="bottom left", annotation_font=dict(color="white", size=13), row=1, col=1)
                    fig.add_hline(y=atr_stop, line_dash="dash", line_color="#BC13FE", annotation_text=f"🛡️ 1.5 ATR 止損: ${atr_stop:.2f}", annotation_position="bottom right", annotation_font=dict(color="white", size=13), row=1, col=1)
                    
                    max_c = max(counts) if len(counts) > 0 and max(counts) > 0 else 1
                    fig.add_trace(go.Bar(y=(bins[:-1]+bins[1:])/2, x=counts, orientation='h', marker_color='rgba(136, 136, 136, 0.4)', name='重貨區 HVN', hoverinfo='skip', xaxis='x7', yaxis='y1'))
                    
                    v_colors = ['#00FF00' if df['Close'].iloc[i] >= df['Open'].iloc[i] else '#FF0000' for i in range(len(df))]
                    fig.add_trace(go.Bar(x=dates, y=df['Volume'], marker_color=v_colors, name="成交量"), row=2, col=1)
                    for i in range(len(df)):
                        if df['Close'].iloc[i] > df['Open'].iloc[i] and df['Volume'].iloc[i] > df['Vol50'].iloc[i]*1.5:
                            fig.add_annotation(x=dates[i], y=df['Volume'].iloc[i], text="🌟", showarrow=False, yanchor="bottom", xanchor="center", font=dict(size=14, color="#FFD700"), row=2, col=1)

                    add_energy_subplots(fig, df, row_start=3)

                    fig.add_trace(go.Scatter(x=dates, y=rs_line, mode='lines', line=dict(color='#BC13FE', width=2), name="RS線"), row=6, col=1)
                    if df['Close'].iloc[-1] < df['Close'].tail(20).max() * 0.98 and rs_line.iloc[-1] >= rs_line.tail(20).max() * 0.99:
                        fig.add_annotation(x=dates[-1], y=rs_line.iloc[-1], text="🌟 起步點！", showarrow=True, ax=-40, ay=-30, font=dict(color="white", size=14), row=6, col=1)

                    fig.update_layout(template="plotly_dark", paper_bgcolor='#0e1117', plot_bgcolor='#111', height=1050, barmode='overlay',
                                      hovermode='x unified', xaxis_rangeslider_visible=False, 
                                      xaxis=dict(type='category', showticklabels=False), 
                                      xaxis6=dict(type='category', title="日期", showspikes=True, spikemode='across', spikecolor="white", spikethickness=1, spikedash='dot'), 
                                      xaxis7=dict(overlaying='x1', anchor='y1', side='top', range=[0, max_c*4], showgrid=False, showticklabels=False),
                                      yaxis=dict(title="股價"), yaxis2=dict(title="成交量", showticklabels=False),
                                      yaxis6=dict(title="RS Rating", showticklabels=False),
                                      legend=dict(font=dict(color="white", size=13), orientation="h", yanchor="bottom", y=1.02, xanchor="right", x=1))
                    st.plotly_chart(fig, use_container_width=True, key=f"d_chart_{sel_target}")

                    risk_alert = f"<span style='color:#FF4B4B;'>⚠️ 長線防波堤極限風險 ({risk_pct:.1f}%)，請相應縮小買入倉位！</span>" if risk_pct > 7.0 else f"<span style='color:#00FFCC;'>✅ 長線防波堤風險可控 ({risk_pct:.1f}%)</span>"
                    st.markdown(f"<div style='background-color:#111; padding:20px; border-radius:10px; border:2px solid #FFD700;'><h4 style='color:#FFD700; margin-top:0;'>🛡️ 三重防線管理</h4><p style='font-size:1.2rem; color:white;'>🎯 設定買入觸發價 (Pivot)： <b style='color:#00FFCC;'>${pivot_price:.2f}</b></p><hr style='border-color:#333;'><p style='font-size:1.1rem; color:white;'>1️⃣ 極限短炒止盈 (10 EMA)： <b style='color:orange;'>${df['EMA10'].iloc[-1]:.2f}</b></p><p style='font-size:1.1rem; color:white;'>2️⃣ 波段抗震止損 (1.5 ATR)： <b style='color:#BC13FE;'>${atr_stop:.2f}</b></p><p style='font-size:1.1rem; color:white;'>3️⃣ 終極底線止損 (HVN 重貨區)： <b style='color:#FF4B4B;'>${stop_loss:.2f}</b></p><p>{risk_alert}</p></div>", unsafe_allow_html=True)
                except Exception as e: st.error(f"繪圖出錯: {e}")
    else:
        if 'vcp_scanned_stocks' in st.session_state and not st.session_state.vcp_scanned_stocks:
            st.warning("💤 雷達掃描完畢，未有符合過濾之標的。")

# =========================================================================
# 🌊 模式 E：海龜回測加注雷達 (🌟 Fix 5: 圖表加入三層能量指標)
# =========================================================================
elif app_mode == "🌊 海龜回測加注雷達 (Mode E)":
    st.markdown("<h1 class='main-title'>🌊 海龜回測加注雷達 (Mode E)</h1>", unsafe_allow_html=True)
    st.markdown("""
    <div style='background-color:#111; padding:15px; border-radius:10px; border-left: 5px solid #00FFCC; margin-bottom: 20px;'>
        <h3 style='color:#00FFCC; margin-top:0;'>🐢 N字型突破加注法 (1-2-3 Continuation)</h3>
        <p style='color:#ddd; margin-bottom:0;'>此雷達已實裝「真龍基因過濾」：先過濾最強 RS，再搵 <b>N字回測 10 EMA</b>。<br>
        確保踢走所有弱勢股，只搵強者回調嘅黃金加注機會！</p>
    </div>
    """, unsafe_allow_html=True)
    
    c1, c2, c3 = st.columns([1, 1, 1.5])
    with c1: asset_type = st.radio("1. 掃描對象", ["🏢 領頭個股", "🧺 優質 ETF"])
    with c2: market_choice = st.radio("2. 掃描市場", ["🇺🇸 美股", "🇭🇰 港股"])
    with c3: turtle_strat = st.radio("3. 海龜戰術 (機變)", ["🔥 極致真龍 (ATH 回測)", "🐉 潛龍初醒 (剛入強勢)"])

    is_us = "美股" in market_choice; is_etf = "ETF" in asset_type
    target_dict = (US_ETF_MAP if is_etf else US_STOCK_MAP) if is_us else (HK_ETF_MAP if is_etf else HK_STOCK_MAP)
    s_choice = st.selectbox("4. 選擇掃描範圍", ["🌐 啟動全星系大規模搜索"] + list(target_dict.keys()), key=f"e_rng_{asset_type}_{market_choice}")

    if 'e_scanned_stocks' not in st.session_state: st.session_state.e_scanned_stocks = []

    if st.button("📡 發射真龍 N 字雷達！"):
        tickers = list(set([t for sub in target_dict.values() for t in sub])) if "星系" in s_choice else target_dict.get(s_choice, [])
        found = []; pb = st.progress(0)
        
        with st.spinner("⏳ 雷達正在慢速穩定過濾「去弱留強」 N 字加注點..."):
            yearly_returns = {}; valid_dfs = {}
            for idx, t in enumerate(tickers):
                pb.progress((idx + 1) / len(tickers))
                if idx > 0 and idx % 10 == 0: time.sleep(1.0)
                try:
                    df_t = smart_fetch(t, period="1y")
                    # 🌟 Fix 1: 0100.hk 醫治 (確保20日即可掃描)
                    if len(df_t) >= 20:
                        ret = (df_t['Close'].iloc[-1] / df_t['Close'].iloc[0]) - 1
                        yearly_returns[t] = ret; valid_dfs[t] = df_t
                except: continue
            
            if yearly_returns:
                all_rets = pd.Series(list(yearly_returns.values()))
                for t, ret in yearly_returns.items():
                    df = valid_dfs[t].copy()
                    
                    denom = np.maximum(df['High'] - df['Low'], 0.001)
                    df['BuyVol'] = np.where(df['High'] > df['Low'], df['Volume'] * (df['Close'] - df['Low']) / denom, 0)
                    df['SellVol'] = np.where(df['High'] > df['Low'], df['Volume'] * (df['High'] - df['Close']) / denom, 0)
                    df['NetVol'] = df['BuyVol'] - df['SellVol']
                    df['NETMA'] = df['NetVol'].rolling(10, min_periods=1).mean()
                    
                    v_ma20 = df['Volume'].rolling(20, min_periods=1).mean()
                    v_std20 = df['Volume'].rolling(20, min_periods=1).std().fillna(0)
                    v_upper = v_ma20 + (2.0 * v_std20)
                    v_ma60 = df['Volume'].rolling(60, min_periods=1).mean()
                    roc = df['Close'].pct_change() * 100
                    df['Magenta'] = (df['Volume'] > v_upper) & (df['Volume'] > v_ma60 * 1.9) & (roc.abs() > 2.0) & (df['Close'] <= df['Open'])
                    
                    has_cyan_3d = ((df['Volume'] > v_upper) & (df['Volume'] > v_ma60 * 1.9) & (roc.abs() > 2.0) & (df['Close'] > df['Open'])).tail(3).any()

                    curr_p = df['Close'].iloc[-1]
                    ma50 = df['Close'].rolling(50, min_periods=1).mean().iloc[-1]
                    ma150 = df['Close'].rolling(150, min_periods=1).mean().iloc[-1]
                    ma200 = df['Close'].rolling(200, min_periods=1).mean().iloc[-1]
                    ema10 = df['Close'].ewm(span=10, adjust=False).mean().iloc[-1]
                    ath = df['High'].tail(252).max()
                    
                    rs_rating = int((all_rets[all_rets <= ret].count() / len(all_rets)) * 99)
                    
                    if not (curr_p > ma50 and ma50 > ma150): continue
                    if turtle_strat == "🔥 極致真龍 (ATH 回測)":
                        if not (ma150 > ma200): continue 
                        if (curr_p / ath) < 0.90: continue
                        if rs_rating < 80: continue
                    else: 
                        if not (0.75 <= (curr_p / ath) <= 0.92): continue 
                        if rs_rating < 70: continue

                    last_20_high = df['High'].tail(20).max()
                    high_idx = df['High'].tail(20).argmax()
                    days_since_high = 19 - high_idx
                    
                    df['Vol50'] = df['Volume'].rolling(50, min_periods=1).mean()
                    whale_count = len(df.tail(10)[(df.tail(10)['Close'] > df.tail(10)['Open']) & (df.tail(10)['Volume'] > df.tail(10)['Vol50'] * 1.5)])
                    
                    if 2 <= days_since_high <= 15: 
                        pullback_pct = ((curr_p - last_20_high) / last_20_high) * 100
                        if -15 <= pullback_pct <= -1:
                            if ema10 * 0.98 <= curr_p <= ema10 * 1.04:
                                pullback_magenta = df['Magenta'].iloc[-days_since_high:].any()
                                current_netma = df['NETMA'].iloc[-1]
                                
                                if current_netma > 0 and not pullback_magenta:
                                    swing_low = df['Low'].iloc[-days_since_high:].min()
                                    found.append({
                                        'Ticker': t, 'Price': curr_p, 'High': last_20_high,
                                        'Low': swing_low, 'Pullback': pullback_pct, 'EMA10': ema10,
                                        'Days Since High': days_since_high,
                                        'Tags': f"🔥 大戶掃貨 ({whale_count}/10)" + (" 💰" if has_cyan_3d else "")
                                    })
            st.session_state.e_scanned_stocks = sorted(found, key=lambda x: x['Pullback'], reverse=True)

    if st.session_state.e_scanned_stocks:
        st.success(f"🎉 捕捉到 {len(st.session_state.e_scanned_stocks)} 隻健康回測中嘅目標！")
        for p in st.session_state.e_scanned_stocks:
            st.markdown(f"""
            <div class='pullback-card'>
                <div style='display:flex; justify-content:space-between; align-items:center;'>
                    <span style='font-size:1.8rem; font-weight:bold; color:white;'>🎯 [{p['Ticker']}] {p['Tags']}</span>
                    <span style='font-size:1.2rem; font-weight:bold; color:#00FFCC;'>現價: ${p['Price']:.2f}</span>
                </div>
                <hr style='border-color:#444; margin:10px 0;'>
                <div style='display:flex; justify-content:space-between;'>
                    <span>📈 前高阻力 (海龜買入點): <b style='color:#00FFCC;'>${p['High']:.2f}</b> <span style='font-size:0.9rem;'>({p['Days Since High']} 日前)</span></span>
                    <span>📉 回落幅度: <b style='color:#FF4B4B;'>{p['Pullback']:.1f}%</b></span>
                </div>
                <div style='display:flex; justify-content:space-between; margin-top:5px;'>
                    <span>🛡️ 極限防守 (10 EMA): <b style='color:orange;'>${p['EMA10']:.2f}</b></span>
                    <span>🛑 N字波谷底 (海龜止損): <b style='color:#FF00FF;'>${p['Low']:.2f}</b></span>
                </div>
            </div>
            """, unsafe_allow_html=True)
        
        st.write("---")
        sel_target = st.selectbox("🎯 選擇目標查看 X 光戰術圖", [s['Ticker'] for s in st.session_state.e_scanned_stocks])
        if sel_target:
            p_data = next(x for x in st.session_state.e_scanned_stocks if x['Ticker'] == sel_target)
            with st.spinner("正在為您繪製專屬海龜回測戰術圖表..."):
                try:
                    df = smart_fetch(sel_target, period="6mo")
                    if df.empty: st.warning("數據不足繪製圖表"); st.stop()
                    df['MA50'] = df['Close'].rolling(50, min_periods=1).mean()
                    df['EMA10'] = df['Close'].ewm(span=10, adjust=False).mean()
                    
                    fig = make_subplots(rows=5, cols=1, shared_xaxes=True, row_heights=[0.45, 0.1, 0.2, 0.15, 0.1], vertical_spacing=0.02)
                    dates = df.index.strftime('%Y-%m-%d')
                    
                    fig.add_trace(go.Candlestick(x=dates, open=df['Open'], high=df['High'], low=df['Low'], close=df['Close'], name="K線"), row=1, col=1)
                    fig.add_trace(go.Scatter(x=dates, y=df['MA50'], mode='lines', name='50MA', line=dict(color='yellow', width=1.5)), row=1, col=1)
                    fig.add_trace(go.Scatter(x=dates, y=df['EMA10'], mode='lines', name='10 EMA', line=dict(color='orange', width=2, dash='dot')), row=1, col=1)
                    
                    fig.add_hline(y=p_data['High'], line_dash="dash", line_color="#00FFCC", annotation_text=f"🐢 破頂買入: ${p_data['High']:.2f}", annotation_position="top left", annotation_font=dict(color="white", size=13), row=1, col=1)
                    fig.add_hline(y=p_data['Low'], line_dash="solid", line_color="#FF00FF", annotation_text=f"🛑 波谷止損: ${p_data['Low']:.2f}", annotation_position="bottom left", annotation_font=dict(color="white", size=13), row=1, col=1)
                    
                    counts, bins = np.histogram(df['Close'], bins=30, weights=df['Volume'])
                    max_c = max(counts) if len(counts) > 0 and max(counts) > 0 else 1
                    fig.add_trace(go.Bar(y=(bins[:-1]+bins[1:])/2, x=counts, orientation='h', marker_color='rgba(150,150,150,0.3)', name='重貨區', hoverinfo='skip', xaxis='x6', yaxis='y1'))

                    v_colors = ['#00FF00' if df['Close'].iloc[i] >= df['Open'].iloc[i] else '#FF0000' for i in range(len(df))]
                    fig.add_trace(go.Bar(x=dates, y=df['Volume'], marker_color=v_colors, name="成交量"), row=2, col=1)
                    
                    df['Vol50'] = df['Volume'].rolling(50, min_periods=1).mean()
                    for i in range(len(df)):
                        if df['Close'].iloc[i] > df['Open'].iloc[i] and df['Volume'].iloc[i] > df['Vol50'].iloc[i]*1.5:
                            fig.add_annotation(x=dates[i], y=df['Volume'].iloc[i], text="🌟", showarrow=False, yanchor="bottom", xanchor="center", font=dict(size=14, color="#FFD700"), row=2, col=1)
                    
                    add_energy_subplots(fig, df, row_start=3)
                    
                    fig.update_layout(template="plotly_dark", paper_bgcolor='#0e1117', plot_bgcolor='#111', height=950, barmode='overlay',
                                      hovermode='x unified', xaxis_rangeslider_visible=False, 
                                      xaxis=dict(type='category', showticklabels=False), 
                                      xaxis5=dict(type='category', title="日期", showspikes=True, spikemode='across', spikecolor="white", spikethickness=1, spikedash='dot'), 
                                      xaxis6=dict(overlaying='x1', anchor='y1', side='top', range=[0, max_c*4], showgrid=False, showticklabels=False),
                                      yaxis=dict(title="股價"), yaxis2=dict(title="成交量", showticklabels=False),
                                      legend=dict(font=dict(color="white", size=13), orientation="h", yanchor="bottom", y=1.02, xanchor="right", x=1))
                    st.plotly_chart(fig, use_container_width=True, key=f"e_chart_{sel_target}")
                except Exception as e: st.error(f"繪圖出錯: {e}")
    else:
        if 'e_scanned_stocks' in st.session_state and not st.session_state.e_scanned_stocks:
            st.warning("💤 雷達掃描完畢，未有符合過濾之標的。")
