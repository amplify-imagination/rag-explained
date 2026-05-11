"""EP05 — generate_trace.py.

Runs the 3-way EP05 benchmark (naive_baseline / ep04_winner / late_chunking)
against the canonical SKU-1042 query, then captures the same query through the
audit-log-retention counter-example for Scene 8.

Captures everything the Remotion scenes need:

    states.pipelines        # ordered list with labels and per-pipeline p@3
    states.scoreboard       # ranked p@3 for the primary query
    states.pre_rerank       # split-screen support for Scene 7 — top-3 BEFORE
                            # the reranker, naive_baseline vs late_chunking
    states.query1           # primary query benchmark per pipeline
    states.query2           # secondary query (Scene 8) per pipeline
    states.code_files       # pipeline.py for any code panel
    states.providers        # composition: bge-m3 (embed) + gemini (chat)

Quota note: BGE-M3 is local; only the chat() calls hit Gemini. Total Gemini
embed cost: 0. Gemini chat cost: 1 call per pipeline per query = 6 chat calls.
This script is quota-immune compared to EP04.
"""
from __future__ import annotations

import fcntl
import json
import sys
import time
from pathlib import Path

HERE = Path(__file__).resolve().parent
EPISODE_DIR = HERE.parent
ROOT = EPISODE_DIR.parent
sys.path.insert(0, str(ROOT / "shared"))
sys.path.insert(0, str(HERE))

# ── Single-instance guard ──────────────────────────────────────────────
# Same flock pattern as EP02-EP04 — even though EP05 is quota-immune for
# embeddings, the BGE-M3 model load is heavy and parallel runs would just
# waste MPS memory.
_LOCK_PATH = HERE / ".generate_trace.lock"
_LOCK_FH = open(_LOCK_PATH, "w")
try:
    fcntl.flock(_LOCK_FH, fcntl.LOCK_EX | fcntl.LOCK_NB)
except BlockingIOError:
    print(
        f"[ep05:trace] ABORT — another generate_trace.py is already running "
        f"(lock {_LOCK_PATH}). Kill it first: `pkill -f generate_trace.py`.",
        file=sys.stderr,
    )
    sys.exit(2)

import pipeline as ep05  # noqa: E402
from llm_provider import get_provider  # noqa: E402
from trace_utils import TraceBuilder  # noqa: E402

PRIMARY_QUERY = "What is the cancellation policy for SKU-1042?"
PRIMARY_EXPECTED = {"product_catalog.md", "faq.md"}

# Counter-example for Scene 8 — late chunking shouldn't help here because the
# answer hinges on a rare hyphenated keyword that semantic search smooths over.
SECONDARY_QUERY = "What's the latency tax on the audit-log retention rebuild?"
SECONDARY_EXPECTED = {"meeting_notes.md"}

TRACE_OUT = EPISODE_DIR / "trace" / "pipeline_trace.json"

# Per-pipeline UI labels (Scene 6 / Scene 7).
PIPELINE_META = [
    {
        "id": "naive_baseline",
        "label": "Naive baseline",
        "subtitle": "fixed-size chunks · embedded alone",
        "embed_timing": "early",
    },
    {
        "id": "ep04_winner",
        "label": "EP04 winner",
        "subtitle": "markdown-header chunks · embedded alone",
        "embed_timing": "early",
    },
    {
        "id": "late_chunking",
        "label": "Late chunking",
        "subtitle": "same markdown-header chunks · embedded with document context",
        "embed_timing": "late",
    },
]

# Scene 3 — the canonical "Annual refunds are not available" chunk +
# the surrounding document text that gives it context.
ISOLATED_CHUNK = "Annual refunds are not available."
SURROUNDING_DOC_HEADING = "## SKU-1042 · Lumenflow Standard"


def _read_code_file(name: str, relative_to: Path) -> dict:
    p = relative_to / name
    text = p.read_text(encoding="utf-8")
    return {"name": name, "text": text, "line_count": text.count("\n") + 1}


def _bench_query(query: str, expected: set[str]) -> dict:
    return ep05.benchmark(query, expected)


