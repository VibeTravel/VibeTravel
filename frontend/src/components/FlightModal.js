import React, { useCallback, useEffect, useMemo, useRef, useState } from "react";
import FlightDropdown from "./FlightDropdown";
import { searchFlights } from "../api/searchFlights";
import { saveFlightSelection } from "../api/saveFlightSelection";
import "./FlightModal.css";

const ISO_TODAY = new Date().toISOString().slice(0, 10);

const initialStatus = {
  loading: false,
  error: null,
  outboundFlights: [],
  outboundCandidates: [],
  outboundMessage: null,
  outboundMetadata: null,
  returnFlights: [],
  returnCandidates: [],
  returnMessage: null,
  returnMetadata: null,
};

function coerceCity(value) {
  if (!value) {
    return "";
  }
  return String(value).trim();
}

function FlightModal({ isOpen, onClose, destination, tripDetails, onFlightSaved }) {
  const travellersFromPhase1 = tripDetails?.travellers || tripDetails?.travelers || tripDetails?.numTravelers || 1;
  const totalBudgetFromPhase1 = tripDetails?.totalBudget || tripDetails?.budget || 0;

  const [formValues, setFormValues] = useState({
    currentCity: "",
    destinationCity: "",
    travellers: Number(travellersFromPhase1) > 0 ? Number(travellersFromPhase1) : 1,
    totalBudget: Number(totalBudgetFromPhase1) > 0 ? Number(totalBudgetFromPhase1) : 0,
    outboundDate: ISO_TODAY,
    returnDate: "",
  });

  const [searchState, setSearchState] = useState({ ...initialStatus });
  const [supervisorResult, setSupervisorResult] = useState(null);
  const [selectedOutbound, setSelectedOutbound] = useState(null);
  const [selectedReturn, setSelectedReturn] = useState(null);
  const [isSaving, setIsSaving] = useState(false);
  const [saveResult, setSaveResult] = useState(null);
  const hasPreloadedRef = useRef(false);

  const budgetForFlightFinder = useMemo(() => {
    const divisor = supervisorResult?.budget?.budgetDivisor || 2;
    if (!formValues.totalBudget || formValues.totalBudget <= 0) {
      return 0;
    }
    if (supervisorResult?.budget?.budgetForFlightFinder) {
      return supervisorResult.budget.budgetForFlightFinder;
    }
    return formValues.totalBudget / divisor;
  }, [formValues.totalBudget, supervisorResult]);

  const resetState = useCallback(() => {
    setSearchState({ ...initialStatus });
    setSupervisorResult(null);
    setSelectedOutbound(null);
    setSelectedReturn(null);
    setSaveResult(null);
    setIsSaving(false);
    hasPreloadedRef.current = false;
  }, []);

  const loadFlights = useCallback(
    async (values) => {
      setSearchState({ ...initialStatus, loading: true });
      setSelectedOutbound(null);
      setSelectedReturn(null);
      setSaveResult(null);

      try {
        const response = await searchFlights(values);
        const outboundResult = response?.flightFinder?.outbound || null;
        const returnResult = response?.flightFinder?.return || null;

        const outboundFlights = outboundResult?.dropdownFlights || [];
        const outboundCandidates = outboundResult?.candidateFlights || [];
        const outboundMessage = outboundResult?.status === "no_results"
          ? outboundResult?.message || "No outbound flights found for this search."
          : null;

        const returnFlights = returnResult?.dropdownFlights || [];
        const returnCandidates = returnResult?.candidateFlights || [];
        const returnMessage = returnResult?.status === "no_results"
          ? returnResult?.message || "No return flights found for this search."
          : null;

        setSearchState({
          loading: false,
          error: null,
          outboundFlights,
          outboundCandidates,
          outboundMessage,
          outboundMetadata: outboundResult?.metadata || null,
          returnFlights,
          returnCandidates,
          returnMessage,
          returnMetadata: returnResult?.metadata || null,
        });

        setSupervisorResult(response);
      } catch (error) {
        setSearchState({
          loading: false,
          error: error.message || "Flight search failed",
          outboundFlights: [],
          outboundCandidates: [],
          outboundMessage: null,
          outboundMetadata: null,
          returnFlights: [],
          returnCandidates: [],
          returnMessage: null,
          returnMetadata: null,
        });
        setSupervisorResult(null);
      }
    },
    []
  );

  useEffect(() => {
    if (!isOpen) {
      resetState();
      return;
    }

    const defaults = {
      currentCity: coerceCity(tripDetails?.currentCity || tripDetails?.location || ""),
      destinationCity: coerceCity(destination?.destination || destination?.city || tripDetails?.destinationCity || ""),
      travellers: Number(travellersFromPhase1) > 0 ? Number(travellersFromPhase1) : 1,
      totalBudget: Number(totalBudgetFromPhase1) > 0 ? Number(totalBudgetFromPhase1) : 0,
      outboundDate: (tripDetails?.outboundDate || tripDetails?.startDate || ISO_TODAY),
      returnDate: tripDetails?.returnDate || tripDetails?.endDate || "",
    };

    setFormValues(defaults);

    if (defaults.currentCity && defaults.destinationCity && defaults.totalBudget > 0) {
      if (!hasPreloadedRef.current) {
        hasPreloadedRef.current = true;
        loadFlights(defaults);
      }
    } else {
      setSearchState({
        ...initialStatus,
        error: "Please provide cities and a positive total budget.",
      });
    }
  }, [isOpen, destination, tripDetails, travellersFromPhase1, totalBudgetFromPhase1, loadFlights, resetState]);

  const handleChange = (event) => {
    const { name, value } = event.target;
    if (name !== "outboundDate" && name !== "returnDate") {
      return;
    }
    setFormValues((prev) => ({
      ...prev,
      [name]: value,
    }));
  };

  const handleSubmit = async (event) => {
    event.preventDefault();
    await loadFlights(formValues);
  };

  const handleSelectOutbound = (flight) => {
    setSelectedOutbound(flight);
  };

  const handleSelectReturn = (flight) => {
    setSelectedReturn(flight);
  };

  const handleSaveSelection = async () => {
    if (!selectedOutbound || !selectedReturn) {
      setSaveResult({
        success: false,
        message: "Select an outbound and a return flight before saving.",
      });
      return;
    }

    setIsSaving(true);
    setSaveResult(null);

    try {
      const outbound = selectedOutbound.outbound || {};
      const inbound = selectedReturn.outbound || {};

      const flightSummary = {
        airline: selectedOutbound.airline,
        departure_time: outbound.departureTime || "Unknown",
        arrival_time: outbound.arrivalTime || "Unknown",
        duration: selectedOutbound.totalDuration || "Unknown",
        price: selectedOutbound.price,
        booking_url: selectedOutbound.bookingUrl,
        stops: outbound.stops ?? 0,
        departure_airport: outbound.departureAirport || "",
        arrival_airport: outbound.arrivalAirport || "",
      };

      const returnSummary = {
        airline: selectedReturn.airline,
        departure_time: inbound.departureTime || "Unknown",
        arrival_time: inbound.arrivalTime || "Unknown",
        duration: selectedReturn.totalDuration || "Unknown",
        price: selectedReturn.price,
        booking_url: selectedReturn.bookingUrl,
        stops: inbound.stops ?? 0,
        departure_airport: inbound.departureAirport || "",
        arrival_airport: inbound.arrivalAirport || "",
      };

      const noteParts = [];
      if (searchState.outboundMetadata?.note) {
        noteParts.push(`Outbound: ${searchState.outboundMetadata.note}`);
      }
      if (searchState.returnMetadata?.note) {
        noteParts.push(`Return: ${searchState.returnMetadata.note}`);
      }

      const aggregatedNote = noteParts.length > 0 ? noteParts.join("\n\n") : null;

      const payload = {
        origin: formValues.currentCity,
        destination: formValues.destinationCity,
        outbound_date: formValues.outboundDate,
        return_date: formValues.returnDate || null,
        travelers: formValues.travellers,
        budget: budgetForFlightFinder || 0,
        total_budget: formValues.totalBudget || null,
        flight: flightSummary,
        return_flight: returnSummary,
        note: aggregatedNote,
        metadata: {
          outbound: searchState.outboundMetadata,
          return: searchState.returnMetadata,
        },
      };

      const response = await saveFlightSelection(payload);

      setSaveResult({
        success: true,
        downloadUrl: response.download_url,
        file: response.file,
      });

      if (typeof onFlightSaved === "function") {
        onFlightSaved({
          locationName: formValues.destinationCity,
          outbound: flightSummary,
          inbound: returnSummary,
          createdAt: new Date().toISOString(),
          downloadUrl: response.download_url,
          fileName: response.file,
        });
      }
    } catch (error) {
      setSaveResult({
        success: false,
        message: error.message || "Failed to save selection.",
      });
    } finally {
      setIsSaving(false);
    }
  };

  if (!isOpen) {
    return null;
  }

  const errorMessage = searchState.error;

  return (
    <div className="flight-modal-overlay" role="dialog" aria-modal="true">
      <div className="flight-modal">
        <header className="flight-modal__header">
          <div>
            <h2>Choose Your Round-Trip Flight</h2>
            <p>{formValues.currentCity || "Current city"} → {formValues.destinationCity || "Destination"}</p>
          </div>
          <button type="button" className="flight-modal__close" onClick={onClose}>
            ×
          </button>
        </header>

        <section className="flight-modal__form">
          <form onSubmit={handleSubmit} className="flight-modal__grid">
            <label>
              Current City
              <input
                name="currentCity"
                value={formValues.currentCity}
                onChange={handleChange}
                placeholder="e.g., New York"
                disabled
                required
              />
            </label>
            <label>
              Destination City
              <input
                name="destinationCity"
                value={formValues.destinationCity}
                onChange={handleChange}
                placeholder="e.g., Tokyo"
                disabled
                required
              />
            </label>
            <label>
              Travellers
              <input
                type="number"
                name="travellers"
                min={1}
                value={formValues.travellers}
                onChange={handleChange}
                disabled
                required
              />
            </label>
            <label>
              Total Budget (USD)
              <input
                type="number"
                name="totalBudget"
                min={1}
                value={formValues.totalBudget}
                onChange={handleChange}
                disabled
                required
              />
            </label>
            <label>
              Outbound Date
              <input
                type="date"
                name="outboundDate"
                value={formValues.outboundDate}
                onChange={handleChange}
                required
              />
            </label>
            <label>
              Return Date (optional)
              <input
                type="date"
                name="returnDate"
                value={formValues.returnDate}
                onChange={handleChange}
              />
            </label>
            <button type="submit" className="modal-primary-btn flight-modal__submit" disabled={searchState.loading}>
              {searchState.loading ? "Searching…" : "Search Flights"}
            </button>
          </form>
        </section>

        <section className="flight-modal__body">
          <div className="flight-modal__summary">
            <span>Travellers: {formValues.travellers}</span>
            <span>Total Budget: ${formValues.totalBudget.toFixed(2)}</span>
            <span>Budget for Flight Finder: ${budgetForFlightFinder.toFixed(2)}</span>
          </div>

          {errorMessage && (
            <div className="flight-modal__alert flight-modal__alert--error">{errorMessage}</div>
          )}

          {searchState.loading && (
            <div className="flight-modal__placeholder">Gathering flights…</div>
          )}

          {!searchState.loading && (
            <div className="flight-modal__legs">
              <div className="flight-modal__leg">
                <h3>Outbound Flight</h3>

                {searchState.outboundMetadata?.note && (
                  <div className="flight-modal__alert flight-modal__alert--note">
                    {searchState.outboundMetadata.note}
                  </div>
                )}

                {searchState.outboundMetadata?.warnings?.length ? (
                  <div className="flight-modal__alert flight-modal__alert--warning">
                    <strong>Warnings:</strong>
                    <ul>
                      {searchState.outboundMetadata.warnings.map((warning, index) => (
                        <li key={index}>{warning}</li>
                      ))}
                    </ul>
                  </div>
                ) : null}

                {searchState.outboundFlights.length > 0 ? (
                  <FlightDropdown
                    options={searchState.outboundFlights}
                    selectedId={selectedOutbound?.id || null}
                    onSelect={handleSelectOutbound}
                    disabled={searchState.loading}
                    placeholder="Select outbound flight"
                  />
                ) : (
                  <div className="flight-modal__placeholder">
                    {searchState.outboundMessage || "No outbound flights found for this search."}
                  </div>
                )}

              </div>

              <div className="flight-modal__leg">
                <h3>Return Flight</h3>

                {searchState.returnMetadata?.note && (
                  <div className="flight-modal__alert flight-modal__alert--note">
                    {searchState.returnMetadata.note}
                  </div>
                )}

                {searchState.returnMetadata?.warnings?.length ? (
                  <div className="flight-modal__alert flight-modal__alert--warning">
                    <strong>Warnings:</strong>
                    <ul>
                      {searchState.returnMetadata.warnings.map((warning, index) => (
                        <li key={index}>{warning}</li>
                      ))}
                    </ul>
                  </div>
                ) : null}

                {searchState.returnFlights.length > 0 ? (
                  <FlightDropdown
                    options={searchState.returnFlights}
                    selectedId={selectedReturn?.id || null}
                    onSelect={handleSelectReturn}
                    disabled={searchState.loading}
                    placeholder="Select return flight"
                  />
                ) : (
                  <div className="flight-modal__placeholder">
                    {searchState.returnMessage || "No return flights found for this search."}
                  </div>
                )}

              </div>
            </div>
          )}
        </section>

        <footer className="flight-modal__footer">
          <div className="flight-modal__actions">
            <button type="button" className="modal-secondary-btn" onClick={onClose}>
              Close
            </button>
            <button
              type="button"
              className="modal-primary-btn"
              onClick={handleSaveSelection}
              disabled={!selectedOutbound || !selectedReturn || isSaving}
            >
              {isSaving ? "Saving…" : "Save Selection"}
            </button>
          </div>

          {saveResult && (
            <div className={saveResult.success ? "flight-modal__alert flight-modal__alert--success" : "flight-modal__alert flight-modal__alert--error"}>
              {saveResult.success ? (
                <>
                  Selection saved. Download the PDF:
                  {saveResult.downloadUrl ? (
                    <a href={`http://127.0.0.1:8000${saveResult.downloadUrl}`} target="_blank" rel="noreferrer">
                      {saveResult.file}
                    </a>
                  ) : null}
                </>
              ) : (
                saveResult.message
              )}
            </div>
          )}
        </footer>
      </div>
    </div>
  );
}

export default FlightModal;
