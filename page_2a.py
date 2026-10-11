import streamlit as st
import pandas as pd
import numpy as np
import yfinance as yf
import time

# 👑 鋼鐵直連技術：全面採用空白分隔字串，變數名稱 100% 嚴絲合縫對齊！
hz_str = "0001.HK 0002.HK 0003.HK 0005.HK 0006.HK 0011.HK 0012.HK 0016.HK 0017.HK 0027.HK 0066.HK 0101.HK 0135.HK 0151.HK 0175.HK 0241.HK 0267.HK 0288.HK 0291.HK 0316.HK 0322.HK 0384.HK 0386.HK 0388.HK 0669.HK 0688.HK 0700.HK 0762.HK 0817.HK 0823.HK 0836.HK 0857.HK 0868.HK 0883.HK 0902.HK 0914.HK 0916.HK 0939.HK 0941.HK 0960.HK 0968.HK 0992.HK 0998.HK 1038.HK 1044.HK 1088.HK 1093.HK 1109.HK 1113.HK 1177.HK 1193.HK 1211.HK 1288.HK 1299.HK 1378.HK 1398.HK 1658.HK 1810.HK 1876.HK 1928.HK 1929.HK 1999.HK 2015.HK 2020.HK 2196.HK 2269.HK 2313.HK 2318.HK 2319.HK 2331.HK 2359.HK 2382.HK 2388.HK 2628.HK 2688.HK 2899.HK 3311.HK 3320.HK 3690.HK 3968.HK 3988.HK 6098.HK 6186.HK 6690.HK 6862.HK 9618.HK 9633.HK 9868.HK 9888.HK 9961.HK 9988.HK 9999.HK 3908.HK"

kh_str = "0700.HK 9988.HK 3690.HK 1810.HK 9618.HK 1024.HK 9888.HK 2015.HK 1211.HK 9868.HK 9866.HK 0981.HK 1347.HK 2382.HK 2018.HK 0992.HK 0268.HK 1797.HK 6618.HK 2400.HK 0285.HK 0522.HK 1310.HK 0008.HK 1478.HK 0321.HK 0596.HK 0732.HK 1070.HK 0099.HK"

wd_str = "AAPL MSFT UNH JNJ XOM JPM V PG HD CVX MRK KO ABBV BAC AVGO PEP TMO COST CSCO MCD CRM DIS LIN ABN ACN AMD WFC NFLX INTC CAT"

ns_str = "AAPL MSFT AMZN NVDA GOOGL GOOG META TSLA AVGO COST PEP CSCO AMD NFLX TMUS CMG AMGN INTU QCOM TXN HON AMAT ISRG BKNG VRTX ADI LRCX MDLZ REGN PANW NOW MU MELI SNPS CDNS KLAC GILD PDD CHTR INTC ADBE MAR ORLY CTAS NXPI WDAY MNST LULU PCAR ROST PAYX KDP ADSK AEP ODFL AZN EXC MCHP IDXX CPRT MRVL CSX BIIB CTSH GEHC EOG FAST EA VRSK DDOG XEL SIRI ANSS TEAM ILMN ALGN WBD MDB BKR ZSCALE FTNT KEYS CRWD CEG DXCM SBUX MRNA ZM OKTA DLTR ROKU KHC EBAY"

