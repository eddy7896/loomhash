"""StorageBackend contract tests (D-10): upsert-on-re-enroll and delete
semantics. Mix StorageBackendContractTests into a TestCase per concrete
backend that has a live, reachable service to test against -- see
docs/verification-checklist.md. Only InMemoryStorageBackend is exercised
here; PostgresRedisStorageBackend has no live Postgres/Redis available in
this environment (see loomhash/storage/postgres.py and redis_cache.py).
"""

import unittest

from loomhash.storage import EnrollmentRecord, InMemoryStorageBackend


class StorageBackendContractTests:
    def make_backend(self):
        raise NotImplementedError

    def test_get_missing_user_returns_none(self):
        backend = self.make_backend()
        self.assertIsNone(backend.get("nobody"))

    def test_enroll_then_get_round_trips(self):
        backend = self.make_backend()
        record = EnrollmentRecord(user_id="alice", seed=b"s" * 32, loom_hash=b"h" * 32, lsh_version=1)
        backend.enroll(record)
        self.assertEqual(backend.get("alice"), record)

    def test_re_enroll_upserts(self):
        backend = self.make_backend()
        backend.enroll(EnrollmentRecord("alice", b"s" * 32, b"h" * 32, 1))
        new_record = EnrollmentRecord("alice", b"t" * 32, b"i" * 32, 1)
        backend.enroll(new_record)
        self.assertEqual(backend.get("alice"), new_record)

    def test_enroll_does_not_affect_other_users(self):
        backend = self.make_backend()
        backend.enroll(EnrollmentRecord("alice", b"s" * 32, b"h" * 32, 1))
        backend.enroll(EnrollmentRecord("bob", b"t" * 32, b"i" * 32, 1))
        self.assertEqual(backend.get("alice").user_id, "alice")
        self.assertEqual(backend.get("bob").user_id, "bob")

    def test_delete_removes_record(self):
        backend = self.make_backend()
        backend.enroll(EnrollmentRecord("alice", b"s" * 32, b"h" * 32, 1))
        self.assertTrue(backend.delete("alice"))
        self.assertIsNone(backend.get("alice"))

    def test_delete_is_idempotent_for_unknown_user(self):
        backend = self.make_backend()
        self.assertTrue(backend.delete("nobody"))

    def test_delete_then_reenroll_works(self):
        backend = self.make_backend()
        backend.enroll(EnrollmentRecord("alice", b"s" * 32, b"h" * 32, 1))
        backend.delete("alice")
        backend.enroll(EnrollmentRecord("alice", b"t" * 32, b"i" * 32, 1))
        self.assertEqual(backend.get("alice").seed, b"t" * 32)


class TestInMemoryStorageBackend(StorageBackendContractTests, unittest.TestCase):
    def make_backend(self):
        return InMemoryStorageBackend()


if __name__ == "__main__":
    unittest.main()
