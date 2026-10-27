from tkn.rewrite import truncate


def test_respecte_le_plafond():
    text = "x" * 10_000
    for limit in (50, 100, 500, 1000, 5000):
        out, cut = truncate(text, limit)
        assert cut is True
        assert len(out) <= limit, f"depassement avec limit={limit}"


def test_petit_plafond_ne_grossit_pas():
    """Le bug : 25 caracteres tronques a 20 en sortaient 41."""
    out, cut = truncate("y" * 25, 20)
    assert cut is True
    assert len(out) <= 20


def test_sous_le_plafond_intact():
    out, cut = truncate("abc", 100)
    assert out == "abc" and cut is False


def test_conserve_le_debut_et_la_fin():
    out, _ = truncate("D" * 500 + "M" * 500 + "F" * 500, 200)
    assert out.startswith("D") and out.endswith("F")
    assert "tronques" in out