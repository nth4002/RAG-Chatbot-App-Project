// src/components/ChatInterface.js
import React, { useState, useEffect, useRef } from "react";
import { getApiResponse } from "../services/api";
import UserIcon from "../icons/UserIcon"; // Adjust path if icons are in src/icons
import ChatbotIcon from "../icons/ChatbotIcon"; // Adjust path if icons are in src/icons
import "./ChatInterface.css";

function ChatInterface({ selectedModel, sessionId, onSessionIdChange }) {
  const [messages, setMessages] = useState([]);
  const [userInput, setUserInput] = useState("");
  const [isLoading, setIsLoading] = useState(false);
  const [error, setError] = useState(null);
  const [responseDetails, setResponseDetails] = useState(null);
  const messagesEndRef = useRef(null);

  useEffect(() => {
     messagesEndRef.current?.scrollIntoView({ behavior: "smooth" });
  }, [messages]);

  const handleInputChange = (event) => {
      setUserInput(event.target.value);
  };

  const handleSubmit = async (event) => {
      event.preventDefault();
      if (!userInput.trim() || isLoading) return;

      const newUserMessage = { role: "user", content: userInput };
      setMessages((prevMessages) => [...prevMessages, newUserMessage]);
      setUserInput("");
      setIsLoading(true);
      setError(null);
      setResponseDetails(null);

      try {
          const response = await getApiResponse(userInput, sessionId, selectedModel);
          if (response && response.answer) {
              const assistantMessage = { role: "assistant", content: response.answer };
              setMessages((prevMessages) => [...prevMessages, assistantMessage]);
              onSessionIdChange(response.session_id);
              setResponseDetails({
                  answer: response.answer,
                  model: response.model,
                  sessionId: response.session_id,
              });
          }
          else {
              setError("Received an empty or invalid response from the API.");
              setMessages((prevMessages) => [...prevMessages, { role: "assistant", content: "Sorry, I encountered an issue getting a response." }]);
          }
      }
      catch (err) {
          setError(`Failed to get response: ${err.message}`);
          setMessages((prevMessages) => [...prevMessages, { role: "assistant", content: `Sorry, an error occurred: ${err.message}` }]);
      }
      finally {
          setIsLoading(false);
      }
  };

  return (
    <div className="chat-interface">
      <div className="message-list">
        {messages.map((msg, index) => (
          // The main message container now uses flex
          <div key={index} className={`message ${msg.role}`}>
            {/* Conditionally render the icon */}
            <div className="message-icon-container">
              {msg.role === 'user' ? (
                  <UserIcon className="message-icon user-icon" />
              ) : (
                  <ChatbotIcon className="message-icon assistant-icon" />
              )}
            </div>
            {/* The text content bubble */}
            <div className="message-content-container">
              <div className="message-content">{msg.content}</div>
            </div>
          </div>
        ))}

        {/* Loading indicator - might want an icon here too? */}
        {isLoading && (
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

      {responseDetails && (
         <details className="response-details">
          {/* ... expander content ... */}
           <summary>Details</summary>
          <div>
            <h4>Generated Answer</h4><pre><code>{responseDetails.answer}</code></pre>
            <h4>Model Used</h4><pre><code>{responseDetails.model}</code></pre>
            <h4>Session ID</h4><pre><code>{responseDetails.sessionId}</code></pre>
          </div>
         </details>
      )}

      <form onSubmit={handleSubmit} className="input-form">
        <input type="text" value={userInput} onChange={handleInputChange} placeholder="Query:" disabled={isLoading}/>
        <button type="submit" disabled={isLoading || !userInput.trim()}>{isLoading ? "..." : "Send"}</button>
      </form>
    </div>
  );
}

export default ChatInterface;