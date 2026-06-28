import { useState, useEffect, useRef } from "react";
import axios from "axios";
import "./App.css";

const SUGGESTED_QUESTIONS = [
  "Who is the president of the club?",
  "Best performer yaaru?",
  "Inactive members yaaru?",
  "Next president ku yaaru suitable?",
  "Club summary sollu",
  "Arun pathi sollu",
];

function App() {
  const [messages, setMessages] = useState([]);
  const [input, setInput] = useState("");
  const [loading, setLoading] = useState(false);
  const [stats, setStats] = useState(null);
  const [showSuggestions, setShowSuggestions] = useState(true);
  const chatEndRef = useRef(null);
  const inputRef = useRef(null);

  useEffect(() => {
    axios.get("http://localhost:8000/stats")
      .then(res => setStats(res.data))
      .catch(err => console.log(err));
  }, []);

  useEffect(() => {
    chatEndRef.current?.scrollIntoView({ behavior: "smooth" });
  }, [messages]);

  const askAgent = async (question) => {
    if (!question.trim() || loading) return;
    setShowSuggestions(false);

    const userMsg = { role: "user", content: question, time: new Date() };
    setMessages(prev => [...prev, userMsg]);
    setInput("");
    setLoading(true);

    try {
      const res = await axios.post("http://localhost:8000/ask", { question });
      setMessages(prev => [...prev, {
        role: "agent",
        content: res.data.answer,
        time: new Date()
      }]);
    } catch (err) {
      setMessages(prev => [...prev, {
        role: "agent",
        content: "Something went wrong. Please try again!",
        time: new Date()
      }]);
    }
    setLoading(false);
    inputRef.current?.focus();
  };

  const formatTime = (date) => {
    return date?.toLocaleTimeString([], { hour: '2-digit', minute: '2-digit' });
  };

  const clearChat = () => {
    setMessages([]);
    setShowSuggestions(true);
  };

  return (
    <div className="app">
      {/* Sidebar */}
      <div className="sidebar">
        <div className="sidebar-header">
          <div className="logo">⚡</div>
          <span>TechNova</span>
        </div>

        <button className="new-chat-btn" onClick={clearChat}>
          <span>+</span> New Chat
        </button>

        {stats && (
          <div className="stats-panel">
            <p className="stats-title">Club Stats</p>
            <div className="stat-item">
              <span>Total Members</span>
              <span className="stat-val">{stats.total_members}</span>
            </div>
            <div className="stat-item">
              <span>Active</span>
              <span className="stat-val green">{stats.active_members}</span>
            </div>
            <div className="stat-item">
              <span>Inactive</span>
              <span className="stat-val red">{stats.inactive_members}</span>
            </div>
            <div className="stat-item">
              <span>Events</span>
              <span className="stat-val">{stats.total_events}</span>
            </div>
            <div className="stat-item">
              <span>Attendance</span>
              <span className="stat-val">{stats.average_attendance}%</span>
            </div>
          </div>
        )}

        <div className="sidebar-footer">
          <div className="club-info">
            <div className="club-avatar">KCE</div>
            <div>
              <p className="club-name">TechNova Club</p>
              <p className="club-college">Karpagam College</p>
            </div>
          </div>
        </div>
      </div>

      {/* Main Chat */}
      <div className="main">
        {/* Top Bar */}
        <div className="topbar">
          <div className="topbar-left">
            <div className="agent-avatar">🤖</div>
            <div>
              <p className="agent-name">TechNova AI Agent</p>
              <p className="agent-status">
                <span className="status-dot"></span> Online
              </p>
            </div>
          </div>
          <div className="topbar-right">
            <button className="clear-btn" onClick={clearChat}>Clear</button>
          </div>
        </div>

        {/* Messages */}
        <div className="messages">
          {messages.length === 0 && showSuggestions && (
            <div className="welcome">
              <div className="welcome-icon">⚡</div>
              <h2>TechNova Club AI Agent</h2>
              <p>Ask me anything about the club — English, Tamil, or Tanglish!</p>

              <div className="suggestion-grid">
                {SUGGESTED_QUESTIONS.map((q, i) => (
                  <button
                    key={i}
                    className="suggestion-card"
                    onClick={() => askAgent(q)}
                  >
                    <span className="suggestion-icon">💬</span>
                    <span>{q}</span>
                  </button>
                ))}
              </div>
            </div>
          )}

          {messages.map((msg, i) => (
            <div key={i} className={`message-row ${msg.role}`}>
              <div className="avatar">
                {msg.role === "user" ? "👤" : "🤖"}
              </div>
              <div className="bubble-wrap">
                <div className="bubble">
                  {msg.content}
                </div>
                <span className="time">{formatTime(msg.time)}</span>
              </div>
            </div>
          ))}

          {loading && (
            <div className="message-row agent">
              <div className="avatar">🤖</div>
              <div className="bubble-wrap">
                <div className="bubble typing-bubble">
                  <div className="typing-dots">
                    <span></span><span></span><span></span>
                  </div>
                  <span className="typing-text">Analyzing club data...</span>
                </div>
              </div>
            </div>
          )}
          <div ref={chatEndRef} />
        </div>

        {/* Quick Suggestions (while chatting) */}
        {messages.length > 0 && (
          <div className="quick-suggestions">
            {SUGGESTED_QUESTIONS.slice(0, 3).map((q, i) => (
              <button
                key={i}
                className="quick-btn"
                onClick={() => askAgent(q)}
                disabled={loading}
              >
                {q}
              </button>
            ))}
          </div>
        )}

        {/* Input */}
        <div className="input-bar">
          <div className="input-wrap">
            <input
              ref={inputRef}
              type="text"
              value={input}
              onChange={e => setInput(e.target.value)}
              onKeyPress={e => e.key === "Enter" && askAgent(input)}
              placeholder="Ask anything in English, Tamil, or Tanglish..."
              disabled={loading}
            />
            <button
              className="send-btn"
              onClick={() => askAgent(input)}
              disabled={loading || !input.trim()}
            >
              {loading ? "..." : "➤"}
            </button>
          </div>
          <p className="input-hint">
            Try: "Arun pathi sollu" • "யாரு best performer?" • "Club summary"
          </p>
        </div>
      </div>
    </div>
  );
}

export default App;