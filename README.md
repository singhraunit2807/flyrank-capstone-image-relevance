# FlyRank AI Image Understanding & Content Matching Engine

A runnable FastAPI capstone demo that stores structured image metadata, ranks candidate images against article/post text, rejects clear subject mismatches and low-confidence records, and exposes explanations plus human-review endpoints.

> Scope note: this repository implements an offline lexical similarity baseline and a metadata API. It does not run a trained vision model on raw image files. The /images/analyze endpoint accepts structured metadata produced by a vision model or entered by a human.

## What works

- FastAPI application with interactive Swagger UI.
- Seeded demo catalogue (fox, wolf, dog, bear, deer, cat, bird).
- Metadata validation and confidence range checks.
- Stable, offline feature-hashing similarity score.
- Explicit subject mismatch guard (for example, reject a wolf for a fox post).
- Ranked match results with an explanation for each decision.
- Approve/reject review endpoints and review status.
- Automated API regression tests.

## Run locally (Windows PowerShell)

    py -m venv .venv
    .\.venv\Scripts\Activate.ps1
    python -m pip install -r requirements.txt
    python -m uvicorn app.main:app --reload

Open http://127.0.0.1:8000/docs. The server automatically seeds demo records at startup. To reset the catalogue, call POST /demo/seed from Swagger UI.

## Run with Docker

    docker compose up --build

Open http://127.0.0.1:8000/docs.

## Try the API

### 1. Check health

    curl http://127.0.0.1:8000/health

### 2. Match a post to images

    curl -X POST http://127.0.0.1:8000/posts/fox-post/match -H "Content-Type: application/json" -d '{"post_id":"fox-post","text":"The behavior of red foxes","threshold":0.10}'

The response includes a top suggestion (if any), ranked candidates, a score, a decision, and a reason. Wolf candidates are rejected by the explicit subject guard.

### 3. Add metadata for an image

    curl -X POST http://127.0.0.1:8000/images/analyze -H "Content-Type: application/json" -d '{"subject":"red fox","category":"animal","attributes":["orange fur","forest"],"caption":"A red fox in a forest","confidence":0.96}'

This endpoint receives metadata, not an image upload.

### 4. Explain and review a suggestion

Use the suggestion_id returned from a match with:
- GET /review/{suggestion_id}/why
- POST /review/{suggestion_id}/approve
- POST /review/{suggestion_id}/reject

## Tests

    python -m pytest -q

Tests cover health, catalogue seeding, request validation, fox-vs-wolf rejection, match ranking, review status, and post ID validation.

## Limitations and next steps

- Feature hashing is a transparent, deterministic lexical baseline, not a trained semantic embedding model.
- Vision tags/captions are supplied as structured metadata; raw image ingestion and model inference are not implemented.
- State is in memory and resets when the API process restarts; use a database before production deployment.
- The project is a working educational demo, not a production-ready moderation or recommendation service.

## Security

Do not commit API keys or a real .env file. The current demo does not require any external API key.

## License

MIT
