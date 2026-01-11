import React, { useEffect, useRef, useState } from "react";
import "./App.css";

/**
 * GLOBAL BUFFERS (persist outside React renders)
 */
let actor_lines = [];
let critic_lines = [];

const POLL_INTERVAL = 500;     // ms
const TYPE_INTERVAL = 18;      // ms per character (slightly faster for snappier feel)

export default function App() {
  const [backendUrl, setBackendUrl] = useState("");
  const [started, setStarted] = useState(false);

  const [actorDisplay, setActorDisplay] = useState([
    { ts: "", text: ">> Awaiting uplink... establishing signal...\n" },
  ]);
  const [criticDisplay, setCriticDisplay] = useState([
    { text: ">> Critic module standby...\n" },
  ]);

  // Track if currently typing for visual caret
  const [isActorTyping, setIsActorTyping] = useState(false);
  const [isCriticTyping, setIsCriticTyping] = useState(false);

  const actorQueue = useRef([]);
  const criticQueue = useRef([]);

  const actorTyping = useRef(false);
  const criticTyping = useRef(false);

  const actorEndRef = useRef(null);
  const criticEndRef = useRef(null);

  /**
   * -----------------------------
   * Boot terminal submit
   * -----------------------------
   */
  const handleKeyDown = async (e) => {
    if (e.key === "Enter" && backendUrl.trim() !== "") {
      setStarted(true);

      try {
        await fetch("http://localhost:8000/apply", {
          method: "POST",
          headers: { "Content-Type": "application/json" },
          body: JSON.stringify({ url: backendUrl }),
        });
      } catch (err) {
        console.error("Failed to POST /apply", err);
      }
    }
  };

  /**
   * -----------------------------
   * Poll actor + critic endpoints
   * -----------------------------
   */
  useEffect(() => {
    if (!started) return;

    const poll = async () => {
      try {
        const [actorRes, criticRes] = await Promise.all([
          fetch("http://localhost:8000/get_actor"),
          fetch("http://localhost:8000/get_critic"),
        ]);

        const actorData = await actorRes.json();
        const criticData = await criticRes.json();

        // ACTOR: list of [timestamp, text]
        if (actorData.length > actor_lines.length) {
          const newItems = actorData.slice(actor_lines.length);
          actor_lines = actorData;

          newItems.forEach(([ts, text]) => {
            actorQueue.current.push({ ts, text });
          });
        }

        // CRITIC: list of strings
        if (criticData.length > critic_lines.length) {
          const newItems = criticData.slice(critic_lines.length);
          critic_lines = criticData;

          newItems.forEach((line) => {
            criticQueue.current.push(line);
          });
        }
      } catch (err) {
        console.error("Polling error", err);
      }
    };

    poll();
    const id = setInterval(poll, POLL_INTERVAL);
    return () => clearInterval(id);
  }, [started]);

  /**
   * -----------------------------
   * Typing engine (Actor)
   * -----------------------------
   */
  useEffect(() => {
    if (!started) return;

    const tick = () => {
      if (actorTyping.current) return;
      if (actorQueue.current.length === 0) {
        setIsActorTyping(false);
        return;
      }

      const { ts, text } = actorQueue.current.shift();
      actorTyping.current = true;
      setIsActorTyping(true);

      // Immediately render timestamp (no slow typing)
      setActorDisplay((prev) => [
        ...prev,
        { ts: formatTs(ts), text: "" },
      ]);

      let i = 0;

      const typer = setInterval(() => {
        i++;
        setActorDisplay((prev) => {
          const copy = [...prev];
          copy[copy.length - 1].text = text.slice(0, i);
          return copy;
        });

        if (i >= text.length) {
          clearInterval(typer);
          actorTyping.current = false;
          // Small delay before removing caret if queue is empty
          setTimeout(() => {
            if (actorQueue.current.length === 0) {
              setIsActorTyping(false);
            }
          }, 300);
        }
      }, TYPE_INTERVAL);
    };

    const id = setInterval(tick, 40);
    return () => clearInterval(id);
  }, [started]);

  /**
   * -----------------------------
   * Typing engine (Critic)
   * -----------------------------
   */
  useEffect(() => {
    if (!started) return;

    const tick = () => {
      if (criticTyping.current) return;
      if (criticQueue.current.length === 0) {
        setIsCriticTyping(false);
        return;
      }

      const line = criticQueue.current.shift();
      criticTyping.current = true;
      setIsCriticTyping(true);

      setCriticDisplay((prev) => [...prev, { text: "" }]);

      let i = 0;

      const typer = setInterval(() => {
        i++;
        setCriticDisplay((prev) => {
          const copy = [...prev];
          copy[copy.length - 1].text = line.slice(0, i);
          return copy;
        });

        if (i >= line.length) {
          clearInterval(typer);
          criticTyping.current = false;
          // Small delay before removing caret if queue is empty
          setTimeout(() => {
            if (criticQueue.current.length === 0) {
              setIsCriticTyping(false);
            }
          }, 300);
        }
      }, TYPE_INTERVAL);
    };

    const id = setInterval(tick, 40);
    return () => clearInterval(id);
  }, [started]);

  /**
   * -----------------------------
   * Auto-scroll terminals
   * -----------------------------
   */
  useEffect(() => {
    actorEndRef.current?.scrollIntoView({ behavior: "smooth" });
  }, [actorDisplay]);

  useEffect(() => {
    criticEndRef.current?.scrollIntoView({ behavior: "smooth" });
  }, [criticDisplay]);

  return (
    <div className={`app ${started ? "started" : ""}`}>
      {/* Boot Terminal */}
      <div className="boot-terminal">
        <span className="prompt">{">"}</span>
        <input
          className="url-input"
          value={backendUrl}
          onChange={(e) => setBackendUrl(e.target.value)}
          onKeyDown={handleKeyDown}
          placeholder="Enter target URL..."
          autoFocus
        />
        {!started && <span className="caret" />}
      </div>

      {/* Split Terminals */}
      <div className="split-terminals">
        {/* ACTOR */}
        <div className="terminal actor">
          <div className="terminal-header">
            ACTOR
            <span className="status-indicator">
              <span className="status-dot" />
              {isActorTyping ? "PROCESSING" : "READY"}
            </span>
          </div>
          <div className="terminal-body">
            {actorDisplay.map((line, idx) => (
              <div key={idx} className="line">
                {line.ts && (
                  <span className="timestamp">[{line.ts}]</span>
                )}
                <span>{line.text}</span>
              </div>
            ))}
            {isActorTyping && <span className="typing-caret" />}
            <div ref={actorEndRef} />
          </div>
        </div>

        {/* Animated Divider */}
        <div className="terminal-divider" />

        {/* CRITIC */}
        <div className="terminal critic">
          <div className="terminal-header">
            CRITIC
            <span className="status-indicator">
              <span className="status-dot" />
              {isCriticTyping ? "ANALYZING" : "STANDBY"}
            </span>
          </div>
          <div className="terminal-body">
            {criticDisplay.map((line, idx) => (
              <div key={idx} className="line">
                {line.text}
              </div>
            ))}
            {isCriticTyping && <span className="typing-caret" />}
            <div ref={criticEndRef} />
          </div>
        </div>
      </div>
    </div>
  );
}

/**
 * Trim timestamp to readable seconds
 */
function formatTs(ts) {
  if (!ts) return "";
  return ts.replace("T", " ").split(".")[0];
}
