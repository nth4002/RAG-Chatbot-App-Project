from pydantic import BaseModel, Field
from enum import Enum
from datetime import datetime

# import os
# model_dir = os.path.join(os.pardir, "models")
# model_paths = [os.path.join(model_dir,model_path) for model_path in os.listdir(model_dir)]
# print(model_paths)
# print(model_paths[1])

"""
ModelName (Enum):
    - This enum defines the available language models for our RAG system.
    - Using an enum ensure only valid model names can be used
"""
class ModelName(str, Enum):
    # LLAMA_2_13B = "/home/feba6204/AI/RAG/gpt4all-master/models/llama2-13b-estopia.Q3_K_M.gguf"
    # LLAMA_PRO_8B = "/home/feba6204/AI/RAG/gpt4all-master/models/llama-pro-8b-instruct.Q5_K_M.gguf"
    # LLAMA_2_7B = "/home/feba6204/AI/RAG/gpt4all-master/models/llama-2-7b.Q4_K_M.gguf"
    # LLAMA_3_1B = "/home/feba6204/AI/RAG/gpt4all-master/models/llama-3.2-1b-instruct-q8_0.gguf"
    # LLAMA_3B = "Llama-3.2-3B-Instruct-Q4_0.gguf"
    # LLAMA_13B = "llama-2-13b-chat.Q4_0.gguf"
    # NOUS_HERMES_2 = "Nous-Hermes-2-Mistral-7B-DPO.Q4_0.gguf"
    GEMINI_PRO = "gemini-1.5-pro"
    GEMINI_FLASH = "gemini-1.5-flash"
    GEMINI_2 = "gemini-2.0-flash-001"
    
    
    
"""
QueryInput:  represents the input for a chat query
    - question: the user's question (required)
    - session_id: optional session id. If not provided, one will be generated
    - model: the language model to use. Default is LLAMA_3B
"""
class QueryInput(BaseModel):
    question: str
    session_id: str = Field(default=None)
    model: ModelName = Field(default=ModelName.GEMINI_PRO)
    
"""
QueryResponse: represents the response to a chat query
    - answer: the string response as generated answer
    - session_id: the session id (it's useful for continuing conversations)
    - model: the model used to genrate the response
"""
class QueryResponse(BaseModel):
    answer: str
    session_id: str
    model: ModelName
    
    
    
"""
DocumentINfo: represents metadata about an indexed document
    - id: Unique identifier for the document
    - filename: name of the file uploaded by the user
    - upload_timestamp: the timestamp when the file was uploaded and indexed
"""
class DocumentInfo(BaseModel):
    id: int
    filename: str
    upload_timestamp: datetime
    


"""
DeleteFileRequest: represents the request to delete an indexed document
    - file id: the id of the document that is requested to be deleted
""" 
class DeleteFileRequest(BaseModel):
    file_id: int
    