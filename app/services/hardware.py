"""Read-only hardware inventory. No network, camera or microphone access."""

import json
import os
import platform
import subprocess

import psutil


def hardware_info() -> dict:
    info = {
        "os": platform.platform(),
        "python": platform.python_version(),
        "cpu": platform.processor() or "Unknown CPU",
        "logical_cpus": os.cpu_count(),
        "ram_gb": round(psutil.virtual_memory().total / 1024**3, 1),
        "gpu": "No NVIDIA GPU detected; CPU fallback planned for speech/LLM.",
    }
    flags = subprocess.CREATE_NO_WINDOW if os.name == "nt" else 0
    try:
        result = subprocess.run(
            ["nvidia-smi", "--query-gpu=name,memory.total,driver_version", "--format=csv,noheader"],
            capture_output=True,
            text=True,
            timeout=4,
            creationflags=flags,
            check=False,
        )
        if result.returncode == 0 and result.stdout.strip():
            info["gpu"] = result.stdout.strip()
    except (OSError, subprocess.TimeoutExpired):
        pass
    return info


if __name__ == "__main__":
    print(json.dumps(hardware_info(), indent=2))
