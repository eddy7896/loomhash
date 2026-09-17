# Hallucination-check protocol

Every agent (Claude, Gemini, OpenAI, Cursor, or otherwise) must run this checklist against its own output **before** presenting code or a plan as finished. This operationalizes system.md section 2 ("Agent Directives and Hallucination Checks"). It is a pre-flight gate, not a substitute for human review.

## The four immutable constraints

| # | Constraint | What to check in your own diff before finishing |
| --- | --- | --- |
| 1 | No vector DBs for identity matching | No import of `faiss`, `pinecone`, `pymilvus`/`milvus`, or any ANN-index library anywhere in matching code. Identity comparison must be native `int.bit_count()` XOR only. |
| 2 | Python >= 3.10, `int.bit_count()` mandatory | Hamming-distance code must call `.bit_count()`, not `bin(x).count('1')`, `popcount` libraries, or NumPy bit-tricks. Confirm no code path assumes Python < 3.10 syntax/stdlib. |
| 3 | No raw image data persisted anywhere on the server | Grep your own diff for `cv2.imwrite`, `.save(` on a PIL/array object, `open(path, 'wb')` near an image/frame variable, or any log statement that could contain a frame, landmark mesh, or raw byte buffer of image data. Only 128-d float vectors and 256-bit hashes may exist in server memory/logs/cache. |
| 4 | Media processing confined to the client | The server API must never import `mediapipe`, `cv2`/OpenCV video capture, or any camera/frame-processing library. If a server-side file imports one of these, that is a constraint violation, not a convenience. |

## Process checks (from "Ask, Do Not Assume")

Before finishing any change, confirm all of the following are true — if any is false, stop and ask the user instead of proceeding:

- [ ] No new third-party dependency was added without explicit user consent in this conversation.
- [ ] No API route, request/response shape, or database column/table was invented. If [requirements.md](requirements.md) or [open-decisions.md](open-decisions.md) doesn't already specify it, it was asked about, not assumed.
- [ ] Every technical detail filled in beyond system.md's literal text (landmark pairs, LSH projection distribution, seed encoding, etc.) was either explicitly approved by the user or is flagged as a proposal in open-decisions.md — not silently implemented as if final.
- [ ] The change stays inside its module boundary (see [architecture.md](architecture.md) and the relevant `agents/<module>.md` file). Cross-module logic (e.g., cryptography code reaching into storage internals) is a decoupling violation.
- [ ] If this change resolves one of the open decisions (D-01..D-10 in open-decisions.md), that file is updated to record the resolution and its date — the decision log is not allowed to go stale.
- [ ] If this change alters approved architecture, system.md itself is rewritten to reflect it (per system.md section 5) — the source of truth is not allowed to drift from what was actually built.
- [ ] STATUS.md gets a timestamped entry describing what was actually done, not what was intended.

## Automated support: `scripts/check_constraints.py`

A best-effort static scanner lives at [../scripts/check_constraints.py](../scripts/check_constraints.py). It greps the repository for:

- Forbidden imports (`faiss`, `pinecone`, `pymilvus`/`milvus`).
- `mediapipe` or OpenCV camera-capture imports outside an `edge`/`client` path.
- Heuristic raw-image-write patterns (`cv2.imwrite`, `.save(` near image-like names, `open(..., 'wb')` near frame/image-like names).
- Use of `bin(x).count('1')`-style popcounts where `.bit_count()` was expected.

It is a heuristic grep, not a type-aware analyzer: it will miss obfuscated violations and can flag unrelated code (e.g., a legitimate non-image binary write). Treat a clean run as necessary, not sufficient, and treat a flagged line as a prompt to look, not an automatic failure. Run it with:

```sh
python scripts/check_constraints.py
```

It exits non-zero only on the hard violations (forbidden imports, server-side media processing imports); heuristic image-write and popcount matches are printed as warnings for manual review.

There is currently no application code in this repository, so running the script today will report nothing to scan. It is included now so it's already in place once implementation starts.

## Enforcement

This checklist isn't only aspirational — it's wired into the repo:

- `scripts/check_docs.py` cross-checks the documentation memory files themselves (requirement IDs, decision IDs, expected agent-context files) for consistency. See [memory-system.md](memory-system.md).
- Both `check_constraints.py` and `check_docs.py` run as a git pre-commit hook (tracked at [../hooks/pre-commit](../hooks/pre-commit), installed at `.git/hooks/pre-commit`) and again in CI ([../.github/workflows/guardrails.yml](../.github/workflows/guardrails.yml)). A commit with a hard violation or a doc-consistency error is blocked locally and flagged in CI.
- The root [../CLAUDE.md](../CLAUDE.md) file is what makes Claude Code actually load this checklist automatically at the start of every session, rather than relying on an agent to remember to open this file.
