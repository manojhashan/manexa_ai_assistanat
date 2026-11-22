"""Run with python -m app.main. No model downloads or hardware capture at startup."""

import argparse
import json
import os
import sqlite3
import sys
import tempfile
from pathlib import Path


def parse_args(argv=None):
    parser = argparse.ArgumentParser(description="MANEXA AI desktop assistant")
    display = parser.add_mutually_exclusive_group()
    display.add_argument("--windowed", action="store_true", help="Start in a normal window")
    display.add_argument(
        "--fullscreen",
        action="store_true",
        help="Start fullscreen, overriding saved display preference",
    )
    parser.add_argument("--software-rendering", action="store_true", help="Use software WebGL")
    parser.add_argument("--smoke-test", action="store_true", help="Launch, inspect and exit safely")
    parser.add_argument("--smoke-report", type=Path, help="Write smoke diagnostics as JSON")
    parser.add_argument("--screenshot", type=Path, help="Capture the smoke-test window")
    return parser.parse_args(argv)


def main(argv=None) -> int:
    args = parse_args(argv)
    if args.software_rendering:
        # Qt 6.8 wheels do not bundle SwiftShader. Windows WARP is the verified fallback.
        os.environ["QSG_RHI_BACKEND"] = "d3d11"
        os.environ["QSG_RHI_PREFER_SOFTWARE_RENDERER"] = "1"
        os.environ["QTWEBENGINE_CHROMIUM_FLAGS"] = "--ignore-gpu-blocklist"
    # Import QtWebEngine before constructing QApplication.
    from PySide6.QtCore import QCoreApplication, Qt, QTimer
    from PySide6.QtGui import QColor, QPalette
    from PySide6.QtWidgets import QApplication, QMessageBox

    from app.config.store import SettingsStore
    from app.ui.window import MainWindow

    QCoreApplication.setAttribute(Qt.ApplicationAttribute.AA_ShareOpenGLContexts)
    application = QApplication(sys.argv[:1])
    application.setApplicationName("MANEXA AI")
    application.setOrganizationName("MANEXA")
    palette = QPalette()
    palette.setColor(QPalette.ColorRole.Window, QColor("#080f19"))
    palette.setColor(QPalette.ColorRole.WindowText, QColor("#d4e7f0"))
    application.setPalette(palette)
    temporary = tempfile.TemporaryDirectory(prefix="manexa-smoke-") if args.smoke_test else None
    try:
        store = SettingsStore(Path(temporary.name) / "settings.db" if temporary else None)
        settings = store.load()
    except (OSError, ValueError, sqlite3.Error) as exc:
        if args.smoke_test:
            print(json.dumps({"ok": False, "error": str(exc)}))
        else:
            QMessageBox.critical(None, "MANEXA · Startup", str(exc))
        return 1
    window = MainWindow(store, settings, smoke=args.smoke_test)
    exit_code = 0
    finished = False

    def finish(report):
        nonlocal exit_code, finished
        if finished:
            return
        finished = True
        exit_code = 0 if report.get("ok") else 1
        payload = json.dumps(report, indent=2)
        print(payload)
        if args.smoke_report:
            args.smoke_report.parent.mkdir(parents=True, exist_ok=True)
            args.smoke_report.write_text(payload, encoding="utf-8")
        if args.screenshot:
            args.screenshot.parent.mkdir(parents=True, exist_ok=True)
            if not window.grab().save(str(args.screenshot)):
                exit_code = 1
        window.close()
        application.quit()

    if args.smoke_test:
        window.renderer_failed.connect(lambda error: finish({"ok": False, "error": error}))

        def inspected(payload):
            try:
                diagnostics = json.loads(payload)
                ok = (
                    diagnostics.get("ready") is True
                    and diagnostics.get("frameCount", 0) > 1
                    and diagnostics.get("nonBackgroundPixels", 0) > 10
                    and diagnostics.get("visibleText") == "MANEXA"
                    and diagnostics.get("branding", {}).get("centered") is True
                    and (
                        not args.fullscreen
                        or (
                            window.isFullScreen()
                            and window.geometry() == window.screen().geometry()
                        )
                    )
                )
            except (TypeError, ValueError):
                diagnostics, ok = {}, False
            finish(
                {
                    "ok": ok,
                    "renderer": diagnostics,
                    "off_the_record": window.profile.isOffTheRecord(),
                    "visible_gear": window.gear.isVisible(),
                    "window": [window.width(), window.height()],
                    "fullscreen": window.isFullScreen(),
                    "screen": [
                        window.screen().geometry().width(),
                        window.screen().geometry().height(),
                    ],
                }
            )

        def inspect(_):
            QTimer.singleShot(
                1500,
                lambda: window.page.runJavaScript(
                    "JSON.stringify(window.manexa.diagnostics())", inspected
                ),
            )

        window.renderer_ready.connect(inspect)
        QTimer.singleShot(
            20000, lambda: finish({"ok": False, "error": "Renderer startup timed out."})
        )
    if args.fullscreen or (not args.windowed and not args.smoke_test and settings.fullscreen):
        window.showFullScreen()
    else:
        window.show()
    application.exec()
    # Dispose the page before its profile; avoid WebEngine shutdown races.
    window.view.setPage(None)
    window.page.deleteLater()
    application.sendPostedEvents(None, 0)
    if temporary:
        temporary.cleanup()
    return exit_code


if __name__ == "__main__":
    raise SystemExit(main())
