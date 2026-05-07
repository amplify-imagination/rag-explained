"""Thin wrapper around the embedding + chat models.

Swap Gemini for OpenAI or Ollama by changing this file. The pipeline
never imports a vendor SDK directly.
"""
from __future__ import annotations

import os
import sys
from pathlib import Path

# Reuse the shared provider abstraction so EP02 stays in lockstep with EP01.
SHARED = Path(__file__).resolve().parent.parent.parent / "shared"
sys.path.insert(0, str(SHARED))

from llm_provider import get_provider  # noqa: E402

PROVIDER = get_provider()  # Gemini Flash by default — see ../.env


def embed(texts: list[str]) -> list[list[float]]:
    """Return one 768-dim vector per input text."""
    return PROVIDER.embed(texts)


def chat(prompt: str, max_tokens: int = 400) -> str:
    """Send a prompt to the chat model and return the answer text."""
    result = PROVIDER.chat(
        [{"role": "user", "content": prompt}],
        temperature=0.0,
        max_tokens=max_tokens,
    )
    return result.text
