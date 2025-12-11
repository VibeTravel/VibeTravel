# backend/routes/phase3.py

from typing import Dict, Any
from fastapi import APIRouter, HTTPException, Query
from fastapi.responses import FileResponse, StreamingResponse
from pydantic import BaseModel
from io import BytesIO
import os
import re

from agents.utils.data_models import (
    Phase3Input,
    Phase3Response,
)
from agents.phase3.supervisor import phase3_supervisor, ITINERARY_STORAGE

router = APIRouter(prefix="/phase3", tags=["phase3"])

try:
    from reportlab.lib.pagesizes import letter, A4
    from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
    from reportlab.lib.units import inch
    from reportlab.platypus import SimpleDocTemplate, Paragraph, Spacer, Table, TableStyle, PageBreak
    from reportlab.lib import colors
    from reportlab.lib.enums import TA_LEFT, TA_CENTER, TA_RIGHT
    REPORTLAB_AVAILABLE = True
except ImportError:
    REPORTLAB_AVAILABLE = False
    print("[Phase3] Warning: reportlab not installed. PDF generation will not work.")


@router.post("/create-itinerary")
async def create_itinerary(request: Phase3Input) -> Phase3Response:
    """
    Phase 3: Create final day-by-day itinerary.
    
    Receives:
    - User selections from Phase 2 (flights, hotel, activities)
    - Complete trip context (dates, budget, travelers, etc.)
    
    Process:
    1. Itinerary Planner Agent analyzes selections
    2. Creates optimized day-by-day plan
    3. Respects budget and time constraints
    4. Returns structured itinerary
    
    Returns:
    - Daily plans with activities, times, and notes
    - Cost breakdown
    - Selected flights, hotel, activities
    """
    
    print(f"[Phase3] ===== Starting Itinerary Creation =====")
    print(f"[Phase3] Destination: {request.destination}")
    print(f"[Phase3] Dates: {request.trip_start_date} to {request.trip_end_date}")
    print(f"[Phase3] Travelers: {request.num_travelers}")
    print(f"[Phase3] Selected Activities: {len(request.selected_activities)}")
    
    try:
        # Call Phase 3 Supervisor
        result = await phase3_supervisor.run(request)
        return result
        
    except Exception as e:
        print(f"[Phase3] Error: {str(e)}")
        import traceback
        traceback.print_exc()
        
        raise HTTPException(status_code=500, detail=str(e))


