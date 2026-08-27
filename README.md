# FlyRank AI Image Understanding & Content Matching Engine

A backend capstone that understands an image library, creates structured image metadata, matches images to article/post content using semantic similarity, and rejects unsafe or low-confidence matches with an explanation.

## Project goal

Given a post such as **"The behavior of red foxes"**, the service should rank a red-fox image highly and reject a wolf image when the mismatch guard detects that the candidate is not actually a fox.

The capstone brief requires a dedicated public repository, reproducible run/seed steps, evidence for requirements, an AI-usage log, and no committed secrets.

## Architecture

```text
Images
  |
  v
Vision provider -> structured tags/caption/confidence -> validation
  |                                      |
  +-> image embedding -------------------+
                                         v
Post text -> post embedding -> similarity ranking
                                         |
                                         v
                              Mismatch Guard
                           /                  \
                    confident match       reject + reason
                           |                  |
                           +--------> Review API
```

## Current implementation

This repository starts with a runnable FastAPI backend and a provider abstraction so the project can be developed without committing an API key. The default development mode uses deterministic local embeddings and seeded metadata; a vision/embedding provider can be plugged in later.

### Planned core endpoints

- `GET /health`
- `GET /posts/{post_id}/images` — ranked image suggestions with guard decisions
- `POST /review/{suggestion_id}/approve`
- `POST /review/{suggestion_id}/reject`
- `GET /review/{suggestion_id}/why`
- `POST /images/analyze` — validate structured vision output

## Run locally

### Option A — Python

```bash
python -m venv .venv
# Windows
.venv\\Scripts\\activate
# macOS/Linux
# source .venv/bin/activate

pip install -r requirements.txt
python -m app.seed
uvicorn app.main:app --reload
```

Then open `http://127.0.0.1:8000/docs`.

### Option B — Docker

```bash
docker compose up --build
```

## Test

```bash
pytest -q
```

## Environment

Copy `.env.example` to `.env`. Never commit `.env` or real API keys.

## Evaluation

The project will maintain a small labeled evaluation set and report top-1 precision in this README once the evaluation pipeline is complete. The threshold must be selected from evaluation data rather than guessed.

## Limitations

- The initial scaffold does not claim production-grade vision accuracy.
- Local deterministic embeddings are a development fallback, not a substitute for a trained semantic embedding model.
- The vision provider is intentionally abstracted so Gemini or a local Ollama vision model can be added without changing the API contract.
- The repository currently contains the backend foundation; evidence will be updated as each capstone requirement is actually implemented and tested.

## License

MIT
