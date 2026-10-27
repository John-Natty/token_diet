import copy

from tkn.proxy import _extract_usage, _fields
from tkn.rewrite import fp, rewrite


def _stats():
    return {"chars_saved": 0, "truncated": 0, "deduped": 0, "ansi": 0}


# ---------------------------------------------------------- reecriture

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


def test_troncature_ne_depasse_pas_le_plafond():
    data = {"messages": [{"role": "tool", "content": "q" * 50_000}]}
    out = rewrite(copy.deepcopy(data), limit=300, stats=_stats())
    assert len(out["messages"][0]["content"]) <= 300


# ---------------------------------------------------------- lecture d'usage

def test_usage_stream_chat_completions():
    payload = (b'data: {"model":"gpt-6.1-sol",'
               b'"usage":{"prompt_tokens":10,"completion_tokens":2}}\n\n'
               b'data: [DONE]\n\n')
    assert _extract_usage(payload)["usage"]["prompt_tokens"] == 10


def test_usage_stream_responses():
    payload = (b'data: {"type":"response.output_text.delta","delta":"hi"}\n\n'
               b'data: {"type":"response.completed","response":{"model":"gpt-6-astra",'
               b'"usage":{"input_tokens":10,"output_tokens":2}}}\n\n')
    info = _extract_usage(payload)
    assert info["usage"]["input_tokens"] == 10
    assert info["model"] == "gpt-6-astra"


def test_usage_non_streaming():
    info = _extract_usage(b'{"model":"gpt-6.1-sol","usage":{"prompt_tokens":5}}')
    assert info["usage"]["prompt_tokens"] == 5


def test_usage_avec_enveloppe_response():
    info = _extract_usage(b'{"response":{"model":"x","usage":{"input_tokens":3}}}')
    assert info["usage"]["input_tokens"] == 3


def test_usage_illisible():
    assert _extract_usage(b"pas du json") is None


def test_usage_absent():
    assert _extract_usage(b'{"model":"x"}') is None


def test_fields_lit_cache_et_raisonnement():
    got = _fields({"input_tokens": 100, "output_tokens": 10,
                   "input_tokens_details": {"cached_tokens": 40,
                                            "cache_write_tokens": 5},
                   "output_tokens_details": {"reasoning_tokens": 7}})
    assert got == (100, 40, 5, 10, 7)


def test_fields_avec_noms_chat_completions():
    got = _fields({"prompt_tokens": 20, "completion_tokens": 3})
    assert got == (20, 0, 0, 3, 0)