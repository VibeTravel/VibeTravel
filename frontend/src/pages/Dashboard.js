import React, { useState } from 'react';
import DestinationRating from './DestinationRating';
import { planItinerary } from '../api/planItinerary';
import { createItinerary } from '../api/createItinerary';
import './Dashboard.css'; // We'll create this

function Dashboard({ destinations, onBack, tripDetails }) {
  const [activeTab, setActiveTab] = useState('suggestions');
  const [allRatings, setAllRatings] = useState([]);
  const [showModal, setShowModal] = useState(false);
  const [isGenerating, setIsGenerating] = useState(false);
  const [selectedDestination, setSelectedDestination] = useState(null);
  const [itineraryData, setItineraryData] = useState(null);
  
  // Step-by-step selection state
  const [currentStep, setCurrentStep] = useState('flights'); // 'flights', 'hotels', 'activities'
  const [selectedOutboundFlight, setSelectedOutboundFlight] = useState(null);
  const [selectedReturnFlight, setSelectedReturnFlight] = useState(null);
  const [selectedHotel, setSelectedHotel] = useState(null);
  const [selectedActivities, setSelectedActivities] = useState([]);
  
  // Saved itineraries
  const [savedItineraries, setSavedItineraries] = useState([]);
  const [selectedItinerary, setSelectedItinerary] = useState(null);
  const [showItineraryModal, setShowItineraryModal] = useState(false);

  const handleRatingStored = (rating) => {
    setAllRatings(prev => [...prev, rating]);
  };

  // Sort preferred destinations by rating (highest first)
  const preferredDestinations = allRatings
    .filter(r => r.rating >= 5)
    .sort((a, b) => b.rating - a.rating);

  const handleDestinationClick = async (destination) => {
    console.log('Clicked destination:', destination);
    setSelectedDestination(destination);
    setShowModal(true);
    setIsGenerating(true);
    setItineraryData(null);
    
    // Reset step-by-step selections
    setCurrentStep('flights');
    setSelectedOutboundFlight(null);
    setSelectedReturnFlight(null);
    setSelectedHotel(null);
    setSelectedActivities([]);

    try {
      // Prepare Phase 2 request payload
      const payload = {
        selected_destination: {
          destination: destination.destination,
          country: destination.country,
          recommended_activities: destination.recommended_activities || [],
          description: destination.description || '',
          estimated_budget: destination.estimated_budget || ''
        },
        trip_context: {
          origin_location: tripDetails.location,
          numTravelers: tripDetails.travelers,
          budget_per_person: tripDetails.budget / tripDetails.travelers,
          startDate: tripDetails.startDate,
          endDate: tripDetails.endDate,
          numDays: Math.max((new Date(tripDetails.endDate) - new Date(tripDetails.startDate)) / (1000 * 60 * 60 * 24) - 2, 0),
          additionalDetails: tripDetails.additionalDetails ? 
            tripDetails.additionalDetails.split(',').map(d => d.trim()).filter(d => d) : []
        }
      };

      console.log('Calling Phase 2 API with payload:', payload);
      const response = await planItinerary(payload);
      console.log('Phase 2 response:', response);
      console.log('Hotels data:', response.hotels);
      console.log('Scenario A hotels:', response.hotels?.scenario_A);
      console.log('Scenario B hotels:', response.hotels?.scenario_B);
      
      setItineraryData(response);
      setIsGenerating(false);
      // Keep modal open to show results
      
    } catch (error) {
      console.error('Failed to generate itinerary:', error);
      alert('Failed to generate itinerary. Please try again.');
      setIsGenerating(false);
      setShowModal(false);
    }
  };

  const handleConfirmFlights = () => {
    if (selectedOutboundFlight !== null && selectedReturnFlight !== null) {
      setCurrentStep('hotels');
    }
  };

  const handleConfirmHotel = () => {
    if (selectedHotel !== null) {
      setCurrentStep('activities');
    }
  };

  const toggleActivity = (activityIndex) => {
    if (selectedActivities.includes(activityIndex)) {
      setSelectedActivities(selectedActivities.filter(idx => idx !== activityIndex));
    } else {
      setSelectedActivities([...selectedActivities, activityIndex]);
    }
  };

  const handleSubmit = async () => {
    const selections = {
      outboundFlight: itineraryData.flights.outbound_flights[selectedOutboundFlight],
      returnFlight: itineraryData.flights.return_flights[selectedReturnFlight],
      hotel: getHotelsByScenario()[selectedHotel],
      activities: selectedActivities.map(idx => itineraryData.activities.activities[idx])
    };
    
    console.log('Final selections:', selections);
    
    // Show loading
    setIsGenerating(true);
    setCurrentStep('generating');
    
    try {
      // Prepare Phase 3 payload
      const phase3Payload = {
        destination: `${selectedDestination.destination}, ${selectedDestination.country}`,
        origin_location: tripDetails.location,
        trip_start_date: tripDetails.startDate,
        trip_end_date: tripDetails.endDate,
        num_travelers: tripDetails.travelers,
        num_days: Math.max((new Date(tripDetails.endDate) - new Date(tripDetails.startDate)) / (1000 * 60 * 60 * 24) - 2, 0),
        budget_per_person: tripDetails.budget / tripDetails.travelers,
        additional_details: tripDetails.additionalDetails ? 
          tripDetails.additionalDetails.split(',').map(d => d.trim()).filter(d => d) : [],
        outbound_flight: selections.outboundFlight,
        return_flight: selections.returnFlight,
        selected_hotel: selections.hotel,
        selected_activities: selections.activities
      };
      
      console.log('Creating itinerary with Phase 3:', phase3Payload);
      const finalItinerary = await createItinerary(phase3Payload);
      console.log('Phase 3 response:', finalItinerary);
      
      // Save to local state
      setSavedItineraries(prev => [...prev, finalItinerary]);
      
      // Close modal and switch to itineraries tab
      setIsGenerating(false);
      setShowModal(false);
      setActiveTab('itineraries');
      
    } catch (error) {
      console.error('Failed to create itinerary:', error);
      alert('Failed to create itinerary. Please try again.');
      setIsGenerating(false);
      setCurrentStep('activities'); // Go back to activities step
    }
  };

  const getHotelsByScenario = () => {
    if (!itineraryData?.hotels) return [];
    // If first outbound flight selected (index 0), use scenario_A, otherwise scenario_B
    return selectedOutboundFlight === 0 
      ? itineraryData.hotels.scenario_A?.hotels || []
      : itineraryData.hotels.scenario_B?.hotels || [];
  };

  return (
    <div style={styles.dashboardContainer}>
      <div style={styles.tabBar}>
        <button
          style={{
            ...styles.tab,
            ...(activeTab === 'profile' ? styles.tabActive : {})
          }}
          onClick={() => setActiveTab('profile')}
        >
          Profile
        </button>
        <button
          style={{
            ...styles.tab,
            ...(activeTab === 'suggestions' ? styles.tabActive : {})
          }}
          onClick={() => setActiveTab('suggestions')}
        >
          Suggestions
        </button>
        <button
          style={{
            ...styles.tab,
            ...(activeTab === 'planning' ? styles.tabActive : {})
          }}
          onClick={() => setActiveTab('planning')}
        >
          Start Planning
        </button>
        <button
          style={{
            ...styles.tab,
            ...(activeTab === 'itineraries' ? styles.tabActive : {})
          }}
          onClick={() => setActiveTab('itineraries')}
        >
          My Itineraries {savedItineraries.length > 0 && `(${savedItineraries.length})`}
        </button>
      </div>

      <div style={styles.content}>
        {activeTab === 'profile' && (
          <div style={styles.section}>
            <h2 style={styles.sectionTitle}>Your Profile</h2>
            <p style={styles.placeholder}>Profile settings coming soon...</p>
            <button style={styles.backButton} onClick={onBack}>
              ← Back to Search
            </button>
          </div>
        )}

        {activeTab === 'suggestions' && (
          <DestinationRating 
            destinations={destinations}
            onRatingStored={handleRatingStored}
          />
        )}

        {activeTab === 'itineraries' && (
          <div style={styles.section}>
            <h2 style={styles.sectionTitle}>My Itineraries</h2>
            
            {savedItineraries.length === 0 ? (
              <div style={styles.emptyState}>
                <p>No itineraries yet!</p>
                <p style={styles.hint}>Create your first itinerary by selecting a destination and planning your trip.</p>
                <button 
                  style={styles.primaryButton}
                  onClick={() => setActiveTab('planning')}
                >
                  Start Planning
                </button>
              </div>
            ) : (
              <div style={styles.itinerariesList}>
                {savedItineraries.map((itinerary, idx) => (
                  <div 
                    key={idx} 
                    style={styles.itinerarySummaryCard}
                    onClick={() => {
                      setSelectedItinerary(itinerary);
                      setShowItineraryModal(true);
                    }}
                  >
                    <div style={styles.summaryCardHeader}>
                      <div>
                        <h3 style={styles.summaryCardTitle}>{itinerary.destination}</h3>
                        <p style={styles.summaryCardDates}>{itinerary.dates}</p>
                      </div>
                      <div style={styles.summaryCardCost}>
                        <span style={styles.costLabel}>Total</span>
                        <span style={styles.costValue}>${itinerary.total_cost.toFixed(2)}</span>
                      </div>
                    </div>
                    
                    <div style={styles.summaryCardMeta}>
                      <span>👥 {itinerary.num_travelers} traveler{itinerary.num_travelers > 1 ? 's' : ''}</span>
                      <span>📅 {itinerary.daily_plans.length} days</span>
                      <span>🎯 {itinerary.activities.length} activities</span>
                    </div>
                    
                    <div style={styles.summaryCardFooter}>
                      <span style={styles.viewDetailsText}>Click to view full itinerary →</span>
                    </div>
                  </div>
                ))}
              </div>
            )}
          </div>
        )}

        {activeTab === 'planning' && (
          <div style={styles.section}>
            <h2 style={styles.sectionTitle}>Start Planning</h2>
            
            {preferredDestinations.length === 0 ? (
              <div style={styles.emptyState}>
                <p>No destinations rated yet!</p>
                <p style={styles.hint}>Go to "Suggestions" and rate some destinations (5+ rating) to start planning.</p>
                <button 
                  style={styles.primaryButton}
                  onClick={() => setActiveTab('suggestions')}
                >
                  Rate Destinations
                </button>
              </div>
            ) : (
              <div>
                <p style={styles.subtitle}>
                  You've rated {preferredDestinations.length} destination{preferredDestinations.length !== 1 ? 's' : ''} as preferred!
                  <br/>
                  <span style={styles.subtitleHint}>Sorted by rating (highest first) • Click any destination to view itinerary</span>
                </p>
                
                <div style={styles.preferredList}>
                  {preferredDestinations.map((dest, idx) => (
                    <div 
                      key={idx} 
                      className="preferred-card-hover"
                      style={styles.preferredCard}
                      onClick={() => handleDestinationClick(dest)}
                    >
                      <div style={styles.preferredHeader}>
                        <h3 style={styles.preferredTitle}>
                          {dest.destination}, {dest.country}
                        </h3>
                        <span style={styles.ratingBadge}>
                          ⭐ {dest.rating}/10
                        </span>
                      </div>
                      <p style={styles.preferredBudget}>{dest.estimated_budget}</p>
                      <p style={styles.clickHint}>Click to view itinerary →</p>
                    </div>
                  ))}
                </div>
              </div>
            )}
          </div>
        )}
      </div>
      {/* Itinerary Modal */}
      {showModal && (
        <div style={styles.modalOverlay} onClick={() => !isGenerating && setShowModal(false)}>
          <div style={styles.modalContent} onClick={(e) => e.stopPropagation()}>
            {isGenerating && currentStep === 'generating' ? (
              <>
                <div style={styles.spinner}></div>
                <h2 style={styles.modalTitle}>
                  Creating your personalized itinerary...
                </h2>
                <p style={styles.modalText}>
                  Planning your perfect trip to<br/>
                  <strong>{selectedDestination?.destination}, {selectedDestination?.country}</strong>
                </p>
                <p style={styles.modalSubtext}>Organizing activities, optimizing schedule... 📅✨</p>
              </>
            ) : isGenerating ? (
              <>
                <div style={styles.spinner}></div>
                <h2 style={styles.modalTitle}>
                  Finding flights and hotels...
                </h2>
                <p style={styles.modalText}>
                  Searching the best options for<br/>
                  <strong>{selectedDestination?.destination}, {selectedDestination?.country}</strong>
                </p>
                <p style={styles.modalSubtext}>This may take a moment ✈️🏨</p>
              </>
            ) : itineraryData ? (
              <div style={styles.resultsContainer}>
                <div style={styles.modalHeader}>
                  <h2 style={styles.modalTitle}>
                    Plan Your Trip to {selectedDestination?.destination}
                  </h2>
                  <button 
                    style={styles.closeButton}
                    onClick={() => setShowModal(false)}
                  >
                    ✕
                  </button>
                </div>
                
                {/* Progress Indicator */}
                <div style={styles.progressBar}>
                  <div style={{...styles.progressStep, ...(currentStep === 'flights' ? styles.progressStepActive : {})}}>
                    ✈️ Flights
                  </div>
                  <div style={{...styles.progressStep, ...(currentStep === 'hotels' ? styles.progressStepActive : {})}}>
                    🏨 Hotels
                  </div>
                  <div style={{...styles.progressStep, ...(currentStep === 'activities' ? styles.progressStepActive : {})}}>
                    🎯 Activities
                  </div>
                </div>
                
                <div style={styles.scrollableContent}>
                  {/* STEP 1: FLIGHTS */}
                  {currentStep === 'flights' && itineraryData.flights && (
                    <section style={styles.section}>
                      <h3 style={styles.sectionHeader}>✈️ Select Your Flights</h3>
                      <p style={styles.instruction}>Choose 1 outbound and 1 return flight</p>
                      
                      <h4 style={styles.subHeader}>Outbound Flights</h4>
                      <div style={styles.grid}>
                        {itineraryData.flights.outbound_flights?.map((flight, idx) => (
                          <div 
                            key={idx} 
                            style={{
                              ...styles.selectableCard,
                              ...(selectedOutboundFlight === idx ? styles.selectedCard : {})
                            }}
                            onClick={() => setSelectedOutboundFlight(idx)}
                          >
                            {selectedOutboundFlight === idx && (
                              <div style={styles.checkmark}>✓</div>
                            )}
                            <h4 style={styles.cardTitle}>{flight.airline}</h4>
                            <p style={styles.cardText}>
                              {flight.departure_airport_code} → {flight.arrival_airport_code}
                            </p>
                            <div style={styles.cardDetails}>
                              <div>🛫 {flight.departure_time}</div>
                              <div>🛬 {flight.arrival_time}</div>
                              <div>⏱️ {Math.floor(flight.total_duration_minutes / 60)}h {flight.total_duration_minutes % 60}m</div>
                              <div>🔄 {flight.stops} stop(s)</div>
                            </div>
                            <strong style={styles.price}>${flight.price_usd}</strong>
                          </div>
                        ))}
                      </div>

                      <h4 style={styles.subHeader}>Return Flights</h4>
                      <div style={styles.grid}>
                        {itineraryData.flights.return_flights?.map((flight, idx) => (
                          <div 
                            key={idx} 
                            style={{
                              ...styles.selectableCard,
                              ...(selectedReturnFlight === idx ? styles.selectedCard : {})
                            }}
                            onClick={() => setSelectedReturnFlight(idx)}
                          >
                            {selectedReturnFlight === idx && (
                              <div style={styles.checkmark}>✓</div>
                            )}
                            <h4 style={styles.cardTitle}>{flight.airline}</h4>
                            <p style={styles.cardText}>
                              {flight.departure_airport_code} → {flight.arrival_airport_code}
                            </p>
                            <div style={styles.cardDetails}>
                              <div>🛫 {flight.departure_time}</div>
                              <div>🛬 {flight.arrival_time}</div>
                              <div>⏱️ {Math.floor(flight.total_duration_minutes / 60)}h {flight.total_duration_minutes % 60}m</div>
                              <div>🔄 {flight.stops} stop(s)</div>
                            </div>
                            <strong style={styles.price}>${flight.price_usd}</strong>
                          </div>
                        ))}
                      </div>

                      <button 
                        style={{
                          ...styles.confirmButton,
                          ...(selectedOutboundFlight === null || selectedReturnFlight === null ? styles.confirmButtonDisabled : {})
                        }}
                        onClick={handleConfirmFlights}
                        disabled={selectedOutboundFlight === null || selectedReturnFlight === null}
                      >
                        Confirm Flights →
                      </button>
                    </section>
                  )}

                  {/* STEP 2: HOTELS */}
                  {currentStep === 'hotels' && (
                    <section style={styles.section}>
                      <h3 style={styles.sectionHeader}>🏨 Select Your Hotel</h3>
                      <p style={styles.instruction}>Choose 1 hotel for your stay</p>
                      
                      <div style={styles.grid}>
                        {getHotelsByScenario().map((hotel, idx) => (
                          <div 
                            key={idx} 
                            style={{
                              ...styles.selectableCard,
                              ...(selectedHotel === idx ? styles.selectedCard : {})
                            }}
                            onClick={() => setSelectedHotel(idx)}
                          >
                            {/* Category Badge (Cheapest, Highest Rated, Luxury) */}
                            {hotel.category && (
                              <div style={styles.categoryBadge}>{hotel.category}</div>
                            )}
                            {/* Checkmark (placed on left to avoid overlap) */}
                            {selectedHotel === idx && (
                              <div style={styles.checkmark}>✓</div>
                            )}
                            <h4 style={styles.cardTitle}>
                              <a 
                                href={hotel.link} 
                                target="_blank" 
                                rel="noopener noreferrer"
                                style={styles.hotelLink}
                                onClick={(e) => e.stopPropagation()}
                              >
                                {hotel.name}
                              </a>
                            </h4>
                            <div style={styles.cardDetails}>
                              <div>⭐ {hotel.rating} ({hotel.reviews} reviews)</div>
                            </div>
                            <strong style={styles.price}>${hotel.price}/night</strong>
                          </div>
                        ))}
                      </div>

                      <button 
                        style={{
                          ...styles.confirmButton,
                          ...(selectedHotel === null ? styles.confirmButtonDisabled : {})
                        }}
                        onClick={handleConfirmHotel}
                        disabled={selectedHotel === null}
                      >
                        Confirm Hotel →
                      </button>
                    </section>
                  )}

                  {/* STEP 3: ACTIVITIES */}
                  {currentStep === 'activities' && itineraryData.activities?.activities && (
                    <section style={styles.section}>
                      <h3 style={styles.sectionHeader}>🎯 Select Your Activities</h3>
                      <p style={styles.instruction}>Choose as many activities as you'd like (click to select/deselect)</p>
                      
                      <div style={styles.activityList}>
                        {itineraryData.activities.activities.map((activity, idx) => (
                          <div 
                            key={idx} 
                            style={{
                              ...styles.activityItem,
                              ...(selectedActivities.includes(idx) ? styles.selectedActivity : {})
                            }}
                            onClick={() => toggleActivity(idx)}
                          >
                            <div style={styles.activityCheckbox}>
                              {selectedActivities.includes(idx) && (
                                <div style={styles.checkmarkSmall}>✓</div>
                              )}
                            </div>
                            <div style={styles.activityContent}>
                              <h4 style={styles.activityTitle}>{activity.name}</h4>
                              <p style={styles.activityDescription}>{activity.description}</p>
                              <div style={styles.activityMeta}>
                                <span style={styles.badge}>{activity.category}</span>
                                <span>⏱️ {activity.estimated_duration}</span>
                                <span>💵 ${activity.estimated_cost_per_person}/person</span>
                              </div>
                            </div>
                          </div>
                        ))}
                      </div>

                      <button 
                        style={styles.confirmButton}
                        onClick={handleSubmit}
                      >
                        Submit Itinerary
                      </button>
                    </section>
                  )}

                  {/* Errors */}
                  {itineraryData.errors?.length > 0 && (
                    <div style={styles.errorBanner}>
                      <strong>Errors:</strong>
                      <ul>
                        {itineraryData.errors.map((err, idx) => (
                          <li key={idx}>{err}</li>
                        ))}
                      </ul>
                    </div>
                  )}
                </div>
              </div>
            ) : null}
          </div>
        </div>
      )}

      {/* Full Itinerary Detail Modal */}
      {showItineraryModal && selectedItinerary && (
        <div style={styles.modalOverlay} onClick={() => setShowItineraryModal(false)}>
          <div style={{...styles.modalContent, maxWidth: '1000px'}} onClick={(e) => e.stopPropagation()}>
            <div style={styles.modalHeader}>
              <div>
                <h2 style={styles.modalTitle}>{selectedItinerary.destination}</h2>
                <p style={styles.modalSubtitle}>{selectedItinerary.dates}</p>
              </div>
              <button 
                style={styles.closeButton}
                onClick={() => setShowItineraryModal(false)}
              >
                ✕
              </button>
            </div>
            
            <div style={styles.scrollableContent}>
              {/* Trip Summary */}
              <div style={styles.tripSummaryBox}>
                <div style={styles.summaryRow}>
                  <div style={styles.summaryCol}>
                    <span style={styles.summaryLabel}>Travelers</span>
                    <span style={styles.summaryValue}>👥 {selectedItinerary.num_travelers}</span>
                  </div>
                  <div style={styles.summaryCol}>
                    <span style={styles.summaryLabel}>Duration</span>
                    <span style={styles.summaryValue}>📅 {selectedItinerary.daily_plans.length} days</span>
                  </div>
                  <div style={styles.summaryCol}>
                    <span style={styles.summaryLabel}>Total Cost</span>
                    <span style={{...styles.summaryValue, color: '#3b82f6', fontWeight: '700'}}>
                      ${selectedItinerary.total_cost.toFixed(2)}
                    </span>
                  </div>
                </div>
              </div>

              {/* Flights */}
              <section style={styles.detailSection}>
                <h3 style={styles.detailSectionHeader}>✈️ Flights</h3>
                <div style={styles.flightDetailGrid}>
                  <div style={styles.flightDetailCard}>
                    <h4 style={styles.flightDetailTitle}>Outbound</h4>
                    <p style={styles.flightDetailRoute}>
                      {selectedItinerary.outbound_flight.departure_airport_code} → {selectedItinerary.outbound_flight.arrival_airport_code}
                    </p>
                    <div style={styles.flightDetailInfo}>
                      <p>🛫 Depart: {selectedItinerary.outbound_flight.departure_time}</p>
                      <p>🛬 Arrive: {selectedItinerary.outbound_flight.arrival_time}</p>
                      <p>✈️ {selectedItinerary.outbound_flight.airline}{selectedItinerary.outbound_flight.airplane && selectedItinerary.outbound_flight.airplane !== 'N/A' ? ` - ${selectedItinerary.outbound_flight.airplane}` : ''}</p>
                    </div>
                    <p style={styles.flightPrice}>${selectedItinerary.outbound_flight.price_usd}</p>
                  </div>
                  <div style={styles.flightDetailCard}>
                    <h4 style={styles.flightDetailTitle}>Return</h4>
                    <p style={styles.flightDetailRoute}>
                      {selectedItinerary.return_flight.departure_airport_code} → {selectedItinerary.return_flight.arrival_airport_code}
                    </p>
                    <div style={styles.flightDetailInfo}>
                      <p>🛫 Depart: {selectedItinerary.return_flight.departure_time}</p>
                      <p>🛬 Arrive: {selectedItinerary.return_flight.arrival_time}</p>
                      <p>✈️ {selectedItinerary.return_flight.airline}{selectedItinerary.return_flight.airplane && selectedItinerary.return_flight.airplane !== 'N/A' ? ` - ${selectedItinerary.return_flight.airplane}` : ''}</p>
                    </div>
                    <p style={styles.flightPrice}>${selectedItinerary.return_flight.price_usd}</p>
                  </div>
                </div>
              </section>

              {/* Hotel */}
              <section style={styles.detailSection}>
                <h3 style={styles.detailSectionHeader}>🏨 Accommodation</h3>
                <div style={styles.hotelDetailCard}>
                  <div style={styles.hotelDetailHeader}>
                    <h4 style={styles.hotelDetailName}>{selectedItinerary.hotel.name}</h4>
                    <div style={styles.hotelDetailRating}>
                      ⭐ {selectedItinerary.hotel.rating} ({selectedItinerary.hotel.reviews} reviews)
                    </div>
                  </div>
                  <p style={styles.hotelPrice}>${selectedItinerary.hotel.price} per night</p>
                  <a 
                    href={selectedItinerary.hotel.link} 
                    target="_blank" 
                    rel="noopener noreferrer"
                    style={styles.hotelLink}
                  >
                    View Hotel →
                  </a>
                </div>
              </section>

              {/* Daily Itinerary */}
              <section style={styles.detailSection}>
                <h3 style={styles.detailSectionHeader}>📋 Day-by-Day Itinerary</h3>
                <div style={styles.dailyItineraryList}>
                  {selectedItinerary.daily_plans.map((day, idx) => (
                    <div key={idx} style={styles.dayDetailCard}>
                      <div style={styles.dayDetailHeader}>
                        <span style={styles.dayNumber}>Day {day.day_number}</span>
                        <span style={styles.dayDate}>{day.date}</span>
                      </div>
                      <h4 style={styles.dayDetailTitle}>{day.title}</h4>
                      <div style={styles.dayActivities}>
                        {day.activities.map((activity, actIdx) => {
                          // Highlight times in the activity text
                          const timePattern = /(\d{1,2}:\d{2}\s*(?:AM|PM|am|pm)(?:\s*-\s*\d{1,2}:\d{2}\s*(?:AM|PM|am|pm))?)/g;
                          const parts = activity.split(timePattern);
                          
                          return (
                            <div key={actIdx} style={styles.activityDetailItem}>
                              <span style={styles.activityBullet}>•</span>
                              <span style={styles.activityDetailText}>
                                {parts.map((part, i) => {
                                  // If this part matches the time pattern, bold it
                                  if (part.match(/\d{1,2}:\d{2}/)) {
                                    return <strong key={i} style={{color: '#3b82f6'}}>{part}</strong>;
                                  }
                                  return part;
                                })}
                              </span>
                            </div>
                          );
                        })}
                      </div>
                    </div>
                  ))}
                </div>
              </section>

              {/* Activities Summary */}
              <section style={styles.detailSection}>
                <h3 style={styles.detailSectionHeader}>🎯 Included Activities</h3>
                <div style={styles.activitiesSummaryGrid}>
                  {selectedItinerary.activities.map((activity, idx) => (
                    <div key={idx} style={styles.activitySummaryCard}>
                      <h4 style={styles.activitySummaryName}>{activity.name}</h4>
                      <p style={styles.activitySummaryDesc}>{activity.description}</p>
                      <div style={styles.activitySummaryMeta}>
                        <span>⏱️ {activity.estimated_duration}</span>
                        <span>💵 ${activity.estimated_cost_per_person}/person</span>
                      </div>
                    </div>
                  ))}
                </div>
              </section>

              {/* Cost Breakdown */}
              <section style={styles.detailSection}>
                <h3 style={styles.detailSectionHeader}>💰 Cost Breakdown</h3>
                <div style={styles.costBreakdownDetail}>
                  {Object.entries(selectedItinerary.cost_breakdown).map(([key, value]) => (
                    <div key={key} style={styles.costBreakdownRow}>
                      <span style={styles.costBreakdownLabel}>
                        {key.replace(/_/g, ' ').replace(/\b\w/g, l => l.toUpperCase())}
                      </span>
                      <span style={styles.costBreakdownValue}>${value.toFixed(2)}</span>
                    </div>
                  ))}
                  <div style={styles.costBreakdownTotal}>
                    <span style={styles.costTotalLabel}>Total Trip Cost</span>
                    <span style={styles.costTotalValue}>${selectedItinerary.total_cost.toFixed(2)}</span>
                  </div>
                </div>
              </section>

              {/* Download Button */}
              <div style={styles.downloadButtonContainer}>
                <button 
                  style={styles.downloadButton}
                  onClick={() => window.open(`http://127.0.0.1:8000/phase3/download-pdf?created_at=${selectedItinerary.created_at}`, '_blank')}
                >
                  📥 Download as PDF
                </button>
              </div>
            </div>
          </div>
        </div>
      )}

    </div>
  );
}

