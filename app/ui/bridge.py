"""Narrow WebChannel boundary: renderer health only, no system execution API."""

import json

from PySide6.QtCore import QObject, Signal, Slot


class RendererBridge(QObject):
    ready = Signal(dict)
    failed = Signal(str)

    @Slot(str)
    def rendererReady(self, payload: str):
        try:
            value = json.loads(payload)
            if isinstance(value, dict) and value.get("ready") is True:
                self.ready.emit(value)
        except (ValueError, TypeError):
            self.failed.emit("The renderer returned an invalid health report.")

    @Slot(str)
    def rendererFailed(self, reason: str):
        # A scene has no access to settings, the vault or a command execution method.
        self.failed.emit(reason[:400])
