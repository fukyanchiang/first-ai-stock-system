import streamlit as st
import yfinance as yf
import pandas as pd

# 🌐 港股 CSV 在 GitHub 的遠端連結
HK_STOCK_CSV_URL = "https://raw.githubusercontent.com/fukyanchiang/my-cosmos-vision/refs/heads/main/hk_stock.csv"
HK_ETF_CSV_URL = "https://raw.githubusercontent.com/fukyanchiang/my-cosmos-vision/refs/heads/main/hk_etf.csv"

def fetch_tickers_from_csv(source_key):
    """根據選擇從 CSV 自動讀取股票/ETF 代碼"""
    try:
        if source_key == "US_MARKET_FOCUS":
            df = pd.read_csv("Market_Focus.csv")
        elif source_key == "US_SP500":
            df = pd.read_csv("SP500_Equities.csv")
        elif source_key == "US_INDUSTRY":
            df = pd.read_csv("Industry_Focus.csv")
        elif source_key == "US_ETFS":
            df = pd.read_csv("US_ETFs.csv")
        elif source_key == "HK_STOCKS":
            df = pd.read_csv(HK_STOCK_CSV_URL)
        elif source_key == "HK_ETFS":
            df = pd.read_csv(HK_ETF_CSV_URL)
        else:
            return []

        # 自動尋找包含代碼的欄位
        col = [c for c in df.columns if c.lower() in ['ticker', 'symbol', '代號', 'code']][0]
        raw_tickers = df[col].dropna().astype(str).tolist()
        
        # 格式化代碼 (特別處理港股格式)
        formatted_tickers = []
        for t in raw_tickers:
            t = t.strip().upper()
            if source_key in ["HK_STOCKS", "HK_ETFS"]:
                if not t.endswith(".HK"):
                    t = f"{t.zfill(4)}.HK"
            formatted_tickers.append(t)
            
        return list(dict.fromkeys(formatted_tickers)) # 去重
    except Exception as e:
        st.error(f"⚠️ 讀取 CSV 名單失敗: {e}")
        return []

