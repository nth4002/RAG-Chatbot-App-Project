# Vector store integration
"""
This file contains functions for interacting with the
Chroma vector store, which is essential for our
RAG system's retrieval capabilities.
"""

from langchain_community.document_loaders import PyPDFLoader, Docx2txtLoader, UnstructuredHTMLLoader
from langchain_text_splitters import RecursiveCharacterTextSplitter
from langchain_chroma import Chroma
from typing import List
from langchain_core.documents import Document
from langchain_huggingface import HuggingFaceEmbeddings


import os

embeddings = HuggingFaceEmbeddings(model_name="all-MiniLM-L6-v2")
text_splitters = RecursiveCharacterTextSplitter(chunk_size=1000, chunk_overlap=200, length_function=len)


vectorstore = Chroma(
    # collection_name="chroma",
    embedding_function=embeddings,
    persist_directory="./chroma_db"
)

"""
Document Loading and Splitting
This functions handles loading different types of documents (pdf, docx, html)
and splitting them into smaller chunks. 
"""

def load_and_split_document(file_path: str) -> List[Document]:
    if file_path.endswith(".pdf"):
        loader = PyPDFLoader(file_path)
    elif file_path.endswith('.docx'):
        loader = Docx2txtLoader(file_path)
    elif file_path.endswith('.html'):
        loader = UnstructuredHTMLLoader(file_path)
    else:
        raise ValueError("Unsupported file type: {file_path}")
    
    documents = loader.load()
    return text_splitters.split_documents(documents)


"""
Indexing documents
"""

def index_document_to_chroma(file_path: str, file_id: int) -> bool:
    try:
        # load and split the document into smaller chunks
        splits = load_and_split_document(file_path)
        # each document contains 2 attributes: a dictionary called metadata and a string called page_content
        for split in splits:
            # add file id to the metadata of each split
            split.metadata['file_id'] = file_id
        
        # add the document chunks to the vector store
        vectorstore.add_documents(splits)
        
        return True
    except Exception as e:
        print(f"Error indexing document: {e}")
        return False
    
    
"""Deleting documents"""

def delete_doc_from_chroma(file_id: int) -> bool:
    try:
        # get the document with the specified file_id
        # meaning all chunks of the document
        docs = vectorstore.get(where={"file_id": file_id})
        print(f"Found {len(docs['ids'])} document chunks for file_id {file_id}")
        
        # delete the document
        vectorstore._collection.delete(where={"file_id": file_id})
        # vectorstore.delete(ids=docs['ids'])
        print(f"Succesfully deleted document with file_id {file_id}")
        
        return True
    
    except Exception as e:
        print(f"Error deleting document with file_id {file_id} from Chroma: {str(e)}")
        return False