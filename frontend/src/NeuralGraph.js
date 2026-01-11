import React, { useEffect, useRef, useState, useCallback } from "react";
import "./NeuralGraph.css";

// Sample data extracted from test_info.json - flatten all values
const PROFILE_DATA = {
  // Personal
  first_name: "Zhurong",
  preferred_name: "Max",
  last_name: "Wang",
  email: "maxwang315@gmail.com",
  phone: "250-661-7096",
  city: "Victoria",
  province: "British Columbia",
  country: "Canada",
  postal_code: "V8X 5G6",
  
  // Education
  university: "University of Waterloo",
  faculty: "Math",
  major: "Computer Science",
  degree: "Bachelors",
  gpa: "3.9",
  year: "Year 1",
  
  // Skills
  python: "Python",
  java: "Java",
  javascript: "Javascript",
  rust: "Rust",
  html: "HTML",
  css: "CSS",
  pandas: "Pandas",
  
  // Work
  job_title: "Keyboard Accompanist",
  company: "St Paul's United Church",
  
  // Languages
  english: "English",
  chinese: "Chinese",
  
  // Other
  linkedin: "LinkedIn",
  github: "GitHub",
};

// Convert to array of nodes
const ALL_WORDS = Object.entries(PROFILE_DATA).map(([key, value], idx) => ({
  id: key,
  label: value,
  x: 0,
  y: 0,
  vx: 0,
  vy: 0,
  size: 12 + Math.random() * 8,
}));

