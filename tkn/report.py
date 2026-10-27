#!/usr/bin/env python3
"""Lit le journal d'usage et agrege. Les tarifs inconnus sont visibles.

Usage: python -m tkn.report [--log chemin] [--top 20] [--kind credits|usd] [--stats]
"""
from __future__ import annotations
import argparse
import json
import os
from collections import defaultdict
from pathlib import Path

from tkn import rates

STATS_PATH = Path.home() / ".tkn" / "proxy_stats.jsonl"


def log_path() -> Path:
    return Path(os.environ.get("TKN_LOG", Path.home() / ".tkn" / "usage.jsonl"))


def read_log(path=None) -> list[dict]:
    p = Path(path) if path else log_path()
    if not p.exists():
        return []
    rows = []
    for line in p.read_text().splitlines():
        line = line.strip()
        if not line:
            continue
        try:
            rows.append(json.loads(line))
        except json.JSONDecodeError:
            continue
    return rows


def show_stats(a) -> int:
    if not STATS_PATH.exists():
        print(f"aucune stats : {STATS_PATH}")
        print("le proxy les ecrit automatiquement, meme en mode observation.")
        return 0
    rows = [json.loads(l) for l in STATS_PATH.read_text().splitlines() if l.strip()]
    before = sum(r.get("chars_before", 0) for r in rows)
    saved = sum(r.get("chars_saved", 0) for r in rows)
    cut = sum(r.get("truncated", 0) for r in rows)
    dedup = sum(r.get("deduped", 0) for r in rows)
    print(f"{len(rows)} requetes observees")
    print(f"  caracteres envoyes      : {before:,}")
    print(f"  caracteres evites       : {saved:,} "
          f"({saved / before * 100:.1f} %)" if before else "")
    print(f"  blocs tronques          : {cut}")
    print(f"  blocs dedupliques       : {dedup}")
    print(f"  -> ~{saved / 4:,.0f} tokens d'entree evitables")
    print("\nActiver avec : tkn proxy --mode actif")
    return 0


def main() -> int:
    ap = argparse.ArgumentParser(prog="tkn report")
    ap.add_argument("--log", default=None)
    ap.add_argument("--top", type=int, default=20)
    ap.add_argument("--kind", choices=["credits", "usd"], default="credits")
    ap.add_argument("--stats", action="store_true")
    a = ap.parse_args()

    if a.stats:
        return show_stats(a)

    rows = read_log(a.log)
    if not rows:
        print(f"journal vide : {log_path()}")
        print("lance `tkn proxy` puis pointe ton agent dessus.")
        return 0

    unknown: set[str] = set()
    acc: dict[str, float] = defaultdict(float)
    total = 0.0
    for r in rows:
        c = rates.cost(r, a.kind)
        if c is None:
            unknown.add(r.get("model") or "(vide)")
            continue
        total += c
        acc[r.get("label") or "(sans run)"] += c

    print(f"{len(rows)} requetes, {total:.2f} {a.kind} identifies "
          f"(releve tarifs {rates.RELEVE})\n")
    for name, value in sorted(acc.items(), key=lambda x: -x[1])[: a.top]:
        print(f"  {value:>10.2f}  {name}")

    if unknown:
        print(f"\ntarif inconnu pour : {', '.join(sorted(unknown))}")
        print("  ajoute-les dans ~/.tkn/rates.json, sinon la somme reste partielle")

    heavy = sum(1 for r in rows if r.get("input", 0) > 200_000)
    if heavy:
        print(f"\n{heavy} requetes au-dessus de 200k tokens d'entree "
              f"(falaise des 272k en approche)")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())