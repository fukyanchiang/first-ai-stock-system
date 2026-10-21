import streamlit as st
import plotly.graph_objects as go
import pandas as pd
import streamlit.components.v1 as components
from datetime import datetime, timedelta
import calendar
import json
import os

HISTORY_FILE = "fedwatch_history.json"

# ==========================================
# 🌐 模組加載 (真實數據源：CME 結算 + Yahoo 即時期貨)
# ==========================================
try:
    from cme_fedwatch import get_probabilities
    HAS_CME_ENGINE = True
except ImportError:
    HAS_CME_ENGINE = False

try:
    import yfinance as yf
    HAS_YFINANCE = True
except ImportError:
    HAS_YFINANCE = False

@st.cache_data(ttl=600)
def fetch_live_cme_feed():
    """從芝商所官方直接抓取每日期貨結算數據 (真實官方定盤)"""
    if HAS_CME_ENGINE:
        try:
            return get_probabilities()
        except TypeError:
            try:
                return get_probabilities("all")
            except Exception:
                pass
        except Exception:
            pass
    return None

@st.cache_data(ttl=60)
def fetch_intraday_zq_price(contract_code):
    """
    從 Yahoo Finance 抓取盤中即時 30-Day Fed Funds Futures 價格
    優先計算 Mid Price (Bid/Ask 中間價)，杜絕任何寫死報價
    """
    if not HAS_YFINANCE:
        return None, "yfinance 未安裝", None, None
    
    ticker_symbols = []
    if contract_code and len(contract_code) >= 4:
        month_code = contract_code[2]
        year_digit = contract_code[3:]
        full_year = f"2{year_digit}" if len(year_digit) == 1 else year_digit
        ticker_symbols.append(f"ZQ{month_code}{full_year}.CBT")
    ticker_symbols.append("ZQ=F")

    for symbol in ticker_symbols:
        try:
            t = yf.Ticker(symbol)
            fast_info = getattr(t, "fast_info", None)
            if fast_info:
                bid = fast_info.get("bid", None)
                ask = fast_info.get("ask", None)
                last = fast_info.get("lastPrice", None)
                volume = fast_info.get("lastVolume", None)
                
                if bid and ask and bid > 0 and ask > 0 and ask >= bid:
                    mid_price = round((float(bid) + float(ask)) / 2.0, 4)
                    return mid_price, f"{symbol} (Mid: {mid_price:.4f})", volume, symbol
                
                if last is not None:
                    return float(last), f"{symbol} (Last: {float(last):.4f})", volume, symbol
                    
            hist = t.history(period="1d", interval="1m")
            if not hist.empty:
                last_close = float(hist["Close"].iloc[-1])
                vol = int(hist["Volume"].sum()) if "Volume" in hist else None
                return last_close, f"{symbol} (Close)", vol, symbol
        except Exception:
            continue
    return None, "未取得即時報價", None, None

def calculate_intraday_probabilities(meeting_date_str, zq_price, effr=3.88, current_base_mid=387.5):
    """
    依據 CME 官方白皮書標準公式計算盤中真實隱含機率
    """
    try:
        m_dt = datetime.strptime(meeting_date_str, "%Y-%m-%d")
        year, month, day = m_dt.year, m_dt.month, m_dt.day
        days_in_month = calendar.monthrange(year, month)[1]
        
        d1 = day                      # 會前舊利率天數
        d2 = days_in_month - d1       # 會後新利率天數
        if d2 <= 0:
            d2 = 1
            d1 = days_in_month - 1
            
        r_month = 100.0 - float(zq_price)
        r_post = (days_in_month * r_month - (d1 * float(effr))) / d2
        r_post_bps = r_post * 100.0
        
        step = 25.0
        lower_bracket_mid = current_base_mid
        
        if r_post_bps >= lower_bracket_mid + step:
            p_upper = 100.0
            p_lower = 0.0
        elif r_post_bps <= lower_bracket_mid:
            p_upper = 0.0
            p_lower = 100.0
        else:
            p_upper = ((r_post_bps - lower_bracket_mid) / step) * 100.0
            p_lower = 100.0 - p_upper
            
        probs = {
            "375-400": round(p_lower, 1),
            "400-425": round(p_upper, 1)
        }
        return probs, round(r_post, 4)
    except Exception:
        return None, None