def main() -> int:
    embed_p = get_provider("bge-m3")
    chat_p = get_provider("gemini")
    print(f"[ep05:trace] embed provider = {embed_p.name} ({embed_p.embedding_model_name})")
    print(f"[ep05:trace] chat provider  = {chat_p.name} ({chat_p.chat_model_name})")

    t0 = time.perf_counter()
    print("[ep05:trace] benchmarking primary query across 3 pipelines ...")
    q1 = _bench_query(PRIMARY_QUERY, PRIMARY_EXPECTED)
    primary_ms = (time.perf_counter() - t0) * 1000.0

    t1 = time.perf_counter()
    print("[ep05:trace] benchmarking secondary query (Scene 8 counter-example) ...")
    q2 = _bench_query(SECONDARY_QUERY, SECONDARY_EXPECTED)
    secondary_ms = (time.perf_counter() - t1) * 1000.0

    # Scoreboard — ranked p@3 for primary query.
    scoreboard = sorted(
        [
            {
                "id": m["id"],
                "label": m["label"],
                "subtitle": m["subtitle"],
                "embed_timing": m["embed_timing"],
                "p_at_3": q1[m["id"]]["p_at_3"],
                "chunks_total": q1[m["id"]]["chunks_total"],
                "is_baseline": m["id"] == "naive_baseline",
            }
            for m in PIPELINE_META
        ],
        key=lambda x: -x["p_at_3"],
    )

    # Pre-rerank top-3 — Scene 7's split-screen visual proof that late chunking
    # improves candidates BEFORE the reranker, not because of it.
    pre_rerank = {
        m["id"]: q1[m["id"]]["pre_rerank_top_3"]
        for m in PIPELINE_META
    }

    code_files = [_read_code_file("pipeline.py", HERE)]

    tb = TraceBuilder(
        episode="ep05",
        title="Late chunking — same chunks, better vectors",
        query=PRIMARY_QUERY,
        expected_sources=sorted(PRIMARY_EXPECTED),
    )
    # Composition: record both providers explicitly. provider.info() defaults to
    # one provider; we override with a dict that documents the EP05 pattern.
    tb.provider = {
        "provider": "composed",
        "embedding_provider": embed_p.info(),
        "chat_provider": chat_p.info(),
    }
    tb.corpus = {"total_chunks_per_pipeline": {m["id"]: q1[m["id"]]["chunks_total"] for m in PIPELINE_META}}
    tb.add_state("pipelines", PIPELINE_META)
    tb.add_state("isolated_chunk", ISOLATED_CHUNK)
    tb.add_state("surrounding_heading", SURROUNDING_DOC_HEADING)
    tb.add_state("query1", {"query": PRIMARY_QUERY, "expected": sorted(PRIMARY_EXPECTED), "results": q1})
    tb.add_state("query2", {"query": SECONDARY_QUERY, "expected": sorted(SECONDARY_EXPECTED), "results": q2})
    tb.add_state("scoreboard", scoreboard)
    tb.add_state("pre_rerank", pre_rerank)
    tb.add_state("code_files", code_files)
    tb.add_state("reranker_model", ep05.RERANKER_MODEL)

    tb.add_metric("primary_query_total_ms", round(primary_ms, 1))
    tb.add_metric("secondary_query_total_ms", round(secondary_ms, 1))
    tb.add_metric("p_at_3_winner", scoreboard[0]["p_at_3"])
    tb.add_metric("p_at_3_baseline", q1["naive_baseline"]["p_at_3"])
    tb.add_metric("p_at_3_late_vs_baseline", round(q1["late_chunking"]["p_at_3"] - q1["naive_baseline"]["p_at_3"], 3))

    out_path = tb.save(TRACE_OUT)
    print(f"\n[ep05:trace] wrote {out_path}")
    print(json.dumps(
        {
            "scoreboard": [{s["label"]: s["p_at_3"]} for s in scoreboard],
            "winner": scoreboard[0]["label"],
            "baseline": "naive_baseline (p@3=" + str(q1["naive_baseline"]["p_at_3"]) + ")",
            "late_chunking": "p@3=" + str(q1["late_chunking"]["p_at_3"]),
        },
        indent=2,
    ))
    return 0


if __name__ == "__main__":
    sys.exit(main())
