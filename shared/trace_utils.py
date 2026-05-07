"""TraceBuilder — the contract between the real pipeline and the animation.

Every episode's `generate_trace.py` constructs one of these and saves it as
`trace/pipeline_trace.json`. Remotion scenes read that file back; the JSON is
the *only* thing that crosses from Layer 1 (reality) to Layer 2 (animation).

The schema is versioned. Bumps require updating `TRACE_SCHEMA_VERSION` and
adding a migration hint in references/trace-schema.md.

Standard top-level keys:

    {
      "trace_schema_version": "1",
      "episode": "ep01",
      "title": "What is RAG?",
      "query": "...",
      "expected_sources": ["faq.md", ...],
      "provider": {...},
      "corpus": {...},
      "states": {
          # Per-episode keys live here. EP1 uses chunks, embeddings_preview,
          # stored_count, query_vector, similarity_scores, top_k_final, llm_answer.
      },
      "metrics": {
          # Reproducible measurements that feed shared/scoreboard.json.
      },
      "generated_at": "ISO-8601 UTC"
    }

Use `TraceBuilder.add_state()` for any free-form per-episode state and
`add_metric()` for scoreboard contributions.
"""
from __future__ import annotations

import datetime as _dt
import json
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any

TRACE_SCHEMA_VERSION = "1"


@dataclass
class TraceBuilder:
    episode: str
    title: str
    query: str
    expected_sources: list[str] = field(default_factory=list)
    states: dict[str, Any] = field(default_factory=dict)
    metrics: dict[str, Any] = field(default_factory=dict)
    provider: dict[str, Any] = field(default_factory=dict)
    corpus: dict[str, Any] = field(default_factory=dict)

    def add_state(self, key: str, value: Any) -> None:
        self.states[key] = value

    def add_metric(self, key: str, value: Any) -> None:
        self.metrics[key] = value

    def to_dict(self) -> dict:
        return {
            "trace_schema_version": TRACE_SCHEMA_VERSION,
            "episode": self.episode,
            "title": self.title,
            "query": self.query,
            "expected_sources": self.expected_sources,
            "provider": self.provider,
            "corpus": self.corpus,
            "states": self.states,
            "metrics": self.metrics,
            "generated_at": _dt.datetime.now(_dt.timezone.utc).isoformat(),
        }

    def save(self, path: str | Path) -> Path:
        p = Path(path)
        p.parent.mkdir(parents=True, exist_ok=True)
        p.write_text(json.dumps(self.to_dict(), indent=2, ensure_ascii=False))
        return p

    @staticmethod
    def round_vec(vec, dims: int = 5, places: int = 4) -> list[float]:
        """Truncate + round a vector for display. Used for `embeddings_preview`."""
        return [round(float(x), places) for x in list(vec)[:dims]]
