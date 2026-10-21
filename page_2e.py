import streamlit as st
import yfinance as yf
import pandas as pd
import plotly.graph_objects as go
from plotly.subplots import make_subplots

# ===================================================
# 🗄️ 核心成份股字典 (全量覆蓋 1,127 隻，壓縮極速版)
# ===================================================
DIA_TICKERS = "AAPL,AMGN,AXP,BA,CAT,CRM,CSCO,CVX,DIS,DOW,GS,HD,HON,IBM,INTC,JNJ,JPM,KO,MCD,MMM,MRK,MSFT,NKE,PG,TRV,UNH,V,VZ,WMT,AMZN"
QQQ_TICKERS = "CSCO,BIIB,ADP,ASML,AVGO,TXN,SNPS,GFS,CDNS,DLTR,WBD,CHTR,ROST,PYPL,META,SPLK,MDB,NET,DASH,KHC,ORLY,VRTX,TSLA,PANW,PLTR,COST,PEP,ON,HON,MELI,EXC,CPRT,LULU,NVDA,BKR,CTSH,FAST,MNST,MDLZ,CCEP,REGN,ZM,SIRI,AMAT,MCHP,EA,GOOG,CTAS,CSGP,INTU,INTC,WDAY,AMD,QCOM,AAPL,OKTA,MAR,KLAC,NXPI,CRWD,U,BKNG,VRSK,DDOG,TEAM,FTNT,ADI,AEP,ISRG,FANG,CMCSA,MRNA,ILMN,ROKU,PDD,ZS,MSFT,GOOGL,XEL,DXCM,EBAY,CSX,AMZN,AMGN,LRCX,GILD,PAYX,ODFL,NFLX,TMUS,SBUX,TTWO,KDP,WBA,SNOW,PCAR,DOCU"
SPY_TICKERS = "PH,CSCO,MU,NVR,AMT,TDG,AVGO,GD,AWK,SNPS,BBAI,DISCA,IBM,CTLT,CDNS,SNI,HSY,LDOS,CPB,LW,AIG,SYK,META,VTR,HIG,AZO,GRMN,ASTS,FISV,BX,FCX,RS,IFF,PNW,DGX,LIN,LH,JNJ,WEC,NKE,BBY,XLNX,RXRX,ZTS,SBNY,CTVA,DRI,KR,MELI,WSM,TSCO,CPRT,LUMN,SHLS,BKR,LHX,CTSH,EMN,FAST,DLR,HPQ,ABBV,PRDO,WYNN,VAR,COG,RUN,AMAT,PRGO,DTE,DIS,LVS,PEG,WLTW,INTU,BMY,AMD,NWS,PVH,LRN,KKR,RL,LOW,NRG,BSX,JKHY,CVX,BWA,TAP,NXPI,RF,BKSY,KMX,SWK,PKG,VRSK,UPS,IP,LEG,MS,MTD,RJF,PPG,AEP,PRU,TFX,VMC,CROX,DPZ,J,UNH,FSLR,HPE,CLX,FANG,AMCR,HAL,CMCSA,CGNX,ADSK,SHW,QRVO,PWR,KMI,AON,PG,ESS,GS,ANSS,EQR,LKQ,WRK,PNR,EVRG,TMUS,SBAC,HCA,EWBC,GLW,CERN,COO,FFIV,GM,APD,AEM,PXD,SCCO,ETR,NOW,PFG,ROL,SYY,GPN,GOLD,HD,BIO,VFC,CHTR,STE,BLK,CELH,DOV,WM,TRMB,ALK,X,CINF,MXIM,KEYS,ADM,TROW,WELL,ZION,NCLH,TPR,MAA,MRO,TSLA,COST,HII,UNP,MMM,L,LYV,MTB,HUM,URI,APP,MO,DOW,CAH,LULU,KRE,TEL,KEY,LEN,ABT,GE,MIDD,PAYC,CAG,DG,K,SCHW,PM,UNM,FMC,MPC,ABNB,ISGN,HRL,MCHP,MET,BDX,YUM,DISCK,AAPL,CLF,WMT,WST,COF,DFS,WU,XRAY,PKI,STLD,WING,CB,IPGP,UHS,OTIS,SNA,EFX,HBI,TMO,FTI,DVA,REG,SQ,BAX,APTV,WDC,V,HUT,MRNA,SYF,HOLX,MSFT,VLO,FE,EW,EBAY,SEDG,CNC,BMRN,AMGN,ELF,WY,LRCX,VRSN,GPC,PAYX,NTR,MARA,CMI,HST,SPG,SBUX,LMT,FBHS,AVY,STZ,EXPE,COUR,BA,AMP,TFC,BEN,PPL,GNRC,MSCI,WBA,GIS,AFRM,C,NSC,FIS,OKE,IVZ,ATO,CHRW,IR,BIIB,UAA,BF-B,TXN,MKTX,RE,MOS,IQV,ETN,CNP,MSI,MMC,MAS,ROST,LUV,PYPL,ABG,TJX,PNC,TYL,KO,APO,PL,KHC,COP,AKAM,VRTX,OSK,TWTR,DXC,ALB,PEP,INFO,NOV,PATH,F,EXC,OXY,CFG,IPG,CAT,JBHT,FB,NVDA,ENPH,MNST,MDLZ,FRT,MRK,ULTA,VNO,SLB,EA,EOG,GOOG,CTAS,EXPD,NTAP,CHGG,TOL,WAT,NLOK,UA,PSX,QCOM,CTXS,AI,ROP,SJM,CRM,EQIX,HES,MAR,KLAC,HLT,DRE,UDR,MCD,CE,FITB,SPCE,TER,XOM,CBRE,MCO,FRC,IRM,STT,ECL,FTNT,ADI,IEX,BXP,DHI,ORCL,RTX,NWL,ZBH,NWSA,TGT,ILMN,HBAN,CVS,SRE,AJG,WAB,TSN,SYM,CL,DXCM,IDXX,CRL,AMZN,AIV,NOC,SOUN,GILD,DISH,ITW,KIM,AAL,MKC,ODFL,AVB,PBCT,USB,CARR,NFLX,FOX,JNPR,ELV,MLM,CMG,STX,MDT,PCAR,UAL,ETSY,CZR,ACN,ADP,NI,AXP,DE,RKLB,MA,FTV,WFC,RCL,APH,DUK,SPGI,APA,HIVE,MCK,KEX,DLTR,HWM,MGM,BRK-B,ANF,JPM,TXT,TDY,PEAK,INCY,PFE,ORLY,DD,GPS,PSA,O,ADBE,PANW,ZBRA,DHR,VZ,TT,TWOU,COIN,AIZ,NUE,NTRS,GL,VTRS,CF,LB,HON,D,EL,CI,RIOT,ALGN,DVN,CCL,OMC,LNC,XYL,SWKS,GWW,BAC,REGN,WHR,NLSN,BLL,WMB,CMA,T"
IWM_TICKERS = "COHR,BJ,CVGI,CHRS,BLMN,AYI,BSGM,HBNC,GFS,HUD,HCI,CLSK,GLUE,CTLT,CRC,FPH,HSTM,HSY,COPX,GRP,CLH,FOSL,GAM,CPB,ESE,HSON,DNLI,GBX,CREE,CYTK,GTLS,HTBK,ARQT,GRMN,CLPR,FCX,CNK,CMRE,CREG,SWTX,GH,FIF,GSBC,HUBG,ADUS,CIT,CST,DSPG,CPAH,FTEK,CVSB,RXRX,EGF,CIVB,CHCO,EQC,AEIS,CWH,ENVA,FMNB,CNEX,CTVA,GMDA,CRI,FNKO,DRI,FLWS,APYX,GPI,HBM,CTOS,CYH,GNMK,GRTS,CTSH,BILL,HMSY,COLM,EML,EGHT,CSV,AAWW,BZFD,CHDN,CTRA,EAT,FCCY,FL,GTN,GHG,FR,DTE,GILT,ACVA,CVCY,DAIO,FOLD,FRPT,HIL,GPRO,GLPI,CPK,AZTA,ENZ,FATE,FPAY,FVE,BWA,EMP,FNCB,EEFT,BVS,DRH,FTFT,EDR,GWRE,CRNX,HWC,CZFS,GNTX,BRY,AMBC,EYPT,FACA,CNDT,CPE,APPF,CNM,FLGT,MNDY,CRVS,CROX,GORO,CWT,HE,HIBB,CLX,BTT,GEVO,GPK,AXON,AMKR,GIMO,FFG,CFFN,DIN,FENG,GNL,CTT,CLPS,RCRT,FPI,CNMD,GATX,CPIX,CYCC,FONR,CPSS,BLKB,HTGC,AMED,BIG,HBT,HMNF,EAF,DADA,GCBC,ACAD,BANR,CMC,CSOD,CYRX,HCA,DJCO,EXTR,FPA,IMVT,GLW,CURI,EOLS,AMBA,EBC,CNCE,GROW,FFIV,EGP,CUE,CWBC,FDBC,GFPA,FMBH,APPN,CLFD,AKRO,CHMG,CTMX,HSAI,FCN,DFRG,CRK,CTLP,GPN,CVI,FFNW,BANC,HD,FRO,HUBB,COMM,CELH,FULC,GMS,CINF,HOMB,CVLT,GNE,CYN,GOOD,FELE,FTR,CLDT,HMN,FCRD,ENTA,HAFC,CXW,HURC,BBIO,HOFT,ARCB,CRMD,APP,COGT,DSWG,GNK,CHMI,GDI,HLI,HEES,GLBE,BCO,INSM,CONN,ASAN,CXDC,HSKA,GCI,FSS,GOOS,CPLP,BPTH,CURO,FI,DRQ,DENN,FPF,HRL,GBCI,HASI,HURN,APLS,CRBG,CLNE,CLF,DXPE,DWSN,FIBK,BKD,COKE,FINW,CRDL,FSTR,GLT,GOLF,CWK,GTT,CSTA,BL,GMED,DVD,MEDP,FCCO,BMRE,DTC,GWGH,HA,BDC,COHU,DZZ,CUR,CVNA,WING,DDOG,FMAO,EPZM,CRCT,BLNK,EYE,FNWB,GRTX,FTAI,GLRE,APOG,CWEN,FCPT,DUOL,FBM,EZPW,EMCI,FET,HRC,CYRN,CVLY,ELY,FCF,CTCM,CYTO,CWAN,BHLB,BTI,DHIL,CRGY,EXLS,ABCB,RYTM,COTY,GBLI,FWRD,CRIS,CYTR,FORR,HVT,CSWI,HIMX,CUNB,HIHO,FLIR,ELF,GPC,GHC,ARWR,EBS,CULL,GAIA,HTBI,GPRE,HTLF,CPS,CMI,HST,FBRT,CSSE,GTY,CYAN,CVBF,COUR,SNOW,CPRI,GNRC,HRTX,DOCN,ENS,FCBC,GRA,CRNT,BNED,FMNI,CPAC,GTHX,CHRW,CMCO,CRTO,FDEF,GTE,HCSG,CLVT,FTDR,PTCT,CNFR,CRUS,AZZ,CHCT,HOPE,GIII,CNP,CHEF,FNB,FTHM,ECPG,CHRA,ENR,HLIO,GHM,BSET,CRBP,FBK,GWRS,ABG,BOOM,HIFS,HDS,NET,FLY,FLNT,FFBC,CYBN,CWST,GOGO,FUND,CSL,EDU,CUBI,ERII,GFF,DOX,ELLI,EMAN,CSTL,CSTR,FIGS,CVM,HILI,BANF,GRBK,CLW,FCFS,HWKN,FPAC,EGRX,CYXT,FC,CNO,CYBE,FTK,CRH,CHS,FIZZ,DGII,FUN,BLD,BKI,CZNC,FIX,GEOS,COLB,GERN,FOR,BOOT,CSS,GDEN,AMN,EE,HQY,FPRO,AXSM,EPC,CXM,FRT,GOSS,BRC,FTSV,CRZO,DCO,FCEL,FDP,CLS,FRPH,CTAS,CNXN,CPF,CHGG,CRKN,BRP,CVAC,CWCO,CHH,EGBN,FDS,EPAY,EB,DHC,CHRD,FAD,BCYC,CUB,HRTG,EEX,HMTV,EBSB,BSQR,CPSI,CUK,HMST,HZO,BXMT,CRY,FRC,CUBE,DMRC,FICO"