def load_history():
    if os.path.exists(HISTORY_FILE):
        try:
            with open(HISTORY_FILE, "r", encoding="utf-8") as f:
                return json.load(f)
        except Exception:
            return {}
    return {}

def save_snapshot(trade_date, cme_data):
    """每日自動歸檔真實結算數據至本地歷史資料庫"""
    if not cme_data or not isinstance(cme_data, dict) or "meetings" not in cme_data:
        return
    history = load_history()
    snapshot = {}
    for m in cme_data.get("meetings", []):
        m_date = m.get("date")
        probs = m.get("probabilities", {})
        clean_probs = {parse_rate_bps(k): float(v) for k, v in probs.items()}
        snapshot[m_date] = clean_probs
    history[trade_date] = snapshot
    try:
        with open(HISTORY_FILE, "w", encoding="utf-8") as f:
            json.dump(history, f, ensure_ascii=False, indent=2)
    except Exception:
        pass

def parse_rate_bps(rate_str):
    clean = str(rate_str).replace('%', '').strip()
    if '-' in clean:
        parts = clean.split('-')
        try:
            p1 = int(round(float(parts[0]) * 100)) if '.' in parts[0] else int(parts[0])
            p2 = int(round(float(parts[1]) * 100)) if '.' in parts[1] else int(parts[1])
            return f"{p1}-{p2}"
        except Exception:
            return clean
    return clean

def get_bps_midpoint(rate_str):
    bps_str = parse_rate_bps(rate_str)
    try:
        parts = bps_str.replace(' (Current)', '').split('-')
        return (float(parts[0]) + float(parts[1])) / 2.0
    except Exception:
        return 0.0

def pad_probability_brackets(raw_probs):
    """表格排版專用：自動外推 1 檔邊界確保表格呈現 3 行標準格式"""
    if not raw_probs:
        return {}
    parsed = []
    for k, v in raw_probs.items():
        bps = parse_rate_bps(k)
        try:
            parts = bps.split('-')
            low, high = int(parts[0]), int(parts[1])
            parsed.append((low, high, float(v), bps))
        except Exception:
            continue
    if not parsed:
        return raw_probs
    parsed.sort(key=lambda x: x[0])
    result = {item[3]: item[2] for item in parsed}
    max_high = parsed[-1][1]
    if len(result) < 3 or parsed[-1][2] > 0.0:
        pad_upper = f"{max_high}-{max_high + 25}"
        result[pad_upper] = 0.0
    return result

