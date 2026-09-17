# Agent context: API Gateway module

Read this before touching FastAPI routes or request/response handling. Also read [../memory-system.md](../memory-system.md)'s session-start protocol first.

## Role

FastAPI + Uvicorn (behind Caddy) service that receives numerical biometric input from clients and coordinates the enrollment/authentication flows across the Cryptography and Storage modules. Owns request validation and HTTP-level response semantics; does not own the LSH/matching math or persistence details itself.

## I/O contract

- **Accepts:** numerical vectors (128-d feature vector) plus whatever identity/session metadata gets approved. Never accepts images, frames, or mesh data — see constraint 4.
- **Returns:** per AUT-04, 200 for a successful authentication match, 401 for a mismatch. Other failure modes (validation errors, unknown user, rate limits) are unspecified — do not invent status codes/response bodies for them without flagging it as a proposal.

## Immutable constraints that apply here

- **Constraint 3 (Data Privacy):** no endpoint may accept, cache, or log raw image data. Reject any request-body design that includes an image/frame field.
- **Constraint 4 (Compute Location):** this module must never import mediapipe or perform frame/mesh processing server-side. If a "convenience" feature seems to require that, it's a scope change requiring explicit approval, not a routine implementation choice.

## What is NOT yet defined — do not invent it

Per [../open-decisions.md](../open-decisions.md) D-05 and D-10: exact route paths, request/response schemas, how a caller's identity/session is authenticated and bound to a user_id, and error-response contracts beyond the specified 200/401. Do not scaffold a REST API surface and present it as final — propose routes explicitly and get them approved, since system.md's "Ask, Do Not Assume" rule specifically calls out not inferring API routes.

## Related requirements / decisions

Requirements: ENR-03, ENR-05, AUT-01..AUT-04, REV-01 (as the entry point coordinating storage/compliance). Open decisions: D-05, D-06, D-10.
