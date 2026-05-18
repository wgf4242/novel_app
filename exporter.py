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
