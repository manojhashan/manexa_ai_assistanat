"""Particle-orb desktop. Native settings stay separate from the renderer."""

import json
from pathlib import Path

from PySide6.QtCore import Qt, QTimer, QUrl, Signal, Slot
from PySide6.QtGui import QColor, QKeySequence, QShortcut
from PySide6.QtWebChannel import QWebChannel
from PySide6.QtWebEngineCore import (
    QWebEnginePage,
    QWebEngineProfile,
    QWebEngineSettings,
    QWebEngineUrlRequestInterceptor,
)
from PySide6.QtWebEngineWidgets import QWebEngineView
from PySide6.QtWidgets import QMainWindow, QMessageBox

from app.config.settings import Settings
from app.config.store import SettingsStore
from app.core.state import AssistantState, HeadPose
from app.ui.assets import REQUIRED_ASSETS
from app.ui.bridge import RendererBridge
from app.ui.gear import SettingsGear
from app.ui.settings_dialog import SettingsDialog
from app.voice.recognition import check_recognition
from app.voice.session import VoiceSession

WEB_ROOT = Path(__file__).parent / "web"


def renderer_url_allowed(url: QUrl) -> bool:
    # Reject UNC/network-share file URLs before even resolving a filesystem path.
    if url.host():
        return False
    if url.scheme() == "qrc":
        return url.path() == "/qtwebchannel/qwebchannel.js"
    if url.isLocalFile():
        path = Path(url.toLocalFile()).resolve()
        return path.is_relative_to(WEB_ROOT.resolve()) and path.is_file()
    return url.toString() == "about:blank"


class LocalAssetsOnly(QWebEngineUrlRequestInterceptor):
    def interceptRequest(self, info):
        if not renderer_url_allowed(info.requestUrl()):
            info.block(True)


class ScenePage(QWebEnginePage):
    def acceptNavigationRequest(self, url, navigation_type, is_main_frame):
        return renderer_url_allowed(url)

    def javaScriptConsoleMessage(self, level, message, line_number, source_id):
        # Do not persist console content. Renderer failures are reported over the typed bridge.
        pass


