import os
import subprocess

# 1. 自動校正並生成 run_daily_all_eod.sh
sh_path = "/Users/nam/Desktop/asset_tracker/run_daily_all_eod.sh"
sh_code = """#!/bin/bash
cd /Users/nam/Desktop/asset_tracker

if [ -f "venv/bin/python" ]; then
    PY="venv/bin/python"
else
    PY="python3"
fi

echo "========================================" >> eod_auto.log
echo "🚀 [$(date)] 啟動美股全天網與科技先鋒數據同步..." >> eod_auto.log

$PY market_monitor_sync_all_indices_eod.py >> eod_auto.log 2>&1
$PY _01_page_market_monitor_sync_nasdaq_tech_eod.py >> eod_auto.log 2>&1

echo "✅ [$(date)] 雙軌數據自動更新完成！" >> eod_auto.log
echo "========================================" >> eod_auto.log
"""

with open(sh_path, "w", encoding="utf-8") as f:
    f.write(sh_code)

os.chmod(sh_path, 0o755)
print("✅ 1. 成功建立並授權：run_daily_all_eod.sh")

# 2. 自動加入 Mac crontab 排程
cron_line = "0 6 * * 2-6 /Users/nam/Desktop/asset_tracker/run_daily_all_eod.sh\n"

try:
    old_cron = subprocess.check_output(["crontab", "-l"]).decode("utf-8")
except Exception:
    old_cron = ""

if "run_daily_all_eod.sh" in old_cron:
    print("ℹ️ 2. 排程之前已經加入過，無需重複添加！")
else:
    new_cron = old_cron.strip() + "\n\n# --- 宏觀天網與科技先鋒雙軌 EOD 自動同步 ---\n" + cron_line
    proc = subprocess.run(["crontab", "-"], input=new_cron.encode("utf-8"))
    if proc.returncode == 0:
        print("✅ 2. 成功寫入 Mac 系統排程 (每週二至週六清晨 6:00 自動執行)！")
    else:
        print("❌ 寫入 crontab 失敗")

print("\n" + "=" * 50)
print("🎉 大功告成！全自動無人駕駛已經啟動！")
print("以後每個美股交易日收市後，Mac 都會自動在背景更新數據。")
print("=" * 50)