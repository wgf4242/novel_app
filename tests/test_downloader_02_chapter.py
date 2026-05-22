import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent.parent))

from config import ConfigManager
from downloader import Downloader

import unittest


class Test(unittest.TestCase):
    def setUp(self) -> None:
        super().setUp()

    def test_download_single_chapter_01_cuoceng(self):
        """测试下载单章内容"""

        # 测试错层小说网（可能被 Cloudflare 拦截）
        cuoceng_url = "https://m.cuoceng.com/book/80a32c66-79f7-4188-9291-4a628dc505f3/770e6782-94f6-4efb-a57c-373f19b80fdc.html"

        print("=" * 60)
        print("测试错层小说网章节下载")
        print("=" * 60)

        config_manager = ConfigManager()
        site_config = config_manager.get_site_by_url(cuoceng_url)

        if not site_config:
            print("未找到站点配置")
            return

        downloader = Downloader(site_config)
        html_content = downloader.fetch_url(cuoceng_url)

        if not html_content:
            print("获取页面失败")
        elif "Cloudflare" in html_content or "Attention Required" in html_content:
            print("警告: 该网站使用 Cloudflare 反爬虫保护")
            print("章节下载暂时不可用")
            with open("tests/cloudflare_page.html", "w", encoding="utf-8") as f:
                f.write(html_content)
        else:
            content = downloader.parser.parse_content(html_content)
            if content:
                print(f"下载成功，内容长度: {len(content)} 字符")
                with open("tests/cuoceng_chapter_1.txt", "w", encoding="utf-8") as f:
                    f.write(content)
                print("章节内容已保存到 tests/cuoceng_chapter_1.txt")
            else:
                print("解析内容失败")

    def test_download_single_chapter_02_biquge(self):
        # 测试新笔趣阁（应该可以正常下载）
        print("\n" + "=" * 60)
        print("测试新笔趣阁章节下载")
        print("=" * 60)

        xbqg_url = "https://www.xbqg8.net/176/176829/1.html"

        config_manager = ConfigManager()
        site_config = config_manager.get_site_by_url(xbqg_url)

        if not site_config:
            print("未找到新笔趣阁站点配置")
            return

        downloader = Downloader(site_config)
        content = downloader.download_chapter(xbqg_url)

        if content:
            print(f"下载成功，内容长度: {len(content)} 字符")

            # 保存内容
            with open("tests/xbqg_chapter_1.txt", "w", encoding="utf-8") as f:
                f.write(content)
            print("章节内容已保存到 tests/xbqg_chapter_1.txt")

            # 显示预览
            print("\n内容预览:")
            print("-" * 80)
            preview = content[:1000]
            print(preview)
            if len(content) > 1000:
                print("...")
            print("-" * 80)

            # 统计信息
            paragraphs = [p for p in content.split('\n\n') if p.strip()]
            print(f"\n统计信息:")
            print(f"  - 段落数: {len(paragraphs)}")
            print(f"  - 字符数: {len(content)}")
            print(f"  - 行数: {content.count('\n') + 1}")
        else:
            print("下载失败")

    def test_download_single_chapter_03_xiapi(self):
        # 测试新笔趣阁（应该可以正常下载）
        print("\n" + "=" * 60)
        print("测试虾皮小说章节下载")
        print("=" * 60)

        xbqg_url = "https://www.xpxs.net/chapter/43222/13096782.html"
        xbqg_url = "https://www.xpxs.net/chapter/43222/13096792.html"

        config_manager = ConfigManager()
        site_config = config_manager.get_site_by_url(xbqg_url)

        if not site_config:
            print("未找到新笔趣阁站点配置")
            return

        downloader = Downloader(site_config)
        content = downloader.download_chapter(xbqg_url)

        if content:
            print(f"下载成功，内容长度: {len(content)} 字符")

            # 保存内容
            with open("tests/xbqg_chapter_1.txt", "w", encoding="utf-8") as f:
                f.write(content)
            print("章节内容已保存到 tests/xbqg_chapter_1.txt")

            # 显示预览
            print("\n内容预览:")
            print("-" * 80)
            preview = content[:1000]
            print(preview)
            if len(content) > 1000:
                print("...")
            print("-" * 80)

            # 统计信息
            paragraphs = [p for p in content.split('\n\n') if p.strip()]
            print(f"\n统计信息:")
            print(f"  - 段落数: {len(paragraphs)}")
            print(f"  - 字符数: {len(content)}")
            print(f"  - 行数: {content.count('\n') + 1}")
        else:
            print("下载失败")
