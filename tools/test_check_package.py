"""安装/升级映射与包资产的回归用例（维护者资产，不安装到目标项目）。"""
import json
import os
import shutil
import subprocess
import sys
import tempfile
import unittest
from pathlib import Path

REPO = Path(__file__).resolve().parents[1]
TOOLS = REPO / "tools"
sys.path.insert(0, str(TOOLS))
import check_package  # noqa: E402


def copy_repo(testcase):
    tmp = tempfile.TemporaryDirectory()
    testcase.addCleanup(tmp.cleanup)
    dst = Path(tmp.name) / "skill"
    shutil.copytree(REPO, dst, ignore=shutil.ignore_patterns(
        ".git", ".zcode", "__pycache__", "local", "_adflow_backup"))
    return dst


def rewrite(testcase, root, old, new):
    path = root / "workflow.yaml"
    text = path.read_text(encoding="utf-8")
    testcase.assertEqual(text.count(old), 1, "负例锚点必须唯一: %r" % old)
    path.write_text(text.replace(old, new), encoding="utf-8")


def render(text):
    return text.replace("MyProject", "FixtureProj").replace("YYYY-MM-DD", "2026-11-17")


def render_install(dest_root, entries, source_root=REPO):
    """按映射把安装资产渲染进目标工程；返回实际写入的相对路径集合。"""
    written = set()
    for entry in entries:
        source = source_root / entry["source"]
        content = source.read_text(encoding="utf-8")
        if entry["source"].endswith(".tpl"):
            content = render(content)
        dest = dest_root / entry["dest"]
        dest.parent.mkdir(parents=True, exist_ok=True)
        dest.write_text(content, encoding="utf-8")
        os.chmod(str(dest), 0o755 if entry["dest"] == "scripts/adflow-verify" else 0o644)
        written.add(entry["dest"])
    return written


class PackageBaselineTests(unittest.TestCase):
    def test_repository_package_is_consistent(self):
        self.assertEqual(check_package.verify(REPO), [])

    def test_workflow_yaml_matches_machine_blocks(self):
        try:
            import yaml
        except ImportError:  # pragma: no cover - CI 安装 PyYAML 后执行
            self.skipTest("PyYAML 不可用；本地或 CI 安装后启用")
        text = (REPO / "workflow.yaml").read_text(encoding="utf-8")
        doc = yaml.safe_load(text)
        blocks, problems = check_package.load_blocks(text)
        self.assertEqual(problems, [])
        pipeline = doc["pipeline"]
        self.assertEqual(pipeline[3]["inputs"], blocks["install-agents"])
        self.assertEqual(pipeline[4]["mappings"], blocks["install-readmes"])
        self.assertEqual(pipeline[5]["mappings"], blocks["install-hubs"])
        assertions = pipeline[7]["assertions"]
        self.assertEqual(assertions["required_files_exist"], blocks["required-files"])
        self.assertEqual(assertions["verifier_files_required"], blocks["verifier-files"])
        self.assertEqual(assertions["forbidden_files_not_exist"], blocks["forbidden-files"])
        upgrade = {step["step"]: step for step in doc["upgrade_pipeline"]["steps"]}
        self.assertEqual(upgrade["U2_SYNC_AGENTS_CONSTITUTION"]["template"],
                         blocks["upgrade-agents"])
        self.assertEqual(upgrade["U3_SYNC_DIRECTORY_READMES"]["targets"],
                         blocks["upgrade-readmes"])
        self.assertEqual(upgrade["U4_SYNC_CARD_TEMPLATES"]["targets"], blocks["upgrade-targets"])
        self.assertEqual(upgrade["U4_SYNC_CARD_TEMPLATES"]["retire_legacy"],
                         blocks["upgrade-retire"])
        self.assertEqual(len(blocks["install-readmes"]), 10)
        self.assertEqual(len(blocks["install-hubs"]), 15)
        self.assertEqual(len(blocks["required-files"]), 24)

    def test_install_graph_is_24_plus_2(self):
        blocks, problems = check_package.load_blocks(
            (REPO / "workflow.yaml").read_text(encoding="utf-8"))
        self.assertEqual(problems, [])
        entries = check_package.install_entries(blocks)
        verifier = set(blocks["verifier-files"])
        self.assertEqual(len(entries), 26)
        self.assertEqual(len([e for e in entries if e["dest"] in verifier]), 2)
        self.assertEqual(len([e for e in entries if e["dest"] not in verifier]), 24)