INDEX_COMPONENTS = {
    "S&P 500 (SPY)": SPY_TICKERS.split(","),
    "Nasdaq 100 (QQQ)": QQQ_TICKERS.split(","),
    "Dow Jones (DIA)": DIA_TICKERS.split(","),
    "Russell 2000 (IWM)": IWM_TICKERS.split(",")
}

ETF_MAPPING = {
    "S&P 500 (SPY)": "SPY",
    "Nasdaq 100 (QQQ)": "QQQ",
    "Dow Jones (DIA)": "DIA",
    "Russell 2000 (IWM)": "IWM"
}

# ===================================================
# ⚙ 核心運算引擎 (加入 250日新高/新低計算)
# ===================================================
@st.cache_data(ttl=1800, show_spinner=False)
def fetch_and_calculate_breadth(index_name):
    tickers = INDEX_COMPONENTS[index_name]
    etf_ticker = ETF_MAPPING[index_name]
    
    try:
        raw_data = yf.download(tickers + [etf_ticker], period="250d", auto_adjust=True, progress=False, group_by="ticker")
    except Exception as e:
        return pd.DataFrame(), pd.DataFrame(), pd.DataFrame()

    if raw_data.empty:
        return pd.DataFrame(), pd.DataFrame(), pd.DataFrame()

    # 提取 ETF 主圖價格
    try:
        if isinstance(raw_data.columns, pd.MultiIndex):
            df_etf = raw_data[etf_ticker][['Open', 'High', 'Low', 'Close']].copy().dropna()
        else:
            df_etf = pd.DataFrame()
    except Exception:
        df_etf = pd.DataFrame()

    # 提取所有成份股 Close, High, Low
    close_prices, high_prices, low_prices = {}, {}, {}
    if isinstance(raw_data.columns, pd.MultiIndex):
        for tick in tickers:
            if tick in raw_data.columns.get_level_values(0):
                if 'Close' in raw_data[tick] and 'High' in raw_data[tick] and 'Low' in raw_data[tick]:
                    close_prices[tick] = raw_data[tick]['Close']
                    high_prices[tick] = raw_data[tick]['High']
                    low_prices[tick] = raw_data[tick]['Low']
    
    if not close_prices:
        return pd.DataFrame(), pd.DataFrame(), pd.DataFrame()
        
    comp_close = pd.DataFrame(close_prices).dropna(how='all', axis=1).ffill()
    comp_high = pd.DataFrame(high_prices).dropna(how='all', axis=1).ffill()
    comp_low = pd.DataFrame(low_prices).dropna(how='all', axis=1).ffill()
    
    total_valid = comp_close.notna().sum(axis=1)
    
    # 1. 計算 20MA 同 50MA 市寬
    ma20 = comp_close.rolling(window=20).mean()
    ma50 = comp_close.rolling(window=50).mean()
    above_ma20 = (comp_close > ma20).sum(axis=1)
    above_ma50 = (comp_close > ma50).sum(axis=1)
    
    breadth_fast = (above_ma20 / total_valid * 100).fillna(0)
    breadth_slow = (above_ma50 / total_valid * 100).fillna(0)
    
    df_breadth = pd.DataFrame({
        "Fast_20MA": breadth_fast,
        "Slow_50MA": breadth_slow
    })

    # 2. 計算 52 週 (250日) 新高新低 (NH/NL)
    rolling_250_high = comp_high.rolling(window=250, min_periods=60).max()
    rolling_250_low = comp_low.rolling(window=250, min_periods=60).min()
    
    new_highs_count = (comp_high >= rolling_250_high).sum(axis=1)
    new_lows_count = (comp_low <= rolling_250_low).sum(axis=1)
    net_new_highs = new_highs_count - new_lows_count

    df_nhnl = pd.DataFrame({
        "New_Highs": new_highs_count,
        "New_Lows": new_lows_count,
        "Net_Highs": net_new_highs,
        "Total_Valid": total_valid
    })
    
    return df_etf, df_breadth, df_nhnl

