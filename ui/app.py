import os
import tkinter as tk
from tkinter import filedialog, messagebox, ttk
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
from ui.theme import (
    COLOR_PRIMARY, COLOR_PRIMARY_HOVER,
    COLOR_SECONDARY, COLOR_SECONDARY_HOVER,
    COLOR_AI, COLOR_AI_TEXT,
    THEME_COLORS, apply_treeview_theme
)

class SidebarNavButton(ctk.CTkFrame):
    """侧边栏独立导航胶囊按钮（严格对齐图标与文字，解决跨平台/多字符集 Emoji 宽度错位问题）"""

    def __init__(self, master, icon: str, title: str, command=None, **kwargs):
        super().__init__(
            master,
            height=38,
            corner_radius=8,
            fg_color="transparent",
            cursor="hand2",
            **kwargs
        )
        self.command = command
        self.is_active = False
        self.pack_propagate(False)

        # 1. 严格固定宽度的图标容器 (固定 26px 居中对齐)
        self.icon_label = ctk.CTkLabel(
            self,
            text=icon,
            width=26,
            font=ctk.CTkFont(size=14),
            text_color=("gray20", "gray85"),
            anchor="center"
        )
        self.icon_label.pack(side="left", padx=(10, 8))

        # 2. 严格左对齐的标题文本 (所有行起始 X 坐标 100% 绝对对齐)
        self.title_label = ctk.CTkLabel(
            self,
            text=title,
            font=ctk.CTkFont(size=13, weight="bold"),
            text_color=("gray20", "gray85"),
            anchor="w"
        )
        self.title_label.pack(side="left", fill="x", expand=True, padx=(0, 10))

        # 绑定点击与悬浮事件
        for widget in (self, self.icon_label, self.title_label):
            widget.bind("<Button-1>", lambda e: self._handle_click())
            widget.bind("<Enter>", lambda e: self._handle_enter())
            widget.bind("<Leave>", lambda e: self._handle_leave())

    def _handle_click(self):
        if self.command:
            self.command()

    def _handle_enter(self):
        if not self.is_active:
            self.configure(fg_color=("gray90", "#252B3B"))

    def _handle_leave(self):
        if not self.is_active:
            self.configure(fg_color="transparent")

    def set_active(self, active: bool):
        self.is_active = active
        if active:
            self.configure(fg_color=COLOR_PRIMARY)
            self.icon_label.configure(text_color="white")
            self.title_label.configure(text_color="white")
        else:
            self.configure(fg_color="transparent")
            self.icon_label.configure(text_color=("gray20", "gray85"))
            self.title_label.configure(text_color=("gray20", "gray85"))


