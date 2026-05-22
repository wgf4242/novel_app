import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent.parent))

from config import ConfigManager
from downloader import Downloader

import unittest


class Test(unittest.TestCase):
    def setUp(self) -> None:
        super().setUp()

    def test_catalog1(self):
        url = "https://m.cuoceng.com/book/chapter/80a32c66-79f7-4188-9291-4a628dc505f3/1.html"

        config_manager = ConfigManager()
        site_config = config_manager.get_site_by_url(url)

        if not site_config:
            print("未找到站点配置")
            return

        print(f"找到站点配置: {site_config.name}")
        print(f"目录分页 XPath: {site_config.catalog_next_page_xpath}")

        downloader = Downloader(site_config)

        print("正在下载目录（支持分页）...")
        chapters = downloader.download_catalog(url)

        if chapters:
            print(f"成功获取 {len(chapters)} 章")

            print("前10章:")
            for i, ch in enumerate(chapters[:10], 1):
                print(f"{i}. {ch['title'][:40]}... -> {ch['url']}")

            print("最后10章:")
            for i, ch in enumerate(chapters[-10:], len(chapters) - 9):
                print(f"{i}. {ch['title'][:40]}... -> {ch['url']}")

            with open("tests/cuoceng_chapters.txt", "w", encoding="utf-8") as f:
                for i, ch in enumerate(chapters, 1):
                    f.write(f"{i}\t{ch['title']}\t{ch['url']}\n")
            print(f"章节列表已保存到 tests/cuoceng_chapters.txt")
        else:
            print("获取章节列表失败")

    def test_catalog_xiapi(self):
        url = "https://www.xpxs.net/indexs/9145149/"

        config_manager = ConfigManager()
        site_config = config_manager.get_site_by_url(url)

        if not site_config:
            print("未找到站点配置")
            return

        print(f"找到站点配置: {site_config.name}")
        print(f"目录分页 XPath: {site_config.catalog_next_page_xpath}")

        downloader = Downloader(site_config)

        print("正在下载目录（支持分页）...")
        chapters = downloader.download_catalog(url)

        if chapters:
            print(f"成功获取 {len(chapters)} 章")

            print("前10章:")
            for i, ch in enumerate(chapters[:10], 1):
                print(f"{i}. {ch['title'][:40]}... -> {ch['url']}")

            print("最后10章:")
            for i, ch in enumerate(chapters[-10:], len(chapters) - 9):
                print(f"{i}. {ch['title'][:40]}... -> {ch['url']}")

            with open("tests/cuoceng_chapters.txt", "w", encoding="utf-8") as f:
                for i, ch in enumerate(chapters, 1):
                    f.write(f"{i}\t{ch['title']}\t{ch['url']}\n")
            print(f"章节列表已保存到 tests/cuoceng_chapters.txt")
        else:
            print("获取章节列表失败")
