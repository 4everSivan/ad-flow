# 01 - 本地部署指南

> **created**: YYYY-MM-DD ｜ **last-change**: YYYY-MM-DD ｜ **status**: active ｜ **version**: >=v0.1.0

---

## 一、环境准备

### 1. 系统与运行时依赖
- 操作系统支持：macOS / Linux
- 运行环境与版本要求（根据具体技术栈配置）：
  - Node.js / Python / Go / Rust 等版本说明

### 2. 端口规划与隔离约定
- 本地调试默认端口：`8080`（或按项目自定义）
- 隔离目录：所有编译与打包产物（`local/dist/`、`local/bin/`）、本地数据（`local/data/`）、运行时日志（`local/logs/`）全量写入 `local/` 目录

---

## 二、配置与环境变量

创建本地环境配置文件 `.env`（严禁提交至 Git）：

```bash
# 本地服务端口
PORT=8080

# 数据与日志路径（收拢于 local/）
DB_PATH=local/data/app.db
LOG_PATH=local/logs/app.log
```

---

## 三、构建与打包规约（Build & Package）

所有编译输出与打包分发产物**强制全量收拢至 `local/` 隔离区**，严禁在项目根目录下直接产生未经隔离的构建物：

```bash
# 示例：前端打包（显式指定输出目录至 local/dist）
npm run build -- --outDir local/dist

# 示例：Go 语言编译（显式指定二进制输出至 local/bin/）
go build -o local/bin/app ./cmd/main.go

# 示例：Python 构建分发包输出
python -m build --outdir local/dist
```

---

## 四、启动与部署步骤

### 1. 安装依赖
```bash
# 安装项目依赖
npm install # 或 pip install / go mod download / cargo build
```

### 2. 服务启动
```bash
# 启动本地服务
npm run dev # 或 python -m app.main
```

---

## 五、部署报告产出规范（必填）

部署成功后，**必须在 `local/` 目录下生成 `local/deploy_report.md`**：

```markdown
# 本地部署验收报告 (deploy_report.md)

| 监控项 | 采集值 |
|---|---|
| 生成时间 | YYYY-MM-DD HH:MM:SS |
| Git 分支 / 提交 | main / <commit_hash> |
| 实际监听端口 | 8080 |
| 实际数据库路径 | local/data/app.db |
| 日志文件 | local/logs/app.log |
| 健康检查端点 | http://127.0.0.1:8080/health |
```

> ⚠️ **红线提醒**：后续所有自动化测试与重新部署均参考 `local/deploy_report.md` 实际运行数据执行，严禁抛开报告重新翻阅本指南！
