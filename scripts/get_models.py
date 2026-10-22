"""Download speech models into models/ (needs internet once; the server then runs offline).

    python scripts/get_models.py            # small (best accuracy on a laptop)
    python scripts/get_models.py base       # lighter, for slow machines
"""
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]


def main() -> None:
    size = sys.argv[1] if len(sys.argv) > 1 else "small"
    from faster_whisper.utils import download_model

    target = ROOT / "models" / f"whisper-{size}"
    target.mkdir(parents=True, exist_ok=True)
    path = download_model(size, output_dir=str(target))
    print(f"model ready: {path}")


if __name__ == "__main__":
    main()
