import React from "react";

export default function PredictionList({ predictions = [] }) {
  if (!predictions.length) {
    return <div className="muted">No possible conditions to display.</div>;
  }
  return (
    <div className="stack" aria-label="Possible conditions (unconfirmed)">
      {predictions.map((p, idx) => {
        const pct = Math.max(0, Math.min(100, Math.round((p.probability || 0) * 100)));
        return (
          <div key={`${p.condition}-${idx}`} className="prediction-item">
            <div className="section-title">
              <div>
                <strong>{p.condition}</strong>
                <div className="muted" style={{ fontSize: "0.9rem" }}>Possible condition (unconfirmed) • {p.confidence_label}</div>
              </div>
              <span className="badge">{pct}%</span>
            </div>
            <div className="prob-bar" aria-label={`Model probability ${pct}%`}>
              <div className="prob-fill" style={{ width: `${pct}%` }}></div>
            </div>
            {p.supporting_symptoms?.length ? (
              <div style={{ marginTop: "0.55rem" }}>
                <div className="muted" style={{ fontWeight: 600, marginBottom: "0.25rem" }}>Supporting symptoms (from your input/model mapping):</div>
                <div className="pill-list">
                  {p.supporting_symptoms.map((s, i) => <span key={i} className="badge">{s}</span>)}
                </div>
              </div>
            ) : null}
          </div>
        );
      })}
    </div>
  );
}
