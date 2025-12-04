import React from "react";
import "./Dashboard.css";

function formatPrice(value) {
  if (typeof value !== "number" || Number.isNaN(value)) {
    return "--";
  }
  return `$${value.toFixed(2)}`;
}

function FlightRow({ label, flight }) {
  if (!flight) {
    return null;
  }

  const stopsLabel = (() => {
    if (flight.stops === 0) {
      return "Direct";
    }
    if (flight.stops === 1) {
      return "1 stop";
    }
    return `${flight.stops} stops`;
  })();

  return (
    <div className="itinerary-flight">
      <div className="itinerary-flight__label">{label}</div>
      <div className="itinerary-flight__route">
        {flight.departure_airport} → {flight.arrival_airport}
      </div>
      <div className="itinerary-flight__times">
        {flight.departure_time} · {flight.arrival_time}
      </div>
      <div className="itinerary-flight__meta">
        <span>{flight.airline}</span>
        <span>{flight.duration}</span>
        <span>{stopsLabel}</span>
      </div>
      <div className="itinerary-flight__price">{formatPrice(flight.price)}</div>
      {flight.booking_url ? (
        <a
          className="itinerary-flight__link"
          href={flight.booking_url}
          target="_blank"
          rel="noreferrer"
        >
          Google Flights
        </a>
      ) : null}
    </div>
  );
}

function Itinerary({ entries }) {
  if (!entries || entries.length === 0) {
    return (
      <div className="itinerary-empty">
        <h3>No flights saved yet</h3>
        <p>Select outbound and return flights to build your itinerary.</p>
      </div>
    );
  }

  return (
    <div className="itinerary-list">
      {entries.map((entry, index) => (
        <article className="itinerary-card" key={`${entry.locationName}-${index}`}>
          <header className="itinerary-card__header">
            <div>
              <h3>{entry.locationName}</h3>
              <span className="itinerary-card__timestamp">
                Saved {new Date(entry.createdAt).toLocaleString()}
              </span>
            </div>
            {entry.downloadUrl ? (
              <a
                className="itinerary-card__download"
                href={`http://127.0.0.1:8000${entry.downloadUrl}`}
                target="_blank"
                rel="noreferrer"
              >
                Download PDF
              </a>
            ) : null}
          </header>

          <div className="itinerary-card__body">
            <FlightRow label="Outbound" flight={entry.outbound} />
            <FlightRow label="Return" flight={entry.inbound} />
          </div>
        </article>
      ))}
    </div>
  );
}

export default Itinerary;
