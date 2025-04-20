from fastapi import FastAPI, File, UploadFile, HTTPException, Body
from contextlib import asynccontextmanager
from pydantic_models import QueryInput, QueryResponse, DocumentInfo, DeleteFileRequest
from langchain_utils import get_rag_chain
from db_utils import (
    insert_application_logs, 
    get_chat_history, 
    get_all_documents, 
    insert_document_record, 
    delete_document_record,
    create_application_logs,
    create_document_store
)
from mongo_db_utils import index_document_to_mongodb, delete_doc_from_mongodb
import os
import uuid
import logging
import os
import shutil
from typing import Optional, Dict, Union
import requests
from bs4 import BeautifulSoup
from datetime import datetime

logging.basicConfig(filename='rag_chatbot_app.log', level=logging.INFO)

@asynccontextmanager
async def lifespan(app: FastAPI):
    """Initialize database tables when the FastAPI server starts"""
    logging.info("Initializing database tables...")
    create_application_logs()
    create_document_store()
    logging.info("Database tables initialized successfully")
    yield
    # Cleanup code (if any) goes here

app = FastAPI(lifespan=lifespan)

def scrape_website(url: str) -> str:
    """Scrape website content and return cleaned text."""
    try:
        response = requests.get(url, timeout=10)
        response.raise_for_status()
        
        soup = BeautifulSoup(response.text, 'html.parser')
        
        # Remove script and style elements
        for element in soup(['script', 'style', 'header', 'footer', 'nav']):
            element.decompose()
        
        # Get text content
        text = soup.get_text()
        
        # Clean text
        lines = (line.strip() for line in text.splitlines())
        chunks = (phrase.strip() for line in lines for phrase in line.split("  "))
        text = ' '.join(chunk for chunk in chunks if chunk)
        
        return text
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to scrape website: {str(e)}")

@app.post("/chat", response_model=QueryResponse)
def chat(query_input: QueryInput):
    # get the session id from the input, if not present, generate a new one
    session_id = query_input.session_id
    logging.info(f"Session ID: {session_id}, User Query: {query_input.question},\
        Model: {query_input.model.value}")
    if not session_id:
        session_id = str(uuid.uuid4())

    # get the chat history for the session id, the result is a list of dictionaries
    chat_history = get_chat_history(session_id)
    logging.info(f"Chat History: {chat_history}")
    
    rag_chain = get_rag_chain(query_input.model.value)
    try:
        answer = rag_chain.invoke({
            "input": query_input.question,
            "chat_history": chat_history
        })['answer']
    except Exception as e:
        logging.error(f"Error invoking RAG chain: {str(e)}")
        raise
    
    insert_application_logs(session_id, query_input.question, answer, query_input.model.value)
    logging.info(f"Session ID: {session_id}, AI Response: {answer}")
    return QueryResponse(answer=answer, session_id=session_id, model=query_input.model)

@app.post('/upload-file')
async def upload_file(
    file: UploadFile = File(...)
):  
    logging.info(f"Processing file: {file.filename}")
    print(f"Processing file: {file.filename}")

    try:
        allowed_extensions = [".pdf", "'.docx"]
        file_extension = os.path.splitext(file.filename)[1].lower() # tuple of(root, ext)
        if file_extension not in allowed_extensions:
            raise HTTPException(
                status_code=400,
                detail=f"Unsupported file type. Allowed types are: {', '.join(allowed_extensions)}"
            )
        
        tmp_file_path = f"tmp_{file.filename}"
        try:
            with open(tmp_file_path, 'wb') as buffer:
                shutil.copyfileobj(file.file, buffer)
            file_id = insert_document_record(file.filename)
            success = index_document_to_mongodb(tmp_file_path, file_id)
            if success:
                logging.info(f"File {file.filename} indexed successfully, file_id = {file_id}")
                return {
                    "message": f"File {file.filename} has been successfully uploaded and indexed!",
                    "file_id": file_id
                }
            else:
                delete_document_record(file_id)
                raise HTTPException(status_code=500, 
                                    detail=f"Failed to index file {file.filename}")
            
        finally:
            if os.path.exists(tmp_file_path):
                os.remove(tmp_file_path)
    except Exception as e:
        logging.error(f"Error in upload file: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))

@app.post('/upload-website')
async def upload_website(website: Dict = Body(...)):
    logging.info(f"Received website data: {website}")
    print(f"Received website data: {website}")

    if 'url' not in website:
        raise HTTPException(status_code=500, detail=f"Invalid input. URL not found in website data!")
    
    try:
        url = website['url']
        dtype = website['type']
        logging.info(f"Processing website URL: {url} (type: {dtype})")
        print(f'Processing {url} (type: {dtype})')

        domain = url.split('//')[-1].split('/')[0]
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        filename = f"{domain}_{timestamp}.html"

        content = scrape_website(url)
        tmp_file_path = f'tmp_{filename}'
        try:
            with open(tmp_file_path, 'w', encoding='utf-8') as f:
                f.write(content)
            file_id = insert_document_record(filename)
            success = index_document_to_mongodb(url, file_id)

            if success:
                logging.info(f"Website {url} indexed successfully, file_id = {file_id}")
                return {
                    "message": f"Website {url} has been successfully scraped and indexed."
                    , "file_id": file_id
                }
            else:
                delete_document_record(file_id)
                raise HTTPException(status_code=500, detail=f"Failed to index website content from {url}")
        finally:
            if os.path.exists(tmp_file_path):
                os.remove(tmp_file_path)

    except Exception as e:
        logging.error(f"ERROR in upload website: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))
@app.get("/list-docs", response_model=list[DocumentInfo])
def list_documents():
    return get_all_documents()

@app.post("/delete-doc")
def delete_document(request: DeleteFileRequest):
    # Delete from MongoDB
    mongodb_delete_success = delete_doc_from_mongodb(request.file_id)

    if mongodb_delete_success:
        # If successfully deleted from MongoDB, delete from our sqlite3 database
        db_delete_success = delete_document_record(request.file_id)
        if db_delete_success:
            return {"message": f"Successfully deleted document with file_id {request.file_id} from the system."}
        else:
            return {"error": f"Deleted from MognoDB Atlas but failed to delete document with file_id {request.file_id} from the database."}
    else:
        return {"error": f"Failed to delete document with file_id {request.file_id} from MongoDB."}