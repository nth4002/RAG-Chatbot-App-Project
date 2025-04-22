// src/components/UserIcon.js
import React from 'react';

function UserIcon(props) {
  return (
    <svg
      xmlns="http://www.w3.org/2000/svg"
      viewBox="0 0 24 24"
      fill="currentColor"
      stroke="currentColor" // Optional: Add stroke if needed
      strokeWidth="0.5"     // Optional: Adjust stroke width
      strokeLinecap="round" // Optional
      strokeLinejoin="round"// Optional
      className={props.className} // Pass className for styling
      style={props.style}       // Pass style object
      width="1em" // Default size, can be overridden by CSS
      height="1em"
      aria-hidden="true" // Hide decorative icons from screen readers
    >
      <path d="M12 12c2.21 0 4-1.79 4-4s-1.79-4-4-4-4 1.79-4 4 1.79 4 4 4zm0 2c-2.67 0-8 1.34-8 4v2h16v-2c0-2.66-5.33-4-8-4z" />
      {/* Simple person outline */}
    </svg>
  );
}

export default UserIcon;