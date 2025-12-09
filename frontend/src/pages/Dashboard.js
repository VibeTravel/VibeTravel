import React, { useState } from 'react';
import DestinationRating from './DestinationRating';
import './Dashboard.css'; // We'll create this

function Dashboard({ destinations, onBack }) {
  const [activeTab, setActiveTab] = useState('suggestions');
  const [allRatings, setAllRatings] = useState([]);
  const [showModal, setShowModal] = useState(false);
  const [isGenerating, setIsGenerating] = useState(false);
  const [selectedDestination, setSelectedDestination] = useState(null);

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

    try {
      // TODO: Create this API call
      // const response = await planItinerary({
      //   destination: destination.destination,
      //   country: destination.country,
      //   origin: 'New York', // Get from stored search request
      //   startDate: '2025-12-20', // Get from stored search request
      //   endDate: '2025-12-28', // Get from stored search request
      //   numTravelers: 2, // Get from stored search request
      //   budget_per_person: 1000 // Get from stored search request
      // });
      
      // Simulate API call for now
      await new Promise(resolve => setTimeout(resolve, 3000));
      
      console.log('Itinerary generated!');
      alert('Itinerary ready! (Next: Show itinerary page)');
      
    } catch (error) {
      console.error('Failed to generate itinerary:', error);
      alert('Failed to generate itinerary. Please try again.');
    } finally {
      setIsGenerating(false);
      setShowModal(false);
    }
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
      {/* Loading Modal */}
      {showModal && (
        <div style={styles.modalOverlay}>
          <div style={styles.modalContent}>
            <div style={styles.spinner}></div>
            <h2 style={styles.modalTitle}>
              Generating your itinerary...
            </h2>
            <p style={styles.modalText}>
              Finding the best flights and hotels for<br/>
              <strong>{selectedDestination?.destination}, {selectedDestination?.country}</strong>
            </p>
            <p style={styles.modalSubtext}>This may take a moment ✈️🏨</p>
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
  padding: '50px 60px',
  borderRadius: '20px',
  textAlign: 'center',
  maxWidth: '500px',
  boxShadow: '0 20px 60px rgba(0, 0, 0, 0.3)',
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
};

export default Dashboard;