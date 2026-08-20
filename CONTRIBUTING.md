# 贡献指南 | Contributing Guide

感谢你对 **Smart Folder Manager Pro** 的关注！欢迎通过 Issue 反馈或 Pull Request 参与贡献。

---

## 🐛 报告 Bug

1. 使用 [Bug Report 模板](.github/ISSUE_TEMPLATE/bug_report.md) 提交 Issue。
2. 请附上 **操作系统版本、Python 版本、复现步骤** 和 **报错日志** (`error.log`)。

## 💡 提出功能建议

1. 使用 [Feature Request 模板](.github/ISSUE_TEMPLATE/feature_request.md) 提交 Issue。
2. 描述你希望的功能场景和预期行为。

---

## 🔧 Pull Request 流程

1. **Fork** 本仓库，并 **Clone** 到本地。
2. 从 `main` 创建功能分支：
   ```bash
   git checkout -b feature/your-feature-name
   ```
3. 完成代码修改，确保：
   - 所有现有测试通过：`python -m unittest discover -s tests -v`
   - 新功能附带对应的单元测试
4. **Commit** 信息请遵循 [Conventional Commits](https://www.conventionalcommits.org/) 规范：
   ```
   feat: add batch rename preview mode
   fix: resolve duplicate detection edge case
   docs: update README quick start section
   ```
5. **Push** 到你的 Fork 并创建 **Pull Request**。

---

## 📏 代码风格约定

| 约定 | 说明 |
|------|------|
| **GUI 框架** | `customtkinter` + 定制 `tkinter.ttk` (Clam 主题) |
| **设计 Token** | 所有颜色、字体、尺寸定义在 `ui/theme.py`，禁止硬编码散落 |
| **文件安全** | 删除操作使用 `send2trash`，I/O 必须经 `TaskRunner` 子线程执行 |
| **事务一致性** | 文件移动与重命名必须通过 `core/undo_manager.py` 记录事务 |
| **命名规范** | 模块 `snake_case`、类 `PascalCase`、常量 `UPPER_SNAKE_CASE` |
| **文档字符串** | 公共函数与类需附中文文档字符串 |

---

## 🔒 安全注意事项

- **不要** 在 PR 中提交 `config.json`、API Key、`.env` 等包含凭据的文件。
- AI 功能相关的密钥请通过环境变量 `SFM_AI_API_KEY` 设置。

---

感谢你的贡献！🎉
