from pathlib import Path
from typing import Dict, Any, Optional
from datetime import datetime

from fastapi import APIRouter, HTTPException
from fastapi.responses import FileResponse
from pydantic import BaseModel, Field
from fpdf import FPDF


router = APIRouter(prefix="/itineraries", tags=["itineraries"])

SAVE_DIR = Path(__file__).resolve().parent.parent / "saved_itineraries"
SAVE_DIR.mkdir(parents=True, exist_ok=True)


class FlightSummary(BaseModel):
	airline: str
	departure_time: str
	arrival_time: str
	duration: str
	price: float
	booking_url: str
	stops: int
	departure_airport: str
	arrival_airport: str


class FlightSelection(BaseModel):
	origin: str
	destination: str
	outbound_date: str
	return_date: Optional[str] = None
	travelers: int = Field(1, gt=0)
	budget: float = Field(..., gt=0)
	total_budget: Optional[float] = None
	flight: FlightSummary
	return_flight: Optional[FlightSummary] = None
	note: Optional[str] = None
	metadata: Optional[Dict[str, Any]] = None


def _sanitize_slug(value: str, fallback: str) -> str:
	slug = "".join(ch for ch in value.upper() if ch.isalnum())
	return slug or fallback


@router.post("/save-flight")
async def save_flight(selection: FlightSelection):
	try:
		timestamp = datetime.utcnow().strftime("%Y%m%d_%H%M%S")
		origin_slug = _sanitize_slug(selection.origin, "ORIGIN")
		destination_slug = _sanitize_slug(selection.destination, "DEST")
		filename = f"flight_{origin_slug}_{destination_slug}_{timestamp}.pdf"
		file_path = SAVE_DIR / filename

		pdf = FPDF()
		pdf.set_auto_page_break(auto=True, margin=15)
		pdf.add_page()

		pdf.set_font("Helvetica", "B", 18)
		pdf.cell(0, 12, "Flight Selection Summary", ln=True)

		pdf.set_font("Helvetica", size=12)
		pdf.ln(4)
		pdf.cell(0, 8, f"Generated: {datetime.utcnow().strftime('%Y-%m-%d %H:%M UTC')}", ln=True)

		pdf.ln(6)
		pdf.set_font("Helvetica", "B", 14)
		pdf.cell(0, 10, "Trip Overview", ln=True)

		pdf.set_font("Helvetica", size=12)
		pdf.cell(0, 8, f"Origin: {selection.origin}", ln=True)
		pdf.cell(0, 8, f"Destination: {selection.destination}", ln=True)
		pdf.cell(0, 8, f"Outbound Date: {selection.outbound_date}", ln=True)
		pdf.cell(0, 8, f"Return Date: {selection.return_date or 'One-way'}", ln=True)
		pdf.cell(0, 8, f"Travelers: {selection.travelers}", ln=True)
		pdf.cell(0, 8, f"Budget (per traveler): ${selection.budget:,.2f}", ln=True)
		if selection.total_budget:
			pdf.cell(0, 8, f"Total Trip Budget: ${selection.total_budget:,.2f}", ln=True)

		if selection.note:
			pdf.ln(4)
			pdf.set_font("Helvetica", "B", 12)
			pdf.cell(0, 8, "Notes", ln=True)
			pdf.set_font("Helvetica", size=12)
			pdf.multi_cell(0, 7, selection.note)

		if selection.metadata and selection.metadata.get("warnings"):
			pdf.ln(4)
			pdf.set_font("Helvetica", "B", 12)
			pdf.cell(0, 8, "Warnings", ln=True)
			pdf.set_font("Helvetica", size=12)
			for warning in selection.metadata.get("warnings", []):
				pdf.multi_cell(0, 7, f"- {warning}")

		flight = selection.flight
		pdf.ln(6)
		pdf.set_font("Helvetica", "B", 14)
		pdf.cell(0, 10, "Selected Flights", ln=True)

		pdf.set_font("Helvetica", size=12)
		pdf.cell(0, 8, "Outbound:", ln=True)
		pdf.cell(0, 8, f"  Airline(s): {flight.airline}", ln=True)
		pdf.cell(0, 8, f"  Departure: {flight.departure_airport} at {flight.departure_time}", ln=True)
		pdf.cell(0, 8, f"  Arrival: {flight.arrival_airport} at {flight.arrival_time}", ln=True)
		pdf.cell(0, 8, f"  Duration: {flight.duration}", ln=True)
		pdf.cell(0, 8, f"  Stops: {flight.stops}", ln=True)
		pdf.cell(0, 8, f"  Price: ${flight.price:,.2f}", ln=True)
		pdf.ln(4)
		pdf.multi_cell(0, 7, f"  Google Flights Link: {flight.booking_url}")

		if selection.return_flight:
			ret = selection.return_flight
			pdf.ln(6)
			pdf.cell(0, 8, "Return:", ln=True)
			pdf.cell(0, 8, f"  Airline(s): {ret.airline}", ln=True)
			pdf.cell(0, 8, f"  Departure: {ret.departure_airport} at {ret.departure_time}", ln=True)
			pdf.cell(0, 8, f"  Arrival: {ret.arrival_airport} at {ret.arrival_time}", ln=True)
			pdf.cell(0, 8, f"  Duration: {ret.duration}", ln=True)
			pdf.cell(0, 8, f"  Stops: {ret.stops}", ln=True)
			pdf.cell(0, 8, f"  Price: ${ret.price:,.2f}", ln=True)
			pdf.ln(4)
			pdf.multi_cell(0, 7, f"  Google Flights Link: {ret.booking_url}")

		pdf.output(str(file_path))

		download_url = f"/itineraries/files/{filename}"
		return {
			"status": "success",
			"file": filename,
			"download_url": download_url,
		}

	except Exception as exc:
		raise HTTPException(status_code=500, detail=f"Failed to create PDF: {exc}")


	@router.get("/save-flight")
	async def save_flight_get():
		raise HTTPException(
			status_code=405,
			detail="Use POST /itineraries/save-flight with the flight selection JSON payload.",
		)


@router.get("/files/{filename}")
async def get_saved_itinerary(filename: str):
	safe_name = Path(filename).name
	if safe_name != filename:
		raise HTTPException(status_code=400, detail="Invalid filename")

	file_path = SAVE_DIR / safe_name
	if not file_path.exists():
		raise HTTPException(status_code=404, detail="File not found")

	return FileResponse(file_path, media_type="application/pdf", filename=safe_name)
