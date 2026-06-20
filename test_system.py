import sys
import os
import requests
import json
import time

def test_model_loading():
    """Test if the ML model loads correctly"""
    print("Testing ML model loading...")
    try:
        sys.path.append('ml_model')
        from bot_classifier import BotClassifier
        import joblib
        
        # Load the saved model
        model_data = joblib.load('ml_model/bot_classifier.pkl')
        print("[OK] Model loaded successfully")
        print(f"Features: {len(model_data['feature_names'])}")
        return True
    except Exception as e:
        print(f"[FAIL] Model loading failed: {e}")
        return False

def test_backend_api():
    """Test if the backend API is running"""
    print("Testing backend API...")
    try:
        # Sample behavioral data
        test_data = {
            "sessionId": "test_session_123",
            "timeOnPage": 30.5,
            "totalMouseMovements": 150,
            "totalClicks": 5,
            "totalScrollEvents": 10,
            "avgMouseSpeed": 200.5,
            "mouseSpeedVariance": 5000.2,
            "avgTimeBetweenMoves": 100.3,
            "straightLineRatio": 0.3,
            "avgClickInterval": 800.1,
            "clickIntervalVariance": 50000.5,
            "avgScrollSpeed": 300.2,
            "scrollDirection": 0.1,
            "doubleClickCount": 1
        }
        
        response = requests.post('http://localhost:5000/api/analyze', 
                               json=test_data, timeout=5)
        
        if response.status_code == 200:
            result = response.json()
            print("[OK] Backend API is working")
            print(f"Prediction: {result.get('prediction')}")
            print(f"Confidence: {result.get('confidence', 0):.3f}")
            return True
        else:
            print(f"[FAIL] API returned status code: {response.status_code}")
            return False
            
    except requests.exceptions.ConnectionError:
        print("[FAIL] Backend API is not running")
        return False
    except Exception as e:
        print(f"[FAIL] API test failed: {e}")
        return False

def test_database():
    """Test database functionality"""
    print("Testing database...")
    try:
        import sqlite3
        
        # Check if database exists and has tables
        if os.path.exists('backend/data/interactions.db'):
            conn = sqlite3.connect('backend/data/interactions.db')
            cursor = conn.cursor()
            
            # Check tables
            cursor.execute("SELECT name FROM sqlite_master WHERE type='table';")
            tables = cursor.fetchall()
            
            if len(tables) >= 2:
                print("[OK] Database tables exist")
                return True
            else:
                print("[FAIL] Database tables missing")
                return False
        else:
            print("[FAIL] Database file not found")
            return False
            
    except Exception as e:
        print(f"[FAIL] Database test failed: {e}")
        return False

def main():
    print("=== Bot Detection System Test ===")
    print()
    
    # Test model
    model_ok = test_model_loading()
    print()
    
    # Test database
    db_ok = test_database()
    print()
    
    # Test API (only if backend is running)
    api_ok = test_backend_api()
    print()
    
    # Summary
    print("=== Test Summary ===")
    print(f"ML Model: {'[PASS]' if model_ok else '[FAIL]'}")
    print(f"Database: {'[PASS]' if db_ok else '[FAIL]'}")
    print(f"Backend API: {'[PASS]' if api_ok else '[FAIL] (start backend first)'}")
    
    if model_ok and db_ok:
        print("\nCore components are working!")
        print("\nTo start the full system:")
        print("1. Run: start_backend.bat")
        print("2. Run: start_dashboard.bat") 
        print("3. Run: start_frontend.bat")
        print("4. Open: http://localhost:8000")
    else:
        print("\nSome components need attention")

if __name__ == "__main__":
    main()