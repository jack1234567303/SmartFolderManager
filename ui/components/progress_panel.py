import customtkinter as ctk
from typing import Optional, Callable
from ui.theme import (
    COLOR_PRIMARY, COLOR_DANGER, COLOR_DANGER_HOVER,
    COLOR_SECONDARY, COLOR_SECONDARY_HOVER,
    THEME_COLORS
)

class ProgressPanel(ctk.CTkFrame):
    """
    智能可折叠终端面板 (Collapsible Studio Terminal)
    默认紧凑胶囊展示进度与状态，支持向上展开极客代码终端日志。
    """
    def __init__(self, master, on_cancel: Optional[Callable[[], None]] = None, **kwargs):
        super().__init__(master, fg_color="transparent", **kwargs)
        self.on_cancel = on_cancel
        self.log_expanded = False

        self._build_ui()

    def _build_ui(self):
        # 1. 顶部控制与状态栏卡片
        self.status_card = ctk.CTkFrame(
            self,
            corner_radius=8,
            border_width=1,
            border_color=("gray85", "#2E3648"),
            fg_color=("white", "#1B1F2A"),
            height=38
        )
        self.status_card.pack(fill="x", pady=(0, 2))

        # 状态指示灯与文字
        self.status_indicator = ctk.CTkLabel(
            self.status_card,
            text="●",
            font=ctk.CTkFont(size=13, weight="bold"),
            text_color="#10B981"
        )
        self.status_indicator.pack(side="left", padx=(10, 4))

        self.status_label = ctk.CTkLabel(
            self.status_card,
            text="就绪",
            font=ctk.CTkFont(size=12, weight="bold"),
            anchor="w"
        )
        self.status_label.pack(side="left", fill="x", expand=True, padx=(0, 10))

        # 进度百分比标签
        self.percent_label = ctk.CTkLabel(
            self.status_card,
            text="",
            font=ctk.CTkFont(size=11, weight="bold"),
            text_color=("gray40", "gray60")
        )
        self.percent_label.pack(side="right", padx=(0, 8))

        # 日志展开/收起按钮
        self.toggle_log_btn = ctk.CTkButton(
            self.status_card,
            text="📋 日志 ▼",
            width=70,
            height=24,
            font=ctk.CTkFont(size=11),
            fg_color="transparent",
            border_width=1,
            border_color=("gray75", "#3A4459"),
            text_color=("gray20", "gray85"),
            hover_color=("gray90", "#262D3D"),
            command=self._toggle_log
        )
        self.toggle_log_btn.pack(side="right", padx=(0, 8))

        # 中止任务按钮 (初始隐藏)
        self.cancel_btn = ctk.CTkButton(
            self.status_card,
            text="✕ 中止",
            width=65,
            height=24,
            font=ctk.CTkFont(size=11, weight="bold"),
            fg_color=COLOR_DANGER,
            hover_color=COLOR_DANGER_HOVER,
            command=self._handle_cancel
        )
        self.cancel_btn.pack(side="right", padx=(0, 8))
        self.cancel_btn.pack_forget()

        # 2. 细致进度条
        self.progress_bar = ctk.CTkProgressBar(
            self,
            height=4,
            corner_radius=2,
            progress_color=COLOR_PRIMARY,
            fg_color=("gray85", "#252B3B")
        )
        self.progress_bar.pack(fill="x", pady=(2, 4))
        self.progress_bar.set(0)

        # 3. 可折叠终端代码日志框 (默认隐藏)
        self.log_container = ctk.CTkFrame(
            self,
            corner_radius=8,
            border_width=1,
            border_color=("gray85", "#2E3648"),
            fg_color=("white", "#1B1F2A")
        )

        log_top = ctk.CTkFrame(self.log_container, fg_color="transparent", height=28)
        log_top.pack(fill="x", padx=8, pady=(4, 2))

        ctk.CTkLabel(
            log_top,
            text="💻 终端执行日志 (Terminal Output)",
            font=ctk.CTkFont(family="Consolas", size=11, weight="bold"),
            text_color=("gray30", "#93C5FD")
        ).pack(side="left")

        self.clear_btn = ctk.CTkButton(
            log_top,
            text="清空",
            width=48,
            height=20,
            font=ctk.CTkFont(size=10),
            fg_color="transparent",
            border_width=1,
            border_color=("gray75", "#3A4459"),
            text_color=("gray30", "gray70"),
            hover_color=("gray90", "#262D3D"),
            command=self.clear_log
        )
        self.clear_btn.pack(side="right")

        self.log_box = ctk.CTkTextbox(
            self.log_container,
            height=100,
            font=ctk.CTkFont(family="Consolas", size=11),
            fg_color=("#F1F5F9", "#0D1017"),
            text_color=("#0F172A", "#A7F3D0"),
            wrap="word",
            corner_radius=6
        )
        self.log_box.pack(fill="both", expand=True, padx=8, pady=(0, 6))

    def _toggle_log(self):
        if self.log_expanded:
            self.log_container.pack_forget()
            self.toggle_log_btn.configure(text="📋 日志 ▼")
            self.log_expanded = False
        else:
            self.log_container.pack(fill="both", expand=True, pady=(2, 0))
            self.toggle_log_btn.configure(text="📋 日志 ▲")
            self.log_expanded = True

    def _handle_cancel(self):
        if self.on_cancel:
            self.on_cancel()
        self.set_status("正在中止任务...", is_active=True)

    def start_progress(self, status_text: str = "处理中..."):
        self.progress_bar.set(0)
        self.percent_label.configure(text="0%")
        self.set_status(status_text, is_active=True)
        self.cancel_btn.pack(side="right", padx=(0, 8))

    def update_progress(self, percent: float, status_text: str = ""):
        pct = max(0.0, min(1.0, percent))
        self.progress_bar.set(pct)
        self.percent_label.configure(text=f"{int(pct * 100)}%")
        if status_text:
            self.status_label.configure(text=status_text)

    def finish_progress(self, status_text: str = "完成"):
        self.progress_bar.set(1.0)
        self.percent_label.configure(text="100%")
        self.set_status(status_text, is_active=False)
        self.cancel_btn.pack_forget()

    def set_status(self, text: str, is_active: bool = False):
        self.status_label.configure(text=text)
        if is_active:
            self.status_indicator.configure(text_color="#F59E0B")  # 黄色处理中
        else:
            self.status_indicator.configure(text_color="#10B981")  # 绿色就绪

    def append_log(self, msg: str):
        self.log_box.insert("end", msg + "\n")
        self.log_box.see("end")

    def clear_log(self):
        self.log_box.delete("1.0", "end")
