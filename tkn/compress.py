#!/usr/bin/env python3
"""Extrait les signatures : noms, types, exports, emplacements. Aucun corps.

Chaque ligne porte son numero de ligne (prefixe L<n>) pour que l'agent puisse
dire "modifie L45-72" au lieu de relire le fichier.

Usage:
  python -m tkn.compress src/auth.py
  python -m tkn.compress src/ --budget 2000
"""
from __future__ import annotations
import argparse
import ast
import os
import re
from pathlib import Path

from tkn.audit import SKIP_DIRS

PY = {".py", ".pyi"}
CLIKE = {".js", ".jsx", ".ts", ".tsx", ".mjs", ".cjs", ".go", ".rs", ".java",
         ".kt", ".swift", ".c", ".h", ".cc", ".cpp", ".hpp", ".cs", ".php",
         ".scala", ".dart"}
IMPORTS = ("import ", "from ", "use ", "package ", "#include", "using ",
           "mod ", "require(")
SKIP = ("//", "/*", "*", "*/", "#!")
KEYWORDS = {"if", "for", "while", "switch", "catch", "return", "else", "do",
            "try", "elif", "with", "match", "finally"}

# Ces mots ouvrent un conteneur : on descend au lieu de sauter le corps.
CONTAINERS = {"class", "interface", "struct", "impl", "namespace", "module",
              "enum", "record", "trait", "protocol", "extension", "union"}

SIG = re.compile(r"""^\s*(?:
      (?:export\s+)?(?:default\s+)?(?:abstract\s+|final\s+|open\s+|public\s+|
       private\s+|protected\s+|internal\s+|static\s+|async\s+|readonly\s+|pub\s+)*
      (?:function|func|fn|def|class|interface|type|struct|enum|trait|impl|
       namespace|module|protocol|extension|record|union)\b
    | (?:pub\s+)?(?:const|static)\s+\w+
    | (?:export\s+)?(?:const|let|var)\s+\w+\s*(?::\s*[^=]+)?=\s*(?:async\s*)?(?:\(|function)
    | (?:public|private|protected|internal|static|final|override|abstract|async)\s+
      [\w<>\[\]?.,:]+\s+\w+\s*\(
    | \w+\s*\([^;{)]*\)\s*(?::\s*[^;{]+)?\s*\{
    | @\w+
  )""", re.VERBOSE)

_STR = re.compile(r'"(?:[^"\\]|\\.)*"|\'(?:[^\'\\]|\\.)*\'')
_LINE_COMMENT = re.compile(r"//.*$")


def _brace_delta(line: str) -> int:
    """Accolades hors chaines et hors commentaires."""
    clean = _LINE_COMMENT.sub("", _STR.sub('""', line))
    return clean.count("{") - clean.count("}")


# ------------------------------------------------------------------ Python

def _arg(node: ast.arg, default=None, prefix: str = "") -> str:
    s = prefix + node.arg
    if node.annotation is not None:
        s += f": {ast.unparse(node.annotation)}"
    if default is not None:
        s += f" = {ast.unparse(default)}"
    return s


def _args(a: ast.arguments) -> str:
    pos = a.posonlyargs + a.args
    defaults = [None] * (len(pos) - len(a.defaults)) + list(a.defaults)
    parts = [_arg(x, d) for x, d in zip(pos, defaults)]
    if a.posonlyargs:
        parts.insert(len(a.posonlyargs), "/")
    if a.vararg:
        parts.append("*" + _arg(a.vararg))
    elif a.kwonlyargs:
        parts.append("*")
    parts += [_arg(x, d) for x, d in zip(a.kwonlyargs, a.kw_defaults)]
    if a.kwarg:
        parts.append("**" + _arg(a.kwarg))
    return ", ".join(parts)


def _decorators(node) -> list[str]:
    return [f"@{ast.unparse(d)}" for d in getattr(node, "decorator_list", [])]


def _fn_sig(node, indent: str) -> str:
    pre = "async " if isinstance(node, ast.AsyncFunctionDef) else ""
    ret = f" -> {ast.unparse(node.returns)}" if node.returns is not None else ""
    return f"{indent}{pre}def {node.name}({_args(node.args)}){ret}"


def _class_head(node, indent: str) -> str:
    bases = ", ".join(ast.unparse(b) for b in node.bases)
    return f"{indent}class {node.name}({bases})"


