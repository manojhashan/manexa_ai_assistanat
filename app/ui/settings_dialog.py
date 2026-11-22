"""Functional preferences; future device features are explicitly marked unavailable."""

from dataclasses import replace

from PySide6.QtCore import QThreadPool, Signal, Slot
from PySide6.QtMultimedia import QMediaDevices
from PySide6.QtWidgets import (
    QCheckBox,
    QComboBox,
    QDialog,
    QDialogButtonBox,
    QDoubleSpinBox,
    QFileDialog,
    QFormLayout,
    QHBoxLayout,
    QLabel,
    QLineEdit,
    QMessageBox,
    QPushButton,
    QScrollArea,
    QSpinBox,
    QTabWidget,
    QVBoxLayout,
    QWidget,
)

from app import __version__
from app.ai.probe import probe_provider
from app.config.settings import PROVIDER_DEFAULTS, Settings
from app.config.store import SettingsStore
from app.security.credentials import CredentialError, CredentialVault
from app.services.hardware import hardware_info
from app.services.tasks import Task
from app.speech.sapi import SpeechError, list_voices

STYLE = """
QDialog { background: #080f19; color: #d4e7f0; }
QWidget { color: #d4e7f0; font-family: 'Segoe UI'; font-size: 13px; }
QTabWidget::pane { border: 1px solid #1d303e; border-radius: 8px; }
QTabBar::tab { background: #0e1925; padding: 11px 16px; color: #7b9bab; }
QTabBar::tab:selected { color: #6de8ff; background: #132734; }
QLineEdit, QComboBox, QDoubleSpinBox {
    background: #0c1824; border: 1px solid #284150; border-radius: 5px;
    padding: 7px; min-height: 20px; selection-background-color: #14576f;
}
QComboBox QAbstractItemView { background: #0c1824; selection-background-color: #14576f; }
QPushButton { background: #132c3b; border: 1px solid #29546a; border-radius: 5px;
    padding: 8px 15px; }
QPushButton:hover { background: #1b4053; border-color: #4fabc5; }
QPushButton:disabled { color: #54707d; border-color: #233340; }
QCheckBox { spacing: 10px; padding: 5px 0; }
QLabel[muted="true"] { color: #82a0b0; }
QLabel[title="true"] { color: #e0f9ff; font-size: 23px; font-weight: 600; }
"""


def note(text: str) -> QLabel:
    label = QLabel(text)
    label.setWordWrap(True)
    label.setProperty("muted", True)
    return label


