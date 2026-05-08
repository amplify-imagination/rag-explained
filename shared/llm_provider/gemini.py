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

import json
import os
import re
import sys
import time
from datetime import datetime, timedelta, timezone
from pathlib import Path
from typing import Sequence

from .base import ChatResult, LLMProvider, ProviderError

# ── Daily budget tracker ─────────────────────────────────────────────
# Free tier: 1000 embed_content requests/day per project (UTC midnight reset).
# We persist a counter and warn/abort when approaching the cap. Set
# GEMINI_DAILY_EMBED_BUDGET=<int> to override the soft cap (defaults 900 — 10%
# safety margin). Set GEMINI_BUDGET_DISABLE=1 to turn the tracker off entirely.
_BUDGET_DIR = Path.home() / "SoMe" / "rag-explained" / ".runtime"
_BUDGET_FILE = _BUDGET_DIR / "gemini_quota.json"
_BUDGET_SOFT_CAP = int(os.getenv("GEMINI_DAILY_EMBED_BUDGET", "900"))
_BUDGET_DISABLED = os.getenv("GEMINI_BUDGET_DISABLE") == "1"


def _utc_today_key() -> str:
    """Return the date key Google's free-tier RPD quota uses.

    Google resets free-tier daily quotas at midnight Pacific Time (UTC-7 in PDT,
    UTC-8 in PST). We approximate the boundary as "8 hours behind UTC" — close
    enough for the safety margin we operate with. Off by ~1h during DST
    shoulders is fine; the soft cap (900 vs 1000) absorbs that.
    """
    pacific = datetime.now(timezone.utc).astimezone(timezone(timedelta(hours=-8)))
    return pacific.strftime("%Y-%m-%d")


def _read_budget() -> dict:
    if not _BUDGET_FILE.exists():
        return {"date": _utc_today_key(), "embed_count": 0}
    try:
        d = json.loads(_BUDGET_FILE.read_text())
    except Exception:
        return {"date": _utc_today_key(), "embed_count": 0}
    if d.get("date") != _utc_today_key():
        return {"date": _utc_today_key(), "embed_count": 0}
    return d


def _write_budget(d: dict) -> None:
    _BUDGET_DIR.mkdir(parents=True, exist_ok=True)
    _BUDGET_FILE.write_text(json.dumps(d))


def _check_budget(planned_calls: int) -> None:
    if _BUDGET_DISABLED:
        return
    d = _read_budget()
    used = d["embed_count"]
    remaining = _BUDGET_SOFT_CAP - used
    if planned_calls > remaining:
        print(
            f"[gemini] DAILY EMBED BUDGET ALMOST GONE: {used}/{_BUDGET_SOFT_CAP} "
            f"used today (UTC), need {planned_calls} more, {remaining} remaining. "
            f"Set GEMINI_BUDGET_DISABLE=1 to override, or wait until UTC midnight reset.",
            file=sys.stderr,
        )
        raise ProviderError(
            f"Gemini daily embed budget exhausted ({used} used, {planned_calls} requested, "
            f"cap={_BUDGET_SOFT_CAP}). Override with GEMINI_BUDGET_DISABLE=1."
        )
    if used > 0 or planned_calls > 50:
        # Only print on substantial usage — quiet for tiny scripts
        print(
            f"[gemini] embed budget: {used}/{_BUDGET_SOFT_CAP} used today, "
            f"requesting {planned_calls} more.",
            file=sys.stderr,
        )


def _record_budget(actual_calls: int) -> None:
    if _BUDGET_DISABLED:
        return
    d = _read_budget()
    d["embed_count"] = d.get("embed_count", 0) + actual_calls
    _write_budget(d)


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
        # Pre-flight: bail out if today's budget is exhausted, so we don't waste
        # 60+ seconds on retry-backoff just to crash with 429.
        _check_budget(len(texts))
        cfg = self._types.EmbedContentConfig(output_dimensionality=self.embedding_dim)

        # Free-tier embed limit is 100 RPM and "list of N" counts as N requests.
        # We process in small chunks and sleep between to stay safely under the cap.
        # Each chunk-call also wraps with backoff so a 429 self-heals.
        # Budget: CHUNK / SLEEP_BETWEEN must stay below 100/60 = 1.67 RPS to fit
        # the per-minute quota with headroom. 10 / 8s = 75 RPM steady-state, leaves
        # 25 RPM buffer for the chat() calls in the same script.
        CHUNK = 10            # 10 texts per request — counts as 10 against the RPM quota
        SLEEP_BETWEEN = 8.0   # 8s between batches; effective ~75 RPM steady-state

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
            _record_budget(len(batch))
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
