import pytest
from fastapi.testclient import TestClient

from app.schemas.envelopes import NOT_IMPLEMENTED_CODE, NOT_IMPLEMENTED_MESSAGE

REGISTERED_API_ROUTES = [
    ("POST", "/api/cases"),
    ("GET", "/api/cases/{case_id}"),
    ("PATCH", "/api/cases/{case_id}"),
    ("POST", "/api/cases/{case_id}/transcription-token"),
    ("POST", "/api/cases/{case_id}/extract"),
    ("PATCH", "/api/cases/{case_id}/clarifications/{clarification_id}"),
    ("POST", "/api/cases/{case_id}/draft"),
    ("PATCH", "/api/cases/{case_id}/draft"),
]

DEFERRED_API_ROUTES = [
    ("POST", "/api/cases/1/extract", {}),
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


@pytest.mark.parametrize("method,path,kwargs", DEFERRED_API_ROUTES)
def test_deferred_api_route_returns_not_implemented_envelope(
    client: TestClient,
    method: str,
    path: str,
    kwargs: dict,
) -> None:
    response = client.request(method, path, **kwargs)

    assert response.status_code == 501
    assert response.json() == EXPECTED_ERROR
