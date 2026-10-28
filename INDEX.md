# INDEX

Carte de symboles generee par `tkn index`. Ne pas editer a la main.
Les prefixes `L<n>` sont des numeros de ligne : demande les plages
precises a l'agent plutot que de lui faire relire les fichiers.

### tkn/__init__.py
```
```

### tkn/audit.py
```
L11 from __future__ import annotations
L12 import argparse
L13 import json
L14 import os
L15 import re
L16 from pathlib import Path
L51 def active_lines(path: Path) -> list[str]
L51     """Lignes utiles. Un '#node_modules' ne protege rien."""
L63 def verdict(line: str) -> str
L63     """exclusion | ambigu | negation. Le texte de la ligne est rendu au lecteur."""
L72 def walk(root: Path)
L81 def count_lines(p: Path) -> int
L89 def audit(root: Path, cfg: dict) -> dict
L154 def render(r: dict, verbose: bool = False) -> str
L216 def has_failures(r: dict) -> bool
L216     """Vrai quand --check doit rendre l'audit bloquant."""
L221 def main() -> int
```

### tkn/bench.py
```
L12 from __future__ import annotations
L13 import argparse
L14 import json
L15 import sys
L16 import time
L17 from pathlib import Path
L19 from tkn import rates
L20 from tkn.report import log_path, read_log
L26 def _append(entry: dict) -> None
L33 def cmd_start(a) -> int
L43 def cmd_end(a) -> int
L55 def cmd_mark(a) -> int
L63 def last_mark() -> float
L70 def aggregate(rows: list[dict]) -> dict
L70     """Une tache = un run. Les requetes orphelines vont dans un seau separe."""
L105 def by_label(runs: dict) -> dict
L129 def cmd_record(a) -> int
L143 def cmd_report(a) -> int
L159 def cmd_snapshot(a) -> int
L174 def cmd_compare(a) -> int
L217 def main() -> int
```

### tkn/cli.py
```
L5 from __future__ import annotations
L6 import sys
L30 def cmd_rates(_argv) -> int
L43 def main(argv = None) -> int
```

### tkn/compress.py
```
L11 from __future__ import annotations
L12 import argparse
L13 import ast
L14 import os
L15 import re
L16 from pathlib import Path
L18 from tkn.audit import SKIP_DIRS
L51 def _brace_delta(line: str) -> int
L51     """Accolades hors chaines et hors commentaires."""
L59 def _arg(node: ast.arg, default = None, prefix: str = '') -> str
L68 def _args(a: ast.arguments) -> str
L84 def _decorators(node) -> list[str]
L88 def _fn_sig(node, indent: str) -> str
L94 def _class_head(node, indent: str) -> str
L99 def py_signatures(src: str) -> list[str]
L143 def clike_signatures(src: str) -> list[str]
L182 def compress_text(path: Path) -> list[str]
L195 def clip(lines: list[str], budget: int) -> list[str]
L207 def iter_sources(root: Path)
L207     """Les exclusions de l'audit s'appliquent aussi ici."""
L221 def main() -> int
```

### tkn/count.py
```
L11 from __future__ import annotations
L12 import argparse
L13 import sys
L14 from pathlib import Path
L16 from tkn import rates
L19 def _encoder()
L30 def count(text: str) -> int
L36 def plan_fixed(size: int, turns: int) -> int
L36     """Fichier de taille fixe reinjecte turns fois. Lineaire, par definition."""
L41 def plan_growth(size: int, turns: int, growth: float) -> float
L41     """Simulation : le contexte grossit a chaque tour. Geometrique."""
L50 def main() -> int
L94 def _cost(total_in: float, model: str | None, table: dict) -> None
```

### tkn/index.py
```
L9 from __future__ import annotations
L10 import argparse
L11 from pathlib import Path
L13 from tkn.audit import DEFAULTS
L14 from tkn.compress import PY, CLIKE, compress_text, clip, iter_sources
L17 def _rank(p: Path, root: Path) -> tuple[int, str]
L17     """Sources d'abord, tests ensuite."""
L23 def build(root: Path, max_lines: int, budget: int, omitted: list | None = None) -> str
L64 def main() -> int
```

### tkn/init.py
```
L8 from __future__ import annotations
L9 import argparse
L10 import shutil
L11 import stat
L12 import time
L13 from pathlib import Path
L122 def put(path: Path, content: str, force: bool) -> str
L136 def main() -> int
```

### tkn/proxy.py
```
L11 from __future__ import annotations
L12 import argparse
L13 import http.client
L14 import json
L15 import os
L16 import time
L17 import urllib.error
L18 import urllib.request
L19 from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
L20 from pathlib import Path
L22 from tkn.rewrite import rewrite
L31 def current_run() -> str
L38 def _usage_from_obj(obj: dict, previous: dict | None = None) -> dict | None
L50 class _SSEUsageParser()
L53     def __init__(self) -> None
L57     def feed(self, chunk: bytes) -> None
L66     def finish(self) -> None
L71     def _line(self, line: bytes) -> None
L85 def _extract_usage(payload: bytes) -> dict | None
L100 def _fields(u: dict) -> tuple[int, int, int, int, int]
L112 def record(payload: bytes, label: str, req: dict | None, stats: dict, mode: str, usage_info: dict | None = None) -> None
L134 class Handler(BaseHTTPRequestHandler)
L141     def log_message(self, fmt, *args)
L145     def do_GET(self)
L148     def do_POST(self)
L151     def _forward(self, method: str) -> None
L209     def _relay(self, resp, label, req_data, stats) -> None
L235 def main() -> int
```

### tkn/rates.py
```
L6 from __future__ import annotations
L7 import json
L8 import os
L9 from pathlib import Path
L39 def user_path() -> Path
L43 def load() -> dict
L59 def cost(entry: dict, kind: str = 'credits') -> float | None
L59     """Cout d'une entree. None si le tarif du modele est inconnu."""
L80 def fmt(value: float | None, width: int = 10, digits: int = 2) -> str
```

### tkn/report.py
```
L6 from __future__ import annotations
L7 import argparse
L8 import json
L9 import os
L10 from collections import defaultdict
L11 from pathlib import Path
L13 from tkn import rates
L18 def log_path() -> Path
L22 def read_log(path = None) -> list[dict]
L38 def show_stats(a) -> int
L59 def main() -> int
```

... [seuil de lignes atteint, 11 omis] ...