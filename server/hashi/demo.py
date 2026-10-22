"""Mock Comfort Profiles for the demo flight (Delhi to Tokyo, Zone B).

Real profiles come from the passenger's own phone; these let the crew dashboard show a
believable cabin before any phone has joined. No real people are described here.
"""
from __future__ import annotations

from .store import Flight

PROFILES = [
    # seat, language, extra fields
    ("24C", "pa", {"senior": True, "first_time": True, "pictures_first": True, "needs": ["hearing", "veg"]}),
    ("24A", "pa", {"needs": ["veg"]}),
    ("24B", "hi", {"first_time": True}),
    ("18E", "hi", {"senior": True, "needs": ["mobility"]}),
    ("18F", "hi", {}),
    ("12F", "pa", {"senior": True, "needs": ["hearing"]}),
    ("12E", "pa", {}),
    ("15A", "hi", {"first_time": True, "pictures_first": True}),
    ("15B", "en", {}),
    ("21D", "hi", {"needs": ["veg"]}),
    ("21E", "pa", {"senior": True}),
    ("27C", "pa", {"first_time": True}),
    ("27D", "hi", {}),
    ("30A", "hi", {"senior": True, "needs": ["mobility", "hearing"]}),
]


def seed(flight: Flight) -> int:
    for seat, lang, extra in PROFILES:
        flight.register(seat, lang=lang, **extra)
    return len(PROFILES)
