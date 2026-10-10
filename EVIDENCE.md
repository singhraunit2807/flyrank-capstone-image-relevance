# Evidence

This file separates implemented functionality from capabilities that still require additional engineering or verification.

## Current evidence

| Requirement | Status | Proof |
|---|---|---|
| Public dedicated GitHub repository | DONE | Public repository dedicated to this capstone. |
| Runnable FastAPI backend | IMPLEMENTED | Startup seeds a demo catalogue; interactive API docs are available at /docs. |
| Structured image metadata schema | IMPLEMENTED | POST /images/analyze validates subject, category, attributes, caption, and confidence. |
| Offline relevance ranking | IMPLEMENTED | app/core.py provides stable feature-hashing similarity and ranked decisions. |
| Clear subject mismatch guard | IMPLEMENTED | tests/test_api.py checks that wolf records are rejected for a fox post. |
| Low-confidence rejection | IMPLEMENTED | Candidates below the configured confidence floor are rejected. |
| Explanation endpoint | IMPLEMENTED | GET /review/{suggestion_id}/why returns score, decision, and reason after matching. |
| Human review status | IMPLEMENTED IN MEMORY | Approve/reject endpoints update review status; state is lost on process restart. |
| Automated API tests | ADDED, RUN PENDING | Six regression tests are committed; a successful CI run has not yet been verified. |
| GitHub Actions workflow | ADDED, RUN PENDING | .github/workflows/tests.yml runs pytest on push, pull request, or manual dispatch. |
| Raw image upload and vision-model inference | TODO | The API currently accepts structured metadata, not image files. |
| Trained semantic embedding provider | TODO | Current matcher is a deterministic lexical baseline, not a trained semantic model. |
| Batch processing and retries | TODO | Not implemented. |
| Cost tracking | TODO | Not implemented. |
| Persistent database and audit trail | TODO | Catalogue and review state are in memory. |
| Labeled evaluation set and measured top-1 precision | TODO | No measured benchmark is claimed. |

## Local verification

Run the following commands from the repository root:

    python -m pip install -r requirements.txt
    python -m pytest -q

The test suite must pass in a local or CI environment before marking automated verification complete.
