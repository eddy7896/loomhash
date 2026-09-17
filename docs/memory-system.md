# System memory model

system.md section 5 requires agents to manage context via explicit file reads/writes rather than relying on LLM thread history. This document names the files that make up that memory, what each one is for, and the read/write protocol every agent (regardless of which model runs it) must follow.

## The memory tiers

| File | Role | Mutability |
| --- | --- | --- |
| [CLAUDE.md](../CLAUDE.md) | Auto-loaded by Claude Code at session start. A distilled pointer into the other tiers plus the immutable constraints, so this protocol is actually followed without relying on the agent to remember to open these files. | Update when the reading order, constraints, or guardrail wiring change; keep it a pointer, not a duplicate source of truth. |
| [system.md](../system.md) | Source of truth for mission, constraints, architecture, and feature specs. | Changed only when the user explicitly approves an architectural change; the approving agent then rewrites it. Never edited speculatively. |
| [STATUS.md](../STATUS.md) | Append-only narrative log of what was actually built or analyzed, with timestamps. Short-term handoff memory between sessions/agents. | Append new timestamped entries only. Do not rewrite or delete prior entries. |
| [docs/open-decisions.md](open-decisions.md) | Log of unresolved ambiguities/conflicts (D-01, D-02, ...) and, once answered, their resolutions. Medium-term "what's still uncertain" memory. | Edited in place: a resolved item moves to a "Resolved decisions" section with the decision, date, and rationale — it is not deleted, so the reasoning stays auditable. |
| [docs/verification-checklist.md](verification-checklist.md) | Per-requirement Pending/Verified/Blocked status with evidence links. Long-term "is this actually proven to work" memory. | A row moves from Pending only when real evidence (test output, reviewed run, commit reference) exists — never on the assumption that code exists therefore it works. |
| [docs/requirements.md](requirements.md), [docs/architecture.md](architecture.md), [docs/use-cases.md](use-cases.md), [docs/agents/*.md](agents/) | Derived analysis documents. Reference/working memory that explains and decomposes system.md — not independent authority. | Updated whenever system.md changes, or when analysis itself was wrong and needs correcting (state that it's a correction). |

## Session start protocol (every agent, every session)

Read in this order before touching any code or making any claim about project state:

1. `system.md` — the immutable spec.
2. `STATUS.md` — what has actually been done so far, most recent entries first.
3. `docs/open-decisions.md` — what is still unresolved; do not re-litigate items already resolved there, and do not silently assume an answer to items still open.
4. The specific `docs/agents/<module>.md` file(s) relevant to the task at hand.

Do not rely on the current chat/thread history as the record of prior sessions' work — a different agent or model may have done that work, and it will not be in this thread.

## Session end protocol (every agent, every session)

1. Append a timestamped entry to `STATUS.md` describing what changed, matching the existing entry format.
2. If a decision in `open-decisions.md` was resolved during the session, move it to that file's "Resolved decisions" section with the resolution and date.
3. If a requirement's implementation was actually verified (not just written), update its row in `docs/verification-checklist.md` with the evidence.
4. If the user approved an architectural change, rewrite the affected part of `system.md` — do not leave the source of truth describing a superseded design.

## Why this exists

Different sessions may be run by different models (Claude, Gemini, GPT, Cursor's model) with no shared context window. Without an explicit, versioned file-based memory, each new session would have to re-derive project state from scratch, risking contradictory assumptions, duplicated work, or silently re-opening a decision that was already made. Treating these files as the memory — and reading/writing them every session — is what keeps multi-agent, multi-session work coherent.
