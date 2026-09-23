# 开发环境与治理指南 (env/)

> **created**: YYYY-MM-DD ｜ **last-change**: YYYY-MM-DD ｜ **status**: active
> **定位**: 开发环境配置、依赖管理、磁盘缓存盘点与环境安全清理规范
> **适用平台**: macOS (Darwin) / Linux / Windows

---

## 1. 文档清单

| 文档 | 核心内容 | 状态 | 最后更新 |
|---|---|---|---|
| [01-环境缓存与依赖清理指南.md](01-环境缓存与依赖清理指南.md) | 盘点开发过程中产生的本地与全局缓存（含构建中间件、包管理器缓存、单测缓存与虚拟环境），提供分级清理命令与一键重置指引 | 现行有效 | YYYY-MM-DD |

---

## 2. 常用分级清理命令速查 (Quick Cleanup Commands)

- **方案 A：日常轻量瘦身（不破坏依赖与运行环境，耗时 1 秒）**：
  ```bash
  # 清理单测与增量编译缓存
  rm -rf .pytest_cache coverage/ *.tsbuildinfo
  find . -type d -name "__pycache__" -exec rm -rf {} + 2>/dev/null
  find . -name ".DS_Store" -delete 2>/dev/null
  ```

- **方案 B：重置仿真世界（仅清除本地调试数据库，恢复首启空态）**：
  ```bash
  # 清除 local/ 隔离区中的本地运行时数据库
  rm -f local/data/*.db* local/data/*.sqlite*
  ```

- **方案 C：工作区完全纯净（还原代码库，清除工作区生成的依赖与虚拟环境）**：
  ```bash
  # 移除本地虚拟环境、依赖包与构建打包产物
  rm -rf .venv node_modules local/dist local/build local/bin
  ```

- **方案 D：全局深度释放（彻底释放系统级包缓存与运行时）**：
  ```bash
  # 清理系统级全局包缓存（根据实际技术栈选用）
  uv cache clean 2>/dev/null || pip cache purge 2>/dev/null
  npm cache clean --force 2>/dev/null || pnpm store prune 2>/dev/null
  ```