# 🎯 標指 400 隻彈夾
sp_p1 = "AAPL MSFT AMZN NVDA GOOGL META LLY AVGO JPM UNH V XOM PG HD JNJ MA COST MRK ABBV AMD ADBE CRM QCOM WFC DIS TXN PM BAC AMGN INTU VZ COP PEP TMO MCD CSCO CMG PFE LIN C BMY WMT SCHW LOW AXP INTC CAT MS GS HON GE PLTR IBM ORCL NOW AMAT DE UBER LMT LRCX BKNG ADI MDLZ TJX ISRG SYK NKE GILD REGN VRTX ADP CVS CI MU PANW MMC EXP GL WELL F GM MET TRV ALL KRE"
sp_p2 = "PNC TFC USB DFS STT BK AMP BLK ACN ACGL ADM AEE AEP AES AFL AAL ALB ALGN ALLE AME ANET ANSS AOS APD APTV ARE ATO AVB AVY AWK AXON AZO BALL BAX BBWI BDX BEN BF-B BG BIIB BIO BR BRO BWA BXP CBOE CBRE CCI CCK CE CEG CF CFG CHD CHRW CHTR CINF CLX CMA CMI CMS CNC CNP COO CPB CPRT CPT CPAY CRWD CSGP CSX CTAS CTLT CTSH CTVA D DAL DD DGX DG DHI DLR DLTR DOV DOW DPZ DRI DTE DVA DVN DXCM DXC EA EFX EIX EL EMN ENPH EPAM EQR EQT ES ESS"
sp_p3 = "ETN ETSY EVRG EW EXC EXPE EXPD EXR FANG FAST FE FFIV FIS FITB FOX FOXA FRT FTI FTNT FTV GEV GEHC GIS GL GLW GNRC GPC GPN GRMN GWW HAL HAS HBAN HES HIG HII HLT HOLX HPE HPQ HRL HSIC HSY HWM IDXX IEX IFF ILMN INCY INVH IP IPG IQV IR IRM IT IVZ J JBHT JCI JKHY JNPR K KDP KEY KEYS KHC KIM KLAC KMB KMX KMX KMI KNX KR KSS L LAD LEN LH LHX LKQ LNT LULU LUV LYV MAS MAT MCHP MCK MCO MDT MHK MKC MKTX MLM MSCI"
sp_p4 = "MSI MTB MTCH MTD NDSN NEE NEM NFG NFLX NI NOC NOV NRG NTAP NTR NTRS NVR NVT NWL NWSA NWS O ODFL OGE OGN OKE OMC ON OUT PAYC PAYX PCAR PCG PEG PENN PFG PH PHM PKG PKI PODD POOL PPG PPL PRU PSA PSX PTC PVH PWR PXD PYPL QRVO REG RF RHI RJM RL RMD ROK ROL ROST RSG RTX SBAC SRE STE STT STX STZ TROW DD PANW NKE GILD CVS CI BK BLK ACN SPG LMT LOW HD COST LLY JPM TSLA"

# 🎯 羅素 400 隻彈夾
iwm_p1 = "SMCI MSTR CELH WING ELF ANF MOD TMDX AXON FOUR INDI VRT SOFI NU GPN AFRM TOST RUN FSLR ENPH SHLS PLUG DKNG RBLX HOOD COIN U AI SOUN RXRX BBAI VLD IONQ CRDO NRDS LUNA QBTS KTRA RGTI ARQQ INVZ RKLB SPCE PL BKSY ASTS RDW MNTS LLAP SIDU SPIR SATS LUNR ACHR JOBY SYM CGNX ISGN KEX LECO ROK PTC FARO CHGG COUR LRN TWOU PRDO STRA APEI ATGE LOPE UTI LAUR BFAM CROX DECK ONON SKX PLCE FL LEVI VFC KTB BOOT WWW SHOO TBLA RCKY"
iwm_p2 = "CF MOS NTR SMG SQM IPI UAN SEB BIOC LMNR AVD CVA LNN X CLF RS WOR RYI TMST CRS HAYN KALU ATI SCHN USAP ZEUS SEDG CWEN AY NOVA MAXN SPWR ARRY STEM BNTX AXSM PTCT BPMC FATE NVAX HALO PBYI GBT MRTX MGTA XENC MREO SANA RLAY CUE SFIX OLLI PAG AN AMKR DIOD CCMP SIMO POWI FORM ONTO CAMT ICHR COHU AOSL GSI UMC ASX HIMX BLKB PRO SPSX ALRM QLYS TENB VRNS RPD GUID ASAN SMAR PD DT BASE UPWK FIVN BAND TWLO AVAYA LPSN"
iwm_p3 = "DBX EGHT RING VON SSTK SHUT TCX GTT CNSL HCAT QMCO HANY SOS NCTY BTBT MIGI WULF GREE RENN XNET PHUN AMBA AEHR SEMR CALX DZSI LTRX SGH SANM PLXS JBL FLEX FLIR ALTR NVMI ACLS CAMT WSM GPC TSCO MIDD SAIA EXPD CHRW GGG DOV NDSN LECO WTS ITW NVAX HALO OLLI RH PAG AN RXO KNX SOFI NU GPN AFRM TOST RUN FSLR ENPH SHLS PLUG DKNG RBLX HOOD COIN APP CELH WING ELF ANF MOD TMDX AXON FOUR INDI VRT MARA RIOT CLSK CIFR HUT CORZ IREN"
iwm_p4 = "AAON ABCB ABG ABM ACAD ACER ACGL ACHC ACIW ACM ACNB ACRE ACRS ACTG ACVA ADUS ADV ADVM AEIS AEL AEO AERC AERI AERY AFBI AFG AFIB AFMD AGCO AGEN AGIO AGL AGM AGNC AGO AGS AHH AHR AHT AIB AIH AIK AIL AIMC AIN AIR AIRG AIRT AIT AIV AIZ AJX AKBA AKR AKRO AKTS AL ALCO ALDX ALE ALEC ALEX ORIG ALHC ALIM ALKS ALKT ALLE ALLK ALLO ALLR ALLT ALLY ALNA ALNY ALOT ALPN ALRM ALRN ALRS ALSA ALSN ALT ALTA ALTO ALTR ALVR ALX AMAL EXPD SAIA ODFL OPY LSTR MATX ARCB XPO KNX SNDR HTLD CVTI WERN HUBG MRIN REVG BKI LPRO"

