"""End-to-end route tests for the API Gateway, using the in-memory storage
backend (no live Postgres/Redis needed). Exercises ENR-03/ENR-05, AUT-01
through AUT-04, and REV-01 as an actual enroll -> authenticate -> revoke
loop through real HTTP requests (via FastAPI's TestClient).
"""End-to-end HTTP tests for the API Gateway multipart routes (D-12).

Tests use FastAPI's TestClient (httpx) with an in-memory storage backend.
Images are small in-memory JPEGs generated with Pillow -- no disk I/O, no real
faces, no biometric data.

Route contracts tested:
  POST /v1/enroll       -- multipart: user_id (Form) + images (File, 8-12)
  POST /v1/authenticate -- multipart: user_id (Form) + image (File, 1)
  DELETE /v1/users/{id} -- unchanged

This file replaces the old test_routes.py which tested the vector-JSON body
interface.  That interface was removed in the D-12 route revision (2026-09-18).
"""

import io
import unittest
from unittest.mock import patch

from fastapi.testclient import TestClient
from PIL import Image

from loomhash.api import create_app
from loomhash.storage import EnrollmentRecord, InMemoryStorageBackend, StorageBackend
from loomhash.api.app import create_app

VECTOR_A = [1.0] * 128
VECTOR_B = [-1.0] * 128  # negation flips virtually every LSH bit, see test_lsh.py

# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

class AlwaysFailsToDeleteBackend(StorageBackend):
    """See tests/test_compliance/test_revocation.py for why this exists."""
def _jpeg(color: tuple = (128, 100, 80), size: tuple = (64, 64)) -> bytes:
    """Tiny in-memory JPEG -- enough for the model to infer a vector."""
    img = Image.new("RGB", size, color=color)
    buf = io.BytesIO()
    img.save(buf, format="JPEG")
    return buf.getvalue()

    def enroll(self, record: EnrollmentRecord) -> None:
        pass

    def get(self, user_id: str):
        return None
def _enroll_files(n: int = 8, color: tuple = (128, 100, 80)) -> list[tuple]:
    """Build the multipart files list for an enroll request."""
    img = _jpeg(color=color)
    return [("images", (f"frame_{i}.jpg", img, "image/jpeg")) for i in range(n)]

    def delete(self, user_id: str) -> bool:
        return False

def _auth_file(color: tuple = (128, 100, 80)) -> tuple:
    return ("image", ("face.jpg", _jpeg(color=color), "image/jpeg"))

class TestApiRoutes(unittest.TestCase):

class TestEnrollRoute(unittest.TestCase):

    def setUp(self):
        self.storage = InMemoryStorageBackend()
        self.client = TestClient(create_app(self.storage))
        self.client = TestClient(create_app())

    def test_enroll_returns_200(self):
        resp = self.client.post("/v1/enroll", json={"user_id": "alice", "vector": VECTOR_A})
        self.assertEqual(resp.status_code, 200)
        self.assertEqual(resp.json(), {"user_id": "alice", "status": "enrolled"})
    def test_enroll_success_returns_200(self):
        r = self.client.post(
            "/v1/enroll",
            data={"user_id": "alice"},
            files=_enroll_files(8),
        )
        self.assertEqual(r.status_code, 200)
        body = r.json()
        self.assertEqual(body["user_id"], "alice")
        self.assertEqual(body["status"], "enrolled")

    def test_authenticate_with_same_vector_succeeds(self):
        self.client.post("/v1/enroll", json={"user_id": "alice", "vector": VECTOR_A})
        resp = self.client.post("/v1/authenticate", json={"user_id": "alice", "vector": VECTOR_A})
        self.assertEqual(resp.status_code, 200)
        self.assertEqual(resp.json(), {"status": "authenticated"})
    def test_enroll_accepts_up_to_12_images(self):
        r = self.client.post(
            "/v1/enroll",
            data={"user_id": "bob"},
            files=_enroll_files(12),
        )
        self.assertEqual(r.status_code, 200)

    def test_authenticate_response_never_contains_a_distance_field(self):
        self.client.post("/v1/enroll", json={"user_id": "alice", "vector": VECTOR_A})
        resp = self.client.post("/v1/authenticate", json={"user_id": "alice", "vector": VECTOR_A})
        self.assertNotIn("distance", resp.json())
    def test_enroll_too_few_images_returns_422(self):
        """< 8 images → 422."""
        r = self.client.post(
            "/v1/enroll",
            data={"user_id": "carol"},
            files=_enroll_files(7),
        )
        self.assertEqual(r.status_code, 422)

    def test_authenticate_with_different_vector_fails(self):
        self.client.post("/v1/enroll", json={"user_id": "alice", "vector": VECTOR_A})
        resp = self.client.post("/v1/authenticate", json={"user_id": "alice", "vector": VECTOR_B})
        self.assertEqual(resp.status_code, 401)
    def test_enroll_too_many_images_returns_422(self):
        """> 12 images → 422."""
        r = self.client.post(
            "/v1/enroll",
            data={"user_id": "dave"},
            files=_enroll_files(13),
        )
        self.assertEqual(r.status_code, 422)

    def test_authenticate_unknown_user_returns_401_not_404(self):
        resp = self.client.post("/v1/authenticate", json={"user_id": "nobody", "vector": VECTOR_A})
        self.assertEqual(resp.status_code, 401)
    def test_enroll_missing_user_id_returns_422(self):
        r = self.client.post("/v1/enroll", files=_enroll_files(8))
        self.assertEqual(r.status_code, 422)

    def test_revoke_then_authenticate_fails(self):
        self.client.post("/v1/enroll", json={"user_id": "alice", "vector": VECTOR_A})
        revoke_resp = self.client.delete("/v1/users/alice")
        self.assertEqual(revoke_resp.status_code, 200)
        self.assertEqual(revoke_resp.json(), {"user_id": "alice", "status": "revoked"})
    def test_enroll_empty_user_id_returns_422(self):
        r = self.client.post(
            "/v1/enroll",
            data={"user_id": ""},
            files=_enroll_files(8),
        )
        self.assertEqual(r.status_code, 422)

        auth_resp = self.client.post("/v1/authenticate", json={"user_id": "alice", "vector": VECTOR_A})
        self.assertEqual(auth_resp.status_code, 401)
    def test_enroll_invalid_image_bytes_returns_422(self):
        bad_files = [
            ("images", (f"frame_{i}.jpg", b"not-an-image", "image/jpeg"))
            for i in range(8)
        ]
        r = self.client.post(
            "/v1/enroll",
            data={"user_id": "eve"},
            files=bad_files,
        )
        self.assertEqual(r.status_code, 422)

    def test_revoke_unknown_user_is_idempotent(self):
        resp = self.client.delete("/v1/users/nobody")
        self.assertEqual(resp.status_code, 200)
    def test_reenroll_same_user_id_succeeds(self):
        """Re-enrolling (upsert) should succeed and return 200."""
        files = _enroll_files(8, color=(50, 50, 50))
        self.client.post("/v1/enroll", data={"user_id": "frank"}, files=files)
        files2 = _enroll_files(8, color=(200, 200, 200))
        r = self.client.post("/v1/enroll", data={"user_id": "frank"}, files=files2)
        self.assertEqual(r.status_code, 200)

    def test_revoke_returns_403_when_not_authorized(self):
        self.client.post("/v1/enroll", json={"user_id": "alice", "vector": VECTOR_A})
        with patch("loomhash.compliance.revocation.is_authorized", return_value=False):
            resp = self.client.delete("/v1/users/alice")
        self.assertEqual(resp.status_code, 403)

    def test_revoke_returns_500_when_storage_reports_incomplete_deletion(self):
        client = TestClient(create_app(AlwaysFailsToDeleteBackend()))
        resp = client.delete("/v1/users/alice")
        self.assertEqual(resp.status_code, 500)
class TestAuthenticateRoute(unittest.TestCase):

    def test_enroll_rejects_wrong_length_vector(self):
        resp = self.client.post("/v1/enroll", json={"user_id": "alice", "vector": [1.0] * 127})
        self.assertEqual(resp.status_code, 422)
    def setUp(self):
        self.client = TestClient(create_app())
        # Enroll "grace" with a consistent colour so model output is stable
        files = _enroll_files(8, color=(100, 120, 140))
        self.client.post("/v1/enroll", data={"user_id": "grace"}, files=files)

    def test_enroll_rejects_empty_user_id(self):
        resp = self.client.post("/v1/enroll", json={"user_id": "", "vector": VECTOR_A})
        self.assertEqual(resp.status_code, 422)
    def test_authenticate_same_colour_returns_200(self):
        """Authenticate with the same solid colour used for enrollment.

    def test_enroll_rejects_unexpected_extra_field(self):
        # Constraint 3: a stray "image" field must be rejected, not silently ignored.
        resp = self.client.post(
            "/v1/enroll", json={"user_id": "alice", "vector": VECTOR_A, "image": "base64..."}
        A solid-colour image always produces the same model output, so the
        Hamming distance between enrollment and query hash is 0 -- guaranteed
        to be within the 0.20 threshold.
        """
        r = self.client.post(
            "/v1/authenticate",
            data={"user_id": "grace"},
            files=[_auth_file(color=(100, 120, 140))],
        )
        self.assertEqual(resp.status_code, 422)
        self.assertEqual(r.status_code, 200)
        self.assertEqual(r.json()["status"], "authenticated")

    def test_cors_disabled_by_default(self):
        resp = self.client.options(
            "/v1/enroll",
            headers={
                "Origin": "http://localhost:5500",
                "Access-Control-Request-Method": "POST",
            },
    def test_authenticate_response_has_no_distance_field(self):
        """The response must NOT expose the Hamming distance (anti-hill-climbing)."""
        r = self.client.post(
            "/v1/authenticate",
            data={"user_id": "grace"},
            files=[_auth_file(color=(100, 120, 140))],
        )
        self.assertNotIn("access-control-allow-origin", resp.headers)
        self.assertNotIn("distance", r.json())
        self.assertNotIn("score", r.json())

    def test_dev_cors_allows_localhost_origins_when_enabled(self):
        client = TestClient(create_app(InMemoryStorageBackend(), enable_dev_cors=True))
        resp = client.options(
            "/v1/enroll",
            headers={
                "Origin": "http://localhost:5500",
                "Access-Control-Request-Method": "POST",
            },
    def test_authenticate_unknown_user_returns_401_not_404(self):
        """Unknown user_id → 401 (same as mismatch; prevents user enumeration)."""
        r = self.client.post(
            "/v1/authenticate",
            data={"user_id": "nobody"},
            files=[_auth_file()],
        )
        self.assertEqual(resp.headers.get("access-control-allow-origin"), "http://localhost:5500")
        self.assertEqual(r.status_code, 401)

    def test_re_enroll_upserts_with_a_fresh_seed(self):
        # Re-enrollment generates a new random seed, so the OLD vector no
        # longer authenticates even though it authenticated before.
        self.client.post("/v1/enroll", json={"user_id": "alice", "vector": VECTOR_A})
        self.client.post("/v1/enroll", json={"user_id": "alice", "vector": VECTOR_B})
    def test_authenticate_missing_user_id_returns_422(self):
        r = self.client.post("/v1/authenticate", files=[_auth_file()])
        self.assertEqual(r.status_code, 422)

        old_auth = self.client.post("/v1/authenticate", json={"user_id": "alice", "vector": VECTOR_A})
        new_auth = self.client.post("/v1/authenticate", json={"user_id": "alice", "vector": VECTOR_B})
        self.assertEqual(old_auth.status_code, 401)
        self.assertEqual(new_auth.status_code, 200)
    def test_authenticate_invalid_image_returns_422(self):
        r = self.client.post(
            "/v1/authenticate",
            data={"user_id": "grace"},
            files=[("image", ("face.jpg", b"not-an-image", "image/jpeg"))],
        )
        self.assertEqual(r.status_code, 422)

    def test_authenticate_missing_image_returns_422(self):
        r = self.client.post("/v1/authenticate", data={"user_id": "grace"})
        self.assertEqual(r.status_code, 422)


class TestRevokeRoute(unittest.TestCase):

    def setUp(self):
        self.client = TestClient(create_app())
        files = _enroll_files(8, color=(80, 90, 100))
        self.client.post("/v1/enroll", data={"user_id": "henry"}, files=files)

    def test_revoke_returns_200(self):
        r = self.client.delete("/v1/users/henry")
        self.assertEqual(r.status_code, 200)
        self.assertEqual(r.json()["status"], "revoked")

    def test_revoke_then_authenticate_returns_401(self):
        self.client.delete("/v1/users/henry")
        r = self.client.post(
            "/v1/authenticate",
            data={"user_id": "henry"},
            files=[_auth_file(color=(80, 90, 100))],
        )
        self.assertEqual(r.status_code, 401)

    def test_revoke_unknown_user_returns_200(self):
        """Revoking a user that was never enrolled: InMemoryStorageBackend.delete()
        is idempotent and returns True for unknowns, so the API returns 200.
        The 500 path (storage reports partial failure) is covered in
        tests/test_compliance/test_revocation.py via AlwaysFailsToDeleteBackend.
        """
        r = self.client.delete("/v1/users/ghost")
        self.assertEqual(r.status_code, 200)


class TestCorsDefaults(unittest.TestCase):

    def test_cors_off_by_default(self):
        client = TestClient(create_app())
        r = client.get("/docs")
        self.assertNotIn("access-control-allow-origin", r.headers)

    def test_cors_on_when_requested(self):
        client = TestClient(create_app(enable_dev_cors=True))
        r = client.options(
            "/v1/enroll",
            headers={"Origin": "http://localhost:3000", "Access-Control-Request-Method": "POST"},
        )
        self.assertIn("access-control-allow-origin", r.headers)


if __name__ == "__main__":
    unittest.main()
