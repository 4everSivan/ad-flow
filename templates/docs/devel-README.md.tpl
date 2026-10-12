# Development

> **created**: YYYY-MM-DD | **last-change**: YYYY-MM-DD | **status**: active

## 1. Purpose

`docs/devel/` organizes designs, execution records and maintenance. Identify the appropriate track, then read its design, template and index. Daily work does not require `$ad-flow`.

Shared metadata, paths, authority and gates are in [Documentation](../README.md); collaboration rules are in [AGENTS.md](../../AGENTS.md). Reusable standards and card templates live in `docs/standards/`.

## 2. Index

| Entry | Contents | When to use |
|---|---|---|
| [Coding standards](../standards/coding.json) | Common and language requirements, including comments | Before coding/review |
| [Change template](../standards/change-template.json) / [Task template](../standards/task-template.json) | Reusable C/T schemas and placeholders | Registering real work |
| [Design](design/README.md) | Overall/module rules, topics and evolution | Understanding or revising behavior |
| [Change](change/README.md) / [Index](change/index.json) | Repairs, differences and evidence | Defects, callbacks, parameter changes and refactoring |
| [Task](task/README.md) / [Index](task/index.json) | Capabilities, milestones and dependencies | Features and module delivery |
| [Todo](todo/README.md) | Work not yet registered as a card | Unclear facts or execution conditions |
| [Environment](env/README.md) | Inventory, dependencies and recovery | Environment preparation/maintenance |
| [Archive](../archive/README.md) | Read-only released cards and snapshots | Release or historical trace |

Machine routing is in [index.json](index.json), with standards routed by [docs/index.json](../index.json). Register only actual assets; keep new design/card/todo collections empty.

## 3. Development Rules

- Read the coding standard's common and selected language requirements, especially API contracts and comments. Existing project/tool configuration takes priority; avoid unrelated reformatting.
- Use C cards for concrete fixes and differences, and T cards for capability delivery and dependencies. Do not duplicate one execution item across tracks.
- Link a concrete design and matching `@topic`; write missing design text before registration. README files only navigate and explain operations.
- Distinguish approved rules, implemented code, tests and human acceptance. T cards track approved capability that is still unimplemented.
- Copy the appropriate `docs/standards/*-template.json`, define the batch, branch, goal and acceptance conditions, then register it. Remove a matching todo row only after registration.
- Synchronize card/index states and inspect ID collisions, dependencies and routes before merging or archiving.

## 4. Daily Sequence

| Stage | C track | T track |
|---|---|---|
| Define | Identify failure, cause and rule difference | Define capability, design and completion conditions |
| Register | Create C card and `verification.checks` | Create T card, `tasks[]`, dependencies and acceptance checks |
| Implement | Authorized prechecks/callbacks, repair and regression | Start after dependencies complete, then deliver and test |
| Accept | Human confirmation, `verified` preflight; merge/writeback, `closed` preflight | Required acceptance and `completed` preflight |
| Archive | This released batch's `closed` cards | This released batch's `completed` cards |

See [Change operations](change/README.md) and [Task operations](task/README.md) for commands, evidence and exceptions. After Exit 0 synchronize states and run ordinary verification. Card completion does not authorize push, deployment or release.

Follow [Archive operations](../archive/README.md) for released batches. Current indexes retain IDs and update routes. Future tasks may depend on completed archived tasks; archived card bytes remain frozen.
