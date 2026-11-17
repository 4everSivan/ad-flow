#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""Maintainer check: validate workflow.yaml machine manifests and package assets.

Not installed into target projects. Stdlib only.

  python3 tools/check_package.py [--root DIR]

Reads the "# @adflow:manifest-begin <name>" / "# @adflow:manifest-end <name>" blocks
(JSON values that are also valid YAML values) and asserts:

  * every expected block appears exactly once and parses as JSON;
  * install mappings cover 24 governance files + 2 verifier files with unique,
    project-relative destinations and existing template sources;
  * no orphan .tpl assets, every JSON asset/example parses;
  * upgrade mappings only touch managed assets with the same sources;
  * verifier constants (BASE_FILES/STANDARD_FILES/TOOL_FILES/LEGACY_FILES) agree;
  * version anchors and the wrapper executable bit are intact.
"""
import argparse
import importlib.util
import json
import os
import re
import sys
from pathlib import Path

TARGET_PREFIX = "${target_dir}/"
MARKER_BEGIN = re.compile(r"^\s*#\s*@adflow:manifest-begin\s+(\S+)\s*$")
MARKER_END = re.compile(r"^\s*#\s*@adflow:manifest-end\s+(\S+)\s*$")
LANGS_RE = re.compile(r"available_languages:\s*(\[[^\]]*\])")

# name -> expected JSON type
BLOCK_TYPES = {
    "install-agents": dict,
    "install-readmes": list,
    "install-hubs": list,
    "verifier-files": list,
    "required-files": list,
    "forbidden-files": list,
    "upgrade-agents": str,
    "upgrade-readmes": list,
    "upgrade-targets": list,
    "upgrade-retire": list,
}
REQUIRED_KEYS = {
    "install-agents": {"template", "target_file"},
    "install-readmes": {"dir", "readme", "template"},
    "install-hubs": {"dest", "template"},
    "upgrade-targets": {"dest", "template"},
}
OPTIONAL_KEYS = {
    "install-readmes": {"constraints"},
    "install-hubs": {"note"},
    "upgrade-targets": {"note"},
}


class Problem(Exception):
    """A single package inconsistency, reported with block/entry context."""


class DuplicateKey(ValueError):
    pass


def _no_duplicate_keys(pairs):
    seen = set()
    for key, _ in pairs:
        if key in seen:
            raise DuplicateKey("重复字段 %r（JSON 重名键会静默吞掉一侧）" % key)
        seen.add(key)
    return dict(pairs)


def _loads(text):
    return json.loads(text, object_pairs_hook=_no_duplicate_keys)


def load_blocks(text):
    """Return ({name: value}, [problems]) for the delimited JSON blocks."""
    blocks, problems, current, buf = {}, [], None, []
    for lineno, line in enumerate(text.splitlines(), 1):
        m = MARKER_BEGIN.match(line)
        if m:
            name = m.group(1)
            if current is not None:
                problems.append("workflow.yaml:%d: manifest 块未闭合就开始了 %s" % (lineno, name))
            if name in blocks:
                problems.append("workflow.yaml:%d: manifest 块重复出现: %s" % (lineno, name))
            current, buf = name, []
            continue
        m = MARKER_END.match(line)
        if m:
            name = m.group(1)
            if current != name:
                problems.append("workflow.yaml:%d: manifest-end %s 与当前块 %r 不匹配"
                                % (lineno, name, current))
                current = None
                continue
            try:
                blocks[name] = _loads("\n".join(buf))
            except Exception as e:  # noqa: BLE001
                problems.append("workflow.yaml:%d: 块 %s 不是合法 JSON: %s" % (lineno, name, e))
            current = None
            continue
        if current is not None:
            buf.append(line)
    if current is not None:
        problems.append("workflow.yaml: manifest 块未闭合: %s" % current)
    return blocks, problems


def rel_target(value):
    """Normalize ${target_dir}/X to project-relative X; reject absolute/traversal."""
    if not isinstance(value, str):
        raise Problem("目标路径必须是字符串: %r" % (value,))
    value = value.strip()
    if value.startswith(TARGET_PREFIX):
        value = value[len(TARGET_PREFIX):]
    parts = Path(value).parts
    if not value or value.startswith("/") or "\\" in value or ".." in parts:
        raise Problem("目标路径必须是项目内相对路径: %r" % value)
    return value


def _entry(block, item, index, problems):
    """Validate one mapping entry's keys; returns it, or None on error."""
    where = "%s[%d]" % (block, index)
    if not isinstance(item, dict):
        problems.append("%s: 条目必须是对象，实际为 %s" % (where, type(item).__name__))
        return None
    keys = set(item)
    missing = REQUIRED_KEYS[block] - keys
    unknown = keys - REQUIRED_KEYS[block] - OPTIONAL_KEYS.get(block, set())
    if missing:
        problems.append("%s: 缺少字段 %s" % (where, ", ".join(sorted(missing))))
    if unknown:
        problems.append("%s: 未知映射字段 %s" % (where, ", ".join(sorted(unknown))))
    return item


