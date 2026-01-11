import React, { useEffect, useRef, useState } from "react";
import "./App.css";
import NeuralGraph from "./NeuralGraph";

/**
 * GLOBAL BUFFERS (persist outside React renders)
 */
let actor_lines = [];
let critic_lines = [];

const TYPE_INTERVAL = 18;

// ASCII Art Logo
const ASCII_LOGO = `
                                       ,,           ,,        
      db                 mm            db          *MM        
     ;MM:                MM                         MM        
    ,V^MM.  \`7MM  \`7MM mmMMmm ,pW"Wq.\`7MM  ,pW"Wq.  MM,dMMb.  
   ,M  \`MM    MM    MM   MM  6W'   \`Wb MM 6W'   \`Wb MM    \`Mb 
   AbmmmqMA   MM    MM   MM  8M     M8 MM 8M     M8 MM     M8 
  A'     VML  MM    MM   MM  YA.   ,A9 MM YA.   ,A9 MM.   ,M9 
.AMA.   .AMMA.\`Mbod"YML. \`Mbmo\`Ybmd9'  MM  \`Ybmd9'  P^YbmdP'  
                                    QO MP                     
                                    \`bmP                      
`;

export default function App() {
  // ==================== STATE ====================
  const [currentView, setCurrentView] = useState("home"); // home, single, batch, profile, running
  const [singleUrl, setSingleUrl] = useState("");
  const [batchUrls, setBatchUrls] = useState("");
  const [profileData, setProfileData] = useState(getDefaultProfile());
  const [typedText, setTypedText] = useState("");
  const [showCursor, setShowCursor] = useState(true);

  // Running state
  const [actorDisplay, setActorDisplay] = useState([
    { ts: "", text: ">> Critic module standby...\n" },
  ]);
  const [criticDisplay, setCriticDisplay] = useState([
    { text: ">> Awaiting uplink... establishing signal...\n" },
  ]);
  const [isActorTyping, setIsActorTyping] = useState(false);
  const [isCriticTyping, setIsCriticTyping] = useState(false);
  const [actorLineCount, setActorLineCount] = useState(0);
  const [criticLineCount, setCriticLineCount] = useState(0);

  const actorQueue = useRef([]);
  const criticQueue = useRef([]);
  const actorTyping = useRef(false);
  const criticTyping = useRef(false);
  const actorEndRef = useRef(null);
  const criticEndRef = useRef(null);

  // ==================== TYPING EFFECT FOR HERO ====================
  useEffect(() => {
    if (currentView !== "home") return;
    
    const tagline = "Automate your job applications with AI";
    let i = 0;
    setTypedText("");
    
    const typeInterval = setInterval(() => {
      if (i < tagline.length) {
        setTypedText(tagline.slice(0, i + 1));
        i++;
      } else {
        clearInterval(typeInterval);
      }
    }, 50);

    return () => clearInterval(typeInterval);
  }, [currentView]);

  // Cursor blink
  useEffect(() => {
    const cursorInterval = setInterval(() => {
      setShowCursor(prev => !prev);
    }, 530);
    return () => clearInterval(cursorInterval);
  }, []);

  // ==================== HANDLERS ====================
  const handleSingleSubmit = async () => {
    if (!singleUrl.trim()) return;
    setCurrentView("running");
    
    try {
      await fetch("http://localhost:8000/apply", {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ url: singleUrl }),
      });
    } catch (err) {
      console.error("Failed to POST /apply", err);
    }
  };

  const handleBatchSubmit = async () => {
    if (!batchUrls.trim()) return;
    const urls = batchUrls.split("\n").filter(u => u.trim());
    if (urls.length === 0) return;
    
    setCurrentView("running");
    
    // Submit first URL, queue the rest
    try {
      await fetch("http://localhost:8000/apply", {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ url: urls[0], batch: urls }),
      });
    } catch (err) {
      console.error("Failed to POST batch /apply", err);
    }
  };

  const handleProfileSave = async () => {
    try {
      await fetch("http://localhost:8000/save_profile", {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify(profileData),
      });
      alert("Profile saved successfully!");
    } catch (err) {
      console.error("Failed to save profile", err);
      alert("Failed to save profile");
    }
  };

  // Helper to update nested profile data
  const updateProfile = (path, value) => {
    setProfileData(prev => {
      const newData = JSON.parse(JSON.stringify(prev));
      const keys = path.split(".");
      let obj = newData;
      for (let i = 0; i < keys.length - 1; i++) {
        const key = isNaN(keys[i]) ? keys[i] : parseInt(keys[i]);
        if (!obj[key]) obj[key] = {};
        obj = obj[key];
      }
      const lastKey = isNaN(keys[keys.length - 1]) ? keys[keys.length - 1] : parseInt(keys[keys.length - 1]);
      obj[lastKey] = value;
      return newData;
    });
  };

  // ==================== WEBSOCKET FOR RUNNING VIEW ====================
  useEffect(() => {
    if (currentView !== "running") return;

    const connectWebSocket = () => {
      const ws = new WebSocket("ws://localhost:8000/ws");
      
      ws.onopen = () => console.log("WebSocket connected");
      
      ws.onmessage = (event) => {
        try {
          const data = JSON.parse(event.data);
          
          if (data.type === "actor_line" && data.ts && data.text) {
            actorQueue.current.push({ ts: data.ts, text: data.text });
            setActorLineCount(prev => prev + 1);
          }
          
          if (data.type === "critic_line" && data.line) {
            criticQueue.current.push(data.line);
            setCriticLineCount(prev => prev + 1);
          }
        } catch (e) {
          // Ignore non-JSON
        }
      };
      
      ws.onclose = () => setTimeout(connectWebSocket, 3000);
      ws.onerror = (error) => console.error("WebSocket error:", error);
      
      return ws;
    };

    const ws = connectWebSocket();
    return () => ws?.close();
  }, [currentView]);

  // ==================== TYPING ENGINES ====================
  useEffect(() => {
    if (currentView !== "running") return;

    const tick = () => {
      if (actorTyping.current || actorQueue.current.length === 0) {
        if (actorQueue.current.length === 0) setIsActorTyping(false);
        return;
      }

      const { ts, text } = actorQueue.current.shift();
      actorTyping.current = true;
      setIsActorTyping(true);

      setActorDisplay((prev) => [...prev, { ts: formatTs(ts), text: "" }]);

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
          setTimeout(() => {
            if (actorQueue.current.length === 0) setIsActorTyping(false);
          }, 300);
        }
      }, TYPE_INTERVAL);
    };

    const id = setInterval(tick, 40);
    return () => clearInterval(id);
  }, [currentView]);

  useEffect(() => {
    if (currentView !== "running") return;

    const tick = () => {
      if (criticTyping.current || criticQueue.current.length === 0) {
        if (criticQueue.current.length === 0) setIsCriticTyping(false);
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
          setTimeout(() => {
            if (criticQueue.current.length === 0) setIsCriticTyping(false);
          }, 300);
        }
      }, TYPE_INTERVAL);
    };

    const id = setInterval(tick, 40);
    return () => clearInterval(id);
  }, [currentView]);

  // Auto-scroll
  useEffect(() => {
    actorEndRef.current?.scrollIntoView({ behavior: "smooth" });
  }, [actorDisplay]);

  useEffect(() => {
    criticEndRef.current?.scrollIntoView({ behavior: "smooth" });
  }, [criticDisplay]);

  // ==================== RENDER ====================
  if (currentView === "running") {
    return (
      <div className="app running">
        <div className="main-layout visible">
          <div className="split-terminals">
            <div className="terminal actor">
              <div className="terminal-header">
                CRITIC
                <span className="status-indicator">
                  <span className="status-dot" />
                  {isActorTyping ? "PROCESSING" : "READY"}
                </span>
              </div>
              <div className="terminal-body">
                {actorDisplay.map((line, idx) => (
                  <div key={idx} className="line">
                    {line.ts && <span className="timestamp">[{line.ts}]</span>}
                    <span>{line.text}</span>
                  </div>
                ))}
                {isActorTyping && <span className="typing-caret" />}
                <div ref={actorEndRef} />
              </div>
            </div>

            <div className="terminal-divider" />

            <div className="terminal critic">
              <div className="terminal-header">
                ACTOR
                <span className="status-indicator">
                  <span className="status-dot" />
                  {isCriticTyping ? "ANALYZING" : "STANDBY"}
                </span>
              </div>
              <div className="terminal-body">
                {criticDisplay.map((line, idx) => (
                  <div key={idx} className="line">{line.text}</div>
                ))}
                {isCriticTyping && <span className="typing-caret" />}
                <div ref={criticEndRef} />
              </div>
            </div>
          </div>

          <div className="neural-panel">
            <NeuralGraph
              actorLines={actorLineCount}
              criticLines={criticLineCount}
              isSearching={isActorTyping || isCriticTyping}
            />
          </div>
        </div>
      </div>
    );
  }

  return (
    <div className="app home">
      {/* Navigation */}
      <nav className="nav-bar">
        <div className="nav-brand" onClick={() => setCurrentView("home")}>
          <span className="nav-symbol">&gt;</span> AUTOJOB
        </div>
        <div className="nav-links">
          <button 
            className={`nav-link ${currentView === "single" ? "active" : ""}`}
            onClick={() => setCurrentView("single")}
          >
            [1] SINGLE
          </button>
          <button 
            className={`nav-link ${currentView === "batch" ? "active" : ""}`}
            onClick={() => setCurrentView("batch")}
          >
            [2] BATCH
          </button>
          <button 
            className={`nav-link ${currentView === "profile" ? "active" : ""}`}
            onClick={() => setCurrentView("profile")}
          >
            [3] PROFILE
          </button>
        </div>
      </nav>

      {/* Home View */}
      {currentView === "home" && (
        <div className="hero-section">
          <pre className="ascii-logo">{ASCII_LOGO}</pre>
          <p className="tagline">
            {typedText}
            <span className={`cursor ${showCursor ? "visible" : ""}`}>█</span>
          </p>
          <div className="hero-buttons">
            <button className="hero-btn primary" onClick={() => setCurrentView("single")}>
              <span className="btn-icon">▶</span> Start Application
            </button>
            <button className="hero-btn secondary" onClick={() => setCurrentView("profile")}>
              <span className="btn-icon">◆</span> Setup Profile
            </button>
          </div>
          <div className="hero-stats">
            <div className="stat">
              <span className="stat-value">∞</span>
              <span className="stat-label">Applications</span>
            </div>
            <div className="stat">
              <span className="stat-value">AI</span>
              <span className="stat-label">Powered</span>
            </div>
            <div className="stat">
              <span className="stat-value">0</span>
              <span className="stat-label">Effort</span>
            </div>
          </div>
        </div>
      )}

      {/* Single URL View */}
      {currentView === "single" && (
        <div className="form-section">
          <div className="form-container">
            <div className="form-header">
              <span className="form-icon">◉</span>
              <h2>SINGLE APPLICATION</h2>
            </div>
            <p className="form-desc">&gt; Enter the job application URL to begin automated submission</p>
            
            <div className="input-group">
              <label className="input-label">TARGET_URL:</label>
              <input
                type="text"
                className="terminal-input"
                value={singleUrl}
                onChange={(e) => setSingleUrl(e.target.value)}
                placeholder="https://careers.company.com/apply/..."
                onKeyDown={(e) => e.key === "Enter" && handleSingleSubmit()}
                autoFocus
              />
            </div>

            <div className="form-actions">
              <button className="action-btn primary" onClick={handleSingleSubmit}>
                <span className="btn-prefix">&gt;</span> EXECUTE
              </button>
              <button className="action-btn secondary" onClick={() => setCurrentView("home")}>
                <span className="btn-prefix">×</span> ABORT
              </button>
            </div>
          </div>
        </div>
      )}

      {/* Batch URL View */}
      {currentView === "batch" && (
        <div className="form-section">
          <div className="form-container wide">
            <div className="form-header">
              <span className="form-icon">◎</span>
              <h2>BATCH PROCESSING</h2>
            </div>
            <p className="form-desc">&gt; Enter multiple URLs (one per line) for sequential processing</p>
            
            <div className="input-group">
              <label className="input-label">URL_QUEUE[]:</label>
              <textarea
                className="terminal-textarea"
                value={batchUrls}
                onChange={(e) => setBatchUrls(e.target.value)}
                placeholder={"https://job1.com/apply\nhttps://job2.com/apply\nhttps://job3.com/apply"}
                rows={8}
                autoFocus
              />
            </div>

            <div className="batch-info">
              <span className="batch-count">
                {batchUrls.split("\n").filter(u => u.trim()).length} URLs queued
              </span>
            </div>

            <div className="form-actions">
              <button className="action-btn primary" onClick={handleBatchSubmit}>
                <span className="btn-prefix">&gt;</span> EXECUTE_BATCH
              </button>
              <button className="action-btn secondary" onClick={() => setCurrentView("home")}>
                <span className="btn-prefix">×</span> ABORT
              </button>
            </div>
          </div>
        </div>
      )}

      {/* Profile View */}
      {currentView === "profile" && (
        <div className="form-section profile">
          <div className="form-container wide">
            <div className="form-header">
              <span className="form-icon">◈</span>
              <h2>USER PROFILE CONFIGURATION</h2>
            </div>
            <p className="form-desc">&gt; Configure your profile data for automated form filling</p>
            
            <div className="profile-grid">
              {/* Personal Information */}
              <fieldset className="profile-section">
                <legend>▸ PERSONAL_INFO</legend>
                <div className="field-row">
                  <label>first_name:</label>
                  <input
                    type="text"
                    value={profileData.personal_information.legal_name.first_name}
                    onChange={(e) => updateProfile("personal_information.legal_name.first_name", e.target.value)}
                  />
                </div>
                <div className="field-row">
                  <label>last_name:</label>
                  <input
                    type="text"
                    value={profileData.personal_information.legal_name.last_name}
                    onChange={(e) => updateProfile("personal_information.legal_name.last_name", e.target.value)}
                  />
                </div>
                <div className="field-row">
                  <label>preferred_name:</label>
                  <input
                    type="text"
                    value={profileData.personal_information.preferred_name.first_name}
                    onChange={(e) => updateProfile("personal_information.preferred_name.first_name", e.target.value)}
                  />
                </div>
                <div className="field-row">
                  <label>date_of_birth:</label>
                  <input
                    type="text"
                    value={profileData.personal_information.date_of_birth}
                    onChange={(e) => updateProfile("personal_information.date_of_birth", e.target.value)}
                    placeholder="YYYY-MM-DD"
                  />
                </div>
              </fieldset>

              {/* Contact Information */}
              <fieldset className="profile-section">
                <legend>▸ CONTACT_INFO</legend>
                <div className="field-row">
                  <label>email:</label>
                  <input
                    type="email"
                    value={profileData.contact_information.email}
                    onChange={(e) => updateProfile("contact_information.email", e.target.value)}
                  />
                </div>
                <div className="field-row">
                  <label>phone:</label>
                  <input
                    type="text"
                    value={profileData.contact_information.phone.phone_number}
                    onChange={(e) => updateProfile("contact_information.phone.phone_number", e.target.value)}
                  />
                </div>
                <div className="field-row">
                  <label>city:</label>
                  <input
                    type="text"
                    value={profileData.contact_information.address.city}
                    onChange={(e) => updateProfile("contact_information.address.city", e.target.value)}
                  />
                </div>
                <div className="field-row">
                  <label>country:</label>
                  <input
                    type="text"
                    value={profileData.contact_information.address.country}
                    onChange={(e) => updateProfile("contact_information.address.country", e.target.value)}
                  />
                </div>
              </fieldset>

              {/* Education */}
              <fieldset className="profile-section">
                <legend>▸ EDUCATION</legend>
                <div className="field-row">
                  <label>university:</label>
                  <input
                    type="text"
                    value={profileData.education[0]?.university || ""}
                    onChange={(e) => updateProfile("education.0.university", e.target.value)}
                  />
                </div>
                <div className="field-row">
                  <label>major:</label>
                  <input
                    type="text"
                    value={profileData.education[0]?.major || ""}
                    onChange={(e) => updateProfile("education.0.major", e.target.value)}
                  />
                </div>
                <div className="field-row">
                  <label>degree:</label>
                  <input
                    type="text"
                    value={profileData.education[0]?.degree_type || ""}
                    onChange={(e) => updateProfile("education.0.degree_type", e.target.value)}
                  />
                </div>
                <div className="field-row">
                  <label>gpa:</label>
                  <input
                    type="text"
                    value={profileData.education[0]?.gpa || ""}
                    onChange={(e) => updateProfile("education.0.gpa", e.target.value)}
                  />
                </div>
              </fieldset>

              {/* Skills */}
              <fieldset className="profile-section">
                <legend>▸ SKILLS</legend>
                <div className="field-row">
                  <label>languages:</label>
                  <input
                    type="text"
                    value={profileData.skills.programming_languages.join(", ")}
                    onChange={(e) => updateProfile("skills.programming_languages", e.target.value.split(",").map(s => s.trim()))}
                    placeholder="Python, Java, JavaScript..."
                  />
                </div>
                <div className="field-row">
                  <label>frameworks:</label>
                  <input
                    type="text"
                    value={profileData.skills.frameworks_tools.join(", ")}
                    onChange={(e) => updateProfile("skills.frameworks_tools", e.target.value.split(",").map(s => s.trim()))}
                    placeholder="React, Node.js, Django..."
                  />
                </div>
                <div className="field-row">
                  <label>web_tech:</label>
                  <input
                    type="text"
                    value={profileData.skills.web_technologies.join(", ")}
                    onChange={(e) => updateProfile("skills.web_technologies", e.target.value.split(",").map(s => s.trim()))}
                    placeholder="HTML, CSS, REST..."
                  />
                </div>
              </fieldset>

              {/* Socials */}
              <fieldset className="profile-section">
                <legend>▸ SOCIALS</legend>
                <div className="field-row">
                  <label>linkedin:</label>
                  <input
                    type="text"
                    value={profileData.socials.linkedin}
                    onChange={(e) => updateProfile("socials.linkedin", e.target.value)}
                  />
                </div>
                <div className="field-row">
                  <label>github:</label>
                  <input
                    type="text"
                    value={profileData.socials.github}
                    onChange={(e) => updateProfile("socials.github", e.target.value)}
                  />
                </div>
                <div className="field-row">
                  <label>website:</label>
                  <input
                    type="text"
                    value={profileData.socials.website}
                    onChange={(e) => updateProfile("socials.website", e.target.value)}
                  />
                </div>
              </fieldset>

              {/* Work Experience Preview */}
              <fieldset className="profile-section">
                <legend>▸ WORK_EXPERIENCE</legend>
                <div className="field-row">
                  <label>job_title:</label>
                  <input
                    type="text"
                    value={profileData.work_experience[0]?.job_title || ""}
                    onChange={(e) => updateProfile("work_experience.0.job_title", e.target.value)}
                  />
                </div>
                <div className="field-row">
                  <label>company:</label>
                  <input
                    type="text"
                    value={profileData.work_experience[0]?.company || ""}
                    onChange={(e) => updateProfile("work_experience.0.company", e.target.value)}
                  />
                </div>
                <div className="field-row">
                  <label>description:</label>
                  <textarea
                    value={profileData.work_experience[0]?.description || ""}
                    onChange={(e) => updateProfile("work_experience.0.description", e.target.value)}
                    rows={2}
                  />
                </div>
              </fieldset>
            </div>

            <div className="form-actions">
              <button className="action-btn primary" onClick={handleProfileSave}>
                <span className="btn-prefix">&gt;</span> SAVE_PROFILE
              </button>
              <button className="action-btn secondary" onClick={() => setCurrentView("home")}>
                <span className="btn-prefix">×</span> CANCEL
              </button>
            </div>
          </div>
        </div>
      )}

      {/* Footer */}
      <footer className="footer">
        <span className="footer-text">AUTOJOB v1.0.0 | SYSTEM READY</span>
        <span className="footer-status">
          <span className="status-dot green"></span> ONLINE
        </span>
      </footer>
    </div>
  );
}

