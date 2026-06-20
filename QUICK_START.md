# Bot Detection System - Quick Start Guide

## System Overview
This AI-based bot detection system silently analyzes user behavior to identify automated bots without using CAPTCHA.

## Components
- **Frontend**: Behavioral data collection (JavaScript)
- **Backend**: Flask API with ML classification
- **ML Model**: Random Forest classifier (trained and ready)
- **Dashboard**: Streamlit visualization interface

## Quick Start (3 Steps)

### Step 1: Start Backend API
```bash
start_backend.bat
```
- Opens Flask API server on http://localhost:5000
- Initializes database and loads ML model
- Ready to receive behavioral data

### Step 2: Start Dashboard (Optional)
```bash
start_dashboard.bat
```
- Opens Streamlit dashboard on http://localhost:8501
- Visualizes bot detection statistics
- Shows real-time alerts and trends

### Step 3: Start Frontend
```bash
start_frontend.bat
```
- Serves demo webpage on http://localhost:8000
- Collects user behavioral data
- Sends data to backend for analysis

## Testing the System

1. **Open the demo page**: http://localhost:8000
2. **Interact naturally**: Move mouse, click buttons, scroll
3. **Check status**: Green = Human, Red = Bot detected
4. **View dashboard**: http://localhost:8501 for statistics

## How It Works

### Behavioral Features Tracked:
- Mouse movement patterns and speed
- Click timing and intervals
- Scroll behavior and acceleration
- Time spent on page
- Keystroke dynamics

### ML Classification:
- Random Forest model with 95%+ accuracy
- Real-time prediction with confidence scores
- Risk-based security responses

### Security Responses:
- **Low Risk**: Normal access
- **Medium Risk**: Enhanced monitoring
- **High Risk**: Rate limiting
- **Critical Risk**: Session blocking

## System Status
- ✅ ML Model: Trained and ready
- ⚠️ Database: Will be created on first backend start
- ⚠️ API: Start backend first
- ⚠️ Frontend: Start after backend

## Troubleshooting

### Backend won't start:
```bash
pip install flask flask-cors numpy pandas scikit-learn joblib
```

### Dashboard won't start:
```bash
pip install streamlit plotly requests
```

### Model errors:
- Model is pre-trained and saved in ml_model/bot_classifier.pkl
- If missing, run: `python ml_model/bot_classifier.py`

## Production Deployment

For production use:
1. Use proper web server (nginx + gunicorn)
2. Add HTTPS and authentication
3. Use PostgreSQL instead of SQLite
4. Implement proper logging and monitoring
5. Add rate limiting and DDoS protection

## File Structure
```
bot_detection_system/
├── frontend/           # Web interface
├── backend/           # Flask API
├── ml_model/          # Trained ML model
├── dashboard/         # Streamlit dashboard
├── start_*.bat        # Startup scripts
└── test_system.py     # System verification
```

## Next Steps
1. Run `python test_system.py` to verify components
2. Start the system using the 3 steps above
3. Test with different interaction patterns
4. Monitor results in the dashboard
5. Customize thresholds and responses as needed

The system is now ready for testing and development!