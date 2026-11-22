"""Real WebGL integration checks; inputs are test stimuli, not synthetic speech.

Run from the repository root: python -m scripts.check_renderer
Never opens a microphone, camera or AI provider.
"""

import argparse
import json
import os
import sys
import tempfile
from dataclasses import replace
from pathlib import Path

from PySide6.QtCore import QCoreApplication, Qt, QTimer
from PySide6.QtTest import QTest
from PySide6.QtWidgets import QApplication, QDialogButtonBox, QTabWidget

from app.config.settings import Settings
from app.config.store import SettingsStore
from app.core.state import AssistantState, HeadPose
from app.ui.window import MainWindow


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--report", type=Path, default=Path("artifacts/renderer-check.json"))
    parser.add_argument("--screenshot", type=Path, default=Path("artifacts/orb-quarter.png"))
    parser.add_argument(
        "--fullscreen", action="store_true", help="Verify the actual fullscreen desktop"
    )
    args = parser.parse_args()
    # Verification must keep producing real frames while the user works in another window.
    # Production retains normal occlusion/background throttling for battery/GPU savings.
    flags = os.environ.get("QTWEBENGINE_CHROMIUM_FLAGS", "")
    os.environ["QTWEBENGINE_CHROMIUM_FLAGS"] = flags + (
        " --disable-backgrounding-occluded-windows --disable-renderer-backgrounding"
        " --disable-background-timer-throttling --disable-features=CalculateNativeWinOcclusion"
    )
    QCoreApplication.setAttribute(Qt.ApplicationAttribute.AA_ShareOpenGLContexts)
    application = QApplication(sys.argv[:1])
    temporary = tempfile.TemporaryDirectory(prefix="manexa-render-check-")
    window = MainWindow(SettingsStore(Path(temporary.name) / "settings.db"), Settings(), smoke=True)
    checks = {}
    samples = {}
    finished = False
    amplitude_timer = QTimer(window)
    amplitude_timer.setInterval(50)
    amplitude_timer.timeout.connect(lambda: window.set_speech_level(0.85))
    visibility_timer = QTimer(window)
    visibility_timer.setInterval(80)
    visibility_timer.timeout.connect(lambda: window.page.setVisible(True))
    visibility_timer.start()

    def finish(error=None):
        nonlocal finished
        if finished:
            return
        finished = True
        amplitude_timer.stop()
        visibility_timer.stop()
        report = {
            "ok": bool(checks) and all(checks.values()) and not error,
            "checks": checks,
            "samples": samples,
        }
        if error:
            report["error"] = error
        args.report.parent.mkdir(parents=True, exist_ok=True)
        args.report.write_text(json.dumps(report, indent=2), encoding="utf-8")
        print(json.dumps(report, indent=2))
        application.exit(0 if report["ok"] else 1)

    def read(callback):
        def result(payload):
            if finished:
                return
            try:
                value = json.loads(payload)
                if not isinstance(value, dict):
                    raise ValueError
                callback(value)
            except (ValueError, TypeError, KeyError) as exc:
                finish(f"Renderer diagnostics invalid: {type(exc).__name__}")

        window.page.runJavaScript("JSON.stringify(window.manexa.diagnostics())", result)

    def baseline(value):
        samples["idle"] = value
        checks["real_particles_rendered"] = (
            value["ready"]
            and value["triangles"] == 0
            and value["drawCalls"] == 1
            and value["nonBackgroundPixels"] > 10
        )
        checks["brand_only_single_canvas"] = (
            value["visibleText"] == "MANEXA" and value["canvasCount"] == 1
        )
        checks["spaced_brand_centered_inside_orb"] = (
            value["branding"]["centered"]
            and value["branding"]["text"] == "MANEXA"
            and value["branding"]["letterCount"] == 6
            and value["branding"]["letterGap"] >= 7
        )
        checks["silent_orb_has_no_speech_pulse"] = value["orbResponse"] == 0
        checks["blue_orb_with_inner_nucleus"] = (
            value["visualStyle"] == "blue-particle-orb" and value["innerNucleus"]
        )
        checks["no_face_neck_or_shoulders"] = not any(
            value[key] for key in ("face", "neck", "shoulders")
        )
        checks["restrained_default_bloom"] = 0 < value["bloomStrength"] <= 0.35
        checks["no_bust_core_rings_or_orange_face"] = not any(
            value[key]
            for key in ("solidBust", "chestCore", "orbitalRings", "warmFace", "wireShoulders")
        )
        checks["rendered_palette_has_no_orange"] = value["warmPixels"] == 0
        checks["thousands_of_surface_particles"] = value["particleCount"] >= 4000
        args.screenshot.parent.mkdir(parents=True, exist_ok=True)
        if args.fullscreen:
            checks["fullscreen_covers_display"] = (
                window.isFullScreen() and window.geometry() == window.screen().geometry()
            )
            checks["fullscreen_screenshot_saved"] = window.grab().save(
                str(args.screenshot.parent / "phase1-fullscreen.png")
            )
            QTest.keyClick(window, Qt.Key.Key_Escape)
            application.processEvents()
            checks["escape_leaves_fullscreen"] = not window.isFullScreen()
            QTest.keyClick(window, Qt.Key.Key_F11)
            application.processEvents()
            checks["f11_restores_fullscreen"] = window.isFullScreen()
        window.set_state(AssistantState.LISTENING)
        QTimer.singleShot(160, lambda: read(listening))

    def listening(value):
        checks["listening_state_delivered"] = (
            value["state"] == "listening" and value["listeningEnergy"] == 1
        )
        window.set_state(AssistantState.THINKING)
        QTimer.singleShot(160, lambda: read(thinking))

    def thinking(value):
        checks["thinking_changes_scan"] = value["state"] == "thinking" and value["scanSpeed"] > 1
        window.set_state(AssistantState.SPEAKING)
        window.set_speech_level(0.85)
        amplitude_timer.start()
        QTimer.singleShot(300, lambda: read(speaking))

    def speaking(value):
        samples["speech_amplitude_test"] = value
        checks["amplitude_expands_orb"] = (
            value["orbResponse"] > 0.5 and value["radialExpansion"] > 0.04
        )
        checks["amplitude_drives_energy"] = value["speechEnergy"] > 0.5
        checks["brand_responds_to_speech"] = value["branding"]["speechEnergy"] > 0.5
        amplitude_timer.stop()
        # Stale audio must decay even if a producer fails to send a final zero sample.
        QTimer.singleShot(650, lambda: read(silent))

    def silent(value):
        checks["stale_amplitude_stops_speech_pulse"] = (
            value["orbResponse"] < 0.02 and value["speechEnergy"] < 0.02
        )
        checks["brand_speech_pulse_decays"] = value["branding"]["speechEnergy"] < 0.02
        window.set_state(AssistantState.IDLE)
        window.set_pose(HeadPose(yaw=0.43, pitch=-0.20))
        QTimer.singleShot(1600, lambda: read(posed))

    def posed(value):
        samples["pose_test"] = value
        checks["real_frames_keep_advancing"] = (
            value["frameCount"] > samples["idle"]["frameCount"] + 30
        )
        checks["pose_actually_moves_mesh"] = value["yaw"] > 0.30 and value["pitch"] < -0.13
        args.screenshot.parent.mkdir(parents=True, exist_ok=True)
        checks["screenshot_saved"] = window.grab().save(str(args.screenshot))
        window.set_pose(HeadPose())
        window.apply_settings(replace(Settings(), quality="performance", motion=False, glow=0.7))
        QTimer.singleShot(1000, lambda: read(performance))

    def performance(value):
        checks["performance_settings_applied"] = (
            value["quality"] == "performance"
            and value["targetFPS"] == 30
            and value["pixelRatio"] <= 1
            and value["motion"] is False
            and abs(value["glow"] - 0.7) < 0.001
            and value["branding"]["motion"] is False
            and value["branding"]["animationDuration"] == "0s"
        )
        window.apply_settings(replace(Settings(), quality="high"))
        QTimer.singleShot(160, lambda: read(high_quality))

    def high_quality(value):
        checks["high_quality_settings_applied"] = value["targetFPS"] == 60
        window.apply_settings(replace(Settings(), animation_speed=2.0))
        window.reconstruct_hologram()
        QTimer.singleShot(1700, lambda: read(dissolved))

    def dissolved(value):
        samples["dissolution"] = value
        checks["actual_particle_dissolution"] = value["dissolve"] > 0.65
        window.grab().save(str(args.screenshot.parent / "hologram-dissolved.png"))
        QTimer.singleShot(2400, lambda: read(reconstructed))

    def reconstructed(value):
        samples["reconstruction"] = value
        checks["orb_reconstructs"] = value["dissolve"] < 0.06
        checks["surface_scan_advances"] = value["scanTime"] > samples["idle"]["scanTime"]
        window.apply_settings(
            replace(
                Settings(),
                quality="performance",
                particle_density=0.25,
                advanced_effects=False,
                animation_speed=0.5,
            )
        )
        QTimer.singleShot(200, lambda: read(simple_effects))

    def simple_effects(value):
        checks["advanced_effects_can_be_disabled"] = value["advancedEffects"] is False
        checks["particle_budget_applies"] = value["particleCount"] <= 600
        checks["animation_speed_applies"] = value["animationSpeed"] == 0.5
        QTest.mouseClick(window.gear, Qt.MouseButton.LeftButton)
        QTimer.singleShot(200, settings_check)

    def settings_check():
        dialog = window._dialog
        checks["native_gear_opens_settings"] = dialog.isVisible()
        tabs = dialog.findChild(QTabWidget)
        checks["all_settings_tabs_available"] = tabs.count() == 4
        for index, name in enumerate(("ai", "appearance", "voice", "system")):
            tabs.setCurrentIndex(index)
            QTest.qWait(60)
            dialog.grab().save(str(args.screenshot.parent / f"phase1-settings-{name}.png"))
        buttons = dialog.findChild(QDialogButtonBox)
        checks["save_and_cancel_fit_on_screen"] = (
            dialog.screen().availableGeometry().contains(dialog.frameGeometry())
            and buttons.button(QDialogButtonBox.StandardButton.Save).isVisible()
            and buttons.button(QDialogButtonBox.StandardButton.Cancel).isVisible()
        )
        tabs.setCurrentIndex(1)
        dialog.quality.setCurrentIndex(dialog.quality.findData("balanced"))
        dialog.glow.setValue(0.8)
        dialog.particle_density.setValue(0.5)
        QTest.mouseClick(
            buttons.button(QDialogButtonBox.StandardButton.Save), Qt.MouseButton.LeftButton
        )
        QTimer.singleShot(300, lambda: read(saved_settings))

    def saved_settings(value):
        persisted = SettingsStore(window.store.path).load()
        checks["settings_save_persists_to_disk"] = (
            persisted == window.settings and persisted.glow == 0.8
        )
        checks["settings_save_updates_real_renderer"] = (
            value["quality"] == "balanced"
            and abs(value["glow"] - 0.8) < 0.001
            and value["particleCount"] == 3500
        )
        QTest.mouseClick(window.gear, Qt.MouseButton.LeftButton)
        application.processEvents()
        dialog = window._dialog
        checks["reopened_settings_match_disk"] = (
            dialog.glow.value() == 0.8 and dialog.particle_density.value() == 0.5
        )
        dialog.glow.setValue(1.6)
        buttons = dialog.findChild(QDialogButtonBox)
        QTest.mouseClick(
            buttons.button(QDialogButtonBox.StandardButton.Cancel), Qt.MouseButton.LeftButton
        )
        QTimer.singleShot(200, lambda: read(canceled_settings))

    def canceled_settings(value):
        checks["cancel_discards_unsaved_changes"] = (
            abs(value["glow"] - 0.8) < 0.001
            and SettingsStore(window.store.path).load().glow == 0.8
            and not window._dialog.isVisible()
        )
        finish()

    window.renderer_ready.connect(lambda _: QTimer.singleShot(250, lambda: read(baseline)))
    window.renderer_failed.connect(finish)
    QTimer.singleShot(35000, lambda: finish("Renderer integration check timed out."))
    if args.fullscreen:
        window.showFullScreen()
    else:
        window.show()
    window.raise_()
    window.activateWindow()
    result = application.exec()
    window.close()
    window.view.setPage(None)
    window.page.deleteLater()
    application.sendPostedEvents(None, 0)
    temporary.cleanup()
    return result


if __name__ == "__main__":
    raise SystemExit(main())
