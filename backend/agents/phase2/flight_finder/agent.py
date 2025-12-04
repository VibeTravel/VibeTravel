"""Async Phase 2 Flight Finder orchestration."""

from __future__ import annotations

from dataclasses import asdict, dataclass
from datetime import date, datetime
from typing import Any, Dict, List, Optional, Tuple
import json
import logging
import os
import re

from dotenv import load_dotenv
from openai import AsyncOpenAI

from .flight_scraper import FlightScraper, FlightScraperError, ScrapedFlight
from .selector import CheapestSelector
from .ai_ranker import AIRanker

load_dotenv()

MIN_FLIGHTS_TARGET = 5
STOP_SEQUENCE = (1, 2)  # SerpAPI: 1 => direct, 2 => at most one connection

LOGGER = logging.getLogger("phase2.flight_finder")
LOGGER.setLevel(logging.INFO)
if not LOGGER.handlers:
    _handler = logging.StreamHandler()
    _handler.setFormatter(
        logging.Formatter("%(asctime)s [%(levelname)s] %(name)s: %(message)s")
    )
    LOGGER.addHandler(_handler)
AIRPORT_MODEL = "gpt-4o-mini"

_AIRPORT_CACHE: Dict[str, Tuple["LLMAirport", ...]] = {}


async def flight_finder(req: Dict[str, Any]) -> Dict[str, Any]:
    """Entry point consumed by the supervisor layer."""
    payload = _validate_request(req)

    try:
        scraper = FlightScraper(os.getenv("SERPAPI_KEY"))
    except FlightScraperError as exc:
        raise ValueError(str(exc)) from exc

    ranker = AIRanker(os.getenv("OPENAI_API_KEY"))
    airport_client = _build_airport_client()

    origin_airports = await _resolve_airports_with_llm(payload["from_city"], airport_client)
    destination_airports = await _resolve_airports_with_llm(payload["to_city"], airport_client)

    LOGGER.debug(
        "Flight finder received cities %s -> %s",
        payload["from_city"],
        payload["to_city"],
    )

    if not origin_airports:
        raise ValueError(f"No airports found near {payload['from_city']}")
    if not destination_airports:
        raise ValueError(f"No airports found near {payload['to_city']}")

    LOGGER.info(
        "Current: [%s]\nTravel: [%s]",
        ",".join(airport.code for airport in origin_airports),
        ",".join(airport.code for airport in destination_airports),
    )

    combos = _build_combo_plan(origin_airports, destination_airports)
    if not combos:
        raise ValueError("Unable to build airport combinations for search")

    LOGGER.debug("Prepared %d route combinations", len(combos))

    gathered: List[ScrapedFlight] = []
    warnings: List[str] = []
    seen: set[Tuple[str, str, str, Optional[str], str, float]] = set()
    attempt_log: List[Dict[str, Any]] = []
    attempted_keys: set[Tuple[str, str, int]] = set()

    # Fallback order: 00, 01, 10, 11 with two stop settings per combination
    for combo in combos:
        if len(gathered) >= MIN_FLIGHTS_TARGET:
            break

        for stops in STOP_SEQUENCE:
            if len(gathered) >= MIN_FLIGHTS_TARGET:
                break

            attempt_key = (combo.origin.code, combo.destination.code, stops)
            if attempt_key in attempted_keys:
                continue
            attempted_keys.add(attempt_key)

            attempt_entry = {
                "origin": combo.origin.code,
                "destination": combo.destination.code,
                "stops": stops,
                "status": "pending",
                "flights_added": 0,
            }

            try:
                flights = await scraper.scrape_round_trip(
                    departure_id=combo.origin.code,
                    arrival_id=combo.destination.code,
                    outbound_date=payload["outbound_date"],
                    return_date=payload["return_date"],
                    stops=stops,
                    adults=payload["travellers"],
                )
            except FlightScraperError as exc:
                attempt_entry["status"] = "error"
                attempt_entry["error"] = str(exc)
                message = f"{combo.origin.code}->{combo.destination.code} (stop = {stops}) = 0"
                attempt_entry["message"] = message
                LOGGER.info(message)
                attempt_log.append(attempt_entry)
                continue

            added = 0
            for flight in flights:
                if flight.dedupe_key in seen:
                    continue
                seen.add(flight.dedupe_key)
                gathered.append(flight)
                added += 1
                if len(gathered) >= MIN_FLIGHTS_TARGET:
                    break

            attempt_entry["status"] = "success" if added else "empty"
            attempt_entry["flights_added"] = added
            attempt_entry["message"] = (
                f"{combo.origin.code}->{combo.destination.code} (stop = {stops}) = {added}"
            )
            LOGGER.info(attempt_entry["message"])
            attempt_log.append(attempt_entry)

    if not gathered:
        return {
            "status": "no_results",
            "message": "No flights found for the supplied cities and dates.",
            "dropdownFlights": [],
            "candidateFlights": [],
            "metadata": _build_metadata(
                payload, origin_airports, destination_airports, attempt_log, warnings, gathered
            ),
        }

    candidates = CheapestSelector.select(gathered)
    ranked = await ranker.rank(
        candidates,
        context={
            "travellers": payload["travellers"],
            "attemptedRoutes": attempt_log,
        },
        budget=payload["budget"],
    )

    candidate_payload = [_format_flight(flight, payload["budget"]) for flight in candidates]
    dropdown_payload = [_format_flight(flight, payload["budget"]) for flight in ranked]

    metadata = _build_metadata(
        payload,
        origin_airports,
        destination_airports,
        attempt_log,
        warnings,
        gathered,
    )

    if all(flight["overBudget"] for flight in dropdown_payload) and dropdown_payload:
        metadata["note"] = (
            "All suggested flights currently exceed the provisional budget. "
            "Costs shown for awareness."
        )

    return {
        "status": "success",
        "dropdownFlights": dropdown_payload,
        "candidateFlights": candidate_payload,
        "metadata": metadata,
    }


