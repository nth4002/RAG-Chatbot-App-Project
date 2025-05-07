from fastapi import FastAPI, File, UploadFile, HTTPException, Body, Path, Form
# import CORS middleware
from fastapi.middleware.cors import CORSMiddleware
from contextlib import asynccontextmanager
from pydantic_models import (
    QueryInput,
    QueryResponse, 
    DocumentInfo, 
    DeleteFileRequest,
    ChatSessionInfo,
    LandmarkInfoInput
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
import os, re
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

# setup logging (locally development)
# logging.basicConfig(filename='rag_chatbot_app.log', level=logging.INFO)
#W setup logging for containerized app
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s', # Example format
    # No filename argument - defaults to stderr
)
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
    # if delete_collection():
    #     logging.info("MongoDB vector store collection deleted successfully during shutdown")
    # else:
    #     logging.error("Failed to delete MongoDB store collection during shutdown")    
    # print("App shutdown: Deleting MongoDB collections...")
    # result = delete_logs_and_documents_collections()
    # if result:
    #     logging.info(f"Chatbot database deleted successfully during shutdown")
    # else:
    #     logging.error("Failed to delete Chatbot database during shutdown")
    # logging.info(f"Cleanup done: {result}")

app = FastAPI(lifespan=lifespan)


# configure and add the cors middleware
origins = [
    'http://localhost:3000',
    'http://localhost:5173'
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
    session_id = query_input.session_id
    logging.info(f"Session ID: {session_id}, User Query: {query_input.question}, Model: {query_input.model.value}, Heritage Filter: {query_input.heritage_id_filter}")
    if not session_id:
        session_id = str(uuid.uuid4())

    chat_history = get_chat_history(session_id) # For conversational chain state
    config = {"configurable": {"session_id": session_id}}
    logging.info(f"Chat History for session {session_id}: {chat_history}")
     
    conversational_rag_chain = get_rag_chain(query_input.model.value)
    
    try:
        # --- Context Retrieval with Filtering ---
        search_kwargs = {"k": 3} # Number of documents to retrieve
        if query_input.heritage_id_filter:
            # MongoDB Atlas Vector Search uses a 'filter' dict for pre-filtering
            # The metadata field name must match exactly how it's stored.
            search_kwargs["filter"] = {"heritage_id": query_input.heritage_id_filter}
            logging.info(f"Performing similarity search with filter: {search_kwargs['filter']}")
        else:
            logging.info("Performing similarity search without heritage_id filter.")

        
        if query_input.heritage_id_filter:
            # Create a specific retriever for this request
            filtered_retriever = vector_store.as_retriever(
                search_kwargs={'k': 3, 'filter': {'heritage_id': query_input.heritage_id_filter}}
            )
            logging.info(f"Using filtered retriever with filter: {{'heritage_id': '{query_input.heritage_id_filter}'}}")
        else:
            # Default retriever
            filtered_retriever = vector_store.as_retriever(search_kwargs={'k': 3})
            logging.info("Using default retriever without heritage filter.")

        context_documents = filtered_retriever.invoke(query_input.question)
        
        # Log the retrieved documents
        if context_documents:
            logging.info(f"Retrieved {len(context_documents)} documents for context:")
            for doc in context_documents:
                logging.info(f" - Source: {doc.metadata.get('file_id', 'N/A')}, Heritage: {doc.metadata.get('heritage_id', 'N/A')}, Content snippet: {doc.page_content[:100]}...")
        else:
            logging.warning("No relevant documents were retrieved for this query with the given filters.")
            
        final_chain = get_rag_chain(query_input.model.value, retriever_to_use=filtered_retriever)
        result = final_chain.invoke(
            {"input": query_input.question}, # Langchain chains usually expect "input" not "question"
            config=config,
        )
        answer = result['answer']
            
    except Exception as e:
        logging.error(f"Error invoking RAG chain: {str(e)}", exc_info=True)
        raise HTTPException(status_code=500, detail=f"Error processing chat: {str(e)}")
    
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
    file: UploadFile = File(...),
    heritage_id: Optional[str] = Form(None) # Accept heritage_id from form data
):  
    logging.info(f"Processing file: {file.filename}, heritage_id: {heritage_id}")

    try:
        # ... (file type validation) ...
        
        tmp_file_path = f"tmp_{file.filename}"
        try:
            with open(tmp_file_path, 'wb') as buffer:
                shutil.copyfileobj(file.file, buffer)
            
            file_id = insert_document_records(file.filename) # Records the file itself
            # Index with heritage_id if provided
            success = index_document_to_mongodb(tmp_file_path, file_id, heritage_id=heritage_id) 
            
            if success:
                logging.info(f"File {file.filename} indexed successfully with file_id={file_id}, heritage_id={heritage_id}")
                return {
                    "message": f"File {file.filename} has been successfully uploaded and indexed!",
                    "file_id": file_id,
                    "heritage_id": heritage_id
                }
            # ... (error handling) ...
        finally:
            if os.path.exists(tmp_file_path):
                os.remove(tmp_file_path)
    # ... (exception handling) ...
    except Exception as e:
        logging.error(f"Error in upload file: {str(e)}", exc_info=True)
        raise HTTPException(status_code=500, detail=str(e))

