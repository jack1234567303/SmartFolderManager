import threading
import tkinter as tk
from tkinter import messagebox
import customtkinter as ctk
from typing import Callable, Optional
from utils.config_manager import config_mgr
from ai.ai_service import AIService

class SettingsModal(ctk.CTkToplevel):
    """设置中心模态窗口（带防死锁与安全焦点管理）"""

    def __init__(self, master, on_save_callback: Optional[Callable[[], None]] = None):
        super().__init__(master)
        self.title("⚙️ 系统偏好与大模型设置")
        self.geometry("560x620")
        self.resizable(False, False)
        self.on_save_callback = on_save_callback

        # 窗口关闭协议处理
        self.protocol("WM_DELETE_WINDOW", self._on_close)

        self._build_ui()
        self._load_current_values()

        # 安全挂载模态
        self.transient(master)
        self.after(50, self._safe_grab_focus)

    def _safe_grab_focus(self):
        try:
            self.lift()
            self.focus_force()
            self.grab_set()
        except Exception:
            pass

    def _on_close(self):
        try:
            self.grab_release()
        except Exception:
            pass
        self.destroy()

    def _build_ui(self):
        main_frame = ctk.CTkScrollableFrame(self, fg_color="transparent")
        main_frame.pack(fill="both", expand=True, padx=20, pady=15)

        # 1. 界面外观设置
        ui_group = ctk.CTkFrame(main_frame)
        ui_group.pack(fill="x", pady=(0, 15))

        ctk.CTkLabel(ui_group, text="🎨 外观与主题", font=ctk.CTkFont(size=14, weight="bold")).pack(anchor="w", padx=15, pady=(10, 5))

        theme_row = ctk.CTkFrame(ui_group, fg_color="transparent")
        theme_row.pack(fill="x", padx=15, pady=6)
        ctk.CTkLabel(theme_row, text="界面色彩模式:").pack(side="left")
        self.theme_mode_combo = ctk.CTkComboBox(
            theme_row,
            values=["System", "Dark", "Light"],
            command=self._on_theme_mode_change
        )
        self.theme_mode_combo.pack(side="right")

        # 2. AI 大模型设置
        ai_group = ctk.CTkFrame(main_frame)
        ai_group.pack(fill="x", pady=(0, 15))

        ctk.CTkLabel(ai_group, text="🤖 大模型 (OpenAI / DeepSeek / Kimi / Ollama)", font=ctk.CTkFont(size=14, weight="bold")).pack(anchor="w", padx=15, pady=(10, 5))

        # 服务商预设
        provider_row = ctk.CTkFrame(ai_group, fg_color="transparent")
        provider_row.pack(fill="x", padx=15, pady=6)
        ctk.CTkLabel(provider_row, text="服务商预设:").pack(side="left")
        self.provider_combo = ctk.CTkComboBox(
            provider_row,
            values=["Moonshot", "DeepSeek", "OpenAI", "Ollama (Local)", "Custom"],
            command=self._on_provider_change
        )
        self.provider_combo.pack(side="right")

        # Base URL
        url_row = ctk.CTkFrame(ai_group, fg_color="transparent")
        url_row.pack(fill="x", padx=15, pady=6)
        ctk.CTkLabel(url_row, text="API Base URL:").pack(side="left")
        self.base_url_entry = ctk.CTkEntry(url_row, width=320)
        self.base_url_entry.pack(side="right")

        # API Key
        key_row = ctk.CTkFrame(ai_group, fg_color="transparent")
        key_row.pack(fill="x", padx=15, pady=6)
        ctk.CTkLabel(key_row, text="API Key 密钥:").pack(side="left")
        
        self.show_key_var = tk.BooleanVar(value=False)
        self.api_key_entry = ctk.CTkEntry(key_row, width=240, show="*")
        self.api_key_entry.pack(side="left", padx=(10, 5))
        
        self.eye_btn = ctk.CTkCheckBox(key_row, text="显示", width=50, command=self._toggle_show_key)
        self.eye_btn.pack(side="right")

        # Model Name
        model_row = ctk.CTkFrame(ai_group, fg_color="transparent")
        model_row.pack(fill="x", padx=15, pady=6)
        ctk.CTkLabel(model_row, text="模型名称 (Model):").pack(side="left")
        self.model_entry = ctk.CTkEntry(model_row, width=320)
        self.model_entry.pack(side="right")

        # 测试连通性按钮
        test_row = ctk.CTkFrame(ai_group, fg_color="transparent")
        test_row.pack(fill="x", padx=15, pady=(10, 10))
        self.test_btn = ctk.CTkButton(
            test_row,
            text="📡 测试模型连通性",
            fg_color="#337ab7",
            hover_color="#286090",
            command=self._test_api_connection
        )
        self.test_btn.pack(side="left")

        self.test_status_label = ctk.CTkLabel(test_row, text="", font=ctk.CTkFont(size=12))
        self.test_status_label.pack(side="left", padx=10)

        # 底部按钮
        btn_frame = ctk.CTkFrame(self, fg_color="transparent")
        btn_frame.pack(fill="x", padx=20, pady=(0, 15), side="bottom")

        self.save_btn = ctk.CTkButton(
            btn_frame,
            text="💾 保存配置",
            fg_color="#5cb85c",
            hover_color="#449d44",
            command=self._save_settings
        )
        self.save_btn.pack(side="right", padx=(10, 0))

        self.cancel_btn = ctk.CTkButton(
            btn_frame,
            text="取消",
            fg_color="gray",
            hover_color="#555",
            command=self._on_close
        )
        self.cancel_btn.pack(side="right")

    def _load_current_values(self):
        theme = config_mgr.get("theme_mode", "System")
        self.theme_mode_combo.set(theme)

        ai_cfg = config_mgr.get("ai", {})
        provider = ai_cfg.get("provider", "Moonshot")
        self.provider_combo.set(provider)
        self.base_url_entry.insert(0, ai_cfg.get("base_url", ""))
        self.api_key_entry.insert(0, ai_cfg.get("api_key", ""))
        self.model_entry.insert(0, ai_cfg.get("model", ""))

    def _on_theme_mode_change(self, choice: str):
        ctk.set_appearance_mode(choice)

    def _on_provider_change(self, choice: str):
        presets = config_mgr.get("providers_preset", {})
        if choice in presets:
            preset = presets[choice]
            self.base_url_entry.delete(0, "end")
            self.base_url_entry.insert(0, preset.get("base_url", ""))
            self.model_entry.delete(0, "end")
            self.model_entry.insert(0, preset.get("model", ""))

    def _toggle_show_key(self):
        if self.eye_btn.get() == 1:
            self.api_key_entry.configure(show="")
        else:
            self.api_key_entry.configure(show="*")

    def _test_api_connection(self):
        base_url = self.base_url_entry.get().strip()
        api_key = self.api_key_entry.get().strip()
        model = self.model_entry.get().strip()

        if not base_url or not model:
            messagebox.showwarning("提示", "请填写完整的 Base URL 和模型名称后再测试。", parent=self)
            return

        self.test_status_label.configure(text="正在测试连通性...", text_color="#f0ad4e")
        self.test_btn.configure(state="disabled")

        def run_test():
            success, msg = AIService.test_connection(base_url, api_key, model)
            def update_ui():
                self.test_btn.configure(state="normal")
                if success:
                    self.test_status_label.configure(text="✔ 连接成功！", text_color="#5cb85c")
                    messagebox.showinfo("测试成功", msg, parent=self)
                else:
                    self.test_status_label.configure(text="✖ 连接失败", text_color="#d9534f")
                    messagebox.showerror("测试失败", msg, parent=self)
            self.after(0, update_ui)

        threading.Thread(target=run_test, daemon=True).start()

    def _save_settings(self):
        theme_mode = self.theme_mode_combo.get()
        provider = self.provider_combo.get()
        base_url = self.base_url_entry.get().strip()
        api_key = self.api_key_entry.get().strip()
        model = self.model_entry.get().strip()

        config_mgr.set("theme_mode", theme_mode)
        config_mgr.set("ai.provider", provider)
        config_mgr.set("ai.base_url", base_url)
        config_mgr.set("ai.api_key", api_key)
        config_mgr.set("ai.model", model)

        if config_mgr.save_config():
            messagebox.showinfo("成功", "配置已成功保存！", parent=self)
            if self.on_save_callback:
                self.on_save_callback()
            self._on_close()
        else:
            messagebox.showerror("错误", "保存配置文件失败，请检查文件写入权限。", parent=self)
