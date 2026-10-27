#!/usr/bin/env python3
"""Compte les tokens. Deux modes distincts, jamais confondus.

  --reinfections N   un fichier de taille FIXE reinjecte N fois (lineaire)
  --simulate TURNS   le contexte grossit a chaque tour (geometrique)

Usage:
  python -m tkn.count AGENTS.md --reinfections 50 --model gpt-6.1-sol
  python -m tkn.count AGENTS.md --simulate 50 --model gpt-6.1-sol
"""
from __future__ import annotations
import argparse
import sys
from pathlib import Path

from tkn import rates


def _encoder():
    try:
        import tiktoken
        return tiktoken.get_encoding("o200k_base").encode, "o200k_base"
    except Exception:
        return None, None


_ENC, _ENC_NAME = _encoder()


def count(text: str) -> int:
    if _ENC is not None:
        return len(_ENC(text))
    return max(1, round(len(text) / 4))


def plan_fixed(size: int, turns: int) -> int:
    """Fichier de taille fixe reinjecte turns fois. Lineaire, par definition."""
    return size * turns


def plan_growth(size: int, turns: int, growth: float) -> float:
    """Simulation : le contexte grossit a chaque tour. Geometrique."""
    total, ctx = 0.0, float(size)
    for _ in range(turns):
        total += ctx
        ctx *= 1 + growth
    return total


def main() -> int:
    ap = argparse.ArgumentParser(prog="tkn count")
    ap.add_argument("files", nargs="*")
    ap.add_argument("--model", default=None)
    ap.add_argument("--reinfections", type=int, default=0,
                    help="fichier fixe reinjecte N fois")
    ap.add_argument("--simulate", type=int, default=0,
                    help="N tours avec croissance du contexte")
    ap.add_argument("--growth", type=float, default=0.15,
                    help="croissance par tour, pour --simulate uniquement")
    a = ap.parse_args()

    total = 0
    for name in a.files or ["-"]:
        text = sys.stdin.read() if name == "-" else Path(name).read_text(errors="replace")
        n = count(text)
        total += n
        print(f"{n:>9,}  {'stdin' if name == '-' else name}")
    print(f"{total:>9,}  TOTAL")

    if _ENC:
        print(f"tiktoken {_ENC_NAME} - NON garanti pour ce modele")
    else:
        print("ESTIMATION chars/4 - tiktoken absent, ecart possible de 20 %")

    table = rates.load()
    for kind in ("usd", "credits"):
        if a.model and table[kind].get(a.model) is None:
            print(f"tarif {kind} inconnu pour {a.model}")

    if a.reinfections:
        total_in = plan_fixed(total, a.reinfections)
        print(f"\nreinjection d'un fichier FIXE sur {a.reinfections} tours")
        print(f"  entrees cumulees : {total_in:,} tokens  (lineaire)")
        _cost(total_in, a.model, table)
    if a.simulate:
        total_in = plan_growth(total, a.simulate, a.growth)
        print(f"\nSIMULATION sur {a.simulate} tours, croissance {a.growth:.0%}/tour")
        print(f"  entrees cumulees : {total_in:,.0f} tokens  (geometrique)")
        print("  hypothese, pas une mesure : depend de tes /compact")
        _cost(total_in, a.model, table)
    return 0


def _cost(total_in: float, model: str | None, table: dict) -> None:
    if not model:
        return
    usd = table["usd"].get(model)
    cr = table["credits"].get(model)
    if usd:
        print(f"  cout API        : {total_in * usd['in'] / 1e6:.4f} $")
    if cr:
        print(f"  cout Work/Codex : {total_in * cr['in'] / 1e6:.1f} credits")


if __name__ == "__main__":
    raise SystemExit(main())