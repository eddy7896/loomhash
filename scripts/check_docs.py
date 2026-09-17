#!/usr/bin/env python3
"""Repo-health / doctor check for LoomHash's documentation memory system
(see docs/memory-system.md). Verifies the memory files exist and stay
internally consistent with each other, so drift between them is caught
before it misleads a future agent. Exits non-zero on any inconsistency.
"""

import re
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
REQUIRED_FILES = [
    "system.md",
    "STATUS.md",
    "docs/README.md",
    "docs/requirements.md",
    "docs/architecture.md",
    "docs/open-decisions.md",
    "docs/verification-checklist.md",
    "docs/memory-system.md",
    "docs/hallucination-checks.md",
]
EXPECTED_AGENT_FILES = [
    "edge-extraction.md",
    "cryptography.md",
    "inference.md",
    "storage.md",
    "compliance.md",
    "api-gateway.md",
]

REQUIREMENT_ID_RE = re.compile(r"\b([A-Z]{3}-\d{2})\b")
DECISION_ID_RE = re.compile(r"\bD-(\d+)\b")


def read(path: Path) -> str:
    return path.read_text(encoding="utf-8", errors="ignore")


def main() -> int:
    errors: list = []
    warnings: list = []

    for rel in REQUIRED_FILES:
        if not (ROOT / rel).exists():
            errors.append(f"missing required file: {rel}")

    if errors:
        _report(errors, warnings)
        return 1

    status_text = read(ROOT / "STATUS.md")
    if not re.search(r"##\s+\d{4}-\d{2}-\d{2}", status_text):
        warnings.append("STATUS.md has no dated '## YYYY-MM-DD ...' entry heading")

    open_decisions_path = ROOT / "docs" / "open-decisions.md"
    open_decisions_text = read(open_decisions_path)
    defined_decision_ids = set(DECISION_ID_RE.findall(open_decisions_text))

    referenced_decision_ids: set = set()
    for md in (ROOT / "docs").rglob("*.md"):
        if md == open_decisions_path:
            continue
        for did in DECISION_ID_RE.findall(read(md)):
            referenced_decision_ids.add(did)

    for did in sorted(referenced_decision_ids - defined_decision_ids, key=int):
        errors.append(
            f"D-{did} is referenced under docs/ but not defined in docs/open-decisions.md"
        )

    requirements_text = read(ROOT / "docs" / "requirements.md")
    verification_text = read(ROOT / "docs" / "verification-checklist.md")
    requirement_ids = set(REQUIREMENT_ID_RE.findall(requirements_text))
    verification_ids = set(REQUIREMENT_ID_RE.findall(verification_text))

    for rid in sorted(requirement_ids - verification_ids):
        errors.append(
            f"requirement {rid} is defined in docs/requirements.md but missing from docs/verification-checklist.md"
        )

    for line in verification_text.splitlines():
        if "|" not in line or "Verified" not in line:
            continue
        cells = [c.strip() for c in line.strip().strip("|").split("|")]
        if len(cells) < 3:
            continue
        status_cell = cells[2] if len(cells) > 2 else ""
        evidence_cell = cells[-1]
        if status_cell == "Verified" and evidence_cell in ("", "-", "—"):
            errors.append(
                f"docs/verification-checklist.md row marked Verified with no evidence: {line.strip()}"
            )

    agents_dir = ROOT / "docs" / "agents"
    if not agents_dir.exists():
        errors.append("docs/agents/ directory is missing")
    else:
        for fname in EXPECTED_AGENT_FILES:
            if not (agents_dir / fname).exists():
                errors.append(f"expected agent context file missing: docs/agents/{fname}")

    return _report(errors, warnings)


def _report(errors: list, warnings: list) -> int:
    if warnings:
        print("Warnings:")
        for w in warnings:
            print(f"  - {w}")
        print()

    if errors:
        print("Doc-consistency errors:")
        for e in errors:
            print(f"  - {e}")
        print()
        return 1

    print("Documentation memory files present and internally consistent.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
