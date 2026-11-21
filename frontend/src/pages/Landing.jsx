import React from "react";
import { Link } from "react-router-dom";
import DisclaimerBanner from "../components/DisclaimerBanner";

export default function Landing() {
  return (
    <div className="stack">
      <section className="hero">
        <div className="card">
          <span className="badge">Academic healthcare decision-support prototype</span>
          <h1 style={{ marginTop: "0.6rem", marginBottom: "0.5rem" }}>Smart Health Assistant</h1>
          <p className="muted" style={{ fontSize: "1.05rem" }}>
            Describe your symptoms in plain language and get a cautious, easy-to-understand overview of <strong>possible conditions (unconfirmed)</strong>,
            supporting symptoms, retrieved medical information, and safe next steps.
          </p>
          <div className="btn-row" style={{ marginTop: "1rem" }}>
            <Link to="/analyze" className="btn">Start Symptom Analysis</Link>
            <Link to="/dashboard" className="btn secondary">Open Dashboard</Link>
          </div>
          <div className="alert info" style={{ marginTop: "1rem" }}>
            <strong>Simple example:</strong> Symptoms: "fever and cough" &nbsp;|&nbsp; Duration: "3 days" → click <em>Analyze Symptoms</em>.
            <div className="muted" style={{ marginTop: "0.25rem" }}>Duration-only input (e.g. "3 days") is not enough and will be rejected. This app does not provide a confirmed diagnosis.</div>
          </div>
          <div className="divider"></div>
          <DisclaimerBanner compact />
        </div>

        <div className="card">
          <h2>How it works</h2>
          <ol className="list">
            <li>Describe symptoms in natural language and provide duration separately.</li>
            <li>Backend NLP extracts and maps symptoms to dataset features (duration is never treated as a symptom).</li>
            <li>ML model predicts <strong>possible conditions</strong> (not confirmed diagnoses).</li>
            <li>RAG retrieves relevant medical information from the local knowledge base.</li>
            <li>Gemini (or safe fallback) generates a contextual, cautious explanation.</li>
          </ol>
          <div className="alert info" style={{ marginTop: "0.8rem" }}>
            <strong>Safety-first behavior:</strong> empty/duration-only inputs are rejected (no symptom invention, no prediction), unsupported symptoms are reported, and results include medical disclaimers and emergency guidance.
          </div>
          <div className="alert warning" style={{ marginTop: "0.8rem" }}>
            <strong>When to seek urgent care:</strong> severe chest pain, trouble breathing, confusion, fainting, signs of stroke, severe bleeding, or rapidly worsening symptoms require immediate medical attention.
          </div>
        </div>
      </section>

      <section className="grid grid-3">
        <div className="card">
          <h3>ML + NLP</h3>
          <p className="muted">Symptom extraction, normalization, duration parsing, feature mapping, and scikit-learn prediction on the uploaded dataset.</p>
        </div>
        <div className="card">
          <h3>RAG + Gemini</h3>
          <p className="muted">ChromaDB-backed retrieval from curated medical documents with backend-only Gemini integration and graceful fallback.</p>
        </div>
        <div className="card">
          <h3>History + DevOps</h3>
          <p className="muted">PostgreSQL-ready persistence for analysis history, plus Docker Compose and Kubernetes manifests for deployment.</p>
        </div>
      </section>
    </div>
  );
}