@app.post('/upload-landmark-info')
async def upload_landmark_info(landmark_data: LandmarkInfoInput = Body(...)):
    logging.info(f"Received landmark data for: {landmark_data.name}, ID: {landmark_data._id}")

    # ... (content aggregation as before) ...
    content = "..." # Your existing logic to build content string

    # Use landmark_data._id as the heritage_id for indexing
    heritage_id_for_indexing = landmark_data._id
    
    # ... (sanitized_name, tmp_file_path logic as before) ...
    sanitized_name = re.sub(r'[^\w\- ]', '', landmark_data.name)
    sanitized_name = re.sub(r'\s+', '_', sanitized_name).strip('_') or f"landmark_{heritage_id_for_indexing}"
    timestamp = datetime.now().strftime("%Y%m%d%H%M%S")
    tmp_filename = f"tmp_{sanitized_name}_{timestamp}.txt"
    tmp_file_path = tmp_filename

    file_id_record = None
    try:
        with open(tmp_file_path, 'w', encoding='utf-8') as f:
            f.write(content)

        # Use landmark_data.name for the document record filename, or a more descriptive name
        file_id_record = insert_document_records(f"{landmark_data.name}_info.txt")
        logging.info(f"Inserted document record for '{landmark_data.name}', file_id: {file_id_record}")

        success = index_document_to_mongodb(tmp_file_path, file_id_record, heritage_id=heritage_id_for_indexing)

        if success:
            logging.info(f"Landmark info '{landmark_data.name}' (file_id: {file_id_record}, heritage_id: {heritage_id_for_indexing}) indexed.")
            return {
                "message": f"Landmark information for '{landmark_data.name}' processed and indexed.",
                "file_id": file_id_record, # This is the ID of the document record itself
                "heritage_id": heritage_id_for_indexing # This is the ID used for grouping/filtering
            }
        # ... (error handling and rollback as before, using file_id_record) ...
    # ... (exception and finally block as before) ...
    except Exception as e:
        logging.error(f"Error processing landmark info '{landmark_data.name}': {str(e)}", exc_info=True)
        if file_id_record:
            try:
                delete_document_record(file_id_record)
                logging.info(f"Rolled back document record insertion for file_id: {file_id_record} due to exception.")
            except Exception as del_e:
                logging.error(f"Failed to rollback document record {file_id_record} after error: {del_e}")
        raise HTTPException(status_code=500, detail=f"An error occurred processing landmark information: {str(e)}")
    finally:
        if os.path.exists(tmp_file_path):
            try:
                os.remove(tmp_file_path)
                logging.info(f"Removed temporary file: {tmp_file_path}")
            except Exception as e:
                logging.error(f"Error removing temporary file {tmp_file_path}: {str(e)}")

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
    

