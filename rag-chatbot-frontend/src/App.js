// src/App.js
import React, { useState } from "react";
import Sidebar from "./components/Sidebar";
import ChatInterface from "./components/ChatInterface";
import "./App.css"; // Main layout styles

function App() {
  // --- State ---
  const [selectedModel, setSelectedModel] = useState("gemini-1.5-flash");
  const [sessionId, setSessionId] = useState(null);
  const [documents, setDocuments] = useState([]);
  // --- Lifted State ---
  const [isSidebarOpen, setIsSidebarOpen] = useState(true); // Sidebar starts open

  // --- Handlers ---
  const handleModelChange = (newModel) => {
    setSelectedModel(newModel);
  };

  const handleSessionIdChange = (newSessionId) => {
    setSessionId(newSessionId);
  };

  const handleDocumentsUpdate = (updatedDocs) => {
    setDocuments(updatedDocs);
  };

  // --- Function to toggle sidebar state ---
  const toggleSidebar = () => {
    setIsSidebarOpen(!isSidebarOpen);
  };

  return (
    <div className="app-container">
      {/* Pass isOpen state and toggle function to Sidebar */}
      <Sidebar
        isOpen={isSidebarOpen}
        toggleSidebar={toggleSidebar}
        selectedModel={selectedModel}
        onModelChange={handleModelChange}
        onDocumentsUpdate={handleDocumentsUpdate}
      />

      {/* Main content area that includes the header and chat */}
      <div className="main-content">
        {/* Header that changes position */}
        <header className={`app-header ${isSidebarOpen ? 'sidebar-open' : 'sidebar-closed'}`}>
           <h1>QA Chatbot</h1>
        </header>

        {/* Chat interface */}
        <ChatInterface
          selectedModel={selectedModel}
          sessionId={sessionId}
          onSessionIdChange={handleSessionIdChange}
        />
      </div>
    </div>
  );
}

export default App;