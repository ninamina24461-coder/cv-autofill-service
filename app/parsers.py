from __future__ import annotations

import re
from typing import Dict, List, Optional, Tuple

from rapidfuzz import fuzz

from .utils import (
    clean_text,
    extract_email,
    extract_urls,
    first_year,
    normalize_email,
    normalize_phone,
    normalize_url,
    parse_date,
    title_case_name,
)

SECTION_ALIASES = {
    "education": ["education", "qualifications", "academic background", "studies"],
    "experience": ["experience", "work experience", "employment history", "professional experience", "work history"],
    "skills": ["skills", "technical skills", "core competencies", "competencies"],
    "certifications": ["certifications", "licenses", "professional certifications"],
    "languages": ["languages"],
    "projects": ["projects", "personal projects"],
    "achievements": ["awards", "honors", "honours", "achievements", "publications"],
}


def split_sections(text: str) -> Dict[str, str]:
    lines = [ln.rstrip() for ln in (text or "").splitlines()]
    if not lines:
        return {k: "" for k in SECTION_ALIASES}

    section_positions: List[Tuple[int, str]] = []
    for idx, line in enumerate(lines):
        normalized = re.sub(r'[^a-z ]', '', line.lower()).strip()
        for section, aliases in SECTION_ALIASES.items():
            if any(normalized == alias for alias in aliases):
                section_positions.append((idx, section))
                break

    if not section_positions:
        return {k: "" for k in SECTION_ALIASES}

    section_positions.sort()
    sections = {k: "" for k in SECTION_ALIASES}
    markers = section_positions + [(len(lines), "__end__")]
    for (start_idx, section), (end_idx, _) in zip(markers, markers[1:]):
        sections[section] = "\n".join(lines[start_idx + 1:end_idx]).strip()
    return sections


def extract_personal_info(text: str, default_region: str = "ZA") -> Dict[str, Optional[str]]:
    lines = [clean_text(x) for x in (text or "").splitlines() if clean_text(x)]
    head = lines[:10]

    email = extract_email(text)
    phone = _find_phone(text, default_region)
    linked = _find_link(text, "linkedin.com")
    github = _find_link(text, "github.com")
    portfolio = _find_portfolio(text)

    # Enhanced extraction for mixed line formats
    location = None
    linkedin_enhanced = None
    github_enhanced = None
    portfolio_enhanced = None
    
    for line in lines[:15]:  # Check more lines for better detection
        low = line.lower()
        
        # Extract location from mixed lines like "Johannesburg, South Africa | phone | email"
        if not location and any(city in low for city in ['johannesburg', 'cape town', 'durban', 'pretoria', 'south africa']):
            # Extract location part before first | or phone/email
            location_part = re.split(r'\s*\|\s*', line)[0]
            if any(city in location_part.lower() for city in ['johannesburg', 'cape town', 'durban', 'pretoria', 'south africa']):
                location = location_part.strip()
        
        # Extract LinkedIn from lines like "LinkedIn: linkedin.com/in/sarahjohnsondev"
        if not linkedin_enhanced and 'linkedin:' in low:
            linkedin_match = re.search(r'linkedin:\s*(\S+)', low)
            if linkedin_match:
                linkedin_enhanced = "https://" + linkedin_match.group(1)
        
        # Extract GitHub from lines like "GitHub: github.com/sjohnson"
        if not github_enhanced and 'github:' in low:
            github_match = re.search(r'github:\s*(\S+)', low)
            if github_match:
                github_enhanced = "https://" + github_match.group(1)
        
        # Extract Portfolio from lines like "Portfolio: sarahjohnson.dev"
        if not portfolio_enhanced and 'portfolio:' in low:
            portfolio_match = re.search(r'portfolio:\s*(\S+)', low)
            if portfolio_match:
                portfolio_url = portfolio_match.group(1)
                # Add https:// if no protocol present
                if not portfolio_url.startswith(('http://', 'https://')):
                    portfolio_enhanced = "https://" + portfolio_url
                else:
                    portfolio_enhanced = portfolio_url

    title = None
    name = None
    for line in head:
        low = line.lower()
        if email and email in low:
            continue
        if phone and phone.replace("+", "") in re.sub(r'\D', '', line):
            continue
        if any(domain in low for domain in ["linkedin.com", "github.com", "http", "www."]):
            continue

        if name is None and _looks_like_name(line):
            name = line
            continue

        if title is None and _looks_like_title(line):
            title = line
            continue

    summary = _find_summary(text)
    return {
        "full_name": title_case_name(name),
        "email": normalize_email(email),
        "phone": phone,
        "address": _find_label_value(text, "address"),
        "location": location or _find_label_value(text, "location") or _find_label_value(text, "city"),
        "dob": parse_date(_find_label_value(text, "date of birth") or _find_label_value(text, "dob")),
        "gender": _find_gender(text),
        "nationality": _find_label_value(text, "nationality"),
        "linkedin": normalize_url(linkedin_enhanced or linked),
        "github": normalize_url(github_enhanced or github),
        "portfolio": normalize_url(portfolio_enhanced or portfolio),
        "summary": summary,
        "title": title,
    }


