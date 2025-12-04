"""Utilities for selecting candidate flights."""

from __future__ import annotations

from typing import Iterable, List

from .flight_scraper import ScrapedFlight


class CheapestSelector:
    """Pick the three cheapest flights from a collection."""

    TOP_COUNT = 3

    @classmethod
    def select(cls, flights: Iterable[ScrapedFlight]) -> List[ScrapedFlight]:
        ordered = sorted(flights, key=lambda flight: flight.price)
        return ordered[: cls.TOP_COUNT]
