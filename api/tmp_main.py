from fastapi import FastAPI, File, UploadFile, HTTPException, Body, Path
from fastapi.middleware.cors import CORSMiddleware
from contextlib import asynccontextmanager
from pydantic_models import (
    QueryInput,
    QueryResponse,
    DocumentInfo,
    DeleteFileRequest,
    ChatSessionInfo,
    LandmarkInfoInput,
)
from langchain_utils import get_rag_chain, get_session_history
from new_db_util import (
    insert_document_records,
    insert_application_logs,
    get_all_documents,
    get_chat_history,
    delete_document_record,
    delete_logs_and_documents_collections,
    DB_NAME,
    MONGODB_ATLAS_CLUSTER_URI_2,
    LOG_COLLECTION_NAME,
)
from vector_store_utils import (
    index_document_to_mongodb,
    delete_doc_from_mongodb,
    initialize_vector_store,
    delete_collection,
    create_index,
)
import os
import re
import uuid
import logging
import shutil
from typing import Optional, Dict, Union
import requests
from bs4 import BeautifulSoup
from datetime import datetime
from vector_store_utils import vector_store
from langchain_core.messages import HumanMessage, AIMessage
from pymongo import MongoClient
from typing import List

# Setup logging
logging.basicConfig(filename="rag_chatbot_app.log", level=logging.INFO)


@asynccontextmanager
async def lifespan(app: FastAPI):
    """Initialize database tables and MongoDB vector store when the FastAPI server starts"""
    logging.info("Initializing database tables and vector store...")
    initialize_vector_store()
    create_index()
    logging.info("Database tables and vector store initialized successfully")
    yield
    logging.info("Shutting down server, deleting MongoDB vector store collection...")


app = FastAPI(lifespan=lifespan)

