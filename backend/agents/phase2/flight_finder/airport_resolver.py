"""Airport resolution helpers for Phase 2 Flight Finder."""

from __future__ import annotations

import difflib
import logging
from dataclasses import dataclass, replace
from functools import lru_cache
from typing import List, Optional, Tuple

from airportsdata import load as load_airports
from geopy.distance import geodesic

from agents.phase2.tools.geocode import geocode_location


LOGGER = logging.getLogger("phase2.airport_resolver")
LOGGER.setLevel(logging.INFO)
DISALLOWED_NAME_KEYWORDS = (
    "heliport",
    "helipad",
    "helistop",
    "helicopter",
    "seaplane",
    "skyport",
    "seaport",
    "amphibious",
    "water aerodrome",
)


@dataclass(frozen=True)
class AirportCandidate:
    """Normalized information about a potential airport."""

    code: str
    name: str
    city: str
    country: str
    latitude: float
    longitude: float
    kind: str
    distance_km: Optional[float] = None

    @property
    def departure_id(self) -> str:
        return self.code

    @property
    def arrival_id(self) -> str:
        return self.code


class AirportResolver:
    """Resolve user-supplied locations into nearby airport candidates."""

    MAX_CANDIDATES = 2

    @classmethod
    @lru_cache(maxsize=1)
    def _airports(cls) -> dict[str, dict]:
        return load_airports("IATA")

    @classmethod
    @lru_cache(maxsize=1)
    def _airport_list(cls) -> List[AirportCandidate]:
        airports: List[AirportCandidate] = []
        for code, payload in cls._airports().items():
            city = (payload.get("city") or "").strip()
            lat = payload.get("lat") or payload.get("latitude")
            lon = payload.get("lon") or payload.get("longitude")
            if not city or lat is None or lon is None:
                continue
            if not _is_viable_airport(payload):
                continue
            candidate = AirportCandidate(
                code=code,
                name=payload.get("name", code),
                city=city,
                country=payload.get("country", ""),
                latitude=float(lat),
                longitude=float(lon),
                kind=str(payload.get("type") or "").lower(),
            )
            airports.append(candidate)
        return airports

    @classmethod
    @lru_cache(maxsize=1)
    def _city_index(cls) -> dict[str, list[AirportCandidate]]:
        index: dict[str, list[AirportCandidate]] = {}
        for candidate in cls._airport_list():
            index.setdefault(candidate.city.lower(), []).append(candidate)
        for candidates in index.values():
            candidates.sort(key=_airport_priority)
        return index

    @classmethod
    def _nearby_by_city(cls, city: str) -> List[AirportCandidate]:
        index = cls._city_index()
        lower = city.lower()
        if lower in index:
            return index[lower][: cls.MAX_CANDIDATES]

        matches = difflib.get_close_matches(lower, list(index.keys()), n=3, cutoff=0.7)
        seen: set[str] = set()
        ordered: list[AirportCandidate] = []
        for match in matches:
            for candidate in index.get(match, []):
                if candidate.code in seen:
                    continue
                ordered.append(candidate)
                seen.add(candidate.code)
                if len(ordered) >= cls.MAX_CANDIDATES:
                    return ordered
        return ordered

    @classmethod
    def get_closest_airports_by_coordinates(cls, latitude: float, longitude: float) -> List[AirportCandidate]:
        ranked: List[Tuple[float, AirportCandidate]] = []
        origin = (latitude, longitude)
        for candidate in cls._airport_list():
            distance_km = geodesic(origin, (candidate.latitude, candidate.longitude)).kilometers
            ranked.append((distance_km, candidate))

        ranked.sort(key=lambda item: (item[0], _airport_priority(item[1])))
        trimmed: List[AirportCandidate] = []
        for distance, candidate in ranked[: cls.MAX_CANDIDATES]:
            trimmed.append(replace(candidate, distance_km=round(distance, 2)))
        return trimmed

    @classmethod
    async def get_closest_airports(cls, city: Optional[str]) -> List[AirportCandidate]:
        """Return up to two airports sorted by distance for the supplied location."""
        if not city:
            return []

        coords = await geocode_location(city)
        if coords:
            airports = cls.get_closest_airports_by_coordinates(coords[0], coords[1])
            if airports:
                LOGGER.info(
                    "Resolved airport candidates for %s -> %s",
                    city,
                    ", ".join(candidate.code for candidate in airports),
                )
            return airports

        airports = cls._nearby_by_city(city)
        if airports:
            LOGGER.info(
                "Resolved airport candidates for %s via fuzzy city match -> %s",
                city,
                ", ".join(candidate.code for candidate in airports),
            )
        return airports


def _airport_priority(airport: AirportCandidate) -> tuple[int, int]:
    name = airport.name.lower()

    type_priority = {
        "large_airport": 0,
        "airport": 1,
        "medium_airport": 1,
        "small_airport": 2,
        "": 3,
    }
    type_score = type_priority.get(airport.kind, 3)

    international_score = 0 if "international" in name else 1

    regional_penalty = 1 if any(keyword in name for keyword in ("regional", "municipal", "county", "private")) else 0

    name_length_score = len(name)

    return type_score, international_score + regional_penalty, name_length_score


def _is_viable_airport(payload: dict) -> bool:
    """Return True when the airport entry appears usable for commercial flights."""

    name = (payload.get("name") or "").lower()
    if any(keyword in name for keyword in DISALLOWED_NAME_KEYWORDS):
        return False

    airport_type = (payload.get("type") or "").lower()
    if airport_type and airport_type not in {"airport", "large_airport", "medium_airport", "small_airport"}:
        return False

    iata = payload.get("iata") or payload.get("iata_code")
    if not iata:
        return False

    return True
