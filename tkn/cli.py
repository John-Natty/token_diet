"""tkn - point d'entree unique.

Livre par ordre de confiance : audit, index, bench d'abord. Le proxy ensuite.
"""
from __future__ import annotations
import sys

HELP = """tkn - reduire le contexte inutile, en verifiant que la qualite tient

  tkn audit [chemin]        constats mesurables, en lecture seule
  tkn count <fichiers...>   compte les tokens (exact ou estime, c'est dit)
  tkn compress <fichier>    signatures seules, avec numeros de ligne
  tkn index [chemin]        genere INDEX.md
  tkn bench start|end|record|report|snapshot|compare
  tkn proxy                 proxy en OBSERVATION par defaut
  tkn report [--stats]      usage journalise
  tkn rates                 affiche les tarifs charges et leur source
  tkn init [chemin]         installe un profil (equilibre | strict)

Options globales : -h, -V
"""

MODULES = {
    "audit": "tkn.audit", "count": "tkn.count", "compress": "tkn.compress",
    "index": "tkn.index", "bench": "tkn.bench", "proxy": "tkn.proxy",
    "report": "tkn.report", "init": "tkn.init",
}


def cmd_rates(_argv) -> int:
    from tkn import rates
    table = rates.load()
    path = rates.user_path()
    print(f"releve   : {table['releve']}")
    print(f"override : {path} ({'present' if path.exists() else 'absent'})")
    for kind in ("usd", "credits"):
        print(f"\n{kind}")
        for model, r in sorted(table[kind].items()):
            print(f"  {model:<16} {r if r else 'inconnu'}")
    return 0


def main(argv=None) -> int:
    argv = list(sys.argv[1:] if argv is None else argv)
    if not argv or argv[0] in ("-h", "--help"):
        print(HELP)
        return 0
    cmd = argv.pop(0)
    if cmd in ("-V", "--version"):
        from tkn import __version__
        print(__version__)
        return 0
    if cmd == "rates":
        return cmd_rates(argv)
    mod = MODULES.get(cmd)
    if mod is None:
        print(f"commande inconnue : {cmd}\n\n{HELP}")
        return 2
    sys.argv = [f"tkn {cmd}"] + argv
    return __import__(mod, fromlist=["main"]).main()


if __name__ == "__main__":
    raise SystemExit(main())