# 小说下载阅读器实现计划

> **面向 AI 代理的工作者：** 必需子技能：使用 superpowers:subagent-driven-development（推荐）或 superpowers:executing-plans 逐任务实现此计划。步骤使用复选框（`- [ ]`）语法来跟踪进度。

**目标：** 开发一个 Python 桌面 GUI 小说下载阅读器，支持从小说网站下载章节、增量更新、导出 TXT。

**架构：** 多模块分层架构，分为配置层、数据层、解析层、下载层、导出层、界面层。使用 SQLite 存储数据，requests + lxml 解析 HTML，tkinter 构建 GUI。

**技术栈：** Python 3.13, tkinter, sqlite3, requests, lxml, concurrent.futures

---

## 文件结构

| 文件 | 职责 |
|------|------|
| `config.py` | 配置管理，加载网站规则 |
| `sites.json` | 网站规则配置文件 |
| `database.py` | 数据库操作，小说和章节的 CRUD |
| `parser.py` | HTML 解析，提取目录和正文 |
| `downloader.py` | 并发下载器，下载章节内容 |
| `exporter.py` | 导出器，生成 TXT 文件 |
| `gui.py` | GUI 界面，tkinter 实现 |
| `main.py` | 主入口，启动应用 |

---

## 任务 1：项目初始化和依赖安装

**文件：**
- 修改：`pyproject.toml`
- 创建：`sites.json`

- [ ] **步骤 1：更新 pyproject.toml 添加依赖**

```toml
[project]
name = "novel-app"
version = "0.1.0"
description = "小说下载阅读器"
readme = "README.md"
requires-python = ">=3.13"
dependencies = [
    "requests>=2.28.0",
    "lxml>=4.9.0",
]
```

- [ ] **步骤 2：使用 uv 安装依赖**

运行：`uv sync`
预期：成功安装 requests 和 lxml

- [ ] **步骤 3：创建网站规则配置文件 sites.json**

```json
{
  "sites": [
    {
      "name": "新笔趣阁",
      "domain": "xbqg8.net",
      "encoding": "utf-8",
      "catalog": {
        "start_marker": "### 全部章节",
        "end_marker": "本站所有小说为转载作品"
      },
      "content": {
        "start_marker": null,
        "end_marker": "本章未完，请翻下一页继续阅读",
        "ad_patterns": [
          "看正@版.*?章节.*",
          "最新章节首发.*?阅读。",
          "<[^>]+>"
        ]
      },
      "chapter_url_pattern": "/\\d+/\\d+/\\d+\\.html"
    }
  ]
}
```

---

## 任务 2：配置管理模块

**文件：**
- 创建：`config.py`

- [ ] **步骤 1：编写配置管理模块**

```python
import json
from pathlib import Path
from dataclasses import dataclass
from typing import Optional


@dataclass
class SiteConfig:
    name: str
    domain: str
    encoding: str
    catalog_start_marker: Optional[str]
    catalog_end_marker: Optional[str]
    content_start_marker: Optional[str]
    content_end_marker: Optional[str]
    ad_patterns: list[str]
    chapter_url_pattern: str


class ConfigManager:
    def __init__(self, config_path: str = "sites.json"):
        self.config_path = Path(config_path)
        self.sites: list[SiteConfig] = []
        self.load()

    def load(self) -> None:
        if not self.config_path.exists():
            return
        with open(self.config_path, "r", encoding="utf-8") as f:
            data = json.load(f)
        self.sites = []
        for site in data.get("sites", []):
            config = SiteConfig(
                name=site["name"],
                domain=site["domain"],
                encoding=site.get("encoding", "utf-8"),
                catalog_start_marker=site.get("catalog", {}).get("start_marker"),
                catalog_end_marker=site.get("catalog", {}).get("end_marker"),
                content_start_marker=site.get("content", {}).get("start_marker"),
                content_end_marker=site.get("content", {}).get("end_marker"),
                ad_patterns=site.get("content", {}).get("ad_patterns", []),
                chapter_url_pattern=site.get("chapter_url_pattern", ""),
            )
            self.sites.append(config)

    def get_site_by_url(self, url: str) -> Optional[SiteConfig]:
        from urllib.parse import urlparse
        domain = urlparse(url).netloc
        for site in self.sites:
            if site.domain in domain:
                return site
        return None
```

- [ ] **步骤 2：验证配置模块可导入**

