# Open decisions and validation plan

Analysis date: 2026-09-17. These findings do not change system.md. Proposals require confirmation before affected implementation begins.

## Resolved decisions

| Date | Decision | Resolution |
| --- | --- | --- |
| 2026-09-17 | Initial milestone target (referenced below as "the first useful clarification") | **Feasibility prototype**: correctness of the geometric enrollment/authentication/revocation pipeline. Adversarial hardening (replay resistance, liveness, deepfake defense, formal zero-knowledge proof) is deferred, not implemented, for this milestone. See [use-cases.md](use-cases.md) for the resulting scoped flows and [agents/](agents/) for per-module guidance. |
| 2026-09-17 | D-03: seeded LSH definition | **Random-hyperplane (SimHash-style) projection, version 1**: a 256x128 matrix of iid N(0,1) samples, deterministically generated from the 32-byte seed via `numpy.random.default_rng(int.from_bytes(seed, "big"))`; bit i = 1 if the i-th projected component >= 0 else 0; bits packed MSB-first into a 256-bit integer; float64 throughout. Implemented in [loomhash/cryptography/lsh.py](../loomhash/cryptography/lsh.py) as `LSH_VERSION = 1`. Changing any of these parameters requires bumping `LSH_VERSION` and recording the change here, since it invalidates every previously stored hash. Verified deterministic/boundary behavior against synthetic (non-biometric) vectors in [tests/test_cryptography/](../tests/test_cryptography/); see [verification-checklist.md](verification-checklist.md) for ENR-04/AUT-03/AUT-04. |

This resolution reclassifies the items below: D-01, D-02, D-03, D-06, and D-10 remain **blocking** — the prototype cannot be built without them. D-04 (ONNX purpose), D-07 (deepfake/liveness threat model), D-08 (formal zero-knowledge definition), and D-09 (legal anonymization evidence) are **deferred** — a technical seed-deletion mechanism is still built for D-09's underlying REV-01 requirement, but no anonymization/compliance claim is asserted until that item is separately resolved. D-05 (identity/API/storage contracts) is blocking in a minimal form — the prototype needs some caller-supplied user_id and basic request contract, but full authorization hardening is deferred.

## Decisions that block implementation

| ID | Gap or conflict | Decision needed |
| --- | --- | --- |
| D-01 | The exact 128 distances are absent. | Supply/approve landmark index pairs, coordinate units, alignment, scale normalization, precision, and feature version. |
| D-02 | Enrollment averages landmarks across changing poses. | Define pose registration, yaw coverage, rejected-frame handling, and how enrollment remains comparable to a single-frame query. |
| D-03 | ~~Seeded LSH is named but not defined.~~ **Resolved 2026-09-17** — see "Resolved decisions" above. | ~~Approve projection distribution and dimensions, seed-to-generator mapping, sign/tie rule, numeric precision, bit order, and compatibility/version policy.~~ |
| D-04 | ONNX is required but absent from both pipelines. | Define the model's purpose, vector-compatible input/output, artifact and training source, or explicitly approve deferral. |
| D-05 | User lookup requires identity context, while the API is described as accepting only vectors. | Define identity transport, caller authentication, account binding, and whether the restriction applies only to biometric content. |
| D-06 | Literal memory constraints exclude required seeds and computation state. | Clarify which data classes are prohibited and which necessary non-image state is allowed. |
| D-07 | Deepfake resistance lacks a threat model or enforcement mechanism. | Define relevant attacks and how capture freshness and authenticity will be established with a vector-only server. |
| D-08 | The zero-knowledge label has no protocol definition. | Decide whether it means keeping images local or requires a formal cryptographic property; define the latter if intended. |
| D-09 | Seed removal is described as guaranteed anonymization. | Define deletion scope, remaining identity links, backups, replicas, in-flight requests, and evidence for any anonymity claim. |
| D-10 | Persistence and API behavior are only logical descriptions. | Approve routes, schemas, enrollment replacement policy, error behavior, cache policy, and revocation event contract. |

