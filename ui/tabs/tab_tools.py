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
from ui.theme import (
    COLOR_PRIMARY, COLOR_PRIMARY_HOVER,
    COLOR_ACTION_ALT, COLOR_ACTION_ALT_HOVER,
    COLOR_CYAN, COLOR_CYAN_HOVER,
    COLOR_DANGER, COLOR_DANGER_HOVER,
    COLOR_SECONDARY, COLOR_SECONDARY_HOVER
)
from send2trash import send2trash

class ToolsTab(ctk.CTkFrame):
    """实用工具箱：重复文件哈希查重与空文件夹清理 (Modern Slate Modular Card)"""

    def __init__(self, master, get_current_path: Callable[[], str], on_changed: Optional[Callable[[], None]] = None, **kwargs):
        super().__init__(master, fg_color="transparent", **kwargs)
        self.get_current_path = get_current_path
        self.on_changed = on_changed
        self.task_runner = TaskRunner(self)
        self.duplicate_groups: List[Dict[str, Any]] = []
        self.empty_folders: List[Dict[str, Any]] = []

        self._build_ui()

    def _build_ui(self):
        # 1. 顶部操作工具栏卡片
        tools_card = ctk.CTkFrame(
            self,
            corner_radius=10,
            border_width=1,
            border_color=("gray85", "#2E3648"),
            fg_color=("white", "#1B1F2A")
        )
        tools_card.pack(fill="x", padx=10, pady=(6, 8))

        row1 = ctk.CTkFrame(tools_card, fg_color="transparent")
        row1.pack(fill="x", padx=16, pady=12)

        # 重复文件工具组
        ctk.CTkLabel(row1, text="🔍 重复文件查重:", font=ctk.CTkFont(size=12, weight="bold")).pack(side="left", padx=(0, 6))
        self.scan_dup_btn = ctk.CTkButton(
            row1,
            text="扫描重复文件",
            width=120,
            height=32,
            font=ctk.CTkFont(size=12, weight="bold"),
            fg_color=COLOR_PRIMARY,
            hover_color=COLOR_PRIMARY_HOVER,
            text_color="white",
            command=self._on_scan_duplicates
        )
        self.scan_dup_btn.pack(side="left", padx=(0, 10))

        self.clean_dup_btn = ctk.CTkButton(
            row1,
            text="🗑 清理副本(留一)",
            width=140,
            height=32,
            font=ctk.CTkFont(size=12, weight="bold"),
            fg_color=COLOR_DANGER,
            hover_color=COLOR_DANGER_HOVER,
            text_color="white",
            command=self._on_clean_duplicate_copies
        )
        self.clean_dup_btn.pack(side="left", padx=(0, 24))

        # 空文件夹工具组
        ctk.CTkLabel(row1, text="📁 空文件夹整理:", font=ctk.CTkFont(size=12, weight="bold")).pack(side="left", padx=(0, 6))
        self.scan_empty_btn = ctk.CTkButton(
            row1,
            text="扫描空文件夹",
            width=120,
            height=32,
            font=ctk.CTkFont(size=12, weight="bold"),
            fg_color=COLOR_CYAN,
            hover_color=COLOR_CYAN_HOVER,
            text_color="white",
            command=self._on_scan_empty_folders
        )
        self.scan_empty_btn.pack(side="left", padx=(0, 10))

        self.clean_empty_btn = ctk.CTkButton(
            row1,
            text="🧹 一键清理空目录",
            width=135,
            height=32,
            font=ctk.CTkFont(size=12, weight="bold"),
            fg_color=COLOR_ACTION_ALT,
            hover_color=COLOR_ACTION_ALT_HOVER,
            text_color="white",
            command=self._on_clean_empty_folders
        )
        self.clean_empty_btn.pack(side="left")

        # 2. 中间：结果表格
        table_container = ctk.CTkFrame(
            self,
            corner_radius=10,
            border_width=1,
            border_color=("gray85", "#2E3648"),
            fg_color=("white", "#1B1F2A")
        )
        table_container.pack(fill="both", expand=True, padx=10, pady=(0, 8))

        table_header = ctk.CTkFrame(table_container, fg_color="transparent", height=30)
        table_header.pack(fill="x", padx=12, pady=(8, 4))
        ctk.CTkLabel(
            table_header,
            text="📊 工具扫描结果清单 (双击定位文件)",
            font=ctk.CTkFont(size=13, weight="bold"),
            text_color=("gray20", "gray85")
        ).pack(side="left")

        self.result_table = ResultTable(
            table_container,
            columns=[
                ("item_name", "文件名 / 分组", 220),
                ("type_tag", "属性 / 状态", 130),
                ("size_info", "文件大小", 100),
                ("wasted_info", "可释放空间 / 说明", 160),
                ("path", "完整路径", 350)
            ]
        )
        self.result_table.pack(fill="both", expand=True, padx=8, pady=(0, 8))

        # 3. 底部进度与日志
        self.progress_panel = ProgressPanel(self, on_cancel=self._on_cancel_clicked)
        self.progress_panel.pack(fill="x", padx=10, pady=(0, 8))

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
            for f in g["files"][1:]:
                to_trash_files.append(f["path"])

        if not to_trash_files:
            messagebox.showinfo("提示", "没有可清理的重复副本。", parent=top_win)
            return

        if not messagebox.askyesno("清理确认", f"即将将 {len(to_trash_files)} 个多余重复副本移至系统回收站（保留每组第1个原文件）。\n\n是否继续？", parent=top_win):
            return

        self.clean_dup_btn.configure(state="disabled")
        self.progress_panel.start_progress("正在复核重复文件并移入回收站...")

        def worker(token, progress_cb, log_cb):
            success_count = 0
            fail_count = 0
            errors = []
            total = max(1, len(to_trash_files))
            processed = 0

            for group_index, group in enumerate(self.duplicate_groups, start=1):
                if token.is_cancelled:
                    break

                files = group.get("files", [])
                expected_md5 = group.get("md5", "")

                group_valid = True
                group_error = ""
                for file_info in files:
                    valid, reason = Deduplicator.verify_file_snapshot(
                        file_info,
                        expected_md5,
                        token=token
                    )
                    if not valid:
                        group_valid = False
                        group_error = f"{file_info.get('path', '')}: {reason}"
                        break

                if not group_valid:
                    duplicate_count = max(0, len(files) - 1)
                    fail_count += duplicate_count
                    errors.append(f"第 {group_index} 组已跳过：{group_error}")
                    if log_cb:
                        log_cb(f"⚠ 第 {group_index} 组重复结果已过期，跳过清理：{group_error}")
                    processed += duplicate_count
                    if progress_cb:
                        progress_cb(processed / total, f"已复核第 {group_index} 组")
                    continue

                for file_info in files[1:]:
                    if token.is_cancelled:
                        break
                    processed += 1
                    valid, reason = Deduplicator.verify_file_snapshot(
                        file_info,
                        expected_md5,
                        token=token
                    )
                    path = file_info.get("path", "")
                    if not valid:
                        fail_count += 1
                        error = f"{path}: {reason}"
                        errors.append(error)
                        if log_cb:
                            log_cb(f"⚠ 跳过过期副本: {error}")
                        continue
                    try:
                        send2trash(path)
                        success_count += 1
                    except Exception as exc:
                        fail_count += 1
                        error = f"{path}: {exc}"
                        errors.append(error)
                        if log_cb:
                            log_cb(f"✖ 回收失败: {error}")

                    if progress_cb:
                        progress_cb(processed / total, f"正在清理: {os.path.basename(path)}")

            return success_count, fail_count, errors

        def on_success(result):
            success_count, fail_count, errors = result
            self.clean_dup_btn.configure(state="normal")
            self.progress_panel.finish_progress(
                f"重复副本清理完成！成功 {success_count} 个，失败 {fail_count} 个。"
            )
            self.duplicate_groups.clear()
            self.result_table.clear()
            if self.on_changed and success_count:
                self.on_changed()

            msg = f"成功移入回收站: {success_count} 个\n失败或已跳过: {fail_count} 个"
            if errors:
                msg += "\n\n请重新扫描以获取最新结果。"
            if fail_count:
                messagebox.showwarning("清理完成（有项目跳过）", msg, parent=top_win)
            else:
                messagebox.showinfo("清理完成", msg, parent=top_win)

        def on_error(exc):
            self.clean_dup_btn.configure(state="normal")
            self.progress_panel.finish_progress("重复副本清理出错")
            messagebox.showerror("错误", str(exc), parent=top_win)

        def on_cancelled():
            self.clean_dup_btn.configure(state="normal")
            self.progress_panel.finish_progress("重复副本清理已取消")
            self.duplicate_groups.clear()
            self.result_table.clear()

        self.task_runner.run_task(
            worker,
            on_progress=self.progress_panel.update_progress,
            on_log=self.progress_panel.append_log,
            on_success=on_success,
            on_error=on_error,
            on_cancelled=on_cancelled
        )

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