运行：`uv run python -c "from config import ConfigManager; cm = ConfigManager(); print(len(cm.sites))"`
预期：输出 `1`

---

## 任务 3：数据库模块

**文件：**
- 创建：`database.py`

- [ ] **步骤 1：编写数据库模块**

```python
import sqlite3
from datetime import datetime
from pathlib import Path
from dataclasses import dataclass
from typing import Optional


@dataclass
class Novel:
    id: Optional[int]
    title: str
    author: str
    catalog_url: str
    site_name: str
    total_chapters: int
    downloaded_chapters: int
    status: str
    created_at: Optional[str] = None
    updated_at: Optional[str] = None


@dataclass
class Chapter:
    id: Optional[int]
    novel_id: int
    chapter_index: int
    title: str
    url: str
    content: str
    downloaded: bool
    created_at: Optional[str] = None


class Database:
    def __init__(self, db_path: str = "novels.db"):
        self.db_path = Path(db_path)
        self.conn: Optional[sqlite3.Connection] = None
        self._init_db()

    def _init_db(self) -> None:
        self.conn = sqlite3.connect(self.db_path)
        self.conn.row_factory = sqlite3.Row
        cursor = self.conn.cursor()
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS novels (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                title TEXT NOT NULL,
                author TEXT,
                catalog_url TEXT UNIQUE NOT NULL,
                site_name TEXT,
                total_chapters INTEGER DEFAULT 0,
                downloaded_chapters INTEGER DEFAULT 0,
                status TEXT DEFAULT '连载中',
                created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
                updated_at DATETIME DEFAULT CURRENT_TIMESTAMP
            )
        """)
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS chapters (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                novel_id INTEGER NOT NULL,
                chapter_index INTEGER NOT NULL,
                title TEXT NOT NULL,
                url TEXT UNIQUE NOT NULL,
                content TEXT,
                downloaded INTEGER DEFAULT 0,
                created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
                FOREIGN KEY (novel_id) REFERENCES novels(id)
            )
        """)
        self.conn.commit()

    def add_novel(self, novel: Novel) -> int:
        cursor = self.conn.cursor()
        cursor.execute("""
            INSERT INTO novels (title, author, catalog_url, site_name, total_chapters, downloaded_chapters, status)
            VALUES (?, ?, ?, ?, ?, ?, ?)
        """, (novel.title, novel.author, novel.catalog_url, novel.site_name, novel.total_chapters, novel.downloaded_chapters, novel.status))
        self.conn.commit()
        return cursor.lastrowid

    def get_novel_by_url(self, catalog_url: str) -> Optional[Novel]:
        cursor = self.conn.cursor()
        cursor.execute("SELECT * FROM novels WHERE catalog_url = ?", (catalog_url,))
        row = cursor.fetchone()
        if row:
            return Novel(**dict(row))
        return None

    def get_all_novels(self) -> list[Novel]:
        cursor = self.conn.cursor()
        cursor.execute("SELECT * FROM novels ORDER BY updated_at DESC")
        return [Novel(**dict(row)) for row in cursor.fetchall()]

    def update_novel(self, novel: Novel) -> None:
        cursor = self.conn.cursor()
        cursor.execute("""
            UPDATE novels SET title=?, author=?, total_chapters=?, downloaded_chapters=?, status=?, updated_at=?
            WHERE id=?
        """, (novel.title, novel.author, novel.total_chapters, novel.downloaded_chapters, novel.status, datetime.now().isoformat(), novel.id))
        self.conn.commit()

    def delete_novel(self, novel_id: int) -> None:
        cursor = self.conn.cursor()
        cursor.execute("DELETE FROM chapters WHERE novel_id = ?", (novel_id,))
        cursor.execute("DELETE FROM novels WHERE id = ?", (novel_id,))
        self.conn.commit()

    def add_chapter(self, chapter: Chapter) -> int:
        cursor = self.conn.cursor()
        cursor.execute("""
            INSERT INTO chapters (novel_id, chapter_index, title, url, content, downloaded)
            VALUES (?, ?, ?, ?, ?, ?)
        """, (chapter.novel_id, chapter.chapter_index, chapter.title, chapter.url, chapter.content, chapter.downloaded))
        self.conn.commit()
        return cursor.lastrowid

    def get_chapters_by_novel(self, novel_id: int) -> list[Chapter]:
        cursor = self.conn.cursor()
        cursor.execute("SELECT * FROM chapters WHERE novel_id = ? ORDER BY chapter_index", (novel_id,))
        return [Chapter(**dict(row)) for row in cursor.fetchall()]

    def get_undownloaded_chapters(self, novel_id: int) -> list[Chapter]:
        cursor = self.conn.cursor()
        cursor.execute("SELECT * FROM chapters WHERE novel_id = ? AND downloaded = 0 ORDER BY chapter_index", (novel_id,))
        return [Chapter(**dict(row)) for row in cursor.fetchall()]

    def update_chapter_content(self, chapter_id: int, content: str) -> None:
        cursor = self.conn.cursor()
        cursor.execute("""
            UPDATE chapters SET content=?, downloaded=1 WHERE id=?
        """, (content, chapter_id))
        self.conn.commit()

    def close(self) -> None:
        if self.conn:
            self.conn.close()
```