def _expect_list_of_str(block, value, problems):
    if not isinstance(value, list) or not all(isinstance(x, str) for x in value):
        problems.append("%s: 必须是非空字符串数组" % block)
        return []
    return value


def install_entries(blocks):
    """Return [{'dest','source','group'}]; raises Problem on structural errors."""
    entries = []
    agents = blocks.get("install-agents") or {}
    if not isinstance(agents, dict):
        raise Problem("install-agents: 必须是对象")
    for source in ("install-readmes", "install-hubs"):
        if not isinstance(blocks.get(source), list):
            raise Problem("%s: 必须是数组" % source)
    entries.append({"dest": rel_target(agents.get("target_file")),
                    "source": agents.get("template"), "group": "agents"})
    for item in blocks["install-readmes"]:
        entries.append({"dest": rel_target(item.get("readme")),
                        "source": item.get("template"), "group": "readmes"})
    for item in blocks["install-hubs"]:
        entries.append({"dest": rel_target(item.get("dest")),
                        "source": item.get("template"), "group": "hubs"})
    return entries


def _source_ok(source):
    if not isinstance(source, str) or not source:
        return False
    if Path(source).is_absolute() or "\\" in source or ".." in Path(source).parts:
        return False
    return source.startswith("templates/") or source.startswith("scripts/")


def _load_verifier(root):
    spec = importlib.util.spec_from_file_location(
        "adflow_verify_package_check", str(root / "scripts" / "adflow_verify.py"))
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


