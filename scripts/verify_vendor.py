"""Offline integrity check for the pinned, MIT-licensed Three.js distribution."""

import hashlib
from pathlib import Path

VENDOR = Path(__file__).resolve().parents[1] / "app" / "ui" / "web" / "vendor"
HASHES = {
    "three.module.js": "ce1fa418de16a19495a9f72495580e3015d7745c296d3ce0485897f902ddedfb",
    "THREE-LICENSE.txt": "4c40a1ef62450b857c3b2aaf294936304cd552d965fbcd9d32d4c5bcf4ba4454",
    "face-geometry.js": "7a1ce1b1a2354ac8a5864e6d1783cef4b3d1d6398c5f35e45387a04f68e97bde",
    "MEDIAPIPE-LICENSE.txt": "8707eef0533987efc5b155d64761eeb6e20793f50b9bd1a68dad1cf4719d0ed8",
    "LeePerrySmith_License.txt": "7cf4da43a6ae6d32f7f7d063fe129a19468af6f4fe7c53b937f83959709fcb50",
}


def main():
    for name, expected in HASHES.items():
        path = VENDOR / name
        if not path.is_file() or hashlib.sha256(path.read_bytes()).hexdigest() != expected:
            print(f"Bundled asset missing or modified: {name}")
            return 1
    print("Three.js, facial geometry and attribution: SHA-256 verified (offline).")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