- [ ] **步骤 2：验证数据库模块可导入**

运行：`uv run python -c "from database import Database; db = Database(':memory:'); print('OK')"`
预期：输出 `OK`

---

## 任务 4：HTML 解析模块

**文件：**
- 创建：`parser.py`

- [ ] **步骤 1：编写解析模块**

```python
import re
from urllib.parse import urljoin
from lxml import html
from config import SiteConfig
from typing import Optional


class Parser:
    def __init__(self, site_config: SiteConfig):
        self.config = site_config

    def parse_catalog(self, html_content: str, base_url: str) -> list[dict]:
        tree = html.fromstring(html_content)
        chapters = []
        links = tree.xpath('//a[@href]')
        in_range = False
        for link in links:
            href = link.get('href', '')
            text = link.text_content().strip()
            if self.config.catalog_start_marker:
                if self.config.catalog_start_marker in text:
                    in_range = True
                    continue
            if self.config.catalog_end_marker:
                if self.config.catalog_end_marker in text:
                    break
            if self.config.chapter_url_pattern:
                if not re.search(self.config.chapter_url_pattern, href):
                    continue
            if in_range or not self.config.catalog_start_marker:
                full_url = urljoin(base_url, href)
                chapters.append({
                    'title': text,
                    'url': full_url
                })
        return chapters

    def parse_content(self, html_content: str) -> str:
        tree = html.fromstring(html_content)
        body = tree.xpath('//body')[0] if tree.xpath('//body') else tree
        content_parts = []
        for node in body.iter():
            if node.text:
                content_parts.append(node.text)
            if node.tail:
                content_parts.append(node.tail)
        content = '\n'.join(content_parts)
        content = self._clean_content(content)
        return content.strip()

    def _clean_content(self, content: str) -> str:
        for pattern in self.config.ad_patterns:
            content = re.sub(pattern, '', content)
        content = re.sub(r'\n{3,}', '\n\n', content)
        if self.config.content_end_marker:
            idx = content.find(self.config.content_end_marker)
            if idx > 0:
                content = content[:idx]
        return content

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
```

- [ ] **步骤 2：验证解析模块可导入**

运行：`uv run python -c "from parser import Parser; print('OK')"`
预期：输出 `OK`

---

## 任务 5：下载器模块

**文件：**
- 创建：`downloader.py`

- [ ] **步骤 1：编写下载器模块**

```python
import requests
from concurrent.futures import ThreadPoolExecutor, as_completed
from typing import Callable, Optional
from parser import Parser
from config import SiteConfig


class Downloader:
    def __init__(self, site_config: SiteConfig, max_workers: int = 5):
        self.config = site_config
        self.max_workers = max_workers
        self.parser = Parser(site_config)
        self.session = requests.Session()
        self.session.headers.update({
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36'
        })
        self._stop_flag = False

    def fetch_url(self, url: str) -> Optional[str]:
        try:
            resp = self.session.get(url, timeout=30)
            resp.encoding = self.config.encoding
            return resp.text
        except Exception as e:
            print(f"Error fetching {url}: {e}")
            return None

    def download_chapter(self, url: str) -> Optional[str]:
        html_content = self.fetch_url(url)
        if html_content:
            return self.parser.parse_content(html_content)
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
```

- [ ] **步骤 2：验证下载器模块可导入**

运行：`uv run python -c "from downloader import Downloader; print('OK')"`
预期：输出 `OK`

---

## 任务 6：导出器模块

**文件：**
- 创建：`exporter.py`

- [ ] **步骤 1：编写导出器模块**