def generate_itinerary_pdf(itinerary: Phase3Response) -> BytesIO:
    """
    Generate a beautifully formatted PDF from itinerary data.
    """
    if not REPORTLAB_AVAILABLE:
        raise HTTPException(status_code=500, detail="PDF generation not available (reportlab not installed)")
    
    buffer = BytesIO()
    doc = SimpleDocTemplate(buffer, pagesize=letter, topMargin=0.5*inch, bottomMargin=0.5*inch)
    
    # Container for PDF elements
    elements = []
    
    # Styles
    styles = getSampleStyleSheet()
    title_style = ParagraphStyle(
        'CustomTitle',
        parent=styles['Heading1'],
        fontSize=24,
        textColor=colors.HexColor('#1e293b'),
        spaceAfter=12,
        alignment=TA_CENTER
    )
    heading_style = ParagraphStyle(
        'CustomHeading',
        parent=styles['Heading2'],
        fontSize=16,
        textColor=colors.HexColor('#3b82f6'),
        spaceAfter=10,
        spaceBefore=15
    )
    subheading_style = ParagraphStyle(
        'CustomSubheading',
        parent=styles['Heading3'],
        fontSize=13,
        textColor=colors.HexColor('#475569'),
        spaceAfter=8
    )
    normal_style = ParagraphStyle(
        'CustomNormal',
        parent=styles['Normal'],
        fontSize=11,
        textColor=colors.HexColor('#1e293b'),
        spaceAfter=6
    )
    
    # Title
    elements.append(Paragraph(f"<b>{itinerary.destination}</b>", title_style))
    elements.append(Paragraph(f"<i>{itinerary.dates}</i>", normal_style))
    elements.append(Spacer(1, 0.3*inch))
    
    # Trip Summary
    summary_data = [
        ['Travelers', 'Duration', 'Total Cost'],
        [str(itinerary.num_travelers), f"{len(itinerary.daily_plans)} days", f"${itinerary.total_cost:,.2f}"]
    ]
    summary_table = Table(summary_data, colWidths=[2*inch, 2*inch, 2*inch])
    summary_table.setStyle(TableStyle([
        ('BACKGROUND', (0, 0), (-1, 0), colors.HexColor('#eff6ff')),
        ('TEXTCOLOR', (0, 0), (-1, 0), colors.HexColor('#1e293b')),
        ('ALIGN', (0, 0), (-1, -1), 'CENTER'),
        ('FONTNAME', (0, 0), (-1, 0), 'Helvetica-Bold'),
        ('FONTSIZE', (0, 0), (-1, 0), 12),
        ('BOTTOMPADDING', (0, 0), (-1, 0), 12),
        ('BACKGROUND', (0, 1), (-1, -1), colors.white),
        ('FONTNAME', (0, 1), (-1, -1), 'Helvetica'),
        ('FONTSIZE', (0, 1), (-1, -1), 11),
        ('GRID', (0, 0), (-1, -1), 1, colors.HexColor('#e2e8f0'))
    ]))
    elements.append(summary_table)
    elements.append(Spacer(1, 0.3*inch))
    
    # Flights
    elements.append(Paragraph("<b>✈️ Flights</b>", heading_style))
    flight_data = [
        ['Direction', 'Route', 'Departure', 'Arrival', 'Price'],
        [
            'Outbound',
            f"{itinerary.outbound_flight.departure_airport_code} → {itinerary.outbound_flight.arrival_airport_code}",
            itinerary.outbound_flight.departure_time,
            itinerary.outbound_flight.arrival_time,
            f"${itinerary.outbound_flight.price_usd:,.2f}"
        ],
        [
            'Return',
            f"{itinerary.return_flight.departure_airport_code} → {itinerary.return_flight.arrival_airport_code}",
            itinerary.return_flight.departure_time,
            itinerary.return_flight.arrival_time,
            f"${itinerary.return_flight.price_usd:,.2f}"
        ]
    ]
    flight_table = Table(flight_data, colWidths=[1*inch, 1.5*inch, 1.5*inch, 1.5*inch, 1*inch])
    flight_table.setStyle(TableStyle([
        ('BACKGROUND', (0, 0), (-1, 0), colors.HexColor('#eff6ff')),
        ('TEXTCOLOR', (0, 0), (-1, 0), colors.HexColor('#1e293b')),
        ('ALIGN', (0, 0), (-1, -1), 'CENTER'),
        ('FONTNAME', (0, 0), (-1, 0), 'Helvetica-Bold'),
        ('FONTSIZE', (0, 0), (-1, 0), 10),
        ('FONTNAME', (0, 1), (-1, -1), 'Helvetica'),
        ('FONTSIZE', (0, 1), (-1, -1), 9),
        ('GRID', (0, 0), (-1, -1), 1, colors.HexColor('#e2e8f0'))
    ]))
    elements.append(flight_table)
    elements.append(Spacer(1, 0.2*inch))
    
    # Hotel
    elements.append(Paragraph("<b>🏨 Accommodation</b>", heading_style))
    elements.append(Paragraph(f"<b>{itinerary.hotel.name}</b>", subheading_style))
    elements.append(Paragraph(f"⭐ {itinerary.hotel.rating}/5 ({itinerary.hotel.reviews} reviews) - ${itinerary.hotel.price:,.2f} per night", normal_style))
    elements.append(Spacer(1, 0.2*inch))
    
    # Daily Itinerary
    elements.append(Paragraph("<b>📋 Day-by-Day Itinerary</b>", heading_style))
    for day in itinerary.daily_plans:
        elements.append(Paragraph(f"<b>Day {day.day_number} - {day.date}</b>", subheading_style))
        for activity in day.activities:
            # Try to bold times and key parts
            formatted_activity = activity
            # Bold times (e.g., "12:05 PM", "12:05 PM - 1:30 PM")
            formatted_activity = re.sub(
                r'(\d{1,2}:\d{2}\s*(?:AM|PM|am|pm)(?:\s*-\s*\d{1,2}:\d{2}\s*(?:AM|PM|am|pm))?)',
                r'<b>\1</b>',
                formatted_activity
            )
            elements.append(Paragraph(f"• {formatted_activity}", normal_style))
        elements.append(Spacer(1, 0.15*inch))
    
    # Cost Breakdown
    elements.append(Spacer(1, 0.2*inch))
    elements.append(Paragraph("<b>💰 Cost Breakdown</b>", heading_style))
    cost_data = [['Category', 'Amount']]
    for key, value in itinerary.cost_breakdown.items():
        label = key.replace('_', ' ').title()
        cost_data.append([label, f"${value:,.2f}"])
    cost_data.append(['Total', f"${itinerary.total_cost:,.2f}"])
    
    cost_table = Table(cost_data, colWidths=[4*inch, 2*inch])
    cost_table.setStyle(TableStyle([
        ('BACKGROUND', (0, 0), (-1, 0), colors.HexColor('#eff6ff')),
        ('TEXTCOLOR', (0, 0), (-1, 0), colors.HexColor('#1e293b')),
        ('ALIGN', (0, 0), (0, -1), 'LEFT'),
        ('ALIGN', (1, 0), (1, -1), 'RIGHT'),
        ('FONTNAME', (0, 0), (-1, 0), 'Helvetica-Bold'),
        ('FONTSIZE', (0, 0), (-1, 0), 11),
        ('FONTNAME', (0, 1), (-1, -2), 'Helvetica'),
        ('FONTSIZE', (0, 1), (-1, -2), 10),
        ('FONTNAME', (0, -1), (-1, -1), 'Helvetica-Bold'),  # Total row already bold via TableStyle
        ('FONTSIZE', (0, -1), (-1, -1), 12),
        ('LINEABOVE', (0, -1), (-1, -1), 2, colors.HexColor('#3b82f6')),
        ('GRID', (0, 0), (-1, -2), 1, colors.HexColor('#e2e8f0'))
    ]))
    elements.append(cost_table)
    
    # Build PDF
    doc.build(elements)
    buffer.seek(0)
    return buffer


