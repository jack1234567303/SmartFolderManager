import tkinter as tk
from tkinter import ttk
import customtkinter as ctk
from typing import List, Dict, Tuple, Any, Optional, Callable
from utils.file_utils import reveal_in_explorer, open_file_with_default_app

class ResultTable(ctk.CTkFrame):
    """
    通用数据与结果表格组件（基于 Treeview 深度定制样式，支持双击定位与右键菜单）
    """
    def __init__(
        self,
        master,
        columns: List[Tuple[str, str, int]],  # [(col_id, col_title, width), ...]
        on_double_click: Optional[Callable[[Dict[str, Any]], None]] = None,
        **kwargs
    ):
        super().__init__(master, **kwargs)
        self.columns_config = columns
        self.on_double_click_custom = on_double_click
        self.item_data_map: Dict[str, Dict[str, Any]] = {}

        self._setup_style()
        self._build_ui()

    def _setup_style(self):
        self.style = ttk.Style()
        # 优化树形表格显示字体与行高
        self.style.theme_use("clam")
        self.style.configure(
            "Custom.Treeview",
            background="#2b2b2b",
            foreground="#ffffff",
            fieldbackground="#2b2b2b",
            rowheight=28,
            font=("微软雅黑", 10)
        )
        self.style.configure(
            "Custom.Treeview.Heading",
            background="#3a3a3a",
            foreground="#ffffff",
            font=("微软雅黑", 10, "bold"),
            padding=4
        )
        self.style.map(
            "Custom.Treeview",
            background=[("selected", "#1f6aa5")],
            foreground=[("selected", "#ffffff")]
        )

    def _build_ui(self):
        col_ids = [c[0] for c in self.columns_config]
        
        # 容器
        table_container = ttk.Frame(self)
        table_container.pack(fill="both", expand=True, padx=2, pady=2)

        # 滚动条
        v_scroll = ttk.Scrollbar(table_container, orient="vertical")
        h_scroll = ttk.Scrollbar(table_container, orient="horizontal")

        self.tree = ttk.Treeview(
            table_container,
            columns=col_ids,
            show="headings",
            style="Custom.Treeview",
            yscrollcommand=v_scroll.set,
            xscrollcommand=h_scroll.set
        )

        v_scroll.config(command=self.tree.yview)
        h_scroll.config(command=self.tree.xview)

        v_scroll.pack(side="right", fill="y")
        h_scroll.pack(side="bottom", fill="x")
        self.tree.pack(side="left", fill="both", expand=True)

        for col_id, col_title, width in self.columns_config:
            self.tree.heading(col_id, text=col_title)
            self.tree.column(col_id, width=width, minwidth=60, anchor="w")

        # 绑定事件
        self.tree.bind("<Double-1>", self._on_double_click)
        self.tree.bind("<Button-3>", self._on_right_click)

        # 快捷右键菜单
        self.context_menu = tk.Menu(self, tearoff=0)
        self.context_menu.add_command(label="📂 在资源管理器中定位", command=self._action_reveal)
        self.context_menu.add_command(label="▶ 打开此文件", command=self._action_open)
        self.context_menu.add_separator()
        self.context_menu.add_command(label="📋 复制完整路径", command=self._action_copy_path)

    def update_theme(self, mode: str):
        """根据深色/浅色模式切换 Treeview 调色"""
        if mode.lower() == "light":
            self.style.configure(
                "Custom.Treeview",
                background="#ffffff",
                foreground="#000000",
                fieldbackground="#ffffff"
            )
            self.style.configure(
                "Custom.Treeview.Heading",
                background="#e0e0e0",
                foreground="#000000"
            )
        else:
            self.style.configure(
                "Custom.Treeview",
                background="#2b2b2b",
                foreground="#ffffff",
                fieldbackground="#2b2b2b"
            )
            self.style.configure(
                "Custom.Treeview.Heading",
                background="#3a3a3a",
                foreground="#ffffff"
            )

    def clear(self):
        self.tree.delete(*self.tree.get_children())
        self.item_data_map.clear()

    def add_row(self, values: List[Any], raw_data: Optional[Dict[str, Any]] = None) -> str:
        item_id = self.tree.insert("", "end", values=values)
        if raw_data:
            self.item_data_map[item_id] = raw_data
        return item_id

    def set_rows(self, rows: List[Tuple[List[Any], Optional[Dict[str, Any]]]]):
        self.clear()
        for values, raw_data in rows:
            self.add_row(values, raw_data)

    def get_selected_data(self) -> Optional[Dict[str, Any]]:
        sel = self.tree.selection()
        if not sel:
            return None
        return self.item_data_map.get(sel[0])

    def _on_double_click(self, event):
        data = self.get_selected_data()
        if not data:
            return
        if self.on_double_click_custom:
            self.on_double_click_custom(data)
        else:
            # 默认：在资源管理器中定位
            path = data.get("path") or data.get("current_path") or data.get("old_path")
            if path:
                reveal_in_explorer(path)

    def _on_right_click(self, event):
        row_id = self.tree.identify_row(event.y)
        if row_id:
            self.tree.selection_set(row_id)
            self.context_menu.tk_popup(event.x_root, event.y_root)

    def _action_reveal(self):
        data = self.get_selected_data()
        if data:
            path = data.get("path") or data.get("current_path") or data.get("old_path")
            if path:
                reveal_in_explorer(path)

    def _action_open(self):
        data = self.get_selected_data()
        if data:
            path = data.get("path") or data.get("current_path") or data.get("old_path")
            if path:
                open_file_with_default_app(path)

    def _action_copy_path(self):
        data = self.get_selected_data()
        if data:
            path = data.get("path") or data.get("current_path") or data.get("old_path")
            if path:
                self.clipboard_clear()
                self.clipboard_append(path)
