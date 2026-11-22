"""Real PCM playback clock drives facial animation; reset flushes interrupted audio."""

from threading import Event

from PySide6.QtCore import (
    QBuffer,
    QByteArray,
    QIODevice,
    QObject,
    QThreadPool,
    QTimer,
    Signal,
    Slot,
)
from PySide6.QtMultimedia import QAudio, QAudioFormat, QAudioSink, QMediaDevices

from app.config.settings import Settings
from app.core.state import AssistantState
from app.services.tasks import Task
from app.speech.audio import SpeechAudio, output_pcm
from app.speech.sapi import SpeechCancelled, SpeechError, synthesize


class SpeechService(QObject):
    state_changed = Signal(object)
    level_changed = Signal(float)
    failed = Signal(str)
    finished = Signal()

    def __init__(self, parent=None, synthesizer=synthesize):
        super().__init__(parent)
        self._synthesizer = synthesizer
        self._generation = 0
        self._cancel = Event()
        self._jobs = {}
        self._sink = None
        self._buffer = None
        self._audio = None
        self._stopping = False
        self._state = AssistantState.IDLE
        self._timer = QTimer(self)
        self._timer.setInterval(25)
        self._timer.timeout.connect(self._tick)

    @property
    def state(self):
        return self._state

    def _set_state(self, state):
        if state != self._state:
            self._state = state
            self.state_changed.emit(state)

    def speak(self, text: str, settings: Settings):
        self.stop()
        generation, cancel = self._generation, self._cancel
        if QMediaDevices.defaultAudioOutput().isNull():
            self.failed.emit("No audio output device is available.")
            return
        output_format = QMediaDevices.defaultAudioOutput().preferredFormat()
        names = {
            QAudioFormat.SampleFormat.Int16: "int16",
            QAudioFormat.SampleFormat.Int32: "int32",
            QAudioFormat.SampleFormat.Float: "float",
            QAudioFormat.SampleFormat.UInt8: "uint8",
        }
        kind = names.get(output_format.sampleFormat())
        if kind is None:
            self.failed.emit("Unsupported audio output sample format.")
            return
        rate, channels = output_format.sampleRate(), output_format.channelCount()
        self._set_state(AssistantState.THINKING)

        def prepare():
            try:
                result = self._synthesizer(
                    text,
                    voice_id=settings.voice_id,
                    rate=settings.voice_rate,
                    language=settings.speech_language,
                    cancel=cancel,
                )
                result = (result, output_pcm(result, rate, channels, kind), rate, channels, kind)
            except SpeechCancelled:
                result = None
            except SpeechError as exc:
                result = str(exc)
            except Exception:
                result = "Could not prepare speech for the selected audio output."
            return generation, result

        task = Task(prepare)
        self._jobs[generation] = task
        task.signals.finished.connect(self._prepared)
        task.signals.failed.connect(self._worker_failed)
        QThreadPool.globalInstance().start(task)

    @Slot(object)
    def _prepared(self, payload):
        generation, result = payload
        self._jobs.pop(generation, None)
        if generation != self._generation or self._cancel.is_set():
            return
        if not isinstance(result, tuple) or not isinstance(result[0], SpeechAudio):
            self._set_state(AssistantState.IDLE)
            if result:
                self.failed.emit(result)
            return
        audio, playback, rate, channels, kind = result
        self._audio = audio
        audio_format = QAudioFormat()
        audio_format.setSampleRate(rate)
        audio_format.setChannelCount(channels)
        formats = {
            "int16": QAudioFormat.SampleFormat.Int16,
            "int32": QAudioFormat.SampleFormat.Int32,
            "float": QAudioFormat.SampleFormat.Float,
            "uint8": QAudioFormat.SampleFormat.UInt8,
        }
        audio_format.setSampleFormat(formats[kind])
        device = QMediaDevices.defaultAudioOutput()
        if not device.isFormatSupported(audio_format):
            self.stop()
            self.failed.emit("The audio output does not support the synthesized PCM format.")
            return
        self._buffer = QBuffer(self)
        self._buffer.setData(QByteArray(playback))
        self._buffer.open(QIODevice.OpenModeFlag.ReadOnly)
        self._sink = QAudioSink(device, audio_format, self)
        self._sink.setBufferSize(int(audio_format.bytesPerFrame() * rate * 0.06))
        self._sink.stateChanged.connect(self._audio_state)
        self._sink.start(self._buffer)
        if self._sink and self._sink.error() != QAudio.Error.NoError:
            self.stop()
            self.failed.emit("Audio playback could not start.")
            return
        if self._sink is not None:
            self._timer.start()

    @Slot(object)
    def _audio_state(self, state):
        if self._stopping:
            return
        if state == QAudio.State.ActiveState:
            self._set_state(AssistantState.SPEAKING)
        elif state == QAudio.State.IdleState:
            self.stop()
            self.finished.emit()
        elif state == QAudio.State.StoppedState and self._sink:
            if self._sink.error() != QAudio.Error.NoError:
                self.stop()
                self.failed.emit("Audio output was disconnected or playback failed.")

    @Slot()
    def _tick(self):
        if self._sink and self._audio and self._state == AssistantState.SPEAKING:
            self.level_changed.emit(self._audio.level_at(self._sink.processedUSecs()))

    @Slot(str)
    def _worker_failed(self, _message):
        self.stop()
        self.failed.emit("The speech worker could not complete synthesis.")

    @Slot()
    def stop(self):
        self._generation += 1
        self._cancel.set()
        self._cancel = Event()
        self._stopping = True
        self._timer.stop()
        if self._sink:
            self._sink.blockSignals(True)
            self._sink.reset()  # Stop immediately and discard queued device audio.
            self._sink.deleteLater()
            self._sink = None
        if self._buffer:
            self._buffer.close()
            self._buffer.deleteLater()
            self._buffer = None
        self._audio = None
        self.level_changed.emit(0.0)
        self._set_state(AssistantState.IDLE)
        self._stopping = False
