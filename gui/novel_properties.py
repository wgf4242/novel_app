import tkinter as tk
from tkinter import ttk, messagebox
from typing import TYPE_CHECKING
from database import Novel

if TYPE_CHECKING:
    from .main_window import NovelApp


class NovelPropertiesDialog:
    def __init__(self, parent: tk.Tk, app: 'NovelApp'):
        self.parent = parent
        self.app = app
        self._create_dialog()
    
    def _create_dialog(self) -> None:
        if not self.app.current_novel:
            messagebox.showwarning("提示", "请先选择小说")
            return
        
        self.dialog = tk.Toplevel(self.parent)
        self.dialog.title("小说属性")
        self.dialog.geometry("400x300")
        self.dialog.resizable(False, False)
        self.dialog.transient(self.parent)
        self.dialog.grab_set()
        
        frame = ttk.Frame(self.dialog, padding=10)
        frame.pack(fill=tk.BOTH, expand=True)
        
        novel = self.app.current_novel
        
        # 书名
        ttk.Label(frame, text="书名:").grid(row=0, column=0, sticky=tk.W, pady=5)
        self.title_var = tk.StringVar(value=novel.title)
        ttk.Entry(frame, textvariable=self.title_var, width=40).grid(row=0, column=1, pady=5)
        
        # 作者
        ttk.Label(frame, text="作者:").grid(row=1, column=0, sticky=tk.W, pady=5)
        self.author_var = tk.StringVar(value=novel.author)
        ttk.Entry(frame, textvariable=self.author_var, width=40).grid(row=1, column=1, pady=5)
        
        # 目录URL
        ttk.Label(frame, text="目录URL:").grid(row=2, column=0, sticky=tk.W, pady=5)
        self.url_var = tk.StringVar(value=novel.catalog_url)
        url_entry = ttk.Entry(frame, textvariable=self.url_var, width=40)
        url_entry.grid(row=2, column=1, pady=5)
        
        # 来源网站
        ttk.Label(frame, text="来源网站:").grid(row=3, column=0, sticky=tk.W, pady=5)
        self.site_var = tk.StringVar(value=novel.site_name)
        ttk.Entry(frame, textvariable=self.site_var, width=40).grid(row=3, column=1, pady=5)
        
        # 状态
        ttk.Label(frame, text="状态:").grid(row=4, column=0, sticky=tk.W, pady=5)
        self.status_var = tk.StringVar(value=novel.status)
        ttk.Combobox(frame, textvariable=self.status_var, values=["连载中", "已完结", "未知"], width=37).grid(row=4, column=1, pady=5)
        
        # 统计信息（只读）
        ttk.Label(frame, text="章节总数:").grid(row=5, column=0, sticky=tk.W, pady=5)
        ttk.Label(frame, text=str(novel.total_chapters)).grid(row=5, column=1, sticky=tk.W, pady=5)
        
        ttk.Label(frame, text="已下载:").grid(row=6, column=0, sticky=tk.W, pady=5)
        ttk.Label(frame, text=str(novel.downloaded_chapters)).grid(row=6, column=1, sticky=tk.W, pady=5)
        
        # 按钮
        button_frame = ttk.Frame(self.dialog)
        button_frame.pack(fill=tk.X, padx=10, pady=10)
        
        ttk.Button(button_frame, text="确定", command=self._save_properties).pack(side=tk.RIGHT, padx=5)
        ttk.Button(button_frame, text="取消", command=self.dialog.destroy).pack(side=tk.RIGHT)
    
    def _save_properties(self) -> None:
        title = self.title_var.get().strip()
        author = self.author_var.get().strip()
        url = self.url_var.get().strip()
        site_name = self.site_var.get().strip()
        status = self.status_var.get()
        
        if not title:
            messagebox.showerror("错误", "书名不能为空")
            return
        
        if not url:
            messagebox.showerror("错误", "URL不能为空")
            return
        
        novel = self.app.current_novel
        novel.title = title
        novel.author = author
        novel.catalog_url = url
        novel.site_name = site_name
        novel.status = status
        
        self.app.db.update_novel(novel)
        self.app._load_novels()
        self.app.progress_var.set("属性已更新")
        self.dialog.destroy()