# Release and Milestone Archive

> **created**: YYYY-MM-DD | **last-change**: YYYY-MM-DD | **status**: active

## 1. Purpose

Archive C/T cards from released batches or closed milestones. Freeze card contents and states; current indexes continue to route historical IDs and dependencies. Current designs remain under `docs/devel/design/`.

Archiving belongs to an authorized release/closure operation. Card completion does not authorize tagging, push or deployment.

## 2. Index

| Entry or location | Contents | Maintenance |
|---|---|---|
| [Current change index](../devel/change/index.json) | Active/historical C cards and topic routes | Keep registrations; update `file` when archived |
| [Current task index](../devel/task/index.json) | Active/historical T cards, milestones and dependencies | Keep registrations; update `file` when archived |
| `<version>/change/` | This batch's `closed` C cards and optional index snapshot | Read-only after archiving |
| `<version>/task/` | This batch's `completed` T cards and optional index snapshot | Read-only after archiving |

### Archived Batches

| Release or milestone | Path | Archived on | Scope |
|---|---|---|---|

Register only actual archived batches. Do not pre-create sample releases or cards.

## 3. Archiving Rules

- Select cards by their real `version` and release scope: C cards must be `closed`, T cards `completed`. Leave other batches and unfinished work active.
- Complete required build/test/release acceptance, todo review and CHANGELOG/version alignment. Ordinary verification must return Exit 0 before archiving.
- Moving a card must not rewrite its state, acceptance, commit or gate. Later corrections use current designs/new cards rather than changing historical evidence.
- Retain IDs, topics and dependencies in current indexes; update actual routes only. Archived index snapshots never replace current routing.
- Inspect every destination before moving. Resolve existing-name collisions without overwriting; archiving does not itself require design edits or renumbering.

## 4. Archive a Batch

All paths are project-root relative; replace `<version>` with the real batch.

1. **Confirm scope and destinations:** list selected IDs and original paths, inspect destinations, then create `docs/archive/<version>/change/` and `task/`. Exclude other batches.
2. **Move terminal cards:** move only selected cards, preserving bytes and checking counts. Never overwrite a destination.
3. **Update current routes:** change `cards[Cxxx].file` or `tasks[Txx].file`, for example to `docs/archive/<version>/task/T01.json`. Preserve an existing `cards` task-index structure. Save optional index snapshots in the batch directory, then register the batch above.
4. **Verify and freeze:** run ordinary verification, trace design topic to current index to archived card, and check ID/status/dependency reachability. Confirm card bytes and baseline text did not change.

```bash
scripts/adflow-verify --json
```

Future tasks may use an archived prerequisite's `completed` status through current routing. The tool checks existence, identity and status without reaccepting or rewriting archived cards. Post-archive Exit 0 does not replace pre-archive business acceptance.

If interrupted, retain completed moves and repair remaining routes to actual paths rather than repeating all moves. Build outputs, runtime data and reports stay in `local/`; archiving does not authorize cleanup of `local/` or `_adflow_backup/`.
