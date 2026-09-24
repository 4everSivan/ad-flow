# Changelog

All notable changes to this project will be documented in this file.

The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.0.0/),
and this project adheres to [Semantic Versioning](https://semver.org/spec/v2.0.0.html).

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
