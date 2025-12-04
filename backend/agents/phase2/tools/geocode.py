"""Shared geocoding utilities for Phase 2 agents."""

from __future__ import annotations

import asyncio
from functools import lru_cache
from typing import Optional, Tuple

from geopy.extra.rate_limiter import RateLimiter
from geopy.geocoders import Nominatim


_GEOCODER = Nominatim(user_agent="vibetravel-phase2", timeout=10)
_RATE_LIMITED = RateLimiter(_GEOCODER.geocode, min_delay_seconds=1.0, max_retries=2, error_wait_seconds=1.0, swallow_exceptions=True)


@lru_cache(maxsize=256)
def _geocode_sync(query: str) -> Optional[Tuple[float, float]]:
    if not query:
        return None
    location = _RATE_LIMITED(query, exactly_one=True, language="en")
    if not location:
        return None
    return float(location.latitude), float(location.longitude)


async def geocode_location(query: str) -> Optional[Tuple[float, float]]:
    """Return ``(latitude, longitude)`` for the given location text."""
    if not query:
        return None
    loop = asyncio.get_running_loop()
    return await loop.run_in_executor(None, _geocode_sync, query)
