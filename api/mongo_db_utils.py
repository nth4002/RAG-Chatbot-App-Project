# Vector store integration
"""
This file contains functions for interacting with the
MongoDB Atlas  vector store, which is essential for our
RAG system's retrieval capabilities.
"""

from langchain_community.document_loaders import PyPDFLoader, Docx2txtLoader, UnstructuredHTMLLoader
from langchain_google_genai import GoogleGenerativeAIEmbeddings
from langchain_text_splitters import RecursiveCharacterTextSplitter

from typing import List
from langchain_core.documents import Document
from langchain_huggingface import HuggingFaceEmbeddings
from dotenv import load_dotenv, find_dotenv
from langchain_mongodb import MongoDBAtlasVectorSearch
from pymongo import MongoClient

import os
import logging

from scraper import WebScraper


# force reload the .env file
load_dotenv(find_dotenv(), override=True)

# set up logging
logging.basicConfig(filename="rag_chatbot_app.log", level=logging.INFO)


local_embeddings = HuggingFaceEmbeddings(model_name="all-MiniLM-L6-v2")
text_splitters = RecursiveCharacterTextSplitter(chunk_size=1000, chunk_overlap=200, length_function=len)

gemini_embeddings = GoogleGenerativeAIEmbeddings(
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
    embedding=gemini_embeddings,
    index_name=ATLAS_VECTOR_SEARCH_INDEX_NAME,
    relevance_score_fn="cosine"
)


"""
Document Loading and Splitting
This functions handles loading different types of documents (pdf, docx, html)
and splitting them into smaller chunks. 
"""

def load_and_split_html(base_url: str) -> List[Document]:
    # base_url = "https://apidog.com/vi/blog/rag-deepseek-r1-ollama-vi/"  # Replace with your target website
    scraper = WebScraper(base_url)
    # print("step 1")
    # Scrape the website
    scraped_content = scraper.scrape_website(max_pages=1)
    # print("step 2")
    # Process and split the content
    processed_chunks = scraper.process_content(scraped_content)
    # print("step 3")
    documents = []
    for chunk in processed_chunks:
        documents.append(
            Document(
                page_content = chunk.get('content'),
                metadata = {"source": chunk.get('url')}
            )
        )

    # Print results
    print(f"Total pages scraped: {len(scraped_content)}")
    print(f"Total chunks created: {len(processed_chunks)}")
    
    # Example of accessing the first chunk
    return documents


def load_and_split_document(file_path: str) -> List[Document]:
    if file_path.endswith(".pdf"):
        print(f"Processing the PDF file!")
        loader = PyPDFLoader(file_path)
    elif file_path.endswith('.docx'):
        print(f"Processing the Docx file!")
        loader = Docx2txtLoader(file_path)
    elif file_path.endswith('.html'):
        print(f"Processing the html file!")
        return load_and_split_html(file_path)
    else:
        raise ValueError("Unsupported file type: {file_path}")
    
    documents = loader.load()
    return text_splitters.split_documents(documents)


"""
Indexing documents
"""

def index_document_to_mongodb(file_path: str, file_id: int) -> bool:
    try:
        # load and split the document into smaller chunks
        splits = load_and_split_document(file_path)
        logging.info(f"Loaded {len(splits)} document chunks from {file_path}")
        # each document contains 2 attributes: a dictionary called metadata and a string called page_content
        for split in splits:
            # add file id to the metadata of each split
            split.metadata['file_id'] = file_id
        
        # add the document chunks to the vector store
        vector_store.add_documents(splits)
        
        return True
    except Exception as e:
        print(f"Error indexing document: {e}")
        return False
    
    
"""Deleting documents"""

def delete_doc_from_mongodb(file_id: int) -> bool:
    try:
        # get the document with the specified file_id
        # meaning all chunks of the document
        docs = vector_store.get(where={"file_id": file_id})
        print(f"Found {len(docs['ids'])} document chunks for file_id {file_id}")
        
        # delete the document
        vector_store._collection.delete(where={"file_id": file_id})
        # vectorstore.delete(ids=docs['ids'])
        print(f"Succesfully deleted document with file_id {file_id}")
        
        return True
    
    except Exception as e:
        print(f"Error deleting document with file_id {file_id} from MongoDB: {str(e)}")
        return False