"""Read-only readiness checks. No event creation and no token/credential output."""
import argparse, os, sys
from pathlib import Path
from runtime_config import resolve_model

def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--firebase", action="store_true", help="Check actual Firebase access (read only)")
    args = parser.parse_args()
    for name in ("fire_best.pt", "plant_disease_best.pt"):
        path = resolve_model(name)
        print(f"PASS: {name} ({path.stat().st_size} bytes)")
    if args.firebase:
        from firebase_diagnostics import check_firebase
        return 0 if check_firebase() else 1
    return 0

if __name__ == "__main__":
    try:
        raise SystemExit(main())
    except Exception as exc:
        from firebase_diagnostics import describe_error
        print("FAIL [Readiness check]: " + describe_error(exc))
        raise SystemExit(1)
