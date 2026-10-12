# Todo Buffer

> **created**: YYYY-MM-DD | **last-change**: YYYY-MM-DD | **status**: active

## 1. Purpose

This directory buffers defects, ideas and technical debt that have no registered card. Existing-card progress, blockers and acceptance remain on that card rather than being duplicated here.

## 2. Index

| Entry | Input | Destination |
|---|---|---|
| [now.md](now.md) | Current defects, experience or parameter adjustments | C card or current-stage T card |
| [future.md](future.md) | Future capabilities, debt and unclear directions | Register, defer or discard after review |
| [C track](../change/README.md) | Concrete repairs and rule differences | C card and change index |
| [T track](../task/README.md) | Capabilities and dependencies | T card and task index |

## 3. Buffer Rules

- Record only unregistered work: symptom/direction, module, date and necessary context. Keep unknown causes or target versions explicit.
- When a real C/T card is created and registered, physically remove the matching todo row in the same operation. Do not remove the row before its card is registered.
- Do not retain rows marked completed or registered. Cards, indexes and Git preserve history. Rejection/rework continues on the existing C card.
- Drafting or approving a design alone does not register execution; keep the item until its card exists in the index.

## 4. Review and Routing

1. Check existing todo and C/T indexes before recording an item; continue its existing card if one exists.
2. Once execution conditions are clear, complete the design, create/register the proper card and remove the original row.
3. Before release, review both buffers: registered items must be absent; unregistered items may be registered, deferred or discarded. Zero sediment does not require every unregistered item to disappear.
4. Run `scripts/adflow-verify --json` from the project root and inspect semantic duplicates manually; the tool cannot recognize every reworded item.
