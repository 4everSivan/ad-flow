"""指令层回归：所有 CLI 参数都必须由 Agent 在 SKILL/AGENTS 中使用。"""
import re
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
    "source AGENTS": REPO / "AGENTS.md",
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

    def cli_flags(self):
        result = subprocess.run([sys.executable, str(TOOL), "--help"],
                                capture_output=True, text=True)
        self.assertEqual(result.returncode, 0, result.stderr)
        return sorted(set(re.findall(r"(?<![\w-])--[a-z][a-z-]+", result.stdout)) - {"--help"})

    def test_cli_exposes_every_documented_flag(self):
        for flag in NEW_FLAGS:
            self.assertIn(flag, self.cli_flags(), flag)

    def test_every_cli_flag_is_in_skill_and_agents(self):
        flags = self.cli_flags()
        self.assertGreaterEqual(len(flags), 20, flags)
        for name in ("SKILL.md", "AGENTS template"):
            text = self.text(SURFACES[name])
            for flag in flags:
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
        for name in ("source AGENTS", "AGENTS template", "change SOP", "task SOP"):
            self.assertIn("--scaffold new-card --plan", self.text(SURFACES[name]), name)

    def test_source_task_grill_me_precedes_a6(self):
        prompt = "templates/docs/task/README.md.tpl#grill-me"
        for name, prefix in (("source AGENTS", ""), ("task SOP", "../")):
            with self.subTest(surface=name):
                text = self.text(SURFACES[name])
                link = "(" + prefix + prompt + ")"
                self.assertIn(link, text)
                before_plan = text.split("--scaffold new-card --plan", 1)[0]
                self.assertIn(link, before_plan)
        self.assertNotIn("grill-me", self.text(SURFACES["change SOP"]).lower())

    def test_source_checkout_reuses_card_templates(self):
        for name in ("change-template.json", "task-template.json"):
            with self.subTest(template=name):
                checkout_template = REPO / "docs/standards" / name
                package_template = REPO / "templates/docs/standards" / (name + ".tpl")
                self.assertEqual(checkout_template.resolve(strict=True),
                                 package_template.resolve(strict=True))

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
