"""Only non-secret preferences belong in this schema."""

from dataclasses import asdict, dataclass
from urllib.parse import urlsplit

PROVIDERS = ("ollama", "openai", "gemini", "claude", "custom")
PROVIDER_DEFAULTS = {
    "ollama": ("http://127.0.0.1:11434", "qwen3:1.7b"),
    "openai": ("https://api.openai.com/v1", ""),
    "gemini": ("https://generativelanguage.googleapis.com/v1beta", ""),
    "claude": ("https://api.anthropic.com/v1", ""),
    "custom": ("", ""),
}


def validate_endpoint(value: str, *, local_only: bool = False) -> str:
    """Require TLS except on loopback. Reject embedded keys, queries and fragments."""
    if not isinstance(value, str):
        raise ValueError("Enter a valid provider URL.")
    value = value.strip().rstrip("/")
    try:
        parsed = urlsplit(value)
        port = parsed.port
    except ValueError as exc:
        raise ValueError("Enter a valid provider URL.") from exc
    if parsed.scheme not in ("http", "https") or not parsed.hostname:
        raise ValueError("The provider URL must start with http:// or https://.")
    if parsed.username or parsed.password or parsed.query or parsed.fragment:
        raise ValueError("Keep credentials, query strings and fragments out of the base URL.")
    loopback = parsed.hostname.lower() in ("localhost", "127.0.0.1", "::1")
    if (local_only or parsed.scheme == "http") and not loopback:
        raise ValueError("Offline endpoints must use loopback; remote endpoints require HTTPS.")
    if port == 0 or any(char.isspace() for char in value) or "\\" in value:
        raise ValueError("Enter a valid provider URL.")
    return value


@dataclass(frozen=True)
class Settings:
    provider: str = "ollama"
    mode: str = "offline"
    base_url: str = "http://127.0.0.1:11434"
    model: str = "qwen3:1.7b"
    fullscreen: bool = True
    quality: str = "balanced"
    motion: bool = True
    glow: float = 1.0
    particle_density: float = 1.0
    animation_speed: float = 1.0
    advanced_effects: bool = True
    voice_engine: str = "sapi"
    voice_id: str = ""
    voice_rate: int = 0
    speech_language: str = "auto"
    asr_model_path: str = ""
    microphone_id: str = ""

    def validate(self) -> "Settings":
        if self.provider not in PROVIDERS:
            raise ValueError("Unknown AI provider.")
        if self.mode not in ("offline", "online", "auto"):
            raise ValueError("Unknown connection preference.")
        if self.quality not in ("performance", "balanced", "high"):
            raise ValueError("Unknown rendering quality.")
        if type(self.fullscreen) is not bool or type(self.motion) is not bool:
            raise ValueError("Fullscreen and motion must be boolean values.")
        if type(self.glow) not in (float, int) or not 0.3 <= self.glow <= 1.8:
            raise ValueError("Hologram brightness must be between 0.3 and 1.8.")
        for value, name, lower, upper in (
            (self.particle_density, "Particle density", 0.25, 2.0),
            (self.animation_speed, "Animation speed", 0.25, 2.0),
        ):
            if type(value) not in (float, int) or not lower <= value <= upper:
                raise ValueError(f"{name} must be between {lower} and {upper}.")
        if type(self.advanced_effects) is not bool:
            raise ValueError("Advanced effects must be a boolean value.")
        if self.voice_engine != "sapi":
            raise ValueError("Only the installed Windows SAPI engine is supported.")
        if type(self.voice_rate) is not int or not -5 <= self.voice_rate <= 5:
            raise ValueError("Voice speed must be between -5 and 5; zero preserves the default.")
        if self.speech_language not in ("auto", "en", "si"):
            raise ValueError("Select automatic, English or Sinhala speech.")
        for value in (self.voice_id, self.asr_model_path, self.microphone_id):
            if not isinstance(value, str) or len(value) > 2048:
                raise ValueError("A device or model setting is invalid.")
        if not isinstance(self.model, str) or len(self.model) > 200:
            raise ValueError("The model name must be at most 200 characters.")
        if any(ord(char) < 32 for char in self.model):
            raise ValueError("The model name contains a control character.")
        validate_endpoint(self.base_url, local_only=self.mode == "offline")
        if self.mode == "offline" and self.provider != "ollama":
            raise ValueError("Offline mode uses Ollama. Select online or auto for an API provider.")
        return self

    def to_dict(self) -> dict:
        return asdict(self)
