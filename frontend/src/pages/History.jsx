import React, { useEffect, useState } from "react";
import { api } from "../api/client";
import LoadingState from "../components/LoadingState";
import AnalysisResults from "../components/AnalysisResults";

export default function History() {
  const [items, setItems] = useState([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState("");
  const [selectedId, setSelectedId] = useState(null);
  const [detail, setDetail] = useState(null);
  const [detailLoading, setDetailLoading] = useState(false);

  async function loadHistory() {
    setLoading(true);
    setError("");
    try {
      const data = await api.history(30);
      setItems(data || []);
    } catch (e) {
      setError(e.message || "Failed to load history");
    } finally {
      setLoading(false);
    }
  }

  useEffect(() => { loadHistory(); }, []);

  async function openDetail(id) {
    setSelectedId(id);
    setDetail(null);
    setDetailLoading(true);
    try {
      const d = await api.historyDetail(id);
      // shape for AnalysisResults-like rendering
      setDetail({
        status: d.status,
        message: "Historical analysis record",
        nlp: {
          extracted_symptoms: d.extracted_symptoms || [],
          normalized_symptoms: d.normalized_symptoms || [],
          mapped_features: d.mapped_features || [],
          unsupported_symptoms: d.unsupported_symptoms || [],
          duration: d.duration_text,
          notes: d.notes ? [d.notes] : [],
        },
        predictions: d.predictions || [],
        retrieved_sources: d.retrieved_sources || [],
        explanation: d.explanation || {},
        disclaimer: d.explanation?.disclaimer || "This is not a confirmed diagnosis.",
        record_id: d.id,
      });
    } catch (e) {
      setError(e.message || "Failed to load record details");
    } finally {
      setDetailLoading(false);
    }
  }

  async function removeItem(id) {
    try {
      await api.deleteHistory(id);
      setItems((prev) => prev.filter((x) => x.id !== id));
      if (selectedId === id) {
        setSelectedId(null);
        setDetail(null);
      }
    } catch (e) {
      setError(e.message || "Failed to delete record");
    }
  }

  return (
    <div className="stack">
      <div className="card">
        <div className="section-title">
          <div>
            <h1 style={{ marginBottom: "0.25rem" }}>Analysis History</h1>
            <div className="muted">Saved analysis records from the database (if persistence is enabled).</div>
          </div>
          <button className="btn secondary" onClick={loadHistory}>Refresh</button>
        </div>
        {loading ? <LoadingState text="Loading history..." /> : null}
        {error ? <div className="alert error" role="alert"><strong>Error:</strong> {error}</div> : null}
      </div>

      <div className="grid grid-2">
        <div className="card">
          <h2>Records</h2>
          {!loading && !items.length ? <p className="muted">No history records found.</p> : null}
          <div className="stack">
            {items.map((item) => (
              <div
                key={item.id}
                className={`prediction-item history-item ${selectedId === item.id ? "selected" : ""}`}
                onClick={() => openDetail(item.id)}
                role="button"
                tabIndex={0}
                onKeyDown={(e) => { if (e.key === "Enter" || e.key === " ") openDetail(item.id); }}
              >
                <div className="section-title">
                  <strong>Record #{item.id}</strong>
                  <span className="badge">{item.status}</span>
                </div>
                <div className="muted" style={{ fontSize: "0.9rem" }}>{new Date(item.created_at).toLocaleString()}</div>
                <div style={{ marginTop: "0.3rem" }}><strong>Symptoms:</strong> {item.symptoms_text}</div>
                <div className="muted">Duration: {item.duration_text || "N/A"}</div>
                <div className="muted">Normalized: {(item.normalized_symptoms || []).join(", ") || "None"}</div>
                {item.predictions?.length ? (
                  <div style={{ marginTop: "0.3rem" }}><span className="muted">Top:</span> <strong>{item.predictions[0].condition}</strong> (unconfirmed)</div>
                ) : null}
                <div className="btn-row" style={{ marginTop: "0.5rem" }}>
                  <button className="btn ghost" onClick={(e) => { e.stopPropagation(); openDetail(item.id); }}>View</button>
                  <button className="btn secondary" onClick={(e) => { e.stopPropagation(); removeItem(item.id); }}>Delete</button>
                </div>
              </div>
            ))}
          </div>
        </div>

        <div className="stack">
          <div className="card">
            <h2>Record Details</h2>
            {!selectedId && !detailLoading ? <p className="muted">Select a record to view full details.</p> : null}
            {detailLoading ? <LoadingState text="Loading record details..." /> : null}
          </div>
          {detail ? <AnalysisResults result={detail} /> : null}
        </div>
      </div>
    </div>
  );
}
