#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""adflow-verify —— ad-flow 流程纪律的可执行校验层（方案 W：纯工作流内嵌，无钩子/CI）。

把 ad-flow 的不变量与双轨卡片 SOP 从"散文要求"变成"可机械判定"的门禁：
  * 流程门禁（默认）：状态感知地扫描活跃卡（docs/devel/change、docs/devel/task），
    按每张卡当前的 status 只校验"该状态此刻应成立的前提"（P1-P14）。
  * 初始化 DoD（--mode init）：一次性核对 23 个基础治理文件、禁占位、版本标签。

设计原则：
  * 仅用标准库，栈无关——可在任意目标工程里运行。
  * 退出码对齐 references/05-audit-checklist：0 干净 / 4 确定性违规 / 6 仅软告警。
  * 只读；除非 --record（由工具把自己真实的运行结果回写进卡片 gate 块）。
  * gate 证伪：声称 exit_code==0 的终态卡，会被独立复算，矛盾即 GATE_CLAIM_CONTRADICTION。

用法：
  adflow-verify [target_dir=.] [--json] [--warn-only] [--mode init] [--record]
"""
import argparse
import json
import re
import subprocess
import sys
from datetime import date
from pathlib import Path

VERSION = "1.1.0"

# ---- 常量 ----
TOPIC_RE = re.compile(r"<!--\s*@topic:\s*([A-Za-z0-9_]+)\s*-->")
TAG_RE = re.compile(r"@ad-flow:\s*initialized(?:\s+v([0-9.]+))?")
RUNID_RE = re.compile(r"^(\d+|local-[\d\-]+)$")              # 纯数字或 local-YYYYMMDD-HH，禁内网
CARD_ID_RE = re.compile(r"\b([CT]\d{2,3})\b")                # Cxxx / Txx
SRC_PATH_RE = re.compile(r"(?:^|/)(src|app|lib|cmd|internal)/[\w/.\-]+\.\w+")
CANNED_QUOTES = {"已确认", "确认", "已通过", "同意", "ok", "yes", "done", "tested", "lgtm"}
PATH_KEYS = {"files", "file", "paths", "file_path", "filepath", "sources"}
TERMINAL = {"verified", "closed", "completed"}
CLOSED = {"closed", "completed"}

# workflow.yaml Step 8 的 23 个基础治理文件
BASE_FILES = [
    "AGENTS.md", "CHANGELOG.md",
    "docs/README.md", "docs/index.json", "docs/assets/README.md",
    "docs/guide/README.md", "docs/guide/index.json", "docs/guide/01-本地部署指南.md",
    "docs/devel/README.md", "docs/devel/index.json", "docs/devel/design/README.md",
    "docs/devel/change/README.md", "docs/devel/change/index.json", "docs/devel/change/template.json",
    "docs/devel/task/README.md", "docs/devel/task/index.json", "docs/devel/task/template.json",
    "docs/devel/todo/README.md", "docs/devel/todo/now.md", "docs/devel/todo/future.md",
    "docs/devel/env/README.md", "docs/devel/env/01-环境缓存与依赖清理指南.md",
    "docs/archive/README.md",
]
PLACEHOLDER = "docs/devel/design/01-系统设计方案.md"


class Ctx:
    """一次运行的共享上下文。"""

    def __init__(self, root):
        self.root = Path(root).resolve()
        self.findings = []          # list[dict(sev, code, card, path, msg)]
        self._json_cache = {}
        self._text_cache = {}
        self._git = None            # None=未知, True/False

    # ---- 基础读取 ----
    def read_text(self, rel):
        if rel not in self._text_cache:
            p = self.root / rel
            self._text_cache[rel] = p.read_text(encoding="utf-8") if p.exists() else None
        return self._text_cache[rel]

    def load_json(self, rel):
        if rel not in self._json_cache:
            p = self.root / rel
            if not p.exists():
                self._json_cache[rel] = None
            else:
                try:
                    self._json_cache[rel] = json.loads(p.read_text(encoding="utf-8"))
                except Exception as e:  # noqa: BLE001
                    self.add("ERROR", "JSON_PARSE", None, rel, "JSON 解析失败: %s" % e)
                    self._json_cache[rel] = None
        return self._json_cache[rel]

    def exists(self, rel):
        return (self.root / rel).exists()

    def topics_in(self, rel):
        txt = self.read_text(rel)
        return set(TOPIC_RE.findall(txt)) if txt else set()

    def git_ok(self):
        if self._git is None:
            try:
                subprocess.run(["git", "rev-parse", "--is-inside-work-tree"],
                               cwd=self.root, stdout=subprocess.DEVNULL,
                               stderr=subprocess.DEVNULL, check=True)
                self._git = True
            except Exception:  # noqa: BLE001
                self._git = False
        return self._git

    def is_ancestor(self, commit):
        """commit 是否为 HEAD 祖先。True/False；无 git 返回 None。"""
        if not self.git_ok():
            return None
        if not commit:
            return False
        try:
            r = subprocess.run(["git", "merge-base", "--is-ancestor", str(commit), "HEAD"],
                               cwd=self.root, stdout=subprocess.DEVNULL,
                               stderr=subprocess.DEVNULL)
            return r.returncode == 0
        except Exception:  # noqa: BLE001
            return None

    # ---- findings ----
    def add(self, sev, code, card, path, msg):
        self.findings.append({"sev": sev, "code": code, "card": card, "path": path, "msg": msg})

    def hard(self, code, card, path, msg):
        self.add("ERROR", code, card, path, msg)

    def soft(self, code, card, path, msg):
        self.add("WARN", code, card, path, msg)


def is_readme(rel):
    return Path(rel).name.lower() == "readme.md"


def checks_of(card):
    """变更轨读 verification.checks，任务轨读 acceptance.checks。"""
    if isinstance(card.get("verification"), dict) and card["verification"].get("checks"):
        return card["verification"]["checks"]
    if isinstance(card.get("acceptance"), dict) and card["acceptance"].get("checks"):
        return card["acceptance"]["checks"]
    return []


def runid_ok(rid):
    rid = str(rid or "").strip()
    return bool(RUNID_RE.match(rid)) and "http" not in rid and "://" not in rid


# ---- 单卡结构校验（与终态无关，任何 status 都查）----
def check_structural(ctx, card, cid, rel):
    t = card.get("target", {}) or {}
    doc = t.get("design_doc")
    topic = t.get("design_topic")

    # P1 设计挂接
    if not doc:
        ctx.hard("DESIGN_DOC_MISSING", cid, rel, "缺少 target.design_doc（文档先行：必须先挂接现行基线设计）")
    elif is_readme(doc):
        ctx.hard("NO_README_AS_DESIGN_DOC", cid, rel, "design_doc 指向 README: %s" % doc)
    elif not ctx.exists(doc):
        ctx.hard("DESIGN_DOC_MISSING", cid, rel, "设计文档不存在: %s" % doc)
    elif topic and topic not in ctx.topics_in(doc):
        ctx.hard("TOPIC_ANCHOR_MISSING", cid, rel, "@%s 锚标未出现在 %s" % (topic, doc))

    # P5 二值契约对称
    for c in checks_of(card):
        ti = str(c.get("true_if", "")).strip()
        fi = str(c.get("false_if", "")).strip()
        if not ti or not fi:
            ctx.hard("CONTRACT_INCOMPLETE", cid, rel, "checks[].true_if/false_if 不完整: %r" % c.get("item"))
        elif ti == fi:
            ctx.hard("CONTRACT_SYMMETRIC", cid, rel, "true_if 与 false_if 相同: %r" % c.get("item"))

    # P12 悬空依赖（任务卡，任何状态都查存在性）
    for dep in card.get("depends_on", []) or []:
        if dep not in ctx.all_ids:
            ctx.hard("DEP_DANGLING", cid, rel, "depends_on 引用了不存在的卡: %s" % dep)

    # P6 脱钩物理路径（软）
    def scan(obj):
        if isinstance(obj, dict):
            for k, v in obj.items():
                if k in PATH_KEYS:
                    vals = v if isinstance(v, list) else [v]
                    for s in vals:
                        if isinstance(s, str) and SRC_PATH_RE.search(s):
                            ctx.soft("DECOUPLING_VIOLATION", cid, rel,
                                     "卡片硬编码源码物理路径（应只声明 module/component/capability）: %s" % s)
                else:
                    scan(v)
        elif isinstance(obj, list):
            for v in obj:
                scan(v)
    scan(card)


# ---- 单卡终态前置（状态感知）----
def check_state(ctx, card, cid, rel, track):
    status = card.get("status")
    checks = checks_of(card)
    v = card.get("verification", {}) if isinstance(card.get("verification"), dict) else {}
    acc = card.get("acceptance", {}) if isinstance(card.get("acceptance"), dict) else {}
    run_id = v.get("run_id") or acc.get("run_id")
    quote = v.get("user_quote")
    signoff = v.get("signoff")

    if status in TERMINAL:
        if not runid_ok(run_id):
            ctx.hard("EVIDENCE_RUNID", cid, rel, "run_id 为空或含内网/非法格式: %r" % run_id)
        if track == "change":
            if not str(quote or "").strip():
                ctx.hard("EVIDENCE_QUOTE", cid, rel, "缺少人类原话 user_quote（严禁 AI 自导自演代签）")
            elif str(quote).strip().lower() in CANNED_QUOTES or len(str(quote).strip()) < 6:
                ctx.soft("EVIDENCE_QUOTE_CANNED", cid, rel, "user_quote 疑似套话: %r" % quote)
            if not str(signoff or "").strip():
                ctx.hard("EVIDENCE_SIGNOFF", cid, rel, "缺少 signoff")
        if any(c.get("result") is None for c in checks):
            ctx.hard("CHECK_RESULT_MISSING", cid, rel, "存在 result 未裁决的验收项（二值契约必须落 true/false）")

    if status in CLOSED:
        # P8 commit 祖先
        commit = (card.get("sync", {}) or {}).get("commit")
        anc = ctx.is_ancestor(commit)
        if anc is None:
            ctx.soft("COMMIT_SKIPPED_NO_GIT", cid, rel, "无 git 环境，跳过 commit 祖先校验")
        elif not commit:
            ctx.hard("COMMIT_MISSING", cid, rel, "终态卡缺少 sync.commit")
        elif not anc:
            ctx.hard("COMMIT_NOT_ANCESTOR", cid, rel, "sync.commit 非 HEAD 祖先（疑伪造）: %s" % commit)
        # P9 CHANGELOG 互链（软）
        if status == "closed":
            cl = ctx.read_text("CHANGELOG.md") or ""
            if cid not in cl:
                ctx.soft("CHANGELOG_LINK_MISSING", cid, rel, "closed 卡号未出现在 CHANGELOG.md")
        # P12 前置闭环（任务卡 completed）
        if status == "completed":
            for dep in card.get("depends_on", []) or []:
                dc = ctx.all_ids.get(dep)
                if dc is not None and dc.get("status") != "completed":
                    ctx.hard("DEP_NOT_COMPLETED", cid, rel, "前置任务 %s 尚未 completed" % dep)

    if status == "rejected":
        rej = card.get("rejections") or []
        if not rej or any(not str(r.get("reason", "")).strip() for r in rej):
            ctx.hard("REJECTION_NO_AUDIT", cid, rel, "rejected 卡缺少含 reason 的驳回审计记录")

    # P13 hotfix 超期（软）
    if card.get("is_hotfix") and status in ("draft", "pending", "in_progress"):
        ctx.soft("HOTFIX_OPEN", cid, rel, "hotfix 卡仍未闭环，需在故障恢复后 24h 内补票")

    # P3 gate 追责 + 证伪
    if status in CLOSED:
        gate = card.get("gate", {}) or {}
        if gate.get("exit_code") != 0:
            ctx.hard("GATE_EXIT_NONZERO", cid, rel,
                     "终态卡未记录 adflow-verify gate.exit_code==0（收口前必须过门禁并回写）")


def check_card(ctx, card, cid, rel, track):
    before = len([f for f in ctx.findings if f["card"] == cid and f["sev"] == "ERROR"])
    check_structural(ctx, card, cid, rel)
    check_state(ctx, card, cid, rel, track)
    # gate 证伪：声称已过门禁但实测有硬违规 → 追责
    if card.get("status") in CLOSED and (card.get("gate", {}) or {}).get("exit_code") == 0:
        after = [f for f in ctx.findings if f["card"] == cid and f["sev"] == "ERROR"]
        if len(after) > before:
            ctx.hard("GATE_CLAIM_CONTRADICTION", cid, rel,
                     "卡片声称 gate.exit_code==0，但实测存在硬违规（伪造/漏跑门禁）")


# ---- 全局检查 ----
def check_globals(ctx):
    # P7 卡号唯一
    seen = {}
    for cid in ctx.all_ids:
        seen[cid] = seen.get(cid, 0) + 1
    for cid, n in seen.items():
        if n > 1:
            ctx.hard("ID_DUPLICATE", cid, "-", "卡号在 change/task 全域重复 %d 次（并行防撞号）" % n)

    # P11 零沉淀：todo 行内含已存在卡号
    for todo in ("docs/devel/todo/now.md", "docs/devel/todo/future.md"):
        txt = ctx.read_text(todo)
        if not txt:
            continue
        for i, line in enumerate(txt.splitlines(), 1):
            for m in CARD_ID_RE.findall(line):
                if m in ctx.all_ids:
                    ctx.hard("ZERO_SEDIMENT_VIOLATION", m, "%s:%d" % (todo, i),
                             "todo 残留已建卡事项 %s（落地建卡即应物理删除）" % m)

    # P14 版本一致
    am = ctx.read_text("AGENTS.md") or ""
    tag = TAG_RE.search(am)
    idx = ctx.load_json("docs/index.json") or {}
    ver = idx.get("adflow_version")
    if not tag or not tag.group(1):
        ctx.hard("TAG_MISSING", None, "AGENTS.md", "缺少 <!-- @ad-flow: initialized vX.Y.Z --> 标签")
    elif ver and tag.group(1) != str(ver):
        ctx.hard("VERSION_DRIFT", None, "AGENTS.md",
                 "AGENTS.md 标签 v%s 与 docs/index.json adflow_version=%s 不一致" % (tag.group(1), ver))

    # index.topics 的 design_doc 也不得指向 README / 必须存在 / 含锚标
    for idx_rel in ("docs/devel/change/index.json", "docs/devel/task/index.json"):
        data = ctx.load_json(idx_rel) or {}
        for topic, tinfo in (data.get("topics", {}) or {}).items():
            d = (tinfo or {}).get("design_doc")
            if not d:
                continue
            if is_readme(d):
                ctx.hard("INDEX_TOPIC_README", None, idx_rel, "topics[%s].design_doc 指向 README: %s" % (topic, d))
            elif not ctx.exists(d):
                ctx.hard("DESIGN_DOC_MISSING", None, idx_rel, "topics[%s].design_doc 不存在: %s" % (topic, d))
            elif topic not in ctx.topics_in(d):
                ctx.hard("TOPIC_ANCHOR_MISSING", None, idx_rel, "topics[%s] 锚标未出现在 %s" % (topic, d))


# ---- 采集活跃卡 ----
def collect_cards(ctx):
    ctx.all_ids = {}
    cards = []  # (rel, dict, cid)
    for sub in ("docs/devel/change", "docs/devel/task"):
        idx_rel = sub + "/index.json"
        idx = ctx.load_json(idx_rel) or {}
        reg = idx.get("cards", {}) or {}
        d = ctx.root / sub
        if not d.exists():
            continue
        for jf in sorted(d.glob("*.json")):
            if jf.name in ("index.json", "template.json"):
                continue
            rel = str(jf.relative_to(ctx.root))
            card = ctx.load_json(rel)
            if card is None:
                continue
            cid = str(card.get("id", jf.stem))
            cards.append((rel, card, cid))
            ctx.all_ids[cid] = card
            # P2 中枢对齐
            ent = reg.get(cid)
            if ent is None:
                ctx.hard("INDEX_MISSING_CARD", cid, rel, "卡片未登记到 %s" % idx_rel)
            else:
                if ent.get("status") != card.get("status"):
                    ctx.hard("INDEX_STATUS_DRIFT", cid, idx_rel,
                             "索引状态 %r 与卡片 %r 不一致" % (ent.get("status"), card.get("status")))
                f = ent.get("file")
                if f and not ctx.exists(f):
                    ctx.hard("INDEX_FILE_DEAD", cid, idx_rel, "索引 file 路径失效: %s" % f)
    return cards


# ---- 初始化 DoD ----
def run_init(ctx):
    for f in BASE_FILES:
        if not ctx.exists(f):
            ctx.hard("BASE_FILE_MISSING", None, f, "缺少基础治理文件（应 >=23）")
    if ctx.exists(PLACEHOLDER):
        ctx.hard("PLACEHOLDER_DESIGN_EXISTS", None, PLACEHOLDER, "存在禁用占位设计文档")
    am = ctx.read_text("AGENTS.md") or ""
    if not TAG_RE.search(am):
        ctx.hard("TAG_MISSING", None, "AGENTS.md", "缺少 @ad-flow 初始化版本标签")


# ---- --record：把本次真实结果回写进卡片 gate 块 ----
def record_gates(ctx, cards):
    for rel, card, cid in cards:
        errs = [f for f in ctx.findings if f["card"] == cid and f["sev"] == "ERROR"]
        warns = [f for f in ctx.findings if f["card"] == cid and f["sev"] == "WARN"]
        code = 4 if errs else (6 if warns else 0)
        card["gate"] = {"tool": "adflow-verify", "version": VERSION,
                        "ran_at": date.today().isoformat(), "exit_code": code}
        p = ctx.root / rel
        p.write_text(json.dumps(card, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")


# ---- 报告 ----
def summarize(ctx):
    errs = [f for f in ctx.findings if f["sev"] == "ERROR"]
    warns = [f for f in ctx.findings if f["sev"] == "WARN"]
    code = 4 if errs else (6 if warns else 0)
    return errs, warns, code


def report(ctx, mode, as_json, warn_only):
    errs, warns, code = summarize(ctx)
    if warn_only:
        code = 0 if not warns else 6
        for f in ctx.findings:
            f["sev"] = "WARN"
        errs, warns = [], ctx.findings
    if as_json:
        print(json.dumps({"tool": "adflow-verify", "version": VERSION, "mode": mode,
                          "target": str(ctx.root), "exit_code": code,
                          "summary": {"errors": len(errs), "warnings": len(warns)},
                          "findings": ctx.findings}, ensure_ascii=False, indent=2))
    else:
        print("adflow-verify v%s  mode=%s  target=%s" % (VERSION, mode, ctx.root))
        for f in ctx.findings:
            loc = f["path"] if f["card"] in (None, "-") else "%s [%s]" % (f["path"], f["card"])
            print("  [%s] %-24s %s: %s" % (f["sev"], f["code"], loc, f["msg"]))
        print("summary: %d error(s), %d warning(s)" % (len(errs), len(warns)))
        print("exit code: %d" % code)
    return code


def main(argv=None):
    ap = argparse.ArgumentParser(description="ad-flow 流程纪律可执行校验层（方案 W）")
    ap.add_argument("target_dir", nargs="?", default=".", help="目标工程根目录，默认当前目录")
    ap.add_argument("--json", action="store_true", help="JSON 输出，供 CI/Agent 消费")
    ap.add_argument("--warn-only", action="store_true", help="全部降级为告警，不阻断（试点期）")
    ap.add_argument("--mode", choices=["process", "init"], default="process",
                    help="process=流程门禁(默认)；init=初始化 DoD")
    ap.add_argument("--record", action="store_true", help="把本次各卡真实结果回写进卡片 gate 块")
    args = ap.parse_args(argv)

    ctx = Ctx(args.target_dir)
    if args.mode == "init":
        run_init(ctx)
    else:
        cards = collect_cards(ctx)
        for rel, card, cid in cards:
            track = "change" if "/devel/change/" in rel else "task"
            check_card(ctx, card, cid, rel, track)
        check_globals(ctx)
        if args.record:
            record_gates(ctx, cards)

    code = report(ctx, args.mode, args.json, args.warn_only)
    return code


if __name__ == "__main__":
    sys.exit(main())
