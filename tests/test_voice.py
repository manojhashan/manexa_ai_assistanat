import math
from array import array
from dataclasses import replace
from threading import Event

import httpx
import pytest

from app.ai.local_reply import local_reply
from app.config.settings import Settings
from app.speech.audio import InputConverter, SpeechAudio, output_pcm, pcm_level
from app.speech.sapi import SpeechError, language_runs
from app.voice.recognition import check_recognition


def test_pcm_envelope_comes_from_samples_not_a_speaking_flag():
    samples = array("h", [int(6000 * math.sin(i * 0.2)) for i in range(2205)])
    audio = SpeechAudio(bytes(4410) + samples.tobytes() + bytes(4410))
    assert audio.level_at(0) == 0
    assert audio.level_at(120000) > 0.4
    assert audio.level_at(280000) == 0
    assert audio.level_at(10000000) == 0
    assert pcm_level(b"\0") == 0


def test_native_float_stereo_conversion_preserves_clock_and_amplitude_across_chunks():
    original = SpeechAudio(array("h", [6000] * 2205).tobytes())
    native = output_pcm(original, 48000, 2, "float")
    assert len(native) == 4800 * 2 * 4
    converter = InputConverter(48000, 2, "float")
    result = b"".join(converter.convert(native[i : i + 53]) for i in range(0, len(native), 53))
    samples = array("h")
    samples.frombytes(result)
    assert abs(len(samples) - 1600) <= 1
    assert all(abs(value - 6000) <= 2 for value in samples)


def test_script_detection_preserves_mixed_language_text():
    text = "Hello, ආයුබෝවන්. Welcome back."
    runs = language_runs(text)
    assert "".join(value for value, _ in runs) == text
    assert [lang for _, lang in runs] == ["en", "si", "en"]
    assert language_runs("kohomada", "si") == [("kohomada", "si")]


def test_unsupported_language_and_oversized_speech_fail_honestly():
    for value in ("你好", "", "x" * 4001):
        with pytest.raises(SpeechError):
            language_runs(value)


def test_legacy_settings_pick_up_new_defaults_without_losing_ai_configuration(tmp_path):
    import json
    import sqlite3

    from app.config.store import SettingsStore

    store = SettingsStore(tmp_path / "settings.db")
    old = {
        "provider": "ollama",
        "mode": "offline",
        "base_url": "http://localhost:11434",
        "model": "custom-local-model",
        "quality": "performance",
        "glow": 0.7,
        "fullscreen": False,
        "motion": False,
    }
    with sqlite3.connect(store.path) as connection:
        connection.execute("INSERT INTO settings VALUES(1,1,?)", (json.dumps(old),))
    loaded = store.load()
    assert loaded.model == "custom-local-model" and loaded.quality == "performance"
    assert loaded.particle_density == 1 and loaded.voice_rate == 0
    store.save(replace(loaded, particle_density=0.5, advanced_effects=False, voice_rate=-1))
    assert store.load().advanced_effects is False


@pytest.mark.parametrize(
    "changes",
    [
        {"particle_density": float("nan")},
        {"animation_speed": 100},
        {"advanced_effects": "yes"},
        {"voice_rate": 6},
        {"voice_engine": "mock"},
    ],
)
def test_invalid_effect_or_voice_preferences_are_rejected(changes):
    with pytest.raises(ValueError):
        replace(Settings(), **changes).validate()


def test_missing_recognition_model_is_not_downloaded_or_simulated():
    with pytest.raises(ValueError, match="local Faster-Whisper"):
        check_recognition("")


def test_local_inference_stream_is_stateless_and_has_no_action_execution():
    def respond(request):
        import json

        payload = json.loads(request.content)
        assert request.url == "http://127.0.0.1:11434/api/chat"
        assert len(payload["messages"]) == 2
        assert payload["options"]["num_ctx"] == 2048
        assert "tools" not in payload
        return httpx.Response(
            200,
            content=(
                b'{"message":{"content":"A real "},"done":false}\n'
                b'{"message":{"content":"stream."},"done":true}\n'
            ),
        )

    assert (
        local_reply("hello", Settings(), Event(), httpx.MockTransport(respond)) == "A real stream."
    )


def test_local_voice_pipeline_rejects_remote_endpoint_even_in_online_mode():
    with pytest.raises(ValueError, match="loopback"):
        local_reply(
            "hello", replace(Settings(), mode="online", base_url="https://example.com"), Event()
        )


def test_sapi_receives_plain_text_and_never_reads_markup_files(monkeypatch):
    from types import SimpleNamespace

    from app.speech import sapi

    calls = []
    token = SimpleNamespace(
        Id="voice-en", GetDescription=lambda: "English test voice", GetAttribute=lambda _: "409"
    )
    tokens = SimpleNamespace(Count=1, Item=lambda _: token)
    voice = SimpleNamespace(
        Voice=token,
        GetVoices=lambda: tokens,
        Speak=lambda text, flags: calls.append((text, flags)),
        WaitUntilDone=lambda _: True,
    )
    stream = SimpleNamespace(Format=SimpleNamespace(Type=None), GetData=lambda: bytes(1000))
    fake_com = SimpleNamespace(CoInitialize=lambda: None, CoUninitialize=lambda: None)
    monkeypatch.setattr(
        sapi,
        "_com",
        lambda: (fake_com, lambda name, **_: voice if name == "SAPI.SpVoice" else stream),
    )
    text = "<audio src='file:///private.txt'>hello</audio>"
    sapi.synthesize(text)
    assert calls == [(text, 17)]
    assert stream.Format.Type == 22
    calls.clear()
    with pytest.raises(SpeechError, match="Sinhala"):
        sapi.synthesize("ආයුබෝවන්")
    assert calls == []
