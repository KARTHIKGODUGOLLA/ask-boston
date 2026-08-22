"""One place that knows how to talk to a model.

Everything in civic/ goes through here, so switching models (or dropping to
a cloud fallback at 2pm when a laptop melts) is a one-line change, not a
grep-and-pray across six files.

Env:
  OLLAMA_MODEL   default granite3.1-dense:8b
  CIVIC_SQL_MODEL   optional; a code-tuned model for text-to-SQL only
                    (qwen2.5:7b is a good pick if you pulled it)
"""
from __future__ import annotations

import os
import re
import sys
from functools import lru_cache

CHAT_MODEL = os.environ.get("OLLAMA_MODEL", "granite3.1-dense:8b")
SQL_MODEL = os.environ.get("CIVIC_SQL_MODEL", CHAT_MODEL)


@lru_cache(maxsize=4)
def _client(model: str):
    from langchain_ollama import ChatOllama
    return ChatOllama(model=model, temperature=0)


def complete(prompt: str, model: str | None = None) -> str | None:
    """One completion, or None if the model is unreachable. Never raises."""
    name = model or CHAT_MODEL
    try:
        return _client(name).invoke(prompt).content.strip()
    except Exception as exc:
        print(f"[!] model '{name}' unreachable ({type(exc).__name__}): {exc}", file=sys.stderr)
        print(f"[!] fix: ollama serve && ollama pull {name}", file=sys.stderr)
        return None


def first_word(text: str | None, allowed: tuple[str, ...], default: str) -> str:
    """Pull one label out of a chatty model reply. Small models editorialize."""
    if not text:
        return default
    low = text.lower()
    hits = [(low.find(a), a) for a in allowed if a in low]
    return min(hits)[1] if hits else default


def extract_code(text: str | None, lang: str = "sql") -> str | None:
    """Strip ```sql fences that models add no matter how you ask them not to."""
    if not text:
        return None
    fenced = re.search(rf"```(?:{lang})?\s*(.+?)```", text, re.S | re.I)
    body = (fenced.group(1) if fenced else text).strip()
    return body or None
