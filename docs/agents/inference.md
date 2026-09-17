# Agent context: Inference module

Read this before touching any ONNX Runtime code. Also read [../memory-system.md](../memory-system.md)'s session-start protocol first.

## Role

CPU-only ONNX Runtime execution of an INT8-quantized regressor (MobileNetV4 or ConvNeXt family, per system.md). **This module's actual purpose in the pipeline is currently undefined.**

## Do not implement this module yet

Per [../open-decisions.md](../open-decisions.md) D-04: system.md names a model family and runtime but does not say what the model predicts, what its inputs/outputs are, where the trained artifact comes from, or where in the enrollment/authentication flow it's called. Neither [../architecture.md](../architecture.md)'s specified pipeline diagram nor [../use-cases.md](../use-cases.md) place this module anywhere. Do not:

- Guess a plausible task for the model (e.g., "it must be a liveness classifier" or "it must refine the landmark vector") and implement against that guess.
- Add a server-side image-consuming model to "make ONNX useful" — that would directly violate constraint 4 (media processing confined to the client) if it means the server touches images.

## If asked to work on this module

Ask the user to specify: the model's task, its exact input/output tensor shapes and whether they're vector-compatible with the 128-d feature or the 256-bit hash, the source/provenance of the trained weights, and which pipeline step (enrollment, authentication, or neither yet) calls it. Treat this as a blocking clarification, not something to scaffold speculatively.

## Immutable constraints that would apply once scoped

- **Constraint 2:** Python >= 3.10 runtime environment.
- **Constraint 3:** if the model's input is ever an image rather than a vector, it cannot run server-side without first re-opening constraint 4 with the user — that would be an architecture change to system.md, not a routine implementation detail.

## Related requirements / decisions

No requirement ID currently references this module. Open decision: D-04 (blocking any implementation here).
