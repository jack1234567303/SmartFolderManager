import os
from tkinter import messagebox
import customtkinter as ctk
from typing import Callable, Optional
from core.classifier import Classifier
from utils.task_runner import TaskRunner
from ui.components.result_table import ResultTable
from ui.components.progress_panel import ProgressPanel

class ClassifyTab(ctk.CTkFrame):
    """智能分类标签页"""

    def __init__(self, master, get_current_path: Callable[[], str], on_changed: Optional[Callable[[], None]] = None, **kwargs):
        super().__init__(master, fg_color="transparent", **kwargs)
        self.get_current_path = get_current_path
        self.on_changed = on_changed
        self.task_runner = TaskRunner(self)

        self._build_ui()

    def _build_ui(self):
        # 1. 顶部控制栏
        control_card = ctk.CTkFrame(self)
        control_card.pack(fill="x", padx=10, pady=(10, 8))

        mode_row = ctk.CTkFrame(control_card, fg_color="transparent")
        mode_row.pack(fill="x", padx=15, pady=10)

        ctk.CTkLabel(mode_row, text="📁 分类规则方式:", font=ctk.CTkFont(size=14, weight="bold")).pack(side="left", padx=(0, 10))

        self.mode_combo = ctk.CTkComboBox(
            mode_row,
            values=["按文件类型", "按文件大小", "按修改日期", "AI 智能分类"],
            width=160,
            font=ctk.CTkFont(size=13)
        )
        self.mode_combo.pack(side="left", padx=(0, 20))
        self.mode_combo.set("按文件类型")

        self.preview_btn = ctk.CTkButton(
            mode_row,
            text="👁️ 预览分类计划",
            width=130,
            fg_color="#f0ad4e",
            hover_color="#ec971f",
            command=self._on_preview_clicked
        )
        self.preview_btn.pack(side="left", padx=(0, 15))

        self.execute_btn = ctk.CTkButton(
            mode_row,
            text="🚀 开始执行分类",
            width=130,
            fg_color="#1f6aa5",
            hover_color="#144870",
            command=self._on_execute_clicked
        )
        self.execute_btn.pack(side="left")

        # 2. 中间：分类结果表格
        table_label_row = ctk.CTkFrame(self, fg_color="transparent")
        table_label_row.pack(fill="x", padx=12, pady=(0, 4))
        ctk.CTkLabel(table_label_row, text="📊 分类计划与文件清单（双击可在资源管理器定位）", font=ctk.CTkFont(size=12, weight="bold")).pack(side="left")

        self.result_table = ResultTable(
            self,
            columns=[
                ("filename", "文件名", 220),
                ("target_category", "目标分类文件夹", 140),
                ("size", "文件大小", 100),
                ("status", "状态", 100),
                ("current_path", "完整路径", 350)
            ],
            height=260
        )
        self.result_table.pack(fill="both", expand=True, padx=10, pady=(0, 8))

        # 3. 底部：进度与日志面板
        self.progress_panel = ProgressPanel(self, on_cancel=self._on_cancel_clicked)
        self.progress_panel.pack(fill="x", padx=10, pady=(0, 10))

    def _set_buttons_state(self, is_running: bool):
        state = "disabled" if is_running else "normal"
        self.preview_btn.configure(state=state)
        self.execute_btn.configure(state=state)
        self.mode_combo.configure(state=state)

    def _on_cancel_clicked(self):
        self.task_runner.cancel_current_task()

    def _on_preview_clicked(self):
        top_win = self.winfo_toplevel()
        path = self.get_current_path()
        if not path or not os.path.exists(path):
            messagebox.showwarning("提示", "请先在顶部选择有效的文件夹路径。", parent=top_win)
            return

        mode = self.mode_combo.get()
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
