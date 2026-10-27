"""Tarifs, sources et dates. Aucune valeur par defaut silencieuse.

Les valeurs ci-dessous sont un releve, pas une verite. Un modele absent doit
s'afficher "?" plutot que d'heriter d'un tarif voisin.
"""
from __future__ import annotations
import json
import os
from pathlib import Path

RELEVE = "2026-10-25"

# source: developers.openai.com/api/docs/pricing
# "write" est le tarif d'ecriture en cache. Il REMPLACE le tarif d'entree pour
# les tokens concernes : ce n'est pas une surcharge universelle.
# Au-dela de long_threshold, la requete ENTIERE est facturee au tarif long :
# long_mult s'applique a tout, entree, cache, ecriture et sortie compris.
USD = {
    "gpt-6-astra": {"in": 10.00, "cached": 1.00, "write": 12.50, "out": 50.00,
                    "long_threshold": 272_000, "long_mult": 2.0},
    "gpt-6.1-sol": {"in": 2.00, "cached": 0.10, "write": 2.50, "out": 10.00},
    "gpt-6-luna": {"in": 0.10, "cached": 0.01, "write": 0.125, "out": 0.50},
}

# source: learn.chatgpt.com/docs/pricing
# gpt-6-luna absent de la doc au releve : None, pas devine.
# Pas de champ "write" documente : cost() retombe sur le tarif d'entree.
CREDITS = {
    "gpt-6-astra": {"in": 250, "cached": 25, "out": 1250},
    "gpt-6.1-sol": {"in": 50, "cached": 5, "out": 250},
    "gpt-6-luna": None,
}


def user_path() -> Path:
    return Path(os.environ.get("TKN_RATES", Path.home() / ".tkn" / "rates.json"))


def load() -> dict:
    table = {"usd": dict(USD), "credits": dict(CREDITS), "releve": RELEVE}
    path = user_path()
    if not path.exists():
        return table
    try:
        user = json.loads(path.read_text())
    except (json.JSONDecodeError, OSError):
        return table
    for kind in ("usd", "credits"):
        for model, rates in (user.get(kind) or {}).items():
            table[kind][model] = rates
    table["releve"] = user.get("releve", RELEVE)
    return table


def cost(entry: dict, kind: str = "credits") -> float | None:
    """Cout d'une entree. None si le tarif du modele est inconnu."""
    rates = load().get(kind, {}).get(entry.get("model") or "")
    if not rates:
        return None

    mult = 1.0
    threshold = rates.get("long_threshold")
    if threshold and entry.get("input", 0) > threshold:
        mult = rates.get("long_mult", 1.0)

    written = entry.get("cache_write", 0)
    fresh = max(0, entry.get("input", 0) - entry.get("cached", 0) - written)
    return mult * (fresh * rates["in"]
                   + entry.get("cached", 0) * rates["cached"]
                   + written * rates.get("write", rates["in"])
                   + entry.get("output", 0) * rates["out"]) / 1_000_000


def fmt(value: float | None, width: int = 10, digits: int = 2) -> str:
    return f"{'?':>{width}}" if value is None else f"{value:>{width}.{digits}f}"