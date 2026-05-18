import tkinter as tk
from tkinter import ttk, messagebox, filedialog, simpledialog
from typing import Optional
from database import Database, Novel, Chapter
from config import ConfigManager, SiteConfig
from downloader import Downloader
from exporter import Exporter
import threading
from .settings_dialog import SettingsDialog
from .chapter_manager import ChapterManager
from .novel_properties import NovelPropertiesDialog


class NovelApp:
    def __init__(self, root: tk.Tk):
        self.root = root
        self.root.title("小说下载阅读器")
        self.root.geometry("1200x700")
        self.db = Database()
        self.config_manager = ConfigManager()
        self.current_novel: Optional[Novel] = None
        self.downloader: Optional[Downloader] = None
        self.chapter_manager = ChapterManager(self)
        self._setup_ui()
        self._load_novels()
    
    def _center_window(self, window: tk.Toplevel) -> None:
        """将窗口居中显示在主窗口"""
        self.root.update_idletasks()
        
        main_x = self.root.winfo_x()
        main_y = self.root.winfo_y()
        main_w = self.root.winfo_width()
        main_h = self.root.winfo_height()
        
        window.update_idletasks()
        win_w = window.winfo_width()
        win_h = window.winfo_height()
        
        x = main_x + (main_w - win_w) // 2
        y = main_y + (main_h - win_h) // 2
        
        window.geometry(f"{win_w}x{win_h}+{x}+{y}")

    def _setup_ui(self) -> None:
        self._setup_toolbar()
        self._setup_main_paned()
        self._setup_status_bar()

    def _setup_toolbar(self) -> None:
        toolbar = ttk.Frame(self.root)
        toolbar.pack(fill=tk.X, padx=5, pady=5)
        
        ttk.Button(toolbar, text="添加小说", command=self._add_novel).pack(side=tk.LEFT, padx=2)
        ttk.Button(toolbar, text="更新选中", command=self._update_novel).pack(side=tk.LEFT, padx=2)
        ttk.Button(toolbar, text="导出TXT", command=self._export_novel).pack(side=tk.LEFT, padx=2)
        ttk.Button(toolbar, text="删除", command=self._delete_novel).pack(side=tk.LEFT, padx=2)
        ttk.Button(toolbar, text="设置", command=self._show_settings).pack(side=tk.LEFT, padx=2)
        self.stop_btn = ttk.Button(toolbar, text="停止", command=self._stop_download, state=tk.DISABLED)
        self.stop_btn.pack(side=tk.LEFT, padx=2)
        
        self.delay_var = tk.StringVar(value=f"延迟: {self.config_manager.app_config.download_delay}s")
        delay_label = ttk.Label(toolbar, textvariable=self.delay_var)
        delay_label.pack(side=tk.RIGHT, padx=5)

    def _setup_main_paned(self) -> None:
        main_frame = ttk.Frame(self.root)
        main_frame.pack(fill=tk.BOTH, expand=True, padx=5, pady=5)
        
        paned = ttk.PanedWindow(main_frame, orient=tk.HORIZONTAL)
        paned.pack(fill=tk.BOTH, expand=True)
        
        self._setup_novel_list(paned)
        self.chapter_manager.setup_chapter_list(paned)
        self._setup_preview(paned)

    def _setup_novel_list(self, paned: ttk.PanedWindow) -> None:
        left_frame = ttk.LabelFrame(paned, text="小说列表")
        paned.add(left_frame, weight=1)
        
        novel_scroll = ttk.Scrollbar(left_frame)
        novel_scroll.pack(side=tk.RIGHT, fill=tk.Y)
        
        columns = ("title", "author", "progress", "site", "status")
        self.novel_tree = ttk.Treeview(left_frame, columns=columns, show="headings", yscrollcommand=novel_scroll.set)
        self.novel_tree.heading("title", text="书名")
        self.novel_tree.heading("author", text="作者")
        self.novel_tree.heading("progress", text="进度")
        self.novel_tree.heading("site", text="来源")
        self.novel_tree.heading("status", text="状态")
        self.novel_tree.column("title", width=150, minwidth=100)
        self.novel_tree.column("author", width=80, minwidth=60)
        self.novel_tree.column("progress", width=80, minwidth=60)
        self.novel_tree.column("site", width=80, minwidth=60)
        self.novel_tree.column("status", width=60, minwidth=40)
        self.novel_tree.pack(fill=tk.BOTH, expand=True)
        novel_scroll.config(command=self.novel_tree.yview)
        self.novel_tree.bind("<<TreeviewSelect>>", self._on_novel_select)
        self.novel_tree.bind("<Button-3>", self._show_novel_context_menu)
        
        self.novel_menu = tk.Menu(self.root, tearoff=0)
        self.novel_menu.add_command(label="属性", command=self._show_novel_properties)

    def _setup_preview(self, paned: ttk.PanedWindow) -> None:
        right_frame = ttk.LabelFrame(paned, text="预览")
        paned.add(right_frame, weight=2)
        
        self.preview_text = tk.Text(right_frame, wrap=tk.WORD, padx=5, pady=5, font=("Arial", 10))
        self.preview_text.pack(fill=tk.BOTH, expand=True)
        
        preview_scroll = ttk.Scrollbar(self.preview_text, command=self.preview_text.yview)
        preview_scroll.pack(side=tk.RIGHT, fill=tk.Y)
        self.preview_text.config(yscrollcommand=preview_scroll.set)
        self.preview_text.config(state=tk.DISABLED)

    def _setup_status_bar(self) -> None:
        self.progress_var = tk.StringVar(value="就绪")
        status_bar = ttk.Label(self.root, textvariable=self.progress_var, relief=tk.SUNKEN)
        status_bar.pack(fill=tk.X, side=tk.BOTTOM)

    def _show_settings(self) -> None:
        SettingsDialog(self.root, self.config_manager, self)

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
            self.chapter_manager.load_chapters(self.current_novel.id)
            self._clear_preview()

    def _clear_preview(self) -> None:
        self.preview_text.config(state=tk.NORMAL)
        self.preview_text.delete(1.0, tk.END)
        self.preview_text.config(state=tk.DISABLED)

    def _show_preview(self, title: str, content: str) -> None:
        self.preview_text.config(state=tk.NORMAL)
        self.preview_text.delete(1.0, tk.END)
        self.preview_text.insert(tk.END, f"{title}\n\n")
        self.preview_text.insert(tk.END, content)
        self.preview_text.config(state=tk.DISABLED)

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
        
        downloader = Downloader(
            site_config, 
            max_workers=self.config_manager.app_config.max_workers,
            download_delay=self.config_manager.app_config.download_delay,
            proxy_config=self.config_manager.app_config.proxy
        )
        
        html_content = downloader.fetch_url(url)
        if not html_content:
            messagebox.showerror("错误", "获取页面失败")
            return
            
        from parser import Parser
        parser = Parser(site_config)
        novel_info = parser.extract_novel_info(html_content)
        
        self.progress_var.set("正在获取章节列表...")
        self.root.update()
        
        chapters = downloader.download_catalog(url)
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
        
        chapters = self.db.get_undownloaded_chapters(self.current_novel.id)
        if not chapters:
            messagebox.showinfo("提示", "所有章节已下载")
            return
        
        site_config = self.config_manager.get_site_by_url(self.current_novel.catalog_url)
        if not site_config:
            messagebox.showerror("错误", "未找到网站配置")
            return
        
        self._start_download(chapters, site_config)

    def _start_download(self, chapters: list[Chapter], site_config: SiteConfig) -> None:
        self.stop_btn.config(state=tk.NORMAL)
        
        self.downloader = Downloader(
            site_config,
            max_workers=self.config_manager.app_config.max_workers,
            download_delay=self.config_manager.app_config.download_delay,
            proxy_config=self.config_manager.app_config.proxy
        )
        
        chapter_dicts = [{'url': ch.url, 'title': ch.title, 'id': ch.id} for ch in chapters]
        total = len(chapters)
        
        def on_progress(completed: int, total: int) -> None:
            self.progress_var.set(f"下载中: {completed}/{total}")
            self.root.update()
        
        def on_chapter(ch: dict, content: str) -> None:
            def update_db():
                self.db.update_chapter_content(ch['id'], content)
                self.current_novel.downloaded_chapters += 1
                self.db.update_novel(self.current_novel)
                self.chapter_manager.update_chapter_status(ch['id'], True)
            self.root.after(0, update_db)
        
        def download_task():
            self.downloader.download_chapters(chapter_dicts, on_progress, on_chapter)
            self.root.after(0, self._on_download_complete)
        
        thread = threading.Thread(target=download_task, daemon=True)
        thread.start()

    def _on_download_complete(self) -> None:
        self.stop_btn.config(state=tk.DISABLED)
        self.chapter_manager.load_chapters(self.current_novel.id)
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
        
        selected_chapters = [cid for cid, checked in self.chapter_manager.chapter_checkboxes.items() if checked]
        
        export_dialog = tk.Toplevel(self.root)
        export_dialog.title("导出选项")
        export_dialog.geometry("300x150")
        export_dialog.resizable(False, False)
        export_dialog.transient(self.root)
        export_dialog.grab_set()
        self._center_window(export_dialog)
        
        export_type = tk.IntVar(value=1)
        
        ttk.Radiobutton(export_dialog, text="导出全部章节", variable=export_type, value=0).pack(pady=5)
        ttk.Radiobutton(export_dialog, text="导出选中章节", variable=export_type, value=1).pack(pady=5)
        
        def do_export():
            file_path = filedialog.asksaveasfilename(
                defaultextension=".txt",
                filetypes=[("文本文件", "*.txt")],
                initialfile=f"{self.current_novel.title}.txt"
            )
            
            if not file_path:
                export_dialog.destroy()
                return
            
            exporter = Exporter(self.db)
            chapter_ids = None
            
            if export_type.get() == 1:
                if not selected_chapters:
                    messagebox.showwarning("提示", "没有选中任何章节")
                    export_dialog.destroy()
                    return
                chapter_ids = [int(cid) for cid in selected_chapters]
            
            if exporter.export_to_txt(self.current_novel, file_path, chapter_ids):
                messagebox.showinfo("成功", f"已导出到: {file_path}")
            else:
                messagebox.showerror("错误", "导出失败，可能没有已下载的章节")
            
            export_dialog.destroy()
        
        button_frame = ttk.Frame(export_dialog)
        button_frame.pack(fill=tk.X, padx=10, pady=10)
        
        ttk.Button(button_frame, text="确定", command=do_export).pack(side=tk.RIGHT, padx=5)
        ttk.Button(button_frame, text="取消", command=export_dialog.destroy).pack(side=tk.RIGHT)

    def _delete_novel(self) -> None:
        if not self.current_novel:
            messagebox.showwarning("提示", "请先选择小说")
            return
        
        if messagebox.askyesno("确认", f"确定删除《{self.current_novel.title}》？"):
            self.db.delete_novel(self.current_novel.id)
            self.current_novel = None
            self._load_novels()
            self.chapter_manager.clear_chapters()
            self._clear_preview()
            self.progress_var.set("已删除")

    def _show_novel_context_menu(self, event) -> None:
        item = self.novel_tree.identify_row(event.y)
        if item:
            self.novel_tree.selection_set(item)
            self.novel_menu.post(event.x_root, event.y_root)

    def _show_novel_properties(self) -> None:
        NovelPropertiesDialog(self.root, self)