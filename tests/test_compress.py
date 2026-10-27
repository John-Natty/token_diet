from tkn.compress import py_signatures


def test_decorateur_de_niveau_principal_conserve():
    src = "import functools\n\n@functools.lru_cache\ndef f(x: int) -> str:\n    return ''\n"
    assert any("@functools.lru_cache" in s for s in py_signatures(src))


def test_annotations_defauts_et_separateurs_conserves():
    src = ("def f(a: int, b: str = 'x', /, c: float = 1.0, *, "
           "d: bool = False) -> None:\n    pass\n")
    sig = next(s for s in py_signatures(src) if "def f" in s)
    assert "a: int" in sig and "b: str = 'x'" in sig
    assert "/" in sig and "*" in sig and "-> None" in sig


def test_numero_de_ligne_present():
    src = "\n\n\ndef f():\n    pass\n"
    assert any(s.startswith("L4 ") for s in py_signatures(src))


def test_methode_de_classe_conservee():
    src = "class A:\n    def m(self, x: int = 1) -> int:\n        return x\n"
    sigs = py_signatures(src)
    assert any("class A" in s for s in sigs)
    assert any("def m(self, x: int = 1) -> int" in s for s in sigs)