class _Combo:
    """Represents a single origin/destination fallback pairing."""

    def __init__(self, origin: "LLMAirport", destination: "LLMAirport") -> None:
        self.origin = origin
        self.destination = destination


def _build_combo_plan(
    origins: List["LLMAirport"],
    destinations: List["LLMAirport"],
) -> List[_Combo]:
    combos: List[_Combo] = []
    seen: set[tuple[str, str]] = set()

    def append_if_available(o_index: int, d_index: int) -> None:
        try:
            origin = origins[o_index]
            destination = destinations[d_index]
        except IndexError:
            return
        key = (origin.code, destination.code)
        if key in seen:
            return
        seen.add(key)
        combos.append(_Combo(origin, destination))

    append_if_available(0, 0)
    append_if_available(0, 1)
    append_if_available(1, 0)
    append_if_available(1, 1)

    return combos


def _validate_request(req: Dict[str, Any]) -> Dict[str, Any]:
    def _extract(keys: List[str]) -> Any:
        for key in keys:
            if key in req:
                return req[key]
        return None

    from_city = _normalise_city(_extract(["fromCity", "from_city"]))
    to_city = _normalise_city(_extract(["toCity", "to_city"]))
    if not from_city or not to_city:
        raise ValueError("Both fromCity and toCity are required")
    if from_city.lower() == to_city.lower():
        raise ValueError("Origin and destination cities must differ")

    travellers_raw = _extract(["travellers", "travelers"])
    try:
        travellers = int(travellers_raw)
    except (TypeError, ValueError) as exc:
        raise ValueError("travellers must be a positive integer") from exc
    if travellers <= 0:
        raise ValueError("travellers must be at least 1")

    budget_raw = _extract(["budgetForFlightFinder", "budget_for_flight_finder", "budget"])
    try:
        budget = float(budget_raw)
    except (TypeError, ValueError) as exc:
        raise ValueError("budgetForFlightFinder must be a positive number") from exc
    if budget <= 0:
        raise ValueError("budgetForFlightFinder must be greater than zero")

    outbound_date = _ensure_date(_extract(["outboundDate", "outbound_date"]), "outboundDate")
    return_date_value = _extract(["returnDate", "return_date"])
    return_date = None
    if return_date_value:
        return_date = _ensure_date(return_date_value, "returnDate")
        if return_date < outbound_date:
            raise ValueError("returnDate cannot be earlier than outboundDate")

    today = date.today()
    if outbound_date < today:
        raise ValueError("outboundDate cannot be in the past")
    if return_date and return_date < today:
        raise ValueError("returnDate cannot be in the past")

    return {
        "from_city": from_city,
        "to_city": to_city,
        "travellers": travellers,
        "budget": budget,
        "outbound_date": outbound_date.isoformat(),
        "return_date": return_date.isoformat() if return_date else None,
    }


def _normalise_city(value: Any) -> Optional[str]:
    if value is None:
        return None
    text = " ".join(str(value).split())
    return text if text else None


def _ensure_date(raw: Any, label: str) -> date:
    if not raw:
        raise ValueError(f"{label} is required")
    try:
        parsed = datetime.strptime(str(raw), "%Y-%m-%d").date()
    except ValueError as exc:
        raise ValueError(f"{label} must be in YYYY-MM-DD format") from exc
    return parsed


