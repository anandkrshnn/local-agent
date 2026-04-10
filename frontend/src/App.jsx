/**
 * Local Agent v4.0 Ultimate Edition - React Frontend
 * Features: High-end Cyber-Glass UI, System Dashboard, Hardened Connection
 */

import React, { useState, useEffect, useRef, useCallback } from 'react';
import './App.css';

function App() {
  const [messages, setMessages] = useState([
    { id: 1, role: 'assistant', content: "Welcome to Local Agent v4.0 Ultimate. System is hardened and ready for high-assurance tasks.", timestamp: Date.now() }
  ]);
  const [input, setInput] = useState('');
  const [isConnected, setIsConnected] = useState(false);
  const [isConnecting, setIsConnecting] = useState(false);
  const [systemStats, setSystemStats] = useState(null);
  const [apiUrl, setApiUrl] = useState(localStorage.getItem('api_url') || 'http://localhost:8000');
  const [apiKey, setApiKey] = useState(localStorage.getItem('api_key') || '');
  const [sessionId] = useState(localStorage.getItem('session_id') || crypto.randomUUID());
  const [showAuth, setShowAuth] = useState(!localStorage.getItem('api_key'));
  
  const wsRef = useRef(null);
  const messagesEndRef = useRef(null);

  // Poll for system stats
  useEffect(() => {
    if (!isConnected && !apiKey) return;

    const fetchStats = async () => {
      try {
        const res = await fetch(`${apiUrl}/api/system/stats`, {
          headers: { 'X-API-Key': apiKey }
        });
        if (res.ok) {
          const data = await res.json();
          setSystemStats(data);
        }
      } catch (err) {
        console.error("Stats fetch error:", err);
      }
    };

    fetchStats();
    const interval = setInterval(fetchStats, 5000);
    return () => clearInterval(interval);
  }, [isConnected, apiUrl, apiKey]);

  // WebSocket Logic
  const connect = useCallback((url, key) => {
    if (isConnecting) return;
    setIsConnecting(true);
    
    // Ensure data dir exists on backend (handled by run_prod.ps1)
    localStorage.setItem('session_id', sessionId);
    
    const wsUrl = `${url.replace('http', 'ws')}/ws/chat/${sessionId}?api_key=${encodeURIComponent(key)}`;
    const ws = new WebSocket(wsUrl);
    wsRef.current = ws;

    ws.onopen = () => {
      setIsConnected(true);
      setIsConnecting(false);
      setShowAuth(false);
    };

    ws.onclose = () => {
      setIsConnected(false);
      setIsConnecting(false);
      // Auto reconnect
      setTimeout(() => connect(url, key), 10000);
    };

    ws.onmessage = (event) => {
      try {
        const data = JSON.parse(event.data);
        if (data.type === 'response') {
          setMessages(prev => [...prev, { 
            id: Date.now(), 
            role: 'assistant', 
            content: data.content, 
            provider: data.provider, 
            latency: data.latency_ms,
            timestamp: Date.now() 
          }]);
        }
      } catch (e) { console.error("WS Message Parse Error", e); }
    };
  }, [sessionId, isConnecting]);

  useEffect(() => {
    if (apiUrl && apiKey) connect(apiUrl, apiKey);
  }, []);

  useEffect(() => {
    messagesEndRef.current?.scrollIntoView({ behavior: 'smooth' });
  }, [messages]);

  const handleSend = () => {
    if (!input.trim() || !isConnected) return;
    
    const userMsg = input.trim();
    setMessages(prev => [...prev, { id: Date.now(), role: 'user', content: userMsg, timestamp: Date.now() }]);
    setInput('');
    
    if (wsRef.current?.readyState === WebSocket.OPEN) {
      wsRef.current.send(JSON.stringify({ type: 'chat', content: userMsg }));
    }
  };

  if (showAuth) {
    return (
      <div className="auth-overlay">
        <div className="auth-panel">
          <h1>AGENT 4.0</h1>
          <div className="field">
            <label>Server Endpoint</label>
            <input value={apiUrl} onChange={e => setApiUrl(e.target.value)} placeholder="http://localhost:8000" />
          </div>
          <div className="field">
            <label>Master API Key</label>
            <input type="password" value={apiKey} onChange={e => setApiKey(e.target.value)} placeholder="Enter secure key" />
          </div>
          <button className="primary-btn" onClick={() => {
            localStorage.setItem('api_url', apiUrl);
            localStorage.setItem('api_key', apiKey);
            connect(apiUrl, apiKey);
          }}>
            Initialize Secure Link
          </button>
        </div>
      </div>
    );
  }

  return (
    <div className="ultimate-app">
      {/* Sidebar Dashboard */}
      <aside className="system-dashboard">
        <div className="dashboard-header">
          <h2><span>🤖</span> CORE STATUS</h2>
        </div>

        <div className="stat-group">
          <span className="stat-label">AI Runtime</span>
          <div className="stat-card">
            <span className="stat-value">{systemStats?.db?.db_type?.toUpperCase() || 'OFFLINE'}</span>
            <small style={{color: 'var(--text-dim)'}}>Vector Memory: DuckDB</small>
          </div>
        </div>

        <div className="stat-group">
          <span className="stat-label">System Resources</span>
          <div className="stat-card">
            <div style={{display: 'flex', justifyContent: 'space-between'}}>
              <span>CPU Load</span>
              <span>{systemStats?.resources?.cpu || 0}%</span>
            </div>
            <div className="progress-bar"><div className="progress-fill" style={{width: `${systemStats?.resources?.cpu || 0}%`}}></div></div>
          </div>
          <div className="stat-card">
            <div style={{display: 'flex', justifyContent: 'space-between'}}>
              <span>Memory</span>
              <span>{systemStats?.resources?.memory || 0}%</span>
            </div>
            <div className="progress-bar"><div className="progress-fill" style={{width: `${systemStats?.resources?.memory || 0}%`}}></div></div>
          </div>
        </div>

        <div className="stat-group" style={{marginTop: 'auto'}}>
          <div className={`status-indicator ${isConnected ? 'connected' : 'disconnected'}`}>
            <span className={`dot ${isConnected ? 'connected' : 'disconnected'}`}></span>
            {isConnected ? 'SECURE LINK ACTIVE' : 'NO CARRIER'}
          </div>
        </div>
      </aside>

      {/* Main Chat */}
      <main className="chat-orchestrator">
        <header className="chat-header">
          <div className="header-meta">
            <span style={{color: 'var(--text-dim)', fontSize: '0.75rem'}}>SESSION ID</span>
            <div style={{fontSize: '0.875rem', fontWeight: 'bold'}}>{sessionId.split('-')[0]}...</div>
          </div>
          <button className="icon-btn" onClick={() => {
            localStorage.clear();
            window.location.reload();
          }}>LOGOUT</button>
        </header>

        <div className="messages-viewport">
          {messages.map(msg => (
            <div key={msg.id} className={`message-node ${msg.role}`}>
              <div className="bubble">
                {msg.content}
              </div>
              <div className="msg-meta">
                <span>{new Date(msg.timestamp).toLocaleTimeString([], {hour: '2-digit', minute:'2-digit'})}</span>
                {msg.provider && <span>🚀 {msg.provider} • {msg.latency?.toFixed(0)}ms</span>}
              </div>
            </div>
          ))}
          <div ref={messagesEndRef} />
        </div>

        <div className="input-composer">
          <div className="composer-box">
            <textarea 
              value={input} 
              onChange={e => setInput(e.target.value)}
              onKeyDown={e => { if (e.key === 'Enter' && !e.shiftKey) { e.preventDefault(); handleSend(); }}}
              placeholder="Enter instruction for Sovereign AI..."
              rows={1}
            />
            <button className="send-btn" onClick={handleSend} disabled={!isConnected || !input.trim()}>
              DISPATCH
            </button>
          </div>
        </div>
      </main>
    </div>
  );
}

export default App;
