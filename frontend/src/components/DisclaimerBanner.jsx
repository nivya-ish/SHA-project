import React from "react";

export default function DisclaimerBanner({ compact = false }) {
  return (
    <div className="disclaimer-banner" role="note" aria-label="Medical disclaimer">
      <strong>Important:</strong> Smart Health Assistant is an academic experimental decision-support tool. It may suggest <strong>possible conditions</strong> based on symptoms and available data, but it does <strong>not</strong> provide a confirmed diagnosis{compact ? "." : " and is not clinically validated. Always consult a qualified healthcare professional for diagnosis, treatment, or urgent concerns."}
    </div>
  );
}
