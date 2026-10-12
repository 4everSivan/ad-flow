{
  "$schema": "adflow-devel-index-v1",
  "project": "MyProject",
  "created": "YYYY-MM-DD",
  "last_change": "YYYY-MM-DD",
  "status": "active",
  "description": "Routes for current design baselines and development records.",
  "subsystems": [
    {
      "name": "design",
      "path": "docs/devel/design",
      "type": "living_baseline",
      "description": "Current design baselines and stable topic anchors.",
      "readme": "docs/devel/design/README.md"
    },
    {
      "name": "change",
      "path": "docs/devel/change",
      "type": "bugfix_and_change_pool",
      "description": "Defect fixes, behavior changes and verification records.",
      "readme": "docs/devel/change/README.md",
      "index": "docs/devel/change/index.json"
    },
    {
      "name": "task",
      "path": "docs/devel/task",
      "type": "milestone_task_pool",
      "description": "Milestone capabilities, dependencies and acceptance records.",
      "readme": "docs/devel/task/README.md",
      "index": "docs/devel/task/index.json"
    },
    {
      "name": "todo",
      "path": "docs/devel/todo",
      "type": "buffer_pool",
      "description": "Unregistered current and future work; remove items after card registration.",
      "readme": "docs/devel/todo/README.md"
    },
    {
      "name": "env",
      "path": "docs/devel/env",
      "type": "environment_governance",
      "description": "Environment inventory, dependency recovery and scoped maintenance.",
      "readme": "docs/devel/env/README.md"
    }
  ]
}
