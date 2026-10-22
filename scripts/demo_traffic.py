"""Fire demo requests from fake passengers, so the crew dashboard can be shown without phones.

    python scripts/demo_traffic.py water          # seat 24C asks for water
    python scripts/demo_traffic.py help 12F       # seat 12F presses the big help button
    python scripts/demo_traffic.py sequence       # a short scripted run of requests
    python scripts/demo_traffic.py ack            # every seeded seat confirms the newest announcement
    python scripts/demo_traffic.py ack 24C 18E    # only these seats confirm (leaves the rest waiting)
Needs the server to be running with `make demo`.
"""
import asyncio
import json
import sys
import time
import urllib.request

import websockets

HOST = "127.0.0.1:8000"
SEQUENCE = [("24C", "water"), ("18E", "blanket"), ("21D", "veg_meal"), ("12F", "unwell"), ("15A", "toilet")]


async def request(seat: str, intent: str) -> None:
    async with websockets.connect(f"ws://{HOST}/ws/passenger?seat={seat}") as ws:
        await ws.send(json.dumps({"t": "hello"}))
        await ws.recv()
        await ws.send(json.dumps({"t": "request", "intent": intent, "via": "tap"}))
        await ws.recv()
        print(f"{seat} -> {intent}")


async def ack_all(only: list[str]) -> None:
    snap = json.load(urllib.request.urlopen(f"http://{HOST}/api/health"))
    print("server ok:", snap["ok"])
    async with websockets.connect(f"ws://{HOST}/ws/crew") as crew:
        data = json.loads(await crew.recv())
    anns = data["announcements"]
    if not anns:
        print("no announcements yet")
        return
    ann = anns[-1]
    for seat in [s for s in ann["acks"] if not only or s in only]:
        async with websockets.connect(f"ws://{HOST}/ws/passenger?seat={seat}") as ws:
            await ws.send(json.dumps({"t": "ack", "ann_id": ann["id"]}))
            await asyncio.sleep(0.15)
        print(f"{seat} understood")


async def main() -> None:
    args = sys.argv[1:] or ["sequence"]
    if args[0] == "sequence":
        for seat, intent in SEQUENCE:
            await request(seat, intent)
            time.sleep(1.5)
    elif args[0] == "ack":
        await ack_all([x.upper() for x in args[1:]])
    else:
        await request(args[1] if len(args) > 1 else "24C", args[0])


if __name__ == "__main__":
    asyncio.run(main())
