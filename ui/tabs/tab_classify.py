import os
from tkinter import messagebox
import customtkinter as ctk
from typing import Callable, Optional
from core.classifier import Classifier
from utils.task_runner import TaskRunner
from ui.components.result_table import ResultTable
from ui.components.progress_panel import ProgressPanel
from ui.theme import (
    COLOR_PRIMARY, COLOR_PRIMARY_HOVER,
    COLOR_ACTION_ALT, COLOR_ACTION_ALT_HOVER,
    COLOR_AI, COLOR_AI_HOVER
)

class ClassifyTab(ctk.CTkFrame):
    """智能分类标签页 (Modern Slate Modular Card)"""

    def __init__(self, master, get_current_path: Callable[[], str], on_changed: Optional[Callable[[], None]] = None, **kwargs):
        super().__init__(master, fg_color="transparent", **kwargs)
        self.get_current_path = get_current_path
        self.on_changed = on_changed
        self.task_runner = TaskRunner(self)

        self._build_ui()

    def _build_ui(self):
        # 1. 顶部控制卡片
        control_card = ctk.CTkFrame(
            self,
            corner_radius=10,
            border_width=1,
            border_color=("gray85", "#2E3648"),
            fg_color=("white", "#1B1F2A")
        )
        control_card.pack(fill="x", padx=10, pady=(6, 8))

        mode_row = ctk.CTkFrame(control_card, fg_color="transparent")
        mode_row.pack(fill="x", padx=16, pady=12)

        ctk.CTkLabel(
            mode_row,
            text="📁 整理规则:",
            font=ctk.CTkFont(size=13, weight="bold")
        ).pack(side="left", padx=(0, 10))

        self.mode_combo = ctk.CTkComboBox(
            mode_row,
            values=["按文件类型", "按文件大小", "按修改日期", "AI 智能分类"],
            width=160,
            font=ctk.CTkFont(size=12)
        )
        self.mode_combo.pack(side="left", padx=(0, 20))
        self.mode_combo.set("按文件类型")

        self.preview_btn = ctk.CTkButton(
            mode_row,
            text="👁 预览分类计划",
            width=130,
            height=32,
            font=ctk.CTkFont(size=12, weight="bold"),
            fg_color=COLOR_ACTION_ALT,
            hover_color=COLOR_ACTION_ALT_HOVER,
            text_color="white",
            command=self._on_preview_clicked
        )
        self.preview_btn.pack(side="left", padx=(0, 12))

        self.execute_btn = ctk.CTkButton(
            mode_row,
            text="🚀 开始执行分类",
            width=130,
            height=32,
            font=ctk.CTkFont(size=12, weight="bold"),
            fg_color=COLOR_PRIMARY,
            hover_color=COLOR_PRIMARY_HOVER,
            text_color="white",
            command=self._on_execute_clicked
        )
        self.execute_btn.pack(side="left")

        # 2. 中间：分类结果表格容器
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
            text="📊 拟移动文件清单与目标规划 (双击行可直接在资源管理器定位)",
            font=ctk.CTkFont(size=13, weight="bold"),
            text_color=("gray20", "gray85")
        ).pack(side="left")

        self.result_table = ResultTable(
            table_container,
            columns=[
                ("filename", "文件名", 240),
                ("target_category", "目标分类文件夹", 150),
                ("size", "文件大小", 100),
                ("status", "状态", 100),
                ("current_path", "完整源路径", 350)
            ]
        )
        self.result_table.pack(fill="both", expand=True, padx=8, pady=(0, 8))

        # 3. 底部：智能折叠进度与终端面板
        self.progress_panel = ProgressPanel(self, on_cancel=self._on_cancel_clicked)
        self.progress_panel.pack(fill="x", padx=10, pady=(0, 8))

    def _set_buttons_state(self, is_running: bool):
        state = "disabled" if is_running else "normal"
        self.preview_btn.configure(state=state)
        self.execute_btn.configure(state=state)
        self.mode_combo.configure(state=state)

    def _on_cancel_clicked(self):
        self.task_runner.cancel_current_task()

    def _confirm_ai_privacy(self, parent) -> bool:
        return messagebox.askyesno(
            "AI 隐私提示",
            "AI 智能分类会读取每个文件的文件名和最多约 2000 个字符的文本片段，\n"
            "并发送到当前配置的大模型服务商进行分析。\n\n"
            "请不要对包含密码、个人信息或公司机密的目录使用此功能。\n\n"
            "仍要继续吗？",
            parent=parent
        )

    def _on_preview_clicked(self):
        top_win = self.winfo_toplevel()
        path = self.get_current_path()
        if not path or not os.path.exists(path):
            messagebox.showwarning("提示", "请先在顶部选择有效的文件夹路径。", parent=top_win)
            return

        mode = self.mode_combo.get()
        if mode == "AI 智能分类" and not self._confirm_ai_privacy(top_win):
            return
        self._set_buttons_state(True)
        self.result_table.clear()
        self.progress_panel.start_progress(f"正在分析并生成【{mode}】预览...")

        def worker(token, progress_cb, log_cb):
            return Classifier.preview_classification(path, mode, token, progress_cb, log_cb)

        def on_success(results):
            self._set_buttons_state(False)
            self.progress_panel.finish_progress(f"预览生成完毕，共 {len(results)} 个文件。")
            rows = []
            for item in results:
                values = [
                    item["filename"],
                    item["target_category"],
                    item["size"],
                    item["status"],
                    item["current_path"]
                ]
                rows.append((values, item))
            self.result_table.set_rows(rows)

        def on_error(exc):
            self._set_buttons_state(False)
            self.progress_panel.finish_progress("预览生成出错")
            self.progress_panel.append_log(f"✖ 错误: {str(exc)}")
            messagebox.showerror("错误", f"预览过程出错: {str(exc)}", parent=top_win)

        def on_cancelled():
            self._set_buttons_state(False)
            self.progress_panel.finish_progress("已取消预览")

        self.task_runner.run_task(
            worker,
            on_progress=self.progress_panel.update_progress,
            on_log=self.progress_panel.append_log,
            on_success=on_success,
            on_error=on_error,
            on_cancelled=on_cancelled
        )

    def _on_execute_clicked(self):
        top_win = self.winfo_toplevel()
        path = self.get_current_path()
        if not path or not os.path.exists(path):
            messagebox.showwarning("提示", "请先在顶部选择有效的文件夹路径。", parent=top_win)
            return

        mode = self.mode_combo.get()
        if mode == "AI 智能分类" and not self._confirm_ai_privacy(top_win):
            return
        if not messagebox.askyesno("确认分类", f"即将对路径下的所有文件按【{mode}】进行分类整理并移动至子文件夹。\n\n是否继续？（可在历史记录中一键撤销）", parent=top_win):
            return

        self._set_buttons_state(True)
        self.progress_panel.start_progress(f"正在执行【{mode}】...")

        def worker(token, progress_cb, log_cb):
            return Classifier.execute_classification(path, mode, token, progress_cb, log_cb)

        def on_success(result):
            success_count, fail_count, errors = result
            self._set_buttons_state(False)
            self.progress_panel.finish_progress(f"分类完成！成功 {success_count} 项，失败 {fail_count} 项。")
            
            if self.on_changed:
                self.on_changed()
            
            msg = f"分类执行完成！\n成功移动: {success_count} 个文件\n失败: {fail_count} 个文件"
            if success_count > 0:
                msg += "\n\n💡 提示：如需复原，可前往【📜 历史撤销】标签页一键恢复！"
            messagebox.showinfo("完成", msg, parent=top_win)

        def on_error(exc):
            self._set_buttons_state(False)
            self.progress_panel.finish_progress("分类过程发生异常")
            self.progress_panel.append_log(f"✖ 错误: {str(exc)}")
            messagebox.showerror("错误", f"分类过程异常: {str(exc)}", parent=top_win)

        def on_cancelled():
            self._set_buttons_state(False)
            self.progress_panel.finish_progress("分类任务已中止")
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
