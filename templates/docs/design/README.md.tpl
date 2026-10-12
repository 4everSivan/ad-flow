# Design Center

> **created**: YYYY-MM-DD | **last-change**: YYYY-MM-DD | **status**: active

## 1. Purpose

Overall and module designs describe business rules, boundaries, interfaces and acceptance criteria. Approved designs form the current baseline; T cards track capabilities still to be delivered. Completion requires actual code and acceptance evidence.

**This README is navigation and an outline, never a valid `design_doc` or `design.doc`.** Cross-cutting changes target the overall design; module changes target concrete module text.

## 2. Index

### 2.1 Document Organization

| Document | Default naming | Responsibility |
|---|---|---|
| Overall design | `00-system-overview.md` | Boundaries, architecture, module matrix and cross-module rules |
| Module design | `01~99-[module-name].md` | Domain requirements, contracts and business rules |
| Execution records | [Change index](../change/index.json) / [Task index](../task/index.json) | Rule changes, delivery, evidence and dependencies |

Preserve established filenames and references in existing projects; English defaults do not rename historical designs automatically.

### Module Matrix

| Document | Topic | Document ID | Responsibility | Status | Last change |
|---|---|---|---|---|---|

Register only generated, source-backed designs here and in [Development index](../index.json). Empty projects keep this matrix empty. Distinguish drafts from approved baselines; examples are not delivered capabilities.

## 3. Maintenance Rules

- Use stable `<!-- @topic: TopicName -->` anchors matching `target.design_topic` exactly. The overall design hosts cross-module topics; modules host domain topics.
- Card design paths are project-root relative. Designs link `[Change index (TopicName)](../change/index.json#TopicName)`; resolve the JSON topic via `topics[TopicName]`.
- Keep current rules self-consistent. Evolution tables summarize IDs, types and rule differences; indexes locate historical cards. Do not link moving card files directly from baseline history.
- When a C card changes rules, compare `design.rule_diff` and update the text. A repair restoring an existing rule need not invent a design change. Register a new domain in the overall design before its module design and T cards.
- Follow [shared metadata](../../README.md). Maintain dates, not isolated design patch versions. Unconfirmed content remains `draft`; record sources and open questions without invented metrics, approvals or acceptance.

## 4. Design Outline

Use four top-level sections. Requirements, architecture, rules, verification, evolution and references fit into relevant subsections. Scale detail to the module; replace bracketed content with real evidence. The overall design omits a link to itself.

```markdown
# [Module Name] Design

> **created**: YYYY-MM-DD | **last-change**: YYYY-MM-DD | **status**: draft

## 1. Purpose

Describe context, module role, sources and approval status.

## 2. Index

- Document ID: DESIGN-[MODULE]
- Overall design: [System overview](00-system-overview.md)
- Topic: TopicName
- Execution history: [Change index (TopicName)](../change/index.json#TopicName)

## 3. Requirements and Contracts

State goals/non-goals, functionality, confirmed constraints, inputs, outputs,
failure conditions and boundaries. Mark unsupported or unresolved targets.

## 4. Design Details

### 4.1 Architecture and Behavior

Describe relationships, data flow and core operations; use diagrams where useful.

### 4.2 Business Rules

<!-- @topic: TopicName -->

Describe domain models, algorithms, interfaces and boundaries.
Cover storage, networking, security or recovery only where relevant.

### 4.3 Verification and Implementation

Define how to verify rules, related T cards, implemented capabilities and open work.
Record conflicting sources and unverified conclusions; plans are not facts.

### 4.4 Rule Evolution

| ID | Type | Summary | Rule change |
|---|---|---|---|

### 4.5 References

List the actual requirements, source locations, protocols or design materials used.
```