def py_signatures(src: str) -> list[str]:
    tree = ast.parse(src)
    out: list[str] = []

    def emit(body, indent: int) -> None:
        pad = "    " * indent
        for node in body:
            if isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef)):
                for dec in _decorators(node):
                    out.append(f"L{node.lineno} {pad}{dec}")
                out.append(f"L{node.lineno} {_fn_sig(node, pad)}")
            elif isinstance(node, ast.ClassDef):
                for dec in _decorators(node):
                    out.append(f"L{node.lineno} {pad}{dec}")
                out.append(f"L{node.lineno} {_class_head(node, pad)}")
                emit(node.body, indent + 1)
            elif isinstance(node, ast.AnnAssign) and isinstance(node.target, ast.Name):
                out.append(f"L{node.lineno} {pad}{node.target.id}: "
                           f"{ast.unparse(node.annotation)}")
            elif isinstance(node, ast.Assign):
                for t in node.targets:
                    if isinstance(t, ast.Name) and t.id.isupper():
                        out.append(f"L{node.lineno} {pad}{t.id} = ...")

    for node in tree.body:
        if isinstance(node, (ast.Import, ast.ImportFrom)):
            out.append(f"L{node.lineno} {ast.unparse(node)}")
        elif isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef)):
            for dec in _decorators(node):
                out.append(f"L{node.lineno} {dec}")
            doc = ast.get_docstring(node)
            out.append(f"L{node.lineno} {_fn_sig(node, '')}")
            if doc:
                out.append(f'L{node.lineno}     """{doc.splitlines()[0]}"""')
        elif isinstance(node, ast.ClassDef):
            for dec in _decorators(node):
                out.append(f"L{node.lineno} {dec}")
            out.append(f"L{node.lineno} {_class_head(node, '')}")
            emit(node.body, 1)
    return out


# ------------------------------------------------------------------ C-like

def clike_signatures(src: str) -> list[str]:
    lines = src.splitlines()
    out: list[str] = []
    i, n = 0, len(lines)
    while i < n:
        line = lines[i].strip()
        lineno = i + 1
        i += 1
        if not line or line.startswith(SKIP):
            continue
        if line.startswith(IMPORTS):
            out.append(f"L{lineno} {line}")
            continue
        word = re.match(r"[\w@]+", line)
        if word and word.group(0) in KEYWORDS:
            continue
        if not SIG.match(line):
            continue

        buf = [line]
        while not re.search(r"[{;]\s*$", line) and len(buf) < 6 and i < n:
            line = lines[i].strip()
            i += 1
            if line:
                buf.append(line)
        sig = " ".join(buf)
        out.append(f"L{lineno} {sig}")

        if not sig.rstrip().endswith("{"):
            continue
        if any(re.search(rf"\b{kw}\b", sig) for kw in CONTAINERS):
            continue                      # conteneur : on descend
        depth = 1
        while i < n and depth > 0:        # fonction : on saute le corps
            depth += _brace_delta(lines[i])
            i += 1
    return out


def compress_text(path: Path) -> list[str]:
    src = path.read_text(errors="replace")
    suffix = path.suffix.lower()
    if suffix in PY:
        try:
            return py_signatures(src)
        except SyntaxError:
            return clike_signatures(src)
    if suffix in CLIKE:
        return clike_signatures(src)
    return [f"L{i + 1} {l}" for i, l in enumerate(src.splitlines())]


def clip(lines: list[str], budget: int) -> list[str]:
    out, used = [], 0
    for line in lines:
        cost = max(1, round(len(line) / 4))
        if used + cost > budget:
            out.append(f"... [{len(lines) - len(out)} lignes coupees] ...")
            break
        out.append(line)
        used += cost
    return out


def iter_sources(root: Path):
    """Les exclusions de l'audit s'appliquent aussi ici."""
    if root.is_file():
        yield root
        return
    for dirpath, dirnames, filenames in os.walk(root):
        dirnames[:] = sorted(d for d in dirnames
                             if d not in SKIP_DIRS and not d.startswith("."))
        for name in sorted(filenames):
            p = Path(dirpath) / name
            if p.suffix.lower() in PY | CLIKE:
                yield p


def main() -> int:
    ap = argparse.ArgumentParser(prog="tkn compress")
    ap.add_argument("path")
    ap.add_argument("--budget", type=int, default=0)
    a = ap.parse_args()

    targets = list(iter_sources(Path(a.path)))
    for p in targets:
        lines = compress_text(p)
        if a.budget:
            lines = clip(lines, a.budget)
        if len(targets) > 1:
            print(f"## {p}")
        print("\n".join(lines))
        if len(targets) > 1:
            print()
    return 0


if __name__ == "__main__":
    raise SystemExit(main())