class MappingNegativeTests(unittest.TestCase):
    def problems(self, mutate):
        root = copy_repo(self)
        mutate(root)
        return check_package.verify(root)

    def test_renamed_mapping_is_detected(self):
        def mutate(root):
            rewrite(self, root,
                    '"readme": "${target_dir}/docs/archive/README.md"',
                    '"readme": "${target_dir}/docs/archive/README-legacy.md"')
        problems = self.problems(mutate)
        self.assertTrue(any("required_files_exist" in p or "包含" in p for p in problems), problems)

    def test_duplicate_destination_is_detected(self):
        def mutate(root):
            rewrite(self, root,
                    '"readme": "${target_dir}/docs/archive/README.md"',
                    '"readme": "${target_dir}/docs/assets/README.md"')
        problems = self.problems(mutate)
        self.assertTrue(any("目的地重复" in p for p in problems), problems)

    def test_unknown_mapping_field_is_detected(self):
        def mutate(root):
            rewrite(self, root,
                    '{"dest": "${target_dir}/CHANGELOG.md", "template": "templates/docs/changelog.md.tpl"}',
                    '{"dest": "${target_dir}/CHANGELOG.md", "template": "templates/docs/changelog.md.tpl", "owner": "root"}')
        problems = self.problems(mutate)
        self.assertTrue(any("未知映射字段" in p for p in problems), problems)

    def test_duplicate_json_key_is_detected(self):
        def mutate(root):
            rewrite(self, root,
                    '{"dest": "${target_dir}/CHANGELOG.md"',
                    '{"dest": "${target_dir}/CHANGELOG.md", "dest": "${target_dir}/CHANGELOG.md"')
        problems = self.problems(mutate)
        self.assertTrue(any("重复字段" in p for p in problems), problems)

    def test_unparseable_block_is_detected(self):
        def mutate(root):
            rewrite(self, root,
                    '      ]\n      # @adflow:manifest-end install-hubs',
                    '      # @adflow:manifest-end install-hubs')
        problems = self.problems(mutate)
        self.assertTrue(any("合法 JSON" in p or "未闭合" in p for p in problems), problems)

    def test_missing_block_is_detected(self):
        def mutate(root):
            rewrite(self, root,
                    '# @adflow:manifest-begin upgrade-retire',
                    '# @adflow:manifest-begin upgrade-retire-renamed')
            rewrite(self, root,
                    '# @adflow:manifest-end upgrade-retire',
                    '# @adflow:manifest-end upgrade-retire-renamed')
        problems = self.problems(mutate)
        self.assertTrue(any("缺少 manifest 块" in p or "未知 manifest 块" in p for p in problems),
                        problems)

    def test_orphan_template_is_detected(self):
        def mutate(root):
            (root / "templates" / "orphan.md.tpl").write_text("# orphan\n", encoding="utf-8")
        problems = self.problems(mutate)
        self.assertTrue(any("未挂接的模板" in p for p in problems), problems)

    def test_broken_nested_json_is_detected(self):
        def mutate(root):
            (root / "templates" / "coding-standards" / "python.json").write_text(
                "{broken", encoding="utf-8")
        problems = self.problems(mutate)
        self.assertTrue(any("JSON 无法解析" in p for p in problems), problems)

    def test_missing_executable_bit_is_detected(self):
        def mutate(root):
            os.chmod(str(root / "scripts" / "adflow-verify"), 0o644)
        problems = self.problems(mutate)
        self.assertTrue(any("可执行权限" in p for p in problems), problems)

    def test_upgrade_template_mismatch_is_detected(self):
        def mutate(root):
            rewrite(self, root,
                    '{"dest": "docs/standards/coding.json", "template": "templates/docs/standards/coding.json.tpl"',
                    '{"dest": "docs/standards/coding.json", "template": "templates/docs/standards/change-template.json.tpl"')
        problems = self.problems(mutate)
        self.assertTrue(any("模板与安装映射不一致" in p for p in problems), problems)


