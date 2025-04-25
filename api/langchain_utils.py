from langchain_google_genai import ChatGoogleGenerativeAI
from langchain_core.output_parsers import StrOutputParser
from langchain_core.prompts import ChatPromptTemplate, MessagesPlaceholder
from langchain.chains import create_history_aware_retriever, create_retrieval_chain
from langchain.chains.combine_documents import create_stuff_documents_chain
from typing import List
from langchain_core.documents import Document

from langchain_mongodb import MongoDBChatMessageHistory
from langchain_community.chat_message_histories import ChatMessageHistory
# from langchain_core.chat_history import BaseChatMessageHistory
from langchain_core.runnables.history import RunnableWithMessageHistory

import os
import logging
from dotenv import load_dotenv, find_dotenv
from vector_store_utils import vector_store


# import API key, DB name and collection
from new_db_util import (
    DB_NAME,
    MONGODB_ATLAS_CLUSTER_URI_2,
    ATLAS_VECTOR_SEARCH_INDEX_NAME, 
    LOG_COLLECTION_NAME
)

load_dotenv(find_dotenv(), override=True)
GOOGLE_API_KEY = os.environ.get("GOOGLE_API_KEY")

retriever = vector_store.as_retriever(
    search_type="similarity_score_threshold",
    search_kwargs={"k": 8, "score_threshold": 0.4},
)
output_parser = StrOutputParser()

# logging.basicConfig(filename="rag_chatbot_app.log", level=logging.INFO)
#W setup logging for containerized app
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s', # Example format
    # No filename argument - defaults to stderr
)


# Set up prompts and chains
# contextualize_q_system_prompt = (
#     "Given a chat history and the latest user question "
#     "which might reference context in the chat history, "
#     "formulate a standalone question which can be understood "
#     "without the chat history. Do NOT answer the question, "
#     "just reformulate it if needed and otherwise return it as is."
# )

contextualize_q_system_prompt = (
    "Với lịch sử trò chuyện và câu hỏi mới nhất của người dùng, "
    "câu hỏi có thể tham chiếu đến ngữ cảnh trong lịch sử trò chuyện, "
    "hãy xây dựng một câu hỏi độc lập có thể hiểu được"
    "mà không cần lịch sử trò chuyện. KHÔNG trả lời câu hỏi, "
    "chỉ cần xây dựng lại câu hỏi nếu cần và nếu không thì giữ nguyên câu hỏi như hiện tại."
)

contextualize_q_prompt = ChatPromptTemplate([
    ("system", contextualize_q_system_prompt),
    MessagesPlaceholder("chat_history"),
    ("human", "{input}"),
])

# system_prompt = (
#     "You are an assistant for question-answering tasks. "
#     "Use the following pieces of retrieved context to answer "
#     "the question. If you don't know the answer, say that you "
#     "don't know. Use three sentences maximum and keep the "
#     "answer concise."
#     "\n\n"
#     "{context}"
# )

system_prompt = (
    "Bạn là trợ lý cho các nhiệm vụ trả lời câu hỏi. "
    "Sử dụng các phần ngữ cảnh sau đây để trả lời "
    "câu hỏi. Các câu hỏi sẽ liên quan với nhau hoặc có trong ngữ cảnh"
    "Nếu bạn không biết câu trả lời, hãy nói rằng bạn "
    "không biết. Sử dụng tối đa ba câu và giữ cho câu trả lời ngắn gọn nhưng đầy đủ nội dung."
    "Nếu người dùng cảm thán hoặc nói chuyện bình thường mà không hỏi gì,"
    "hoặc nói chuyện hay hỏi câu hỏi không liên quan,"
    "hãy trả lời theo ý của bạn một cách lịch sự nhất có thể."
     "\n\n"
    "{context}"
)

qa_prompt = ChatPromptTemplate(
    [
        ("system", system_prompt),
        MessagesPlaceholder("chat_history"),
        ("human", "{input}"),
    ]
)


def get_session_history(session_id: str) -> MongoDBChatMessageHistory:
    history = MongoDBChatMessageHistory(
        connection_string=MONGODB_ATLAS_CLUSTER_URI_2,
        session_id = session_id,
        create_index=True,
        database_name=DB_NAME,
        collection_name=LOG_COLLECTION_NAME,
    )
    return history


def get_rag_chain(model="gemini-2.0-flash-001"):
    llm = ChatGoogleGenerativeAI(model=model, google_api_key=GOOGLE_API_KEY)
    history_aware_retriever = create_history_aware_retriever(llm, retriever, contextualize_q_prompt)
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

