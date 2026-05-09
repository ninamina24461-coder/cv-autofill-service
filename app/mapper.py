from __future__ import annotations

from typing import Any, Dict, List, Optional, Tuple

from .confidence import build_confidence
from .extractors import extract_text
from .parsers import (
    extract_achievements,
    extract_certifications,
    extract_education,
    extract_experience,
    extract_languages,
    extract_personal_info,
    extract_projects,
    extract_skills,
    split_sections,
)
from .schemas import AutofillResult, EducationInfo, ExperienceInfo, PersonalInfo
from .utils import clean_text


def map_resume(filename: str, content: bytes, mime_type: Optional[str], default_phone_region: str = "ZA", max_chars: int = 80000) -> Tuple[AutofillResult, List[str], List[str]]:
    extraction = extract_text(filename, content, mime_type)
    text = (extraction.text or "")[:max_chars]
    warnings = list(extraction.warnings)
    errors: List[str] = []

    if not text.strip():
        return AutofillResult(raw_text="", confidence={}), warnings, ["no_text_extracted"]

    sections = split_sections(text)

    personal = extract_personal_info(text, default_phone_region)
    education = extract_education(text, sections.get("education", ""))
    experience = extract_experience(text, sections.get("experience", ""))
    skills = extract_skills(text, sections.get("skills", ""))
    certifications = extract_certifications(text, sections.get("certifications", ""))
    languages = extract_languages(text, sections.get("languages", ""))
    projects = extract_projects(text, sections.get("projects", ""))
    achievements = extract_achievements(text, sections.get("achievements", ""))

    confidence = build_confidence(personal, education, experience, skills, certifications, languages)

    result = AutofillResult(
        personal=PersonalInfo(**personal),
        education=[EducationInfo(**x) for x in education],
        experience=[ExperienceInfo(**x) for x in experience],
        skills=skills,
        certifications=certifications,
        languages=languages,
        projects=projects,
        achievements=achievements,
        raw_text=text,
        confidence=confidence,
    )
    return result, warnings, errors


def to_candidate_payload(extracted: AutofillResult) -> Dict[str, Any]:
    p = extracted.personal.model_dump(exclude_none=True)
    education = [item.model_dump(exclude_none=True) for item in extracted.education]
    experience = [item.model_dump(exclude_none=True) for item in extracted.experience]

    payload = {
        "full_name": p.get("full_name"),
        "phone": p.get("phone"),
        "dob": p.get("dob"),
        "address": p.get("address"),
        "location": p.get("location"),
        "gender": p.get("gender"),
        "nationality": p.get("nationality"),
        "bio": p.get("summary"),
        "title": p.get("title"),
        "linkedin": p.get("linkedin"),
        "github": p.get("github"),
        "portfolio": p.get("portfolio"),
        "education": education,
        "skills": extracted.skills,
        "work_experience": experience,
        "certifications": extracted.certifications,
        "languages": extracted.languages,
        "profile": {
            "projects": extracted.projects,
            "achievements": extracted.achievements,
            "confidence": extracted.confidence,
        },
        "education_level": education[0].get("degree") if education else None,
        "education_field": education[0].get("field") if education else None,
        "university": education[0].get("university") if education else None,
        "graduation_year": education[0].get("year") if education else None,
        "previous_companies": ", ".join([x.get("company") for x in experience if x.get("company")]),
        "experience_summary": " ".join([x.get("description", "") for x in experience if x.get("description")]),
        "position": experience[0].get("title") if experience else None,
    }
    return {k: v for k, v in payload.items() if v not in (None, "", [], {})}


def merge_candidate(current_candidate: Dict[str, Any], extracted: AutofillResult) -> Tuple[Dict[str, Any], Dict[str, Any]]:
    current = dict(current_candidate or {})
    candidate = to_candidate_payload(extracted)
    changes: Dict[str, Any] = {}

    for key, new_val in candidate.items():
        old_val = current.get(key)
        if old_val in (None, "", [], {}):
            current[key] = new_val
            changes[key] = {"from": old_val, "to": new_val}
        elif key in {"skills", "certifications", "languages"} and isinstance(old_val, list) and isinstance(new_val, list):
            merged = _dedupe_list(old_val + new_val)
            if merged != old_val:
                current[key] = merged
                changes[key] = {"from": old_val, "to": merged}
        elif key == "profile" and isinstance(old_val, dict) and isinstance(new_val, dict):
            merged = {**old_val, **new_val}
            if merged != old_val:
                current[key] = merged
                changes[key] = {"from": old_val, "to": merged}
    return current, changes


def _dedupe_list(items: List[Any]) -> List[Any]:
    seen = set()
    out = []
    for item in items:
        key = str(item).strip().lower()
        if key in seen or not key:
            continue
        seen.add(key)
        out.append(item)
    return out
