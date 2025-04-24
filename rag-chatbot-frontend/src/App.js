// src/App.js
import React, { useState, useEffect, useCallback, useRef } from "react"; // Added useCallback
import Sidebar from "./components/Sidebar"; //left sidebar
import ChatHistorySidebar from "./components/ChatHistorySidebar"; // Right Sidebar (History)
import ChatInterface from "./components/ChatInterface";

// *** Import the new API function ***
import { listChatSessions } from "./services/api";
import "./App.css";

// A built-in browser API that provides storage for key-value pairs (as strings). 
// Crucially, data stored in sessionStorage persists only for the duration of the page session. 
// This means the data remains available if the user reloads the page or navigates away and comes back within
// the same browser tab, but it's cleared when the tab or browser is closed.

// Purpose: To remember the currently active chat session ID if the user reloads the page within the same tab,
// allowing the app to automatically load the history for that session upon reload instead of starting fresh.
const SESSION_ID_STORAGE_KEY = 'rag_chat_session_id';

function App() {
    // --- State ---
    const [selectedModel, setSelectedModel] = useState("gemini-1.5-flash");
    const [sessionId, setSessionId] = useState(() => sessionStorage.getItem(SESSION_ID_STORAGE_KEY));
    const [documents, setDocuments] = useState([]);
    const [isSidebarOpen, setIsSidebarOpen] = useState(true);
    const [messages, setMessages] = useState([]);
    const [responseDetails, setResponseDetails] = useState(null);
    // --- NEW State for chat sessions list ---
    const [chatSessionsList, setChatSessionsList] = useState([]);
    const [isLoadingSessions, setIsLoadingSessions] = useState(false); // Optional loading state

    // --- Ref to store the previous session ID ---
    const prevSessionIdRef = useRef(sessionId);
    // --- This effect runs after the component mounts and any time the sessionId state changes. ---
    useEffect(() => {
        if (sessionId) {
            sessionStorage.setItem(SESSION_ID_STORAGE_KEY, sessionId);
        }   
        else {
            sessionStorage.removeItem(SESSION_ID_STORAGE_KEY);
        }
        // --- Update previous session ID ref after state update ---
        prevSessionIdRef.current = sessionId;
    }, [sessionId]);

    // Effect to fetch chat session list on initial load
    // stop react re-create this fetchSessionList whenever react re-render
    const fetchSessionList = useCallback(async (showLoading = true) => { // Add parameter
        if (showLoading) setIsLoadingSessions(true);
        try {
            const sessions = await listChatSessions();
            console.log("Session list: ", sessions);
            // Sort sessions potentially (newest first is common, requires backend timestamp)
            // sessions.sort((a, b) => (b.timestamp || 0) - (a.timestamp || 0)); // Example if timestamp added
            setChatSessionsList(sessions || []);
        } 
        catch (error) {
            console.error("App: Failed to fetch sessions:", error);
            setChatSessionsList([]);
        }
        finally {
            if (showLoading) setIsLoadingSessions(false);
        }
    }, []); // No dependencies needed for the function itself

 
    useEffect(() => {
        fetchSessionList(); // Fetch on initial mount
    }, [fetchSessionList]); // Depend on the memoized function
  
  // --- Handlers ---
    const handleModelChange = (newModel) => { setSelectedModel(newModel); };
    const handleDocumentsUpdate = (updatedDocs) => { setDocuments(updatedDocs); };
    const toggleSidebar = () => { setIsSidebarOpen(!isSidebarOpen); };

    // Modified handleSessionIdChange
    const handleSessionIdChange = (newSessionId) => {
        // --- Check if a NEW session was just established ---
        // This happens when the previous ID was null (meaning we clicked "New Chat")
        // and now we received a non-null ID from the backend after the first message.
        const previousSessionId = prevSessionIdRef.current;
        if (previousSessionId === null && newSessionId !== null) {
            // console.log("App: New session established, refreshing session list.");
            // Refresh the list to include the session that was just implicitly 'saved'
            fetchSessionList(false); // Fetch silently without showing main loading indicator
        }
        // --- Always update the current session ID state ---
        setSessionId(newSessionId);
  };
    const handleNewChat = () => {
        setMessages([]);
        setResponseDetails(null);
        setSessionId(null);
        // Potentially refresh session list here if needed, but usually not required
    };

    const handleSelectSession = (selectedSessionId) => {
        if (selectedSessionId !== sessionId) {
            // console.log("App: Selecting session:", selectedSessionId);
            setMessages([]); // Clear UI immediately
            setResponseDetails(null);
            setSessionId(selectedSessionId); // Trigger history fetch in ChatInterface
        }
    };

    return (
    <div className="app-container">
      <Sidebar
        isOpen={isSidebarOpen}
        toggleSidebar={toggleSidebar}
        selectedModel={selectedModel}
        onModelChange={handleModelChange}
        onDocumentsUpdate={handleDocumentsUpdate}
      />
  
      <div className="main-content">
        <header className={`app-header ${isSidebarOpen ? 'sidebar-open' : 'sidebar-closed'}`}>
          <h1>QA Chatbot</h1>
          <button onClick={handleNewChat} className="new-chat-button" title="Start New Chat" aria-label="Start New Chat">
             <svg xmlns="http://www.w3.org/2000/svg" width="16" height="16" fill="currentColor" viewBox="0 0 16 16"><path d="M8 4a.5.5 0 0 1 .5.5v3h3a.5.5 0 0 1 0 1h-3v3a.5.5 0 0 1-1 0v-3h-3a.5.5 0 0 1 0-1h3v-3A.5.5 0 0 1 8 4z"/></svg>
             {isSidebarOpen && <span className="new-chat-text">New Chat</span>}
          </button>
        </header>
        <ChatInterface
          selectedModel={selectedModel}
          sessionId={sessionId}
          onSessionIdChange={handleSessionIdChange} // Pass the modified handler
          messages={messages}
          setMessages={setMessages}
          responseDetails={responseDetails}
          setResponseDetails={setResponseDetails}
        />
      </div>

      <ChatHistorySidebar
        sessionsList={chatSessionsList}
        currentSessionId={sessionId}
        onSelectSession={handleSelectSession}
        isLoading={isLoadingSessions}
      />

      
    </div>
  );
}

export default App;