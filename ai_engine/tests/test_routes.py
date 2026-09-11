import pytest
from fastapi.testclient import TestClient

from app.schemas.envelopes import NOT_IMPLEMENTED_CODE, NOT_IMPLEMENTED_MESSAGE

REGISTERED_API_ROUTES = [
    ("POST", "/api/cases"),
    ("GET", "/api/cases/{case_id}"),
    ("PATCH", "/api/cases/{case_id}"),
    ("POST", "/api/cases/{case_id}/transcribe"),
    ("POST", "/api/cases/{case_id}/extract"),
    ("PATCH", "/api/cases/{case_id}/clarifications/{clarification_id}"),
    ("POST", "/api/cases/{case_id}/draft"),
    ("PATCH", "/api/cases/{case_id}/draft"),
]

API_ROUTES = [
    ("POST", "/api/cases", {"json": {"input_mode": "typed", "case_text": "Problem"}}),
    ("GET", "/api/cases/1", {}),
    ("PATCH", "/api/cases/1", {"json": {"case_text": "Updated problem"}}),
    (
        "POST",
        "/api/cases/1/transcribe",
        {"files": {"audio": ("sample.webm", b"audio-bytes", "audio/webm")}},
    ),
    ("POST", "/api/cases/1/extract", {}),
    (
        "PATCH",
        "/api/cases/1/clarifications/10",
        {"json": {"status": "answered", "answer": "Converge ICT"}},
    ),
    ("POST", "/api/cases/1/draft", {}),
    (
        "PATCH",
        "/api/cases/1/draft",
        {"json": {"subject": "Updated subject", "body": "Updated body"}},
    ),
]

EXPECTED_ERROR = {
    "error": {
        "code": NOT_IMPLEMENTED_CODE,
        "message": NOT_IMPLEMENTED_MESSAGE,
    }
}


def test_health_endpoint_is_unchanged(client: TestClient) -> None:
    response = client.get("/health")

    assert response.status_code == 200
    assert response.json() == {"status": "ok"}


def test_all_api_routes_are_registered(client: TestClient) -> None:
    openapi_paths = client.app.openapi()["paths"]
    registered_paths = {
        (method.upper(), path)
        for path, operations in openapi_paths.items()
        for method in operations
    }

    for method, path in REGISTERED_API_ROUTES:
        assert (method, path) in registered_paths


@pytest.mark.parametrize("method,path,kwargs", API_ROUTES)
def test_api_route_returns_not_implemented_envelope(
    client: TestClient,
    method: str,
    path: str,
    kwargs: dict,
) -> None:
    response = client.request(method, path, **kwargs)

    assert response.status_code == 501
    assert response.json() == EXPECTED_ERROR
