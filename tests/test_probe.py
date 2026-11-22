from dataclasses import replace

import httpx
import pytest

from app.ai.probe import probe_provider
from app.config.settings import Settings


def test_missing_ollama_is_reported_without_fake_success():
    def unavailable(request):
        raise httpx.ConnectError("not running", request=request)

    result = probe_provider(Settings(), transport=httpx.MockTransport(unavailable))
    assert not result.ok
    assert "start Ollama" in result.message


def test_real_model_list_protocol():
    def provider(request):
        assert request.url == "http://127.0.0.1:11434/api/tags"
        assert "authorization" not in request.headers
        return httpx.Response(200, json={"models": [{"name": "qwen3:1.7b"}]})

    result = probe_provider(Settings(), transport=httpx.MockTransport(provider))
    assert result.ok


def test_missing_model_is_not_reported_ready():
    result = probe_provider(
        Settings(),
        transport=httpx.MockTransport(lambda _: httpx.Response(200, json={"models": []})),
    )
    assert not result.ok
    assert "not listed" in result.message


@pytest.mark.parametrize(
    "provider,endpoint,header,field,entry",
    [
        ("openai", "https://api.openai.com/v1", "authorization", "data", {"id": "test-model"}),
        ("claude", "https://api.anthropic.com/v1", "x-api-key", "data", {"id": "test-model"}),
        (
            "gemini",
            "https://generativelanguage.googleapis.com/v1beta",
            "x-goog-api-key",
            "models",
            {"name": "models/test-model"},
        ),
    ],
)
def test_provider_authentication_and_model_listing(provider, endpoint, header, field, entry):
    settings = replace(
        Settings(), provider=provider, mode="online", base_url=endpoint, model="test-model"
    )

    def response(request):
        assert request.url.path.endswith("/models")
        assert "sensitive-test-value" in request.headers[header]
        assert "key=" not in str(request.url)
        return httpx.Response(200, json={field: [entry]})

    assert probe_provider(settings, "sensitive-test-value", httpx.MockTransport(response)).ok


def test_redirect_does_not_forward_api_key():
    requests = []

    def redirect(request):
        requests.append(request)
        return httpx.Response(302, headers={"Location": "https://elsewhere.test"})

    settings = replace(
        Settings(), provider="custom", mode="online", base_url="https://test.example/v1"
    )
    result = probe_provider(settings, "secret", httpx.MockTransport(redirect))
    assert not result.ok
    assert len(requests) == 1
    assert "secret" not in result.message


@pytest.mark.parametrize("status,body", [(401, {}), (200, []), (200, {"models": "invalid"})])
def test_invalid_provider_results_are_failures(status, body):
    result = probe_provider(
        Settings(), transport=httpx.MockTransport(lambda _: httpx.Response(status, json=body))
    )
    assert not result.ok


def test_oversized_response_is_refused():
    result = probe_provider(
        Settings(),
        transport=httpx.MockTransport(lambda _: httpx.Response(200, content=b" " * 2_100_000)),
    )
    assert not result.ok
    assert "large" in result.message
