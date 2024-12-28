import streamlit as st
import random
import time
# from langchain_community.llms import LlamaCpp
from llama_index.llms.llama_cpp import LlamaCPP
# from llama_index.llms.llama_utils import messages_to_prompt, completion_to_prompt

from langchain import PromptTemplate
from langchain.callbacks.manager import CallbackManager
from langchain.callbacks.streaming_stdout import StreamingStdOutCallbackHandler
# from llama_index.llms.langchain import LangChainLLM

template = """
<s>[INST] <<SYS>>
Act as an Astronomer engineer who is teaching high school students.
<</SYS>>
 
{text} [/INST]
"""
 
prompt = PromptTemplate(
    input_variables=["text"],
    template=template,
)
# Callbacks support token-wise streaming
callback_manager = CallbackManager([StreamingStdOutCallbackHandler()])
model_path = "../models/llama-3.2-1b-instruct-q8_0.gguf"
llm = LlamaCPP(
    model_path=model_path,
    temperature=0.5,
    max_new_tokens=1024,
    context_window=3960,
    callback_manager=callback_manager,
    verbose=True,  # Verbose is required to pass to the callback manager
)
response_iter = llm.stream_complete("Can you write me a poem about fast cars?")
for response in response_iter:
    print(response.delta, end="", flush=True)