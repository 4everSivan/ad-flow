# Documentation Assets

> **created**: YYYY-MM-DD | **last-change**: YYYY-MM-DD | **status**: active

## 1. Purpose

Store architecture diagrams, flows, prototypes, screenshots and reusable demonstration media referenced by documentation. Maintain media together with its explanation and reachable links.

Runtime-loaded assets retain their actual build-contract locations. Build outputs, temporary debugging captures, raw logs and one-run reports belong in the project's `local/` output area.

## 2. Index

| Category | Example prefix | Contents | Preferred formats |
|---|---|---|---|
| Architecture/flow | `arch-` / `flow-` | Relationships, sequences, data flow and topology | SVG, PNG |
| Prototype/interface | `ui-` / `app-` | Interaction designs and observed interfaces | PNG, WebP, JPG |
| Documentation branding | `logo-` / `icon-` | Documentation identifiers and icons | SVG, PNG |
| Reusable demos/evidence | `demo-` / `evidence-` | Selected explanatory or inspectable media | PNG, WebP, GIF |

These categories aid naming; they do not require pre-created directories or another machine index.

## 3. Asset Rules

- Use descriptive lowercase hyphenated names, such as `arch-system-overview.svg` or `ui-login-error.png`, rather than generic screenshot names.
- Prefer vectors for diagrams/icons; compress raster images and normally keep each image below 2 MB. Use project-approved external storage for large videos or design source files.
- Check source and applicability, redact secrets/personal data and label mocks/prototypes/illustrations. They cannot substitute for observed runtime evidence.
- Resolve Markdown media relative to the current document and provide meaningful alternative text. Update captions when media or behavior changes.

Syntax examples only; replace with actual assets:

```markdown
<!-- In docs/README.md -->
![System modules](assets/arch-system-overview.svg)

<!-- In docs/devel/design/01-module.md -->
![Module call flow](../../assets/flow-module-call.svg)
```

## 4. Updates and Cleanup

1. Identify the consuming document, use a semantic name and add a real reference. Keep the actual drawing source or source link when reproduction is needed.
2. Before moving/replacing assets, inspect current and historical references. Preserve media still referenced by frozen archives; do not rewrite archived cards to hide broken links.
3. Before release, confirm whether unreferenced media is obsolete. Delete only within authorized scope; temporary/runtime evidence follows the protection rules of its output location.
