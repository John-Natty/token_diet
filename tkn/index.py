#!/usr/bin/env python3
"""Genere INDEX.md. Le seuil vient de la meme constante que tkn.audit.

Les blocs sont toujours entiers : aucun ` ``` ` ouvert a la fin, seuil respecte.

Usage: python -m tkn.index [chemin] [--out INDEX.md] [--lines 200] [--budget 6000]
"""
from __future__ import annotations
import argparse
from pathlib import Path

from tkn.audit import DEFAULTS
from tkn.compress import PY, CLIKE, compress_text, clip, iter_sources


def build(root: Path, max_lines: int, budget: int) -> str:
    head = [
        "# INDEX",
        "",
        "Carte de symboles generee par `tkn index`. Ne pas editer a la main.",
        "Les prefixes `L<n>` sont des numeros de ligne : demande les plages",
        "precises a l'agent plutot que de lui faire relire les fichiers.",
        "",
    ]
    body: list[str] = []
    used_tokens = 0
    used_lines = len(head)

    for p in iter_sources(root):
        if p.suffix.lower() not in PY | CLIKE or p.name == "INDEX.md":
            continue
        rel = p.relative_to(root)
        block = [f"### {rel}", "```"] + clip(compress_text(p), 400) + ["```", ""]
        cost = sum(max(1, round(len(x) / 4)) for x in block)

        if used_tokens + cost > budget:
            body.append(f"... [budget atteint, {rel} et suivants omis] ...")
            break
        if used_lines + len(block) + 1 > max_lines:
            body.append(f"... [seuil de lignes atteint, {rel} et suivants omis] ...")
            break
        body += block
        used_tokens += cost
        used_lines += len(block)

    return "\n".join(head + body)


def main() -> int:
    ap = argparse.ArgumentParser(prog="tkn index")
    ap.add_argument("path", nargs="?", default=".")
    ap.add_argument("--out", default="INDEX.md")
    ap.add_argument("--lines", type=int, default=DEFAULTS["generated_lines"])
    ap.add_argument("--budget", type=int, default=6000)
    a = ap.parse_args()
    root = Path(a.path).resolve()
    out = Path(a.out) if Path(a.out).is_absolute() else root / a.out
    text = build(root, a.lines, a.budget)
    out.write_text(text)
    print(f"{out} ecrit ({len(text.splitlines())} lignes, seuil {a.lines})")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())