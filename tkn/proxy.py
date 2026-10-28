#!/usr/bin/env python3
"""Serveur proxy. La logique de reecriture est dans tkn/rewrite.py.

En OBSERVATION par defaut : transmet la requete INCHANGEE et journalise ce
qu'il aurait coupe. --mode actif pour appliquer.

Usage:
  python -m tkn.proxy --port 8787
  export OPENAI_BASE_URL=http://127.0.0.1:8787/v1
"""
from __future__ import annotations
import argparse
import http.client
import json
import os
import time
import urllib.error
import urllib.request
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
from pathlib import Path

from tkn.rewrite import rewrite

LOG_PATH = Path(os.environ.get("TKN_LOG", Path.home() / ".tkn" / "usage.jsonl"))
STATS_PATH = Path.home() / ".tkn" / "proxy_stats.jsonl"
RUN_FILE = Path.home() / ".tkn" / "current_run"
STREAM_CHUNK_SIZE = 16 * 1024
MAX_SSE_LINE = 1024 * 1024


def current_run() -> str:
    try:
        return RUN_FILE.read_text().strip()
    except OSError:
        return ""


def _usage_from_obj(obj: dict, previous: dict | None = None) -> dict | None:
    model = (previous or {}).get("model")
    usage = (previous or {}).get("usage")
    if isinstance(obj.get("response"), dict):
        response = obj["response"]
        model = response.get("model") or model
        usage = response.get("usage") or usage
    model = obj.get("model") or model
    usage = obj.get("usage") or usage
    return {"model": model, "usage": usage} if usage else previous


class _SSEUsageParser:
    """Extrait l'usage sans conserver le flux complet en memoire."""

    def __init__(self) -> None:
        self.pending = bytearray()
        self.info: dict | None = None

    def feed(self, chunk: bytes) -> None:
        self.pending.extend(chunk)
        while b"\n" in self.pending:
            line, _, rest = self.pending.partition(b"\n")
            self.pending = bytearray(rest)
            self._line(line.rstrip(b"\r"))
        if len(self.pending) > MAX_SSE_LINE:
            self.pending.clear()

    def finish(self) -> None:
        if self.pending:
            self._line(bytes(self.pending).rstrip(b"\r"))
            self.pending.clear()

    def _line(self, line: bytes) -> None:
        if not line.startswith(b"data:"):
            return
        data = line[5:].strip()
        if not data or data == b"[DONE]" or len(data) > MAX_SSE_LINE:
            return
        try:
            obj = json.loads(data)
        except json.JSONDecodeError:
            return
        if isinstance(obj, dict):
            self.info = _usage_from_obj(obj, self.info)


def _extract_usage(payload: bytes) -> dict | None:
    text = payload.decode("utf-8", "replace")
    if "data:" in text:
        parser = _SSEUsageParser()
        parser.feed(payload)
        parser.finish()
        return parser.info

    try:
        obj = json.loads(text)
    except json.JSONDecodeError:
        return None
    return _usage_from_obj(obj) if isinstance(obj, dict) else None


def _fields(u: dict) -> tuple[int, int, int, int, int]:
    ind = u.get("prompt_tokens_details") or u.get("input_tokens_details") or {}
    outd = u.get("completion_tokens_details") or u.get("output_tokens_details") or {}
    ind = ind if isinstance(ind, dict) else {}
    outd = outd if isinstance(outd, dict) else {}
    return (u.get("prompt_tokens") or u.get("input_tokens") or 0,
            ind.get("cached_tokens", 0),
            ind.get("cache_write_tokens", 0),
            u.get("completion_tokens") or u.get("output_tokens") or 0,
            outd.get("reasoning_tokens", 0))


def record(payload: bytes, label: str, req: dict | None, stats: dict, mode: str,
           usage_info: dict | None = None) -> None:
    LOG_PATH.parent.mkdir(parents=True, exist_ok=True)
    info = usage_info or _extract_usage(payload)
    if info and info.get("usage"):
        inp, cached, written, out, reasoning = _fields(info["usage"])
        entry = {"ts": time.time(), "label": label, "mode": mode,
                 "run_id": current_run(),
                 "model": info.get("model") or (req or {}).get("model") or "",
                 "input": inp, "cached": cached, "cache_write": written,
                 "output": out, "reasoning": reasoning,
                 "saved_chars": stats.get("chars_saved", 0)}
        with LOG_PATH.open("a") as fh:
            fh.write(json.dumps(entry) + "\n")
    if stats:
        stats["ts"] = time.time()
        stats["label"] = label
        stats["mode"] = mode
        with STATS_PATH.open("a") as fh:
            fh.write(json.dumps(stats) + "\n")


