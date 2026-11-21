import React, { useEffect, useState } from "react";
import { Link } from "react-router-dom";
import { api } from "../api/client";
import LoadingState from "../components/LoadingState";

export default function Dashboard() {
  const [health, setHealth] = useState(null);
  const [rag, setRag] = useState(null);
  const [history, setHistory] = useState([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState("");

  useEffect(() => {
    let mounted = true;
    async function load() {
      setLoading(true);
      setError("");
      try {
        const [h, r, hist] = await Promise.allSettled([
          api.health(),
          api.ragStatus(),
          api.history(5),
        ]);
        if (!mounted) return;
        if (h.status === "fulfilled") setHealth(h.value); else setHealth(null);
        if (r.status === "fulfilled") setRag(r.value); else setRag(null);
        if (hist.status === "fulfilled") setHistory(hist.value || []); else setHistory([]);
        const errs = [h, r, hist].filter(x => x.status === "rejected").map(x => x.reason?.message || "Request failed");
        if (errs.length) setError(errs.join(" | "));
      } finally {
        if (mounted) setLoading(false);
      }
    }
    load();
    return () => { mounted = false; };
  }, []);

  return (
    <div className="stack">
      <div className="card">
        <div className="section-title">
          <div>
            <h1 style={{ marginBottom: "0.25rem" }}>Dashboard</h1>
            <div className="muted">System status, recent analyses, and quick actions.</div>
          </div>
          <Link to="/analyze" className="btn">New Analysis</Link>
        </div>
        {loading ? <LoadingState text="Loading dashboard..." /> : null}
        {error ? <div className="alert error" role="alert"><strong>Some data could not be loaded:</strong> {error}</div> : null}

        <div className="status-grid" style={{ marginTop: "0.8rem" }}>
          <div className="status-card">
            <div className="muted">API / App</div>
            <div className={health?.status === "ok" ? "status-ok" : "status-no"}>{health?.status === "ok" ? "Online" : "Unavailable"}</div>
            <div className="muted" style={{ fontSize: "0.9rem" }}>{health?.app || "Smart Health Assistant"}</div>
          </div>
          <div className="status-card">
            <div className="muted">ML Model</div>
            <div className={health?.ml_ready ? "status-ok" : "status-no"}>{health?.ml_ready ? "Ready" : "Not ready"}</div>
            <div className="muted" style={{ fontSize: "0.9rem" }}>Artifacts loaded for prediction</div>
          </div>
          <div className="status-card">
            <div className="muted">RAG / ChromaDB</div>
            <div className={health?.rag_ready ? "status-ok" : "status-no"}>{health?.rag_ready ? "Available" : "Limited/Unavailable"}</div>
            <div className="muted" style={{ fontSize: "0.9rem" }}>Docs: {rag?.document_count ?? "n/a"} {rag?.error ? "(fallback may apply)" : ""}</div>
          </div>
          <div className="status-card">
            <div className="muted">Gemini</div>
            <div className={health?.gemini_configured ? "status-ok" : "status-no"}>{health?.gemini_configured ? "Configured" : "Fallback mode"}</div>
            <div className="muted" style={{ fontSize: "0.9rem" }}>Backend-only API integration</div>
          </div>
          <div className="status-card">
            <div className="muted">Database</div>
            <div className={health?.database_ok ? "status-ok" : "status-no"}>{health?.database_ok ? "Connected" : "Error"}</div>
            <div className="muted" style={{ fontSize: "0.9rem" }}>History persistence</div>
          </div>
        </div>
      </div>

      <div className="grid grid-2">
        <div className="card">
          <h2>Quick Actions</h2>
          <div className="stack">
            <Link to="/analyze" className="btn">Analyze Symptoms</Link>
            <Link to="/history" className="btn secondary">View Analysis History</Link>
            <div className="alert info">
              <strong>Reminder:</strong> Enter symptoms and duration in separate fields. Duration-only input will not trigger prediction.
            </div>
          </div>
        </div>
        <div className="card">
          <h2>Recent Analyses</h2>
          {history.length ? (
            <div className="stack">
              {history.map((item) => (
                <div key={item.id} className="prediction-item">
                  <div className="section-title">
                    <strong>Record #{item.id}</strong>
                    <span className="badge">{item.status}</span>
                  </div>
                  <div className="muted" style={{ fontSize: "0.9rem" }}>{new Date(item.created_at).toLocaleString()}</div>
                  <div style={{ marginTop: "0.3rem" }}><strong>Symptoms:</strong> {item.symptoms_text}</div>
                  <div className="muted">Duration: {item.duration_text || "N/A"}</div>
                  {item.predictions?.length ? (
                    <div style={{ marginTop: "0.35rem" }}>
                      <span className="muted">Top possible condition: </span>
                      <strong>{item.predictions[0].condition}</strong> (unconfirmed)
                    </div>
                  ) : null}
                </div>
              ))}
            </div>
          ) : (
            <p className="muted">No analysis history yet.</p>
          )}
        </div>
      </div>
    </div>
  );
}
