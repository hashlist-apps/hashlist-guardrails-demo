"""Convenience entry point: python checker.py  (runs guardrails/checker.py)."""
import runpy
import sys
from pathlib import Path

if __name__ == "__main__":
    sys.argv[0] = str(Path(__file__).parent / "guardrails" / "checker.py")
    runpy.run_path(sys.argv[0], run_name="__main__")
