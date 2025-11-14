import { useState, useRef, useEffect } from "react";
import axios from "axios";

// Base API URL comes from Vite env. Create `.env.local` with `VITE_API_URL`.
const API_BASE = import.meta.env.VITE_API_URL || 'http://localhost:8080';

function App() {
  const [input, setInput] = useState("");
  const [messages, setMessages] = useState([]);

  async function sendMessage() {
    if (!input || !input.trim()) return;

      try {
      const res = await axios.post(`${API_BASE}/query`, {
        query: input
      });

      const results = res.data.results || [];

      // Confidence threshold (read from Vite env; default 0.12)
      const CONF_THRESHOLD = parseFloat(import.meta.env.VITE_CONFIDENCE_THRESHOLD ?? '0.12');

      // Only keep results that have a numeric score and meet the threshold
      const filtered = results.filter(r => typeof r.score === 'number' && r.score >= CONF_THRESHOLD);

      const answer = filtered.length > 0
        ? filtered.map((r, i) => `${i + 1}. ${r.text} (source: ${r.source}, score: ${r.score.toFixed(3)})`).join("\n\n")
        : "No high-confidence results found.";

      const sources = filtered.map(r => r.source);

      setMessages([
        ...messages,
        { from: "user", text: input },
        { from: "bot", text: answer, sources }
      ]);

      setInput("");
    } catch (err) {
      console.error(err);
      const errMsg = err.response?.data?.detail || err.message || String(err);
      setMessages([
        ...messages,
        { from: "user", text: input },
        { from: "bot", text: `Error: ${errMsg}` }
      ]);
      setInput("");
    }
  }

  // UI styling
  const styles = {
    container: {
      maxWidth: 900,
      margin: '24px auto',
      padding: 24,
      fontFamily: 'Inter, Roboto, system-ui, -apple-system, "Segoe UI", sans-serif',
      color: '#111827'
    },
    header: {
      display: 'flex',
      alignItems: 'center',
      gap: 12,
      marginBottom: 16
    },
    title: {
      margin: 0,
      fontSize: 20
    },
    chatWindow: {
      height: '60vh',
      border: '1px solid #e5e7eb',
      borderRadius: 12,
      padding: 16,
      overflowY: 'auto',
      background: '#ffffff'
    },
    messageRow: {
      display: 'flex',
      marginBottom: 12
    },
    userRow: {
      justifyContent: 'flex-end'
    },
    bubble: {
      maxWidth: '75%',
      padding: '10px 14px',
      borderRadius: 12,
      lineHeight: 1.4,
      whiteSpace: 'pre-wrap',
      boxShadow: '0 1px 2px rgba(0,0,0,0.03)'
    },
    userBubble: {
      background: '#111827',
      color: '#fff',
      borderBottomRightRadius: 4
    },
    botBubble: {
      background: '#f3f4f6',
      color: '#111827',
      borderBottomLeftRadius: 4
    },
    sources: {
      marginTop: 8,
      fontSize: 12,
      color: '#6b7280'
    },
    inputRow: {
      display: 'flex',
      gap: 8,
      marginTop: 12
    },
    input: {
      flex: 1,
      padding: '10px 12px',
      borderRadius: 8,
      border: '1px solid #d1d5db',
      fontSize: 14
    },
    button: {
      padding: '10px 16px',
      borderRadius: 8,
      border: 'none',
      background: '#2563eb',
      color: '#fff',
      cursor: 'pointer'
    },
    buttonDisabled: {
      background: '#93c5fd',
      cursor: 'not-allowed'
    }
  };

  const chatRef = useRef(null);
  useEffect(() => {
    // scroll to bottom when messages update
    if (chatRef.current) {
      chatRef.current.scrollTop = chatRef.current.scrollHeight;
    }
  }, [messages]);

  return (
    <div style={styles.container}>
      <div style={styles.header}>
        <h1 style={styles.title}>Legal RAG Chat</h1>
      </div>

      <div ref={chatRef} style={styles.chatWindow}>
        {messages.map((m, i) => {
          const isUser = m.from === 'user';
          return (
            <div
              key={i}
              style={{
                ...styles.messageRow,
                ...(isUser ? styles.userRow : {})
              }}
            >
              <div
                style={{
                  ...styles.bubble,
                  ...(isUser ? styles.userBubble : styles.botBubble)
                }}
              >
                <div>{m.text}</div>
                {m.sources && m.sources.length > 0 && (
                  <div style={styles.sources}>Sources: {m.sources.join(', ')}</div>
                )}
              </div>
            </div>
          );
        })}
      </div>

      <div style={styles.inputRow}>
        <input
          style={styles.input}
          value={input}
          placeholder="Ask a legal question..."
          onChange={(e) => setInput(e.target.value)}
          onKeyDown={(e) => { if (e.key === 'Enter') sendMessage(); }}
        />

        <button
          onClick={sendMessage}
          style={{
            ...styles.button,
            ...(!input || !input.trim() ? styles.buttonDisabled : {})
          }}
          disabled={!input || !input.trim()}
        >
          Send
        </button>
      </div>
    </div>
  );
}

export default App;
