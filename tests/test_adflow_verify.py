"""CLI behavior and compatibility checks using isolated project fixtures."""
import copy
import json
import shutil
import subprocess
import sys
import tempfile
import unittest
from pathlib import Path


REPO = Path(__file__).resolve().parents[1]
TOOL = REPO / "scripts/adflow_verify.py"


class VerifyTests(unittest.TestCase):
    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory()
        self.addCleanup(self.tmp.cleanup)
        self.root = Path(self.tmp.name)
        self.write("AGENTS.md", "<!-- @ad-flow: initialized v1.1.0 -->")
        self.write_json("docs/index.json", {"adflow_version": "1.1.0"})
        self.write("docs/devel/design/01-core.md", "<!-- @topic: Core -->")
        self.write_json("docs/devel/change/index.json", {"cards": {}})
        self.write_json("docs/devel/task/index.json", {"cards": {}})

    def write(self, rel, text):
        p = self.root / rel
        p.parent.mkdir(parents=True, exist_ok=True)
        p.write_text(text, encoding="utf-8")

    def write_json(self, rel, value):
        self.write(rel, json.dumps(value, ensure_ascii=False))

    def read_json(self, rel):
        return json.loads((self.root / rel).read_text(encoding="utf-8"))

    def card(self, cid="C001", track="change", status="pending"):
        checks = [{"item": "behavior", "true_if": "correct", "false_if": "incorrect",
                   "result": True, "evidence": "fixture evidence"}]
        card = {"id": cid, "status": status,
                "target": {"design_doc": "docs/devel/design/01-core.md", "design_topic": "Core"},
                "verification" if track == "change" else "acceptance": {
                    "run_id": "local-20261010-01", "checks": checks}}
        if track == "change":
            card["verification"].update(user_quote="这次实测符合预期，可以验收", signoff="Owner (AI代签)")
        self.save_card(card, track)
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

    def run_tool(self, *args, expect=0):
        result = subprocess.run([sys.executable, str(TOOL), str(self.root), "--json", *args],
                                capture_output=True, text=True)
        self.assertEqual(result.returncode, expect, result.stdout + result.stderr)
        data = json.loads(result.stdout)
        self.assertEqual(data["exit_code"], expect)
        return data

    def files(self):
        return {str(p.relative_to(self.root)): p.read_bytes()
                for p in self.root.rglob("*") if p.is_file()}

    def git_commit(self):
        subprocess.run(["git", "init", "-q", str(self.root)], check=True, capture_output=True)
        subprocess.run(["git", "-c", "user.name=Fixture", "-c", "user.email=fixture@example.test",
                        "commit", "--allow-empty", "-qm", "fixture"], cwd=self.root,
                       check=True, capture_output=True)
        return subprocess.check_output(["git", "rev-parse", "HEAD"], cwd=self.root, text=True).strip()

    def closed_cards(self, *ids):
        commit = self.git_commit()
        for cid in ids:
            card = self.card(cid, status="closed")
            card.update(sync={"commit": commit}, gate={"exit_code": 0})
            self.save_card(card)
        self.write("CHANGELOG.md", " ".join(ids))

    def install_skeleton(self):
        sources = {
            "AGENTS.md": "AGENTS.md.tpl", "CHANGELOG.md": "docs/changelog.md.tpl",
            "docs/README.md": "docs/README.md.tpl", "docs/index.json": "docs/index.json.tpl",
            "docs/assets/README.md": "docs/assets/README.md.tpl",
            "docs/guide/README.md": "docs/guide/README.md.tpl",
            "docs/guide/index.json": "docs/guide/index.json.tpl",
            "docs/guide/01-local-deployment.md": "docs/guide/01-local-deployment.md.tpl",
            "docs/devel/README.md": "docs/devel-README.md.tpl",
            "docs/devel/index.json": "docs/devel-index.json.tpl",
            "docs/standards/coding.json": "docs/standards/coding.json.tpl",
            "docs/devel/design/README.md": "docs/design/README.md.tpl",
            "docs/devel/change/README.md": "docs/change/README.md.tpl",
            "docs/devel/change/index.json": "docs/change/index.json.tpl",
            "docs/standards/change-template.json": "docs/standards/change-template.json.tpl",
            "docs/devel/task/README.md": "docs/task/README.md.tpl",
            "docs/devel/task/index.json": "docs/task/index.json.tpl",
            "docs/standards/task-template.json": "docs/standards/task-template.json.tpl",
            "docs/devel/todo/README.md": "docs/todo/README.md.tpl",
            "docs/devel/todo/now.md": "docs/todo/now.md.tpl",
            "docs/devel/todo/future.md": "docs/todo/future.md.tpl",
            "docs/devel/env/README.md": "docs/env/README.md.tpl",
            "docs/devel/env/01-cache-and-dependency-cleanup.md": "docs/env/01-cache-and-dependency-cleanup.md.tpl",
            "docs/archive/README.md": "docs/archive-README.md.tpl",
        }
        for dest, source in sources.items():
            self.write(dest, (REPO / "templates" / source).read_text(encoding="utf-8"))
        self.write("AGENTS.md", (self.root / "AGENTS.md").read_text(encoding="utf-8") +
                   "\n<!-- @ad-flow: initialized v1.2.0 -->")
        for name in ("adflow_verify.py", "adflow-verify"):
            self.write("scripts/" + name, (REPO / "scripts" / name).read_text(encoding="utf-8"))

    def test_legacy_version_passes_read_only(self):
        self.card()
        before = self.files()
        self.run_tool()
        self.assertEqual(before, self.files())

    def test_missing_topic_is_nonblocking_advisory(self):
        card = self.card()
        del card["target"]["design_topic"]
        self.save_card(card)
        result = self.run_tool()
        self.assertEqual(result["summary"]["advisories"], 1)
        self.assertEqual(result["findings"][0]["sev"], "ADVISORY")

    def test_dependency_cycle_is_nonblocking_advisory(self):
        for cid, dep in (("T01", "T02"), ("T02", "T01")):
            card = self.card(cid, "task")
            card["depends_on"] = [dep]
            self.save_card(card, "task")
        result = self.run_tool()
        self.assertIn("DEP_CYCLE", {f["code"] for f in result["findings"]})

    def test_existing_dangling_dependency_still_blocks(self):
        card = self.card("T01", "task")
        card["depends_on"] = ["T99"]
        self.save_card(card, "task")
        self.run_tool(expect=4)

    def test_task_template_index_key_is_supported(self):
        self.card("T01", "task")
        index = self.read_json("docs/devel/task/index.json")
        index["tasks"] = index.pop("cards")
        self.write_json("docs/devel/task/index.json", index)
        self.run_tool()

    def test_preview_verified_checks_future_evidence_without_writes(self):
        card = self.card()
        card["verification"]["user_quote"] = ""
        self.save_card(card)
        before = self.files()
        result = self.run_tool("--card", "C001", "--to", "verified", expect=4)
        self.assertIn("EVIDENCE_QUOTE", {f["code"] for f in result["findings"]})
        self.assertEqual(before, self.files())

    def test_preview_record_changes_only_selected_gate(self):
        original = self.card()
        self.card("C002")
        before = self.files()
        self.run_tool("--card", "C001", "--to", "verified", "--record")
        after = self.files()
        self.assertEqual({p for p in before if before[p] != after[p]},
                         {"docs/devel/change/C001.json"})
        actual = self.read_json("docs/devel/change/C001.json")
        gate = actual.pop("gate")
        self.assertEqual(actual, original)
        self.assertEqual(gate["target_status"], "verified")
        self.assertEqual(gate["exit_code"], 0)

    def test_closed_candidate_can_record_before_status_change(self):
        commit = self.git_commit()
        card = self.card(status="verified")
        card["sync"] = {"commit": commit}
        self.save_card(card)
        self.write("CHANGELOG.md", "C001")
        self.run_tool("--card", "C001", "--to", "closed", "--record")
        card = self.read_json("docs/devel/change/C001.json")
        self.assertEqual(card["status"], "verified")
        card["status"] = "closed"
        self.save_card(card)
        self.run_tool()

    def test_task_candidate_requires_completed_dependencies(self):
        commit = self.git_commit()
        self.card("T01", "task")
        card = self.card("T02", "task", "in_progress")
        card.update(depends_on=["T01"], sync={"commit": commit})
        self.save_card(card, "task")
        result = self.run_tool("--card", "T02", "--to", "completed", expect=4)
        self.assertIn("DEP_NOT_COMPLETED", {f["code"] for f in result["findings"]})

    def test_completed_task_records_then_validates(self):
        commit = self.git_commit()
        card = self.card("T01", "task", "in_progress")
        card["sync"] = {"commit": commit}
        self.save_card(card, "task")
        self.run_tool("--card", "T01", "--to", "completed", "--record")
        card = self.read_json("docs/devel/task/T01.json")
        self.assertEqual(card["status"], "in_progress")
        card["status"] = "completed"
        self.save_card(card, "task")
        self.run_tool()

    def test_wrong_track_or_missing_card_does_not_record(self):
        self.card()
        before = self.files()
        self.run_tool("--card", "C001", "--to", "completed", "--record", expect=4)
        self.run_tool("--card", "C099", "--to", "verified", "--record", expect=4)
        self.assertEqual(before, self.files())

    def test_global_violation_is_recorded_as_failure(self):
        self.card()
        self.write_json("docs/index.json", {"adflow_version": "0.9.0"})
        self.run_tool("--card", "C001", "--to", "verified", "--record", expect=4)
        self.assertEqual(self.read_json("docs/devel/change/C001.json")["gate"]["exit_code"], 4)

    def test_duplicate_ids_block_and_do_not_record(self):
        card = self.card()
        self.write_json("docs/devel/change/C002.json", copy.deepcopy(card))
        before = self.files()
        result = self.run_tool("--record", expect=4)
        self.assertIn("ID_DUPLICATE", {f["code"] for f in result["findings"]})
        self.assertEqual(before, self.files())

    def test_warn_only_never_reports_errors_as_zero(self):
        self.card()
        self.write_json("docs/index.json", {"adflow_version": "0.9.0"})
        result = self.run_tool("--warn-only", expect=6)
        self.assertEqual(result["summary"]["errors"], 0)
        self.assertGreater(result["summary"]["warnings"], 0)

    def test_warn_only_cannot_record(self):
        self.card()
        before = self.files()
        result = subprocess.run([sys.executable, str(TOOL), str(self.root),
                                 "--warn-only", "--record"], capture_output=True, text=True)
        self.assertEqual(result.returncode, 2)
        self.assertEqual(before, self.files())

    def test_legacy_record_still_records_all_active_cards(self):
        self.card()
        self.card("C002")
        self.run_tool("--record")
        for cid in ("C001", "C002"):
            self.assertEqual(self.read_json("docs/devel/change/%s.json" % cid)["gate"]["exit_code"], 0)

    def test_existing_warning_exit_is_preserved(self):
        card = self.card()
        card["is_hotfix"] = True
        self.save_card(card)
        self.run_tool(expect=6)

    def test_failed_acceptance_is_reported_without_new_hard_gate(self):
        card = self.card()
        card["verification"]["checks"][0]["result"] = False
        self.save_card(card)
        result = self.run_tool("--card", "C001", "--to", "verified")
        self.assertIn("CHECKS_NOT_ALL_TRUE", {f["code"] for f in result["findings"]})

    def test_registered_card_missing_from_disk_blocks(self):
        self.card()
        (self.root / "docs/devel/change/C001.json").unlink()
        result = self.run_tool(expect=4)
        self.assertIn("INDEX_FILE_DEAD", {f["code"] for f in result["findings"]})

    def test_index_cannot_point_to_a_different_card(self):
        self.card()
        self.card("C002")
        index = self.read_json("docs/devel/change/index.json")
        index["cards"]["C001"]["file"] = "docs/devel/change/C002.json"
        self.write_json("docs/devel/change/index.json", index)
        result = self.run_tool(expect=4)
        codes = {f["code"] for f in result["findings"]}
        self.assertIn("INDEX_ID_DRIFT", codes)
        self.assertIn("INDEX_FILE_DRIFT", codes)

    def test_missing_empty_card_index_blocks(self):
        (self.root / "docs/devel/task/index.json").unlink()
        result = self.run_tool(expect=4)
        self.assertIn("INDEX_MISSING", {f["code"] for f in result["findings"]})

    def test_unregistered_active_card_still_blocks(self):
        self.card()
        self.write_json("docs/devel/change/index.json", {"cards": {}})
        result = self.run_tool(expect=4)
        self.assertIn("INDEX_MISSING_CARD", {f["code"] for f in result["findings"]})

    def test_card_route_must_stay_in_its_track(self):
        card = self.card()
        card["verification"] = {}
        for route in ("docs/other/C001.json", "docs/devel/task/C001.json",
                      "docs/archive/v1/task/C001.json"):
            with self.subTest(route=route):
                self.write_json(route, card)
                self.write_json("docs/devel/change/index.json", {"cards": {
                    "C001": {"status": card["status"], "file": route}}})
                result = self.run_tool(expect=4)
                self.assertIn("INDEX_FILE_INVALID", {f["code"] for f in result["findings"]})
                (self.root / route).unlink()

    def test_real_task_template_closes_and_resolves_archived_dependency(self):
        commit = self.git_commit()
        template = json.loads((REPO / "templates/docs/standards/task-template.json.tpl").read_text(encoding="utf-8"))
        self.write_json("docs/devel/task/index.json", json.loads(
            (REPO / "templates/docs/task/index.json.tpl").read_text(encoding="utf-8")))
        card = copy.deepcopy(template)
        card.update(id="T01", version="v0.1.0", target={"design_doc": "docs/devel/design/01-core.md",
                                                     "design_topic": "Core"})
        card["sync"]["commit"] = commit
        card["acceptance"].update(result=True, run_id="local-20261012-01")
        for task in card["tasks"]:
            task["done"] = True
        for check in card["acceptance"]["checks"]:
            check.update(result=True, evidence="fixture acceptance")
        self.save_card(card, "task")
        self.run_tool("--card", "T01", "--to", "completed", "--record")
        card = self.read_json("docs/devel/task/T01.json")
        self.assertEqual(card["status"], "pending")
        card["status"] = "completed"
        self.save_card(card, "task")
        self.run_tool()
        archived = "docs/archive/v0.1.0/task/T01.json"
        card["target"]["design_doc"] = "docs/devel/design/removed-historical-design.md"
        self.write_json(archived, card)
        (self.root / "docs/devel/task/T01.json").unlink()
        index = self.read_json("docs/devel/task/index.json")
        index["tasks"]["T01"]["file"] = archived
        self.write_json("docs/devel/task/index.json", index)
        archived_before = (self.root / archived).read_bytes()
        successor = self.card("T02", "task", "in_progress")
        successor.update(depends_on=["T01"], sync={"commit": commit})
        self.save_card(successor, "task")
        self.run_tool("--card", "T02", "--to", "completed", "--record")
        self.run_tool("--record")
        self.assertEqual((self.root / archived).read_bytes(), archived_before)
        self.assertEqual(self.read_json("docs/devel/task/T02.json")["gate"]["exit_code"], 0)

    def test_archived_task_identity_and_status_still_match_index(self):
        rel = "docs/archive/v0.1.0/task/T01.json"
        self.write_json(rel, {"id": "T02", "status": "completed"})
        self.write_json("docs/devel/task/index.json", {"tasks": {
            "T01": {"status": "completed", "file": rel}}})
        result = self.run_tool(expect=4)
        self.assertIn("INDEX_ID_DRIFT", {f["code"] for f in result["findings"]})
        self.write_json(rel, {"id": "T01", "status": "pending"})
        result = self.run_tool(expect=4)
        self.assertIn("INDEX_STATUS_DRIFT", {f["code"] for f in result["findings"]})

    def test_archived_and_active_duplicate_ids_still_block_record(self):
        card = self.card("T01", "task")
        rel = "docs/archive/v0.1.0/task/T01.json"
        self.write_json(rel, card)
        self.write_json("docs/devel/task/index.json", {"tasks": {
            "T01": {"status": card["status"], "file": rel}}})
        before = self.files()
        result = self.run_tool("--record", expect=4)
        self.assertIn("ID_DUPLICATE", {f["code"] for f in result["findings"]})
        self.assertEqual(before, self.files())

    def test_batch_record_recovers_after_global_failure_is_fixed(self):
        self.closed_cards("C001", "C002")
        self.run_tool()
        self.write_json("docs/index.json", {"adflow_version": "0.9.0"})
        self.run_tool("--record", expect=4)
        for cid in ("C001", "C002"):
            self.assertEqual(self.read_json("docs/devel/change/%s.json" % cid)["gate"]["exit_code"], 4)
        self.write_json("docs/index.json", {"adflow_version": "1.1.0"})
        result = self.run_tool(expect=4)
        self.assertEqual({f["code"] for f in result["findings"]}, {"GATE_EXIT_NONZERO"})
        self.run_tool("--record")
        self.run_tool()

    def test_selected_record_rechecks_own_gate_but_not_other_gate(self):
        self.closed_cards("C001", "C002")
        for cid in ("C001", "C002"):
            card = self.read_json("docs/devel/change/%s.json" % cid)
            card["gate"]["exit_code"] = 4
            self.save_card(card)
        result = self.run_tool("--card", "C001", "--record", expect=4)
        self.assertEqual({f["card"] for f in result["findings"] if f["code"] == "GATE_EXIT_NONZERO"},
                         {"C002"})
        self.run_tool("--record")
        self.run_tool()

    def test_record_does_not_ignore_current_evidence_failure(self):
        self.closed_cards("C001")
        card = self.read_json("docs/devel/change/C001.json")
        card["verification"]["user_quote"] = ""
        self.save_card(card)
        result = self.run_tool(expect=4)
        self.assertIn("GATE_CLAIM_CONTRADICTION", {f["code"] for f in result["findings"]})
        result = self.run_tool("--record", expect=4)
        self.assertIn("EVIDENCE_QUOTE", {f["code"] for f in result["findings"]})
        self.assertEqual(self.read_json("docs/devel/change/C001.json")["gate"]["exit_code"], 4)

    def test_status_must_be_valid_for_its_track(self):
        for cid, track, status in (("C001", "change", "closed "),
                                   ("C001", "change", "completed"), ("T01", "task", "closed")):
            with self.subTest(track=track, status=status):
                self.card(cid, track, status)
                result = self.run_tool(expect=4)
                self.assertTrue(any(f["code"] == "STATUS_INVALID" and f["card"] == cid
                                    for f in result["findings"]))

    def test_rejected_status_keeps_its_audit_contract(self):
        card = self.card(status="rejected")
        card["rejections"] = [{"reason": "实测行为未符合契约"}]
        self.save_card(card)
        self.run_tool()

    def test_bad_card_field_types_return_json_findings(self):
        original = self.card()
        for field, value in (("status", {}), ("target", []), ("depends_on", [1]),
                             ("verification", {"checks": [None]}), ("gate", 4)):
            with self.subTest(field=field):
                card = copy.deepcopy(original)
                card[field] = value
                self.write_json("docs/devel/change/C001.json", card)
                result = self.run_tool(expect=4)
                self.assertIn("JSON_TYPE", {f["code"] for f in result["findings"]})

    def test_bad_index_types_return_json_findings(self):
        for data in ([], {"cards": []}, {"cards": {"C001": []}}, {"topics": [None]}):
            with self.subTest(data=data):
                self.write_json("docs/devel/change/index.json", data)
                result = self.run_tool(expect=4)
                self.assertIn("JSON_TYPE", {f["code"] for f in result["findings"]})

    def test_design_doc_alias_cannot_point_to_readme(self):
        card = self.card()
        card["design"] = {"doc": "docs/devel/design/README.md"}
        self.save_card(card)
        result = self.run_tool(expect=4)
        self.assertIn("NO_README_AS_DESIGN_DOC", {f["code"] for f in result["findings"]})

    def test_init_checks_tools_json_and_version_without_requiring_empty_project_design(self):
        self.install_skeleton()
        (self.root / "docs/devel/design/01-core.md").unlink()
        self.run_tool("--mode", "init")
        for rel in ("scripts/adflow_verify.py", "scripts/adflow-verify"):
            original = (self.root / rel).read_bytes()
            (self.root / rel).unlink()
            result = self.run_tool("--mode", "init", expect=4)
            self.assertIn("BASE_FILE_MISSING", {f["code"] for f in result["findings"]})
            (self.root / rel).write_bytes(original)
        self.write("docs/devel/index.json", "{invalid")
        result = self.run_tool("--mode", "init", expect=4)
        self.assertIn("JSON_PARSE", {f["code"] for f in result["findings"]})
        self.write_json("docs/devel/index.json", {})
        self.write_json("docs/index.json", {"adflow_version": "0.9.0"})
        result = self.run_tool("--mode", "init", expect=4)
        self.assertIn("VERSION_DRIFT", {f["code"] for f in result["findings"]})

    def test_init_registered_standards_require_canonical_files(self):
        for rel in ("docs/standards/coding.json", "docs/standards/task-template.json",
                    "docs/standards/change-template.json"):
            with self.subTest(rel=rel):
                self.install_skeleton()
                original = (self.root / rel).read_bytes()
                (self.root / rel).unlink()
                # A stale legacy copy must not mask a broken canonical registration.
                legacy = {"coding.json": "docs/devel/coding-standards.json",
                          "task-template.json": "docs/devel/task/template.json",
                          "change-template.json": "docs/devel/change/template.json"}[Path(rel).name]
                self.write(legacy, original.decode())
                result = self.run_tool("--mode", "init", expect=4)
                self.assertIn(rel, {f["path"] for f in result["findings"]
                                    if f["code"] == "BASE_FILE_MISSING"})
                self.write(rel, original.decode())

    def test_init_legacy_layout_is_read_only_and_preserves_custom_policy(self):
        self.install_skeleton()
        index = self.read_json("docs/index.json")
        del index["standards"]
        self.write_json("docs/index.json", index)
        for current, legacy in (
            ("docs/standards/task-template.json", "docs/devel/task/template.json"),
            ("docs/standards/change-template.json", "docs/devel/change/template.json"),
            ("docs/guide/01-local-deployment.md", "docs/guide/01-本地部署指南.md"),
            ("docs/devel/env/01-cache-and-dependency-cleanup.md",
             "docs/devel/env/01-环境缓存与依赖清理指南.md"),
        ):
            (self.root / current).rename(self.root / legacy)
        (self.root / "docs/standards/coding.json").unlink()
        before = self.files()
        self.run_tool("--mode", "init")
        self.assertEqual(before, self.files())
        rel = "docs/devel/coding-standards.json"
        devel = self.read_json("docs/devel/index.json")
        devel["coding_standards"] = rel
        self.write_json("docs/devel/index.json", devel)
        result = self.run_tool("--mode", "init", expect=4)
        self.assertIn(rel, {f["path"] for f in result["findings"]
                            if f["code"] == "BASE_FILE_MISSING"})
        self.write(rel, '{ "common": ["custom rule"], "languages": {}, "custom": true }\n')
        before = self.files()
        self.run_tool("--mode", "init")
        self.assertEqual(before, self.files())
        # Retained project guides also work after standards are explicitly synchronized.
        for current, legacy in (
            ("docs/standards/task-template.json", "docs/devel/task/template.json"),
            ("docs/standards/change-template.json", "docs/devel/change/template.json"),
            ("docs/standards/coding.json", rel),
        ):
            self.write(current, (self.root / legacy).read_text())
        index["standards"] = {"coding": "docs/standards/coding.json",
                              "task_template": "docs/standards/task-template.json",
                              "change_template": "docs/standards/change-template.json"}
        self.write_json("docs/index.json", index)
        self.run_tool("--mode", "init")

    def test_init_standards_routes_and_json_are_validated(self):
        self.install_skeleton()
        for routes in ([], None, {}, {"coding": "../outside.json"}):
            with self.subTest(routes=routes):
                index = self.read_json("docs/index.json")
                index["standards"] = routes
                self.write_json("docs/index.json", index)
                result = self.run_tool("--mode", "init", expect=4)
                self.assertIn("STANDARD_ROUTE", {f["code"] for f in result["findings"]})
        self.install_skeleton()
        for rel in ("docs/standards/coding.json", "docs/devel/coding-standards.json"):
            for invalid, code in (("{invalid", "JSON_PARSE"), ("[]", "JSON_TYPE")):
                with self.subTest(rel=rel, invalid=invalid):
                    self.write(rel, invalid)
                    result = self.run_tool("--mode", "init", expect=4)
                    self.assertIn(code, {f["code"] for f in result["findings"]})
            self.write_json(rel, {"common": ["custom"], "languages": {}, "custom": True})

    def test_init_rejects_missing_version_and_nonobject_json(self):
        self.install_skeleton()
        self.write_json("docs/index.json", {})
        self.write_json("docs/guide/index.json", [])
        result = self.run_tool("--mode", "init", expect=4)
        codes = {f["code"] for f in result["findings"]}
        self.assertIn("VERSION_MISSING", codes)
        self.assertIn("JSON_TYPE", codes)

    def test_installed_wrapper_runs_outside_skill_source(self):
        self.card()
        scripts = self.root / "scripts"
        scripts.mkdir()
        for name in ("adflow_verify.py", "adflow-verify"):
            shutil.copy2(REPO / "scripts" / name, scripts / name)
        result = subprocess.run([str(scripts / "adflow-verify"), "--json"],
                                cwd=self.root, capture_output=True, text=True)
        self.assertEqual(result.returncode, 0, result.stdout + result.stderr)
        self.assertEqual(json.loads(result.stdout)["target"], str(self.root.resolve()))


if __name__ == "__main__":
    unittest.main()
