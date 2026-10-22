"""Find the address phones should use to reach this laptop."""
from __future__ import annotations

import ipaddress
import os
import socket


def _rank(ip: str) -> int:
    # Windows mobile hotspot is 192.168.137.x; other hotspots are usually 192.168.x or 10.x
    if ip.startswith("192.168.137."):
        return 0
    if ip.startswith("192.168."):
        return 1
    if ip.startswith("10."):
        return 2
    if ip.startswith("172."):
        return 3
    return 4


def candidate_ips() -> list[str]:
    """Private IPv4 addresses of this machine, hotspot-like ones first."""
    found: set[str] = set()
    try:
        for info in socket.getaddrinfo(socket.gethostname(), None, socket.AF_INET):
            found.add(info[4][0])
    except OSError:
        pass
    s = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
    try:
        s.connect(("10.255.255.255", 1))  # no packet is sent; this only picks an interface
        found.add(s.getsockname()[0])
    except OSError:
        pass
    finally:
        s.close()
    ips = []
    for ip in found:
        addr = ipaddress.ip_address(ip)
        if addr.is_private and not addr.is_loopback and not addr.is_link_local:
            ips.append(ip)
    return sorted(ips, key=lambda i: (_rank(i), i)) or ["127.0.0.1"]


def lan_ip() -> str:
    """HASHI_HOST_IP overrides the guess (set it if the QR shows the wrong address)."""
    return os.environ.get("HASHI_HOST_IP") or candidate_ips()[0]
