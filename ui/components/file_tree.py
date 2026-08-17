import os
import tkinter as tk
from tkinter import ttk
import customtkinter as ctk
from typing import Optional, Callable
from utils.file_utils import reveal_in_explorer

class LazyFileTree(ctk.CTkFrame):
    """
    虚拟懒加载文件目录树（解决大目录递归加载全量卡死问题）
    """
    def __init__(
        self,
        master,
        on_directory_selected: Optional[Callable[[str], None]] = None,
        on_directory_navigate: Optional[Callable[[str], None]] = None,
        **kwargs
    ):
        super().__init__(master, **kwargs)
        self.on_directory_selected = on_directory_selected
        self.on_directory_navigate = on_directory_navigate
        self.current_root_path = ""
        self.node_path_map = {}

        self._build_ui()

    def _build_ui(self):
        tree_container = ttk.Frame(self)
        tree_container.pack(fill="both", expand=True, padx=2, pady=2)

        v_scroll = ttk.Scrollbar(tree_container, orient="vertical")
        h_scroll = ttk.Scrollbar(tree_container, orient="horizontal")

        self.tree = ttk.Treeview(
            tree_container,
            show="tree",
            style="Custom.Treeview",
            yscrollcommand=v_scroll.set,
            xscrollcommand=h_scroll.set
        )

        v_scroll.config(command=self.tree.yview)
        h_scroll.config(command=self.tree.xview)

        v_scroll.pack(side="right", fill="y")
        h_scroll.pack(side="bottom", fill="x")
        self.tree.pack(side="left", fill="both", expand=True)

        self.tree.bind("<<TreeviewOpen>>", self._on_node_open)
        self.tree.bind("<<TreeviewSelect>>", self._on_node_select)
        self.tree.bind("<Double-1>", self._on_double_click)

    def set_root_path(self, root_path: str):
        """设置根路径并初始化第一层节点"""
        self.tree.delete(*self.tree.get_children())
        self.node_path_map.clear()
        self.current_root_path = root_path

        if not os.path.exists(root_path) or not os.path.isdir(root_path):
            return

        # 创建根节点
        root_name = os.path.basename(root_path) or root_path
        root_node = self.tree.insert("", "end", text=f"📁 {root_name}", open=True)
        self.node_path_map[root_node] = root_path

        self._populate_children(root_node, root_path)

    def _populate_children(self, parent_node: str, folder_path: str):
        """懒加载填充子节点"""
        # 清除现有子节点（包括虚拟 dummy 节点）
        for child in self.tree.get_children(parent_node):
            self.tree.delete(child)

        try:
            items = os.listdir(folder_path)
            items.sort(key=lambda x: (not os.path.isdir(os.path.join(folder_path, x)), x.lower()))
        except Exception:
            return

        for item in items:
            full_path = os.path.join(folder_path, item)
            is_dir = os.path.isdir(full_path)
            icon = "📁 " if is_dir else "📄 "
            
            node = self.tree.insert(parent_node, "end", text=f"{icon}{item}", open=False)
            self.node_path_map[node] = full_path

            if is_dir:
                # 插入一个哑节点以显示展开箭头 [+]
                self.tree.insert(node, "end", text="__dummy__")

    def _on_node_open(self, event):
        """当用户点击 [+] 展开目录时触发懒加载"""
        # 扫描当前已处于 open 状态且未加载真实子节点的项
        def check_node(item_id):
            children = self.tree.get_children(item_id)
            if children and len(children) == 1 and self.tree.item(children[0], "text") == "__dummy__":
                path = self.node_path_map.get(item_id)
                if path and os.path.isdir(path):
                    self._populate_children(item_id, path)
            for child in self.tree.get_children(item_id):
                if self.tree.item(child, "open"):
                    check_node(child)

        for root_item in self.tree.get_children(""):
            check_node(root_item)

    def _on_node_select(self, event):
        sel = self.tree.selection()
        if not sel:
            return
        node = sel[0]
        if node not in self.node_path_map:
            return
        path = self.node_path_map[node]
        if self.on_directory_selected and os.path.isdir(path):
            self.on_directory_selected(path)

    def _on_double_click(self, event):
        sel = self.tree.selection()
        if not sel:
            return
        node = sel[0]
        if node not in self.node_path_map:
            return
        path = self.node_path_map[node]
        if os.path.isdir(path):
            if self.on_directory_navigate:
                self.on_directory_navigate(path)
            elif self.on_directory_selected:
                self.on_directory_selected(path)
        else:
            reveal_in_explorer(path)

    def refresh(self):
        if self.current_root_path:
            self.set_root_path(self.current_root_path)
