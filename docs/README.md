# LoomHash documentation

Initial requirements analysis: 2026-09-17.

LoomHash is intended to be a self-hosted facial authentication microservice. The client extracts facial geometry locally; the server converts numerical features into a user-specific 256-bit template and compares subsequent samples using Hamming distance. Enrollment, authentication, and consent revocation are the three explicitly specified features.

## Reading order

1. [Requirements](requirements.md): explicit scope, constraints, and acceptance evidence.
2. [Architecture](architecture.md): module responsibilities, data flows, and trust boundaries.
3. [Use cases](use-cases.md): actor-level enrollment/authentication/revocation flows and edge cases, scoped to the feasibility-prototype milestone.
4. [Open decisions and validation](open-decisions.md): gaps, conflicting requirements, resolved decisions, and proposed next steps.
5. [Memory system](memory-system.md): what STATUS.md, open-decisions.md, and verification-checklist.md are for, and the session read/write protocol every agent follows.
6. [Hallucination checks](hallucination-checks.md): the pre-flight checklist (plus [scripts/check_constraints.py](../scripts/check_constraints.py)) every agent runs against its own output before calling a change finished.
7. [Verification checklist](verification-checklist.md): per-requirement Pending/Verified/Blocked tracking with evidence links — separate from STATUS.md's freeform log.
8. [agents/](agents/): one context file per module (edge-extraction, cryptography, inference, storage, compliance, api-gateway) — read only the one(s) relevant to the task at hand.

## Authority and current state

- [system.md](../system.md) is the supplied architectural source of truth. It has not been changed by this analysis.
- [STATUS.md](../STATUS.md) records completed work and the next step.
- These documents distinguish **specified requirements**, **analysis**, and **proposals**. Analysis does not approve an architectural change.
- No application code, database schema, API routes, models, or dependency manifests exist yet.
- The documentation set targets the **feasibility prototype** milestone (resolved 2026-09-17, see [open-decisions.md](open-decisions.md)'s "Resolved decisions"); adversarial hardening is deferred, not implemented.
- Zero-knowledge, deepfake resistance, enterprise readiness, and anonymization are product objectives or claims awaiting evidence, not demonstrated properties.

## Working rules

Read system.md and STATUS.md at the start of each session (full protocol in [memory-system.md](memory-system.md)). Clarify ambiguous technical details before implementing the affected component. Obtain explicit consent before adding dependencies. Do not invent API routes or database schemas. Run the [hallucination-check](hallucination-checks.md) protocol before calling any change finished. Record completed components with timestamps in STATUS.md, and update [verification-checklist.md](verification-checklist.md) when a requirement is actually proven, not just coded. Update system.md when the user approves architectural changes.
