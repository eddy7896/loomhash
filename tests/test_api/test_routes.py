"""End-to-end HTTP tests for the API Gateway multipart routes (D-12).

Tests use FastAPI's TestClient (httpx) with an in-memory storage backend.
Images are small in-memory JPEGs generated with Pillow -- no disk I/O, no real
faces, no biometric data.

All requests pass a valid API key via X-API-Key header (D-05). Dedicated tests
verify that missing/invalid keys produce 401.
"""

import io
import unittest
from unittest.mock import patch

from fastapi.testclient import TestClient
from PIL import Image

from loomhash.api.app import create_app
from loomhash.auth import InMemoryAPIKeyStore, RateLimiter, generate_api_key
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

    def list_users(self) -> list[str]:
        return []


def _jpeg(color: tuple = (128, 100, 80), size: tuple = (64, 64)) -> bytes:
    """Tiny in-memory JPEG -- enough for the model to infer a vector."""
    img = Image.new("RGB", size, color=color)
    buf = io.BytesIO()
    img.save(buf, format="JPEG")
    return buf.getvalue()


def _enroll_files(count: int, *, varied: bool = True, color: tuple = (128, 100, 80)):
    """Generate enrollment files.

    varied=True produces frames with distinct colours (passes liveness).
    varied=False produces identical frames (fails liveness).
    """
    if varied:
        return [
            ("images", (f"frame_{i}.jpg", _jpeg(color=(color[0] + i * 8, color[1] + i * 5, color[2] + i * 3)), "image/jpeg"))
            for i in range(count)
        ]
    return [
        ("images", (f"frame_{i}.jpg", _jpeg(color=color), "image/jpeg"))
        for i in range(count)
    ]


def _auth_file(color: tuple = (128, 100, 80)):
    return ("image", ("frame_auth.jpg", _jpeg(color=color), "image/jpeg"))


def _setup_key_store():
    """Create an InMemoryAPIKeyStore with one active key. Returns (store, raw_key)."""
    store = InMemoryAPIKeyStore()
    raw_key, record = generate_api_key()
    store.store(record)
    return store, raw_key


def _auth_headers(raw_key: str) -> dict[str, str]:
    return {"X-API-Key": raw_key}


# ---------------------------------------------------------------------------
# Tests
# ---------------------------------------------------------------------------

class TestEnrollRoute(unittest.TestCase):
    def setUp(self):
        self.key_store, self.api_key = _setup_key_store()
        self.app = create_app(key_store=self.key_store)
        self.client = TestClient(self.app)
        self.headers = _auth_headers(self.api_key)

    def test_enroll_success_returns_200(self):
        files = _enroll_files(8)
        r = self.client.post("/v1/enroll", data={"user_id": "alice"}, files=files, headers=self.headers)
        self.assertEqual(r.status_code, 200)
        self.assertEqual(r.json()["status"], "enrolled")
        self.assertEqual(r.json()["user_id"], "alice")

    def test_enroll_too_few_images_returns_422(self):
        files = _enroll_files(7)
        r = self.client.post("/v1/enroll", data={"user_id": "bob"}, files=files, headers=self.headers)
        self.assertEqual(r.status_code, 422)

    def test_enroll_too_many_images_returns_422(self):
        files = _enroll_files(13)
        r = self.client.post("/v1/enroll", data={"user_id": "bob"}, files=files, headers=self.headers)
        self.assertEqual(r.status_code, 422)

    def test_enroll_invalid_image_bytes_returns_422(self):
        bad_files = [
            ("images", (f"frame_{i}.jpg", b"not-an-image", "image/jpeg"))
            for i in range(8)
        ]
        r = self.client.post("/v1/enroll", data={"user_id": "eve"}, files=bad_files, headers=self.headers)
        self.assertEqual(r.status_code, 422)


class TestAuthenticateRoute(unittest.TestCase):
    def setUp(self):
        self.key_store, self.api_key = _setup_key_store()
        self.client = TestClient(create_app(key_store=self.key_store))
        self.headers = _auth_headers(self.api_key)
        # Enroll "grace" with varied frames (passes liveness) of consistent base colour
        files = _enroll_files(8, color=(100, 120, 140))
        self.client.post("/v1/enroll", data={"user_id": "grace"}, files=files, headers=self.headers)

    def test_authenticate_same_colour_returns_200(self):
        r = self.client.post(
            "/v1/authenticate",
            data={"user_id": "grace"},
            files=[_auth_file(color=(100, 120, 140))],
            headers=self.headers,
        )
        self.assertEqual(r.status_code, 200)
        self.assertEqual(r.json()["status"], "authenticated")

    def test_authenticate_unknown_user_returns_401(self):
        r = self.client.post(
            "/v1/authenticate",
            data={"user_id": "nobody"},
            files=[_auth_file()],
            headers=self.headers,
        )
        self.assertEqual(r.status_code, 401)

    def test_authenticate_missing_image_returns_422(self):
        r = self.client.post("/v1/authenticate", data={"user_id": "grace"}, headers=self.headers)
        self.assertEqual(r.status_code, 422)

    def test_authenticate_invalid_image_returns_422(self):
        r = self.client.post(
            "/v1/authenticate",
            data={"user_id": "grace"},
            files=[("image", ("face.jpg", b"not-an-image", "image/jpeg"))],
            headers=self.headers,
        )
        self.assertEqual(r.status_code, 422)

    def test_authenticate_response_has_no_distance_field(self):
        r = self.client.post(
            "/v1/authenticate",
            data={"user_id": "grace"},
            files=[_auth_file(color=(100, 120, 140))],
            headers=self.headers,
        )
        self.assertNotIn("distance", r.json())
        self.assertNotIn("score", r.json())


