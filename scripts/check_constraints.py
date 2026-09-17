#!/usr/bin/env python3
"""Heuristic static scan for LoomHash's immutable constraints (see system.md section 2
and docs/hallucination-checks.md). Grep-based, not a type-aware analyzer: a clean run
is necessary but not sufficient, and a flagged line is a prompt for human review, not
an automatic failure. Exits non-zero only on hard violations (forbidden imports and
server-side media-processing imports); everything else is printed as a warning.
"""

import re
import sys
from pathlib import Path

EXCLUDED_DIRS = {
    ".git", ".kilo", "node_modules", "venv", ".venv", "env",
    "__pycache__", ".mypy_cache", ".pytest_cache", "dist", "build",
}

SERVER_PATH_HINTS = ("server", "api", "backend", "gateway")

FORBIDDEN_IMPORT_RE = re.compile(
    r"^\s*(?:import|from)\s+(faiss|pinecone|pymilvus|milvus)\b", re.IGNORECASE
)
MEDIA_IMPORT_RE = re.compile(
    r"^\s*(?:import|from)\s+(mediapipe|cv2)\b", re.IGNORECASE
)
IMAGE_LIKE_NAME_RE = re.compile(r"(image|frame|img|photo|mesh|landmark)", re.IGNORECASE)
CV2_IMWRITE_RE = re.compile(r"\bcv2\.imwrite\s*\(")
DOT_SAVE_RE = re.compile(r"\.save\s*\(")
OPEN_WB_RE = re.compile(r"open\s*\([^)]*['\"]wb['\"]")
POPCOUNT_FALLBACK_RE = re.compile(r"bin\s*\([^)]*\)\.count\s*\(\s*['\"]1['\"]\s*\)")


def iter_python_files(root: Path):
    for path in root.rglob("*.py"):
        if any(part in EXCLUDED_DIRS for part in path.parts):
            continue
        yield path


def is_server_path(path: Path) -> bool:
    lowered = [p.lower() for p in path.parts]
    return any(hint in part for part in lowered for hint in SERVER_PATH_HINTS)


def scan_file(path: Path, hard: list, soft: list) -> None:
    try:
        lines = path.read_text(encoding="utf-8", errors="ignore").splitlines()
    except OSError as exc:
        soft.append(f"{path}: could not read file ({exc})")
        return

    server_path = is_server_path(path)

    for lineno, line in enumerate(lines, start=1):
        m = FORBIDDEN_IMPORT_RE.match(line)
        if m:
            hard.append(
                f"{path}:{lineno}: forbidden import '{m.group(1)}' "
                "(constraint 1: no vector DBs for identity matching)"
            )

        m = MEDIA_IMPORT_RE.match(line)
        if m and server_path:
            hard.append(
                f"{path}:{lineno}: '{m.group(1)}' imported under a server-like path "
                "(constraint 4: media processing confined to the client)"
            )

        if CV2_IMWRITE_RE.search(line):
            soft.append(f"{path}:{lineno}: cv2.imwrite(...) — verify this isn't writing raw image data to disk (constraint 3)")

        if DOT_SAVE_RE.search(line) and IMAGE_LIKE_NAME_RE.search(line):
            soft.append(f"{path}:{lineno}: '.save(' near an image/frame-like name — verify no raw image is persisted (constraint 3)")

        if OPEN_WB_RE.search(line) and IMAGE_LIKE_NAME_RE.search(line):
            soft.append(f"{path}:{lineno}: binary file write near an image/frame-like name — verify no raw image is persisted (constraint 3)")

        if POPCOUNT_FALLBACK_RE.search(line):
            soft.append(f"{path}:{lineno}: bin(x).count('1') popcount pattern — constraint 2 mandates int.bit_count() instead")


def main() -> int:
    root = Path(sys.argv[1]) if len(sys.argv) > 1 else Path(".")
    hard: list = []
    soft: list = []
    scanned = 0

    for path in iter_python_files(root):
        scanned += 1
        scan_file(path, hard, soft)

    print(f"Scanned {scanned} Python file(s) under {root.resolve()}\n")

    if soft:
        print("Warnings (manual review recommended):")
        for line in soft:
            print(f"  - {line}")
        print()

    if hard:
        print("Hard violations (must fix):")
        for line in hard:
            print(f"  - {line}")
        print()
        return 1

    if scanned == 0:
        print("No Python files found to scan yet.")
    else:
        print("No hard constraint violations found.")

    if sys.version_info < (3, 10):
        print(
            f"Warning: running interpreter is Python {sys.version_info.major}.{sys.version_info.minor}, "
            "but system.md mandates Python >= 3.10 (constraint 2)."
        )

    return 0


if __name__ == "__main__":
    raise SystemExit(main())
