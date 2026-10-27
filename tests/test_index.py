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


def test_fichiers_omis_sont_rapportes(tmp_path):
    for i in range(40):
        (tmp_path / f"f{i:02d}.py").write_text("def f():\n    pass\n")
    omitted: list[str] = []
    build(tmp_path, max_lines=10_000, budget=60, omitted=omitted)
    assert omitted
    assert all(o.endswith(".py") for o in omitted)


def test_source_avant_tests(tmp_path):
    (tmp_path / "tests").mkdir()
    (tmp_path / "tests" / "a.py").write_text("def t():\n    pass\n")
    (tmp_path / "src").mkdir()
    (tmp_path / "src" / "b.py").write_text("def b():\n    pass\n")
    text = build(tmp_path, 10_000, 10_000)
    assert text.index("src/b.py") < text.index("tests/a.py")