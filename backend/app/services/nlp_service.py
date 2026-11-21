"""NLP and symptom processing for Smart Health Assistant.

CRITICAL: duration is NOT a symptom. Never invent symptoms.
"""
from __future__ import annotations

import re
from dataclasses import dataclass, field
from typing import Dict, Iterable, List, Tuple
from difflib import get_close_matches


# Keep duration detection separate from symptom extraction.
DURATION_PATTERN = re.compile(
    r"\b(?:for\s+)?(?P<num>\d{1,3})\s*(?P<unit>day|days|week|weeks|month|months|year|years|hr|hrs|hour|hours)\b",
    re.IGNORECASE,
)
DURATION_ONLY_PATTERNS = [
    re.compile(r"^\s*(?:for\s*)?\d{1,3}\s*(?:day|days|week|weeks|month|months|year|years|hr|hrs|hour|hours)\.?\s*$", re.IGNORECASE),
    re.compile(r"^\s*(?:since|from)\s+(?:yesterday|today|last\s+\w+|monday|tuesday|wednesday|thursday|friday|saturday|sunday)\.?\s*$", re.IGNORECASE),
]

SPLIT_PATTERN = re.compile(r"[,;\n]+|\band\b|\bwith\b|\balong with\b|\bplus\b", re.IGNORECASE)


@dataclass
class NLPExtractionResult:
    extracted_symptoms: List[str] = field(default_factory=list)
    normalized_symptoms: List[str] = field(default_factory=list)
    mapped_features: List[str] = field(default_factory=list)
    unsupported_symptoms: List[str] = field(default_factory=list)
    duration: str | None = None
    notes: List[str] = field(default_factory=list)
    valid_for_prediction: bool = False
    validation_message: str | None = None


