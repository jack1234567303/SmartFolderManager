# 智能文件夹管理大师 Pro (SFM Pro) — 协作与治理规范

一款基于 Python + CustomTkinter 的现代化桌面文件管理与智能批处理工具，融合 MVC 分层、事务级可撤销栈与多大模型能力。

## 🚀 常用运行与测试命令

- **启动主程序**：`python main.py`
- **运行单元测试**：`python -m unittest discover -s tests -v`
- **安装依赖**：`pip install -r requirements.txt`

## 🛠️ 技术栈与设计规范

- **GUI 框架**：`customtkinter` + 定制 `tkinter.ttk` (Clam 主题)。
- **设计系统**：`ui/theme.py` 统一定义 Modern Slate Token，禁止在业务组件内散落硬编码颜色。
- **文件安全与 I/O**：使用 `send2trash` 安全放入回收站；I/O 及 AI 网络请求必须经 `TaskRunner` 在子线程执行并支持 `CancellationToken` 取消。
- **事务一致性**：文件移动与批量重命名必须通过 `core.undo_manager` 记录事务。

## 🔒 安全边界

以下操作 **禁止** AI Agent 执行：

- **不修改** `core/`、`ai/`、`ui/`、`utils/`、`main.py` 中的核心业务逻辑与 UI 交互代码，除非用户明确要求。
- **不删除** 用户数据文件（`config.json`、`history.json`）、`tests/` 测试文件。
- **不提交** API Key、`config.json`、`.env` 等包含凭据的文件到仓库。
- **不修改** `requirements.txt` 中已有的依赖版本范围，新增依赖需用户确认。
- **不发布** 绝对用户路径、截图、偏好设置等机器特定信息到公共文档。

## 📂 核心目录与约定

```
SFM/
├── main.py              # 程序统一启动入口
├── core/                # 业务逻辑层 (分类/批处理/查重/搜索/清理/撤销栈)
├── ai/                  # AI 服务抽象层 (OpenAI/DeepSeek/Kimi/Ollama)
├── ui/                  # UI 界面层 (app.py, theme.py, components/, tabs/)
├── utils/               # 工具层 (配置管理、文件辅助、TaskRunner 调度)
└── tests/               # 单元测试集 (test_core.py, test_ui_init.py)
```

## 📌 当前状态与下一步

- **当前状态**：UI 已全面升级为 Studio Pro 现代工作站设计语言；支持深浅色自适应、可折叠目录树、纯粹单色结果表、折叠代码终端及事务撤销。16 项单元测试全部通过。
- **下一步规划**：增加更多文件格式解析预览器，支持多语言国际化 (i18n)。
