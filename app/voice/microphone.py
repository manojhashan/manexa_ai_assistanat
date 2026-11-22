"""Bounded in-memory microphone capture; no files and no always-on recording."""

import time

from PySide6.QtCore import QObject, QTimer, Signal, Slot
from PySide6.QtMultimedia import QAudio, QAudioFormat, QAudioSource, QMediaDevices

from app.speech.audio import InputConverter, pcm_level


class MicrophoneCapture(QObject):
    active = Signal()
    captured = Signal(bytes)
    failed = Signal(str)

    def __init__(self, parent=None):
        super().__init__(parent)
        self._source = self._device = None
        self._converter = None
        self._pcm = bytearray()
        self._started = self._last_voice = 0.0
        self._heard = False
        self._timer = QTimer(self)
        self._timer.setInterval(80)
        self._timer.timeout.connect(self._check_end)

    def start(self, device_id=""):
        self.stop()
        devices = QMediaDevices.audioInputs()
        device = next((item for item in devices if bytes(item.id()).hex() == device_id), None)
        if device_id and device is None:
            self.failed.emit("The selected microphone is no longer available.")
            return
        device = device if device is not None else QMediaDevices.defaultAudioInput()
        if device.isNull():
            self.failed.emit("No microphone is available.")
            return
        audio_format = device.preferredFormat()
        if not device.isFormatSupported(audio_format):
            self.failed.emit("This microphone's preferred PCM format is unavailable.")
            return
        names = {
            QAudioFormat.SampleFormat.Int16: "int16",
            QAudioFormat.SampleFormat.Int32: "int32",
            QAudioFormat.SampleFormat.Float: "float",
            QAudioFormat.SampleFormat.UInt8: "uint8",
        }
        kind = names.get(audio_format.sampleFormat())
        if kind is None:
            self.failed.emit("This microphone uses an unsupported sample format.")
            return
        self._converter = InputConverter(
            audio_format.sampleRate(), audio_format.channelCount(), kind
        )
        self._source = QAudioSource(device, audio_format, self)
        self._source.setBufferSize(
            int(audio_format.sampleRate() * audio_format.bytesPerFrame() * 0.1)
        )
        self._source.stateChanged.connect(self._state)
        self._device = self._source.start()
        if not self._device or self._source.error() != QAudio.Error.NoError:
            self.stop()
            self.failed.emit("Microphone access failed. Check Windows microphone permissions.")
            return
        self._device.readyRead.connect(self._read)
        self._started = time.monotonic()
        self._last_voice = self._started
        self._heard = False
        self._timer.start()

    @Slot(object)
    def _state(self, state):
        if state == QAudio.State.ActiveState:
            self.active.emit()
        elif state == QAudio.State.StoppedState and self._source:
            if self._source.error() != QAudio.Error.NoError:
                self.stop()
                self.failed.emit("The microphone stopped or was disconnected.")

    @Slot()
    def _read(self):
        if not self._device:
            return
        chunk = self._converter.convert(bytes(self._device.readAll()))
        # Hard memory bound even if the Qt event loop was temporarily busy.
        remaining = max(0, 16000 * 2 * 16 - len(self._pcm))
        chunk = chunk[:remaining]
        self._pcm.extend(chunk)
        if pcm_level(chunk) > 0.07:
            self._heard = True
            self._last_voice = time.monotonic()

    @Slot()
    def _check_end(self):
        now = time.monotonic()
        if (self._heard and now - self._last_voice > 0.9) or now - self._started > 15:
            pcm, heard = bytes(self._pcm), self._heard
            self.stop()
            if heard:
                self.captured.emit(pcm)
            else:
                self.failed.emit("No speech was detected. The microphone has been released.")

    @Slot()
    def stop(self):
        self._timer.stop()
        if self._source:
            self._source.blockSignals(True)
            self._source.stop()
            self._source.deleteLater()
        self._source = self._device = None
        self._converter = None
        self._pcm.clear()
