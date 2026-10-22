"""Start the cabin server.

    python run.py                 plain http on port 8000
    python run.py --https         https with a self-signed certificate (needed for the
                                  microphone on phones)
    python run.py --demo          also seed the demo flight with mock Comfort Profiles
"""
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
    ap.add_argument("--https", action="store_true", help="self-signed https (phone microphone)")
    ap.add_argument("--demo", action="store_true", help="seed the demo flight")
    args = ap.parse_args()
    os.environ["HASHI_PORT"] = str(args.port)
    os.environ["HASHI_SCHEME"] = "https" if args.https else "http"
    if args.demo:
        os.environ["HASHI_DEMO"] = "1"

    import uvicorn

    from hashi.main import app
    from hashi.netinfo import candidate_ips, lan_ip

    ip = lan_ip()
    ssl = {}
    if args.https:
        from hashi.cert import ensure_cert
        cert, key = ensure_cert(ROOT / "certs", candidate_ips())
        ssl = {"ssl_certfile": str(cert), "ssl_keyfile": str(key)}
    scheme = "https" if args.https else "http"
    print(f"\n  HASHI cabin server\n  crew tablet : {scheme}://{ip}:{args.port}/crew/"
          f"\n  passengers  : {scheme}://{ip}:{args.port}/p/\n")
    uvicorn.run(app, host=args.host, port=args.port, log_level="warning", **ssl)


if __name__ == "__main__":
    main()
