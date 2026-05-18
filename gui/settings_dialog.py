import tkinter as tk
from tkinter import ttk, messagebox
from typing import TYPE_CHECKING
from config import ConfigManager

if TYPE_CHECKING:
    from .main_window import NovelApp


class SettingsDialog:
    def __init__(self, parent: tk.Tk, config_manager: ConfigManager, app: 'NovelApp'):
        self.parent = parent
        self.config_manager = config_manager
        self.app = app
        self._create_dialog()
    
    def _create_dialog(self) -> None:
        self.settings_window = tk.Toplevel(self.parent)
        self.settings_window.title("设置")
        self.settings_window.geometry("400x500")
        self.settings_window.resizable(False, False)
        self.settings_window.transient(self.parent)
        self.settings_window.grab_set()
        self._center_window(self.settings_window)
        self._create_dialog_content()
    
    def _center_window(self, window: tk.Toplevel) -> None:
        """将窗口居中显示在主窗口"""
        self.parent.update_idletasks()
        
        main_x = self.parent.winfo_x()
        main_y = self.parent.winfo_y()
        main_w = self.parent.winfo_width()
        main_h = self.parent.winfo_height()
        
        window.update_idletasks()
        win_w = window.winfo_width()
        win_h = window.winfo_height()
        
        x = main_x + (main_w - win_w) // 2
        y = main_y + (main_h - win_h) // 2
        
        window.geometry(f"{win_w}x{win_h}+{x}+{y}")
    
    def _create_dialog_content(self) -> None:
        notebook = ttk.Notebook(self.settings_window)
        notebook.pack(fill=tk.BOTH, expand=True, padx=10, pady=10)
        
        self._create_download_tab(notebook)
        self._create_proxy_tab(notebook)
        
        button_frame = ttk.Frame(self.settings_window)
        button_frame.pack(fill=tk.X, padx=10, pady=10)
        
        ttk.Button(button_frame, text="保存", command=self._save_settings).pack(side=tk.RIGHT, padx=5)
        ttk.Button(button_frame, text="取消", command=self.settings_window.destroy).pack(side=tk.RIGHT)
    
    def _create_download_tab(self, notebook: ttk.Notebook) -> None:
        download_frame = ttk.Frame(notebook, padding=10)
        notebook.add(download_frame, text="下载设置")
        
        self.delay_var = tk.DoubleVar(value=self.config_manager.app_config.download_delay)
        ttk.Label(download_frame, text="下载间隔(秒):").grid(row=0, column=0, sticky=tk.W, pady=10)
        ttk.Spinbox(
            download_frame, 
            from_=0.0, to=10.0, increment=0.1, 
            textvariable=self.delay_var, width=15
        ).grid(row=0, column=1, pady=10)
        
        self.workers_var = tk.IntVar(value=self.config_manager.app_config.max_workers)
        ttk.Label(download_frame, text="并发下载数:").grid(row=1, column=0, sticky=tk.W, pady=10)
        ttk.Spinbox(
            download_frame, 
            from_=1, to=10, 
            textvariable=self.workers_var, width=15
        ).grid(row=1, column=1, pady=10)
    
    def _create_proxy_tab(self, notebook: ttk.Notebook) -> None:
        proxy_frame = ttk.Frame(notebook, padding=10)
        notebook.add(proxy_frame, text="代理设置")
        
        self.proxy_enabled_var = tk.BooleanVar(value=self.config_manager.app_config.proxy.enabled)
        ttk.Checkbutton(proxy_frame, text="启用代理", variable=self.proxy_enabled_var).grid(
            row=0, column=0, columnspan=2, sticky=tk.W, pady=10
        )
        
        self.proxy_type_var = tk.StringVar(value=self.config_manager.app_config.proxy.proxy_type)
        ttk.Label(proxy_frame, text="代理类型:").grid(row=1, column=0, sticky=tk.W, pady=5)
        ttk.Combobox(
            proxy_frame, 
            textvariable=self.proxy_type_var, 
            values=["http", "https", "socks5"], 
            width=12
        ).grid(row=1, column=1, pady=5)
        
        self.proxy_host_var = tk.StringVar(value=self.config_manager.app_config.proxy.host)
        ttk.Label(proxy_frame, text="代理地址:").grid(row=2, column=0, sticky=tk.W, pady=5)
        ttk.Entry(proxy_frame, textvariable=self.proxy_host_var, width=20).grid(row=2, column=1, pady=5)
        
        self.proxy_port_var = tk.IntVar(value=self.config_manager.app_config.proxy.port)
        ttk.Label(proxy_frame, text="代理端口:").grid(row=3, column=0, sticky=tk.W, pady=5)
        ttk.Entry(proxy_frame, textvariable=self.proxy_port_var, width=15).grid(row=3, column=1, pady=5)
        
        self.proxy_user_var = tk.StringVar(value=self.config_manager.app_config.proxy.username)
        ttk.Label(proxy_frame, text="用户名:").grid(row=4, column=0, sticky=tk.W, pady=5)
        ttk.Entry(proxy_frame, textvariable=self.proxy_user_var, width=20).grid(row=4, column=1, pady=5)
        
        self.proxy_pass_var = tk.StringVar(value=self.config_manager.app_config.proxy.password)
        ttk.Label(proxy_frame, text="密码:").grid(row=5, column=0, sticky=tk.W, pady=5)
        ttk.Entry(proxy_frame, textvariable=self.proxy_pass_var, show="*", width=20).grid(row=5, column=1, pady=5)
    
    def _save_settings(self) -> None:
        delay = self.delay_var.get()
        workers = self.workers_var.get()
        
        if delay < 0:
            messagebox.showerror("错误", "下载间隔不能为负数")
            return
        
        if workers < 1 or workers > 10:
            messagebox.showerror("错误", "并发数必须在1-10之间")
            return
        
        if self.proxy_enabled_var.get():
            if not self.proxy_host_var.get():
                messagebox.showerror("错误", "请输入代理地址")
                return
            
            if self.proxy_port_var.get() < 1 or self.proxy_port_var.get() > 65535:
                messagebox.showerror("错误", "端口号必须在1-65535之间")
                return
        
        self.config_manager.app_config.download_delay = delay
        self.config_manager.app_config.max_workers = workers
        self.config_manager.app_config.proxy.enabled = self.proxy_enabled_var.get()
        self.config_manager.app_config.proxy.proxy_type = self.proxy_type_var.get()
        self.config_manager.app_config.proxy.host = self.proxy_host_var.get()
        self.config_manager.app_config.proxy.port = self.proxy_port_var.get()
        self.config_manager.app_config.proxy.username = self.proxy_user_var.get()
        self.config_manager.app_config.proxy.password = self.proxy_pass_var.get()
        self.config_manager.save_app_config()
        
        self.app.delay_var.set(f"延迟: {delay}s")
        self.settings_window.destroy()
        messagebox.showinfo("成功", "设置已保存")
