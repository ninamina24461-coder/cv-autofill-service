# CV Autofill System

A small external service for extracting structured CV data and returning a payload that can directly autofill your recruitment app.

## What it does

- Accepts PDF, DOCX, TXT, and MD uploads
- Extracts plain text
- Detects:
  - personal details
  - education
  - work experience
  - skills
  - certifications
  - languages
  - projects
  - achievements
- Normalizes phones, names, years, links, and dates
- Returns both:
  - a structured extraction payload
  - a candidate-shaped payload for database autofill

## Run locally

```bash
python -m venv .venv
source .venv/bin/activate   # Windows: .venv\Scripts\activate
pip install -r requirements.txt
cp .env.example .env
uvicorn app.main:app --reload --port 8000
```

## Endpoints

- `GET /health`
- `POST /v1/extract`
- `POST /v1/autofill`
- `POST /v1/merge`

## Recommended integration flow

1. Upload CV to `/v1/extract`
2. Review JSON result
3. Send result to `/v1/autofill` or `/v1/merge`
4. Persist the returned `candidate_payload` into your database

## Deployment

### Render (Recommended)

1. **Push to GitHub** (see below for security checklist)
2. **Create Render account**: https://render.com
3. **New Web Service** → Connect your GitHub repo
4. **Configure**:
   - Build Command: `pip install -r requirements.txt`
   - Start Command: `uvicorn app.main:app --host 0.0.0.0 --port $PORT`
   - Environment: Set `APP_ENV=production`

Or use `render.yaml` (Blueprints) for automatic deployment.

### Docker

```bash
docker build -t cv-autofill .
docker run -p 8000:8000 cv-autofill
```

## Pre-Deployment Security Checklist

Before pushing to GitHub:

- [ ] `.env` file contains NO database passwords or secrets
- [ ] `.gitignore` includes: `.env`, `.venv/`, `__pycache__/`, `*.pyc`
- [ ] Test files (PDFs, DOCXs) are in `.gitignore` or removed
- [ ] `render.yaml` is configured with proper environment variables

## Notes

- This version is deterministic and does not depend on a cloud AI service.
- OCR is left optional; the service works best with text-based CVs.
- For scanned PDFs, add OCR later as a separate worker.
