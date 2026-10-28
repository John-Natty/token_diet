import pytest

from tkn import rates


def test_tarifs_api_standard_sont_separes_des_credits():
    assert rates.USD["gpt-6-astra"]["in"] == 10
    assert rates.USD["gpt-6.1-sol"]["in"] == 2
    assert rates.USD["gpt-6-luna"]["in"] == 0.10
    assert all("long_threshold" not in table for table in rates.CREDITS.values())


def test_modele_inconnu_renvoie_none():
    assert rates.cost({"model": "nexiste-pas", "input": 1_000_000}, "usd") is None


def test_tarif_d_ecriture_de_cache_est_utilise():
    entry = {"model": "gpt-6-astra", "input": 0, "cached": 0,
             "output": 0, "cache_write": 1_000_000}
    assert rates.cost(entry, "usd") == pytest.approx(12.50)


def test_tarifs_en_credits_sont_actualises():
    assert rates.cost({"model": "gpt-6.1-sol", "input": 0, "cached": 1_000_000},
                      "credits") == pytest.approx(2.5)
    assert rates.cost({"model": "gpt-6-luna", "input": 1_000_000},
                      "credits") == pytest.approx(2.5)


def test_fmt_affiche_un_point_d_interrogation():
    assert rates.fmt(None).strip() == "?"


@pytest.mark.parametrize("model", ["gpt-6-astra", "gpt-6.1-sol", "gpt-6-luna"])
def test_contexte_long_applique_les_multiplicateurs_api(model):
    table = rates.USD[model]
    entry = {"model": model, "input": 1_000_000, "cached": 200_000,
             "cache_write": 100_000, "output": 1_000_000}
    expected_inputs = (700_000 * table["in"] + 200_000 * table["cached"]
                       + 100_000 * table["write"]) * 2
    expected_output = 1_000_000 * table["out"] * 1.5
    assert rates.cost(entry, "usd") == pytest.approx(
        (expected_inputs + expected_output) / 1_000_000)


def test_seuil_non_franchi_garde_le_tarif_standard():
    entry = {"model": "gpt-6-astra", "input": 272_000, "output": 0}
    assert rates.cost(entry, "usd") == pytest.approx(2.72)


def test_tarifs_credits_ne_recoivent_pas_le_multiplicateur_api():
    entry = {"model": "gpt-6-astra", "input": 1_000_000, "output": 1_000_000}
    assert rates.cost(entry, "credits") == pytest.approx(1500)
