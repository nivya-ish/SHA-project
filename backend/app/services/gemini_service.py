"""Gemini integration (backend-only) with safe fallback."""
from __future__ import annotations

import json
import re
from typing import Any, Dict, List

from app.core.config import settings


DISCLAIMER = (
    "This is an academic experimental healthcare decision-support system, not a clinically validated diagnostic tool. "
    "It provides possible conditions and educational information only, not a confirmed diagnosis. "
    "Consult a qualified healthcare professional for medical advice, diagnosis, or treatment."
)


class GeminiService:
    def __init__(self):
        self._model = None
        self.init_error: str | None = None

    @property
    def configured(self) -> bool:
        return bool(settings.gemini_enabled and settings.gemini_api_key)

    def _ensure_model(self):
        if not self.configured:
            self.init_error = "Gemini API key not configured or Gemini disabled."
            return None
        if self._model is not None:
            return self._model
        try:
            import google.generativeai as genai
            genai.configure(api_key=settings.gemini_api_key)
            self._model = genai.GenerativeModel(settings.gemini_model)
            self.init_error = None
            return self._model
        except Exception as e:
            self.init_error = str(e)
            self._model = None
            return None

    def _fallback(self, symptoms: List[str], duration: str | None, predictions: List[Dict[str, Any]], sources: List[Dict[str, Any]], notes: List[str]) -> Dict[str, Any]:
        pred_expl = []
        for p in predictions[:3]:
            pred_expl.append({
                "condition": p.get("condition"),
                "why_possible": "This condition is listed as a possible match because some reported symptoms overlap with patterns learned from the dataset. This is not a confirmed diagnosis.",
                "supporting_symptoms": p.get("supporting_symptoms", []),
                "model_confidence_note": p.get("confidence_label", "model estimate"),
            })
        retrieved_info = []
        for s in sources[:4]:
            retrieved_info.append({
                "title": s.get("title"),
                "source": s.get("source"),
                "summary": s.get("snippet"),
            })
        safe_steps = [
            "Monitor symptoms and note any changes in severity or new symptoms.",
            "Rest, hydrate, and use general supportive care appropriate to how you feel, if safe for you.",
            "Consult a qualified healthcare professional for personalized assessment, especially if symptoms persist, worsen, or concern you.",
        ]
        if duration:
            safe_steps.insert(0, f"You reported a duration of {duration}; consider sharing this timeline with a clinician.")
        emergency = [
            "Seek urgent medical care immediately for severe chest pain, trouble breathing, confusion, fainting, signs of stroke, severe bleeding, or rapidly worsening symptoms.",
            "If you think this may be an emergency, contact local emergency services right away.",
        ]
        followups = [
            "Have any symptoms worsened, improved, or stayed the same since they started?",
            "Do you have any relevant medical history, allergies, or current medications a clinician should know about?",
            "Are there additional symptoms (e.g., fever severity, pain location, breathing issues) not yet mentioned?",
        ]
        summary = (
            "Based on the symptoms you provided, the system identified possible conditions from the trained model and retrieved related educational medical information. "
            "These results are decision-support suggestions only and must be reviewed with a healthcare professional."
        )
        return {
            "summary": summary,
            "predicted_conditions_explained": pred_expl,
            "retrieved_medical_information": retrieved_info,
            "safe_next_steps": safe_steps,
            "follow_up_questions": followups,
            "emergency_guidance": emergency,
            "disclaimer": DISCLAIMER,
            "generator": "fallback",
            "limitations": [
                "Predictions depend on dataset coverage and symptom mapping quality.",
                "No clinical validation or diagnostic accuracy is claimed.",
                "Gemini-generated explanation unavailable or disabled; a rule-based safe summary was used." if not self.configured or self.init_error else "Rule-based fallback used.",
            ] + (notes or []),
        }

    def generate(self, symptoms: List[str], duration: str | None, predictions: List[Dict[str, Any]], sources: List[Dict[str, Any]], notes: List[str] | None = None) -> Dict[str, Any]:
        notes = notes or []
        model = self._ensure_model()
        if model is None:
            return self._fallback(symptoms, duration, predictions, sources, notes)
        try:
            prompt = self._build_prompt(symptoms, duration, predictions, sources)
            resp = model.generate_content(
                prompt,
                generation_config={"temperature": 0.2, "max_output_tokens": 900},
            )
            text = getattr(resp, "text", None) or ""
            parsed = self._parse_json_response(text)
            if not parsed:
                return self._fallback(symptoms, duration, predictions, sources, notes + ["Gemini response could not be parsed; fallback used."])
            parsed.setdefault("disclaimer", DISCLAIMER)
            parsed.setdefault("generator", "gemini")
            parsed.setdefault("limitations", [])
            if not isinstance(parsed.get("limitations"), list):
                parsed["limitations"] = [str(parsed.get("limitations"))]
            parsed["limitations"].append("AI explanation is for educational decision support only and may be incomplete.")
            return parsed
        except Exception as e:
            self.init_error = str(e)
            return self._fallback(symptoms, duration, predictions, sources, notes + [f"Gemini error: {e}"])

    def _build_prompt(self, symptoms: List[str], duration: str | None, predictions: List[Dict[str, Any]], sources: List[Dict[str, Any]]) -> str:
        payload = {
            "symptoms": symptoms,
            "duration": duration,
            "predicted_possible_conditions_from_ml_model": predictions,
            "retrieved_medical_sources_rag": sources,
            "requirements": [
                "Do not provide a confirmed diagnosis.",
                "Do not prescribe medications or dosages.",
                "Do not invent medical facts or references; use only provided RAG snippets when citing retrieved information.",
                "Clearly separate ML predictions, retrieved medical evidence, and AI explanation.",
                "Include safe next steps and emergency escalation guidance for concerning symptoms.",
                "Be conservative and mention uncertainty/limitations.",
            ],
            "output_json_schema": {
                "summary": "string",
                "predicted_conditions_explained": [{"condition": "string", "why_possible": "string", "supporting_symptoms": ["string"], "model_confidence_note": "string"}],
                "retrieved_medical_information": [{"title": "string", "source": "string", "summary": "string"}],
                "safe_next_steps": ["string"],
                "follow_up_questions": ["string"],
                "emergency_guidance": ["string"],
                "disclaimer": "string",
                "limitations": ["string"]
            }
        }
        return (
            "You are generating a cautious healthcare decision-support explanation for an academic experimental app. "
            "Return ONLY valid JSON matching the requested schema. No markdown fences.\n"
            + json.dumps(payload, ensure_ascii=False)
        )

    def _parse_json_response(self, text: str) -> Dict[str, Any] | None:
        if not text:
            return None
        text = text.strip()
        # strip fences if present
        if text.startswith("```"):
            text = re.sub(r"^```(?:json)?", "", text, flags=re.IGNORECASE).strip()
            text = re.sub(r"```$", "", text).strip()
        try:
            obj = json.loads(text)
            return obj if isinstance(obj, dict) else None
        except Exception:
            # try to extract JSON object
            m = re.search(r"\{.*\}", text, re.DOTALL)
            if not m:
                return None
            try:
                obj = json.loads(m.group(0))
                return obj if isinstance(obj, dict) else None
            except Exception:
                return None


gemini_service = GeminiService()
