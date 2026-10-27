from tkn.audit import DEFAULTS, audit, render


def test_consigne_positive_est_signalee_comme_ambigue(tmp_path):
    (tmp_path / "AGENTS.md").write_text("Tu peux lire node_modules pour les types.")
    r = audit(tmp_path, DEFAULTS)
    e = next(x for x in r["declared"] if "node_modules" in x["line"])
    assert e["verdict"] == "ambigu"
    assert e["source"].startswith("AGENTS.md")


def test_negation_est_detectee(tmp_path):
    (tmp_path / ".codexignore").write_text("dist/\n!dist/vendor\n")
    r = audit(tmp_path, DEFAULTS)
    verdicts = {e["line"].strip(): e["verdict"] for e in r["declared"]}
    assert verdicts["dist/"] == "exclusion"
    assert verdicts["!dist/vendor"] == "negation"


def test_fichiers_d_ignore_listes_comme_presents(tmp_path):
    (tmp_path / ".codexignore").write_text("node_modules/\n")
    r = audit(tmp_path, DEFAULTS)
    assert ".codexignore" in r["ignore_files"]["present"]


def test_une_consigne_ambigue_ne_couvre_pas(tmp_path):
    (tmp_path / "AGENTS.md").write_text("Tu peux lire node_modules")
    r = audit(tmp_path, DEFAULTS)
    assert "node_modules" in r["uncovered_paths"]


def test_handoff_est_on_demand_pas_injected(tmp_path):
    (tmp_path / "AGENTS.md").write_text("\n".join("x" for _ in range(100)))
    (tmp_path / "HANDOFF.md").write_text("\n".join("l" for _ in range(400)))
    r = audit(tmp_path, DEFAULTS)
    kinds = {f["file"]: f["kind"] for f in r["findings"]}
    assert kinds["AGENTS.md"] == "injected"
    assert kinds["HANDOFF.md"] == "on_demand"


def test_ligne_commentee_ne_protege_pas(tmp_path):
    (tmp_path / ".codexignore").write_text("# node_modules/\n")
    r = audit(tmp_path, DEFAULTS)
    assert r["declared"] == []


def test_render_regroupe_les_regles_identiques(tmp_path):
    for name in (".codexignore", ".cursorignore"):
        (tmp_path / name).write_text("node_modules/\n")
    out = render(audit(tmp_path, DEFAULTS))
    assert out.count("node_modules/") == 1
    assert "(2 fichiers)" in out


def test_index_est_exclu_du_total(tmp_path):
    (tmp_path / "a.py").write_text("x = 1\n" * 500)
    (tmp_path / "INDEX.md").write_text("y\n" * 400)
    r = audit(tmp_path, DEFAULTS)
    assert r["total_lines"] == 500
    assert r["generated_lines"] == 400


def test_init_couvre_tout_ce_que_l_audit_reclame(tmp_path):
    from tkn.init import IGNORE_CONTENT
    (tmp_path / ".codexignore").write_text(IGNORE_CONTENT)
    r = audit(tmp_path, DEFAULTS)
    assert r["uncovered_paths"] == []