"""诊断目录、修复提示与单次统计的回归用例（维护者资产，不安装到目标项目）。"""
import ast
import json
import re
import subprocess
import sys
import tempfile
import unittest
from pathlib import Path

REPO = Path(__file__).resolve().parents[1]
TOOL = REPO / "scripts/adflow_verify.py"
VERSION = re.search(r'^VERSION = "([^"]+)"', TOOL.read_text(encoding="utf-8"), re.M).group(1)
sys.path.insert(0, str(REPO / "scripts"))
import adflow_verify as av  # noqa: E402


def emission_scan(path):
    """返回 (literal emission points, non-literal points, findings.append lines, add span)。"""
    tree = ast.parse(path.read_text(encoding="utf-8"))
    points, dynamic, appends, add_span = [], [], [], None
    for node in ast.walk(tree):
        if isinstance(node, ast.FunctionDef) and node.name == "add":
            add_span = (node.lineno, node.end_lineno)
        if not isinstance(node, ast.Call):
            continue
        func = node.func
        name = func.attr if isinstance(func, ast.Attribute) else None
        if name in ("hard", "soft", "advisory") and node.args:
            sev = {"hard": "ERROR", "soft": "WARN", "advisory": "ADVISORY"}[name]
            arg = node.args[0]
            if isinstance(arg, ast.Constant) and isinstance(arg.value, str):
                points.append((arg.value, sev, node.lineno))
            else:
                dynamic.append((name, node.lineno))
        if name == "add" and len(node.args) >= 2:
            code, sev = node.args[1], node.args[0]
            if (isinstance(code, ast.Constant) and isinstance(code.value, str)
                    and isinstance(sev, ast.Constant)):
                points.append((code.value, sev.value, node.lineno))
        if (name == "append" and isinstance(func.value, ast.Attribute)
                and func.value.attr == "findings"):
            appends.append(node.lineno)
    return points, dynamic, appends, add_span


class CliFixture(unittest.TestCase):
    """最小可复核工程夹具；只构造用例需要的事实。"""

    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory()
        self.addCleanup(self.tmp.cleanup)
        self.root = Path(self.tmp.name)
        self.write("AGENTS.md", "<!-- @ad-flow: initialized v%s -->" % VERSION)
        self.write_json("docs/index.json", {"adflow_version": VERSION})
        self.write("docs/devel/design/01-core.md", "<!-- @topic: Core -->")
        self.write_json("docs/devel/change/index.json", {"cards": {}, "topics": {}})
        self.write_json("docs/devel/task/index.json", {"tasks": {}, "topics": {}})
        self.write("CHANGELOG.md", "# Changelog\n")

    def write(self, rel, text):
        p = self.root / rel
        p.parent.mkdir(parents=True, exist_ok=True)
        p.write_text(text, encoding="utf-8")

    def write_json(self, rel, value):
        self.write(rel, json.dumps(value, ensure_ascii=False))

    def read_json(self, rel):
        return json.loads((self.root / rel).read_text(encoding="utf-8"))

    def card(self, cid="C001", status="pending", design_doc="docs/devel/design/01-core.md"):
        card = {"id": cid, "status": status,
                "target": {"design_doc": design_doc, "design_topic": "Core"},
                "verification": {
                    "run_id": "local-20261117-01",
                    "checks": [{"item": "behavior", "true_if": "correct",
                                "false_if": "incorrect", "result": True,
                                "evidence": "fixture evidence"}],
                    "user_quote": "这次实测符合预期，可以验收", "signoff": "Owner (AI代签)"}}
        self.save_card(card)
        return card

    def save_card(self, card, track="change"):
        cid = card["id"]
        rel = "docs/devel/%s/%s.json" % (track, cid)
        self.write_json(rel, card)
        index_rel = "docs/devel/%s/index.json" % track
        index = self.read_json(index_rel)
        key = "tasks" if track == "task" and "tasks" in index else "cards"
        index[key][cid] = {"status": card["status"], "file": rel}
        self.write_json(index_rel, index)

    def run_cli(self, *args):
        return subprocess.run([sys.executable, str(TOOL), str(self.root), *args],
                              capture_output=True, text=True)

    def run_json(self, *args, expect):
        result = self.run_cli("--json", *args)
        self.assertEqual(result.returncode, expect, result.stdout + result.stderr)
        data = json.loads(result.stdout)
        self.assertEqual(data["exit_code"], expect)
        return data

    def findings(self, data, code):
        return [f for f in data["findings"] if f["code"] == code]

    def snapshot(self):
        return {str(p.relative_to(self.root)): p.read_bytes()
                for p in self.root.rglob("*") if p.is_file()}


