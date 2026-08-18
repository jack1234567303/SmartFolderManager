"""
SFM Pro - 现代设计系统与主题 Token (Modern Slate / Studio Pro)
提供深浅色模式自适应的语义配色、标准尺寸、字体规范及 ttk 组件样式统一配置。
"""

from typing import Dict, Any
from tkinter import ttk

# ==========================================
# 1. 调色板设计系统 (Palette Tokens)
# ==========================================

# 核心主操作色 (Primary Blue)
COLOR_PRIMARY = "#2563EB"          # 电光深蓝 (Primary Blue)
COLOR_PRIMARY_HOVER = "#1D4ED8"    # 主色悬浮态
COLOR_PRIMARY_SUBTLE = "#1E3A8A"   # 主色浅底

# 次级核心/预览动作色 (High Contrast Teal - 替代刺眼难读的浅黄色/橙色)
COLOR_ACTION_ALT = "#0D9488"       # 现代钛青色 (Teal 600，高清晰度对比)
COLOR_ACTION_ALT_HOVER = "#0F766E" # 钛青悬浮态 (Teal 700)
COLOR_ACTION_ALT_SUBTLE = "#134E4A"# 钛青浅底

# 天空海青色 (Cyan / Sky)
COLOR_CYAN = "#0284C7"             # 海青色 (Sky 600)
COLOR_CYAN_HOVER = "#0369A1"       # 海青悬浮态

# AI 专属科技标识色 (针对 Dark 模式彻底消除紫色色散发飘，Light 模式保持优雅紫罗兰)
COLOR_AI = ("#7C3AED", "#0284C7")            # 按钮底色
COLOR_AI_HOVER = ("#6D28D9", "#0369A1")      # 按钮悬浮态
COLOR_AI_TEXT = ("#7C3AED", "#38BDF8")       # 文字色彩: Light 模式保留优雅紫罗兰 (#7C3AED), Dark 模式采用高清晰度冰青色 (#38BDF8, 彻底消除暗黑底色色散与发飘感)

# 状态语义色
COLOR_SUCCESS = "#10B981"          # 成功翠绿 (Success Emerald)
COLOR_SUCCESS_HOVER = "#059669"
COLOR_SUCCESS_SUBTLE = "#064E3B"

COLOR_WARNING = "#D97706"          # 沉稳琥珀 (Deep Warm Amber)
COLOR_WARNING_HOVER = "#B45309"
COLOR_WARNING_SUBTLE = "#78350F"

COLOR_DANGER = "#EF4444"           # 危险/删除绯红 (Danger Crimson)
COLOR_DANGER_HOVER = "#DC2626"
COLOR_DANGER_SUBTLE = "#7F1D1D"

COLOR_SECONDARY = "#4B5563"        # 次级操作灰
COLOR_SECONDARY_HOVER = "#374151"

# 深浅色容器与表面语义表
THEME_COLORS: Dict[str, Dict[str, str]] = {
    "dark": {
        "bg": "#12151B",                # 窗体全局底色 (Deep Slate)
        "surface": "#1B1F2A",           # 卡片/侧边栏表面色 (Slate Card)
        "surface_elevated": "#222836",  # 浮层/二级容器色
        "surface_active": "#2A3142",    # 激活容器色
        "border": "#2E3648",            # 1px 微边框色
        "border_focus": "#3B82F6",      # 聚焦边框色
        "text_primary": "#F3F4F6",      # 主标题/高亮字色
        "text_secondary": "#9CA3AF",    # 次级说明字色
        "text_muted": "#6B7280",        # 占位/微弱字色
        "table_bg": "#171A23",          # 数据表纯底色 (Monochrome)
        "table_fg": "#E5E7EB",          # 数据表文字色
        "table_header_bg": "#1F2432",   # 表头底色
        "table_header_fg": "#93C5FD",   # 表头标题色 (微蓝高质感)
        "table_selected_bg": "#1E40AF", # 选中行背景 (Cobalt Blue)
        "table_selected_fg": "#FFFFFF", # 选中文字色
        "terminal_bg": "#0D1017",       # 终端代码框黑底
        "terminal_fg": "#A7F3D0",       # 终端日志高亮青色
    },
    "light": {
        "bg": "#F8FAFC",                # 窗体全局底色
        "surface": "#FFFFFF",           # 卡片表面色
        "surface_elevated": "#F1F5F9",  # 浮层色
        "surface_active": "#E2E8F0",    # 激活容器色
        "border": "#E2E8F0",            # 分割线与边框色
        "border_focus": "#2563EB",      # 聚焦边框色
        "text_primary": "#0F172A",      # 主标题字色
        "text_secondary": "#475569",    # 次级说明字色
        "text_muted": "#94A3B8",        # 占位/微弱字色
        "table_bg": "#FFFFFF",          # 数据表纯底色
        "table_fg": "#1E293B",          # 数据表文字色
        "table_header_bg": "#F1F5F9",   # 表头底色
        "table_header_fg": "#1D4ED8",   # 表头标题色
        "table_selected_bg": "#DBEAFE", # 选中行背景
        "table_selected_fg": "#1E3A8A", # 选中文字色
        "terminal_bg": "#0F172A",       # 终端日志深色底
        "terminal_fg": "#34D399",       # 终端日志文字
    }
}

# ==========================================
# 2. 字体规范 (Typography Scale)
# ==========================================
FONT_FAMILY = "Segoe UI"
FONT_FAMILY_CN = "Microsoft YaHei"
FONT_FAMILY_MONO = "Consolas"

# ==========================================
# 3. TTK (Treeview / Scrollbar) 主题配置辅助
# ==========================================
def apply_treeview_theme(style: ttk.Style, mode: str = "Dark"):
    """
    配置 ttk.Treeview 深度定制样式，去除原生白边与粗糙质感，使其与 Studio Pro 完全融合。
    字号调整为清晰舒适的 11pt，行高升级至 34px。
    """
    theme_key = "light" if mode.lower() == "light" else "dark"
    colors = THEME_COLORS[theme_key]

    style.theme_use("clam")

    # 1. 目录树与表格内容区 (升级字号为 11pt，舒适行高 34px)
    style.configure(
        "Custom.Treeview",
        background=colors["table_bg"],
        foreground=colors["table_fg"],
        fieldbackground=colors["table_bg"],
        borderwidth=0,
        highlightthickness=0,
        rowheight=34,
        font=(FONT_FAMILY_CN, 11)
    )

    # 2. 表头配置 (升级字号为 11pt 粗体)
    style.configure(
        "Custom.Treeview.Heading",
        background=colors["table_header_bg"],
        foreground=colors["table_header_fg"],
        relief="flat",
        borderwidth=0,
        font=(FONT_FAMILY_CN, 11, "bold"),
        padding=(8, 7)
    )

    # 3. 选举行与悬浮
    style.map(
        "Custom.Treeview",
        background=[("selected", colors["table_selected_bg"])],
        foreground=[("selected", colors["table_selected_fg"])]
    )

    style.map(
        "Custom.Treeview.Heading",
        background=[("active", colors["surface_active"])]
    )

    # 4. 滚动条现代样式
    style.configure(
        "TScrollbar",
        background=colors["surface"],
        troughcolor=colors["bg"],
        borderwidth=0,
        arrowsize=11,
        relief="flat"
    )
