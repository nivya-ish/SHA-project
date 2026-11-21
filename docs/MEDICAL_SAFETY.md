# Medical Safety & Disclaimer

## Intended Use
Smart Health Assistant is an **academic/experimental healthcare decision-support prototype**. It is designed to demonstrate symptom NLP, ML prediction, retrieval-augmented information lookup, and AI explanation workflows using the provided dataset and curated reference documents.

## Not a Medical Device / Not a Diagnosis
- The system provides **possible conditions only** (unconfirmed). It does **not** provide confirmed diagnoses, clinical decisions, prescriptions, or treatment plans.
- Outputs are **not clinically validated** and may be incomplete, incorrect, or not applicable to an individual.
- The application must **not** be used as a substitute for professional medical advice, diagnosis, or emergency care.

## Safety Behaviors Implemented
- **Input validation:** rejects empty input, irrelevant/unmappable input, and duration-only input.
- **Duration is not a symptom:** duration is extracted/stored separately and never treated as a symptom feature.
- **No symptom invention:** the system does not fabricate symptoms or run ML prediction on invalid/duration-only input.
- **Grounded, cautious outputs:** ML predictions, retrieved medical information (RAG), and AI explanations are presented separately; Gemini prompts/fallbacks are constrained to be conservative and to avoid unsupported claims.
- **No fabricated references/results:** retrieved sources come from curated local medical documents; evaluation/test claims should be based on actually executed runs.
- **Emergency guidance:** responses include conservative guidance to seek urgent/emergency care for severe, sudden, or worsening symptoms (e.g. chest pain, trouble breathing, confusion, fainting, stroke signs, severe bleeding).
- **Privacy-minded data handling:** stores analysis inputs/results for history functionality but avoids requiring unnecessary personal/sensitive identifiers.

## User Guidance
- Always consult a qualified healthcare professional for medical concerns, diagnosis, or treatment.
- If symptoms are severe, rapidly worsening, or potentially life-threatening, seek emergency medical care immediately (contact local emergency services).
- Provide additional context to clinicians (medical history, medications, allergies, symptom progression) rather than relying on this tool.

## Limitations
- ML model performance is dataset-dependent (trained/evaluated on the provided symptom-disease dataset) and may not generalize to real-world clinical cases.
- RAG responses depend on the curated local knowledge base and retrieval quality (semantic embeddings when available; keyword fallback when not).
- Gemini explanations require a valid API key and network access; otherwise a safe fallback summary is used.
- Public deployment security, availability, and compliance (e.g. HIPAA/GDPR/clinical regulations) are **out of scope** for this student prototype unless specifically implemented and validated.
