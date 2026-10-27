#!/usr/bin/env python3
"""Mesure par tache. Une tache = un run, pas une requete.

  tkn bench start --label refactor-auth --model gpt-6.1-sol
  # ... tu executes la tache ...
  tkn bench end --tests pass
  tkn bench snapshot apres.json
  tkn bench compare avant.json apres.json

Le chiffre qui compte est le cout d'une tache REELLEMENT terminee.
"""
from __future__ import annotations
import argparse
import json
import sys
import time
from pathlib import Path

from tkn import rates
from tkn.report import log_path, read_log

MARK_PATH = Path.home() / ".tkn" / "marks.jsonl"
RUN_FILE = Path.home() / ".tkn" / "current_run"


def _append(entry: dict) -> None:
    p = log_path()
    p.parent.mkdir(parents=True, exist_ok=True)
    with p.open("a") as fh:
        fh.write(json.dumps(entry) + "\n")


def cmd_start(a) -> int:
    run_id = f"{int(time.time())}-{a.label}"
    RUN_FILE.parent.mkdir(parents=True, exist_ok=True)
    RUN_FILE.write_text(run_id)
    _append({"ts": time.time(), "run_id": run_id, "kind": "start",
             "label": a.label, "model": a.model})
    print(f"run '{run_id}' ouvert. Clos-le : tkn bench end --tests pass")
    return 0


def cmd_end(a) -> int:
    if not RUN_FILE.exists():
        print("aucun run ouvert")
        return 1
    run_id = RUN_FILE.read_text().strip()
    _append({"ts": time.time(), "run_id": run_id, "kind": "end",
             "tests": a.tests})
    RUN_FILE.unlink()
    print(f"run '{run_id}' clos, tests={a.tests}")
    return 0


def cmd_mark(a) -> int:
    MARK_PATH.parent.mkdir(parents=True, exist_ok=True)
    with MARK_PATH.open("a") as fh:
        fh.write(json.dumps({"ts": time.time(), "name": a.name}) + "\n")
    print(f"marqueur '{a.name}' pose a {time.strftime('%H:%M:%S')}")
    return 0


def last_mark() -> float:
    if not MARK_PATH.exists():
        return 0.0
    rows = [l for l in MARK_PATH.read_text().splitlines() if l.strip()]
    return json.loads(rows[-1])["ts"] if rows else 0.0


def aggregate(rows: list[dict]) -> dict:
    """Une tache = un run. Les requetes orphelines vont dans un seau separe."""
    runs: dict[str, dict] = {}
    for r in rows:
        rid = r.get("run_id") or ""
        run = runs.setdefault(rid, {"label": r.get("label") or "(sans run)",
                                    "model": r.get("model") or "",
                                    "requests": 0, "credits": 0.0,
                                    "rate_known": True, "tests": None,
                                    "ts": r.get("ts", 0.0), "duration": 0.0})
        kind = r.get("kind")
        if kind == "start":
            run["label"] = r.get("label") or run["label"]
            run["model"] = r.get("model") or run["model"]
            run["ts"] = r.get("ts", run["ts"])
            continue
        if kind == "end":
            run["tests"] = r.get("tests")
            run["duration"] = r.get("ts", 0.0) - run["ts"]
            continue
        run["requests"] += 1
        c = rates.cost(r, "credits")
        if c is None:
            run["rate_known"] = False
        else:
            run["credits"] += c

    for run in runs.values():
        run["tasks"] = 1
        run["per_task"] = run["credits"] if run["rate_known"] else None
        ok = run["tests"] == "pass" and run["rate_known"]
        run["per_success"] = run["credits"] if ok else None
    return runs


def by_label(runs: dict) -> dict:
    out: dict[str, dict] = {}
    for run in runs.values():
        a = out.setdefault(run["label"], {"tasks": 0, "requests": 0, "credits": 0.0,
                                          "passed": 0, "failed": 0,
                                          "unevaluated": 0, "rate_known": True})
        a["tasks"] += 1
        a["requests"] += run["requests"]
        a["credits"] += run["credits"]
        if not run["rate_known"]:
            a["rate_known"] = False
        if run["tests"] == "pass":
            a["passed"] += 1
        elif run["tests"] == "fail":
            a["failed"] += 1
        else:
            a["unevaluated"] += 1
    for a in out.values():
        a["per_task"] = a["credits"] / a["tasks"] if a["rate_known"] and a["tasks"] else None
        a["per_success"] = (a["credits"] / a["passed"]
                            if a["rate_known"] and a["passed"] else None)
    return out


def cmd_record(a) -> int:
    entry = {"ts": time.time(), "label": a.label, "model": a.model,
             "input": a.input, "cached": a.cached, "cache_write": a.cache_write,
             "output": a.output, "tests": a.tests, "kind": "request",
             "run_id": a.run or (RUN_FILE.read_text().strip() if RUN_FILE.exists() else "")}
    _append(entry)
    c = rates.cost(entry, "credits")
    print(f"enregistre : {a.label} "
          f"({'? credits' if c is None else f'{c:.2f} credits'})")
    print("  attention : ne double pas avec les requetes deja journalisees par"
          " le proxy si le run est le meme")
    return 0