class Handler(BaseHTTPRequestHandler):
    upstream = "https://api.openai.com"
    limit = 6000
    mode = "observe"
    ansi_scope = "tool"
    protocol_version = "HTTP/1.1"

    def log_message(self, fmt, *args):
        if os.environ.get("TKN_VERBOSE"):
            super().log_message(fmt, *args)

    def do_GET(self):
        self._forward("GET")

    def do_POST(self):
        self._forward("POST")

    def _forward(self, method: str) -> None:
        length = int(self.headers.get("content-length") or 0)
        raw = self.rfile.read(length) if length else b""
        label = self.headers.get("x-tkn-label", "")
        req_data, out_raw = None, raw
        stats: dict = {"mode": self.mode, "chars_saved": 0, "truncated": 0,
                       "deduped": 0, "ansi": 0, "chars_before": len(raw)}

        if raw:
            try:
                req_data = json.loads(raw)
                if self.mode == "actif" and req_data.get("stream"):
                    req_data.setdefault("stream_options", {})["include_usage"] = True
                rewritten = rewrite(req_data, self.limit, stats, self.ansi_scope)
                out_raw = (json.dumps(rewritten).encode()
                           if self.mode == "actif" else raw)
            except json.JSONDecodeError:
                req_data = None

        req = urllib.request.Request(
            self.upstream + self.path,
            data=out_raw if method != "GET" else None, method=method)
        for key, value in self.headers.items():
            if key.lower() in ("host", "content-length", "accept-encoding", "connection"):
                continue
            req.add_header(key, value)

        try:
            with urllib.request.urlopen(req) as resp:
                if "text/event-stream" in (resp.headers.get("content-type") or ""):
                    self._relay(resp, label, req_data, stats)
                else:
                    payload = resp.read()
                    self.send_response(resp.status)
                    for key, value in resp.headers.items():
                        if key.lower() in ("transfer-encoding", "content-encoding",
                                           "content-length"):
                            continue
                        self.send_header(key, value)
                    self.send_header("content-length", str(len(payload)))
                    self.end_headers()
                    self.wfile.write(payload)
                    record(payload, label, req_data, stats, self.mode)
        except urllib.error.HTTPError as exc:
            payload = exc.read()
            self.send_response(exc.code)
            self.send_header("content-type", "application/json")
            self.send_header("content-length", str(len(payload)))
            self.end_headers()
            self.wfile.write(payload)
        except Exception as exc:  # noqa: BLE001
            msg = json.dumps({"error": {"message": str(exc)}}).encode()
            self.send_response(502)
            self.send_header("content-type", "application/json")
            self.send_header("content-length", str(len(msg)))
            self.end_headers()
            self.wfile.write(msg)

    def _relay(self, resp, label, req_data, stats) -> None:
        self.send_response(resp.status)
        for key, value in resp.headers.items():
            if key.lower() in ("transfer-encoding", "content-encoding", "content-length"):
                continue
            self.send_header(key, value)
        self.send_header("transfer-encoding", "chunked")
        self.end_headers()
        parser = _SSEUsageParser()
        try:
            while True:
                chunk = resp.read1(STREAM_CHUNK_SIZE)
                if not chunk:
                    break
                parser.feed(chunk)
                self.wfile.write(b"%X\r\n%s\r\n" % (len(chunk), chunk))
                self.wfile.flush()
            parser.finish()
            self.wfile.write(b"0\r\n\r\n")
            self.wfile.flush()
        except (OSError, http.client.HTTPException):
            self.close_connection = True
            return
        record(b"", label, req_data, stats, self.mode, parser.info)


def main() -> int:
    ap = argparse.ArgumentParser(prog="tkn proxy")
    ap.add_argument("--port", type=int, default=8787)
    ap.add_argument("--upstream",
                    default=os.environ.get("TKN_UPSTREAM", "https://api.openai.com"))
    ap.add_argument("--limit", type=int, default=6000,
                    help="caracteres max pour une sortie d'outil")
    ap.add_argument("--mode", choices=["observe", "actif"], default="observe")
    ap.add_argument("--ansi-scope", choices=["tool", "all"], default="tool")
    a = ap.parse_args()

    Handler.upstream = a.upstream.rstrip("/")
    Handler.limit = a.limit
    Handler.mode = a.mode
    Handler.ansi_scope = a.ansi_scope
    srv = ThreadingHTTPServer(("127.0.0.1", a.port), Handler)

    print(f"mode : {a.mode}" + (" (rien n'est modifie)" if a.mode == "observe" else ""))
    print(f"base_url : http://127.0.0.1:{a.port}/v1")
    print("stats    : python3 -m tkn.cli report --stats")
    try:
        srv.serve_forever()
    except KeyboardInterrupt:
        print("\narret.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
