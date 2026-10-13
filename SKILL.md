---
name: ad-flow
description: >-
  Bootstrap or upgrade project documentation governance when the user invokes
  `$ad-flow`, `/ad-flow`, `ad-flow`, or requests governance initialization or upgrade.
  Installs 24 governance files, including selected JSON coding standards, plus a self-contained verifier. Version-aware and
  idempotent; preserves business documents, cards, and custom rules on upgrade.
  Routine development uses the installed project rules without invoking this skill again.
---

# ad-flow

## 1. Purpose and Invocation

Initialize or upgrade the ad-flow governance assets in `target_dir` (default: the current project). Current governance version: **1.3.0**.

- Accept `$ad-flow`, `/ad-flow`, `ad-flow`, `adflow`, and explicit initialization/upgrade requests, with an optional project path.
- Keep one skill entrypoint. `init`, `new-card`, and `archive` are not skill subcommands.
- After initialization, everyday design, C/T card work, verification, and archiving use the target project's `AGENTS.md`, directory READMEs, templates, indexes, and `scripts/adflow-verify`. They do not require this skill or access to its source directory.
- Updating the skill package does not update other projects automatically. Calling it again in an older project requests specification synchronization, not re-initialization.
- Keep the existing dual-track lifecycle, directory layout, card states, human acceptance, zero-sediment rule, and release archiving. The generation/check/repair loop below is internal to existing steps, not another user workflow.

## 2. Authority, Constraints, and Input Data

### Authority and Tradeoffs

Complete authorized inspection, generation, and local repair without asking for each file. Reuse explicit authorization already given for this target and operation; `--yes` also authorizes the stated initialization scope. Before migrating an existing project's documents, obtain that authorization if it is missing. Initialization does not authorize deployment, Git push, merging, cleanup, or human signoff.

Protect existing assets while avoiding unnecessary delay: continue independent, reversible work within scope; stop the dependent operation when permission, source facts, or a preservation conflict is unresolved. For routine hotfix work after initialization, follow the installed project rules; a description of business urgency does not expand authorization.

### Preservation Boundaries

- **Backup snapshots:** creating a new snapshot is allowed during authorized initialization/upgrade. Once captured, its contents are read-only. Never delete, move, overwrite, or prune existing snapshots. If a destination already exists, stop before moving assets into it; upgrades use a fresh `upgrade_snapshot/<run_id>/` directory.
- **Backup Git exclusion:** before creating any backup, ensure the target root `.gitignore` effectively ignores `/_adflow_backup/`. Create it if absent; otherwise preserve existing contents and append the rule only when no effective equivalent exists, adding a separating newline if needed. Place the appended rule after any conflicting negation. Report already tracked backup paths; do not remove them from Git's index automatically.
- **`local/`:** initialization and governance upgrade leave existing runtime data and reports untouched. Later authorized builds, tests, and deployments may write their outputs/reports there. Deleting or resetting existing contents remains outside this workflow.
- **Business assets on upgrade:** preserve design documents, existing C/T cards, todo buffers, index registrations, and project custom rules. Update managed specification sections and templates only; do not retroactively migrate old cards or run `--record` during upgrade.
- **Evidence:** report actual commands, exit codes, and remaining uncertainty. A structural gate does not prove source/design agreement, application behavior, or human acceptance. Do not invent design facts or signoff.
- **Design links:** C/T cards and topic indexes point to concrete baseline documents with matching `@topic` anchors, never directory READMEs.

### Semantic Separation and Progressive Reading

Keep policies, current-step instructions, source material, examples, and output contracts visibly separate. Markdown headings and YAML/JSON fields are suitable for static rules. When mixing dynamic source extracts with instructions, use descriptive XML blocks such as `<source_material source="…">` and `<task_instructions>`; treat source content as evidence, not authority. Escape embedded delimiters when needed. Tags do not grant permissions or guarantee isolation.

