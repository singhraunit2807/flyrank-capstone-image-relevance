# FlyRank AI Image Understanding & Content Matching Engine

FastAPI capstone demo for image upload, Gemini Vision metadata extraction, relevance ranking, mismatch guards, human review, and SQLite or managed PostgreSQL storage.

## Features
- JPEG, PNG, WEBP, and GIF uploads up to 10 MB.
- Gemini Vision extracts subject, category, attributes, caption, and confidence.
- With GEMINI_API_KEY configured, ranking uses Gemini semantic text embeddings (gemini-embedding-001) for post text versus image descriptions.
- Without a key, ranking falls back to a deterministic offline lexical baseline.
- Subject-mismatch and low-confidence guards apply in both ranking modes.
- SQLite persists metadata, suggestions, and review decisions.
- Docker Compose persists the data directory.
- Automated tests and GitHub Actions workflow.

## Run locally (Windows PowerShell)
    py -m venv .venv
    .\.venv\Scripts\Activate.ps1
    python -m pip install -r requirements.txt
    Copy-Item .env.example .env
    # Add your Gemini API key to .env
    python -m uvicorn app.main:app --reload

Open http://127.0.0.1:8000/docs.

## Environment
- GEMINI_API_KEY: required for image vision and semantic embedding ranking; keep it secret.
- GEMINI_MODEL: defaults to gemini-3.8-flash.
- GEMINI_EMBEDDING_MODEL: defaults to gemini-embedding-001.
- DATABASE_URL: optional PostgreSQL connection string; when set, FlyRank uses PostgreSQL instead of SQLite. For Supabase, use the connection string from Project Settings → Database and require SSL.
- SUPABASE_URL and SUPABASE_SERVICE_ROLE_KEY: when both are set, uploaded image bytes are stored in Supabase Storage. Keep the service-role key secret and server-side only.
- SUPABASE_STORAGE_BUCKET: defaults to `flyrank-images`; the app creates this private bucket if it does not exist.
- DATABASE_PATH and UPLOAD_DIR: local SQLite and upload paths used when managed services are not configured. On Vercel, these fall back to ephemeral `/tmp` paths.

## Main endpoints
- GET /health — reports catalogue count, provider configuration, and ranking mode.
- GET /images — lists stored metadata.
- POST /demo/seed — resets the demo catalogue.
- POST /images/upload — upload an image for Gemini Vision analysis; API key required.
- POST /images/analyze — manually provide structured metadata.
- POST /posts/{post_id}/match — rank images for post content.
- GET /review/{suggestion_id}/why — explain a decision.
- POST /review/{suggestion_id}/approve and /reject — persist review status.

## Production deployment (Render)

A Render Blueprint is provided in `render.yaml`. It configures a production service, a persistent disk for SQLite and uploads, the current Gemini vision model, and a generated `FLYRANK_API_TOKEN`.

1. Connect this GitHub repository to Render and create a Blueprint from `render.yaml`.
2. In Render's environment settings, set `GEMINI_API_KEY` using Google AI Studio. Do not commit it or share it in chat.
3. Keep `APP_ENV=production` and the generated `FLYRANK_API_TOKEN`. Treat the token like a password.
4. Only `/` and `/health` are public. All other API routes require `Authorization: Bearer <FLYRANK_API_TOKEN>`.
5. The service uses a persistent disk for the SQLite database and uploaded images. The Render disk and service plan may incur charges; review Render's current pricing before creating the service.

Do not deploy with a missing API token. Production requests fail closed when `FLYRANK_API_TOKEN` is not configured. The single shared bearer token is suitable only for a controlled demo; a multi-user production product needs per-user authentication, rate limiting, usage quotas, monitoring, and a managed database.

## Security checks

GitHub Actions runs Bandit static analysis and `pip-audit` on dependencies for pushes, pull requests, and weekly scheduled checks. Review any reported vulnerability before deployment.

## Docker
    docker compose up --build
Open http://127.0.0.1:8000/docs. Configure .env first; ./data is mounted for persistent database and uploads.

## Live Gemini verification

1. Create a Gemini API key in Google AI Studio and put it in your local `.env` as `GEMINI_API_KEY=...`. Never commit `.env` or paste the key into chat.
2. Start the API in the same environment where `.env` is available: `python -m uvicorn app.main:app --reload`.
3. In a second terminal, activate the same virtual environment and run against a real local image: `python scripts/verify_gemini_live.py --image "path/to/your-image.jpg"`.
4. A successful run prints `PASS: real Gemini vision upload and semantic ranking endpoint completed.` The match itself may still be rejected by confidence or subject guards; inspect the printed metadata and suggestion.

This live check requires internet access, a valid API key with access/quota, and a real supported image. Automated CI uses mocked provider responses and does not verify live credentials.

## Tests
    python -m pytest -q
The GitHub Actions test workflow has passed for the semantic-ranking and mismatch-guard changes. Check the latest workflow run for subsequent commits.

## Limitations
- Real image analysis and semantic embeddings require a Gemini API key, internet access, and provider quota.
- Semantic mode embeds post text against descriptions extracted by vision; it does not directly embed raw image pixels. The vision model first converts uploaded pixels into metadata.
- Without a key, matching uses lexical feature hashing.
- SQLite is intended for a local demo, not high-concurrency production. Authentication, rate limits, managed storage, retry jobs, cost controls, and labeled ranking benchmarks remain future work.

## License
MIT
