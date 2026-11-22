"""Check that a wheel contains all active renderer assets and no obsolete cached assets."""

import argparse
from pathlib import Path
from zipfile import ZipFile

from app.ui.assets import REQUIRED_ASSETS


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("wheel", type=Path)
    args = parser.parse_args()
    expected = {f"app/ui/web/{name}" for name in REQUIRED_ASSETS}
    with ZipFile(args.wheel) as wheel:
        actual = {name for name in wheel.namelist() if name.startswith("app/ui/web/")}
    if actual != expected:
        print("Missing renderer assets:", sorted(expected - actual))
        print("Unexpected renderer assets:", sorted(actual - expected))
        return 1
    print(f"Package verified: {len(actual)} active orb assets; no legacy avatar assets.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