FULL_INDEX_TICKERS = {
    "恒指": hz_str.split(),
    "科指": kh_str.split(),
    "道指": wd_str.split(),
    "納市": ns_str.split(),
    "標指": f"{sp_p1} {sp_p2} {sp_p3} {sp_p4}".split(),
    "IWM": f"{iwm_p1} {iwm_p2} {iwm_p3} {iwm_p4}".split()
}

def compute_all_global_matrix():
    master_unique_tickers = set()
    for tickers in FULL_INDEX_TICKERS.values():
        master_unique_tickers.update(tickers)
    master_unique_tickers = list(master_unique_tickers)
    
    status_text = st.empty()
    status_text.markdown("🚀 **母艦全火力開進：正在跨海批量下載全球 800+ 隻權重股歷史數據...**")
    
    try:
        raw_data = yf.download(
            master_unique_tickers,
            period="1y",
            auto_adjust=True,
            progress=False,
            threads=True  
        )
    except Exception as e:
        st.error(f"❌ 全球洗盤批量下載失敗: {e}")
        return {}
        
    status_text.markdown("🔮 **大數據下載完成！正在啟動四維矩陣高速向量化計算...**")
    
    if 'Close' in raw_data.columns:
        close_matrix = raw_data['Close']
    else:
        close_matrix = raw_data
        
    stock_status = {}
    
    for t in close_matrix.columns:
        c = close_matrix[t].dropna()
        if len(c) < 50: continue
        
        curr = c.iloc[-1]
        
        stock_status[t] = {
            '20': curr > c.rolling(20).mean().iloc[-1],
            '50': curr > c.rolling(50).mean().iloc[-1],
            '100': curr > c.rolling(100).mean().iloc[-1] if len(c) >= 100 else curr > c.rolling(50).mean().iloc[-1],
            '200': curr > c.rolling(200).mean().iloc[-1] if len(c) >= 200 else curr > c.rolling(50).mean().iloc[-1]
        }
            
    status_text.empty()
    
    final_report = {}
    for idx_name, tickers in FULL_INDEX_TICKERS.items():
        v20 = v50 = v100 = v200 = valid_count = 0
        for t in tickers:
            if t in stock_status:
                valid_count += 1
                if stock_status[t]['20']: v20 += 1
                if stock_status[t]['50']: v50 += 1
                if stock_status[t]['100']: v100 += 1
                if stock_status[t]['200']: v200 += 1
                
        valid_count = max(1, valid_count)
        final_report[idx_name] = {
            'count': valid_count,
            'p20': (v20 / valid_count) * 100,
            'p50': (v50 / valid_count) * 100,
            'p100': (v100 / valid_count) * 100,
            'p200': (v200 / valid_count) * 100
        }
    return final_report

