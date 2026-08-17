import os
from tkinter import messagebox
import customtkinter as ctk
from typing import Callable, Optional
from core.batch_ops import BatchOps
from utils.task_runner import TaskRunner
from ui.components.result_table import ResultTable
from ui.components.progress_panel import ProgressPanel

class BatchTab(ctk.CTkFrame):
    """批量操作标签页：批量创建、重命名、安全删除"""

    def __init__(self, master, get_current_path: Callable[[], str], on_changed: Optional[Callable[[], None]] = None, **kwargs):
        super().__init__(master, fg_color="transparent", **kwargs)
        self.get_current_path = get_current_path
        self.on_changed = on_changed
        self.task_runner = TaskRunner(self)

        self._build_ui()

    def _build_ui(self):
        # 1. 顶部输入卡片
        input_card = ctk.CTkFrame(self)
        input_card.pack(fill="x", padx=10, pady=(10, 8))

        # 前缀与后缀
        fix_row = ctk.CTkFrame(input_card, fg_color="transparent")
        fix_row.pack(fill="x", padx=15, pady=(8, 4))

        ctk.CTkLabel(fix_row, text="统一前缀:").pack(side="left")
        self.prefix_entry = ctk.CTkEntry(fix_row, width=120, placeholder_text="可选前缀")
        self.prefix_entry.pack(side="left", padx=(5, 20))

        ctk.CTkLabel(fix_row, text="统一后缀:").pack(side="left")
        self.suffix_entry = ctk.CTkEntry(fix_row, width=120, placeholder_text="可选后缀")
        self.suffix_entry.pack(side="left", padx=(5, 10))

        # 文本框与提示
        text_row = ctk.CTkFrame(input_card, fg_color="transparent")
        text_row.pack(fill="x", padx=15, pady=(4, 8))

        left_text_col = ctk.CTkFrame(text_row, fg_color="transparent")
        left_text_col.pack(side="left", fill="both", expand=True)

        ctk.CTkLabel(left_text_col, text="📝 名称列表（每行一个；重命名请用英文逗号分隔：原名,新名）：", font=ctk.CTkFont(size=12)).pack(anchor="w", pady=(0, 2))
        
        self.names_textbox = ctk.CTkTextbox(left_text_col, height=80, font=ctk.CTkFont(family="Consolas", size=12))
        self.names_textbox.pack(fill="x", expand=True)

        # 操作按钮组
        btn_col = ctk.CTkFrame(text_row, fg_color="transparent")
        btn_col.pack(side="right", padx=(15, 0), fill="y")

        self.btn_create = ctk.CTkButton(
            btn_col,
            text="📁 批量创建",
            width=120,
            fg_color="#1f6aa5",
            hover_color="#144870",
            command=self._on_create_clicked
        )
        self.btn_create.pack(pady=3)

        self.btn_rename_prev = ctk.CTkButton(
            btn_col,
            text="✏️ 批量重命名",
            width=120,
            fg_color="#f0ad4e",
            hover_color="#ec971f",
            command=self._on_rename_clicked
        )
        self.btn_rename_prev.pack(pady=3)

        self.btn_delete = ctk.CTkButton(
            btn_col,
            text="🗑️ 安全删除(回收站)",
            width=120,
            fg_color="#d9534f",
            hover_color="#c9302c",
            command=self._on_delete_clicked
        )
        self.btn_delete.pack(pady=3)

        # 2. 中间：操作预览与结果表格
        self.result_table = ResultTable(
            self,
            columns=[
                ("old_name", "原名称 / 操作项", 220),
                ("new_name", "新名称 / 目标", 220),
                ("status", "状态", 140),
                ("old_path", "路径", 350)
            ],
            height=200
        )
        self.result_table.pack(fill="both", expand=True, padx=10, pady=(0, 8))

        # 3. 底部进度面板
        self.progress_panel = ProgressPanel(self, on_cancel=self._on_cancel_clicked)
        self.progress_panel.pack(fill="x", padx=10, pady=(0, 10))

    def _get_input_lines(self):
        raw = self.names_textbox.get("1.0", "end").strip()
        if not raw:
            return []
        return [line.strip() for line in raw.splitlines() if line.strip()]

    def _on_cancel_clicked(self):
        self.task_runner.cancel_current_task()

    def _on_create_clicked(self):
        top_win = self.winfo_toplevel()
        path = self.get_current_path()
        if not path or not os.path.exists(path):
            messagebox.showwarning("提示", "请选择有效的根目录。", parent=top_win)
            return

        lines = self._get_input_lines()
        if not lines:
            messagebox.showwarning("提示", "请输入要创建的文件夹名称。", parent=top_win)
            return

        prefix = self.prefix_entry.get().strip()
        suffix = self.suffix_entry.get().strip()

        self.progress_panel.start_progress("正在批量创建文件夹...")
        self.result_table.clear()

        def worker(token, progress_cb, log_cb):
            return BatchOps.batch_create_folders(path, lines, prefix, suffix, token, progress_cb, log_cb)

        def on_success(result):
            s_count, f_count, errors = result
            self.progress_panel.finish_progress(f"创建完成！成功 {s_count} 项，失败 {f_count} 项。")
            if self.on_changed:
                self.on_changed()
            messagebox.showinfo("完成", f"批量创建完成！\n成功: {s_count}\n失败: {f_count}", parent=top_win)

        def on_error(exc):
            self.progress_panel.finish_progress("创建失败")
            messagebox.showerror("错误", str(exc), parent=top_win)

        def on_cancelled():
            self.progress_panel.finish_progress("操作已取消")
            if self.on_changed:
                self.on_changed()

        self.task_runner.run_task(
            worker,
            on_progress=self.progress_panel.update_progress,
            on_log=self.progress_panel.append_log,
            on_success=on_success,
            on_error=on_error,
            on_cancelled=on_cancelled
        )

    def _on_rename_clicked(self):
        top_win = self.winfo_toplevel()
        path = self.get_current_path()
        if not path or not os.path.exists(path):
            messagebox.showwarning("提示", "请选择有效的根目录。", parent=top_win)
            return

        lines = self._get_input_lines()
        if not lines:
            messagebox.showwarning("提示", "请输入重命名对应对，格式：原名,新名", parent=top_win)
            return

        name_pairs = []
        for line in lines:
            parts = line.split(",", 1)
            if len(parts) == 2:
                name_pairs.append((parts[0].strip(), parts[1].strip()))

        if not name_pairs:
            messagebox.showwarning("提示", "未找到有效的重命名对（请确保每行用英文逗号分隔：原名,新名）", parent=top_win)
            return

        prefix = self.prefix_entry.get().strip()
        suffix = self.suffix_entry.get().strip()

        # 预览
        preview_list = BatchOps.preview_batch_rename(path, name_pairs, prefix, suffix)
        rows = []
        for item in preview_list:
            values = [item["old_name"], item["new_name"], item["status"], item["old_path"]]
            rows.append((values, item))
        self.result_table.set_rows(rows)

        if not messagebox.askyesno("确认重命名", f"已生成 {len(preview_list)} 条重命名计划。\n是否立即执行重命名？\n（可在历史记录中一键撤销恢复）", parent=top_win):
            return

        self.progress_panel.start_progress("正在执行批量重命名...")

        def worker(token, progress_cb, log_cb):
            return BatchOps.execute_batch_rename(path, name_pairs, prefix, suffix, token, progress_cb, log_cb)

        def on_success(result):
            s_count, f_count, errors = result
            self.progress_panel.finish_progress(f"重命名完成！成功 {s_count} 项，失败 {f_count} 项。")
            if self.on_changed:
                self.on_changed()
            messagebox.showinfo("完成", f"批量重命名完成！\n成功: {s_count}\n失败: {f_count}", parent=top_win)

        def on_error(exc):
            self.progress_panel.finish_progress("重命名异常")
            messagebox.showerror("错误", str(exc), parent=top_win)

        def on_cancelled():
            self.progress_panel.finish_progress("重命名已中止")
            if self.on_changed:
                self.on_changed()

        self.task_runner.run_task(
            worker,
            on_progress=self.progress_panel.update_progress,
            on_log=self.progress_panel.append_log,
            on_success=on_success,
            on_error=on_error,
            on_cancelled=on_cancelled
        )

    def _on_delete_clicked(self):
        top_win = self.winfo_toplevel()
        path = self.get_current_path()
        if not path or not os.path.exists(path):
            messagebox.showwarning("提示", "请选择有效的根目录。", parent=top_win)
            return

        lines = self._get_input_lines()
        if not lines:
            messagebox.showwarning("提示", "请输入要删除的文件夹或文件名。", parent=top_win)
            return

        prefix = self.prefix_entry.get().strip()
        suffix = self.suffix_entry.get().strip()

        if not messagebox.askyesno("安全删除确认", f"确定要将这 {len(lines)} 项文件/文件夹移至系统回收站吗？\n（移至回收站后仍可随时还原）", parent=top_win):
            return

        self.progress_panel.start_progress("正在安全删除中...")

        def worker(token, progress_cb, log_cb):
            return BatchOps.batch_safe_delete(path, lines, prefix, suffix, token, progress_cb, log_cb)

        def on_success(result):
            s_count, f_count, errors = result
            self.progress_panel.finish_progress(f"删除完成！已移至回收站: {s_count} 项，失败: {f_count} 项。")
            if self.on_changed:
                self.on_changed()
            messagebox.showinfo("完成", f"安全删除完成！\n移至回收站: {s_count}\n失败: {f_count}", parent=top_win)

        def on_error(exc):
            self.progress_panel.finish_progress("删除出错")
            messagebox.showerror("错误", str(exc), parent=top_win)

        def on_cancelled():
            self.progress_panel.finish_progress("操作已取消")
            if self.on_changed:
                self.on_changed()

        self.task_runner.run_task(
            worker,
            on_progress=self.progress_panel.update_progress,
            on_log=self.progress_panel.append_log,
            on_success=on_success,
            on_error=on_error,
            on_cancelled=on_cancelled
        )