def _format_flight(flight: ScrapedFlight, budget: float) -> Dict[str, Any]:
    outbound_info = {
        "departureAirport": flight.departure_airport,
        "arrivalAirport": flight.arrival_airport,
        "departureTime": flight.outbound_departure_time,
        "arrivalTime": flight.outbound_arrival_time,
        "stops": flight.outbound_stops,
        "stopsLabel": _stops_label(flight.outbound_stops),
        "route": flight.outbound_route,
        "routeDisplay": _route_display(flight.outbound_route),
    }

    return_info = None
    if flight.return_route:
        return_departure_airport = flight.return_route[0] if flight.return_route else flight.arrival_airport
        return_arrival_airport = flight.return_route[-1] if flight.return_route else flight.departure_airport
        return_info = {
            "departureAirport": return_departure_airport,
            "arrivalAirport": return_arrival_airport,
            "departureTime": flight.return_departure_time,
            "arrivalTime": flight.return_arrival_time,
            "stops": flight.return_stops,
            "stopsLabel": _stops_label(flight.return_stops),
            "route": flight.return_route,
            "routeDisplay": _route_display(flight.return_route),
        }

    return {
        "id": flight.id,
        "airline": flight.airline,
        "price": flight.price,
        "priceDisplay": f"${flight.price:,.2f}",
        "overBudget": flight.price > budget,
        "currency": flight.currency,
        "totalDuration": flight.total_duration,
        "outbound": outbound_info,
        "return": return_info,
        "bookingUrl": flight.booking_url,
    }


def _stops_label(stops: int) -> str:
    if stops <= 0:
        return "Direct"
    if stops == 1:
        return "1 stop"
    return f"{stops} stops"


def _route_display(route: List[str]) -> str:
    return " -> ".join(route) if route else ""


def _build_metadata(
    payload: Dict[str, Any],
    origin_airports: List["LLMAirport"],
    destination_airports: List["LLMAirport"],
    attempt_log: List[Dict[str, Any]],
    warnings: List[str],
    gathered: List[ScrapedFlight],
) -> Dict[str, Any]:
    metadata: Dict[str, Any] = {
        "budgetForFlightFinder": payload["budget"],
        "travellers": payload["travellers"],
        "attemptedRoutes": attempt_log,
        "collectedFlights": len(gathered),
        "originAirports": [asdict(candidate) for candidate in origin_airports],
        "destinationAirports": [asdict(candidate) for candidate in destination_airports],
        "searchDates": {
            "outbound": payload["outbound_date"],
            "return": payload.get("return_date"),
        },
    }
    if payload.get("return_date"):
        metadata["tripType"] = "round_trip"
    else:
        metadata["tripType"] = "one_way"
    if warnings:
        metadata["warnings"] = warnings
    return metadata


@dataclass(frozen=True)
class LLMAirport:
    code: str
    name: str


def _build_airport_client() -> Optional[AsyncOpenAI]:
    api_key = os.getenv("OPENAI_API_KEY")
    if not api_key:
        return None
    return AsyncOpenAI(api_key=api_key)


async def _resolve_airports_with_llm(city: str, client: Optional[AsyncOpenAI]) -> List[LLMAirport]:
    if not client:
        raise ValueError("OPENAI_API_KEY is required to resolve airport codes")

    cache_key = city.strip().lower()
    cached = _AIRPORT_CACHE.get(cache_key)
    if cached is not None:
        return list(cached)

    prompt = (
        "You know the most common passenger airports. Given a city or metro area, "
        "return JSON with key 'airports' containing up to two objects with 'code' (IATA) "
        "and 'name'. Focus on major airports that handle international routes. City: "
        f"{city!r}."
    )

    try:
        response = await client.chat.completions.create(
            model=AIRPORT_MODEL,
            temperature=0.0,
            max_tokens=120,
            messages=[
                {"role": "system", "content": "Reply using valid JSON only."},
                {"role": "user", "content": prompt},
            ],
        )
    except Exception as exc:
        raise ValueError(f"Airport lookup failed for {city}: {exc}") from exc

    content = response.choices[0].message.content if response.choices else ""
    if not content:
        raise ValueError(f"Airport lookup returned empty response for {city}")

    content = content.strip()
    if content.startswith("```"):
        content = re.sub(r"^```[a-zA-Z]*\n?", "", content)
        if content.endswith("```"):
            content = content[:-3]
        content = content.strip()

    try:
        parsed = json.loads(content)
    except json.JSONDecodeError:
        match = re.search(r"\{.*\}", content, re.DOTALL)
        if match:
            LOGGER.warning("Cleaning non-JSON LLM airport response for %s: %s", city, content)
            try:
                parsed = json.loads(match.group(0))
            except json.JSONDecodeError as exc:
                raise ValueError(f"Airport lookup returned invalid JSON for {city}") from exc
        else:
            raise ValueError(f"Airport lookup returned invalid JSON for {city}")

    airports_payload = []
    if isinstance(parsed, dict):
        airports_payload = parsed.get("airports") or []
    elif isinstance(parsed, list):
        airports_payload = parsed

    results: List[LLMAirport] = []
    for item in airports_payload[:2]:
        if not isinstance(item, dict):
            continue
        code = str(item.get("code") or "").strip().upper()
        name = str(item.get("name") or "").strip() or code
        if len(code) == 3 and code.isalpha():
            results.append(LLMAirport(code=code, name=name))

    if not results:
        raise ValueError(f"Unable to resolve airports for {city}")

    LOGGER.debug(
        "LLM resolved airports for %s -> %s",
        city,
        ", ".join(f"{airport.code} ({airport.name})" for airport in results),
    )

    _AIRPORT_CACHE[cache_key] = tuple(results)
    return list(results)
