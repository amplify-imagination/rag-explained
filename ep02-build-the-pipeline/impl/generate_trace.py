"""EP02 — generate_trace.py.

Runs the EP02 pipeline (60-line tutorial version: pipeline.py + provider.py
+ corpus_loader.py) against the canonical query and captures every state
the Remotion scenes need. Differs from EP01's trace in three ways:

    states.code_files            # raw text of pipeline.py / provider.py / corpus_loader.py
                                 # so Scene 2 can show the source on screen
    states.chroma_sql_preview    # actual SQLite query + result rows from Chroma's
                                 # internal DB — proves Scene 5's "it's just SQLite" beat
    states.prompt_template       # the f-string with placeholders
    states.assembled_prompt      # the rendered prompt with the 3 retrieved chunks

Run:

    python ep02-build-the-pipeline/impl/generate_trace.py
"""
from __future__ import annotations

import fcntl
import json
import sqlite3
import sys
import time
from pathlib import Path

# ── Single-instance guard ──────────────────────────────────────────────
# See ep04-chunking-benchmarks/impl/generate_trace.py for rationale —
# Gemini free-tier 1000-embed daily quota is per-PROJECT, both ~/.env keys
# share it, and parallel runs blow it through in seconds.
_LOCK_PATH = Path(__file__).resolve().parent / ".generate_trace.lock"
_LOCK_FH = open(_LOCK_PATH, "w")
try:
    fcntl.flock(_LOCK_FH, fcntl.LOCK_EX | fcntl.LOCK_NB)
except BlockingIOError:
    print(
        f"[ep02:trace] ABORT — another generate_trace.py is already running "
        f"(lock {_LOCK_PATH}). Kill it first: `pkill -f generate_trace.py`.",
        file=sys.stderr,
    )
    sys.exit(2)

HERE = Path(__file__).resolve().parent
EPISODE_DIR = HERE.parent
ROOT = EPISODE_DIR.parent
sys.path.insert(0, str(ROOT / "shared"))
sys.path.insert(0, str(HERE))

import pipeline as ep02  # the 60-line tutorial pipeline  # noqa: E402
from llm_provider import get_provider  # noqa: E402
from trace_utils import TraceBuilder  # noqa: E402

EP_QUERY = "What is the cancellation policy for SKU-1042?"
EXPECTED_SOURCES = ["product_catalog.md", "faq.md"]
TRACE_OUT = EPISODE_DIR / "trace" / "pipeline_trace.json"


def _read_code_file(name: str) -> dict:
    """Capture a source file as text + line count for the Scene 2 code panel."""
    path = HERE / name
    text = path.read_text(encoding="utf-8")
    return {
        "name": name,
        "text": text,
        "line_count": text.count("\n") + 1,
    }


def _chroma_sql_preview(persist_dir: str, collection_name: str) -> dict:
    """Run a real SQL query against Chroma's SQLite file.

    Scene 5's aha moment is "Chroma is just SQLite". So we open the
    actual sqlite file and pull a few rows out of the embeddings_queue
    + segments tables. We don't pretend — we hand the visualizer the
    exact column names and a slice of real values.
    """
    db_path = Path(persist_dir) / "chroma.sqlite3"
    if not db_path.exists():
        return {
            "available": False,
            "reason": f"chroma.sqlite3 not at {db_path}",
        }

    con = sqlite3.connect(db_path)
    con.row_factory = sqlite3.Row

    tables = [
        r["name"]
        for r in con.execute(
            "SELECT name FROM sqlite_master WHERE type='table' ORDER BY name"
        ).fetchall()
    ]

    # Documents live in `embedding_metadata` keyed 'chroma:document'.
    # The actual float-vector blob lives inside Chroma's segment files (HNSW
    # binary). We surface that fact in the result by reporting the embedding
    # dimension * 4 bytes (Chroma stores float32 internally).
    DIM_BYTES = 768 * 4  # gemini-embedding-001 dim × float32
    sql = (
        "-- chunks_payload sitting on disk\n"
        "SELECT em.id AS chunk_id,\n"
        "       substr(em.string_value, 1, 80) AS text_preview\n"
        "FROM embedding_metadata em\n"
        "WHERE em.key = 'chroma:document'\n"
        "ORDER BY em.id\n"
        "LIMIT 3;"
    )
    rows: list[dict] = []
    try:
        for r in con.execute(sql).fetchall():
            rows.append({
                "chunk_id": r["chunk_id"],
                "text_preview": r["text_preview"],
                "embedding_bytes": DIM_BYTES,
            })
    except sqlite3.Error as exc:
        rows = [{"error": str(exc)}]

    # Also count rows so the SQL panel can show the running total.
    try:
        total = con.execute(
            "SELECT COUNT(*) AS n FROM embedding_metadata WHERE key='chroma:document';"
        ).fetchone()["n"]
    except sqlite3.Error:
        total = None

    con.close()
    return {
        "available": True,
        "db_path": str(db_path),
        "tables": tables,
        "sql": sql,
        "rows": rows,
        "row_count": total,
        "columns": ["chunk_id", "text_preview", "embedding_bytes"],
    }


