"""Stateless local Ollama replies; no action execution or conversation persistence."""

import json
import time

import httpx

from app.config.settings import Settings, validate_endpoint


def local_reply(text: str, settings: Settings, cancel, transport=None) -> str:
    if cancel.is_set():
        return ""
    if settings.provider != "ollama":
        raise ValueError(
            "Live voice replies currently require Ollama. Provider tests are unchanged."
        )
    base = validate_endpoint(settings.base_url, local_only=True)
    if not settings.model:
        raise ValueError("Configure a local Ollama model first.")
    payload = {
        "model": settings.model,
        "stream": True,
        "think": False,
        "messages": [
            {
                "role": "system",
                "content": "You are MANEXA, a voice assistant. Reply briefly in plain English, "
                "unless explicitly asked for Sinhala. Understand Sinhala and romanized Sinhala "
                "when possible. Never claim to execute PC actions: no action tools are connected. "
                "Do not invent current facts. This is a single turn without persistent history.",
            },
            {"role": "user", "content": text[:4000]},
        ],
        "options": {"num_ctx": 2048, "num_predict": 180, "temperature": 0.5},
        "keep_alive": "2m",
    }
    result = []
    size = 0
    deadline = time.monotonic() + 60
    try:
        with httpx.Client(
            timeout=httpx.Timeout(12, connect=3),
            trust_env=False,
            follow_redirects=False,
            transport=transport,
        ) as client:
            with client.stream("POST", base + "/api/chat", json=payload) as response:
                if response.status_code != 200:
                    raise ValueError("Ollama rejected the request. Check the installed model.")
                for line in response.iter_lines():
                    if cancel.is_set():
                        return ""
                    if time.monotonic() > deadline:
                        raise ValueError("Local AI exceeded its response time limit.")
                    size += len(line)
                    if size > 100_000:
                        raise ValueError("Local AI returned an excessive response.")
                    if not line:
                        continue
                    value = json.loads(line)
                    if value.get("error"):
                        raise ValueError("Ollama reported an inference error. Check the model.")
                    content = value.get("message", {}).get("content", "")
                    if not isinstance(content, str):
                        raise ValueError("Ollama returned an invalid response.")
                    result.append(content)
                    if value.get("done"):
                        break
    except httpx.HTTPError as exc:
        raise ValueError(
            "Ollama is unavailable. Start Ollama and install the configured model."
        ) from exc
    except (json.JSONDecodeError, AttributeError) as exc:
        raise ValueError("Ollama returned an invalid response.") from exc
    reply = "".join(result).strip()
    if not reply:
        raise ValueError("Local AI did not produce a spoken reply.")
    return reply[:4000]
