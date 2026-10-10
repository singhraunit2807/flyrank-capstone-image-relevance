# Evidence

## Implemented in the repository

| Requirement | Status | Proof |
|---|---|---|
| FastAPI backend and Swagger UI | IMPLEMENTED | app/main.py |
| Structured image metadata validation | IMPLEMENTED | POST /images/analyze |
| Persistent image metadata | IMPLEMENTED | SQLite tables in app/database.py |
| Persistent match decisions and reviews | IMPLEMENTED | suggestions table in app/database.py |
| Local image file upload | IMPLEMENTED | POST /images/upload; MIME and 10 MB checks |
| Vision provider integration | IMPLEMENTED, KEY REQUIRED | app/vision.py calls Gemini Vision when GEMINI_API_KEY is configured |
| Offline relevance ranking | IMPLEMENTED BASELINE | app/core.py stable lexical feature hashing |
| Subject mismatch and confidence guards | IMPLEMENTED | app/core.py and tests/test_api.py |
| Automated tests | COMMITTED, EXECUTION NOT VERIFIED HERE | Run python -m pytest -q or inspect GitHub Actions |
| GitHub Actions workflow | ADDED | .github/workflows/tests.yml |
| Trained multimodal embedding model | TODO | Current matcher is lexical, not a trained semantic model |
| Batch jobs, retry queue, cost tracking | TODO | Not implemented |
| Production database deployment | TODO | SQLite is used for the local demo |
| Labeled evaluation benchmark | TODO | No accuracy metric is claimed |

## Local verification
    python -m pip install -r requirements.txt
    python -m pytest -q

For real image analysis, configure GEMINI_API_KEY in a local .env. Do not commit credentials. Without the key, the upload endpoint returns HTTP 503 and explains the missing configuration.
