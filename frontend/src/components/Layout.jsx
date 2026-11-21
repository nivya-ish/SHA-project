import React from "react";
import { NavLink } from "react-router-dom";

export default function Layout({ children }) {
  return (
    <div className="app-shell">
      <header className="topbar">
        <div className="container topbar-inner">
          <div className="brand" aria-label="Smart Health Assistant">
            <div className="brand-badge" aria-hidden="true">+</div>
            <div>
              Smart Health Assistant
              <span className="brand-sub">AI-powered healthcare decision support (academic/experimental)</span>
            </div>
          </div>
          <nav className="nav-links" aria-label="Primary navigation">
            <NavLink to="/" className={({ isActive }) => `nav-link ${isActive ? "active" : ""}`}>Home</NavLink>
            <NavLink to="/dashboard" className={({ isActive }) => `nav-link ${isActive ? "active" : ""}`}>Dashboard</NavLink>
            <NavLink to="/analyze" className={({ isActive }) => `nav-link ${isActive ? "active" : ""}`}>Symptom Analysis</NavLink>
            <NavLink to="/history" className={({ isActive }) => `nav-link ${isActive ? "active" : ""}`}>History</NavLink>
          </nav>
        </div>
      </header>
      <main className="main-content">
        <div className="container">{children}</div>
      </main>
      <footer className="footer">
        <div className="container">
          <div><strong>Medical disclaimer:</strong> This application provides possible conditions and educational information only. It is not a confirmed diagnosis and not clinically validated. Consult a qualified healthcare professional for medical advice.</div>
        </div>
      </footer>
    </div>
  );
}
