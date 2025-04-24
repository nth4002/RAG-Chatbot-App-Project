// src/icons/UserIcon.js
import React from 'react';

// Filled user icon
function UserIcon(props) {
  return (
    <svg
      xmlns="http://www.w3.org/2000/svg"
      viewBox="0 0 24 24" // Standard Material Symbols viewBox
      fill="currentColor" // Use fill
      // stroke="none" // Explicitly no stroke needed
      className={props.className}
      style={props.style}
      width="1em"
      height="1em"
      aria-hidden="true"
    >
      {/* Material Symbols Person Filled */}
      <path d="M12 12c2.21 0 4-1.79 4-4s-1.79-4-4-4-4 1.79-4 4 1.79 4 4 4Zm0 2c-2.67 0-8 1.34-8 4v1c0 .55.45 1 1 1h14c.55 0 1-.45 1-1v-1c0-2.66-5.33-4-8-4Z"/>
    </svg>
  );
}

export default UserIcon;