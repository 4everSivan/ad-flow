# 开发环境缓存与依赖清理指南

> **文档ID**: ENV-01 ｜ **状态**: 现行有效
> **适用平台**: macOS (Darwin) / Linux / Windows ｜ **最后更新**: YYYY-MM-DD

---

## 1. 概览与磁盘占用盘点

在项目开发、依赖安装、自动化测试（单测/集成测试/E2E 测试）以及本地服务运行过程中，产生的文件分布在**项目工作区内**与**用户主目录系统级缓存**两大部分。

标准环境磁盘占用分类盘点参考如下：

| 类别 | 常见路径 | 预估占用 | 性质 | 清理后影响 |
|---|---|---|---|---|
| **E2E 浏览器运行时** | `~/Library/Caches/ms-playwright/` 或 `~/.cache/ms-playwright/` | **~500 MB+** | 全局下载运行时 | 无法直接运行无头 E2E 测试，需重新 `playwright install` |
| **npm / pnpm 全局缓存** | `~/.npm/` 或 `~/.local/share/pnpm/store/` | **~500 MB~1.5 GB** | 全局包缓存 | 不影响项目运行，后续首次依赖安装稍慢 |
| **uv / pip 全局缓存** | `~/.cache/uv/` 或 `~/Library/Caches/pip/` | **~300 MB~1 GB** | 全局 Wheel 缓存 | 不影响项目运行，后续首次安装稍慢 |
| **前端/Node 依赖包** | `node_modules/` | **~100 MB~500 MB** | 本地依赖包 | 无法开发与构建前端，需重新 `npm/pnpm/yarn install` |
| **Python 虚拟环境** | `.venv/` 或 `venv/` | **~50 MB~300 MB** | 本地虚拟环境 | 无法运行后端，需重新创建虚拟环境与安装依赖 |
| **本地运行时数据** | `local/data/` | **按需** | 本地调试数据库 | 丢失本地创建的测试记录，恢复首启空世界 |
| **编译打包产物** | `local/dist/`、`local/build/`、`local/bin/` | **按需** | 构建分发产物 | 需重新触发构建脚本方可生成 |
| **增量编译缓存** | `*.tsbuildinfo` | **~100 KB** | 增量编译元数据 | 下次构建重新全量编译，耗时微增 |
| **语言字节码/测试缓存** | `.pytest_cache/`、`__pycache__/`、`.turbo/` | **~10 MB** | 单测与字节码缓存 | 下次运行自动化套件自动重新生成 |
| **系统隐藏文件** | `.DS_Store`、`Thumbs.db` | **少量** | 系统元数据 | 0 影响，建议定期彻底清理 |

---

## 2. 细项清单与分类说明

### 2.1 系统全局层（Out-of-Workspace）
此类文件保存在用户主目录（`$HOME`）下，占用空间最大：
1. **包管理器全局缓存**：
   - uv 缓存：`uv cache clean`
   - pip 缓存：`pip cache purge`
   - npm 缓存：`npm cache clean --force`
   - pnpm 存储库：`pnpm store prune`
2. **测试与无头浏览器运行时**（若项目引入 Playwright/Puppeteer）：
   - `rm -rf ~/Library/Caches/ms-playwright`（macOS）或 `rm -rf ~/.cache/ms-playwright`（Linux）

### 2.2 工作区依赖与编译层
1. **依赖库目录**：
   - Node: `node_modules/`
   - Python: `.venv/`、`venv/`
2. **构建打包产物（强制收拢于 `local/`）**：
   - `local/dist/`、`local/build/`、`local/bin/`

### 2.3 测试与字节码缓存
- Python: `find . -type d -name "__pycache__" -exec rm -rf {} +` 与 `rm -rf .pytest_cache`
- TypeScript: `rm -f *.tsbuildinfo`
- 覆盖率报表: `rm -rf coverage/ .nyc_output/ htmlcov/`

### 2.4 本地运行时数据（`local/data/`）
- 本地调试 SQLite / DuckDB / 日志文件收拢于 `local/data/` 与 `local/logs/`。
- 清理该目录将系统复位为首启“空世界”状态。

---

## 3. 分级清理场景与操作指引

根据后续清理意图不同，推荐选择对应层级的清理操作：

### 方案 A：轻量瘦身（日常清理，耗时 1 秒，不损耗依赖）
> **适用场景**: 日常开发单测完毕、清理临时文件与增量缓存，保持能直接启动开发。

```bash
# 1. 清理单测与编译缓存
rm -rf .pytest_cache coverage/ htmlcov/ *.tsbuildinfo
find . -type d -name "__pycache__" -exec rm -rf {} + 2>/dev/null

# 2. 清理系统隐藏元数据
find . -name ".DS_Store" -delete 2>/dev/null
```

---

### 方案 B：重置仿真世界（数据归零，耗时 1 秒）
> **适用场景**: 清理演练测试数据，将系统复位为空世界首启状态。

```bash
# 清空 local/ 中的本地数据库（服务停止状态下执行）
rm -f local/data/*.db* local/data/*.sqlite* local/data/*.duckdb*
```

---

### 方案 C：工作区完全纯净（还原代码库，耗时 3 秒）
> **适用场景**: 向远端推送或归档项目源码，清除所有工作区生成的依赖与虚拟环境。

```bash
# 1. 移除虚拟环境与依赖
rm -rf .venv venv node_modules

# 2. 清除编译产物与运行时数据
rm -rf local/dist local/build local/bin local/data local/logs

# 3. 递归清除缓存与系统垃圾
find . -type d -name "__pycache__" -exec rm -rf {} + 2>/dev/null
find . -name ".DS_Store" -delete 2>/dev/null
```

---

### 方案 D：全局极限释放（释放系统磁盘空间，释放数 GB）
> **适用场景**: 彻底归档项目，释放主机系统磁盘占用。

```bash
# 1. 执行方案 C 清理工作区
rm -rf .venv venv node_modules local/dist local/build local/bin

# 2. 清理全局包管理器缓存
uv cache clean 2>/dev/null || pip cache purge 2>/dev/null
npm cache clean --force 2>/dev/null || pnpm store prune 2>/dev/null

# 3. 清理 E2E 浏览器缓存
rm -rf ~/Library/Caches/ms-playwright ~/.cache/ms-playwright 2>/dev/null
```

---

## 4. 环境重新初始化指引（清理后的快速恢复）

若执行了【方案 C】或【方案 D】清理后需恢复开发与测试环境，执行以下通用步骤即可一键重建：

### 4.1 恢复后端环境 (Python 示例)
```bash
uv venv
source .venv/bin/activate
uv pip install -e ".[dev]"
pytest  # 验证测试套件就绪
```

### 4.2 恢复前端环境 (Node / Web 示例)
```bash
npm install
npm run build
npm run test
```

---

## 5. .gitignore 规则核验与建议

对照根目录 `.gitignore`，请确保以下通用项已被严格忽略：
- 本地隔离区：`local/dist/`、`local/build/`、`local/bin/`、`local/data/`、`local/logs/`
- 依赖目录：`node_modules/`、`.venv/`、`venv/`
- 缓存与临时文件：`__pycache__/`、`.pytest_cache/`、`*.tsbuildinfo`、`coverage/`、`.DS_Store`
