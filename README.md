# RAG Explained — code companion

Public code for the **RAG Explained** YouTube playlist by [Amplify Imagination](https://www.youtube.com/@AmplifyImagination).

> **RAG from visual intuition to production engineering — with real traces, benchmarks, and a single shared corpus across all 9 episodes.**

Every score, vector, and answer shown in every video came from running the code in this repo against the same demo corpus. The pipeline traces are committed (`*/trace/pipeline_trace.json`) so you can verify the numbers, or regenerate them yourself.

A running **scoreboard** in [`shared/scoreboard.json`](shared/scoreboard.json) tracks how each episode's technique moves the same metrics on the same corpus. The series isn't 9 standalone videos — it's a progressive engineering journey from baseline RAG to production.

## Who this is for

Backend and platform engineers building production RAG systems. The first two episodes are accessible to anyone curious about RAG; from EP3 onwards the material is for engineers who already know what an embedding is and want to ship something that works at scale.

## The 9 episodes

| # | Title | Difficulty | Status | Folder |
|---|---|---|---|---|
| 1 | What is RAG? | Beginner | Shipped | [ep01-what-is-rag/](ep01-what-is-rag/) |
| 2 | Build the pipeline from scratch | Beginner | Shipped | [ep02-build-the-pipeline/](ep02-build-the-pipeline/) |
| 3 | Reranking | Intermediate | In progress | _coming soon_ |
| 4 | Chunking benchmarks | Intermediate | In progress | _coming soon_ |
| 5 | Late chunking | Intermediate | In progress | _coming soon_ |
| 6 | Hybrid search | Intermediate | In progress | _coming soon_ |
| 7 | Graph RAG with Neo4j | Advanced | In progress | _coming soon_ |
| 8 | RAG evaluation | Advanced | In progress | _coming soon_ |
| 9 | Productionizing RAG | Advanced | In progress | _coming soon_ |

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
- **Embeddings:** Google `text-embedding-004` (or local `bge-small-en-v1.5`)
- **Vector store:** ChromaDB (local)
- **Reranker:** `BAAI/bge-reranker-v2-m3` (local)

Total cost to clone, run, and reproduce every trace in this repo: $0. See [shared/llm_provider/](shared/llm_provider/) to swap in OpenAI or local Ollama.

## The shared demo corpus

All 9 episodes use the same 5 documents in [shared/corpus/](shared/corpus/). Each document is engineered to make at least one naive RAG strategy fail visibly. See [shared/corpus/CORPUS.md](shared/corpus/CORPUS.md) for the design rationale.

## License

MIT — see [LICENSE](LICENSE). Use the code freely; attribution appreciated.
