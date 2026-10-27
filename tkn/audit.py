#!/usr/bin/env python3
"""tkn audit - constats mesurables, en lecture seule.

Distingue trois choses que l'on confond souvent :
  - un fichier d'ignore PRESENT
  - une consigne DECLAREE dans un fichier (avec le texte de la ligne)
  - un comportement OBSERVE (via le journal d'usage)

Usage: python -m tkn.audit [chemin] [--json] [--verbose] [--config seuils.json]
"""
from __future__ import annotations
import argparse
import json
import os
import re
from pathlib import Path

SKIP_DIRS = {".git", "node_modules", "dist", "build", ".venv", "venv",
             "__pycache__", "coverage", ".next", "target", ".idea", ".cache"}
SKIP_EXT = {".lock", ".map", ".png", ".jpg", ".jpeg", ".svg", ".ico",
            ".woff", ".woff2", ".pdf", ".zip", ".gif", ".webp"}

# Auto-injectes par l'agent a chaque tour.
INJECTED = ("AGENTS.md", "CLAUDE.md", ".cursorrules")
# Lus a la demande, edites a la main.
ON_DEMAND = ("HANDOFF.md",)
# Produits par l'outil : sortis du total, mais verifies quand meme.
GENERATED = ("INDEX.md",)

AGENT_IGNORE = (".codexignore", ".cursorignore", ".aiderignore", ".clineignore",
                ".rooignore", ".aiignore", ".ignore")
DECLARATION_SOURCES = AGENT_IGNORE + ("AGENTS.md", "CLAUDE.md", ".gitignore")

SHOULD_IGNORE = [".git", "node_modules", "dist", "build", "coverage", ".venv",
                 "target", "__pycache__"]

DEFAULTS = {
    "injected_lines": 60,
    "on_demand_lines": 200,
    "generated_lines": 200,
    "file_lines": 300,
    "chars_per_token": 4,
}

POSITIVE_RE = re.compile(
    r"\b(?:peux|peut|peuvent)\s+lire\b|\blire\b|\bread\b|\binclure\b|\binclus\b",
    re.IGNORECASE)
NEGATION_RE = re.compile(r"^\s*!|\bne\s+pas\s+lire\b|\bexclu", re.IGNORECASE)


def active_lines(path: Path) -> list[str]:
    """Lignes utiles. Un '#node_modules' ne protege rien."""
    if not path.exists():
        return []
    out = []
    for line in path.read_text(errors="replace").splitlines():
        s = line.strip()
        if s and not s.startswith("#"):
            out.append(s)
    return out


def verdict(line: str) -> str:
    """exclusion | ambigu | negation. Le texte de la ligne est rendu au lecteur."""
    if NEGATION_RE.search(line):
        return "negation"
    if POSITIVE_RE.search(line):
        return "ambigu"
    return "exclusion"


def walk(root: Path):
    for dirpath, dirnames, filenames in os.walk(root):
        dirnames[:] = [d for d in dirnames if d not in SKIP_DIRS]
        for name in filenames:
            p = Path(dirpath) / name
            if p.suffix not in SKIP_EXT:
                yield p


def count_lines(p: Path) -> int:
    try:
        with p.open("rb") as fh:
            return sum(1 for _ in fh)
    except OSError:
        return 0


def audit(root: Path, cfg: dict) -> dict:
    findings: list[dict] = []
    total_lines = 0
    generated_lines = 0

    for p in walk(root):
        n = count_lines(p)
        rel = str(p.relative_to(root))

        if p.name in GENERATED:
            generated_lines += n
            lim = cfg["generated_lines"]
            if n > lim:
                findings.append({"kind": "generated", "severity": "low",
                                 "file": rel, "lines": n, "max": lim})
            continue

        total_lines += n
        if p.name in INJECTED:
            lim = cfg["injected_lines"]
            if n > lim:
                findings.append({"kind": "injected", "severity": "high",
                                 "file": rel, "lines": n, "max": lim})
        elif p.name in ON_DEMAND:
            lim = cfg["on_demand_lines"]
            if n > lim:
                findings.append({"kind": "on_demand", "severity": "medium",
                                 "file": rel, "lines": n, "max": lim})
        elif n > cfg["file_lines"]:
            findings.append({"kind": "bloat", "severity": "medium",
                             "file": rel, "lines": n, "max": cfg["file_lines"]})

    declared: list[dict] = []
    present: list[str] = []
    for name in DECLARATION_SOURCES:
        p = root / name
        if not p.exists():
            continue
        if name in AGENT_IGNORE:
            present.append(name)
        for i, line in enumerate(active_lines(p), 1):
            if any(d in line for d in SHOULD_IGNORE):
                declared.append({"source": f"{name}:{i}", "line": line,
                                 "verdict": verdict(line)})

    covered = {d for d in SHOULD_IGNORE
               if any(d in e["line"] and e["verdict"] == "exclusion"
                      for e in declared)}

    return {
        "root": str(root),
        "chars_per_token": cfg["chars_per_token"],
        "total_lines": total_lines,
        "generated_lines": generated_lines,
        "findings": findings,
        "ignore_files": {"present": present,
                         "absent": [n for n in AGENT_IGNORE if n not in present]},
        "declared": declared,
        "uncovered_paths": [d for d in SHOULD_IGNORE if d not in covered],
        "index_missing": not (root / "INDEX.md").exists(),
        "injected_total_lines": sum(f["lines"] for f in findings
                                    if f["kind"] == "injected"),
    }


