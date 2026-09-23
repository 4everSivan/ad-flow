{
  "$schema": "https://ad-flow.org/schemas/adflow-config.v1.json",
  "project_name": "MyProject",
  "version": "1.0",
  "doc_root": "docs/devel",
  "archive_root": "docs/archive",
  "enforcement": {
    "require_change_card": true,
    "zero_sediment": true,
    "require_evidence_anchors": true,
    "forbid_concrete_paths_in_cards": true
  },
  "topics": [
    "CoreModule",
    "AuthService",
    "DataEngine"
  ],
  "test_suites": {
    "unit": "pytest",
    "e2e": "npm run test:e2e"
  }
}
