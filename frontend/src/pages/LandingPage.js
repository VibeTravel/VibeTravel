import React, { useState } from "react";
import { searchLocations } from "../api/searchLocations";
import Dashboard from "./Dashboard";

function LandingPage() {
  const [showDashboard, setShowDashboard] = useState(false);
  const [destinations, setDestinations] = useState([]);
  const [isLoading, setIsLoading] = useState(false);
  const [tripDetails, setTripDetails] = useState(null);

  // Form states
  const [location, setLocation] = useState("");
  const [numTravelers, setNumTravelers] = useState("");
  const [activities, setActivities] = useState("");
  const [budget, setBudget] = useState("");
  const [startDate, setStartDate] = useState("");
  const [endDate, setEndDate] = useState("");
  const [additionalDetails, setAdditionalDetails] = useState("");

  const handleSubmit = async (e) => {
    e.preventDefault();

    const payload = {
      location,
      numTravelers: Number(numTravelers),
      activities: activities
        .split(",")
        .map((a) => a.trim())
        .filter((a) => a),
      budget: Number(budget),
      dateMode: "date_range",
      numDays: null,
      startDate,
      endDate,
      additionalDetails: additionalDetails
        .split(",")
        .map((d) => d.trim())
        .filter((d) => d),
    };

    console.log("Sending to backend:", payload);
    setIsLoading(true);

    try {
      const result = await searchLocations(payload);
      console.log("Response from backend:", result);

      setDestinations(result.destinations);

      setTripDetails({
        location,
        activities,
        budget: Number(budget),
        travelers: Number(numTravelers),
        startDate,
        endDate,
        additionalDetails,
      });

      setIsLoading(false);
      setShowDashboard(true);
    } catch (err) {
      console.error("Error sending to backend:", err);
      setIsLoading(false);
      alert("Failed to get destinations. Please try again.");
    }
  };

  const handleBackToSearch = () => {
    setShowDashboard(false);
  };

  if (isLoading) {
    return (
      <div className="App">
        <div className="loading-container">
          <div className="spinner"></div>
          <h2>Customizing your perfect destinations...</h2>
          <p>Finding the best places just for you ✨</p>
        </div>
      </div>
    );
  }

  if (showDashboard) {
    return (
      <Dashboard
        destinations={destinations}
        onBack={handleBackToSearch}
        tripDetails={tripDetails}
      />
    );
  }

  return (
    <div className="App">
      <div className="form-container">
        <h2>Plan Your Trip</h2>

        <form onSubmit={handleSubmit}>
          <label>Current Location:</label>
          <input
            type="text"
            value={location}
            onChange={(e) => setLocation(e.target.value)}
            required
          />

          <label>Number of Travelers:</label>
          <input
            type="number"
            min="1"
            value={numTravelers}
            onChange={(e) => setNumTravelers(e.target.value)}
            required
          />

          <label>Total Budget (USD):</label>
          <input
            type="number"
            min="0"
            value={budget}
            onChange={(e) => setBudget(e.target.value)}
            required
          />

          <label>Start Date:</label>
          <input
            type="date"
            value={startDate}
            onChange={(e) => setStartDate(e.target.value)}
            min={new Date().toISOString().split("T")[0]}
            required
          />

          <label>End Date:</label>
          <input
            type="date"
            value={endDate}
            onChange={(e) => setEndDate(e.target.value)}
            min={startDate || new Date().toISOString().split("T")[0]}
            required
          />

          <label>Preferred Activities (comma separated):</label>
          <input
            type="text"
            value={activities}
            onChange={(e) => setActivities(e.target.value)}
            placeholder="e.g., hiking, museums, beaches"
            required
          />

          <label>Additional Details or Restrictions (comma separated, optional):</label>
          <textarea
            value={additionalDetails}
            onChange={(e) => setAdditionalDetails(e.target.value)}
            placeholder="e.g., vegetarian food, pet-friendly hotels"
            rows="3"
          />

          <button type="submit" className="submit-btn">
            Search Destinations
          </button>
        </form>
      </div>
    </div>
  );
}

export default LandingPage;
