# The shared demo corpus

All 9 episodes of the **RAG Explained** playlist use the same 5 documents. This is deliberate — by holding the corpus constant we get fair before/after comparisons across strategies, and viewers build a mental model of the data instead of being re-introduced to a new corpus every episode.

Each document is also engineered: it is shaped to make at least one naive RAG strategy fail visibly, so the corresponding episode has *real* numbers to animate, not synthetic ones.

| File | Bytes | Designed to demonstrate | Naive failure mode | Used in |
|---|---|---|---|---|
| `policy_manual.md` | ~2000 words | parent-child chunking, hierarchical retrieval | fixed-size chunks split mid-clause inside numbered procedures, losing section heading context | EP4 (chunking benchmarks), EP5 (late chunking) |
| `product_catalog.md` | 30 SKUs in tables | hybrid search (BM25 + dense vectors) | pure vector search misses exact `SKU-XXXX` matches, returning semantically similar but wrong products | EP6 (hybrid search) |
| `meeting_notes.md` | 10 weekly meetings | late chunking, contextual retrieval | naive chunking by meeting loses cross-meeting references that resolve only with prior context | EP5 (late chunking) |
| `tech_spec.md` | 15 components, typed relationships | graph RAG, multi-hop traversal | vector search cannot follow `A depends on B reads from C` chains across documents | EP7 (Graph RAG + Neo4j) |
| `faq.md` | 50 Q&A pairs, 8 surface-similar | reranking, cross-encoder scoring | bi-encoder cosine similarity ranks the wrong FAQ first when surface text is similar but the answer is materially different | EP3 (reranking), EP8 (RAG evaluation) |

## Why one corpus, not nine

A separate corpus per episode would mean every video starts with "here is today's data" — that's a re-introduction tax viewers pay nine times. With a shared corpus, by EP3 the audience already remembers what `SKU-1042` is and which company `Jensen Huang` runs. That recognition is what turns nine standalone videos into a *series* the audience commits to.

It also means cross-episode callbacks land. EP3's reranking demo can literally say *"remember when chunk 3 in EP1's pipeline was actually the most relevant? Here's why."* EP5's benchmark runs against the EP1 baseline. EP7's knowledge graph is built from `tech_spec.md` that the audience has seen since EP1.

## Loading

`corpus_loader.py` uses [IBM Docling](https://github.com/DS4SD/docling) to convert each document, preserving heading hierarchy, tables, and structure. It then runs Docling's `HybridChunker` (tokenizer: `BAAI/bge-small-en-v1.5`) and writes a single `corpus.json` containing every chunk with metadata: text, source file, heading path (list of ancestor headings), chunk index, character count.

```bash
python shared/corpus_loader.py
# → shared/corpus/corpus.json
```

Episodes load `corpus.json` rather than re-parsing the markdown. That keeps the chunk boundaries identical across all 9 traces.

## Engineering principles

The corpus follows four principles:

1. **Each document targets a specific failure mode.** The point of the policy manual isn't to be a real policy manual — it's to fail under fixed-size chunking. That failure has to be reproducible: given the same chunker and the same query, the same chunk has to land in the wrong rank every time.
2. **Realism is a budget, not a goal.** Documents only need to be plausible enough that a viewer doesn't reject them. Beyond that, every paragraph earns its place by being part of an engineered failure or a callback.
3. **Cross-document references.** Some queries can only be answered by combining `tech_spec.md` and `meeting_notes.md` — that's the soil for graph RAG and multi-hop reasoning episodes.
4. **A locked query set.** A separate `queries.json` (next to this file) defines the canonical question set used to benchmark every strategy. Same questions, same corpus, different strategies — that is the whole experimental control of the series.
