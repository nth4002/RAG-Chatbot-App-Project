import React, { useState, useRef, useEffect } from "react";

function RenderCounter() {
  const [count, setCount] = useState(0);

  // This ref will persist across renders but won't cause re-renders
  const renderCount = useRef(1);

  // Every time the component renders, update the render count
  useEffect(() => {
    console.log(renderCount.current);
    renderCount.current += 1;
  }, []);

  return (
    <div>
      <h2>Clicked {count} times</h2>
      <p>Component has rendered {renderCount.current} times</p>
      <button onClick={() => setCount(count + 1)}>Click Me</button>
    </div>
  );
}
export default RenderCounter;