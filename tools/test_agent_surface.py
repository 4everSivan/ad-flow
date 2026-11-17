"""指令层回归：v1.8.0 新增参数必须由 Agent 在 SKILL/AGENTS 中使用。"""
import subprocess
import sys
import unittest
from pathlib import Path

REPO = Path(__file__).resolve().parents[1]
TOOL = REPO / "scripts/adflow_verify.py"
NEW_FLAGS = ["--list-checks", "--scaffold", "--plan", "--track", "--design-topic",
             "--title", "--card-version", "--branch", "--design-doc", "--todo",
             "--milestone"]
SURFACES = {
    "SKILL.md": REPO / "SKILL.md",
    "AGENTS template": REPO / "templates/AGENTS.md.tpl",
    "change SOP": REPO / "references/02-change-sop.md",
    "task SOP": REPO / "references/03-task-sop.md",
    "change README": REPO / "templates/docs/change/README.md.tpl",
    "task README": REPO / "templates/docs/task/README.md.tpl",
    "workflow": REPO / "workflow.yaml",
}


class AgentSurfaceTests(unittest.TestCase):
    def text(self, path):
        return path.read_text(encoding="utf-8")

    def test_cli_exposes_every_documented_flag(self):
        result = subprocess.run([sys.executable, str(TOOL), "--help"],
                                capture_output=True, text=True)
        self.assertEqual(result.returncode, 0, result.stderr)
        for flag in NEW_FLAGS:
            self.assertIn(flag, result.stdout, flag)

    def test_every_new_flag_is_in_skill_and_agents(self):
        for name in ("SKILL.md", "AGENTS template"):
            text = self.text(SURFACES[name])
            for flag in NEW_FLAGS:
                self.assertIn(flag, text, "%s 缺少 %s" % (name, flag))

    def test_every_new_flag_appears_in_at_least_two_surfaces(self):
        for flag in NEW_FLAGS:
            hits = [name for name, path in SURFACES.items() if flag in self.text(path)]
            self.assertGreaterEqual(len(hits), 2, "%s 只出现在 %r" % (flag, hits))

    def test_agent_consumes_hint_and_summary_codes(self):
        for name in ("SKILL.md", "AGENTS template"):
            text = self.text(SURFACES[name])
            for token in ("hint", "summary.codes", "--list-checks"):
                self.assertIn(token, text, "%s 缺少 %s" % (name, token))

    def test_card_creation_requires_read_only_plan(self):
        for name in ("AGENTS template", "change SOP", "task SOP"):
            self.assertIn("--scaffold new-card --plan", self.text(SURFACES[name]), name)

    def test_agents_rule_keeps_human_out_of_the_cli(self):
        text = self.text(SURFACES["AGENTS template"])
        self.assertIn("自然语言", text)
        self.assertIn("Agent 执行", text)

    def test_workflow_contract_names_the_surface(self):
        text = self.text(SURFACES["workflow"])
        self.assertIn("agent_command_surface", text)
        for token in ("--list-checks", "--scaffold", "--design-topic", "--todo"):
            self.assertIn(token, text)


if __name__ == "__main__":
    unittest.main()
