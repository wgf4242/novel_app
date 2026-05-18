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
        self._init_db()

    def _get_connection(self) -> sqlite3.Connection:
        # 每次操作时创建新连接
        conn = sqlite3.connect(self.db_path, check_same_thread=False)
        conn.row_factory = sqlite3.Row
        return conn

    def _init_db(self) -> None:
        conn = self._get_connection()
        cursor = conn.cursor()
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
        conn.commit()
        conn.close()

    def add_novel(self, novel: Novel) -> int:
        conn = self._get_connection()
        cursor = conn.cursor()
        cursor.execute("""
            INSERT INTO novels (title, author, catalog_url, site_name, total_chapters, downloaded_chapters, status)
            VALUES (?, ?, ?, ?, ?, ?, ?)
        """, (novel.title, novel.author, novel.catalog_url, novel.site_name, novel.total_chapters, novel.downloaded_chapters, novel.status))
        conn.commit()
        last_id = cursor.lastrowid
        conn.close()
        return last_id

    def get_novel_by_url(self, catalog_url: str) -> Optional[Novel]:
        conn = self._get_connection()
        cursor = conn.cursor()
        cursor.execute("SELECT * FROM novels WHERE catalog_url = ?", (catalog_url,))
        row = cursor.fetchone()
        result = None
        if row:
            result = Novel(**dict(row))
        conn.close()
        return result

    def get_all_novels(self) -> list[Novel]:
        conn = self._get_connection()
        cursor = conn.cursor()
        cursor.execute("SELECT * FROM novels ORDER BY updated_at DESC")
        result = [Novel(**dict(row)) for row in cursor.fetchall()]
        conn.close()
        return result

    def update_novel(self, novel: Novel) -> None:
        conn = self._get_connection()
        cursor = conn.cursor()
        cursor.execute("""
            UPDATE novels SET title=?, author=?, catalog_url=?, site_name=?, total_chapters=?, downloaded_chapters=?, status=?, updated_at=?
            WHERE id=?
        """, (novel.title, novel.author, novel.catalog_url, novel.site_name, novel.total_chapters, novel.downloaded_chapters, novel.status, datetime.now().isoformat(), novel.id))
        conn.commit()
        conn.close()

    def delete_novel(self, novel_id: int) -> None:
        conn = self._get_connection()
        cursor = conn.cursor()
        cursor.execute("DELETE FROM chapters WHERE novel_id = ?", (novel_id,))
        cursor.execute("DELETE FROM novels WHERE id = ?", (novel_id,))
        conn.commit()
        conn.close()

    def add_chapter(self, chapter: Chapter) -> int:
        conn = self._get_connection()
        cursor = conn.cursor()
        cursor.execute("""
            INSERT INTO chapters (novel_id, chapter_index, title, url, content, downloaded)
            VALUES (?, ?, ?, ?, ?, ?)
        """, (chapter.novel_id, chapter.chapter_index, chapter.title, chapter.url, chapter.content, chapter.downloaded))
        conn.commit()
        last_id = cursor.lastrowid
        conn.close()
        return last_id

    def get_chapters_by_novel(self, novel_id: int) -> list[Chapter]:
        conn = self._get_connection()
        cursor = conn.cursor()
        cursor.execute("SELECT * FROM chapters WHERE novel_id = ? ORDER BY chapter_index", (novel_id,))
        result = [Chapter(**dict(row)) for row in cursor.fetchall()]
        conn.close()
        return result

    def get_undownloaded_chapters(self, novel_id: int) -> list[Chapter]:
        conn = self._get_connection()
        cursor = conn.cursor()
        cursor.execute("SELECT * FROM chapters WHERE novel_id = ? AND downloaded = 0 ORDER BY chapter_index", (novel_id,))
        result = [Chapter(**dict(row)) for row in cursor.fetchall()]
        conn.close()
        return result

    def update_chapter_content(self, chapter_id: int, content: str) -> None:
        conn = self._get_connection()
        cursor = conn.cursor()
        cursor.execute("""
            UPDATE chapters SET content=?, downloaded=1 WHERE id=?
        """, (content, chapter_id))
        conn.commit()
        conn.close()

    def close(self) -> None:
        pass  # 不再需要保留连接，每次操作都新建连接
