from __future__ import annotations

from fastapi import FastAPI, File, HTTPException, UploadFile
from fastapi.middleware.cors import CORSMiddleware

from .core.config import settings
from .mapper import map_resume, merge_candidate, to_candidate_payload
from .schemas import AutofillResponse, MergeRequest, MergeResponse

app = FastAPI(title=settings.app_name, version="2.0.0")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


@app.get("/health")
def health():
    return {"status": "ok", "service": settings.app_name, "env": settings.app_env}


@app.post("/v1/extract", response_model=AutofillResponse)
async def extract_cv(file: UploadFile = File(...)):
    content = await file.read()
    if not content:
        raise HTTPException(status_code=400, detail="empty file")

    extracted, warnings, errors = map_resume(
        filename=file.filename,
        content=content,
        mime_type=file.content_type,
        default_phone_region=settings.default_phone_region,
        max_chars=settings.max_text_chars,
    )

    return AutofillResponse(
        filename=file.filename,
        mime_type=file.content_type,
        extracted=extracted,
        candidate_payload=to_candidate_payload(extracted),
        warnings=warnings,
        errors=errors,
    )


@app.post("/v1/autofill", response_model=AutofillResponse)
async def autofill_cv(file: UploadFile = File(...)):
    content = await file.read()
    if not content:
        raise HTTPException(status_code=400, detail="empty file")

    extracted, warnings, errors = map_resume(
        filename=file.filename,
        content=content,
        mime_type=file.content_type,
        default_phone_region=settings.default_phone_region,
        max_chars=settings.max_text_chars,
    )

    return AutofillResponse(
        filename=file.filename,
        mime_type=file.content_type,
        extracted=extracted,
        candidate_payload=to_candidate_payload(extracted),
        warnings=warnings,
        errors=errors,
    )


@app.post("/v1/merge", response_model=MergeResponse)
def merge_cv(payload: MergeRequest):
    merged, changes = merge_candidate(payload.current_candidate, payload.extracted)
    return MergeResponse(merged_candidate_payload=merged, changes=changes)
