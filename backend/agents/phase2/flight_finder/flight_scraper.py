"""Async SerpAPI scraper with fallback handling for Phase 2 Flight Finder."""

from __future__ import annotations

from dataclasses import dataclass
import json
import logging
from typing import Any, Dict, List, Optional, Tuple

import httpx


class FlightScraperError(Exception):
    """Raised when SerpAPI cannot be queried successfully."""


@dataclass
class ScrapedFlight:
    """Normalized flight information used internally by the flight finder."""

    id: str
    airline: str
    price: float
    currency: str
    outbound_departure_time: str
    outbound_arrival_time: str
    return_departure_time: Optional[str]
    return_arrival_time: Optional[str]
    total_duration: str
    outbound_stops: int
    return_stops: int
    departure_airport: str
    arrival_airport: str
    outbound_route: List[str]
    return_route: List[str]
    booking_url: str
    raw: Dict[str, Any]

    @property
    def dedupe_key(self) -> Tuple[str, str, str, Optional[str], str, float]:
        return (
            self.departure_airport,
            self.arrival_airport,
            self.outbound_departure_time,
            self.return_departure_time,
            self.airline,
            self.price,
        )


class FlightScraper:
    """Fetch round-trip flight information from SerpAPI."""

    API_URL = "https://serpapi.com/search"

    LOGGER = logging.getLogger("phase2.flight_scraper")
    LOGGER.setLevel(logging.INFO)
    if not LOGGER.handlers:
        _handler = logging.StreamHandler()
        _handler.setFormatter(
            logging.Formatter("%(asctime)s [%(levelname)s] %(name)s: %(message)s")
        )
        LOGGER.addHandler(_handler)

    def __init__(self, api_key: Optional[str]) -> None:
        if not api_key:
            raise FlightScraperError("SERPAPI_KEY not configured")
        self._api_key = api_key

    async def scrape_round_trip(
        self,
        *,
        departure_id: str,
        arrival_id: str,
        outbound_date: str,
        return_date: Optional[str],
        stops: int,
        adults: int,
    ) -> List[ScrapedFlight]:
        params = self._build_params(
            departure_id=departure_id,
            arrival_id=arrival_id,
            outbound_date=outbound_date,
            return_date=return_date,
            stops=stops,
            adults=adults,
        )

        async with httpx.AsyncClient(timeout=httpx.Timeout(30.0)) as client:
            try:
                response = await client.get(self.API_URL, params=params)
            except httpx.TimeoutException as exc:
                raise FlightScraperError("SerpAPI request timed out") from exc
            except httpx.HTTPError as exc:
                raise FlightScraperError(f"SerpAPI request failed: {exc}") from exc

        payload = self._parse_response(response)
        flights = self._extract_flights(payload)

        normalised: List[ScrapedFlight] = []
        for item in flights:
            try:
                enriched_item = item
                if return_date and not self._has_return_segments(item) and item.get("departure_token"):
                    try:
                        return_segments = await self._fetch_return_segments(item["departure_token"])
                        if return_segments:
                            self.LOGGER.info(
                                "Fetched %d return segments via departure_token", len(return_segments)
                            )
                            enriched_item = {**item, "return_flights": return_segments}
                        else:
                            self.LOGGER.warning("No return segments found for departure_token")
                    except FlightScraperError as exc:
                        self.LOGGER.warning("Return-flight fetch failed: %s", exc)

                normalised.append(self._normalise_item(enriched_item, departure_id, arrival_id))
            except ValueError:
                # Skip flights we cannot normalise; keep the search resilient
                continue

        return normalised

    def _build_params(
        self,
        *,
        departure_id: str,
        arrival_id: str,
        outbound_date: str,
        return_date: Optional[str],
        stops: int,
        adults: int,
    ) -> Dict[str, Any]:
        params: Dict[str, Any] = {
            "engine": "google_flights",
            "departure_id": departure_id,
            "arrival_id": arrival_id,
            "outbound_date": outbound_date,
            "currency": "USD",
            "adults": adults,
            "api_key": self._api_key,
            "stops": stops,
            # use "1" for round-trip when return date present, else "2" for one-way per SerpAPI docs
            "type": 1 if return_date else 2,
        }
        if return_date:
            params["return_date"] = return_date
        return params

    @staticmethod
    def _parse_response(response: httpx.Response) -> Dict[str, Any]:
        try:
            payload = response.json()
        except json.JSONDecodeError as exc:
            raise FlightScraperError("SerpAPI returned malformed JSON") from exc

        if response.status_code != 200:
            error_text = payload.get("error") or payload.get("raw_html") or "Unknown error"
            raise FlightScraperError(f"SerpAPI HTTP {response.status_code}: {error_text}")

        if "error" in payload:
            raise FlightScraperError(f"SerpAPI error: {payload['error']}")

        return payload

    @staticmethod
    def _extract_flights(payload: Dict[str, Any]) -> List[Dict[str, Any]]:
        flights = payload.get("best_flights") or []
        if payload.get("other_flights"):
            flights.extend(payload["other_flights"])
        return flights

    @staticmethod
    def _has_return_segments(item: Dict[str, Any]) -> bool:
        return bool(
            item.get("return_flights")
            or item.get("inbound_flights")
            or item.get("return_flight")
        )

    async def _fetch_return_segments(self, departure_token: str) -> List[Dict[str, Any]]:
        params = {
            "engine": "google_flights",
            "departure_token": departure_token,
            "api_key": self._api_key,
        }

        async with httpx.AsyncClient(timeout=httpx.Timeout(30.0)) as client:
            try:
                response = await client.get(self.API_URL, params=params)
            except httpx.TimeoutException as exc:
                raise FlightScraperError("SerpAPI return-flight request timed out") from exc
            except httpx.HTTPError as exc:
                raise FlightScraperError(f"SerpAPI return-flight request failed: {exc}") from exc

        payload = self._parse_response(response)
        return (
            payload.get("return_flights")
            or payload.get("flights")
            or payload.get("other_flights")
            or []
        )

    @staticmethod
    def _normalise_item(item: Dict[str, Any], origin_code: str, dest_code: str) -> ScrapedFlight:
        price = _parse_price(item.get("price"))
        if price is None:
            raise ValueError("Flight missing price")

        flights = item.get("flights") or []

        outbound_segments = (
            item.get("departure_flights")
            or item.get("outbound_flights")
            or item.get("outbound_flight")
            or []
        )
        return_segments = (
            item.get("return_flights")
            or item.get("inbound_flights")
            or item.get("return_flight")
            or []
        )

        if not outbound_segments and not return_segments:
            outbound_segments, return_segments = _partition_segments(flights)
        elif not outbound_segments:
            outbound_segments, _ = _partition_segments(flights)
        elif not return_segments:
            _, return_segments = _partition_segments(flights)

        outbound_departure_time, outbound_arrival_time, outbound_departure_airport, outbound_arrival_airport = _segment_bounds(
            outbound_segments,
            default_origin=origin_code,
            default_dest=dest_code,
        )
        return_departure_time, return_arrival_time, return_departure_airport, return_arrival_airport = _segment_bounds(
            return_segments,
            default_origin=dest_code,
            default_dest=origin_code,
        )

        outbound_route = _segment_route(outbound_segments, origin_code, dest_code)
        return_route = _segment_route(return_segments, dest_code, origin_code) if return_segments else []

        airline = _determine_airline(outbound_segments + return_segments, fallback=item.get("airline", "Unknown"))
        total_duration = _humanize_minutes(item.get("total_duration"))
        booking_url = _build_booking_url(item, origin_code, dest_code)

        outbound_stops = max(len(outbound_segments) - 1, 0) if outbound_segments else 0
        return_stops = max(len(return_segments) - 1, 0) if return_segments else 0

        identifier = item.get("booking_token") or _build_identifier(
            outbound_departure_airport,
            outbound_arrival_airport,
            outbound_departure_time,
            return_departure_time,
            airline,
            price,
        )

        return ScrapedFlight(
            id=str(identifier),
            airline=airline,
            price=float(price),
            currency="USD",
            outbound_departure_time=outbound_departure_time,
            outbound_arrival_time=outbound_arrival_time,
            return_departure_time=return_departure_time,
            return_arrival_time=return_arrival_time,
            total_duration=total_duration,
            outbound_stops=outbound_stops,
            return_stops=return_stops,
            departure_airport=outbound_departure_airport,
            arrival_airport=outbound_arrival_airport,
            outbound_route=outbound_route,
            return_route=return_route,
            booking_url=booking_url,
            raw=item,
        )


