{
  "$schema": "https://ad-flow.org/schemas/task-card.v1.json",
  "id": "T[01~99]",
  "title": "Describe the task goal",
  "version": "",
  "milestone": "M[1~99]-MilestoneName",
  "status": "pending",
  "branch": "feat/T[01~99]-[short-desc]",
  "depends_on": [],
  "target": {
    "module": "ModuleName",
    "design_doc": "docs/devel/design/01-core-service.md",
    "design_topic": "CoreService"
  },
  "goal": "Describe the domain capability and business outcome to deliver.",
  "precheck": {
    "description": "Check whether the capability is already implemented and satisfies the completion criteria.",
    "command": "",
    "expected": "",
    "is_completed": false,
    "evidence": ""
  },
  "callback": {
    "before": [
      "# Replace with authorized environment checks, branch preparation or fixture setup."
    ],
    "after": [
      "# Replace with applicable formatting, static analysis, tests or build checks.",
      "scripts/adflow-verify  # Completion preflight: use --card <id> --to completed --record; sync states only after Exit 0."
    ]
  },
  "tasks": [
    {
      "id": "T01-1",
      "title": "Subtask title",
      "capability": "Describe a capability, data contract or interface to deliver.",
      "done": false
    }
  ],
  "acceptance": {
    "result": null,
    "run_id": "",
    "checks": [
      {
        "item": "Architecture boundaries",
        "true_if": "The implementation follows the declared layering and dependency direction.",
        "false_if": "The implementation introduces a prohibited cross-layer dependency.",
        "evidence": "",
        "result": null
      },
      {
        "item": "Business rule coverage",
        "true_if": "All required business scenarios are covered by meaningful checks.",
        "false_if": "A required scenario or boundary lacks a meaningful check.",
        "evidence": "",
        "result": null
      }
    ]
  },
  "sync": {
    "commit": ""
  },
  "gate": {
    "tool": "adflow-verify",
    "version": "1.2.0",
    "ran_at": "",
    "exit_code": null
  }
}
