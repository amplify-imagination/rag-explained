"""EP1 — generate_trace.py.

Runs the EP1 RAG pipeline against the canonical EP1 query and captures
every intermediate state into trace/pipeline_trace.json. Remotion scenes
read this file directly.

Captured states (per Production Guide §EP1 schema):

    states.chunks                # First 10 chunks shown in scene 2
    states.embeddings_preview    # First 5 dims of the first 5 chunk embeddings
    states.stored_count          # Total chunks in the vector DB
    states.query_vector          # First 5 dims of the query embedding
    states.similarity_scores     # Top 10 similarity scores
    states.top_k_final           # Top 3 retrieved (text, score, source)
    states.llm_answer            # Final answer from the LLM

Re-run any time the corpus or provider changes:

    python ep01-what-is-rag/impl/generate_trace.py
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

from main import RagPipeline  # noqa: E402  (sibling import)
from llm_provider import get_provider  # noqa: E402
from trace_utils import TraceBuilder  # noqa: E402

EP_QUERY = "What is the cancellation policy for SKU-1042?"
EXPECTED_SOURCES = ["product_catalog.md", "faq.md"]
TRACE_OUT = EPISODE_DIR / "trace" / "pipeline_trace.json"


def main() -> int:
    provider = get_provider()
    print(f"[ep01:trace] provider = {provider.name} ({provider.chat_model_name})")

    # Use the persistent Chroma collection unless the user passes --force-reindex.
    # This avoids re-embedding all 150 chunks on every trace run, which would burn
    # the free-tier quota in a couple of iterations.
    force = "--force-reindex" in sys.argv
    pipeline = RagPipeline(provider=provider)
    print(f"[ep01:trace] ingesting corpus (force={force})...")
    t0 = time.perf_counter()
    stored_count = pipeline.ingest(force=force)
    ingest_ms = (time.perf_counter() - t0) * 1000.0
    print(f"[ep01:trace] indexed {stored_count} chunks in {ingest_ms:.0f}ms")

    # ---- capture state.chunks (10 chunks: SKU-1042 + 3 catalog + 6 mixed) ----
    # Scene 3 narration specifically references the product catalog, so we
    # prioritise catalog chunks (including the SKU-1042 chunk) over the load
    # order. This keeps "every value comes from real Python execution" honest
    # while making sure visuals match what the narrator says.
    chunks_payload = pipeline._load_corpus_chunks()

    def _to_record(c):
        return {
            "chunk_id": c["chunk_id"],
            "text": c["text"][:280],
            "source": c["source_file"],
            "heading_path": c["heading_path"],
        }

    catalog_chunks = [c for c in chunks_payload if c["source_file"] == "product_catalog.md"]
    sku_chunk = next((c for c in chunks_payload if "SKU-1042" in c["text"]), None)

    sample_chunks: list = []
    seen_ids: set = set()
    if sku_chunk is not None:
        sample_chunks.append(sku_chunk)
        seen_ids.add(sku_chunk["chunk_id"])
    # Then fill from catalog (skipping already-seen)
    for c in catalog_chunks:
        if c["chunk_id"] in seen_ids:
            continue
        sample_chunks.append(c)
        seen_ids.add(c["chunk_id"])
        if len(sample_chunks) >= 4:
            break
    # Then any remaining slots filled in load order from the rest of the corpus
    for c in chunks_payload:
        if len(sample_chunks) >= 10:
            break
        if c["chunk_id"] in seen_ids:
            continue
        sample_chunks.append(c)
        seen_ids.add(c["chunk_id"])

    first_10_chunks = [_to_record(c) for c in sample_chunks[:10]]
    first_5_embeddings = provider.embed([c["text"] for c in chunks_payload[:5]])
    embeddings_preview = [TraceBuilder.round_vec(v) for v in first_5_embeddings]

    # ---- capture state.query_vector ----
    t1 = time.perf_counter()
    q_vec = pipeline.embed_query(EP_QUERY)
    embed_query_ms = (time.perf_counter() - t1) * 1000.0
    query_vector = TraceBuilder.round_vec(q_vec)

    # ---- capture state.similarity_scores + top_k_final ----
    t2 = time.perf_counter()
    top_10 = pipeline.search(EP_QUERY, k=10)
    search_ms = (time.perf_counter() - t2) * 1000.0
    similarity_scores = [round(c.score, 4) for c in top_10]
    top_k_final = [
        {
            "chunk_id": c.chunk_id,
            "text": c.text[:280],
            "score": round(c.score, 4),
            "source": c.source,
        }
        for c in top_10[:3]
    ]

    # ---- capture state.llm_answer ----
    t3 = time.perf_counter()
    answer, _ = pipeline.answer(EP_QUERY, k=3)
    llm_ms = (time.perf_counter() - t3) * 1000.0

    # ---- assemble trace ----
    tb = TraceBuilder(
        episode="ep01",
        title="What is RAG?",
        query=EP_QUERY,
        expected_sources=EXPECTED_SOURCES,
    )
    tb.provider = provider.info()
    tb.corpus = {
        "total_chunks": stored_count,
        "source": "shared/corpus/corpus.json",
    }
    tb.add_state("chunks", first_10_chunks)
    tb.add_state("embeddings_preview", embeddings_preview)
    tb.add_state("stored_count", stored_count)
    tb.add_state("query_vector", query_vector)
    tb.add_state("similarity_scores", similarity_scores)
    tb.add_state("top_k_final", top_k_final)
    tb.add_state("llm_answer", answer)

    # Naive precision@3 for the scoreboard: how many of top_k_final are in expected sources
    p_at_3 = (
        sum(1 for c in top_k_final if c["source"] in EXPECTED_SOURCES) / 3.0
    )
    tb.add_metric("precision_at_3", round(p_at_3, 3))
    tb.add_metric("ingest_ms", round(ingest_ms, 1))
    tb.add_metric("embed_query_ms", round(embed_query_ms, 1))
    tb.add_metric("search_ms", round(search_ms, 1))
    tb.add_metric("llm_ms", round(llm_ms, 1))
    tb.add_metric("e2e_ms", round(embed_query_ms + search_ms + llm_ms, 1))

    out_path = tb.save(TRACE_OUT)
    print(f"\n[ep01:trace] wrote {out_path}")
    print(json.dumps(
        {
            "stored_count": stored_count,
            "p@3": round(p_at_3, 3),
            "answer_preview": answer[:200],
            "top_k_sources": [c["source"] for c in top_k_final],
        },
        indent=2,
    ))
    return 0


if __name__ == "__main__":
    sys.exit(main())
