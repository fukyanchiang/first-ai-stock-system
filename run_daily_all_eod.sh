#!/bin/bash
# -------------------------------------------------------------
# 🚀 美股盤後全天網、科技先鋒與板塊監測全自動同步防彈腳本
# -------------------------------------------------------------

export PATH="/Library/Developer/CommandLineTools/usr/bin:/usr/local/bin:/usr/bin:/bin:/usr/sbin:/sbin"
cd /Users/nam/Desktop/asset_tracker

# 鎖定有效 Python 直譯器
if [ -f "/Users/nam/Desktop/asset_tracker/venv/bin/python" ]; then
    PY="/Users/nam/Desktop/asset_tracker/venv/bin/python"
else
    PY="/Library/Developer/CommandLineTools/usr/bin/python3"
fi

LOG_FILE="/Users/nam/Desktop/asset_tracker/eod_auto.log"

echo "==================================================" >> "$LOG_FILE"
echo "🕒 [$(date '+%Y-%m-%d %H:%M:%S')] 啟動每日盤後數據全自動同步..." >> "$LOG_FILE"

# 1. 美股全天網 (Market Monitor)
echo "📡 [1/2] 正在同步美股全天網..." >> "$LOG_FILE"
$PY market_monitor_sync_all_indices_eod.py >> "$LOG_FILE" 2>&1

# 2. 科技先鋒 (Nasdaq & AI Monitor)
echo "⚡ [2/2] 正在同步納指科技先鋒..." >> "$LOG_FILE"
$PY _01_page_market_monitor_sync_nasdaq_tech_eod.py >> "$LOG_FILE" 2>&1

# 3. 如果專案內有獨立的全球板塊同步腳本，自動跟進執行
if [ -f "sync_sector_monitor_eod.py" ]; then
    echo "🌐 [3/3] 正在同步全球板塊矩陣..." >> "$LOG_FILE"
    $PY sync_sector_monitor_eod.py >> "$LOG_FILE" 2>&1
fi

echo "✅ [$(date '+%Y-%m-%d %H:%M:%S')] 全天網數據自動同步完畢！" >> "$LOG_FILE"
echo "==================================================" >> "$LOG_FILE"