def show_hard_market_scanner():
    st.header("🔍 爛市尋強者 - 9大 SEPA 條件 100% 嚴格篩選")
    st.markdown("完全忠於量化邏輯：1-8 條件為硬性門檻，第 9 條件作均線糾纏度智能排序。")

    # 🎛️ 戰略名單來源選擇器
    source_option = st.selectbox(
        "📍 請選擇要掃描的美股/港股戰略名單：",
        [
            "✍️ 自訂手動輸入",
            "🇺🇸 美股 - 精選名單 (Market_Focus.csv)",
            "🇺🇸 美股 - 大藍籌 S&P 500 (SP500_Equities.csv)",
            "🇺🇸 美股 - 行業焦點 (Industry_Focus.csv)",
            "🇺🇸 美股 - 美股 ETF (US_ETFs.csv)",
            "🇭🇰 港股 - 全港股名單 (hk_stock.csv)",
            "🇭🇰 港股 - 港股 ETF 名單 (hk_etf.csv)"
        ]
    )

    ticker_list = []
    
    if source_option == "✍️ 自訂手動輸入":
        tickers_input = st.text_input(
            "輸入要掃描的美股/港股代碼 (用逗號分隔)：", 
            "NVDA, TSLA, AAPL, AMD, MSFT, META, AMZN, GOOGL, PLTR, ARM"
        )
        ticker_list = [t.strip().upper() for t in tickers_input.split(",") if t.strip()]
    else:
        # 🛠️ 爺爺修復：全部改用「完全精準匹配」，徹底杜絕掃錯名單！
        if source_option == "🇺🇸 美股 - 精選名單 (Market_Focus.csv)":
            ticker_list = fetch_tickers_from_csv("US_MARKET_FOCUS")
        elif source_option == "🇺🇸 美股 - 大藍籌 S&P 500 (SP500_Equities.csv)":
            ticker_list = fetch_tickers_from_csv("US_SP500")
        elif source_option == "🇺🇸 美股 - 行業焦點 (Industry_Focus.csv)":
            ticker_list = fetch_tickers_from_csv("US_INDUSTRY")
        elif source_option == "🇺🇸 美股 - 美股 ETF (US_ETFs.csv)":
            ticker_list = fetch_tickers_from_csv("US_ETFS")
        elif source_option == "🇭🇰 港股 - 全港股名單 (hk_stock.csv)":
            ticker_list = fetch_tickers_from_csv("HK_STOCKS")
        elif source_option == "🇭🇰 港股 - 港股 ETF 名單 (hk_etf.csv)":
            ticker_list = fetch_tickers_from_csv("HK_ETFS")

        st.info(f"📊 已成功加載戰略名單，共找到 **{len(ticker_list)}** 隻標的準備進行 9 大條件雷達掃描。")

    if st.button("🚀 開始 9 大條件 100% 嚴格篩選"):
        if not ticker_list:
            st.warning("請先選擇或輸入股票代碼！")
            return

        results = []
        progress_bar = st.progress(0)
        status_text = st.empty()
        
        for idx, symbol in enumerate(ticker_list):
            status_text.markdown(f"**📡 正在進行 9 大條件深度分析:** `{symbol}` ({idx+1}/{len(ticker_list)})")
            try:
                # 抓取足夠長度的歷史數據
                df = yf.download(symbol, period="1y", interval="1d", progress=False)
                
                if isinstance(df.columns, pd.MultiIndex):
                    df.columns = df.columns.get_level_values(0)

                if len(df) < 200:
                    continue

                close = df['Close']
                high = df['High']
                low = df['Low']
                vol = df['Volume']

                c_curr = float(close.iloc[-1])
                
                # ==========================================
                # 🛡️ 1-8 條硬性過濾門檻 (Must Pass)
                # ==========================================

                # 條件 1: 3個月內(約60交易日)回報不低於 20%
                c_60d = float(close.iloc[-60]) if len(close) >= 60 else float(close.iloc[0])
                ret_3m = (c_curr - c_60d) / c_60d
                cond1 = ret_3m >= 0.20

                # 條件 2: 股價不可低於 20日內的最低位
                low_20 = float(low.tail(20).min())
                cond2 = c_curr >= low_20 

                # 條件 3 & 4: 整固 >= 5日，但同時少於 40日，且整固 range < 8%
                # 嚴格算法：逐一掃描過去 5 日至 39 日的視窗，若有任何一段區間高低波幅 < 8% 即屬過關
                cond3_4 = False
                best_consolidation_range = 999.0
                for w in range(5, 40):
                    w_high = float(high.tail(w).max())
                    w_low = float(low.tail(w).min())
                    w_range = (w_high - w_low) / w_low
                    if w_range < 0.08:
                        cond3_4 = True
                        if w_range < best_consolidation_range:
                            best_consolidation_range = w_range
                
                # 條件 5: Average daily range (20日平均) > 3.5%
                adr = float(((high - low) / low).tail(20).mean())
                cond5 = adr > 0.035

                # 條件 6: 股價大於 $5
                cond6 = c_curr > 5.0

                # 條件 7: 每日成交金額 50日平均大於 500萬美金
                turnover_50m = float((close * vol).tail(50).mean())
                cond7 = turnover_50m > 5_000_000

                # 條件 8: 不可高於 200日線 60%
                ema200 = float(close.ewm(span=200, adjust=False).mean().iloc[-1])
                dist_ema200 = (c_curr - ema200) / ema200
                cond8 = dist_ema200 <= 0.60

                # ==========================================
                # 🧠 第 9 條智能排序引擎 (愈接近 10, 20, 50 EMA 愈好)
                # ==========================================
                ema10 = float(close.ewm(span=10, adjust=False).mean().iloc[-1])
                ema20 = float(close.ewm(span=20, adjust=False).mean().iloc[-1])
                ema50 = float(close.ewm(span=50, adjust=False).mean().iloc[-1])
                
                # 計算三大均線與現價的總離散度 (分數越小，代表三線糾纏得越緊密)
                ema_diff_score = (abs(c_curr - ema10) + abs(c_curr - ema20) + abs(c_curr - ema50)) / c_curr

                # 判定 1-8 條件是否 100% 全過
                all_passed = cond1 and cond2 and cond3_4 and cond5 and cond6 and cond7 and cond8

                # 為了畫面整潔，若沒有符合 8% 以下的整固區間，則顯示過去 20 日的波幅作為參考
                display_range = best_consolidation_range if cond3_4 else (float(high.tail(20).max()) - low_20) / low_20

                results.append({
                    "股票": symbol,
                    "現價": f"${c_curr:.2f}",
                    "3個月回報": f"{ret_3m*100:+.1f}%",
                    "最小整固波幅": f"{display_range*100:.1f}%",
                    "ADR均幅": f"{adr*100:.1f}%",
                    "50日均成交": f"${turnover_50m/1e6:.1f}M",
                    "偏離200日線": f"{dist_ema200*100:+.1f}%",
                    "狀態": "🔥 強勢入選" if all_passed else "❌ 淘汰",
                    "_passed": all_passed,
                    "_score": ema_diff_score
                })
            except Exception as e:
                pass
            
            # 更新進度條
            progress_bar.progress((idx + 1) / len(ticker_list))

        status_text.empty()
        
        # 輸出結果
        if results:
            res_df = pd.DataFrame(results)
            # 排序邏輯：首先將「🔥 強勢入選」(_passed=True) 排喺最頂，然後按「均線糾纏度」(_score) 由細到大排序！
            res_df = res_df.sort_values(by=["_passed", "_score"], ascending=[False, True])
            
            # 隱藏排序用的背景欄位
            res_df = res_df.drop(columns=["_passed", "_score"])
            
            st.dataframe(res_df, use_container_width=True)
            st.success("✅ 掃描完成！排在最頂部的股票，代表其 10、20、50 日均線最為糾纏，是爆發前夕的最佳目標。")
        else:
            st.warning("💤 名單內暫無符合 9 大嚴格條件的標的。")
