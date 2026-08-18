from tkinter import messagebox
import customtkinter as ctk
from typing import Callable, Optional
from core.undo_manager import undo_mgr
from ui.components.result_table import ResultTable
from ui.theme import (
    COLOR_PRIMARY, COLOR_PRIMARY_HOVER,
    COLOR_DANGER, COLOR_DANGER_HOVER,
    COLOR_SECONDARY, COLOR_SECONDARY_HOVER
)

class HistoryTab(ctk.CTkFrame):
    """历史记录与一键撤销标签页 (Modern Slate Modular Card)"""

    def __init__(self, master, on_changed: Optional[Callable[[], None]] = None, **kwargs):
        super().__init__(master, fg_color="transparent", **kwargs)
        self.on_changed = on_changed

        self._build_ui()
        self.refresh_history()

    def _build_ui(self):
        # 1. 顶部操作栏卡片
        top_bar = ctk.CTkFrame(
            self,
            corner_radius=10,
            border_width=1,
            border_color=("gray85", "#2E3648"),
            fg_color=("white", "#1B1F2A")
        )
        top_bar.pack(fill="x", padx=10, pady=(6, 8))

        bar_inner = ctk.CTkFrame(top_bar, fg_color="transparent")
        bar_inner.pack(fill="x", padx=16, pady=12)

        ctk.CTkLabel(
            bar_inner,
            text="📜 事务操作履历 (支持对移动/重命名等分类与批处理操作一键安全逆向还原)",
            font=ctk.CTkFont(size=12, weight="bold")
        ).pack(side="left")

        self.undo_btn = ctk.CTkButton(
            bar_inner,
            text="↩ 撤销选中事务",
            width=140,
            height=32,
            font=ctk.CTkFont(size=12, weight="bold"),
            fg_color=COLOR_DANGER,
            hover_color=COLOR_DANGER_HOVER,
            text_color="white",
            command=self._on_undo_clicked
        )
        self.undo_btn.pack(side="right", padx=(10, 0))

        self.refresh_btn = ctk.CTkButton(
            bar_inner,
            text="🔄 刷新",
            width=80,
            height=32,
            font=ctk.CTkFont(size=12),
            fg_color=COLOR_PRIMARY,
            hover_color=COLOR_PRIMARY_HOVER,
            text_color="white",
            command=self.refresh_history
        )
        self.refresh_btn.pack(side="right", padx=(10, 0))

        self.clear_btn = ctk.CTkButton(
            bar_inner,
            text="清空历史",
            width=80,
            height=32,
            font=ctk.CTkFont(size=12),
            fg_color="transparent",
            border_width=1,
            border_color=("gray75", "#3A4459"),
            text_color=("gray20", "gray85"),
            hover_color=("gray90", "#262D3D"),
            command=self._on_clear_history
        )
        self.clear_btn.pack(side="right")

        # 2. 中间：历史表格
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
            text="📋 历史事务记录清单",
            font=ctk.CTkFont(size=13, weight="bold"),
            text_color=("gray20", "gray85")
        ).pack(side="left")

        self.result_table = ResultTable(
            table_container,
            columns=[
                ("tx_id", "事务 ID", 140),
                ("title", "操作类型", 160),
                ("count", "涉及文件", 90),
                ("status", "状态", 110),
                ("time", "操作时间", 160),
                ("description", "备注说明", 260)
            ]
        )
        self.result_table.pack(fill="both", expand=True, padx=8, pady=(0, 8))

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
