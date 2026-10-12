# Change and Verification Pool

> **created**: YYYY-MM-DD | **last-change**: YYYY-MM-DD | **status**: active

## 1. Purpose

C cards record defect fixes, callbacks, parameter/contract changes and refactoring: cause, before/after differences, impact and evidence. Capability delivery follows the [T track](../task/README.md).

Use this project's assets directly. Shared paths, authority, gate meanings and repair limits are in [Documentation](../../README.md).

## 2. Index

| Entry | Purpose | Maintenance |
|---|---|---|
| [Change template](../../standards/change-template.json) | Copy to create a real C card | Replace placeholders at registration |
| [index.json](index.json) | `cards` routes and `topics` design associations | Registration, transitions and archiving |
| [Design center](../design/README.md) | Concrete baseline text and topics | Before registration and rule writeback |
| [Todo](../todo/README.md) | Work not yet registered | Remove its row after registration |
| [Archive](../../archive/README.md) | Released batch history | After closure and release prerequisites |

## 3. Registration and State Rules

Allocate the next ID, such as `C001`, from the current index including archived registrations; do not reset IDs per release. Maximum +1 is not an atomic reservation. Check `ID_DUPLICATE` and Git conflicts before merging; repair conflicting IDs/references without replacing another item.

| Fields | At registration | At closure |
|---|---|---|
| Identity/context | `id`, `title`, real batch `version`, execution `branch` | Match the index |
| `target` / `design` | Module/component, concrete design/topic and whether rules change | Required text updates and `rule_diff` |
| `why` / `changes` | Failure, cause, differences and impact | Correct to observed behavior |
| `precheck` / `callback` | Applicable checks and authorized commands | Actual results and executed callbacks |
| `verification` | Defined `true_if`/`false_if`, results initially `null` | Actual evidence, run ID, result, human quotation and signoff |
| `sync` / `gate` | Template defaults | Real commit/writeback facts and tool-recorded gate |

Design paths are project-root relative, reference concrete baseline text rather than a README/standard/template, and match `<!-- @topic: TopicName -->`. Necessary command/evidence paths do not violate source-impact decoupling.

| State | Meaning |
|---|---|
| `draft` / `pending` | Being defined or waiting |
| `in_progress` | Repair and evidence in progress |
| `rejected` | Explicit human rejection; audit retained for same-card rework |
| `verified` | Business checks, human confirmation and state preflight passed |
| `closed` | Authorized merge, required writeback and CHANGELOG completed; closure preflight passed |

## 4. Execution and Closure

1. **Register:** copy the template into this pool, define the contract and register the path/state in `index.json.cards`. Remove its matching todo row in the same operation.
2. **Check and repair:** run authorized `precheck.command`. If already fixed, retain evidence and skip duplicate coding, not verification. Otherwise execute applicable callbacks, implement and add targeted regression coverage.
3. **Verify and confirm:** compare each condition with actual commands/results, using a numeric or `local-YYYYMMDD-HH` run ID. Report all business checks; only after explicit human confirmation record the actual `user_quote` and signoff attribution.
4. **Preflight `verified`:** keep current card/index states while running the command below. After Exit 0 set both to `verified` and run ordinary verification.

Examples use `C001`; substitute the actual ID and run from the project root:

```bash
scripts/adflow-verify --card C001 --to verified --record
```

5. **Merge and write back:** merge only when authorized. Record the actual `sync.commit` and verify HEAD ancestry. Update changed design rules and root CHANGELOG `[Unreleased]`, including topic associations; reflect actual `sync.design_pinned` and `sync.changelog` facts.
6. **Preflight `closed`:** after prerequisites are satisfied, run the command below. After Exit 0 synchronize both states to `closed` and recheck. Do not invent `sync.tag`.

```bash
scripts/adflow-verify --card C001 --to closed --record
```

After each successful preflight and state update run `scripts/adflow-verify --json`. Recording updates only the selected real `gate`, not states or human acceptance. Follow [shared verification rules](../../README.md#4-verification-and-closure); do not edit gate values to erase failure.

**Rejection:** synchronize the card/index to `rejected` after an explicit rejection, append date/reason/rework actions to `rejections`, and continue repair, evidence and confirmation on the same card. Do not create a replacement ID or return it to todo.

**Hotfix:** authorized S1/P0 recovery may precede paperwork. Mark `is_hotfix: true` and finish the card, checks, required design updates and CHANGELOG within 24 hours of recovery. Urgency does not authorize deployment, push or signoff.
