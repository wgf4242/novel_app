import tkinter as tk
from tkinter import ttk, messagebox
from typing import TYPE_CHECKING, Optional

if TYPE_CHECKING:
    from .main_window import NovelApp


class ChapterManager:
    def __init__(self, app: 'NovelApp'):
        self.app = app
        self.chapter_tree: Optional[ttk.Treeview] = None
        self.chapter_checkboxes = {}
        self.chapter_menu = None
    
    def setup_chapter_list(self, paned: ttk.PanedWindow) -> None:
        middle_frame = ttk.LabelFrame(paned, text="章节列表")
        paned.add(middle_frame, weight=2)
        
        chapter_scroll = ttk.Scrollbar(middle_frame)
        chapter_scroll.pack(side=tk.RIGHT, fill=tk.Y)
        
        ch_columns = ("checkbox", "title", "status")
        self.chapter_tree = ttk.Treeview(
            middle_frame, 
            columns=ch_columns, 
            show="headings", 
            yscrollcommand=chapter_scroll.set,
            selectmode="extended"
        )
        self.chapter_tree.heading("checkbox", text="")
        self.chapter_tree.heading("title", text="章节")
        self.chapter_tree.heading("status", text="状态")
        self.chapter_tree.column("checkbox", width=40, minwidth=40)
        self.chapter_tree.column("title", width=300, minwidth=150)
        self.chapter_tree.column("status", width=80, minwidth=60)
        self.chapter_tree.pack(fill=tk.BOTH, expand=True)
        chapter_scroll.config(command=self.chapter_tree.yview)
        
        self.chapter_tree.bind("<<TreeviewSelect>>", self._on_chapter_select)
        self.chapter_tree.bind("<Control-1>", self._on_chapter_ctrl_click)
        self.chapter_tree.bind("<Button-3>", self._show_chapter_context_menu)
        
        self._setup_context_menu()
    
    def _setup_context_menu(self) -> None:
        self.chapter_menu = tk.Menu(self.app.root, tearoff=0)
        self.chapter_menu.add_command(label="全选", command=self._check_all_chapters)
        self.chapter_menu.add_command(label="取消全选", command=self._uncheck_all_chapters)
        self.chapter_menu.add_separator()
        self.chapter_menu.add_command(label="选中", command=self._check_selected_chapters)
        self.chapter_menu.add_command(label="取消选中", command=self._uncheck_selected_chapters)
        self.chapter_menu.add_separator()
        self.chapter_menu.add_command(label="下载选中章节", command=self._download_selected_chapters)
        self.chapter_menu.add_command(label="下载未完成章节", command=self._download_incomplete_chapters)
    
    def load_chapters(self, novel_id: int) -> None:
        self.clear_chapters()
        
        chapters = self.app.db.get_chapters_by_novel(novel_id)
        for ch in chapters:
            status = "已下载" if ch.downloaded else "未下载"
            checkbox = "[ ]"
            self.chapter_tree.insert("", tk.END, iid=str(ch.id), values=(checkbox, ch.title, status))
            self.chapter_checkboxes[str(ch.id)] = False
        
        self.app.progress_var.set(f"已下载 {self.app.current_novel.downloaded_chapters} 章 / 共 {self.app.current_novel.total_chapters} 章")
    
    def clear_chapters(self) -> None:
        if self.chapter_tree:
            for item in self.chapter_tree.get_children():
                self.chapter_tree.delete(item)
        self.chapter_checkboxes.clear()
    
    def update_chapter_status(self, chapter_id: int, downloaded: bool) -> None:
        item_id = str(chapter_id)
        if item_id in self.chapter_checkboxes:
            values = list(self.chapter_tree.item(item_id, "values"))
            if len(values) >= 3:
                values[2] = "已下载" if downloaded else "未下载"
                self.chapter_tree.item(item_id, values=tuple(values))
    
    def _on_chapter_select(self, event) -> None:
        selection = self.chapter_tree.selection()
        if not selection or not self.app.current_novel:
            return
        
        chapter_id = int(selection[0])
        chapters = self.app.db.get_chapters_by_novel(self.app.current_novel.id)
        chapter = next((ch for ch in chapters if ch.id == chapter_id), None)
        
        if chapter:
            if chapter.downloaded and chapter.content:
                self.app._show_preview(chapter.title, chapter.content)
            else:
                self.app._show_preview(chapter.title, "[该章节尚未下载]")
    
    def _on_chapter_ctrl_click(self, event) -> None:
        item = self.chapter_tree.identify_row(event.y)
        if item:
            self._toggle_chapter_checkbox(item)
    
    def _toggle_chapter_checkbox(self, item_id: str) -> None:
        if item_id in self.chapter_checkboxes:
            self.chapter_checkboxes[item_id] = not self.chapter_checkboxes[item_id]
            checkbox = "[✓]" if self.chapter_checkboxes[item_id] else "[ ]"
            values = list(self.chapter_tree.item(item_id, "values"))
            if len(values) >= 3:
                values[0] = checkbox
                self.chapter_tree.item(item_id, values=tuple(values))
    
    def _show_chapter_context_menu(self, event) -> None:
        item = self.chapter_tree.identify_row(event.y)
        if item:
            self.chapter_tree.selection_add(item)
            self.chapter_menu.post(event.x_root, event.y_root)
    
    def _check_all_chapters(self) -> None:
        for item_id in self.chapter_checkboxes:
            self.chapter_checkboxes[item_id] = True
            checkbox = "[✓]"
            values = list(self.chapter_tree.item(item_id, "values"))
            if len(values) >= 3:
                values[0] = checkbox
                self.chapter_tree.item(item_id, values=tuple(values))
    
    def _uncheck_all_chapters(self) -> None:
        for item_id in self.chapter_checkboxes:
            self.chapter_checkboxes[item_id] = False
            checkbox = "[ ]"
            values = list(self.chapter_tree.item(item_id, "values"))
            if len(values) >= 3:
                values[0] = checkbox
                self.chapter_tree.item(item_id, values=tuple(values))
    
    def _check_selected_chapters(self) -> None:
        selected_items = self.chapter_tree.selection()
        for item_id in selected_items:
            if item_id in self.chapter_checkboxes:
                self.chapter_checkboxes[item_id] = True
                checkbox = "[✓]"
                values = list(self.chapter_tree.item(item_id, "values"))
                if len(values) >= 3:
                    values[0] = checkbox
                    self.chapter_tree.item(item_id, values=tuple(values))
    
    def _uncheck_selected_chapters(self) -> None:
        selected_items = self.chapter_tree.selection()
        for item_id in selected_items:
            if item_id in self.chapter_checkboxes:
                self.chapter_checkboxes[item_id] = False
                checkbox = "[ ]"
                values = list(self.chapter_tree.item(item_id, "values"))
                if len(values) >= 3:
                    values[0] = checkbox
                    self.chapter_tree.item(item_id, values=tuple(values))
    
    def _download_selected_chapters(self) -> None:
        if not self.app.current_novel:
            messagebox.showwarning("提示", "请先选择小说")
            return
        
        selected_chapter_ids = [cid for cid, checked in self.chapter_checkboxes.items() if checked]
        if not selected_chapter_ids:
            messagebox.showwarning("提示", "请先选中要下载的章节")
            return
        
        site_config = self.app.config_manager.get_site_by_url(self.app.current_novel.catalog_url)
        if not site_config:
            messagebox.showerror("错误", "未找到网站配置")
            return
        
        chapters = []
        for cid in selected_chapter_ids:
            ch_list = self.app.db.get_chapters_by_novel(self.app.current_novel.id)
            ch = next((c for c in ch_list if str(c.id) == cid), None)
            if ch:
                chapters.append(ch)
        
        if not chapters:
            messagebox.showwarning("提示", "未找到选中的章节")
            return
        
        self.app._start_download(chapters, site_config)
    
    def _download_incomplete_chapters(self) -> None:
        if not self.app.current_novel:
            messagebox.showwarning("提示", "请先选择小说")
            return
        
        chapters = self.app.db.get_undownloaded_chapters(self.app.current_novel.id)
        if not chapters:
            messagebox.showinfo("提示", "所有章节已下载")
            return
        
        site_config = self.app.config_manager.get_site_by_url(self.app.current_novel.catalog_url)
        if not site_config:
            messagebox.showerror("错误", "未找到网站配置")
            return
        
        self.app._start_download(chapters, site_config)