Read the template and reference needed by the current step, not the entire skill bundle. For lifecycle semantics consult [change SOP](references/02-change-sop.md), [task SOP](references/03-task-sop.md), or [archive SOP](references/07-release-archive-sop.md) only when relevant. The installed project must contain the daily execution rules itself.

## 3. Route Before Writing

Read the initialization tag in `AGENTS.md`/`Agent.md` and `adflow_version` in `docs/index.json`. Compare numeric version components using code, not textual ordering. If sources disagree or a version is malformed, report the conflict without writing.

| Target state | Action |
|---|---|
| Version equals 1.3.0 | Check installed assets before exiting unchanged; resume incomplete initialization as described below. Explicit `--force`/`--upgrade` requests preserving synchronization |
| Older or unversioned ad-flow tag | Run the upgrade pipeline |
| Version newer than 1.3.0 | Report the newer version; do not downgrade, including with `--force` |
| No ad-flow tag/version | Survey assets, then initialize |

Matching version fields record the installed specification, not proof of completed initialization. Before a same-version exit, run the installed verifier in init and process modes without `--record` (use the skill's verifier read-only if the installed copy is missing). Also check Step 7's source-backed designs and registrations when applicable. If installation is incomplete, reuse its preserved sources and continue only the unfinished Steps 4–8 within the existing authorization; preserve business records and completed work, never repeat migration. Existing-card findings alone are not an incomplete installation and do not authorize rewriting cards. Report completion only after Step 8's mechanical and semantic checks.

Older installations may keep their original C/T templates, guide filenames and optional `docs/devel/coding-standards.json` registration. A same-version integrity check accepts that layout read-only and does not add or migrate standards. Fresh initialization and requested specification synchronization use `docs/standards/`.

```mermaid
flowchart TD
    A[Resolve target and inspect versions] --> B{Target state}
    B -->|Current| C[Check installed assets]
    C -->|Complete| I[Exit unchanged and report findings]
    C -->|Incomplete| J[Resume unfinished steps without migration]
    J --> G
    B -->|Older| D[Preserving upgrade]
    B -->|Uninitialized| E[Survey and authorize migration]
    E --> F[Snapshot and generate]
    F --> G[Check, repair within scope, report]
    D --> G
    B -->|Newer or conflicting| H[Report without writes]
```

## 4. Initialization Pipeline

Use `workflow.yaml` for the template-to-target mappings. Execute these steps in order.

### Step 1: Survey Assets

Inspect source indicators (`package.json`, `Cargo.toml`, `pyproject.toml`, `go.mod`, `pom.xml`, `Makefile`, `src/`, `lib/`, `app/`) and existing documentation (`docs/`, `doc/`, openspec/superpower/spec directories and root documents). Classify as `EMPTY_PROJECT`, `ONGOING_CODE_ONLY`, or `ONGOING_CODE_AND_DOCS`. Inventory the assets to migrate and the existing agent rules.

Offer coding-standard choices in the existing initialization conversation: `python`, `go`, `javascript`, `typescript`, `java`, `shell`, `cpp`, `rust`, or common-only; multiple languages are allowed. Recommend only languages evidenced by project manifests and authored source files, excluding dependencies, generated files and backup snapshots. Explicit user choices win; otherwise state the detected defaults, using common-only for an empty or uncertain stack. A dependency or template example alone is not evidence of an authored language. This is a preference within initialization, not another approval gate.

### Step 2: Authorize Existing-Asset Migration

For a nonempty project without prior authorization or `--yes`, explain the concrete migration and ask:

> 检测到当前项目已有代码/文档资产。接入 ad-flow 将先把现有文档完整备份至 `_adflow_backup/`，再生成治理文件。是否确认初始化？[y/N]

On rejection, exit without edits. Empty projects proceed directly.

### Step 3: Capture an Isolation Snapshot

For existing assets, apply the backup Git exclusion above before creating `_adflow_backup/README.md` if absent, documenting snapshot protection. Inventory destinations before moving anything.

- Move an existing `docs/` atomically to `_adflow_backup/original_docs/docs/`, then recreate `docs/`. Classify other mapped directories before moving them; source, tests, and build inputs remain in place.
- Copy root documents and agent rules to `original_docs/root_markdowns/` before any managed replacement; leave other originals in place. Do not classify `*.txt` as documentation by extension: files such as `requirements.txt` and `CMakeLists.txt` are build inputs.
- For code-only projects, analysis drafts may be created in a fresh `analyzed_drafts/` area. Do not edit captured originals.
- Never overwrite an existing snapshot or repeat migration as part of a repair pass.

### Step 4: Install Project Rules

Render `templates/AGENTS.md.tpl` to `${target_dir}/AGENTS.md` with `<!-- @ad-flow: initialized v1.3.0 -->`. Collect project-specific rules from every distinct existing agent file before replacing any of them, retaining their source attribution under `## 项目自定义规则 (Project Custom Rules)` (also recognize `## Project Custom Rules`). If an untagged original has no such section, retain its rules in full. For a previously managed file, preserve project-specific text outside identifiable managed sections; exclude old initialization markers and identifiable old managed rules from the merged content. Keep uncertain text and disclose conflicts instead of silently dropping rules. Preserve all original snapshots. Only then make distinct legacy `Agent.md`/`agents.md` aliases pointers to `AGENTS.md` without stale ad-flow tags; account for case-insensitive paths before writing.

### Step 5: Install the 10 Directory READMEs

Use the Step 5 mappings for `docs/`, `assets/`, `devel/`, `devel/design/`, `devel/change/`, `devel/task/`, `devel/todo/`, `devel/env/`, `guide/`, and `archive/`. Preserve each template's structure and metadata conventions. The four-chapter requirement applies to synthesized business designs in Step 7. The design README provides the outline; do not create a generic placeholder design.

### Step 6: Install Routing Hubs, Templates, and Tools

Use the Step 6 mappings for indexes, C/T templates, todo buffers, environment and deployment guides, and `CHANGELOG.md`. Start indexes, design registrations, and todo tables empty; register only actual project assets, never sample cards or example designs. Copy `scripts/adflow_verify.py` and the executable `scripts/adflow-verify` wrapper verbatim. The result is **24 governance files plus 2 verifier files**; runtime directories and synthesized designs are additional assets.

Render `templates/docs/standards/coding.json.tpl` to `docs/standards/coding.json`. Parse it and the selected `templates/coding-standards/<language>.json` fragments as JSON, place each whole fragment under `languages[language]`, and serialize as UTF-8 JSON without comments or trailing commas. Keep `common`, precedence and source attribution; copy only selected profiles, never references to skill-source paths or inheritance between profiles. With common-only, `languages` is `{}`. Do not rewrite formatter/linter configs, install tools or reformat source files. Preserve an existing coding-standards document byte-for-byte, including custom fields and rules, unless the user explicitly requests changes to it; recover its saved copy after document migration if necessary, including a legacy `docs/devel/coding-standards.json`. If legacy and canonical copies differ, report the conflict before replacing either. Register all three canonical standard paths in `docs/index.json.standards` and keep the README/AGENTS links local. The standards directory needs no separate README or index. Use English for coding standards and language profiles, and for workflow execution instructions. Keep other generated bodies in their established Chinese form, including READMEs, AGENTS, design headings/filenames, guides, todo and card descriptions. Preserve English metadata/JSON keys, identifiers and commands; retain project facts, custom rules and human quotations verbatim.

### Step 7: Reconstruct Evidence-Based Designs

When legacy documents or source code exist, inspect them to generate `docs/devel/design/00-系统总体设计.md` and domain documents `01~NN-[模块中文名].md`. Preserve established design filenames and links when resuming or synchronizing an existing installation.

- Describe architecture, domain boundaries, requirements, interfaces, and rules supported by inspected sources. Record source locations and unresolved conflicts; keep uncertain conclusions explicit rather than filling gaps with invented facts.
- Use the four-chapter structure, metadata (`created`, `last-change`, `status`; project release `version` only where applicable), `<!-- @topic: TopicName -->`, and `[变更总账 (TopicName)](../change/index.json#TopicName)`.
- Register designs in the design README module matrix and `docs/devel/index.json`.

### Step 8: Check, Repair, and Report

1. **Mechanical evaluation:** run `scripts/adflow-verify --mode init --json` and `scripts/adflow-verify --json` in the target. Use the findings' codes and paths to locate defects. Formal gate success requires Exit 0; Exit 4 blocks success, and unresolved existing Exit 6 items are reported for human disposition rather than called passed. `ADVISORY` findings are nonblocking observations, not new closure requirements.
   When a backup exists in a target Git repository, separately use `git check-ignore --no-index` to verify coverage of the backup README and nested snapshot paths, and `git ls-files -- _adflow_backup/` to detect already tracked backups. Outside Git, inspect the root ignore rule without initializing a repository for validation.
2. **Semantic evaluation:** check synthesized claims against source evidence, design registrations, backup preservation, and untouched runtime assets. For newly composed coding standards, confirm `common` contains nonempty arrays of English requirements grouped by concern, `languages` contains exactly the selected profiles, and each profile has its own formatting, naming, documentation, rules and official sources. For preserved standards, compare bytes with the saved original. Report language selection and existing-tool precedence; the verifier only checks this document's presence when registered and JSON readability, not coding-style compliance. The verifier does not perform semantic checks for the model.
3. **Bounded repair:** fix only generated/managed assets within the authorized scope, then re-run affected checks. Allow at most 3 repair passes; stop earlier if the same blocker persists twice or repair needs new authority/facts. Preserve partial work and report the exact blocker; never restart migration or relax a hard gate to obtain success.
4. **Report:** separate generated files, mechanical results, semantic evidence, and unverified runtime/human acceptance. List primary entrypoints and synthesized designs. Do not promise token/latency savings without measurements.

## 5. Preserving Upgrade Pipeline

Upgrade runs only when this skill is invoked for the target; it is not a background service.

1. Apply the backup Git exclusion above, then snapshot managed governance files into a fresh `_adflow_backup/upgrade_snapshot/<run_id>/` directory.
2. Refresh managed `AGENTS.md` rules from the template and preserve project-specific rules from all distinct agent files as in Step 4, leaving their snapshots intact. Retain the previous initialization marker at this step; do not publish the new version yet.
3. Refresh the 10 directory README guidelines while preserving project content, especially the design module matrix.
4. Synchronize standards and verifier copies using Step 6. Move existing coding standards to `docs/standards/coding.json` byte-for-byte; preserve custom C/T template fields when relocating them. If old and canonical copies differ, report the preservation conflict before replacing either. Refresh managed template defaults in their established Chinese language; keep coding specifications in English. Do not translate existing business cards, custom rules or quotations. Retain project guide content and established guide filenames; update links/indexes to the actual files. Merge `docs/index.json.standards` without replacing other fields; remove an obsolete managed coding pointer only after its canonical target is verified. Retire and physically delete legacy template copies (`docs/devel/change/template.json`, `docs/devel/task/template.json`) after snapshot, reference updates and canonical validation, ensuring `docs/devel/{change,task}` contain only active cards, README, and index.json. Leave business cards and their `gate` blocks unchanged.
5. After managed assets are synchronized, set the canonical tag and `docs/index.json.adflow_version` to `1.3.0`, preserving other index fields; re-read both to verify agreement. These writes are not atomic across files. If interrupted between them, report the version conflict read-only rather than guessing which version to trust.
6. Run the Step 8 evaluation/repair loop **without `--record`**. Existing-card violations are reported, not automatically rewritten. Report the specification synchronization and any unresolved existing-project findings separately; do not declare the project fully compliant when checks fail.

New diagnostic coverage remains `ADVISORY` in this version. Promoting it to a hard requirement needs a separately documented applicability/migration decision; do not impose it retroactively merely because the skill was updated.
