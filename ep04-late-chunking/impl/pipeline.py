"""EP05 — Late chunking. Three pipelines, one query, one variable: WHEN we embed.

The point of EP05 is *not* to compare chunkers (that was EP04). The variable is
the embedding timing:
    - naive_baseline:  fixed-size chunks, embedded individually        (early)
    - ep04_winner:     markdown-header chunks, embedded individually   (early)
    - late_chunking:   markdown-header chunks, embedded as a document  (late)

Per Stig's v0.2 script note: all three pipelines use BGE-M3 for embeddings, so
the only difference between ep04_winner and late_chunking is when the embedding
happens. Naive baseline shares the embedder too — it's there as a "where we
started" reference, not as a stack-comparison.

Provider composition (intentional, pedagogical):
    embedding_provider = get_provider("bge-m3")     # local, free, 8K context
    chat_provider      = get_provider("gemini")     # final answer step only

    python pipeline.py "What is the cancellation policy for SKU-1042?"
"""
from __future__ import annotations

import sys
from pathlib import Path
from typing import Callable

import chromadb
from sentence_transformers import CrossEncoder

# Reuse EP02's corpus_loader and EP04's chunkers — corpus is shared by design.
EP02 = Path(__file__).resolve().parent.parent.parent / "ep02-build-the-pipeline" / "impl"
EP04 = Path(__file__).resolve().parent.parent.parent / "ep04-chunking-benchmarks" / "impl"
SHARED = Path(__file__).resolve().parent.parent.parent / "shared"
sys.path.insert(0, str(EP02))
sys.path.insert(0, str(EP04))
sys.path.insert(0, str(SHARED))

from corpus_loader import CORPUS_DIR  # noqa: E402
from llm_provider import get_provider  # noqa: E402

# Import EP04's chunkers verbatim — same algorithms, same outputs.
import pipeline as ep04  # noqa: E402

PROMPT_TEMPLATE = """\
You are a precise assistant. Use ONLY the context to answer.

Context:
{context}

Question: {question}

Answer concisely. Cite the source filename. If the context does not
contain the answer, say so.
"""

# 90 MB cross-encoder. Loaded once, shared across pipelines.
RERANKER_MODEL = "cross-encoder/ms-marco-MiniLM-L-6-v2"
_RERANKER: CrossEncoder | None = None

# Per-pipeline collection — keep them isolated so we don't mix early and late vectors.
PERSIST_DIR = str(Path(__file__).resolve().parent / "chroma_db")


def _reranker() -> CrossEncoder:
    global _RERANKER
    if _RERANKER is None:
        _RERANKER = CrossEncoder(RERANKER_MODEL)
    return _RERANKER


# Lazy provider singletons so we only pay the BGE-M3 load cost once per run.
_EMBED_PROVIDER = None
_CHAT_PROVIDER = None


def embed_provider():
    global _EMBED_PROVIDER
    if _EMBED_PROVIDER is None:
        _EMBED_PROVIDER = get_provider("bge-m3")
    return _EMBED_PROVIDER


def chat_provider():
    global _CHAT_PROVIDER
    if _CHAT_PROVIDER is None:
        _CHAT_PROVIDER = get_provider("gemini")
    return _CHAT_PROVIDER


# ── Pipelines ──────────────────────────────────────────────────────
# Each ingest function: chunks → embeddings → ChromaDB collection.
# The only thing that varies between them is HOW the embeddings are computed.

PIPELINES = ["naive_baseline", "ep04_winner", "late_chunking"]


def _read_docs() -> list[dict]:
    """Yield {source, text} per document. Same as EP04's _read_docs."""
    out = []
    for p in sorted(CORPUS_DIR.glob("*.md")):
        out.append({"source": p.name, "text": p.read_text(encoding="utf-8")})
    return out


def _chunks_for(pipeline_name: str) -> list[dict]:
    """Return the chunks for a given pipeline. Each item: {text, source, char_start, char_end}.

    char_start / char_end are *within the source document* — late chunking needs
    them so we can pool the right token embeddings back into the chunk vector.
    """
    if pipeline_name == "naive_baseline":
        # Re-derive fixed_500 chunks but track char ranges in the source.
        out = []
        for d in _read_docs():
            text = d["text"]
            i = 0
            while i < len(text):
                j = min(i + 500, len(text))
                piece = text[i:j].strip()
                if piece:
                    out.append({"text": piece, "source": d["source"], "char_start": i, "char_end": j})
                i = j
        return out
    if pipeline_name in ("ep04_winner", "late_chunking"):
        # Markdown-header chunker — split at headings. Track char ranges per source.
        import re
        head_re = re.compile(r"^(#+\s.+)$", re.MULTILINE)
        out = []
        for d in _read_docs():
            text = d["text"]
            starts = [m.start() for m in head_re.finditer(text)]
            if not starts:
                out.append({"text": text, "source": d["source"], "char_start": 0, "char_end": len(text)})
                continue
            starts.append(len(text))
            for i in range(len(starts) - 1):
                a, b = starts[i], starts[i + 1]
                piece = text[a:b].strip()
                if piece:
                    out.append({"text": piece, "source": d["source"], "char_start": a, "char_end": b})
        return out
    raise ValueError(f"Unknown pipeline: {pipeline_name}")