export default function NeuralGraph({ actorLines, criticLines, isSearching }) {
  const canvasRef = useRef(null);
  const nodesRef = useRef([]);
  const connectionsRef = useRef([]);
  const animationRef = useRef(null);
  const wsRef = useRef(null);
  const searchStateRef = useRef({
    isSearching: true,  // START searching by default
    targetNode: null,
    searchProgress: 0,
    activatedNodes: new Set(),
    pulseNodes: [],
    startTime: Date.now(),
  });

  const [highlightedWord, setHighlightedWord] = useState(null);
  const triggerFnRef = useRef(null); // Ref to hold trigger function for WebSocket

  // Initialize nodes with positions
  useEffect(() => {
    const canvas = canvasRef.current;
    if (!canvas) return;

    const width = canvas.width;
    const height = canvas.height;
    const centerX = width / 2;
    const centerY = height / 2;

    // Initialize nodes in a circular pattern with some randomness
    nodesRef.current = ALL_WORDS.map((word, idx) => {
      const angle = (idx / ALL_WORDS.length) * Math.PI * 2;
      const radius = 80 + Math.random() * 100;
      return {
        ...word,
        x: centerX + Math.cos(angle) * radius + (Math.random() - 0.5) * 40,
        y: centerY + Math.sin(angle) * radius + (Math.random() - 0.5) * 40,
        vx: (Math.random() - 0.5) * 0.5,
        vy: (Math.random() - 0.5) * 0.5,
        baseSize: word.size,
        currentSize: word.size,
        alpha: 0.6,
        highlighted: false,
      };
    });

    // Create some random connections between nodes
    const connections = [];
    for (let i = 0; i < nodesRef.current.length; i++) {
      const numConnections = 1 + Math.floor(Math.random() * 2);
      for (let j = 0; j < numConnections; j++) {
        const target = Math.floor(Math.random() * nodesRef.current.length);
        if (target !== i) {
          connections.push({
            from: i,
            to: target,
            alpha: 0.1,
            active: false,
          });
        }
      }
    }
    connectionsRef.current = connections;
    
    // Start the searching animation immediately
    searchStateRef.current = {
      isSearching: true,
      targetNode: null,
      searchProgress: 0,
      activatedNodes: new Set(),
      pulseNodes: [],
      startTime: Date.now(),
    };
  }, []);

  // Function to highlight a word (called when WebSocket receives a word)
  // This STOPS searching, highlights the word, then resumes after 0.5s
  const highlightWord = useCallback((word) => {
    console.log("Highlighting word:", word);
    
    // Clear any previous temporary nodes
    nodesRef.current = nodesRef.current.filter((n) => !n.isTemporary);
    connectionsRef.current = connectionsRef.current.filter((c) => !c.isTemporary);
    
    // Reset all node highlighting
    nodesRef.current.forEach((node) => {
      node.highlighted = false;
      node.currentSize = node.baseSize;
      node.alpha = 0.6;
    });

    // Find or create the target node
    let targetNode = nodesRef.current.find(
      (node) => node.label.toLowerCase() === word.toLowerCase()
    );

    if (!targetNode) {
      // Create a temporary node for this word
      const canvas = canvasRef.current;
      const centerX = canvas ? canvas.width / 2 : 200;
      const centerY = canvas ? canvas.height / 2 : 150;
      
      const tempNode = {
        id: `temp_${Date.now()}`,
        label: word,
        x: centerX + (Math.random() - 0.5) * 100,
        y: centerY + (Math.random() - 0.5) * 100,
        vx: 0,
        vy: 0,
        baseSize: 16,
        currentSize: 16,
        alpha: 0.6,
        highlighted: false,
        isTemporary: true,
      };

      nodesRef.current.push(tempNode);
      
      // Add connections to the temp node
      const tempNodeIdx = nodesRef.current.length - 1;
      for (let i = 0; i < 3; i++) {
        const randomTarget = Math.floor(Math.random() * (nodesRef.current.length - 1));
        connectionsRef.current.push({
          from: tempNodeIdx,
          to: randomTarget,
          alpha: 0.1,
          active: false,
          isTemporary: true,
        });
      }

      targetNode = tempNode;
    }

    // STOP searching - highlight the word
    searchStateRef.current.isSearching = false;
    targetNode.highlighted = true;
    targetNode.currentSize = targetNode.baseSize * 2;
    targetNode.alpha = 1;
    targetNode.bouncePhase = 0;
    
    setHighlightedWord(targetNode.label);

    // After 0.5 seconds, resume searching
    setTimeout(() => {
      // Reset highlighting
      targetNode.highlighted = false;
      targetNode.currentSize = targetNode.baseSize;
      targetNode.alpha = 0.6;
      
      // Remove temporary node if it was one
      if (targetNode.isTemporary) {
        nodesRef.current = nodesRef.current.filter((n) => !n.isTemporary);
        connectionsRef.current = connectionsRef.current.filter((c) => !c.isTemporary);
      }
      
      // Resume searching animation
      searchStateRef.current = {
        isSearching: true,
        targetNode: null,
        searchProgress: 0,
        activatedNodes: new Set(),
        pulseNodes: [],
        startTime: Date.now(),
      };
      
      setHighlightedWord(null);
    }, 500);
  }, []);

  // Keep the ref updated so WebSocket can call it
  useEffect(() => {
    triggerFnRef.current = highlightWord;
  }, [highlightWord]);

  // Initialize WebSocket connection
  useEffect(() => {
    const connectWebSocket = () => {
      const ws = new WebSocket("ws://localhost:8000/ws");
      
      ws.onopen = () => {
        console.log("WebSocket connected to neural graph");
      };
      
      ws.onmessage = (event) => {
        try {
          const data = JSON.parse(event.data);
          if (data.type === "actor_word" && data.word) {
            console.log("Received actor_word via WebSocket:", data.word);
            if (triggerFnRef.current) {
              triggerFnRef.current(data.word);
            }
          }
        } catch (e) {
          // If it's not JSON, treat it as a plain string word
          const word = event.data;
          if (word && !word.startsWith("You said:")) {
            console.log("Received word via WebSocket:", word);
            if (triggerFnRef.current) {
              triggerFnRef.current(word);
            }
          }
        }
      };
      
      ws.onclose = () => {
        console.log("WebSocket disconnected, attempting to reconnect...");
        // Attempt to reconnect after 3 seconds
        setTimeout(connectWebSocket, 3000);
      };
      
      ws.onerror = (error) => {
        console.error("WebSocket error:", error);
      };
      
      wsRef.current = ws;
    };

    connectWebSocket();

    return () => {
      if (wsRef.current) {
        wsRef.current.close();
      }
    };
  }, []);

  // Main animation loop
  useEffect(() => {
    const canvas = canvasRef.current;
    if (!canvas) return;

    const ctx = canvas.getContext("2d");
    const width = canvas.width;
    const height = canvas.height;
    const centerX = width / 2;
    const centerY = height / 2;

    const animate = () => {
      ctx.clearRect(0, 0, width, height);

      const state = searchStateRef.current;
      const isSearching = state.isSearching;
      const elapsed = Date.now() - (state.startTime || Date.now());
      // Use modulo to loop the animation continuously (every 3 seconds)
      const progress = (elapsed % 3000) / 3000;

      // Update node positions (gentle floating)
      nodesRef.current.forEach((node, idx) => {
        // Gentle attraction to center
        const dx = centerX - node.x;
        const dy = centerY - node.y;
        const dist = Math.sqrt(dx * dx + dy * dy);

        if (dist > 150) {
          node.vx += (dx / dist) * 0.02;
          node.vy += (dy / dist) * 0.02;
        }

        // Repulsion from other nodes
        nodesRef.current.forEach((other, otherIdx) => {
          if (idx === otherIdx) return;
          const ox = node.x - other.x;
          const oy = node.y - other.y;
          const oDist = Math.sqrt(ox * ox + oy * oy);
          if (oDist < 60 && oDist > 0) {
            node.vx += (ox / oDist) * 0.3;
            node.vy += (oy / oDist) * 0.3;
          }
        });

        // Apply velocity with damping
        node.vx *= 0.95;
        node.vy *= 0.95;
        node.x += node.vx;
        node.y += node.vy;

        // Bounce off edges
        if (node.x < 50) node.vx += 0.5;
        if (node.x > width - 50) node.vx -= 0.5;
        if (node.y < 30) node.vy += 0.5;
        if (node.y > height - 30) node.vy -= 0.5;

        // Bounce animation for highlighted node
        if (node.highlighted && node.bouncePhase !== undefined) {
          node.bouncePhase += 0.15;
          const bounce = Math.sin(node.bouncePhase) * Math.exp(-node.bouncePhase * 0.3);
          node.currentSize = node.baseSize * 2 + bounce * 15;
          if (node.bouncePhase > 10) {
            node.bouncePhase = undefined;
            node.currentSize = node.baseSize * 1.8;
          }
        }
      });

      // Draw connections
      connectionsRef.current.forEach((conn) => {
        const from = nodesRef.current[conn.from];
        const to = nodesRef.current[conn.to];

        let alpha = 0.08;
        let lineWidth = 1;
        let color = "100, 200, 255";

        // During search, animate connections
        if (isSearching) {
          const waveProgress = (progress * 5 + conn.from * 0.1) % 1;
          if (waveProgress < 0.3) {
            alpha = 0.3 + waveProgress;
            lineWidth = 2;
            color = "0, 255, 150";
          }
        }

        // Connection to highlighted node
        if (from.highlighted || to.highlighted) {
          alpha = 0.5;
          lineWidth = 2;
          color = "255, 215, 0";
        }

        ctx.beginPath();
        ctx.moveTo(from.x, from.y);
        ctx.lineTo(to.x, to.y);
        ctx.strokeStyle = `rgba(${color}, ${alpha})`;
        ctx.lineWidth = lineWidth;
        ctx.stroke();
      });

      // Draw "scanning" pulses during search
      if (isSearching) {
        const numPulses = 3;
        for (let i = 0; i < numPulses; i++) {
          const pulseProgress = ((progress * 2 + i / numPulses) % 1);
          const pulseRadius = pulseProgress * 200;
          const pulseAlpha = (1 - pulseProgress) * 0.3;

          ctx.beginPath();
          ctx.arc(centerX, centerY, pulseRadius, 0, Math.PI * 2);
          ctx.strokeStyle = `rgba(0, 255, 150, ${pulseAlpha})`;
          ctx.lineWidth = 2;
          ctx.stroke();
        }

        // Random "activation" flashes on nodes
        if (Math.random() < 0.1) {
          const randomNode = nodesRef.current[Math.floor(Math.random() * nodesRef.current.length)];
          randomNode.flashAlpha = 1;
        }
      }

      // Draw nodes
      nodesRef.current.forEach((node) => {
        // Flash decay
        if (node.flashAlpha) {
          node.flashAlpha *= 0.9;
          if (node.flashAlpha < 0.1) node.flashAlpha = 0;
        }

        let alpha = node.alpha;
        let glowColor = "127, 216, 255";
        let textColor = "#7fd8ff";

        if (node.highlighted) {
          alpha = 1;
          glowColor = "255, 215, 0";
          textColor = "#ffd700";
        } else if (isSearching && node.flashAlpha) {
          alpha = 0.4 + node.flashAlpha * 0.6;
          glowColor = "0, 255, 150";
        }

        // Glow effect
        ctx.shadowColor = `rgba(${glowColor}, 0.8)`;
        ctx.shadowBlur = node.highlighted ? 20 : 8;

        // Draw node circle
        ctx.beginPath();
        ctx.arc(node.x, node.y, node.currentSize / 3, 0, Math.PI * 2);
        ctx.fillStyle = `rgba(${glowColor}, ${alpha * 0.3})`;
        ctx.fill();

        ctx.shadowBlur = 0;

        // Draw label
        ctx.font = `${Math.floor(node.currentSize)}px "Courier New", monospace`;
        ctx.fillStyle = textColor;
        ctx.globalAlpha = alpha;
        ctx.textAlign = "center";
        ctx.textBaseline = "middle";
        ctx.fillText(node.label, node.x, node.y);
        ctx.globalAlpha = 1;
      });

      animationRef.current = requestAnimationFrame(animate);
    };

    animate();

    return () => {
      if (animationRef.current) {
        cancelAnimationFrame(animationRef.current);
      }
    };
  }, [highlightedWord]);

  return (
    <div className="neural-graph-container">
      <div className="neural-graph-header">
        <span className="neural-title">NEURAL MATCHER</span>
      </div>
      <canvas
        ref={canvasRef}
        width={400}
        height={300}
        className="neural-canvas"
      />
    </div>
  );
}
