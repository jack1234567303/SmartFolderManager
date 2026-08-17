import os
from tkinter import messagebox
import customtkinter as ctk
from typing import Callable, Optional
from core.search_engine import SearchEngine
from utils.task_runner import TaskRunner
from ui.components.result_table import ResultTable
from ui.components.progress_panel import ProgressPanel

class SearchTab(ctk.CTkFrame):
    """多维度与 AI 智能搜索标签页"""

    def __init__(self, master, get_current_path: Callable[[], str], **kwargs):
        super().__init__(master, fg_color="transparent", **kwargs)
        self.get_current_path = get_current_path
        self.task_runner = TaskRunner(self)

        self._build_ui()

    def _build_ui(self):
        # 1. 顶部搜索条件卡片
        search_card = ctk.CTkFrame(self)
        search_card.pack(fill="x", padx=10, pady=(10, 8))

        row1 = ctk.CTkFrame(search_card, fg_color="transparent")
        row1.pack(fill="x", padx=15, pady=(10, 5))

        ctk.CTkLabel(row1, text="🔍 搜索模式:").pack(side="left", padx=(0, 5))
        self.mode_combo = ctk.CTkComboBox(
            row1,
            values=["规则搜索", "🤖 AI 语义搜索"],
            width=150,
            command=self._on_mode_change
        )
        self.mode_combo.pack(side="left", padx=(0, 15))
        self.mode_combo.set("规则搜索")

        ctk.CTkLabel(row1, text="目标类型:").pack(side="left", padx=(0, 5))
        self.type_combo = ctk.CTkComboBox(
            row1,
            values=["全部", "仅文件", "仅文件夹"],
            width=120
        )
        self.type_combo.pack(side="left", padx=(0, 15))
        self.type_combo.set("全部")

        ctk.CTkLabel(row1, text="拓展名过滤:").pack(side="left", padx=(0, 5))
        self.ext_entry = ctk.CTkEntry(row1, width=130, placeholder_text="如: .png, .pdf")
        self.ext_entry.pack(side="left")

        # 搜索输入行
        row2 = ctk.CTkFrame(search_card, fg_color="transparent")
        row2.pack(fill="x", padx=15, pady=(5, 10))

        self.search_entry = ctk.CTkEntry(
            row2,
            placeholder_text="输入搜索关键字，或输入 AI 语义描述（如：查找包含用户登录逻辑的代码）...",
            height=34
        )
        self.search_entry.pack(side="left", fill="x", expand=True, padx=(0, 15))
        self.search_entry.bind("<Return>", lambda e: self._on_search_clicked())

        self.search_btn = ctk.CTkButton(
            row2,
            text="🚀 开始搜索",
            width=120,
            height=34,
            fg_color="#1f6aa5",
            hover_color="#144870",
            command=self._on_search_clicked
        )
        self.search_btn.pack(side="right")

        # 2. 中间：搜索结果表格
        self.result_table = ResultTable(
            self,
            columns=[
                ("name", "名称", 200),
                ("type", "类型", 90),
                ("size", "大小", 90),
                ("mtime", "修改时间", 150),
                ("path", "完整路径", 350)
            ],
            height=260
        )
        self.result_table.pack(fill="both", expand=True, padx=10, pady=(0, 8))

        # 3. 底部进度面板
        self.progress_panel = ProgressPanel(self, on_cancel=self._on_cancel_clicked)
        self.progress_panel.pack(fill="x", padx=10, pady=(0, 10))

    def _on_mode_change(self, mode: str):
        if mode == "🤖 AI 语义搜索":
            self.type_combo.configure(state="disabled")
            self.ext_entry.configure(state="disabled")
        else:
            self.type_combo.configure(state="normal")
            self.ext_entry.configure(state="normal")

    def _on_cancel_clicked(self):
        self.task_runner.cancel_current_task()

    def _on_search_clicked(self):
        top_win = self.winfo_toplevel()
        path = self.get_current_path()
        if not path or not os.path.exists(path):
            messagebox.showwarning("提示", "请先在顶部选择有效的根目录路径。", parent=top_win)
            return

        kw = self.search_entry.get().strip()
        mode = self.mode_combo.get()
        target_type = self.type_combo.get()
        ext_str = self.ext_entry.get().strip()
        exts = [e.strip() for e in ext_str.replace("，", ",").split(",") if e.strip()] if ext_str else None

        if not kw and mode == "🤖 AI 语义搜索":
            messagebox.showwarning("提示", "请输入要搜索的自然语言意图描述。", parent=top_win)
            return

        self.search_btn.configure(state="disabled")
        self.result_table.clear()
        self.progress_panel.start_progress(f"正在以【{mode}】检索中...")

        def worker(token, progress_cb, log_cb):
            if mode == "🤖 AI 语义搜索":
                return SearchEngine.search_ai_semantic(path, kw, token, progress_cb, log_cb)
            else:
                return SearchEngine.search_local(
                    path,
                    keyword=kw,
                    target_type=target_type,
                    ext_filter=exts,
                    token=token,
                    progress_cb=progress_cb,
                    log_cb=log_cb
                )

        def on_success(results):
            self.search_btn.configure(state="normal")
            self.progress_panel.finish_progress(f"搜索完成，找到 {len(results)} 个匹配项。")
            rows = []
            for item in results:
                values = [item["name"], item["type"], item["size"], item["mtime"], item["path"]]
                rows.append((values, item))
            self.result_table.set_rows(rows)

        def on_error(exc):
            self.search_btn.configure(state="normal")
            self.progress_panel.finish_progress("搜索出错")
            messagebox.showerror("搜索失败", str(exc), parent=top_win)

        def on_cancelled():
            self.search_btn.configure(state="normal")
            self.progress_panel.finish_progress("搜索已取消")

        self.task_runner.run_task(
            worker,
            on_progress=self.progress_panel.update_progress,
            on_log=self.progress_panel.append_log,
            on_success=on_success,
            on_error=on_error,
            on_cancelled=on_cancelled
        )
