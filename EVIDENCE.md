# Evidence

Only verified work is recorded here. Each capstone requirement will receive a concrete proof as it is implemented.

## Current evidence

| Requirement | Status | Proof |
|---|---|---|
| Public dedicated GitHub repository | DONE | Repository is public and dedicated to this capstone. |
| Runnable backend | DONE | `uvicorn app.main:app --host 0.0.0.0 --port 8000` is the documented run command. |
| Structured image metadata schema | DONE | `POST /images/analyze` validates subject, category, attributes, caption, and confidence with Pydantic. |
| Mismatch guard | PARTIAL | Automated test covers rejection of a wolf candidate for a fox post. A full evaluation proof will be added after the real embedding/provider layer is complete. |
| Batch processing + retries | TODO | Not yet implemented. |
| Cost tracking | TODO | Not yet implemented. |
| Persistent database models/indexes | TODO | PostgreSQL layer not yet implemented. |
| Review workflow | PARTIAL | Approve/reject/why endpoints exist; persistence and full audit trail are still TODO. |
| Labeled evaluation set | TODO | Not yet implemented. |
| Top-1 precision | TODO | Will be measured after the evaluation set is complete. |

## Test command

```bash
pytest -q
```
