# Documentation

> **created**: YYYY-MM-DD | **last-change**: YYYY-MM-DD | **status**: active

## 1. Purpose

This is the documentation entrypoint and the home of shared conventions. Designs describe approved business rules; C/T cards record execution and acceptance; guides explain operations; archives preserve history.

After initialization, use this project's [AGENTS.md](../AGENTS.md), READMEs, indexes, templates and verifier. Invoke `$ad-flow` again only to synchronize governance specifications.

## 2. Index

| Goal | Entry | Route or record | Deliverable |
|---|---|---|---|
| Write or review code | [Coding standards](standards/coding.json) | Common and selected language requirements | Code, comments and API documentation consistent with project conventions |
| Create a change card | [Change template](standards/change-template.json) / [Change pool](devel/change/README.md) | [Change index](devel/change/index.json) | C card, evidence and applicable design updates |
| Create a task card | [Task template](standards/task-template.json) / [Task pool](devel/task/README.md) | [Task index](devel/task/index.json) | T card, dependencies and capability acceptance |
| Understand or revise design | [Design center](devel/design/README.md) | [Development index](devel/index.json) | Concrete design text and matching `@topic` |
| Buffer unregistered work | [Todo pool](devel/todo/README.md) | `now.md` / `future.md` | Brief problem or direction |
| Prepare or troubleshoot an environment | [Guides](guide/README.md) / [Environment](devel/env/README.md) | [Guide index](guide/index.json) | Applicable procedures and observed results |
| Store documentation media | [Assets](assets/README.md) | Relative document links | Reusable media |
| Release or trace history | [Archive](archive/README.md) | Current C/T index routes | Batch cards and optional index snapshots |

The machine entrypoint is [index.json](index.json). Its `standards` object routes the three reusable standards/template files. `standards/` needs no separate README or index. Actual designs and cards remain under `devel/`.

## 3. Shared Conventions

### 3.1 Metadata and Versions

Use English for newly generated template content and lowercase metadata keys. Preserve user quotations, custom rules and historical evidence verbatim. Dates are real `YYYY-MM-DD` values:

```markdown
# Document title

> **created**: YYYY-MM-DD | **last-change**: YYYY-MM-DD | **status**: draft
```

Keep `created` stable and update `last-change` for substantive edits. Use one status such as `draft`, `active`, `baseline` or `deprecated`; explain approval and applicability in the body. Todo files use their shorter headers.

Project releases use Git tags and [CHANGELOG.md](../CHANGELOG.md). C/T `version` is the real release batch. Designs do not increment isolated document versions. `docs/index.json.adflow_version` tracks governance separately.

### 3.2 Paths, Topics and Indexes

- Resolve Markdown navigation and media relative to the containing document.
- Card design paths, current index `file` routes, `topics[TopicName].design_doc` and top-level `standards` paths are project-root relative. Guide `guides[].file` paths are relative to `docs/guide/`.
- Design links must target concrete design text with a matching `<!-- @topic: TopicName -->`, never a README, coding standard or card template.
- Cards describe source impact with `module`, `component` and `capability`; commits trace changed source files. Necessary paths in commands, design references and evidence are allowed.
- Synchronize cards and index states/routes on registration, transition and archiving. Keep historical IDs and increment across releases.

### 3.3 Facts, Authority and Protection

An approved design does not prove implemented capability. T cards track unfinished delivery; actual code and acceptance evidence support completion claims. Unapproved designs remain `draft`.

Continue authorized work. A card or guide does not itself authorize deployment, push, merge, cleanup or signoff. Verify existing instances against the deployment report and current runtime. Keep outputs under `local/`; AI must not delete/reset its existing contents. Captured backup snapshots remain read-only.

## 4. Verification and Closure

Run from the project root:

```bash
# Initialization/synchronization: files, registered standards, JSON and versions
scripts/adflow-verify --mode init --json

# Daily discipline: active cards and global prerequisites
scripts/adflow-verify --json
```

| Result | Meaning | Required response |
|---|---|---|
| Exit 0 | Covered structural/process checks passed | Still verify business acceptance and operation authority |
| Exit 4 | Deterministic governance violation | Repair and recheck; blocks affected closure/merge/archive |
| Exit 6 | Existing warning or evidence gap needs disposition | Resolve the facts; formal closure still needs Exit 0 |
| `ADVISORY` | Nonblocking observation | Report separately without inventing a new gate |

For transitions, follow the C/T README's `--card ... --to ... --record` command. It preflights the state in memory and records only the selected card's real `gate`; after Exit 0, synchronize card/index states and run ordinary verification. Unscoped recording writes all active gates; specification upgrades never use it.

Recording re-evaluates the selected card's actual prerequisites rather than failing solely on its old receipt. Other cards and global violations still apply. Do not manually change `gate.exit_code` to zero, or use `--warn-only` as formal success.

Repair locally within authorized scope, at most three passes; stop dependent work if the same blocker persists twice or facts/authority are missing. Report structure, business tests, runtime and human acceptance separately. The verifier checks standard-file routing/readability, not source style or comment quality.
