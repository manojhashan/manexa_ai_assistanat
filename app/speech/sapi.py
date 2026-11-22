"""SAPI memory-stream synthesis on a worker, without XML or file interpretation."""

import locale
import sys
import time
from dataclasses import dataclass
from threading import Event

from app.speech.audio import SpeechAudio


class SpeechError(RuntimeError):
    pass


class SpeechCancelled(SpeechError):
    pass


@dataclass(frozen=True)
class VoiceInfo:
    id: str
    name: str
    languages: tuple[str, ...]


def language_runs(text: str, language: str = "auto") -> list[tuple[str, str]]:
    """Switch by script; romanized Sinhala needs an explicit language hint."""
    if not isinstance(text, str) or not text.strip() or len(text) > 4000:
        raise SpeechError("Speech requires between 1 and 4000 characters.")
    if language not in ("auto", "en", "si"):
        raise SpeechError("Unsupported speech language.")
    runs: list[tuple[str, str]] = []
    current = "si" if language == "si" else "en"
    for char in text:
        if "\u0d80" <= char <= "\u0dff":
            detected = "si"
        elif char.isascii() and char.isalpha():
            detected = "si" if language == "si" else "en"
        elif char.isalpha():
            raise SpeechError("This speech adapter supports Sinhala and English text only.")
        else:
            detected = current
        if runs and runs[-1][1] == detected:
            runs[-1] = (runs[-1][0] + char, detected)
        else:
            runs.append((char, detected))
        current = detected
    return [(value, lang) for value, lang in runs if value.strip()]


def _voice_info(token) -> VoiceInfo:
    languages = []
    for value in token.GetAttribute("Language").split(";"):
        try:
            name = locale.windows_locale.get(int(value, 16), "")
            if name:
                languages.append(name.split("_")[0])
        except ValueError:
            continue
    return VoiceInfo(token.Id, token.GetDescription(), tuple(languages))


def _com():
    if sys.platform != "win32":
        raise SpeechError("Windows SAPI speech requires Windows.")
    try:
        import comtypes
        from comtypes.client import CreateObject
    except ImportError as exc:
        raise SpeechError("Install the runtime dependencies to enable Windows speech.") from exc
    return comtypes, CreateObject


def list_voices() -> list[VoiceInfo]:
    comtypes, create = _com()
    comtypes.CoInitialize()
    try:
        voice = create("SAPI.SpVoice", dynamic=True)
        tokens = voice.GetVoices()
        return [_voice_info(tokens.Item(i)) for i in range(tokens.Count)]
    except Exception as exc:
        raise SpeechError("Windows speech voices could not be enumerated.") from exc
    finally:
        comtypes.CoUninitialize()


def synthesize(text: str, *, voice_id="", rate=0, language="auto", cancel=None) -> SpeechAudio:
    cancel = cancel if cancel is not None else Event()
    runs = language_runs(text, language)
    comtypes, create = _com()
    comtypes.CoInitialize()
    voice = stream = None
    try:
        voice = create("SAPI.SpVoice", dynamic=True)
        tokens = voice.GetVoices()
        available = [(tokens.Item(i), _voice_info(tokens.Item(i))) for i in range(tokens.Count)]
        if voice_id and not any(info.id == voice_id for _, info in available):
            raise SpeechError("The selected Windows voice is no longer installed.")
        selected = []
        default_id = voice_id or voice.Voice.Id
        for _, lang in runs:
            matches = [(token, info) for token, info in available if lang in info.languages]
            if not matches:
                name = "Sinhala" if lang == "si" else "English"
                raise SpeechError(
                    f"No installed offline {name} SAPI voice. No substitute was used."
                )
            selected.append(
                next((token for token, info in matches if info.id == default_id), matches[0][0])
            )
        stream = create("SAPI.SpMemoryStream", dynamic=True)
        stream.Format.Type = 22  # SAFT22kHz16BitMono: verified 22050 Hz, signed int16 mono.
        voice.AudioOutputStream = stream
        voice.Rate = max(-5, min(5, int(rate)))
        deadline = time.monotonic() + 30
        for (value, _), token in zip(runs, selected, strict=True):
            if cancel.is_set():
                raise SpeechCancelled("Speech cancelled.")
            voice.Voice = token
            voice.Speak(value, 1 | 16)  # Async, plain text; never XML or a filename.
            while not voice.WaitUntilDone(25):
                if cancel.is_set() or time.monotonic() > deadline:
                    voice.Speak("", 1 | 2 | 16)
                    raise SpeechCancelled("Speech cancelled or synthesis timed out.")
        if cancel.is_set():
            raise SpeechCancelled("Speech cancelled.")
        pcm = bytes(stream.GetData())
        if not pcm or len(pcm) > 16_000_000:
            raise SpeechError("Speech synthesis returned empty or excessive audio.")
        return SpeechAudio(pcm)
    except SpeechError:
        raise
    except Exception as exc:
        raise SpeechError("Windows speech synthesis failed. Check the installed voice.") from exc
    finally:
        voice = stream = None
        comtypes.CoUninitialize()
