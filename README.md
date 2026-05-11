# RAG Explained — code companion

Public code for the **RAG Explained** YouTube playlist by [Amplify Imagination](https://www.youtube.com/@AmplifyImagination).

> **RAG from visual intuition to production engineering — with real traces, benchmarks, and shared corpora across all 10 episodes.**

Every score, vector, and answer shown in every video came from running the code in this repo against the demo corpus. The pipeline traces are committed (`*/trace/pipeline_trace.json`) so you can verify the numbers, or regenerate them yourself.

A running **scoreboard** in [`shared/scoreboard.json`](shared/scoreboard.json) tracks how each episode's technique moves the same metrics on the same corpus. The series isn't 10 standalone videos — it's a progressive engineering journey from baseline RAG to production. Two of the episodes (EP07 BM25 reversal and the EP04 late-chunking lesson) use a second, deliberately-different corpus to demonstrate when the same technique behaves differently — see [`shared/corpus_technical/`](shared/corpus_technical/).

## Who this is for

Backend and platform engineers building production RAG systems. The first two episodes are accessible to anyone curious about RAG; from EP3 onwards the material is for engineers who already know what an embedding is and want to ship something that works at scale.

## The 10 episodes

| # | Title | Difficulty | Status | Folder |
|---|---|---|---|---|
| 1 | What is RAG? | Beginner | Shipped | [ep01-what-is-rag/](ep01-what-is-rag/) |
| 2 | Build the pipeline from scratch | Beginner | Shipped | [ep02-build-the-pipeline/](ep02-build-the-pipeline/) |
| 3 | Reranking (closes the 0.80 loop) | Intermediate | Shipped | [ep03-reranking/](ep03-reranking/) |
| 4 | Late chunking — when it helps, when it hurts | Intermediate | Shipped | [ep04-late-chunking/](ep04-late-chunking/) |
| 5 | Hybrid search (BM25 + dense + RRF) | Intermediate | In progress | [ep05-hybrid/](ep05-hybrid/) |
| 6 | Query rewriting (HyDE / multi-query / step-back) | Advanced | In progress | [ep06-query-rewriting/](ep06-query-rewriting/) |
| 7 | BM25 reversal — when the simplest retriever wins | Intermediate | In progress | [ep07-bm25-reversal/](ep07-bm25-reversal/) |
| 8 | RAG tools compared (LangChain / LlamaIndex / Haystack / custom) | Advanced | Pending | _coming soon_ |
| 9 | Evaluation (RAGAS, golden sets) | Advanced | Pending | _coming soon_ |
| 10 | Production (caching, monitoring, cost) | Advanced | Pending | _coming soon_ |

## Quickstart

```bash
git clone https://github.com/amplify-imagination/rag-explained.git
cd rag-explained
python3 -m venv .venv && source .venv/bin/activate
pip install -r requirements.txt
cp .env.example .env  # then add your free Gemini API key

# Build the shared corpus (once)
python shared/corpus_loader.py

# Run any episode
cd ep01-what-is-rag
python impl/generate_trace.py
```

## Free stack by default

- **LLM:** Gemini Flash via the free [AI Studio API](https://aistudio.google.com)
- **Embeddings:** Google `text-embedding-004` for EP01-EP03 · `BAAI/bge-m3` (local) for EP04+ (long-context required for late chunking)
- **Vector store:** ChromaDB (local)
- **Reranker:** `BAAI/bge-reranker-v2-m3` (local)

Total cost to clone, run, and reproduce every trace in this repo: $0. See [shared/llm_provider/](shared/llm_provider/) to swap in OpenAI or local Ollama.

## The shared demo corpora

EP01-EP06 + EP08-EP10 use the same 5-document **prose corpus** in [shared/corpus/](shared/corpus/) — a Lumenflow company knowledge base (FAQ, manual, meeting notes, product catalog, tech spec). Each document is engineered to make at least one naive RAG strategy fail visibly. See [shared/corpus/CORPUS.md](shared/corpus/CORPUS.md) for the design rationale.

EP07 (BM25 reversal) introduces a deliberately-different second corpus in [shared/corpus_technical/](shared/corpus_technical/) — API reference, support chat logs, incident postmortems, and code samples. The contrast between the two corpora is the episode's whole point: the same retriever can win on one and lose on the other.

## License

MIT — see [LICENSE](LICENSE). Use the code freely; attribution appreciated.
