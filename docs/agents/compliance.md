# Agent context: Compliance module

Read this before touching consent-revocation/crypto-shredding code. Also read [../memory-system.md](../memory-system.md)'s session-start protocol first.

## Role

Event listener for consent revocation. On a revocation event, deletes the affected user's cryptographic seed from PostgreSQL and Redis (delegating the actual delete to the Storage module's adapters — this module owns the *event handling and authorization*, not a second copy of the delete logic).

## I/O contract

- **In:** a revocation event for a user_id.
- **Out:** seed deleted from both stores; subsequent authentication for that user_id can no longer succeed (see REV-01).

## What is NOT yet defined — do not invent it

Per [../open-decisions.md](../open-decisions.md) D-05/D-10, the following are unresolved: who/what is authorized to trigger a revocation event and how that's verified, the event's transport/contract, behavior when the user_id has no stored seed (idempotent no-op vs. error), and partial-failure handling if deletion succeeds in one store but not the other. Do not assume "any caller can revoke any user" or "partial failure is fine" — both are security/correctness decisions that need explicit approval.

## Legal/compliance claims — do not assert these in code comments or responses

Per [../open-decisions.md](../open-decisions.md) D-09, deleting a seed prevents the *specified future projection*, provided every usable copy (including backups/replicas/in-flight process memory) is actually gone. That is a narrower and more conditional claim than "converts pseudonymous data into fully anonymized data." Do not write code, docstrings, or API responses that assert full legal anonymization or DPDP/GDPR compliance as an established fact — that determination is outside this module's (or any single agent's) authority. Also note: system.md's "DPDP Act 2026" reference does not match the actual named law (Digital Personal Data Protection Act, 2023, with Rules 2025) — don't propagate that name into new documentation without flagging the discrepancy.

## Related requirements / decisions

Requirements: REV-01. Open decisions: D-05, D-09, D-10.
