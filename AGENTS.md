# AGENTS.md

<!-- @ad-flow: initialized v1.8.0 -->

> ad-flow 技能包自身的执行约定，用于维护本仓库与 `docs/devel/` 卡片。安装到目标项目时使用 [templates/AGENTS.md.tpl](templates/AGENTS.md.tpl)，技能入口见 [SKILL.md](SKILL.md)。

## 项目自定义规则 (Project Custom Rules)

- 安装资产（`scripts/`、`templates/`、`workflow.yaml` 的 24+2 契约）与维护者工具（`tools/`）的修改必须同步 `tools/check.sh` 与回归测试；安装资产不进入 `tests/`。
- 技能包源码修改使用 Conventional Commits；提交不带 AI 署名尾注。
- 技能自身的能力演进记录在 `docs/devel/task/` 与设计基线；v1.8.0 批次以 T01–T03 收口。
- 校验器输出、`hint`、`--list-checks`、`--scaffold` 与 `--scope` 的 Agent 使用约定见 [SKILL.md 的 Agent Command Surface](SKILL.md#agent-command-surface)。人类只用自然语言提出需求。

## 本仓库建卡与归档流程

1. 按[变更 SOP](references/02-change-sop.md)或[任务 SOP](references/03-task-sop.md)确定 C/T 轨道、现行设计主题、标题、卡片版本与分支。T 卡同时确定里程碑。有对应待办时，先定位原文行。
2. **建卡前生成只读计划（A6）。** Agent 在当前工作树运行 `scripts/adflow-verify --scaffold new-card --plan --json`，按 Agent Command Surface 传参。本仓 `docs/standards/` 的 C/T 模板分别链接到技能包的模板源。若 `scaffold.executable=false`，补齐 `scaffold.missing` 后重跑。取得 `scaffold.executable=true` 后，按既有门禁处理 `exit_code` 和 `findings`，并核对现行设计、建议卡号、目标文件、总账和待办原文。发现冲突或输入变化时重新计划。
3. 按计划的 `writes`、`topics` 与 `todo` 创建卡片、登记总账与主题，并移出计划中唯一匹配的待办行。按所选 SOP 补齐正文、里程碑和验收条件。落盘后逐项核对差异，再运行 `scripts/adflow-verify --json`。中断后先核对已写入的卡与登记再继续，避免重复建卡。

发版时按[归档 SOP](references/07-release-archive-sop.md)确认批次范围并执行预检。
