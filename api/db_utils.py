import sqlite3
from datetime import datetime

DB_NAME = "rag_app.db"


"""
the get_db_connection function creates a connection to SQLite databse
and setting the row factory to sqlite3.Row to return rows as dictionaries (for easier data access)
"""
def get_db_connection():
    conn = sqlite3.connect(DB_NAME)
    # this configuration makes the rows returned by queries bahave like dictionaries,
    # allowing access to columns by name
    conn.row_factory = sqlite3.Row
    return conn

# Create the database tables
# application_logs: stores chat history and model responses
def create_application_logs():
    conn = get_db_connection()
    conn.execute("""
                 CREATE TABLE IF NOT EXISTS application_logs
                 (id INTEGER PRIMARY KEY AUTOINCREMENT,
                 session_id TEXT,
                 user_query TEXT,
                 llm_response TEXT,
                 model TEXT,
                 created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP)
                 """)
    conn.close()
    

# document_store: keeps track of uploaded documents
def create_document_store():
    conn = get_db_connection()
    conn.execute("""
                 CREATE TABLE IF NOT EXISTS document_store
                 (id INTEGER PRIMARY KEY AUTOINCREMENT,
                 filename TEXT,
                 upload_timestamp TIMESTAMP DEFAULT CURRENT_TIMESTAMP)
                 """)
    conn.close()
    
    

"""Managing chat logs
- insert_application_logs: inserts a chat log into the application_logs table
- get_chat_history: retrieves chat history for a given session_id
The chat history is formatted to be easily usable by our RAG system
"""

def insert_application_logs(session_id, user_query, llm_response, model):
    conn = get_db_connection()
    conn.execute('INSERT INTO application_logs \
        (session_id, user_query, llm_response, model) \
        VALUES (?, ?, ?, ?)', \
        (session_id, user_query, llm_response, model))
    conn.commit()
    conn.close()

    
def get_chat_history(session_id):
    conn = get_db_connection()
    cursor = conn.cursor()
    cursor.execute('SELECT user_query, llm_response FROM \
                   application_logs WHERE session_id = ? \
                       ORDER BY created_at', (session_id,))
    messages = []
    # cursor.fetchall() returns a list of dictionary, each tuple represents a row from the query result
    for row in cursor.fetchall():
        messages.extend([
            {"role": "human", "content": row['user_query']},
            {"role": "ai", "content": row['llm_response']}
        ])
    conn.close()
    return messages


"""
Managing document records
- insert_document_record: inserting new document records
- get_all_documents: retrieving all document records
- delete_document_record: deleting a document record
"""
def insert_document_record(filename: str):
    conn = get_db_connection()
    cursor = conn.cursor()
    cursor.execute('INSERT INTO document_store \
        (filename) VALUES (?)', (filename, ))
    file_id = cursor.lastrowid
    conn.commit()
    conn.close()
    return file_id


def delete_document_record(file_id: int):
    conn = get_db_connection()
    conn.execute('DELETE FROM document_store \
        WHERE id = (?)', (file_id, ))
    conn.commit()
    conn.close()
   

def get_all_documents():
    conn = get_db_connection()
    cursor = conn.cursor()
    cursor.execute("SELECT id, filename, upload_timestamp \
        FROM document_store ORDER BY upload_timestamp DESC")
    documents = cursor.fetchall()
    conn.close()
    return [dict(doc) for doc in documents]

"""Ensure tables are created when the application starts (if they don't already exist) by initializing databse tables
"""
create_application_logs()
create_document_store()