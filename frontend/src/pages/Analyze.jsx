import React, { useState } from "react";
import { api } from "../api/client";
import DisclaimerBanner from "../components/DisclaimerBanner";
import LoadingState from "../components/LoadingState";
import AnalysisResults from "../components/AnalysisResults";

export default function Analyze() {
  const [symptomsText, setSymptomsText] = useState("");
  const [durationText, setDurationText] = useState("");
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState("");
  const [result, setResult] = useState(null);

  async function onSubmit(e) {
    e.preventDefault();
    setError("");
    setResult(null);
    setLoading(true);
    try {
      const data = await api.analyze({
        symptoms_text: symptomsText,
        duration_text: durationText,
      });
      setResult(data);
    } catch (err) {
      setError(err.message || "Analysis failed. Please try again.");
    } finally {
      setLoading(false);
    }
  }

  function onClear() {
    setSymptomsText("");
    setDurationText("");
    setError("");
    setResult(null);
  }

  return (
    <div className="stack">
      <div className="card">
        <h1 style={{ marginBottom: "0.25rem" }}>Symptom Analysis</h1>
        <p className="muted" style={{ marginTop: 0 }}>
          Describe your symptoms in natural language and enter duration separately. The system will extract symptoms, run ML prediction, retrieve medical information, and generate a cautious explanation.
        </p>
        <div className="alert info" style={{ marginBottom: "0.8rem" }}>
          <strong>How to use (quick guide):</strong> 1) Enter symptoms in plain language. 2) Enter duration separately (e.g. "3 days"). 3) Click <strong>Analyze Symptoms</strong>. Duration-only inputs are rejected and never treated as a symptom.
        </div>
        <DisclaimerBanner compact />

        <form onSubmit={onSubmit} className="stack" style={{ marginTop: "1rem" }} aria-label="Symptom analysis form">
          <div>
            <label htmlFor="symptoms">Symptoms (natural language)</label>
            <textarea
              id="symptoms"
              name="symptoms"
              placeholder="Example: I have fever, cough, and sore throat..."
              value={symptomsText}
              onChange={(e) => setSymptomsText(e.target.value)}
            />
            <div className="form-help">Do not include duration here only. If symptoms are empty, analysis will not run.</div>
          </div>

          <div className="grid grid-2">
            <div>
              <label htmlFor="duration">Duration (separate field)</label>
              <input
                id="duration"
                name="duration"
                type="text"
                placeholder="Example: 3 days"
                value={durationText}
                onChange={(e) => setDurationText(e.target.value)}
              />
              <div className="form-help">Duration is stored separately and is <strong>not</strong> treated as a symptom.</div>
            </div>
            <div className="alert info" style={{ alignSelf: "end" }}>
              <strong>Examples</strong>
              <ul className="list">
                <li>Symptoms: "fever and cough", Duration: "3 days" → valid</li>
                <li>Symptoms: "3 days", Duration empty → rejected (duration is not a symptom)</li>
                <li>Symptoms empty, Duration: "3 days" → rejected</li>
                <li>Symptoms: "headache and nausea", Duration: "since yesterday" → valid</li>
              </ul>
            </div>
          </div>

          <div className="btn-row">
            <button type="submit" className="btn" disabled={loading}>Analyze Symptoms</button>
            <button type="button" className="btn secondary" onClick={onClear} disabled={loading}>Clear</button>
          </div>
        </form>

        {loading ? <div style={{ marginTop: "1rem" }}><LoadingState text="Validating input, extracting symptoms, running ML/RAG/Gemini analysis..." /></div> : null}
        {error ? <div className="alert error" role="alert" style={{ marginTop: "1rem" }}><strong>Error:</strong> {error}</div> : null}
      </div>

      {result ? <AnalysisResults result={result} onStartNew={onClear} /> : null}
    </div>
  );
}