def render_breadth_tab():
    st.markdown("<h1 style='color:#00ff88; font-size:42px; text-align:left; font-family:Arial Black;'>📊 艙房 2a：全球 6 大核心指數真・全量市寬大面板</h1>", unsafe_allow_html=True)
    st.markdown("<hr style='border:3px solid #00ff88; margin:20px 0;'>", unsafe_allow_html=True)
    
    if 'global_breadth_data' not in st.session_state:
        st.session_state['global_breadth_data'] = None

    if st.button("🚀 啟動全球真全量部隊跨星系大洗盤清算"):
        st.session_state['global_breadth_data'] = compute_all_global_matrix()
        st.success("🎉 全球跨星系大數據庫矩陣洗盤完畢！四維真實市寬 100% 釋放對齊！")

    report = st.session_state['global_breadth_data']
    if report is None:
        st.info("💡 請點擊上方按鈕，啟動真全量星系大洗盤，解鎖最真實的市底多空真相！")
        return

    try:
        sp_50 = report['標指']['p50']
        nd_50 = report['納市']['p50']
        iwm_50 = report['IWM']['p50']
        hsi_50 = report['恒指']['p50']
        hsi_200 = report['恒指']['p200']
        sp_200 = report['標指']['p200']
        
        summary = (
            f"【艙房 2a 全球大盤市寬戰報】：\n"
            f"1. 🇺🇸 美股陣營：標普500 (50日線市寬 {sp_50:.1f}%, 200日線 {sp_200:.1f}%) | 納指 (50日線市寬 {nd_50:.1f}%) | 羅素中小盤 (50日線市寬 {iwm_50:.1f}%)\n"
            f"2. 🇭🇰 港股陣營：恒生指數 (50日線市寬 {hsi_50:.1f}%, 200日線 {hsi_200:.1f}%)\n"
            f"3. 核心定性判斷基準：若 50日線市寬 > 50% 屬健康多頭，若 < 30% 屬極度超賣或熊市主導。"
        )
        st.session_state["data_page_2a"] = summary
    except Exception as e:
        st.session_state["data_page_2a"] = "【艙房 2a】：大數據已洗盤生成，但提煉戰略情報時發生小錯誤。"

    def draw_index_card(title, data, color_theme):
        st.markdown(f"<div style='background-color:#111b24; padding:20px; border-radius:12px; border:2px solid {color_theme}; margin-bottom:20px;'><h3 style='color:{color_theme}; margin-top:0; font-weight:bold; font-size:1.6rem;'>{title} ({data['count']} 隻真成份)</h3></div>", unsafe_allow_html=True)
        st.markdown(f"⚪ **20市寬線之上**：`{data['p20']:.1f}%`")
        st.progress(data['p20'] / 100)
        st.markdown(f"🟡 **50市寬線之上**：<span style='color:#00ff88; font-weight:bold;'>{data['p50']:.1f}%</span>", unsafe_allow_html=True)
        st.progress(data['p50'] / 100)
        st.markdown(f"🔵 **100市寬線之上**：`{data['p100']:.1f}%`")
        st.progress(data['p100'] / 100)
        st.markdown(f"🟣 **200市寬線之上**：`{data['p200']:.1f}%`")
        st.progress(data['p200'] / 100)
        st.write("")

    c1, c2 = st.columns(2)
    with c1:
        st.markdown("<h2 style='color:#00f2ff; font-weight:bold;'>🇺🇸 美美戰區</h2>", unsafe_allow_html=True)
        draw_index_card("🇺🇸 S&P 500 (標指 400 隻全量解鎖)", report['標指'], "#00f2ff")
        draw_index_card("⚡ Nasdaq 100 (納指 101 隻完全體)", report['納市'], "#33ff33")
        draw_index_card("🏛️ Dow Jones (道指 30 隻完全體)", report['道指'], "#FFD700")
        draw_index_card("🔮 Russell 2000 (羅素 400 隻全量解鎖)", report['IWM'], "#FF00FF")
    with c2:
        st.markdown("<h2 style='color:#ffaa00; font-weight:bold;'>🇭🇰 港港戰區</h2>", unsafe_allow_html=True)
        draw_index_card("🦁 Hang Seng Index (恒指 93 隻真全量)", report['恒指'], "#ffaa00")
        draw_index_card("🤖 Hang Seng Tech (科指 30 隻完全體)", report['科指'], "#00FFCC")

def render_page_2a():
    render_breadth_tab()

if __name__ == "__main__":
    render_page_2a()