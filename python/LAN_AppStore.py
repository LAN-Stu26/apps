import os
import requests
import json
import sys
import ctypes

# 設定雲端配置路徑
JSON_RAW_URL = "https://raw.githubusercontent.com/LAN-Stu26/apps/main/python/version.json"
CURRENT_FILENAME = "LAN_AppStore.py"
CURRENT_VERSION = "1.2"  # 更新版本號

def is_admin():
    """檢查是否具有管理員權限"""
    try:
        return ctypes.windll.shell32.IsUserAnAdmin()
    except:
        return False

def run_as_admin():
    """嘗試以管理員身份重新啟動程式"""
    if is_admin():
        return True
    else:
        # 重新啟動程式並請求提升權限
        ctypes.windll.shell32.ShellExecuteW(None, "runas", sys.executable, " ".join(sys.argv), None, 1)
        return False

def get_cloud_config():
    try:
        response = requests.get(JSON_RAW_URL, timeout=10)
        response.raise_for_status()
        return response.json()
    except Exception as e:
        print(f"❌ 無法連接伺服器: {e}")
        return None

def fix_github_url(url):
    if "github.com" in url and "raw.githubusercontent.com" not in url:
        url = url.replace("github.com", "raw.githubusercontent.com")
        url = url.replace("/tree/main/", "/main/")
        url = url.replace("/blob/main/", "/main/")
    return url

def download_file(url, filename):
    try:
        raw_url = fix_github_url(url)
        res = requests.get(raw_url, timeout=15)
        res.raise_for_status()
        # 寫入檔案
        with open(filename, "wb") as f:
            f.write(res.content)
        return True
    except PermissionError:
        print(f"❌ 權限不足：無法寫入檔案 '{filename}'。請嘗試以管理員身份執行此程式。")
        return False
    except Exception as e:
        print(f"❌ 下載失敗: {e}")
        return False

def check_self_update(config):
    if "LAN_AppStore" in config:
        cloud_version = str(config["LAN_AppStore"]["version"])
        if cloud_version != CURRENT_VERSION:
            print(f"🚀 偵測到下載工具新版本 (v{CURRENT_VERSION} -> v{cloud_version})")
            print("正在自動更新主程式...")
            if download_file(config["LAN_AppStore"]["url"], CURRENT_FILENAME):
                print("✅ 主程式更新完成！請重新啟動程式。")
                sys.exit()
    return

def main():
    # 權限檢查 (可選：如果權限不足，可以解除下方註解強制跳出 UAC)
    # if not is_admin():
    #     print("權限檢查中... 正在請求管理員權限...")
    #     if not run_as_admin():
    #         sys.exit()

    config = get_cloud_config()
    if config:
        check_self_update(config)

    while True:
        print("\n" + "="*45)
        print(f"      LAN-Stu26 檔案下載與更新工具 (v{CURRENT_VERSION})")
        print("="*45)

        if not config:
            config = get_cloud_config()
            if not config:
                input("無法取得配置，按 Enter 鍵退出..."); break

        print(f"\n{'代號':<6} {'檔案名稱':<25} {'最新版本':<10}")
        print("-" * 45)
        
        mapping = {}
        display_idx = 1
        for name, info in config.items():
            if name == "LAN_AppStore": continue
            mapping[display_idx] = {"name": name, "version": info['version'], "url": info['url']}
            print(f"[{display_idx:^4}] {name:<25} v{info['version']:<10}")
            display_idx += 1
        print("-" * 45)

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

        target_name = choice['name']
        latest_ver = choice['version']
        target_filename = f"{target_name}-{latest_ver}.py"
        
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
            
            if download_file(choice['url'], target_filename):
                print(f"✅ 檔案已成功下載：{target_filename}")

        if input("\n是否繼續下載其他檔案？(y/n): ").lower() != 'y':
            print("👋 感謝使用！")
            break

if __name__ == "__main__":
    main()
