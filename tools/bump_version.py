#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""Maintainer tool: keep every ad-flow governance version site in sync and cut a release.

  python3 tools/bump_version.py --check                   # all sites agree with scripts/adflow_verify.py
  python3 tools/bump_version.py 1.6.0 [--date YYYY-MM-DD]  # bump every site, move [Unreleased] to [1.6.0]

The tool only edits files. Commit, tag and push stay manual (see README, "技能维护与发版").
It is not installed into target projects.
"""
import argparse
import re
import sys
from datetime import date
from pathlib import Path

REPO_URL = "https://github.com/4everSivan/ad-flow"
SEMVER = r"(\d+\.\d+\.\d+)"
# (file, pattern): every `{v}` is a version site that must equal the tool VERSION.
# A pattern that stops matching fails --check, so reworded lines are noticed rather than skipped.
SITES = [
    ("scripts/adflow_verify.py", r'^VERSION = "{v}"'),
    ("workflow.yaml", r'^version: "{v}"'),
    ("workflow.yaml", r'current_version: "{v}"'),
    ("workflow.yaml", r'templates to v{v}"'),
    ("workflow.yaml", r'canonical_tag: "<!-- @ad-flow: initialized v{v} -->"'),
    ("workflow.yaml", r'value: "{v}"'),
    ("SKILL.md", r'Current governance version: \*\*{v}\*\*'),
    ("SKILL.md", r'\| Version equals {v} \|'),
    ("SKILL.md", r'\| Version newer than {v} \|'),
    ("SKILL.md", r'with `<!-- @ad-flow: initialized v{v} -->`'),
    ("SKILL.md", r'`docs/index\.json\.adflow_version` to `{v}`'),
    ("README.md", r'当前治理规范版本：\[\*\*{v}\*\*\]\(%s/releases/tag/v{v}\)' % re.escape(REPO_URL)),
    ("README.md", r'initialized v{v} -->'),
    ("README.md", r'\| 低于 {v}，'),
    ("README.md", r'\| 等于 {v} \|'),
    ("README.md", r'\| 高于 {v} \|'),
    ("references/01-mental-model.md", r'initialized v{v} -->'),
    ("references/01-mental-model.md", r'"adflow_version": "{v}"'),
    ("templates/AGENTS.md.tpl", r'initialized v{v} -->'),
    ("templates/AGENTS.md.tpl", r'\(ad-flow v{v}\)'),
    ("templates/docs/index.json.tpl", r'"adflow_version": "{v}"'),
    ("templates/docs/standards/change-template.json.tpl", r'"tool": "adflow-verify",\s*"version": "{v}"'),
    ("templates/docs/standards/task-template.json.tpl", r'"tool": "adflow-verify",\s*"version": "{v}"'),
]
CHANGELOG = "CHANGELOG.md"
UNRELEASED_RE = re.compile(r"^## \[Unreleased\][^\n]*\n(.*?)(?=^## \[)", re.M | re.S)
UNRELEASED_LINK_RE = re.compile(r"^\[Unreleased\]: .*$", re.M)


def parse(v):
    return tuple(int(p) for p in v.split("."))


def tool_version(root):
    m = re.search(r'^VERSION = "([^"]+)"', (root / SITES[0][0]).read_text(encoding="utf-8"), re.M)
    if not m or not re.fullmatch(SEMVER, m.group(1)):
        raise SystemExit("cannot read VERSION from %s" % SITES[0][0])
    return m.group(1)


def site_matches(root):
    """Yield (rel, pattern, match) per site; match is None when the site is missing."""
    for rel, pat in SITES:
        text = (root / rel).read_text(encoding="utf-8")
        found = list(re.finditer(pat.replace("{v}", SEMVER), text, re.M))
        for m in found or [None]:
            yield rel, pat, m


def check(root, expected):
    problems = []
    for rel, pat, m in site_matches(root):
        if m is None:
            problems.append("%s: version site not found: %s" % (rel, pat))
        elif set(m.groups()) != {expected}:
            problems.append("%s: %r should carry %s" % (rel, m.group(0), expected))
    log = (root / CHANGELOG).read_text(encoding="utf-8")
    if not re.search(r"^## \[%s\] - \d{4}-\d{2}-\d{2}$" % re.escape(expected), log, re.M):
        problems.append("%s: missing release heading ## [%s] - YYYY-MM-DD" % (CHANGELOG, expected))
    if not re.search(r"^\[%s\]: %s/" % (re.escape(expected), re.escape(REPO_URL)), log, re.M):
        problems.append("%s: missing link reference [%s]" % (CHANGELOG, expected))
    want = "[Unreleased]: %s/compare/v%s...HEAD" % (REPO_URL, expected)
    if want not in log:
        problems.append("%s: expected link %s" % (CHANGELOG, want))
    return problems


def bump(root, new, day):
    current = tool_version(root)
    if parse(new) <= parse(current):
        raise SystemExit("new version %s must be greater than current %s" % (new, current))
    problems = check(root, current)
    if problems:
        raise SystemExit("fix the current release state first:\n  " + "\n  ".join(problems))

    log = (root / CHANGELOG).read_text(encoding="utf-8")
    section = UNRELEASED_RE.search(log)
    if not section or not re.search(r"^- ", section.group(1), re.M):
        raise SystemExit("[Unreleased] has no entries; record the changes before releasing")
    log = (log[:section.start(1)] + "\n## [%s] - %s\n\n" % (new, day)
           + section.group(1).lstrip("\n") + log[section.end(1):])
    log = UNRELEASED_LINK_RE.sub(
        "[Unreleased]: %s/compare/v%s...HEAD\n[%s]: %s/compare/v%s...v%s"
        % (REPO_URL, new, new, REPO_URL, current, new), log, count=1)

    # Rewrite every site in memory first so a missing site never leaves a half-bumped tree.
    texts = {CHANGELOG: log}
    for rel, pat in SITES:
        text = texts.get(rel) or (root / rel).read_text(encoding="utf-8")

        def swap(m):
            s, base = m.group(0), m.start(0)
            for i in range(len(m.groups()), 0, -1):
                s = s[:m.start(i) - base] + new + s[m.end(i) - base:]
            return s
        text, n = re.subn(pat.replace("{v}", SEMVER), swap, text, flags=re.M)
        if not n:
            raise SystemExit("%s: version site not found: %s" % (rel, pat))
        texts[rel] = text
    for rel, text in texts.items():
        (root / rel).write_text(text, encoding="utf-8")
    problems = check(root, new)
    if problems:
        raise SystemExit("bump left inconsistencies:\n  " + "\n  ".join(problems))
    return current


def main(argv=None):
    ap = argparse.ArgumentParser(description="Bump or check ad-flow governance version sites")
    ap.add_argument("version", nargs="?", help="new version X.Y.Z; omit with --check")
    ap.add_argument("--check", action="store_true", help="verify all sites agree; no writes")
    ap.add_argument("--date", default=date.today().isoformat(), help="release date, default today")
    ap.add_argument("--root", default=str(Path(__file__).resolve().parents[1]), help=argparse.SUPPRESS)
    args = ap.parse_args(argv)
    root = Path(args.root)
    if args.check == bool(args.version):
        ap.error("pass either a new version or --check")
    if args.check:
        current = tool_version(root)
        problems = check(root, current)
        for p in problems:
            print(p)
        print("version %s: %s" % (current, "consistent" if not problems else "%d problem(s)" % len(problems)))
        return 1 if problems else 0
    if not re.fullmatch(SEMVER, args.version):
        ap.error("version must be X.Y.Z")
    if not re.fullmatch(r"\d{4}-\d{2}-\d{2}", args.date):
        ap.error("--date must be YYYY-MM-DD")
    old = bump(root, args.version, args.date)
    print("bumped %s -> %s. Next: run the tests, commit 'chore(release): publish v%s', "
          "then tag that commit v%s." % (old, args.version, args.version, args.version))
    return 0


if __name__ == "__main__":
    sys.exit(main())