class App(ctk.CTk):
    """智能文件夹管理大师 Pro (SFM Pro) - Modern Slate 主工作站"""

    def __init__(self):
        super().__init__()

        # 加载外观配置
        theme_mode = config_mgr.get("theme_mode", "System")
        color_theme = config_mgr.get("color_theme", "blue")
        ctk.set_appearance_mode(theme_mode)
        ctk.set_default_color_theme(color_theme)

        self.title("智能文件夹管理大师 Pro - Smart Folder Manager")
        self.geometry("1280x840")
        self.minsize(1020, 700)

        # 当前选中的根路径
        last_path = config_mgr.get("last_path", "")
        if not last_path or not os.path.exists(last_path):
            last_path = os.getcwd()
        self.current_path_var = tk.StringVar(value=last_path)
        self.tree_visible = True

        self._build_layout()
        self._init_data()

    def _build_layout(self):
        # 整体左右分栏
        self.grid_rowconfigure(0, weight=1)
        self.grid_columnconfigure(1, weight=1)

        # ==========================================
        # 1. 左侧导航侧边栏 (Sidebar Navigation)
        # ==========================================
        self.sidebar = ctk.CTkFrame(
            self,
            width=210,
            corner_radius=0,
            border_width=1,
            border_color=("gray85", "#2E3648"),
            fg_color=("white", "#1B1F2A")
        )
        self.sidebar.grid(row=0, column=0, sticky="nsew")
        self.sidebar.grid_rowconfigure(7, weight=1)

        # 品牌 Logo 卡片
        logo_card = ctk.CTkFrame(self.sidebar, fg_color="transparent")
        logo_card.grid(row=0, column=0, padx=16, pady=(20, 16), sticky="ew")

        brand_top = ctk.CTkFrame(logo_card, fg_color="transparent")
        brand_top.pack(fill="x")

        ctk.CTkLabel(
            brand_top,
            text="📁 SFM",
            font=ctk.CTkFont(size=20, weight="bold"),
            text_color=COLOR_PRIMARY
        ).pack(side="left")

        pro_badge = ctk.CTkLabel(
            brand_top,
            text="PRO",
            font=ctk.CTkFont(size=10, weight="bold"),
            fg_color=COLOR_PRIMARY,
            text_color="white",
            corner_radius=4,
            width=36,
            height=18
        )
        pro_badge.pack(side="left", padx=(6, 0))

        ctk.CTkLabel(
            logo_card,
            text="智能文件夹管理大师",
            font=ctk.CTkFont(size=12, weight="bold"),
            text_color=("gray30", "gray85")
        ).pack(anchor="w", pady=(2, 0))

        # 导航胶囊按钮组 (图标与文字严格对齐)
        self.nav_buttons = {}
        nav_items = [
            ("classify", "📁", "智能分类", self._show_classify_tab),
            ("batch", "⚡", "批量操作", self._show_batch_tab),
            ("search", "🔍", "智能搜索", self._show_search_tab),
            ("tools", "🛠", "实用工具", self._show_tools_tab),
            ("history", "📜", "历史撤销", self._show_history_tab),
        ]

        for idx, (tab_key, icon, title, cmd) in enumerate(nav_items, start=1):
            btn = SidebarNavButton(
                self.sidebar,
                icon=icon,
                title=title,
                command=cmd
            )
            btn.grid(row=idx, column=0, padx=12, pady=3, sticky="ew")
            self.nav_buttons[tab_key] = btn

        # 侧边栏底部设置与主题
        bottom_box = ctk.CTkFrame(self.sidebar, fg_color="transparent")
        bottom_box.grid(row=8, column=0, padx=12, pady=(0, 16), sticky="sew")

        self.settings_btn = ctk.CTkButton(
            bottom_box,
            text="⚙ 设置中心",
            height=34,
            corner_radius=8,
            font=ctk.CTkFont(size=12, weight="bold"),
            fg_color="transparent",
            border_width=1,
            border_color=("gray75", "#3A4459"),
            text_color=("gray20", "gray85"),
            hover_color=("gray90", "#252B3B"),
            command=self._open_settings_modal
        )
        self.settings_btn.pack(fill="x", pady=(0, 8))

        theme_row = ctk.CTkFrame(bottom_box, fg_color="transparent")
        theme_row.pack(fill="x")

        # 优化“主题”二字字体大小为 13pt 加粗，更加醒目清晰
        ctk.CTkLabel(
            theme_row,
            text="🌓 主题:",
            font=ctk.CTkFont(size=13, weight="bold"),
            text_color=("gray20", "gray85")
        ).pack(side="left")

        self.theme_switch = ctk.CTkOptionMenu(
            theme_row,
            values=["System", "Dark", "Light"],
            command=self._on_theme_switch,
            height=30,
            width=120,
            font=ctk.CTkFont(size=12)
        )
        self.theme_switch.set(config_mgr.get("theme_mode", "System"))
        self.theme_switch.pack(side="right")

        # ==========================================
        # 2. 右侧主工作区 (Main Workspace)
        # ==========================================
        self.main_work_area = ctk.CTkFrame(self, fg_color="transparent")
        self.main_work_area.grid(row=0, column=1, sticky="nsew", padx=12, pady=12)
        self.main_work_area.grid_rowconfigure(1, weight=1)
        self.main_work_area.grid_columnconfigure(0, weight=1)

        # 2.1 顶部现代化一体地址栏 (Omnibar)
        self.top_bar = ctk.CTkFrame(
            self.main_work_area,
            height=46,
            corner_radius=10,
            border_width=1,
            border_color=("gray85", "#2E3648"),
            fg_color=("white", "#1B1F2A")
        )
        self.top_bar.grid(row=0, column=0, sticky="ew", pady=(0, 8))

        ctk.CTkLabel(
            self.top_bar,
            text="📍 当前路径:",
            font=ctk.CTkFont(size=12, weight="bold"),
            text_color=("gray20", "gray85")
        ).pack(side="left", padx=(14, 6))

        self.path_entry = ctk.CTkEntry(
            self.top_bar,
            textvariable=self.current_path_var,
            font=ctk.CTkFont(size=12),
            height=30
        )
        self.path_entry.pack(side="left", fill="x", expand=True, padx=(0, 8))
        self.path_entry.bind("<Return>", lambda e: self._on_path_entry_submitted())

        self.browse_btn = ctk.CTkButton(
            self.top_bar,
            text="📂 浏览...",
            width=80,
            height=30,
            font=ctk.CTkFont(size=12, weight="bold"),
            fg_color=COLOR_PRIMARY,
            hover_color=COLOR_PRIMARY_HOVER,
            command=self._browse_directory
        )
        self.browse_btn.pack(side="left", padx=(0, 6))

        self.refresh_btn = ctk.CTkButton(
            self.top_bar,
            text="🔄 刷新",
            width=70,
            height=30,
            font=ctk.CTkFont(size=12),
            fg_color="transparent",
            border_width=1,
            border_color=("gray75", "#3A4459"),
            text_color=("gray20", "gray85"),
            hover_color=("gray90", "#252B3B"),
            command=self.refresh_all
        )
        self.refresh_btn.pack(side="left", padx=(0, 6))

        self.open_dir_btn = ctk.CTkButton(
            self.top_bar,
            text="↗ 打开",
            width=65,
            height=30,
            font=ctk.CTkFont(size=12),
            fg_color="transparent",
            border_width=1,
            border_color=("gray75", "#3A4459"),
            text_color=("gray20", "gray85"),
            hover_color=("gray90", "#252B3B"),
            command=self._open_in_explorer
        )
        self.open_dir_btn.pack(side="left", padx=(0, 6))

        self.toggle_tree_btn = ctk.CTkButton(
            self.top_bar,
            text="◀ 树图",
            width=65,
            height=30,
            font=ctk.CTkFont(size=12),
            fg_color="transparent",
            border_width=1,
            border_color=("gray75", "#3A4459"),
            text_color=("gray20", "gray85"),
            hover_color=("gray90", "#252B3B"),
            command=self._toggle_tree_visibility
        )
        self.toggle_tree_btn.pack(side="left", padx=(0, 10))

        # 2.2 中间工作区（左侧可折叠目录树 + 右侧 Tab 工作区）
        self.center_split = ctk.CTkFrame(self.main_work_area, fg_color="transparent")
        self.center_split.grid(row=1, column=0, sticky="nsew")
        self.center_split.grid_rowconfigure(0, weight=1)
        self.center_split.grid_columnconfigure(0, weight=0)
        self.center_split.grid_columnconfigure(1, weight=1)

        # 左侧可折叠目录树容器卡片
        self.tree_container = ctk.CTkFrame(
            self.center_split,
            width=240,
            corner_radius=10,
            border_width=1,
            border_color=("gray85", "#2E3648"),
            fg_color=("white", "#1B1F2A")
        )
        self.tree_container.grid(row=0, column=0, sticky="nsew", padx=(0, 8))
        self.tree_container.pack_propagate(False)

        tree_header = ctk.CTkFrame(self.tree_container, fg_color="transparent", height=32)
        tree_header.pack(fill="x", padx=10, pady=(8, 4))
        ctk.CTkLabel(
            tree_header,
            text="🌳 目录树",
            font=ctk.CTkFont(size=13, weight="bold"),
            text_color=("gray20", "gray85")
        ).pack(side="left")

        self.file_tree = LazyFileTree(
            self.tree_container,
            on_directory_selected=self._on_tree_dir_selected,
            on_directory_navigate=self._on_tree_dir_navigate
        )
        self.file_tree.pack(fill="both", expand=True, padx=6, pady=(0, 6))

        # 右侧 Tab 内容容器
        self.tab_container = ctk.CTkFrame(self.center_split, fg_color="transparent")
        self.tab_container.grid(row=0, column=1, sticky="nsew")

        # 实例化所有业务 Tab
        self.tab_instances = {
            "classify": ClassifyTab(self.tab_container, get_current_path=self.get_current_path, on_changed=self.refresh_all),
            "batch": BatchTab(self.tab_container, get_current_path=self.get_current_path, on_changed=self.refresh_all),
            "search": SearchTab(self.tab_container, get_current_path=self.get_current_path),
            "tools": ToolsTab(self.tab_container, get_current_path=self.get_current_path, on_changed=self.refresh_all),
            "history": HistoryTab(self.tab_container, on_changed=self.refresh_all)
        }

        # 2.3 底部状态栏卡片
        self.status_bar = ctk.CTkFrame(
            self.main_work_area,
            height=28,
            corner_radius=8,
            border_width=1,
            border_color=("gray85", "#2E3648"),
            fg_color=("white", "#1B1F2A")
        )
        self.status_bar.grid(row=2, column=0, sticky="ew", pady=(8, 0))

        self.status_label = ctk.CTkLabel(
            self.status_bar,
            text="● 系统就绪",
            font=ctk.CTkFont(size=11),
            text_color="#10B981",
            anchor="w"
        )
        self.status_label.pack(side="left", padx=12)

        ai_provider = config_mgr.get("ai.provider", "Moonshot")
        ai_model = config_mgr.get("ai.model", "moonshot-v1-8k")
        self.ai_indicator = ctk.CTkLabel(
            self.status_bar,
            text=f"🤖 AI 模型: {ai_provider} ({ai_model})",
            font=ctk.CTkFont(size=11, weight="bold"),
            text_color=COLOR_AI_TEXT
        )
        self.ai_indicator.pack(side="right", padx=12)

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

    def _toggle_tree_visibility(self):
        """切换左侧目录树的折叠/展开"""
        if self.tree_visible:
            self.tree_container.grid_remove()
            self.toggle_tree_btn.configure(text="▶ 树图")
            self.tree_visible = False
        else:
            self.tree_container.grid()
            self.toggle_tree_btn.configure(text="◀ 树图")
            self.tree_visible = True

    def refresh_all(self):
        path = self.get_current_path()
        if path and os.path.exists(path):
            self.file_tree.set_root_path(path)
        # 如果当前在历史记录页，则刷新历史
        if hasattr(self.tab_instances["history"], "refresh_history"):
            self.tab_instances["history"].refresh_history()

    def _show_tab(self, tab_key: str):
        for k, btn in self.nav_buttons.items():
            btn.set_active(k == tab_key)

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

        # 刷新所有表格与树图的 ttk 样式
        self.file_tree.update_theme(mode)
        for tab in self.tab_instances.values():
            if hasattr(tab, "result_table"):
                tab.result_table.update_theme(mode)

    def _open_settings_modal(self):
        def on_settings_saved():
            provider = config_mgr.get("ai.provider", "Moonshot")
            model = config_mgr.get("ai.model", "moonshot-v1-8k")
            self.ai_indicator.configure(text=f"🤖 AI 模型: {provider} ({model})")
            mode = config_mgr.get("theme_mode", "System")
            self._on_theme_switch(mode)
        SettingsModal(self, on_save_callback=on_settings_saved)
