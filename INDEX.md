# INDEX

Carte de symboles generee par `tkn index`. Ne pas editer a la main.
Les prefixes `L<n>` sont des numeros de ligne : demande les plages
precises a l'agent plutot que de lui faire relire les fichiers.

### tests/conftest.py
```
L1 import pathlib
L2 import sys
```

### tests/test_audit.py
```
L1 from tkn.audit import DEFAULTS, audit, render
L4 def test_consigne_positive_est_signalee_comme_ambigue(tmp_path)
L12 def test_negation_est_detectee(tmp_path)
L20 def test_fichiers_d_ignore_listes_comme_presents(tmp_path)
L26 def test_une_consigne_ambigue_ne_couvre_pas(tmp_path)
L32 def test_handoff_est_on_demand_pas_injected(tmp_path)
L41 def test_ligne_commentee_ne_protege_pas(tmp_path)
L47 def test_render_regroupe_les_regles_identiques(tmp_path)
L55 def test_index_est_exclu_du_total(tmp_path)
L63 def test_init_couvre_tout_ce_que_l_audit_reclame(tmp_path)
```

### tests/test_bench.py
```
L1 from tkn.bench import aggregate, by_label
L4 def _row(run, model = 'gpt-6.1-sol', inp = 10000)
L9 def test_une_tache_n_est_pas_une_requete()
L17 def test_resultat_de_test_porte_par_le_run()
L25 def test_tarif_inconnu_rend_le_cout_non_concluant()
L31 def test_requetes_hors_run_sont_isolees()
L39 def test_tache_non_evaluee_compte_a_part()
```

### tests/test_compress.py
```
L1 from tkn.compress import py_signatures
L4 def test_decorateur_de_niveau_principal_conserve()
L9 def test_annotations_defauts_et_separateurs_conserves()
L17 def test_numero_de_ligne_present()
L22 def test_methode_de_classe_conservee()
```

### tests/test_count.py
```
L1 from tkn.count import plan_fixed, plan_growth
L4 def test_reinjection_d_un_fichier_fixe_est_lineaire()
L8 def test_croissance_est_geometrique_et_superieure()
L12 def test_croissance_nulle_egale_le_lineaire()
```

### tests/test_index.py
```
L1 from tkn.index import build
L4 def test_le_break_arrete_vraiment(tmp_path)
L12 def test_bloc_markdown_jamais_ouvert_a_la_fin(tmp_path)
L20 def test_seuil_de_lignes_respecte(tmp_path)
```

### tests/test_proxy.py
```
L1 import copy
L3 from tkn.rewrite import fp, rewrite
L6 def _stats()
L10 def test_system_message_is_never_modified()
L23 def test_ansi_untouched_outside_tool_messages()
L29 def test_list_content_of_user_message_is_untouched()
L36 def test_ansi_scope_all_extends_to_user_messages()
L42 def test_fingerprint_detects_middle_difference()
```

### tests/test_rates.py
```
L1 import pytest
L3 from tkn import rates
L6 def test_modele_inconnu_renvoie_none()
L10 def test_tarif_d_ecriture_de_cache_est_utilise()
L16 def test_luna_en_credits_reste_inconnu()
L20 def test_fmt_affiche_un_point_d_interrogation()
```

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
L216 def main() -> int
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
L8 from __future__ import annotations
L9 import argparse
L10 from pathlib import Path
L12 from tkn.audit import DEFAULTS
L13 from tkn.compress import PY, CLIKE, compress_text, clip, iter_sources
L16 def build(root: Path, max_lines: int, budget: int) -> str
L49 def main() -> int
```

... [seuil de lignes atteint, tkn/init.py et suivants omis] ...