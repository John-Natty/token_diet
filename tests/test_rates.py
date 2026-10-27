import pytest

from tkn import rates


def test_modele_inconnu_renvoie_none():
    assert rates.cost({"model": "nexiste-pas", "input": 1_000_000}, "usd") is None


def test_tarif_d_ecriture_de_cache_est_utilise():
    entry = {"model": "gpt-6-astra", "input": 0, "cached": 0,
             "output": 0, "cache_write": 1_000_000}
    assert rates.cost(entry, "usd") == pytest.approx(12.50)


def test_luna_en_credits_reste_inconnu():
    assert rates.cost({"model": "gpt-6-luna", "input": 1_000_000}, "credits") is None


def test_fmt_affiche_un_point_d_interrogation():
    assert rates.fmt(None).strip() == "?"