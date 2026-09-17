# LoomHash — agent instructions

This file is auto-loaded at the start of every Claude Code session in this repo. Read it, then follow it — it is how system.md's "agents must parse this file at the start of every new session" requirement is actually enforced for this tool.

## Read before doing anything else

1. [system.md](system.md) — the immutable source of truth for mission, constraints, architecture, and feature specs. Do not treat chat history as authoritative over this file.
2. [STATUS.md](STATUS.md) — most recent entries first: what has actually been built or analyzed so far.
3. [docs/open-decisions.md](docs/open-decisions.md) — unresolved ambiguities and, in its "Resolved decisions" section, what's already been decided (the project is currently scoped to the **feasibility prototype** milestone; adversarial hardening is deferred).
4. The relevant `docs/agents/<module>.md` file for whatever module you're about to touch (edge-extraction, cryptography, inference, storage, compliance, api-gateway).

Full protocol, including the session-end steps: [docs/memory-system.md](docs/memory-system.md).

## Immutable constraints (system.md section 2) — check every diff against these

1. No `faiss`, `pinecone`, `pymilvus`/milvus, or any vector-DB/ANN library for identity matching. Matching is native `int.bit_count()` XOR only.
2. Target Python >= 3.10. Hamming distance uses `int.bit_count()`, never `bin(x).count('1')`.
3. No raw image/frame/mesh data may ever be written to disk, cache, or logs on the server. Only 128-d vectors and 256-bit hashes exist server-side.
4. Media processing (MediaPipe, camera capture) is client-side only. The server never imports mediapipe or does frame processing.

Full checklist: [docs/hallucination-checks.md](docs/hallucination-checks.md).

## Guardrails already wired up in this repo

- `python scripts/check_constraints.py` — heuristic scan for the four constraints above. Also runs as the pre-commit hook (`hooks/pre-commit`, installed at `.git/hooks/pre-commit`) and in CI (`.github/workflows/guardrails.yml`).
- `python scripts/check_docs.py` — verifies the documentation memory files (system.md, STATUS.md, open-decisions.md, verification-checklist.md, docs/agents/*) exist and stay cross-referenced correctly. Same hook/CI wiring as above.
- Both scripts must pass before a commit succeeds locally, and run again in CI.
- `pyproject.toml` pins `requires-python = ">=3.10"` and declares no dependencies — none have been approved yet.

## Working rules (system.md section 1, "Ask, Do Not Assume")

- Do not add a third-party dependency without explicit user consent in the conversation.
- Do not invent API routes, database schemas, or algorithmic details (LSH projection, landmark pairs, etc.) that aren't already specified in [docs/requirements.md](docs/requirements.md). If it's not specified, ask, or record it as an explicit proposal in [docs/open-decisions.md](docs/open-decisions.md) — never ship a guess as if it were final.
- Stay inside the module boundary you're working in (see [docs/architecture.md](docs/architecture.md)); don't reach into another module's internals.
- End of session: append a timestamped entry to STATUS.md, update [docs/verification-checklist.md](docs/verification-checklist.md) if a requirement was actually verified (not just coded), and update open-decisions.md if something was resolved. Rewrite system.md only when the user has approved an architectural change.
