from langchain_core.documents import Document
from langchain_mongodb import MongoDBAtlasVectorSearch
from pymongo import MongoClient
from uuid import uuid4
from langchain_google_genai import GoogleGenerativeAIEmbeddings
from dotenv import load_dotenv, find_dotenv
import os
import random

# force reload the .env file
load_dotenv(find_dotenv(), override=True)
embeddings = GoogleGenerativeAIEmbeddings(
    model="models/text-embedding-004",
    google_api_key=os.getenv("GOOGLE_API_KEY")
)
# create embeddings using Gemini embeddings

# step 4: Setting Up the vector store for RAG system, we gonna use MongoDBAtlas

#$ initialize the MongoDB python client
MONGODB_ATLAS_CLUSTER_URI = os.getenv("MONGODB_ATLAS_CLUSTER_URI")
client = MongoClient(
    MONGODB_ATLAS_CLUSTER_URI
)
DB_NAME = "RAG-Chatbot-Cluster"
COLLECTION_NAME = "RAG-Chatbot-Collection"
ATLAS_VECTOR_SEARCH_INDEX_NAME = "RAG-Chatbot-Index"

MONGODB_COLLECTION = client[DB_NAME][COLLECTION_NAME]

vector_store = MongoDBAtlasVectorSearch(
    collection=MONGODB_COLLECTION,
    embedding=embeddings,
    index_name=ATLAS_VECTOR_SEARCH_INDEX_NAME,
    relevance_score_fn="cosine"
)
# create a vector search index on the collection
vector_store.create_vector_search_index(dimensions=768)
print(f"[INFO] Created a vector search index on the collection '{COLLECTION_NAME}' in the database '{DB_NAME}'!")

# step 5: performing similarity search

# manage the vector store
document_1 = Document(
    page_content="I had chocalate chip pancakes and scrambled eggs for breakfast this morning.",
    metadata={"source": "tweet"},
)

document_2 = Document(
    page_content="The weather forecast for tomorrow is cloudy and overcast, with a high of 62 degrees.",
    metadata={"source": "news"},
)

document_3 = Document(
    page_content="Building an exciting new project with LangChain - come check it out!",
    metadata={"source": "tweet"},
)

document_4 = Document(
    page_content="Robbers broke into the city bank and stole $1 million in cash.",
    metadata={"source": "news"},
)

document_5 = Document(
    page_content="Wow! That was an amazing movie. I can't wait to see it again.",
    metadata={"source": "tweet"},
)

document_6 = Document(
    page_content="Is the new iPhone worth the price? Read this review to find out.",
    metadata={"source": "website"},
)

document_7 = Document(
    page_content="The top 10 soccer players in the world right now.",
    metadata={"source": "website"},
)

document_8 = Document(
    page_content="LangGraph is the best framework for building stateful, agentic applications!",
    metadata={"source": "tweet"},
)

document_9 = Document(
    page_content="The stock market is down 500 points today due to fears of a recession.",
    metadata={"source": "news"},
)

document_10 = Document(
    page_content="I have a bad feeling I am going to get deleted :(",
    metadata={"source": "tweet"},
)

documents = [
    document_1,
    document_2,
    document_3,
    document_4,
    document_5,
    document_6,
    document_7,
    document_8,
    document_9,
    document_10,
]
uuids = [
    str(uuid4()) for _ in range(len(documents))
]
vector_store.add_documents(
    documents=documents,
    ids=uuids
)
print(f"[INFO] Added {len(documents)} documents to the vector store!")

# delete itemms
# vector_store.delete(ids=uuids)
# print(f"[INFO] Deleted {len(documents)} documents from the vecotr store!")

# query vector store
# similarity search
query = "langchain provides a framework for building LLM applications"  
print(f"[INFO] Searching for the query: {query}")
results = vector_store.similarity_search(
    query=query  
)
for result in results:
    print(f"* {result.page_content} (source: {result.metadata['source']})")

# similarity search with score
query = "Will it be hot tomorrow?"
results = vector_store.similarity_search_with_score(
    query=query,
    k=3
)
print(f"[INFO] Types of results: {type(results)}")
for result, score in results:
    print(f"* {result.page_content} (source: {result.metadata['source']}) with score: {score}")

# pre-filtering with similarity search
# query = "foo"
# vector_store.create_vector_search_index(
#     dimensions=768,
#     filters=[{"type": "filter", "path": "source"}],
#     update=True
# )
# results = vector_store.similarity_search(
#     query=query,
#     k=1, 
#     pre_filter={"source": {"$eq": "https://example.com"}} 
# )
# for doc in results:
#     print(f"* {doc.page_content} (source: [{doc.metadata}])")


# query by turning into retriever
retriever = vector_store.as_retriever(
    search_type="similarity_score_threshold",
    search_kwargs={"k": 1, "score_threshold": 0.2},
)
result = retriever.invoke("Stealing from the bank is a crime")
print(f"[INFO] Querying the retriever: {result }")