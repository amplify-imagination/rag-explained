# EP1 core snippet — shown in scenes 5-6 of the video.
# The query side: same model, same embedding space, distance becomes
# similarity. Top-k retrieval is just a sorted distance lookup.

# 1. Embed the question with the SAME model that embedded the chunks.
query_vec = embeddings.embed_query("What is the cancellation policy for SKU-1042?")

# 2. Similarity search — return the k chunks closest to the query in vector space.
results = vectorstore.similarity_search_with_score(
    query="What is the cancellation policy for SKU-1042?",
    k=3,
)

# 3. Each result is (Document, distance). Closer distance = higher similarity.
for doc, distance in results:
    similarity = 1 / (1 + distance)
    print(f"[{doc.metadata['source_file']}] {similarity:.3f}  {doc.page_content[:80]}")