@app.post('/upload-landmark-info')
async def upload_landmark_info(landmark_data: LandmarkInfoInput = Body(...)):
    """
    Accepts landmark information as JSON, extracts relevant text,
    saves it to a temporary file, and indexes it.
    """
    logging.info(f"Received landmark data for: {landmark_data.name}")
    print(f"Received landmark data for: {landmark_data.name}")

    # 1. Extract relevant text fields
    content_parts = []
    content_parts.append(f"Name: {landmark_data.name}")
    if landmark_data.description:
        content_parts.append(f"Description: {landmark_data.description}")

    # Extract historical events if they exist
    if landmark_data.additionalInfo and landmark_data.additionalInfo.historicalEvents:
        content_parts.append("\nHistorical Events:")
        for event in landmark_data.additionalInfo.historicalEvents:
            content_parts.append(f"\n---\nTitle: {event.title}\nDescription: {event.description}")

    content = "\n".join(content_parts)
    logging.info(content)
    # 2. Sanitize the name for use as a filename
    # Remove non-alphanumeric characters (except spaces, hyphens, underscores) and replace spaces with underscores
    sanitized_name = re.sub(r'[^\w\- ]', '', landmark_data.name)
    sanitized_name = re.sub(r'\s+', '_', sanitized_name).strip('_')
    if not sanitized_name: # Handle cases where the name becomes empty after sanitization
        sanitized_name = f"landmark_{landmark_data._id}"

    # Create a unique temporary filename based on the sanitized name
    timestamp = datetime.now().strftime("%Y%m%d%H%M%S")
    tmp_filename = f"tmp_{sanitized_name}_{timestamp}.txt"
    tmp_file_path = tmp_filename # Assuming it's created in the current directory

    logging.info(f"Aggregated content length: {len(content)} chars.")
    logging.info(f"Using temporary file path: {tmp_file_path}")

    file_id = None # Initialize file_id
    try:
        # 3. Write content to temporary file
        with open(tmp_file_path, 'w', encoding='utf-8') as f:
            f.write(content)

        # 4. Insert record into your document tracking database
        # Use the original landmark name for the record
        full_path = os.path.abspath(tmp_file_path)
        logging.info(full_path)
        file_id = insert_document_records(landmark_data.name) # Append context
        logging.info(f"Inserted document record for '{landmark_data.name}', file_id: {file_id}")

        # 5. Index the temporary file content into MongoDB Vector Store
        success = index_document_to_mongodb(full_path, file_id)

        if success:
            logging.info(f"Landmark info '{landmark_data.name}' (file_id: {file_id}) indexed successfully from temporary file.")
            return {
                "message": f"Landmark information for '{landmark_data.name}' has been successfully processed and indexed.",
                "file_id": file_id
            }
        else:
            # If indexing fails, attempt to roll back the document record insertion
            logging.error(f"Failed to index landmark info '{landmark_data.name}' (file_id: {file_id}) from {full_path}.")
            if file_id:
                delete_document_record(file_id)
                logging.info(f"Rolled back document record insertion for file_id: {file_id}")
            raise HTTPException(status_code=500, detail=f"Failed to index landmark information for '{landmark_data.name}'")

    except Exception as e:
        logging.error(f"Error processing landmark info '{landmark_data.name}': {str(e)}", exc_info=True)
         # Attempt rollback if file_id was generated before the exception
        if file_id:
             try:
                 # Check if the record still exists before trying to delete
                 # Note: This might require a function like `check_document_exists(file_id)`
                 # For simplicity, we just try to delete. If it fails, log it.
                 delete_document_record(file_id)
                 logging.info(f"Rolled back document record insertion for file_id: {file_id} due to exception.")
             except Exception as del_e:
                 logging.error(f"Failed to rollback document record {file_id} after error: {del_e}")
        raise HTTPException(status_code=500, detail=f"An error occurred processing landmark information: {str(e)}")

    finally:
        # 6. Clean up the temporary file
        if os.path.exists(tmp_file_path):
            try:
                os.remove(tmp_file_path)
                logging.info(f"Removed temporary file: {tmp_file_path}")
            except Exception as e:
                logging.error(f"Error removing temporary file {tmp_file_path}: {str(e)}")