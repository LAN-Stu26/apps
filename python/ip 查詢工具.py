import requests
import sys

def get_ip_location(ip_address=""):
    """
    查詢 IP 地址的地理位置資訊。
    如果 ip_address 為空，API 會自動回傳請求者的公網 IP。
    """
    # 使用 ip-api.com 的繁體中文介面
    url = f"http://ip-api.com/json/{ip_address}?lang=zh-TW"

    try:
        response = requests.get(url, timeout=10)
        response.raise_for_status()
        data = response.json()

        if data.get("status") == "success":
            # 依照要求的格式輸出
            print(f"\n[ 查詢結果: {data.get('query')} ]")
            print(f"----------------------------------")
            print(f"國家: {data.get('country')}")
            print(f"城市: {data.get('city')}")
            print(f"區域/省份: {data.get('regionName')}")
            print(f"時區: {data.get('timezone')}")
            print(f"ISP 業者: {data.get('isp')}")
            print(f"經緯度: {data.get('lat')}, {data.get('lon')}")
            print(f"----------------------------------\n")
            return True
        else:
            print(f"\n查詢失敗: {data.get('message')} (請檢查輸入格式)")
            return False

    except requests.exceptions.RequestException as e:
        print(f"\n連線錯誤: {e}")
        return False

def main():
    print("========================================")
    print("      IP 地理位置查詢工具 v3.0")
    print("  - 輸入特定 IP 進行查詢")
    print("  - 輸入 'my' 查詢您的公網位置")
    print("  - 輸入 'exit' 或 'q' 離開程式")
    print("========================================")

    while True:
        user_input = input("請輸入 IP 地址或 'my': ").strip().lower()

        # 結束程式的指令
        if user_input in ['exit', 'q', 'quit']:
            print("程式已結束。")
            break
        
        # 處理 'my' 指令 (傳送空字串給 API)
        if user_input == 'my':
            success = get_ip_location("")
        elif user_input == "":
            # 如果使用者直接按 Enter，視為無效輸入但不報錯，提示重新輸入
            print("請輸入有效的 IP 或 'my'")
            continue
        else:
            # 處理一般 IP 查詢
            success = get_ip_location(user_input)

        # 依照要求：如果回應失敗（輸入錯誤或網路問題），則終止程式
        if not success:
            print("偵測到錯誤回應，程式自動停止運作。")
            break

if __name__ == "__main__":
    try:
        main()
    except KeyboardInterrupt:
        print("\n\n偵測到中斷指令，程式退出。")
        sys.exit()