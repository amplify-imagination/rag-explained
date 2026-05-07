"""The whole RAG pipeline. Three functions. About 60 lines.

    python pipeline.py "What are the cancellation terms for SKU-1042?"
"""
from __future__ import annotations

import sys
from pathlib import Path

import chromadb

from corpus_loader import load_and_chunk
from provider import embed, chat

PROMPT_TEMPLATE = """\
You are a precise assistant. Use ONLY the context to answer.

Context:
{context}

Question: {question}

Answer concisely. Cite the source filename. If the context does not
contain the answer, say so.
"""

PERSIST_DIR = str(Path(__file__).parent / "chroma_db")
COLLECTION = "ep02-baseline"


def ingest() -> int:
    """Embed every chunk and store it in Chroma. Idempotent."""
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


def search(query: str, k: int = 5) -> list[dict]:
    """Embed the query and return the top-k chunks ranked by similarity."""
    client = chromadb.PersistentClient(path=PERSIST_DIR)
    coll = client.get_collection(name=COLLECTION)
    q_vec = embed([query])[0]
    res = coll.query(query_embeddings=[q_vec], n_results=k)
    out = []
    for text, meta, dist in zip(res["documents"][0], res["metadatas"][0], res["distances"][0]):
        out.append({
            "text": text,
            "source": meta["source"],
            "score": 1.0 / (1.0 + float(dist)),
        })
    return out


def answer(query: str, k: int = 3) -> str:
    """Search top-k chunks, build the prompt, and call the chat model."""
    top = search(query, k=k)
    context = "\n\n".join(f"[{c['source']}] {c['text']}" for c in top)
    prompt = PROMPT_TEMPLATE.format(context=context, question=query)
    return chat(prompt)


if __name__ == "__main__":
    q = " ".join(sys.argv[1:]) or "What are the cancellation terms for SKU-1042?"
    n = ingest()
    print(f"indexed {n} chunks")
    print(f"\nQ: {q}\n\nA: {answer(q)}")