# Configure and add CORS middleware
origins = ["http://localhost:3000", "http://localhost:5173"]
app.add_middleware(
    CORSMiddleware,
    allow_origins=origins,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


def scrape_website(url: str) -> str:
    """Scrape website content and return cleaned text."""
    try:
        url = url.strip()
        response = requests.get(url, timeout=10)
        response.raise_for_status()
        soup = BeautifulSoup(response.text, "html.parser")
        for element in soup(["script", "style", "header", "footer", "nav"]):
            element.decompose()
        text = soup.get_text()
        lines = (line.strip() for line in text.splitlines())
        chunks = (phrase.strip() for line in lines for phrase in line.split("  "))
        text = " ".join(chunk for chunk in chunks if chunk)
        return text
    except Exception as e:
        raise HTTPException(
            status_code=500, detail=f"Failed to scrape website: {str(e)}"
        )


@app.post("/chat", response_model=QueryResponse)
def chat(query_input: QueryInput):
    session_id = query_input.session_id
    if not session_id:
        session_id = str(uuid.uuid4())

    logging.info(
        f"Session ID: {session_id}, User Query: {query_input.question}, "
        f"Model: {query_input.model}, Heritage Name: {query_input.heritageName or 'None'}"
    )

    # Get chat history
    chat_history = get_chat_history(session_id)
    config = {"configurable": {"session_id": session_id}}
    logging.info(f"Chat History: {chat_history}")

    # Construct contextualized question
    user_question = query_input.question
    question = user_question
    if query_input.heritageName:
        logging.info(f"Contextualized Query: {question}")
        # question = user_question
        question = f"Dựa trên thông tin di tích {query_input.heritageName}. Nội dung câu hỏi: {user_question}"

    conversational_rag_chain = get_rag_chain(query_input.model)
    try:
        result = conversational_rag_chain.invoke(
            {"input": question},  # Use contextualized question
            config=config,
        )
        answer = result["answer"]
        context = vector_store.similarity_search(question, k=2)

        if context:
            logging.info(f"Retrieved documents: {context}")
        else:
            logging.warning("No relevant documents were retrieved for this query")

    except Exception as e:
        logging.error(f"Error invoking RAG chain: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))

    # Log only the raw user question
    insert_application_logs(session_id, user_question, answer, query_input.model)
    logging.info(f"Session ID: {session_id}, AI Response: {answer}")
    return QueryResponse(answer=answer, session_id=session_id, model=query_input.model)


@app.get("/chat/history/{session_id}")
async def get_history(
    session_id: str = Path(
        ..., description="The ID of the session to retrieve history for"
    )
):
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
        logging.info(
            f"Successfully retrieved {len(formatted_messages)} messages for session {session_id}"
        )
        return formatted_messages
    except Exception as e:
        logging.error(
            f"Error occurred while retrieving history for session {session_id}: {str(e)}"
        )
        raise HTTPException(
            status_code=500, detail=f"Could not retrieve chat history, error: {str(e)}"
        )


@app.get("/chat/sessions", response_model=List[ChatSessionInfo])
async def get_chat_sessions():
    logging.info("Attempting to retrieve list of all chat sessions")
    try:
        client = MongoClient(MONGODB_ATLAS_CLUSTER_URI_2)
        db = client[DB_NAME]
        logs_collection = db[LOG_COLLECTION_NAME]
        logging.info(
            f"Find total {logs_collection.count_documents({})} documents in log collection"
        )
        distinct_session_ids = logs_collection.distinct("session_id")
        logging.info(f"Found {len(distinct_session_ids)} distinct session IDs.")
        sessions_info = []
        for session_id in distinct_session_ids:
            display_name = (
                f"Chat ...{session_id[-6:]}" if len(session_id) > 6 else session_id
            )
            sessions_info.append(
                ChatSessionInfo(session_id=session_id, display_name=display_name)
            )
        client.close()
        return sessions_info
    except Exception as e:
        logging.error(f"Error retrieving chat session list: {str(e)}")
        try:
            client.close()
        except:
            pass
        raise HTTPException(
            status_code=500, detail="Could not retrieve chat session list."
        )


@app.post("/upload-file")
async def upload_file(file: UploadFile = File(...)):
    logging.info(f"Processing file: {file.filename}")
    try:
        allowed_extensions = [".pdf", ".docx"]
        file_extension = os.path.splitext(file.filename)[1].lower()
        if file_extension not in allowed_extensions:
            raise HTTPException(
                status_code=400,
                detail=f"Unsupported file type. Allowed types are: {', '.join(allowed_extensions)}",
            )
        tmp_file_path = f"tmp_{file.filename}"
        try:
            with open(tmp_file_path, "wb") as buffer:
                shutil.copyfileobj(file.file, buffer)
            file_id = insert_document_records(file.filename)
            success = index_document_to_mongodb(tmp_file_path, file_id)
            if success:
                logging.info(
                    f"File {file.filename} indexed successfully, file_id = {file_id}"
                )
                return {
                    "message": f"File {file.filename} has been successfully uploaded and indexed!",
                    "file_id": file_id,
                }
            else:
                delete_document_record(file_id)
                raise HTTPException(
                    status_code=500, detail=f"Failed to index file {file.filename}"
                )
        finally:
            if os.path.exists(tmp_file_path):
                os.remove(tmp_file_path)
    except Exception as e:
        logging.error(f"Error in upload file: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))


@app.post("/upload-website")
async def upload_website(website: Dict = Body(...)):
    logging.info(f"Received website data: {website}")
    if "url" not in website:
        raise HTTPException(
            status_code=500, detail="Invalid input. URL not found in website data!"
        )
    try:
        url = website["url"]
        dtype = website["type"]
        logging.info(f"Processing website URL: {url} (type: {dtype})")
        domain = url.split("//")[-1].split("/")[0]
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        filename = f"{domain}_{timestamp}.html"
        content = scrape_website(url)
        tmp_file_path = f"tmp_{filename}"
        try:
            with open(tmp_file_path, "w", encoding="utf-8") as f:
                f.write(content)
            file_id = insert_document_records(filename)
            success = index_document_to_mongodb(url, file_id)
            if success:
                logging.info(f"Website {url} indexed successfully, file_id = {file_id}")
                return {
                    "message": f"Website {url} has been successfully scraped and indexed.",
                    "file_id": file_id,
                }
            else:
                delete_document_record(file_id)
                raise HTTPException(
                    status_code=500,
                    detail=f"Failed to index website content from {url}",
                )
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
    mongodb_delete_success = delete_doc_from_mongodb(request.file_id)
    if mongodb_delete_success:
        db_delete_success = delete_document_record(request.file_id)
        if db_delete_success:
            return {
                "message": f"Successfully deleted document with file_id {request.file_id} from the system."
            }
        else:
            return {
                "error": f"Deleted from MongoDB Atlas but failed to delete document with file_id {request.file_id} from the database."
            }
    else:
        return {
            "error": f"Failed to delete document with file_id {request.file_id} from MongoDB."
        }


@app.post("/upload-landmark-info")
async def upload_landmark_info(landmark_data: LandmarkInfoInput = Body(...)):
    logging.info(f"Received landmark data for: {landmark_data.name}")
    content_parts = []
    content_parts.append(f"Name: {landmark_data.name}")
    if landmark_data.description:
        content_parts.append(f"Description: {landmark_data.description}")
    if landmark_data.additionalInfo and landmark_data.additionalInfo.historicalEvents:
        content_parts.append("\nHistorical Events:")
        for event in landmark_data.additionalInfo.historicalEvents:
            content_parts.append(
                f"\n---\nTitle: {event.title}\nDescription: {event.description}"
            )
    content = "\n".join(content_parts)
    logging.info(content)
    sanitized_name = re.sub(r"[^\w\- ]", "", landmark_data.name)
    sanitized_name = re.sub(r"\s+", "_", sanitized_name).strip("_")
    if not sanitized_name:
        sanitized_name = f"landmark_{landmark_data.id_}"
    timestamp = datetime.now().strftime("%Y%m%d%H%M%S")
    tmp_filename = f"tmp_{sanitized_name}_{timestamp}.txt"
    tmp_file_path = tmp_filename
    logging.info(f"Aggregated content length: {len(content)} chars.")
    logging.info(f"Using temporary file path: {tmp_file_path}")
    file_id = None
    try:
        with open(tmp_file_path, "w", encoding="utf-8") as f:
            f.write(content)
        full_path = os.path.abspath(tmp_file_path)
        logging.info(full_path)
        file_id = insert_document_records(landmark_data.name + ".json_info")
        logging.info(
            f"Inserted document record for '{landmark_data.name}', file_id: {file_id}"
        )
        success = index_document_to_mongodb(full_path, file_id)
        if success:
            logging.info(
                f"Landmark info '{landmark_data.name}' (file_id: {file_id}) indexed successfully from temporary file."
            )
            return {
                "message": f"Landmark information for '{landmark_data.name}' has been successfully processed and indexed.",
                "file_id": file_id,
            }
        else:
            logging.error(
                f"Failed to index landmark info '{landmark_data.name}' (file_id: {file_id}) from {full_path}."
            )
            if file_id:
                delete_document_record(file_id)
                logging.info(
                    f"Rolled back document record insertion for file_id: {file_id}"
                )
            raise HTTPException(
                status_code=500,
                detail=f"Failed to index landmark information for '{landmark_data.name}'",
            )
    except Exception as e:
        logging.error(
            f"Error processing landmark info '{landmark_data.name}': {str(e)}",
            exc_info=True,
        )
        if file_id:
            try:
                delete_document_record(file_id)
                logging.info(
                    f"Rolled back document record insertion for file_id: {file_id} due to exception."
                )
            except Exception as del_e:
                logging.error(
                    f"Failed to rollback document record {file_id} after error: {del_e}"
                )
        raise HTTPException(
            status_code=500,
            detail=f"An error occurred processing landmark information: {str(e)}",
        )
    finally:
        if os.path.exists(tmp_file_path):
            try:
                os.remove(tmp_file_path)
                logging.info(f"Removed temporary file: {tmp_file_path}")
            except Exception as e:
                logging.error(
                    f"Error removing temporary file {tmp_file_path}: {str(e)}"
                )