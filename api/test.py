# test_mongo_connect.py
import os
from pymongo import MongoClient
from dotenv import load_dotenv, find_dotenv

load_dotenv(find_dotenv()) # Load .env from current dir
MONGODB_ATLAS_CLUSTER_URI_2 = os.getenv("MONGODB_ATLAS_CLUSTER_URI_2")
client = MongoClient(
    MONGODB_ATLAS_CLUSTER_URI_2
)
DB_NAME = "Chatbot-Database-Cluster"
# CHATBOT_COLLECTION_NAME = "Chatbot-Database-Collection"
ATLAS_VECTOR_SEARCH_INDEX_NAME = "Chatbot-Database-Index"
LOG_COLLECTION_NAME = "application_logs"
DOC_COLLECTION_NAME = "document_store"
# CHATBOT_COLLECTION = client[DB_NAME][CHATBOT_COLLECTION_NAME]
db = client[DB_NAME]
logs_collection = db[LOG_COLLECTION_NAME]
documents_collection = db[DOC_COLLECTION_NAME]

if not MONGODB_ATLAS_CLUSTER_URI_2:
    print("ERROR: Connection string is not set in environment.")
else:
    try:
        client = MongoClient(MONGODB_ATLAS_CLUSTER_URI_2)
        # The ismaster command is cheap and does not require auth.
        # client.admin.command('ismaster')
        # print("Initial connection successful (ismaster command ok).")

        # Attempt an operation that requires auth, like listing collections in the target DB
        db = client[DB_NAME]
        print(f"Listing collections in '{DB_NAME}':")
        collections = db.list_collection_names()
        print(collections)

        # Try a basic find_one on the target collection
        print(f"Attempting find_one on '{DOC_COLLECTION_NAME}'...")
        doc = db[DOC_COLLECTION_NAME].find_one()
        print(f"find_one result (sample): {doc}")

        print("\nAuthentication and basic operation successful!")

    except Exception as e:
        print(f"\nConnection or Authentication FAILED: {e}")
    finally:
        if 'client' in locals() and client:
            client.close()
            print("Connection closed.")