#!/usr/bin/env python3
"""Genere INDEX.md. Le seuil vient de la meme constante que tkn.audit.

Les blocs sont toujours entiers : aucun ` ``` ` ouvert a la fin, seuil respecte.
Les sources passent avant les tests, et les fichiers omis sont rapportes.

Usage: python -m tkn.index [chemin] [--out INDEX.md] [--lines 200] [--budget 12000]
"""
from __future__ import annotations
import argparse
from pathlib import Path

from tkn.audit import DEFAULTS
from tkn.compress import PY, CLIKE, compress_text, clip, iter_sources


def _rank(p: Path, root: Path) -> tuple[int, str]:
    """Sources d'abord, tests ensuite."""
    rel = str(p.relative_to(root))
    return (1 if rel.startswith("tests/") else 0, rel)


def build(root: Path, max_lines: int, budget: int,
          omitted: list | None = None) -> str:
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

    sources = sorted(
        (p for p in iter_sources(root)
         if p.suffix.lower() in PY | CLIKE and p.name != "INDEX.md"),
        key=lambda p: _rank(p, root))

    for i, p in enumerate(sources):
        rel = p.relative_to(root)
        block = [f"### {rel}", "```"] + clip(compress_text(p), 400) + ["```", ""]
        cost = sum(max(1, round(len(x) / 4)) for x in block)

        if used_tokens + cost > budget:
            body.append(f"... [budget atteint, {len(sources) - i} fichiers omis] ...")
            if omitted is not None:
                omitted.extend(str(q.relative_to(root)) for q in sources[i:])
            break
        if used_lines + len(block) + 1 > max_lines:
            body.append(f"... [seuil de lignes atteint, {len(sources) - i} omis] ...")
            if omitted is not None:
                omitted.extend(str(q.relative_to(root)) for q in sources[i:])
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
    ap.add_argument("--budget", type=int, default=12000)
    a = ap.parse_args()
    root = Path(a.path).resolve()
    out = Path(a.out) if Path(a.out).is_absolute() else root / a.out

    omitted: list[str] = []
    text = build(root, a.lines, a.budget, omitted)
    out.write_text(text)

    print(f"{out} ecrit ({len(text.splitlines())} lignes, seuil {a.lines})")
    if omitted:
        apercu = ", ".join(omitted[:5]) + (" ..." if len(omitted) > 5 else "")
        print(f"{len(omitted)} fichiers omis : {apercu}")
        print("  augmente --budget pour les inclure")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())