def verify(root):
    """Return a list of human-readable problems; [] means consistent."""
    root = Path(root)
    problems = []
    text = (root / "workflow.yaml").read_text(encoding="utf-8")
    blocks, block_problems = load_blocks(text)
    problems += block_problems

    missing = set(BLOCK_TYPES) - set(blocks)
    unknown = set(blocks) - set(BLOCK_TYPES)
    if missing:
        problems.append("workflow.yaml: 缺少 manifest 块 %s" % ", ".join(sorted(missing)))
    if unknown:
        problems.append("workflow.yaml: 未知 manifest 块 %s" % ", ".join(sorted(unknown)))
    fatal = False
    for name, kind in BLOCK_TYPES.items():
        if name in blocks and not isinstance(blocks[name], kind):
            problems.append("%s: 期望 %s，实际 %s" % (name, kind.__name__, type(blocks[name]).__name__))
            fatal = True
    if fatal or missing:
        return problems

    # ---- entry shape ----
    if isinstance(blocks.get("install-agents"), dict):
        _entry("install-agents", blocks["install-agents"], 0, problems)
    for block in ("install-readmes", "install-hubs", "upgrade-targets"):
        for index, item in enumerate(blocks.get(block) or []):
            _entry(block, item, index, problems)
    for block in ("verifier-files", "required-files", "forbidden-files",
                  "upgrade-readmes", "upgrade-retire"):
        if block in blocks:
            _expect_list_of_str(block, blocks[block], problems)

    # ---- install graph ----
    try:
        entries = install_entries(blocks)
    except Problem as e:
        problems.append(str(e))
        return problems

    dests = [e["dest"] for e in entries]
    duplicates = sorted({d for d in dests if dests.count(d) > 1})
    if duplicates:
        problems.append("安装目的地重复: %s" % ", ".join(duplicates))
    verifier_set = set(blocks.get("verifier-files") or [])
    for entry in entries:
        expected_root = "scripts/" if entry["dest"] in verifier_set else "templates/"
        if not _source_ok(entry["source"]) or not entry["source"].startswith(expected_root):
            problems.append("%s: 模板路径必须是项目内 %s 下的相对路径: %r"
                            % (entry["dest"], expected_root, entry["source"]))
        elif not (root / entry["source"]).is_file():
            problems.append("%s: 模板不存在: %s" % (entry["dest"], entry["source"]))
    for block in ("required-files", "verifier-files", "forbidden-files"):
        values = blocks.get(block) or []
        if len(values) != len(set(values)):
            problems.append("%s: 存在重复条目" % block)

    for item in blocks.get("install-readmes") or []:
        try:
            if rel_target(item.get("dir")) != str(Path(rel_target(item.get("readme"))).parent):
                problems.append("%s: dir 必须是 readme 的父目录" % rel_target(item.get("readme")))
        except Problem as e:
            problems.append(str(e))

    verifier = set(blocks.get("verifier-files") or [])
    governance = [e for e in entries if e["dest"] not in verifier]
    governance_set = {e["dest"] for e in governance}
    required = set(blocks.get("required-files") or [])
    if len(governance) != 24:
        problems.append("治理文件映射应为 24 项，实际 %d 项" % len(governance))
    if governance_set != required:
        only_map = sorted(governance_set - required)
        only_req = sorted(required - governance_set)
        problems.append("安装映射与 required_files_exist 不一致: 映射多出 %r，清单多出 %r"
                        % (only_map, only_req))
    hubs = {e["dest"] for e in entries if e["group"] == "hubs"}
    if verifier - hubs:
        problems.append("verifier_files_required 未出现在 Step 6 映射中: %s"
                        % ", ".join(sorted(verifier - hubs)))
    if len(verifier) != 2:
        problems.append("校验器文件应为 2 项，实际 %d 项" % len(verifier))

    # ---- ownership ----
    def owner(dest):
        if "/" not in dest:
            return "root"
        if dest.startswith("docs/standards/"):
            return "docs/standards"
        return dest.split("/", 1)[0]

    owners = {}
    for dest in dests:
        owners.setdefault(owner(dest), set()).add(dest)
    expected_owners = {
        "root": {"AGENTS.md", "CHANGELOG.md"},
        "docs/standards": {"docs/standards/coding.json",
                           "docs/standards/change-template.json",
                           "docs/standards/task-template.json"},
        "scripts": {"scripts/adflow_verify.py", "scripts/adflow-verify"},
    }
    for name, expected in expected_owners.items():
        if owners.get(name) != expected:
            problems.append("%s 归属不符: 期望 %r，实际 %r"
                            % (name, sorted(expected), sorted(owners.get(name) or [])))
    if set(owners) - {"root", "docs", "docs/standards", "scripts"}:
        problems.append("存在未声明的顶层归属: %s"
                        % ", ".join(sorted(set(owners) - {"root", "docs", "docs/standards", "scripts"})))

    # ---- assets ----
    used = {e["source"] for e in entries}
    templates = {str(p.relative_to(root)) for p in (root / "templates").rglob("*.tpl")}
    orphans = sorted(templates - used)
    if orphans:
        problems.append("存在未挂接的模板: %s" % ", ".join(orphans))
    for asset in sorted((root / "templates").rglob("*.json")) + \
            sorted((root / "templates").rglob("*.json.tpl")) + \
            sorted((root / "examples").glob("*.json")):
        try:
            json.loads(asset.read_text(encoding="utf-8"))
        except Exception as e:  # noqa: BLE001
            problems.append("%s: JSON 无法解析: %s" % (asset.relative_to(root), e))

    try:
        devel_tpl = json.loads((root / "templates/docs/devel-index.json.tpl")
                               .read_text(encoding="utf-8"))
    except Exception:  # noqa: BLE001 - 解析失败已由上一段报告
        devel_tpl = None
    if isinstance(devel_tpl, dict):
        subsystems = devel_tpl.get("subsystems")
        design = next((s for s in subsystems if isinstance(s, dict) and s.get("name") == "design"),
                      None) if isinstance(subsystems, list) else None
        if not isinstance(design, dict):
            problems.append("docs/devel/index.json 模板缺少 design 子系统")
        elif not isinstance(design.get("designs"), list):
            problems.append("docs/devel/index.json 模板的 design 子系统缺少 designs 数组")

    m = LANGS_RE.search(text)
    if not m:
        problems.append("workflow.yaml: 缺少 available_languages 列表")
    else:
        try:
            langs = set(json.loads(m.group(1)))
        except Exception as e:  # noqa: BLE001
            problems.append("workflow.yaml: available_languages 无法解析: %s" % e)
            langs = set()
        fragments = {p.stem for p in (root / "templates" / "coding-standards").glob("*.json")}
        if langs != fragments:
            problems.append("available_languages 与语言片段不一致: 清单多出 %r，片段多出 %r"
                            % (sorted(langs - fragments), sorted(fragments - langs)))

    # ---- upgrade mappings ----
    if blocks.get("upgrade-agents") != blocks.get("install-agents", {}).get("template"):
        problems.append("U2 同步模板与 Step 4 安装模板不一致")
    readme_dests = {e["dest"] for e in entries if e["group"] == "readmes"}
    if set(blocks.get("upgrade-readmes") or []) != readme_dests:
        problems.append("U3 同步目标与 Step 5 README 映射不一致")
    sources = {e["dest"]: e["source"] for e in entries}
    for index, item in enumerate(blocks.get("upgrade-targets") or []):
        if not isinstance(item, dict):
            continue
        dest = item.get("dest")
        if dest not in sources:
            problems.append("upgrade-targets[%d]: %r 不是受管理的安装资产" % (index, dest))
            continue
        if item.get("template") != sources[dest]:
            problems.append("upgrade-targets[%d]: %s 的模板与安装映射不一致（%r != %r）"
                            % (index, dest, item.get("template"), sources[dest]))
        if not _source_ok(item.get("template")) or not (root / item.get("template")).is_file():
            problems.append("upgrade-targets[%d]: 模板不存在: %r" % (index, item.get("template")))
    if sorted(blocks.get("upgrade-retire") or []) != ["docs/devel/change/template.json",
                                                     "docs/devel/task/template.json"]:
        problems.append("upgrade-retire 必须只退役旧的 C/T 模板副本")

    # ---- verifier constants ----
    try:
        verifier_module = _load_verifier(root)
    except Exception as e:  # noqa: BLE001
        problems.append("无法载入校验器常量: %s" % e)
        verifier_module = None
    if verifier_module is not None:
        expected_governance = set(verifier_module.BASE_FILES) | set(
            verifier_module.STANDARD_FILES.values())
        if governance_set != expected_governance:
            problems.append("安装映射与校验器 BASE_FILES/STANDARD_FILES 不一致: 映射多出 %r，校验器多出 %r"
                            % (sorted(governance_set - expected_governance),
                               sorted(expected_governance - governance_set)))
        if verifier != set(verifier_module.TOOL_FILES):
            problems.append("verifier_files_required 与校验器 TOOL_FILES 不一致")
        legacy = set(verifier_module.LEGACY_FILES) - governance_set
        if legacy:
            problems.append("校验器 LEGACY_FILES 的 canonical 路径不在安装映射中: %s"
                            % ", ".join(sorted(legacy)))
        legacy_overlap = set(verifier_module.LEGACY_FILES.values()) & governance_set
        if legacy_overlap:
            problems.append("旧布局路径不得作为新装目的地: %s" % ", ".join(sorted(legacy_overlap)))
        if verifier_module.PLACEHOLDER not in set(blocks.get("forbidden-files") or []):
            problems.append("forbidden_files_not_exist 未包含校验器的占位设计路径")

        # ---- version anchors ----
        version = verifier_module.VERSION
        if (root / "templates" / "AGENTS.md.tpl").read_text(encoding="utf-8").count(
                "initialized v%s" % version) < 1:
            problems.append("AGENTS 模板未携带当前版本标签 v%s" % version)
        try:
            index_tpl = json.loads((root / "templates" / "docs" / "index.json.tpl")
                                   .read_text(encoding="utf-8"))
        except Exception as e:  # noqa: BLE001
            problems.append("docs/index.json 模板无法解析: %s" % e)
        else:
            if index_tpl.get("adflow_version") != version:
                problems.append("docs/index.json 模板的 adflow_version 与 VERSION 不一致")
        if ('canonical_tag: "<!-- @ad-flow: initialized v%s -->"' % version) not in text:
            problems.append("workflow.yaml 的 canonical_tag 未携带当前版本")
        if re.search(r'^\s+value: "%s"$' % re.escape(version), text, re.M) is None:
            problems.append("workflow.yaml 的 U5 版本值未携带当前版本")

    # ---- permissions ----
    wrapper = root / "scripts" / "adflow-verify"
    if not wrapper.is_file():
        problems.append("缺少 scripts/adflow-verify")
    elif not os.access(str(wrapper), os.X_OK):
        problems.append("scripts/adflow-verify 缺少可执行权限")

    return problems


def main(argv=None):
    ap = argparse.ArgumentParser(description="Validate ad-flow workflow manifests and package assets")
    ap.add_argument("--root", default=str(Path(__file__).resolve().parents[1]), help=argparse.SUPPRESS)
    args = ap.parse_args(argv)
    problems = verify(Path(args.root))
    for problem in problems:
        print(problem)
    print("package: %s" % ("consistent" if not problems else "%d problem(s)" % len(problems)))
    return 1 if problems else 0


if __name__ == "__main__":
    sys.exit(main())
