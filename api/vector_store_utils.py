# Vector store integration
"""
This file contains functions for interacting with the
MongoDB Atlas  vector store, which is essential for our
RAG system's retrieval capabilities.
"""

from langchain_community.document_loaders import PyPDFLoader, Docx2txtLoader, TextLoader
from langchain_google_genai import GoogleGenerativeAIEmbeddings
from langchain_text_splitters import RecursiveCharacterTextSplitter

from typing import List, Optional
from langchain_core.documents import Document
from langchain_huggingface import HuggingFaceEmbeddings
from dotenv import load_dotenv, find_dotenv
from langchain_mongodb import MongoDBAtlasVectorSearch
# from pymongo import MongoClient
from pymongo.mongo_client import MongoClient
from pymongo.operations import SearchIndexModel

from fastapi import HTTPException

import os
import logging

from scraper import WebScraper


# force reload the .env file
load_dotenv(find_dotenv(), override=True)

# set up logging
# logging.basicConfig(filename="rag_chatbot_app.log", level=logging.INFO)
#W setup logging for containerized app
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s', # Example format
    # No filename argument - defaults to stderr
)

# local_embeddings = HuggingFaceEmbeddings(model_name="all-MiniLM-L6-v2")
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
DB_NAME = "Vector-Store-Cluster"
COLLECTION_NAME = "Vector-Store-Collection"
ATLAS_VECTOR_SEARCH_INDEX_NAME = "Vector-Store-Index"

MONGODB_COLLECTION = client[DB_NAME][COLLECTION_NAME]

vector_store = MongoDBAtlasVectorSearch(
    collection=MONGODB_COLLECTION,
    embedding=gemini_embeddings,
    index_name=ATLAS_VECTOR_SEARCH_INDEX_NAME,
    relevance_score_fn="cosine"
)

def initialize_vector_store():
    """Initialize the MongoDB collection and verify the vector search index."""
    try:
        # Verify MongoDB connection
        client.server_info()  # Raises an exception if connection fails
        logging.info("MongoDB connection established successfully")

        # Check if collection exists
        if COLLECTION_NAME not in client[DB_NAME].list_collection_names():
            client[DB_NAME].create_collection(COLLECTION_NAME)
            logging.info(f"Created collection {COLLECTION_NAME}")
        else:
            logging.info(f"Collection {COLLECTION_NAME} already exists")


        # Note: Vector search index must be created in MongoDB Atlas UI or via API
        logging.info(f"Ensure vector search index '{ATLAS_VECTOR_SEARCH_INDEX_NAME}' is configured in MongoDB Atlas for collection {COLLECTION_NAME}")
        # vector_store.create_vector_search_index(
        #     dimensions=768,
        #     filters=[{"type":"filter", "path": "source"}],
        #     update=True
        # )
        # Test vector store by adding a dummy document
        dummy_doc = Document(page_content="Test document", metadata={"file_id": 0})
        vector_store.add_documents([dummy_doc])
        logging.info("Added test document to vector store")

        # Log the inserted document to inspect its structure
        inserted_doc = vector_store._collection.find_one({"file_id": 0})
        if inserted_doc:
            logging.info(f"Inserted test document: {inserted_doc.get('file_id')}")
        else:
            logging.error("Test document not found after insertion")

        # Delete the test document
        result = vector_store._collection.delete_one({"file_id": 0})
        if result.deleted_count > 0:
            logging.info("Successfully deleted test document")
        else:
            logging.warning("No test document was deleted; check document structure or query")

        # Verify deletion
        remaining_doc = vector_store._collection.find_one({".file_id": 0})
        if remaining_doc:
            logging.error(f"Test document still exists after deletion attempt: {remaining_doc}")
        else:
            logging.info("Confirmed test document was deleted")

    except Exception as e:
        logging.error(f"Failed to initialize vector store: {str(e)}")
        raise

