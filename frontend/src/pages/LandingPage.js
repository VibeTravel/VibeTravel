import React, { useState } from "react";
import { searchLocations } from "../api/searchLocations";
import Dashboard from "./Dashboard";

function LandingPage() {
  const [showDashboard, setShowDashboard] = useState(false);
  const [destinations, setDestinations] = useState([]);
  const [isLoading, setIsLoading] = useState(false);
  
  const [location, setLocation] = useState("");
  const [activities, setActivities] = useState("");
  const [budget, setBudget] = useState("");
  const [useDays, setUseDays] = useState(true);
  const [numDays, setNumDays] = useState("");
  const [startDate, setStartDate] = useState("");
  const [endDate, setEndDate] = useState("");

  const handleSubmit = async (e) => {
    e.preventDefault();

    const payload = {
      location,
      activities: activities.split(",").map((a) => a.trim()),
      budget: Number(budget),
      dateMode: useDays ? "number_of_days" : "date_range",
      numDays: useDays ? Number(numDays) : null,
      startDate: useDays ? null : startDate,
      endDate: useDays ? null : endDate,
    };

    console.log("Sending to backend:", payload);
    setIsLoading(true);

    try {
      const result = await searchLocations(payload);
      console.log("Response from backend:", result);
      
      setDestinations(result.destinations);
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
    // Optionally clear form or keep values
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

          <label>Preferred Activities (comma separated):</label>
          <input
            type="text"
            value={activities}
            onChange={(e) => setActivities(e.target.value)}
            placeholder="e.g., hiking, museums, beaches"
            required
          />

          <label>Budget (USD):</label>
          <input
            type="number"
            value={budget}
            onChange={(e) => setBudget(e.target.value)}
            required
          />

          <label>Choose date mode:</label>
          <div className="radio-group">
            <label>
              <input
                type="radio"
                checked={useDays}
                onChange={() => setUseDays(true)}
              />
              Number of Days
            </label>

            <label>
              <input
                type="radio"
                checked={!useDays}
                onChange={() => setUseDays(false)}
              />
              Start & End Date
            </label>
          </div>

          {useDays && (
            <div>
              <label>Number of Days:</label>
              <input
                type="number"
                value={numDays}
                onChange={(e) => setNumDays(e.target.value)}
                required
              />
            </div>
          )}

          {!useDays && (
            <div>
              <label>Start Date:</label>
              <input
                type="date"
                value={startDate}
                onChange={(e) => setStartDate(e.target.value)}
                required
              />

              <label>End Date:</label>
              <input
                type="date"
                value={endDate}
                onChange={(e) => setEndDate(e.target.value)}
                required
              />
            </div>
          )}

          <button type="submit" className="submit-btn">
            Search Destinations
          </button>
        </form>
      </div>
    </div>
  );
}

export default LandingPage;