# ===================================================
# 🔴 頁面渲染 (三層樓終極版)
# ===================================================
def render_page_2e():
    st.markdown("<h1 style='color:#00ff88; font-family:Arial Black;'>🧩 艙房 2e：美股四大指數全量市寬 + 動能掃描</h1>", unsafe_allow_html=True)
    st.markdown("<p style='color:#aaa;'>三維矩陣：價量背離 (主圖) ＋ 52週新高新低 (副圖1) ＋ 淨推進力 (副圖2)</p>", unsafe_allow_html=True)
    st.markdown("<hr style='border:3px solid #00ff88; margin-bottom:20px;'>", unsafe_allow_html=True)
    
    all_indices = ["S&P 500 (SPY)", "Nasdaq 100 (QQQ)", "Dow Jones (DIA)", "Russell 2000 (IWM)"]
    count_map = {"S&P 500 (SPY)": 500, "Nasdaq 100 (QQQ)": 97, "Dow Jones (DIA)": 30, "Russell 2000 (IWM)": 500}
    
    for target_index in all_indices:
        with st.spinner(f"📡 正在自動全量加載 {target_index} (共 {count_map[target_index]} 隻成份股)..."):
            df_etf, df_breadth, df_nhnl = fetch_and_calculate_breadth(target_index)

        if df_etf.empty or df_breadth.empty or df_nhnl.empty:
            st.error(f"⚠️ 無法獲取 {target_index} 數據，可能觸發伺服器流量限制，請稍後重試。")
            continue

        # 對齊日期 (取最近 180 天讓圖表清晰展示)
        df_etf = df_etf.tail(180)
        df_breadth = df_breadth.reindex(df_etf.index).fillna(method='ffill')
        df_nhnl = df_nhnl.reindex(df_etf.index).fillna(0)

        # ==========================================
        # 📈 繪製三層圖表 (3 Subplots)
        # ==========================================
        fig = make_subplots(
            rows=3, cols=1, shared_xaxes=True, vertical_spacing=0.03,
            row_heights=[0.5, 0.25, 0.25], 
            specs=[[{"secondary_y": True}], [{"secondary_y": False}], [{"secondary_y": False}]]
        )

        # ------------------------------------
        # 🏢 第一層：主圖 K線 + 快慢市寬
        # ------------------------------------
        fig.add_trace(go.Candlestick(
            x=df_etf.index, open=df_etf['Open'], high=df_etf['High'], low=df_etf['Low'], close=df_etf['Close'], 
            name=f'{ETF_MAPPING[target_index]} 價格',
            increasing_line_color='#26a69a', decreasing_line_color='#ef5350', showlegend=False
        ), row=1, col=1, secondary_y=False)

        fig.add_trace(go.Scatter(
            x=df_breadth.index, y=df_breadth['Fast_20MA'], mode='lines', line=dict(color='#9c27b0', width=2), name='20MA %'
        ), row=1, col=1, secondary_y=True)

        fig.add_trace(go.Scatter(
            x=df_breadth.index, y=df_breadth['Slow_50MA'], mode='lines', line=dict(color='#2196f3', width=2), name='50MA %'
        ), row=1, col=1, secondary_y=True)

        hline_configs = [(85, '#4caf50', 'dash'), (75, '#4caf50', 'dash'), (25, '#4caf50', 'dash'), (15, '#4caf50', 'dash'),
                         (90, '#e91e63', 'solid'), (70, '#e91e63', 'solid'), (30, '#00bcd4', 'solid'), (17.5, '#00bcd4', 'solid'), (5, '#00bcd4', 'solid')]
        for y_val, color, style in hline_configs:
            fig.add_hline(y=y_val, line_dash=style, line_color=color, line_width=1, opacity=0.5, row=1, col=1, secondary_y=True)

        # ------------------------------------
        # 🏢 第二層：絕對新高 / 新低 (Gross NH/NL)
        # ------------------------------------
        fig.add_trace(go.Bar(
            x=df_nhnl.index, y=df_nhnl['New_Highs'], 
            marker_color='#4caf50', name='創52週新高 (隻)',
            hovertemplate='%{y} 隻<extra></extra>'
        ), row=2, col=1)
        
        fig.add_trace(go.Bar(
            x=df_nhnl.index, y=-df_nhnl['New_Lows'], 
            marker_color='#e91e63', name='創52週新低 (隻)',
            hovertemplate='%{customdata} 隻<extra></extra>',
            customdata=df_nhnl['New_Lows'] 
        ), row=2, col=1)

        # ------------------------------------
        # 🏢 第三層：淨新高推進力 (Net NH-NL)
        # ------------------------------------
        net_colors = ['#4caf50' if val >= 0 else '#e91e63' for val in df_nhnl['Net_Highs']]
        fig.add_trace(go.Bar(
            x=df_nhnl.index, y=df_nhnl['Net_Highs'], 
            marker_color=net_colors, name='淨新高 (隻)',
            hovertemplate='淨值: %{y} 隻<extra></extra>'
        ), row=3, col=1)

        # ==========================================
        # 🎨 圖表排版與美化 (🌟 爺爺修正了字體顏色)
        # ==========================================
        fig.update_layout(
            title=dict(text=f"🎯 {target_index} 多維度動能掃描 (全陣列 {count_map[target_index]} 隻)", font=dict(color='white', size=22)),
            template="plotly_dark", height=850, margin=dict(l=50, r=60, t=60, b=20),
            xaxis_rangeslider_visible=False, showlegend=True, barmode='relative',
            font=dict(color="white"), # 🌟 強制全域字體變白
            legend=dict(orientation="h", yanchor="bottom", y=1.01, xanchor="right", x=1, font=dict(color="white")), # 🌟 強制圖例變白
            paper_bgcolor="#1e212b", plot_bgcolor="#1e212b"
        )
        
        fig.update_yaxes(title_text="價格", row=1, col=1, secondary_y=False, gridcolor="#333", showgrid=True)
        fig.update_yaxes(title_text="市寬 %", range=[0, 100], row=1, col=1, secondary_y=True, showgrid=False, tickvals=[5,15,17.5,25,30,50,70,75,85,90], tickfont=dict(color="#00ff88"))
        fig.update_yaxes(title_text="新高/低", row=2, col=1, gridcolor="#333", zerolinecolor="#fff", zerolinewidth=1)
        fig.update_yaxes(title_text="淨新高", row=3, col=1, gridcolor="#333", zerolinecolor="#fff", zerolinewidth=1)
        
        fig.update_xaxes(showticklabels=False, row=1, col=1, gridcolor="#333")
        fig.update_xaxes(showticklabels=False, row=2, col=1, gridcolor="#333")
        fig.update_xaxes(showticklabels=True, row=3, col=1, gridcolor="#333")

        st.plotly_chart(fig, use_container_width=True, config={'displayModeBar': True})
        st.markdown("<hr style='border:1px dashed #555; margin: 30px 0;'>", unsafe_allow_html=True)

if __name__ == "__main__":
    render_page_2e()