```python
from database import Database, Novel, Chapter
from pathlib import Path


class Exporter:
    def __init__(self, db: Database):
        self.db = db

    def export_to_txt(self, novel: Novel, output_path: str) -> bool:
        chapters = self.db.get_chapters_by_novel(novel.id)
        downloaded_chapters = [ch for ch in chapters if ch.downloaded]
        if not downloaded_chapters:
            return False
        content_lines = [
            novel.title,
            f"作者：{novel.author}",
            "",
            ""
        ]
        for chapter in downloaded_chapters:
            content_lines.append(f"========== {chapter.title} ==========")
            content_lines.append("")
            content_lines.append(chapter.content or "")
            content_lines.append("")
            content_lines.append("")
        output_file = Path(output_path)
        output_file.parent.mkdir(parents=True, exist_ok=True)
        with open(output_file, "w", encoding="utf-8") as f:
            f.write("\n".join(content_lines))
        return True
```

- [ ] **步骤 2：验证导出器模块可导入**

运行：`uv run python -c "from exporter import Exporter; print('OK')"`
预期：输出 `OK`

---

## 任务 7：GUI 界面模块

**文件：**
- 创建：`gui.py`

- [ ] **步骤 1：编写 GUI 主框架**

```python
import tkinter as tk
from tkinter import ttk, messagebox, filedialog, simpledialog
from typing import Optional
from database import Database, Novel, Chapter
from config import ConfigManager, SiteConfig
from downloader import Downloader
from exporter import Exporter
import threading


class NovelApp:
    def __init__(self, root: tk.Tk):
        self.root = root
        self.root.title("小说下载阅读器")
        self.root.geometry("1000x700")
        self.db = Database()
        self.config_manager = ConfigManager()
        self.current_novel: Optional[Novel] = None
        self.downloader: Optional[Downloader] = None
        self._setup_ui()
        self._load_novels()

    def _setup_ui(self) -> None:
        toolbar = ttk.Frame(self.root)
        toolbar.pack(fill=tk.X, padx=5, pady=5)
        ttk.Button(toolbar, text="添加小说", command=self._add_novel).pack(side=tk.LEFT, padx=2)
        ttk.Button(toolbar, text="更新选中", command=self._update_novel).pack(side=tk.LEFT, padx=2)
        ttk.Button(toolbar, text="导出TXT", command=self._export_novel).pack(side=tk.LEFT, padx=2)
        ttk.Button(toolbar, text="删除", command=self._delete_novel).pack(side=tk.LEFT, padx=2)
        ttk.Button(toolbar, text="预览", command=self._preview_chapter).pack(side=tk.LEFT, padx=2)
        self.stop_btn = ttk.Button(toolbar, text="停止", command=self._stop_download, state=tk.DISABLED)
        self.stop_btn.pack(side=tk.LEFT, padx=2)
        main_frame = ttk.Frame(self.root)
        main_frame.pack(fill=tk.BOTH, expand=True, padx=5, pady=5)
        left_frame = ttk.LabelFrame(main_frame, text="小说列表")
        left_frame.pack(side=tk.LEFT, fill=tk.BOTH, expand=True, padx=2)
        columns = ("title", "author", "progress", "site", "status")
        self.novel_tree = ttk.Treeview(left_frame, columns=columns, show="headings", height=15)
        self.novel_tree.heading("title", text="书名")
        self.novel_tree.heading("author", text="作者")
        self.novel_tree.heading("progress", text="进度")
        self.novel_tree.heading("site", text="来源")
        self.novel_tree.heading("status", text="状态")
        self.novel_tree.column("title", width=150)
        self.novel_tree.column("author", width=80)
        self.novel_tree.column("progress", width=80)
        self.novel_tree.column("site", width=80)
        self.novel_tree.column("status", width=60)
        self.novel_tree.pack(fill=tk.BOTH, expand=True)
        self.novel_tree.bind("<<TreeviewSelect>>", self._on_novel_select)
        right_frame = ttk.LabelFrame(main_frame, text="章节列表")
        right_frame.pack(side=tk.RIGHT, fill=tk.BOTH, expand=True, padx=2)
        ch_columns = ("title", "status")
        self.chapter_tree = ttk.Treeview(right_frame, columns=ch_columns, show="headings", height=15)
        self.chapter_tree.heading("title", text="章节")
        self.chapter_tree.heading("status", text="状态")
        self.chapter_tree.column("title", width=200)
        self.chapter_tree.column("status", width=80)
        self.chapter_tree.pack(fill=tk.BOTH, expand=True)
        self.progress_var = tk.StringVar(value="就绪")
        status_bar = ttk.Label(self.root, textvariable=self.progress_var, relief=tk.SUNKEN)
        status_bar.pack(fill=tk.X, side=tk.BOTTOM)

    def _load_novels(self) -> None:
        for item in self.novel_tree.get_children():
            self.novel_tree.delete(item)
        novels = self.db.get_all_novels()
        for novel in novels:
            progress = f"{novel.downloaded_chapters}/{novel.total_chapters}"
            self.novel_tree.insert("", tk.END, iid=str(novel.id), values=(
                novel.title, novel.author, progress, novel.site_name, novel.status
            ))

    def _on_novel_select(self, event) -> None:
        selection = self.novel_tree.selection()
        if not selection:
            return
        novel_id = int(selection[0])
        novels = [n for n in self.db.get_all_novels() if n.id == novel_id]
        if novels:
            self.current_novel = novels[0]
            self._load_chapters()

    def _load_chapters(self) -> None:
        for item in self.chapter_tree.get_children():
            self.chapter_tree.delete(item)
        if not self.current_novel:
            return
        chapters = self.db.get_chapters_by_novel(self.current_novel.id)
        for ch in chapters:
            status = "已下载" if ch.downloaded else "未下载"
            self.chapter_tree.insert("", tk.END, iid=str(ch.id), values=(ch.title, status))
        self.progress_var.set(f"已下载 {self.current_novel.downloaded_chapters} 章 / 共 {self.current_novel.total_chapters} 章")

    def _add_novel(self) -> None:
        url = simpledialog.askstring("添加小说", "请输入目录页 URL:")
        if not url:
            return
        site_config = self.config_manager.get_site_by_url(url)
        if not site_config:
            messagebox.showerror("错误", "未找到匹配的网站配置")
            return
        existing = self.db.get_novel_by_url(url)
        if existing:
            messagebox.showinfo("提示", "该小说已存在")
            return
        self._fetch_and_save_novel(url, site_config)

    def _fetch_and_save_novel(self, url: str, site_config: SiteConfig) -> None:
        self.progress_var.set("正在获取小说信息...")
        self.root.update()
        downloader = Downloader(site_config)
        html_content = downloader.fetch_url(url)
        if not html_content:
            messagebox.showerror("错误", "获取页面失败")
            return
        from parser import Parser
        parser = Parser(site_config)
        novel_info = parser.extract_novel_info(html_content)
        chapters = parser.parse_catalog(html_content, url)
        if not chapters:
            messagebox.showerror("错误", "未找到章节列表")
            return
        novel = Novel(
            id=None,
            title=novel_info['title'],
            author=novel_info['author'],
            catalog_url=url,
            site_name=site_config.name,
            total_chapters=len(chapters),
            downloaded_chapters=0,
            status=novel_info['status']
        )
        novel.id = self.db.add_novel(novel)
        for idx, ch in enumerate(chapters, 1):
            chapter = Chapter(
                id=None,
                novel_id=novel.id,
                chapter_index=idx,
                title=ch['title'],
                url=ch['url'],
                content="",
                downloaded=False
            )
            self.db.add_chapter(chapter)
        self._load_novels()
        self.progress_var.set(f"已添加: {novel.title}")

    def _update_novel(self) -> None:
        if not self.current_novel:
            messagebox.showwarning("提示", "请先选择小说")
            return
        site_config = self.config_manager.get_site_by_url(self.current_novel.catalog_url)
        if not site_config:
            messagebox.showerror("错误", "未找到网站配置")
            return
        chapters = self.db.get_undownloaded_chapters(self.current_novel.id)
        if not chapters:
            messagebox.showinfo("提示", "所有章节已下载")
            return
        self._start_download(chapters, site_config)

    def _start_download(self, chapters: list[Chapter], site_config: SiteConfig) -> None:
        self.stop_btn.config(state=tk.NORMAL)
        self.downloader = Downloader(site_config)
        chapter_dicts = [{'url': ch.url, 'title': ch.title, 'id': ch.id} for ch in chapters]
        total = len(chapters)
        def on_progress(completed: int, total: int) -> None:
            self.progress_var.set(f"下载中: {completed}/{total}")
            self.root.update()
        def on_chapter(ch: dict, content: str) -> None:
            self.db.update_chapter_content(ch['id'], content)
            self.current_novel.downloaded_chapters += 1
            self.db.update_novel(self.current_novel)
        def download_task():
            self.downloader.download_chapters(chapter_dicts, on_progress, on_chapter)
            self.root.after(0, self._on_download_complete)
        thread = threading.Thread(target=download_task, daemon=True)
        thread.start()

    def _on_download_complete(self) -> None:
        self.stop_btn.config(state=tk.DISABLED)
        self._load_chapters()
        self._load_novels()
        self.progress_var.set("下载完成")

    def _stop_download(self) -> None:
        if self.downloader:
            self.downloader.stop()
        self.stop_btn.config(state=tk.DISABLED)

    def _export_novel(self) -> None:
        if not self.current_novel:
            messagebox.showwarning("提示", "请先选择小说")
            return
        file_path = filedialog.asksaveasfilename(
            defaultextension=".txt",
            filetypes=[("文本文件", "*.txt")],
            initialfile=f"{self.current_novel.title}.txt"
        )
        if not file_path:
            return
        exporter = Exporter(self.db)
        if exporter.export_to_txt(self.current_novel, file_path):
            messagebox.showinfo("成功", f"已导出到: {file_path}")
        else:
            messagebox.showerror("错误", "导出失败，可能没有已下载的章节")

    def _delete_novel(self) -> None:
        if not self.current_novel:
            messagebox.showwarning("提示", "请先选择小说")
            return
        if messagebox.askyesno("确认", f"确定删除《{self.current_novel.title}》？"):
            self.db.delete_novel(self.current_novel.id)
            self.current_novel = None
            self._load_novels()
            for item in self.chapter_tree.get_children():
                self.chapter_tree.delete(item)
            self.progress_var.set("已删除")

    def _preview_chapter(self) -> None:
        selection = self.chapter_tree.selection()
        if not selection:
            messagebox.showwarning("提示", "请先选择章节")
            return
        chapter_id = int(selection[0])
        chapters = self.db.get_chapters_by_novel(self.current_novel.id)
        chapter = next((ch for ch in chapters if ch.id == chapter_id), None)
        if not chapter or not chapter.downloaded:
            messagebox.showwarning("提示", "该章节未下载")
            return
        preview_window = tk.Toplevel(self.root)
        preview_window.title(chapter.title)
        preview_window.geometry("600x500")
        text = tk.Text(preview_window, wrap=tk.WORD, padx=10, pady=10)
        text.pack(fill=tk.BOTH, expand=True)
        text.insert(tk.END, chapter.content)
        text.config(state=tk.DISABLED)


def main():
    root = tk.Tk()
    app = NovelApp(root)
    root.mainloop()


if __name__ == "__main__":
    main()
```

