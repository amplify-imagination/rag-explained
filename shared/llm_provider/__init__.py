"""LLM provider abstraction for the RAG Explained playlist.

Every episode imports `get_provider()` and never names a vendor directly.
Switching from Gemini → OpenAI → Ollama is a single env-var change.

Usage:

    from llm_provider import get_provider
    p = get_provider()  # reads SHOW_AND_TELL_PROVIDER, default 'gemini'
    vecs = p.embed(["hello", "world"])
    answer = p.chat([{"role": "user", "content": "Why is the sky blue?"}])

Selection by env var:
    SHOW_AND_TELL_PROVIDER=gemini      (default — free tier, fastest setup)
    SHOW_AND_TELL_PROVIDER=openai      (paid, used in EP8 evaluation comparisons)
    SHOW_AND_TELL_PROVIDER=ollama      (local, zero-network)
    SHOW_AND_TELL_PROVIDER=jina-local  (Jina v3 — embed-only; deferred due
                                        to transformers compat issue)
    SHOW_AND_TELL_PROVIDER=bge-m3      (EP5 late chunking — BAAI/bge-m3,
                                        embed-only, compose with chat provider)

Each provider is independently importable so missing keys for one provider
don't break the others.
"""
from __future__ import annotations

import os
from pathlib import Path

# Auto-load .env files so episode scripts (generate_trace.py etc.) pick up
# keys without needing `export GEMINI_API_KEY=...` every shell.
# Order: ~/.env first (global), then repo-local .env (overrides nothing).
try:
    from dotenv import load_dotenv
    load_dotenv(Path.home() / ".env")
    # Walk up to find the repo root .env (the one next to .env.example)
    here = Path(__file__).resolve()
    for parent in [here.parent, *here.parents]:
        if (parent / ".env.example").exists():
            load_dotenv(parent / ".env", override=False)
            break
except ImportError:
    # python-dotenv not installed — fall back to env vars set in the shell
    pass

from .base import LLMProvider, ProviderError

__all__ = ["LLMProvider", "ProviderError", "get_provider"]


def get_provider(name: str | None = None) -> LLMProvider:
    """Return an LLMProvider instance for the given name (or env default).

    Selection order:
      1. Explicit `name` argument
      2. SHOW_AND_TELL_PROVIDER env var
      3. Auto-detect: if GEMINI_API_KEY (or GOOGLE_API_KEY) is set → gemini,
         else fall back to synthetic with a printed warning so CI / no-key dev
         still works end-to-end.

    Lazy imports the concrete provider so a missing optional dep
    (e.g. openai SDK) doesn't fail when using gemini.
    """
    explicit = name or os.getenv("SHOW_AND_TELL_PROVIDER")
    if explicit:
        chosen = explicit.strip().lower()
    elif os.getenv("GEMINI_API_KEY") or os.getenv("GOOGLE_API_KEY"):
        chosen = "gemini"
    else:
        import sys
        print(
            "[llm_provider] no GEMINI_API_KEY found; using synthetic provider. "
            "Get a free key at https://aistudio.google.com and set "
            "GEMINI_API_KEY in .env to swap to real Gemini.",
            file=sys.stderr,
        )
        chosen = "synthetic"

    if chosen == "gemini":
        from .gemini import GeminiProvider
        return GeminiProvider()
    if chosen == "openai":
        from .openai_provider import OpenAIProvider
        return OpenAIProvider()
    if chosen == "ollama":
        from .ollama import OllamaProvider
        return OllamaProvider()
    if chosen in ("jina-local", "jina_local"):
        from .jina_local import JinaLocalProvider
        return JinaLocalProvider()
    if chosen in ("bge-m3", "bge_m3", "bgem3"):
        from .bge_m3 import BGEM3Provider
        return BGEM3Provider()
    if chosen == "synthetic":
        from .synthetic import SyntheticProvider
        return SyntheticProvider()
    raise ProviderError(
        f"Unknown provider: {chosen!r}. Valid: gemini, openai, ollama, jina-local, bge-m3, synthetic."
    )
