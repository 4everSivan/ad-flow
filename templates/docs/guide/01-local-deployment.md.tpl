# Local Deployment

> **created**: YYYY-MM-DD | **last-change**: YYYY-MM-DD | **status**: active

Replace examples with commands and prerequisites established from this project's actual manifests, scripts and environment. Mark unsupported or unverified steps; projects without a deployable service describe their real execution method.

## 1. Prerequisites and Configuration

Record supported platforms/runtime versions, dependency setup, working directory, required configuration and port/data isolation. Do not assume every project supports macOS/Linux or uses a database.

Inject secrets through ignored configuration/environment. The following is an example only; use the project's actual parameter names and paths:

```sh
PORT=8080
DB_PATH=local/data/app.db
LOG_PATH=local/logs/app.log
```

All build/package outputs, runtime data and logs belong under `local/`. Inspect existing data before authorized startup and never reset it implicitly.

## 2. Build and Start

Use the actual toolchain. Examples of output isolation, applicable only to corresponding project commands:

```sh
# Frontend example; the script must support this option.
npm run build -- --outDir local/dist

# Go example; substitute the actual main package.
go build -o local/bin/app ./cmd/app

# Python distribution example; use the project's build environment.
python -m build --outdir local/dist
```

Document dependency installation, configuration, launch, stop/restart and health commands supported by this project. Label expected exits and observable output, known failures and actual recovery steps. Generic examples do not authorize deployment or prove support.

## 3. Deployment Report

After an actual deployment, create/update `local/deploy_report.md` with observed facts. This is the report structure, not sample acceptance:

```markdown
# Deployment Report

| Observation | Actual value |
|---|---|
| Recorded at | Actual timestamp |
| Branch / commit / release | Actual identifiers |
| Start command and process management | Actual command and PID/service |
| Listening ports | Observed listeners |
| Data and log paths | Actual paths |
| Health command and result | Actual command, exit and response |
| Remaining limitations | Untested conditions or manual work |
```

Redact secrets, mark inapplicable fields and distinguish expected output from actual evidence.

## 4. Existing Instances and Changes

For tests, restarts or redeployment involving an existing instance, locate it through the report and verify current runtime. If absent/stale, investigate with this guide and actual environment. Pause changes when required runtime parameters remain unknown.

Refresh the report after an authorized restart or configuration change; update the guide if the supported procedure changes. Isolated unit tests do not require this report. Initialization/governance upgrades leave existing `local/` untouched; AI must not delete or reset its contents.