def render(r: dict, verbose: bool = False) -> str:
    L = []
    inj = [f for f in r["findings"] if f["kind"] == "injected"]
    if inj:
        L.append("AUTO-INJECTE A CHAQUE TOUR - cout multiplie par le nombre de tours")
        for f in sorted(inj, key=lambda x: -x["lines"]):
            L.append(f"  {f['file']} : {f['lines']} lignes (seuil {f['max']})")
        L.append(f"  total permanent : {r['injected_total_lines']} lignes")
        L.append("")

    for kind, title in (("on_demand", "LU A LA DEMANDE (seuil depasse)"),
                        ("generated", "GENERE (seuil depasse)"),
                        ("bloat", "FICHIERS TROP GROS")):
        rows = [f for f in r["findings"] if f["kind"] == kind]
        if not rows:
            continue
        L.append(title)
        for f in sorted(rows, key=lambda x: -x["lines"])[:15]:
            L.append(f"  {f['file']} : {f['lines']} lignes (seuil {f['max']})")
        L.append("")

    if r["declared"]:
        L.append("CONSIGNES D'EXCLUSION TROUVEES")
        marks = {"exclusion": " ", "ambigu": "?", "negation": "!"}
        by_rule: dict[str, dict] = {}
        for e in r["declared"]:
            g = by_rule.setdefault(e["line"].strip(),
                                   {"verdict": e["verdict"], "n": 0})
            g["n"] += 1
        for rule, g in sorted(by_rule.items()):
            suffix = f"   ({g['n']} fichiers)" if g["n"] > 1 else ""
            L.append(f"  {marks[g['verdict']]} {rule[:58]}{suffix}")
        sources = sorted({e["source"].split(":")[0] for e in r["declared"]})
        L.append(f"  sources : {', '.join(sources)}")
        if verbose:
            for e in r["declared"]:
                L.append(f"    {e['source']:<26} {e['line'][:50]}")
        L.append("  '?' = la ligne dit peut-etre l'inverse"
                 " (ex: 'tu peux lire node_modules')")
        L.append("  '!' = negation : le chemin est en fait INCLUS")
        L.append("")

    if r["uncovered_paths"]:
        L.append("EXCLUS D'AUCUNE CONSIGNE D'EXCLUSION")
        L.append(f"  fichiers d'ignore presents : "
                 f"{', '.join(r['ignore_files']['present']) or 'aucun'}")
        for d in r["uncovered_paths"]:
            L.append(f"  - {d}")
        L.append("  (.gitignore ne suffit pas : il regit git, pas les lectures)")
        L.append("")

    if r["index_missing"]:
        L.append("INDEX.md absent : l'agent explorera a l'aveugle.")
        L.append("")

    L.append(f"Total : {r['total_lines']} lignes lisibles.")
    if r["generated_lines"]:
        L.append(f"(+{r['generated_lines']} lignes generees, hors total)")
    L.append(f"(estimation a {r['chars_per_token']} caracteres/token)")
    return "\n".join(L)


def main() -> int:
    ap = argparse.ArgumentParser(prog="tkn audit")
    ap.add_argument("path", nargs="?", default=".")
    ap.add_argument("--json", action="store_true")
    ap.add_argument("--verbose", action="store_true")
    ap.add_argument("--config", default=None)
    a = ap.parse_args()

    cfg = dict(DEFAULTS)
    if a.config:
        cfg.update(json.loads(Path(a.config).read_text()))

    r = audit(Path(a.path), cfg)
    print(json.dumps(r, indent=2, ensure_ascii=False) if a.json
          else render(r, a.verbose))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())