- [ ] **步骤 2：验证 GUI 模块可导入**

运行：`uv run python -c "from gui import NovelApp; print('OK')"`
预期：输出 `OK`

---

## 任务 8：更新主入口

**文件：**
- 修改：`main.py`

- [ ] **步骤 1：更新 main.py**

```python
from gui import main

if __name__ == "__main__":
    main()
```

- [ ] **步骤 2：测试应用启动**

运行：`uv run python main.py`
预期：GUI 窗口正常显示

---

## 任务 9：功能测试

- [ ] **步骤 1：测试添加小说**

1. 启动应用
2. 点击"添加小说"
3. 输入 URL: `https://www.xbqg8.net/176/176829/`
4. 验证小说信息正确显示

- [ ] **步骤 2：测试下载章节**

1. 选择刚添加的小说
2. 点击"更新选中"
3. 观察下载进度
4. 验证章节状态变为"已下载"

- [ ] **步骤 3：测试导出 TXT**

1. 选择小说
2. 点击"导出TXT"
3. 选择保存路径
4. 验证文件内容正确

- [ ] **步骤 4：测试预览功能**

1. 选择已下载的章节
2. 点击"预览"
3. 验证预览窗口显示正确内容

---

## 任务 10：最终验证

- [ ] **步骤 1：运行应用完整流程**

运行：`uv run python main.py`
操作：添加小说 -> 下载 -> 预览 -> 导出

- [ ] **步骤 2：验证数据库文件生成**

检查：`novels.db` 文件是否存在

- [ ] **步骤 3：验证导出文件**

检查：导出的 TXT 文件内容是否正确
