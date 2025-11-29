import React, { useState } from 'react';
import { storeRating } from '../api/storeRating';

function DestinationRating({ destinations, onRatingStored }) {
  const [currentIndex, setCurrentIndex] = useState(0);
  const [isAnimating, setIsAnimating] = useState(false);
  const [isSaving, setIsSaving] = useState(false);

  if (!destinations || destinations.length === 0) {
    return (
      <div style={styles.container}>
        <div style={styles.errorBox}>
          <h2>No destinations found</h2>
        </div>
      </div>
    );
  }

  const currentDestination = destinations[currentIndex];

  const handleRatingClick = async (rating) => {
    setIsSaving(true);

    const ratingData = {
      destination: currentDestination.destination,
      country: currentDestination.country,
      description: currentDestination.description,
      recommended_activities: currentDestination.recommended_activities,
      estimated_budget: currentDestination.estimated_budget,
      rating: rating,
    };

    try {
      const result = await storeRating(ratingData);
      console.log('Rating stored:', result);

      if (onRatingStored) {
        onRatingStored(ratingData);
      }

      setIsAnimating(true);
      
      setTimeout(() => {
        if (currentIndex < destinations.length - 1) {
          setCurrentIndex(currentIndex + 1);
          setIsAnimating(false);
          setIsSaving(false);
        } else {
          setIsAnimating(false);
          setIsSaving(false);
          alert('You\'ve rated all available destinations! Go to "Start Planning" to create your itinerary.');
        }
      }, 400);
    } catch (error) {
      console.error('Failed to store rating:', error);
      setIsSaving(false);
      alert('Failed to save rating. Please try again.');
    }
  };

  const progress = ((currentIndex + 1) / destinations.length) * 100;

  return (
    <div style={styles.container}>
      <div style={styles.progressBar}>
        <div style={{...styles.progressFill, width: `${progress}%`}}></div>
      </div>

      <div style={styles.counter}>
        {currentIndex + 1} / {destinations.length}
      </div>

      <div style={{
        ...styles.card,
        transform: isAnimating ? 'translateX(-100%)' : 'translateX(0)',
        opacity: isAnimating ? 0 : 1,
      }}>
        <div style={styles.imageContainer}>
          <img 
            src={currentDestination.image_url} 
            alt={currentDestination.destination}
            style={styles.image}
          />
          <div style={styles.overlay}>
            <h1 style={styles.destinationTitle}>
              {currentDestination.destination}
            </h1>
            <p style={styles.country}>{currentDestination.country}</p>
          </div>
        </div>

        <div style={styles.content}>
          <div style={styles.section}>
            <h3 style={styles.sectionTitle}>About</h3>
            <p style={styles.description}>{currentDestination.description}</p>
          </div>

          <div style={styles.section}>
            <h3 style={styles.sectionTitle}>Budget</h3>
            <p style={styles.budget}>{currentDestination.estimated_budget}</p>
          </div>

          <div style={styles.section}>
            <h3 style={styles.sectionTitle}>Recommended Activities</h3>
            <ul style={styles.activitiesList}>
              {currentDestination.recommended_activities.map((activity, i) => (
                <li key={i} style={styles.activityItem}>
                  {activity}
                </li>
              ))}
            </ul>
          </div>
        </div>
      </div>

      <div style={styles.ratingSection}>
        <h3 style={styles.ratingTitle}>
          {isSaving ? 'Saving your preference...' : 'How interested are you in this destination?'}
        </h3>
        <p style={styles.ratingSubtitle}>
          Click a number: 0 = Not interested • 10 = Must visit!
        </p>
        <div style={styles.ratingButtons}>
          {[0, 1, 2, 3, 4, 5, 6, 7, 8, 9, 10].map((rating) => (
            <button
              key={rating}
              onClick={() => handleRatingClick(rating)}
              disabled={isSaving}
              style={{
                ...styles.ratingButton,
                ...(isSaving ? styles.ratingButtonDisabled : {})
              }}
            >
              {rating}
            </button>
          ))}
        </div>
        {isSaving && (
          <div style={styles.savingIndicator}>
            <div style={styles.spinner}></div>
          </div>
        )}
      </div>
    </div>
  );
}