def ingest(pipeline_name: str) -> int:
    """Embed and persist chunks for one pipeline. Idempotent per pipeline."""
    chunks = _chunks_for(pipeline_name)
    if not chunks:
        return 0
    coll_name = f"ep05-{pipeline_name}"
    client = chromadb.PersistentClient(path=PERSIST_DIR)
    coll = client.get_or_create_collection(name=coll_name)
    if coll.count():
        return coll.count()

    p = embed_provider()
    if pipeline_name in ("naive_baseline", "ep04_winner"):
        # Early chunking: embed each chunk in isolation (the EP02-EP04 pattern).
        vecs = p.embed([c["text"] for c in chunks])
    elif pipeline_name == "late_chunking":
        # Late chunking: per source document, one forward pass through the
        # encoder + pool token representations into chunk vectors using char ranges.
        # Group chunks by source so we batch by document.
        by_source: dict[str, list[dict]] = {}
        for c in chunks:
            by_source.setdefault(c["source"], []).append(c)
        # Materialize each document text once.
        docs = {d["source"]: d["text"] for d in _read_docs()}
        vecs: list[list[float]] = []
        out_chunks_in_order: list[dict] = []
        for src in sorted(by_source.keys()):
            doc_text = docs[src]
            chunks_in_doc = by_source[src]
            boundaries = [(c["char_start"], c["char_end"]) for c in chunks_in_doc]
            doc_vecs = p.embed_late(doc_text, boundaries)
            vecs.extend(doc_vecs)
            out_chunks_in_order.extend(chunks_in_doc)
        # Re-order chunks list to match vec order
        chunks = out_chunks_in_order
    else:
        raise ValueError(f"Unknown pipeline: {pipeline_name}")

    coll.add(
        ids=[f"{pipeline_name}-{i}" for i in range(len(chunks))],
        documents=[c["text"] for c in chunks],
        embeddings=vecs,
        metadatas=[
            {"source": c["source"], "pipeline": pipeline_name, "char_start": c["char_start"], "char_end": c["char_end"]}
            for c in chunks
        ],
    )
    return coll.count()


def vector_search(query: str, pipeline_name: str, k: int = 20) -> list[dict]:
    coll_name = f"ep05-{pipeline_name}"
    client = chromadb.PersistentClient(path=PERSIST_DIR)
    coll = client.get_collection(name=coll_name)
    p = embed_provider()
    q_vec = p.embed_query(query)
    res = coll.query(query_embeddings=[q_vec], n_results=k)
    out = []
    for text, meta, dist in zip(res["documents"][0], res["metadatas"][0], res["distances"][0]):
        out.append({
            "text": text,
            "source": meta["source"],
            "score": 1.0 / (1.0 + float(dist)),
        })
    return out


def rerank(query: str, candidates: list[dict], top_n: int = 3) -> list[dict]:
    pairs = [(query, c["text"]) for c in candidates]
    relevance_scores = _reranker().predict(pairs).tolist()
    for c, r in zip(candidates, relevance_scores):
        c["rerank_score"] = float(r)
    candidates.sort(key=lambda c: c["rerank_score"], reverse=True)
    return candidates[:top_n]


def answer(query: str, pipeline_name: str, top_k_retrieve: int = 20, top_n_rerank: int = 3) -> dict:
    """Run the full pipeline. Embedding via BGE-M3, chat via Gemini."""
    retrieved = vector_search(query, pipeline_name, k=top_k_retrieve)
    top = rerank(query, retrieved, top_n=top_n_rerank)
    context = "\n\n".join(f"[{c['source']}] {c['text']}" for c in top)
    prompt = PROMPT_TEMPLATE.format(context=context, question=query)
    chat_result = chat_provider().chat([{"role": "user", "content": prompt}], temperature=0.0, max_tokens=400)
    return {
        "pipeline": pipeline_name,
        "top_n": top,
        "answer": chat_result.text,
    }


def benchmark(query: str, expected_sources: set[str], top_k_retrieve: int = 20) -> dict:
    """Run all 3 pipelines against the same query. Returns precision-at-3 per pipeline."""
    results = {}
    for pipeline_name in PIPELINES:
        n = ingest(pipeline_name)
        retrieved = vector_search(query, pipeline_name, k=top_k_retrieve)
        # Capture pre-reranker top-3 for Scene 7's split-screen visual.
        pre_rerank_top3 = retrieved[:3]
        reranked = rerank(query, [dict(c) for c in retrieved], top_n=top_k_retrieve)
        top3 = reranked[:3]
        p_at_3 = sum(1 for c in top3 if c["source"] in expected_sources) / 3.0
        results[pipeline_name] = {
            "chunks_total": n,
            "p_at_3": round(p_at_3, 3),
            "pre_rerank_top_3": [
                {"rank": i + 1, "source": c["source"], "text": c["text"][:240], "score": round(c["score"], 4)}
                for i, c in enumerate(pre_rerank_top3)
            ],
            "top_3": [
                {"rank": i + 1, "source": c["source"], "text": c["text"][:240], "rerank_score": round(c["rerank_score"], 4)}
                for i, c in enumerate(top3)
            ],
        }
    return results


if __name__ == "__main__":
    q = " ".join(sys.argv[1:]) or "What is the cancellation policy for SKU-1042?"
    print(f"\nQ: {q}\n")
    expected = {"product_catalog.md", "faq.md"}
    bench = benchmark(q, expected)
    for name, r in bench.items():
        print(f"  {name:18s}  p@3={r['p_at_3']}  chunks={r['chunks_total']}  top1={r['top_3'][0]['source']}")
