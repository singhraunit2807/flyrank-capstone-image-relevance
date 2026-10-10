# Build Log

## Session 1 — Repository foundation
- Created FastAPI scaffold, offline lexical matching, demo data, initial tests, and evaluator documentation.

## Session 2 — Functional offline demo
- Made feature-hashing similarity deterministic across runs.
- Added demo catalogue startup seeding, mismatch guard, review endpoints, and regression tests.
- Added a GitHub Actions test workflow.

## Session 3 — Image ingestion and persistence
- Added SQLite schema and repository helpers for image metadata, suggestions, and review status.
- Added image upload endpoint with allowed MIME types and 10 MB request-size limit.
- Added Gemini Vision provider integration for structured subject, category, attributes, caption, and confidence extraction.
- Uploaded image files are stored under the configured upload directory; metadata and review decisions persist in SQLite.
- Added multipart dependency and updated Docker Compose to persist the data directory.
- Expanded tests for metadata persistence and invalid upload types.
- Updated setup instructions, environment configuration, evidence matrix, and limitations.

## Verification status
The implementation has been committed to GitHub, but a successful test run has not been confirmed in this session. Run python -m pytest -q locally or check the GitHub Actions run before claiming the tests pass.

## Remaining work for a production-grade system
- Replace lexical feature hashing with a trained multimodal embedding model and evaluate it on labeled data.
- Add background batch processing, retries, cost tracking, authentication/rate limits, and a production database for concurrent deployment.
- Measure ranking quality on a labeled benchmark.

AI assistance was used to draft and revise code, tests, and documentation. Review the code and verify behavior before deployment.
