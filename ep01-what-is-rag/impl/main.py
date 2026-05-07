"""EP1 — What is RAG? Reference implementation.

The educational snippets shown on screen (`../snippets/*.py`) use LangChain
for clarity. This implementation uses chromadb directly + the project's
LLMProvider abstraction to keep the dependency graph small. Both paths
produce identical traces against the same corpus.

Run via the trace generator:

    python ep01-what-is-rag/impl/generate_trace.py

Or call `RagPipeline` from anywhere. It loads the shared corpus exactly
once into a local Chroma collection (per-episode subdirectory) and answers
queries.
"""
from __future__ import annotations

import json
import os
import sys
from dataclasses import dataclass
from pathlib import Path

# Resolve project root so this module is importable from anywhere
ROOT = Path(__file__).resolve().parent.parent.parent
sys.path.insert(0, str(ROOT / "shared"))

from llm_provider import LLMProvider, get_provider  # noqa: E402

CORPUS_PATH = ROOT / "shared" / "corpus" / "corpus.json"


@dataclass
class RetrievedChunk:
    text: str
    source: str
    score: float
    chunk_id: int


class RagPipeline:
    """Minimal but real RAG pipeline.

    1. Load chunks from shared/corpus/corpus.json.
    2. Embed each chunk via LLMProvider.embed() (batched).
    3. Store in a local Chroma collection.
    4. On query: embed the query, top-k similarity search, compose prompt,
       answer with the same provider's chat.
    """

    PROMPT_TEMPLATE = (
        "You are a precise assistant. Use ONLY the context to answer.\n\n"
        "Context:\n{context}\n\n"
        "Question: {question}\n\n"
        "Answer concisely. If the context does not contain the answer, say so."
    )

    def __init__(
        self,
        provider: LLMProvider | None = None,
        collection_name: str = "ep01-baseline",
        persist_dir: str | None = None,
    ) -> None:
        import chromadb

        self.provider = provider or get_provider()
        persist = persist_dir or str(Path(__file__).parent.parent / "chroma_db")
        self._client = chromadb.PersistentClient(path=persist)
        self._collection = self._client.get_or_create_collection(name=collection_name)
        self._loaded = False

    # ---------- ingestion ----------

    def _load_corpus_chunks(self) -> list[dict]:
        if not CORPUS_PATH.exists():
            raise FileNotFoundError(
                f"corpus.json not found at {CORPUS_PATH}. "
                "Run `python shared/corpus_loader.py` first."
            )
        return json.loads(CORPUS_PATH.read_text(encoding="utf-8"))["chunks"]

    def ingest(self, force: bool = False) -> int:
        """Embed and store every chunk in Chroma. Idempotent unless force=True."""
        existing = self._collection.count()
        if existing and not force:
            self._loaded = True
            return existing

        if force and existing:
            # Recreate collection cleanly
            name = self._collection.name
            self._client.delete_collection(name)
            self._collection = self._client.get_or_create_collection(name=name)

        chunks = self._load_corpus_chunks()
        # Batch embedding for throughput
        BATCH = 32
        for i in range(0, len(chunks), BATCH):
            batch = chunks[i : i + BATCH]
            vecs = self.provider.embed([c["text"] for c in batch])
            self._collection.add(
                ids=[str(c["chunk_id"]) for c in batch],
                documents=[c["text"] for c in batch],
                embeddings=vecs,
                metadatas=[
                    {
                        "source_file": c["source_file"],
                        "heading_path": " > ".join(c["heading_path"]),
                        "chunk_id": c["chunk_id"],
                    }
                    for c in batch
                ],
            )
        self._loaded = True
        return self._collection.count()

    # ---------- query ----------

    def embed_query(self, query: str) -> list[float]:
        return self.provider.embed([query])[0]

    def search(self, query: str, k: int = 10) -> list[RetrievedChunk]:
        if not self._loaded:
            self.ingest()
        q_vec = self.embed_query(query)
        res = self._collection.query(query_embeddings=[q_vec], n_results=k)
        out: list[RetrievedChunk] = []
        for text, meta, dist in zip(res["documents"][0], res["metadatas"][0], res["distances"][0]):
            # Chroma returns squared L2 by default; convert to a [0,1] similarity
            # using 1 / (1 + dist) which is monotonic in distance.
            similarity = 1.0 / (1.0 + float(dist))
            out.append(
                RetrievedChunk(
                    text=text,
                    source=meta["source_file"],
                    score=similarity,
                    chunk_id=int(meta["chunk_id"]),
                )
            )
        return out

    def answer(self, query: str, k: int = 3) -> tuple[str, list[RetrievedChunk]]:
        top = self.search(query, k=k)
        context = "\n\n".join(
            f"[{c.source}#{c.chunk_id}] {c.text}" for c in top
        )
        prompt = self.PROMPT_TEMPLATE.format(context=context, question=query)
        result = self.provider.chat(
            [{"role": "user", "content": prompt}],
            temperature=0.0,
            max_tokens=400,
        )
        return result.text, top


def main() -> int:
    p = RagPipeline()
    n = p.ingest()
    print(f"[ep01] indexed {n} chunks via provider={p.provider.name}")
    q = "What is the cancellation policy for SKU-1042?"
    answer, sources = p.answer(q, k=3)
    print(f"\nQ: {q}\n")
    print(f"A: {answer}\n")
    print("Sources:")
    for s in sources:
        print(f"  {s.source}#{s.chunk_id}  score={s.score:.3f}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
