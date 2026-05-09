from __future__ import annotations

import re
from datetime import date, datetime
from typing import Optional

import phonenumbers
from dateutil import parser as date_parser

EMAIL_RE = re.compile(r'\b[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\.[A-Za-z]{2,}\b')
URL_RE = re.compile(r'https?://[^\s)\]]+|www\.[^\s)\]]+', re.IGNORECASE)


def clean_text(value: Optional[str]) -> Optional[str]:
    if value is None:
        return None
    value = " ".join(str(value).split())
    return value.strip() or None


def title_case_name(value: Optional[str]) -> Optional[str]:
    if not value:
        return None
    return " ".join(part.capitalize() if part.isalpha() else part for part in clean_text(value).split())


def normalize_email(value: Optional[str]) -> Optional[str]:
    if not value:
        return None
    value = clean_text(value)
    return value.lower() if value else None


def normalize_phone(value: Optional[str], default_region: str = "ZA") -> Optional[str]:
    if not value:
        return None
    value = clean_text(value)
    try:
        parsed = phonenumbers.parse(value, default_region)
        if phonenumbers.is_valid_number(parsed):
            return phonenumbers.format_number(parsed, phonenumbers.PhoneNumberFormat.E164)
    except Exception:
        return value
    return value


def normalize_url(value: Optional[str]) -> Optional[str]:
    if not value:
        return None
    value = clean_text(value)
    if not value:
        return None
    if value.startswith("www."):
        return "https://" + value
    return value


def extract_email(text: str) -> Optional[str]:
    m = EMAIL_RE.search(text or "")
    return normalize_email(m.group(0)) if m else None


def extract_urls(text: str):
    return [m.group(0).rstrip(".,;") for m in URL_RE.finditer(text or "")]


def first_year(text: str) -> Optional[str]:
    if not text:
        return None
    m = re.search(r'\b(19\d{2}|20\d{2})\b', text)
    return m.group(1) if m else None


def parse_date(value: Optional[str]) -> Optional[str]:
    if not value:
        return None
    value = clean_text(value)
    try:
        dt = date_parser.parse(value, fuzzy=True, dayfirst=True)
        return dt.date().isoformat()
    except Exception:
        return None
