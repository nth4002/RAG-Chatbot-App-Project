from fastapi import FastAPI, File, UploadFile, HTTPException, Body, Path 
# import CORS middleware
from fastapi.middleware.cors import CORSMiddleware
from contextlib import asynccontextmanager
from pydantic_models import (
    QueryInput,
    QueryResponse, 
    DocumentInfo, 
    DeleteFileRequest,
    ChatSessionInfo
)
from langchain_utils import (
    get_rag_chain, 
    get_session_history
)
from new_db_util import (
    insert_document_records,
    insert_application_logs,
    get_all_documents,
    get_chat_history,
    delete_document_record,
    delete_logs_and_documents_collections,
    DB_NAME,
    MONGODB_ATLAS_CLUSTER_URI_2,
    LOG_COLLECTION_NAME
)
from vector_store_utils import (
    index_document_to_mongodb,
    delete_doc_from_mongodb, 
    initialize_vector_store, 
    delete_collection,
    create_index
)
import os
import uuid
import logging
import os
import shutil
from typing import Optional, Dict, Union
import requests
from bs4 import BeautifulSoup
from datetime import datetime
from vector_store_utils import vector_store

from langchain_core.messages import HumanMessage, AIMessage
from pymongo import MongoClient

from typing import List

# setup logging
logging.basicConfig(filename='rag_chatbot_app.log', level=logging.INFO)

@asynccontextmanager
async def lifespan(app: FastAPI):
    """Initialize database tables and MongoDB vector store when the FastAPI server starts"""
    logging.info("Initializing database tables and vector store...")
    initialize_vector_store()
    create_index()
    logging.info("Database tables and vector store initialized successfully")
    yield
    # Cleanup: Delete the MongoDB collection on shutdown
    logging.info("Shutting down server, deleting MongoDB vector store collection...")
    if delete_collection():
        logging.info("MongoDB vector store collection deleted successfully during shutdown")
    else:
        logging.error("Failed to delete MongoDB store collection during shutdown")    
    print("App shutdown: Deleting MongoDB collections...")
    result = delete_logs_and_documents_collections()
    if result:
        logging.info(f"Chatbot database deleted successfully during shutdown")
    else:
        logging.error("Failed to delete Chatbot database during shutdown")
    # logging.info(f"Cleanup done: {result}")

app = FastAPI(lifespan=lifespan)


# configure and add the cors middleware
origins = [
    'http://localhost:3000'
]
app.add_middleware(
    CORSMiddleware,
    allow_origins=origins,
    allow_credentials=True, # allow cookies and authorization headers if needed
    allow_methods=["*"], # allow all standard method (GET, POST, DELETE,PUT, etc)
    allow_headers=["*"] # allow all  headers (including content-type, authorization, etc.)
)

def scrape_website(url: str) -> str:
    """Scrape website content and return cleaned text."""
    try:
        url = url.strip()
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
    config = {
        "configurable": {"session_id": session_id}
    }
    logging.info(f"Chat History: {chat_history}")
    
    conversational_rag_chain = get_rag_chain(query_input.model.value)
    try:
        result = conversational_rag_chain.invoke(
            {"input": query_input.question},
            config=config,
        )
        # result is a dictionary with keys include (input, context (list of Document objects), answer)
        answer = result['answer']
        # context = result['context']
        context = vector_store.similarity_search(query_input.question, k=2)
        
        # Log the retrieved documents
        if context:
            logging.info(f"Retrieved documents: {context}")
            
        else:
            logging.warning("No relevant documents were retrieved for this query")
            
    except Exception as e:
        logging.error(f"Error invoking RAG chain: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))
    
    insert_application_logs(session_id, query_input.question, answer, query_input.model.value)
    logging.info(f"Session ID: {session_id}, AI Response: {answer}")
    return QueryResponse(answer=answer, session_id=session_id, model=query_input.model)

# this endpoint is for reloading (F5) and still get the same chat history (not going back to the original state)
@app.get('/chat/history/{session_id}')
async def get_history(session_id: str = Path(..., description="The ID of the session to retrieve history for")):
    logging.info(f"Attempting to retrieve chat history for session id: {session_id}")

    try: 
        history = get_session_history(session_id)
        messages = history.messages
        formatted_messages = []
        for msg in messages:
            if isinstance(msg, HumanMessage):
                formatted_messages.append({"role": "user", "content": msg.content})
            elif isinstance(msg, AIMessage):
                formatted_messages.append({"role": "assistant", "content": msg.content})
        logging.info(f"Successfully retrieved {len(formatted_messages)} messages for session {session_id}")
        return formatted_messages
    
    except Exception as e:
        logging.error(f"Error occured while retrieving history for session {session_id}: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Could not retrieve chat history, error: {str(e)}")



# this endpoint is for accessing to one of those past chat histories in the sidebar
@app.get("/chat/sessions", response_model=List[ChatSessionInfo])
async def get_chat_sessions():
    """Retrieves a list of all unique chat session IDs."""
    logging.info("Attempting to retrieve list of all chat sessions")
    try:
        # Connect directly to MongoDB to query the chat history collection
        client = MongoClient(MONGODB_ATLAS_CLUSTER_URI_2)
        db = client[DB_NAME]
        logs_collection = db[LOG_COLLECTION_NAME] # Collection used by MongoDBChatMessageHistory
        logging.info(f"Find total {logs_collection.count_documents({})}documents in log collection")
        logging.info(f"the keys for logs collection is: {logs_collection.find_one().keys()}")
        # Find distinct SessionId values
        distinct_session_ids = logs_collection.distinct("session_id")
        logging.info(f"Found {len(distinct_session_ids)} distinct session IDs.")

        # Create response data (simplified for now)
        sessions_info = []
        for session_id in distinct_session_ids:
             # Create a basic display name (e.g., "Chat ****uuid_end")
             display_name = f"Chat ...{session_id[-6:]}" if len(session_id) > 6 else session_id
             sessions_info.append(ChatSessionInfo(session_id=session_id, display_name=display_name))

        # Optional Enhancement: Sort by most recent? Requires fetching timestamps.

        client.close() # Close the connection
        return sessions_info

    except Exception as e:
        logging.error(f"Error retrieving chat session list: {str(e)}")
        # Close client if open on error
        try: client.close()
        except: pass
        raise HTTPException(status_code=500, detail="Could not retrieve chat session list.")
    

@app.post('/upload-file')
async def upload_file(
    file: UploadFile = File(...)
):  
    logging.info(f"Processing file: {file.filename}")
    print(f"Processing file: {file.filename}")

    try:
        allowed_extensions = [".pdf", ".docx"]
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
            file_id = insert_document_records(file.filename)
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
            file_id = insert_document_records(filename)
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