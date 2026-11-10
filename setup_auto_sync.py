"""
Filename: setup_auto_sync.py
Description: ⏰ 一鍵安裝 Mac 盤後全自動排程 (徹底告別 Terminal)
- 港股：週一至週五 下午 16:35 自動同步
- 美股：週二至週六 清晨 05:30 自動同步
"""

import os
import sys
import subprocess

def install_cron():
    cwd = os.path.abspath(os.path.dirname(__file__))
    py_exec = sys.executable

    # 1. 港股排程 (週一至五 16:35)
    hk_job = f"35 16 * * 1-5 cd {cwd} && {py_exec} sync_hk_indices_eod.py --target all >> {cwd}/sync_hk.log 2>&1"
    
    # 2. 美股排程 (週二至六 05:30)
    us_job = f"30 5 * * 2-6 cd {cwd} && {py_exec} sync_all_indices_eod.py --target all >> {cwd}/sync_us.log 2>&1"

    # 讀取現有 crontab
    res = subprocess.run(["crontab", "-l"], stdout=subprocess.PIPE, stderr=subprocess.PIPE, text=True)
    existing = res.stdout if res.returncode == 0 else ""

    # 清除舊排程，換上新排程
    lines = [l for l in existing.splitlines() if "sync_hk_indices_eod.py" not in l and "sync_all_indices_eod.py" not in l and l.strip()]
    lines.append("# --- 港美股市場市寬全自動同步排程 ---")
    lines.append(hk_job)
    lines.append(us_job)
    new_crontab = "\n".join(lines) + "\n"

    # 寫入系統排程
    p = subprocess.Popen(["crontab", "-"], stdin=subprocess.PIPE, text=True)
    p.communicate(input=new_crontab)

    print("\n" + "=" * 50)
    print("🎉 全自動排程已成功安裝進你的 Mac 系統！")
    print("=" * 50)
    print(f"⏰ 港股：每週一至五 下午 16:35 自動同步 (3000/800/500/2000 隻)")
    print(f"⏰ 美股：每週二至六 清晨 05:30 自動同步 (3380/1500/2000/1000 隻)")
    print("📁 日誌檔案將自動記錄在 sync_hk.log 與 sync_us.log")
    print("=" * 50)
    print("🚀 從此以後，你不需要再手動執行任何同步指令，系統全自動運行！\n")

if __name__ == "__main__":
    install_cron()