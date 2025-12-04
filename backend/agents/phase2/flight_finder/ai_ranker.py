"""OpenAI-powered ranking helper for Phase 2 Flight Finder."""

from __future__ import annotations

import json
import re
from typing import Any, Dict, List, Optional

from openai import AsyncOpenAI

from .flight_scraper import ScrapedFlight


class AIRanker:
    """Rank candidate flights using an external LLM."""

    MODEL = "gpt-4o-mini"

    def __init__(self, api_key: Optional[str]) -> None:
        self._client: Optional[AsyncOpenAI] = AsyncOpenAI(api_key=api_key) if api_key else None

    async def rank(
        self,
        flights: List[ScrapedFlight],
        *,
        context: Dict[str, Any],
        budget: float,
    ) -> List[ScrapedFlight]:
        if not flights:
            return []
        if len(flights) <= 2:
            return flights[:2]
        if not self._client:
            return flights[:2]

        payload = [_to_serialisable(flight, budget) for flight in flights]
        prompt_context = json.dumps(context, indent=2)
        flights_json = json.dumps(payload, indent=2)

        prompt = (
            "You are assisting a travel concierge. Review the provided flights and return a JSON "
            "object with a key 'selectedIds' containing exactly two flight IDs in preference order. "
            "Ranking priorities, in order: (1) shortest total duration, (2) lowest price, (3) fewer "
            "connections, (4) prefer direct flights when other factors are similar, (5) overall "
            "convenience (earlier departures acceptable if ties remain)."
            "\n\nContext:\n"
            f"{prompt_context}\n\nFlights:\n{flights_json}\n"
        )

        try:
            response = await self._client.chat.completions.create(
                model=self.MODEL,
                temperature=0.1,
                max_tokens=400,
                messages=[
                    {
                        "role": "system",
                        "content": "Respond ONLY with valid JSON. Never include commentary.",
                    },
                    {"role": "user", "content": prompt},
                ],
            )
        except Exception:
            return flights[:2]

        content = response.choices[0].message.content if response.choices else ""
        if not content:
            return flights[:2]

        cleaned = re.sub(r"```json\s*", "", content)
        cleaned = re.sub(r"```\s*", "", cleaned)

        try:
            parsed = json.loads(cleaned)
        except json.JSONDecodeError:
            return flights[:2]

        ids = parsed.get("selectedIds") if isinstance(parsed, dict) else None
        if not isinstance(ids, list):
            return flights[:2]

        lookup = {flight.id: flight for flight in flights}
        ordered: List[ScrapedFlight] = []
        for flight_id in ids:
            flight = lookup.get(str(flight_id))
            if flight and flight not in ordered:
                ordered.append(flight)
                if len(ordered) == 2:
                    break

        if len(ordered) < 2:
            fallback = [flight for flight in flights if flight not in ordered]
            ordered.extend(fallback[: 2 - len(ordered)])

        return ordered[:2]


def _to_serialisable(flight: ScrapedFlight, budget: float) -> Dict[str, Any]:
    return {
        "id": flight.id,
        "airline": flight.airline,
        "price": flight.price,
        "overBudget": flight.price > budget,
        "totalDuration": flight.total_duration,
        "outboundStops": flight.outbound_stops,
        "returnStops": flight.return_stops,
        "outboundDepartureTime": flight.outbound_departure_time,
        "outboundArrivalTime": flight.outbound_arrival_time,
        "returnDepartureTime": flight.return_departure_time,
        "returnArrivalTime": flight.return_arrival_time,
    }
