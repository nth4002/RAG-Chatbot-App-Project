import streamlit as st
from api_utils import get_api_response
from api.pydantic_models import ModelName

def display_chat_interface():
    # Display entire chat history
    # st.write(f"model = {st.session_state.model}")
    for message in st.session_state.messages:
        with st.chat_message(message["role"]):
            st.markdown(message["content"])

    # Handle new user input
    if prompt := st.chat_input("Query:"):
        st.session_state.messages.append({"role": "user", "content": prompt})
        with st.chat_message("user"):
            st.markdown(prompt)
        
        # GET API response
        with st.spinner("Generating response..."):
            response = get_api_response(prompt, st.session_state.session_id, st.session_state.model)
            
            # if response is not None
            # response includes 
            if response:
                st.session_state.session_id = response.get("session_id")
                st.session_state.messages.append({"role": "assistant", "content": response['answer']})
                
                # show the response
                with st.chat_message("assistant"):
                    st.markdown(response['answer'])
                
                # additional details about response
                with st.expander("Details"):
                    st.subheader("Generated Answer")
                    st.code(response['answer'])
                    st.subheader("Model Used")
                    st.code(response['model'])
                    st.subheader("Session ID")
                    st.code(response['session_id'])
                    
            else:
                st.error("failed to get a response from the API. Please try again.")
                    
                    