import urllib.request
import urllib.parse
from html.parser import HTMLParser
import time
import sys
import ssl

# 建立一個 HTML 解析器類別，替代 BeautifulSoup
class SimpleLinkParser(HTMLParser):
    def __init__(self, base_url):
        super().__init__()
        self.base_url = base_url
        self.found_links = []
        self.tags_attrs = {
            'a': 'href',
            'img': 'src',
            'link': 'href',
            'script': 'src',
            'source': 'src',
            'video': 'src',
            'audio': 'src'
        }

    def handle_starttag(self, tag, attrs):
        if tag in self.tags_attrs:
            attr_name = self.tags_attrs[tag]
            for attr, value in attrs:
                if attr == attr_name and value:
                    # 補足相對路徑為絕對路徑
                    full_url = urllib.parse.urljoin(self.base_url, value)
                    self.found_links.append(full_url)

class WebsiteCrawler:
    def __init__(self, base_url):
        self.base_url = base_url.rstrip('/')
        self.domain = urllib.parse.urlparse(base_url).netloc
        self.visited_pages = set()
        self.found_resources = set()
        self.queue = [self.base_url]
        
        # 忽略 SSL 憑證檢查 (避免某些網站報錯)
        self.ssl_context = ssl._create_unverified_context()

    def is_internal_page(self, url):
        parsed = urllib.parse.urlparse(url)
        if parsed.netloc != self.domain:
            return False
        
        path = parsed.path.lower()
        file_exts = ('.jpg', '.jpeg', '.png', '.gif', '.pdf', '.zip', '.mp4', '.css', '.js', '.svg', '.webp', '.woff', '.woff2', '.ttf')
        if any(path.endswith(ext) for ext in file_exts):
            return False
        return True

    def draw_progress_bar(self, current, total, resource_count):
        """替代 tqdm 的自製進度條"""
        width = 30
        percent = current / total
        filled = int(width * percent)
        bar = '█' * filled + '-' * (width - filled)
        sys.stdout.write(f'\r分析進度: |{bar}| {current}/{total} 頁 (資源數: {resource_count})')
        sys.stdout.flush()

    def start_analysis(self):
        print(f"\n[開始分析] 網域: {self.domain} (使用 Python 內建庫)")
        print("-" * 50)
        
        index = 0
        while index < len(self.queue):
            current_url = self.queue[index]
            index += 1
            
            if current_url in self.visited_pages:
                continue

            self.visited_pages.add(current_url)
            self.draw_progress_bar(len(self.visited_pages), len(self.queue), len(self.found_resources))

            try:
                headers = {
                    'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36'
                }
                req = urllib.request.Request(current_url, headers=headers)
                
                with urllib.request.urlopen(req, context=self.ssl_context, timeout=10) as response:
                    content_type = response.info().get_content_type()
                    
                    # 記錄當前路徑
                    path = urllib.parse.urlparse(current_url).path
                    self.found_resources.add(path if path else "/")

                    # 如果是 HTML，解析裡面的資源
                    if "text/html" in content_type:
                        html_content = response.read().decode('utf-8', errors='ignore')
                        parser = SimpleLinkParser(current_url)
                        parser.feed(html_content)

                        for full_url in parser.found_links:
                            if full_url.startswith('mailto:') or full_url.startswith('tel:'):
                                continue
                                
                            parsed_res = urllib.parse.urlparse(full_url)
                            if parsed_res.netloc == self.domain:
                                # 記錄資源路徑
                                res_path = parsed_res.path
                                self.found_resources.add(res_path if res_path else "/")
                                
                                # 檢查是否為新網頁並加入排隊
                                clean_url = full_url.split('#')[0].split('?')[0].rstrip('/')
                                if self.is_internal_page(clean_url) and clean_url not in self.visited_pages and clean_url not in self.queue:
                                    self.queue.append(clean_url)
                
            except Exception:
                pass 
            
            time.sleep(0.1) # 稍微增加延遲，對內建庫連線較穩定
        
        print("\n\n分析完成！")

    def display_all_resources(self):
        sorted_files = sorted(list(self.found_resources))
        total_count = len(sorted_files)

        print("\n" + "="*60)
        print(f"結果清單：")
        print("="*60)
        
        for i, file_path in enumerate(sorted_files, 1):
            print(f"[{i:03}] {file_path}")
            
        print("="*60)
        print(f"總計資源數量: {total_count}")
        print("="*60)

if __name__ == "__main__":
    url_input = input("請輸入要分析的網址: ").strip()
    if not url_input.startswith('http'):
        url_input = 'https://' + url_input

    crawler = WebsiteCrawler(url_input)
    crawler.start_analysis()
    crawler.display_all_resources()