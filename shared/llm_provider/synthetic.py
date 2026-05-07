"""Synthetic provider — deterministic local stub used for CI and pre-key dev.

This provider produces plausible-shaped embeddings and answers without making
any network calls. Embeddings are derived from a hashed-bag-of-words projection
into 384 dims (just enough to pass downstream cosine-similarity machinery and
return non-degenerate rankings). Chat completions are template-based.

Use cases:
  * CI / smoke tests with no API key
  * Reviewing the pipeline structure before wiring real providers
  * Demonstrating that the trace contract is provider-agnostic

Not for: shipping real episode traces. Replace with a real provider before
generating the trace that's committed to the repo.

Selection: SHOW_AND_TELL_PROVIDER=synthetic
"""
from __future__ import annotations

import hashlib
import math
import re
from typing import Sequence

from .base import ChatResult, LLMProvider

_TOKEN_RE = re.compile(r"[A-Za-z][A-Za-z0-9_-]+")


def _bag(text: str) -> list[str]:
    return [t.lower() for t in _TOKEN_RE.findall(text)]


def _hash_to_unit_vector(tokens: list[str], dim: int = 384) -> list[float]:
    """Random-projection-style embedding from token bag. Deterministic per text."""
    vec = [0.0] * dim
    for tok in tokens:
        h = int.from_bytes(hashlib.sha1(tok.encode("utf-8")).digest()[:8], "big")
        for i in range(8):
            idx = (h >> (i * 5)) & (dim - 1)
            sign = 1.0 if ((h >> (40 + i)) & 1) else -1.0
            vec[idx] += sign
    norm = math.sqrt(sum(x * x for x in vec)) or 1.0
    return [x / norm for x in vec]


class SyntheticProvider(LLMProvider):
    name = "synthetic"
    chat_model_name = "synthetic-stub-1.0"
    embedding_model_name = "synthetic-hash-bow-384"
    embedding_dim = 384

    def embed(self, texts: Sequence[str]) -> list[list[float]]:
        return [_hash_to_unit_vector(_bag(t)) for t in texts]

    def chat(
        self,
        messages: list[dict],
        *,
        temperature: float = 0.0,
        max_tokens: int = 512,
    ) -> ChatResult:
        # Build a canned but content-aware answer from the user prompt + any
        # 'context' the prompt template usually injects.
        user = "\n".join(m["content"] for m in messages if m["role"] == "user")
        # Extract a context block if present in the standard RAG template
        ctx_match = re.search(r"Context:\s*(.+?)(?:Question:|Q:)", user, re.S)
        ctx = ctx_match.group(1).strip() if ctx_match else ""
        q_match = re.search(r"(?:Question|Q):\s*(.+)$", user, re.S)
        question = q_match.group(1).strip() if q_match else user.strip()

        if ctx:
            # Pull the first 2 sentences from context that mention any token in question
            q_tokens = set(_bag(question))
            sentences = re.split(r"(?<=[.!?])\s+", ctx)
            relevant = [s for s in sentences if q_tokens & set(_bag(s))][:2]
            answer = " ".join(relevant) if relevant else (sentences[0] if sentences else "")
            text = f"Based on the retrieved context: {answer}".strip()
        else:
            text = "[synthetic stub answer — replace SHOW_AND_TELL_PROVIDER with gemini/openai/ollama for a real model]"

        return ChatResult(
            text=text,
            input_tokens=len(user.split()),
            output_tokens=len(text.split()),
            cost_usd=0.0,
            raw_meta={"finish_reason": "stop", "synthetic": True},
        )
