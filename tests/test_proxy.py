import copy

from tkn.rewrite import fp, rewrite


def _stats():
    return {"chars_saved": 0, "truncated": 0, "deduped": 0, "ansi": 0}


def test_system_message_is_never_modified():
    system = "CONSIGNE: " + "x" * 40_000
    data = {"messages": [
        {"role": "system", "content": system},
        {"role": "user", "content": system},
        {"role": "tool", "content": "y" * 40_000},
    ]}
    out = rewrite(copy.deepcopy(data), limit=1000, stats=_stats())
    assert out["messages"][0]["content"] == system
    assert out["messages"][1]["content"] == system
    assert len(out["messages"][2]["content"]) < 40_000


def test_ansi_untouched_outside_tool_messages():
    data = {"messages": [{"role": "user", "content": "\x1b[31mrouge\x1b[0m"}]}
    out = rewrite(copy.deepcopy(data), limit=1000, stats=_stats())
    assert out["messages"][0]["content"] == "\x1b[31mrouge\x1b[0m"


def test_list_content_of_user_message_is_untouched():
    text = "z" * 40_000
    data = {"messages": [{"role": "user", "content": [{"type": "text", "text": text}]}]}
    out = rewrite(copy.deepcopy(data), limit=1000, stats=_stats())
    assert out["messages"][0]["content"][0]["text"] == text


def test_ansi_scope_all_extends_to_user_messages():
    data = {"messages": [{"role": "user", "content": "\x1b[31mrouge\x1b[0m"}]}
    out = rewrite(copy.deepcopy(data), limit=1000, stats=_stats(), ansi_scope="all")
    assert out["messages"][0]["content"] == "rouge"


def test_fingerprint_detects_middle_difference():
    a = "A" * 300 + "milieu1" + "B" * 300
    b = "A" * 300 + "milieu2" + "B" * 300
    assert fp(a) != fp(b)