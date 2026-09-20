"""Tests for loomhash.auth: key generation, hashing, verification, and storage."""

import unittest

from loomhash.auth import (
    APIKey,
    InMemoryAPIKeyStore,
    generate_api_key,
    parse_key_id,
    verify_api_key,
)


class TestKeyGeneration(unittest.TestCase):
    def test_raw_key_starts_with_prefix(self):
        raw, _ = generate_api_key()
        self.assertTrue(raw.startswith("lh_"))

    def test_raw_key_has_parseable_key_id(self):
        raw, record = generate_api_key()
        parsed = parse_key_id(raw)
        self.assertIsNotNone(parsed)
        self.assertEqual(parsed, record.key_id)

    def test_generated_key_is_active(self):
        _, record = generate_api_key()
        self.assertTrue(record.is_active)

    def test_two_generated_keys_have_different_ids(self):
        _, r1 = generate_api_key()
        _, r2 = generate_api_key()
        self.assertNotEqual(r1.key_id, r2.key_id)

    def test_key_hash_is_32_bytes(self):
        _, record = generate_api_key()
        self.assertEqual(len(record.key_hash), 32)  # SHA-256

    def test_salt_is_16_bytes(self):
        _, record = generate_api_key()
        self.assertEqual(len(record.salt), 16)


class TestParseKeyId(unittest.TestCase):
    def test_valid_key(self):
        self.assertEqual(parse_key_id("lh_abcdefgh_secretstuff"), "abcdefgh")

    def test_wrong_prefix(self):
        self.assertIsNone(parse_key_id("xx_abcdefgh_secretstuff"))

    def test_missing_secret(self):
        self.assertIsNone(parse_key_id("lh_abcdefgh"))

    def test_wrong_key_id_length(self):
        self.assertIsNone(parse_key_id("lh_short_secretstuff"))

    def test_empty_string(self):
        self.assertIsNone(parse_key_id(""))


class TestVerification(unittest.TestCase):
    def test_correct_key_verifies(self):
        raw, record = generate_api_key()
        self.assertTrue(verify_api_key(raw, record))

    def test_wrong_key_does_not_verify(self):
        _, record = generate_api_key()
        self.assertFalse(verify_api_key("lh_XXXXXXXX_wrong_secret", record))

    def test_inactive_key_does_not_verify(self):
        raw, record = generate_api_key()
        inactive = APIKey(
            key_id=record.key_id,
            key_hash=record.key_hash,
            salt=record.salt,
            created_at=record.created_at,
            is_active=False,
        )
        self.assertFalse(verify_api_key(raw, inactive))


class TestInMemoryAPIKeyStore(unittest.TestCase):
    def test_store_and_retrieve(self):
        store = InMemoryAPIKeyStore()
        _, record = generate_api_key()
        store.store(record)
        retrieved = store.get_by_id(record.key_id)
        self.assertIsNotNone(retrieved)
        self.assertEqual(retrieved.key_id, record.key_id)
        self.assertEqual(retrieved.key_hash, record.key_hash)

    def test_get_unknown_returns_none(self):
        store = InMemoryAPIKeyStore()
        self.assertIsNone(store.get_by_id("nonexistent"))

    def test_deactivate(self):
        store = InMemoryAPIKeyStore()
        raw, record = generate_api_key()
        store.store(record)
        self.assertTrue(store.deactivate(record.key_id))
        retrieved = store.get_by_id(record.key_id)
        self.assertFalse(retrieved.is_active)
        # Raw key should no longer verify
        self.assertFalse(verify_api_key(raw, retrieved))

    def test_deactivate_unknown_returns_false(self):
        store = InMemoryAPIKeyStore()
        self.assertFalse(store.deactivate("nonexistent"))


if __name__ == "__main__":
    unittest.main()
