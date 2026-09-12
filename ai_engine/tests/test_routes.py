from fastapi.testclient import TestClient

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
