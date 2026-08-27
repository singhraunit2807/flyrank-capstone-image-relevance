# Build Log

This file records AI-assisted development honestly, as required by the capstone brief.

## Session 1 — Repository foundation

- Created the dedicated public repository.
- Added the evaluator-facing README, `capstone.yaml`, `EVIDENCE.md`, `.env.example`, and `.gitignore`.
- Added a FastAPI application scaffold.
- Added a provider-independent deterministic embedding fallback for local development.
- Added a first mismatch-guard implementation and tests.

### AI assistance

AI was used to draft the initial repository structure, API scaffolding, matching-engine code, tests, and documentation.

### Human verification still required

- Run the application and tests locally.
- Replace the deterministic embedding fallback with a genuine embedding model/provider.
- Implement the vision provider and schema validation against actual model output.
- Implement background jobs, retries, cost tracking, PostgreSQL persistence, evaluation data, and measured precision.

### Important limitation

The current scaffold is intentionally not marked as a complete capstone. `EVIDENCE.md` distinguishes implemented, partial, and TODO requirements so that the repository does not claim work that has not been verified.
