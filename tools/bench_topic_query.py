#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""T03 基准：对比 `--topic` 全量查询与 `--scope active|history` 的读取量和延迟。

  python3 tools/bench_topic_query.py [--tiers 0,500,2000,5000] [--runs 20]

构造固定 20 个归档批次；Core 主题固定命中 3 张活跃卡和 5 张历史卡，其余归档卡
不属于查询主题。读取计数在进程内统计，延迟用独立 CLI 进程预热后测量。
结果写入 local/bench/（不纳入版本控制）。
"""
import argparse
import json
import statistics
import subprocess
import sys
import tempfile
import time
from contextlib import redirect_stdout
from datetime import datetime
from io import StringIO
from pathlib import Path
from unittest import mock

REPO = Path(__file__).resolve().parents[1]
TOOL = REPO / "scripts" / "adflow_verify.py"
sys.path.insert(0, str(REPO / "scripts"))
import adflow_verify as av  # noqa: E402

DESIGN = "docs/devel/design/01-core.md"


def write(root, rel, text):
    path = root / rel
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(text, encoding="utf-8")


def write_json(root, rel, value):
    write(root, rel, json.dumps(value, ensure_ascii=False))


def card(cid, title, version):
    return {"id": cid, "title": title, "version": version, "status": "pending",
            "target": {"design_doc": DESIGN, "design_topic": "Core"},
            "verification": {"run_id": "local-20261117-01", "checks": [
                {"item": "行为", "true_if": "正常", "false_if": "异常",
                 "result": None, "evidence": ""}]}}


def build(root, archived, batches=20):
    root.mkdir(parents=True, exist_ok=True)
    write(root, "AGENTS.md", "<!-- @ad-flow: initialized v%s -->" % av.VERSION)
    write_json(root, "docs/index.json", {"adflow_version": av.VERSION})
    write(root, "docs/devel/design/01-core.md",
          "<!-- @topic: Core -->\n\n# Core\n\n<!-- @topic: Bulk -->\n")
    write_json(root, "docs/devel/task/index.json", {"tasks": {}, "topics": {}})

    active_ids = ["C001", "C002", "C003"]
    cards = {}
    for cid in active_ids:
        write_json(root, "docs/devel/change/%s.json" % cid, card(cid, "active-" + cid, "v1.0.0"))
        cards[cid] = {"status": "pending", "file": "docs/devel/change/%s.json" % cid}
    write_json(root, "docs/devel/change/index.json", {
        "topics": {"Core": {"design_doc": DESIGN, "changes": active_ids}},
        "cards": cards})

    core_total = min(5, archived)
    bulk_total = archived - core_total
    per_batch = [0] * batches
    for i in range(archived):
        per_batch[i % batches] += 1
    core_by_batch = {i: [] for i in range(batches)}
    for i in range(core_total):
        core_by_batch[i].append("C9%03d" % (i + 1))

    bulk_index = 0
    for b in range(batches):
        if per_batch[b] == 0 and not core_by_batch[b]:
            continue
        batch_dir = "v0.%d.0" % (b + 1)
        entries = {}
        for cid in core_by_batch[b]:
            rel = "docs/archive/%s/change/%s.json" % (batch_dir, cid)
            write_json(root, rel, {"id": cid, "status": "closed"})
            entries[cid] = {"status": "closed", "file": rel, "title": "history-" + cid,
                            "version": batch_dir}
        remaining = per_batch[b] - len(core_by_batch[b])
        for _ in range(remaining):
            bulk_index += 1
            cid = "C%04d" % (1000 + bulk_index)
            rel = "docs/archive/%s/change/%s.json" % (batch_dir, cid)
            write_json(root, rel, {"id": cid, "status": "closed"})
            entries[cid] = {"status": "closed", "file": rel, "version": batch_dir}
        topics = {"Core": {"design_doc": DESIGN, "changes": core_by_batch[b]}} \
            if core_by_batch[b] else {}
        write_json(root, "docs/archive/%s/index.json" % batch_dir, {
            "$schema": "adflow-archive-batch-v1", "release": batch_dir,
            "archived_at": "2026-11-01", "cards": entries, "tasks": {}, "topics": topics})
    return active_ids, core_total


def classify(root, path):
    try:
        return Path(path).relative_to(root)
    except ValueError:
        return None


def measure(root, args):
    counts = {"archive_dir": 0, "manifest": 0, "card": 0, "active": 0}
    original_read = Path.read_text
    original_glob = Path.glob
    original_rglob = Path.rglob

    def read_text(self, *a, **k):
        rel = classify(root, self)
        if rel is not None:
            parts = Path(rel).parts
            if parts[:2] == ("docs", "archive"):
                if len(parts) == 4 and parts[-1] == "index.json":
                    counts["manifest"] += 1
                elif len(parts) == 5 and parts[-1].endswith(".json"):
                    counts["card"] += 1
            elif (parts[:2] == ("docs", "devel") and len(parts) == 4
                  and parts[2] in ("change", "task") and parts[-1].endswith(".json")):
                counts["active"] += 1
        return original_read(self, *a, **k)

    def walk(original):
        def wrapper(self, *a, **k):
            rel = classify(root, self)
            if rel is not None and Path(rel).parts[:2] == ("docs", "archive"):
                counts["archive_dir"] += 1
            return original(self, *a, **k)
        return wrapper

    out = StringIO()
    with mock.patch.object(Path, "read_text", read_text), \
            mock.patch.object(Path, "glob", walk(original_glob)), \
            mock.patch.object(Path, "rglob", walk(original_rglob)):
        with redirect_stdout(out):
            code = av.main([str(root), *args, "--json"])
    return code, counts, json.loads(out.getvalue())


def latency(root, args, runs):
    cmd = [sys.executable, str(TOOL), str(root), *args, "--json"]
    subprocess.run(cmd, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
    values = []
    for _ in range(runs):
        start = time.perf_counter()
        subprocess.run(cmd, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
        values.append((time.perf_counter() - start) * 1000)
    values.sort()
    p95 = values[min(len(values) - 1, max(0, int(round(0.95 * len(values))) - 1))]
    return {"p50": round(statistics.median(values), 2), "p95": round(p95, 2)}


def ids_of(data):
    return [c["id"] for c in data.get("topic", {}).get("cards", [])]


def main(argv=None):
    ap = argparse.ArgumentParser(description="Topic query benchmark (T03)")
    ap.add_argument("--tiers", default="0,500,2000,5000")
    ap.add_argument("--batches", type=int, default=20)
    ap.add_argument("--runs", type=int, default=20)
    ap.add_argument("--out-dir", default=str(REPO / "local/bench"))
    args = ap.parse_args(argv)

    tiers = [int(value) for value in args.tiers.split(",") if value.strip()]
    rows, failed = [], False
    for archived in tiers:
        with tempfile.TemporaryDirectory() as tmp:
            root = (Path(tmp) / "project").resolve()
            active_ids, core_total = build(root, archived, args.batches)
            cases = {
                "default": ["--topic", "Core"],
                "active": ["--topic", "Core", "--scope", "active"],
                "history": ["--topic", "Core", "--scope", "history"],
            }
            reads, codes, hits, lat = {}, {}, {}, {}
            for name, cli in cases.items():
                code, counter, data = measure(root, cli)
                reads[name] = counter
                codes[name] = code
                hits[name] = ids_of(data)
                lat[name] = latency(root, cli, args.runs)
            active_zero = reads["active"]["archive_dir"] == 0 \
                and reads["active"]["manifest"] == 0 and reads["active"]["card"] == 0
            history_zero = reads["history"]["card"] == 0
            failed = failed or not (active_zero and history_zero)
            rows.append({
                "archived": archived, "batches": args.batches,
                "hits": {"active": len(hits["active"]), "history": len(hits["history"]),
                         "default": len(hits["default"]), "expected_history": core_total},
                "reads": reads, "latency_ms": lat, "exit_codes": codes,
                "acceptance": {"active_zero_archive_io": active_zero,
                               "history_zero_card_body_reads": history_zero},
            })
            print("archived=%-5d active(reads=%s, p50=%.2fms) history(reads=%s, p50=%.2fms) "
                  "default(p50=%.2fms)"
                  % (archived, reads["active"], lat["active"]["p50"],
                     reads["history"], lat["history"]["p50"], lat["default"]["p50"]))
            if len(hits["active"]) != len(active_ids):
                print("WARN active hits != %d: %r" % (len(active_ids), hits["active"]))
            if len(hits["history"]) != core_total:
                print("WARN history hits != %d: %r" % (core_total, hits["history"]))

    payload = {
        "tool": "bench_topic_query", "version": av.VERSION,
        "generated_at": datetime.now().isoformat(timespec="seconds"),
        "batches": args.batches, "runs": args.runs, "tiers": rows,
        "acceptance": {"passed": not failed,
                       "rule": "active archive_dir/manifest/card reads=0; history card reads=0"},
    }
    out_dir = Path(args.out_dir)
    out_dir.mkdir(parents=True, exist_ok=True)
    stamp = datetime.now().strftime("%Y%m%d-%H%M%S")
    json_path = out_dir / ("topic-query-%s.json" % stamp)
    json_path.write_text(json.dumps(payload, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    lines = ["# Topic query benchmark", "",
             "- generated: %s" % payload["generated_at"],
             "- batches: %d · CLI runs per case: %d" % (args.batches, args.runs),
             "- rule: %s" % payload["acceptance"]["rule"], "",
             "| archived | hits active/history | active reads (dir/manifest/card) "
             "| history reads (manifest/card) | default reads (manifest/card) "
             "| p50/p95 active | p50/p95 history | p50/p95 default |",
             "|---|---|---|---|---|---|---|---|"]
    for row in rows:
        lines.append("| %d | %d/%d | %d/%d/%d | %d/%d | %d/%d | %.2f/%.2f | %.2f/%.2f | %.2f/%.2f |" % (
            row["archived"], row["hits"]["active"], row["hits"]["history"],
            row["reads"]["active"]["archive_dir"], row["reads"]["active"]["manifest"],
            row["reads"]["active"]["card"],
            row["reads"]["history"]["manifest"], row["reads"]["history"]["card"],
            row["reads"]["default"]["manifest"], row["reads"]["default"]["card"],
            row["latency_ms"]["active"]["p50"], row["latency_ms"]["active"]["p95"],
            row["latency_ms"]["history"]["p50"], row["latency_ms"]["history"]["p95"],
            row["latency_ms"]["default"]["p50"], row["latency_ms"]["default"]["p95"]))
    md_path = out_dir / ("topic-query-%s.md" % stamp)
    md_path.write_text("\n".join(lines) + "\n", encoding="utf-8")
    print("benchmark: %s" % json_path)
    print("summary:   %s" % md_path)
    print("acceptance: %s" % ("PASS" if not failed else "FAIL"))
    return 0 if not failed else 1


if __name__ == "__main__":
    sys.exit(main())
