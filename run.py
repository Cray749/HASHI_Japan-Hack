"""Start the cabin server: python run.py [--demo] [--port 8000]."""
import argparse
import os
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent
sys.path.insert(0, str(ROOT / "server"))


def main() -> None:
    ap = argparse.ArgumentParser()
    ap.add_argument("--port", type=int, default=int(os.environ.get("HASHI_PORT", "8000")))
    ap.add_argument("--host", default="0.0.0.0")
    ap.add_argument("--demo", action="store_true", help="seed the demo flight")
    args = ap.parse_args()
    os.environ["HASHI_PORT"] = str(args.port)
    if args.demo:
        os.environ["HASHI_DEMO"] = "1"

    import uvicorn

    from hashi.main import app, lan_ip

    print(f"\n  HASHI cabin server\n  crew tablet : http://{lan_ip()}:{args.port}/crew/"
          f"\n  passengers  : http://{lan_ip()}:{args.port}/p/\n")
    uvicorn.run(app, host=args.host, port=args.port, log_level="warning")


if __name__ == "__main__":
    main()
