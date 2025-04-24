// src/icons/ChatbotIcon.js
// (Or update src/components/ChatbotIcon.js)

import React from 'react';

// Icon based on the Google Gemini sparkle/star image provided
function ChatbotIcon(props) {
  return (
    <svg
      xmlns="http://www.w3.org/2000/svg"
      // Using a viewBox that fits the typical path data well
      // This maintains the aspect ratio of the path within the SVG viewport.
      viewBox="0 0 24 24"
      // We use fill="currentColor" so the SVG inherits the color
      // set by the parent CSS rule (e.g., .assistant-icon color).
      // The gradient definition itself will override this for the path shape.
      fill="currentColor"
      // Pass down className and style props for flexibility
      className={props.className}
      style={props.style}
      // Default size, controllable via CSS font-size or specific width/height
      width="1em"
      height="1em"
      // Hide purely decorative icons from assistive technologies
      aria-hidden="true"
    >
      {/*
        Define the gradient within <defs>.
        It won't be rendered directly but can be referenced by its ID.
      */}
      <defs>
        {/*
          Define a linear gradient.
          id: Unique identifier to reference this gradient.
          x1, y1, x2, y2: Define the start and end points of the gradient vector.
            Here, 0% 0% to 0% 100% means a vertical gradient from top to bottom.
        */}
        <linearGradient id="geminiSparkleGradient" x1="0%" y1="0%" x2="0%" y2="100%">
          {/*
            Define color stops along the gradient.
            offset: Position along the gradient vector (0% is start, 100% is end).
            stop-color: The color at that position.
            stop-opacity: Opacity at that position (1 is fully opaque).
            We are approximating the blue-to-white/light-grey gradient.
          */}
          <stop offset="5%" style={{ stopColor: '#E8F0FE', stopOpacity: 1 }} />
          <stop offset="95%" style={{ stopColor: '#4285F4', stopOpacity: 1 }} />
        </linearGradient>
      </defs>

      {/*
        The path element defines the actual shape of the icon.
        fillRule/clipRule="evenodd": Helps ensure correct filling for complex shapes.
        d: The path data string defining points and curves.
           M = Move to (start point)
           C = Cubic Bezier curve (start control, end control, end point)
           Z = Close path (connects end back to start)
        fill="url(#geminiSparkleGradient)": This tells the path to use the
           gradient defined above (with id="geminiSparkleGradient") as its fill.
      */}
      <path
         fillRule="evenodd"
         clipRule="evenodd"
         d="M12 1.5C14.21 6.52 17.48 9.79 22.5 12C17.48 14.21 14.21 17.48 12 22.5C9.79 17.48 6.52 14.21 1.5 12C6.52 9.79 9.79 6.52 12 1.5Z"
         // Apply the gradient fill defined in <defs>
         fill="url(#geminiSparkleGradient)"
       />
    </svg>
  );
}

export default ChatbotIcon;