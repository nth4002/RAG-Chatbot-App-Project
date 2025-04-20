# the file contains functions for interacting with FastAPI backend
from io import BytesIO
from streamlit.runtime.uploaded_file_manager import UploadedFile
from typing import Union, Dict
import requests
import streamlit as st

def streaming_testing(query: str):
    try:
        # the stream parameter tells the requests library to keep the connection open and stream the response data 
        # Streaming: iter_lines reads the response incrementally
        # Decoding: each chunk is decoded as a line of text
        # Buffering: it buffers the response content and yields lines as they are received
        place_holder = st.empty()
        url = f"http://localhost:8000/stream"
        query_params = {"query": query}
        answer_stream = ""
        response = requests.get(url, params=query_params, stream=True)
        for chunk in response.iter_content(chunk_size=None, decode_unicode=True):
            if chunk:
                answer_stream += chunk
                place_holder.markdown(answer_stream)
    except Exception as e:
        st.error(f"An error occurred: {str(e)}")
        
def get_api_response(question, session_id, model):
    headers = {'accept': 'application/json', 'Content-Type': 'application/json'}
    data = {'question': question, 'model': model}
    if session_id:
        data['session_id'] = session_id
    
    try:
        response = requests.post("http://localhost:8000/chat", headers=headers, json=data)
        if response.status_code == 200:
            return response.json()
        else:
            st.error(f"API request failed with status code {response.status_code}: {response.text}")
            return None
    except Exception as e:
        st.error(f"an error occurred: {str(e)}")
        return None
    

def upload_document(input_data: Union[UploadedFile, Dict, BytesIO]):
    """
    Upload either a file or website URL to the backend.
    
    Args:
        input_data: Either a Streamlit UploadedFile, BytesIO, or a dictionary containing website URL
        
    Returns:
        dict: Response from the server or None if upload fails
    """
    try:
        if isinstance(input_data, dict) and 'url' in input_data:
            # Handle website URL
            headers = {
                'accept': 'application/json',
                'Content-Type': 'application/json'
            }
            
            print("Sending website data to endpoint:")
            print(f"Headers: {headers}")
            print(f"Data: {input_data}")
            
            response = requests.post(
                "http://localhost:8000/upload-website",
                headers=headers,
                json=input_data  # No wrapping needed
            )
        elif isinstance(input_data, (UploadedFile, BytesIO)):
            # Handle file upload
            if isinstance(input_data, UploadedFile):
                file_name = input_data.name
                file_type = input_data.type
                file_content = input_data.getvalue()
            else:
                file_name = "uploaded_file"
                file_type = "application/octet-stream"
                file_content = input_data
                
            print(f"File upload: name={file_name}, type={file_type}")
            files = {"file": (file_name, file_content, file_type)}
            response = requests.post(
                "http://localhost:8000/upload-file",
                files=files
            )
        else:
            raise ValueError(f"Invalid input_data type: {type(input_data)}")

        if response.status_code == 200:
            return response.json()
        else:
            error_msg = "Failed to upload website" if isinstance(input_data, dict) else "Failed to upload file"
            st.error(f"{error_msg}. Error: {response.status_code} - {response.text}")
            print(f"Response content: {response.text}")
            return None

    except Exception as e:
        error_msg = "An error occurred while processing the website" if isinstance(input_data, dict) else "An error occurred while uploading the file"
        st.error(f"{error_msg}: {str(e)}")
        print(f"Exception details: {str(e)}")
        return None
    
    
def list_documents():
    try:
        response = requests.get("http://localhost:8000/list-docs")
        if response.status_code == 200:
            return response.json()
        
        else:
            st.error(f"failed to fetch document list. Error {response.status_code} - {response.text}")
            return []
    except Exception as e:
        st.error(f"Error occured while fetching the document list: {str(e)}")
        return []
    
def delete_document(file_id: int):
    headers = {'accept': 'application/json', 'Content-Type': 'application/json'}
    data = {'file_id': file_id}
    
    try:
        response = requests.post("http://localhost:8000/delete-doc", headers=headers, json=data)
        if response.status_code == 200:
            return response.json()
        else:
            st.error(f"Failed to delete document. Error: {response.status_code} - {response.text}")
            return None
        
    except Exception as e:
        st.error(f"An error occurred while deleting the document: {str(e)}")
        return None