@router.get("/download-pdf")
async def download_itinerary_pdf(created_at: str = Query(..., description="Timestamp of the itinerary")):
    """
    Download itinerary as PDF.
    
    Query parameter:
    - created_at: The timestamp (ISO format) when the itinerary was created
    """
    print(f"[Phase3] PDF download requested for itinerary: {created_at}")
    
    # Retrieve itinerary from storage
    if created_at not in ITINERARY_STORAGE:
        raise HTTPException(status_code=404, detail="Itinerary not found")
    
    itinerary = ITINERARY_STORAGE[created_at]
    
    try:
        # Generate PDF
        pdf_buffer = generate_itinerary_pdf(itinerary)
        
        # Create filename
        destination_name = itinerary.destination.replace(' ', '_').replace(',', '')
        filename = f"itinerary_{destination_name}.pdf"
        
        return StreamingResponse(
            pdf_buffer,
            media_type="application/pdf",
            headers={"Content-Disposition": f"attachment; filename={filename}"}
        )
        
    except Exception as e:
        print(f"[Phase3] PDF generation error: {str(e)}")
        import traceback
        traceback.print_exc()
        raise HTTPException(status_code=500, detail=f"PDF generation failed: {str(e)}")


@router.get("/health")
async def phase3_health():
    """Health check for Phase 3 routes"""
    return {
        "status": "Phase 3 routes active",
        "endpoints": ["/create-itinerary", "/download-pdf"],
        "agents": {
            "itinerary_planner": "ready"
        },
        "pdf_generation": "available" if REPORTLAB_AVAILABLE else "unavailable"
    }