def main() -> int:
    provider = get_provider()
    print(f"[ep02:trace] provider = {provider.name} ({provider.chat_model_name})")

    # ---- 1. Ingest (idempotent) ----
    t0 = time.perf_counter()
    stored_count = ep02.ingest()
    ingest_ms = (time.perf_counter() - t0) * 1000.0
    print(f"[ep02:trace] indexed {stored_count} chunks in {ingest_ms:.0f}ms")

    # ---- 2. Capture chunk preview (first 10) ----
    from corpus_loader import load_and_chunk

    all_chunks = load_and_chunk(chunk_size=900, chunk_overlap=100)
    sources = sorted({c["source"] for c in all_chunks})

    # Prioritise the SKU-1042 chunk + product_catalog so Scene 3 visuals
    # match what the narrator references.
    catalog = [c for c in all_chunks if c["source"] == "product_catalog.md"]
    sku_chunk = next((c for c in all_chunks if "SKU-1042" in c["text"]), None)
    sample: list = []
    seen: set = set()
    if sku_chunk is not None:
        sample.append(sku_chunk)
        seen.add(sku_chunk["chunk_id"])
    for c in catalog:
        if c["chunk_id"] in seen:
            continue
        sample.append(c)
        seen.add(c["chunk_id"])
        if len(sample) >= 4:
            break
    for c in all_chunks:
        if len(sample) >= 10:
            break
        if c["chunk_id"] in seen:
            continue
        sample.append(c)
        seen.add(c["chunk_id"])

    chunks_payload = [
        {
            "chunk_id": c["chunk_id"],
            "text": c["text"][:280],
            "source": c["source"],
        }
        for c in sample[:10]
    ]

    # ---- 3. Embeddings preview (first 5 dims of first 5 chunks) ----
    first_5_embeddings = provider.embed([c["text"] for c in all_chunks[:5]])
    embeddings_preview = [TraceBuilder.round_vec(v) for v in first_5_embeddings]

    # ---- 4. Query embedding ----
    t1 = time.perf_counter()
    q_vec = provider.embed([EP_QUERY])[0]
    embed_query_ms = (time.perf_counter() - t1) * 1000.0
    query_vector = TraceBuilder.round_vec(q_vec)

    # ---- 5. Search ----
    t2 = time.perf_counter()
    top_10_raw = ep02.search(EP_QUERY, k=10)
    search_ms = (time.perf_counter() - t2) * 1000.0
    similarity_scores = [round(c["score"], 4) for c in top_10_raw]
    top_k_final = [
        {
            "chunk_id": i,  # ep02 search doesn't return chunk_id; index suffices for the visual
            "text": c["text"][:280],
            "score": round(c["score"], 4),
            "source": c["source"],
        }
        for i, c in enumerate(top_10_raw[:3])
    ]

    # ---- 6. Build the prompt + capture template + assembled ----
    template = ep02.PROMPT_TEMPLATE
    context = "\n\n".join(f"[{c['source']}] {c['text']}" for c in top_10_raw[:3])
    assembled = template.format(context=context, question=EP_QUERY)

    # ---- 7. Call the chat model ----
    t3 = time.perf_counter()
    answer = ep02.answer(EP_QUERY, k=3)
    llm_ms = (time.perf_counter() - t3) * 1000.0

    # ---- 8. SQL peek into Chroma ----
    sql_preview = _chroma_sql_preview(ep02.PERSIST_DIR, ep02.COLLECTION)

    # ---- 9. Code files (for the Scene 2 source panel) ----
    code_files = [
        _read_code_file("pipeline.py"),
        _read_code_file("provider.py"),
        _read_code_file("corpus_loader.py"),
    ]

    # ---- 10. Assemble trace ----
    tb = TraceBuilder(
        episode="ep02",
        title="Build the pipeline from scratch",
        query=EP_QUERY,
        expected_sources=EXPECTED_SOURCES,
    )
    tb.provider = provider.info()
    tb.corpus = {
        "total_chunks": stored_count,
        "sources": sources,
        "chunk_size": 500,
        "chunk_overlap": 50,
    }
    tb.add_state("chunks", chunks_payload)
    tb.add_state("embeddings_preview", embeddings_preview)
    tb.add_state("stored_count", stored_count)
    tb.add_state("query_vector", query_vector)
    tb.add_state("similarity_scores", similarity_scores)
    tb.add_state("top_k_final", top_k_final)
    tb.add_state("llm_answer", answer)
    tb.add_state("prompt_template", template)
    tb.add_state("assembled_prompt", assembled)
    tb.add_state("chroma_sql_preview", sql_preview)
    tb.add_state("code_files", code_files)

    p_at_3 = sum(1 for c in top_k_final if c["source"] in EXPECTED_SOURCES) / 3.0
    tb.add_metric("precision_at_3", round(p_at_3, 3))
    tb.add_metric("ingest_ms", round(ingest_ms, 1))
    tb.add_metric("embed_query_ms", round(embed_query_ms, 1))
    tb.add_metric("search_ms", round(search_ms, 1))
    tb.add_metric("llm_ms", round(llm_ms, 1))
    tb.add_metric("e2e_ms", round(embed_query_ms + search_ms + llm_ms, 1))

    out_path = tb.save(TRACE_OUT)
    print(f"\n[ep02:trace] wrote {out_path}")
    print(json.dumps(
        {
            "stored_count": stored_count,
            "p@3": round(p_at_3, 3),
            "top_score": similarity_scores[0] if similarity_scores else None,
            "answer_preview": answer[:160],
            "top_k_sources": [c["source"] for c in top_k_final],
            "sql_rows": len(sql_preview.get("rows", [])),
        },
        indent=2,
    ))
    return 0


if __name__ == "__main__":
    sys.exit(main())