class SettingsDialog(QDialog):
    applied = Signal(object)
    preview_requested = Signal(str, object)
    stop_requested = Signal()
    reconstruct_requested = Signal()

    def __init__(self, store: SettingsStore, settings: Settings, parent=None):
        super().__init__(parent)
        self.store = store
        self.current = settings
        self.vault = CredentialVault()
        self._task = None
        self._voice_task = None
        self.setWindowTitle("MANEXA · Settings")
        self.setMinimumSize(640, 550)
        self.resize(720, 620)
        self.setStyleSheet(STYLE)
        self.setModal(True)
        root = QVBoxLayout(self)
        root.setContentsMargins(28, 24, 28, 20)
        root.setSpacing(18)
        title = QLabel("MANEXA")
        title.setProperty("title", True)
        root.addWidget(title)
        root.addWidget(note("Your Intelligent Personal Assistant"))
        tabs = QTabWidget()
        root.addWidget(tabs, 1)
        tabs.addTab(self._ai_tab(), "AI")
        tabs.addTab(self._scroll(self._appearance_tab()), "Appearance")
        tabs.addTab(self._scroll(self._devices_tab()), "Voice & camera")
        tabs.addTab(self._system_tab(), "System & privacy")
        self.status = note("")
        self.status.setMinimumHeight(38)
        root.addWidget(self.status)
        buttons = QDialogButtonBox(
            QDialogButtonBox.StandardButton.Save | QDialogButtonBox.StandardButton.Cancel
        )
        buttons.accepted.connect(self._save)
        buttons.rejected.connect(self.reject)
        root.addWidget(buttons)

    @staticmethod
    def _scroll(widget):
        area = QScrollArea()
        area.setWidgetResizable(True)
        area.setWidget(widget)
        area.setStyleSheet("QScrollArea { border: 0; background: #080f19; }")
        return area

    def _ai_tab(self) -> QWidget:
        tab = QWidget()
        layout = QVBoxLayout(tab)
        layout.setContentsMargins(20, 20, 20, 20)
        form = QFormLayout()
        form.setSpacing(13)
        self.provider = QComboBox()
        for label, value in (
            ("Ollama · free, local", "ollama"),
            ("OpenAI", "openai"),
            ("Google Gemini", "gemini"),
            ("Anthropic Claude", "claude"),
            ("Custom OpenAI-compatible", "custom"),
        ):
            self.provider.addItem(label, value)
        self.provider.setCurrentIndex(self.provider.findData(self.current.provider))
        self.mode = QComboBox()
        for label, value in (
            ("Offline · loopback Ollama only", "offline"),
            ("Online", "online"),
            ("Automatic fallback (Phase 9)", "auto"),
        ):
            self.mode.addItem(label, value)
        self.mode.setCurrentIndex(self.mode.findData(self.current.mode))
        self.base_url = QLineEdit(self.current.base_url)
        self.model = QLineEdit(self.current.model)
        self.model.setPlaceholderText("Enter the model ID offered by your provider")
        self.key = QLineEdit()
        self.key.setEchoMode(QLineEdit.EchoMode.Password)
        self.key.setPlaceholderText("Leave blank to keep the stored key")
        self.key.setMaxLength(8192)
        form.addRow("Provider", self.provider)
        form.addRow("Preference", self.mode)
        form.addRow("Base URL", self.base_url)
        form.addRow("Model", self.model)
        form.addRow("API key", self.key)
        layout.addLayout(form)
        actions = QHBoxLayout()
        self.test_button = QPushButton("Test connection")
        self.test_button.clicked.connect(self._test)
        self.forget_button = QPushButton("Remove stored key")
        self.forget_button.clicked.connect(self._forget_key)
        actions.addWidget(self.test_button)
        actions.addWidget(self.forget_button)
        actions.addStretch()
        layout.addLayout(actions)
        layout.addWidget(
            note(
                "Connection testing lists real models; it does not generate a reply. "
                "Keys are stored only in Windows Credential Manager, scoped to this endpoint. "
                "Live voice replies use local Ollama. Cloud generation and automatic fallback "
                "are not active."
            )
        )
        layout.addStretch()
        self.provider.currentIndexChanged.connect(self._provider_changed)
        return tab

    @Slot()
    def _provider_changed(self):
        provider = self.provider.currentData()
        endpoint, model = PROVIDER_DEFAULTS[provider]
        self.base_url.setText(endpoint)
        self.model.setText(model)
        self.key.clear()
        self.mode.setCurrentIndex(
            self.mode.findData("offline" if provider == "ollama" else "online")
        )

    def _appearance_tab(self) -> QWidget:
        tab = QWidget()
        form = QFormLayout(tab)
        form.setContentsMargins(20, 20, 20, 20)
        form.setSpacing(18)
        self.fullscreen = QCheckBox("Start in fullscreen")
        self.fullscreen.setChecked(self.current.fullscreen)
        self.motion = QCheckBox("Breathing, scanning and ambient particles")
        self.motion.setChecked(self.current.motion)
        self.quality = QComboBox()
        for label, value in (
            ("Performance · 30 FPS / 1× pixels", "performance"),
            ("Balanced · 45 FPS / up to 1.5× pixels", "balanced"),
            ("High · 60 FPS / up to 2× pixels", "high"),
        ):
            self.quality.addItem(label, value)
        self.quality.setCurrentIndex(self.quality.findData(self.current.quality))
        self.glow = QDoubleSpinBox()
        self.glow.setRange(0.3, 1.8)
        self.glow.setSingleStep(0.1)
        self.glow.setValue(self.current.glow)
        self.particle_density = QDoubleSpinBox()
        self.particle_density.setRange(0.25, 2.0)
        self.particle_density.setSingleStep(0.25)
        self.particle_density.setValue(self.current.particle_density)
        self.animation_speed = QDoubleSpinBox()
        self.animation_speed.setRange(0.25, 2.0)
        self.animation_speed.setSingleStep(0.25)
        self.animation_speed.setValue(self.current.animation_speed)
        self.advanced_effects = QCheckBox("Particle dissolution and reconstruction")
        self.advanced_effects.setChecked(self.current.advanced_effects)
        form.addRow("Display", self.fullscreen)
        form.addRow("Ambient animation", self.motion)
        form.addRow("Hologram quality", self.quality)
        form.addRow("Hologram brightness", self.glow)
        form.addRow("Particle density", self.particle_density)
        form.addRow("Animation speed", self.animation_speed)
        form.addRow("Advanced effects", self.advanced_effects)
        reconstruct = QPushButton("Dissolve and reconstruct · Ctrl+D")
        reconstruct.clicked.connect(self.reconstruct_requested)
        form.addRow(reconstruct)
        form.addRow(
            note("Save applies appearance immediately. F11 toggles fullscreen; Esc leaves it.")
        )
        return tab

    def _devices_tab(self) -> QWidget:
        tab = QWidget()
        layout = QVBoxLayout(tab)
        layout.setContentsMargins(20, 20, 20, 20)
        layout.setSpacing(18)
        form = QFormLayout()
        self.voice_engine = QComboBox()
        self.voice_engine.addItem("Windows SAPI · offline PCM", "sapi")
        self.voice_id = QComboBox()
        self.voice_id.addItem("Preserve Windows default voice", "")
        if self.current.voice_id:
            self.voice_id.addItem("Saved voice · refresh to verify", self.current.voice_id)
            self.voice_id.setCurrentIndex(1)
        self.voice_rate = QSpinBox()
        self.voice_rate.setRange(-5, 5)
        self.voice_rate.setValue(self.current.voice_rate)
        self.speech_language = QComboBox()
        for label, value in (
            ("Automatic · detect Sinhala script", "auto"),
            ("English", "en"),
            ("Sinhala / Singlish language hint", "si"),
        ):
            self.speech_language.addItem(label, value)
        self.speech_language.setCurrentIndex(
            self.speech_language.findData(self.current.speech_language)
        )
        self.test_sentence = QLineEdit("MANEXA. Your intelligent personal assistant.")
        self.test_sentence.setMaxLength(4000)
        form.addRow("Speech engine", self.voice_engine)
        form.addRow("Default voice", self.voice_id)
        form.addRow("Voice speed · 0 is normal", self.voice_rate)
        form.addRow("Language", self.speech_language)
        form.addRow("Voice test sentence", self.test_sentence)
        layout.addLayout(form)
        actions = QHBoxLayout()
        refresh = QPushButton("Find installed voices")
        refresh.clicked.connect(self._find_voices)
        preview = QPushButton("Speak test sentence")
        preview.clicked.connect(self._preview)
        stop = QPushButton("Stop speech")
        stop.clicked.connect(self.stop_requested)
        for button in (refresh, preview, stop):
            actions.addWidget(button)
        layout.addLayout(actions)
        self.voice_status = note(
            "Speech uses installed Windows voices without pitch or sound-effect processing. "
            "Sinhala speech requires an installed Sinhala voice; "
            "romanized Singlish is ambiguous, so use the explicit language hint when needed."
        )
        layout.addWidget(self.voice_status)
        capture_form = QFormLayout()
        self.microphone = QComboBox()
        self.microphone.addItem("Windows default microphone", "")
        for device in QMediaDevices.audioInputs():
            self.microphone.addItem(device.description(), bytes(device.id()).hex())
        if self.current.microphone_id and self.microphone.findData(self.current.microphone_id) < 0:
            self.microphone.addItem(
                "Saved device · currently unavailable", self.current.microphone_id
            )
        self.microphone.setCurrentIndex(self.microphone.findData(self.current.microphone_id))
        self.asr_path = QLineEdit(self.current.asr_model_path)
        self.asr_path.setPlaceholderText("Local Faster-Whisper folder containing model.bin")
        browse = QPushButton("Choose recognition model folder")
        browse.clicked.connect(self._choose_model)
        capture_form.addRow("Microphone", self.microphone)
        capture_form.addRow("Local ASR model", self.asr_path)
        capture_form.addRow(browse)
        layout.addLayout(capture_form)
        layout.addWidget(
            note(
                "Save, then Ctrl+Space starts one real microphone turn and interrupts "
                "current speech. Ctrl+Backspace stops immediately. Recognition needs the optional "
                "requirements-voice.txt dependencies and local multilingual model weights. "
                "Spoken replies use local Ollama. No microphone opens at startup. "
                "Always-on wake word and acoustic barge-in are not enabled."
            )
        )
        layout.addWidget(QLabel("Camera · inactive / permission not requested"))
        layout.addWidget(
            note("Camera tracking is not enabled. No camera frames are captured or saved.")
        )
        layout.addStretch()
        return tab

    @Slot()
    def _choose_model(self):
        path = QFileDialog.getExistingDirectory(self, "Local Faster-Whisper model folder")
        if path:
            self.asr_path.setText(path)

    @Slot()
    def _find_voices(self):
        if self._voice_task:
            return
        self.voice_status.setText("Reading installed Windows SAPI voice capabilities…")

        def find():
            try:
                return list_voices()
            except SpeechError:
                return []

        self._voice_task = Task(find)
        self._voice_task.signals.finished.connect(self._voices_found)
        self._voice_task.signals.failed.connect(self._voices_failed)
        QThreadPool.globalInstance().start(self._voice_task)

    @Slot(object)
    def _voices_found(self, voices):
        saved = self.voice_id.currentData()
        self.voice_id.clear()
        self.voice_id.addItem("Preserve Windows default voice", "")
        for voice in voices:
            self.voice_id.addItem(f"{voice.name} · {', '.join(voice.languages)}", voice.id)
        index = self.voice_id.findData(saved)
        if saved and index < 0:
            self.voice_id.addItem("Saved voice · unavailable", saved)
            index = self.voice_id.findData(saved)
        self.voice_id.setCurrentIndex(max(0, index))
        sinhala = any("si" in voice.languages for voice in voices)
        self.voice_status.setText(
            f"{len(voices)} installed SAPI voices. "
            + (
                "Sinhala voice installed; pronunciation still needs listening tests."
                if sinhala
                else "No Sinhala SAPI voice installed. Sinhala TTS is unavailable."
            )
        )
        self._voice_task = None

    @Slot(str)
    def _voices_failed(self, message):
        self.voice_status.setText(message)
        self._voice_task = None

    @Slot()
    def _preview(self):
        try:
            settings = replace(
                self.current,
                voice_id=self.voice_id.currentData(),
                voice_rate=self.voice_rate.value(),
                speech_language=self.speech_language.currentData(),
            )
            settings.validate()
            self.preview_requested.emit(self.test_sentence.text(), settings)
        except ValueError as exc:
            self.status.setText(str(exc))

    def _system_tab(self) -> QWidget:
        tab = QWidget()
        layout = QVBoxLayout(tab)
        layout.setContentsMargins(20, 20, 20, 20)
        layout.setSpacing(16)
        layout.addWidget(QLabel(f"MANEXA desktop · version {__version__}"))
        layout.addWidget(
            note(
                "No conversation history, microphone recordings or camera images are stored. "
                "The renderer has no network or operating-system command access. "
                "No startup registration or system automation is enabled."
            )
        )
        path_label = note(f"Preferences: {self.store.path}")
        layout.addWidget(path_label)
        self.hardware_label = note("Hardware information has not been read yet.")
        layout.addWidget(self.hardware_label)
        self.hardware_button = QPushButton("Detect hardware")
        self.hardware_button.clicked.connect(self._detect_hardware)
        layout.addWidget(self.hardware_button)
        layout.addWidget(
            note(
                "Recommended starting point: Qwen3 1.7B Q4 via Ollama, 2K context; "
                "multilingual Whisper small int8 on CPU to leave VRAM for the desktop and LLM."
            )
        )
        layout.addStretch()
        return tab

    def _draft(self) -> Settings:
        return replace(
            self.current,
            provider=self.provider.currentData(),
            mode=self.mode.currentData(),
            base_url=self.base_url.text().strip().rstrip("/"),
            model=self.model.text().strip(),
            fullscreen=self.fullscreen.isChecked(),
            quality=self.quality.currentData(),
            motion=self.motion.isChecked(),
            glow=self.glow.value(),
            particle_density=self.particle_density.value(),
            animation_speed=self.animation_speed.value(),
            advanced_effects=self.advanced_effects.isChecked(),
            voice_engine=self.voice_engine.currentData(),
            voice_id=self.voice_id.currentData(),
            voice_rate=self.voice_rate.value(),
            speech_language=self.speech_language.currentData(),
            asr_model_path=self.asr_path.text().strip(),
            microphone_id=self.microphone.currentData(),
        ).validate()

    @Slot()
    def _save(self):
        try:
            settings = self._draft()
            key = self.key.text().strip()
            if key:
                self.vault.set(settings.provider, settings.base_url, key)
            self.store.save(settings)
        except (ValueError, CredentialError, OSError) as exc:
            self.status.setText(str(exc))
            return
        except Exception:
            self.status.setText("Preferences could not be saved. Check data-folder access.")
            return
        self.key.clear()
        self.current = settings
        self.applied.emit(settings)
        self.accept()

    @Slot()
    def _test(self):
        if self._task:
            return
        try:
            settings = self._draft()
            key = self.key.text().strip()
            if not key and settings.provider != "ollama":
                key = self.vault.get(settings.provider, settings.base_url)
        except (ValueError, CredentialError) as exc:
            self.status.setText(str(exc))
            return
        self.status.setText("Connecting to the configured provider…")
        self.test_button.setEnabled(False)
        self.hardware_button.setEnabled(False)
        self._task = Task(lambda: probe_provider(settings, key))
        self._task.signals.finished.connect(self._probe_finished)
        self._task.signals.failed.connect(self._task_failed)
        QThreadPool.globalInstance().start(self._task)

    @Slot(object)
    def _probe_finished(self, result):
        self.status.setText(result.message)
        self._finish_task()

    @Slot(str)
    def _task_failed(self, message):
        self.status.setText(message)
        self._finish_task()

    def _finish_task(self):
        self._task = None
        self.test_button.setEnabled(True)
        self.hardware_button.setEnabled(True)

    @Slot()
    def _forget_key(self):
        try:
            settings = self._draft()
            result = QMessageBox.question(
                self, "Remove API key", "Remove the stored key for this provider and endpoint?"
            )
            if result != QMessageBox.StandardButton.Yes:
                return
            self.vault.delete(settings.provider, settings.base_url)
            self.key.clear()
            self.status.setText("Stored API key removed.")
        except (ValueError, CredentialError) as exc:
            self.status.setText(str(exc))

    @Slot()
    def _detect_hardware(self):
        if self._task:
            return
        self.hardware_button.setEnabled(False)
        self.test_button.setEnabled(False)
        self._task = Task(hardware_info)
        self._task.signals.finished.connect(self._hardware_finished)
        self._task.signals.failed.connect(self._task_failed)
        QThreadPool.globalInstance().start(self._task)

    @Slot(object)
    def _hardware_finished(self, info):
        self.hardware_label.setText(
            f"{info['os']}\n{info['cpu']} · {info['logical_cpus']} logical CPUs\n"
            f"{info['ram_gb']} GB RAM\n{info['gpu']}\nPython {info['python']}"
        )
        self._finish_task()
