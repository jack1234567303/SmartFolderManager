# Changelog

本项目所有重要更改记录均遵循 [Keep a Changelog](https://keepachangelog.com/zh-CN/1.1.0/) 格式。

---

## [1.1.0] - 2025-07-XX

### ✨ Added
- 全新 **Modern Slate / Studio Pro** 设计系统与主题 Token 规范 (`ui/theme.py`)
- 侧边栏导航胶囊按钮 (`SidebarNavButton`) 严格像素对齐
- 一体化现代地址栏 (Omnibar)，集成目录树折叠/展开切换
- 纯粹单色数据表 (ResultTable)，11pt 字号 + 34px 行高
- 可折叠终端面板 (ProgressPanel)，支持展开等宽代码日志
- 深浅色模式自适应调色体系（Dark / Light）
- 高对比度钛青色预览按钮语义优化
- 自适应 AI 文字色彩（Light 紫罗兰 / Dark 冰青色）

### 🔄 Changed
- 所有业务面板 (classify, batch, search, tools, history) 重构为模块化卡片布局
- TTK Treeview 深度定制样式，消除原生白边与粗糙质感

---

## [1.0.1] - 2025-07-XX

### 🐛 Fixed
- 强化文件操作与 Undo 事务处理的边界场景鲁棒性
- 修复移动文件时同名冲突未正确自动重命名的问题

---

## [1.0.0] - 2025-07-XX

### ✨ Added
- 初始项目结构与核心功能
- **智能分类引擎**：按文件类型、大小、日期或 AI 语义自动分类
- **批量操作**：批量创建、批量重命名、回收站安全删除
- **多维搜索引擎**：关键字、正则、大小、日期、AI 语义搜索
- **两阶段查重**：文件大小预筛 + MD5 流式校验
- **空文件夹清理**：自底向上递归扫描安全清理
- **事务级撤销栈**：Undo Manager 完整事务记录与一键恢复
- **多 AI 模型支持**：OpenAI / DeepSeek / Moonshot (Kimi) / Ollama
- **全异步调度**：TaskRunner 后台线程池 + CancellationToken
- 自动错误日志 (`error.log`) 与启动异常弹窗