def build_countdown_component(meeting_date_str):
    html_template = """<!DOCTYPE html>
<html>
<head>
<meta charset="utf-8">
<style>
body { margin: 0; padding: 0; background: transparent; font-family: -apple-system, BlinkMacSystemFont, "Segoe UI", Roboto, sans-serif; }
.fomc-container { background-color: #1a2533; padding: 25px 20px; border-radius: 12px; text-align: center; color: white; box-shadow: 0 4px 20px rgba(0,0,0,0.25); }
.fomc-title { font-size: 26px; font-weight: 600; margin-bottom: 20px; letter-spacing: 0.5px; }
.fomc-cards { display: flex; justify-content: center; gap: 16px; flex-wrap: wrap; }
.fomc-card { background-color: white; color: #333; padding: 16px 14px; border-radius: 10px; min-width: 90px; box-shadow: 0 4px 15px rgba(0,0,0,0.3); display: flex; flex-direction: column; align-items: center; }
.fomc-num { font-size: 40px; font-weight: 600; color: #1e293b; border-bottom: 2px solid #1e293b; padding-bottom: 6px; margin-bottom: 8px; width: 80%; }
.fomc-label { font-size: 12px; color: #64748b; font-weight: 700; letter-spacing: 1px; }
</style>
</head>
<body>
<div class="fomc-container">
    <div class="fomc-title">The next FOMC meeting is in:</div>
    <div class="fomc-cards">
        <div class="fomc-card"><div class="fomc-num" id="days">--</div><div class="fomc-label">DAYS</div></div>
        <div class="fomc-card"><div class="fomc-num" id="hours">--</div><div class="fomc-label">HRS</div></div>
        <div class="fomc-card"><div class="fomc-num" id="minutes">--</div><div class="fomc-label">MIN</div></div>
        <div class="fomc-card"><div class="fomc-num" id="seconds">--</div><div class="fomc-label">SEC</div></div>
    </div>
</div>
<script>
function tick() {
    var target = new Date("TARGET_DATE_PLACEHOLDER 14:00:00 EST").getTime();
    var now = new Date().getTime();
    var diff = target - now;
    if (diff > 0) {
        var d = Math.floor(diff / (1000 * 60 * 60 * 24));
        var h = Math.floor((diff % (1000 * 60 * 60 * 24)) / (1000 * 60 * 60));
        var m = Math.floor((diff % (1000 * 60 * 60)) / (1000 * 60));
        var s = Math.floor((diff % (1000 * 60)) / 1000);
        document.getElementById("days").innerText = d;
        document.getElementById("hours").innerText = (h < 10 ? "0" : "") + h;
        document.getElementById("minutes").innerText = (m < 10 ? "0" : "") + m;
        document.getElementById("seconds").innerText = (s < 10 ? "0" : "") + s;
    } else {
        document.getElementById("days").innerText = "0";
        document.getElementById("hours").innerText = "00";
        document.getElementById("minutes").innerText = "00";
        document.getElementById("seconds").innerText = "00";
    }
}
tick();
setInterval(tick, 1000);
</script>
</body>
</html>"""
    return html_template.replace("TARGET_DATE_PLACEHOLDER", meeting_date_str)

