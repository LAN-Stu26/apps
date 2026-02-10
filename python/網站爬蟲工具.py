import requests
from bs4 import BeautifulSoup
from urllib.parse import urljoin, urlparse
from tqdm import tqdm
import time

class WebsiteCrawler:
    def __init__(self, base_url):
        # 確保網址格式正確
        self.base_url = base_url.rstrip('/')
        self.domain = urlparse(base_url).netloc
        self.visited_pages = set()  # 真正「爬進去」分析過的 HTML 頁面
        self.found_resources = set() # 所有找到的資源檔案路徑
        self.queue = [self.base_url] # 待分析的頁面隊列

    def is_internal_page(self, url):
        """檢查是否為同網域且值得爬進去的 HTML 頁面"""
        parsed = urlparse(url)
        if parsed.netloc != self.domain:
            return False
        
        # 如果是明顯的檔案格式，就不進去「分析內容」，但會記錄在資源裡
        path = parsed.path.lower()
        file_exts = ('.jpg', '.jpeg', '.png', '.gif', '.pdf', '.zip', '.mp4', '.css', '.js', '.svg', '.webp', '.woff', '.woff2', '.ttf')
        if any(path.endswith(ext) for ext in file_exts):
            return False
            
        return True

    def start_analysis(self):
        print(f"\n[開始分析] 網域: {self.domain}")
        print("-" * 50)
        
        # 進度條設定：total 會隨著發現新頁面動態增加
        pbar = tqdm(total=1, desc="分析進度", unit="頁", bar_format='{l_bar}{bar:30}{r_bar}{bar:-10b}')
        
        index = 0
        while index < len(self.queue):
            current_url = self.queue[index]
            index += 1
            
            if current_url in self.visited_pages:
                pbar.update(1)
                continue

            self.visited_pages.add(current_url)

            try:
                # 模擬瀏覽器，避免 403 錯誤
                headers = {
                    'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36'
                }
                response = requests.get(current_url, headers=headers, timeout=10)
                
                # 只要是成功請求，將目前的 URL 路徑加入資源清單
                path = urlparse(current_url).path
                self.found_resources.add(path if path else "/")

                # 只對 HTML 內容進行深度解析（找裡面的連結與檔案）
                if "text/html" in response.headers.get("Content-Type", "").lower():
                    soup = BeautifulSoup(response.text, "html.parser")

                    # 定義所有可能包含檔案路徑的標籤
                    tags_attrs = {
                        'a': 'href',
                        'img': 'src',
                        'link': 'href',
                        'script': 'src',
                        'source': 'src',
                        'video': 'src',
                        'audio': 'src'
                    }

                    for tag, attr in tags_attrs.items():
                        for resource in soup.find_all(tag):
                            link = resource.get(attr)
                            if not link or link.startswith('#') or link.startswith('mailto:') or link.startswith('tel:'):
                                continue
                            
                            # 補足相對路徑
                            full_url = urljoin(current_url, link)
                            parsed_res = urlparse(full_url)
                            
                            # 只要是同網域的，通通記錄下來
                            if parsed_res.netloc == self.domain:
                                res_path = parsed_res.path
                                if not res_path: res_path = "/"
                                self.found_resources.add(res_path)
                                
                                # 如果是網頁，加入待爬取的 queue
                                clean_url = full_url.split('#')[0].split('?')[0].rstrip('/')
                                if self.is_internal_page(clean_url) and clean_url not in self.visited_pages and clean_url not in self.queue:
                                    self.queue.append(clean_url)
                                    pbar.total = len(self.queue) # 更新總數
                
                # 即時更新進度條右側的資源統計
                pbar.set_postfix({"目前找到資源數": len(self.found_resources)})
                
            except Exception:
                pass # 忽略單一頁面錯誤，繼續分析
            
            pbar.update(1)
            time.sleep(0.05) # 微小延遲防止被封 IP

        pbar.close()

    def display_all_resources(self):
        # 將結果排序，讓輸出更好閱讀
        sorted_files = sorted(list(self.found_resources))
        total_count = len(sorted_files)

        print("\n" + "="*60)
        print(f"分析完成！總共在網站中找到 {total_count} 個資源檔案：")
        print("="*60)
        
        for i, file_path in enumerate(sorted_files, 1):
            print(f"[{i:03}] {file_path}")
            
        print("="*60)
        print(f"總計資源數量: {total_count}")
        print("="*60)

if __name__ == "__main__":
    url_input = input("請輸入要分析的網址 (例如 https://example.com): ").strip()
    if not url_input.startswith('http'):
        url_input = 'https://' + url_input

    crawler = WebsiteCrawler(url_input)
    crawler.start_analysis()
    crawler.display_all_resources()