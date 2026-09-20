"""API key authentication, hashing, and verification.

Implements D-05 hardening: caller authentication via API keys. Keys are
prefixed with ``lh_`` followed by a ``key_id`` (8 chars) and a secret portion,
making the key_id extractable for store lookup without requiring a full-table
scan.

Security properties:
  - Keys are stored as SHA-256(salt ‖ raw_key), never in plaintext.
  - Verification uses ``hmac.compare_digest`` for constant-time comparison.
  - Salts are per-key, 16-byte, cryptographically random.
"""

from __future__ import annotations

import hashlib
import hmac
import secrets
from dataclasses import dataclass
from datetime import datetime, timezone


@dataclass(frozen=True)
class APIKey:
    """Stored representation of an API key (never contains the raw secret)."""

    key_id: str  # 8-char identifier, extractable from the raw key prefix
    key_hash: bytes  # SHA-256(salt ‖ raw_key)
    salt: bytes  # 16-byte per-key salt
    created_at: datetime
    is_active: bool = True


# ---------------------------------------------------------------------------
# Key format: lh_<key_id (8 chars)>_<secret (43 chars base64)>
# ---------------------------------------------------------------------------

_PREFIX = "lh_"
_KEY_ID_LEN = 8
_SECRET_BYTES = 32  # 32 bytes → 43 chars urlsafe-b64


def generate_api_key() -> tuple[str, APIKey]:
    """Generate a new API key.

    Returns:
        (raw_key, api_key_record) — the raw_key is shown once to the caller;
        the APIKey record (with hashed secret) is stored.
    """
    # token_hex produces [0-9a-f] only — no underscores, so the key_id
    # portion can be unambiguously separated by the first underscore after
    # the prefix in parse_key_id().
    key_id = secrets.token_hex(_KEY_ID_LEN // 2)[:_KEY_ID_LEN]
    secret = secrets.token_urlsafe(_SECRET_BYTES)
    raw_key = f"{_PREFIX}{key_id}_{secret}"

    salt = secrets.token_bytes(16)
    key_hash = _hash_key(raw_key, salt)

    record = APIKey(
        key_id=key_id,
        key_hash=key_hash,
        salt=salt,
        created_at=datetime.now(timezone.utc),
    )
    return raw_key, record


def parse_key_id(raw_key: str) -> str | None:
    """Extract the key_id from a raw API key string, or None if malformed."""
    if not raw_key.startswith(_PREFIX):
        return None
    rest = raw_key[len(_PREFIX) :]
    parts = rest.split("_", 1)
    if len(parts) != 2 or len(parts[0]) != _KEY_ID_LEN:
        return None
    return parts[0]


def verify_api_key(raw_key: str, stored: APIKey) -> bool:
    """Constant-time verification of a raw key against a stored APIKey record."""
    if not stored.is_active:
        return False
    candidate_hash = _hash_key(raw_key, stored.salt)
    return hmac.compare_digest(candidate_hash, stored.key_hash)


# ---------------------------------------------------------------------------
# Internal
# ---------------------------------------------------------------------------


def _hash_key(raw_key: str, salt: bytes) -> bytes:
    """SHA-256(salt ‖ raw_key) — the stored hash representation."""
    return hashlib.sha256(salt + raw_key.encode("utf-8")).digest()
