from tkn.count import plan_fixed, plan_growth


def test_reinjection_d_un_fichier_fixe_est_lineaire():
    assert plan_fixed(1_000, 50) == 50_000


def test_croissance_est_geometrique_et_superieure():
    assert plan_growth(1_000, 50, 0.15) > 50_000


def test_croissance_nulle_egale_le_lineaire():
    assert plan_growth(1_000, 50, 0.0) == 50_000