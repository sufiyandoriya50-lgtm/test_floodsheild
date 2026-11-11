
import pytest

from app import create_app
from app.config import TestingConfig


# Creates an isolated Flask application for rate-limit tests.
@pytest.fixture
def rate_limit_client():
    """Provide a fresh application and limiter state for each test."""

    class RateLimitTestingConfig(TestingConfig):
        RATELIMIT_ENABLED = True
        RATELIMIT_STORAGE_URI = "memory://"
        RATELIMIT_HEADERS_ENABLED = True

    app = create_app(RateLimitTestingConfig)

    with app.test_client() as client:
        yield client


# Verifies that citizen login requests are blocked after five attempts.
def test_citizen_login_rate_limit(rate_limit_client):
    """Block the sixth citizen login request within one minute."""

    responses = []

    for _ in range(6):
        response = rate_limit_client.post(
            "/api/auth/login",
            json={}
        )
        responses.append(response)

    assert all(
        response.status_code == 400
        for response in responses[:5]
    )

    assert responses[5].status_code == 429


# Verifies that rate-limit errors use the application's JSON format.
def test_rate_limit_response_is_json(rate_limit_client):
    """Return a JSON error when the login limit is exceeded."""

    responses = []

    for _ in range(6):
        response = rate_limit_client.post(
            "/api/auth/login",
            json={}
        )
        responses.append(response)

    blocked_response = responses[5]

    assert blocked_response.status_code == 429
    assert blocked_response.is_json

    data = blocked_response.get_json()

    assert data["status"] == "error"
    assert data["error"] == "Too Many Requests"
