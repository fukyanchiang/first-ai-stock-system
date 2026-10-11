import os
import pandas as pd
import numpy as np
import yfinance as yf
import streamlit as st
from datetime import datetime

# 嘗試導入天外飛仙核心演算法
try:
    from Speed_defines_the_winner_VerRS import run_tianwai_feixian
except ImportError:
    # 備用：若無法導入獨立模組，則提示警報
    def run_tianwai_feixian(df, sctr_rank_from_master=0.0):
        st.error("❌ 找不到 Speed_defines_the_winner_VerRS.py 模組！")
        return pd.DataFrame()

# ----------------------------------------------------
# 1. 直連 GitHub Raw 雲端 SCTR Master 數據庫 (自動避開 Cache)
# ----------------------------------------------------
RAW_SCTR_URL = "https://raw.githubusercontent.com/fukyanchiang/my-cosmos-vision/main/SCTR_Master.csv"

@st.cache_data(ttl=300) # 快取 5 分鐘，確保實時性
def load_sctr_master():
    try:
        # 優先直連 GitHub 雲端最新產生的 11,726 隻全宇宙數據
        df = pd.read_csv(RAW_SCTR_URL)
        return df, "雲端 GitHub Raw 直連"
    except Exception as e:
        # 備用：若網絡不通則嘗試讀取本地檔案
        if os.path.exists("SCTR_Master.csv"):
            df = pd.read_csv("SCTR_Master.csv")
            return df, "本地 SCTR_Master.csv 備份"
        return None, str(e)

@st.cache_data(ttl=1800)
def fetch_historical_data(tickers):
    """多線程批次下載指定 Tickers 的 1 年歷史 K 線數據"""
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

# ----------------------------------------------------
# 2. 艙房 1a 渲染主函數
# ----------------------------------------------------
def render_page_1a():
    st.title("🛸 艙房 1a：天外飛仙 (RS 強勢爆發掃描器)")
    st.caption("結合全宇宙 SCTR 百分位排名 (11,000+ 隻資產) + Minervini 雙軌屠龍刀演算法，極速捕捉真龍與真皇爆發股")
    
    # 載入 SCTR Master 數據庫
    df_master, source_info = load_sctr_master()
    
    if df_master is None or df_master.empty:
        st.warning(f"⚠️ 尚未能讀取全宇宙 SCTR Master 數據庫 ({source_info})，請確認 GitHub Actions 是否已執行完畢！")
        return

    # 顯示數據源提示
    st.success(f"🌐 成功連線全宇宙數據庫 [{source_info}]！共計載入 **{len(df_master):,}** 隻資產 SCTR 排名數據。")

    # ------------------------------------
    # 左側控制台：過濾與門檻設定
    # ------------------------------------
    st.sidebar.markdown("---")
    st.sidebar.subheader("🛸 天外飛仙雷達控制台")
    
    categories = df_master['Category'].unique().tolist() if 'Category' in df_master.columns else []
    selected_cats = st.sidebar.multiselect("選擇資產類別", categories, default=categories)
    
    min_sctr = st.sidebar.slider("SCTR 最低百分位門檻", 50.0, 99.0, 80.0, 1.0)
    max_scan_count = st.sidebar.slider("掃描標的數量上限 (預防網頁卡頓)", 50, 500, 150, 50)
    
    # 篩選符合條件的初選名單
    df_filtered = df_master.copy()
    if selected_cats:
        df_filtered = df_filtered[df_filtered['Category'].isin(selected_cats)]
    
    df_filtered = df_filtered[df_filtered['SCTR'] >= min_sctr].sort_values(by='SCTR', ascending=False)
    candidate_tickers = df_filtered['Ticker'].tolist()[:max_scan_count]
    
    sctr_dict = dict(zip(df_filtered['Ticker'], df_filtered['SCTR']))

    st.info(f"📊 初選過濾：在符合條件 (SCTR ≥ {min_sctr}) 的標的中，鎖定 Top **{len(candidate_tickers)}** 隻頂尖動能股進行天外飛仙雙軌二次深度掃描。")

    # ------------------------------------
    # 觸發按鈕與執行掃描
    # ------------------------------------
    if st.button("🚀 開始全天外飛仙雙軌雷達大掃描", type="primary"):
        with st.spinner(f"正在為 {len(candidate_tickers)} 隻標的抓取最新 K 線與運算 21 大非必要加分引擎..."):
            hist_dict = fetch_historical_data(candidate_tickers)
            
            feixian_results = []
            
            for ticker in candidate_tickers:
                if ticker not in hist_dict:
                    continue
                
                df_k = hist_dict[ticker]
                sctr_rank = sctr_dict.get(ticker, 0.0)
                
                try:
                    # 執行天外飛仙 Minervini 雙軌運算
                    df_res = run_tianwai_feixian(df_k, sctr_rank_from_master=sctr_rank)
                    
                    if not df_res.empty:
                        last_row = df_res.iloc[-1]
                        state = last_row.get('天外飛仙_狀態', 0)
                        score = last_row.get('霸王總分', -9999)
                        tags = last_row.get('天外飛仙_標籤', '')
                        
                        # 過濾機制：觸發熱區(1)、冷區(2)、SCTR特權軌道(3) 或 有標籤/總分>0
                        if state in [1, 2, 3] or score > 0 or len(tags) > 0:
                            cat_val = df_master[df_master['Ticker'] == ticker]['Category'].values
                            feixian_results.append({
                                'Ticker': ticker,
                                'Category': cat_val[0] if len(cat_val) > 0 else 'Unassigned',
                                'SCTR排名': last_row.get('SCTR_Rank', sctr_rank),
                                'SCTR4.0原始分': last_row.get('SCTR_Raw_4_0', 0),
                                '霸王總分': round(score, 1),
                                '最新收盤價': round(last_row.get('Close', 0), 2),
                                '起爆日數': last_row.get('起爆日數', 0),
                                'RS強度': round(last_row.get('RS', 0), 2),
                                '量比': round(last_row.get('Vol_Ratio', 0), 2),
                                '戰略標籤': tags
                            })
                except Exception as e:
                    continue
            
            if not feixian_results:
                st.warning("⚠️ 經過天外飛仙嚴格篩選，目前初選標的中暫無觸發條件之標的。可嘗試調低 SCTR 門檻。")
                return

            df_res_show = pd.DataFrame(feixian_results).sort_values(by='霸王總分', ascending=False)

            # ------------------------------------
            # 戰果看板展示
            # ------------------------------------
            m1, m2, m3 = st.columns(3)
            m1.metric("👑 觸發標的總數", f"{len(df_res_show)} 隻")
            m2.metric("🐉 包含真龍/真皇數量", f"{len(df_res_show[df_res_show['戰略標籤'].str.contains('真龍|真皇', na=False)])} 隻")
            m3.metric("🔥 最佳霸王最高分", f"{df_res_show['霸王總分'].max()} 分")

            st.subheader("🔥 龍魂戰略總部 - 天外飛仙二次篩選結果")
            st.dataframe(
                df_res_show,
                column_config={
                    "Ticker": "股票/ETF代號",
                    "Category": "資產類別",
                    "SCTR排名": st.column_config.NumberColumn("SCTR 排名", format="%.1f"),
                    "霸王總分": st.column_config.NumberColumn("霸王總分", format="%.1f"),
                    "戰略標籤": st.column_config.TextColumn("戰略標籤 / 爆發訊號", width="large")
                },
                use_container_width=True,
                hide_index=True
            )

if __name__ == "__main__":
    render_page_1a()
