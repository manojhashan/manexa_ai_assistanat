"""Typed renderer events. No simulated microphone, speech or AI responses."""

import math
from dataclasses import dataclass
from enum import StrEnum


class AssistantState(StrEnum):
    IDLE = "idle"
    LISTENING = "listening"
    THINKING = "thinking"
    SPEAKING = "speaking"
    ERROR = "error"


@dataclass(frozen=True)
class HeadPose:
    yaw: float = 0.0
    pitch: float = 0.0

    def to_dict(self) -> dict:
        if not all(math.isfinite(value) for value in (self.yaw, self.pitch)):
            raise ValueError("Head pose must be finite.")
        return {"yaw": max(-0.6, min(0.6, self.yaw)), "pitch": max(-0.4, min(0.4, self.pitch))}
