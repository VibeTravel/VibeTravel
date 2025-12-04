"""Phase 2 Supervisor (temporary implementation)."""

from __future__ import annotations

import json
import os
import difflib
from datetime import datetime
from functools import lru_cache
from typing import Any, Dict, Optional

from airportsdata import load as load_airports
import logging
from dotenv import load_dotenv
from openai import AsyncOpenAI

from agents.phase2.flight_finder.agent import flight_finder


@lru_cache(maxsize=1)
def _known_cities() -> dict[str, str]:
    data = load_airports("IATA")
    mapping: dict[str, str] = {}
    for payload in data.values():
        city = (payload.get("city") or "").strip()
        country = (payload.get("country") or "").strip()
        if not city:
            continue
        canonical = f"{city}, {country}" if country else city
        mapping.setdefault(city.lower(), canonical)
        mapping.setdefault(canonical.lower(), canonical)
    return mapping


load_dotenv()

BUDGET_DIVISOR = 2  # Configurable so future changes only require editing the constant
CITY_MODEL = "gpt-4o-mini"


LOGGER = logging.getLogger("phase2.supervisor")
LOGGER.setLevel(logging.INFO)

class Phase2Supervisor:
    """Validate Phase 1 output and orchestrate the flight finder call."""

    def __init__(self) -> None:
        api_key = os.getenv("OPENAI_API_KEY")
        self._client: Optional[AsyncOpenAI] = AsyncOpenAI(api_key=api_key) if api_key else None
        self._city_lookup = _known_cities()
        self._city_keys = list(self._city_lookup.keys())

    async def run(self, req) -> Dict[str, Any]:
        try:
            payload = self._coerce_request(req)
            validated = self._validate_numbers(payload)

            raw_current = payload["currentCity"]
            raw_destination = payload["destinationCity"]

            normalised_current = await self._resolve_city_name(raw_current)
            normalised_destination = await self._resolve_city_name(raw_destination)

            LOGGER.info(
                "City resolution: '%s' -> '%s', '%s' -> '%s'",
                raw_current,
                normalised_current or "<unresolved>",
                raw_destination,
                normalised_destination or "<unresolved>",
            )

            if not normalised_current or not normalised_destination:
                return {
                    "status": "error",
                    "source": "phase2_supervisor",
                    "error": "Unable to resolve one or both cities. Please adjust the locations and try again.",
                }

            budget_for_flight_finder = validated["totalBudget"] / BUDGET_DIVISOR

            outbound_request = {
                "fromCity": normalised_current,
                "toCity": normalised_destination,
                "budgetForFlightFinder": budget_for_flight_finder,
                "travellers": validated["travellers"],
                "outboundDate": validated["outboundDate"],
                "returnDate": None,
            }

            return_request = {
                "fromCity": normalised_destination,
                "toCity": normalised_current,
                "budgetForFlightFinder": budget_for_flight_finder,
                "travellers": validated["travellers"],
                "outboundDate": validated["returnDate"],
                "returnDate": None,
            }

            outbound_result = await flight_finder(outbound_request)
            return_result = await flight_finder(return_request)

            return {
                "status": "success",
                "source": "phase2_supervisor",
                "normalizedCities": {
                    "current": normalised_current,
                    "destination": normalised_destination,
                },
                "budget": {
                    "totalBudget": validated["totalBudget"],
                    "budgetDivisor": BUDGET_DIVISOR,
                    "budgetForFlightFinder": budget_for_flight_finder,
                },
                "travellers": validated["travellers"],
                "dates": {
                    "outbound": validated["outboundDate"],
                    "return": validated.get("returnDate"),
                },
                "flightFinder": {
                    "outbound": outbound_result,
                    "return": return_result,
                },
            }

        except ValueError as exc:
            return {
                "status": "error",
                "source": "phase2_supervisor",
                "error": str(exc),
            }
        except Exception as exc:
            return {
                "status": "error",
                "source": "phase2_supervisor",
                "error": f"Unexpected supervisor error: {exc}",
            }

    async def _resolve_city_name(self, raw_city: Optional[str]) -> Optional[str]:
        """Resolve a user-supplied city name into a canonical airport city."""

        normalised = self._normalise_city(raw_city)
        if not normalised:
            return None

        match = self._match_known_city(normalised)
        if match:
            return match

        llm_suggestion = await self._llm_city_lookup(normalised)
        if llm_suggestion:
            LOGGER.info("LLM suggested city '%s' for input '%s'", llm_suggestion, raw_city)
            match = self._match_known_city(llm_suggestion)
            if match:
                return match
            return llm_suggestion

        return None

    def _match_known_city(self, candidate: str) -> Optional[str]:
        lower = candidate.lower()
        if lower in self._city_lookup:
            return self._city_lookup[lower]

        matches = difflib.get_close_matches(lower, self._city_keys, n=1, cutoff=0.82)
        if matches:
            return self._city_lookup[matches[0]]
        return None

    async def _llm_city_lookup(self, query: str) -> Optional[str]:
        if not self._client:
            return None

        prompt = (
            "You normalise noisy travel city inputs. Given an input city name, "
            "respond with strictly valid JSON containing keys 'city' and 'country'. "
            "Example output: {\"city\": \"Kathmandu\", \"country\": \"Nepal\"}. "
            "If unsure, return the best guess. Input: "
            f"{query!r}"
        )

        try:
            response = await self._client.chat.completions.create(
                model=CITY_MODEL,
                temperature=0.1,
                max_tokens=40,
                messages=[
                    {"role": "system", "content": "Return only JSON objects."},
                    {"role": "user", "content": prompt},
                ],
            )
        except Exception:
            LOGGER.exception("City normalisation LLM call failed for '%s'", query)
            return None

        content = response.choices[0].message.content if response.choices else None
        if not content:
            return None

        try:
            parsed = json.loads(content)
        except json.JSONDecodeError:
            return None

        city_value = parsed.get("city") if isinstance(parsed, dict) else None
        if not city_value:
            return None

        country = parsed.get("country") if isinstance(parsed, dict) else None
        if country:
            return f"{city_value}, {country}"
        return str(city_value)

    @staticmethod
    def _normalise_city(value: Optional[str]) -> Optional[str]:
        if value is None:
            return None
        text = " ".join(str(value).split())
        return text if text else None

    def _coerce_request(self, req) -> Dict[str, Any]:
        if isinstance(req, dict):
            return dict(req)
        if hasattr(req, "model_dump"):
            return req.model_dump()
        return {
            "currentCity": getattr(req, "currentCity", None),
            "destinationCity": getattr(req, "destinationCity", None),
            "totalBudget": getattr(req, "totalBudget", None),
            "travellers": getattr(req, "travellers", getattr(req, "numTravelers", None)),
            "outboundDate": getattr(req, "outboundDate", getattr(req, "startDate", None)),
            "returnDate": getattr(req, "returnDate", getattr(req, "endDate", None)),
        }

    def _validate_numbers(self, payload: Dict[str, Any]) -> Dict[str, Any]:
        required_fields = ["currentCity", "destinationCity", "totalBudget", "travellers", "outboundDate"]
        missing = [field for field in required_fields if not payload.get(field)]
        if missing:
            raise ValueError(f"Missing required fields: {', '.join(missing)}")

        try:
            total_budget = float(payload["totalBudget"])
        except (TypeError, ValueError) as exc:
            raise ValueError("totalBudget must be a positive number") from exc
        if total_budget <= 0:
            raise ValueError("totalBudget must be greater than zero")

        try:
            travellers = int(payload["travellers"])
        except (TypeError, ValueError) as exc:
            raise ValueError("travellers must be a positive integer") from exc
        if travellers <= 0:
            raise ValueError("travellers must be at least 1")

        outbound = str(payload["outboundDate"]).strip()
        if not _is_iso_date(outbound):
            raise ValueError("outboundDate must be in YYYY-MM-DD format")

        return_date = payload.get("returnDate")
        if not return_date:
            raise ValueError("returnDate is required for round-trip planning")

        return_date = str(return_date).strip()
        if not _is_iso_date(return_date):
            raise ValueError("returnDate must be in YYYY-MM-DD format")

        return {
            "currentCity": str(payload["currentCity"]).strip(),
            "destinationCity": str(payload["destinationCity"]).strip(),
            "totalBudget": total_budget,
            "travellers": travellers,
            "outboundDate": outbound,
            "returnDate": return_date,
        }


def _is_iso_date(value: str) -> bool:
    try:
        datetime.strptime(value, "%Y-%m-%d")
        return True
    except ValueError:
        return False


phase2_supervisor = Phase2Supervisor()