def extract_education(text: str, section_text: str) -> List[Dict[str, Optional[str]]]:
    blob = section_text or text
    lines = [clean_text(ln) for ln in blob.splitlines() if clean_text(ln)]
    items: List[Dict[str, Optional[str]]] = []
    buffer: List[str] = []

    def flush():
        nonlocal buffer
        if not buffer:
            return
        item = _edu_from_blob(" | ".join(buffer))
        if any(item.values()):
            items.append(item)
        buffer = []

    for line in lines:
        if _is_education_line(line) or first_year(line):
            buffer.append(line)
        elif buffer:
            buffer.append(line)
            if len(buffer) >= 4:
                flush()
        else:
            continue

        if len(buffer) >= 3 and first_year(buffer[-1]):
            flush()

    flush()
    return _dedupe_dicts(items)


def extract_experience(text: str, section_text: str) -> List[Dict[str, Optional[str]]]:
    blob = section_text or text
    lines = [clean_text(ln) for ln in blob.splitlines() if clean_text(ln)]
    items: List[Dict[str, Optional[str]]] = []
    current: List[str] = []

    for line in lines:
        if _looks_like_experience_header(line):
            if current:
                items.append(_exp_from_blob(" | ".join(current)))
            current = [line]
        else:
            current.append(line)

    if current:
        items.append(_exp_from_blob(" | ".join(current)))

    return [x for x in _dedupe_dicts(items) if any(x.values())]


def extract_list_from_section(text: str, section_text: str) -> List[str]:
    blob = section_text or text
    items: List[str] = []
    for line in blob.splitlines():
        line = clean_text(line)
        if not line:
            continue
        line = line.lstrip("•*-–— ").strip()
        if not line:
            continue
        parts = [p.strip() for p in re.split(r',|\|', line) if p.strip()]
        if len(parts) > 1:
            items.extend(parts)
        else:
            items.append(line)
    return _dedupe_strings(items)


def extract_skills(text: str, section_text: str) -> List[str]:
    items = extract_list_from_section(text, section_text)
    common_skills = [
        "python", "java", "javascript", "typescript", "react", "node", "django", "flask",
        "fastapi", "sql", "postgresql", "mysql", "mongodb", "redis", "html", "css",
        "git", "docker", "kubernetes", "aws", "azure", "gcp", "linux", "excel",
        "power bi", "tableau", "powerbi", "machine learning", "data analysis",
        "communication", "leadership", "project management", "customer service",
        "problem solving", "teamwork"
    ]
    out = []
    hay = text.lower()
    for skill in common_skills:
        if skill in hay or any(fuzz.partial_ratio(skill, x.lower()) >= 92 for x in items):
            out.append(skill.title() if skill not in {"sql", "aws", "gcp"} else skill.upper())
    for item in items:
        out.append(item.title())
    return _dedupe_strings(out)


def extract_languages(text: str, section_text: str) -> List[str]:
    items = extract_list_from_section(text, section_text)
    known = ["English", "Afrikaans", "Zulu", "Xhosa", "French", "German", "Spanish", "Portuguese", "Arabic", "Chinese"]
    out = []
    hay = text.lower()
    for lang in known:
        if lang.lower() in hay or any(fuzz.partial_ratio(lang.lower(), x.lower()) >= 90 for x in items):
            out.append(lang)
    out.extend([x.title() for x in items])
    return _dedupe_strings(out)


def extract_certifications(text: str, section_text: str) -> List[str]:
    return _dedupe_strings(extract_list_from_section(text, section_text))


def extract_projects(text: str, section_text: str) -> List[str]:
    return _dedupe_strings(extract_list_from_section(text, section_text))


def extract_achievements(text: str, section_text: str) -> List[str]:
    return _dedupe_strings(extract_list_from_section(text, section_text))


def _find_phone(text: str, default_region: str) -> Optional[str]:
    candidates = re.findall(r'(?:\+?\d[\d\s().-]{7,}\d)', text or "")
    for c in candidates:
        norm = normalize_phone(c, default_region)
        if norm:
            return norm
    return None


def _find_link(text: str, domain: str) -> Optional[str]:
    for url in extract_urls(text):
        if domain in url.lower():
            return url
    return None


