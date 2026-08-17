# 智能文件夹管理大师 Pro (Smart Folder Manager Pro)

一款高颜值、高性能、生产级安全保障与多大模型赋能的现代化桌面文件智能管理工具。

---

## 🌟 核心亮点与技术特色 (Resume Highlights)

1. **现代化交互界面 (CustomTkinter)**
   - 采用深色 / 浅色自适应主题与扁平化卡片布局，告别传统 Tkinter 的粗糙质感。
   - 内置高性能虚拟懒加载目录树（`<<TreeviewOpen>>` 按需加载），解决成千上万大目录遍历时的界面卡顿问题。
   - 内嵌交互式结果看板，支持双击在系统资源管理器直接定位文件或直接打开。

2. **全异步防假死调度 (Async Worker & Task Runner)**
   - 采用后台工作线程池 + 线程安全主事件循环桥接机制，所有文件 I/O、哈希计算及 AI 网络请求均在子线程运行。
   - 支持实时进度条、毫秒级执行日志输出以及**随时可中断/取消任务 (CancellationToken)**。

3. **双重安全机制与事务级撤销 (Undo Manager & Safe Recycle)**
   - **操作撤销栈 (Undo Stack)**：每次批量分类与批量重命名生成事务日志（Transaction），支持在历史记录面板一键逆向恢复文件。
   - **防误删保护**：文件删除全面接入系统回收站（`send2trash`），杜绝直接物理粉碎造成的数据丢失风险。
   - **智能防覆盖**：目标文件夹存在同名文件时自动重命名（如 `file (1).txt`），保障数据安全。

4. **通用大模型赋能 (OpenAI-Compatible AI Layer)**
   - 采用标准 OpenAI API 协议抽象层，支持在设置中心自由切换 **DeepSeek**、**Moonshot (Kimi)**、**OpenAI** 或 **本地 Ollama**。
   - 提供**内容智能分类**与**自然语言语义搜索**（如“找出包含用户登录逻辑的代码”）。
   - 密钥与偏好设置通过图形化面板持久化管理，支持一键连通性探测。

5. **实用文件管理工具箱 (Deduplicator & Cleaner)**
   - **两阶段高效查重**：第一阶段文件大小预筛查，第二阶段流式分块 MD5 校验，快速找出重复冗余文件并支持一键清理副本。
   - **空文件夹清理**：自底向上递归扫描，安全清理无用空目录。

---

## 📂 项目模块结构 (MVC / Service 分层)

```
FP/
├── main.py                     # 程序统一启动入口
├── requirements.txt            # 项目依赖清单
├── config.json                 # 全局配置与模型偏好持久化
├── core/                       # 核心业务逻辑层
│   ├── classifier.py          # 智能分类引擎 (类型/大小/日期/AI) & 预览生成
│   ├── batch_ops.py           # 批量创建、批量重命名、回收站安全删除
│   ├── search_engine.py       # 多维度文件/目录搜索引擎
│   ├── deduplicator.py        # 大小预筛 + MD5 流式查重引擎
│   ├── cleaner.py             # 空文件夹扫描与清理
│   └── undo_manager.py        # 事务记录与一键撤销 (Undo) 栈
├── ai/                         # AI 大模型服务层
│   ├── ai_service.py          # 通用多模型接口客户端 (OpenAI/DeepSeek/Kimi/Ollama)
│   └── prompts.py             # 优化的分类与语义搜索 Prompt 模板
├── ui/                         # 现代化 UI 界面层 (CustomTkinter)
│   ├── app.py                 # 主窗口与侧边栏导航框架
│   ├── components/            # 可复用组件 (懒加载文件树/结果表格/进度面板/设置中心)
│   └── tabs/                  # 业务功能面板 (分类/批处理/搜索/工具箱/历史撤销)
├── utils/                      # 通用工具层 (配置管理/文件辅助/异步调度)
└── tests/                      # 单元测试集
```

---

## 🚀 快速启动

### 1. 安装依赖
```bash
pip install -r requirements.txt
```

### 2. 运行程序
```bash
python main.py
```

### 3. 运行单元测试
```bash
python -m unittest tests/test_core.py
```
