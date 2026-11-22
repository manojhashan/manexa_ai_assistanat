from PySide6.QtCore import QCoreApplication, Qt
from PySide6.QtTest import QTest
from PySide6.QtWidgets import QApplication, QDialogButtonBox

import app.ui.window as window_module
from app.config.settings import Settings
from app.config.store import SettingsStore
from app.ui.settings_dialog import SettingsDialog
from app.ui.window import MainWindow


def qt_app():
    QCoreApplication.setAttribute(Qt.ApplicationAttribute.AA_ShareOpenGLContexts)
    return QApplication.instance() or QApplication([])


def test_settings_dialog_saves_real_preferences(tmp_path):
    app = qt_app()
    store = SettingsStore(tmp_path / "settings.db")
    dialog = SettingsDialog(store, Settings())
    dialog.fullscreen.setChecked(False)
    dialog.motion.setChecked(False)
    dialog.quality.setCurrentIndex(dialog.quality.findData("performance"))
    dialog.glow.setValue(0.6)
    dialog.particle_density.setValue(0.5)
    dialog.animation_speed.setValue(0.75)
    dialog.advanced_effects.setChecked(False)
    dialog.voice_rate.setValue(-1)
    dialog._save()
    app.processEvents()
    persisted = SettingsStore(store.path).load()
    assert persisted.fullscreen is False
    assert persisted.motion is False
    assert persisted.quality == "performance"
    assert persisted.glow == 0.6
    assert persisted.particle_density == 0.5
    assert persisted.animation_speed == 0.75
    assert persisted.advanced_effects is False
    assert persisted.voice_rate == -1
    reopened = SettingsDialog(store, persisted)
    assert reopened.quality.currentData() == "performance"
    assert not reopened.motion.isChecked()
    dialog.close()
    reopened.close()


def test_provider_change_clears_unsaved_key_and_sets_safe_defaults(tmp_path):
    app = qt_app()
    store = SettingsStore(tmp_path / "settings.db")
    dialog = SettingsDialog(store, Settings())
    dialog.key.setText("test-only-unsaved-secret")
    dialog.provider.setCurrentIndex(dialog.provider.findData("openai"))
    app.processEvents()
    assert dialog.key.text() == ""
    assert dialog.mode.currentData() == "online"
    assert dialog.base_url.text() == "https://api.openai.com/v1"
    dialog.reject()
    assert store.load() == Settings()


def test_fullscreen_escape_and_native_settings_gear(tmp_path):
    app = qt_app()
    store = SettingsStore(tmp_path / "settings.db")
    window = MainWindow(store, Settings(), smoke=True)
    window.showFullScreen()
    app.processEvents()
    assert window.isFullScreen()
    assert window.gear.isVisible()
    assert window.profile.isOffTheRecord()
    window.leave_fullscreen()
    app.processEvents()
    assert not window.isFullScreen()
    QTest.mouseClick(window.gear, Qt.MouseButton.LeftButton)
    app.processEvents()
    assert window._dialog.isVisible()
    window._dialog.reject()
    window.close()
    window.view.setPage(None)
    window.page.deleteLater()
    app.processEvents()


def test_settings_save_changes_fullscreen_and_cancel_keeps_persisted_preferences(tmp_path):
    app = qt_app()
    store = SettingsStore(tmp_path / "settings.db")
    window = MainWindow(store, Settings())
    window.showFullScreen()
    app.processEvents()
    QTest.mouseClick(window.gear, Qt.MouseButton.LeftButton)
    app.processEvents()
    dialog = window._dialog
    dialog.fullscreen.setChecked(False)
    dialog.glow.setValue(0.8)
    buttons = dialog.findChild(QDialogButtonBox)
    QTest.mouseClick(
        buttons.button(QDialogButtonBox.StandardButton.Save), Qt.MouseButton.LeftButton
    )
    app.processEvents()
    assert not window.isFullScreen()
    assert window.settings == SettingsStore(store.path).load()
    assert window.settings.glow == 0.8
    QTest.mouseClick(window.gear, Qt.MouseButton.LeftButton)
    app.processEvents()
    reopened = window._dialog
    assert reopened.glow.value() == 0.8
    reopened.fullscreen.setChecked(True)
    reopened.glow.setValue(1.5)
    buttons = reopened.findChild(QDialogButtonBox)
    QTest.mouseClick(
        buttons.button(QDialogButtonBox.StandardButton.Cancel), Qt.MouseButton.LeftButton
    )
    app.processEvents()
    assert not window.isFullScreen()
    assert window.settings.glow == 0.8
    assert SettingsStore(store.path).load() == window.settings
    window.close()
    window.view.setPage(None)
    window.page.deleteLater()
    app.processEvents()


def test_missing_stylesheet_fails_before_loading_an_unstyled_scene(tmp_path, monkeypatch):
    app = qt_app()
    assets = tmp_path / "web"
    for name in window_module.REQUIRED_ASSETS:
        if name == "scene.css":
            continue
        asset = assets / name
        asset.parent.mkdir(parents=True, exist_ok=True)
        asset.write_text("", encoding="utf-8")
    monkeypatch.setattr(window_module, "WEB_ROOT", assets)
    window = MainWindow(SettingsStore(tmp_path / "settings.db"), Settings(), smoke=True)
    errors = []
    window.renderer_failed.connect(errors.append)
    app.processEvents()
    assert errors == ["A bundled renderer asset is missing."]
    assert not window._startup_timer.isActive()
    assert window.view.url().isEmpty()
    window.close()
    window.view.setPage(None)
    window.page.deleteLater()
    app.processEvents()


class FailingSettingsStore:
    def __init__(self, failure):
        self.failure = failure
        self.path = __file__

    def save(self, settings):
        raise self.failure


class MemoryCredentialVault:
    def __init__(self, existing=""):
        self.existing = existing

    def get(self, provider, endpoint):
        return self.existing

    def set(self, provider, endpoint, value):
        self.existing = value

    def delete(self, provider, endpoint):
        self.existing = ""


def test_settings_save_rolls_back_new_credential_when_sqlite_save_fails(tmp_path):
    app = qt_app()
    dialog = SettingsDialog(FailingSettingsStore(OSError("disk unavailable")), Settings())
    dialog.vault = MemoryCredentialVault(existing="previous-key")
    dialog.key.setText("new-key")

    dialog._save()
    app.processEvents()

    assert dialog.vault.existing == "previous-key"
    assert dialog.status.text()
    dialog.close()
    dialog.deleteLater()
    app.processEvents()


def test_settings_save_deletes_new_credential_when_no_previous_key_exists(tmp_path):
    app = qt_app()
    dialog = SettingsDialog(FailingSettingsStore(OSError("disk unavailable")), Settings())
    dialog.vault = MemoryCredentialVault(existing="")
    dialog.key.setText("new-key")

    dialog._save()
    app.processEvents()

    assert dialog.vault.existing == ""
    assert dialog.status.text()
    dialog.close()
    dialog.deleteLater()
    app.processEvents()