class SymptomNLPProcessor:
    def __init__(self, feature_columns: Iterable[str]):
        self.feature_columns = [self.normalize_feature_name(c) for c in feature_columns]
        self.feature_set = set(self.feature_columns)
        self.feature_display = {c: c.replace("_", " ") for c in self.feature_columns}
        self.alias_map = self._build_alias_map(self.feature_columns)

    @staticmethod
    def normalize_text(text: str) -> str:
        text = (text or "").strip().lower()
        text = text.replace("-", " ")
        text = re.sub(r"[^a-z0-9\s]", " ", text)
        text = re.sub(r"\s+", " ", text).strip()
        return text

    @staticmethod
    def normalize_feature_name(name: str) -> str:
        name = (name or "").strip().lower().replace(" ", "_")
        name = re.sub(r"__+", "_", name)
        return name

    def _build_alias_map(self, feature_columns: List[str]) -> Dict[str, str]:
        aliases: Dict[str, str] = {}
        def add(alias: str, feature: str):
            key = self.normalize_text(alias)
            if key:
                aliases[key] = feature
        for f in feature_columns:
            spaced = f.replace("_", " ")
            add(spaced, f)
            add(f, f)
            # common variants
            add(spaced.replace("  ", " "), f)
            add(spaced.replace("and", "&"), f)
        # hand-curated/common aliases for known dataset features
        manual = {
            "fever": "high_fever",
            "high fever": "high_fever",
            "mild fever": "mild_fever",
            "temperature": "high_fever",
            "coughing": "cough",
            "cold": "chills",  # approximate but common; still maps to dataset feature
            "runny nose": "runny_nose",
            "running nose": "runny_nose",
            "sore throat": "throat_irritation",
            "throat pain": "throat_irritation",
            "shortness of breath": "breathlessness",
            "difficulty breathing": "breathlessness",
            "breathing difficulty": "breathlessness",
            "tiredness": "fatigue",
            "tired": "fatigue",
            "exhaustion": "fatigue",
            "throwing up": "vomiting",
            "vomitting": "vomiting",
            "loose motions": "diarrhoea",
            "loose motion": "diarrhoea",
            "diarrhea": "diarrhoea",
            "stomach ache": "stomach_pain",
            "abdominal pain": "abdominal_pain",
            "belly pain": "belly_pain",
            "head ache": "headache",
            "body ache": "muscle_pain",
            "body pain": "muscle_pain",
            "muscle ache": "muscle_pain",
            "joint ache": "joint_pain",
            "skin rash": "skin_rash",
            "rash": "skin_rash",
            "itching": "itching",
            "itchy": "itching",
            "sneezing": "continuous_sneezing",
            "watery eyes": "watering_from_eyes",
            "yellow skin": "yellowish_skin",
            "yellow eyes": "yellowing_of_eyes",
            "dark urine": "dark_urine",
            "weight loss": "weight_loss",
            "weight gain": "weight_gain",
            "loss of appetite": "loss_of_appetite",
            "no appetite": "loss_of_appetite",
            "dizziness": "dizziness",
            "dizzy": "dizziness",
            "chest pain": "chest_pain",
            "back pain": "back_pain",
            "neck pain": "neck_pain",
            "anxiety": "anxiety",
            "depression": "depression",
            "sweating": "sweating",
            "dehydration": "dehydration",
            "nausea": "nausea",
            "constipation": "constipation",
            "acidity": "acidity",
            "indigestion": "indigestion",
        }
        for k, v in manual.items():
            if v in self.feature_set:
                add(k, v)
        return aliases

    def extract_duration(self, text: str) -> str | None:
        if not text:
            return None
        m = DURATION_PATTERN.search(text)
        if m:
            num = m.group("num")
            unit = m.group("unit").lower()
            # normalize unit pluralization
            if not unit.endswith("s") and num != "1":
                unit = unit + "s"
            if unit.endswith("s") and num == "1":
                unit = unit[:-1]
            return f"{num} {unit}"
        norm = self.normalize_text(text)
        # textual duration-only hints
        if norm in {"since yesterday", "since today"}:
            return norm
        return None

    def is_duration_only(self, symptoms_text: str, duration_text: str | None = None) -> bool:
        text = (symptoms_text or "").strip()
        if not text:
            return False
        for pat in DURATION_ONLY_PATTERNS:
            if pat.match(text):
                return True
        # remove duration phrases; if nothing symptom-like remains, treat as duration-only
        without_duration = DURATION_PATTERN.sub(" ", text)
        norm = self.normalize_text(without_duration)
        if not norm:
            return True
        # if the only token(s) resemble duration markers
        if norm in {"day", "days", "week", "weeks", "month", "months", "year", "years", "hour", "hours", "since yesterday", "since today"}:
            return True
        return False

    def _candidate_phrases(self, text: str) -> List[str]:
        # Remove duration fragments before splitting so "fever for 3 days" -> "fever"
        cleaned = DURATION_PATTERN.sub(" ", text or "")
        cleaned = cleaned.replace("/", " ")
        parts = [p.strip() for p in SPLIT_PATTERN.split(cleaned) if p and p.strip()]
        if not parts:
            parts = [cleaned.strip()] if cleaned.strip() else []
        # also consider whole cleaned text for multi-word matches
        norm_whole = self.normalize_text(cleaned)
        if norm_whole and norm_whole not in [self.normalize_text(p) for p in parts]:
            parts.append(norm_whole)
        # de-duplicate preserving order
        out = []
        seen = set()
        for p in parts:
            n = self.normalize_text(p)
            if not n or n in seen:
                continue
            seen.add(n)
            out.append(p)
        return out

    def _match_feature(self, phrase: str) -> str | None:
        norm = self.normalize_text(phrase)
        if not norm:
            return None
        # direct alias/feature lookup
        if norm in self.alias_map:
            return self.alias_map[norm]
        underscored = norm.replace(" ", "_")
        if underscored in self.feature_set:
            return underscored
        # try token-contained alias matching for short phrases
        # prefer longer alias matches
        for alias in sorted(self.alias_map.keys(), key=len, reverse=True):
            if len(alias) < 4:
                continue
            if alias == norm:
                return self.alias_map[alias]
            if f" {alias} " in f" {norm} ":
                return self.alias_map[alias]
        # fuzzy match against aliases and feature display names
        choices = list(self.alias_map.keys())
        match = get_close_matches(norm, choices, n=1, cutoff=0.88)
        if match:
            return self.alias_map[match[0]]
        # fuzzy against features
        feat_match = get_close_matches(underscored, self.feature_columns, n=1, cutoff=0.9)
        if feat_match:
            return feat_match[0]
        return None

    def process(self, symptoms_text: str, duration_text: str | None = None) -> NLPExtractionResult:
        result = NLPExtractionResult()
        symptoms_text = symptoms_text or ""
        duration_text = (duration_text or "").strip() or None

        # Extract duration separately (never treat as symptom)
        result.duration = duration_text or self.extract_duration(symptoms_text)

        # Validation: empty
        if not symptoms_text.strip() and not duration_text:
            result.validation_message = "Please enter your symptoms before starting the analysis."
            result.notes.append("Empty symptoms and duration.")
            return result
        if not symptoms_text.strip() and duration_text:
            result.validation_message = "Please enter your symptoms before starting the analysis."
            result.notes.append("Duration provided without symptoms.")
            return result
        if self.is_duration_only(symptoms_text, duration_text):
            result.validation_message = "Duration alone is not enough. Please describe your symptoms (for example: fever, cough, headache)."
            result.notes.append("Rejected duration-only symptom input.")
            return result

        phrases = self._candidate_phrases(symptoms_text)
        mapped: List[str] = []
        unsupported: List[str] = []
        extracted: List[str] = []
        seen_features = set()
        for phrase in phrases:
            norm_phrase = self.normalize_text(phrase)
            if not norm_phrase:
                continue
            # skip pure duration phrases if somehow remain
            if DURATION_PATTERN.fullmatch(phrase.strip() or ""):
                continue
            feature = self._match_feature(phrase)
            if feature:
                if feature not in seen_features:
                    mapped.append(feature)
                    seen_features.add(feature)
                extracted.append(norm_phrase)
            else:
                # avoid adding empty/generic noise
                if len(norm_phrase) >= 3 and norm_phrase not in {"symptom", "symptoms", "pain"}:
                    unsupported.append(norm_phrase)
                    extracted.append(norm_phrase)

        # de-duplicate unsupported while preserving order
        seen_u = set()
        unsupported_unique = []
        for u in unsupported:
            if u not in seen_u:
                unsupported_unique.append(u)
                seen_u.add(u)

        result.extracted_symptoms = extracted
        result.normalized_symptoms = [f.replace("_", " ") for f in mapped]
        result.mapped_features = mapped
        result.unsupported_symptoms = unsupported_unique

        if not mapped:
            result.validation_message = "No supported symptoms could be identified. Please describe specific symptoms such as fever, cough, headache, nausea, or skin rash."
            result.notes.append("No mappable symptoms found; prediction will not run.")
            return result

        result.valid_for_prediction = True
        if unsupported_unique:
            result.notes.append("Some symptoms were not recognized and were excluded from model input.")
        if result.duration:
            result.notes.append("Duration captured separately and not used as a symptom feature.")
        return result
