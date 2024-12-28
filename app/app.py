import streamlit as st
from sidebar import display_sidebar
from chat_interface import display_chat_interface
from api_utils import streaming_testing

st.title("Langchain RAG chatbot")

# Initialize session state variables
if "messages" not in st.session_state:
    # messages stores the chat history
    st.session_state.messages = []

if "session_id" not in st.session_state:
    # session_id is used to keep track of the current chat session
    st.session_state['session_id'] = None
    
# display sidebar
display_sidebar()

# st.write("Testing ...")
# query = "Write the python code to calculate the area of the following shapes: circle, rectangle and triangle."
# streaming_testing(query)
# display the chat interface
display_chat_interface()
# print("Testin successfully!")

