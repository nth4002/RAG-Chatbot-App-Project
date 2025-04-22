// src/components/ChatbotIcon.js
import React from 'react';

function ChatbotIcon(props) {
  return (
    <svg
      xmlns="http://www.w3.org/2000/svg"
      viewBox="0 0 24 24"
      fill="currentColor"
      stroke="currentColor" // Optional
      strokeWidth="0.5"     // Optional
      strokeLinecap="round" // Optional
      strokeLinejoin="round"// Optional
      className={props.className} // Pass className for styling
      style={props.style}       // Pass style object
      width="1em" // Default size, can be overridden by CSS
      height="1em"
      aria-hidden="true" // Hide decorative icons from screen readers
    >
      {/* Simple robot head outline */}
      <path d="M12 2a2 2 0 0 1 2 2v2h-4V4a2 2 0 0 1 2-2zM6.88 9.55c-.55 0-1-.45-1-1s.45-1 1-1 1 .45 1 1-.45 1-1 1zm10.24 0c-.55 0-1-.45-1-1s.45-1 1-1 1 .45 1 1-.45 1-1 1zM19 10v9c0 1.1-.9 2-2 2H7c-1.1 0-2-.9-2-2v-9c0-1.1.9-2 2-2h10c1.1 0 2 .9 2 2zM8 16h8v2H8v-2z"/>

    </svg>
  );
}

export default ChatbotIcon;