The first useful clarification is the intended initial milestone: a feasibility prototype for geometric matching or an authentication service expected to resist malicious clients. Both can honor local image processing, but their validation and protocol needs differ substantially.

## Findings and supporting sources

### Facial landmarks are an input, not proof of identity or liveness

MediaPipe documents outputs consisting of 3D landmarks, expression coefficients, and optional transformation matrices. That does not supply LoomHash's 128-feature definition or validate biometric authentication. Treating those outputs as sufficiently stable cranial measurements is a project hypothesis requiring evaluation. See the [official Face Landmarker web guide](https://developers.google.com/edge/mediapipe/solutions/vision/face_landmarker/web_js).

The replay weakness described in [architecture.md](architecture.md) follows from the specified deterministic matching flow. Client-side yaw movement during enrollment alone does not establish the authenticity of subsequent server requests.

### Model integration requires an actual model contract

ONNX Runtime supports 8-bit quantization for CPU inference, but its documentation calls for accuracy evaluation when quantizing. The runtime and a model-family name do not define LoomHash's regression task. See [ONNX Runtime quantization documentation](https://onnxruntime.ai/docs/performance/model-optimizations/quantization.html). An image-consuming server model would conflict with the current vector-only requirement; input compatibility must be verified from the selected artifact.

### Seed deletion is not yet an anonymization proof

Removing a seed may prevent the prescribed future projection, provided every usable copy is removed. It does not remove a retained user_id-to-hash association, an immutable reference, or a backup by itself. This is an architectural finding, not a determination of legal compliance. A remaining identity association directly undermines the specification's unconditional claim of untraceability.

The EDPB's [January 2025 pseudonymisation guidelines](https://www.edpb.europa.eu/system/files/2025-01/edpb_guidelines_202501_pseudonymisation_en.pdf) are explicitly a public-consultation version; they are contextual guidance, not treated here as a final legal ruling or current compliance certification.

### The DPDP reference needs correction before compliance planning

The source calls the law the “DPDP Act 2026.” Official material identifies the Digital Personal Data Protection Act, 2023, and MeitY publishes Digital Personal Data Protection Rules, 2025. See the [government consultation background identifying the Act](https://innovateindia.mygov.in/dpdp-rules-2025/) and [MeitY's Rules 2025 listing](https://www.meity.gov.in/documents/act-and-policies/digital-personal-dataprotection-rules-2025gDOxUjMtQWa?pageTitle=Digital-Personal-Data-ProtectionRules-2025). Applicability and commencement obligations have not been assessed here. The original wording remains unchanged pending approval.

## Proposed validation sequence

1. Resolve the feature and projection contracts (D-01 through D-03), then use non-biometric synthetic vectors to verify deterministic projection, encoding, and Hamming boundaries. Synthetic checks establish algorithm behavior only.
2. Define a consented biometric evaluation protocol: genuine/impostor comparisons, repeated sessions, supported devices, pose and lighting variation, failure-to-capture rate, false accepts, and false rejects. Select numerical acceptance targets before judging results.
3. Define and test replay, injected-vector, virtual-camera, photo/video, and generated-media threats relevant to D-07. Do not equate a successful landmark detection with a passed liveness test.
4. Resolve identity/API/storage contracts before building adapters or routes. Validate malformed inputs, authorization boundaries, duplicate enrollment, cache failure, and partial writes against approved behavior.
5. Validate revocation across both stores, retries, concurrent authentication, process memory, replicas, and backup restoration against an agreed completion condition.
6. Integrate ONNX only after D-04 is resolved; compare model accuracy and CPU performance before/after INT8 quantization if it remains in scope.
7. Assess operational targets and compliance evidence before making enterprise-readiness claims.

No additional dependency, API route, database field, liveness mechanism, or deployment choice is approved by this proposed sequence.