const styles = {
  dashboardContainer: {
    minHeight: '100vh',
    background: 'linear-gradient(135deg, #dbeafe, #eff6ff)',
  },
  tabBar: {
    display: 'flex',
    justifyContent: 'center',
    gap: '10px',
    padding: '20px',
    background: 'rgba(255, 255, 255, 0.3)',
    backdropFilter: 'blur(10px)',
    position: 'sticky',
    top: 0,
    zIndex: 100,
  },
  tab: {
    padding: '12px 30px',
    border: 'none',
    borderRadius: '10px',
    background: 'rgba(255, 255, 255, 0.5)',
    color: '#334155',
    fontSize: '15px',
    fontWeight: '600',
    cursor: 'pointer',
    transition: 'all 0.2s ease',
  },
  tabActive: {
    background: '#3b82f6',
    color: 'white',
    boxShadow: '0 4px 12px rgba(59, 130, 246, 0.3)',
  },
  content: {
    padding: '20px',
  },
  section: {
    maxWidth: '800px',
    margin: '0 auto',
    padding: '40px',
    background: 'rgba(255, 255, 255, 0.6)',
    borderRadius: '18px',
    backdropFilter: 'blur(18px)',
    boxShadow: '0 8px 25px rgba(0, 0, 0, 0.12)',
  },
  sectionTitle: {
    fontSize: '28px',
    fontWeight: '700',
    color: '#1e293b',
    marginBottom: '20px',
    textAlign: 'center',
  },
  subtitle: {
    fontSize: '16px',
    color: '#334155',
    marginBottom: '25px',
    textAlign: 'center',
    lineHeight: '1.6',
  },
  subtitleHint: {
    fontSize: '14px',
    color: '#64748b',
    fontWeight: '500',
  },
  placeholder: {
    fontSize: '16px',
    color: '#64748b',
    textAlign: 'center',
    padding: '40px 0',
  },
  emptyState: {
    textAlign: 'center',
    padding: '60px 20px',
  },
  hint: {
    fontSize: '14px',
    color: '#64748b',
    marginTop: '10px',
    textAlign: 'center',
  },
  modalOverlay: {
  position: 'fixed',
  top: 0,
  left: 0,
  right: 0,
  bottom: 0,
  backgroundColor: 'rgba(0, 0, 0, 0.7)',
  display: 'flex',
  alignItems: 'center',
  justifyContent: 'center',
  zIndex: 1000,
  backdropFilter: 'blur(8px)',
},
modalContent: {
  background: 'white',
  padding: '30px',
  borderRadius: '20px',
  textAlign: 'center',
  maxWidth: '900px',
  maxHeight: '90vh',
  boxShadow: '0 20px 60px rgba(0, 0, 0, 0.3)',
  position: 'relative',
},
spinner: {
  width: '60px',
  height: '60px',
  margin: '0 auto 30px',
  border: '6px solid #e5e7eb',
  borderTop: '6px solid #3b82f6',
  borderRadius: '50%',
  animation: 'spin 1s linear infinite',
},
modalTitle: {
  fontSize: '24px',
  fontWeight: '700',
  color: '#1e293b',
  marginBottom: '15px',
  textAlign: 'center',
},
modalText: {
  fontSize: '16px',
  color: '#475569',
  lineHeight: '1.6',
  marginBottom: '10px',
},
modalSubtext: {
  fontSize: '14px',
  color: '#94a3b8',
  marginTop: '15px',
},
modalHeader: {
  display: 'flex',
  justifyContent: 'space-between',
  alignItems: 'center',
  marginBottom: '20px',
  borderBottom: '2px solid #e5e7eb',
  paddingBottom: '15px',
},
closeButton: {
  background: 'none',
  border: 'none',
  fontSize: '28px',
  color: '#64748b',
  cursor: 'pointer',
  padding: '0',
  width: '40px',
  height: '40px',
  display: 'flex',
  alignItems: 'center',
  justifyContent: 'center',
  borderRadius: '8px',
  transition: 'all 0.2s ease',
},
resultsContainer: {
  textAlign: 'left',
  width: '100%',
},
scrollableContent: {
  maxHeight: '70vh',
  overflowY: 'auto',
  paddingRight: '10px',
},
section: {
  marginBottom: '30px',
},
sectionHeader: {
  fontSize: '20px',
  fontWeight: '700',
  color: '#1e293b',
  marginBottom: '15px',
  borderBottom: '2px solid #3b82f6',
  paddingBottom: '8px',
},
subHeader: {
  fontSize: '16px',
  fontWeight: '600',
  color: '#334155',
  marginTop: '20px',
  marginBottom: '12px',
},
grid: {
  display: 'grid',
  gridTemplateColumns: 'repeat(auto-fill, minmax(280px, 1fr))',
  gap: '15px',
  marginBottom: '20px',
},
card: {
  background: '#f8fafc',
  padding: '15px',
  borderRadius: '10px',
  border: '1px solid #e2e8f0',
  transition: 'all 0.2s ease',
},
cardTitle: {
  fontSize: '16px',
  fontWeight: '600',
  color: '#1e293b',
  marginBottom: '8px',
  marginTop: 0,
},
cardText: {
  fontSize: '14px',
  color: '#64748b',
  marginBottom: '10px',
  lineHeight: '1.5',
},
cardDetails: {
  fontSize: '13px',
  color: '#475569',
  marginBottom: '8px',
  display: 'flex',
  flexDirection: 'column',
  gap: '4px',
},
badge: {
  display: 'inline-block',
  padding: '4px 10px',
  background: '#dbeafe',
  color: '#1e40af',
  borderRadius: '6px',
  fontSize: '12px',
  fontWeight: '600',
  marginTop: '8px',
},
priceRow: {
  display: 'flex',
  justifyContent: 'space-between',
  alignItems: 'center',
  marginTop: '12px',
  paddingTop: '12px',
  borderTop: '1px solid #e2e8f0',
},
price: {
  fontSize: '18px',
  color: '#3b82f6',
  fontWeight: '700',
},
bookButton: {
  padding: '8px 16px',
  background: '#3b82f6',
  color: 'white',
  textDecoration: 'none',
  borderRadius: '6px',
  fontSize: '14px',
  fontWeight: '600',
  transition: 'all 0.2s ease',
},
statusBanner: {
  background: '#fef3c7',
  border: '1px solid #fbbf24',
  padding: '12px',
  borderRadius: '8px',
  marginBottom: '20px',
  fontSize: '14px',
  color: '#92400e',
},
errorBanner: {
  background: '#fee2e2',
  border: '1px solid #ef4444',
  padding: '12px',
  borderRadius: '8px',
  marginBottom: '20px',
  fontSize: '14px',
  color: '#991b1b',
},
totalCost: {
  background: '#dbeafe',
  padding: '20px',
  borderRadius: '12px',
  textAlign: 'center',
  marginTop: '30px',
},
totalPrice: {
  fontSize: '32px',
  fontWeight: '700',
  color: '#1e40af',
  margin: '10px 0 0 0',
},
  primaryButton: {
    padding: '14px 30px',
    background: '#3b82f6',
    color: 'white',
    border: 'none',
    borderRadius: '12px',
    fontSize: '16px',
    fontWeight: '600',
    cursor: 'pointer',
    transition: 'all 0.25s ease',
    margin: '20px auto',
    display: 'block',
  },
  backButton: {
    padding: '12px 24px',
    background: 'rgba(255, 255, 255, 0.7)',
    color: '#334155',
    border: 'none',
    borderRadius: '10px',
    fontSize: '15px',
    fontWeight: '600',
    cursor: 'pointer',
    transition: 'all 0.2s ease',
    margin: '20px auto',
    display: 'block',
  },
  preferredList: {
    display: 'flex',
    flexDirection: 'column',
    gap: '15px',
    marginBottom: '30px',
  },
  preferredCard: {
    padding: '20px',
    background: 'rgba(255, 255, 255, 0.8)',
    borderRadius: '12px',
    boxShadow: '0 2px 8px rgba(0, 0, 0, 0.08)',
    cursor: 'pointer',
    transition: 'all 0.3s ease',
  },
  preferredHeader: {
    display: 'flex',
    justifyContent: 'space-between',
    alignItems: 'center',
    marginBottom: '8px',
  },
  preferredTitle: {
    fontSize: '18px',
    fontWeight: '700',
    color: '#1e293b',
    margin: 0,
  },
  ratingBadge: {
    padding: '6px 12px',
    background: '#3b82f6',
    color: 'white',
    borderRadius: '8px',
    fontSize: '14px',
    fontWeight: '600',
  },
  preferredBudget: {
    fontSize: '15px',
    color: '#3b82f6',
    fontWeight: '600',
    margin: 0,
  },
  clickHint: {
    fontSize: '13px',
    color: '#64748b',
    marginTop: '10px',
    marginBottom: 0,
    fontWeight: '500',
  },
  progressBar: {
    display: 'flex',
    justifyContent: 'center',
    gap: '20px',
    padding: '20px',
    background: '#f8fafc',
    borderRadius: '12px',
    marginBottom: '25px',
  },
  progressStep: {
    padding: '10px 20px',
    background: '#e2e8f0',
    color: '#64748b',
    borderRadius: '8px',
    fontSize: '14px',
    fontWeight: '600',
    transition: 'all 0.3s ease',
  },
  progressStepActive: {
    background: '#3b82f6',
    color: 'white',
    transform: 'scale(1.05)',
  },
  instruction: {
    fontSize: '15px',
    color: '#475569',
    marginBottom: '20px',
    textAlign: 'center',
    fontWeight: '500',
  },
  selectableCard: {
    background: '#f8fafc',
    padding: '20px',
    borderRadius: '12px',
    border: '2px solid #e2e8f0',
    cursor: 'pointer',
    transition: 'all 0.3s ease',
    position: 'relative',
    minHeight: '180px',
  },
  selectedCard: {
    border: '2px solid #3b82f6',
    background: '#eff6ff',
    boxShadow: '0 4px 12px rgba(59, 130, 246, 0.25)',
  },
  checkmark: {
    position: 'absolute',
    top: '10px',
    left: '10px',
    width: '30px',
    height: '30px',
    background: '#3b82f6',
    color: 'white',
    borderRadius: '50%',
    display: 'flex',
    alignItems: 'center',
    justifyContent: 'center',
    fontSize: '18px',
    fontWeight: 'bold',
    zIndex: 10,
  },
  categoryBadge: {
    position: 'absolute',
    top: '10px',
    right: '10px',
    background: 'linear-gradient(135deg, #667eea 0%, #764ba2 100%)',
    color: 'white',
    padding: '4px 12px',
    borderRadius: '20px',
    fontSize: '11px',
    fontWeight: '700',
    textTransform: 'uppercase',
    letterSpacing: '0.5px',
    boxShadow: '0 2px 8px rgba(102, 126, 234, 0.3)',
    zIndex: 10,
  },
  hotelLink: {
    color: 'inherit',
    textDecoration: 'none',
    transition: 'color 0.2s ease',
  },
  confirmButton: {
    width: '100%',
    padding: '16px',
    background: '#3b82f6',
    color: 'white',
    border: 'none',
    borderRadius: '12px',
    fontSize: '16px',
    fontWeight: '700',
    cursor: 'pointer',
    marginTop: '30px',
    transition: 'all 0.3s ease',
  },
  confirmButtonDisabled: {
    background: '#cbd5e1',
    cursor: 'not-allowed',
    opacity: 0.6,
  },
  activityList: {
    display: 'flex',
    flexDirection: 'column',
    gap: '12px',
  },
  activityItem: {
    display: 'flex',
    gap: '15px',
    padding: '16px',
    background: '#f8fafc',
    border: '2px solid #e2e8f0',
    borderRadius: '10px',
    cursor: 'pointer',
    transition: 'all 0.3s ease',
  },
  selectedActivity: {
    border: '2px solid #3b82f6',
    background: '#eff6ff',
  },
  activityCheckbox: {
    width: '28px',
    height: '28px',
    minWidth: '28px',
    border: '2px solid #cbd5e1',
    borderRadius: '6px',
    display: 'flex',
    alignItems: 'center',
    justifyContent: 'center',
    background: 'white',
    transition: 'all 0.3s ease',
  },
  checkmarkSmall: {
    color: '#3b82f6',
    fontSize: '18px',
    fontWeight: 'bold',
  },
  activityContent: {
    flex: 1,
  },
  activityTitle: {
    fontSize: '16px',
    fontWeight: '600',
    color: '#1e293b',
    margin: '0 0 8px 0',
  },
  activityDescription: {
    fontSize: '14px',
    color: '#64748b',
    margin: '0 0 10px 0',
    lineHeight: '1.5',
  },
  activityMeta: {
    display: 'flex',
    gap: '15px',
    fontSize: '13px',
    color: '#475569',
    alignItems: 'center',
    flexWrap: 'wrap',
  },
  // Itineraries List View
  itinerariesList: {
    display: 'flex',
    flexDirection: 'column',
    gap: '20px',
  },
  itinerarySummaryCard: {
    background: 'rgba(255, 255, 255, 0.9)',
    padding: '25px',
    borderRadius: '15px',
    boxShadow: '0 4px 12px rgba(0, 0, 0, 0.08)',
    cursor: 'pointer',
    transition: 'all 0.3s ease',
    border: '2px solid transparent',
  },
  summaryCardHeader: {
    display: 'flex',
    justifyContent: 'space-between',
    alignItems: 'flex-start',
    marginBottom: '15px',
  },
  summaryCardTitle: {
    fontSize: '22px',
    fontWeight: '700',
    color: '#1e293b',
    margin: '0 0 5px 0',
  },
  summaryCardDates: {
    fontSize: '14px',
    color: '#64748b',
    margin: 0,
  },
  summaryCardCost: {
    textAlign: 'right',
  },
  costLabel: {
    display: 'block',
    fontSize: '12px',
    color: '#64748b',
    marginBottom: '4px',
  },
  costValue: {
    display: 'block',
    fontSize: '24px',
    fontWeight: '700',
    color: '#3b82f6',
  },
  summaryCardMeta: {
    display: 'flex',
    gap: '20px',
    fontSize: '14px',
    color: '#475569',
    marginBottom: '15px',
    paddingBottom: '15px',
    borderBottom: '1px solid #e2e8f0',
  },
  summaryCardFooter: {
    display: 'flex',
    justifyContent: 'flex-end',
  },
  viewDetailsText: {
    fontSize: '14px',
    color: '#3b82f6',
    fontWeight: '600',
  },
  modalSubtitle: {
    fontSize: '14px',
    color: '#64748b',
    margin: '5px 0 0 0',
  },
  // Trip Summary Box
  tripSummaryBox: {
    background: '#eff6ff',
    padding: '20px',
    borderRadius: '12px',
    marginBottom: '25px',
  },
  summaryRow: {
    display: 'grid',
    gridTemplateColumns: 'repeat(3, 1fr)',
    gap: '20px',
  },
  summaryCol: {
    display: 'flex',
    flexDirection: 'column',
    gap: '8px',
  },
  summaryLabel: {
    fontSize: '13px',
    color: '#64748b',
    fontWeight: '600',
    textTransform: 'uppercase',
  },
  summaryValue: {
    fontSize: '18px',
    color: '#1e293b',
    fontWeight: '600',
  },
  // Detail Sections
  detailSection: {
    marginBottom: '30px',
  },
  detailSectionHeader: {
    fontSize: '20px',
    fontWeight: '700',
    color: '#1e293b',
    marginBottom: '15px',
    paddingBottom: '10px',
    borderBottom: '2px solid #3b82f6',
  },
  // Flight Details
  flightDetailGrid: {
    display: 'grid',
    gridTemplateColumns: 'repeat(2, 1fr)',
    gap: '15px',
  },
  flightDetailCard: {
    background: '#f8fafc',
    padding: '20px',
    borderRadius: '12px',
    border: '1px solid #e2e8f0',
  },
  flightDetailTitle: {
    fontSize: '16px',
    fontWeight: '700',
    color: '#475569',
    margin: '0 0 10px 0',
  },
  flightDetailRoute: {
    fontSize: '18px',
    fontWeight: '600',
    color: '#1e293b',
    marginBottom: '15px',
  },
  flightDetailInfo: {
    fontSize: '14px',
    color: '#475569',
    lineHeight: '1.8',
  },
  flightPrice: {
    fontSize: '20px',
    fontWeight: '700',
    color: '#3b82f6',
    marginTop: '15px',
  },
  // Hotel Details
  hotelDetailCard: {
    background: '#f8fafc',
    padding: '20px',
    borderRadius: '12px',
    border: '1px solid #e2e8f0',
  },
  hotelDetailHeader: {
    display: 'flex',
    justifyContent: 'space-between',
    alignItems: 'center',
    marginBottom: '10px',
  },
  hotelDetailName: {
    fontSize: '18px',
    fontWeight: '700',
    color: '#1e293b',
    margin: 0,
  },
  hotelDetailRating: {
    fontSize: '14px',
    color: '#64748b',
  },
  hotelPrice: {
    fontSize: '16px',
    fontWeight: '600',
    color: '#3b82f6',
    margin: '10px 0',
  },
  hotelLink: {
    display: 'inline-block',
    fontSize: '14px',
    color: '#3b82f6',
    textDecoration: 'none',
    fontWeight: '600',
    marginTop: '10px',
  },
  // Daily Itinerary
  dailyItineraryList: {
    display: 'flex',
    flexDirection: 'column',
    gap: '15px',
  },
  dayDetailCard: {
    background: '#f8fafc',
    padding: '20px',
    borderRadius: '12px',
    border: '1px solid #e2e8f0',
  },
  dayDetailHeader: {
    display: 'flex',
    justifyContent: 'space-between',
    alignItems: 'center',
    marginBottom: '10px',
  },
  dayNumber: {
    fontSize: '16px',
    fontWeight: '700',
    color: '#3b82f6',
  },
  dayDate: {
    fontSize: '14px',
    color: '#64748b',
    fontWeight: '600',
  },
  dayDetailTitle: {
    fontSize: '16px',
    fontWeight: '600',
    color: '#1e293b',
    margin: '0 0 15px 0',
  },
  dayActivities: {
    display: 'flex',
    flexDirection: 'column',
    gap: '8px',
  },
  activityDetailItem: {
    display: 'flex',
    gap: '10px',
    alignItems: 'flex-start',
  },
  activityBullet: {
    color: '#3b82f6',
    fontWeight: '700',
    fontSize: '18px',
  },
  activityDetailText: {
    fontSize: '14px',
    color: '#475569',
    lineHeight: '1.6',
  },
  // Activities Summary
  activitiesSummaryGrid: {
    display: 'grid',
    gridTemplateColumns: 'repeat(auto-fill, minmax(280px, 1fr))',
    gap: '15px',
  },
  activitySummaryCard: {
    background: '#f8fafc',
    padding: '15px',
    borderRadius: '10px',
    border: '1px solid #e2e8f0',
  },
  activitySummaryName: {
    fontSize: '16px',
    fontWeight: '600',
    color: '#1e293b',
    margin: '0 0 8px 0',
  },
  activitySummaryDesc: {
    fontSize: '13px',
    color: '#64748b',
    marginBottom: '10px',
    lineHeight: '1.5',
  },
  activitySummaryMeta: {
    display: 'flex',
    gap: '15px',
    fontSize: '12px',
    color: '#475569',
  },
  // Cost Breakdown Detail
  costBreakdownDetail: {
    background: '#f8fafc',
    padding: '20px',
    borderRadius: '12px',
  },
  costBreakdownRow: {
    display: 'flex',
    justifyContent: 'space-between',
    padding: '12px 0',
    borderBottom: '1px solid #e2e8f0',
  },
  costBreakdownLabel: {
    fontSize: '14px',
    color: '#475569',
    fontWeight: '500',
  },
  costBreakdownValue: {
    fontSize: '14px',
    color: '#1e293b',
    fontWeight: '600',
  },
  costBreakdownTotal: {
    display: 'flex',
    justifyContent: 'space-between',
    padding: '15px 0 0 0',
    marginTop: '10px',
    borderTop: '2px solid #3b82f6',
  },
  costTotalLabel: {
    fontSize: '16px',
    color: '#1e293b',
    fontWeight: '700',
  },
  costTotalValue: {
    fontSize: '20px',
    color: '#3b82f6',
    fontWeight: '700',
  },
  // Download Button
  downloadButtonContainer: {
    display: 'flex',
    justifyContent: 'center',
    marginTop: '30px',
  },
  downloadButton: {
    padding: '14px 30px',
    background: '#10b981',
    color: 'white',
    border: 'none',
    borderRadius: '12px',
    fontSize: '16px',
    fontWeight: '600',
    cursor: 'pointer',
    transition: 'all 0.3s ease',
    boxShadow: '0 4px 12px rgba(16, 185, 129, 0.3)',
  },
};

export default Dashboard;