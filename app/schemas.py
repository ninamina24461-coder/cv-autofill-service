from __future__ import annotations

from typing import Any, Dict, List, Literal, Optional

from pydantic import BaseModel, ConfigDict, EmailStr, Field


class PersonalInfo(BaseModel):
    model_config = ConfigDict(extra="forbid")

    full_name: Optional[str] = None
    email: Optional[EmailStr] = None
    phone: Optional[str] = None
    address: Optional[str] = None
    location: Optional[str] = None
    dob: Optional[str] = None
    gender: Optional[str] = None
    nationality: Optional[str] = None
    linkedin: Optional[str] = None
    github: Optional[str] = None
    portfolio: Optional[str] = None
    summary: Optional[str] = None
    title: Optional[str] = None


class EducationInfo(BaseModel):
    model_config = ConfigDict(extra="forbid")

    degree: Optional[str] = None
    university: Optional[str] = None
    year: Optional[str] = None
    field: Optional[str] = None


class ExperienceInfo(BaseModel):
    model_config = ConfigDict(extra="forbid")

    title: Optional[str] = None
    company: Optional[str] = None
    period: Optional[str] = None
    description: Optional[str] = None
    location: Optional[str] = None
    start_year: Optional[str] = None
    end_year: Optional[str] = None


class AutofillResult(BaseModel):
    model_config = ConfigDict(extra="forbid")

    personal: PersonalInfo = Field(default_factory=PersonalInfo)
    education: List[EducationInfo] = Field(default_factory=list)
    experience: List[ExperienceInfo] = Field(default_factory=list)
    skills: List[str] = Field(default_factory=list)
    certifications: List[str] = Field(default_factory=list)
    languages: List[str] = Field(default_factory=list)
    projects: List[str] = Field(default_factory=list)
    achievements: List[str] = Field(default_factory=list)
    raw_text: Optional[str] = None
    confidence: Dict[str, float] = Field(default_factory=dict)


class AutofillResponse(BaseModel):
    model_config = ConfigDict(extra="forbid")

    status: Literal["ok"] = "ok"
    filename: str
    mime_type: Optional[str] = None
    extracted: AutofillResult
    candidate_payload: Dict[str, Any] = Field(default_factory=dict)
    warnings: List[str] = Field(default_factory=list)
    errors: List[str] = Field(default_factory=list)


class MergeRequest(BaseModel):
    model_config = ConfigDict(extra="forbid")

    current_candidate: Dict[str, Any]
    extracted: AutofillResult


class MergeResponse(BaseModel):
    model_config = ConfigDict(extra="forbid")

    status: Literal["ok"] = "ok"
    merged_candidate_payload: Dict[str, Any]
    changes: Dict[str, Any] = Field(default_factory=dict)
