import streamlit as st
import yfinance as yf
import pandas as pd
from openbb import obb

# 🚨 隱形防護罩：確保母艦冷啟動時，記憶體第一時間預備好變數，防止舊分頁報錯
if 'symbol' not in st.session_state:
    st.session_state['symbol'] = 'NVDA'

# 🚀【極簡直連咒語】：直接召喚所有分艙
from page1 import render_stock_tab
import page_1a  # 🎯 爺爺新增：匯入全新 1a 艙房 (天外飛仙)
from page2 import render_options_tab
from page_2a import render_breadth_tab          
from page_2b import render_master_tower_tab     
from page_2c import render_sentiment_macro_tab   
from page_2bb import render_page_2bb  
from page_2bb_hk import render_page_2bb_hk  
from page_2e import render_page_2e  
from page_2e_hk import render_page_2e_hk  
from page_2f import render_page_2f  
from page_2g import render_page_2g  
from page_2h import render_page_2h  
from page_2i import render_page_2i  
from page_2j import render_page_2j  
from page_2k import render_page_2k  
from page_2l import render_page_2l  
from page_2m import render_page_2m  
from page_2n import render_page_2n  
from page_2o import render_page_2o  
from page_2p import render_page_2p  

# 🚨 爺爺萬能防爆注入：匯入整隻模組，避開函數名稱對不上的 ImportError
import page_2q
import page_2r
import page_2s
import page_2t
import page_2u

from page_2v import render as render_page_2v  
from page_2w import app as render_page_2w   
from page_2w_vwap import app as render_page_2w_vwap 
from page_2x import app as render_page_2x   
from page_2y import app as render_page_2y   
import page_2z 

from page3 import render_macro_tab
from page4 import render_page4  
from pages_5 import render_page5  
from page_ai_prompt import render_prompt_generator  

# 💡 爺爺「萬能相容執行器」：自動掃描並執行 2q-2u 模組內的任何渲染函數！
def run_fed_module(module):
    possible_names = [
        'render_page_2q', 'render_page_2r', 'render_page_2s', 'render_page_2t', 'render_page_2u', 
        'render', 'render_dashboard', 'render_wpc', 'render_btfp', 'render_swpt', 'render_rpf', 'main'
    ]
    for func_name in possible_names:
        if hasattr(module, func_name):
            getattr(module, func_name)()
            return
    st.warning("⚠️ 該 Fed 艙房模組未找到對應的 render() 執行函數。")

# --- 頁面配置 ---
st.set_page_config(
    page_title="全球及亞太區資產動態追蹤系統",
    page_icon="🌐",
    layout="wide",
    initial_sidebar_state="expanded"
)

# 🧙‍♂️ 爺爺的 CSS 黑客魔法：強行將側邊欄 Radio 變成「先直後橫」雙排佈局
st.markdown("""
<style>
    /* 鎖定側邊欄入面嘅單選掣群組，轉為 Column 雙直行佈局 */
    [data-testid="stSidebar"] [role="radiogroup"] {
        column-count: 2 !important;  /* 分割成兩直行 */
        column-gap: 10px !important; /* 左右間距 */
        display: block !important;   /* 取消之前的 Grid 佈局 */
    }
    /* 防止單個選項跨欄斷開，並設定上下間距 */
    [data-testid="stSidebar"] [role="radiogroup"] > label {
        break-inside: avoid !important;
        margin-bottom: 8px !important; 
        display: flex !important;
    }
    /* 稍微縮細字體，防止字數太長逼爆格，同時隱藏超出範圍的文字並加上省略號 */
    [data-testid="stSidebar"] [role="radiogroup"] span {
        font-size: 13px !important;
        white-space: nowrap; 
        overflow: hidden;
        text-overflow: ellipsis;
    }
</style>
""", unsafe_allow_html=True)

st.markdown("<h1>🌐 大指揮官・全球資產與期權量化終端</h1>", unsafe_allow_html=True)

# =========================================================================
# 🎮 👑 核心框架改造：左側鋼鐵戰略側邊欄
# =========================================================================
st.sidebar.markdown("## 🧭 戰略艙房導航中心")

