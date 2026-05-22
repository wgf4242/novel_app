import re
from urllib.parse import urljoin
from lxml import html
from config import SiteConfig
from typing import Optional


class Parser:
    def __init__(self, site_config: SiteConfig):
        self.config = site_config

    def parse_catalog(self, html_content: str, base_url: str) -> list[dict]:
        """解析目录，支持分页"""
        chapters = []
        next_page_url = self._parse_catalog_page(html_content, base_url, chapters)
        return chapters
    
    def _parse_catalog_page(self, html_content: str, base_url: str, chapters: list) -> Optional[str]:
        """解析单页目录并提取章节，返回下一页URL"""
        tree = html.fromstring(html_content)

        if self.config.catalog_container_xpath:
            # 使用配置的 XPath 查找章节链接
            chapter_links = tree.xpath(self.config.catalog_container_xpath)
        else:
            # 回退到原始方法
            links = tree.xpath('//a[@href]')
            in_range = False
            chapter_links = []
            for link in links:
                if self.config.catalog_start_marker:
                    text = link.text_content().strip()
                    if self.config.catalog_start_marker in text:
                        in_range = True
                        continue
                if self.config.catalog_end_marker:
                    text = link.text_content().strip()
                    if self.config.catalog_end_marker in text:
                        break
                if in_range or not self.config.catalog_start_marker:
                    chapter_links.append(link)

        for link in chapter_links:
            href = link.get('href', '')
            text = link.text_content().strip()
            
            if text and href:
                full_url = urljoin(base_url, href)
                chapters.append({
                    'title': text,
                    'url': full_url
                })
        
        # 提取下一页链接
        return self._extract_catalog_next_page(tree, base_url)
    
    def _extract_catalog_next_page(self, tree, base_url: str) -> Optional[str]:
        """提取目录的下一页链接"""
        if not self.config.catalog_next_page_xpath:
            return None
            
        next_links = tree.xpath(self.config.catalog_next_page_xpath)
        if next_links:
            href = next_links[0].get('href', '')
            if href:
                return urljoin(base_url, href)
        return None

    def parse_content(self, html_content: str) -> str:
        tree = html.fromstring(html_content)
        content_parts = []

        if self.config.content_xpath:
            # 使用配置的 XPath 查找内容容器
            content_nodes = tree.xpath(self.config.content_xpath)
            if content_nodes:
                for node in content_nodes:
                    content_parts.append(node.text_content())
        else:
            # 回退到原始方法
            body = tree.xpath('//body')[0] if tree.xpath('//body') else tree
            for node in body.iter():
                if node.text:
                    content_parts.append(node.text)
                if node.tail:
                    content_parts.append(node.tail)
        
        content = '\n'.join(content_parts)
        content = self._clean_content(content)
        return content.strip()

    def _clean_content(self, content: str) -> str:
        content = re.sub(r'\r\n', '\n', content)
        for pattern in self.config.ad_patterns:
            content = re.sub(pattern, '', content)
        # Normalize newlines
        # Remove excessive whitespace
        content = re.sub(r'[ \t]+', ' ', content)  # Multiple spaces/tabs to one
        # Process lines
        lines = []
        for line in content.split('\n'):
            stripped = line.strip()
            if stripped:
                lines.append(stripped)
            else:
                lines.append('')
        content = '\n'.join(lines)
        # Remove multiple consecutive blank lines
        content = re.sub(r'\n{3,}', '\n\n', content)
        return content.strip()

    def extract_next_page(self, html_content: str, base_url: str) -> Optional[str]:
        """提取下一页链接，如果没有则返回 None"""
        if not self.config.next_page_xpath:
            return None
        
        tree = html.fromstring(html_content)
        next_links = tree.xpath(self.config.next_page_xpath)
        if next_links:
            href = next_links[0].get('href', '')
            if href:
                return urljoin(base_url, href)
        return None

    def extract_novel_info(self, html_content: str) -> dict:
        tree = html.fromstring(html_content)
        title = ''
        author = ''
        status = '连载中'
        title_elem = tree.xpath('//h1')
        if title_elem:
            title = title_elem[0].text_content().strip()
        author_elem = tree.xpath('//a[contains(@href, "author")]')
        if author_elem:
            author = author_elem[0].text_content().strip()
        status_elem = tree.xpath('//*[contains(text(), "状态")]')
        if status_elem:
            status_text = status_elem[0].text_content()
            if '完结' in status_text:
                status = '已完结'
        return {
            'title': title,
            'author': author,
            'status': status
        }
