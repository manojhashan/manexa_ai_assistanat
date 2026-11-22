"""Connect actual capture, recognition, inference and playback to the existing scene states."""

from threading import Event

from PySide6.QtCore import QObject, QThreadPool, Signal, Slot

from app.ai.local_reply import local_reply
from app.core.state import AssistantState
from app.services.tasks import Task
from app.speech.service import SpeechService
from app.voice.microphone import MicrophoneCapture
from app.voice.recognition import LocalRecognizer, check_recognition


class VoiceSession(QObject):
    state_changed = Signal(object)
    level_changed = Signal(float)
    failed = Signal(str)

    def __init__(self, parent=None):
        super().__init__(parent)
        self.speech = SpeechService(self)
        self.capture = MicrophoneCapture(self)
        self.recognizer = LocalRecognizer()
        self._generation = 0
        self._cancel = Event()
        self._settings = None
        self._jobs = {}
        self.speech.state_changed.connect(self.state_changed)
        self.speech.level_changed.connect(self.level_changed)
        self.speech.failed.connect(self.failed)
        self.capture.active.connect(lambda: self.state_changed.emit(AssistantState.LISTENING))
        self.capture.captured.connect(self._captured)
        self.capture.failed.connect(self._capture_failed)

    def preview(self, text, settings):
        self.stop()
        self.speech.speak(text, settings)

    def listen(self, settings):
        self.stop()  # Flush audio before any model/device readiness check.
        try:
            check_recognition(settings.asr_model_path)
        except ValueError as exc:
            self.failed.emit(str(exc))
            return
        self._settings = settings
        self.capture.start(settings.microphone_id)

    @Slot(bytes)
    def _captured(self, pcm):
        self.state_changed.emit(AssistantState.THINKING)
        generation, cancel, settings = self._generation, self._cancel, self._settings

        def process():
            try:
                text = self.recognizer.transcribe(
                    pcm, settings.asr_model_path, settings.speech_language, cancel
                )
                if cancel.is_set():
                    return generation, None, None
                if not text:
                    return generation, None, "No intelligible speech was recognized."
                reply = local_reply(text, settings, cancel)
                return generation, reply, None
            except ValueError as exc:
                return generation, None, str(exc)
            except Exception:
                return (
                    generation,
                    None,
                    "Local recognition failed. Check the model and dependencies.",
                )

        task = Task(process)
        self._jobs[generation] = task
        task.signals.finished.connect(self._processed)
        task.signals.failed.connect(self._capture_failed)
        QThreadPool.globalInstance().start(task)

    @Slot(object)
    def _processed(self, payload):
        generation, reply, error = payload
        self._jobs.pop(generation, None)
        if generation != self._generation:
            return
        if error:
            self.state_changed.emit(AssistantState.IDLE)
            self.failed.emit(error)
        elif reply:
            self.speech.speak(reply, self._settings)

    @Slot(str)
    def _capture_failed(self, message):
        self.state_changed.emit(AssistantState.IDLE)
        self.failed.emit(message)

    @Slot()
    def stop(self):
        self._generation += 1
        self._cancel.set()
        self._cancel = Event()
        self.capture.stop()
        self.speech.stop()
        self.level_changed.emit(0.0)
        self.state_changed.emit(AssistantState.IDLE)
