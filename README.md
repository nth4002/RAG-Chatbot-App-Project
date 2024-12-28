# RAG-Chatbot
This repository is used for experimenting to get more insights in RAG-Chatbot. This RAG features in store chat history of conversation
by configuring the prompt for RAG chain.
Feel free to download and playing around with it

## Getting Started

### Dependencies

All the dependencies and packages needed is listed in `requirements.txt`

### Usage

Follow these steps to set up and run the project:

1. Create a virtual environment:
```
python3 -m venv my_env
source my_env/bin/activate 
```

2. Install dependencies:
```
pip install -r requirements.txt
```

3. Run the application:
- Inside app folder:
```
streamlit run app_chat.py
```
- Inside api folder:
```
uvicorn main:app --reload
```

4. Access the application in your browser at  http://localhost:8501

5. Start a conversation with the chatbot!

## How it Works

The app as follows:

1. The user first choose a model before beginning chat (`gemini-1.5-pro by default`).

2. User have to upload the document It then will be index and store into the database and vectorstore.

3. Start chatting by input your query.

4. The Gemini model generates a response from documents it has retrieved from the vectorstore combining with query.

5. The chat history will be saved for answering the next query.

6. A new chat is created if the user initiates a conversation that hasn't been stored before, or user can go back to past chats.