# 🎯 集中定義導航選項字典
NAV_OPTIONS = {
    "P1": "📊 艙房一：六維王者矩陣 (股票)",
    "P1A": "🛸 艙房 1a：天外飛仙 (RS 強勢爆發)", # 🎯 爺爺新增：完美安插在 P1 與 P2 之間
    "P2": "🔥 艙房二：期權多維雷達 (Options)",
    "P2A": "📊 艙房 2a：全球市場市寬大面板",
    "P2B": "🛡️ 艙房 2b：環球市底大師指揮塔",
    "P2C": "🦅 艙房 2c：宏觀恐懼與美債雷達",
    "P2BB": "📡 艙房 2bb：個股版塊拔河熱力圖 (美股)",
    "P2BB_HK": "🇭🇰 艙房 2bb-HK：個股版塊拔河熱力圖 (港股)",
    "P2E": "🧩 艙房 2e：美股原版真實市寬",
    "P2E_HK": "🧩 艙房 2e-HK：港股原版真實市寬",
    "P2F": "🧩 艙房 2f：債市恐慌 MOVE 終極拆解",
    "P2G": "🧩 艙房 2g：FRED (BofA 高收益債利差) + HYG",
    "P2H": "🧩 艙房 2h：銅期貨 HG=F / 金期貨 GC=F 或 COPX/GLD",
    "P2I": "☢️ 艙房 2i：SEC Form 4 / 國會巨鯨內幕",
    "P2J": "🧲 艙房 2j：期權全量鏈 (yfinance) / 暗池 DIX",
    "P2K": "🌊 艙房 2k：美聯儲流動性水閘 (Fed Net Liquidity)",
    "P2L": "📉 艙房 2L：VIX 恐慌期限結構 (Term Structure)",
    "P2M": "🎡 艙房 2m：華爾街板塊輪動星盤 (Sector Rotation)",
    "P2N": "🏛️ 艙房 2n：壓箱底第一絕 (解除倒掛 Bull Steepener)",
    "P2O": "🏛️ 艙房 2o : 壓箱底第二絕 (VVIX暗流)",
    "P2P": "🏛️ 艙房 2p : 壓箱底第三絕 HYG 與信貸利差",
    "P2Q": "🏦 艙房 2q：美聯儲應急總覽 (Fed Dashboard)",
    "P2R": "🔴 艙房 2r：貼現窗口 (WPC)",
    "P2S": "🟢 艙房 2s：銀行融資 (BTFP)",
    "P2T": "🔵 艙房 2t：央行互換 (SWPT)",
    "P2U": "🟡 艙房 2u：外國逆回購 (RPF)",
    "P2V": "⚖️ 艙房 2v : SPHB / SPLV Ratio (高低波幅比率)",
    "P2W": "🚨 艙房 2w : 四維市寬背馳雷達 (Divergence)", 
    "P2ALPHA": "⚖️ 艙房 2α : 真・好淡分界線 (VWAP & POC)",
    "P2X": "⚔️ 艙房 2x : 華爾街市寬雙核神兵 (MCO & ZBT)", 
    "P2Y": "🌌 艙房 2y : 全球資金同步與板塊星盤 (MISE)", 
    "P2Z": "👁️ 艙房 2z : AI 象形圖表與幾何諧波雷達", 
    "P3": "🌊 艙房三：全球宏觀資金流 (Liquidity)",
    "P4": "🔴 艙房四：機構堡壘情報局 (Bloomberg/RSS)",
    "P5": "🔴 艙房五：機構大鱷持倉與資金流 (13F/EPFR)",
    "P6": "🤖 艙房六：AI 馴服與絕對軍令中心"
}

page_choice = st.sidebar.radio("請點擊切換進入艙房：", list(NAV_OPTIONS.values()))
st.sidebar.markdown("---")

# --- 側邊控制面板 ---
st.sidebar.markdown("### 🛠️ 系統控制面板")
market_type = st.sidebar.selectbox("選擇市場", ["美股", "港股", "日股", "韓股", "台股", "A股", "加密貨幣"])

st.session_state["global_market"] = f"{market_type}陣列"

hints = {
    "美股": "例如：NVDA, AAPL, TSLA", "港股": "例如：0700.HK, 9988.HK (須加 .HK)", "日股": "例如：7203.T", 
    "韓股": "官例：005930.KS", "台股": "例如：2330.TW", "A股": "例如：600519.SS", "加密貨幣": "例如：BTC-USD"
}
st.sidebar.info(f"💡 **輸入格式提示：**\n{hints[market_type]}")

symbol = st.sidebar.text_input("輸入資產代號", value="NVDA" if market_type == "美股" else "0388.HK" if market_type == "港股" else "7203.T")

if st.session_state.get('symbol') != symbol:
    st.session_state['symbol'] = symbol

