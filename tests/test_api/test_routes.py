"""End-to-end HTTP tests for the API Gateway multipart routes (D-12).

Tests use FastAPI's TestClient (httpx) with an in-memory storage backend.
Images are small in-memory JPEGs generated with Pillow -- no disk I/O, no real
faces, no biometric data.
"""

import io
import unittest
from unittest.mock import patch

from fastapi.testclient import TestClient
from PIL import Image

from loomhash.api.app import create_app
from loomhash.storage import EnrollmentRecord, InMemoryStorageBackend, StorageBackend


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

class AlwaysFailsToDeleteBackend(StorageBackend):
    def enroll(self, record: EnrollmentRecord) -> None:
        pass

    def get(self, user_id: str):
        return None

    def delete(self, user_id: str) -> bool:
        return False


def _jpeg(color: tuple = (128, 100, 80), size: tuple = (64, 64)) -> bytes:
    """Tiny in-memory JPEG -- enough for the model to infer a vector."""
    img = Image.new("RGB", size, color=color)
    buf = io.BytesIO()
    img.save(buf, format="JPEG")
    return buf.getvalue()


def _enroll_files(count: int, color: tuple = (128, 100, 80)):
    return [
        ("images", (f"frame_{i}.jpg", _jpeg(color=color), "image/jpeg"))
        for i in range(count)
    ]


def _auth_file(color: tuple = (128, 100, 80)):
    return ("image", ("frame_auth.jpg", _jpeg(color=color), "image/jpeg"))


# ---------------------------------------------------------------------------
# Tests
# ---------------------------------------------------------------------------

class TestEnrollRoute(unittest.TestCase):
    def setUp(self):
        self.app = create_app()
        self.client = TestClient(self.app)

    def test_enroll_success_returns_200(self):
        files = _enroll_files(8)
        r = self.client.post("/v1/enroll", data={"user_id": "alice"}, files=files)
        self.assertEqual(r.status_code, 200)
        self.assertEqual(r.json()["status"], "enrolled")
        self.assertEqual(r.json()["user_id"], "alice")

    def test_enroll_too_few_images_returns_422(self):
        files = _enroll_files(7)
        r = self.client.post("/v1/enroll", data={"user_id": "bob"}, files=files)
        self.assertEqual(r.status_code, 422)

    def test_enroll_too_many_images_returns_422(self):
        files = _enroll_files(13)
        r = self.client.post("/v1/enroll", data={"user_id": "bob"}, files=files)
        self.assertEqual(r.status_code, 422)

    def test_enroll_invalid_image_bytes_returns_422(self):
        bad_files = [
            ("images", (f"frame_{i}.jpg", b"not-an-image", "image/jpeg"))
            for i in range(8)
        ]
        r = self.client.post("/v1/enroll", data={"user_id": "eve"}, files=bad_files)
        self.assertEqual(r.status_code, 422)


class TestAuthenticateRoute(unittest.TestCase):
    def setUp(self):
        self.client = TestClient(create_app())
        # Enroll "grace" with a consistent colour so model output is stable
        files = _enroll_files(8, color=(100, 120, 140))
        self.client.post("/v1/enroll", data={"user_id": "grace"}, files=files)

    def test_authenticate_same_colour_returns_200(self):
        r = self.client.post(
            "/v1/authenticate",
            data={"user_id": "grace"},
            files=[_auth_file(color=(100, 120, 140))],
        )
        self.assertEqual(r.status_code, 200)
        self.assertEqual(r.json()["status"], "authenticated")

    def test_authenticate_unknown_user_returns_401(self):
        r = self.client.post(
            "/v1/authenticate",
            data={"user_id": "nobody"},
            files=[_auth_file()],
        )
        self.assertEqual(r.status_code, 401)

    def test_authenticate_missing_image_returns_422(self):
        r = self.client.post("/v1/authenticate", data={"user_id": "grace"})
        self.assertEqual(r.status_code, 422)

    def test_authenticate_invalid_image_returns_422(self):
        r = self.client.post(
            "/v1/authenticate",
            data={"user_id": "grace"},
            files=[("image", ("face.jpg", b"not-an-image", "image/jpeg"))],
        )
        self.assertEqual(r.status_code, 422)

    def test_authenticate_response_has_no_distance_field(self):
        r = self.client.post(
            "/v1/authenticate",
            data={"user_id": "grace"},
            files=[_auth_file(color=(100, 120, 140))],
        )
        self.assertNotIn("distance", r.json())
        self.assertNotIn("score", r.json())


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
        r = self.client.delete("/v1/users/ghost")
        self.assertEqual(r.status_code, 200)

    def test_revoke_returns_403_when_not_authorized(self):
        with patch("loomhash.compliance.revocation.is_authorized", return_value=False):
            resp = self.client.delete("/v1/users/henry")
        self.assertEqual(resp.status_code, 403)

    def test_revoke_returns_500_when_storage_reports_incomplete_deletion(self):
        client = TestClient(create_app(AlwaysFailsToDeleteBackend()))
        resp = client.delete("/v1/users/henry")
        self.assertEqual(resp.status_code, 500)


class TestCorsDefaults(unittest.TestCase):
    def test_cors_off_by_default(self):
        client = TestClient(create_app())
        r = client.options("/v1/enroll", headers={"Origin": "http://localhost:5500", "Access-Control-Request-Method": "POST"})
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