def _find_portfolio(text: str) -> Optional[str]:
    for url in extract_urls(text):
        low = url.lower()
        if "linkedin.com" in low or "github.com" in low:
            continue
        return url
    return None


def _find_summary(text: str) -> Optional[str]:
    m = re.search(r'(?is)(?:summary|profile|professional summary)\s*[:\-]?\s*(.+?)(?:\n\s*(?:education|experience|work experience|skills|certifications|languages|projects)\b|\Z)', text or "")
    if not m:
        return None
    summary = clean_text(m.group(1))
    return summary[:700] if summary else None


def _find_label_value(text: str, label: str) -> Optional[str]:
    m = re.search(rf'(?im)^\s*{re.escape(label)}\s*[:\-]\s*(.+)$', text or "")
    return clean_text(m.group(1)) if m else None


def _find_gender(text: str) -> Optional[str]:
    m = re.search(r'(?im)^\s*gender\s*[:\-]\s*(male|female|other|non-binary|prefer not to say)\b', text or "")
    return m.group(1).title() if m else None


def _looks_like_name(line: str) -> bool:
    if len(line.split()) < 2 or len(line.split()) > 5:
        return False
    if any(ch.isdigit() for ch in line):
        return False
    if "@" in line or "linkedin" in line.lower() or "github" in line.lower():
        return False
    return True


def _looks_like_title(line: str) -> bool:
    hints = [
        "engineer", "developer", "analyst", "manager", "consultant", "designer",
        "specialist", "administrator", "coordinator", "director", "assistant", "officer"
    ]
    low = line.lower()
    return any(h in low for h in hints) and len(line.split()) <= 8


def _is_education_line(line: str) -> bool:
    low = line.lower()
    hints = [
        "university", "college", "institute", "school", "polytechnic", "bachelor",
        "master", "diploma", "certificate", "degree", "phd", "mba"
    ]
    return any(h in low for h in hints)


def _looks_like_experience_header(line: str) -> bool:
    low = line.lower()
    if " at " in low:
        return True
    if any(h in low for h in ["engineer", "developer", "analyst", "manager", "consultant", "designer", "specialist", "officer", "coordinator"]):
        return True
    return bool(re.search(r'\b(19\d{2}|20\d{2})\b', line) and ("-" in line or "to" in low))


def _edu_from_blob(blob: str) -> Dict[str, Optional[str]]:
    degree = None
    university = None
    year = None
    field = None
    low = blob.lower()

    for hint in ["phd", "doctorate", "mba", "master", "msc", "bsc", "bachelor", "diploma", "certificate", "degree", "honours", "honors"]:
        if hint in low:
            degree = blob
            break

    year = first_year(blob)
    parts = [p.strip() for p in re.split(r'\||,|\s+-\s+', blob) if p.strip()]
    for part in parts:
        plow = part.lower()
        if any(x in plow for x in ["university", "college", "institute", "school", "polytechnic"]):
            university = part
        if any(x in plow for x in ["computer science", "engineering", "accounting", "finance", "business", "mathematics", "information technology", "law"]):
            field = part

    return {"degree": degree, "university": university, "year": year, "field": field}


def _exp_from_blob(blob: str) -> Dict[str, Optional[str]]:
    title = None
    company = None
    period = None
    location = None
    description = None

    parts = [p.strip() for p in re.split(r'\||•', blob) if p.strip()]
    if parts:
        first = parts[0]
        if " at " in first.lower():
            left, right = re.split(r'(?i)\s+at\s+', first, maxsplit=1)
            title, company = left.strip(), right.strip()
        elif " - " in first:
            left, right = first.split(" - ", 1)
            title, company = left.strip(), right.strip()
        else:
            title = first.strip()

    years = re.findall(r'\b(?:19\d{2}|20\d{2})\b', blob)
    if years:
        period = blob[blob.find(years[0]):].strip()

    if len(parts) > 1:
        description = " ".join(parts[1:])

    return {
        "title": title,
        "company": company,
        "period": period,
        "description": description,
        "location": location,
        "start_year": years[0] if len(years) > 0 else None,
        "end_year": years[-1] if len(years) > 1 else None,
    }


def _dedupe_strings(items: List[str]) -> List[str]:
    seen = set()
    out = []
    for item in items:
        item = clean_text(item)
        if not item:
            continue
        key = item.lower()
        if key in seen:
            continue
        seen.add(key)
        out.append(item)
    return out


def _dedupe_dicts(items: List[Dict[str, Optional[str]]]) -> List[Dict[str, Optional[str]]]:
    seen = set()
    out = []
    for item in items:
        key = tuple((k, (v or "").strip().lower()) for k, v in sorted(item.items()))
        if key in seen:
            continue
        seen.add(key)
        out.append(item)
    return out