period = st.sidebar.selectbox("選擇股票 analysis 週期", ["1mo", "3mo", "6mo", "1y", "5y"], index=1)
global_days = st.sidebar.selectbox("📡 拔河熱力圖戰術時間窗", [20, 5], index=0)
st.session_state["global_days"] = global_days

# =========================================================================
# ⚙ 數據分流渲染中心
# =========================================================================
if symbol:
    try:
        ticker = yf.Ticker(symbol)
        df = ticker.history(period="1y")
        if df.empty:
            st.error("❌ 找不到該資產的數據，請檢查代號格式是否正確！")
        else:
            if page_choice == NAV_OPTIONS["P1"]:
                try: render_stock_tab(df, period, market_type, symbol)
                except Exception as e: st.error(f"⚠️ 艙房一系統不兼容: {e}")
                
            elif page_choice == NAV_OPTIONS["P1A"]:  # 🎯 爺爺新增：1a 艙房 Routing
                try: page_1a.render_page_1a()
                except Exception as e: st.error(f"⚠️ 艙房 1a 系統不兼容: {e}")
                
            elif page_choice == NAV_OPTIONS["P2"]:
                try:
                    df_clean_for_opt = df.dropna(subset=['Close']).copy()
                    render_options_tab(ticker, market_type, symbol, df_clean_for_opt)
                except Exception as e: st.error(f"⚠ 艙房二系統不兼容: {e}")
                
            elif page_choice == NAV_OPTIONS["P2A"]:
                try: render_breadth_tab()
                except Exception as e: st.error(f"⚠ 艙房 2a 系統不兼容: {e}")
                
            elif page_choice == NAV_OPTIONS["P2B"]:
                try: render_master_tower_tab()
                except Exception as e: st.error(f"⚠️ 艙房 2b 系統不兼容: {e}")
                
            elif page_choice == NAV_OPTIONS["P2C"]:
                try: render_sentiment_macro_tab()
                except Exception as e: st.error(f"⚠️ 艙房 2c 系統不兼容: {e}")
                
            elif page_choice == NAV_OPTIONS["P2BB"]:
                try: render_page_2bb()
                except Exception as e: st.error(f"⚠️ 艙房 2bb 系統不兼容: {e}")
                
            elif page_choice == NAV_OPTIONS["P2BB_HK"]: 
                try: render_page_2bb_hk()
                except Exception as e: st.error(f"⚠️ 港股艙房 2bb-HK 系統不兼容: {e}")
                
            elif page_choice == NAV_OPTIONS["P2E"]:  
                try: render_page_2e()
                except Exception as e: st.error(f"⚠️ 艙房 2e 系統不兼容: {e}")

            elif page_choice == NAV_OPTIONS["P2E_HK"]:  
                try: render_page_2e_hk()
                except Exception as e: st.error(f"⚠️ 艙房 2e-HK 系統不兼容: {e}")
                
            elif page_choice == NAV_OPTIONS["P2F"]:
                try: render_page_2f()
                except Exception as e: st.error(f"⚠️ 艙房 2f 系統不兼容: {e}")

            elif page_choice == NAV_OPTIONS["P2G"]:
                try: render_page_2g()
                except Exception as e: st.error(f"⚠️ 艙房 2g 系統不兼容: {e}")
                
            elif page_choice == NAV_OPTIONS["P2H"]:  
                try: render_page_2h()
                except Exception as e: st.error(f"⚠️ 艙房 2h 系統不兼容: {e}")
                
            elif page_choice == NAV_OPTIONS["P2I"]:  
                try: render_page_2i()
                except Exception as e: st.error(f"⚠️ 艙房 2i 系統不兼容: {e}")
                
            elif page_choice == NAV_OPTIONS["P2J"]:  
                try: render_page_2j()
                except Exception as e: st.error(f"⚠️ 艙房 2j 系統不兼容: {e}")
                
            elif page_choice == NAV_OPTIONS["P2K"]:  
                try: render_page_2k()
                except Exception as e: st.error(f"⚠️ 艙房 2k 系統不兼容: {e}")
                
            elif page_choice == NAV_OPTIONS["P2L"]:  
                try: render_page_2l()
                except Exception as e: st.error(f"⚠ 艙房 2L 系統不兼容: {e}")
                
            elif page_choice == NAV_OPTIONS["P2M"]:  
                try: render_page_2m()
                except Exception as e: st.error(f"⚠️ 艙房 2m 系統不兼容: {e}")
                
            elif page_choice == NAV_OPTIONS["P2N"]:  
                try: render_page_2n()
                except Exception as e: st.error(f"⚠️ 艙房 2n 系統不兼容: {e}")
                
            elif page_choice == NAV_OPTIONS["P2O"]:  
                try: render_page_2o()
                except Exception as e: st.error(f"⚠️ 艙房 2o 系統不兼容: {e}")

            elif page_choice == NAV_OPTIONS["P2P"]:  
                try: render_page_2p()
                except Exception as e: st.error(f"⚠️ 艙房 2p 系統不兼容: {e}")

            elif page_choice == NAV_OPTIONS["P2Q"]:
                try: run_fed_module(page_2q)
                except Exception as e: st.error(f"⚠️ 艙房 2q 系統不兼容: {e}")

            elif page_choice == NAV_OPTIONS["P2R"]:
                try: run_fed_module(page_2r)
                except Exception as e: st.error(f"⚠️ 艙房 2r 系統不兼容: {e}")

            elif page_choice == NAV_OPTIONS["P2S"]:
                try: run_fed_module(page_2s)
                except Exception as e: st.error(f"⚠️ 艙房 2s 系統不兼容: {e}")

            elif page_choice == NAV_OPTIONS["P2T"]:
                try: run_fed_module(page_2t)
                except Exception as e: st.error(f"⚠️ 艙房 2t 系統不兼容: {e}")

            elif page_choice == NAV_OPTIONS["P2U"]:
                try: run_fed_module(page_2u)
                except Exception as e: st.error(f"⚠️ 艙房 2u 系統不兼容: {e}")
                
            elif page_choice == NAV_OPTIONS["P2V"]:  
                try: render_page_2v()
                except Exception as e: st.error(f"⚠️ 艙房 2v 系統不兼容: {e}")
                
            elif page_choice == NAV_OPTIONS["P2W"]:  
                try: render_page_2w()
                except Exception as e: st.error(f"⚠️ 艙房 2w 系統不兼容: {e}")

            elif page_choice == NAV_OPTIONS["P2ALPHA"]:  
                try: render_page_2w_vwap()
                except Exception as e: st.error(f"⚠️ 艙房 2α 系統不兼容: {e}")

            elif page_choice == NAV_OPTIONS["P2X"]:  
                try: render_page_2x()
                except Exception as e: st.error(f"⚠️ 艙房 2x 系統不兼容: {e}")

            elif page_choice == NAV_OPTIONS["P2Y"]:  
                try: render_page_2y()
                except Exception as e: st.error(f"⚠️ 艙房 2y 系統不兼容: {e}")

            elif page_choice == NAV_OPTIONS["P2Z"]:  
                try: page_2z.render_page_2z()
                except Exception as e: st.error(f"⚠️ 艙房 2z 系統不兼容: {e}")
                
            elif page_choice == NAV_OPTIONS["P3"]:
                try: render_macro_tab()
                except Exception as e: st.error(f"⚠ 艙房三系統不兼容: {e}")
                
            elif page_choice == NAV_OPTIONS["P4"]:
                try: render_page4()
                except Exception as e: st.error(f"⚠️ 艙房四系統不兼容: {e}")
                
            elif page_choice == NAV_OPTIONS["P5"]:
                try: render_page5()
                except Exception as e: st.error(f"⚠️ 艙房五系統不兼容: {e}")
                
            elif page_choice == NAV_OPTIONS["P6"]:
                try: render_prompt_generator()
                except Exception as e: st.error(f"⚠ 艙房六系統不兼容: {e}")
                
    except Exception as e: 
        st.error(f"⚠️ 系統抓取數據時發生錯誤: {str(e)}")

# -----------------------------------------------------------------
# 🎯 華爾街主力資金 —— 精細題材流向雷達
# -----------------------------------------------------------------
st.markdown("---")
st.markdown("### 🎯 華爾街主力資金 —— 精細題材流向雷達 (Detailed Sectors)")

try:
    sector_data = obb.economy.sectors(provider="fmp")
    df_sec = sector_data.to_df()
    if not df_sec.empty:
        df_sorted = df_sec.sort_values(by="change", ascending=False)
        df_sorted = df_sorted.rename(columns={
            "sectorName": "精細題材/行業名稱",
            "change": "今日主力資金漲跌幅 (%)"
        })
        st.dataframe(df_sorted[["精細題材/行業名稱", "今日主力資金漲跌幅 (%)"]], use_container_width=True)
    else:
        st.warning("⚠ 數據源正在更新，請稍後重試。")
except Exception as e:
    st.info("🔄 OpenBB 細分行業資料庫正在後台建立索引中...")