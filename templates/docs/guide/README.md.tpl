# Usage and Deployment Guides

> **created**: YYYY-MM-DD | **last-change**: YYYY-MM-DD | **status**: active

## 1. Purpose

Explain usage, setup, integration, deployment and troubleshooting through prerequisites, commands and observable results. Architecture belongs in [Design](../devel/design/README.md); cache maintenance follows [Environment](../devel/env/README.md).

Guides describe methods; `local/deploy_report.md` records an actual operation. Current runtime verifies whether the report remains valid. Isolated unit tests require neither deployment nor a report.

## 2. Index

| Document | ID | Purpose | Applicable environment | Actual artifact |
|---|---|---|---|---|
| [Local deployment](01-local-deployment.md) | GUIDE-DEPLOY | Local setup, usage/service lifecycle and health checks | Actual platform and dependencies | `local/deploy_report.md` after real deployment; non-service projects describe actual usage |

The [machine index](index.json) resolves `guides[].file` relative to this directory. Register actual guides and applicability; do not invent databases or services to fill a template.

## 3. Writing Rules

Follow [shared metadata and paths](../README.md). Include applicable details without another approval/report template:

| Content | Required information | Evidence |
|---|---|---|
| Prerequisites | Platforms, versions, dependencies, working directory and configuration | Source, project scripts and actual environment |
| Commands | Exact parameters, sources, sequence and scope | Distinguish examples from real operations; explain substitutions |
| Success | Exits, expected output, health or observable behavior | Label expectations; attribute actual output to a run |
| Failure handling | Known errors, diagnosis, stop/recovery procedure | Actual supported capabilities, not an invented rollback |

- Exclude secrets and sensitive addresses; explain injection while retaining reproducible non-sensitive parameters.
- Keep generated outputs/logs/data under `local/`; do not overwrite data or delete evidence to retry.
- Commands grant no authority. Continue existing authorized work; deployment, push and cleanup retain their actual scope boundaries.
- Update routing/applicability when a guide changes and label untested platforms/steps explicitly.

## 4. Execution and Runtime Evidence

1. Read the relevant guide. For existing instances, locate them through the deployment report and verify processes, listeners, configuration and data paths; investigate absent/stale reports.
2. Run applicable authorized commands in sequence and retain real failures. Pause instance changes dependent on unknown parameters while continuing independent checks.
3. After actual deployment/restart/configuration changes, record time, version/commit, launch command, process management, ports/data paths, logs and health results in `local/deploy_report.md`. Redact secrets and mark inapplicable fields.
4. Verify runtime and update the guide/index or C/T evidence when needed. A report describes one operation and does not replace later runtime checks or human acceptance.

AI must not delete/reset existing `local/`. Service shutdown, data reset and cache maintenance retain their distinct authorization and [environment rules](../devel/env/README.md).
