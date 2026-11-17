"""建卡只读计划（A6 试点）的回归用例。"""
import json
import subprocess
import sys
import tempfile
import unittest
from pathlib import Path

REPO = Path(__file__).resolve().parents[1]
TOOL = REPO / "scripts/adflow_verify.py"


class ScaffoldFixture(unittest.TestCase):
    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory()
        self.addCleanup(self.tmp.cleanup)
        self.root = Path(self.tmp.name)
        self.write("AGENTS.md", "<!-- @ad-flow: initialized v1.7.0 -->")
        self.write_json("docs/index.json", {"adflow_version": "1.7.0"})
        self.write("docs/devel/design/01-core.md", "<!-- @topic: Core -->")
        self.write_json("docs/devel/change/index.json", {"cards": {}, "topics": {}})
        self.write_json("docs/devel/task/index.json", {"tasks": {}, "topics": {}})
        self.write("docs/devel/todo/now.md", "| 事项 |\n|---|\n| 修复登录提示 |\n")
        self.write("docs/devel/todo/future.md", "| 事项 |\n|---|\n| 新增导出能力 |\n")
        self.write("CHANGELOG.md", "# Changelog\n")
        self.install_templates()

    def install_templates(self):
        for name in ("change", "task"):
            source = REPO / ("templates/docs/standards/%s-template.json.tpl" % name)
            self.write("docs/standards/%s-template.json" % name,
                       source.read_text(encoding="utf-8"))

    def write(self, rel, text):
        p = self.root / rel
        p.parent.mkdir(parents=True, exist_ok=True)
        p.write_text(text, encoding="utf-8")

    def write_json(self, rel, value):
        self.write(rel, json.dumps(value, ensure_ascii=False))

    def run_plan(self, *args, expect=0):
        result = subprocess.run([sys.executable, str(TOOL), str(self.root),
                                 "--scaffold", "new-card", "--plan", *args],
                                capture_output=True, text=True)
        self.assertEqual(result.returncode, expect, result.stdout + result.stderr)
        return result

    def run_json(self, *args, expect=0):
        result = self.run_plan("--json", *args, expect=expect)
        data = json.loads(result.stdout)
        self.assertEqual(data["exit_code"], expect)
        return data

    def snapshot(self):
        return {str(p.relative_to(self.root)): p.read_bytes()
                for p in self.root.rglob("*") if p.is_file()}


