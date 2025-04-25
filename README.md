# RAG-Chatbot
This repository is used for experimenting to get more insights in RAG-Chatbot. This RAG features in store chat history of conversation
by configuring the prompt for RAG chain.
Feel free to download and playing around with it

## Getting Started (development)

### Dependencies

All the dependencies and packages needed is listed in `requirements.txt`

### Usage

Follow these steps to set up and run the project:

1. Create a virtual environment:
```
python3 -m venv venv
source venv/bin/activate 
```

2. Install dependencies:
```
pip install -r requirements.txt
```

3. Run the application:
- Inside rag-chatbot-frontend folder, run the following command and it will start the UI at http://localhost:3000/
```
npm start
```
- Inside api folder run the following code and it will start the server at http://127.0.0.1:8000
```
uvicorn main:app --reload
```

4. Access the application in your browser at  http://localhost:3000/

5. Start a conversation with the chatbot!

## Getting Started (deploying)
3. Run the application:
- Using docker by running the following command:
``
docker-compose up --build
```

- If Docker tries to reuse existing containers by default, run the following commands:
```
docker-compose down --remove-orphans
docker image prune -f
docker-compose up --build
```

- Access the website at: http://localhost:3000/
## How it Works

The app as follows:

1. The user first choose a model before beginning chat (`gemini-1.5-flash by default`).

2. User have to upload the document It then will be index and store into the database and vectorstore.

3. Start chatting by input your query.

4. The Gemini model generates a response from documents it has retrieved from the vectorstore combining with query.

5. The chat history will be saved for answering the next query.

6. A new chat is created if the user initiates a conversation that hasn't been stored before, or user can go back to past chats.


## Video Demo
[Video](https://drive.google.com/file/d/1rETmluxpHvyJzpO2iYlWnxwNMzvhr7uY/view?usp=sharing)