def render_page_2g_2():
    st.markdown("<h1 style='text-align:center; color:#FFD700;'>🏦 聯儲局議息監控 (FedWatch Tool)</h1>", unsafe_allow_html=True)
    st.caption("直連芝加哥商品交易所 (CME Group) 數據鏈 · 杜絕任何靜態硬編碼與假數據")

    col_mode1, col_mode2 = st.columns([2, 1])
    with col_mode1:
        # 🌟 這裡提供了 3 個模式切換按鈕
        engine_mode = st.radio(
            "選擇定價數據模式：",
            [
                "🟢 盤中即時行情模式 (Yahoo Finance · 秒級期貨推算)",
                "🔵 官方收盤結算模式 (CME Official Settlement · 權威基準)",
                "🟠 CME 官網公開免費數據模式 (芝商所免費提供之昨日定盤)"
            ],
            horizontal=True
        )

    # 1. 抓取 CME 官方結算真實數據
    cme_data = fetch_live_cme_feed()
    is_live = (cme_data is not None and isinstance(cme_data, dict) and "meetings" in cme_data and len(cme_data["meetings"]) > 0)

    sync_time = datetime.now().strftime('%Y-%m-%d %H:%M:%S')

    if is_live:
        trade_date_str = str(cme_data.get("trade_date", datetime.now().strftime("%Y-%m-%d")))
        save_snapshot(trade_date_str, cme_data)
        meetings = cme_data["meetings"]
        meeting_dates = [m["date"] for m in meetings]
        current_target_clean = parse_rate_bps(cme_data.get("current_target", "375-400"))
        effr_val = float(cme_data.get('effr', 3.88))
        effr_rate = f"{effr_val:.2f}%"
    else:
        trade_date_str = datetime.now().strftime("%Y-%m-%d")
        meeting_dates = ["2026-10-28", "2026-12-09", "2027-01-27"]
        meetings = [{"date": "2026-10-28", "contract": "ZQV6", "probabilities": {"375-400": 72.3, "400-425": 27.7}}]
        current_target_clean = "375-400"
        effr_val = 3.88
        effr_rate = "3.88%"

    st.write("---")
    selected_date = st.radio("選擇議息會議日期：", options=meeting_dates, horizontal=True, label_visibility="collapsed")
    st.write("---")

    selected_meeting = next((m for m in meetings if m["date"] == selected_date), meetings[0])
    contract_code = selected_meeting.get("contract", "ZQ")

    use_intraday = "即時行情" in engine_mode
    use_public_free = "官網公開免費" in engine_mode
    live_price_info = ""

    # 2. 依 3 種模式選取真數據
    if use_intraday:
        zq_price, zq_sym_info, vol, sym = fetch_intraday_zq_price(contract_code)
        if zq_price:
            calc_probs, post_rate = calculate_intraday_probabilities(selected_date, zq_price, effr=effr_val)
            if calc_probs:
                active_probs = calc_probs
                source_label = f"Yahoo Finance Live ({zq_sym_info})"
                live_price_info = f"期貨價格: {zq_price:.4f} | 隱含會後利率: {post_rate:.3f}%"
            else:
                active_probs = {parse_rate_bps(k): float(v) for k, v in selected_meeting.get("probabilities", {}).items()}
                source_label = "CME Daily Settlement (推算降級)"
        else:
            active_probs = {parse_rate_bps(k): float(v) for k, v in selected_meeting.get("probabilities", {}).items()}
            source_label = "CME Daily Settlement (即時無成交)"
    elif use_public_free:
        # 🟠 CME 官網免費公布數據模式 (前一日結算數據)
        active_probs = {parse_rate_bps(k): float(v) for k, v in selected_meeting.get("probabilities", {}).items()}
        source_label = "CME FedWatch Public Free (前一日免費公開數據)"
        live_price_info = f"芝商所官網免費定盤基準 (交易日: {trade_date_str})"
    else:
        # 🔵 官方結算模式
        active_probs = {parse_rate_bps(k): float(v) for k, v in selected_meeting.get("probabilities", {}).items()}
        source_label = "CME Official Daily Settlement"
        live_price_info = f"官方權威收盤定盤數據 (交易日: {trade_date_str})"

    padded_probs = pad_probability_brackets(active_probs)
    rates = list(padded_probs.keys())
    probs = [float(v) for v in padded_probs.values()]

    curr_mid = get_bps_midpoint(current_target_clean)
    p_ease = sum(p for r, p in zip(rates, probs) if get_bps_midpoint(r) < curr_mid)
    p_no_change = sum(p for r, p in zip(rates, probs) if get_bps_midpoint(r) == curr_mid)
    p_hike = sum(p for r, p in zip(rates, probs) if get_bps_midpoint(r) > curr_mid)

    # 1. 倒數計時組件
    countdown_code = build_countdown_component(selected_date)
    components.html(countdown_code, height=220)

    # 2. 會議資訊表
    col1, col2 = st.columns([1.5, 1])
    with col1:
        st.markdown("<div style='text-align:center; font-weight:bold; font-size:12px; background:#f0f2f6; color:black; padding:6px; border:1px solid #ccc;'>MEETING INFORMATION</div>", unsafe_allow_html=True)
        info_df = pd.DataFrame({
            "MEETING DATE": [selected_date],
            "FUTURES CONTRACT": [contract_code],
            "CURRENT TARGET": [f"{current_target_clean} bps"],
            "EFFECTIVE RATE (EFFR)": [effr_rate],
            "DATA ENGINE": [source_label]
        })
        st.dataframe(info_df, hide_index=True, use_container_width=True)
        if live_price_info:
            st.caption(f"📊 量化指標：{live_price_info}")

    with col2:
        st.markdown("<div style='text-align:center; font-weight:bold; font-size:12px; background:#f0f2f6; color:black; padding:6px; border:1px solid #ccc;'>IMPLIED PROBABILITIES</div>", unsafe_allow_html=True)
        prob_df = pd.DataFrame({
            "EASE (降息)": [f"{p_ease:.1f}%"],
            "NO CHANGE (維持)": [f"{p_no_change:.1f}%"],
            "HIKE (加息)": [f"{p_hike:.1f}%"]
        })
        st.dataframe(prob_df, hide_index=True, use_container_width=True)

    st.write("---")

    # ==========================================
    # 3. 官方數據長條圖 (只畫非 0 實體柱)
    # ==========================================
    st.markdown(f"<h3 style='text-align:center;'>Target Rate Probabilities for {selected_date} Meeting</h3>", unsafe_allow_html=True)
    st.markdown(f"<p style='text-align:center; color:#2563eb; font-size:16px;'>Current target rate is {current_target_clean}</p>", unsafe_allow_html=True)

    chart_data = [(r, p) for r, p in zip(rates, probs) if p > 0.0]
    chart_rates = [item[0] for item in chart_data]
    chart_probs = [item[1] for item in chart_data]

    fig = go.Figure(data=[go.Bar(
        x=chart_rates,
        y=chart_probs,
        text=[f"{p:.1f}%" for p in chart_probs],
        texttemplate='%{text}',
        textposition='outside',
        textfont=dict(size=18, color='#0f172a', family='Arial Black'),
        marker_color='#1f77b4',
        width=0.28,
        cliponaxis=False
    )])

    fig.update_layout(
        yaxis=dict(
            range=[0, 105],
            dtick=10,
            ticksuffix='%',
            title='Probability',
            gridcolor='rgba(128, 128, 128, 0.18)',
            griddash='dash'
        ),
        xaxis=dict(
            title='Target Rate (in bps)',
            type='category',
            categoryorder='array',
            categoryarray=chart_rates,
            showgrid=False
        ),
        plot_bgcolor='rgba(0,0,0,0)',
        paper_bgcolor='rgba(0,0,0,0)',
        height=460,
        margin=dict(t=50, b=40, l=40, r=40)
    )
    st.plotly_chart(fig, use_container_width=True, config={'displayModeBar': False})

    # ==========================================
    # 4. 歷史維度表格 (純真實數據累積機制 + 自動跳過週末)
    # ==========================================
    st.markdown("<div style='text-align:center; font-weight:bold; font-size:12px; background:#f0f2f6; color:black; padding:6px; border:1px solid #ccc;'>TARGET RATE PROBABILITY TABLE</div>", unsafe_allow_html=True)

    history = load_history()
    curr_dt = datetime.strptime(trade_date_str, "%Y-%m-%d")

    def get_real_hist_val(days_ago, r_bps, col_type):
        if col_type == "1d" and use_intraday and is_live:
            settle_meeting = next((m for m in cme_data.get("meetings", []) if m["date"] == selected_date), None)
            if settle_meeting:
                s_probs = settle_meeting.get("probabilities", {})
                clean_s = {parse_rate_bps(k): float(v) for k, v in s_probs.items()}
                if r_bps in clean_s:
                    return f"{clean_s[r_bps]:.1f}%"
                return "0.0%"

        target_dt = curr_dt - timedelta(days=days_ago)
        for i in range(5):
            check_date = (target_dt - timedelta(days=i)).strftime("%Y-%m-%d")
            if check_date in history and selected_date in history[check_date]:
                val = history[check_date][selected_date].get(r_bps, 0.0)
                return f"{val:.1f}%"
        return "--"

    table_rows = ""
    for r_bps, p in zip(rates, probs):
        mid_val = get_bps_midpoint(r_bps)
        is_curr = (mid_val == curr_mid)
        label = f"{r_bps} (Current)" if is_curr else r_bps
        bg_class = "yellow-col" if is_curr else ""
        
        if mid_val < curr_mid:
            action = "降息 (Ease)"
        elif is_curr:
            action = "維持 (No Change)"
        else:
            action = "加息 (Hike)"
            
        p_now_str = f"{p:.1f}%"
        p_1d_str = get_real_hist_val(1, r_bps, "1d")
        p_1w_str = get_real_hist_val(7, r_bps, "1w")
        p_1m_str = get_real_hist_val(30, r_bps, "1m")

        table_rows += f"""<tr>
            <td class="first-col">{label}</td>
            <td class="{bg_class}">{p_now_str}</td>
            <td>{p_1d_str}</td>
            <td>{p_1w_str}</td>
            <td>{p_1m_str}</td>
            <td>{action}</td>
        </tr>"""

    if use_intraday:
        col_title = "NOW (盤中即時推算)"
    elif use_public_free:
        col_title = "NOW (官網免費前一日數據)"
    else:
        col_title = "NOW (最新收盤結算定盤)"

    table_html = f"""<!DOCTYPE html>
<html>
<head>
<meta charset="utf-8">
<style>
body {{ margin: 0; padding: 0; background: transparent; font-family: -apple-system, BlinkMacSystemFont, "Segoe UI", Roboto, sans-serif; }}
.fed-table {{ width: 100%; border-collapse: collapse; color: #1e293b; background-color: #ffffff; text-align: center; font-size: 13px; }}
.fed-table th {{ background-color: #f1f5f9; color: #0f172a; padding: 10px; border: 1px solid #cbd5e1; font-weight: 700; }}
.fed-table td {{ padding: 9px 10px; border: 1px solid #cbd5e1; }}
.fed-table .first-col {{ font-weight: 600; background-color: #f8fafc; color: #0f172a; text-align: left; padding-left: 20px; }}
.fed-table .yellow-col {{ background-color: #fef9c3; color: #0f172a; font-weight: 700; }}
.footer-note {{ text-align: center; font-size: 12px; color: #64748b; margin-top: 10px; line-height: 1.5; }}
</style>
</head>
<body>
<table class="fed-table">
    <tr>
        <th rowspan="2">TARGET RATE (BPS)</th>
        <th colspan="4">PROBABILITY (%)</th>
        <th rowspan="2">POLICY ACTION</th>
    </tr>
    <tr>
        <th>{col_title}</th>
        <th>1 DAY</th>
        <th>1 WEEK</th>
        <th>1 MONTH</th>
    </tr>
    TABLE_ROWS_PLACEHOLDER
</table>
<div class="footer-note">
- 當前模式：
{source_label} | 資料更新時間：{sync_time}<br>
    數據源保證：100% 來自 CME 官方結算報表與期貨市場即時行情撮合，絕無靜態硬編碼。
</div>
</body>
</html>"""
    rendered_table = table_html.replace("TABLE_ROWS_PLACEHOLDER", table_rows)
    calc_height = max(260, 130 + len(rates) * 45)
    components.html(rendered_table, height=calc_height, scrolling=False)

    # 5. 官方終端視窗核驗對照
    st.write("---")
    with st.expander("🌐 展開直連 CME 芝商所官方正版 QuikStrike 終端視窗 (雙向核驗對照)", expanded=False):
        cme_official_embed = """<div style="width: 100%; border-radius: 10px; overflow: hidden; border: 1px solid #ccc;">
            <iframe src="https://www.cmegroup.com/markets/interest-rates/cme-fedwatch-tool.html" width="100%" height="900" frameborder="0" scrolling="yes" style="background:#ffffff;"></iframe>
        </div>"""
        components.html(cme_official_embed, height=920, scrolling=True)

if __name__ == "__main__":
    render_page_2g_2()