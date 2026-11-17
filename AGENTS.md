# AGENTS.md

<!-- @ad-flow: initialized v1.8.0 -->

> ad-flow 技能包自身的执行约定，用于维护本仓库与 `docs/devel/` 卡片。安装到目标项目时使用 [templates/AGENTS.md.tpl](templates/AGENTS.md.tpl)，技能入口见 [SKILL.md](SKILL.md)。

## 项目自定义规则 (Project Custom Rules)

- 安装资产（`scripts/`、`templates/`、`workflow.yaml` 的 24+2 契约）与维护者工具（`tools/`）的修改必须同步 `tools/check.sh` 与回归测试；安装资产不进入 `tests/`。
- 技能包源码修改使用 Conventional Commits；提交不带 AI 署名尾注。
- 技能自身的能力演进记录在 `docs/devel/task/` 与设计基线；v1.8.0 批次以 T01–T03 收口。
- 校验器输出、`hint`、`--list-checks`、`--scaffold` 与 `--scope` 的 Agent 使用约定见 `SKILL.md` 的 Agent Command Surface；人类只用自然语言提出需求。
