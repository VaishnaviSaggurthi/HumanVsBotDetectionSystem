import os
import sys
import subprocess
from ml_model.bot_classifier import BotClassifier
import joblib

def install_requirements():
    """Install required packages"""
    print("Installing required packages...")
    subprocess.check_call([sys.executable, "-m", "pip", "install", "-r", "requirements.txt"])

def train_initial_model():
    """Train the initial ML model"""
    print("Training initial bot detection model...")
    
    # Create directories
    os.makedirs('ml_model', exist_ok=True)
    os.makedirs('backend/data', exist_ok=True)
    
    # Train model
    classifier = BotClassifier()
    trained_model = classifier.train_model()
    
    # Save model
    joblib.dump(trained_model, 'ml_model/bot_classifier.pkl')
    print("Model trained and saved successfully!")

def create_startup_scripts():
    """Create startup scripts for different components"""
    
    # Backend startup script
    backend_script = """@echo off
echo Starting Bot Detection Backend...
cd backend
python app.py
pause
"""
    
    with open('start_backend.bat', 'w') as f:
        f.write(backend_script)
    
    # Dashboard startup script
    dashboard_script = """@echo off
echo Starting Bot Detection Dashboard...
cd dashboard
streamlit run dashboard.py --server.port 8501
pause
"""
    
    with open('start_dashboard.bat', 'w') as f:
        f.write(dashboard_script)
    
    # Frontend startup script (simple HTTP server)
    frontend_script = """@echo off
echo Starting Frontend Server...
cd frontend
python -m http.server 8000
pause
"""
    
    with open('start_frontend.bat', 'w') as f:
        f.write(frontend_script)
    
    print("Startup scripts created successfully!")

def main():
    print("=== Bot Detection System Setup ===")
    
    try:
        # Install requirements
        install_requirements()
        
        # Train initial model
        train_initial_model()
        
        # Create startup scripts
        create_startup_scripts()
        
        print("\n✅ Setup completed successfully!")
        print("\nTo start the system:")
        print("1. Run 'start_backend.bat' to start the API server")
        print("2. Run 'start_dashboard.bat' to start the dashboard")
        print("3. Run 'start_frontend.bat' to start the frontend")
        print("4. Open http://localhost:8000 in your browser")
        
    except Exception as e:
        print(f"❌ Setup failed: {e}")
        sys.exit(1)

if __name__ == "__main__":
    main()