import streamlit as st
import yfinance as yf
import pandas as pd
import numpy as np
import plotly.graph_objects as go
import plotly.express as px
from plotly.subplots import make_subplots
from datetime import datetime, timedelta
import urllib.request
import re

# ==========================================
# 頁面與基本設定
# ==========================================
def app():
    st.set_page_config(layout="wide")
    st.title("🌌 艙房 2y : 華爾街宏觀上帝視角與全球資產戰略終端")
    
    # ---------------------------------------------------------
    # 📚 實戰解讀指南 (詳細文字說明)
    # ---------------------------------------------------------
    with st.expander("📖 點擊展開：雷達信號實戰解讀指南 (How to Trade)", expanded=True):
        st.markdown("### 🎯 1. 尋找「假突破 / 假跌破」 (紅綠三角形)")
        st.markdown("""
        *   🔻 **紅色向下三角 (頂背馳 / 假突破)**：當背景灰虛線 (大盤價格) 創出 20 日新高，但代表底層實體經濟的綠線 (小型股市寬) 卻**拒絕跟隨創新高，甚至掉頭向下**。這代表「升勢是假的」，大鱷只是在拉升幾隻巨頭 (如 NVDA, AAPL) 來掩護出貨。**行動：準備清倉、做空或買入 Put 避險。**
        *   🔺 **綠色向上三角 (底背馳 / 假跌破)**：當背景灰虛線 (大盤價格) 創出 20 日新低，市場一片恐慌，但綠線 (小型股市寬) 卻**拒絕創新低，甚至率先反彈**。這代表「跌勢已盡」，大鱷正在暗中吸納平貨。**行動：準備大舉抄底、做多或買入 Call。**
        """)
        
        st.markdown("### 📊 2. 判斷資金撕裂度 (下方紅綠柱狀圖)")
        st.markdown("""
        *   🟥 **紅色柱 (巨頭吸血 / 危險信號)**：當柱狀圖呈現紅色 (數值 > 15)，代表藍線 (大型股) 遠遠拋離綠線 (小型股)。整個市場的資金被抽乾，只去炒作最頂端的幾間巨頭。這通常發生在**牛市末期或極端泡沫中**，大盤隨時崩盤。
        *   🟩 **綠色柱 (細股狂熱 / 健康牛市)**：當柱狀圖呈現綠色 (數值 < -15)，代表綠線 (小型股) 的表現遠超藍線 (大型股)。市場炒作氣氛濃厚，資金全面向下滲透尋寶，這是**牛市初期或中期最健康的特徵**。
        """)

        st.markdown("### 📏 3. 捕捉極端情緒邊界 (紅綠橫向虛線與灰色軌道)")
        st.markdown("""
        *   🔴 **紅色虛線 (80 樓上 - 極度超買)**：當市寬線衝破 80，代表超過 80% 的股票都在均線之上。市場處於極度貪婪狀態，**不要追高**，隨時準備迎接回調。
        *   🟢 **綠色虛線 (20 樓下 - 極度超賣)**：當市寬線跌穿 20，代表市場血流成河，極度恐慌。這通常是**長線資金進場的最佳黃金坑**。
        *   🌪️ **淺灰色動態帶 (2-StdDev 軌道)**：市場在強勢時可以長期停留在 80 以上。因此，當藍線**向上突破**灰色帶的頂部，才是真正的「瘋狂超買」；當藍線**向下跌穿**灰色帶的底部，才是真正的「絕望超賣」。
        """)
    st.divider()

    # --- 頂部控制面板 ---
    col_cfg1, col_cfg2, col_cfg3 = st.columns([1, 1.2, 1.2])
    with col_cfg1:
        lookback_days = st.slider("歷史回溯日數 (畫圖範圍)", min_value=100, max_value=800, value=250)
    with col_cfg2:
        macro_mode = st.radio(
            "📡 選擇【上層大局視角】數據深度", 
            ["👑 華爾街機構級 S&P 1500 (最精準 / 載入需時)", "🚀 實打實 600 隻全覆蓋模式 (極速平衡)"], 
            index=0
        )
    with col_cfg3:
        bg_benchmark_choice = st.radio(
            "📈 選擇背景對比指數 (灰虛線)", 
            ["SPY (標普500)", "QQQ (納斯達克)", "IWM (羅素2000)", "DIA (道瓊斯)"], 
            index=0
        )

    end_date = datetime.today()
    end_date = datetime(end_date.year, end_date.month, end_date.day)
    start_date = end_date - timedelta(days=lookback_days)
    fetch_start = start_date - timedelta(days=365) 
    
    bg_ticker = bg_benchmark_choice.split(" ")[0]

    # ==========================================
    # 核心一：數據抓取 (含三大脈搏與 VIX)
    # ==========================================
    @st.cache_data(ttl=3600, show_spinner=False)
    def load_macro_pulses_data():
        macro_tickers = ['HYG', 'TLT', 'COPX', 'GLD', 'BTC-USD', '^VIX', 'SPY']
        try:
            data = yf.download(macro_tickers, start=fetch_start, end=end_date, progress=False)['Close']
            data = data.ffill().bfill()
            data.index = data.index.tz_localize(None)
            return data
        except:
            return pd.DataFrame()

    macro_data = load_macro_pulses_data()

    if not macro_data.empty:
        hyg_tlt = (macro_data['HYG'] / macro_data['TLT']) if ('HYG' in macro_data and 'TLT' in macro_data) else pd.Series()
        copx_gld = (macro_data['COPX'] / macro_data['GLD']) if ('COPX' in macro_data and 'GLD' in macro_data) else pd.Series()
        btc_gld = (macro_data['BTC-USD'] / macro_data['GLD']) if ('BTC-USD' in macro_data and 'GLD' in macro_data) else pd.Series()
        vix_series = macro_data['^VIX'] if '^VIX' in macro_data else pd.Series()
        spy_price = macro_data['SPY'] if 'SPY' in macro_data else pd.Series()
    else:
        hyg_tlt, copx_gld, btc_gld, vix_series, spy_price = pd.Series(), pd.Series(), pd.Series(), pd.Series(), pd.Series()

    # ==========================================
    # 🚦 0. A.I. 戰略指揮燈 (Regime Indicator)
    # ==========================================
    st.markdown("### 🚦 A.I. 戰略指揮燈 (Regime Indicator)")
    
    vix_latest = vix_series.iloc[-1] if not vix_series.empty else 15
    vix_chg_20d = ((vix_series.iloc[-1] / vix_series.iloc[-20]) - 1) * 100 if len(vix_series) >= 20 else 0
    hyg_tlt_chg_20d = ((hyg_tlt.iloc[-1] / hyg_tlt.iloc[-20]) - 1) * 100 if len(hyg_tlt) >= 20 else 0
    
    if vix_latest > 25 or (vix_chg_20d > 20 and hyg_tlt_chg_20d < -3):
        st.error("🔴 **【系統警告：宏觀資產避險 (Risk-Off 警報)】** —— VIX 恐慌飆升，債市信用利差擴大！聰明錢撤退，建議減倉或轉入避險防守！")
    elif hyg_tlt_chg_20d > 2 and vix_latest < 18:
        st.success("🟢 **【系統判定：全面狂暴牛市 (Risk-On 極致)】** —— 信用風險情緒健康，VIX 沉寂，大鱷全力押注風險資產，滿倉進攻！")
    else:
        st.warning("🟡 **【系統判定：資金高位撕裂 / 結構性分化 (Caution)】** —— 巨頭與細股出現撕裂背馳，市場進入高位震盪，建議精選龍頭，控制槓桿！")

    st.divider()

    # ==========================================
    # 🩸 1. 聰明錢三大宏觀脈搏心電圖
    # ==========================================
    st.markdown("### 🩸 聰明錢三大宏觀脈搏 (Macro Pulses)")
    st.caption("債市與商品市場講真話：追蹤華爾街大鱷的真實風險偏好與實體經濟體溫。")

    if not hyg_tlt.empty:
        col_p1, col_p2, col_p3 = st.columns(3)
        
        with col_p1:
            curr_ht = hyg_tlt.iloc[-1]
            ht_1m = ((hyg_tlt.iloc[-1] / hyg_tlt.iloc[-22]) - 1) * 100 if len(hyg_tlt) >= 22 else 0
            st.metric("🏦 信貸脈搏 (HYG/TLT)", f"{curr_ht:.3f}", f"{ht_1m:+.2f}% (1個月)")
            st.markdown("<div style='font-size:0.85em; color:gray;'><b>用法</b>：睇華爾街肯唔肯借貴利冒險。<br><span style='color:#00AA00'>▲ 升 (Risk-On)</span> 代表大鱷願意借錢炒股，利好大市；<br><span style='color:red'>▼ 跌 (Risk-Off)</span> 代表債市危機，資金撤退避險。</div>", unsafe_allow_html=True)
            fig_p1 = px.line(hyg_tlt.loc[start_date:end_date], labels={'value': 'HYG/TLT'})
            fig_p1.update_traces(line_color='#FF4500', line_width=2)
            fig_p1.update_layout(height=180, margin=dict(l=10, r=10, t=10, b=10), showlegend=False, xaxis_title=None, yaxis_title=None)
            st.plotly_chart(fig_p1, use_container_width=True)

        with col_p2:
            curr_cg = copx_gld.iloc[-1]
            cg_1m = ((copx_gld.iloc[-1] / copx_gld.iloc[-22]) - 1) * 100 if len(copx_gld) >= 22 else 0
            st.metric("🏭 增長脈搏 (COPX/GLD 銅金比)", f"{curr_cg:.3f}", f"{cg_1m:+.2f}% (1個月)")
            st.markdown("<div style='font-size:0.85em; color:gray;'><b>用法</b>：實時測量全球實體開工率同衰退陰霾。<br><span style='color:#00AA00'>▲ 升</span> 代表全球工廠開工，實體經濟強勁；<br><span style='color:red'>▼ 跌</span> 代表經濟衰退預期升溫，資金買黃金避險。</div>", unsafe_allow_html=True)
            fig_p2 = px.line(copx_gld.loc[start_date:end_date], labels={'value': 'COPX/GLD'})
            fig_p2.update_traces(line_color='#DAA520', line_width=2)
            fig_p2.update_layout(height=180, margin=dict(l=10, r=10, t=10, b=10), showlegend=False, xaxis_title=None, yaxis_title=None)
            st.plotly_chart(fig_p2, use_container_width=True)

        with col_p3:
            curr_bg = btc_gld.iloc[-1]
            bg_1m = ((btc_gld.iloc[-1] / btc_gld.iloc[-22]) - 1) * 100 if len(btc_gld) >= 22 else 0
            st.metric("🪙 流動性脈搏 (BTC/GLD)", f"{curr_bg:.1f}", f"{bg_1m:+.2f}% (1個月)")
            st.markdown("<div style='font-size:0.85em; color:gray;'><b>用法</b>：測量央行水塘嘅剩餘流動性！<br><span style='color:#00AA00'>▲ 升</span> 代表市場銀紙氾濫，熱錢瘋狂湧入投機資產；<br><span style='color:red'>▼ 跌</span> 代表全球流動性收緊，央行正在「收水」。</div>", unsafe_allow_html=True)
            fig_p3 = px.line(btc_gld.loc[start_date:end_date], labels={'value': 'BTC/GLD'})
            fig_p3.update_traces(line_color='#0000FF', line_width=2)
            fig_p3.update_layout(height=180, margin=dict(l=10, r=10, t=10, b=10), showlegend=False, xaxis_title=None, yaxis_title=None)
            st.plotly_chart(fig_p3, use_container_width=True)

    st.divider()

    # ==========================================
    # 核心二：MISE 數據獲取與處理
    # ==========================================
    @st.cache_data(ttl=86400)
    def get_sp1500_tickers_from_web():
        try:
            req_500 = urllib.request.Request('https://en.wikipedia.org/wiki/List_of_S%26P_500_companies', headers={'User-Agent': 'Mozilla/5.0'})
            sp500_table = pd.read_html(urllib.request.urlopen(req_500))[0]
            sp500 = sp500_table['Symbol'].str.replace('.', '-', regex=False).tolist()
            
            req_400 = urllib.request.Request('https://en.wikipedia.org/wiki/List_of_S%26P_400_companies', headers={'User-Agent': 'Mozilla/5.0'})
            sp400_table = pd.read_html(urllib.request.urlopen(req_400))[0]
            sp400 = sp400_table['Symbol'].str.replace('.', '-', regex=False).tolist()
            
            req_600 = urllib.request.Request('https://en.wikipedia.org/wiki/List_of_S%26P_600_companies', headers={'User-Agent': 'Mozilla/5.0'})
            sp600_table = pd.read_html(urllib.request.urlopen(req_600))[0]
            sp600 = sp600_table['Symbol'].str.replace('.', '-', regex=False).tolist()
            return {"Large (SPY)": sp500, "Mid (MDY)": sp400, "Small (IWM)": sp600}
        except: return None

    @st.cache_data(ttl=86400)
    def get_market_cap_tickers(mode_str):
        if not mode_str:
            mode_str = "🚀"

        if "👑" in mode_str:
            sp1500 = get_sp1500_tickers_from_web()
            if sp1500: 
                return sp1500
            mode_str = "🚀"

        large_cap = ['AAPL', 'MSFT', 'NVDA', 'AMZN', 'META', 'GOOGL', 'GOOG', 'BRK-B', 'LLY', 'AVGO', 'JPM', 'TSLA', 'UNH', 'XOM', 'V', 'PG', 'MA', 'JNJ', 'HD', 'ABBV', 'COST', 'MRK', 'CRM', 'CVX', 'NFLX', 'AMD', 'BAC', 'PEP', 'KO', 'WMT', 'LIN', 'TMO', 'MCD', 'DIS', 'ADBE', 'CSCO', 'ABT', 'INTU', 'QCOM', 'IBM', 'CMCSA', 'CAT', 'GE', 'PFE', 'VZ', 'NOW', 'UBER', 'AMAT', 'AXP', 'TXN', 'ISRG', 'PM', 'BKNG', 'GS', 'LOW', 'MS', 'SPGI', 'RTX', 'SPG', 'HON', 'BLK', 'NEE', 'C', 'PGR', 'TJX', 'ELV', 'AMGN', 'SCHW', 'SYK', 'DE', 'UNP', 'COP', 'MDLZ', 'REGN', 'LMT', 'ADP', 'PLTR', 'ADI', 'BSX', 'BX', 'PANW', 'MU']
        mid_cap = ['DECK', 'WWD', 'RGA', 'KNF', 'LBRDA', 'CASY', 'SAIA', 'TOL', 'PEN', 'FN', 'RPM', 'WMS', 'MTD', 'CHDN', 'LECO', 'MUR', 'LSCC', 'SF', 'EGP', 'GL', 'MORN', 'KEX', 'TR', 'SLG', 'CFR', 'PRI', 'SON', 'CBSH', 'UGI', 'HWC', 'GBCI', 'FFIN', 'UHT', 'NJR', 'SRCE', 'TMP', 'NWE', 'MGEE', 'SJI', 'ALE']
        small_cap = ['SMCI', 'CELH', 'RMD', 'ELF', 'ALGN', 'CROX', 'MED', 'FOXF', 'LANC', 'SITM', 'WNC', 'THRM', 'BOOM', 'AMPH', 'LNN', 'ATGE', 'GTY', 'HSTM', 'FLGT', 'EZPW', 'TSRI', 'PBPB', 'TAST', 'RRGB', 'LOCO', 'RICK', 'DINE', 'CHUY', 'PLAY', 'BJRI', 'BLMN', 'CBRL', 'DENN', 'TXRH', 'CAKE', 'IRWD']

        if "🎯" in mode_str:
            large_cap = ['AAPL', 'MSFT', 'NVDA', 'AMZN', 'META', 'GOOGL', 'GOOG', 'BRK-B', 'LLY', 'AVGO', 'JPM', 'TSLA', 'UNH', 'XOM', 'V', 'PG', 'MA', 'JNJ', 'HD', 'ABBV', 'COST', 'MRK', 'CRM', 'CVX', 'NFLX', 'AMD', 'BAC', 'PEP', 'KO', 'WMT', 'LIN', 'TMO', 'MCD', 'DIS', 'ADBE', 'CSCO', 'ABT', 'INTU', 'QCOM', 'IBM', 'CMCSA', 'CAT', 'GE', 'PFE', 'VZ', 'NOW', 'UBER', 'AMAT', 'AXP', 'TXN', 'ISRG', 'PM', 'BKNG', 'GS', 'LOW', 'MS', 'SPGI', 'RTX', 'SPG', 'HON', 'BLK', 'NEE', 'C', 'PGR', 'TJX', 'ELV', 'AMGN', 'SCHW', 'SYK', 'DE', 'UNP', 'COP', 'MDLZ', 'REGN', 'LMT', 'ADP', 'PLTR', 'ADI', 'BSX', 'BX', 'PANW', 'MU']
            mid_cap = ['DECK', 'WWD', 'RGA', 'KNF', 'LBRDA', 'CASY', 'SAIA', 'TOL', 'PEN', 'FN', 'RPM', 'WMS', 'MTD', 'CHDN', 'LECO', 'MUR', 'LSCC', 'SF', 'EGP', 'GL', 'MORN', 'KEX', 'TR', 'SLG', 'CFR', 'PRI', 'SON', 'CBSH', 'UGI', 'HWC', 'GBCI', 'FFIN', 'UHT', 'NJR', 'SRCE', 'TMP', 'NWE', 'MGEE', 'SJI', 'ALE']
            small_cap = ['SMCI', 'CELH', 'RMD', 'ELF', 'ALGN', 'CROX', 'MED', 'FOXF', 'LANC', 'SITM', 'WNC', 'THRM', 'BOOM', 'AMPH', 'LNN', 'ATGE', 'GTY', 'HSTM', 'FLGT', 'EZPW', 'TSRI', 'PBPB', 'TAST', 'RRGB', 'LOCO', 'RICK', 'DINE', 'CHUY', 'PLAY', 'BJRI', 'BLMN', 'CBRL', 'DENN', 'TXRH', 'CAKE', 'IRWD']

        large_clean = list(dict.fromkeys(large_cap))
        mid_clean = [t for t in dict.fromkeys(mid_cap) if t not in large_clean]
        small_clean = [t for t in dict.fromkeys(small_cap) if t not in large_clean and t not in mid_clean]
        return {"Large (SPY)": large_clean, "Mid (MDY)": mid_clean, "Small (IWM)": small_clean}

    @st.cache_data(ttl=3600)
    def calculate_mise_index(tickers, fetch_start):
        data = yf.download(tickers, start=fetch_start, end=datetime.today(), progress=False)
        if data.empty: return pd.Series()
        closes = data['Close'] if 'Close' in data.columns.levels[0] else data
        if isinstance(closes, pd.Series): closes = closes.to_frame()
            
        closes.index = closes.index.tz_localize(None)
        ma20, ma50, ma200 = closes.rolling(20).mean(), closes.rolling(50).mean(), closes.rolling(200).mean()
        
        pct_20 = (closes > ma20).sum(axis=1) / closes.notna().sum(axis=1) * 100
        pct_50 = (closes > ma50).sum(axis=1) / closes.notna().sum(axis=1) * 100
        pct_200 = (closes > ma200).sum(axis=1) / closes.notna().sum(axis=1) * 100
        
        mise_raw = (pct_20 * 0.3) + (pct_50 * 0.4) + (pct_200 * 0.3)
        return mise_raw.ewm(span=5, adjust=False).mean()

    def detect_divergence(price_series, breadth_series, window=20):
        price_roll_max = price_series.rolling(window).max()
        breadth_roll_max = breadth_series.rolling(window).max()
        price_roll_min = price_series.rolling(window).min()
        breadth_roll_min = breadth_series.rolling(window).min()
        
        bear_x, bear_y, bull_x, bull_y = [], [], [], []
        
        for i in range(window, len(price_series)):
            if price_series.iloc[i] >= price_roll_max.iloc[i] and breadth_series.iloc[i] < (breadth_roll_max.iloc[i] - 10):
                if len(bear_x) == 0 or (price_series.index[i] - bear_x[-1]).days > 5:
                    bear_x.append(price_series.index[i])
                    bear_y.append(price_series.iloc[i])
            if price_series.iloc[i] <= price_roll_min.iloc[i] and breadth_series.iloc[i] > (breadth_roll_min.iloc[i] + 10):
                if len(bull_x) == 0 or (price_series.index[i] - bull_x[-1]).days > 5:
                    bull_x.append(price_series.index[i])
                    bull_y.append(price_series.iloc[i])
        return bear_x, bear_y, bull_x, bull_y

    def render_mise_chart(title_text, tickers_dict, bg_series, bg_name):
        total_count = sum(len(v) for v in tickers_dict.values())
        st.markdown(f"#### {title_text}")

        f_large = calculate_mise_index(tickers_dict["Large (SPY)"], fetch_start)
        f_mid = calculate_mise_index(tickers_dict["Mid (MDY)"], fetch_start)
        f_small = calculate_mise_index(tickers_dict["Small (IWM)"], fetch_start)
        if f_large.empty: return

        try:
            m_large, m_mid, m_small = f_large.loc[start_date:end_date], f_mid.loc[start_date:end_date], f_small.loc[start_date:end_date]
            p_bg = bg_series.loc[start_date:end_date]
        except:
            m_large, m_mid, m_small, p_bg = f_large, f_mid, f_small, bg_series

        spread = m_large - m_small
        roll_m = f_large.rolling(126).mean().loc[start_date:end_date]
        roll_s = f_large.rolling(126).std().loc[start_date:end_date]
        up_band, low_band = roll_m + (2 * roll_s), roll_m - (2 * roll_s)
        
        bear_x, bear_y, bull_x, bull_y = detect_divergence(p_bg, m_small)

        fig = make_subplots(rows=2, cols=1, shared_xaxes=True, row_heights=[0.75, 0.25], vertical_spacing=0.05, specs=[[{"secondary_y": True}], [{"secondary_y": False}]])
        
        fig.add_trace(go.Scatter(x=p_bg.index, y=p_bg, name=f"{bg_name}價格", line=dict(color='rgba(80,80,80,0.4)', width=3, dash='dot')), row=1, col=1, secondary_y=True)
        if bear_x: fig.add_trace(go.Scatter(x=bear_x, y=bear_y, mode='markers', marker=dict(symbol='triangle-down', size=12, color='red'), name="頂背馳(紅三角)"), row=1, col=1, secondary_y=True)
        if bull_x: fig.add_trace(go.Scatter(x=bull_x, y=bull_y, mode='markers', marker=dict(symbol='triangle-up', size=12, color='#00AA00'), name="底背馳(綠三角)"), row=1, col=1, secondary_y=True)

        fig.add_trace(go.Scatter(x=up_band.index, y=up_band, line=dict(width=0), showlegend=False, hoverinfo='skip'), row=1, col=1)
        fig.add_trace(go.Scatter(x=low_band.index, y=low_band, line=dict(width=0), fill='tonexty', fillcolor='rgba(128,128,128,0.1)', name="2-StdDev灰色軌道"), row=1, col=1)

        fig.add_trace(go.Scatter(x=m_large.index, y=m_large, name="大型(藍)", line=dict(color='#1f77b4', width=2)), row=1, col=1)
        fig.add_trace(go.Scatter(x=m_mid.index, y=m_mid, name="中型(橙)", line=dict(color='#ff7f0e', width=2)), row=1, col=1)
        fig.add_trace(go.Scatter(x=m_small.index, y=m_small, name="小型(綠)", line=dict(color='#2ca02c', width=2)), row=1, col=1)
        
        fig.add_hline(y=80, line_dash="dash", line_color="red", opacity=0.5, row=1, col=1)
        fig.add_hline(y=20, line_dash="dash", line_color="green", opacity=0.5, row=1, col=1)
        
        colors = ['red' if v > 15 else 'green' if v < -15 else 'rgba(128,128,128,0.3)' for v in spread]
        fig.add_trace(go.Bar(x=spread.index, y=spread, marker_color=colors, name="藍綠撕裂度(紅綠柱)"), row=2, col=1)
        fig.add_hline(y=15, line_dash="dot", line_color="red", opacity=0.5, row=2, col=1, annotation_text="紅柱界線", annotation_position="top left")
        fig.add_hline(y=-15, line_dash="dot", line_color="green", opacity=0.5, row=2, col=1, annotation_text="綠柱界線", annotation_position="bottom left")

        fig.update_layout(height=500, margin=dict(l=20, r=20, t=10, b=10), legend=dict(orientation="h", yanchor="bottom", y=1.02, xanchor="right", x=1))
        fig.update_yaxes(title_text="同步率 (0-100)", range=[0, 100], row=1, col=1, secondary_y=False)
        fig.update_yaxes(title_text="撕裂度", row=2, col=1)
        fig.update_xaxes(range=[start_date, end_date], row=1, col=1)
        fig.update_xaxes(range=[start_date, end_date], row=2, col=1)
        st.plotly_chart(fig, use_container_width=True)

    with st.spinner(f"正在掃描市寬底層數據與 {bg_ticker} 價格..."):
        bg_bench_full = yf.download(bg_ticker, start=fetch_start, end=end_date, progress=False)['Close']
        if isinstance(bg_bench_full, pd.DataFrame): bg_bench_full = bg_bench_full.iloc[:, 0]
        bg_bench_full.index = bg_bench_full.index.tz_localize(None)
            
        render_mise_chart(
            "👑 第一層：上帝視角 (絕對真實底層) —— 動態標準差與極端背馳預警" if "👑" in macro_mode else "🚀 第一層：全景視角 (600隻 平衡大局) —— 動態標準差與極端背馳預警", 
            get_market_cap_tickers(macro_mode), bg_bench_full, bg_ticker
        )
        st.markdown("<br>", unsafe_allow_html=True)
        render_mise_chart("🎯 第二層：熱錢視角 (~158 隻活躍精英) —— 捕捉龍頭背馳與熱錢撕裂", get_market_cap_tickers("🎯"), bg_bench_full, bg_ticker)

    st.divider()

    # ==========================================
    # 核心三：華爾街 34 大板塊 (RRG + Treemap + Bar Chart)
    # ==========================================
    st.markdown("### 🎡 核心二：華爾街 34 大板塊全息星盤與熱力全景")

    MACRO_SECTORS = {
        'XLK': '科技 (XLK)', 'XLF': '金融 (XLF)', 'XLV': '醫療保健 (XLV)',
        'XLE': '能源 (XLE)', 'XLY': '非必需消費 (XLY)', 'XLP': '必需消費 (XLP)',
        'XLI': '工業 (XLI)', 'XLU': '公用事業 (XLU)', 'XLB': '原材料 (XLB)',
        'XLRE': '房地產 (XLRE)', 'XLC': '通訊服務 (XLC)'
    }

    FRONTIER_SECTORS = {
        '🧠 GPU / AI 核心算力 (SMH)': {'etfs': ['SMH', 'SOXX', 'USD'], 'tickers': ['NVDA', 'TSM', 'AVGO', 'AMD', 'ASML', 'ARM', 'MU', 'QCOM']},
        '💻 CPU / 處理器 (SOXX)': {'etfs': ['SOXX', 'XSD'], 'tickers': ['AMD', 'INTC', 'ARM', 'QCOM', 'AAPL', 'NVDA', 'TXN']},
        '💾 DRAM / 存儲與記憶體': {'etfs': ['DRAM', 'CHPX'], 'tickers': ['MU', '000660.KS', '005930.KS', 'WDC', 'STX']},
        '⚡ 光通訊 / 矽光子': {'etfs': ['FOTO'], 'tickers': ['LITE', 'COHR', 'FN', 'CIEN', 'IPGP', 'AAOI', 'CRDO', 'MRVL']},
        '🔋 MLCC / 被動元件': {'etfs': [], 'tickers': ['6981.T', '6762.T', '6976.T', '009150.KS', '2327.TW', '2492.TW']},
        '🏭 AI 伺服器與組裝': {'etfs': [], 'tickers': ['SMCI', 'DELL', 'HPE', '2317.TW', '2382.TW', '2356.TW', '3231.TW']},
        '❄ 發電、液冷與散熱板': {'etfs': ['GRID', 'XLU'], 'tickers': ['GEV', 'CAT', 'CMI', 'CEG', 'VST', 'VRT', 'MOD', '3324.TW', '3017.TW', '3653.TW']},
        '⚡ 變壓器與電網升級': {'etfs': ['GRID', 'PAVE'], 'tickers': ['PWR', 'ETN', 'HUBB', 'ABB', 'EME', 'MYRG']},
        '📱 Edge AI / 端側晶片': {'etfs': [], 'tickers': ['QCOM', 'AAPL', 'AVGO', 'SWKS', 'QRVO', 'LOGI', 'NXPI']},
        '🛡️ 網絡安全': {'etfs': ['CIBR', 'HACK', 'BUG'], 'tickers': ['CRWD', 'PANW', 'ZS', 'FTNT', 'NET', 'CYBR', 'OKTA', 'CHKP']},
        '🧠 LLM 大模型巨頭': {'etfs': ['AIQ', 'BOTZ', 'THNQ'], 'tickers': ['MSFT', 'GOOGL', 'AMZN', 'META', 'ORCL', 'AAPL']},
        '🚗 自動駕駛與 Robotaxi': {'etfs': ['IDRV', 'DRIV', 'HAIL'], 'tickers': ['TSLA', 'GOOGL', 'MBLY', 'UBER', 'HSAI', 'AUR']},
        '🦾 機械人與自動化': {'etfs': ['BOTZ', 'ROBO', 'IRBO'], 'tickers': ['TSLA', 'ISRG', '6954.T', 'PATH', 'SYM', 'TER']},
        '🌌 量子電腦': {'etfs': ['QTUM', 'DEFI'], 'tickers': ['IONQ', 'RGTI', 'QBTS', 'QUBT', 'IBM']},
        '🚀 太空與衛星通訊': {'etfs': ['UFO', 'ROKT', 'ARKX', 'NASA'], 'tickers': ['RKLB', 'ASTS', 'LUNR', 'VSAT', 'IRDM', 'PL']},
        '🪙 加密貨幣與狂熱': {'etfs': ['IBIT', 'BITO', 'WGMI'], 'tickers': ['COIN', 'MSTR', 'MARA', 'RIOT', 'CLSK', 'HOOD']},
        '⚛ 核能、SMR 與鈾礦': {'etfs': ['URA', 'URNM', 'NLR'], 'tickers': ['CCJ', 'OKLO', 'SMR', 'LEU', 'UUUU', 'CEG', 'VST']},
        '🥇 金礦股': {'etfs': ['GDX', 'GDXJ', 'RING'], 'tickers': ['NEM', 'GOLD', 'AEM', 'KGC', 'AUY']},
        '🥈 銀礦股': {'etfs': ['SIL', 'SILJ'], 'tickers': ['AG', 'PAAS', 'HL', 'CDE', 'FSM']},
        '🥉 銅礦股': {'etfs': ['COPX', 'CPER'], 'tickers': ['FCX', 'SCCO', 'ERO', 'TECK', 'HBM']},
        '🧬 前沿生物科技': {'etfs': ['XBI', 'IBB', 'ARKG'], 'tickers': ['MRNA', 'BNTX', 'CRSP', 'VRTX', 'REGN', 'ILMN']},
        '⚔️ 國防與軍工': {'etfs': ['ITA', 'PPA', 'XAR'], 'tickers': ['LMT', 'RTX', 'NOC', 'GD', 'BA', 'LHX', 'HII']},
        '🚀 顛覆性創新 (木頭姐)': {'etfs': ['ARKK', 'ARKW', 'ARKG', 'ARKF', 'ARKX'], 'tickers': ['TSLA', 'ROKU', 'COIN', 'PLTR', 'U']}
    }

    ULTIMATE_SECTORS = {
        '📈 股市總體風險 (SPY)': 'SPY',
        '🗑️ 聰明錢信用風險 (HYG)': 'HYG',
        '🪙 極限流動性 (BTC-USD)': 'BTC-USD',
        '👑 黃金終極避險 (GLD)': 'GLD',
        '🏭 實體基建與通脹 (COPX)': 'COPX',
        '🛍️ 美國消費信心 (XLY)': 'XLY',
        '🧠 AI 算力命脈 (SMH)': 'SMH',
        '⚛️ 核能與終極能源 (URA)': 'URA',
        '⚔️ 地緣政治與軍工 (ITA)': 'ITA'
    }

    def format_name(full_name):
        return full_name.split(" (")[0]

    @st.cache_data(ttl=900, show_spinner=False)
    def load_all_market_data():
        all_tickers = set(['SPY', 'TLT']) 
        all_tickers.update(MACRO_SECTORS.keys())
        all_tickers.update(ULTIMATE_SECTORS.values())
        for sec, info in FRONTIER_SECTORS.items():
            if 'etfs' in info:
                for etf in info['etfs']:
                    if etf: all_tickers.add(etf)
            all_tickers.update(info['tickers'])
        try:
            data = yf.download(list(all_tickers), period='1y', progress=False)['Close']
            return data.ffill().bfill()
        except: return pd.DataFrame()

    def calculate_momentum_table(series_dict, mid_days, short_days):
        data = []
        for name, series in series_dict.items():
            s = series.dropna()
            if len(s) >= 2:
                chg_1d = (s.iloc[-1] / s.iloc[-2] - 1) * 100
                chg_5d = (s.iloc[-1] / s.iloc[-6] - 1) * 100 if len(s) >= 6 else np.nan
                chg_10d = (s.iloc[-1] / s.iloc[-11] - 1) * 100 if len(s) >= 11 else np.nan
                chg_22d = (s.iloc[-1] / s.iloc[-23] - 1) * 100 if len(s) >= 23 else np.nan
                chg_44d = (s.iloc[-1] / s.iloc[-45] - 1) * 100 if len(s) >= 45 else np.nan
                chg_66d = (s.iloc[-1] / s.iloc[-67] - 1) * 100 if len(s) >= 67 else np.nan
                chg_130d = (s.iloc[-1] / s.iloc[-131] - 1) * 100 if len(s) >= 131 else np.nan
                
                chg_mid = (s.iloc[-1] / s.iloc[-mid_days-1] - 1) * 100 if len(s) >= mid_days + 1 else np.nan
                chg_short = (s.iloc[-1] / s.iloc[-short_days-1] - 1) * 100 if len(s) >= short_days + 1 else np.nan
                
                data.append({
                    '板塊': name, 
                    '1日變化 (%)': chg_1d, 
                    '1週 (5日) (%)': chg_5d, 
                    '2週 (10日) (%)': chg_10d,
                    '1個月 (22日) (%)': chg_22d,
                    '2個月 (44日) (%)': chg_44d,
                    '1季 (66日) (%)': chg_66d,
                    '半年 (130日) (%)': chg_130d,
                    '動態中線 (%)': chg_mid,
                    '動態短線 (%)': chg_short
                })
        df = pd.DataFrame(data)
        if not df.empty: df = df.sort_values(by='動態短線 (%)', ascending=False)
        return df

    def calculate_rrg_metrics(price_df, sector_series_dict, window=14, benchmark='SPY', tail_len=10):
        if price_df.empty or benchmark not in price_df.columns: return pd.DataFrame(), []
            
        bench_price = price_df[benchmark]
        rs_df = pd.DataFrame(index=price_df.index)
        for name, series in sector_series_dict.items():
            rs_df[name] = series / bench_price
            
        rs_mean = rs_df.rolling(window).mean()
        rs_std = rs_df.rolling(window).std().replace(0, np.nan)
        rs_ratio = 100 + ((rs_df - rs_mean) / rs_std) * 2
        
        ratio_mean = rs_ratio.rolling(window).mean()
        ratio_std = rs_ratio.rolling(window).std().replace(0, np.nan)
        rs_mom = 100 + ((rs_ratio - ratio_mean) / ratio_std) * 2
        
        rs_ratio_clean = rs_ratio.dropna()
        rs_mom_clean = rs_mom.dropna()
        
        colors = ['#FF0000', '#0000FF', '#008000', '#800080', '#FFA500', '#A52A2A', '#000000', '#FF1493', '#00CED1', '#4B0082', '#8B4513', '#FF4500', '#2E8B57', '#DAA520', '#1E90FF', '#DC143C', '#9932CC', '#8B0000', '#556B2F', '#4682B4', '#D2691E', '#C71585', '#006400', '#483D8B', '#B22222', '#008B8B', '#B8860B', '#6A5ACD', '#8B008B', '#0000CD', '#5F9EA0', '#D2B48C', '#FF6347', '#3CB371']
        
        scatter_data = []
        for i, col in enumerate(rs_ratio_clean.columns):
            tail_x = rs_ratio_clean[col].tail(tail_len).values.tolist()
            tail_y = rs_mom_clean[col].tail(tail_len).values.tolist()
            
            curr_ratio, curr_mom = tail_x[-1], tail_y[-1]
            if curr_ratio >= 100 and curr_mom >= 100: status, emoji = "加速爆發 (Leading)", "🚀"
            elif curr_ratio >= 100 and curr_mom < 100: status, emoji = "步入轉弱 (Weakening)", "⚠️"
            elif curr_ratio < 100 and curr_mom < 100: status, emoji = "深度衰退 (Lagging)", "📉"
            else: status, emoji = "觸底復甦 (Improving)", "🌱"
            
            scatter_data.append({
                "full_name": col, "short_name": format_name(col), 
                "x": tail_x, "y": tail_y, "color": colors[i % len(colors)], "status": f"{emoji} {status}"
            })
            
        return rs_ratio_clean, scatter_data

    def plot_rrg_chart(scatter_data, chart_title):
        if not scatter_data: return
        fig = go.Figure()

        fig.add_shape(type="rect", x0=100, y0=100, x1=120, y1=120, fillcolor="rgba(0, 255, 0, 0.08)", layer="below", line_width=0)
        fig.add_shape(type="rect", x0=100, y0=80, x1=120, y1=100, fillcolor="rgba(255, 255, 0, 0.08)", layer="below", line_width=0)
        fig.add_shape(type="rect", x0=80, y0=80, x1=100, y1=100, fillcolor="rgba(255, 0, 0, 0.08)", layer="below", line_width=0)
        fig.add_shape(type="rect", x0=80, y0=100, x1=100, y1=120, fillcolor="rgba(0, 191, 255, 0.08)", layer="below", line_width=0)
        
        fig.add_vline(x=100, line_width=1.5, line_color="#888888", line_dash="dash")
        fig.add_hline(y=100, line_width=1.5, line_color="#888888", line_dash="dash")
        
        fig.add_annotation(x=0.98, y=0.98, text="領先 (Leading)", showarrow=False, xref="paper", yref="paper", font=dict(color="#008800", size=24, family="Arial Black"), opacity=0.3)
        fig.add_annotation(x=0.98, y=0.02, text="轉弱 (Weakening)", showarrow=False, xref="paper", yref="paper", font=dict(color="#B8860B", size=24, family="Arial Black"), opacity=0.3)
        fig.add_annotation(x=0.02, y=0.02, text="落後 (Lagging)", showarrow=False, xref="paper", yref="paper", font=dict(color="#AA0000", size=24, family="Arial Black"), opacity=0.3)
        fig.add_annotation(x=0.02, y=0.98, text="改善 (Improving)", showarrow=False, xref="paper", yref="paper", font=dict(color="#0066CC", size=24, family="Arial Black"), opacity=0.3)

        all_x, all_y = [], []
        
        for d in scatter_data:
            if len(d['x']) > 1:
                fig.add_trace(go.Scatter(x=d['x'], y=d['y'], mode='lines', line=dict(color=d['color'], width=2.5), opacity=0.6, showlegend=False, hoverinfo='skip'))
            all_x.extend(d['x'])
            all_y.extend(d['y'])

        text_positions = ['top center', 'bottom center', 'middle right', 'middle left', 'top right', 'bottom left', 'top left', 'bottom right']

        for i, d in enumerate(scatter_data):
            pos = text_positions[i % len(text_positions)]
            fig.add_trace(go.Scatter(
                x=[d['x'][-1]], y=[d['y'][-1]], mode='markers+text',
                marker=dict(color=d['color'], size=14, line=dict(color='black', width=1)),
                text=[f" <b>{d['short_name']}</b> "], textposition=pos, textfont=dict(color="black", size=13),
                name=d['short_name'], hovertemplate=f"<b>{d['full_name']}</b><br>強度: %{{x:.2f}}<br>動能: %{{y:.2f}}<extra></extra>"
            ))

        if all_x and all_y:
            min_x, max_x = min(all_x), max(all_x)
            min_y, max_y = min(all_y), max(all_y)
            padding = 2.5
            fig.update_layout(
                title=dict(text=f"🎡 {chart_title}", font=dict(color="#333333", size=20, family="Arial Black")),
                height=800, margin=dict(l=50, r=50, t=50, b=50),
                xaxis=dict(title="RS-Ratio (強度 > 100 為跑贏大市)", range=[min(min_x - padding, 95), max(max_x + padding, 105)], showgrid=True, gridcolor='#EEEEEE', zeroline=False),
                yaxis=dict(title="RS-Momentum (動能 > 100 為向上加速)", range=[min(min_y - padding, 95), max(max_y + padding, 105)], showgrid=True, gridcolor='#EEEEEE', zeroline=False),
                showlegend=False
            )
            st.plotly_chart(fig, use_container_width=True)

    def render_treemap(mom_df, size_col, color_col):
        st.markdown("#### 🗺️ 資金實時板塊熱力圖 (Treemap)")
        st.caption(f"方塊大小代表 **{size_col}** 的絕對波幅，顏色深淺代表 **{color_col}** 的資金流入(綠)或流出(紅)強度。")
        
        tree_df = mom_df.copy()
        tree_df['short_name'] = tree_df['板塊'].apply(format_name)
        tree_df['size'] = tree_df[size_col].abs() + 0.1 
        
        fig_tree = px.treemap(
            tree_df, path=['short_name'], values='size',
            color=color_col,
            color_continuous_scale=['#d62728', '#FFFFFF', '#2ca02c'],
            color_continuous_midpoint=0,
            hover_data={size_col: ':.2f', color_col: ':.2f'}
        )
        fig_tree.update_layout(height=400, margin=dict(l=10, r=10, t=10, b=10))
        st.plotly_chart(fig_tree, use_container_width=True)

    def render_momentum_section(mom_df, scatter_data, section_title, mid_label, short_label, tree_size_col, tree_color_col):
        if mom_df.empty: return
        
        render_treemap(mom_df, tree_size_col, tree_color_col)
        
        st.markdown(f"#### 📊 {section_title} - 資金動能對比")
        fig_bar = go.Figure()
        
        short_names = [format_name(name) for name in mom_df['板塊']]
        
        fig_bar.add_trace(go.Bar(
            x=short_names, y=mom_df['動態中線 (%)'],
            name=mid_label, marker_color='#1f77b4',
            hovertemplate=f'%{{x}}<br>{mid_label}: %{{y:.2f}}%<extra></extra>'
        ))
        colors_short = ['#2ca02c' if val > 0 else '#d62728' for val in mom_df['動態短線 (%)']]
        fig_bar.add_trace(go.Bar(
            x=short_names, y=mom_df['動態短線 (%)'],
            name=short_label, marker_color=colors_short,
            hovertemplate=f'%{{x}}<br>{short_label}: %{{y:.2f}}%<extra></extra>'
        ))
        fig_bar.update_layout(
            barmode='group', height=400, margin=dict(l=20, r=20, t=30, b=20),
            legend=dict(orientation="h", yanchor="bottom", y=1.02, xanchor="right", x=1)
        )
        st.plotly_chart(fig_bar, use_container_width=True)

        st.markdown(f"#### 📋 {section_title} - 詳細數據表")
        status_dict = {d['full_name']: d['status'] for d in scatter_data}
        mom_df['RRG 狀態'] = mom_df['板塊'].map(status_dict)
        
        def color_pct(val):
            if pd.isna(val): return ''
            color = '#008800' if val > 0 else '#cc0000' if val < 0 else 'black'
            return f'color: {color}; font-weight: bold;'
            
        def color_status(val):
            if isinstance(val, str):
                if "🚀" in val: return "background-color: #e6ffe6; color: #006600; font-weight: bold;" 
                if "⚠️" in val: return "background-color: #ffffe6; color: #ffffe6; color: #b38f00; font-weight: bold;" 
                if "📉" in val: return "background-color: #ffe6e6; color: #cc0000; font-weight: bold;" 
                if "🌱" in val: return "background-color: #e6f2ff; color: #004080; font-weight: bold;" 
            return ""

        subset_cols = [
            '1日變化 (%)', '1週 (5日) (%)', '2週 (10日) (%)', 
            '1個月 (22日) (%)', '2個月 (44日) (%)', '1季 (66日) (%)', '半年 (130日) (%)'
        ]
        display_cols = ['板塊'] + subset_cols + ['RRG 狀態']

        dynamic_height = int((len(mom_df) * 36) + 43)
        styled_df = mom_df[display_cols].style.map(color_pct, subset=subset_cols).map(color_status, subset=['RRG 狀態']).format(
            {col: '{:.2f}%' for col in subset_cols}
        )
        st.dataframe(styled_df, use_container_width=True, height=dynamic_height, hide_index=True)

    with st.spinner("📡 正在抓取並計算全網 34 大板塊數據..."):
        price_data = load_all_market_data()

    if not price_data.empty:
        macro_series = {name: price_data[symbol] for symbol, name in MACRO_SECTORS.items() if symbol in price_data.columns}
        
        frontier_series = {}
        for name, info in FRONTIER_SECTORS.items():
            valid_cols = [c for c in info['tickers'] if c in price_data.columns]
            if 'etfs' in info:
                for etf in info['etfs']:
                    if etf in price_data.columns and etf not in valid_cols: valid_cols.append(etf)
            if valid_cols:
                pct_change = price_data[valid_cols].pct_change().mean(axis=1)
                frontier_series[name] = (1 + pct_change.fillna(0)).cumprod() * 100
                
        combined_series = {**macro_series, **frontier_series}
        ultimate_series = {name: price_data[symbol] for name, symbol in ULTIMATE_SECTORS.items() if symbol in price_data.columns}

        st.markdown("### 🌐 展區一：全球 34 大板塊大混戰 (全景對比)")
        
        col_bar1, col_bar2 = st.columns(2)
        with col_bar1:
            mid_days_1 = st.selectbox("📊 選擇動態【中線】時間窗", [10, 22, 44, 66, 130], index=1, format_func=lambda x: f"{x} 個交易日 (" + ("兩週" if x==10 else "1個月" if x==22 else "2個月" if x==44 else "1季" if x==66 else "半年") + ")", key="mid_1")
        with col_bar2:
            short_days_1 = st.selectbox("📊 選擇動態【短線】時間窗", [1, 5, 10], index=1, format_func=lambda x: f"{x} 個交易日 (" + ("單日" if x==1 else "1週" if x==5 else "兩週") + ")", key="short_1")

        col_tree1, col_tree2 = st.columns(2)
        mid_label_1 = "1個月趨勢" if mid_days_1==22 else "2個月趨勢" if mid_days_1==44 else "1季趨勢" if mid_days_1==66 else "半年趨勢" if mid_days_1==130 else "兩週趨勢"
        short_label_1 = "1週爆發力" if short_days_1==5 else "單日爆發力" if short_days_1==1 else "兩週爆發力"
        
        # 🎯 直接明確的時間選單，無撞名困擾
        tree_options = [
            '1日變化 (%)', '1週 (5日) (%)', '2週 (10日) (%)', 
            '1個月 (22日) (%)', '2個月 (44日) (%)', '1季 (66日) (%)', '半年 (130日) (%)'
        ]
        tree_display_map = {
            '1日變化 (%)': '1日', '1週 (5日) (%)': '1週 (5日)', '2週 (10日) (%)': '2週 (10日)',
            '1個月 (22日) (%)': '1個月 (22日)', '2個月 (44日) (%)': '2個月 (44日)',
            '1季 (66日) (%)': '1季 (66日)', '半年 (130日) (%)': '半年 (130日)'
        }
        
        with col_tree1:
            tree_size_1 = st.selectbox("🗺️ 熱力圖方塊【大細】代表", tree_options, index=3, format_func=lambda x: tree_display_map[x], key="tree_s_1")
        with col_tree2:
            tree_color_1 = st.selectbox("🗺️ 熱力圖方塊【顏色】代表", tree_options, index=1, format_func=lambda x: tree_display_map[x], key="tree_c_1")

        col_rrg1, col_rrg2 = st.columns(2)
        with col_rrg1: tail_3 = st.selectbox("🐍 選擇動態軌跡時間窗 (SPY 基準)", [1, 5, 10, 20, 40], index=2, key="tail_3")
        with col_rrg2: smooth_3 = st.selectbox("⚙️ RRG 計算靈敏度 (SPY 基準)", [10, 14, 20], index=1, key="smooth_3")
        
        _, comb_scatter = calculate_rrg_metrics(price_data, combined_series, window=smooth_3, benchmark='SPY', tail_len=tail_3)
        plot_rrg_chart(comb_scatter, f"全球 34 大板塊 RRG 星盤 (基準: SPY)")
        
        comb_mom = calculate_momentum_table(combined_series, mid_days_1, short_days_1)
        render_momentum_section(comb_mom, comb_scatter, "全球 34 大混戰", mid_label_1, short_label_1, tree_size_1, tree_color_1)
        st.markdown("---")

        st.markdown("### 🦅 展區二：大鱷跨資產預警星盤 (以 TLT 為基準)")
        
        col_bar3, col_bar4 = st.columns(2)
        with col_bar3:
            mid_days_2 = st.selectbox("📊 選擇動態【中線】時間窗", [10, 22, 44, 66, 130], index=1, format_func=lambda x: f"{x} 個交易日 (" + ("兩週" if x==10 else "1個月" if x==22 else "2個月" if x==44 else "1季" if x==66 else "半年") + ")", key="mid_2")
        with col_bar4:
            short_days_2 = st.selectbox("📊 選擇動態【短線】時間窗", [1, 5, 10], index=1, format_func=lambda x: f"{x} 個交易日 (" + ("單日" if x==1 else "1週" if x==5 else "兩週") + ")", key="short_2")

        mid_label_2 = "1個月趨勢" if mid_days_2==22 else "2個月趨勢" if mid_days_2==44 else "1季趨勢" if mid_days_2==66 else "半年趨勢" if mid_days_2==130 else "兩週趨勢"
        short_label_2 = "1週爆發力" if short_days_2==5 else "單日爆發力" if short_days_2==1 else "兩週爆發力"
        
        col_tree3, col_tree4 = st.columns(2)
        with col_tree3:
            tree_size_2 = st.selectbox("🗺️ 熱力圖方塊【大細】代表", tree_options, index=3, format_func=lambda x: tree_display_map[x], key="tree_s_2")
        with col_tree4:
            tree_color_2 = st.selectbox("🗺️ 熱力圖方塊【顏色】代表", tree_options, index=1, format_func=lambda x: tree_display_map[x], key="tree_c_2")

        col_rrg3, col_rrg4 = st.columns(2)
        with col_rrg3: tail_4 = st.selectbox("🐍 選擇動態軌跡時間窗 (TLT 基準)", [1, 5, 10, 20, 40], index=2, key="tail_4")
        with col_rrg4: smooth_4 = st.selectbox("⚙️ RRG 計算靈敏度 (TLT 基準)", [10, 14, 20], index=1, key="smooth_4")
        
        _, ulti_scatter = calculate_rrg_metrics(price_data, ultimate_series, window=smooth_4, benchmark='TLT', tail_len=tail_4)
        plot_rrg_chart(ulti_scatter, f"🔥 跨資產宏觀生死共振 (基準: TLT 美債)")
        
        ulti_mom = calculate_momentum_table(ultimate_series, mid_days_2, short_days_2)
        render_momentum_section(ulti_mom, ulti_scatter, "跨資產預警", mid_label_2, short_label_2, tree_size_2, tree_color_2)
        
    st.divider()

    st.markdown("## 🦅 爺爺壓箱底傳授：2026 九維跨資產共振 (The Macro End-Game)")
    st.markdown("展區二係華爾街頂級大鱷嘅**「抄底與逃頂核按鈕」**。呢個圖**唔係同 SPY 比較，而係同 TLT (20年期國債/終極避險資產) 比較！**\n\n2026 年宏觀已由 **AI 算力 (SMH)、核能/鈾礦 (URA) 與 地緣軍工 (ITA)** 主導，佢哋已經加入生死共振監測網！")
    
    st.markdown("### 🔥 【核按鈕用法】：")
    st.markdown("* **終極逃頂信號 (Crash Warning)**：當你見到 SPY, HYG, COPX, BTC-USD 呢幾條蛇，集體由右邊急轉彎，插水進入「落後區 (紅)」（即係跑輸 TLT），代表全球大資金正在瘋狂拋售高風險資產，湧入美債避險。**大崩盤即將來臨，清倉保命！**")
    st.markdown("* **終極抄底信號 (Generational Buy)**：當大市一片恐慌，但你見到 HYG (垃圾債) 同 BTC 率先由「落後區」抬頭，衝入「改善區 (藍)」甚至「領先區 (綠)」，代表大鱷已經開始暗中吸籌Risk-On。**呢個就係十年一遇嘅重倉抄底時機！**")

def render_page_2y():
    app()

if __name__ == "__main__":
    app()