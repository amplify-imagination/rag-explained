"""EP03 — generate_trace.py.

Captures every state the Remotion scenes need:
    states.before_top_k    # top-K from vector search (EP02-style)
    states.after_top_k     # same K reordered by reranker
    states.scatter         # cosine vs cross-encoder relevance for each chunk
    states.llm_answer      # final answer from the LLM
    states.code_files      # pipeline.py source for the Scene 4 panel
"""
from __future__ import annotations

import json
import sys
import time
from pathlib import Path

HERE = Path(__file__).resolve().parent
EPISODE_DIR = HERE.parent
ROOT = EPISODE_DIR.parent
sys.path.insert(0, str(ROOT / "shared"))
sys.path.insert(0, str(HERE))

import pipeline as ep03  # noqa: E402
from llm_provider import get_provider  # noqa: E402
from trace_utils import TraceBuilder  # noqa: E402

EP_QUERY = "What is the cancellation policy for SKU-1042?"
EXPECTED_SOURCES = ["product_catalog.md", "faq.md"]
TRACE_OUT = EPISODE_DIR / "trace" / "pipeline_trace.json"

TOP_K_RETRIEVE = 20  # broad vector recall
TOP_K_DISPLAY = 5    # what we show on screen for the rank-reorder visual


def _read_code_file(name: str, relative_to: Path) -> dict:
    p = relative_to / name
    text = p.read_text(encoding="utf-8")
    return {"name": name, "text": text, "line_count": text.count("\n") + 1}


def main() -> int:
    provider = get_provider()
    print(f"[ep03:trace] provider = {provider.name} ({provider.chat_model_name})")

    # ---- 1. Ingest (idempotent, reuses Chroma if already populated) ----
    t0 = time.perf_counter()
    stored_count = ep03.ingest()
    ingest_ms = (time.perf_counter() - t0) * 1000.0
    print(f"[ep03:trace] indexed {stored_count} chunks in {ingest_ms:.0f}ms")

    # ---- 2. Vector search (the EP02 baseline) ----
    t1 = time.perf_counter()
    retrieved = ep03.vector_search(EP_QUERY, k=TOP_K_RETRIEVE)
    search_ms = (time.perf_counter() - t1) * 1000.0
    print(f"[ep03:trace] vector search {search_ms:.0f}ms; top-1 cosine={retrieved[0]['score']:.4f}")

    before_top_k = [
        {"rank": i + 1, "text": c["text"][:280], "source": c["source"], "score": round(c["score"], 4)}
        for i, c in enumerate(retrieved[:TOP_K_DISPLAY])
    ]

    # ---- 3. Rerank (force a fresh reranker call so we can time it) ----
    # Make a deep-ish copy so rerank() doesn't mutate the original retrieved list
    candidates = [dict(c) for c in retrieved]
    t2 = time.perf_counter()
    reranked = ep03.rerank(EP_QUERY, candidates, top_n=TOP_K_RETRIEVE)
    rerank_ms = (time.perf_counter() - t2) * 1000.0
    print(f"[ep03:trace] rerank {rerank_ms:.0f}ms; top-1 relevance={reranked[0]['rerank_score']:.4f}")

    after_top_k = [
        {
            "rank": i + 1,
            "text": c["text"][:280],
            "source": c["source"],
            "score": round(c["score"], 4),
            "rerank_score": round(c["rerank_score"], 4),
        }
        for i, c in enumerate(reranked[:TOP_K_DISPLAY])
    ]

    # ---- 4. Scatter — cosine vs cross-encoder relevance for ALL retrieved ----
    # Each retrieved chunk has both scores after rerank. Find the original rank
    # so the visual can show "this dot moved from rank 7 to rank 2".
    text_to_orig_rank = {c["text"]: i + 1 for i, c in enumerate(retrieved)}
    text_to_new_rank = {c["text"]: i + 1 for i, c in enumerate(reranked)}
    scatter = [
        {
            "cosine": round(c["score"], 4),
            "relevance": round(c["rerank_score"], 4),
            "source": c["source"],
            "orig_rank": text_to_orig_rank[c["text"]],
            "new_rank": text_to_new_rank[c["text"]],
            "text_preview": c["text"][:80],
        }
        for c in candidates  # candidates was rerank-sorted in place; same content as reranked
    ]

    # ---- 5. LLM answer ----
    t3 = time.perf_counter()
    llm_answer = ep03.answer(EP_QUERY, top_k_retrieve=TOP_K_RETRIEVE, top_n_rerank=3)
    llm_ms = (time.perf_counter() - t3) * 1000.0

    # ---- 6. Code files for Scene 4 ----
    code_files = [_read_code_file("pipeline.py", HERE)]

    # ---- 7. Precision-at-3 before vs after ----
    expected = set(EXPECTED_SOURCES)
    p_at_3_before = sum(1 for c in retrieved[:3] if c["source"] in expected) / 3.0
    p_at_3_after = sum(1 for c in reranked[:3] if c["source"] in expected) / 3.0

    # ---- 8. Assemble trace ----
    tb = TraceBuilder(
        episode="ep03",
        title="Reranking — when 'close' isn't 'right'",
        query=EP_QUERY,
        expected_sources=EXPECTED_SOURCES,
    )
    tb.provider = provider.info()
    tb.corpus = {"total_chunks": stored_count}
    tb.add_state("before_top_k", before_top_k)
    tb.add_state("after_top_k", after_top_k)
    tb.add_state("scatter", scatter)
    tb.add_state("llm_answer", llm_answer)
    tb.add_state("code_files", code_files)
    tb.add_state("reranker_model", ep03.RERANKER_MODEL)

    tb.add_metric("ingest_ms", round(ingest_ms, 1))
    tb.add_metric("search_ms", round(search_ms, 1))
    tb.add_metric("rerank_ms", round(rerank_ms, 1))
    tb.add_metric("llm_ms", round(llm_ms, 1))
    tb.add_metric("p_at_3_before", round(p_at_3_before, 3))
    tb.add_metric("p_at_3_after", round(p_at_3_after, 3))

    out_path = tb.save(TRACE_OUT)
    print(f"\n[ep03:trace] wrote {out_path}")
    print(json.dumps(
        {
            "p@3 before": p_at_3_before,
            "p@3 after": p_at_3_after,
            "search_ms": round(search_ms, 1),
            "rerank_ms": round(rerank_ms, 1),
            "answer_preview": llm_answer[:160],
            "before_sources": [c["source"] for c in retrieved[:3]],
            "after_sources": [c["source"] for c in reranked[:3]],
        },
        indent=2,
    ))
    return 0


if __name__ == "__main__":
    sys.exit(main())
