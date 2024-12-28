from fastapi import FastAPI, File, UploadFile, HTTPException
from pydantic_models import QueryInput, QueryResponse, DocumentInfo, DeleteFileRequest
from langchain_utils import get_rag_chain
from db_utils import insert_application_logs, get_chat_history, get_all_documents, insert_document_record, delete_document_record
from chroma_utils import index_document_to_chroma, delete_doc_from_chroma
import os
import uuid
import logging
import os
import shutil


logging.basicConfig(filename='app.log', level=logging.INFO)
app = FastAPI()

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

@app.post("/upload-doc")
def upload_and_index_document(file: UploadFile = File(...)):
    # this function receives a file which is UploadedFile type in streamlit
    # and then is converted to UploadFile type in FastAPI
    """
    UploadFile has following attributes:
    - filename: str
    - file: A SpooledTemporaryFile object (file-like object) (Binary IO object)
    """
    allowed_extensions = ['.pdf', '.docx', '.html']
    # split pathname into root and extension and returned as tuple
    file_extension = os.path.splitext(file.filename)[1].lower()
    
    if file_extension not in allowed_extensions:
        raise HTTPException(status_code=400, detail=f"Unsupported file type. Allowed types are: {', '.join(allowed_extensions)}")
    
    # a temporary file path to save the upload file
    temp_file_path = f"temp_{file.filename}"
    
    try:
        # Save the uploaded file to a temporary file
        with open(temp_file_path, "wb") as buffer:
            shutil.copyfileobj(file.file, buffer)
        
        # insert into sqlite3 database and get the id returned
        file_id = insert_document_record(file.filename)
        # append the document to the chroma vectorstore with the file_id (success is a boolean)
        success = index_document_to_chroma(temp_file_path, file_id)
        
        if success:
            return {"message": f"File {file.filename} has been successfully uploaded and indexed.", "file_id": file_id}
        else:
            # if not succeeded, delete the document record from sqlite3 database
            delete_document_record(file_id)
            raise HTTPException(status_code=500, detail=f"Failed to index {file.filename}.")
    finally:
        # remove the temporary file on computer for saving memory
        if os.path.exists(temp_file_path):
            os.remove(temp_file_path)

@app.get("/list-docs", response_model=list[DocumentInfo])
def list_documents():
    return get_all_documents()

@app.post("/delete-doc")
def delete_document(request: DeleteFileRequest):
    # Delete from Chroma
    chroma_delete_success = delete_doc_from_chroma(request.file_id)

    if chroma_delete_success:
        # If successfully deleted from Chroma, delete from our sqlite3 database
        db_delete_success = delete_document_record(request.file_id)
        if db_delete_success:
            return {"message": f"Successfully deleted document with file_id {request.file_id} from the system."}
        else:
            return {"error": f"Deleted from Chroma but failed to delete document with file_id {request.file_id} from the database."}
    else:
        return {"error": f"Failed to delete document with file_id {request.file_id} from Chroma."}