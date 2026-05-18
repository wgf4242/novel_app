
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent.parent))

from config import ConfigManager
from downloader import Downloader

def test_chapter_download_with_pagination():
    """测试带分页的章节下载"""
    config_manager = ConfigManager()
    site_config = config_manager.get_site_by_url("https://www.xbqg8.net/176/176829/1.html")
    
    if not site_config:
        print("找不到站点配置")
        return
        
    print(f"找到站点配置: {site_config.name}")
    print(f"  分页模式: {site_config.next_page_pattern}")
    
    downloader = Downloader(site_config)
    
    print("\n正在下载第一章 (带分页)...")
    content = downloader.download_chapter("https://www.xbqg8.net/176/176829/1.html")
    
    if content:
        print(f"下载成功")
        print(f"  总内容长度: {len(content)} 字符")
        
        with open("tests/chapter_1_full.txt", "w", encoding="utf-8") as f:
            f.write(content)
        print("  已保存到 tests/chapter_1_full.txt")
        
        print("\n内容预览:")
        print("-" * 80)
        print(content[:800])
        print("-" * 80)
        
        print("\n内容末尾:")
        print("-" * 80)
        print(content[-400:])
        print("-" * 80)
    else:
        print("下载失败")

if __name__ == "__main__":
    test_chapter_download_with_pagination()