class IndependentContentTests(unittest.TestCase):
    """预期标题独立于映射书写；互换模板时由内容断言而不是映射自身发现问题。"""

    ANCHORS = {
        "docs/assets/README.md": "# 文档资源库 (assets/)",
        "docs/devel/todo/README.md": "# 待办缓冲池 (todo/)",
        "docs/devel/design/README.md": "# 系统设计中心 (design/)",
    }

    def materialize(self, workflow_root, project_root):
        blocks, problems = check_package.load_blocks(
            (workflow_root / "workflow.yaml").read_text(encoding="utf-8"))
        self.assertEqual(problems, [])
        entries = check_package.install_entries(blocks)
        render_install(project_root, entries, source_root=workflow_root)
        return entries

    def test_mapping_targets_match_independent_content(self):
        workflow_root = copy_repo(self)
        project = workflow_root / "fixture_project"
        project.mkdir()
        self.materialize(workflow_root, project)
        for rel, anchor in self.ANCHORS.items():
            first = (project / rel).read_text(encoding="utf-8").splitlines()[0]
            self.assertEqual(first, anchor, "%s 的内容锚点不符" % rel)
        self.assertNotIn("MyProject", (project / "AGENTS.md").read_text(encoding="utf-8"))

    def test_swapped_templates_are_caught_by_content_anchors(self):
        workflow_root = copy_repo(self)
        assets_template = "templates/docs/assets/README.md.tpl"
        todo_template = "templates/docs/todo/README.md.tpl"
        text = (workflow_root / "workflow.yaml").read_text(encoding="utf-8")
        text = text.replace('"template": "%s"' % assets_template,
                            '"template": "@@SWAP@@"', 1)
        text = text.replace('"template": "%s"' % todo_template,
                            '"template": "%s"' % assets_template, 1)
        text = text.replace('"template": "@@SWAP@@"',
                            '"template": "%s"' % todo_template, 1)
        (workflow_root / "workflow.yaml").write_text(text, encoding="utf-8")
        project = workflow_root / "fixture_project"
        project.mkdir()
        self.materialize(workflow_root, project)
        assets_first = (project / "docs/assets/README.md").read_text(encoding="utf-8").splitlines()[0]
        todo_first = (project / "docs/devel/todo/README.md").read_text(encoding="utf-8").splitlines()[0]
        self.assertNotEqual(assets_first, self.ANCHORS["docs/assets/README.md"])
        self.assertNotEqual(todo_first, self.ANCHORS["docs/devel/todo/README.md"])


class InstalledEntryTests(unittest.TestCase):
    """用映射生成真实目标，再通过安装后的 Shell 入口执行 --mode init 与普通复核。"""

    def test_installed_project_passes_init_and_process_checks(self):
        blocks, problems = check_package.load_blocks(
            (REPO / "workflow.yaml").read_text(encoding="utf-8"))
        self.assertEqual(problems, [])
        entries = check_package.install_entries(blocks)
        tmp = tempfile.TemporaryDirectory()
        self.addCleanup(tmp.cleanup)
        project = Path(tmp.name) / "project"
        project.mkdir()
        written = render_install(project, entries)
        self.assertEqual(len(written), 26)
        self.assertEqual(len([p for p in written if p.startswith("docs/")]), 22)
        for rel in ("AGENTS.md", "CHANGELOG.md"):
            self.assertIn(rel, written)

        wrapper = project / "scripts" / "adflow-verify"
        self.assertTrue(os.access(str(wrapper), os.X_OK))
        init = subprocess.run([str(wrapper), str(project), "--mode", "init"],
                              capture_output=True, text=True)
        self.assertEqual(init.returncode, 0, init.stdout + init.stderr)
        process = subprocess.run([str(wrapper), str(project)],
                                 capture_output=True, text=True)
        self.assertEqual(process.returncode, 0, process.stdout + process.stderr)
        self.assertIn("summary: 0 error(s), 0 warning(s)", process.stdout)

        standards = json.loads((project / "docs/standards/coding.json").read_text(encoding="utf-8"))
        self.assertIn("common", standards)
        for rel in ("docs/index.json", "docs/devel/index.json", "docs/guide/index.json",
                    "docs/devel/change/index.json", "docs/devel/task/index.json"):
            data = json.loads((project / rel).read_text(encoding="utf-8"))
            self.assertNotIn("MyProject", json.dumps(data, ensure_ascii=False))


if __name__ == "__main__":
    unittest.main()
