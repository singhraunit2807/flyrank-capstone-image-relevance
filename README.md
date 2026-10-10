# FlyRank AI Image Understanding & Content Matching Engine

A runnable FastAPI capstone demo that stores image metadata, optionally analyzes uploaded images with Gemini Vision, ranks image candidates against article/post text, rejects clear subject mismatches, and supports human review with persistent SQLite storage.

## Features
- FastAPI backend with interactive Swagger UI.
- Demo catalogue covering fox, wolf, dog, bear, deer, cat, and bird.
- JPEG, PNG, WEBP, and GIF upload (maximum 10 MB).
- Optional Gemini Vision metadata extraction: subject, category, attributes, caption, and confidence.
- Stable offline lexical similarity baseline and explicit subject mismatch guard.
- Ranked suggestions, explanations, and human review.
- SQLite persistence for metadata and review results across restarts.
- Automated API regression tests and GitHub Actions workflow.

## Important AI scope note
Uploaded images are sent to the configured Gemini Vision API for analysis. You need your own Gemini API key for that feature. Without a key, the upload endpoint returns a configuration error rather than pretending analysis succeeded. Matching currently uses deterministic lexical feature hashing, not a trained multimodal embedding model. This is an educational working demo, not a production-grade image search system.

## Run locally (Windows PowerShell)
    py -m venv .venv
    .\.venv\Scripts\Activate.ps1
    python -m pip install -r requirements.txt
    Copy-Item .env.example .env
    # Add your GEMINI_API_KEY to .env to enable image vision analysis
    python -m uvicorn app.main:app --reload

Open http://127.0.0.1:8000/docs.

Linux/macOS:
    python -m venv .venv
    source .venv/bin/activate
    python -m pip install -r requirements.txt
    cp .env.example .env
    python -m uvicorn app.main:app --reload

## Environment
- GEMINI_API_KEY: required only for image upload and AI vision analysis.
- GEMINI_MODEL: optional; defaults to gemini-2.5-flash.
- DATABASE_PATH: optional; defaults to data/flyrank.db.
- UPLOAD_DIR: optional; defaults to data/uploads.

Never commit a real API key or populated .env file.

## Try the API
- GET /health reports database mode, catalogue count, and vision configuration.
- GET /images lists persisted image metadata.
- POST /demo/seed resets the catalogue to demo records.
- POST /images/upload accepts an image and uses Gemini Vision to extract metadata; a key is required.
- POST /images/analyze accepts manually supplied structured metadata without a vision key.
- POST /posts/{post_id}/match ranks images for post content.
- GET /review/{suggestion_id}/why explains a decision.
- POST /review/{suggestion_id}/approve and /reject store review decisions.

Manual metadata example:
    curl -X POST http://127.0.0.1:8000/images/analyze -H "Content-Type: application/json" -d '{"subject":"red fox","category":"animal","attributes":["orange fur","forest"],"caption":"A red fox in a forest","confidence":0.96}'

Matching example:
    curl -X POST http://127.0.0.1:8000/posts/fox-post/match -H "Content-Type: application/json" -d '{"post_id":"fox-post","text":"The behavior of red foxes","threshold":0.10}'

## Docker
    docker compose up --build
Open http://127.0.0.1:8000/docs. Docker Compose mounts ./data so the SQLite database and uploaded images survive container recreation.

## Tests
    python -m pytest -q
Tests cover health, demo seeding, metadata validation and persistence, mismatch rejection, ranking, review persistence, invalid post IDs, and upload content-type validation.

## Current limitations
- Gemini vision analysis requires a user-supplied API key and internet access.
- Similarity is lexical feature hashing, not a trained semantic or multimodal embedding model.
- SQLite suits a local demo; concurrent production deployments should use a managed database.
- Confidence is model-reported and is not calibrated certainty.
- No benchmark accuracy or production readiness is claimed.

## License
MIT
