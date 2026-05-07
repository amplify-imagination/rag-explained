"""Ollama provider — local, zero-network, zero-cost.

Stig has Ollama / LM Studio set up locally per the local-env memory.
This is the fallback for engineers who don't want to register for a
free Gemini key, and for the EP8 evaluation episode that compares
local vs hosted models.

Models (override via env):
  chat:      gemma3:27b               (or whatever you've pulled)
  embedding: nomic-embed-text          (768 dims)

Env:
  OLLAMA_HOST           (default: http://localhost:11434)
  OLLAMA_CHAT_MODEL     (override)
  OLLAMA_EMBEDDING_MODEL (override)
"""
from __future__ import annotations

import os
from typing import Sequence

from .base import ChatResult, LLMProvider, ProviderError


class OllamaProvider(LLMProvider):
    name = "ollama"

    def __init__(self) -> None:
        try:
            import ollama  # noqa: F401
        except ImportError as exc:
            raise ProviderError(
                "ollama Python client not installed. pip install ollama"
            ) from exc

        from ollama import Client

        host = os.getenv("OLLAMA_HOST", "http://localhost:11434")
        self.chat_model_name = os.getenv("OLLAMA_CHAT_MODEL", "gemma3:27b")
        self.embedding_model_name = os.getenv("OLLAMA_EMBEDDING_MODEL", "nomic-embed-text")
        self.embedding_dim = 768

        self._client = Client(host=host)

    def embed(self, texts: Sequence[str]) -> list[list[float]]:
        out: list[list[float]] = []
        for t in texts:
            resp = self._client.embed(model=self.embedding_model_name, input=t)
            # ollama returns {"embeddings": [[...]]} for single input
            embs = resp.get("embeddings") or [resp.get("embedding")]
            out.append(list(embs[0]))
        return out

    def chat(
        self,
        messages: list[dict],
        *,
        temperature: float = 0.0,
        max_tokens: int = 512,
    ) -> ChatResult:
        resp = self._client.chat(
            model=self.chat_model_name,
            messages=messages,
            options={"temperature": temperature, "num_predict": max_tokens},
        )
        msg = resp.get("message", {})
        text = msg.get("content", "")
        # ollama exposes prompt_eval_count + eval_count
        in_tok = resp.get("prompt_eval_count")
        out_tok = resp.get("eval_count")
        return ChatResult(
            text=text,
            input_tokens=in_tok,
            output_tokens=out_tok,
            cost_usd=0.0,
            raw_meta={"done_reason": resp.get("done_reason")},
        )