class TestRevokeRoute(unittest.TestCase):
    def setUp(self):
        self.key_store, self.api_key = _setup_key_store()
        self.client = TestClient(create_app(key_store=self.key_store))
        self.headers = _auth_headers(self.api_key)
        files = _enroll_files(8, color=(80, 90, 100))
        self.client.post("/v1/enroll", data={"user_id": "henry"}, files=files, headers=self.headers)

    def test_revoke_returns_200(self):
        r = self.client.delete("/v1/users/henry", headers=self.headers)
        self.assertEqual(r.status_code, 200)
        self.assertEqual(r.json()["status"], "revoked")

    def test_revoke_then_authenticate_returns_401(self):
        self.client.delete("/v1/users/henry", headers=self.headers)
        r = self.client.post(
            "/v1/authenticate",
            data={"user_id": "henry"},
            files=[_auth_file(color=(80, 90, 100))],
            headers=self.headers,
        )
        self.assertEqual(r.status_code, 401)

    def test_revoke_unknown_user_returns_200(self):
        r = self.client.delete("/v1/users/ghost", headers=self.headers)
        self.assertEqual(r.status_code, 200)

    def test_revoke_returns_403_when_not_authorized(self):
        with patch("loomhash.compliance.revocation.is_authorized", return_value=False):
            resp = self.client.delete("/v1/users/henry", headers=self.headers)
        self.assertEqual(resp.status_code, 403)

    def test_revoke_returns_500_when_storage_reports_incomplete_deletion(self):
        client = TestClient(create_app(AlwaysFailsToDeleteBackend(), key_store=self.key_store))
        resp = client.delete("/v1/users/henry", headers=self.headers)
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


# ---------------------------------------------------------------------------
# API Key Authentication (D-05) Tests
# ---------------------------------------------------------------------------

class TestAPIKeyAuthentication(unittest.TestCase):
    """All routes require a valid X-API-Key header."""

    def setUp(self):
        self.key_store, self.api_key = _setup_key_store()
        self.client = TestClient(create_app(key_store=self.key_store))

    def test_enroll_without_key_returns_401(self):
        files = _enroll_files(8)
        r = self.client.post("/v1/enroll", data={"user_id": "x"}, files=files)
        self.assertEqual(r.status_code, 401)
        self.assertIn("API key", r.json()["detail"])

    def test_authenticate_without_key_returns_401(self):
        r = self.client.post(
            "/v1/authenticate",
            data={"user_id": "x"},
            files=[_auth_file()],
        )
        self.assertEqual(r.status_code, 401)

    def test_revoke_without_key_returns_401(self):
        r = self.client.delete("/v1/users/x")
        self.assertEqual(r.status_code, 401)

    def test_invalid_key_returns_401(self):
        r = self.client.post(
            "/v1/enroll",
            data={"user_id": "x"},
            files=_enroll_files(8),
            headers={"X-API-Key": "lh_XXXXXXXX_totally_bogus_secret"},
        )
        self.assertEqual(r.status_code, 401)

    def test_deactivated_key_returns_401(self):
        # Deactivate the key
        from loomhash.auth import parse_key_id
        key_id = parse_key_id(self.api_key)
        self.key_store.deactivate(key_id)
        r = self.client.post(
            "/v1/enroll",
            data={"user_id": "x"},
            files=_enroll_files(8),
            headers={"X-API-Key": self.api_key},
        )
        self.assertEqual(r.status_code, 401)


# ---------------------------------------------------------------------------
# Rate Limiting Tests
# ---------------------------------------------------------------------------

class TestRateLimiting(unittest.TestCase):
    """Rate limiting on /v1/authenticate (D-05 brute-force protection)."""

    def setUp(self):
        self.key_store, self.api_key = _setup_key_store()
        self.limiter = RateLimiter(max_requests=2, window_seconds=60)
        self.client = TestClient(
            create_app(key_store=self.key_store, rate_limiter=self.limiter)
        )
        self.headers = _auth_headers(self.api_key)
        # Enroll a user so auth can reach the limiter
        files = _enroll_files(8, color=(100, 100, 100))
        self.client.post("/v1/enroll", data={"user_id": "rl_user"}, files=files, headers=self.headers)

    def test_rate_limit_returns_429(self):
        for _ in range(2):
            self.client.post(
                "/v1/authenticate",
                data={"user_id": "rl_user"},
                files=[_auth_file(color=(100, 100, 100))],
                headers=self.headers,
            )
        r = self.client.post(
            "/v1/authenticate",
            data={"user_id": "rl_user"},
            files=[_auth_file(color=(100, 100, 100))],
            headers=self.headers,
        )
        self.assertEqual(r.status_code, 429)
        self.assertIn("Retry-After", r.headers)


# ---------------------------------------------------------------------------
# Liveness Tests (via API)
# ---------------------------------------------------------------------------

class TestLivenessViaAPI(unittest.TestCase):
    """Liveness check integration — enrollment with identical frames fails."""

    def setUp(self):
        self.key_store, self.api_key = _setup_key_store()
        self.client = TestClient(create_app(key_store=self.key_store))
        self.headers = _auth_headers(self.api_key)

    def test_identical_frames_returns_422(self):
        # All 8 frames are identical — liveness should fail
        files = _enroll_files(8, varied=False, color=(100, 100, 100))
        r = self.client.post(
            "/v1/enroll",
            data={"user_id": "spoof"},
            files=files,
            headers=self.headers,
        )
        self.assertEqual(r.status_code, 422)
        self.assertIn("liveness", r.json()["detail"])


if __name__ == "__main__":
    unittest.main()