class MainWindow(QMainWindow):
    renderer_ready = Signal(dict)
    renderer_failed = Signal(str)
    voice_failed = Signal(str)

    def __init__(self, store: SettingsStore, settings: Settings, *, smoke=False):
        super().__init__()
        self.store = store
        self.settings = settings
        self.smoke = smoke
        self._dialog = None
        self._dialogs = []
        self._ready = False
        self._closing = False
        self._shutdown_complete = False
        self._last_error = None
        self._microphone_allowed = False
        self.voice = VoiceSession(self)
        self.voice.state_changed.connect(self.set_state)
        self.voice.level_changed.connect(self.set_speech_level)
        self.voice.failed.connect(self._voice_failed)
        self.setWindowTitle("MANEXA AI")
        self.resize(1280, 800)
        self.setMinimumSize(640, 480)
        self.setStyleSheet("QMainWindow { background: #000; }")
        self.view = QWebEngineView(self)
        self.setCentralWidget(self.view)
        # An unnamed profile is off the record: no disk cache, cookies or local storage.
        self.profile = QWebEngineProfile(self)
        self.profile.setHttpCacheType(QWebEngineProfile.HttpCacheType.MemoryHttpCache)
        self.profile.setPersistentCookiesPolicy(
            QWebEngineProfile.PersistentCookiesPolicy.NoPersistentCookies
        )
        self.interceptor = LocalAssetsOnly(self.profile)
        self.profile.setUrlRequestInterceptor(self.interceptor)
        self.page = ScenePage(self.profile, self.view)
        self.page.setBackgroundColor(QColor("#000000"))
        self.view.setPage(self.page)
        self.view.setContextMenuPolicy(Qt.ContextMenuPolicy.NoContextMenu)
        browser_settings = self.page.settings()
        for attribute in (
            QWebEngineSettings.WebAttribute.LocalContentCanAccessRemoteUrls,
            QWebEngineSettings.WebAttribute.JavascriptCanOpenWindows,
            QWebEngineSettings.WebAttribute.FullScreenSupportEnabled,
            QWebEngineSettings.WebAttribute.LocalStorageEnabled,
            QWebEngineSettings.WebAttribute.PluginsEnabled,
        ):
            browser_settings.setAttribute(attribute, False)
        self.channel = QWebChannel(self.page)
        self.bridge = RendererBridge(self.channel)
        self.channel.registerObject("bridge", self.bridge)
        self.page.setWebChannel(self.channel)
        self.bridge.ready.connect(self._on_ready)
        self.bridge.failed.connect(self._on_failed)
        self.page.renderProcessTerminated.connect(
            lambda *_: self._on_failed("The graphics process stopped. Try software rendering.")
        )
        self.view.loadFinished.connect(self._loaded)
        self._startup_timer = QTimer(self)
        self._startup_timer.setSingleShot(True)
        self._startup_timer.timeout.connect(
            lambda: self._on_failed(
                "The renderer did not initialize. Check bundled assets or try software rendering."
            )
        )
        self.gear = SettingsGear(self)
        self.gear.clicked.connect(self.open_settings)
        self._shortcuts = []
        for sequence, action in (
            ("Ctrl+,", self.open_settings),
            ("F11", self.toggle_fullscreen),
            ("Esc", self.leave_fullscreen),
            ("Ctrl+Q", self.close),
            ("Ctrl+D", self.reconstruct_hologram),
            ("Ctrl+Space", self.listen),
            ("Ctrl+Backspace", self.voice.stop),
        ):
            shortcut = QShortcut(QKeySequence(sequence), self)
            shortcut.activated.connect(action)
            self._shortcuts.append(shortcut)
        if all((WEB_ROOT / asset).is_file() for asset in REQUIRED_ASSETS):
            self._startup_timer.start(15000)
            self.view.setUrl(QUrl.fromLocalFile(str(WEB_ROOT / "index.html")))
        else:
            QTimer.singleShot(0, lambda: self._on_failed("A bundled renderer asset is missing."))

    def resizeEvent(self, event):
        super().resizeEvent(event)
        self.gear.move(self.width() - self.gear.width() - 20, self.height() - 65)
        self.gear.raise_()

    @Slot(bool)
    def _loaded(self, ok):
        if not ok:
            self._on_failed("The local scene could not be loaded. Check the installation.")

    @Slot(dict)
    def _on_ready(self, info):
        self._startup_timer.stop()
        self._last_error = None
        self._ready = True
        self._configure_scene()
        self.renderer_ready.emit(info)

    @Slot(str)
    def _on_failed(self, message):
        self._startup_timer.stop()
        if self._closing or self._last_error == message:
            return
        self._last_error = message
        self._ready = False
        self.renderer_failed.emit(message)
        if not self.smoke:
            QMessageBox.warning(self, "MANEXA · Graphics", message)

    def _configure_scene(self):
        if self._ready:
            payload = json.dumps(
                {
                    "quality": self.settings.quality,
                    "motion": self.settings.motion,
                    "glow": self.settings.glow,
                    "particleDensity": self.settings.particle_density,
                    "animationSpeed": self.settings.animation_speed,
                    "advancedEffects": self.settings.advanced_effects,
                }
            )
            self.page.runJavaScript(f"window.manexa.configure({payload})")

    @Slot(object)
    def apply_settings(self, settings):
        self.settings = settings
        self._configure_scene()
        if not self.smoke:
            if settings.fullscreen:
                self.showFullScreen()
            else:
                self.showNormal()

    @Slot()
    def open_settings(self):
        if self._dialog and self._dialog.isVisible():
            self._dialog.raise_()
            self._dialog.activateWindow()
            return
        # Keep a closed dialog alive if its bounded background task has not returned yet.
        active = []
        for dialog in self._dialogs:
            if dialog._task or dialog._voice_task:
                active.append(dialog)
            else:
                dialog.deleteLater()
        self._dialogs = active
        self._dialog = SettingsDialog(self.store, self.settings, self)
        self._dialogs.append(self._dialog)
        self._dialog.applied.connect(self.apply_settings)
        self._dialog.preview_requested.connect(self.voice.preview)
        self._dialog.stop_requested.connect(self.voice.stop)
        self._dialog.reconstruct_requested.connect(self.reconstruct_hologram)
        self._dialog.open()

    @Slot()
    def toggle_fullscreen(self):
        self.showNormal() if self.isFullScreen() else self.showFullScreen()

    @Slot()
    def leave_fullscreen(self):
        if self.isFullScreen():
            self.showNormal()

    def set_state(self, state: AssistantState):
        if not isinstance(state, AssistantState):
            raise TypeError("Use a typed AssistantState event.")
        if self._ready:
            self.page.runJavaScript(f"window.manexa.setState({json.dumps(state.value)})")

    def set_pose(self, pose: HeadPose):
        if self._ready:
            self.page.runJavaScript(f"window.manexa.setPose({json.dumps(pose.to_dict())})")

    def set_speech_level(self, level: float):
        # The real audio playback clock supplies its measured PCM envelope here.
        if not 0.0 <= level <= 1.0:
            raise ValueError("Speech amplitude must be between 0 and 1.")
        if self._ready:
            self.page.runJavaScript(f"window.manexa.setSpeechLevel({float(level)})")

    @Slot()
    def reconstruct_hologram(self):
        if self._ready:
            self.page.runJavaScript("window.manexa.reconstruct()")

    def closeEvent(self, event):
        self._closing = True
        self.shutdown()
        super().closeEvent(event)

    def shutdown(self):
        if getattr(self, "_shutdown_complete", False):
            return
        self._closing = True
        self._startup_timer.stop()
        self.gear._timer.stop()
        self.voice.stop()
        for dialog in list(getattr(self, "_dialogs", [])):
            dialog.close()
            dialog.deleteLater()
        self._dialogs = []
        self._dialog = None
        for shortcut in getattr(self, "_shortcuts", []):
            shortcut.setEnabled(False)
        self._shutdown_complete = True

    @Slot()
    def listen(self):
        self.voice.stop()
        try:
            check_recognition(self.settings.asr_model_path)
        except ValueError as exc:
            self._voice_failed(str(exc))
            return
        if not self._microphone_allowed:
            answer = QMessageBox.question(
                self,
                "MANEXA · Microphone permission",
                "Allow spoken turns through the selected microphone for this session? Audio is "
                "processed locally in memory and never saved. Each capture stops after silence "
                "or 15 seconds. Ctrl+Backspace stops capture and speech.",
            )
            if answer != QMessageBox.StandardButton.Yes:
                return
            self._microphone_allowed = True
        self.voice.listen(self.settings)

    @Slot(str)
    def _voice_failed(self, message):
        self.voice_failed.emit(message)
        if self._dialog and self._dialog.isVisible():
            self._dialog.status.setText(message)
        elif not self.smoke:
            QMessageBox.warning(self, "MANEXA · Voice", message)
