"""Opt-in audible real SAPI â†’ PCM â†’ playback â†’ WebGL verification.

No recording is made. --microphone additionally opens capture briefly in memory.
"""

import argparse
import json
import sys
import tempfile
import time
from pathlib import Path

from PySide6.QtCore import QCoreApplication, Qt, QTimer
from PySide6.QtWidgets import QApplication

from app.config.settings import Settings
from app.config.store import SettingsStore
from app.core.state import AssistantState
from app.speech.sapi import list_voices
from app.ui.window import MainWindow


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--microphone", action="store_true")
    parser.add_argument("--report", type=Path, default=Path("artifacts/voice-check.json"))
    args = parser.parse_args()
    QCoreApplication.setAttribute(Qt.ApplicationAttribute.AA_ShareOpenGLContexts)
    app = QApplication(sys.argv[:1])
    temporary = tempfile.TemporaryDirectory(prefix="manexa-voice-check-")
    window = MainWindow(SettingsStore(Path(temporary.name) / "settings.db"), Settings(), smoke=True)
    checks, samples = {}, {}
    maximum_level, maximum_response, maximum_energy = 0.0, 0.0, 0.0
    finished = False
    timer = QTimer(window)
    timer.setInterval(35)
    talking = False
    stop_scheduled = False
    started = time.monotonic()

    def finish(error=None):
        nonlocal finished
        if finished:
            return
        finished = True
        timer.stop()
        window.voice.stop()
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
        app.exit(0 if report["ok"] else 1)

    def level(value):
        nonlocal maximum_level
        maximum_level = max(maximum_level, value)

    def observed(payload):
        nonlocal maximum_response, maximum_energy
        if finished:
            return
        value = json.loads(payload)
        maximum_response = max(maximum_response, value["orbResponse"])
        maximum_energy = max(maximum_energy, value["speechEnergy"])

    def inspect():
        window.page.runJavaScript("JSON.stringify(window.manexa.diagnostics())", observed)

    def state(value):
        nonlocal talking, stop_scheduled
        if value == AssistantState.SPEAKING and not stop_scheduled:
            talking = True
            stop_scheduled = True
            checks["real_playback_entered_speaking"] = True
            QTimer.singleShot(1500, interrupt)

    def interrupt():
        window.grab().save("artifacts/orb-speaking.png")
        elapsed = time.perf_counter()
        window.voice.stop()
        checks["interruption_flushes_device"] = window.voice.speech._sink is None
        checks["interruption_returns_idle"] = window.voice.speech.state == AssistantState.IDLE
        samples["stop_call_ms"] = (time.perf_counter() - elapsed) * 1000
        checks["stop_call_responsive"] = samples["stop_call_ms"] < 150
        samples["maximum_measured_level"] = maximum_level
        samples["maximum_rendered_orb_response"] = maximum_response
        samples["maximum_rendered_orb_energy"] = maximum_energy
        checks["measured_pcm_drives_orb_pulse"] = (
            maximum_level > 0.1 and maximum_response > 0.02 and maximum_energy > 0.1
        )
        QTimer.singleShot(180, after_interrupt)

    def after_interrupt():
        def stopped(payload):
            value = json.loads(payload)
            checks["no_residual_speaking_animation"] = (
                value["state"] == "idle"
                and value["orbResponse"] == 0
                and value["speechEnergy"] == 0
            )
            window.grab().save("artifacts/voice-idle.png")
            if args.microphone:
                # Explicit opt-in to this script; samples remain RAM-only and are discarded.
                window.voice.capture.active.connect(microphone_active)
                window.voice.capture.start()
            else:
                check_completion()

        window.page.runJavaScript("JSON.stringify(window.manexa.diagnostics())", stopped)

    def microphone_active():
        checks["real_microphone_started"] = True
        QTimer.singleShot(500, microphone_stop)

    def microphone_stop():
        checks["microphone_received_pcm"] = bool(window.voice.capture._pcm)

        def inspected(payload):
            value = json.loads(payload)
            checks["capture_drives_real_listening_state"] = value["state"] == "listening"
            checks["listening_has_no_residual_speech_pulse"] = value["orbResponse"] == 0
            window.voice.stop()
            checks["microphone_released"] = window.voice.capture._source is None
            check_completion()

        window.page.runJavaScript("JSON.stringify(window.manexa.diagnostics())", inspected)

    def check_completion():
        window.voice.speech.finished.connect(completed)
        window.voice.preview("Ready.", Settings())

    def completed():
        checks["normal_completion_releases_playback"] = window.voice.speech._sink is None
        checks["normal_completion_returns_idle"] = window.voice.speech.state == AssistantState.IDLE
        QTimer.singleShot(150, finish)

    def ready(_):
        voices = list_voices()
        samples["installed_voices"] = [{"name": v.name, "languages": v.languages} for v in voices]
        samples["sinhala_installed"] = any("si" in v.languages for v in voices)
        checks["real_installed_voice_available"] = bool(voices)
        timer.start()
        window.voice.preview(
            "MANEXA is ready. My hologram follows the audio you are hearing. "
            "Speech can be interrupted immediately.",
            Settings(),
        )

    timer.timeout.connect(inspect)
    window.voice.level_changed.connect(level)
    window.voice.state_changed.connect(state)
    window.voice_failed.connect(finish)
    window.renderer_failed.connect(finish)
    window.renderer_ready.connect(ready)
    QTimer.singleShot(
        30000, lambda: finish(f"Voice check timed out after {time.monotonic() - started:.1f}s")
    )
    window.show()
    window.raise_()
    window.activateWindow()
    result = app.exec()
    window.close()
    window.view.setPage(None)
    window.page.deleteLater()
    app.sendPostedEvents(None, 0)
    temporary.cleanup()
    return result


if __name__ == "__main__":
    raise SystemExit(main())
