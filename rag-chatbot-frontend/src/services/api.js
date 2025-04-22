// this file centrializes all backend communication
// src/services/api.js
const API_BASE_URL = "http://localhost:8000"; // Your FastAPI backend URL

// Corresponds to get_api_response
export const getApiResponse = async (question, sessionId, model) => {
    const url = `${API_BASE_URL}/chat`;
    const headers = {
        accept: "application/json",
        "Content-Type": "application/json",  
    };
    const data = { question, model };
    if (sessionId) {
          data.sessionId = sessionId;
    }
    try {
        const response = await fetch (url , {
            method: "POST",
            headers: headers,
            body: JSON.stringify(data)
        });

        if (!response.ok) {
            const errorText = await response.text()
            throw new Error(`API request failed with status ${response.status}: ${errorText}`);
        }
        return await response.json();
    }
    catch (error) {
        console.error(`Error fetching API response: ${error}`)
        throw error;
    }
};

export const uploadDocument = async (inputData) => {
    let url;
    let options;

    // case 1: handle File Data
    if (inputData instanceof File) {
        url = `${API_BASE_URL}/upload-file`;
        const formData = new FormData();
        formData.append("file", inputData, inputData.name);
        options = {
            method: "POST",
            body: formData,
            // content-type header is set automatically by browser for formdata
        };
        console.log(`Uploading file: ${inputData.name}`);
    } 
    else if (
        typeof inputData === 'object' && inputData !== null && inputData.url
    ) {
        
        url = `${API_BASE_URL}/upload-website`;
        const headers = {
            accept: 'application/json',
            'Content-Type': 'application/json',
        };
        const body = { url: inputData.url, type: 'html'};
        options = {
            method: "POST",
            headers: headers,
            body: JSON.stringify(body),
        };
        console.log(`Upload website ${body}`);
    }
    else {
        throw new Error('Invalid input data type for uploadDocument');
    }

    try {
        console.log(url);
        const response = await fetch (url, options);
        console.log("Inside uploadDocument");
        if (!response.ok) {
            const errorText = await response.text();
            console.log('Error when uploading with response text: ', errorText);
            throw new Error(`Upload failed with status: ${response.status}: ${errorText}`);
        } 
        return await response.json();
    }
    catch (error) {
        console.log(`Error uploading documents (whether it's website or document): ${error}`)
        throw error;
    }
};


export const listDocuments = async () => {
    const url = `${API_BASE_URL}/list-docs`;
    try {
        const response = await fetch (url, {method: "GET"});
        if (!response.ok) {
            const errorText = await response.text()
            throw new Error(
              `Failed to fecth document list. Status ${response.status}: ${errorText}`
            );
        }
        const data = await response.json();
        console.log(data);
        return Array.isArray(data) ? data : []
    }
    catch (error) {
        console.error(`Error listing document: ${error}`);
        throw error;
    }
};

export const deleteDocument = async (fileId) => {
    const url = `${API_BASE_URL}/delete-doc`;
    const headers = {
      accept: "application/json",
      "Content-Type": "application/json",
    };
    const data = { file_id: fileId};

    try {
        const response = await fetch (url, {
            method: "POST",
            headers: headers,
            body: JSON.stringify(data)
        });
        if (!response.ok) {
            throw new Error(`Failed to delete document. Status ${response.status}: ${response.text}`);
        }
        return await response.json();
    }
    catch (error) {
        console.error("Erro deleting document: ", error);
        throw error;
    }
};
// Note: Streaming endpoint (`/stream`) is not implemented here for simplicity.
// Implementing streaming would require using EventSource or handling chunked responses.