def cmd_report(a) -> int:
    runs = aggregate(read_log(a.log))
    if not runs:
        print("journal vide")
        return 0
    table = by_label(runs)
    print(f"{'tache':<28}{'runs':>6}{'req':>7}{'cred/tache':>12}{'ok':>5}{'cred/ok':>10}")
    print("-" * 70)
    for label, v in sorted(table.items(), key=lambda x: -(x[1]["per_task"] or 0)):
        rate = f"{v['passed']}/{v['tasks']}"
        print(f"{label[:27]:<28}{v['tasks']:>6}{v['requests']:>7}"
              f"{rates.fmt(v['per_task'], 12)}{rate:>5}"
              f"{rates.fmt(v['per_success'], 10)}")
    return 0


def cmd_snapshot(a) -> int:
    rows = read_log(a.log)
    since = 0.0 if a.all else last_mark()
    window = [r for r in rows if r.get("ts", 0) >= since]
    runs = aggregate(window)
    data = {"from": since, "to": time.time(), "releve": rates.RELEVE,
            "labels": by_label(runs), "runs": len(runs), "requests": len(window)}
    Path(a.out).write_text(json.dumps(data, indent=2, ensure_ascii=False))
    print(f"{a.out} : {len(runs)} taches, {len(window)} requetes "
          f"(depuis {time.strftime('%H:%M:%S', time.localtime(since))})")
    if since == 0.0:
        print("  attention : aucun marqueur, la fenetre couvre tout le journal")
    return 0


def cmd_compare(a) -> int:
    before = json.loads(Path(a.before).read_text())
    after = json.loads(Path(a.after).read_text())
    labels = sorted(set(before["labels"]) | set(after["labels"]))

    print(f"taches : {before['runs']} -> {after['runs']}")
    print(f"tarifs releves le {after.get('releve', '?')}")
    print(f"\n{'tache':<26}{'cred/tache':>20}{'reussite':>18}{'cred/reussite':>20}")
    print(f"{'':<26}{'avant':>9}{'apres':>11}{'avant':>9}{'apres':>9}"
          f"{'avant':>10}{'apres':>10}")
    print("-" * 86)

    for label in labels:
        b, c = before["labels"].get(label, {}), after["labels"].get(label, {})
        br = (b["passed"] / b["tasks"]) if b.get("tasks") else None
        cr = (c["passed"] / c["tasks"]) if c.get("tasks") else None
        print(f"{label[:25]:<26}"
              f"{rates.fmt(b.get('per_task'), 9)}{rates.fmt(c.get('per_task'), 11)}"
              f"{rates.fmt(br, 9, 0) if br is None else f'{br * 100:>8.0f}%'}"
              f"{rates.fmt(cr, 9, 0) if cr is None else f'{cr * 100:>8.0f}%'}"
              f"{rates.fmt(b.get('per_success'), 10)}"
              f"{rates.fmt(c.get('per_success'), 10)}")

        if not b.get("rate_known", True) or not c.get("rate_known", True):
            print(f"{'':<26}  /!\\ tarif inconnu : ecart non concluant")
        elif b.get("passed", 0) != b.get("tasks", 0) or c.get("passed", 0) != c.get("tasks", 0):
            print(f"{'':<26}  /!\\ toutes les taches ne sont pas evaluees"
                  f" : comparer a qualite egale")
    print("-" * 86)

    bt = sum(v["credits"] for v in before["labels"].values())
    at = sum(v["credits"] for v in after["labels"].values())
    bp = sum(v["passed"] for v in before["labels"].values())
    ap_ = sum(v["passed"] for v in after["labels"].values())
    print(f"total : {bt:.2f} -> {at:.2f} credits, {bp} -> {ap_} taches reussies")
    if bp and ap_:
        print(f"cout par tache reussie : {bt / bp:.2f} -> {at / ap_:.2f} credits "
              f"({(at / ap_ - bt / bp) / (bt / bp) * 100:+.1f} %)")
        if at / ap_ < bt / bp:
            print(f"soit x{(bt / bp) / (at / ap_):.2f} de travail utile en plus.")
    return 0


def main() -> int:
    ap = argparse.ArgumentParser(prog="tkn bench")
    sub = ap.add_subparsers(dest="cmd", required=True)

    p = sub.add_parser("start"); p.add_argument("--label", required=True)
    p.add_argument("--model", required=True); p.set_defaults(fn=cmd_start)

    p = sub.add_parser("end")
    p.add_argument("--tests", choices=["pass", "fail", "none"], default="none")
    p.set_defaults(fn=cmd_end)

    p = sub.add_parser("mark"); p.add_argument("name"); p.set_defaults(fn=cmd_mark)

    p = sub.add_parser("record")
    p.add_argument("--label", required=True); p.add_argument("--model", required=True)
    p.add_argument("--run", default=None)
    p.add_argument("--in", dest="input", type=int, default=0)
    p.add_argument("--cached", type=int, default=0)
    p.add_argument("--cache-write", dest="cache_write", type=int, default=0)
    p.add_argument("--out", dest="output", type=int, default=0)
    p.add_argument("--tests", choices=["pass", "fail"], default=None)
    p.set_defaults(fn=cmd_record)

    p = sub.add_parser("report"); p.add_argument("--log", default=None)
    p.set_defaults(fn=cmd_report)

    p = sub.add_parser("snapshot"); p.add_argument("out")
    p.add_argument("--log", default=None); p.add_argument("--all", action="store_true")
    p.set_defaults(fn=cmd_snapshot)

    p = sub.add_parser("compare"); p.add_argument("before"); p.add_argument("after")
    p.set_defaults(fn=cmd_compare)

    a = ap.parse_args()
    return a.fn(a)


if __name__ == "__main__":
    sys.exit(main())