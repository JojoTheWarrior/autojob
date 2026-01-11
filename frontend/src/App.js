import React, { useState } from "react";
import "./App.css";

export default function App() {
  const [backendUrl, setBackendUrl] = useState("");
  const [started, setStarted] = useState(false);

  const handleKeyDown = (e) => {
    if (e.key === "Enter" && backendUrl.trim() !== "") {
      setStarted(true);
    }
  };

  return (
    <div className={`app ${started ? "started" : ""}`}>
      {/* Initial Terminal */}
      <div className="boot-terminal">
        <span className="prompt">{">"}</span>
        <input
          className="url-input"
          value={backendUrl}
          onChange={(e) => setBackendUrl(e.target.value)}
          onKeyDown={handleKeyDown}
          placeholder="Enter backend URL"
          autoFocus
        />
        {!started && <span className="caret" />}
      </div>

      {/* Split Terminals */}
      <div className="split-terminals">
        <div className="terminal actor">
          <div className="terminal-header">ACTOR</div>
          <div className="terminal-body">
            ACTOR TERMINAL READY...
          </div>
        </div>

        <div className="terminal critic">
          <div className="terminal-header">CRITIC</div>
          <div className="terminal-body">
            CRITIC TERMINAL READY...
          </div>
        </div>
      </div>
    </div>
  );
}
