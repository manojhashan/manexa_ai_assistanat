"""Keep blocking work off the Qt event loop; signals return results to the UI."""

from collections.abc import Callable

from PySide6.QtCore import QObject, QRunnable, Signal, Slot


class TaskSignals(QObject):
    finished = Signal(object)
    failed = Signal(str)


class Task(QRunnable):
    def __init__(self, function: Callable):
        super().__init__()
        self.function = function
        self.signals = TaskSignals()

    @Slot()
    def run(self):
        try:
            result = self.function()
        except Exception:
            # Exception strings can contain credential-bearing URLs. Do not expose them.
            self.signals.failed.emit("The background operation failed. Check your configuration.")
        else:
            self.signals.finished.emit(result)
