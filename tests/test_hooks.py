from pathlib import Path

from tkn import init

ROOT = Path(__file__).resolve().parents[1]


def test_les_hooks_du_depot_sont_du_bash():
    for name in ("pre-commit", "commit-msg"):
        text = (ROOT / "hooks" / name).read_text()
        assert text.startswith("#!/usr/bin/env bash"), f"{name} n'est pas du bash"
        assert "def main()" not in text, f"{name} contient du Python"


def test_les_hooks_du_depot_correspondent_a_init():
    """Sans ce test, hooks/ et tkn/init.py divergent en silence."""
    assert (ROOT / "hooks" / "pre-commit").read_text() == init.PRE_COMMIT
    assert (ROOT / "hooks" / "commit-msg").read_text() == init.COMMIT_MSG