from tkn.bench import aggregate, by_label


def _row(run, model="gpt-6.1-sol", inp=10_000):
    return {"ts": 1.0, "run_id": run, "label": "t", "model": model,
            "input": inp, "cached": 0, "output": 100, "kind": "request"}


def test_une_tache_n_est_pas_une_requete():
    rows = [_row("r1"), _row("r1"), _row("r1"), _row("r2")]
    agg = aggregate(rows)
    assert agg["r1"]["requests"] == 3
    assert agg["r1"]["tasks"] == 1
    assert len(agg) == 2


def test_resultat_de_test_porte_par_le_run():
    rows = [_row("r1"), {"ts": 2.0, "run_id": "r1", "kind": "end", "tests": "pass"}]
    agg = aggregate(rows)
    assert agg["r1"]["tests"] == "pass"
    assert agg["r1"]["per_success"] is not None
    assert agg["r1"]["duration"] == 1.0


def test_tarif_inconnu_rend_le_cout_non_concluant():
    agg = aggregate([_row("r1", model="modele-inconnu")])
    assert agg["r1"]["rate_known"] is False
    assert agg["r1"]["per_task"] is None


def test_requetes_hors_run_sont_isolees():
    rows = [_row("r1"),
            {"ts": 1.0, "run_id": "", "kind": "request",
             "model": "gpt-6.1-sol", "input": 1, "output": 1}]
    agg = aggregate(rows)
    assert "r1" in agg and "" in agg


def test_tache_non_evaluee_compte_a_part():
    rows = [_row("r1"),
            {"ts": 2.0, "run_id": "r1", "kind": "end", "tests": "none"}]
    table = by_label(aggregate(rows))
    assert table["t"]["unevaluated"] == 1
    assert table["t"]["per_success"] is None