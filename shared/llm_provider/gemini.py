"""Gemini provider — the default free-tier stack for the playlist.

Uses the official google-genai SDK. Free Gemini API keys come from
https://aistudio.google.com (30-second signup).

Models (live as of 2026-05; older `text-embedding-004` was deprecated):
  chat:      gemini-2.5-flash             (current Flash; replaces 2.0)
  embedding: gemini-embedding-001          (default 3072 dims, truncatable)

We request 768 output dimensions explicitly for compact traces compatible
with the rest of the playlist's expectations. Override per env if you want
the full 3072 vectors.

Env:
  GEMINI_API_KEY                (required)
  GEMINI_CHAT_MODEL             (override, default gemini-2.5-flash)
  GEMINI_EMBEDDING_MODEL        (override, default gemini-embedding-001)
  GEMINI_EMBEDDING_DIM          (override, default 768; valid: 768/1536/3072)
"""
from __future__ import annotations

import os
import re
import sys
import time
from typing import Sequence

from .base import ChatResult, LLMProvider, ProviderError


def _retry_after_seconds(exc: Exception) -> float:
    """Extract Google's `retryDelay: 42s` hint from a 429 ClientError. Default 30s."""
    msg = str(exc)
    m = re.search(r"retryDelay['\"]?\s*:\s*['\"]?(\d+(?:\.\d+)?)s", msg)
    if m:
        return float(m.group(1))
    return 30.0


def _is_rate_limit(exc: Exception) -> bool:
    return "429" in str(exc) or "RESOURCE_EXHAUSTED" in str(exc)


def _with_backoff(fn, *args, max_retries: int = 4, **kwargs):
    """Call fn with retry-on-429 using the server's retryDelay hint."""
    for attempt in range(max_retries):
        try:
            return fn(*args, **kwargs)
        except Exception as e:
            if _is_rate_limit(e) and attempt < max_retries - 1:
                wait = _retry_after_seconds(e) + 2.0
                print(f"[gemini] rate-limited, sleeping {wait:.0f}s (attempt {attempt + 1}/{max_retries})", file=sys.stderr)
                time.sleep(wait)
                continue
            raise


class GeminiProvider(LLMProvider):
    name = "gemini"

    def __init__(self) -> None:
        try:
            from google import genai
            from google.genai import types as gen_types
        except ImportError as exc:
            raise ProviderError(
                "google-genai is not installed. pip install google-genai"
            ) from exc

        api_key = os.getenv("GEMINI_API_KEY") or os.getenv("GOOGLE_API_KEY")
        if not api_key:
            raise ProviderError(
                "GEMINI_API_KEY not set. Get one free at https://aistudio.google.com"
            )

        self.chat_model_name = os.getenv("GEMINI_CHAT_MODEL", "gemini-2.5-flash")
        # Separate vision model — qa_episode.py uses Gemma 4 (open-weight) via the
        # same GEMINI_API_KEY for vision review. No internal thinking budget,
        # cheaper input tokens than Gemini 3, free tier sufficient. Override with
        # GEMINI_VISION_MODEL=gemma-4-26b-a4b-it for faster MoE variant.
        self.vision_model_name = os.getenv("GEMINI_VISION_MODEL", "gemma-4-31b-it")
        self.embedding_model_name = os.getenv("GEMINI_EMBEDDING_MODEL", "gemini-embedding-001")
        try:
            self.embedding_dim = int(os.getenv("GEMINI_EMBEDDING_DIM", "768"))
        except ValueError:
            self.embedding_dim = 768

        self._client = genai.Client(api_key=api_key)
        self._types = gen_types

    def embed(self, texts: Sequence[str]) -> list[list[float]]:
        if not texts:
            return []
        cfg = self._types.EmbedContentConfig(output_dimensionality=self.embedding_dim)

        # Free-tier embed limit is 100 RPM and "list of N" counts as N requests.
        # We process in small chunks and sleep between to stay safely under the cap.
        # Each chunk-call also wraps with backoff so a 429 self-heals.
        CHUNK = 20            # 20 texts per request — well under per-request size limits
        SLEEP_BETWEEN = 0.5   # 0.5s between batches; effective ~40 RPS bursts max

        out: list[list[float]] = []
        for i in range(0, len(texts), CHUNK):
            batch = list(texts[i : i + CHUNK])
            result = _with_backoff(
                self._client.models.embed_content,
                model=self.embedding_model_name,
                contents=batch,
                config=cfg,
            )
            out.extend(list(emb.values) for emb in result.embeddings)
            if i + CHUNK < len(texts):
                time.sleep(SLEEP_BETWEEN)
        return out

    def chat(
        self,
        messages: list[dict],
        *,
        temperature: float = 0.0,
        max_tokens: int = 512,
    ) -> ChatResult:
        system_parts = [m["content"] for m in messages if m["role"] == "system"]
        user_msgs = [m for m in messages if m["role"] == "user"]
        system_instruction = "\n\n".join(system_parts) if system_parts else None

        # Vision support: any user message with `image_path` becomes an image part.
        # Gemini accepts contents=[Part.from_bytes(...), text] for multimodal input.
        has_vision = any(m.get("image_path") for m in user_msgs)
        if has_vision:
            from pathlib import Path as _P
            parts: list = []
            for m in user_msgs:
                if m.get("image_path"):
                    img_bytes = _P(m["image_path"]).read_bytes()
                    parts.append(self._types.Part.from_bytes(data=img_bytes, mime_type="image/png"))
                if m.get("content"):
                    parts.append(m["content"])
            contents = parts
        else:
            contents = "\n\n".join(m["content"] for m in user_msgs)

        config = self._types.GenerateContentConfig(
            temperature=temperature,
            max_output_tokens=max_tokens,
            system_instruction=system_instruction,
        )
        # Use vision_model_name when image parts are present; otherwise chat model.
        model = self.vision_model_name if has_vision else self.chat_model_name
        resp = _with_backoff(
            self._client.models.generate_content,
            model=model,
            contents=contents,
            config=config,
        )

        # google-genai returns usage_metadata on the response
        usage = getattr(resp, "usage_metadata", None)
        in_tok = getattr(usage, "prompt_token_count", None) if usage else None
        out_tok = getattr(usage, "candidates_token_count", None) if usage else None

        return ChatResult(
            text=resp.text or "",
            input_tokens=in_tok,
            output_tokens=out_tok,
            cost_usd=0.0,  # free tier
            raw_meta={
                "finish_reason": getattr(resp.candidates[0], "finish_reason", None) if resp.candidates else None,
            },
        )
