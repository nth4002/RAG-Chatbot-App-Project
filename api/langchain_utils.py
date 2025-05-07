from langchain_google_genai import ChatGoogleGenerativeAI
from langchain_core.output_parsers import StrOutputParser
from langchain_core.prompts import ChatPromptTemplate, MessagesPlaceholder
from langchain.chains import create_history_aware_retriever, create_retrieval_chain
from langchain.chains.combine_documents import create_stuff_documents_chain

from langchain_mongodb import MongoDBChatMessageHistory
from langchain_core.runnables.history import RunnableWithMessageHistory
from langchain_core.retrievers import BaseRetriever 

import os
import logging
from dotenv import load_dotenv, find_dotenv
from vector_store_utils import vector_store # vector_store is used in main.py to create the retriever


# import API key, DB name and collection
from new_db_util import (
    DB_NAME,
    MONGODB_ATLAS_CLUSTER_URI_2,
    # ATLAS_VECTOR_SEARCH_INDEX_NAME, # Not directly used here
    LOG_COLLECTION_NAME
)

load_dotenv(find_dotenv(), override=True)
GOOGLE_API_KEY = os.environ.get("GOOGLE_API_KEY")

# The global 'retriever' definition is no longer the primary one for get_rag_chain
# if main.py always passes a configured retriever.
# You can remove it, or rename it e.g., 'default_global_retriever' if needed elsewhere.
# For this change, main.py will construct the retriever.
# retriever = vector_store.as_retriever(
#     search_type="similarity_score_threshold",
#     search_kwargs={"k": 8, "score_threshold": 0.4},
# )

output_parser = StrOutputParser() # This is fine

# Logging setup is fine
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
)

# Prompts are fine
contextualize_q_system_prompt = (
    "Với lịch sử trò chuyện và câu hỏi mới nhất của người dùng, "
    "câu hỏi có thể tham chiếu đến ngữ cảnh trong lịch sử trò chuyện, "
    "hãy xây dựng một câu hỏi độc lập có thể hiểu được"
    "mà không cần lịch sử trò chuyện. KHÔNG trả lời câu hỏi, "
    "chỉ cần xây dựng lại câu hỏi nếu cần và nếu không thì giữ nguyên câu hỏi như hiện tại."
)

contextualize_q_prompt = ChatPromptTemplate.from_messages([ # Corrected: from_messages instead of ChatPromptTemplate([...])
    ("system", contextualize_q_system_prompt),
    MessagesPlaceholder("chat_history"),
    ("human", "{input}"),
])

system_prompt = (
    "Bạn là trợ lý cho các nhiệm vụ trả lời câu hỏi. "
    "Sử dụng các phần ngữ cảnh sau đây để trả lời "
    "câu hỏi. Các câu hỏi sẽ liên quan với nhau hoặc có trong ngữ cảnh. " # Added a period for clarity
    "Nếu bạn không biết câu trả lời, hãy nói rằng bạn "
    "không biết. Sử dụng tối đa ba câu và giữ cho câu trả lời ngắn gọn nhưng đầy đủ nội dung. "
    "Nếu người dùng cảm thán hoặc nói chuyện bình thường mà không hỏi gì, "
    "hoặc nói chuyện hay hỏi câu hỏi không liên quan, "
    "hãy trả lời theo ý của bạn một cách lịch sự nhất có thể."
     "\n\n"
    "{context}"
)

qa_prompt = ChatPromptTemplate.from_messages( # Corrected: from_messages
    [
        ("system", system_prompt),
        MessagesPlaceholder("chat_history"),
        ("human", "{input}"),
    ]
)

# get_session_history is fine
def get_session_history(session_id: str) -> MongoDBChatMessageHistory:
    history = MongoDBChatMessageHistory(
        connection_string=MONGODB_ATLAS_CLUSTER_URI_2,
        session_id = session_id,
        create_index=True, # Be cautious with create_index=True in a per-request function
                           # Ensure it's idempotent or handled correctly by MongoDB driver.
                           # Usually, index creation is a one-time setup.
        database_name=DB_NAME,
        collection_name=LOG_COLLECTION_NAME,
    )
    return history


# Modified get_rag_chain
def get_rag_chain(model_name: str, retriever_to_use: BaseRetriever):
    """
    Creates a RAG chain with the specified model and retriever.

    Args:
        model_name (str): The name of the language model to use (e.g., "gemini-1.5-flash-latest").
        retriever_to_use (BaseRetriever): The retriever instance configured for the request
                                          (e.g., with or without heritage_id filter).
    Returns:
        A RunnableWithMessageHistory instance representing the conversational RAG chain.
    """
    llm = ChatGoogleGenerativeAI(model=model_name, google_api_key=GOOGLE_API_KEY, temperature=0.2) # Added temperature from your main.py example

    # Use the retriever_to_use passed as an argument
    history_aware_retriever = create_history_aware_retriever(
        llm,
        retriever_to_use,
        contextualize_q_prompt
    )
    question_answer_chain = create_stuff_documents_chain(llm, qa_prompt)
    rag_chain = create_retrieval_chain(history_aware_retriever, question_answer_chain)
    
    conversational_rag_chain = RunnableWithMessageHistory(
        rag_chain,
        get_session_history,
        input_messages_key="input",
        history_messages_key="chat_history",
        output_messages_key="answer",
    )

    return conversational_rag_chain