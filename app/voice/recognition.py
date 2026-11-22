"""Optional real Faster-Whisper adapter, loading local weights only."""

import importlib.util
from pathlib import Path
from threading import Lock


def check_recognition(model_path: str):
    if not model_path or not (Path(model_path) / "model.bin").is_file():
        raise ValueError("Select a local Faster-Whisper model folder in Voice settings first.")
    if importlib.util.find_spec("faster_whisper") is None:
        raise ValueError("Install requirements-voice.txt to enable local speech recognition.")


class LocalRecognizer:
    def __init__(self):
        self._model = None
        self._path = ""
        self._lock = Lock()

    def transcribe(self, pcm: bytes, model_path: str, language: str, cancel):
        check_recognition(model_path)
        import numpy as np
        from faster_whisper import WhisperModel

        with self._lock:
            if cancel.is_set():
                return ""
            if self._path != model_path:
                self._model = WhisperModel(
                    model_path,
                    device="cpu",
                    compute_type="int8",
                    cpu_threads=4,
                    num_workers=1,
                    local_files_only=True,
                )
                self._path = model_path
            if cancel.is_set():
                return ""
            audio = np.frombuffer(pcm, dtype="<i2").astype(np.float32) / 32768.0
            segments, _ = self._model.transcribe(
                audio,
                language=None if language == "auto" else language,
                beam_size=3,
                vad_filter=True,
                condition_on_previous_text=False,
            )
            result = []
            for segment in segments:
                if cancel.is_set():
                    return ""
                if segment.no_speech_prob < 0.65 and segment.avg_logprob > -1.2:
                    result.append(segment.text)
            return " ".join(result).strip()
