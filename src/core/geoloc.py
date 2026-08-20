"""IP geolocation helper."""

from __future__ import annotations

import aiohttp


async def geolocate(ip: str, session: aiohttp.ClientSession | None = None) -> str:
    if (
        ip in ("127.0.0.1", "::1", "localhost")
        or ip.startswith(("192.168.", "10.", "172.16.", "172.17.", "172.18.", "172.19.", "172.2", "172.3"))
    ):
        return "LOCAL_NETWORK"

    close = False
    if session is None:
        session = aiohttp.ClientSession()
        close = True
    try:
        url = f"http://ip-api.com/json/{ip}?fields=status,country,countryCode,city"
        async with session.get(url, timeout=aiohttp.ClientTimeout(total=3)) as r:
            if r.status == 200:
                d = await r.json()
                if d.get("status") == "success":
                    city = d.get("city")
                    country = d.get("country", "?")
                    code = d.get("countryCode", "??")
                    if city:
                        return f"{city}, {country} ({code})"
                    return f"{country} ({code})"
    except Exception:
        pass
    finally:
        if close:
            await session.close()
    return "UNKNOWN"
