import React from "react";

export default function LoadingState({ text = "Analyzing symptoms..." }) {
  return (
    <div className="loading" role="status" aria-live="polite">
      <span className="spinner" aria-hidden="true"></span>
      <span>{text}</span>
    </div>
  );
}
