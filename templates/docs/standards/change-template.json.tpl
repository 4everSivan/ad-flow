{
  "$schema": "https://ad-flow.org/schemas/change-card.v1.json",
  "id": "C[001~999]",
  "title": "Describe the change",
  "version": "",
  "type": "BugFix",
  "status": "draft",
  "branch": "fix/C[001~999]-[short-desc]",
  "is_hotfix": false,
  "target": {
    "module": "ModuleName",
    "component": "ComponentName",
    "design_doc": "docs/devel/design/01-core-service.md",
    "design_topic": "CoreService"
  },
  "why": "Explain the observed failure, root cause and reason for this change.",
  "precheck": {
    "description": "Check whether the defect is already fixed or the documented skip condition holds.",
    "command": "",
    "expected": "",
    "is_completed": false,
    "evidence": ""
  },
  "callback": {
    "before": [
      "# Replace with authorized environment checks, branch preparation or snapshots."
    ],
    "after": [
      "# Replace with applicable formatting, lint, regression or build checks.",
      "scripts/adflow-verify  # Closure preflight: use --card <id> --to <state> --record; sync states only after Exit 0."
    ]
  },
  "changes": [
    {
      "scope": "API contract / business rule / failure behavior",
      "before": "Previous behavior",
      "after": "New behavior",
      "impact": "Affected callers or business behavior"
    }
  ],
  "design": {
    "doc": "docs/devel/design/01-core-service.md",
    "topic": "CoreService",
    "modified": true,
    "rule_diff": {
      "before": "Previous design rule",
      "after": "Updated design rule"
    }
  },
  "verification": {
    "result": null,
    "run_id": "",
    "user_quote": "",
    "signoff": "",
    "checks": [
      {
        "item": "Automated regression",
        "true_if": "Relevant tests, including the targeted regression, pass with exit code 0.",
        "false_if": "A relevant test fails or the required regression coverage is missing.",
        "evidence": "",
        "result": null
      },
      {
        "item": "Observed behavior",
        "true_if": "Observed results satisfy the declared behavior and acceptance conditions.",
        "false_if": "Observed behavior violates a declared acceptance condition.",
        "evidence": "",
        "result": null
      },
      {
        "item": "Impact assessment",
        "true_if": "Checks of affected callers and neighboring behavior detect no regression.",
        "false_if": "An affected caller or neighboring behavior regresses.",
        "evidence": "",
        "result": null
      }
    ]
  },
  "rejections": [],
  "sync": {
    "design_pinned": false,
    "changelog": false,
    "commit": "",
    "tag": ""
  },
  "gate": {
    "tool": "adflow-verify",
    "version": "1.2.0",
    "ran_at": "",
    "exit_code": null
  }
}
