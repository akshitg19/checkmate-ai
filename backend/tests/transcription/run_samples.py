"""Run every image in samples/ through transcribe_line and print the result.

Usage:
    python run_samples.py

Manually compare each output against what the image actually says, then
log misses in failures.md (category, expected, actual, notes).
"""
import base64
import sys
from pathlib import Path

sys.stdout.reconfigure(encoding="utf-8")
sys.path.insert(0, str(Path(__file__).resolve().parents[2]))

from transcription import transcribe_line

SAMPLES_DIR = Path(__file__).parent / "samples"
RESULTS_FILE = Path(__file__).parent / "results.txt"


def main():
    images = sorted(SAMPLES_DIR.glob("*.png")) + sorted(SAMPLES_DIR.glob("*.jpg"))
    if not images:
        print(f"No images found in {SAMPLES_DIR}")
        return

    lines = []
    for path in images:
        b64 = base64.b64encode(path.read_bytes()).decode()
        try:
            text, unreadable = transcribe_line(b64)
            result = f"{text}  [unreadable]" if unreadable else text
        except Exception as e:
            result = f"ERROR: {e}"
        line = f"{path.name:30s} -> {result}"
        print(line)
        lines.append(line)

    RESULTS_FILE.write_text("\n".join(lines), encoding="utf-8")


if __name__ == "__main__":
    main()
