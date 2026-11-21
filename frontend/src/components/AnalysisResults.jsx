import React from "react";
import PredictionList from "./PredictionList";

export default function AnalysisResults({ result, onStartNew }) {
  if (!result) return null;
  const { nlp, predictions, retrieved_sources, explanation, disclaimer, status, message } = result;

  if (status === "invalid_input") {
    return (
      <div className="stack">
        <div className="alert warning" role="alert">
          <strong>Input needed:</strong> {message}
        </div>
        {nlp?.notes?.length ? (
          <div className="card">
            <h3>Details</h3>
            <ul className="list">{nlp.notes.map((n, i) => <li key={i}>{n}</li>)}</ul>
          </div>
        ) : null}
        <div className="card">
          <h3>What to do next</h3>
          <ul className="list">
            <li>Enter specific symptoms in plain language (for example: fever, cough, headache, nausea, skin rash).</li>
            <li>Enter duration separately (for example: 3 days). Duration alone is not enough and is never treated as a symptom.</li>
            <li>Duration-only inputs (such as "3 days") are rejected and will not trigger prediction.</li>
          </ul>
          <div className="btn-row" style={{ marginTop: "0.75rem" }}>
            {onStartNew ? <button type="button" className="btn secondary" onClick={onStartNew}>Start a new analysis</button> : null}
          </div>
        </div>
      </div>
    );
  }

  return (
    <div className="stack" aria-live="polite">
      <div className="card">
        <div className="section-title">
          <h2 style={{ margin: 0 }}>Analysis Summary</h2>
          <span className="badge">Status: {status}</span>
        </div>
        <p style={{ marginTop: 0 }}>{message}</p>
        <div className="alert info" style={{ marginBottom: "0.8rem" }}>
          <strong>Important:</strong> Results show <strong>possible conditions (unconfirmed)</strong> for academic decision support only. This is not a confirmed diagnosis and not clinically validated.
        </div>
        <div className="grid grid-2">
          <div>
            <h3>Processed Input (NLP)</h3>
            <div className="kv">
              <div>Duration</div><div>{nlp?.duration || "Not provided"}</div>
              <div>Normalized symptoms</div><div>{nlp?.normalized_symptoms?.length ? nlp.normalized_symptoms.join(", ") : "None"}</div>
              <div>Mapped ML features</div><div>{nlp?.mapped_features?.length ? nlp.mapped_features.join(", ") : "None"}</div>
              <div>Unsupported symptoms</div><div>{nlp?.unsupported_symptoms?.length ? nlp.unsupported_symptoms.join(", ") : "None"}</div>
            </div>
            {nlp?.notes?.length ? (
              <div style={{ marginTop: "0.6rem" }}>
                <strong>NLP notes</strong>
                <ul className="list">{nlp.notes.map((n, i) => <li key={i}>{n}</li>)}</ul>
              </div>
            ) : null}
          </div>
          <div className="alert info">
            <strong>How to read results:</strong>
            <ul className="list">
              <li><strong>ML predictions</strong> are model-generated possible conditions from symptom features.</li>
              <li><strong>Retrieved medical evidence</strong> comes from the local RAG knowledge base.</li>
              <li><strong>AI explanation</strong> summarizes and contextualizes information; it may be Gemini-generated or a safe fallback.</li>
              <li>Seek urgent care for severe, sudden, or rapidly worsening symptoms.</li>
            </ul>
          </div>
        </div>
        {onStartNew ? (
          <div className="btn-row" style={{ marginTop: "0.9rem" }}>
            <button type="button" className="btn secondary" onClick={onStartNew}>Start a new analysis</button>
          </div>
        ) : null}
      </div>

      <div className="grid grid-2">
        <div className="card">
          <h2>Possible Conditions (ML Predictions)</h2>
          <p className="muted" style={{ marginTop: 0 }}>These are <strong>unconfirmed</strong> model predictions, not diagnoses.</p>
          <PredictionList predictions={predictions || []} />
        </div>
        <div className="card">
          <h2>AI Explanation & Safe Guidance</h2>
          <p className="muted" style={{ marginTop: 0 }}>Generator: <strong>{explanation?.generator || "fallback"}</strong></p>
          {explanation?.summary ? <p>{explanation.summary}</p> : <p className="muted">No summary available.</p>}

          {explanation?.predicted_conditions_explained?.length ? (
            <>
              <h3>Prediction Explanations (AI/summary)</h3>
              <ul className="list">
                {explanation.predicted_conditions_explained.map((item, i) => (
                  <li key={i}>
                    <strong>{item.condition || "Condition"}:</strong> {item.why_possible || "Explanation unavailable."}
                  </li>
                ))}
              </ul>
            </>
          ) : null}

          {explanation?.safe_next_steps?.length ? (
            <>
              <h3>Safe Next Steps</h3>
              <ul className="list">{explanation.safe_next_steps.map((s, i) => <li key={i}>{s}</li>)}</ul>
            </>
          ) : null}

          {explanation?.follow_up_questions?.length ? (
            <>
              <h3>Follow-up Questions</h3>
              <ul className="list">{explanation.follow_up_questions.map((q, i) => <li key={i}>{q}</li>)}</ul>
            </>
          ) : null}

          <div className="alert warning" style={{ marginTop: "0.8rem" }}>
            <strong>When to seek urgent/emergency care</strong>
            <ul className="list">
              {(explanation?.emergency_guidance?.length ? explanation.emergency_guidance : [
                "Seek urgent medical care immediately for severe chest pain, trouble breathing, confusion, fainting, signs of stroke, severe bleeding, or rapidly worsening symptoms.",
                "If you think this may be an emergency, contact local emergency services right away."
              ]).map((e, i) => <li key={i}>{e}</li>)}
            </ul>
          </div>
        </div>
      </div>

      <div className="grid grid-2">
        <div className="card">
          <h2>Retrieved Medical Information (RAG)</h2>
          {retrieved_sources?.length ? (
            <div className="stack">
              {retrieved_sources.map((s, i) => (
                <div key={i} className="prediction-item">
                  <div className="section-title">
                    <strong>{s.title || "Medical source"}</strong>
                    {typeof s.score === "number" ? <span className="badge">score: {s.score.toFixed(3)}</span> : null}
                  </div>
                  <div className="muted" style={{ fontSize: "0.9rem", marginBottom: "0.3rem" }}><strong>Source:</strong> {s.source || "Unknown"}</div>
                  <div>{s.snippet}</div>
                </div>
              ))}
            </div>
          ) : (
            <p className="muted">No retrieved sources available. The system may be running without an indexed vector store or matching documents for this query; keyword fallback over curated medical documents is used when available.</p>
          )}
        </div>

        <div className="card">
          <h2>AI-Structured Retrieved Information</h2>
          {explanation?.retrieved_medical_information?.length ? (
            <ul className="list">
              {explanation.retrieved_medical_information.map((r, i) => (
                <li key={i}>
                  <strong>{r.title || "Source"}:</strong> {r.summary || r.snippet || ""}
                  {r.source ? <div className="muted" style={{ fontSize: "0.9rem" }}>Source: {r.source}</div> : null}
                </li>
              ))}
            </ul>
          ) : (
            <p className="muted">No AI-structured source summaries available.</p>
          )}

          {explanation?.limitations?.length ? (
            <>
              <h3>Limitations</h3>
              <ul className="list">{explanation.limitations.map((l, i) => <li key={i}>{l}</li>)}</ul>
            </>
          ) : null}

          <div className="alert info" style={{ marginTop: "0.8rem" }}>
            <strong>Medical disclaimer:</strong> {disclaimer || explanation?.disclaimer || "This is not a confirmed diagnosis. Consult a qualified healthcare professional."}
          </div>
          {onStartNew ? (
            <div className="btn-row" style={{ marginTop: "0.8rem" }}>
              <button type="button" className="btn secondary" onClick={onStartNew}>Start a new analysis</button>
            </div>
          ) : null}
        </div>
      </div>
    </div>
  );
}
