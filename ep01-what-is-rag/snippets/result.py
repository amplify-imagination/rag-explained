# EP1 result snippet — shown in scenes 7-8 of the video.
# The retrieved chunks become "context", the LLM gets the context PLUS
# the question, and produces a grounded answer with citations.

from langchain_core.prompts import ChatPromptTemplate
from langchain_google_genai import ChatGoogleGenerativeAI

template = ChatPromptTemplate.from_messages([
    ("system", "Answer using ONLY the context. If unknown, say so."),
    ("human", "Context:\n{context}\n\nQuestion: {question}"),
])

llm = ChatGoogleGenerativeAI(model="gemini-2.0-flash", temperature=0)

# Top-3 chunks → joined context block
context = "\n\n".join(f"[{d.metadata['source_file']}] {d.page_content}" for d, _ in results)

answer = llm.invoke(template.format_messages(context=context, question=query)).content
print(answer)
# → "The cancellation policy for SKU-1042 is described in [faq.md]. ..."
