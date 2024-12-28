# the file contains functions for interacting with FastAPI backend
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
    

def upload_document(file):
    # file: UploadedFile for streamlit
    # The UploadedFile class is a subclass of BytesIO, 
    # and therefore is "file-like". This means you can pass
    # an instance of it anywhere a file is expected.
    try:
        files = {"file": (file.name, file, file.type)}
        response = requests.post("http://localhost:8000/upload-doc", files=files)
        if response.status_code == 200:
            return response.json()
        
        else:
            st.error(f"Failed to upload file. Error: {response.status_code} - {response.text}")
            return None
        
    except Exception as e:
        st.error(f"An error occurred while uploading the file: {str(e)}")
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