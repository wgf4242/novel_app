import requests
import time
from concurrent.futures import ThreadPoolExecutor, as_completed
from typing import Callable, Optional
from parser import Parser
from config import SiteConfig, ProxyConfig


class Downloader:
    def __init__(
        self, 
        site_config: SiteConfig, 
        max_workers: int = 3, 
        download_delay: float = 1.0,
        proxy_config: Optional[ProxyConfig] = None
    ):
        self.config = site_config
        self.max_workers = max_workers
        self.download_delay = download_delay if download_delay > 0 else site_config.download_delay
        self.proxy_config = proxy_config
        self.parser = Parser(site_config)
        self.session = self._create_session()
        self._stop_flag = False
        self._last_download_time = 0

    def _create_session(self) -> requests.Session:
        """创建带代理配置的会话"""
        session = requests.Session()
        session.headers.update({
            'User-Agent': "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/89.0.4389.90 Safari/537.36"
        })
        
        # 设置代理
        if self.proxy_config and self.proxy_config.enabled and self.proxy_config.host:
            proxy_url = self._build_proxy_url()
            session.proxies = {
                'http': proxy_url,
                'https': proxy_url
            }
        
        return session

    def _build_proxy_url(self) -> str:
        """构建代理 URL"""
        if not self.proxy_config:
            return ""
        
        proxy_type = self.proxy_config.proxy_type.lower()
        host = self.proxy_config.host
        port = self.proxy_config.port
        
        if self.proxy_config.username and self.proxy_config.password:
            return f"{proxy_type}://{self.proxy_config.username}:{self.proxy_config.password}@{host}:{port}"
        else:
            return f"{proxy_type}://{host}:{port}"

    def fetch_url(self, url: str) -> Optional[str]:
        self._wait_for_delay()
        
        try:
            resp = self.session.get(url, timeout=30)
            resp.encoding = resp.apparent_encoding
            self._last_download_time = time.time()
            return resp.text
        except Exception as e:
            print(f"Error fetching {url}: {e}")
            return None

    def _wait_for_delay(self) -> None:
        """等待下载延迟"""
        if self.download_delay <= 0:
            return
        
        elapsed = time.time() - self._last_download_time
        if elapsed < self.download_delay:
            time.sleep(self.download_delay - elapsed)

    def download_chapter(self, url: str) -> Optional[str]:
        """下载章节，支持分页"""
        all_contents = []
        current_url = url
        
        original_chapter_num = self._extract_chapter_number(url)
        
        while current_url:
            html_content = self.fetch_url(current_url)
            if not html_content:
                break
                
            content = self.parser.parse_content(html_content)
            if content:
                all_contents.append(content)
                
            next_url = self.parser.extract_next_page(html_content, current_url)
            
            if not next_url:
                break
                
            if next_url == current_url:
                break
                
            next_chapter_num = self._extract_chapter_number(next_url)
            if next_chapter_num and next_chapter_num != original_chapter_num:
                break
                
            current_url = next_url
            
            if len(all_contents) >= 5:
                break
        
        if all_contents:
            return '\n\n'.join(all_contents)
        return None
        
    def download_catalog(self, url: str) -> list[dict]:
        """下载目录，支持分页"""
        chapters = []
        current_url = url
        page_count = 0
        
        while current_url:
            page_count += 1
            print(f"下载目录第 {page_count} 页: {current_url}")
            
            html_content = self.fetch_url(current_url)
            if not html_content:
                break
                
            from lxml import html
            tree = html.fromstring(html_content)
            
            if self.config.catalog_container_xpath:
                chapter_links = tree.xpath(self.config.catalog_container_xpath)
            else:
                chapter_links = tree.xpath('//a[@href]')
            
            for link in chapter_links:
                href = link.get('href', '')
                text = link.text_content().strip()
                if text and href and '.html' in href:
                    full_url = self._join_url(current_url, href)
                    chapters.append({
                        'title': text,
                        'url': full_url
                    })
            
            next_url = self._extract_catalog_next_page(tree, current_url)
            
            if not next_url or next_url == current_url:
                break
                
            current_url = next_url
            
            if page_count >= 10:
                break
        
        print(f"共找到 {len(chapters)} 章")
        return chapters
        
    def _extract_catalog_next_page(self, tree, base_url: str) -> Optional[str]:
        """提取目录的下一页链接"""
        if not self.config.catalog_next_page_xpath:
            return None
            
        next_links = tree.xpath(self.config.catalog_next_page_xpath)
        if next_links:
            href = next_links[0].get('href', '')
            if href:
                return self._join_url(base_url, href)
        return None
        
    def _join_url(self, base_url: str, href: str) -> str:
        """合并 URL"""
        from urllib.parse import urljoin
        return urljoin(base_url, href)
        
    def _extract_chapter_number(self, url: str) -> Optional[str]:
        """从 URL 中提取章节号"""
        import re
        match = re.search(r'/(\d+)(?:_\d+)?\.html', url)
        if match:
            return match.group(1)
        return None

    def download_chapters(
        self,
        chapters: list[dict],
        progress_callback: Optional[Callable[[int, int], None]] = None,
        chapter_callback: Optional[Callable[[dict, str], None]] = None
    ) -> dict:
        results = {}
        total = len(chapters)
        completed = 0
        self._stop_flag = False
        
        if self.max_workers == 1:
            for ch in chapters:
                if self._stop_flag:
                    break
                try:
                    content = self.download_chapter(ch['url'])
                    if content:
                        results[ch['url']] = content
                        if chapter_callback:
                            chapter_callback(ch, content)
                except Exception as e:
                    print(f"Error downloading {ch['url']}: {e}")
                completed += 1
                if progress_callback:
                    progress_callback(completed, total)
        else:
            with ThreadPoolExecutor(max_workers=self.max_workers) as executor:
                future_to_chapter = {
                    executor.submit(self.download_chapter, ch['url']): ch
                    for ch in chapters
                }
                for future in as_completed(future_to_chapter):
                    if self._stop_flag:
                        executor.shutdown(wait=False, cancel_futures=True)
                        break
                    chapter = future_to_chapter[future]
                    try:
                        content = future.result()
                        if content:
                            results[chapter['url']] = content
                            if chapter_callback:
                                chapter_callback(chapter, content)
                    except Exception as e:
                        print(f"Error downloading {chapter['url']}: {e}")
                    completed += 1
                    if progress_callback:
                        progress_callback(completed, total)
        return results

    def stop(self) -> None:
        self._stop_flag = True