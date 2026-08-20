"""Asynchronous IP geolocation helpers."""

from __future__ import annotations

import aiohttp


async def geolocate(ip: str, session: aiohttp.ClientSession | None = None) -> str:
    """Return a human-readable location string for an IP address."""
    if (
        ip in ("127.0.0.1", "::1", "localhost")
        or ip.startswith("192.168.")
        or ip.startswith("10.")
        or ip.startswith("172.16.")
        or ip.startswith("172.17.")
        or ip.startswith("172.18.")
        or ip.startswith("172.19.")
        or ip.startswith("172.2")
        or ip.startswith("172.3")
    ):
        return "LOCAL_NETWORK"

    close_session = False
    if session is None:
        session = aiohttp.ClientSession()
        close_session = True

    try:
        # ip-api.com free endpoint (HTTPS)
        url = f"http://ip-api.com/json/{ip}?fields=status,country,countryCode,city,isp"
        async with session.get(url, timeout=aiohttp.ClientTimeout(total=3)) as resp:
            if resp.status == 200:
                data = await resp.json()
                if data.get("status") == "success":
                    country = data.get("country", "?")
                    code = data.get("countryCode", "??")
                    city = data.get("city")
                    if city:
                        return f"{city}, {country} ({code})"
                    return f"{country} ({code})"
    except Exception:
        pass
    finally:
        if close_session:
            await session.close()

    return "UNKNOWN"
