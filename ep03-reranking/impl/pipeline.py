"""EP03 — Reranking. About 80 lines. Same pipeline as EP02, plus a reranker.

    python pipeline.py "What is the cancellation policy for SKU-1042?"
"""
from __future__ import annotations

import sys
from pathlib import Path

import chromadb
from sentence_transformers import CrossEncoder

# Reuse EP02's chunk loader + provider (no copy-paste, just import).
EP02 = Path(__file__).resolve().parent.parent.parent / "ep02-build-the-pipeline" / "impl"
sys.path.insert(0, str(EP02))
from corpus_loader import load_and_chunk  # noqa: E402
from provider import embed, chat  # noqa: E402

PROMPT_TEMPLATE = """\
You are a precise assistant. Use ONLY the context to answer.

Context:
{context}

Question: {question}

Answer concisely. Cite the source filename. If the context does not
contain the answer, say so.
"""

# EP03 reuses EP02's already-embedded chunks — same corpus, same model,
# same chunking. No reason to re-embed (and the free Gemini tier won't let
# us anyway). Vector search is identical to EP02; the only new code is the
# rerank step downstream.
PERSIST_DIR = str(Path(__file__).resolve().parent.parent.parent / "ep02-build-the-pipeline" / "impl" / "chroma_db")
COLLECTION = "ep02-baseline"

# 90 MB cross-encoder, MIT-licensed, runs on CPU. Loaded once at import.
RERANKER_MODEL = "cross-encoder/ms-marco-MiniLM-L-6-v2"
_RERANKER: CrossEncoder | None = None


def _reranker() -> CrossEncoder:
    global _RERANKER
    if _RERANKER is None:
        _RERANKER = CrossEncoder(RERANKER_MODEL)
    return _RERANKER


def ingest() -> int:
    """Same ingest as EP02 — embed every chunk, store in Chroma. Idempotent."""
    client = chromadb.PersistentClient(path=PERSIST_DIR)
    coll = client.get_or_create_collection(name=COLLECTION)
    if coll.count():
        return coll.count()
    chunks = load_and_chunk(chunk_size=900, chunk_overlap=100)
    vecs = embed([c["text"] for c in chunks])
    coll.add(
        ids=[str(c["chunk_id"]) for c in chunks],
        documents=[c["text"] for c in chunks],
        embeddings=vecs,
        metadatas=[{"source": c["source"]} for c in chunks],
    )
    return coll.count()


def vector_search(query: str, k: int = 20) -> list[dict]:
    """Bi-encoder retrieval — fast, broad recall. Same code as EP02.search()."""
    client = chromadb.PersistentClient(path=PERSIST_DIR)
    coll = client.get_collection(name=COLLECTION)
    q_vec = embed([query])[0]
    res = coll.query(query_embeddings=[q_vec], n_results=k)
    out = []
    for text, meta, dist in zip(res["documents"][0], res["metadatas"][0], res["distances"][0]):
        out.append({
            "text": text,
            "source": meta["source"],
            "score": 1.0 / (1.0 + float(dist)),  # cosine-like similarity
        })
    return out


def rerank(query: str, candidates: list[dict], top_n: int = 3) -> list[dict]:
    """Cross-encoder rerank — slower, precise. Returns top_n by relevance."""
    pairs = [(query, c["text"]) for c in candidates]
    relevance_scores = _reranker().predict(pairs).tolist()
    for c, r in zip(candidates, relevance_scores):
        c["rerank_score"] = float(r)
    candidates.sort(key=lambda c: c["rerank_score"], reverse=True)
    return candidates[:top_n]


def answer(query: str, top_k_retrieve: int = 20, top_n_rerank: int = 3) -> str:
    """Retrieve broadly, rerank precisely, answer from the top-N."""
    retrieved = vector_search(query, k=top_k_retrieve)
    top = rerank(query, retrieved, top_n=top_n_rerank)
    context = "\n\n".join(f"[{c['source']}] {c['text']}" for c in top)
    prompt = PROMPT_TEMPLATE.format(context=context, question=query)
    return chat(prompt)


if __name__ == "__main__":
    q = " ".join(sys.argv[1:]) or "What is the cancellation policy for SKU-1042?"
    n = ingest()
    print(f"indexed {n} chunks")
    print(f"\nQ: {q}\n\nA: {answer(q)}")
