import copy
import http.client
import json
import threading
import time
from contextlib import contextmanager
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer

from tkn import proxy
from tkn.proxy import _SSEUsageParser, _extract_usage, _fields
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


# ---------------------------------------------------------- transport HTTP

@contextmanager
def _running_server(handler):
    server = ThreadingHTTPServer(("127.0.0.1", 0), handler)
    thread = threading.Thread(target=server.serve_forever, daemon=True)
    thread.start()
    try:
        yield server
    finally:
        server.shutdown()
        server.server_close()
        thread.join(timeout=2)


class _QuietHandler(BaseHTTPRequestHandler):
    protocol_version = "HTTP/1.1"

    def log_message(self, _fmt, *_args):
        pass


def _proxy_handler(upstream):
    class TestProxy(proxy.Handler):
        pass

    TestProxy.upstream = upstream
    TestProxy.mode = "observe"
    return TestProxy


def test_observe_transmet_le_corps_octet_pour_octet(tmp_path, monkeypatch):
    received = []

    class Upstream(_QuietHandler):
        def do_POST(self):
            received.append(self.rfile.read(int(self.headers["content-length"])))
            payload = b'{"model":"x","usage":{"input_tokens":3}}'
            self.send_response(200)
            self.send_header("content-type", "application/json")
            self.send_header("content-length", str(len(payload)))
            self.end_headers()
            self.wfile.write(payload)

    monkeypatch.setattr(proxy, "LOG_PATH", tmp_path / "usage.jsonl")
    monkeypatch.setattr(proxy, "STATS_PATH", tmp_path / "stats.jsonl")
    raw = b'{ "model": "x", "stream": true, "messages": [] }'
    with _running_server(Upstream) as upstream:
        url = f"http://127.0.0.1:{upstream.server_port}"
        with _running_server(_proxy_handler(url)) as server:
            conn = http.client.HTTPConnection("127.0.0.1", server.server_port, timeout=2)
            conn.request("POST", "/v1/responses", raw,
                         {"content-type": "application/json"})
            response = conn.getresponse()
            response.read()
            conn.close()

    assert response.status == 200
    assert received == [raw]


def test_sse_est_transmis_progressivement_et_usage_enregistre(tmp_path, monkeypatch):
    first_sent = threading.Event()
    release_second = threading.Event()
    received = []
    first = b'data: {"type":"response.output_text.delta","delta":"un"}\n\n'
    second = (b'data: {"type":"response.completed","response":{"model":"x",'
              b'"usage":{"input_tokens":7,"output_tokens":2}}}\n\n')

    class Upstream(_QuietHandler):
        def do_POST(self):
            received.append(self.rfile.read(int(self.headers["content-length"])))
            self.send_response(200)
            self.send_header("content-type", "text/event-stream")
            self.send_header("connection", "close")
            self.end_headers()
            self.wfile.write(first)
            self.wfile.flush()
            first_sent.set()
            release_second.wait(timeout=2)
            self.wfile.write(second)
            self.wfile.flush()
            self.close_connection = True

    monkeypatch.setattr(proxy, "LOG_PATH", tmp_path / "usage.jsonl")
    monkeypatch.setattr(proxy, "STATS_PATH", tmp_path / "stats.jsonl")
    raw = b'{"model":"x","stream":true}'
    with _running_server(Upstream) as upstream:
        url = f"http://127.0.0.1:{upstream.server_port}"
        with _running_server(_proxy_handler(url)) as server:
            conn = http.client.HTTPConnection("127.0.0.1", server.server_port, timeout=2)
            conn.request("POST", "/v1/responses", raw,
                         {"content-type": "application/json"})
            response = conn.getresponse()
            assert first_sent.wait(timeout=1)
            got = []
            reader = threading.Thread(target=lambda: got.append(response.read(len(first))))
            reader.start()
            reader.join(timeout=1)
            assert not reader.is_alive(), "le premier evenement SSE reste bloque"
            assert got == [first]
            release_second.set()
            assert response.read() == second
            conn.close()

    assert received == [raw]
    for _ in range(50):
        if (tmp_path / "usage.jsonl").exists():
            break
        time.sleep(0.01)
    entry = json.loads((tmp_path / "usage.jsonl").read_text())
    assert (entry["model"], entry["input"], entry["output"]) == ("x", 7, 2)


def test_analyse_sse_borne_sa_memoire():
    parser = _SSEUsageParser()
    parser.feed(b"data: " + b"x" * (proxy.MAX_SSE_LINE + 1))
    assert len(parser.pending) <= proxy.MAX_SSE_LINE
    parser.feed(b'data: {"model":"x","usage":{"input_tokens":1}}\n')
    assert parser.info["usage"]["input_tokens"] == 1


def test_relay_ferme_la_connexion_si_le_client_interrompt():
    class Response:
        status = 200
        headers = {"content-type": "text/event-stream"}

        def read1(self, _size):
            return b"data: {}\n\n"

    class DisconnectedWriter:
        def write(self, _data):
            raise BrokenPipeError

        def flush(self):
            pass

    handler = object.__new__(proxy.Handler)
    handler.send_response = lambda _status: None
    handler.send_header = lambda _key, _value: None
    handler.end_headers = lambda: None
    handler.wfile = DisconnectedWriter()
    handler.close_connection = False
    handler._relay(Response(), "", None, {})
    assert handler.close_connection is True
