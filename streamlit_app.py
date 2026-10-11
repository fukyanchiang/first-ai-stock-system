import streamlit as st
import yfinance as yf
import pandas as pd
import numpy as np
import plotly.graph_objects as go
from plotly.subplots import make_subplots
from core_logic import scan_dragon_logic, smart_fetch, check_stop_loss
import time
import os
import json
from Speed_defines_the_winner import run_tianwai_feixian
from Speed_defines_the_winner_VerRS import run_tianwai_feixian as run_tianwai_feixian_rs

st.set_page_config(page_title="龍魂神殿 5.0", layout="wide")

HK_STOCK_CSV_URL = "https://raw.githubusercontent.com/fukyanchiang/my-cosmos-vision/refs/heads/main/hk_stock.csv"
HK_ETF_CSV_URL = "https://raw.githubusercontent.com/fukyanchiang/my-cosmos-vision/refs/heads/main/hk_etf.csv"

@st.cache_data(ttl=3600)
def fetch_github_list(url):
    try:
        df = pd.read_csv(url)
        if 'Ticker' in df.columns: df['Ticker'] = df['Ticker'].astype(str)
        return df
    except: return pd.DataFrame()

# ===============================================
# 🪙 HardPenny 專屬核心運算函數
# ===============================================
def run_hardpenny_logic(df: pd.DataFrame, symbol: str, sector: str) -> dict:
    if len(df) < 200: return None
    
    close = df['Close']
    high = df['High']
    low = df['Low']
    vol = df['Volume']
    c_curr = float(close.iloc[-1])

    c_60d = float(close.iloc[-60]) if len(close) >= 60 else float(close.iloc[0])
    ret_3m = (c_curr - c_60d) / c_60d
    cond1 = ret_3m >= 0.20
    low_20 = float(low.tail(20).min())
    cond2 = c_curr >= low_20 
    cond3_4 = False
    for w in range(5, 40):
        w_high = float(high.tail(w).max())
        w_low = float(low.tail(w).min())
        if w_low > 0:
            w_range = (w_high - w_low) / w_low
            if w_range < 0.08:
                cond3_4 = True
                break
    adr = float(((high - low) / low).tail(20).mean())
    cond5 = adr > 0.035
    cond6 = c_curr > 5.0
    turnover_50m = float((close * vol).tail(50).mean())
    cond7 = turnover_50m > 5_000_000
    ema200 = float(close.ewm(span=200, adjust=False).mean().iloc[-1])
    dist_ema200 = (c_curr - ema200) / ema200
    cond8 = dist_ema200 <= 0.60
    all_passed = cond1 and cond2 and cond3_4 and cond5 and cond6 and cond7 and cond8

    if not all_passed: return None

    ema10 = float(close.ewm(span=10, adjust=False).mean().iloc[-1])
    ema20 = float(close.ewm(span=20, adjust=False).mean().iloc[-1])
    ema50 = float(close.ewm(span=50, adjust=False).mean().iloc[-1])
    ema_diff_score = (abs(c_curr - ema10) + abs(c_curr - ema20) + abs(c_curr - ema50)) / c_curr
    ma20 = close.rolling(20).mean().iloc[-1]
    bias = (c_curr - ma20) / ma20 * 100
    rs = (2*c_curr/close.rolling(63, min_periods=1).mean().iloc[-1] + c_curr/close.rolling(126, min_periods=1).mean().iloc[-1] + c_curr/close.rolling(189, min_periods=1).mean().iloc[-1] + c_curr/close.rolling(252, min_periods=1).mean().iloc[-1]) - 5

    return {
        'Ticker': symbol.replace(".HK", ""),
        'Sector': sector,
        'Status': "[🔥 爛市強者]",
        'Score': round(ema_diff_score * 100, 2),
        'RawScore': ema_diff_score,
        'RawPower': round(ret_3m * 100, 1),
        'Penalty': 0,
        'EMA10': round(ema10, 2),
        'Bias': round(bias, 1),
        'RS': round(rs, 1),
        'EJ': round(adr * 100, 1),
        'SE': round(dist_ema200 * 100, 1),
        'Power': round(turnover_50m / 1e6, 1),
        'OBV': '均線糾纏',
        'Icons': '',
        'IsDead': False
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
    "24. 投資與資產 management": "BLK BX TROW APO KKC KKR CG ARES OWL OAK STEP BEN STT BK NTRS IVZ JHG AMG LAZ APAM".split(),
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

with st.sidebar:
    st.markdown("### 🎛️ 系統主指揮中心")
    operation_mode = st.radio(
        "請選擇核心操作模式:",
        [
            "🐉 龍魂神殿雷達系統", 
            "📊 究極資產拔河龍虎榜", 
            "💰 大戶資金流透視 (福德金字塔)"
        ]
    )
    st.markdown("---")
    st.caption("👴 爺爺的操盤矩陣 V188.11 (真龍雙軌升級版)")

if operation_mode == "🐉 龍魂神殿雷達系統":
    MEMORY_FILE = "dragon_memory.json"
    if 'dragon_results' not in st.session_state:
        st.session_state.dragon_results = []
        st.session_state.sl_list = []
        if os.path.exists(MEMORY_FILE):
            try:
                with open(MEMORY_FILE, 'r', encoding='utf-8') as f:
                    saved_data = json.load(f)
                    st.session_state.dragon_results = saved_data.get('results', [])
                    st.session_state.sl_list = saved_data.get('sl_list', [])
            except: pass

    st.markdown("""
        <style>
        .stApp { background-color: #0e1117 !important; color: #FFFFFF !important; }
        div.stButton > button { background-color: #000000 !important; color: #FFFFFF !important; border: 2px solid #FFFFFF !important; border-radius: 0px !important; font-weight: 900 !important; width: 100%; margin-bottom: 5px; }
        div.stButton > button:hover { background-color: #FFFFFF !important; color: #000000 !important; }
        .dragon-card { border-left: 5px solid #00FFCC; background-color: #111111; padding: 15px; margin-bottom: 10px; border-radius: 5px; box-shadow: 0 0 10px rgba(0,255,204,0.1); }
        .data-row { font-size: 0.95rem; color: #CCCCCC; margin-top: 8px; line-height: 1.6; }
        .bear-warning { color: #FF0000 !important; font-size: 1.5rem; font-weight: 900; text-align: center; border: 3px dashed red; background-color: #220000; padding: 15px; margin: 10px 0; border-radius: 10px;}
        </style>
    """, unsafe_allow_html=True)

    def add_energy_subplots(fig, df, dates_chart, row_start):
        var1 = df['Close'] - df['Low']; var2 = df['High'] - df['Close']; var3 = np.maximum(df['High'] - df['Low'], 0.001)
        buyvol = np.where(var3 > 0, df['Volume'] * var1 / var3, 0)
        sellvol = np.where(var3 > 0, df['Volume'] * var2 / var3, 0)
        netvol = buyvol - sellvol
        netma = pd.Series(netvol).rolling(10, min_periods=1).mean()
        
        fig.add_trace(go.Bar(x=dates_chart, y=buyvol, marker_color='#808000', name='買盤', opacity=0.6, hoverinfo='skip'), row=row_start, col=1)
        fig.add_trace(go.Bar(x=dates_chart, y=-sellvol, marker_color='#800000', name='賣盤', opacity=0.6, hoverinfo='skip'), row=row_start, col=1)
        net_colors = ['#00FF00' if val > 0 else '#FF0000' for val in netvol]
        fig.add_trace(go.Bar(x=dates_chart, y=netvol, marker_color=net_colors, name='淨勝方', width=0.4), row=row_start, col=1)
        fig.add_trace(go.Scatter(x=dates_chart, y=netma, mode='lines', line=dict(color='white', width=2), name='氣脈10MA'), row=row_start, col=1)

        v_ma = df['Volume'].rolling(20, min_periods=1).mean()
        v_std = df['Volume'].rolling(20, min_periods=1).std().fillna(0)
        v_upper = v_ma + (2.0 * v_std); ma60 = df['Volume'].rolling(60, min_periods=1).mean(); roc = abs(df['Close'].pct_change()) * 100
        is_burst = (df['Volume'] > v_upper) & (df['Volume'] > ma60 * 1.9) & (roc > 2.0)
        burst_colors = ['#00FFFF' if (is_burst.iloc[i] and df['Close'].iloc[i] > df['Open'].iloc[i]) else ('#FF00FF' if is_burst.iloc[i] else 'rgba(136,136,136,0.3)') for i in range(len(df))]
        fig.add_trace(go.Bar(x=dates_chart, y=df['Volume'], marker_color=burst_colors, name='能量雷達'), row=row_start+1, col=1)

        daily_change = df['Close'].pct_change() * 100
        change_colors = ['#00FF00' if val >= 0 else '#FF0000' for val in daily_change]
        fig.add_trace(go.Bar(x=dates_chart, y=daily_change, marker_color=change_colors, name='日波幅%'), row=row_start+2, col=1)

    if 'page' not in st.session_state: st.session_state.page = 'HOME'
    if 'target' not in st.session_state: st.session_state.target = 'NONE'
    if 'scan_mode' not in st.session_state: st.session_state.scan_mode = 'NORMAL'
    if 'run_mode' not in st.session_state: st.session_state.run_mode = 'NORMAL'

    # ===============================================
    # 總部導航 (7 個按鈕) 
    # ===============================================
    if st.session_state.page == 'HOME':
        st.markdown("<h1 style='text-align:center;font-size:4rem;margin-top:80px;color:#FFD700;'>🐲 龍魂戰略總部</h1>", unsafe_allow_html=True)
        c1, c2, c3, c4, c5, c6, c7 = st.columns(7)
        if c1.button("🐉 龍魂神殿 (普通掃描)"): 
            st.session_state.page = 'DRAGON'; st.session_state.scan_mode = 'NORMAL'
            st.session_state.dragon_results = []; st.session_state.sl_list = []; st.rerun()
        if c2.button("📈 VCP 獵龍 (高勝率模式)"): 
            st.session_state.page = 'DRAGON'; st.session_state.scan_mode = 'VCP'
            st.session_state.dragon_results = []; st.session_state.sl_list = []; st.rerun()
        if c3.button("🐢 海龜加注"): 
            st.info("海龜 模式運作中"); st.session_state.page = 'DRAGON'; st.session_state.scan_mode = 'NORMAL'
            st.session_state.dragon_results = []; st.session_state.sl_list = []; st.rerun()
        if c4.button("🔥 強勢股排列"): 
            st.session_state.page = 'DRAGON'; st.session_state.scan_mode = 'STRONG'
            st.session_state.dragon_results = []; st.session_state.sl_list = []; st.rerun()
        if c5.button("✨ 天外飛仙"): 
            st.session_state.page = 'DRAGON'; st.session_state.scan_mode = 'TIANWAI'; st.session_state.target = 'US_TW'
            st.session_state.dragon_results = []; st.session_state.sl_list = []; st.rerun()
        if c6.button("🪙 HardPenny"): 
            st.session_state.page = 'DRAGON'; st.session_state.scan_mode = 'HARDPENNY'; st.session_state.target = 'US_HP'
            st.session_state.dragon_results = []; st.session_state.sl_list = []; st.rerun()
        if c7.button("⚡ 天外飛仙RS"): 
            st.session_state.page = 'DRAGON'; st.session_state.scan_mode = 'TIANWAI_RS'; st.session_state.target = 'US_TW_RS'
            st.session_state.dragon_results = []; st.session_state.sl_list = []; st.rerun()

    elif st.session_state.page == 'DRAGON':
        selected_tickers = []; market_mode = "HK"; btn_radar = False
        is_ath_mode = False 
        vcp_52w = False 
        
        # ===============================================
        # 專屬：天外飛仙, HardPenny, 天外飛仙RS 極簡 UI (共用結構)
        # ===============================================
        if st.session_state.scan_mode in ['TIANWAI', 'HARDPENNY', 'TIANWAI_RS']:
            is_hp = (st.session_state.scan_mode == 'HARDPENNY')
            is_rs = (st.session_state.scan_mode == 'TIANWAI_RS')
            
            if is_hp: title_text = "🪙 爛市尋強者 - 9大 SEPA 嚴格篩選"; btn_text = "🪙 啟動爛市雷達"; us_target = 'US_HP'; hk_target = 'HK_HP'
            elif is_rs: title_text = "⚡ 天外飛仙RS (SCTR 真龍加強版)"; btn_text = "⚡ 啟動飛仙RS雷達"; us_target = 'US_TW_RS'; hk_target = 'HK_TW_RS'
            else: title_text = "✨ 天外飛仙 (第 6 掣) 極速起爆雷達"; btn_text = "✨ 啟動飛仙雷達"; us_target = 'US_TW'; hk_target = 'HK_TW'

            st.markdown(f"<h1 style='text-align:center; color:#00FFCC;'>{title_text}</h1>", unsafe_allow_html=True)
            nav = st.columns([1, 1, 1, 3])
            if nav[0].button("⬅️ 返回總部"): st.session_state.page = 'HOME'; st.rerun()
            if nav[1].button("🇺🇸 美股"): st.session_state.target = us_target
            if nav[2].button("🇭🇰 港股"): st.session_state.target = hk_target
            
            st.markdown("---")
            
            if st.session_state.target in ['US_TW', 'US_HP', 'US_TW_RS']:
                st.write("### 🇺🇸 選擇美股戰略名單：")
                m = st.columns(4)
                files = [("SP500_Equities.csv", "大藍籌"), ("Market_Focus.csv", "精選"), ("Industry_Focus.csv", "行業"), ("US_ETFs.csv", "美股ETF")]
                for i, (f, name) in enumerate(files):
                    if m[i].button(f"選定 {name}"): 
                        st.session_state.active_file = f; st.success(f"✅ 已選定 {name}")
                st.write("<br>", unsafe_allow_html=True)
                if st.button(btn_text, use_container_width=True): btn_radar = True

            elif st.session_state.target in ['HK_TW', 'HK_HP', 'HK_TW_RS']:
                st.write("### 🇭🇰 選擇港股戰略名單：")
                m = st.columns(2)
                files = [("hk_stock.csv", "港股個股"), ("hk_etf.csv", "港股ETF")]
                for i, (f, name) in enumerate(files):
                    if m[i].button(f"選定 {name}"): 
                        st.session_state.active_file = f; st.success(f"✅ 已選定 {name}")
                st.write("<br>", unsafe_allow_html=True)
                if st.button(btn_text, use_container_width=True): btn_radar = True
                
            if btn_radar:
                st.session_state.run_mode = st.session_state.scan_mode
                if hasattr(st.session_state, 'active_file'):
                    f = st.session_state.active_file
                    try:
                        if f == 'hk_stock.csv': df_csv = fetch_github_list(HK_STOCK_CSV_URL)
                        elif f == 'hk_etf.csv': df_csv = fetch_github_list(HK_ETF_CSV_URL)
                        else: df_csv = pd.read_csv(f)
                        
                        col = [c for c in df_csv.columns if c.lower() in ['ticker', 'symbol', '代號', 'code']][0]
                        tickers = df_csv[col].dropna().astype(str).tolist()
                        if f in ['hk_stock.csv', 'hk_etf.csv']:
                            market_mode = 'HK'
                            tickers = [t.zfill(4) + ".HK" if not t.endswith(".HK") else t for t in tickers]
                        else:
                            market_mode = 'US'
                        
                        if 'Sector' in df_csv.columns:
                            selected_tickers = list(df_csv[[col, 'Sector']].dropna().itertuples(index=False, name=None))
                            if market_mode == 'HK': selected_tickers = [(t.zfill(4)+".HK" if not t.endswith(".HK") else t, sec) for t, sec in selected_tickers]
                        else:
                            selected_tickers = [(t, "雷達掃描") for t in tickers]
                    except: st.error("讀取檔案失敗。")
                else: st.warning("請先選定一個名單！")

        # ===============================================
        # 傳統：龍魂神殿 UI
        # ===============================================
        else:
            if st.session_state.scan_mode == 'STRONG': mode_display = "🔥 強勢股排列 (週線/日線多頭)"
            elif st.session_state.scan_mode == 'VCP': mode_display = "📈 VCP 高勝率獵龍"
            else: mode_display = "🐉 龍魂神殿 5.0 旗艦雷達"
            
            st.markdown(f"<h1 style='text-align:center; color:#00FFCC;'>{mode_display}</h1>", unsafe_allow_html=True)
            
            nav = st.columns(6)
            if nav[0].button("⬅️ 返回總部"): st.session_state.page = 'HOME'; st.rerun()
            if nav[1].button("🇭🇰 港股"): st.session_state.target = 'HK'
            if nav[2].button("🇺🇸 美股"): st.session_state.target = 'US'
            if nav[3].button("📦 ETF"): st.session_state.target = 'ETF'
            if nav[4].button("🔍 個股"): st.session_state.target = 'SINGLE'
            
            st.markdown("---")
            c_ath, c_btn = st.columns([3, 1])
            with c_ath: 
                is_ath_mode = st.checkbox("🔥 啟動 ATH 歷史新高極致過濾")
                vcp_52w = st.checkbox("🎯 啟動 MM 原汁原味 52週高位 25% 內過濾")

            if st.session_state.target == 'US':
                st.write("### 🇺🇸 選擇美股戰略名單：")
                m = st.columns(5)
                files = [("SP500_Equities.csv", "大藍籌"), ("Market_Focus.csv", "精選"), ("Industry_Focus.csv", "行業"), ("Core_Stocks.csv", "核心"), ("US_ETFs.csv", "美股ETF")]
                for i, (f, name) in enumerate(files):
                    if m[i].button(f"選定 {name}"): 
                        st.session_state.active_file = f; st.success(f"✅ 已選定 {f}")
                with c_btn:
                    if st.session_state.scan_mode == 'STRONG':
                        btn_w = st.button("📡 啟動雷達 (週線多頭)", use_container_width=True)
                        btn_d = st.button("📡 日線多頭排順", use_container_width=True)
                        if btn_w: btn_radar = True; st.session_state.run_mode = 'STRONG_WEEKLY'
                        if btn_d: btn_radar = True; st.session_state.run_mode = 'STRONG_DAILY'
                    else:
                        if st.button("📡 啟動雷達", use_container_width=True): 
                            btn_radar = True; st.session_state.run_mode = st.session_state.scan_mode

            elif st.session_state.target == 'SINGLE':
                st.write("### 🔍 個股自訂掃描：")
                col1, col2 = st.columns([3, 1])
                with col1: single_t = st.text_input("輸入股票代號 (例: NVDA, 0700.HK, TSLA)", "").upper().strip()
                with col2:
                    st.write("<br>", unsafe_allow_html=True)
                    if st.session_state.scan_mode == 'STRONG':
                        btn_w = st.button("📡 啟動雷達 (週線多頭)", use_container_width=True)
                        btn_d = st.button("📡 日線多頭排順", use_container_width=True)
                        if btn_w or btn_d:
                            if single_t:
                                selected_tickers = [(single_t, "自選個股")]
                                btn_radar = True
                                st.session_state.run_mode = 'STRONG_WEEKLY' if btn_w else 'STRONG_DAILY'
                            else: st.warning("請先輸入代號！")
                    else:
                        if st.button("📡 立即分析此股", use_container_width=True): 
                            if single_t:
                                selected_tickers = [(single_t, "自選個股")]
                                btn_radar = True
                                st.session_state.run_mode = st.session_state.scan_mode
                            else: st.warning("請先輸入代號！")

            elif st.session_state.target == 'HK':
                st.write("### 🇭🇰 港股板塊掃描 (包含全星系)：")
                df_hk = fetch_github_list(HK_STOCK_CSV_URL)
                hk_sectors = sorted(df_hk['Sector'].dropna().unique().tolist()) if not df_hk.empty else []
                s_choice = st.selectbox("選擇範圍", ["🌐 啟動全星系大規模搜索"] + hk_sectors)
                with c_btn:
                    if st.session_state.scan_mode == 'STRONG':
                        btn_w = st.button("📡 啟動雷達 (週線多頭)", use_container_width=True)
                        btn_d = st.button("📡 日線多頭排順", use_container_width=True)
                        if btn_w: btn_radar = True; st.session_state.run_mode = 'STRONG_WEEKLY'
                        if btn_d: btn_radar = True; st.session_state.run_mode = 'STRONG_DAILY'
                    else:
                        if st.button("📡 啟動雷達", use_container_width=True): 
                            btn_radar = True; st.session_state.run_mode = st.session_state.scan_mode

            elif st.session_state.target == 'ETF':
                st.write("### 📦 港股/美股 ETF 掃描 (包含全星系)：")
                df_etf = fetch_github_list(HK_ETF_CSV_URL)
                etf_sectors = sorted(df_etf['Sector'].dropna().unique().tolist()) if not df_etf.empty else []
                s_choice = st.selectbox("選擇範圍", ["🌐 啟動全星系大規模搜索 (僅限港股 ETF)"] + etf_sectors + list(US_ETF_MAP.keys()))
                with c_btn:
                    if st.session_state.scan_mode == 'STRONG':
                        btn_w = st.button("📡 啟動雷達 (週線多頭)", use_container_width=True)
                        btn_d = st.button("📡 日線多頭排順", use_container_width=True)
                        if btn_w: btn_radar = True; st.session_state.run_mode = 'STRONG_WEEKLY'
                        if btn_d: btn_radar = True; st.session_state.run_mode = 'STRONG_DAILY'
                    else:
                        if st.button("📡 啟動雷達", use_container_width=True): 
                            btn_radar = True; st.session_state.run_mode = st.session_state.scan_mode

            if btn_radar:
                if st.session_state.target == 'SINGLE': market_mode = "US" if not selected_tickers[0][0].endswith(".HK") else "HK"
                elif st.session_state.target == 'US' and hasattr(st.session_state, 'active_file'):
                    try:
                        df_csv = pd.read_csv(st.session_state.active_file)
                        col = [c for c in df_csv.columns if c.lower() in ['ticker', 'symbol', '代號']][0]
                        selected_tickers = [(t, "美股戰略") for t in df_csv[col].dropna().unique()]
                        market_mode = "US"
                    except: st.error("讀取 CSV 失敗，請檢查檔案是否存在。")
                elif st.session_state.target == 'HK':
                    df_hk = fetch_github_list(HK_STOCK_CSV_URL)
                    if not df_hk.empty:
                        if "全星系" in s_choice: selected_tickers = list(df_hk.itertuples(index=False, name=None))
                        else: selected_tickers = list(df_hk[df_hk['Sector'] == s_choice].itertuples(index=False, name=None))
                    market_mode = "HK"
                elif st.session_state.target == 'ETF':
                    df_etf = fetch_github_list(HK_ETF_CSV_URL)
                    raw_list = []
                    if "全星系" in s_choice:
                        if not df_etf.empty: raw_list.extend(list(df_etf.itertuples(index=False, name=None)))
                        selected_tickers = raw_list
                        market_mode = "HK"
                    else:
                        if s_choice in US_ETF_MAP:
                            selected_tickers = [(t, s_choice) for t in US_ETF_MAP[s_choice]]
                            market_mode = "US"
                        else:
                            selected_tickers = list(df_etf[df_etf['Sector'] == s_choice].itertuples(index=False, name=None))
                            market_mode = "HK"

        # ===============================================
        # 共通的雷達掃描與除錯日誌
        # ===============================================
        if btn_radar and selected_tickers:
            st.info(f"🚀 啟動極致穩定雷達 ({len(selected_tickers)} 隻) | 模式: {st.session_state.run_mode}...")
            
            status_text = st.empty()
            pb = st.progress(0)
            
            results = []; sl_list = []; debug_errors = []
            is_single_mode = (st.session_state.target == 'SINGLE')
            fetch_period = "5y" if st.session_state.run_mode == 'STRONG_WEEKLY' else "2y"
            
            for i, (t, sec) in enumerate(selected_tickers):
                pb.progress((i+1)/len(selected_tickers))
                status_text.markdown(f"**📡 正在實時分析:** `{t}` ({i+1}/{len(selected_tickers)})")
                
                try:
                    df = smart_fetch(t, period=fetch_period)
                    if not df.empty and len(df) > 200:
                        if is_ath_mode and (df['Close'].iloc[-1] / df['High'].tail(252).max()) < 0.93: 
                            if not is_single_mode: continue
                        if check_stop_loss(df): sl_list.append(t)
                        
                        if st.session_state.run_mode in ['TIANWAI', 'TIANWAI_RS']:
                            is_rs_mode = (st.session_state.run_mode == 'TIANWAI_RS')
                            if is_rs_mode: res_df = run_tianwai_feixian_rs(df)
                            else: res_df = run_tianwai_feixian(df)
                            
                            latest = res_df.iloc[-1]
                            
                            if latest['天外飛仙_狀態'] > 0:
                                day_num = int(latest.get('起爆日數', 0))
                                
                                if latest['天外飛仙_狀態'] == 1: status_txt = f"[🚀 起爆(1-3日)] ({day_num})"
                                elif latest['天外飛仙_狀態'] == 2: status_txt = f"[🐢 沉底(4-10日)] ({day_num})"
                                else: status_txt = "[🔥 SCTR狂暴突破]"
                                
                                results.append({
                                    'Ticker': t.replace(".HK", ""),
                                    'Sector': sec,
                                    'Status': status_txt,
                                    'Score': round(latest['霸王總分'], 1),
                                    'RawPower': round(latest['Power'], 2),
                                    'Penalty': 0,
                                    'EMA10': round(latest['EMA10'], 2),
                                    'Bias': round(latest['Bias'], 1),
                                    'RS': round(latest['RS'], 1),
                                    'EJ': round(latest['EJ'], 3),
                                    'SE': round(latest['SE'], 2),
                                    'Power': round(latest['Vol_Ratio'], 1),
                                    'OBV': '狀態 1' if latest['天外飛仙_狀態'] == 1 else '狀態 2',
                                    'Icons': latest.get('天外飛仙_標籤', ''),
                                    'IsDead': False,
                                    'SCTR_Score': latest.get('SCTR_Score', 0) if is_rs_mode else None,
                                    'Is_True_Dragon': latest.get('真龍_標記', False) if is_rs_mode else False
                                })
                        elif st.session_state.run_mode == 'HARDPENNY':
                            res = run_hardpenny_logic(df, t, sec)
                            if res: results.append(res)
                        else:
                            res = scan_dragon_logic(df, t, sec, market_mode, mode=st.session_state.run_mode, force_return=is_single_mode, vcp_52w=vcp_52w, vcp_ath=is_ath_mode)
                            if res:
                                res['Status'] = f"[{res['Status']}]"
                                results.append(res)
                except Exception as e:
                    if len(debug_errors) < 5: debug_errors.append(f"{t}: {str(e)}")
            
            pb.empty()
            status_text.empty()
            
            if results:
                sector_counts = {}
                for r in results:
                    if not r.get('IsDead'):
                        sec = r['Sector']
                        sector_counts[sec] = sector_counts.get(sec, 0) + 1
                
                if st.session_state.run_mode == 'HARDPENNY':
                    results = sorted(results, key=lambda x: x['RawScore'], reverse=False)
                else:
                    results = sorted(results, key=lambda x: x['Score'], reverse=True)
                
                for r in results:
                    if not r.get('IsDead') and sector_counts.get(r['Sector'], 0) >= 3:
                        if "📊" not in r['Icons'] and st.session_state.run_mode != 'HARDPENNY': 
                            r['Icons'] += " | 📊板塊共振"
                
                st.session_state.dragon_results = results
                st.session_state.sl_list = sl_list
                
                try:
                    with open(MEMORY_FILE, 'w', encoding='utf-8') as f:
                        json.dump({'results': results, 'sl_list': sl_list}, f, ensure_ascii=False)
                except Exception as e: st.error(f"儲存記憶失敗: {e}")

                if is_single_mode: st.session_state.force_chart_ticker = selected_tickers[0][0]
                
                st.success("✅ 穩定掃描完成！結果已自動封裝入記憶體，唔會再消失！")
                time.sleep(0.5)
                st.rerun() 
            else: 
                st.warning("💤 萬人坑內無生還者。(報告統帥，今日大市無股票符合你嚴格嘅要求！)")
                if debug_errors:
                    with st.expander("🔍 點擊查看前 5 隻股票分析失敗原因（Debug 日誌）："):
                        for err in debug_errors: st.write(f"- {err}")

        # ===============================================
        # 顯示卡片結果區 (完美解決 Markdown 縮排 Bug 版)
        # ===============================================
        if st.session_state.get('dragon_results'):
            if st.session_state.get('sl_list'):
                st.markdown(f"<div class='bear-warning'>🛡️ 戰損置頂: {' | '.join(st.session_state.sl_list)} 跌穿 10-EMA！</div>", unsafe_allow_html=True)
            
            st.write("---")
            if st.session_state.scan_mode not in ['TIANWAI', 'HARDPENNY', 'TIANWAI_RS']:
                col_f1, col_f2 = st.columns([1, 1])
                with col_f1: show_n_shape_only = st.toggle("🔍 只顯示 🪃 N字突破 (今日/昨日剛破頂)")
                with col_f2: show_n_test_only = st.toggle("🔍 只顯示 🎯 N字回測成功 (回踩關鍵位企穩)")
            else:
                show_n_shape_only, show_n_test_only = False, False
            
            st.write("---")
            for r in st.session_state.dragon_results:
                if show_n_shape_only and "🪃" not in r['Icons']: continue 
                if show_n_test_only and "🧱" not in r['Icons']: continue 
                border_color = "#FF4B4B" if r.get('IsDead') else "#00FFCC"
                
                if st.session_state.scan_mode == 'HARDPENNY':
                    card_html = (
                        f"<div class='dragon-card' style='border-left: 5px solid {border_color};'>"
                        f"<div style='font-size:1.3rem;font-weight:bold;color:#FFFFFF;'>{r['Status']} {r['Ticker']} <span style='color:#00FFCC;'>({r['Sector']})</span></div>"
                        f"<div class='data-row'><b>糾纏度評分: {r['Score']}</b> | <b style='color:#FF9900;'>3個月回報: {r.get('RawPower', 0)}% 🔥</b> | <span style='color:#FF4B4B; font-weight:bold;'>🛑 止損(10-EMA): ${r['EMA10']}</span> | Bias: {r['Bias']}%<br>"
                        f"📈 RS: {r['RS']} | 🔋 ADR均幅: {r['EJ']}% | ⚡ 偏離200MA: {r['SE']}% | 🔥 50日均成交: ${r['Power']}M | 📊 OBV: {r.get('OBV', 'N/A')}</div></div>"
                    )
                    st.markdown(card_html, unsafe_allow_html=True)
                
                elif st.session_state.scan_mode == 'TIANWAI_RS':
                    sctr = r.get('SCTR_Score', 0)
                    is_dragon = r.get('Is_True_Dragon', False)
                    sctr_color = "#FFD700" if sctr >= 90 else "#00FFCC"
                    
                    dragon_html = f"<span style='color: #FFD700; font-size: 1.6rem; font-weight: 900; margin-left:10px; text-shadow: 0 0 10px #FFD700;'>👑真龍</span>" if is_dragon else ""
                    display_icons = r['Icons'].replace("👑真龍 | ", "").replace("👑真龍", "")
                    
                    card_html = (
                        f"<div class='dragon-card' style='border-left: 5px solid {border_color};'>"
                        f"<div style='font-size:1.3rem;font-weight:bold;color:#FFFFFF; display:flex; align-items:center; flex-wrap:wrap;'>"
                        f"<span>{r['Status']} {r['Ticker']}</span> <span style='color:#00FFCC; margin-left:5px; margin-right:15px;'>({r['Sector']})</span>"
                        f"<span style='color:{sctr_color}; font-size:1.5rem; font-weight:bold;'>SCTR: {sctr}</span>{dragon_html}</div>"
                        f"<div style='font-size:1.1rem; font-weight:bold; color:#FFD700; margin-top:5px;'>{display_icons}</div>"
                        f"<div class='data-row'><b>戰術總分: {r['Score']}分</b> | <b style='color:#FF9900;'>原始戰力: {r.get('RawPower', 0)} 🔥</b> | <span style='color:#FF4B4B; font-weight:bold;'>🛑 止損(10-EMA): ${r['EMA10']}</span> | Bias: {r['Bias']}%<br>"
                        f"📈 RS: {r['RS']} | 🔋 EJ: {r['EJ']} | ⚡ SE: {r['SE']} | 🔥 買盤力: {r['Power']}x | 📊 OBV: {r.get('OBV', 'N/A')}</div></div>"
                    )
                    st.markdown(card_html, unsafe_allow_html=True)

                else:
                    card_html = (
                        f"<div class='dragon-card' style='border-left: 5px solid {border_color};'>"
                        f"<div style='font-size:1.3rem;font-weight:bold;color:#FFFFFF;'>{r['Status']} {r['Ticker']} <span style='color:#00FFCC;'>({r['Sector']})</span> | <span style='color:#FFD700;'>{r['Icons']}</span></div>"
                        f"<div class='data-row'><b>戰術總分: {r['Score']}分</b> | <b style='color:#FF9900;'>原始戰力: {r.get('RawPower', 0)} 🔥</b> | <b style='color:#FF4B4B;'>扣分: {r.get('Penalty', 0)} 🛑</b> | <span style='color:#FF4B4B; font-weight:bold;'>🛑 止損(10-EMA): ${r['EMA10']}</span> | Bias: {r['Bias']}%<br>"
                        f"📈 RS: {r['RS']} | 🔋 EJ: {r['EJ']} | ⚡ SE: {r['SE']} | 🔥 買盤力: {r['Power']}x | 📊 OBV: {r.get('OBV', 'N/A')}</div></div>"
                    )
                    st.markdown(card_html, unsafe_allow_html=True)

        # ===============================================
        # 全黑戰術圖表繪製
        # ===============================================
        chart_t = None
        if st.session_state.get('dragon_results'):
            st.write("---")
            chart_t = st.selectbox("🎯 查看 X 光戰術圖", [r['Ticker'] for r in st.session_state.dragon_results])
        elif st.session_state.target == 'SINGLE' and hasattr(st.session_state, 'force_chart_ticker'):
            chart_t = st.session_state.force_chart_ticker

        if chart_t:
            with st.spinner("正在繪製全黑戰術圖表..."):
                try:
                    fetch_t = chart_t + ".HK" if str(chart_t).isdigit() else chart_t
                    df_c = smart_fetch(fetch_t, period="6mo")
                    if not df_c.empty:
                        ema10 = df_c['Close'].ewm(span=10, adjust=False).mean()
                        dates_chart = df_c.index.strftime('%Y-%m-%d').tolist()
                        
                        fig = make_subplots(rows=5, cols=1, shared_xaxes=True, row_heights=[0.45, 0.1, 0.2, 0.15, 0.1], vertical_spacing=0.02)
                        
                        fig.add_trace(go.Candlestick(x=dates_chart, open=df_c['Open'], high=df_c['High'], low=df_c['Low'], close=df_c['Close'], name="K線"), row=1, col=1)
                        fig.add_trace(go.Scatter(x=dates_chart, y=df_c['Close'].rolling(50).mean(), mode='lines', name='50MA', line=dict(color='yellow', width=1.5)), row=1, col=1)
                        fig.add_trace(go.Scatter(x=dates_chart, y=ema10, name="10 EMA", line=dict(color='orange', width=2, dash='dot')), row=1, col=1)
                        
                        recent_high = df_c['High'].tail(20).max()
                        fig.add_hline(y=recent_high, line_dash="dash", line_color="#00FFCC", annotation_text=f"🎯 買入點: ${recent_high:.2f}", annotation_position="top right", annotation_font=dict(color="white", size=13), row=1, col=1)
                        
                        counts, bins = np.histogram(df_c['Close'], bins=30, weights=df_c['Volume'])
                        max_c = max(counts) if len(counts) > 0 and max(counts) > 0 else 1
                        hvn_p = (bins[np.argmax(counts)] + bins[np.argmax(counts)+1]) / 2
                        stop_loss = hvn_p * 0.985
                        fig.add_hline(y=stop_loss, line_dash="solid", line_color="#FF4B4B", annotation_text=f"🛑 重貨止損: ${stop_loss:.2f}", annotation_position="bottom right", annotation_font=dict(color="white", size=13), row=1, col=1)
                        
                        fig.add_trace(go.Bar(y=(bins[:-1]+bins[1:])/2, x=counts, orientation='h', marker_color='rgba(136,136,136,0.4)', name='重貨區', hoverinfo='skip', xaxis='x6', yaxis='y1'))

                        v_colors = ['#00FF00' if df_c['Close'].iloc[i] >= df_c['Open'].iloc[i] else '#FF0000' for i in range(len(df_c))]
                        fig.add_trace(go.Bar(x=dates_chart, y=df_c['Volume'], marker_color=v_colors, name="成交量"), row=2, col=1)
                        
                        df_c['Vol50'] = df_c['Volume'].rolling(50).mean()
                        stars = df_c[(df_c['Close'] > df_c['Open']) & (df_c['Volume'] > df_c['Vol50'] * 1.5)]
                        if not stars.empty:
                            star_dates = stars.index.strftime('%Y-%m-%d').tolist()
                            fig.add_trace(go.Scatter(x=star_dates, y=stars['Volume'], mode='markers', marker=dict(symbol='star', size=14, color='#FFD700'), name='大戶星星'), row=2, col=1)

                        add_energy_subplots(fig, df_c, dates_chart, row_start=3)
                        
                        fig.update_layout(
                            template="plotly_dark", paper_bgcolor='#0e1117', plot_bgcolor='#111111', height=950, barmode='overlay', 
                            showlegend=False, hovermode='x unified', dragmode=False, xaxis_rangeslider_visible=False,
                            xaxis6=dict(overlaying='x1', anchor='y1', side='top', range=[0, max_c*1.5], showgrid=False, showticklabels=False), 
                            xaxis=dict(type='category', showticklabels=False), xaxis5=dict(type='category', title="日期")
                        )
                        st.plotly_chart(fig, use_container_width=True, theme=None, config={'displayModeBar': True})
                    else:
                        st.warning(f"⚠️ 無法從 Yahoo Finance 取得 {fetch_t} 的圖表數據！")
                except Exception as e: st.error(f"繪圖出錯: {e}")

elif operation_mode == "📊 究極資產拔河龍虎榜":
    from core_logic import AssetRanker
    
    st.markdown("<h1 style='text-align:center; color:#FFD700;'>🔥 全宇宙資金流相對強度矩陣</h1>", unsafe_allow_html=True)
    st.markdown("<p style='text-align:center; color:#888;'>動態監控大戶資金移防，自動派發 19+2 大情報公仔 🦅🔋⚔️⚡</p>", unsafe_allow_html=True)
    st.write("---")

    with st.expander("📖 爺爺的全公仔情報大滿貫說明書 (按此展開睇秘笈)", expanded=False):
        st.markdown("""
        <div style='background-color:#111111; padding: 20px; border-radius: 12px; border: 1px solid #333; line-height:1.8;'>
            <h3 style='color:#FFD700; margin-top:0;'>📊 龍虎榜基礎動力（Rank & Volume）</h3>
            <ul style='color:#ccc; list-style-type: none; padding-left: 0;'>
                <li><b>🟢 ▲ :</b> 排名大幅急升，大戶正在瘋狂搶入！（美股戰區≥50位，港股戰區≥30位）</li>
                <li><b>🔵 ▼ :</b> 排名大幅下跌（下跌 ≥ 30名），資金正在撤離，萬人坑勿近！</li>
                <li><b>🦅 :</b> 長線王者！代表該股處於全市場 200 日長線回報嘅前 10%！</li>
                <li><b>[1.5x 🔋] :</b> 動能增加，成交量大過平時 1.5 倍，主力引擎開始熱。</li>
                <li><b>[3.0x 🔋🔋] :</b> 極致爆量！成交量大過平時 3 倍，大戶準備強力噴射！</li>
            </ul>
        </div>
        """, unsafe_allow_html=True)
    st.write("---")

    col1, col2 = st.columns([2, 1])
    with col1:
        target_category = st.selectbox("📍 選擇意向掃描戰區", ["📦 美股 ETF (~360隻)", "📦 港股 ETF (139隻)", "🇭🇰 港股個股 (659隻)", "🇺🇸 美股精選 (576隻)", "🇺🇸 美股大藍籌 (500隻)", "🏭 美股選定行業 (1029隻)"])
    with col2:
        lookback_str = st.selectbox("⏳ 設定戰術時間窗", ["5天", "10天", "20天", "40天", "60天", "200天"])
        lookback_days = int(lookback_str.replace("天", ""))

    st.write("---")
    
    col_btn1, col_btn2 = st.columns(2)
    with col_btn1:
        run_normal = st.button("🚀 啟動熱力拔河掃描！", use_container_width=True)
    with col_btn2:
        run_hunt = st.button("🦅 啟動「爆升獵龍」超級特搜！", use_container_width=True)

    if run_normal or run_hunt:
        current_tickers = []
        if target_category == "📦 美股 ETF (~360隻)":
            for sub_list in US_ETF_MAP.values(): current_tickers.extend(sub_list)
            current_tickers = list(set(current_tickers)) 
        elif target_category == "📦 港股 ETF (139隻)":
            df_etf_list = fetch_github_list(HK_ETF_CSV_URL)
            if not df_etf_list.empty and 'Ticker' in df_etf_list.columns: current_tickers = df_etf_list['Ticker'].dropna().unique().tolist()
        elif target_category == "🇭🇰 港股個股 (659隻)":
            df_hk_list = fetch_github_list(HK_STOCK_CSV_URL)
            if not df_hk_list.empty and 'Ticker' in df_hk_list.columns: current_tickers = df_hk_list['Ticker'].dropna().unique().tolist()
        elif target_category == "🇺🇸 美股精選 (576隻)":
            try:
                df_csv = pd.read_csv("Market_Focus.csv")
                col = [c for c in df_csv.columns if c.lower() in ['ticker', 'symbol', '代號']][0]
                current_tickers = df_csv[col].dropna().unique().tolist()
            except: st.error("⚠️ 無法讀取 Market_Focus.csv")
        elif target_category == "🇺🇸 美股大藍籌 (500隻)":
            try:
                df_csv = pd.read_csv("SP500_Equities.csv")
                col = [c for c in df_csv.columns if c.lower() in ['ticker', 'symbol', '代號']][0]
                current_tickers = df_csv[col].dropna().unique().tolist()
            except: st.error("⚠️ 無法讀取 SP500_Equities.csv")
        elif target_category == "🏭 美股選定行業 (1029隻)":
            for sub_list in US_STOCK_MAP.values(): current_tickers.extend(sub_list)
            current_tickers = list(set(current_tickers))

        if current_tickers:
            with st.spinner(f"正在與納斯達克/港交所衛星連線，深度計算 {target_category} 的資金矩陣..."):
                df_result = AssetRanker.get_rank_and_acceleration(current_tickers, lookback_days, target_category)
                if df_result.empty:
                    st.error("⚠️ 運算失敗或回傳數據為空。請確保 Ticker 列表正確。")
                else:
                    if 'Display_Label' in df_result.columns:
                        df_result['Display_Label'] = df_result['Display_Label'].astype(str).str.replace("🚀", "🦅").str.replace("🎯", "⚔️")
                    
                    if run_hunt:
                        is_hk_target = "港股" in target_category
                        rank_threshold = 30 if is_hk_target else 50
                        df_result = df_result[(df_result['RVOL'] >= 1.5) & (df_result['Rank_Change'] >= rank_threshold)]
                        
                    if df_result.empty:
                        st.warning("⚠️ 依據過濾條件，目前戰區內無符合條件之異動股，大戶正在潛伏。")
                    else:
                        df_result = df_result.sort_values(by='Current_Return', ascending=True).reset_index(drop=True)
                        import plotly.express as px
                        fig = px.bar(df_result, x='Current_Return', y='Display_Label', orientation='h', color='Current_Return', color_continuous_scale='YlOrRd', text=df_result.apply(lambda row: f"{row['Current_Return']:.1f}%" if row['Ticker'] != '...' else "", axis=1))
                        
                        is_hk_target_str = "港股" in target_category
                        title_text = f"📊 {target_category} - {lookback_days}日 相對回報龍虎榜 (含大滿貫情報密碼)" if not run_hunt else f"🦅 「爆升獵龍」極速特搜榜 - {target_category} (港股≥30位/美股≥50位 + 🔋爆量)"
                        
                        fig.update_layout(title=title_text, title_font=dict(size=18, color="white"), plot_bgcolor='#0e1117', paper_bgcolor='#0e1117', font=dict(color="white"), yaxis=dict(showgrid=False, title="", tickfont=dict(size=11, color="white", family="Courier New"), fixedrange=True), xaxis=dict(showgrid=False, zeroline=True, zerolinecolor='#444', title="相對平均之超額回報 (Alpha %)", fixedrange=True), height=max(600, len(df_result) * 115), coloraxis_showscale=False, margin=dict(l=160, r=80, t=60, b=20), hovermode=False)
                        fig.update_traces(textposition='outside', textfont=dict(color='white', size=12), cliponaxis=False)
                        
                        st.plotly_chart(fig, use_container_width=True, config={'staticPlot': False, 'scrollZoom': False, 'doubleClick': False, 'displayModeBar': False, 'editable': False})
                        
                        if run_hunt:
                            desc_text = "港股區 (門檻: 🟢急升≥30名 + 🔋爆量)" if is_hk_target_str else "美股區 (門檻: 🟢急升≥50名 + 🔋爆量)"
                            st.success(f"✅ 【爆升獵龍特搜完成】成功為你定位出當前 {desc_text} 剛剛突然發動嘅核心資產！")
                        else:
                            st.success("✅ 全局相對強度矩陣部署完成！快去尋找大魔王吧！")
        else: st.warning("⚠️ 標的名單為空，無法執行掃描。")

elif operation_mode == "💰 大戶資金流透視 (福德金字塔)":
    from core_logic import scan_fude_logic
    
    st.markdown("""
        <style>
        .stApp { background-color: #000000 !important; }
        .fude-card-ind { background-color: #050505 !important; border: 2px solid; border-radius: 12px; padding: 25px; margin-bottom: 30px; box-shadow: 0 4px 20px rgba(0,0,0,1); }
        .fude-title { font-size: 1.5rem; font-weight: 900; margin-bottom: 15px; border-bottom: 1px solid #333; padding-bottom: 10px; display: flex; justify-content: space-between; align-items: center; }
        .fude-table { width: 100%; color: #ddd; font-size: 1.1rem; border-collapse: collapse; margin-bottom: 20px; }
        .fude-table th { text-align: left; padding: 10px 0; border-bottom: 2px solid #555; color: #aaa; font-weight: normal; }
        .fude-table td { padding: 12px 0; border-bottom: 1px solid #222; }
        .fude-table th:nth-child(2), .fude-table th:nth-child(3), .fude-table th:nth-child(4) { text-align: right; }
        .fude-table td:nth-child(2), .fude-table td:nth-child(3), .fude-table td:nth-child(4) { text-align: right; font-weight: bold; }
        .val-pos { color: #00FFCC !important; }
        .val-neg { color: #FF4B4B !important; }
        .pulse-label { font-size: 0.95rem; color: #888; text-align: right; margin-top: 5px; margin-bottom: 20px; font-weight: bold; }
        </style>
    """, unsafe_allow_html=True)

    st.markdown("<h1 style='text-align:center; color:#FFD700;'>💰 大戶資金流透視 (福德金字塔)</h1>", unsafe_allow_html=True)
    st.markdown("""
    <div style='background-color:#111; padding:15px; border-radius:10px; border-left: 5px solid #FFD700; margin-bottom: 20px;'>
        <h3 style='color:#FFD700; margin-top:0;'>⛩️ 華爾街大鱷模擬器 (無米煮飯量價版)</h3>
        <p style='color:#ddd; margin-bottom:0;'>透過 Yahoo 數據進行深度解構，拆解 <b>20日(熱錢) / 60日(底氣) / 200日(福德家底)</b>。<br>
        結合 Force Index、CMF 及 VWAP 偏離度，透視大戶暗中吸籌與派發嘅真實意向。</p>
    </div>
    """, unsafe_allow_html=True)

    col_input, col_btn = st.columns([3, 1])
    with col_input: ticker = st.text_input("輸入股票代號 (例: NVDA, 0700.HK, TSLA)", "NVDA").upper().strip()
    with col_btn: st.write("<br>", unsafe_allow_html=True); run_scan = st.button("📡 透視資金底牌", use_container_width=True)

    if run_scan or ticker:
        with st.spinner(f"⏳ 爺爺正在為你潛入深網，計算 {ticker} 嘅福德家底..."):
            try:
                df = smart_fetch(ticker, period="2y")
                fude_data = scan_fude_logic(df, ticker)
                
                if not fude_data:
                    st.error("⚠️ 數據不足 200 日，無法計算 200日線及重貨區！請轉換其他上市超過一年嘅股票。")
                else:
                    poc_price = fude_data["POC_Price"]; curr_c = fude_data["Current_Price"]; fude_col = fude_data["FColor"]; fude_lvl = fude_data["Fude_Level"]; fude_desc = fude_data["Fude_Desc"]; tags = fude_data["Tags"]; plot_df = fude_data["Plot_Data"]
                    
                    st.markdown(f"### {ticker} 資金命格解讀")
                    c1, c2, c3 = st.columns(3)
                    with c1: st.markdown(f"<div class='dragon-card' style='border-color:{fude_col}; height:220px; display:flex; flex-direction:column; justify-content:center;'><div style='font-size:1.2rem;color:#ccc;'>⛩️ 福德等級 (200日)</div><div style='font-size:2rem; font-weight:bold; color:{fude_col}; margin-top:10px;'>{fude_lvl}</div><div style='font-size:1rem; color:#ccc; margin-top:10px;'>{fude_desc}</div></div>", unsafe_allow_html=True)
                    with c2:
                        poc_status = "✅ 股價已突圍大本營" if curr_c > poc_price else "⚠️ 處於天量套牢區之下"
                        poc_color = "#00FFCC" if curr_c > poc_price else "#FF4B4B"
                        st.markdown(f"<div class='dragon-card' style='border-color:#BC13FE; height:220px; display:flex; flex-direction:column; justify-content:center;'><div style='font-size:1.2rem;color:#ccc;'>🎯 過去200日成交大本營 (POC)</div><div style='font-size:3rem; font-weight:900; color:#BC13FE;'>${poc_price:.2f}</div><div style='font-size:1.1rem; font-weight:bold; color:{poc_color}; margin-top:5px;'>{poc_status}</div></div>", unsafe_allow_html=True)
                    with c3: st.markdown(f"<div class='dragon-card' style='border-color:#00FFFF; height:220px; display:flex; flex-direction:column; justify-content:center;'><div style='font-size:1.2rem;color:#ccc;'>🔍 大戶底氣標籤</div><div style='display:flex; flex-wrap:wrap; gap:10px; justify-content:center; margin-top:15px; font-weight:bold;'>{' '.join(tags) if tags else '無明顯大戶特徵'}</div></div>", unsafe_allow_html=True)
                    
                    if 'Net_Flow' not in plot_df.columns:
                        plot_df['Net_Flow'] = plot_df['Volume'] * plot_df['Close'] * np.where(plot_df['Close'] > plot_df['Close'].shift(1).fillna(plot_df['Close']), 1, -1)
                    if 'OBV_Daily' not in plot_df.columns:
                        plot_df['OBV_Daily'] = np.sign(plot_df['Close'].diff()).fillna(0) * plot_df['Volume']

                    def get_val(key, default=0.0): return fude_data.get(key, default)
                    
                    f20 = get_val('Flow_20_val'); p20 = get_val('Flow_20_pct')
                    f60 = get_val('Flow_60_val'); p60 = get_val('Flow_60_pct')
                    f200 = get_val('Flow_200_val'); p200 = get_val('Flow_200_pct')
                    
                    o20 = get_val('OBV_20_val'); p20_o = get_val('OBV_20_pct')
                    o60 = get_val('OBV_60_val'); p60_o = get_val('OBV_60_pct')
                    o200 = get_val('OBV_200_val'); p200_o = get_val('OBV_200_pct')
                    
                    ej20 = get_val('EJ_20', 50.0); ej20_p = get_val('EJ_20_pct')
                    ej60 = get_val('EJ_60', 50.0); ej60_p = get_val('EJ_60_pct')
                    ej200 = get_val('EJ_200', 50.0); ej200_p = get_val('EJ_200_pct')
                    
                    se20 = get_val('SE_20', 50.0); se20_p = get_val('SE_20_pct')
                    se60 = get_val('SE_60', 50.0); se60_p = get_val('SE_60_pct')
                    se200 = get_val('SE_200', 50.0); se200_p = get_val('SE_200_pct')
                    
                    c20 = get_val('Conc_20'); c20_p = get_val('Conc_20_pct')
                    c60 = get_val('Conc_60'); c60_p = get_val('Conc_60_pct')
                    c200 = get_val('Conc_200'); c200_p = get_val('Conc_200_pct')
                    
                    s20 = get_val('Shares_20'); s60 = get_val('Shares_60'); s200 = get_val('Shares_200')

                    st.write("---")
                    st.markdown(f"### 🌊 獨家解密：主力資金池透視 (5大獨立指標)", unsafe_allow_html=True)

                    def fmt(val): return f"{'+' if val>0 else ''}${val/1e8:.1f}億" if abs(val)>=1e8 else (f"{'+' if val>0 else ''}${val/1e6:.1f}M" if abs(val)>=1e6 else f"{'+' if val>0 else ''}${val:,.0f}")
                    def color_class(val): return "val-pos" if val >= 0 else "val-neg"
                    
                    def get_pulse_fig(pulse_vals, height=100):
                        if len(pulse_vals) == 0: pulse_vals = [0]
                        colors = ['#00FFCC' if v >= 0 else '#FF4B4B' for v in pulse_vals]
                        fig_p = go.Figure(go.Bar(x=list(range(len(pulse_vals))), y=pulse_vals, marker_color=colors, hoverinfo='skip'))
                        fig_p.update_layout(height=height, margin=dict(l=0,r=0,t=0,b=0), paper_bgcolor='rgba(0,0,0,0)', plot_bgcolor='rgba(0,0,0,0)', xaxis=dict(visible=False, fixedrange=True), yaxis=dict(visible=False, fixedrange=True), showlegend=False, dragmode=False)
                        return fig_p

                    def draw_triad_bar(val, color):
                        lit = int((min(120, max(0, val))/120)*21)
                        html = "<div style='display:flex; gap:6px; margin-top: 15px; margin-bottom: 25px;'>"
                        for idx in range(21):
                            c_code = "#FF4B4B" if idx<6 else ("#FFD700" if idx<12 else color)
                            bg = c_code if idx < lit else '#222'
                            op = 1 if idx < lit else 0.3
                            html += f"<div style='width:25px; height:35px; background-color:{bg}; opacity:{op}; border-radius:4px;'></div>"
                        html += "</div>"
                        return html

                    # 1. EJ 錢流底氣 (雙層柱)
                    ej_c = "#00FFFF"
                    st.markdown(f"""
                    <div class='fude-card-ind' style='border-color:{ej_c};'>
                        <div class='fude-title' style='color:{ej_c};'><span>🔋 EJ 錢流底氣 (真金白銀版)</span></div>
                        <table class='fude-table'>
                            <tr><th>週期</th><th>實際吸金量</th><th>變化 %</th></tr>
                            <tr><td>20日底氣</td><td class='{color_class(f20)}'>{fmt(f20)}</td><td class='{color_class(p20)}'>{p20:+.1f}%</td></tr>
                            <tr><td>60日底氣</td><td class='{color_class(f60)}'>{fmt(f60)}</td><td class='{color_class(p60)}'>{p60:+.1f}%</td></tr>
                            <tr><td>200日底氣</td><td class='{color_class(f200)}'>{fmt(f200)}</td><td class='{color_class(p200)}'>{p200:+.1f}%</td></tr>
                        </table>
                        {draw_triad_bar(ej20, ej_c)}
                    </div>
                    """, unsafe_allow_html=True)
                    st.plotly_chart(get_pulse_fig(plot_df['Net_Flow'].tail(20).values), use_container_width=True, key="ej_pulse_20", config={'displayModeBar': True})
                    st.markdown(f"<div class='pulse-label' style='color:{ej_c};'>▲ 最近 20 天微觀錢流爆發</div>", unsafe_allow_html=True)
                    st.plotly_chart(get_pulse_fig(plot_df['Net_Flow'].tail(60).values), use_container_width=True, key="ej_pulse_60", config={'displayModeBar': True})
                    st.markdown(f"<div class='pulse-label' style='color:{ej_c};'>▲ 最近 60 天中線建倉軌跡</div><br>", unsafe_allow_html=True)

                    # 2. 短期能量 BAR (雙層柱)
                    se_c = "#FF00FF"
                    st.markdown(f"""
                    <div class='fude-card-ind' style='border-color:{se_c};'>
                        <div class='fude-title' style='color:{se_c};'><span>⚡ 短期能量 BAR</span></div>
                        <table class='fude-table'>
                            <tr><th>週期</th><th>能量數值</th><th>變化 %</th></tr>
                            <tr><td>20日動能</td><td class='val-pos'>{se20:.1f}%</td><td class='{color_class(se20_p)}'>{se20_p:+.1f}%</td></tr>
                            <tr><td>60日動能</td><td class='val-pos'>{se60:.1f}%</td><td class='{color_class(se60_p)}'>{se60_p:+.1f}%</td></tr>
                            <tr><td>200日動能</td><td class='val-pos'>{se200:.1f}%</td><td class='{color_class(se200_p)}'>{se200_p:+.1f}%</td></tr>
                        </table>
                        {draw_triad_bar(se20, se_c)}
                    </div>
                    """, unsafe_allow_html=True)
                    se_pulse_20 = plot_df['Close'].pct_change().tail(20).fillna(0).values * 100
                    se_pulse_60 = plot_df['Close'].pct_change().tail(60).fillna(0).values * 100
                    st.plotly_chart(get_pulse_fig(se_pulse_20), use_container_width=True, key="se_pulse_20", config={'displayModeBar': True})
                    st.markdown(f"<div class='pulse-label' style='color:{se_c};'>▲ 最近 20 天動能波幅</div>", unsafe_allow_html=True)
                    st.plotly_chart(get_pulse_fig(se_pulse_60), use_container_width=True, key="se_pulse_60", config={'displayModeBar': True})
                    st.markdown(f"<div class='pulse-label' style='color:{se_c};'>▲ 最近 60 天動能波幅</div><br>", unsafe_allow_html=True)

                    # 3. 資金總數 (Money Flow) (雙層柱)
                    flow_color = "#00FFCC" if f20 >= 0 else "#FF4B4B"
                    st.markdown(f"""
                    <div class='fude-card-ind' style='border-color:{flow_color};'>
                        <div class='fude-title' style='color:{flow_color};'><span>💰 資金總數 (Money Flow)</span></div>
                        <table class='fude-table'>
                            <tr><th>週期</th><th>總量</th><th>變化 %</th></tr>
                            <tr><td>20日總量</td><td class='{color_class(f20)}'>{fmt(f20)}</td><td class='{color_class(p20)}'>{p20:+.1f}%</td></tr>
                            <tr><td>60日總量</td><td class='{color_class(f60)}'>{fmt(f60)}</td><td class='{color_class(p60)}'>{p60:+.1f}%</td></tr>
                            <tr><td>200日總量</td><td class='{color_class(f200)}'>{fmt(f200)}</td><td class='{color_class(p200)}'>{p200:+.1f}%</td></tr>
                        </table>
                    </div>
                    """, unsafe_allow_html=True)
                    st.plotly_chart(get_pulse_fig(plot_df['Net_Flow'].tail(20).values), use_container_width=True, key="mf_pulse_20", config={'displayModeBar': True})
                    st.markdown(f"<div class='pulse-label' style='color:{flow_color};'>▲ 最近 20 天資金流向</div>", unsafe_allow_html=True)
                    st.plotly_chart(get_pulse_fig(plot_df['Net_Flow'].tail(60).values), use_container_width=True, key="mf_pulse_60", config={'displayModeBar': True})
                    st.markdown(f"<div class='pulse-label' style='color:{flow_color};'>▲ 最近 60 天資金流向</div><br>", unsafe_allow_html=True)

                    # 4. OBV 軌跡 (雙層柱)
                    obv_color = "#00FFCC" if o20 >= 0 else "#FF4B4B"; trend_str = "📈 流入" if o20 >= 0 else "📉 流出"
                    st.markdown(f"""
                    <div class='fude-card-ind' style='border-color:{obv_color};'>
                        <div class='fude-title' style='color:{obv_color};'><span>📈 OBV 籌碼軌跡</span><span>{trend_str}</span></div>
                        <table class='fude-table'>
                            <tr><th>週期</th><th>累積量</th><th>變化 %</th></tr>
                            <tr><td>20日累積量</td><td class='{color_class(o20)}'>{fmt(o20)}</td><td class='{color_class(p20_o)}'>{p20_o:+.1f}%</td></tr>
                            <tr><td>60日累積量</td><td class='{color_class(o60)}'>{fmt(o60)}</td><td class='{color_class(p60_o)}'>{p60_o:+.1f}%</td></tr>
                            <tr><td>200日累積量</td><td class='{color_class(o200)}'>{fmt(o200)}</td><td class='{color_class(p200_o)}'>{p200_o:+.1f}%</td></tr>
                        </table>
                    </div>
                    """, unsafe_allow_html=True)
                    st.plotly_chart(get_pulse_fig(plot_df['OBV_Daily'].tail(20).values), use_container_width=True, key="obv_pulse_20", config={'displayModeBar': True})
                    st.markdown(f"<div class='pulse-label' style='color:{obv_color};'>▲ 最近 20 天 OBV 變動</div>", unsafe_allow_html=True)
                    st.plotly_chart(get_pulse_fig(plot_df['OBV_Daily'].tail(60).values), use_container_width=True, key="obv_pulse_60", config={'displayModeBar': True})
                    st.markdown(f"<div class='pulse-label' style='color:{obv_color};'>▲ 最近 60 天 OBV 變動</div><br>", unsafe_allow_html=True)

                    # 5. 資金部署集中度 (加股數 + 雙層有紅綠柱)
                    conc_color = "#FF4B4B" if c20 > 35 else ("#FFD700" if c20 > 15 else "#00FFCC")
                    conc_note = "（突發買入或掟貨）" if c20 > 35 else ("（公開正常進出）" if c20 > 15 else "（隱密吸籌/派發）")
                    st.markdown(f"""
                    <div class='fude-card-ind' style='border-color:#BC13FE;'>
                        <div class='fude-title' style='color:#BC13FE;'><span>🎯 資金部署集中度</span><span style='color:{conc_color}; font-size:1.1rem;'>{conc_note}</span></div>
                        <table class='fude-table'>
                            <tr><th>週期</th><th>極值佔比</th><th>變化 %</th><th>估算股數</th></tr>
                            <tr><td>20日</td><td style='color:{conc_color};'>{c20:.1f}%</td><td class='{color_class(c20_p)}'>{c20_p:+.1f}%</td><td class='{color_class(s20)}'>{'+' if s20>0 else ''}{s20:,} 股</td></tr>
                            <tr><td>60日</td><td style='color:#FFF;'>{c60:.1f}%</td><td class='{color_class(c60_p)}'>{c60_p:+.1f}%</td><td class='{color_class(s60)}'>{'+' if s60>0 else ''}{s60:,} 股</td></tr>
                            <tr><td>200日</td><td style='color:#FFF;'>{c200:.1f}%</td><td class='{color_class(c200_p)}'>{c200_p:+.1f}%</td><td class='{color_class(s200)}'>{'+' if s200>0 else ''}{s200:,} 股</td></tr>
                        </table>
                        <div style='width:100%; background-color:#222; border-radius:10px; height:20px; margin-top:30px; margin-bottom:30px; border:1px solid #444;'>
                            <div style='width:{min(100, c20)}%; background-color:{conc_color}; height:100%; box-shadow:0 0 15px {conc_color}; border-radius:10px;'></div>
                        </div>
                    </div>
                    """, unsafe_allow_html=True)
                    st.plotly_chart(get_pulse_fig(plot_df['Net_Flow'].tail(20).values), use_container_width=True, key="conc_pulse_20", config={'displayModeBar': True})
                    st.markdown("<div class='pulse-label' style='color:#BC13FE;'>▲ 最近 20 天集中度分布 (綠=買, 紅=賣)</div>", unsafe_allow_html=True)
                    st.plotly_chart(get_pulse_fig(plot_df['Net_Flow'].tail(60).values), use_container_width=True, key="conc_pulse_60", config={'displayModeBar': True})
                    st.markdown("<div class='pulse-label' style='color:#BC13FE;'>▲ 最近 60 天集中度分布 (綠=買, 紅=賣)</div><br>", unsafe_allow_html=True)

                    # --- 原裝戰術圖表保留區 ---
                    st.write("---")
                    st.markdown("### 📊 摩訶釋達・量價拆解戰術圖 (Force Index & VWAP)")
                    
                    dates = plot_df.index.strftime('%Y-%m-%d')
                    fig = make_subplots(rows=3, cols=1, shared_xaxes=True, row_heights=[0.5, 0.25, 0.25], vertical_spacing=0.03, subplot_titles=("股價與大鱷成本 (VWAP 20) + 🦈 強勢吸籌", "三層福德動力 (Force Index)", "中短線底氣流向 (CMF)"))
                    
                    fig.add_trace(go.Candlestick(x=dates, open=plot_df['Open'], high=plot_df['High'], low=plot_df['Low'], close=plot_df['Close'], name="K線"), row=1, col=1)
                    fig.add_trace(go.Scatter(x=dates, y=plot_df['VWAP_20'], mode='lines', name='VWAP (20日成本)', line=dict(color='orange', width=2, dash='dot')), row=1, col=1)
                    fig.add_hline(y=poc_price, line_dash="solid", line_color="#BC13FE", annotation_text=f"📌 POC 密集區: ${poc_price:.2f}", annotation_position="top left", annotation_font=dict(color="white", size=13), row=1, col=1)
                    
                    for i in range(len(plot_df)):
                        if plot_df['RVOL'].iloc[i] > 1.5 and plot_df['Close'].iloc[i] > plot_df['VWAP_20'].iloc[i] and plot_df['Close'].iloc[i] > plot_df['Open'].iloc[i]:
                            fig.add_annotation(x=dates[i], y=plot_df['Low'].iloc[i], text="🦈", showarrow=True, ax=0, ay=30, arrowcolor="#00FFCC", font=dict(size=18), row=1, col=1)

                    max_20 = max(plot_df['Merit_20'].abs().max(), 1)
                    max_60 = max(plot_df['Merit_60'].abs().max(), 1)
                    max_200 = max(plot_df['Merit_200'].abs().max(), 1)
                    norm_20 = plot_df['Merit_20'] / max_20
                    norm_60 = plot_df['Merit_60'] / max_60
                    norm_200 = plot_df['Merit_200'] / max_200
                    
                    fig.add_trace(go.Scatter(x=dates, y=norm_20, mode='lines', name='熱錢 (20日)', line=dict(color='#FF4B4B', width=1.5)), row=2, col=1)
                    fig.add_trace(go.Scatter(x=dates, y=norm_60, mode='lines', name='底氣 (60日)', line=dict(color='#00FFCC', width=2)), row=2, col=1)
                    fig.add_trace(go.Scatter(x=dates, y=norm_200, mode='lines', name='福德 (200日)', line=dict(color='#FFD700', width=3)), row=2, col=1)
                    fig.add_hline(y=0, line_dash="dash", line_color="rgba(255,255,255,0.3)", row=2, col=1)
                    
                    fig.add_trace(go.Scatter(x=dates, y=plot_df['CMF_20'], mode='lines', name='CMF (20日)', line=dict(color='#FF00FF', width=1.5)), row=3, col=1)
                    fig.add_trace(go.Scatter(x=dates, y=plot_df['CMF_60'], mode='lines', name='CMF (60日)', line=dict(color='white', width=2)), row=3, col=1)
                    fig.add_hline(y=0, line_dash="dash", line_color="rgba(255,255,255,0.3)", row=3, col=1)
                    
                    fig.update_layout(template="plotly_dark", paper_bgcolor='#0e1117', plot_bgcolor='#0e1117', height=950,
                                      hovermode='x unified', dragmode=False, xaxis_rangeslider_visible=False,
                                      xaxis=dict(type='category', showticklabels=False),
                                      xaxis2=dict(type='category', showticklabels=False),
                                      xaxis3=dict(type='category', showspikes=True, spikemode='across', spikecolor="white", spikethickness=1),
                                      legend=dict(orientation="h", yanchor="bottom", y=1.02, xanchor="right", x=1, font=dict(color="white", size=13)))
                    
                    st.plotly_chart(fig, use_container_width=True, config={'displayModeBar': True})
                    
            except Exception as e:
                st.error(f"⚠️ 計算過程發生錯誤: {e}")