function getDefaultProfile() {
  return {
    personal_information: {
      legal_name: { first_name: "", middle_name: "", last_name: "", prefix: "" },
      preferred_name: { first_name: "", last_name: "" },
      date_of_birth: ""
    },
    contact_information: {
      address: { street: "", city: "", province: "", country: "", postal_code: "" },
      email: "",
      phone: { device_type: "Mobile", country_code: "Canada (+1)", phone_number: "" }
    },
    residence_status: { citizenships: "", visa_status: "", sponsorship: "" },
    diversity: { sex: "", identity: "", lgbtq: "", disability: "", race: "" },
    work_experience: [{ job_title: "", company: "", location: "", start_date: "", end_date: "", description: "" }],
    languages: [{ language: "", is_fluent: "", proficiency: { comprehension: "", reading: "", speaking: "", writing: "" } }],
    education: [{ university: "", faculty: "", major: "", degree_type: "", start_date: "", end_date: "", gpa: "", current_year: "" }],
    skills: { programming_languages: [], web_technologies: [], data_science: [], frameworks_tools: [], operating_systems: [] },
    socials: { website: "", linkedin: "", github: "" },
    application_preferences: { how_did_you_hear_about_us: "LinkedIn", has_worked_for_company_before: "" }
  };
}

function formatTs(ts) {
  if (!ts) return "";
  return ts.replace("T", " ").split(".")[0];
}
