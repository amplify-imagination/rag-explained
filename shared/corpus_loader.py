"""Corpus loader for the RAG Explained playlist.

Loads the 5 markdown documents in shared/corpus/, runs IBM Docling's
HybridChunker (tokenizer: BAAI/bge-small-en-v1.5), and writes a single
shared/corpus/corpus.json containing every chunk with metadata:

    {
      "version": "1",
      "chunks": [
        {
          "chunk_id": int,
          "text": str,
          "source_file": str,
          "heading_path": list[str],
          "char_count": int,
          "token_count": int
        },
        ...
      ],
      "summary": {
        "per_file": {filename: chunk_count},
        "total_chunks": int,
        "avg_chunk_chars": float,
        "tokenizer": str
      }
    }

Run once before any episode trace:

    python shared/corpus_loader.py
"""
from __future__ import annotations

import json
import sys
from pathlib import Path

# Tolerate running this from any cwd
HERE = Path(__file__).resolve().parent
CORPUS_DIR = HERE / "corpus"
OUT_PATH = CORPUS_DIR / "corpus.json"

CORPUS_FILES = [
    "policy_manual.md",
    "product_catalog.md",
    "meeting_notes.md",
    "tech_spec.md",
    "faq.md",
]

TOKENIZER = "BAAI/bge-small-en-v1.5"


def _load_with_docling() -> list[dict]:
    """Use IBM Docling. Preserves heading paths and tables.

    Falls back to a markdown-aware naive splitter if Docling is not installed,
    so the rest of the repo can be inspected without the full dependency chain.
    """
    try:
        from docling.document_converter import DocumentConverter
        from docling.chunking import HybridChunker
    except ImportError:
        print("[corpus_loader] docling not installed — falling back to naive splitter.", file=sys.stderr)
        print("[corpus_loader] install with:  pip install docling", file=sys.stderr)
        return _load_naive()

    converter = DocumentConverter()
    chunker = HybridChunker(tokenizer=TOKENIZER)

    chunks: list[dict] = []
    for fname in CORPUS_FILES:
        fpath = CORPUS_DIR / fname
        if not fpath.exists():
            print(f"[corpus_loader] missing: {fpath}", file=sys.stderr)
            continue
        result = converter.convert(str(fpath))
        for ck in chunker.chunk(result.document):
            body = ck.text if hasattr(ck, "text") else str(ck)
            headings = []
            if hasattr(ck, "meta") and ck.meta is not None:
                headings = list(getattr(ck.meta, "headings", []) or [])

            # Prepend heading path into the chunk text so retrieval AND the LLM
            # see the section/product identifier inline. Docling's chunker by
            # default puts headings in metadata only, which means a chunk about
            # "SKU-1042 cancellation terms" loses the SKU identifier from its
            # text — vector search still works on the body, but the LLM can no
            # longer cite the section by name. Standard production-RAG hygiene
            # is to inline the heading path.
            if headings:
                prefix = " > ".join(headings)
                text = f"[{prefix}]\n{body}"
            else:
                text = body

            chunks.append(
                {
                    "chunk_id": len(chunks),
                    "text": text,
                    "source_file": fname,
                    "heading_path": headings,
                    "char_count": len(text),
                    "token_count": len(text.split()),
                }
            )
    return chunks


def _load_naive() -> list[dict]:
    """Heading-aware fallback: split on H2 headings, preserve heading_path.

    Not as good as Docling — table structure is flattened, sub-headings are merged
    into chunk text — but it produces a valid corpus.json for development.
    """
    chunks: list[dict] = []
    for fname in CORPUS_FILES:
        fpath = CORPUS_DIR / fname
        if not fpath.exists():
            print(f"[corpus_loader] missing: {fpath}", file=sys.stderr)
            continue
        text = fpath.read_text(encoding="utf-8")
        h1, h2, h3 = "", "", ""
        buf: list[str] = []
        path: list[str] = []

        def flush():
            nonlocal buf
            body = "\n".join(buf).strip()
            if body:
                chunks.append(
                    {
                        "chunk_id": len(chunks),
                        "text": body,
                        "source_file": fname,
                        "heading_path": [p for p in path if p],
                        "char_count": len(body),
                        "token_count": len(body.split()),
                    }
                )
            buf = []

        for line in text.splitlines():
            if line.startswith("# "):
                flush()
                h1 = line[2:].strip()
                h2 = h3 = ""
                path = [h1]
            elif line.startswith("## "):
                flush()
                h2 = line[3:].strip()
                h3 = ""
                path = [h1, h2]
            elif line.startswith("### "):
                flush()
                h3 = line[4:].strip()
                path = [h1, h2, h3]
            else:
                buf.append(line)
        flush()
    return chunks


def main() -> int:
    chunks = _load_with_docling()
    if not chunks:
        print("[corpus_loader] no chunks produced — corpus loader failed.", file=sys.stderr)
        return 1

    per_file: dict[str, int] = {}
    total_chars = 0
    for ck in chunks:
        per_file[ck["source_file"]] = per_file.get(ck["source_file"], 0) + 1
        total_chars += ck["char_count"]

    payload = {
        "version": "1",
        "chunks": chunks,
        "summary": {
            "per_file": per_file,
            "total_chunks": len(chunks),
            "avg_chunk_chars": round(total_chars / len(chunks), 1),
            "tokenizer": TOKENIZER,
        },
    }
    OUT_PATH.write_text(json.dumps(payload, indent=2, ensure_ascii=False), encoding="utf-8")

    print(f"[corpus_loader] wrote {OUT_PATH}")
    print(f"[corpus_loader] {len(chunks)} chunks total, avg {payload['summary']['avg_chunk_chars']} chars")
    for fname, count in per_file.items():
        print(f"  {fname:24s} {count:4d} chunks")
    return 0


if __name__ == "__main__":
    sys.exit(main())
