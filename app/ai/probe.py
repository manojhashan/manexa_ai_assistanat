"""Explicit connection checks, never invoked at startup or periodically in offline mode."""

import json
import time
from dataclasses import dataclass

import httpx

from app.config.settings import Settings, validate_endpoint


@dataclass(frozen=True)
class ProbeResult:
    ok: bool
    message: str


def probe_provider(settings: Settings, key: str = "", transport=None) -> ProbeResult:
    """List models without generating text or incurring a completion charge."""
    settings.validate()
    base = validate_endpoint(settings.base_url, local_only=settings.mode == "offline")
    headers = {}
    if settings.provider == "ollama":
        route = "/api/tags"
    elif settings.provider == "claude":
        route = "/models"
        headers = {"x-api-key": key, "anthropic-version": "2023-06-01"}
    elif settings.provider == "gemini":
        route = "/models"
        headers = {"x-goog-api-key": key}
    else:
        route = "/models"
        if key:
            headers = {"Authorization": f"Bearer {key}"}
    if settings.provider not in ("ollama", "custom") and not key:
        return ProbeResult(False, "Enter an API key or save one in Credential Manager first.")
    try:
        # Do not follow redirects: they could forward custom API headers to another host.
        # Ignore proxy environment variables so loopback Ollama stays local.
        with httpx.Client(
            timeout=httpx.Timeout(6.0), follow_redirects=False, trust_env=False, transport=transport
        ) as client:
            started = time.monotonic()
            with client.stream("GET", base + route, headers=headers) as response:
                if response.status_code in (401, 403):
                    return ProbeResult(False, "The provider rejected authentication or access.")
                if response.status_code != 200:
                    return ProbeResult(False, f"The provider returned HTTP {response.status_code}.")
                payload = bytearray()
                for chunk in response.iter_bytes(chunk_size=8192):
                    if time.monotonic() - started > 8:
                        return ProbeResult(False, "The provider response took too long.")
                    payload.extend(chunk)
                    if len(payload) > 2_000_000:
                        return ProbeResult(False, "The provider response was unexpectedly large.")
                body = json.loads(payload)
        field = "models" if settings.provider in ("ollama", "gemini") else "data"
        entries = body.get(field)
        if not isinstance(entries, list):
            return ProbeResult(False, "This endpoint did not return a supported model list.")
        ids = {
            str(item.get("name", item.get("id", ""))).removeprefix("models/")
            for item in entries
            if isinstance(item, dict)
        }
        if settings.model and settings.model not in ids:
            return ProbeResult(
                False,
                f"Connected; the configured model is not listed ({len(ids)} models available).",
            )
        return ProbeResult(
            True, f"Connected. {len(ids)} model(s) available. No text was generated."
        )
    except httpx.TimeoutException:
        return ProbeResult(False, "Connection timed out. Check the endpoint and network.")
    except httpx.HTTPError:
        return ProbeResult(False, "Cannot reach the provider. For offline AI, start Ollama first.")
    except (ValueError, TypeError, AttributeError):
        return ProbeResult(False, "The provider returned an invalid model list.")
