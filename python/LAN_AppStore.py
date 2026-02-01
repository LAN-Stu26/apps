import os
import requests
import json
import sys

# 設定專案相關 URL
JSON_RAW_URL = "https://raw.githubusercontent.com/LAN-Stu26/apps/main/python/version.json"
CURRENT_FILENAME = "LAN_AppStore.py"  # 本下載工具的檔名
CURRENT_VERSION = "1.0"               # 本下載工具目前的版本

def get_cloud_config():
    """抓取雲端的 version.json 內容"""
    try:
        response = requests.get(JSON_RAW_URL)
        response.raise_for_status()
        return response.json()
    except Exception as e:
        print(f"❌ 無法讀取雲端配置: {e}")
        return None

def fix_github_url(url):
    """將 GitHub 網頁連結轉換為正確的 Raw 下載連結"""
    if "github.com" in url and "raw.githubusercontent.com" not in url:
        url = url.replace("github.com", "raw.githubusercontent.com")
        url = url.replace("/tree/main/", "/main/")
        url = url.replace("/blob/main/", "/main/")
    return url

def download_file(url, filename):
    """執行下載"""
    try:
        raw_url = fix_github_url(url)
        res = requests.get(raw_url)
        res.raise_for_status()
        with open(filename, "wb") as f:
            f.write(res.content)
        return True
    except Exception as e:
        print(f"❌ 下載失敗: {e}")
        return False

def check_self_update(config):
    """檢查並執行下載工具自身的更新"""
    if "LAN_AppStore" in config:
        cloud_version = config["LAN_AppStore"]["version"]
        if cloud_version != CURRENT_VERSION:
            print(f"🚀 偵測到下載工具新版本 (v{CURRENT_VERSION} -> v{cloud_version})")
            print("正在自動升級主程式...")
            if download_file(config["LAN_AppStore"]["url"], CURRENT_FILENAME):
                print("✅ 主程式更新完成！請重新啟動程式以套用變更。")
                sys.exit() # 更新完後強制結束，讓使用者重新啟動
    return

def main():
    # 啟動後立即檢查更新
    config = get_cloud_config()
    if config:
        check_self_update(config)

    while True:
        print("\n" + "="*45)
        print(f"      LAN-Stu26 專屬檔案更新器 (v{CURRENT_VERSION})")
        print("="*45)

        if not config:
            config = get_cloud_config()
            if not config:
                input("無法連接伺服器，按任意鍵退出..."); break

        # 顯示清單 (排除下載工具本身，不顯示在下載選單中以免混淆)
        print(f"\n{'代號':<6} {'功能名稱':<25} {'最新版本':<10}")
        print("-" * 45)
        
        mapping = {}
        display_idx = 1
        for name, info in config.items():
            if name == "LAN_AppStore": continue # 隱藏主程式更新項
            mapping[display_idx] = {"name": name, "version": info['version'], "url": info['url']}
            print(f"[{display_idx:^4}] {name:<25} v{info['version']:<10}")
            display_idx += 1
        print("-" * 45)

        # 獲取使用者輸入
        choice = None
        while True:
            user_input = input("\n請輸入檔案代號 (或輸入 'q' 離開): ").strip()
            if user_input.lower() == 'q':
                print("👋 感謝使用，程式關閉中..."); return
            
            if user_input.isdigit() and int(user_input) in mapping:
                choice = mapping[int(user_input)]
                break
            else:
                print(f"⚠️  代號「{user_input}」無效！請重新輸入。")

        # 執行其他檔案的更新邏輯
        target_name = choice['name']
        latest_ver = choice['version']
        target_filename = f"{target_name}-{latest_ver}.py"
        
        local_files = [f for f in os.listdir('.') if f.startswith(target_name) and f.endswith('.py')]
        
        if target_filename in local_files:
            print(f"✨ 檢查完畢：本地已是最新版本 (v{latest_ver})。")
        else:
            if local_files:
                print(f"💡 發現舊版本，正在執行更新...")
                for old_f in local_files:
                    try: os.remove(old_f)
                    except: pass
            else:
                print(f"🆕 本地尚未擁有此檔案，準備下載...")
            
            if download_file(choice['url'], target_filename):
                print(f"✅ {target_filename} 下載成功！")

        if input("\n是否繼續操作其他檔案？(y/n): ").lower() != 'y':
            print("👋 再見！")
            break

if __name__ == "__main__":
    main()
