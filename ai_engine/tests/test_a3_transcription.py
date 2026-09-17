import os
from unittest.mock import patch

import httpx
import pytest
from fastapi.testclient import TestClient

from app.core.config import get_settings
from app.services.transcription.assemblyai import AssemblyAIStreamingTokenService
from app.services.transcription.errors import TokenIssuanceFailedError, TokenServiceUnavailableError
from app.services.transcription.fake import FakeStreamingTokenService
from app.services.transcription.protocol import STREAMING_WS_URL, StreamingTokenResult

CASE_NOT_FOUND = {
    "error": {
        "code": "case_not_found",
        "message": "Case not found.",
    }
}

INVALID_CASE_STATE = {
    "error": {
        "code": "invalid_case_state",
        "message": "Streaming tokens are only available for voice cases in transcribing status.",
    }
}

TOKEN_ISSUANCE_FAILED = {
    "error": {
        "code": "token_issuance_failed",
        "message": "Streaming token could not be issued.",
    }
}


def _create_voice_case(client: TestClient) -> dict:
    return client.post("/api/cases", json={"input_mode": "voice"}).json()["data"]


def _issue_token(client: TestClient, case_id: int) -> object:
    return client.post(f"/api/cases/{case_id}/transcription-token")


def test_token_issuance_returns_envelope_without_mutating_case(
    client: TestClient,
    fake_streaming_token_service: FakeStreamingTokenService,
) -> None:
    fake_streaming_token_service._token = "short-lived-token"
    created = _create_voice_case(client)

    response = _issue_token(client, created["id"])

    assert response.status_code == 200
    assert response.json() == {
        "data": {
            "case_id": created["id"],
            "token": "short-lived-token",
            "expires_in_seconds": 60,
            "ws_url": STREAMING_WS_URL,
        }
    }

    loaded = client.get(f"/api/cases/{created['id']}").json()["data"]
    assert loaded["status"] == "transcribing"
    assert loaded["case_text"] is None


def test_reviewed_patch_persists_transcript_and_moves_case_to_input_ready(
    client: TestClient,
) -> None:
    created = _create_voice_case(client)
    token_response = _issue_token(client, created["id"])
    reviewed_text = "Corrected transcript for support."

    patch_response = client.patch(
        f"/api/cases/{created['id']}",
        json={"case_text": reviewed_text},
    )

    assert token_response.status_code == 200
    assert patch_response.status_code == 200
    payload = patch_response.json()["data"]
    assert payload["status"] == "input_ready"
    assert payload["case_text"] == reviewed_text


def test_token_unknown_case_returns_not_found(client: TestClient) -> None:
    response = _issue_token(client, 999)

    assert response.status_code == 404
    assert response.json() == CASE_NOT_FOUND


def test_token_rejects_typed_case(client: TestClient) -> None:
    created = client.post(
        "/api/cases",
        json={"input_mode": "typed", "case_text": "Problem"},
    ).json()["data"]

    response = _issue_token(client, created["id"])

    assert response.status_code == 409
    assert response.json() == INVALID_CASE_STATE


def test_token_rejects_non_transcribing_voice_case(client: TestClient) -> None:
    created = _create_voice_case(client)
    client.patch(
        f"/api/cases/{created['id']}",
        json={"case_text": "Already reviewed transcript."},
    )

    response = _issue_token(client, created["id"])

    assert response.status_code == 409
    assert response.json() == INVALID_CASE_STATE


def test_token_provider_failure_returns_502(
    client: TestClient,
    fake_streaming_token_service: FakeStreamingTokenService,
) -> None:
    fake_streaming_token_service._should_fail = True
    created = _create_voice_case(client)

    response = _issue_token(client, created["id"])

    assert response.status_code == 502
    assert response.json() == TOKEN_ISSUANCE_FAILED


def test_get_streaming_token_service_uses_fake_without_api_key() -> None:
    get_settings.cache_clear()
    with patch.dict(os.environ, {"AI_ENGINE_ASSEMBLYAI_API_KEY": ""}, clear=False):
        get_settings.cache_clear()
        from app.api.dependencies import get_streaming_token_service

        service = get_streaming_token_service()
        assert isinstance(service, FakeStreamingTokenService)


def test_get_streaming_token_service_uses_assemblyai_with_api_key() -> None:
    get_settings.cache_clear()
    with patch.dict(os.environ, {"AI_ENGINE_ASSEMBLYAI_API_KEY": "test-key"}, clear=False):
        get_settings.cache_clear()
        from app.api.dependencies import get_streaming_token_service

        service = get_streaming_token_service()
        assert isinstance(service, AssemblyAIStreamingTokenService)
        assert service._api_key == "test-key"


@pytest.mark.asyncio
async def test_assemblyai_adapter_success_normalizes_result() -> None:
    async def handler(request: httpx.Request) -> httpx.Response:
        assert request.url.path == "/v3/token"
        assert request.url.params.get("expires_in_seconds") == "60"
        return httpx.Response(200, json={"token": "provider-token"})

    transport = httpx.MockTransport(handler)
    client = httpx.AsyncClient(
        base_url="https://streaming.assemblyai.com",
        headers={"authorization": "test-key"},
        transport=transport,
    )
    service = AssemblyAIStreamingTokenService(api_key="test-key", client=client)

    result = await service.issue_token(60)

    assert result == StreamingTokenResult(token="provider-token", expires_in_seconds=60)


@pytest.mark.asyncio
async def test_assemblyai_adapter_empty_token_raises_failed_error() -> None:
    async def handler(request: httpx.Request) -> httpx.Response:
        return httpx.Response(200, json={"token": "   "})

    transport = httpx.MockTransport(handler)
    client = httpx.AsyncClient(
        base_url="https://streaming.assemblyai.com",
        headers={"authorization": "test-key"},
        transport=transport,
    )
    service = AssemblyAIStreamingTokenService(api_key="test-key", client=client)

    with pytest.raises(TokenIssuanceFailedError):
        await service.issue_token(60)


@pytest.mark.asyncio
async def test_assemblyai_adapter_transport_failure_raises_unavailable_error() -> None:
    async def handler(request: httpx.Request) -> httpx.Response:
        raise httpx.ConnectError("network down", request=request)

    transport = httpx.MockTransport(handler)
    client = httpx.AsyncClient(
        base_url="https://streaming.assemblyai.com",
        headers={"authorization": "test-key"},
        transport=transport,
    )
    service = AssemblyAIStreamingTokenService(api_key="test-key", client=client)

    with pytest.raises(TokenServiceUnavailableError):
        await service.issue_token(60)
