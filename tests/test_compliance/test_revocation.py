"""Tests for the Compliance module's revocation handling (REV-01)."""

import unittest
from unittest.mock import patch

from loomhash.auth import generate_api_key
from loomhash.compliance import RevocationDenied, revoke
from loomhash.storage import EnrollmentRecord, InMemoryStorageBackend, StorageBackend


class AlwaysFailsToDeleteBackend(StorageBackend):
    """Simulates a storage backend that can never confirm deletion in every
    store -- exercises the partial-failure path that InMemoryStorageBackend
    can't (it never fails). See docs/verification-checklist.md's REV-01 note.
    """

    def enroll(self, record: EnrollmentRecord) -> None:
        pass

    def get(self, user_id: str):
        return None

    def delete(self, user_id: str) -> bool:
        return False

    def list_users(self) -> list[str]:
        return []


def _active_key():
    """Generate a valid, active APIKey record for testing."""
    _, record = generate_api_key()
    return record


class TestRevoke(unittest.TestCase):
    def test_revoke_deletes_when_authorized(self):
        storage = InMemoryStorageBackend()
        storage.enroll(EnrollmentRecord("alice", b"s" * 32, b"h" * 32, 1))
        self.assertTrue(revoke(storage, _active_key(), "alice"))
        self.assertIsNone(storage.get("alice"))

    def test_revoke_is_idempotent_for_unknown_user(self):
        storage = InMemoryStorageBackend()
        self.assertTrue(revoke(storage, _active_key(), "nobody"))

    def test_revoke_raises_when_not_authorized(self):
        storage = InMemoryStorageBackend()
        with patch("loomhash.compliance.revocation.is_authorized", return_value=False):
            with self.assertRaises(RevocationDenied):
                revoke(storage, _active_key(), "alice")

    def test_revoke_returns_false_on_storage_partial_failure(self):
        storage = AlwaysFailsToDeleteBackend()
        self.assertFalse(revoke(storage, _active_key(), "alice"))


if __name__ == "__main__":
    unittest.main()
