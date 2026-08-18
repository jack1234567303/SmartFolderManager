from tkinter import messagebox
import customtkinter as ctk
from typing import Callable, Optional
from core.undo_manager import undo_mgr
from ui.components.result_table import ResultTable

class HistoryTab(ctk.CTkFrame):
    """历史记录与一键撤销标签页"""

    def __init__(self, master, on_changed: Optional[Callable[[], None]] = None, **kwargs):
        super().__init__(master, fg_color="transparent", **kwargs)
        self.on_changed = on_changed

        self._build_ui()
        self.refresh_history()

    def _build_ui(self):
        # 1. 顶部操作栏
        top_bar = ctk.CTkFrame(self)
        top_bar.pack(fill="x", padx=10, pady=(10, 8))

        bar_inner = ctk.CTkFrame(top_bar, fg_color="transparent")
        bar_inner.pack(fill="x", padx=15, pady=10)

        ctk.CTkLabel(bar_inner, text="📜 操作事务历史（支持对移动/重命名等操作一键还原）：", font=ctk.CTkFont(size=13, weight="bold")).pack(side="left")

        self.undo_btn = ctk.CTkButton(
            bar_inner,
            text="↩ 一键撤销选中操作",
            width=150,
            fg_color="#d9534f",
            hover_color="#c9302c",
            command=self._on_undo_clicked
        )
        self.undo_btn.pack(side="right", padx=(10, 0))

        self.refresh_btn = ctk.CTkButton(
            bar_inner,
            text="🔄 刷新",
            width=80,
            fg_color="#337ab7",
            hover_color="#286090",
            command=self.refresh_history
        )
        self.refresh_btn.pack(side="right", padx=(10, 0))

        self.clear_btn = ctk.CTkButton(
            bar_inner,
            text="清空历史",
            width=80,
            fg_color="gray",
            hover_color="#555",
            command=self._on_clear_history
        )
        self.clear_btn.pack(side="right")

        # 2. 中间：历史表格
        self.result_table = ResultTable(
            self,
            columns=[
                ("tx_id", "事务 ID", 140),
                ("title", "操作类型", 160),
                ("count", "文件数量", 90),
                ("status", "状态", 100),
                ("time", "操作发生时间", 160),
                ("description", "备注描述", 260)
            ],
            height=400
        )
        self.result_table.pack(fill="both", expand=True, padx=10, pady=(0, 10))

    def refresh_history(self):
        records = undo_mgr.get_history()
        rows = []
        for r in records:
            status_text = "已撤销" if r["is_undone"] else "有效 (可撤销)"
            values = [
                r["tx_id"],
                r["title"],
                f"{r['count']} 个",
                status_text,
                r["time"],
                r["description"]
            ]
            rows.append((values, r))
        self.result_table.set_rows(rows)

    def _on_undo_clicked(self):
        top_win = self.winfo_toplevel()
        selected_data = self.result_table.get_selected_data()
        if not selected_data:
            messagebox.showwarning("提示", "请先在列表中选中一条要撤销的操作记录。", parent=top_win)
            return

        tx_id = selected_data["tx_id"]
        title = selected_data["title"]

        if selected_data["is_undone"]:
            messagebox.showinfo("提示", "该操作之前已经撤销过了。", parent=top_win)
            return

        if not messagebox.askyesno("撤销确认", f"确定要撤销【{title}】并将涉及的所有文件复原回原位置吗？", parent=top_win):
            return

        res = undo_mgr.undo_transaction(tx_id)
        self.refresh_history()
        if res["restored"] and self.on_changed:
            self.on_changed()
        if res["success"]:
            messagebox.showinfo("撤销成功", f"{res['message']}", parent=top_win)
        else:
            details = "\n".join(res.get("errors", []))
            message = res["message"]
            if details:
                message += f"\n\n{details}"
            messagebox.showwarning("撤销未完全成功", message, parent=top_win)

    def _on_clear_history(self):
        top_win = self.winfo_toplevel()
        if not messagebox.askyesno("清空确认", "确定要清空全部操作历史记录吗？（清空后将无法撤销既往操作）", parent=top_win):
            return
        undo_mgr.clear_history()
        self.refresh_history()
