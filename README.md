# 🌍 VibeTravel - AI-Powered Trip Planner

An intelligent travel planning application powered by Google's Agent Development Kit (ADK), OpenAI, and SerpAPI. Get personalized destination recommendations, flight & hotel options, and day-by-day itineraries—all in one place!

## ✨ Features

### Phase 1: Destination Discovery 🔍
- **AI-powered location suggestions** based on your budget, interests, and travel dates
- **Interactive rating system** with tilt-based interface (Tinder-style swiping)
- Beautiful destination cards with images from Unsplash

### Phase 2: Smart Planning 🎯
- **Parallel flight search** across multiple airports (40-50% faster!)
- **Hotel recommendations** in 3 categories: Cheapest, Highest Rated, and Luxury
- **Activity suggestions** tailored to your interests and budget
- Real-time pricing and availability

### Phase 3: Itinerary Generation 📅
- **Day-by-day detailed itinerary** with times and activities
- **Accurate cost breakdown** (flights, hotels, activities, meals)
- **PDF export** for easy sharing and offline access
- Save multiple itineraries and compare

## 🚀 Tech Stack

### Backend
- **FastAPI** - High-performance Python web framework
- **Google Agent Development Kit (ADK)** - Multi-agent AI orchestration
- **Gemini 2.5 Flash** - Google's latest LLM model
- **OpenAI GPT-4o-mini** - Airport code lookups
- **SerpAPI** - Real-time flight and hotel data
- **ReportLab** - PDF generation

### Frontend
- **React 19** - Modern UI framework
- **Vanilla JavaScript** - No complex state management needed
- **CSS3** - Custom animations and responsive design

## 📋 Prerequisites

- **Python 3.11+**
- **Node.js 18+** and npm
- **API Keys** (see setup instructions below)

## 🛠️ Installation

### Option 1: Using Conda (Recommended)

```bash
# Clone the repository
git clone <your-repo-url>
cd VibeTravel

# Create conda environment
conda env create -f environment.yml

# Activate environment
conda activate vibetravel
```

### Option 2: Using venv

```bash
# Clone the repository
git clone <your-repo-url>
cd VibeTravel

# Create virtual environment
python -m venv venv

# Activate virtual environment
# On Windows:
venv\Scripts\activate
# On Mac/Linux:
source venv/bin/activate

# Install backend dependencies
cd backend
pip install -r requirements.txt
```

### Frontend Setup

```bash
# Navigate to frontend directory
cd frontend

# Install dependencies
npm install
```

## 🔑 API Keys Setup

Create a `.env` file in the `backend/` directory with the following keys:

```env
# Required API Keys
GOOGLE_API_KEY=your_google_gemini_api_key_here
SERPAPI_API_KEY=your_serpapi_key_here
OPENAI_API_KEY=your_openai_api_key_here


### Getting API Keys:

1. **Google Gemini API** (Free tier available)
   - Visit: https://aistudio.google.com/app/apikey
   - Click "Get API Key"
   - Copy your key

2. **SerpAPI** (Free 100 searches/month)
   - Visit: https://serpapi.com/users/sign_up
   - Register and get your API key
   - Copy from dashboard

3. **OpenAI API** (Pay-as-you-go)
   - Visit: https://platform.openai.com/api-keys
   - Create new secret key
   - Add payment method (GPT-4o-mini is very cheap!)

## 🏃 Running the Application

### Start Backend Server

```bash
# Navigate to backend directory
cd backend

# Activate your environment if not already active
conda activate vibetravel  # or: source venv/bin/activate

# Run the server
uvicorn main:app --reload --port 8000
```

Backend will be running at: **http://localhost:8000**

### Start Frontend Server

```bash
# In a new terminal, navigate to frontend
cd frontend

# Start React development server
npm start
```

Frontend will open automatically at: **http://localhost:3000**

## 📱 Usage Guide

### 1. Search for Destinations
- Enter your home location, budget, travel dates, and interests
- Get 10 AI-curated destination suggestions

### 2. Rate Destinations
- Use the tilt interface to rate destinations (1-10)
- Tilt right = higher rating, tilt left = lower rating
- Destinations rated 5+ appear in "Start Planning"

### 3. Plan Your Trip
- Click a preferred destination
- **Select Flights**: Choose 1 outbound + 1 return flight
- **Select Hotel**: Pick from Cheapest, Highest Rated, or Luxury options
- **Select Activities**: Choose activities you want to include

### 4. Generate Itinerary
- AI creates a day-by-day itinerary with:
  - Departure and arrival details
  - Daily activities with times
  - Restaurant recommendations
  - Free time and flexibility
- View cost breakdown
- Download as PDF

### 5. Manage Itineraries
- View all saved itineraries in "My Itineraries" tab
- Click to view full details
- Download PDFs for offline access


## 🐛 Troubleshooting

### Backend Issues

**Error: `google.genai.errors.ClientError: 429 RESOURCE_EXHAUSTED`**
- **Cause**: Gemini API rate limit exceeded
- **Solution**: 
  1. Check your API key is valid at https://aistudio.google.com/
  2. Wait a few minutes and try again
  3. Consider upgrading to paid tier for higher limits

**Error: `Missing API key`**
- **Cause**: `.env` file not found or keys missing
- **Solution**: Ensure `.env` file exists in `backend/` directory with all required keys

**Error: `Module not found`**
- **Cause**: Dependencies not installed
- **Solution**: Run `pip install -r requirements.txt` in backend directory

### Frontend Issues

**Error: `CORS policy error`**
- **Cause**: Backend not running or wrong port
- **Solution**: Ensure backend is running on port 8000

**Blank screen or white page**
- **Cause**: React build error
- **Solution**: 
  1. Check browser console for errors
  2. Delete `node_modules` and run `npm install` again
  3. Clear browser cache

## 📊 Project Structure

```
VibeTravel/
├── backend/
│   ├── agents/
│   │   ├── phase1/          # Destination finder
│   │   ├── phase2/          # Flights, hotels, activities
│   │   └── phase3/          # Itinerary generator
│   ├── routes/              # FastAPI endpoints
│   ├── tools/               # Utility functions
│   ├── main.py              # FastAPI app
│   ├── requirements.txt     # Python dependencies
│   └── .env                 # API keys (create this!)
├── frontend/
│   ├── src/
│   │   ├── api/             # API client functions
│   │   ├── pages/           # React components
│   │   └── App.js           # Main app component
│   └── package.json         # Node dependencies
├── environment.yml          # Conda environment
└── README.md               # This file
```

