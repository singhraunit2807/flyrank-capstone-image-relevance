# Build Log

This file records AI-assisted development honestly.

## Session 1 — Repository foundation

- Created the dedicated public repository and baseline documentation.
- Added a FastAPI application scaffold, deterministic local matching, demo seed data, and initial tests.
- Added setup instructions, environment example, and repository hygiene files.

## Session 2 — Functional offline demo

- Reworked the feature-hashing matcher to be deterministic across Python processes.
- Added plural normalization and explicit subject mismatch rejection.
- Expanded the demo catalogue with multiple animal categories.
- Added automatic demo seeding on application startup and a POST /demo/seed reset endpoint.
- Improved match responses to include ranked results, score, decision, reason, and review status.
- Added review status tracking for approve/reject actions.
- Expanded API regression tests for metadata validation, matching, mismatch rejection, review status, and invalid post IDs.
- Added a GitHub Actions workflow to run the test suite.
- Updated the README and evidence matrix to distinguish implemented demo behavior from future AI-provider and production features.

## AI assistance

AI was used to draft and revise code, tests, and documentation. The repository owner should review the changes and run the test suite.

## Verification status

The code and test workflow have been committed, but a successful local or GitHub Actions test run has not been confirmed in this session. Do not describe the tests as passing until a run succeeds.

## Remaining work for a production-grade AI system

- Add raw image ingestion and connect a genuine vision model.
- Replace the lexical baseline with a trained semantic embedding provider and evaluate it on labeled data.
- Add durable database storage, audit history, batch processing, retry handling, and cost tracking.
- Measure and publish top-1 precision and other relevant metrics.

## Important limitation

This repository is intended to be a working educational backend demo. It is not yet a production-ready computer-vision system, and documentation should not claim otherwise.
