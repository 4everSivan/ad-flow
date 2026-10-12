# Task Pool

> **created**: YYYY-MM-DD | **last-change**: YYYY-MM-DD | **status**: active

## 1. Purpose

T cards turn approved designs into executable, verifiable capabilities; `depends_on` defines prerequisites. Cards distinguish approved plans from delivered capabilities. Concrete defect repairs follow the [C track](../change/README.md).

Shared paths, authority, gates and repair limits are in [Documentation](../../README.md). Daily work does not require the skill source directory.

## 2. Index

| Entry | Purpose | Maintenance |
|---|---|---|
| [Task template](../../standards/task-template.json) | Copy to create a real T card | Milestone breakdown and registration |
| [index.json](index.json) | `tasks` routes, `milestones` and `topics` | Registration, transitions and archiving |
| [Design center](../design/README.md) | Design/topic and delivery boundaries | Before task breakdown |
| [Todo](../todo/README.md) | Directions not yet registered | Remove its row after registration |
| [Archive](../../archive/README.md) | Completed historical dependencies | Dependency inspection or batch release |

If an existing task index uses `cards`, preserve that structure; specification synchronization does not migrate historical records.

## 3. Registration and Dependencies

Allocate the next ID, such as `T01`, from the index including historical registrations; do not reset per release. IDs are not atomic reservations. Before merging parallel work check duplicates and Git conflicts; update subtask IDs, index entries and dependency references together without overwriting another item.

| Fields | At registration | At completion |
|---|---|---|
| Identity/plan | `id`, `title`, real batch `version`, `milestone`, `branch` | Match the index |
| `target` / `goal` | Concrete design/topic and capability boundary | Correct to actual delivery |
| `tasks[]` / `depends_on` | Capability units, `done: false`, prerequisite IDs | Truthful completion state |
| `precheck` / `callback` | Applicable completion check and authorized commands | Actual results |
| `acceptance` | Defined `true_if`/`false_if`, results initially `null` | Evidence, run ID and acceptance results |
| `sync` / `gate` | Template defaults | Actual ancestor `sync.commit` and tool-recorded gate |

`target.design_doc` is project-root relative and targets concrete text with the matching `@topic`, never a README/standard/template. `tasks[].capability` describes behavior, data contracts or interfaces, not a source-file checklist.

| State | Meaning | Prerequisite |
|---|---|---|
| `pending` | Waiting | Goal, design and acceptance registered |
| `in_progress` | Delivering | All prerequisites `completed`; scope clear |
| `completed` | Accepted and preflight passed | Business acceptance, traceable commit and synchronized index |

Resolve dependencies through current index `file` routes, checking existence, ID and status. Completed archived tasks are valid prerequisites. Read archived cards without reaccepting or rewriting them. Clarify missing, incomplete or cyclic dependencies before treating a task as ready.

## 4. Execution and Completion

1. **Design and register:** break the design into capability/milestone cards and register them. Remove matching todo rows after registration, not merely after design approval.
2. **Choose ready work:** select `pending` tasks whose prerequisites are all `completed`; synchronize card/index to `in_progress`.
3. **Check and implement:** run authorized prechecks/callbacks. An already implemented capability may skip duplicate coding with evidence, while retaining acceptance. Otherwise implement and test the capability.
4. **Accept:** verify `tasks[].done` and every business acceptance check with actual commands, outputs and a run ID. Complete project-required human acceptance. `ADVISORY` neither replaces business judgment nor introduces a new hard gate.
5. **Preflight completion:** record the actual ancestor `sync.commit`; retain current states while running the command below. After Exit 0 synchronize both to `completed`, then run ordinary verification.

Examples use `T01`; substitute the actual ID and run from the project root:

```bash
scripts/adflow-verify --card T01 --to completed --record
```

After a successful preflight and state update run `scripts/adflow-verify --json`. Recording writes only the real gate, not states or proof of delivery. Follow [shared verification rules](../../README.md#4-verification-and-closure); do not rewrite evidence, conditions or dependencies to bypass failure.

6. **Release a batch:** complete required integration/build/release acceptance and update root CHANGELOG. When release is authorized, follow [Archive operations](../../archive/README.md). A completed task does not automatically authorize release, deployment or push.
