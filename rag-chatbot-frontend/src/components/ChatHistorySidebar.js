// src/components/ChatHistorySidebar.js
import React from 'react';
import './ChatHistorySidebar.css'; // We'll create this CSS file

function ChatHistorySidebar({
  sessionsList,     // Renamed from chatSessionsList for local clarity
  currentSessionId,
  onSelectSession,
  isLoading        // Renamed from isLoadingSessions
}) {

  return (
    <div className="chat-history-sidebar">
      <h3>Recent Chats</h3>
      {isLoading && <p className="loading-message">Loading chats...</p>}
      {!isLoading && sessionsList.length === 0 && (
        <p className="no-history-message">No past chats found.</p>
      )}
      {!isLoading && sessionsList.length > 0 && (
        <div className="chat-history-list">
          {sessionsList.map((session) => (
            <button
              key={session.session_id}
              className={`chat-session-item ${session.session_id === currentSessionId ? 'active' : ''}`}
              onClick={() => onSelectSession(session.session_id)}
              title={`Load chat: ${session.display_name}`} // Tooltip
            >
              {/* Simple message icon (optional) */}
              <svg className="chat-session-icon" xmlns="http://www.w3.org/2000/svg" width="16" height="16" fill="currentColor" viewBox="0 0 16 16">
                 <path d="M0 2a2 2 0 0 1 2-2h12a2 2 0 0 1 2 2v8a2 2 0 0 1-2 2h-2.5a1 1 0 0 0-.8.4l-1.9 2.533a1 1 0 0 1-1.6 0L5.3 14.4a1 1 0 0 0-.8-.4H2a2 2 0 0 1-2-2V2zm3.5 1a.5.5 0 0 0 0 1h9a.5.5 0 0 0 0-1h-9zm0 2.5a.5.5 0 0 0 0 1h9a.5.5 0 0 0 0-1h-9zm0 2.5a.5.5 0 0 0 0 1h5a.5.5 0 0 0 0-1h-5z"/>
              </svg>
              <span className="chat-session-name">{session.display_name}</span>
            </button>
          ))}
        </div>
      )}
    </div>
  );
}

export default ChatHistorySidebar;