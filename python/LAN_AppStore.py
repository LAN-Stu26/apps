import os
import requests
import json
import sys

# 設定雲端配置路徑 (根據你的 GitHub 截圖)
JSON_RAW_URL = "https://raw.githubusercontent.com/LAN-Stu26/apps/main/python/version.json"
CURRENT_FILENAME = "LAN_AppStore.py"  # 下載工具自身的檔名
CURRENT_VERSION = "1.1"               # 當前下載工具版本

def get_cloud_config():
    """從 GitHub 獲取最新 version.json"""
    try:
        response = requests.get(JSON_RAW_URL, timeout=10)
        response.raise_for_status()
        return response.json()
    except Exception as e:
        print(f"❌ 無法連接伺服器: {e}")
        return None

def fix_github_url(url):
    """將瀏覽用 URL 轉換為 Raw 下載連結"""
    if "github.com" in url and "raw.githubusercontent.com" not in url:
        url = url.replace("github.com", "raw.githubusercontent.com")
        url = url.replace("/tree/main/", "/main/")
        url = url.replace("/blob/main/", "/main/")
    return url

def download_file(url, filename):
    """執行檔案下載與寫入"""
    try:
        raw_url = fix_github_url(url)
        res = requests.get(raw_url, timeout=15)
        res.raise_for_status()
        with open(filename, "wb") as f:
            f.write(res.content)
        return True
    except Exception as e:
        print(f"❌ 下載失敗: {e}")
        return False

def check_self_update(config):
    """檢查下載工具本身是否有新版本"""
    if "LAN_AppStore" in config:
        cloud_version = config["LAN_AppStore"]["version"]
        if str(cloud_version) != str(CURRENT_VERSION):
            print(f"🚀 偵測到下載工具新版本 (v{CURRENT_VERSION} -> v{cloud_version})")
            print("正在自動更新主程式...")
            if download_file(config["LAN_AppStore"]["url"], CURRENT_FILENAME):
                print("✅ 主程式更新完成！請重新啟動程式。")
                sys.exit()
    return

def main():
    # 1. 啟動檢查：獲取配置與自我更新
    config = get_cloud_config()
    if config:
        check_self_update(config)

    while True:
        print("\n" + "="*45)
        print(f"      LAN-Stu26 檔案下載與更新工具 (v{CURRENT_VERSION})")
        print("="*45)

        if not config:
            config = get_cloud_config() # 嘗試重新獲取
            if not config:
                input("無法取得配置，按 Enter 鍵退出..."); break

        # 2. 顯示所有檔案清單
        print(f"\n{'代號':<6} {'檔案名稱':<25} {'最新版本':<10}")
        print("-" * 45)
        
        mapping = {}
        display_idx = 1
        for name, info in config.items():
            if name == "LAN_AppStore": continue # 不在選單顯示工具本身
            mapping[display_idx] = {"name": name, "version": info['version'], "url": info['url']}
            print(f"[{display_idx:^4}] {name:<25} v{info['version']:<10}")
            display_idx += 1
        print("-" * 45)

        # 3. 獲取代號輸入 (含錯誤重複詢問機制)
        choice = None
        while True:
            user_input = input("\n請輸入檔案代號進行 下載/更新 (或輸入 'q' 離開): ").strip()
            if user_input.lower() == 'q':
                print("👋 程式已關閉。"); return
            
            if user_input.isdigit() and int(user_input) in mapping:
                choice = mapping[int(user_input)]
                break
            else:
                print(f"⚠️  錯誤：代號「{user_input}」不存在，請重新輸入。")

        # 4. 下載與更新邏輯
        target_name = choice['name']
        latest_ver = choice['version']
        target_filename = f"{target_name}-{latest_ver}.py"
        
        # 檢查本地是否已經有該檔案 (包含舊版本)
        local_files = [f for f in os.listdir('.') if f.startswith(target_name) and f.endswith('.py')]
        
        if target_filename in local_files:
            print(f"✨ 檢查完畢：{target_filename} 已存在且為最新版本。")
        else:
            if local_files:
                print(f"💡 發現舊版本，準備更新至 v{latest_ver}...")
                for old_f in local_files:
                    try: os.remove(old_f)
                    except: pass
            else:
                print(f"🆕 本地尚未擁有此檔案，開始執行下載...")
            
            # 執行下載動作
            if download_file(choice['url'], target_filename):
                print(f"✅ 檔案已成功下載：{target_filename}")

        # 5. 詢問是否繼續
        if input("\n是否繼續下載其他檔案？(y/n): ").lower() != 'y':
            print("👋 感謝使用！")
            break

if __name__ == "__main__":
    main()
