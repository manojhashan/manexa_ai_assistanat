"""PCM measurements shared by playback, microphone activity and tests."""

import math
import sys
from array import array
from dataclasses import dataclass


def pcm_level(data: bytes) -> float:
    samples = array("h")
    samples.frombytes(data[: len(data) // 2 * 2])
    if sys.byteorder != "little":
        samples.byteswap()
    if not samples:
        return 0.0
    rms = math.sqrt(sum(value * value for value in samples) / len(samples)) / 32768
    return min(1.0, rms * 5.0)


@dataclass(frozen=True)
class SpeechAudio:
    pcm: bytes
    sample_rate: int = 22050

    @property
    def duration(self) -> float:
        return len(self.pcm) / (self.sample_rate * 2)

    def level_at(self, microseconds: int) -> float:
        start = max(0, int(microseconds * self.sample_rate / 1_000_000)) * 2
        count = max(2, self.sample_rate // 40 * 2)
        return pcm_level(self.pcm[start : start + count])


def output_pcm(audio: SpeechAudio, rate: int, channels: int, kind: str) -> bytes:
    """Resample on the synthesis worker to the real device's preferred format."""
    source = array("h")
    source.frombytes(audio.pcm)
    if sys.byteorder != "little":
        source.byteswap()
    codes = {"int16": "h", "int32": "i", "float": "f", "uint8": "B"}
    if kind not in codes or not 8000 <= rate <= 192000 or not 1 <= channels <= 8:
        raise ValueError("Unsupported audio output format.")
    count = int(len(source) * rate / audio.sample_rate)
    result = array(codes[kind])
    if count * result.itemsize * channels > 64_000_000:
        raise ValueError("Speech is too long for the bounded playback buffer.")
    step = audio.sample_rate / rate
    for i in range(count):
        position = i * step
        index = min(int(position), len(source) - 1)
        fraction = position - index
        value = (
            source[index] * (1 - fraction) + source[min(index + 1, len(source) - 1)] * fraction
        ) / 32768
        sample = (
            value
            if kind == "float"
            else int(value * 32767)
            if kind == "int16"
            else int(value * 2147483647)
            if kind == "int32"
            else int((value + 1) * 127.5)
        )
        result.extend([sample] * channels)
    if sys.byteorder != "little" and result.itemsize > 1:
        result.byteswap()
    return result.tobytes()


class InputConverter:
    """Stateful native-device PCM → 16 kHz mono int16, without numpy or files."""

    def __init__(self, rate: int, channels: int, kind: str):
        self.rate, self.channels, self.kind = rate, channels, kind
        self._samples = []
        self._position = 0.0
        self._partial = b""

    def convert(self, data: bytes) -> bytes:
        code = {"int16": "h", "int32": "i", "float": "f", "uint8": "B"}[self.kind]
        values = array(code)
        frame_size = values.itemsize * self.channels
        data = self._partial + data
        length = len(data) // frame_size * frame_size
        self._partial = data[length:]
        values.frombytes(data[:length])
        if sys.byteorder != "little" and values.itemsize > 1:
            values.byteswap()
        scale = {"int16": 32768, "int32": 2147483648, "float": 1, "uint8": 128}[self.kind]
        for i in range(0, len(values), self.channels):
            mean = sum(values[i : i + self.channels]) / self.channels
            value = (mean - 128) / scale if self.kind == "uint8" else mean / scale
            self._samples.append(value if math.isfinite(value) else 0.0)
        result = array("h")
        step = self.rate / 16000
        while self._position + 1 < len(self._samples):
            index = int(self._position)
            fraction = self._position - index
            value = self._samples[index] * (1 - fraction) + self._samples[index + 1] * fraction
            result.append(int(max(-1.0, min(1.0, value)) * 32767))
            self._position += step
        consumed = min(int(self._position), len(self._samples))
        self._samples = self._samples[consumed:]
        self._position -= consumed
        if sys.byteorder != "little":
            result.byteswap()
        return result.tobytes()
