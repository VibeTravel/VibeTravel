"""Utilities for normalising and validating city names for Phase 2 supervisor."""

from __future__ import annotations

from functools import lru_cache
from typing import Optional
import difflib

from airportsdata import load as load_airports

from agents.phase2.tools.geocode import geocode_location
from agents.phase2.flight_finder.airport_resolver import AirportResolver


@lru_cache(maxsize=1)
def _known_cities() -> dict[str, str]:
    """Return a mapping of lower-case city names to their canonical form."""
    data = load_airports("IATA")
    mapping: dict[str, str] = {}
    for payload in data.values():
        city = (payload.get("city") or "").strip()
        if not city:
            continue
        lower = city.lower()
        # Preserve the first encountered canonical casing to keep output stable
        mapping.setdefault(lower, city)
    return mapping


async def resolve_city_name(city: Optional[str]) -> Optional[str]:
    """Resolve user-supplied city text to a canonical city name.

    A return value of ``None`` indicates we could not confidently match the input.
    """
    if not city:
        return None

    normalised = " ".join(str(city).split())
    if not normalised:
        return None

    cities = _known_cities()
    lower = normalised.lower()

    if lower in cities:
        return cities[lower]

    candidates = difflib.get_close_matches(lower, list(cities.keys()), n=1, cutoff=0.82)
    if candidates:
        return cities[candidates[0]]

    coords = await geocode_location(normalised)
    if coords:
        airports = AirportResolver.get_closest_airports_by_coordinates(coords[0], coords[1])
        if airports:
            resolved = airports[0].city
            lower_resolved = resolved.lower()
            return cities.get(lower_resolved, resolved)

    return None
