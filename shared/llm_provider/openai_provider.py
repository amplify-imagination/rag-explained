"""OpenAI provider — paid, used in EP8 (RAG evaluation) for side-by-side comparisons.

Models:
  chat:      gpt-4o-mini              (cheapest GPT-4 class)
  embedding: text-embedding-3-small   (cheap, 1536 dims, strong on English)

Env:
  OPENAI_API_KEY              (required)
  OPENAI_CHAT_MODEL           (override)
  OPENAI_EMBEDDING_MODEL      (override)

Cost is computed using public per-token pricing snapshotted in this file. Update
PRICE_TABLE if the pricing page changes.
"""
from __future__ import annotations

import os
from typing import Sequence

from .base import ChatResult, LLMProvider, ProviderError

# USD per 1K tokens — snapshot 2026-05. Update if needed.
PRICE_TABLE = {
    "gpt-4o-mini":             {"input": 0.00015, "output": 0.0006},
    "text-embedding-3-small":  {"input": 0.00002, "output": 0.0},
}


class OpenAIProvider(LLMProvider):
    name = "openai"

    def __init__(self) -> None:
        try:
            from openai import OpenAI
        except ImportError as exc:
            raise ProviderError(
                "openai is not installed. pip install openai"
            ) from exc

        api_key = os.getenv("OPENAI_API_KEY")
        if not api_key:
            raise ProviderError("OPENAI_API_KEY not set.")

        self.chat_model_name = os.getenv("OPENAI_CHAT_MODEL", "gpt-4o-mini")
        self.embedding_model_name = os.getenv("OPENAI_EMBEDDING_MODEL", "text-embedding-3-small")
        self.embedding_dim = 1536

        self._client = OpenAI(api_key=api_key)

    def _cost(self, model: str, in_tok: int | None, out_tok: int | None) -> float:
        price = PRICE_TABLE.get(model)
        if not price or in_tok is None:
            return 0.0
        c = (in_tok / 1000.0) * price["input"]
        if out_tok:
            c += (out_tok / 1000.0) * price["output"]
        return round(c, 6)

    def embed(self, texts: Sequence[str]) -> list[list[float]]:
        if not texts:
            return []
        resp = self._client.embeddings.create(
            model=self.embedding_model_name,
            input=list(texts),
        )
        return [row.embedding for row in resp.data]

    def chat(
        self,
        messages: list[dict],
        *,
        temperature: float = 0.0,
        max_tokens: int = 512,
    ) -> ChatResult:
        resp = self._client.chat.completions.create(
            model=self.chat_model_name,
            messages=messages,
            temperature=temperature,
            max_tokens=max_tokens,
        )
        choice = resp.choices[0]
        usage = resp.usage
        return ChatResult(
            text=choice.message.content or "",
            input_tokens=usage.prompt_tokens if usage else None,
            output_tokens=usage.completion_tokens if usage else None,
            cost_usd=self._cost(
                self.chat_model_name,
                usage.prompt_tokens if usage else None,
                usage.completion_tokens if usage else None,
            ),
            raw_meta={"finish_reason": choice.finish_reason},
        )