class ScaffoldPlanTests(ScaffoldFixture):
    def test_complete_change_plan_is_executable_and_read_only(self):
        before = self.snapshot()
        data = self.run_json("--design-topic", "Core", "--title", "修复登录提示",
                             "--card-version", "v0.1.0", "--branch", "fix/C001-login",
                             "--todo", "修复登录提示")
        plan = data["scaffold"]
        self.assertTrue(plan["executable"], plan["missing"])
        self.assertEqual(plan["card_id"], "C001")
        self.assertEqual(plan["design"], {"doc": "docs/devel/design/01-core.md",
                                          "topic": "Core", "anchor_ok": True})
        self.assertEqual(plan["writes"][0]["path"], "docs/devel/change/C001.json")
        self.assertEqual(plan["writes"][0]["content"]["status"], "draft")
        self.assertEqual(plan["writes"][0]["content"]["version"], "v0.1.0")
        self.assertEqual(plan["writes"][0]["content"]["target"]["design_doc"],
                         "docs/devel/design/01-core.md")
        self.assertEqual(plan["writes"][1]["collection"], "cards")
        self.assertEqual(plan["writes"][1]["entry"]["C001"]["file"],
                         "docs/devel/change/C001.json")
        self.assertEqual(plan["topics"]["key"], "changes")
        self.assertEqual(plan["todo"], {"path": "docs/devel/todo/now.md", "action": "remove",
                                        "match": "修复登录提示", "present": True})
        self.assertEqual(before, self.snapshot(), "只读计划不得写入任何文件")

        text = self.run_plan("--design-topic", "Core", "--title", "修复登录提示",
                             "--card-version", "v0.1.0", "--branch", "fix/C001-login").stdout
        self.assertIn("写入计划（未落盘）", text)
        self.assertIn("executable=yes", text)

    def test_missing_inputs_are_listed_and_plan_is_not_executable(self):
        data = self.run_json("--design-topic", "Core")
        plan = data["scaffold"]
        self.assertFalse(plan["executable"])
        for label in ("标题", "发布批次", "执行分支"):
            self.assertIn(label, plan["missing"])
        self.assertEqual(data["summary"]["codes"], {})

    def test_topic_without_anchor_cannot_resolve_design(self):
        data = self.run_json("--design-topic", "Missing", "--title", "x",
                             "--card-version", "v0.1.0", "--branch", "fix/C001-x")
        plan = data["scaffold"]
        self.assertFalse(plan["executable"])
        self.assertIsNone(plan["design"]["doc"])
        self.assertTrue(any("未在任何设计文档中命中" in item for item in plan["missing"]),
                        plan["missing"])

    def test_explicit_design_doc_without_anchor_blocks_plan(self):
        data = self.run_json("--design-topic", "Other", "--design-doc",
                             "docs/devel/design/01-core.md", "--title", "x",
                             "--card-version", "v0.1.0", "--branch", "fix/C001-x")
        plan = data["scaffold"]
        self.assertFalse(plan["executable"])
        self.assertFalse(plan["design"]["anchor_ok"])
        self.assertTrue(any("@Other" in item for item in plan["missing"]), plan["missing"])

    def test_unmatched_todo_text_blocks_plan(self):
        data = self.run_json("--design-topic", "Core", "--title", "x",
                             "--card-version", "v0.1.0", "--branch", "fix/C001-x",
                             "--todo", "不存在的待办事项")
        plan = data["scaffold"]
        self.assertFalse(plan["executable"])
        self.assertFalse(plan["todo"]["present"])
        self.assertTrue(any("todo" in item for item in plan["missing"]), plan["missing"])

    def test_task_track_uses_task_ledger_and_milestone(self):
        data = self.run_json("--track", "task", "--design-topic", "Core",
                             "--title", "导出能力", "--card-version", "v0.2.0",
                             "--branch", "feat/T01-export", "--milestone", "M1-导出",
                             "--todo", "新增导出能力")
        plan = data["scaffold"]
        self.assertTrue(plan["executable"], plan["missing"])
        self.assertEqual(plan["card_id"], "T01")
        self.assertEqual(plan["writes"][0]["path"], "docs/devel/task/T01.json")
        self.assertEqual(plan["writes"][0]["content"]["status"], "pending")
        self.assertEqual(plan["writes"][0]["content"]["milestone"], "M1-导出")
        self.assertEqual(plan["writes"][1]["collection"], "tasks")
        self.assertEqual(plan["topics"]["key"], "tasks")
        self.assertEqual(plan["todo"]["path"], "docs/devel/todo/future.md")

    def test_scaffold_read_only_even_when_project_has_findings(self):
        card = {"id": "C009", "status": "pending",
                "target": {"design_doc": "docs/devel/design/README.md", "design_topic": "Core"},
                "verification": {"run_id": "local-20261117-01", "checks": []}}
        self.write_json("docs/devel/change/C009.json", card)
        self.write_json("docs/devel/change/index.json",
                        {"cards": {"C009": {"status": "pending",
                                            "file": "docs/devel/change/C009.json"}},
                         "topics": {}})
        before = self.snapshot()
        data = self.run_json("--design-topic", "Core", "--title", "x",
                             "--card-version", "v0.1.0", "--branch", "fix/C010-x",
                             expect=4)
        self.assertIn("NO_README_AS_DESIGN_DOC",
                      {f["code"] for f in data["findings"]})
        self.assertEqual(data["scaffold"]["card_id"], "C010")
        self.assertEqual(before, self.snapshot())

    def test_scaffold_argument_rules(self):
        combos = (("--scaffold", "new-card"),
                  ("--scaffold", "new-card", "--plan", "--card", "C001"),
                  ("--scaffold", "new-card", "--plan", "--next-id", "change"),
                  ("--plan",),
                  ("--track", "change"),
                  ("--design-topic", "Core"),
                  ("--title", "x"))
        for extra in combos:
            with self.subTest(args=extra):
                result = subprocess.run([sys.executable, str(TOOL), str(self.root), *extra],
                                        capture_output=True, text=True)
                self.assertEqual(result.returncode, 2, result.stdout + result.stderr)
                self.assertTrue(result.stderr.strip())


if __name__ == "__main__":
    unittest.main()
