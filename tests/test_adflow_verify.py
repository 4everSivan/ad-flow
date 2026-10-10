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
        index["cards"][cid] = {"status": card["status"], "file": rel}
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
