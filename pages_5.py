import streamlit as st
import pandas as pd
import os

# =========================================================
# ❄️ 爺爺加裝：大鱷數據永生冷藏庫 (一槍穿透硬碟，RAM級秒彈)
# =========================================================
@st.cache_data(ttl=3600) # 🎯 記憶體冷藏 1 小時，期間切換分頁絕對不准重新讀取硬碟！
def load_and_clean_excel(filepath):
    # 將重型讀取和欄位清洗封裝在快取中
    df_excel = pd.read_excel(filepath, sheet_name=0, header=None)
    df_excel = df_excel.dropna(subset=[0]) 
    df_excel.columns = ['Ticker', 'History', 'Sector', 'Shares', 'Value', 'Percentage', 'Previous_Pct', 'Rank', 'Change_in_Shares'] + list(df_excel.columns[9:])
    df_excel['Ticker_Str'] = df_excel['Ticker'].astype(str).str.strip().str.upper()
    return df_excel

def render_page5():
    # 🌟 頂部大標題
    st.markdown("<h1 style='color:#ff3333; font-size:46px; text-align:left; font-family:Arial Black;'>🔴 艙房五：華爾街頂級大鱷持倉情報局 (13F Radar)</h1>", unsafe_allow_html=True)
    st.markdown("<hr style='border:3px solid #ff3333; margin:20px 0;'>", unsafe_allow_html=True)
    
    # ⚙️ 選擇大鱷選單 (字體放大)
    st.markdown("<p style='color:#00f2ff; font-size:24px; font-weight:bold; margin-bottom:5px;'>⚙️ 請選擇要解鎖的華爾街主力大腦 / 科技狙擊手：</p>", unsafe_allow_html=True)
    
    god_target = st.selectbox(
        "Select Target",
        [
            "🦅 科技叛徒：Leopold Aschenbrenner (Situational Awareness LP)", 
            "🧙‍♂️ 股神：巴菲特 (Berkshire Hathaway)", 
            "大鱷：索羅斯 (Soros Fund Management)",
            "🏛️ 政壇女股神：佩洛西 (Nancy Pelosi Tracker)"
        ],
        label_visibility="collapsed",
        key="p5_w4_selectbox"
    )
    
    filepath = "filer_summary_sample(1).xlsx"
    
    # 🛠️ 巨型自訂 HTML 表格生成器 (保證字體超大、排版超精美)
    def render_huge_html_table(df, is_short=False):
        border_color = "#ff3333" if is_short else "#00ff88"
        text_color = "#ff9999" if is_short else "#99ffcc"
        
        html = f"""
        <table style="width:100%; border-collapse:collapse; font-size:22px; color:#ffffff; background-color:#141b29; border:3px solid {border_color}; font-family:Arial, sans-serif;">
            <tr style="background-color:#1f293d; color:{border_color}; font-weight:bold; text-align:left; border-bottom:3px solid {border_color};">
        """
        for col in df.columns:
            html += f'<th style="padding:16px; border:1px solid #304156;">{col}</th>'
        html += '</tr>'
        
        for _, row in df.iterrows():
            html += f'<tr style="border-bottom:1px solid #304156; hover {{background-color: #1e2638;}}">'
            # 第一個欄位(代號)特別加粗高亮
            html += f'<td style="padding:16px; border:1px solid #304156; font-weight:bold; color:{text_color};">{row.iloc[0]}</td>'
            for val in row.iloc[1:]:
                html += f'<td style="padding:16px; border:1px solid #304156;">{val}</td>'
            html += '</tr>'
        html += '</table>'
        return html

    # ⚙️ 數據清洗清洗核心
    def clean_num_str(val):
        if pd.isnull(val): return "不詳"
        s = str(val).replace('$', '').replace(',', '').strip()
        try:
            num = float(s)
            if num >= 1e9: return f"${num/1e9:.2f} 億"
            if num >= 1e4: return f"${num/1e4:.2f} 萬"
            return f"${num:,.0f}"
        except:
            return str(val)

    def safe_shares(val):
        if pd.isnull(val): return "不詳"
        s = str(val).replace(',', '').strip()
        try:
            return f"{int(float(s)):,}"
        except:
            return "不詳" if s == "" or s.lower() == 'nan' else str(val)

    def safe_pct(val):
        if pd.isnull(val) or str(val).strip() == "" or str(val).lower() == 'nan': 
            return "---"
        try:
            num = float(str(val).replace('%', '').strip())
            if num <= 1.0 and num > 0:
                return f"{num*100:.2f}%"
            return f"{num:.2f}%"
        except:
            return str(val)

    def safe_change_shares(val):
        if pd.isnull(val) or str(val).strip() == "" or str(val).lower() == 'nan': 
            return "<span style='color:#00ff88; font-weight:bold;'>✨ New 新開倉</span>"
        s = str(val).replace(',', '').replace('+', '').strip()
        try:
            num = int(float(s))
            if num > 0:
                return f"<span style='color:#00ff88; font-weight:bold;'>🔼 +{num:,}</span>"
            elif num < 0:
                return f"<span style='color:#ff3333; font-weight:bold;'>🔽 {num:,}</span>"
            else:
                return "<span style='color:#8892b0;'>持平</span>"
        except:
            return str(val)

    # 🦅 當前選擇 Leopold (讀取實體大字 Excel)
    if "Leopold" in god_target:
        if os.path.exists(filepath):
            try:
                # ⚡ 核心冷藏升級：直接吃 RAM 記憶體快取，跳過實體硬碟讀取！
                df_excel = load_and_clean_excel(filepath)
                
                df_put = df_excel[df_excel['Ticker_Str'].str.endswith('PUT')].copy()
                df_call = df_excel[df_excel['Ticker_Str'].str.endswith('CALL')].copy()
                df_long = df_excel[~df_excel['Ticker_Str'].str.endswith(('PUT', 'CALL'))].copy()
                
                st.markdown(f"""
                <div style="background-color:#141b29; padding:20px; border-radius:10px; border:3px solid #00ff88; margin-top:15px; margin-bottom:25px;">
                    <p style="color:#00ff88; font-size:26px; font-weight:bold; margin-bottom:5px; font-family:Arial Black;">🔥 報告大指揮官：天網大字情報系統點火成功！</p>
                    <p style="color:#ffffff; font-size:20px; margin:0;">成功解析共 <b>{len(df_excel)}</b> 筆機構核心真倉數據。冷藏裝甲已上線，切換分頁 0 秒彈出！</p>
                </div>
                """, unsafe_allow_html=True)
                
                # ❌ 左側：空頭期權
                st.markdown("<h2 style='color:#ff3333; font-size:32px; font-weight:bold; margin-top:20px; margin-bottom:15px;'>❌ 晶片供應鏈空頭防線 (真實 Put / Call 期權明冊)</h2>", unsafe_allow_html=True)
                df_options = pd.concat([df_put, df_call])
                if not df_options.empty:
                    show_options = pd.DataFrame({
                        "📈 期權標的": df_options['Ticker'],
                        "🔢 申報價值": df_options['Value'].apply(clean_num_str),
                        "📊 本季佔比": df_options['Percentage'].apply(safe_pct),
                        "⏳ 上季佔比": df_options['Previous_Pct'].apply(safe_pct),
                        "🧱 持有股數": df_options['Shares'].apply(safe_shares),
                        "🔄 股數變動": df_options['Change_in_Shares'].apply(safe_change_shares)
                    })
                    st.markdown(render_huge_html_table(show_options, is_short=True), unsafe_allow_html=True)
                else:
                    st.markdown("<p style='font-size:20px; color:white;'>未偵測到期權持倉</p>", unsafe_allow_html=True)
                
                st.markdown("<br><hr style='border:1px dashed #304156;'><br>", unsafe_allow_html=True)
                
                # ✅ 右側：多頭現貨
                st.markdown("<h2 style='color:#00ff88; font-size:32px; font-weight:bold; margin-top:20px; margin-bottom:15px;'>✅ 真金白銀多頭基建（真實多頭現貨明冊）</h2>", unsafe_allow_html=True)
                if not df_long.empty:
                    show_long = pd.DataFrame({
                        "📈 持有現貨": df_long['Ticker'],
                        "🔢 持倉市值": df_long['Value'].apply(clean_num_str),
                        "📊 本季佔比": df_long['Percentage'].apply(safe_pct),
                        "⏳ 上季佔比": df_long['Previous_Pct'].apply(safe_pct),
                        "🧱 持有股數": df_long['Shares'].apply(safe_shares),
                        "🔄 股數變動": df_long['Change_in_Shares'].apply(safe_change_shares)
                    })
                    st.markdown(render_huge_html_table(show_long, is_short=False), unsafe_allow_html=True)
                else:
                    st.markdown("<p style='font-size:20px; color:white;'>未偵測到現貨持倉</p>", unsafe_allow_html=True)

                # ===================================================
                # 🧠 大腦同步情報網 (維持實時刷新發送)
                # ===================================================
                try:
                    top_3_long = df_long.sort_values(by='Value', ascending=False).head(3)
                    top_3_str = ", ".join([f"{row['Ticker']}" for _, row in top_3_long.iterrows()])
                    
                    summary = (
                        f"【艙房五 13F 機構大鱷持倉戰報】：\n"
                        f"1. 監測目標：{god_target}\n"
                        f"2. 倉位結構：現貨持倉有 {len(df_long)} 筆，期權對沖持倉有 {len(df_options)} 筆。\n"
                        f"3. 前三大核心多頭底牌現貨：{top_3_str}。\n"
                        f"4. 戰略提示：大鱷正用真金白銀砸出基建底牌，AI 判定策略時應高度參考大鱷前三大的權重排陣。"
                    )
                    st.session_state["data_page5"] = summary
                except Exception as e:
                    st.session_state["data_page5"] = f"【艙房五】：成功解析大鱷數據，但拼裝大腦戰報時發生錯誤 ({e})。"
                    
                return 
            except Exception as e:
                st.warning(f"⚠️ 數據解析中 (異常: {e})")
        
        st.markdown("<p style='font-size:22px; color:#8892b0;'>💡 提示：請將下載的大鱷 Excel 命名為 filer_summary_sample(1).xlsx 並放入專案資料夾，即可在此解鎖大字真倉明細！</p>", unsafe_allow_html=True)
        st.session_state["data_page5"] = f"【艙房五】：已選擇 Leopold 觀測目標，但因項目資料夾缺乏 `{filepath}` 檔案，目前無法提煉核心持倉報告。"
        
    else:
        st.markdown(f"<div style='background-color:#1c2431; padding:30px; border-radius:10px; border:2px solid #00f2ff; margin-top:20px;'>"
                    f"<p style='color:#00f2ff; font-size:26px; font-weight:bold;'>🎯 已鎖定未來擴展目標：{god_target}</p>"
                    f"<p style='color:#ffffff; font-size:22px;'>等大指揮官下一個季度從免費管道（如 Dataroma 或 Capitol Trades）複製新數據後，隨時用新 Excel 覆蓋進來，即可享受同等規格的巨型字體情報大圖表！</p>"
                    f"</div>", unsafe_allow_html=True)
        
        st.session_state["data_page5"] = f"【艙房五 機構大鱷持倉】：目前已鎖定未來的戰略目標為【{god_target}】。該模組處於沙盤待命狀態。"

if __name__ == "__main__":
    st.set_page_config(layout="wide")
    render_page5()