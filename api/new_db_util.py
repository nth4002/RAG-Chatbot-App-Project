from datetime import datetime
from pymongo import MongoClient
from bson.objectid import ObjectId
import os

MONGODB_ATLAS_CLUSTER_URI_2 = os.getenv("MONGODB_ATLAS_CLUSTER_URI_2")
client = MongoClient(
    MONGODB_ATLAS_CLUSTER_URI_2
)
DB_NAME = "Chatbot-Database-Cluster"
COLLECTION_NAME = "Chatbot-Database-Collection"
ATLAS_VECTOR_SEARCH_INDEX_NAME = "Chatbot-Database-Index"

CHATBOT_COLLECTION = client[DB_NAME][COLLECTION_NAME]
db = client["rag_chatbot_app"]
logs_collection = db["application_logs"]
documents_collection = db['document_store']

# managing chat logs
def insert_application_logs(session_id, user_query, llm_response, model):
    log_entry = {
        "session_id": session_id,
        "user_query": user_query,
        "llm_response": llm_response,
        "model": model,
        "created_at": datetime.now()
    }
    logs_collection.insert_one(log_entry)

def get_chat_history(session_id):
    logs = logs_collection.find({"session_id": session_id}).sort("created_at", 1)
    messages = []
    for log in logs:
        messages.extend([
            {"role": "human", "content": log['user_query']},
            {"role": "ai", "content": log['llm_response']}
        ])
    return messages

# managing document records
def insert_document_records(filename: str):
    document = {
        "filename": filename,
        "upload_timestamp": datetime.now()
    }
    result = documents_collection.insert_one(document)
    return str(result.inserted_id)

def delete_document_record(file_id: str):
    documents_collection.delete_one({"_id": ObjectId(file_id) })

def get_all_documents():
    documents = documents_collection.find().sort("upload_timestamp", -1)
    return [
        {
            "id": str(doc["_id"]),
            "filename": doc["filename"],
            "upload_timestamp": doc['upload_timestamp']
        }
        for doc in documents
    ]

def delete_logs_and_documents_collections():
    result1 = documents_collection.delete_many({})
    result2 = logs_collection.delete_many({})
    return {
        "documents_deleted": result1.deleted_count,
        "metadata_deleted": result2.deleted_count
    }