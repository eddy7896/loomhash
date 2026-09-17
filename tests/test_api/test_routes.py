"""End-to-end route tests for the API Gateway, using the in-memory storage
backend (no live Postgres/Redis needed). Exercises ENR-03/ENR-05, AUT-01
through AUT-04, and REV-01 as an actual enroll -> authenticate -> revoke
loop through real HTTP requests (via FastAPI's TestClient).
"""

import unittest

from fastapi.testclient import TestClient

from loomhash.api import create_app
from loomhash.storage import InMemoryStorageBackend

VECTOR_A = [1.0] * 128
VECTOR_B = [-1.0] * 128  # negation flips virtually every LSH bit, see test_lsh.py


class TestApiRoutes(unittest.TestCase):
    def setUp(self):
        self.storage = InMemoryStorageBackend()
        self.client = TestClient(create_app(self.storage))

    def test_enroll_returns_200(self):
        resp = self.client.post("/v1/enroll", json={"user_id": "alice", "vector": VECTOR_A})
        self.assertEqual(resp.status_code, 200)
        self.assertEqual(resp.json(), {"user_id": "alice", "status": "enrolled"})

    def test_authenticate_with_same_vector_succeeds(self):
        self.client.post("/v1/enroll", json={"user_id": "alice", "vector": VECTOR_A})
        resp = self.client.post("/v1/authenticate", json={"user_id": "alice", "vector": VECTOR_A})
        self.assertEqual(resp.status_code, 200)
        self.assertEqual(resp.json(), {"status": "authenticated"})

    def test_authenticate_response_never_contains_a_distance_field(self):
        self.client.post("/v1/enroll", json={"user_id": "alice", "vector": VECTOR_A})
        resp = self.client.post("/v1/authenticate", json={"user_id": "alice", "vector": VECTOR_A})
        self.assertNotIn("distance", resp.json())

    def test_authenticate_with_different_vector_fails(self):
        self.client.post("/v1/enroll", json={"user_id": "alice", "vector": VECTOR_A})
        resp = self.client.post("/v1/authenticate", json={"user_id": "alice", "vector": VECTOR_B})
        self.assertEqual(resp.status_code, 401)

    def test_authenticate_unknown_user_returns_401_not_404(self):
        resp = self.client.post("/v1/authenticate", json={"user_id": "nobody", "vector": VECTOR_A})
        self.assertEqual(resp.status_code, 401)

    def test_revoke_then_authenticate_fails(self):
        self.client.post("/v1/enroll", json={"user_id": "alice", "vector": VECTOR_A})
        revoke_resp = self.client.delete("/v1/users/alice")
        self.assertEqual(revoke_resp.status_code, 200)
        self.assertEqual(revoke_resp.json(), {"user_id": "alice", "status": "revoked"})

        auth_resp = self.client.post("/v1/authenticate", json={"user_id": "alice", "vector": VECTOR_A})
        self.assertEqual(auth_resp.status_code, 401)

    def test_revoke_unknown_user_is_idempotent(self):
        resp = self.client.delete("/v1/users/nobody")
        self.assertEqual(resp.status_code, 200)

    def test_enroll_rejects_wrong_length_vector(self):
        resp = self.client.post("/v1/enroll", json={"user_id": "alice", "vector": [1.0] * 127})
        self.assertEqual(resp.status_code, 422)

    def test_enroll_rejects_empty_user_id(self):
        resp = self.client.post("/v1/enroll", json={"user_id": "", "vector": VECTOR_A})
        self.assertEqual(resp.status_code, 422)

    def test_enroll_rejects_unexpected_extra_field(self):
        # Constraint 3: a stray "image" field must be rejected, not silently ignored.
        resp = self.client.post(
            "/v1/enroll", json={"user_id": "alice", "vector": VECTOR_A, "image": "base64..."}
        )
        self.assertEqual(resp.status_code, 422)

    def test_re_enroll_upserts_with_a_fresh_seed(self):
        # Re-enrollment generates a new random seed, so the OLD vector no
        # longer authenticates even though it authenticated before.
        self.client.post("/v1/enroll", json={"user_id": "alice", "vector": VECTOR_A})
        self.client.post("/v1/enroll", json={"user_id": "alice", "vector": VECTOR_B})

        old_auth = self.client.post("/v1/authenticate", json={"user_id": "alice", "vector": VECTOR_A})
        new_auth = self.client.post("/v1/authenticate", json={"user_id": "alice", "vector": VECTOR_B})
        self.assertEqual(old_auth.status_code, 401)
        self.assertEqual(new_auth.status_code, 200)


if __name__ == "__main__":
    unittest.main()
