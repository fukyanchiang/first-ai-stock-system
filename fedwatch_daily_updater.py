import time
import json
import os
import schedule
from datetime import datetime

# 設定你的 JSON 檔案路徑
HISTORY_FILE = "fedwatch_history.json"

def fetch_and_save_daily_settlement():
    """抓取當日 CME 官方結算並寫入歷史庫"""
    print(f"[{datetime.now().strftime('%Y-%m-%d %H:%M:%S')}] 開始執行每日歷史快照儲存...")
    
    # 這裡放入你原本抓取 CME 官方結算價的代碼
    # 例如：
    # from cme_fedwatch import fetch_data
    # data = fetch_data()
    # today_settlement_rate = data['current_implied_rate'] # 假設這是 72.3%
    
    # 模擬抓取到的官方收盤數據（請替換為你的真實抓取變數）
    today_date = datetime.now().strftime('%Y-%m-%d')
    mock_fetched_rate = 72.3  
    
    # 讀取現有歷史紀錄
    history_data = {}
    if os.path.exists(HISTORY_FILE):
        try:
            with open(HISTORY_FILE, "r") as f:
                history_data = json.load(f)
        except json.JSONDecodeError:
            pass
            
    # 更新今日紀錄
    history_data[today_date] = mock_fetched_rate
    
    # 寫入並儲存
    with open(HISTORY_FILE, "w") as f:
        json.dump(history_data, f, indent=4)
        
    print(f"✅ 成功儲存 {today_date} 的官方結算數據 ({mock_fetched_rate}%)。")

# 設定每日香港時間早上 06:00 (對應美國收盤後) 自動執行
schedule.every().day.at("06:00").do(fetch_and_save_daily_settlement)

print("啟動自動歷史定時器... (按 Ctrl+C 停止)")

# 保持程式持續運行，檢查時間
while True:
    schedule.run_pending()
    time.sleep(60) # 每分鐘檢查一次時間