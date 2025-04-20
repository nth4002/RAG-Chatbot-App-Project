# The sidebar handles document management and model selection
import os, sys
my_folder = os.path.abspath(os.path.join(os.pardir, 'api'))
sys.path.append(my_folder)
sys.path.append(os.path.abspath(os.pardir))
import streamlit as st
from api_utils import upload_document, list_documents, delete_document

def display_sidebar():
    # Sidebar: Model Selection
    model_options = ["gemini-1.5-pro", "gemini-1.5-flash"]
    st.sidebar.selectbox("Select Model", options=model_options, key="model")
    
    # Sidebar: Document Upload Section
    st.sidebar.header("Add Document")
    
    # Add tabs for different input methods
    upload_tab, url_tab = st.sidebar.tabs(["File Upload", "Website URL"])
    
    with upload_tab:
        uploaded_file = st.file_uploader("Upload PDF or DOCX", type=["pdf", "docx"])
        if uploaded_file is not None:
            if st.button("Upload File"):
                with st.spinner("Uploading..."):
                    upload_response = upload_document(uploaded_file)
                    if upload_response:
                        st.success(f"File '{uploaded_file.name}' uploaded successfully with ID {upload_response['file_id']}.")
                        st.session_state.documents = list_documents()
    
    with url_tab:
        website_url = st.text_input("Enter Website URL", placeholder="https://example.com")
        if website_url:
            if st.button("Scrape and Upload"):
                with st.spinner("Scraping and processing website..."):
                    try:
                        website_data = {'url': website_url, 'type': 'html'}
                        print(f"Sending website_data from sidebar: {website_data}")
                        upload_response = upload_document(website_data)
                        if upload_response:
                            st.success(f"Website content uploaded successfully with ID {upload_response['file_id']}.")
                            st.session_state.documents = list_documents()
                    except Exception as e:
                        st.error(f"Error processing website: {str(e)}")

    # Sidebar: List Documents
    st.sidebar.header("Uploaded Documents")
    if st.sidebar.button("Refresh Document List"):
        with st.spinner("Refreshing..."):
            st.session_state.documents = list_documents()

    # Initialize document list if not present
    if "documents" not in st.session_state:
        st.session_state.documents = list_documents()

    documents = st.session_state.documents
    if documents:
        # Create a container for scrollable document list
        with st.sidebar.container():
            for doc in documents:
                # Display document info in a more compact format
                doc_type = "Website" if doc.get('type') == 'html' else "Document"
                st.text(f"{doc['filename']} ({doc_type})")
                st.text(f"ID: {doc['id']}")
                st.text(f"Uploaded: {doc['upload_timestamp']}")
                st.divider()
        
        # Delete Document
        selected_file_id = st.sidebar.selectbox(
            "Select a document to delete", 
            options=[doc['id'] for doc in documents], 
            format_func=lambda x: next(doc['filename'] for doc in documents if doc['id'] == x)
        )
        
        if st.sidebar.button("Delete Selected Document"):
            with st.spinner("Deleting..."):
                delete_response = delete_document(selected_file_id)
                if delete_response:
                    st.sidebar.success(f"Document with ID {selected_file_id} deleted successfully.")
                    st.session_state.documents = list_documents()  # Refresh the list after deletion
                else:
                    st.sidebar.error(f"Failed to delete document with ID {selected_file_id}.")