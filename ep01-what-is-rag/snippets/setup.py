# EP1 setup snippet — shown in scenes 2-3 of the video.
# Real implementation lives in ../impl/main.py. This is the educational
# extraction: the same idea, with LangChain naming so viewers map directly
# to the docs they'll read next.

from langchain_text_splitters import RecursiveCharacterTextSplitter
from langchain_chroma import Chroma
from langchain_google_genai import GoogleGenerativeAIEmbeddings

# Split documents into chunks that are small enough to embed cleanly,
# but large enough to preserve a unit of meaning.
splitter = RecursiveCharacterTextSplitter(chunk_size=500, chunk_overlap=50)
chunks = splitter.split_documents(docs)

# Each chunk becomes a vector. Same model used for chunks and queries.
embeddings = GoogleGenerativeAIEmbeddings(model="text-embedding-004")
vectorstore = Chroma.from_documents(chunks, embeddings, collection_name="rag")
