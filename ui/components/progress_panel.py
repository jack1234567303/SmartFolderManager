import customtkinter as ctk
from typing import Optional, Callable

class ProgressPanel(ctk.CTkFrame):
    """
    通用进度与控制台日志面板
    """
    def __init__(self, master, on_cancel: Optional[Callable[[], None]] = None, **kwargs):
        super().__init__(master, fg_color="transparent", **kwargs)
        self.on_cancel = on_cancel

        # 顶部：状态提示与取消按钮
        self.header_frame = ctk.CTkFrame(self, fg_color="transparent")
        self.header_frame.pack(fill="x", pady=(2, 4))

        self.status_label = ctk.CTkLabel(
            self.header_frame,
            text="就绪",
            font=ctk.CTkFont(size=13),
            anchor="w"
        )
        self.status_label.pack(side="left", fill="x", expand=True)

        self.cancel_btn = ctk.CTkButton(
            self.header_frame,
            text="中止任务",
            width=80,
            height=28,
            fg_color="#d9534f",
            hover_color="#c9302c",
            command=self._handle_cancel
        )
        self.cancel_btn.pack(side="right")
        self.cancel_btn.pack_forget()  # 默认隐藏

        # 进度条
        self.progress_bar = ctk.CTkProgressBar(self, height=8)
        self.progress_bar.pack(fill="x", pady=(0, 6))
        self.progress_bar.set(0)

        # 折叠/展开日志区域
        self.log_container = ctk.CTkFrame(self)
        self.log_container.pack(fill="both", expand=True, pady=(2, 0))

        log_top = ctk.CTkFrame(self.log_container, fg_color="transparent")
        log_top.pack(fill="x", padx=4, pady=2)
        ctk.CTkLabel(log_top, text="📋 执行日志", font=ctk.CTkFont(size=12, weight="bold")).pack(side="left")
        
        self.clear_btn = ctk.CTkButton(
            log_top,
            text="清空日志",
            width=60,
            height=22,
            font=ctk.CTkFont(size=11),
            fg_color="gray",
            hover_color="#555",
            command=self.clear_log
        )
        self.clear_btn.pack(side="right")

        self.log_box = ctk.CTkTextbox(
            self.log_container,
            height=90,
            font=ctk.CTkFont(family="Consolas", size=11),
            wrap="word"
        )
        self.log_box.pack(fill="both", expand=True, padx=4, pady=(0, 4))

    def _handle_cancel(self):
        if self.on_cancel:
            self.on_cancel()
        self.set_status("正在中止任务...")

    def start_progress(self, status_text: str = "处理中..."):
        self.progress_bar.set(0)
        self.status_label.configure(text=status_text)
        self.cancel_btn.pack(side="right")

    def update_progress(self, percent: float, status_text: str = ""):
        self.progress_bar.set(max(0.0, min(1.0, percent)))
        if status_text:
            self.status_label.configure(text=status_text)

    def finish_progress(self, status_text: str = "完成"):
        self.progress_bar.set(1.0)
        self.status_label.configure(text=status_text)
        self.cancel_btn.pack_forget()

    def set_status(self, text: str):
        self.status_label.configure(text=text)

    def append_log(self, msg: str):
        self.log_box.insert("end", msg + "\n")
        self.log_box.see("end")

    def clear_log(self):
        self.log_box.delete("1.0", "end")
