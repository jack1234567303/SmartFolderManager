import os
from tkinter import messagebox
import customtkinter as ctk
from typing import Callable, Optional, List, Dict, Any
from core.deduplicator import Deduplicator
from core.cleaner import Cleaner
from utils.task_runner import TaskRunner
from utils.file_utils import format_size
from ui.components.result_table import ResultTable
from ui.components.progress_panel import ProgressPanel
from send2trash import send2trash

class ToolsTab(ctk.CTkFrame):
    """实用工具箱：重复文件哈希查重与空文件夹清理"""

    def __init__(self, master, get_current_path: Callable[[], str], on_changed: Optional[Callable[[], None]] = None, **kwargs):
        super().__init__(master, fg_color="transparent", **kwargs)
        self.get_current_path = get_current_path
        self.on_changed = on_changed
        self.task_runner = TaskRunner(self)
        self.duplicate_groups: List[Dict[str, Any]] = []
        self.empty_folders: List[Dict[str, Any]] = []

        self._build_ui()

    def _build_ui(self):
        # 1. 顶部操作工具栏
        tools_card = ctk.CTkFrame(self)
        tools_card.pack(fill="x", padx=10, pady=(10, 8))

        row1 = ctk.CTkFrame(tools_card, fg_color="transparent")
        row1.pack(fill="x", padx=15, pady=10)

        # 重复文件工具组
        ctk.CTkLabel(row1, text="🔍 重复文件查重:", font=ctk.CTkFont(weight="bold")).pack(side="left", padx=(0, 5))
        self.scan_dup_btn = ctk.CTkButton(
            row1,
            text="扫描重复文件",
            width=120,
            fg_color="#337ab7",
            hover_color="#286090",
            command=self._on_scan_duplicates
        )
        self.scan_dup_btn.pack(side="left", padx=(0, 10))

        self.clean_dup_btn = ctk.CTkButton(
            row1,
            text="🗑️ 清理多余副本(留一)",
            width=150,
            fg_color="#d9534f",
            hover_color="#c9302c",
            command=self._on_clean_duplicate_copies
        )
        self.clean_dup_btn.pack(side="left", padx=(0, 30))

        # 空文件夹工具组
        ctk.CTkLabel(row1, text="📁 空文件夹整理:", font=ctk.CTkFont(weight="bold")).pack(side="left", padx=(0, 5))
        self.scan_empty_btn = ctk.CTkButton(
            row1,
            text="扫描空文件夹",
            width=120,
            fg_color="#5bc0de",
            hover_color="#31b0d5",
            command=self._on_scan_empty_folders
        )
        self.scan_empty_btn.pack(side="left", padx=(0, 10))

        self.clean_empty_btn = ctk.CTkButton(
            row1,
            text="🧹 一键清理空目录",
            width=130,
            fg_color="#f0ad4e",
            hover_color="#ec971f",
            command=self._on_clean_empty_folders
        )
        self.clean_empty_btn.pack(side="left")

        # 2. 中间：结果表格
        self.result_table = ResultTable(
            self,
            columns=[
                ("item_name", "文件名 / 分组", 200),
                ("type_tag", "属性 / 状态", 120),
                ("size_info", "文件大小", 100),
                ("wasted_info", "可释放空间 / 说明", 150),
                ("path", "完整路径", 350)
            ],
            height=260
        )
        self.result_table.pack(fill="both", expand=True, padx=10, pady=(0, 8))

        # 3. 底部进度与日志
        self.progress_panel = ProgressPanel(self, on_cancel=self._on_cancel_clicked)
        self.progress_panel.pack(fill="x", padx=10, pady=(0, 10))

    def _on_cancel_clicked(self):
        self.task_runner.cancel_current_task()

    def _on_scan_duplicates(self):
        top_win = self.winfo_toplevel()
        path = self.get_current_path()
        if not path or not os.path.exists(path):
            messagebox.showwarning("提示", "请选择有效的根目录。", parent=top_win)
            return

        self.scan_dup_btn.configure(state="disabled")
        self.result_table.clear()
        self.progress_panel.start_progress("正在扫描并比对重复文件（大小筛查 + MD5校验）...")

        def worker(token, progress_cb, log_cb):
            return Deduplicator.find_duplicate_files(path, token, progress_cb, log_cb)

        def on_success(groups):
            self.scan_dup_btn.configure(state="normal")
            self.duplicate_groups = groups
            total_wasted = sum(g["wasted_bytes"] for g in groups)
            self.progress_panel.finish_progress(f"查重完成！发现 {len(groups)} 组重复，可节省 {format_size(total_wasted)}。")
            
            rows = []
            for g_idx, group in enumerate(groups):
                for f_idx, f in enumerate(group["files"]):
                    role = "【保留原件】" if f_idx == 0 else "【重复副本】"
                    values = [
                        f["name"],
                        role,
                        f["size"],
                        f"组 {g_idx + 1} (共{group['count']}份)" if f_idx == 0 else f"冗余 {group['size_str']}",
                        f["path"]
                    ]
                    rows.append((values, f))
            self.result_table.set_rows(rows)

        def on_error(exc):
            self.scan_dup_btn.configure(state="normal")
            self.progress_panel.finish_progress("查重过程出错")
            messagebox.showerror("错误", str(exc), parent=top_win)

        def on_cancelled():
            self.scan_dup_btn.configure(state="normal")
            self.progress_panel.finish_progress("查重已取消")

        self.task_runner.run_task(
            worker,
            on_progress=self.progress_panel.update_progress,
            on_log=self.progress_panel.append_log,
            on_success=on_success,
            on_error=on_error,
            on_cancelled=on_cancelled
        )

    def _on_clean_duplicate_copies(self):
        top_win = self.winfo_toplevel()
        if not self.duplicate_groups:
            messagebox.showinfo("提示", "暂无重复文件结果，请先点击【扫描重复文件】。", parent=top_win)
            return

        to_trash_files = []
        for g in self.duplicate_groups:
            # 保留第一个，其余移至回收站
            for f in g["files"][1:]:
                to_trash_files.append(f["path"])

        if not to_trash_files:
            messagebox.showinfo("提示", "没有可清理的重复副本。", parent=top_win)
            return

        if not messagebox.askyesno("清理确认", f"即将将 {len(to_trash_files)} 个多余重复副本移至系统回收站（保留每组第1个原文件）。\n\n是否继续？", parent=top_win):
            return

        success_count = 0
        fail_count = 0
        for p in to_trash_files:
            try:
                send2trash(p)
                success_count += 1
            except Exception:
                fail_count += 1

        self.progress_panel.append_log(f"重复副本清理完毕：成功移入回收站 {success_count} 个，失败 {fail_count} 个。")
        messagebox.showinfo("清理完成", f"已将 {success_count} 个重复副本移至回收站！", parent=top_win)
        self.duplicate_groups.clear()
        self.result_table.clear()
        if self.on_changed:
            self.on_changed()

    def _on_scan_empty_folders(self):
        top_win = self.winfo_toplevel()
        path = self.get_current_path()
        if not path or not os.path.exists(path):
            messagebox.showwarning("提示", "请选择有效的根目录。", parent=top_win)
            return

        self.scan_empty_btn.configure(state="disabled")
        self.result_table.clear()
        self.progress_panel.start_progress("正在扫描空文件夹...")

        def worker(token, progress_cb, log_cb):
            return Cleaner.find_empty_folders(path, token, progress_cb, log_cb)

        def on_success(empty_list):
            self.scan_empty_btn.configure(state="normal")
            self.empty_folders = empty_list
            self.progress_panel.finish_progress(f"扫描完毕，共发现 {len(empty_list)} 个空文件夹。")
            rows = []
            for item in empty_list:
                values = [
                    item["name"],
                    "空目录",
                    "0 B",
                    "无文件内容",
                    item["path"]
                ]
                rows.append((values, item))
            self.result_table.set_rows(rows)

        def on_error(exc):
            self.scan_empty_btn.configure(state="normal")
            self.progress_panel.finish_progress("扫描出错")
            messagebox.showerror("错误", str(exc), parent=top_win)

        def on_cancelled():
            self.scan_empty_btn.configure(state="normal")
            self.progress_panel.finish_progress("已取消扫描")

        self.task_runner.run_task(
            worker,
            on_progress=self.progress_panel.update_progress,
            on_log=self.progress_panel.append_log,
            on_success=on_success,
            on_error=on_error,
            on_cancelled=on_cancelled
        )

    def _on_clean_empty_folders(self):
        top_win = self.winfo_toplevel()
        if not self.empty_folders:
            messagebox.showinfo("提示", "暂无空文件夹列表，请先点击【扫描空文件夹】。", parent=top_win)
            return

        paths = [item["path"] for item in self.empty_folders]
        if not messagebox.askyesno("清理确认", f"确定要清理这 {len(paths)} 个空文件夹吗？（默认移至回收站）", parent=top_win):
            return

        self.progress_panel.start_progress("正在清理空文件夹...")

        def worker(token, progress_cb, log_cb):
            return Cleaner.clean_empty_folders(paths, use_trash=True, token=token, progress_cb=progress_cb, log_cb=log_cb)

        def on_success(result):
            s_count, f_count, errors = result
            self.progress_panel.finish_progress(f"清理完成！成功清理 {s_count} 个空文件夹。")
            self.empty_folders.clear()
            self.result_table.clear()
            if self.on_changed:
                self.on_changed()
            messagebox.showinfo("完成", f"已成功清理 {s_count} 个空文件夹！", parent=top_win)

        def on_error(exc):
            self.progress_panel.finish_progress("清理出错")
            messagebox.showerror("错误", str(exc), parent=top_win)

        def on_cancelled():
            self.progress_panel.finish_progress("清理已取消")
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
