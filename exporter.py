from database import Database, Novel, Chapter
from pathlib import Path


class Exporter:
    def __init__(self, db: Database):
        self.db = db

    def export_to_txt(self, novel: Novel, output_path: str, chapter_ids: list[int] = None) -> bool:
        if chapter_ids:
            return self._export_selected_chapters(novel, output_path, chapter_ids)
        else:
            return self._export_all_chapters(novel, output_path)
    
    def _export_all_chapters(self, novel: Novel, output_path: str) -> bool:
        chapters = self.db.get_chapters_by_novel(novel.id)
        downloaded_chapters = [ch for ch in chapters if ch.downloaded]
        return self._write_chapters(novel, downloaded_chapters, output_path)
    
    def _export_selected_chapters(self, novel: Novel, output_path: str, chapter_ids: list[int]) -> bool:
        chapters = self.db.get_chapters_by_novel(novel.id)
        selected_chapters = [ch for ch in chapters if ch.id in chapter_ids and ch.downloaded]
        return self._write_chapters(novel, selected_chapters, output_path)
    
    def _write_chapters(self, novel: Novel, chapters: list[Chapter], output_path: str) -> bool:
        if not chapters:
            return False
        
        content_lines = [
            novel.title,
            f"作者：{novel.author}",
            "",
            ""
        ]
        
        for chapter in chapters:
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