from tkn.index import build


def test_le_break_arrete_vraiment(tmp_path):
    for i in range(40):
        (tmp_path / f"f{i:02d}.py").write_text(f"def f{i}():\n    pass\n")
    text = build(tmp_path, max_lines=10_000, budget=60)
    assert "budget atteint" in text
    assert text.count("```") % 2 == 0


def test_bloc_markdown_jamais_ouvert_a_la_fin(tmp_path):
    for i in range(5):
        (tmp_path / f"f{i}.py").write_text("def f():\n    pass\n")
    text = build(tmp_path, max_lines=12, budget=10_000)
    assert text.count("```") % 2 == 0
    assert len(text.splitlines()) <= 12


def test_seuil_de_lignes_respecte(tmp_path):
    for i in range(40):
        (tmp_path / f"f{i:02d}.py").write_text("def f():\n    pass\n")
    text = build(tmp_path, max_lines=25, budget=10_000)
    assert len(text.splitlines()) <= 25
    assert "seuil de lignes atteint" in text