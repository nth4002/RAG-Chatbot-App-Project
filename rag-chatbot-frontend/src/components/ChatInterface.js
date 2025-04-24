// src/components/ChatInterface.js
import React, { useState, useEffect, useRef } from "react";
// *** Import the new API function ***
import { getApiResponse, getChatHistory } from "../services/api";
import UserIcon from "../icons/UserIcon";
import ChatbotIcon from "../icons/ChatbotIcon";
import "./ChatInterface.css";

// *** Receive new props: messages, setMessages, responseDetails, setResponseDetails ***
function ChatInterface({
  selectedModel,
  sessionId,
  onSessionIdChange,
  messages,
  setMessages,
  responseDetails,
  setResponseDetails
}) {
  
    
    const [userInput, setUserInput] = useState("");
    const [isLoading, setIsLoading] = useState(false);
    const [error, setError] = useState(null);
    // const [responseDetails, setResponseDetails] = useState(null);
    const messagesEndRef = useRef(null);

    // --- Effect to scroll to bottom (no change) ---
    useEffect(() => {
      messagesEndRef.current?.scrollIntoView({ behavior: "smooth" });
    }, [messages]);

  // --- Effect to fetch history when sessionId changes ---
    useEffect(() => {
        const fetchHistory = async () => {
            if (sessionId) { // Only fetch if sessionId is valid
                // console.log("ChatInterface: Session ID found, fetching history:", sessionId);
                setIsLoading(true); // Show loading indicator while fetching history
                setError(null);
                try {
                    const historyMessages = await getChatHistory(sessionId);
                    // console.log("ChatInterface: Fetched history:", historyMessages);
                    // Assuming historyMessages is an array like [{ role: 'user', content: '...' }, ...]
                    setMessages(historyMessages || []); // Update the state in App.js
                } 
                catch (err) {
                    console.error("Failed to fetch chat history:", err);
                    setError("Could not load previous chat history.");
                    setMessages([]); // Clear messages on error
                } finally {
                    setIsLoading(false);
                }
            } 
            else {
                // If sessionId is null (new chat or after reset), ensure messages are clear
                // console.log("ChatInterface: No Session ID, clearing messages.");
                setMessages([]);
        }
      };

      fetchHistory();
    // Run when sessionId changes (including from null to a value, or value to null)
  }, [sessionId, setMessages]); // Add setMessages dependency

  // --- Handle Input Change (no change) ---
    const handleInputChange = (event) => {
        setUserInput(event.target.value);
    };

  // --- Handle Submit (use props for state updates) ---
    const handleSubmit = async (event) => {
        event.preventDefault();
        if (!userInput.trim() || isLoading) return;

        const newUserMessage = { role: "user", content: userInput };
        // *** Use setMessages prop ***
        setMessages((prevMessages) => [...prevMessages, newUserMessage]);
        setUserInput("");
        setIsLoading(true);
        setError(null);
        // *** Use setResponseDetails prop ***
        setResponseDetails(null);

        try {
            const response = await getApiResponse(userInput, sessionId, selectedModel);
            if (response && response.answer) {
                const assistantMessage = { role: "assistant", content: response.answer };
                // *** Use setMessages prop ***
                setMessages((prevMessages) => [...prevMessages, assistantMessage]);
                onSessionIdChange(response.session_id); // Let App know about the (potentially new) ID
                // *** Use setResponseDetails prop ***
                setResponseDetails({
                  answer: response.answer,
                  model: response.model,
                  sessionId: response.session_id,
                });
            } 
            else {
                setError("Received an empty or invalid response from the API.");
                setMessages((prevMessages) => [
                  ...prevMessages,
                  { role: "assistant", content: "Sorry, I encountered an issue getting a response." },
                ]);
            }
        } 
        catch (err) {
            setError(`Failed to get response: ${err.message}`);
            setMessages((prevMessages) => [
              ...prevMessages,
              { role: "assistant", content: `Sorry, an error occurred: ${err.message}` },
            ]);
        } 
        finally {
            setIsLoading(false);
        }
  };

  // --- Render function (uses props) ---
  return (
    <div className="chat-interface">
      <div className="message-list">
        {/* Render loading indicator also when fetching history initially */
        /* Note: Initial isLoading is handled by the fetchHistory effect */}
        {isLoading && messages.length === 0 && (
             <div className="message assistant initial-loading">
                {/* Optionally hide icon during initial load or show a spinner */}
                <div className="message-content-container">
                    <div className="message-content loading-dots">
                    <span>.</span><span>.</span><span>.</span>
                    </div>
                </div>
             </div>
        )}
        {/* Render messages from App state */}
        {messages.map((msg, index) => (
          <div key={`${msg.role}-${index}`} className={`message ${msg.role}`}> {/* Use more stable key if possible */}
            <div className="message-icon-container">
              {msg.role === 'user' ? (
                <UserIcon className="message-icon user-icon" />
              ) : (
                <ChatbotIcon className="message-icon assistant-icon" />
              )}
            </div>
            <div className="message-content-container">
              <div className="message-content">{msg.content}</div>
            </div>
          </div>
        ))}

        {/* Loading indicator for new messages */}
        {isLoading && messages.length > 0 && ( // Only show this if messages already exist
          <div className="message assistant">
            <div className="message-icon-container">
              <ChatbotIcon className="message-icon assistant-icon" />
            </div>
            <div className="message-content-container">
              <div className="message-content loading-dots">
                <span>.</span><span>.</span><span>.</span>
              </div>
            </div>
          </div>
        )}
        <div ref={messagesEndRef} />
      </div>

      {error && <p className="error-message chat-error">{error}</p>}

      {/* Use responseDetails from props */}
      {responseDetails && (
        <details className="response-details">
          <summary>Details</summary>
          <div>
            <h4>Generated Answer</h4><pre><code>{responseDetails.answer}</code></pre>
            <h4>Model Used</h4><pre><code>{responseDetails.model}</code></pre>
            <h4>Session ID</h4><pre><code>{responseDetails.sessionId}</code></pre>
          </div>
        </details>
      )}

      <form onSubmit={handleSubmit} className="input-form">
        <input type="text" value={userInput} onChange={handleInputChange} placeholder="Query:" disabled={isLoading} />
        <button type="submit" disabled={isLoading || !userInput.trim()}>{isLoading ? "..." : "Send"}</button>
      </form>
    </div>
  );
}

export default ChatInterface;