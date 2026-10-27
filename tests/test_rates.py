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


def test_contexte_long_applique_le_multiplicateur():
    entry = {"model": "gpt-6-astra", "input": 300_000, "output": 0}
    assert rates.cost(entry, "usd") == pytest.approx(6.00)


def test_seuil_non_franchi_garde_le_tarif_standard():
    entry = {"model": "gpt-6-astra", "input": 272_000, "output": 0}
    assert rates.cost(entry, "usd") == pytest.approx(2.72)


def test_modele_sans_seuil_long_reste_stable():
    entry = {"model": "gpt-6.1-sol", "input": 500_000, "output": 0}
    assert rates.cost(entry, "usd") == pytest.approx(1.00)