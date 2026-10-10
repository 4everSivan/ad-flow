# Changelog

All notable changes to this project will be documented in this file.

The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.0.0/),
and this project adheres to [Semantic Versioning](https://semver.org/spec/v2.0.0.html).

## [Unreleased]

### Changed (governance specification 1.2.0)

- 保留一次初始化、按需升级和日常独立治理；不新增技能子命令、卡片状态或审批流程。同步入口、状态机和目标项目模板的边界说明。
- 区分授权、硬约束、当前阶段步骤与输入资料；收窄部署报告规则，明确初始化保护与日常授权写入 local/ 的作用范围，以及只读原始快照和新升级快照的区别。
- 在现有节点内明确生成、机械/语义评估和最多 3 轮局部修复；不承诺固定性能收益。升级不自动改写已有业务卡片和 gate。

### Added

- 内存目标状态预检 `--card ID --to STATE` 与限定卡片 gate 回写，解决必须先置终态才能检查终态前提的问题；日常使用项目内模板和工具，无需技能源目录。
- 新增 `ADVISORY` 旁路诊断：缺失设计主题、依赖环路、终态验收项未全部为 true；不提高旧项目硬门槛。
- 隔离工程夹具下的 CLI 行为回归测试，覆盖旧版兼容、目标状态预检、只读与限定回写。

### Fixed

- 修复重复卡号被字典覆盖导致漏检的问题（既有卡号唯一约束）。完整门禁的全局违规计入回写结果，避免局部 gate 错记通过。
- `--warn-only` 存在违规时返回 6，禁止与正式 `--record` 合用；不将降级观察结果作为通过证据。
- 初始化索引、设计矩阵和待办表不再预登记示例事项；校验器兼容任务索引的 tasks 与既有 cards 字段，不迁移旧数据。
- 统一初始化清单为 23 个治理文件加 2 个工具文件、10 个目录 README；保留已有发布记录。

### Previously added

- **流程纪律可执行校验层 `scripts/adflow-verify`（方案 W）**：把双轨卡片不变量从散文 SOP 变为可机械判定的门禁。状态感知扫描活跃卡（P1–P14：设计挂接非 README + `@topic` 锚标匹配、证据锚安全真实、`sync.commit` 为 HEAD 祖先、零沉淀、DAG 拓扑闭环、卡号唯一、版本一致等），收口/合入/归档前 Exit 0 才放行；`--record` 将真实结果回写至卡片 `gate` 块，声称 `exit_code==0` 但实测违规被判 `GATE_CLAIM_CONTRADICTION`。`--mode init` 提供 23 文件骨架 DoD；`--json`/`--warn-only` 供消费与试点。作为仓库内可见、版本化资产注入，**不引入 git 钩子或外部 CI**，保持文档治理流程纯净。
- **卡片 `gate` 块与 `callback.after` 预置**：变更卡/任务卡模板新增 `gate` 字段，并在收尾钩子预置 `scripts/adflow-verify`。
- **`INV_ADFLOW_VERIFY_GATE` 不变量**：终态前必须过门禁并回写 `gate`，Exit 4 禁止收口/合入。

### Changed

- `workflow.yaml`：Step 6 注入校验器副本、Step 8 增 `process_gate_check` 断言、升级流 U4 刷新校验器副本。
- `SKILL.md`：Step 6/8 挂接校验器，不变量新增 `INV_ADFLOW_VERIFY_GATE`。
- `references/02/03/07`：变更/任务/归档 SOP 增加收口门禁步骤；`AGENTS.md` 宪法增加收口门禁硬红线。

## [1.1.0] - 2026-09-24

### Added

- **23 篇标准化工程治理底座**：完整建立覆盖文档中心总览、静态资产库、操作指南、研发内场（设计基线、变更卡池、阶段任务、待办缓冲、环境治理）与历史归档的 23 篇相互咬合的脚手架体系。
- **环境与缓存治理体系 (`docs/devel/env/`)**：深度对齐 QTVictory，新增 `README.md` 与 `01-环境缓存与依赖清理指南.md`，提供跨技术栈磁盘占用盘点表、四级分级清理命令速查（方案 A/B/C/D）与一键快速恢复 SOP。
- **卡片预检与生命周期钩子**：在变更卡（`Cxxx.json`）与任务卡（`Txx.json`）模板中原生注入 `branch` 分支标签、`precheck` 嗅探指令与 `callback`（`before / after` 自动化流程钩子）。
- **全平台多协议自适应触发**：原生兼容 `$ad-flow`（Antigravity / Gemini CLI）、`/ad-flow`（Claude Code / Cursor / Windsurf / Copilot）、纯命令 `ad-flow` 与自然语言意图激活。
- **存量文档逆向语义重构**：接入存量工程时自动原子迁移旧文档至 `_adflow_backup/`，并深度研读源码与旧文档，逆向重构生成自洽的现行设计基线（`00-系统总体设计.md` 与 `01~NN.md`）。

### Changed

- **根目录极致纯净化**：彻底消除根目录配置文件 `adflow.config.json`，元数据统一收拢至 `AGENTS.md`（宪法锚标）与 `docs/index.json`（机器路由），根目录仅保留必要文件与 `local/` 隔离区。
- **设计挂接红线加固 (`INV_NO_README_AS_DESIGN_DOC`)**：机械硬判绝对禁止将任何 `README.md` 作为 `design_doc` 进行卡片关联（违规直接 Exit Code 4 阻断），强制执行“文档先行”补全基线。
- **构建产物与运行时物理双隔离**：规范中明文严令所有编译构建产物（`dist/`、`build/`、`bin/`）与实测数据强制输出收拢至 `local/` 隔离区，Git 严格忽略，杜绝源码树污染。
- **版本感知与平滑升级引擎**：目标项目再次键入 `$ad-flow` 时自动比对治理版本号，检测到新版自动平滑升级协作宪法、README 矩阵与卡片模板，100% 保护存量业务设计与卡片数据。