class CatalogTests(unittest.TestCase):
    def test_registry_covers_every_emission_point(self):
        points, dynamic, appends, add_span = emission_scan(TOOL)
        self.assertEqual(dynamic, [], "诊断码必须是可枚举的字符串字面量")
        emitted = {code for code, _, _ in points}
        self.assertEqual(emitted, set(av.CHECKS),
                         "发出点与注册表必须双向一致：%r" % (emitted ^ set(av.CHECKS)))
        for code, severity, lineno in points:
            self.assertEqual(av.CHECKS[code][0], severity,
                             "%s 在 scripts/adflow_verify.py:%d 以 %s 发出，注册表声明 %s"
                             % (code, lineno, severity, av.CHECKS[code][0]))

    def test_findings_are_only_emitted_through_add(self):
        _, _, appends, add_span = emission_scan(TOOL)
        self.assertIsNotNone(add_span, "Ctx.add 是唯一发出路径")
        self.assertEqual(len(appends), 1, "新增的 findings.append 必须改走 add()")
        start, end = add_span
        self.assertTrue(start <= appends[0] <= end,
                        "findings.append 必须位于 Ctx.add 内：%r" % appends)

    def test_registry_entries_are_complete_and_sorted(self):
        self.assertEqual(len(av.CHECKS), 66)
        severity = {"ERROR": 0, "WARN": 0, "ADVISORY": 0}
        for code, (sev, meaning, hint) in av.CHECKS.items():
            self.assertIn(sev, severity, code)
            severity[sev] += 1
            for field, value in (("meaning", meaning), ("hint", hint)):
                self.assertTrue(isinstance(value, str) and value.strip(), "%s.%s 不能为空" % (code, field))
                self.assertEqual(value, value.strip(), "%s.%s 不应带首尾空白" % (code, field))
            self.assertNotIn("TODO", hint.upper(), code)
        self.assertEqual(severity, {"ERROR": 42, "WARN": 6, "ADVISORY": 18})
        catalog = av.check_catalog()
        self.assertEqual([item["code"] for item in catalog], sorted(av.CHECKS))
        for item in catalog:
            self.assertEqual(set(item), {"code", "severity", "meaning", "hint"})

    def test_list_checks_is_target_independent(self):
        with tempfile.TemporaryDirectory() as empty:
            text = subprocess.run([sys.executable, str(TOOL), empty, "--list-checks"],
                                  capture_output=True, text=True)
            self.assertEqual(text.returncode, 0, text.stderr)
            self.assertIn("checks=66", text.stdout)
            self.assertIn("ARCHIVE_NON_TERMINAL", text.stdout)

            data = subprocess.run([sys.executable, str(TOOL), empty, "--list-checks", "--json"],
                                  capture_output=True, text=True)
            self.assertEqual(data.returncode, 0, data.stderr)
            payload = json.loads(data.stdout)
            self.assertEqual(set(payload), {"tool", "version", "checks"})
            self.assertEqual(payload["tool"], "adflow-verify")
            self.assertEqual(payload["version"], VERSION)
            self.assertEqual(len(payload["checks"]), 66)
            self.assertEqual([c["code"] for c in payload["checks"]], sorted(av.CHECKS))
            for item in payload["checks"]:
                self.assertEqual(set(item), {"code", "severity", "meaning", "hint"})
                self.assertTrue(all(item.values()), item["code"])

    def test_list_checks_is_exclusive_and_read_only(self):
        with tempfile.TemporaryDirectory() as empty:
            root = Path(empty)
            before = {str(p.relative_to(root)): p.read_bytes()
                      for p in root.rglob("*") if p.is_file()}
            combos = (("--next-id", "change"), ("--topic", "Core"), ("--card", "C001"),
                      ("--to", "closed"), ("--record",), ("--receipt",),
                      ("--release", "v0.1.0"), ("--warn-only",), ("--mode", "init"))
            for extra in combos:
                with self.subTest(extra=extra):
                    result = subprocess.run(
                        [sys.executable, str(TOOL), "--list-checks", *extra],
                        capture_output=True, text=True)
                    self.assertEqual(result.returncode, 2, result.stdout + result.stderr)
                    self.assertIn("--list-checks", result.stderr)
            after = {str(p.relative_to(root)): p.read_bytes()
                     for p in root.rglob("*") if p.is_file()}
            self.assertEqual(before, after)