def _parse_price(raw_price: Any) -> Optional[float]:
    if raw_price is None:
        return None
    if isinstance(raw_price, (int, float)):
        return float(raw_price)
    if isinstance(raw_price, str):
        cleaned = "".join(ch for ch in raw_price if ch.isdigit() or ch == ".")
        if not cleaned:
            return None
        try:
            return float(cleaned)
        except ValueError:
            return None
    return None


def _partition_segments(segments: List[Dict[str, Any]]) -> Tuple[List[Dict[str, Any]], List[Dict[str, Any]]]:
    if not segments:
        return [], []

    outbound: List[Dict[str, Any]] = []
    inbound: List[Dict[str, Any]] = []

    for segment in segments:
        seg_type = str(segment.get("type") or segment.get("segment_type") or "").lower()
        if "return" in seg_type:
            inbound.append(segment)
        elif "outbound" in seg_type:
            outbound.append(segment)
        else:
            outbound.append(segment)

    if inbound:
        return outbound or segments, inbound

    if len(segments) > 2:
        half = max(len(segments) // 2, 1)
        return segments[:half], segments[half:]

    return segments, []


def _segment_bounds(
    segments: List[Dict[str, Any]],
    *,
    default_origin: str,
    default_dest: str,
) -> Tuple[str, str, str, str]:
    if not segments:
        return "Unknown", "Unknown", default_origin, default_dest

    first = segments[0]
    last = segments[-1]

    departure_time = _extract_time(first, "departure")
    arrival_time = _extract_time(last, "arrival")
    departure_airport = _extract_airport_code(first, "departure", default_origin)
    arrival_airport = _extract_airport_code(last, "arrival", default_dest)
    return departure_time, arrival_time, departure_airport, arrival_airport


def _segment_route(
    segments: List[Dict[str, Any]],
    default_origin: str,
    default_dest: str,
) -> List[str]:
    if not segments:
        return [default_origin, default_dest]

    path: List[str] = []
    current_origin = default_origin
    for index, segment in enumerate(segments):
        departure_code = _extract_airport_code(segment, "departure", current_origin)
        arrival_default = default_dest if index == len(segments) - 1 else current_origin
        arrival_code = _extract_airport_code(segment, "arrival", arrival_default)

        if not path or path[-1] != departure_code:
            path.append(departure_code)
        path.append(arrival_code)
        current_origin = arrival_code

    if len(path) == 1:
        path.append(default_dest)
    return path


def _extract_airport_code(segment: Dict[str, Any], role: str, default: str) -> str:
    keys = [
        f"{role}_airport",
        f"{role}_airport_code",
        f"{role}_code",
        f"{role}Airport",
        f"{role}Code",
    ]

    for key in keys:
        value = segment.get(key)
        if isinstance(value, dict):
            for sub_key in ("id", "code", "iata", "iata_code"):
                if value.get(sub_key):
                    return str(value[sub_key])
        elif isinstance(value, str) and value:
            return value

    return default


def _determine_airline(segments: List[Dict[str, Any]], fallback: str) -> str:
    airlines = {seg.get("airline") for seg in segments if seg.get("airline")}
    if airlines:
        return ", ".join(sorted(airlines))
    return fallback or "Unknown"


def _humanize_minutes(minutes: Any) -> str:
    if not isinstance(minutes, (int, float)):
        return "Unknown"
    total = int(minutes)
    hours, remainder = divmod(total, 60)
    parts: List[str] = []
    if hours:
        parts.append(f"{hours}h")
    if remainder:
        parts.append(f"{remainder}m")
    return " ".join(parts) if parts else "0m"


def _build_booking_url(item: Dict[str, Any], origin: str, destination: str) -> str:
    token = item.get("booking_token")
    if token:
        return f"https://www.google.com/travel/flights/booking?token={token}"
    return f"https://www.google.com/travel/flights?q=Flights%20from%20{origin}%20to%20{destination}"


def _build_identifier(
    origin: str,
    destination: str,
    outbound_departure: str,
    return_departure: Optional[str],
    airline: str,
    price: float,
) -> str:
    parts = [origin, destination, outbound_departure or "", return_departure or "", airline, f"{price:.2f}"]
    return "|".join(parts)


def _extract_time(segment: Dict[str, Any], role: str) -> str:
    keys = [
        f"{role}_airport",
        f"{role}_time",
        f"{role}_time_utc",
        f"{role}_time_local",
        f"{role}_datetime",
        f"{role}_date_time",
        f"{role}Time",
        f"{role}TimeUtc",
    ]

    for key in keys:
        value = segment.get(key)
        if isinstance(value, dict):
            for sub_key in ("time", "time_text", "local_time", "formatted", "value"):
                if sub_key in value and value[sub_key]:
                    return str(value[sub_key])
        elif isinstance(value, str) and value:
            return value

    # Fallback: scan for any string containing role and time
    role_lower = role.lower()
    for key, value in segment.items():
        if isinstance(value, str) and role_lower in key.lower() and "time" in key.lower() and value:
            return value

    return "Unknown"