def create_index():
    # Connect to your Atlas deployment
    # client = MongoClient(
    #     MONGODB_ATLAS_CLUSTER_URI
    # )
    # DB_NAME = "RAG-Chatbot-Cluster"
    # COLLECTION_NAME = "RAG-Chatbot-Collection-Test"
    # ATLAS_VECTOR_SEARCH_INDEX_NAME = "RAG-Chatbot-Index-Test"

    # collection = client[DB_NAME][COLLECTION_NAME]

    # Create your index model, then create the search index
    search_index_model = SearchIndexModel(
                definition={
                    "mappings": {
                        "dynamic": True,
                        "fields": {
                            "embedding": {  # Correct structure: field name as key
                                "type": "knnVector",
                                "dimensions": 768,
                                "similarity": "cosine"
                            }
                        }
                    }
                },
                name=ATLAS_VECTOR_SEARCH_INDEX_NAME,
            )
    
    result = MONGODB_COLLECTION.create_search_index(model=search_index_model)
    logging.info(f"Succesfully creating Atlas Search Index: {result}")


def delete_collection():
    """Delete the entire MongoDB collection."""
    try:
        client[DB_NAME].drop_collection(COLLECTION_NAME)
        logging.info(f"Successfully deleted collection {COLLECTION_NAME}")
        return True
    except Exception as e:
        logging.error(f"Error deleting collection {COLLECTION_NAME}: {str(e)}")
        return False
"""
Document Loading and Splitting
This functions handles loading different types of documents (pdf, docx, html)
and splitting them into smaller chunks. 
"""

def load_and_split_html(base_url: str) -> List[Document]:
    # base_url = "https://apidog.com/vi/blog/rag-deepseek-r1-ollama-vi/"  # Replace with your target website
    base_url = base_url.strip()
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
    logging.info(f"Total pages scraped: {len(scraped_content)}")
    logging.info(f"Total chunks created: {len(processed_chunks)}")
    
    # Example of accessing the first chunk
    return documents


def load_and_split_document(file_path: str) -> List[Document]:
    if file_path.endswith(".pdf"):
        print(f"Processing the PDF file!")
        loader = PyPDFLoader(file_path)
    elif file_path.endswith('.docx'):
        print(f"Processing the Docx file!")
        loader = Docx2txtLoader(file_path)
    elif file_path.endswith('.txt'):
        print('Processing the text file!')
        loader = TextLoader(file_path, encoding='utf-8')
    elif file_path.endswith('.html') or file_path.startswith("http"):
        print(f"Processing the html file!")
        return load_and_split_html(file_path)
    else:
        raise ValueError("Unsupported file type: {file_path}")
    
    documents = loader.load()
    return text_splitters.split_documents(documents)


"""
Indexing documents
"""

def index_document_to_mongodb(file_path: str, file_id: int, heritage_id: Optional[str] = None) -> bool:
    try:
        # load and split the document into smaller chunks
        splits = load_and_split_document(file_path)
        logging.info(f"Loaded {len(splits)} document chunks from {file_path}")
        
        for split in splits:
            split.metadata['file_id'] = file_id  # Unique ID for this specific document content
            if heritage_id:
                split.metadata['heritage_id'] = heritage_id # ID for the overall heritage item
        
        vector_store.add_documents(splits)
        logging.info(f"Successfully indexed {len(splits)} chunks for file_id: {file_id}, heritage_id: {heritage_id}")
        return True
    except Exception as e:
        logging.error(f"Error indexing document (file_id: {file_id}, heritage_id: {heritage_id}): {e}", exc_info=True)
        return False    
    
"""Deleting documents"""

def delete_doc_from_mongodb(file_id: int) -> bool:
    try:
        # get the document with the specified file_id
        # meaning all chunks of the document
        docs = vector_store._collection.find({"file_id": file_id})
        print(f"Found {len(docs.to_list())} document chunks for file_id {file_id}")
        
        # delete the document
        vector_store._collection.delete_many({"file_id": file_id})
        # vectorstore.delete(ids=docs['ids'])
        print(f"Succesfully deleted document with file_id {file_id}")
        
        return True
    
    except Exception as e:
        print(f"Error deleting document with file_id {file_id} from MongoDB: {str(e)}")
        return False