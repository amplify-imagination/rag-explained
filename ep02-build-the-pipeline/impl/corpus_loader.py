"""Read markdown files and split them into chunks. Used by pipeline.py."""
from __future__ import annotations

from pathlib import Path
from langchain_text_splitters import RecursiveCharacterTextSplitter

CORPUS_DIR = Path(__file__).resolve().parent.parent.parent / "shared" / "corpus"
# Only the 5 engineered demo documents — skip CORPUS.md (the README) and JSON.
CORPUS_FILES = [
    "product_catalog.md",
    "faq.md",
    "policy_manual.md",
    "meeting_notes.md",
    "tech_spec.md",
]


def load_and_chunk(chunk_size: int = 500, chunk_overlap: int = 50) -> list[dict]:
    """Load every demo doc in the corpus and split it into chunks.

    Each chunk is a dict with chunk_id + text + source filename.
    """
    splitter = RecursiveCharacterTextSplitter(
        chunk_size=chunk_size,
        chunk_overlap=chunk_overlap,
    )
    chunks: list[dict] = []
    chunk_id = 0
    for filename in CORPUS_FILES:
        md_file = CORPUS_DIR / filename
        text = md_file.read_text(encoding="utf-8")
        for piece in splitter.split_text(text):
            chunks.append({
                "chunk_id": chunk_id,
                "text": piece,
                "source": md_file.name,
            })
            chunk_id += 1
    return chunks
