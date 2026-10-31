"""
gps.py — best-effort real location for the laptop detector.

A laptop has no GPS chip, so we resolve the machine's approximate location
from its public IP (city-level accuracy). Tries several providers (HTTPS
first, since plain-HTTP ip-api is often blocked) and caches the result.
Falls back to (0.0, 0.0) if all fail / offline.
"""

from __future__ import annotations

import json
import urllib.request

_cached: tuple[float, float] | None = None


def _fetch(url: str, parse, timeout: float):
    req = urllib.request.Request(url, headers={"User-Agent": "AgroSentinel/1.0"})
    with urllib.request.urlopen(req, timeout=timeout) as resp:
        data = json.loads(resp.read().decode())
    return parse(data)


def get_coordinates(timeout: float = 6.0) -> tuple[float, float]:
    """Return (latitude, longitude) via IP geolocation. Cached after first call."""
    global _cached
    if _cached is not None:
        return _cached

    providers = [
        # (url, parser -> (lat, lon, label))
        ("https://ipapi.co/json/",
         lambda d: (float(d["latitude"]), float(d["longitude"]),
                    f"{d.get('city')}, {d.get('country_name')}")),
        ("https://ipwho.is/",
         lambda d: (float(d["latitude"]), float(d["longitude"]),
                    f"{d.get('city')}, {d.get('country')}")),
        ("https://ipinfo.io/json",
         lambda d: (float(d["loc"].split(",")[0]), float(d["loc"].split(",")[1]),
                    f"{d.get('city')}, {d.get('country')}")),
        ("http://ip-api.com/json/",
         lambda d: (float(d["lat"]), float(d["lon"]),
                    f"{d.get('city')}, {d.get('country')}")),
    ]

    for url, parser in providers:
        try:
            lat, lon, label = _fetch(url, parser, timeout)
            _cached = (lat, lon)
            print(f"[gps] Location via IP ({url.split('/')[2]}): {label} "
                  f"-> {lat:.5f}, {lon:.5f}")
            return _cached
        except Exception as e:
            print(f"[gps] {url.split('/')[2]} failed: {e}")

    print("[gps] All providers failed; using 0.0, 0.0")
    _cached = (0.0, 0.0)
    return _cached


if __name__ == "__main__":
    print(get_coordinates())