const styles = {
  container: {
    minHeight: '100vh',
    paddingBottom: '40px',
  },
  progressBar: {
    height: '6px',
    backgroundColor: 'rgba(255, 255, 255, 0.3)',
    position: 'sticky',
    top: 0,
    zIndex: 100,
  },
  progressFill: {
    height: '100%',
    background: 'linear-gradient(90deg, #3b82f6, #2563eb)',
    transition: 'width 0.4s ease',
  },
  counter: {
    textAlign: 'center',
    padding: '20px',
    fontSize: '15px',
    color: '#1e293b',
    fontWeight: '700',
  },
  card: {
    maxWidth: '600px',
    margin: '0 auto 30px',
    background: 'rgba(255, 255, 255, 0.6)',
    borderRadius: '18px',
    overflow: 'hidden',
    backdropFilter: 'blur(18px)',
    boxShadow: '0 8px 25px rgba(0, 0, 0, 0.12)',
    transition: 'all 0.4s ease',
  },
  imageContainer: {
    position: 'relative',
    height: '320px',
    overflow: 'hidden',
  },
  image: {
    width: '100%',
    height: '100%',
    objectFit: 'cover',
  },
  overlay: {
    position: 'absolute',
    bottom: 0,
    left: 0,
    right: 0,
    background: 'linear-gradient(to top, rgba(0,0,0,0.75), transparent)',
    padding: '35px 25px 20px',
    color: 'white',
  },
  destinationTitle: {
    margin: '0 0 5px 0',
    fontSize: '32px',
    fontWeight: '700',
  },
  country: {
    margin: 0,
    fontSize: '17px',
    opacity: 0.95,
    fontWeight: '500',
  },
  content: {
    padding: '25px',
  },
  section: {
    marginBottom: '22px',
  },
  sectionTitle: {
    fontSize: '14px',
    fontWeight: '700',
    color: '#1e293b',
    marginBottom: '10px',
    textTransform: 'uppercase',
    letterSpacing: '0.5px',
  },
  description: {
    fontSize: '15px',
    lineHeight: '1.7',
    color: '#334155',
    margin: 0,
  },
  budget: {
    fontSize: '22px',
    color: '#3b82f6',
    fontWeight: '700',
    margin: 0,
  },
  activitiesList: {
    listStyle: 'none',
    padding: 0,
    margin: 0,
  },
  activityItem: {
    padding: '10px 0 10px 20px',
    fontSize: '14px',
    color: '#334155',
    borderBottom: '1px solid rgba(255, 255, 255, 0.5)',
    position: 'relative',
  },
  ratingSection: {
    maxWidth: '600px',
    margin: '0 auto',
    padding: '30px 35px',
    background: 'rgba(255, 255, 255, 0.6)',
    borderRadius: '18px',
    backdropFilter: 'blur(18px)',
    boxShadow: '0 8px 25px rgba(0, 0, 0, 0.12)',
  },
  ratingTitle: {
    textAlign: 'center',
    fontSize: '20px',
    marginBottom: '8px',
    color: '#1e293b',
    fontWeight: '700',
  },
  ratingSubtitle: {
    textAlign: 'center',
    fontSize: '14px',
    color: '#64748b',
    marginBottom: '25px',
    fontWeight: '500',
  },
  ratingButtons: {
    display: 'grid',
    gridTemplateColumns: 'repeat(11, 1fr)',
    gap: '10px',
  },
  ratingButton: {
    height: '55px',
    border: 'none',
    borderRadius: '12px',
    background: 'rgba(255, 255, 255, 0.7)',
    fontSize: '17px',
    fontWeight: '700',
    color: '#1e293b',
    cursor: 'pointer',
    transition: 'all 0.2s ease',
    boxShadow: '0 2px 6px rgba(0, 0, 0, 0.08)',
  },
  ratingButtonDisabled: {
    opacity: 0.5,
    cursor: 'not-allowed',
  },
  savingIndicator: {
    textAlign: 'center',
    marginTop: '15px',
  },
  spinner: {
    width: '30px',
    height: '30px',
    margin: '0 auto',
    border: '3px solid rgba(59, 130, 246, 0.2)',
    borderTopColor: '#3b82f6',
    borderRadius: '50%',
    animation: 'spin 0.8s linear infinite',
  },
  errorBox: {
    textAlign: 'center',
    padding: '50px',
    maxWidth: '440px',
    margin: '100px auto',
    background: 'rgba(255, 255, 255, 0.6)',
    borderRadius: '18px',
    backdropFilter: 'blur(18px)',
    boxShadow: '0 8px 25px rgba(0, 0, 0, 0.12)',
  },
};

export default DestinationRating;