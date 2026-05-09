from __future__ import annotations

from typing import Dict, List, Optional


def confidence_from_presence(value) -> float:
    if value is None:
        return 0.0
    if isinstance(value, str):
        return 0.9 if value.strip() else 0.0
    if isinstance(value, list):
        return min(1.0, 0.35 + 0.12 * len(value))
    if isinstance(value, dict):
        present = sum(1 for v in value.values() if v not in (None, "", [], {}))
        total = max(len(value), 1)
        return round(present / total, 2)
    return 0.5


def build_confidence(personal: dict, education: list, experience: list, skills: list, certifications: list, languages: list) -> Dict[str, float]:
    return {
        "full_name": confidence_from_presence(personal.get("full_name")),
        "email": confidence_from_presence(personal.get("email")),
        "phone": confidence_from_presence(personal.get("phone")),
        "address": confidence_from_presence(personal.get("address")),
        "location": confidence_from_presence(personal.get("location")),
        "dob": confidence_from_presence(personal.get("dob")),
        "title": confidence_from_presence(personal.get("title")),
        "summary": confidence_from_presence(personal.get("summary")),
        "education": confidence_from_presence(education),
        "experience": confidence_from_presence(experience),
        "skills": confidence_from_presence(skills),
        "certifications": confidence_from_presence(certifications),
        "languages": confidence_from_presence(languages),
    }
