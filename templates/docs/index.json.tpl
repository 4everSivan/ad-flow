{
  "$schema": "adflow-docs-index-v1",
  "project": "MyProject",
  "adflow_version": "1.2.0",
  "created": "YYYY-MM-DD",
  "last_change": "YYYY-MM-DD",
  "status": "active",
  "description": "Project documentation routes and responsibilities.",
  "directories": [
    {
      "name": "assets",
      "path": "docs/assets",
      "description": "Documentation diagrams, screenshots and reusable media.",
      "readme": "docs/assets/README.md",
      "index": null
    },
    {
      "name": "guide",
      "path": "docs/guide",
      "description": "Usage, local deployment and troubleshooting instructions.",
      "readme": "docs/guide/README.md",
      "index": "docs/guide/index.json"
    },
    {
      "name": "devel",
      "path": "docs/devel",
      "description": "Design baselines, change cards, task cards, todo buffers and environment guidance.",
      "readme": "docs/devel/README.md",
      "index": "docs/devel/index.json"
    },
    {
      "name": "archive",
      "path": "docs/archive",
      "description": "Read-only cards and snapshots from released batches.",
      "readme": "docs/archive/README.md",
      "index": null
    }
  ],
  "standards": {
    "coding": "docs/standards/coding.json",
    "task_template": "docs/standards/task-template.json",
    "change_template": "docs/standards/change-template.json"
  }
}
