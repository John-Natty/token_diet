"""Reecriture pure des requetes. Testable sans serveur HTTP.

Regle : on ne touche QUE les sorties d'outils, sauf ansi_scope="all".
"""
from __future__ import annotations
import hashlib
import re

ANSI = re.compile(r"\x1b\[[0-9;?]*[A-Za-z]")
TEXT_TYPES = {"text", "input_text", "output_text"}
TOOL_ROLES = {"tool", "function"}
TOOL_TYPES = {"function_call_output", "custom_tool_call_output", "tool_result"}

MIN_KEEP = 20   # en dessous, un marqueur coute plus qu'il n'explique


def strip_ansi(text: str) -> str:
    return ANSI.sub("", text)


def truncate(text: str, limit: int) -> tuple[str, bool]:
    """La sortie ne depasse JAMAIS limit, marqueur compris."""
    if len(text) <= limit:
        return text, False

    marker = f"\n[... {len(text) - limit} caracteres tronques ...]\n"
    keep = limit - len(marker)
    if keep < MIN_KEEP:
        return text[:limit], True

    # deuxieme passe : le compte reel de caracteres retires
    marker = f"\n[... {len(text) - keep} caracteres tronques ...]\n"
    keep = limit - len(marker)
    if keep < MIN_KEEP:
        return text[:limit], True

    head = keep // 2
    tail = keep - head
    return f"{text[:head]}{marker}{text[-tail:]}", True


def fp(text: str) -> str:
    """Empreinte du contenu COMPLET, pas d'echantillons."""
    return hashlib.sha1(text.encode("utf-8", "replace")).hexdigest()


def is_tool(msg: dict) -> bool:
    return msg.get("role") in TOOL_ROLES or msg.get("type") in TOOL_TYPES


def rewrite_text(text: str, limit: int, stats: dict) -> str:
    cleaned = strip_ansi(text)
    if cleaned != text:
        stats["ansi"] += len(text) - len(cleaned)
    if not limit:
        return cleaned
    out, cut = truncate(cleaned, limit)
    if cut:
        stats["truncated"] += 1
        stats["chars_saved"] += len(cleaned) - len(out)
    return out


def rewrite(data: dict, limit: int, stats: dict, ansi_scope: str = "tool") -> dict:
    messages = data.get("messages") or data.get("input")
    if not isinstance(messages, list):
        return data
    seen: set[str] = set()

    for msg in messages:
        if not isinstance(msg, dict):
            continue
        tool = is_tool(msg)
        if not tool and ansi_scope != "all":
            continue                          # on ne touche a RIEN

        cap = limit if tool else 0
        content = msg.get("content")

        if isinstance(content, str):
            msg["content"] = rewrite_text(content, cap, stats)
        elif isinstance(content, list):
            out = []
            for part in content:
                if isinstance(part, str):
                    out.append(rewrite_text(part, cap, stats))
                    continue
                if not isinstance(part, dict) or part.get("type") not in TEXT_TYPES:
                    out.append(part)
                    continue
                text = part.get("text")
                if not isinstance(text, str):
                    out.append(part)
                    continue
                new = rewrite_text(text, cap, stats)
                if tool and len(new) > 500:
                    digest = fp(new)
                    if digest in seen:
                        stats["deduped"] += 1
                        stats["chars_saved"] += len(new)
                        out.append({**part, "text": f"[... bloc identique deja "
                                                    f"present, {len(new)} car. ...]"})
                        continue
                    seen.add(digest)
                out.append({**part, "text": new})
            msg["content"] = out

        if tool and isinstance(msg.get("output"), str):
            msg["output"] = rewrite_text(msg["output"], cap, stats)
        elif tool and isinstance(msg.get("output"), list):
            output = []
            for part in msg["output"]:
                if (isinstance(part, dict) and part.get("type") in TEXT_TYPES
                        and isinstance(part.get("text"), str)):
                    output.append({**part, "text": rewrite_text(part["text"], cap, stats)})
                else:
                    output.append(part)
            msg["output"] = output

    return data
