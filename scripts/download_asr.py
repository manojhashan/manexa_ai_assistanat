"""Explicit model provisioning; the application never downloads weights on its own."""

import argparse
from pathlib import Path


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--model", choices=("base", "small"), default="base")
    parser.add_argument("--directory", type=Path, default=Path("models/whisper-base"))
    args = parser.parse_args()
    from huggingface_hub import snapshot_download

    destination = args.directory.resolve()
    print(f"Downloading multilingual Whisper {args.model} weights to {destination}")
    snapshot_download(
        f"Systran/faster-whisper-{args.model}",
        local_dir=str(destination),
        allow_patterns=["*.json", "*.txt", "model.bin", "README.md"],
    )
    print("Select this folder in Settings > Voice & camera. No microphone was opened.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
