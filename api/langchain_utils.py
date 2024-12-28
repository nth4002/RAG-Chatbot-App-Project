from langchain_google_genai import ChatGoogleGenerativeAI
from langchain_core.output_parsers import StrOutputParser
from langchain_core.prompts import ChatPromptTemplate, MessagesPlaceholder
from langchain.chains import create_history_aware_retriever, create_retrieval_chain
from langchain.chains.combine_documents import create_stuff_documents_chain
from typing import List
from langchain_core.documents import Document
import os
import logging
from dotenv import load_dotenv
load_dotenv()
GOOGLE_API_KEY = os.environ.get("GOOGLE_API_KEY")

from chroma_utils import vectorstore
retriever = vectorstore.as_retriever(search_kwargs={"k": 2})

output_parser = StrOutputParser()

# logging.basicConfig(filename="app.log", level=logging.INFO)


# llm = ChatGoogleGenerativeAI(model="gemini-1.5-pro", google_api_key=GOOGLE_API_KEY)

# Set up prompts and chains
contextualize_q_system_prompt = (
    "Given a chat history and the latest user question "
    "which might reference context in the chat history, "
    "formulate a standalone question which can be understood "
    "without the chat history. Do NOT answer the question, "
    "just reformulate it if needed and otherwise return it as is."
)

contextualize_q_prompt = ChatPromptTemplate.from_messages([
    ("system", contextualize_q_system_prompt),
    MessagesPlaceholder("chat_history"),
    ("human", "{input}"),
])

# history_aware_retriever = create_history_aware_retriever(
#     llm, retriever, contextualize_q_prompt
# )

# qa_prompt = ChatPromptTemplate.from_messages([
#     ("ai", "You are a helpful AI assistant. Use the following context to answer the user's question."),
#     ("ai", "Context: {context}"),
#     MessagesPlaceholder(variable_name="chat_history"),
#     ("human", "{input}")
# ])

# question_answer_chain = create_stuff_documents_chain(llm, qa_prompt)
# rag_chain = create_retrieval_chain(history_aware_retriever, question_answer_chain)

# # 'chat_history': list[typing.Annotated[typing.Union[typing.Annotated[langchain_core.messages.ai.AIMessage, Tag(tag='ai')], typing.Annotated[langchain_core.messages.human.HumanMessage, Tag(tag='human')]
# from langchain_core.messages import HumanMessage, AIMessage

# chat_history = []
# question1 = "When was GreenGrow Innovations founded?"
# answer1 = rag_chain.invoke({"input": question1, "chat_history": chat_history})['answer']
# chat_history.extend([
#     HumanMessage(content=question1),
#     AIMessage(content=answer1)
# ])

# print(f"Human: {question1}")
# print(f"AI: {answer1}\n")

# question2 = "Where is it headquartered?"
# answer2 = rag_chain.invoke({"input": question2, "chat_history": chat_history})['answer']
# chat_history.extend([
#     HumanMessage(content=question2),
#     AIMessage(content=answer2)
# ])

# print(f"Human: {question2}")
# print(f"AI: {answer2}")
qa_prompt = ChatPromptTemplate.from_messages([
    ("ai", "You are a helpful AI assistant. Use the following context to answer the user's question."),
    ("ai", "Context: {context}"),
    MessagesPlaceholder(variable_name="chat_history"),
    ("human", "{input}")
])



def get_rag_chain(model="gemini-1.5-flash"):
    llm = ChatGoogleGenerativeAI(model=model, google_api_key=GOOGLE_API_KEY)
    history_aware_retriever = create_history_aware_retriever(llm, retriever, contextualize_q_prompt)
    question_answer_chain = create_stuff_documents_chain(llm, qa_prompt)
    rag_chain = create_retrieval_chain(history_aware_retriever, question_answer_chain)    
    return rag_chain