class HintTests(CliFixture):
    def test_json_parse_hint_and_summary_codes(self):
        self.write("docs/devel/change/index.json", "{bad json")
        data = self.run_json(expect=4)
        parse = self.findings(data, "JSON_PARSE")
        self.assertEqual(len(parse), 1)
        self.assertIn("JSON", parse[0]["hint"])
        self.assertEqual(data["summary"]["codes"]["JSON_PARSE"], {"ERROR": 1})
        self.assertEqual(sum(data["summary"][k] for k in ("errors", "warnings", "advisories")),
                         len(data["findings"]))

    def test_design_link_hint_is_read_only_and_root_cause_first(self):
        card = self.card(status="verified", design_doc="docs/devel/design/README.md")
        card["gate"] = {"exit_code": 0}
        self.save_card(card)
        before = self.snapshot()
        data = self.run_json(expect=4)
        self.assertEqual(before, self.snapshot(), "只读复核不得改写卡片或 gate")
        link = self.findings(data, "NO_README_AS_DESIGN_DOC")[0]
        self.assertIn("docs/devel/design/", link["hint"])
        self.assertIn("@topic", link["hint"])
        # 修复根因后复核通过；提示不诱导先改写 gate。
        card["target"]["design_doc"] = "docs/devel/design/01-core.md"
        self.save_card(card)
        self.run_json(expect=0)

    def test_missing_user_quote_hint_names_the_field(self):
        card = self.card(status="verified")
        card["verification"]["user_quote"] = ""
        self.save_card(card)
        data = self.run_json(expect=4)
        hint = self.findings(data, "EVIDENCE_QUOTE")[0]["hint"]
        self.assertIn("user_quote", hint)
        self.assertNotIn("--record", hint)

    def test_frozen_archive_hint_points_to_existing_sop(self):
        self.write_json("docs/archive/v0.1.0/change/C009.json",
                        {"id": "C009", "status": "pending"})
        data = self.run_json(expect=4)
        hint = self.findings(data, "ARCHIVE_NON_TERMINAL")[0]["hint"]
        self.assertIn("历史批次账实修复", hint)
        self.assertIn("docs/archive/README.md", hint)

    def test_hint_override_is_honored(self):
        with tempfile.TemporaryDirectory() as tmp:
            ctx = av.Ctx(tmp)
            ctx.hard("JSON_PARSE", None, "broken.json", "msg")
            self.assertEqual(ctx.findings[-1]["hint"], av.CHECKS["JSON_PARSE"][2])
            ctx.hard("JSON_PARSE", None, "broken.json", "msg", hint="更具体的提示")
            self.assertEqual(ctx.findings[-1]["hint"], "更具体的提示")


class DesignRouteTests(CliFixture):
    """设计文档机器路由：声明 designs 才检查，旧布局保持兼容。"""

    def devel_index(self, designs, with_key=True):
        subsystem = {"name": "design", "path": "docs/devel/design",
                     "readme": "docs/devel/design/README.md"}
        if with_key:
            subsystem["designs"] = designs
        self.write_json("docs/devel/index.json", {"subsystems": [subsystem]})

    def drift(self, data):
        return [f for f in data["findings"] if f["code"] == "DESIGN_ROUTE_DRIFT"]

    def test_unregistered_design_is_advisory(self):
        self.devel_index([])
        data = self.run_json(expect=0)
        found = self.drift(data)
        self.assertIn("未登记", " ".join(f["msg"] for f in found))
        self.assertEqual({f["path"] for f in found}, {"docs/devel/design/01-core.md"})

    def test_registered_design_is_silent(self):
        self.devel_index([{"file": "docs/devel/design/01-core.md", "topic": "Core",
                           "status": "baseline", "title": "Core"}])
        data = self.run_json(expect=0)
        self.assertEqual(self.drift(data), [])

    def test_invalid_route_entries_are_advisory(self):
        self.devel_index([{"file": "docs/devel/design/missing.md"},
                          {"topic": "Core"},
                          {"file": "docs/devel/design/01-core.md", "topic": "Other"}])
        data = self.run_json(expect=0)
        messages = " ".join(f["msg"] for f in self.drift(data))
        self.assertIn("不存在", messages)
        self.assertIn("非空 file", messages)
        self.assertIn("@Other", messages)

    def test_non_list_designs_is_advisory(self):
        self.devel_index("not-a-list")
        data = self.run_json(expect=0)
        self.assertIn("必须为数组", " ".join(f["msg"] for f in self.drift(data)))

    def test_legacy_index_without_designs_is_compatible(self):
        self.devel_index([], with_key=False)
        data = self.run_json(expect=0)
        self.assertEqual(self.drift(data), [])


class SummaryCodeTests(CliFixture):
    def test_clean_run_has_empty_code_stats(self):
        data = self.run_json(expect=0)
        self.assertEqual(data["summary"]["codes"], {})

    def test_codes_aggregate_multiple_same_code(self):
        for cid in ("C001", "C002"):
            card = self.card(cid=cid, status="verified",
                             design_doc="docs/devel/design/README.md")
            self.save_card(card)
        data = self.run_json(expect=4)
        self.assertEqual(data["summary"]["codes"]["NO_README_AS_DESIGN_DOC"]["ERROR"], 2)
        seen = {}
        for f in data["findings"]:
            seen.setdefault(f["code"], {}).setdefault(f["sev"], 0)
            seen[f["code"]][f["sev"]] += 1
        self.assertEqual(data["summary"]["codes"], seen)

    def test_codes_follow_warn_only_downgrade(self):
        self.write("docs/devel/change/index.json", "{bad json")
        data = self.run_json("--warn-only", expect=6)
        self.assertEqual(data["summary"]["errors"], 0)
        self.assertEqual(data["summary"]["codes"]["JSON_PARSE"], {"WARN": 1})


if __name__ == "__main__":
    unittest.main()
