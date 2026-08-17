import os
import tkinter as tk
from tkinter import filedialog, messagebox
import customtkinter as ctk

from utils.config_manager import config_mgr
from utils.file_utils import reveal_in_explorer
from ui.components.file_tree import LazyFileTree
from ui.components.settings_modal import SettingsModal

from ui.tabs.tab_classify import ClassifyTab
from ui.tabs.tab_batch import BatchTab
from ui.tabs.tab_search import SearchTab
from ui.tabs.tab_tools import ToolsTab
from ui.tabs.tab_history import HistoryTab

class App(ctk.CTk):
    """智能文件夹管理大师 Pro - 主窗口"""

    def __init__(self):
        super().__init__()

        # 加载外观配置
        theme_mode = config_mgr.get("theme_mode", "System")
        color_theme = config_mgr.get("color_theme", "blue")
        ctk.set_appearance_mode(theme_mode)
        ctk.set_default_color_theme(color_theme)

        self.title("智能文件夹管理大师 Pro - Smart Folder Manager")
        self.geometry("1260x820")
        self.minsize(1000, 680)

        # 当前选中的根路径
        last_path = config_mgr.get("last_path", "")
        if not last_path or not os.path.exists(last_path):
            last_path = os.getcwd()
        self.current_path_var = tk.StringVar(value=last_path)

        self._build_layout()
        self._init_data()

    def _build_layout(self):
        # 整体左右分栏
        self.grid_rowconfigure(0, weight=1)
        self.grid_columnconfigure(1, weight=1)

        # 1. 左侧导航侧边栏
        self.sidebar = ctk.CTkFrame(self, width=200, corner_radius=0)
        self.sidebar.grid(row=0, column=0, sticky="nsew")
        self.sidebar.grid_rowconfigure(7, weight=1)

        # 标题 Logo
        self.logo_label = ctk.CTkLabel(
            self.sidebar,
            text="📁 文件夹管理\n大师 Pro",
            font=ctk.CTkFont(size=18, weight="bold")
        )
        self.logo_label.grid(row=0, column=0, padx=20, pady=(20, 20))

        # 导航按钮组
        self.nav_buttons = {}
        nav_items = [
            ("classify", "📁 智能分类", self._show_classify_tab),
            ("batch", "⚡ 批量操作", self._show_batch_tab),
            ("search", "🔍 智能搜索", self._show_search_tab),
            ("tools", "🛠️ 实用工具", self._show_tools_tab),
            ("history", "📜 历史撤销", self._show_history_tab),
        ]

        for idx, (tab_key, label_text, cmd) in enumerate(nav_items, start=1):
            btn = ctk.CTkButton(
                self.sidebar,
                text=label_text,
                height=36,
                font=ctk.CTkFont(size=13, weight="bold"),
                anchor="w",
                fg_color="transparent",
                text_color=("gray10", "gray90"),
                hover_color=("gray75", "gray25"),
                command=cmd
            )
            btn.grid(row=idx, column=0, padx=15, pady=4, sticky="ew")
            self.nav_buttons[tab_key] = btn

        # 侧边栏底部设置与外观
        self.settings_btn = ctk.CTkButton(
            self.sidebar,
            text="⚙️ 设置中心",
            height=32,
            fg_color="transparent",
            border_width=1,
            text_color=("gray10", "gray90"),
            command=self._open_settings_modal
        )
        self.settings_btn.grid(row=8, column=0, padx=15, pady=(0, 10), sticky="ew")

        self.theme_switch = ctk.CTkOptionMenu(
            self.sidebar,
            values=["System", "Dark", "Light"],
            command=self._on_theme_switch,
            height=28
        )
        self.theme_switch.set(config_mgr.get("theme_mode", "System"))
        self.theme_switch.grid(row=9, column=0, padx=15, pady=(0, 15), sticky="ew")

        # 2. 右侧主工作区
        self.main_work_area = ctk.CTkFrame(self, fg_color="transparent")
        self.main_work_area.grid(row=0, column=1, sticky="nsew", padx=10, pady=10)
        self.main_work_area.grid_rowconfigure(1, weight=1)
        self.main_work_area.grid_columnconfigure(0, weight=1)

        # 2.1 顶部路径与操作工具栏
        self.top_bar = ctk.CTkFrame(self.main_work_area, height=48)
        self.top_bar.grid(row=0, column=0, sticky="ew", pady=(0, 8))

        ctk.CTkLabel(self.top_bar, text="当前路径:", font=ctk.CTkFont(size=13, weight="bold")).pack(side="left", padx=(15, 8))

        self.path_entry = ctk.CTkEntry(self.top_bar, textvariable=self.current_path_var, font=ctk.CTkFont(size=12))
        self.path_entry.pack(side="left", fill="x", expand=True, padx=(0, 8))
        self.path_entry.bind("<Return>", lambda e: self._on_path_entry_submitted())

        self.browse_btn = ctk.CTkButton(
            self.top_bar,
            text="📂 浏览...",
            width=80,
            command=self._browse_directory
        )
        self.browse_btn.pack(side="left", padx=(0, 6))

        self.refresh_btn = ctk.CTkButton(
            self.top_bar,
            text="🔄 刷新",
            width=70,
            fg_color="gray",
            hover_color="#555",
            command=self.refresh_all
        )
        self.refresh_btn.pack(side="left", padx=(0, 6))

        self.open_dir_btn = ctk.CTkButton(
            self.top_bar,
            text="↗ 打开",
            width=65,
            fg_color="gray",
            hover_color="#555",
            command=self._open_in_explorer
        )
        self.open_dir_btn.pack(side="left", padx=(0, 12))

        # 2.2 中间工作区（左侧文件树 + 右侧功能面板）
        self.center_split = ctk.CTkFrame(self.main_work_area, fg_color="transparent")
        self.center_split.grid(row=1, column=0, sticky="nsew")
        self.center_split.grid_rowconfigure(0, weight=1)
        self.center_split.grid_columnconfigure(0, weight=0)
        self.center_split.grid_columnconfigure(1, weight=1)

        # 左侧文件树容器
        self.tree_container = ctk.CTkFrame(self.center_split, width=240)
        self.tree_container.grid(row=0, column=0, sticky="nsew", padx=(0, 8))
        self.tree_container.pack_propagate(False)

        tree_header = ctk.CTkFrame(self.tree_container, fg_color="transparent")
        tree_header.pack(fill="x", padx=6, pady=4)
        ctk.CTkLabel(tree_header, text="🌳 目录树", font=ctk.CTkFont(size=12, weight="bold")).pack(side="left")

        self.file_tree = LazyFileTree(
            self.tree_container,
            on_directory_selected=self._on_tree_dir_selected,
            on_directory_navigate=self._on_tree_dir_navigate
        )
        self.file_tree.pack(fill="both", expand=True, padx=4, pady=(0, 4))

        # 右侧 Tab 内容容器
        self.tab_container = ctk.CTkFrame(self.center_split)
        self.tab_container.grid(row=0, column=1, sticky="nsew")

        # 实例化所有 Tab
        self.tab_instances = {
            "classify": ClassifyTab(self.tab_container, get_current_path=self.get_current_path, on_changed=self.refresh_all),
            "batch": BatchTab(self.tab_container, get_current_path=self.get_current_path, on_changed=self.refresh_all),
            "search": SearchTab(self.tab_container, get_current_path=self.get_current_path),
            "tools": ToolsTab(self.tab_container, get_current_path=self.get_current_path, on_changed=self.refresh_all),
            "history": HistoryTab(self.tab_container, on_changed=self.refresh_all)
        }

        # 2.3 底部状态栏
        self.status_bar = ctk.CTkFrame(self.main_work_area, height=24)
        self.status_bar.grid(row=2, column=0, sticky="ew", pady=(8, 0))

        self.status_label = ctk.CTkLabel(self.status_bar, text="就绪", font=ctk.CTkFont(size=11), anchor="w")
        self.status_label.pack(side="left", padx=10)

        ai_provider = config_mgr.get("ai.provider", "Moonshot")
        ai_model = config_mgr.get("ai.model", "moonshot-v1-8k")
        self.ai_indicator = ctk.CTkLabel(
            self.status_bar,
            text=f"🤖 当前AI模型: {ai_provider} ({ai_model})",
            font=ctk.CTkFont(size=11),
            text_color="#888"
        )
        self.ai_indicator.pack(side="right", padx=10)

    def _init_data(self):
        # 默认选中第一个 Tab
        self._show_tab("classify")
        # 载入初始路径文件树
        current_dir = self.get_current_path()
        if os.path.exists(current_dir):
            self.file_tree.set_root_path(current_dir)

    def get_current_path(self) -> str:
        return self.current_path_var.get().strip()

    def set_current_path(self, path: str):
        if path and os.path.exists(path):
            self.current_path_var.set(path)
            config_mgr.set("last_path", path)
            config_mgr.save_config()
            self.file_tree.set_root_path(path)

    def _browse_directory(self):
        folder = filedialog.askdirectory(initialdir=self.get_current_path(), parent=self)
        if folder:
            self.set_current_path(folder)

    def _on_path_entry_submitted(self):
        path = self.get_current_path()
        if os.path.exists(path) and os.path.isdir(path):
            self.set_current_path(path)
        else:
            messagebox.showwarning("错误", "输入的文件夹路径不存在。", parent=self)

    def _on_tree_dir_selected(self, selected_dir: str):
        self.current_path_var.set(selected_dir)
        config_mgr.set("last_path", selected_dir)
        config_mgr.save_config()

    def _on_tree_dir_navigate(self, dir_path: str):
        """双击子目录时进入该目录作为新根目录"""
        self.set_current_path(dir_path)

    def _open_in_explorer(self):
        path = self.get_current_path()
        if path and os.path.exists(path):
            reveal_in_explorer(path)

    def refresh_all(self):
        path = self.get_current_path()
        if path and os.path.exists(path):
            self.file_tree.set_root_path(path)
        # 如果当前在历史记录页，则刷新历史
        if hasattr(self.tab_instances["history"], "refresh_history"):
            self.tab_instances["history"].refresh_history()

    def _show_tab(self, tab_key: str):
        for k, btn in self.nav_buttons.items():
            if k == tab_key:
                btn.configure(fg_color=("gray70", "gray30"))
            else:
                btn.configure(fg_color="transparent")

        for k, frame in self.tab_instances.items():
            if k == tab_key:
                frame.pack(fill="both", expand=True)
            else:
                frame.pack_forget()

    def _show_classify_tab(self):
        self._show_tab("classify")

    def _show_batch_tab(self):
        self._show_tab("batch")

    def _show_search_tab(self):
        self._show_tab("search")

    def _show_tools_tab(self):
        self._show_tab("tools")

    def _show_history_tab(self):
        self._show_tab("history")
        self.tab_instances["history"].refresh_history()

    def _on_theme_switch(self, mode: str):
        ctk.set_appearance_mode(mode)
        config_mgr.set("theme_mode", mode)
        config_mgr.save_config()

    def _open_settings_modal(self):
        def on_settings_saved():
            provider = config_mgr.get("ai.provider", "Moonshot")
            model = config_mgr.get("ai.model", "moonshot-v1-8k")
            self.ai_indicator.configure(text=f"🤖 当前AI模型: {provider} ({model})")
        SettingsModal(self, on_save_callback=on_settings_saved)
