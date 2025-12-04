import React, { useEffect, useMemo, useState } from "react";
import "./FlightModal.css";

function formatStopsLabel(flight) {
  if (!flight?.outbound) {
    return "Unknown";
  }

  const outboundLabel = flight.outbound.stopsLabel;
  const returnLabel = flight.return?.stopsLabel;

  if (!returnLabel) {
    return outboundLabel;
  }

  if (outboundLabel === returnLabel) {
    return outboundLabel;
  }

  return `${outboundLabel} · Return: ${returnLabel}`;
}

function formatRouteDisplay(routeDisplay, fallbackStart, fallbackEnd) {
  if (routeDisplay && routeDisplay.length > 0) {
    return routeDisplay;
  }
  if (fallbackStart && fallbackEnd) {
    return `${fallbackStart} -> ${fallbackEnd}`;
  }
  return null;
}

function FlightDropdown({ options, selectedId, onSelect, disabled, placeholder = "Select a flight" }) {
  const [isOpen, setIsOpen] = useState(false);

  useEffect(() => {
    if (!selectedId && options.length > 0) {
      setIsOpen(true);
    }
  }, [selectedId, options]);

  const selectedOption = useMemo(
    () => options.find((option) => option.id === selectedId) || null,
    [options, selectedId]
  );

  const handleSelect = (option) => {
    onSelect(option);
    setIsOpen(false);
  };

  const toggle = () => {
    if (disabled || options.length === 0) {
      return;
    }
    setIsOpen((prev) => !prev);
  };

  return (
    <div className="flight-dropdown">
      <button
        type="button"
        className="flight-dropdown__toggle"
        onClick={toggle}
        disabled={disabled || options.length === 0}
      >
        {selectedOption ? (
          <span>
            <strong>{selectedOption.airline}</strong> · {formatRouteDisplay(
              selectedOption.outbound?.routeDisplay,
              selectedOption.outbound?.departureAirport,
              selectedOption.outbound?.arrivalAirport
            )} · {selectedOption.priceDisplay}
          </span>
        ) : (
          <span>{placeholder}</span>
        )}
        <span className="flight-dropdown__caret">▾</span>
      </button>

      {isOpen && options.length > 0 && (
        <ul className="flight-dropdown__menu">
          {options.map((option) => {
            const outboundRoute = formatRouteDisplay(
              option.outbound?.routeDisplay,
              option.outbound?.departureAirport,
              option.outbound?.arrivalAirport
            );
            const returnRoute = option.return
              ? formatRouteDisplay(
                  option.return.routeDisplay,
                  option.return.departureAirport,
                  option.return.arrivalAirport
                )
              : null;

            return (
              <li key={option.id}>
                <button
                  type="button"
                  className="flight-dropdown__option"
                  onClick={() => handleSelect(option)}
                >
                  <div className="flight-dropdown__option-main">
                    <span className="flight-dropdown__airline">{option.airline}</span>
                    <span className={option.overBudget ? "flight-dropdown__price flight-dropdown__price--over" : "flight-dropdown__price"}>
                      {option.priceDisplay}
                    </span>
                  </div>
                  <div className="flight-dropdown__option-meta">
                    {outboundRoute ? <span>{outboundRoute}</span> : null}
                    <span>{option.outbound?.departureTime} → {option.outbound?.arrivalTime}</span>
                    {option.return ? (
                      <>
                        {returnRoute ? <span>Return Route: {returnRoute}</span> : null}
                        <span>Return Times: {option.return.departureTime} → {option.return.arrivalTime}</span>
                      </>
                    ) : null}
                    <span>{option.totalDuration}</span>
                    <span>{formatStopsLabel(option)}</span>
                  </div>
                </button>
              </li>
            );
          })}
        </ul>
      )}

      {selectedOption && (
        <button
          type="button"
          className="flight-dropdown__change"
          onClick={() => setIsOpen(true)}
        >
          Change selection
        </button>
      )}
    </div>
  );
}

export default FlightDropdown;
